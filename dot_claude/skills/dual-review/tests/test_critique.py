import pathlib
import sys
import unittest


sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import review_state


class CritiqueTests(unittest.TestCase):
    def test_unverifiable_refutation_is_downgraded(self):
        record, new_findings = review_state.validate_and_record_critique(
            {"finding_id": "fid_x", "verdict": "반증됨", "evidence": [{"file": "other.py", "line_start": 1}], "new_findings": []},
            {"changed.py"}, 1, "codex", "A", {},
        )
        self.assertEqual(record["verdict"], "미검증")
        self.assertEqual(new_findings, [])

    def test_path_traversal_noninteger_and_diff_outside_evidence_are_downgraded(self):
        for evidence in (
            [{"file": "../changed.py", "line_start": 1, "line_end": 1}],
            [{"file": "changed.py", "line_start": "1", "line_end": 1}],
            [{"file": "changed.py", "line_start": 4, "line_end": 5}],
        ):
            record, _ = review_state.validate_and_record_critique({"finding_id": "fid", "verdict": "반증됨", "evidence": evidence, "new_findings": []}, {"changed.py"}, 1, "codex", "A", {}, {"changed.py": [[1, 3]]})
            self.assertEqual(record["verdict"], "미검증")

    def test_invalid_evidence_downgrades_every_verdict(self):
        for verdict in ("유지", "반증됨", "미검증"):
            record, _ = review_state.validate_and_record_critique(
                {"finding_id": "fid", "verdict": verdict, "evidence": [{"file": "../x.py", "line_start": 1, "line_end": 1}], "new_findings": []},
                {"changed.py"}, 1, "codex", "A", {}, {"changed.py": [[1, 2]]},
            )
            self.assertEqual(record["verdict"], "미검증")

    def test_new_findings_keep_round_and_reviewer_provenance(self):
        sidecar = {}
        record, new_findings = review_state.validate_and_record_critique(
            {"finding_id": "fid_x", "verdict": "유지", "evidence": [{"file": "changed.py", "line_start": 2}], "new_findings": [{"severity": "high", "confidence": 90, "file": "changed.py", "line_start": 2, "line_end": 2, "title": "new", "body": "detail", "recommendation": "fix"}]},
            {"changed.py"}, 2, "claude", "B", sidecar,
        )
        self.assertEqual(record["round"], 2)
        self.assertEqual(new_findings[0]["source"], "claude")
        self.assertEqual(new_findings[0]["producer"], "cross-critique:claude")
        self.assertEqual(sidecar["new_findings"][new_findings[0]["finding_id"]], [{"round": 2, "reviewer": "claude", "original_id": new_findings[0]["original_id"]}])

    def test_repeated_new_finding_preserves_all_provenance_occurrences(self):
        sidecar = {}
        payload = {"finding_id": "fid_x", "verdict": "유지", "evidence": [{"file": "changed.py", "line_start": 2, "line_end": 2}], "new_findings": [{"severity": "high", "confidence": 90, "file": "changed.py", "line_start": 2, "line_end": 2, "title": "new", "body": "detail", "recommendation": "fix"}]}
        first_record, first = review_state.validate_and_record_critique(payload, {"changed.py"}, 1, "claude", "A", sidecar, {"changed.py": [[1, 2]]})
        second_record, second = review_state.validate_and_record_critique(payload, {"changed.py"}, 2, "claude", "A", sidecar, {"changed.py": [[1, 2]]})
        self.assertEqual(first_record["round"], 1)
        self.assertEqual(second_record["round"], 2)
        self.assertEqual(first[0]["finding_id"], second[0]["finding_id"])
        self.assertEqual(sidecar["new_findings"][first[0]["finding_id"]], [
            {"round": 1, "reviewer": "claude", "original_id": first[0]["original_id"]},
            {"round": 2, "reviewer": "claude", "original_id": second[0]["original_id"]},
        ])

    def test_new_findings_reject_invalid_raw_file_and_boolean_numeric_fields(self):
        valid = {"severity": "high", "confidence": 90, "file": "changed.py", "line_start": 2, "line_end": 2, "title": "new", "body": "detail", "recommendation": "fix"}
        invalid_records = [
            {**valid, "file": None},
            {**valid, "file": 7},
            {**valid, "confidence": True},
            {**valid, "line_start": True},
            {**valid, "line_end": True},
        ]
        for raw in invalid_records:
            with self.subTest(raw=raw):
                sidecar = {}
                _, new_findings = review_state.validate_and_record_critique(
                    {"finding_id": "fid_x", "verdict": "유지", "evidence": [{"file": "changed.py", "line_start": 2, "line_end": 2}], "new_findings": [raw]},
                    {"changed.py"}, 1, "claude", "A", sidecar, {"changed.py": [[1, 2]]},
                )
                self.assertEqual(new_findings, [])
                self.assertEqual(len(sidecar["rejected_findings"]), 1)

    def test_critique_manifest_rejects_missing_duplicate_and_unknown_ids(self):
        response = {"status": "ok", "payload": {"critiques": [{"finding_id": "fid_a"}, {"finding_id": "fid_b"}]}}
        self.assertEqual([item["finding_id"] for item in review_state._critique_payloads(response, ["fid_a", "fid_b"])], ["fid_a", "fid_b"])
        for identifiers in (["fid_a"], ["fid_a", "fid_a"], ["fid_a", "fid_unknown"]):
            with self.assertRaises(ValueError):
                review_state._critique_payloads({"status": "ok", "payload": {"critiques": [{"finding_id": value} for value in identifiers]}}, ["fid_a", "fid_b"])


if __name__ == "__main__":
    unittest.main()
