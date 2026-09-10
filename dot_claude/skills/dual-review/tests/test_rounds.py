import pathlib
import sys
import unittest


sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import review_state


class RoundTests(unittest.TestCase):
    def test_round_two_requires_requested_limit_and_new_high(self):
        self.assertEqual(review_state.advance_critique_rounds(True, True, 2, [1]), [1, 2])
        self.assertEqual(review_state.advance_critique_rounds(True, True, 2, [0]), [1])
        self.assertEqual(review_state.advance_critique_rounds(True, True, 1, [1]), [1])
        self.assertEqual(review_state.advance_critique_rounds(True, False, 2, [1]), [])

    def test_termination_priority_and_drift_boundary(self):
        self.assertEqual(review_state.select_termination_reason({"round_cap", "single_reviewer", "no_new_high"}), "single_reviewer")
        self.assertFalse(review_state.is_abstraction_drift(["changed.py", "other.py"], {"changed.py"}))
        self.assertTrue(review_state.is_abstraction_drift(["changed.py", "other.py", "third.py"], {"changed.py"}))
        self.assertFalse(review_state.is_abstraction_drift([], {"changed.py"}))

    def test_every_overlapping_termination_pair_uses_the_specification_order(self):
        canonical = list(review_state.TERMINATION_REASONS)
        for left_index, left in enumerate(canonical):
            for right in canonical[left_index + 1:]:
                self.assertEqual(review_state.select_termination_reason({left, right}), left)

    def test_actual_round_two_is_started_only_after_round_one_adds_high_finding(self):
        class Adapter:
            def start(self, source, prompt): return (source, prompt)
            def read(self, handle):
                return {"status": "ok", "payload": {"verdict": "ok", "summary": "", "next_steps": [], "findings": [{"severity": "low", "finding_confidence": .8, "file": "x.py", "line_start": 1, "line_end": 1, "title": handle[0], "body": "detail", "recommendation": "fix"}]}}
        prompts = []
        class Critique:
            def start(self, source, prompt): prompts.append(prompt); return prompt
            def read(self, prompt):
                return {"status": "ok", "payload": {"critiques": [
                    {"finding_id": item["finding_id"], "verdict": "유지", "evidence": [{"file": "x.py", "line_start": 1, "line_end": 1}], "new_findings": [{"severity": "high", "finding_confidence": .8, "file": "x.py", "line_start": 1, "line_end": 1, "title": "new", "body": "detail", "recommendation": "fix"}]}
                    for item in __import__("json").loads(prompt)["opposing_findings"]
                ]}}
        import pathlib
        import tempfile
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = review_state.run_dual_review(pathlib.Path(temporary_directory), {"base_sha": "a", "head_sha": "b", "files": ["x.py"], "line_ranges": {"x.py": [[1, 2]]}}, {"claude": Adapter(), "codex": Adapter()}, critique_adapter=Critique(), requested_rounds=2)
        self.assertEqual(result["termination_reason"], "round_cap")
        self.assertEqual({__import__("json").loads(prompt)["round"] for prompt in prompts}, {1, 2})

    def test_no_new_high_is_not_hidden_by_requested_round_limit(self):
        class Reviewer:
            def start(self, source, prompt): return source
            def read(self, source): return {"status": "ok", "payload": {"verdict": "ok", "summary": "", "next_steps": [], "findings": [{"severity": "high", "finding_confidence": .8, "file": "x.py", "line_start": 1, "line_end": 1, "title": source, "body": "detail", "recommendation": "fix"}]}}
        class Critique:
            def start(self, source, prompt): return prompt
            def read(self, prompt): return {"status": "ok", "payload": {"critiques": [{"finding_id": item["finding_id"], "verdict": "유지", "evidence": [{"file": "x.py", "line_start": 1, "line_end": 1}], "new_findings": []} for item in __import__("json").loads(prompt)["opposing_findings"]]}}
        import tempfile
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = review_state.run_dual_review(pathlib.Path(temporary_directory), {"base_sha": "a", "head_sha": "b", "files": ["x.py"], "line_ranges": {"x.py": [[1, 1]]}}, {"claude": Reviewer(), "codex": Reviewer()}, critique_adapter=Critique(), requested_rounds=2)
        self.assertEqual(result["termination_reason"], "no_new_high")

    def test_requested_round_one_never_dispatches_round_two_after_new_high(self):
        result, rounds = self._run_round_fixture("in-scope-high", 1)
        self.assertEqual(result["termination_reason"], "requested_round_limit")
        self.assertEqual(rounds, [1, 1])

    def test_round_two_drift_aborts_and_is_reported(self):
        result, rounds = self._run_round_fixture("out-of-scope", 2)
        self.assertEqual(result["termination_reason"], "abstraction_drift")
        self.assertEqual(rounds, [1, 1, 2, 2])

    def test_round_two_exactly_half_out_of_scope_is_not_drift(self):
        result, rounds = self._run_round_fixture("half-out-of-scope", 2)
        self.assertEqual(result["termination_reason"], "round_cap")
        self.assertEqual(rounds, [1, 1, 2, 2])

    def _run_round_fixture(self, behavior, requested_rounds):
        import json
        import tempfile
        class Reviewer:
            def start(self, source, prompt): return source
            def read(self, source):
                return {"status": "ok", "payload": {"verdict": "ok", "summary": "", "next_steps": [], "findings": [{"severity": "low", "finding_confidence": .8, "file": "x.py", "line_start": 1, "line_end": 1, "title": source, "body": "detail", "recommendation": "fix"}]}}
        rounds = []
        class Critique:
            def start(self, source, prompt): return prompt
            def read(self, prompt):
                payload = json.loads(prompt); round_number = payload["round"]; rounds.append(round_number)
                findings = []
                for index, item in enumerate(payload["opposing_findings"]):
                    if round_number == 1:
                        count = 3 if behavior == "out-of-scope" else 1
                        findings.extend({"severity": "high", "finding_confidence": .8, "file": "x.py", "line_start": 1, "line_end": 1, "title": f"high-{index}-{ordinal}", "body": "detail", "recommendation": "fix"} for ordinal in range(count))
                    elif behavior == "out-of-scope":
                        findings = [{"severity": "low", "finding_confidence": .8, "file": "other.py", "line_start": 1, "line_end": 1, "title": "outside", "body": "detail", "recommendation": "fix"}]
                    elif behavior == "half-out-of-scope":
                        findings = [
                            {"severity": "low", "finding_confidence": .8, "file": "x.py", "line_start": 1, "line_end": 1, "title": "inside", "body": "detail", "recommendation": "fix"},
                            {"severity": "low", "finding_confidence": .8, "file": "other.py", "line_start": 1, "line_end": 1, "title": "outside", "body": "detail", "recommendation": "fix"},
                        ]
                return {"status": "ok", "payload": {"critiques": [{"finding_id": item["finding_id"], "verdict": "유지", "evidence": [{"file": "x.py", "line_start": 1, "line_end": 1}], "new_findings": findings if index == 0 else []} for index, item in enumerate(payload["opposing_findings"])]}}
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = review_state.run_dual_review(pathlib.Path(temporary_directory), {"base_sha": "a", "head_sha": "b", "files": ["x.py"], "line_ranges": {"x.py": [[1, 1]]}}, {"claude": Reviewer(), "codex": Reviewer()}, critique_adapter=Critique(), requested_rounds=requested_rounds)
        return result, rounds


if __name__ == "__main__":
    unittest.main()
