import json
import subprocess
import tempfile
import unittest


SCRIPT = (
    "dot_codex/skills/analyzing-open-source-pr-patterns/scripts/validate_corpus.py"
)


def resolved_record(pr_id="PR-001", node_id="node-001", source_key="source-a"):
    return {
        "identity_status": "resolved",
        "record_key": "github-pr:" + node_id,
        "pr_id": pr_id,
        "pull_request_node_id": node_id,
        "repository": {"node_id": "repo-001"},
        "pull_request": {"url": "https://github.com/example/repo/pull/1"},
        "sources": [{"source_key": source_key, "observations": [{"value": "first"}]}],
        "state_history": [{"state": "open"}],
        "analysis_history": [{"analysis": "initial"}],
    }


def unresolved_record(url="https://github.com/example/repo/pull/2"):
    return {
        "identity_status": "unresolved",
        "record_key": None,
        "pr_id": None,
        "pull_request_node_id": None,
        "repository": {"node_id": None},
        "pull_request": {"url": url},
        "sources": [{"source_key": "source-a", "observations": [{"value": "first"}]}],
        "state_history": [{"state": "unknown"}],
    }


def corpus(records, schema_version="1.0.0"):
    return {"schema_version": schema_version, "records": records}


class ValidateCorpusTests(unittest.TestCase):
    def run_validator(self, current, existing=None):
        with tempfile.TemporaryDirectory() as directory:
            current_path = directory + "/current.json"
            with open(current_path, "w") as stream:
                json.dump(current, stream)
            command = ["python3", SCRIPT, current_path]
            if existing is not None:
                existing_path = directory + "/existing.json"
                with open(existing_path, "w") as stream:
                    json.dump(existing, stream)
                command.extend(["--existing", existing_path])
            return subprocess.run(command, capture_output=True, text=True)

    def test_valid_resolved_and_unresolved_corpus_exits_zero(self):
        result = self.run_validator(
            corpus([resolved_record(), unresolved_record()])
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_unsupported_schema_version_exits_one(self):
        result = self.run_validator(corpus([resolved_record()], schema_version="2.0.0"))

        self.assertEqual(result.returncode, 1)
        self.assertIn("unsupported schema_version", result.stderr)

    def test_unresolved_record_cannot_have_pr_id(self):
        record = unresolved_record()
        record["pr_id"] = "PR-001"

        result = self.run_validator(corpus([record]))

        self.assertEqual(result.returncode, 1)
        self.assertIn("unresolved record", result.stderr)
        self.assertIn("pr_id", result.stderr)

    def test_duplicate_node_ids_pr_ids_and_source_keys_are_rejected(self):
        cases = [
            (
                [resolved_record(), resolved_record(pr_id="PR-002")],
                "duplicate pull_request_node_id",
            ),
            (
                [resolved_record(), resolved_record(node_id="node-002")],
                "duplicate pr_id",
            ),
            (
                [
                    dict(
                        resolved_record(),
                        sources=[
                            {"source_key": "source-a", "observations": []},
                            {"source_key": "source-a", "observations": []},
                        ],
                    )
                ],
                "duplicate source_key",
            ),
        ]
        for records, message in cases:
            with self.subTest(message=message):
                result = self.run_validator(corpus(records))
                self.assertEqual(result.returncode, 1)
                self.assertIn(message, result.stderr)

    def test_existing_rejects_changed_pr_ids(self):
        previous = corpus([resolved_record(pr_id="PR-001")])
        current = corpus([resolved_record(pr_id="PR-999")])

        result = self.run_validator(current, previous)

        self.assertEqual(result.returncode, 1)
        self.assertIn("pr_id", result.stderr)

    def test_existing_resolved_record_cannot_acquire_pr_id(self):
        previous = corpus([resolved_record(pr_id=None)])
        current = corpus([resolved_record(pr_id="PR-001")])

        result = self.run_validator(current, previous)

        self.assertEqual(result.returncode, 1)
        self.assertIn("pr_id", result.stderr)

    def test_existing_unresolved_record_may_become_resolved(self):
        previous_record = unresolved_record()
        current_record = resolved_record(pr_id="PR-001", node_id="node-002")
        current_record["pull_request"]["url"] = previous_record["pull_request"]["url"]
        current_record["state_history"] = [
            {"state": "unknown"},
            {"state": "open"},
        ]

        result = self.run_validator(
            corpus([current_record]), corpus([previous_record])
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_existing_rejects_removed_records(self):
        previous = corpus([resolved_record(), unresolved_record()])
        current = corpus([resolved_record()])

        result = self.run_validator(current, previous)

        self.assertEqual(result.returncode, 1)
        self.assertIn("removed", result.stderr)

    def test_existing_rejects_truncated_state_history(self):
        previous_record = resolved_record()
        previous_record["state_history"].append({"state": "merged"})
        current_record = resolved_record()

        result = self.run_validator(
            corpus([current_record]), corpus([previous_record])
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("state_history", result.stderr)
        self.assertIn("prefix", result.stderr)

    def test_existing_rejects_truncated_source_observations(self):
        previous_record = resolved_record()
        previous_record["sources"][0]["observations"].append({"value": "second"})
        current_record = resolved_record()

        result = self.run_validator(
            corpus([current_record]), corpus([previous_record])
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("observations", result.stderr)
        self.assertIn("prefix", result.stderr)

    def test_existing_rejects_truncated_analysis_history(self):
        previous_record = resolved_record()
        previous_record["analysis_history"].append({"analysis": "follow-up"})
        current_record = resolved_record()

        result = self.run_validator(
            corpus([current_record]), corpus([previous_record])
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("analysis_history", result.stderr)
        self.assertIn("prefix", result.stderr)


if __name__ == "__main__":
    unittest.main()
