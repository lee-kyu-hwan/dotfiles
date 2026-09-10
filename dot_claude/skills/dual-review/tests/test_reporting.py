import json
import pathlib
import sys
import tempfile
import unittest


sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import review_state


class ReportingTests(unittest.TestCase):
    def test_full_report_restores_provenance_and_is_order_invariant(self):
        state = {
            "target": {"base_sha": "base", "head_sha": "head", "files": ["a.py"]},
            "termination_reason": "round_cap",
            "reviewers": {"claude": {"status": "valid"}, "codex": {"status": "valid"}},
            "findings": [{"finding_id": "fid_b", "title": "B", "body": "body B"}, {"finding_id": "fid_a", "title": "A", "body": "body A"}],
            "critiques": [{"finding_id": "fid_a", "verdict": "유지", "evidence": [{"file": "a.py", "line_start": 1, "line_end": 1}]}],
            "synthesis": [{"classification": "불일치", "rationale": "conflict", "group_a_finding_ids": ["fid_a"], "group_b_finding_ids": ["fid_b"], "claims": {"A": "claim A", "B": "claim B"}}],
        }
        with tempfile.TemporaryDirectory() as temporary_directory:
            sidecar = pathlib.Path(temporary_directory) / "provenance.json"
            sidecar.write_text(json.dumps({
                "source_groups": {"claude": "A", "codex": "B"},
                "masks": [],
                "findings": {"fid_a": {"source": "claude"}, "fid_b": {"source": "codex"}}}))
            report = review_state.render_report(state, sidecar)
            reordered = dict(state, findings=list(reversed(state["findings"])))
            self.assertEqual(report, review_state.render_report(reordered, sidecar))
        for section in ("## Target", "## Termination reason", "## Reviewer status", "## Findings", "## Critiques", "## Synthesis", "## 두 리뷰어가 갈린 지점"):
            self.assertIn(section, report)
        self.assertIn("claude", report)
        self.assertIn("fid_a", report)
        self.assertIn("claim A", report)
        self.assertIn("a.py:1-1", report)
        self.assertIn("claude=fid_a", report)
        self.assertIn("codex=fid_b", report)
        self.assertNotIn("A=", report)
        self.assertNotIn("B=", report)

    def test_render_refuses_a_group_label_it_cannot_restore(self):
        """A bare A=/B= in the deliverable is an anonymization leak, so the render must stop."""
        state = {
            "target": {"base_sha": "base", "head_sha": "head", "files": ["a.py"]},
            "termination_reason": "round_cap",
            "reviewers": {"claude": {"status": "valid"}, "codex": {"status": "valid"}},
            "findings": [{"finding_id": "fid_a", "title": "A", "body": "body A"}],
            "critiques": [],
            "synthesis": [{"classification": "단일 출처", "rationale": "only one side",
                           "group_a_finding_ids": ["fid_a"], "group_b_finding_ids": [],
                           "claims": {"A": "claim A", "B": ""}}],
            "provenance": {"source_groups": {"claude": "A"}, "masks": [],
                           "findings": {"fid_a": {"source": "claude"}}},
        }
        with self.assertRaises(ValueError):
            review_state.render_report(state)

    def test_group_labels_the_synthesizer_quoted_back_are_relabelled(self):
        """The synthesizer only ever saw A/B, so it may write those labels into free text."""
        state = {
            "target": {"base_sha": "base", "head_sha": "head", "files": ["a.py"]},
            "termination_reason": "round_cap",
            "reviewers": {"claude": {"status": "valid"}, "codex": {"status": "valid"}},
            "findings": [{"finding_id": "fid_a", "title": "A", "body": "body A"},
                         {"finding_id": "fid_b", "title": "B", "body": "body B"}],
            "critiques": [{"finding_id": "fid_a", "verdict": "유지",
                           "evidence": [{"file": "a.py", "line_start": 1, "line_end": 1}]}],
            "synthesis": [{"classification": "불일치", "rationale": "A=holds while B=denies",
                           "group_a_finding_ids": ["fid_a"], "group_b_finding_ids": ["fid_b"],
                           "claims": {"A": "A=stands", "B": "B=refutes"}}],
            "provenance": {"source_groups": {"claude": "A", "codex": "B"}, "masks": [],
                           "findings": {"fid_a": {"source": "claude"}, "fid_b": {"source": "codex"}}},
        }
        report = review_state.render_report(state)
        self.assertIn("claude=holds while codex=denies", report)
        self.assertIn("claude=stands", report)
        self.assertIn("codex=refutes", report)
        for line in report.splitlines():
            self.assertNotRegex(line, r"(?<![0-9A-Za-z_])[AB]=")

    def test_report_surfaces_findings_that_normalization_rejected(self):
        """A dropped finding must be visible in the deliverable, not only inside provenance.json."""
        state = {
            "target": {"base_sha": "base", "head_sha": "head", "files": ["a.py"]},
            "termination_reason": "round_cap",
            "reviewers": {"claude": {"status": "valid"}},
            "findings": [], "critiques": [], "synthesis": [],
            "provenance": {"source_groups": {"claude": "A"}, "masks": [], "findings": {},
                           "rejected_findings": [{"original_id": "producer=comment-analyzer;ordinal=4",
                                                  "reason": "invalid finding fields",
                                                  "raw": {"severity": "Minor", "title": "dropped one"}}]},
        }
        report = review_state.render_report(state)
        self.assertIn("## 버려진 finding", report)
        self.assertIn("producer=comment-analyzer;ordinal=4", report)
        self.assertIn("invalid finding fields", report)


if __name__ == "__main__":
    unittest.main()
