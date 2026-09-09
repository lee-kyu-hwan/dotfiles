import pathlib
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest


sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import review_state


def string_values(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from string_values(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from string_values(nested)


class SynthesisTests(unittest.TestCase):
    def test_producer_is_not_a_reviewer_source_and_critique_identity_is_removed(self):
        findings = [
            {"source": "claude", "producer": "code-reviewer", "original_id": "producer=code-reviewer;ordinal=1", "severity": "high", "file": "a.py", "line_start": 1, "line_end": 1, "title": "silent-failure-hunter", "body": "Finding body: producer=code-reviewer;ordinal=1", "recommendation": "fix"},
            {"source": "claude", "producer": "type-design-analyzer", "original_id": "producer=type-design-analyzer;ordinal=1", "severity": "high", "file": "b.py", "line_start": 1, "line_end": 1, "title": "type-design-analyzer", "body": "detail", "recommendation": "fix"},
            {"source": "codex", "producer": "codex", "original_id": "producer=codex;ordinal=1", "severity": "high", "file": "a.py", "line_start": 1, "line_end": 1, "title": "other", "body": "detail", "recommendation": "fix"},
        ]
        view, sidecar = review_state.build_anonymous_view(
            "run", 1, findings, [{"finding_id": "fid_x", "reviewer": "codex", "verdict": "유지", "evidence": []}], [],
        )
        claude_groups = {sidecar["findings"][item["finding_id"]]["group"] for item in view["findings"] if sidecar["findings"][item["finding_id"]]["source"] == "claude"}
        self.assertEqual(len(claude_groups), 1)
        self.assertNotIn("reviewer", view["critiques"][0])
        public_fields = {"finding_id", "group", "severity", "file", "line_start", "line_end", "title", "body", "recommendation"}
        self.assertTrue(all(set(item) == public_fields for item in view["findings"]))
        self.assertTrue(all("source" not in item for item in view["findings"]))
        forbidden = {"code-reviewer", "silent-failure-hunter", "type-design-analyzer", "producer=code-reviewer;ordinal=1"}
        self.assertTrue(all(token not in text for token in forbidden for text in string_values(view)))

    def test_sidecar_preserves_every_finding_provenance_for_report_restoration(self):
        findings = [
            {"source": "claude", "producer": "comment-analyzer", "original_id": "producer=comment-analyzer;ordinal=1", "severity": "high", "file": "a.py", "line_start": 1, "line_end": 1, "title": "Claude finding", "body": "detail", "recommendation": "fix"},
            {"source": "codex", "producer": "codex", "original_id": "producer=codex;ordinal=1", "severity": "low", "file": "b.py", "line_start": 2, "line_end": 3, "title": "Codex finding", "body": "detail", "recommendation": "fix"},
        ]
        view, sidecar = review_state.build_anonymous_view("run", 1, findings, [], [])
        expected = {}
        for item in findings:
            group = sidecar["source_groups"][item["source"]]
            finding_id = review_state.derive_finding_id(group, item["original_id"], item["file"], item["line_start"], item["line_end"], item["title"], item["body"])
            expected[finding_id] = {key: item[key] for key in ("source", "producer", "original_id")} | {"group": group}
        self.assertEqual(sidecar["findings"], expected)
        report = review_state.render_report({
            "target": {"base_sha": "base", "head_sha": "head", "files": ["a.py", "b.py"]},
            "termination_reason": "round_cap", "reviewers": {}, "findings": view["findings"],
            "critiques": [], "synthesis": [], "provenance": sidecar,
        })
        for finding_id, provenance in expected.items():
            self.assertIn(f"{finding_id} ({provenance['source']}):", report)

    def test_synthesis_rejects_invalid_group_membership_instead_of_trusting_labels(self):
        manifest = {"A": {"fid_a"}, "B": {"fid_b"}}
        with self.assertRaises(ValueError):
            review_state.normalize_synthesis_decisions([{
                "classification": "합의", "decision_confidence": 0.5, "rationale": "invalid",
                "group_a_finding_ids": ["fid_b"], "group_b_finding_ids": ["fid_a"],
                "claims": {"A": "a", "B": "b"},
            }], manifest)

    def test_synthesis_covers_each_finding_once_without_enforcing_candidate_boundaries(self):
        manifest = {"A": {"fid_a", "fid_c"}, "B": {"fid_b"}}
        candidates = [{"finding_ids": ["fid_a", "fid_b"]}, {"finding_ids": ["fid_c"]}]
        merged = [{"classification": "불일치", "decision_confidence": .5, "rationale": "one broader defect", "group_a_finding_ids": ["fid_a", "fid_c"], "group_b_finding_ids": ["fid_b"], "claims": {"A": "a", "B": "b"}}]
        split = [
            {"classification": "합의", "decision_confidence": .5, "rationale": "first", "group_a_finding_ids": ["fid_a"], "group_b_finding_ids": ["fid_b"], "claims": {"A": "a", "B": "b"}},
            {"classification": "단일 출처", "decision_confidence": .5, "rationale": "second", "group_a_finding_ids": ["fid_c"], "group_b_finding_ids": [], "claims": {"A": "c", "B": ""}},
        ]
        self.assertEqual(review_state.normalize_synthesis_decisions(merged, manifest), merged)
        self.assertEqual(review_state.normalize_synthesis_decisions(split, manifest), split)
        for invalid in (split[:1], split + [split[0]]):
            with self.assertRaises(ValueError):
                review_state.normalize_synthesis_decisions(invalid, manifest)
        with self.assertRaises(TypeError):
            review_state.normalize_synthesis_decisions(merged, manifest, candidates)

    def test_synthesis_classification_is_the_synthesizers_judgment(self):
        decision = {"classification": "불일치", "decision_confidence": .5, "rationale": "claims conflict", "group_a_finding_ids": ["fid_a"], "group_b_finding_ids": ["fid_b"], "claims": {"A": "a", "B": "b"}}
        self.assertEqual(review_state.normalize_synthesis_decisions([decision], {"A": {"fid_a"}, "B": {"fid_b"}}), [decision])
    def test_group_assignment_id_derivation_sort_shuffle_and_masking(self):
        producers = list(review_state.CLAUDE_PRODUCERS)
        findings = [
            {"source": "claude", "original_id": "producer=pr-review-toolkit:code-reviewer;ordinal=1", "severity": "high", "file": "a.py", "line_start": 1, "line_end": 2, "title": producers[0], "body": "Finding body: producer=pr-review-toolkit:code-reviewer;ordinal=1", "recommendation": "fix"},
            {"source": "codex", "original_id": "producer=codex;ordinal=1", "severity": "high", "file": "a.py", "line_start": 1, "line_end": 2, "title": "other", "body": "Finding body: detail", "recommendation": "fix"},
        ]
        view, sidecar = review_state.build_anonymous_view("run-1", 1, findings, [], producers)
        reversed_view, _ = review_state.build_anonymous_view("run-1", 1, list(reversed(findings)), [], producers)
        self.assertEqual(view["findings"], reversed_view["findings"])
        self.assertEqual(set(sidecar["source_groups"].values()), {"A", "B"})
        forbidden = producers + [finding["original_id"] for finding in findings]
        self.assertTrue(all(all(token not in text for token in forbidden) for text in string_values(view)))
        self.assertTrue(sidecar["masks"])
        self.assertTrue(all(item["finding_id"].startswith("fid_") for item in view["findings"]))

    def test_anonymous_masking_leaves_claude_and_codex_aliases_symmetric(self):
        findings = [
            {"source": "claude", "producer": "pr-test-analyzer", "original_id": "producer=pr-test-analyzer;ordinal=1", "severity": "low", "file": "dot_claude/example.py", "line_start": 1, "line_end": 1, "title": "claude and codex", "body": "claude and codex", "recommendation": "fix"},
            {"source": "codex", "producer": "codex", "original_id": "producer=codex;ordinal=1", "severity": "low", "file": "dot_codex/example.py", "line_start": 1, "line_end": 1, "title": "claude and codex", "body": "claude and codex", "recommendation": "fix"},
        ]
        view, _ = review_state.build_anonymous_view("run", 1, findings, [])
        public_text = "\n".join(string_values(view))
        self.assertIn("claude", public_text)
        self.assertIn("codex", public_text)
        self.assertIn("dot_claude/example.py", public_text)
        self.assertIn("dot_codex/example.py", public_text)

    def test_group_assignment_uses_run_id_and_execution_parity_per_source(self):
        sources = {"claude", "codex"}
        fixtures = (("a" * 40, "b" * 40), ("c" * 40, "d" * 40), ("e" * 40, "f" * 40), ("0" * 40, "1" * 40), ("2" * 40, "3" * 40), ("4" * 40, "5" * 40))
        for base, head in fixtures:
            with self.subTest(base=base, head=head):
                first_number = 7
                first_run_id = review_state.make_run_id(base, head, first_number)
                second_run_id = review_state.make_run_id(base, head, first_number + 1)
                first = review_state.assign_anonymous_groups(first_run_id, first_number, sources)
                second = review_state.assign_anonymous_groups(second_run_id, first_number + 1, sources)
                self.assertEqual(first, review_state.assign_anonymous_groups(first_run_id, first_number, sources))
                for source in sources:
                    self.assertNotEqual(first[source], second[source])

        first_target = review_state.make_run_id("a" * 40, "b" * 40, 7)
        second_target = review_state.make_run_id("c" * 40, "d" * 40, 7)
        for run_id in (first_target, second_target):
            target = run_id.rsplit("-", 1)[0]
            labels = ("A", "B") if hashlib.sha256(target.encode("utf-8")).digest()[0] & 1 else ("B", "A")
            expected = {source: labels[index] for index, source in enumerate(("claude", "codex"))}
            self.assertEqual(review_state.assign_anonymous_groups(run_id, 7, sources), expected)

    def test_synthesis_prompt_supplies_classification_rules_without_python_oracle(self):
        finding = {"severity": "low", "finding_confidence": .8, "file": "x.py", "line_start": 1, "line_end": 1, "title": "same", "body": "detail", "recommendation": "fix"}
        class Reviewer:
            def start(self, source, prompt): return source
            def read(self, handle): return {"status": "ok", "payload": {"verdict": "ok", "summary": "", "findings": [finding], "next_steps": []}}
        class Synthesizer:
            def __init__(self): self.prompt = None
            def start(self, source, prompt): self.prompt = prompt; return prompt
            def read(self, prompt):
                groups = {item["group"]: item["finding_id"] for item in json.loads(prompt)["anonymous_view"]["findings"]}
                return {"status": "ok", "payload": {"decisions": [{"classification": "불일치", "decision_confidence": .5, "rationale": "synthesizer judgment", "group_a_finding_ids": [groups["A"]], "group_b_finding_ids": [groups["B"]], "claims": {"A": "a", "B": "b"}}]}}
        synthesis = Synthesizer()
        with tempfile.TemporaryDirectory() as temporary_directory:
            review_state.run_dual_review(pathlib.Path(temporary_directory), {"base_sha": "a", "head_sha": "b", "files": ["x.py"]}, {"claude": Reviewer(), "codex": Reviewer()}, synthesis_adapter=synthesis, requested_rounds=1)
        contract = json.loads(synthesis.prompt)["contract"]
        self.assertIn("same issue with both claims maintained or unverified is 합의", contract)
        self.assertIn("conflicting claims or valid refutation is 불일치", contract)
        self.assertIn("an issue from only one group is 단일 출처", contract)
        self.assertIn("Candidate issues are source-neutral assistance only: decide same-defect boundaries yourself and may merge or split them.", contract)

    def test_synthesis_decisions_preserve_disagreement_and_empty_missing_group(self):
        decisions = review_state.normalize_synthesis_decisions([
            {"classification": "불일치", "decision_confidence": 0.6, "rationale": "conflict", "group_a_finding_ids": ["fid_a"], "group_b_finding_ids": ["fid_b"], "claims": {"A": "a", "B": "b"}},
            {"classification": "단일 출처", "decision_confidence": 0.8, "rationale": "alone", "group_a_finding_ids": ["fid_c"], "claims": {"A": "a", "B": ""}},
        ])
        self.assertEqual(decisions[0]["classification"], "불일치")
        self.assertEqual(decisions[1]["group_b_finding_ids"], [])

    def test_conflicting_claims_without_refutation_are_reported_as_disagreement(self):
        finding = {"severity": "high", "finding_confidence": .8, "file": "x.py", "line_start": 1, "line_end": 1, "title": "same location", "body": "pr-test-analyzer detail", "recommendation": "fix"}
        envelope = {"verdict": "ok", "summary": "", "findings": [finding], "next_steps": []}
        class Reviewer:
            def start(self, source, prompt): return source
            def read(self, source): return {"status": "ok", "payload": envelope}
        class Critique:
            def start(self, source, prompt): return prompt
            def read(self, prompt):
                return {"status": "ok", "payload": {"critiques": [{"finding_id": item["finding_id"], "verdict": "유지", "evidence": [{"file": "x.py", "line_start": 1, "line_end": 1}], "new_findings": []} for item in json.loads(prompt)["opposing_findings"]]}}
        class Synthesizer:
            def start(self, source, prompt): return prompt
            def read(self, prompt):
                findings = json.loads(prompt)["anonymous_view"]["findings"]
                groups = {item["group"]: item["finding_id"] for item in findings}
                return {"status": "ok", "payload": {"decisions": [{"classification": "불일치", "decision_confidence": .7, "rationale": "the claims conflict", "group_a_finding_ids": [groups["A"]], "group_b_finding_ids": [groups["B"]], "claims": {"A": "claim one", "B": "claim two"}}]}}
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = review_state.run_dual_review(pathlib.Path(temporary_directory), {"base_sha": "a", "head_sha": "b", "files": ["x.py"], "line_ranges": {"x.py": [[1, 1]]}}, {"claude": Reviewer(), "codex": Reviewer()}, Critique(), Synthesizer(), requested_rounds=1)
            run_dir = pathlib.Path(result["run_dir"])
            synthesis = json.loads((run_dir / "synthesis.json").read_text())
            report = (run_dir / "report.md").read_text()
            input_view = json.loads((run_dir / "synthesis-input.json").read_text())
            sidecar = json.loads((run_dir / "provenance.json").read_text())
        self.assertNotEqual(result["termination_reason"], "reviewer_failure")
        self.assertEqual(synthesis[0]["classification"], "불일치")
        self.assertIn("## 두 리뷰어가 갈린 지점", report)
        self.assertIn("claim one", report)
        self.assertIn("Finding body: pr-test-analyzer detail", report)
        self.assertIn("claude=", report)
        self.assertIn("codex=", report)
        self.assertNotIn("<redacted:", report)
        self.assertNotIn("pr-test-analyzer", json.dumps(input_view))
        self.assertIn("<redacted:", json.dumps(input_view))
        self.assertEqual(set(input_view), {"findings", "critiques", "candidate_issues"})
        self.assertTrue((set(sidecar) - {"findings"}).isdisjoint(input_view))
        for key in ("source", "producer", "original_id", "source_groups", "execution_number", "seed", "masks"):
            self.assertNotIn(key, json.dumps(input_view))

    def test_report_restores_masked_tokens_the_synthesizer_echoed_back(self):
        """The synthesizer only ever sees redaction markers, so whatever it quotes comes back
        masked. The report must un-mask it; otherwise anonymization leaks into the deliverable."""
        finding = {"severity": "high", "finding_confidence": .8, "file": "x.py", "line_start": 1, "line_end": 1, "title": "same location", "body": "pr-test-analyzer detail", "recommendation": "fix"}
        envelope = {"verdict": "ok", "summary": "", "findings": [finding], "next_steps": []}
        class Reviewer:
            def start(self, source, prompt): return source
            def read(self, source): return {"status": "ok", "payload": envelope}
        class Critique:
            def start(self, source, prompt): return prompt
            def read(self, prompt):
                return {"status": "ok", "payload": {"critiques": [{"finding_id": item["finding_id"], "verdict": "유지", "evidence": [{"file": "x.py", "line_start": 1, "line_end": 1}], "new_findings": []} for item in json.loads(prompt)["opposing_findings"]]}}
        class EchoingSynthesizer:
            """Quotes the masked body straight back, the way a real synthesizer would."""
            def start(self, source, prompt): return prompt
            def read(self, prompt):
                view = json.loads(prompt)["anonymous_view"]
                groups = {item["group"]: item for item in view["findings"]}
                quoted = groups["A"]["body"]
                return {"status": "ok", "payload": {"decisions": [{"classification": "불일치", "decision_confidence": .7, "rationale": "A reports " + quoted, "group_a_finding_ids": [groups["A"]["finding_id"]], "group_b_finding_ids": [groups["B"]["finding_id"]], "claims": {"A": quoted, "B": "no such defect"}}]}}
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = review_state.run_dual_review(pathlib.Path(temporary_directory), {"base_sha": "a", "head_sha": "b", "files": ["x.py"], "line_ranges": {"x.py": [[1, 1]]}}, {"claude": Reviewer(), "codex": Reviewer()}, Critique(), EchoingSynthesizer(), requested_rounds=1)
            run_dir = pathlib.Path(result["run_dir"])
            report = (run_dir / "report.md").read_text()
            input_view = json.loads((run_dir / "synthesis-input.json").read_text())
            synthesis = json.loads((run_dir / "synthesis.json").read_text())
        # What the synthesizer received and echoed really was masked.
        self.assertIn("<redacted:", json.dumps(input_view))
        self.assertIn("<redacted:", json.dumps(synthesis))
        self.assertNotIn("pr-test-analyzer", json.dumps(input_view))
        # The report restores it and carries no redaction marker anywhere.
        self.assertNotIn("<redacted:", report)
        self.assertIn("A reports Finding body: pr-test-analyzer detail", report)
        self.assertIn('"claude": "Finding body: pr-test-analyzer detail"', report)
        self.assertIn("claude=", report)
        self.assertIn("codex=", report)

    def test_supplied_group_map_must_cover_every_finding_source(self):
        """A caller-supplied map that omits a source would silently drop that finding's group."""
        findings = [{"source": "codex", "producer": "codex", "original_id": "o1", "severity": "high",
                     "file": "x.py", "line_start": 1, "line_end": 1, "title": "t", "body": "b",
                     "recommendation": "r"}]
        with self.assertRaises(ValueError):
            review_state.build_anonymous_view("target-000001", 1, findings, [], source_groups={"claude": "A"})

    def test_single_source_run_still_restores_the_empty_reviewers_label(self):
        """Both reviewers valid but one finds nothing: the empty group must still be restorable."""
        finding = {"severity": "high", "finding_confidence": .8, "file": "x.py", "line_start": 1, "line_end": 1, "title": "only one side", "body": "detail", "recommendation": "fix"}
        class Loud:
            def start(self, source, prompt): return source
            def read(self, source): return {"status": "ok", "payload": {"verdict": "ok", "summary": "", "findings": [finding], "next_steps": []}}
        class Quiet:
            def start(self, source, prompt): return source
            def read(self, source): return {"status": "ok", "payload": {"verdict": "ok", "summary": "nothing found", "findings": [], "next_steps": []}}
        class Critique:
            def start(self, source, prompt): return prompt
            def read(self, prompt):
                return {"status": "ok", "payload": {"critiques": [{"finding_id": item["finding_id"], "verdict": "유지", "evidence": [{"file": "x.py", "line_start": 1, "line_end": 1}], "new_findings": []} for item in json.loads(prompt)["opposing_findings"]]}}
        class Synthesizer:
            def start(self, source, prompt): return prompt
            def read(self, prompt):
                findings = json.loads(prompt)["anonymous_view"]["findings"]
                by_group = {item["group"]: item["finding_id"] for item in findings}
                return {"status": "ok", "payload": {"decisions": [{"classification": "단일 출처", "decision_confidence": .9, "rationale": "reported by one group only", "group_a_finding_ids": [by_group["A"]] if "A" in by_group else [], "group_b_finding_ids": [by_group["B"]] if "B" in by_group else [], "claims": {"A": "seen" if "A" in by_group else "", "B": "seen" if "B" in by_group else ""}}]}}
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = review_state.run_dual_review(pathlib.Path(temporary_directory), {"base_sha": "a", "head_sha": "b", "files": ["x.py"], "line_ranges": {"x.py": [[1, 1]]}}, {"claude": Loud(), "codex": Quiet()}, Critique(), Synthesizer(), requested_rounds=1)
            run_dir = pathlib.Path(result["run_dir"])
            report = (run_dir / "report.md").read_text()
            sidecar = json.loads((run_dir / "provenance.json").read_text())
        # Codex produced no findings, yet its group label is still restorable.
        self.assertEqual(set(sidecar["source_groups"]), {"claude", "codex"})
        self.assertIn("claude=", report)
        self.assertIn("codex=", report)
        self.assertNotIn("<redacted:", report)
        for line in report.splitlines():
            self.assertNotRegex(line, r"(?<![0-9A-Za-z_])[AB]=")

    def test_mask_sidecar_is_byte_stable_across_hash_seeds(self):
        script = """import json, sys
sys.path.insert(0, sys.argv[1])
import review_state
findings=[{'source':'claude','producer':'pr-test-analyzer','original_id':'original-id-alpha','severity':'high','file':'a.py','line_start':1,'line_end':1,'title':'comment-analyzer pr-test-analyzer original-id-alpha original-id-bravo','body':'detail','recommendation':'fix'},{'source':'codex','producer':'codex','original_id':'original-id-bravo','severity':'high','file':'b.py','line_start':1,'line_end':1,'title':'detail','body':'detail','recommendation':'fix'}]
print(json.dumps(review_state.build_anonymous_view('run', 1, findings, [])[1], ensure_ascii=False, sort_keys=True, separators=(',', ':')))
"""
        scripts = str(pathlib.Path(__file__).resolve().parents[1] / "scripts")
        outputs = []
        for seed in ("1", "2"):
            environment = dict(os.environ, PYTHONHASHSEED=seed, PYTHONDONTWRITEBYTECODE="1")
            outputs.append(subprocess.check_output([sys.executable, "-c", script, scripts], text=True, env=environment))
        self.assertEqual(outputs[0], outputs[1])

    def test_a_refuted_finding_makes_a_one_sided_disagreement_valid(self):
        """Spec R6.4: a valid refutation is a 불일치, and a refutation arrives as a critique verdict
        rather than as a counterpart finding, so the opposing group has nothing to cite."""
        decision = {"classification": "불일치", "decision_confidence": .8, "rationale": "the opposing side refuted it with in-hunk evidence", "group_a_finding_ids": ["fid_a"], "group_b_finding_ids": [], "claims": {"A": "the guard is missing", "B": "the guard is on the preceding line"}}
        manifest = {"A": {"fid_a"}, "B": set()}
        self.assertEqual(review_state.normalize_synthesis_decisions([decision], manifest, refuted_ids={"fid_a"}), [decision])

    def test_a_one_sided_disagreement_without_a_refutation_is_still_rejected(self):
        decision = {"classification": "불일치", "decision_confidence": .8, "rationale": "nothing refuted this", "group_a_finding_ids": ["fid_a"], "group_b_finding_ids": [], "claims": {"A": "the guard is missing", "B": ""}}
        manifest = {"A": {"fid_a"}, "B": set()}
        with self.assertRaises(ValueError):
            review_state.normalize_synthesis_decisions([decision], manifest, refuted_ids=set())

    def test_a_refutation_only_disagreement_does_not_terminate_the_run(self):
        """The most common disagreement — one side raises it, the other refutes it — must survive
        the pipeline instead of failing normalization and reporting reviewer_failure."""
        envelopes = {
            "claude": {"verdict": "ok", "summary": "", "findings": [{"severity": "high", "finding_confidence": .8, "file": "x.py", "line_start": 1, "line_end": 1, "title": "claude issue", "body": "claude detail", "recommendation": "fix"}], "next_steps": []},
            "codex": {"verdict": "ok", "summary": "", "findings": [{"severity": "high", "finding_confidence": .8, "file": "x.py", "line_start": 2, "line_end": 2, "title": "codex issue", "body": "codex detail", "recommendation": "fix"}], "next_steps": []},
        }
        class Reviewer:
            def start(self, source, prompt): return source
            def read(self, source): return {"status": "ok", "payload": envelopes[source]}
        class Critique:
            def start(self, source, prompt): return (source, prompt)
            def read(self, started):
                reviewer, prompt = started
                verdict = "반증됨" if reviewer == "codex" else "유지"
                return {"status": "ok", "payload": {"critiques": [{"finding_id": item["finding_id"], "verdict": verdict, "evidence": [{"file": "x.py", "line_start": 1, "line_end": 2}], "new_findings": []} for item in json.loads(prompt)["opposing_findings"]]}}
        class Synthesizer:
            def start(self, source, prompt): return prompt
            def read(self, prompt):
                view = json.loads(prompt)["anonymous_view"]
                refuted = {item["finding_id"] for item in view["critiques"] if item.get("verdict") == "반증됨"}
                decisions = []
                for item in sorted(view["findings"], key=lambda entry: entry["finding_id"]):
                    ids = {"group_a_finding_ids": [], "group_b_finding_ids": []}
                    ids["group_%s_finding_ids" % item["group"].lower()] = [item["finding_id"]]
                    is_refuted = item["finding_id"] in refuted
                    decisions.append(dict(ids, classification="불일치" if is_refuted else "단일 출처", decision_confidence=.7, rationale="refuted with evidence" if is_refuted else "only one group reported it", claims={"A": "claim one", "B": "claim two"}))
                return {"status": "ok", "payload": {"decisions": decisions}}
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = review_state.run_dual_review(pathlib.Path(temporary_directory), {"base_sha": "a", "head_sha": "b", "files": ["x.py"], "line_ranges": {"x.py": [[1, 2]]}}, {"claude": Reviewer(), "codex": Reviewer()}, Critique(), Synthesizer(), requested_rounds=1)
            run_dir = pathlib.Path(result["run_dir"])
            synthesis = json.loads((run_dir / "synthesis.json").read_text())
            report = (run_dir / "report.md").read_text()
            sidecar = json.loads((run_dir / "provenance.json").read_text())
        self.assertNotEqual(result["termination_reason"], "reviewer_failure")
        self.assertIsNotNone(sidecar["synthesis_status"])
        self.assertEqual(sidecar["synthesis_status"]["status"], "ok")
        self.assertEqual(sorted(item["classification"] for item in synthesis), ["단일 출처", "불일치"])
        disagreement = [item for item in synthesis if item["classification"] == "불일치"][0]
        self.assertEqual(len(disagreement["group_a_finding_ids"]) + len(disagreement["group_b_finding_ids"]), 1)
        self.assertIn("## 두 리뷰어가 갈린 지점", report)
        self.assertIn("반증됨", report)


if __name__ == "__main__":
    unittest.main()
