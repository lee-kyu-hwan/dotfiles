import pathlib
import sys
import unittest


sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import review_state


class NormalizationTests(unittest.TestCase):
    def test_markdown_ordinals_confidence_and_rejected_severity(self):
        markdown = """Title: Bad severity
Severity: surprising
Confidence: 90
File: lib/a.py
Line: 3
Body: rejected
Recommendation: fix

Title: Valid severity
Severity: Important
Confidence: 85
File: lib/a.py
Line: 7
Body: actual body
Recommendation: fix it
"""
        findings, rejected = review_state.normalize_reviewer_findings("pr-review-toolkit:code-reviewer", markdown, "A")
        self.assertEqual(len(rejected), 1)
        self.assertEqual(findings[0]["original_id"], "producer=pr-review-toolkit:code-reviewer;ordinal=2")
        self.assertEqual(findings[0]["severity"], "high")
        self.assertEqual(findings[0]["finding_confidence"], 0.85)

    def test_markdown_parser_keeps_multiline_body_and_label_like_text(self):
        markdown = """Title: Preserve body
Severity: Critical
Confidence: 100
File: lib/a.py
Line: 3
Body: first paragraph

file: this is body text, not a field
second paragraph
Recommendation: first action
second action
"""
        record = review_state._markdown_records(markdown)[0]
        self.assertEqual(record["severity"], "Critical")
        self.assertEqual(record["file"], "lib/a.py")
        self.assertEqual(record["line"], "3")
        self.assertEqual(record["body"], "first paragraph\n\nfile: this is body text, not a field\nsecond paragraph")
        self.assertEqual(record["recommendation"], "first action\nsecond action")

    def test_markdown_parser_accepts_late_metadata_and_decorated_title_labels(self):
        late_metadata = """Title: Late metadata
Body: actual body
Severity: High
Confidence: 90
File: lib/a.py
Line: 3
Recommendation: fix
"""
        decorated_title = """**Title:** Decorated title
Severity: Low
Confidence: 80
File: lib/b.py
Line: 4
Body: actual body
Recommendation: fix
"""
        for markdown, expected_title, expected_file in (
            (late_metadata, "Late metadata", "lib/a.py"),
            (decorated_title, "Decorated title", "lib/b.py"),
        ):
            with self.subTest(markdown=markdown):
                findings, rejected = review_state.normalize_reviewer_findings("pr-test-analyzer", markdown, "A")
                self.assertEqual(rejected, [])
                self.assertEqual([(item["title"], item["file"]) for item in findings], [(expected_title, expected_file)])

    def test_round_zero_prompt_pins_the_markdown_label_grammar(self):
        prompt = review_state.build_round_zero_prompts({"base_sha": "a", "head_sha": "b", "files": [], "diff": ""})["claude"]
        self.assertIn("one finding per block", prompt)
        self.assertIn("Title: first", prompt)
        self.assertIn("one bare Label: value per line", prompt)
        self.assertIn("Body: and Recommendation: last", prompt)

    def test_claude_and_codex_fixtures_have_the_same_normalized_shape(self):
        claude, _ = review_state.normalize_reviewer_findings("pr-test-analyzer", """Title: Same\nSeverity: Low\nConfidence: 80\nFile: a.py\nLine: 2\nBody: detail\nRecommendation: fix\n""", "A", "claude")
        codex, _ = review_state.normalize_reviewer_findings("codex", [{"severity": "low", "finding_confidence": .8, "file": "a.py", "line_start": 2, "line_end": 2, "title": "Same", "body": "detail", "recommendation": "fix"}], "B", "codex")
        self.assertEqual(set(claude[0]), set(codex[0]))
        self.assertEqual({key: claude[0][key] for key in claude[0] if key not in {"source", "producer", "original_id", "finding_id"}}, {key: codex[0][key] for key in codex[0] if key not in {"source", "producer", "original_id", "finding_id"}})

    def test_critical_and_missing_severity_have_specified_defaults(self):
        raw = [
            {"severity": "Critical", "confidence": 90, "file": "a.py", "line_start": 1, "line_end": 1, "title": "critical", "body": "detail", "recommendation": "fix"},
            {"confidence": 90, "file": "a.py", "line_start": 2, "line_end": 2, "title": "default", "body": "detail", "recommendation": "fix"},
        ]
        findings, _ = review_state.normalize_reviewer_findings("codex", raw, "A")
        self.assertEqual([item["severity"] for item in findings], ["critical", "medium"])

    def test_finding_id_is_opaque_and_group_sensitive(self):
        left = review_state.derive_finding_id("A", "producer=x;ordinal=1", "lib/a.py", 2, 4, "Title", "Body")
        right = review_state.derive_finding_id("B", "producer=x;ordinal=1", "lib/a.py", 2, 4, "Title", "Body")
        self.assertRegex(left, r"^fid_[0-9a-f]{64}$")
        self.assertNotIn("producer", left)
        self.assertNotEqual(left, right)

    def test_finding_id_changes_for_each_canonical_input_field(self):
        baseline = ("A", "producer=x;ordinal=1", "lib/a.py", 2, 4, "Title", "Body")
        original_only = ("A", "producer=x;ordinal=2", "lib/a.py", 2, 4, "Title", "Body")
        self.assertNotEqual(review_state.derive_finding_id(*baseline), review_state.derive_finding_id(*original_only))
        for index, changed in ((2, "lib/b.py"), (3, 3), (4, 5), (5, "Other"), (6, "Other body")):
            values = list(baseline); values[index] = changed
            self.assertNotEqual(review_state.derive_finding_id(*baseline), review_state.derive_finding_id(*values))

    def test_invalid_paths_lines_and_confidence_are_rejected_and_bodies_share_shape(self):
        valid = {"severity": "low", "confidence": 1, "file": "a.py", "line_start": 1, "line_end": 1, "title": "x", "body": "b", "recommendation": "r"}
        invalid_records = [
            {**valid, "confidence": 101},
            {**valid, "file": "../a.py"},
            {**valid, "file": "/a.py"},
            {**valid, "line_start": 0},
            {**valid, "line_start": 2, "line_end": 1},
        ]
        for ordinal, raw in enumerate(invalid_records, 1):
            with self.subTest(raw=raw):
                findings, rejected = review_state.normalize_reviewer_findings("codex", [raw], "A")
                self.assertEqual(findings, [])
                self.assertEqual(rejected[0]["original_id"], "producer=codex;ordinal=1")
        first, _ = review_state.normalize_reviewer_findings("codex", [{"severity": "low", "confidence": 1, "file": "a.py", "line_start": 1, "line_end": 1, "title": "x", "body": "one", "recommendation": "r"}], "A")
        second, _ = review_state.normalize_reviewer_findings("codex", [{"severity": "low", "confidence": 1, "file": "a.py", "line_start": 1, "line_end": 1, "title": "x", "body": "two", "recommendation": "r"}], "B")
        self.assertEqual(first[0]["body"].split(":", 1)[0], second[0]["body"].split(":", 1)[0])

    def test_the_reviewer_agent_severity_scale_is_accepted(self):
        """Producers are asked for a Severity label on the Critical/Important/Minor/Trivial scale,
        so the lower half of that scale must map instead of dropping the whole record."""
        template = """Title: {label} finding
Severity: {label}
Confidence: 80
File: lib/a.py
Line: 3
Body: {label} detail
Recommendation: fix
"""
        for label, expected in (("Critical", "critical"), ("Important", "high"), ("Minor", "low"), ("Trivial", "low")):
            with self.subTest(label=label):
                findings, rejected = review_state.normalize_reviewer_findings("pr-review-toolkit:code-reviewer", template.format(label=label), "A")
                self.assertEqual(rejected, [])
                self.assertEqual(findings[0]["severity"], expected)

    def test_the_round_zero_prompt_names_every_severity_word_normalization_accepts(self):
        """A producer that guesses a plausible-but-unlisted word loses its whole finding, so the
        prompt must state the vocabulary and cannot drift from what normalization admits."""
        prompt = review_state.build_round_zero_prompts({"base_sha": "a", "head_sha": "b", "files": [], "diff": ""})["claude"]
        self.assertTrue(review_state.SEVERITY_BY_WORD)
        for word in review_state.SEVERITY_BY_WORD:
            with self.subTest(word=word):
                self.assertIn(word, prompt)
                self.assertIsNotNone(review_state._severity(word))

    def test_round_zero_prompts_cap_the_embedded_diff(self):
        """The real run embedded a 1.1MB diff and produced a 1.16MB prompt per reviewer. The
        prompt must be bounded and must tell the reviewer that hunks were withheld."""
        big = "\n".join("+line %d" % index for index in range(200000))
        self.assertGreater(len(big.encode()), review_state.MAX_PROMPT_DIFF_BYTES)
        prompts = review_state.build_round_zero_prompts({"base_sha": "a", "head_sha": "b", "files": ["a.py"], "diff": big})
        for source, prompt in prompts.items():
            with self.subTest(source=source):
                self.assertLess(len(prompt.encode()), review_state.MAX_PROMPT_DIFF_BYTES + 4096)
                self.assertIn("diff truncated", prompt)

    def test_a_diff_within_the_cap_is_embedded_whole_and_unmarked(self):
        prompts = review_state.build_round_zero_prompts({"base_sha": "a", "head_sha": "b", "files": ["a.py"], "diff": "+one small line"})
        for source, prompt in prompts.items():
            with self.subTest(source=source):
                self.assertIn("+one small line", prompt)
                self.assertNotIn("diff truncated", prompt)


if __name__ == "__main__":
    unittest.main()
