import copy
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "validate_corpus.py"
QUOTE = "The schema constant and its union type drifted apart"
BODY = "<!-- template -->\r\n" + QUOTE + ", so keep both lists<!-- note -->\n  synchronized."
LEDGER = "pattern-extraction: fixture ledger"


def resolved_record(pr_id="PR-001", node_id="node-001", source_key="source-a"):
    return {
        "identity_status": "resolved",
        "record_key": "github-pr:" + node_id,
        "pr_id": pr_id,
        "pull_request_node_id": node_id,
        "repository": {"node_id": "repo-001"},
        "pull_request": {
            "url": "https://github.com/example/repo/pull/1",
            "title": "Keep derived values synchronized",
        },
        "evidence_snapshot": {"body_excerpt": BODY},
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


def two_records():
    return [resolved_record(), resolved_record(pr_id="PR-002", node_id="node-002")]


def corpus(records, schema_version="1.0.0"):
    return {
        "schema_version": schema_version,
        "generated_by": {"name": "fixture-collector", "revision": "fixture-v1"},
        "records": records,
    }


def evidence_claim(value="Observed change", basis="fact"):
    return {
        "value": value,
        "basis": basis,
        "evidence_links": ["https://example.invalid/evidence"],
    }


def confidence(level="medium"):
    return {
        "level": level,
        "evidence": ["Selected local evidence"],
        "limitations": ["Full upstream payload is unavailable"],
    }


def analysis_projection(pattern_ids=None):
    return {
        "change_summary": evidence_claim(),
        "motivation": evidence_claim("Stated motivation"),
        "review_judgment": evidence_claim("Accepted", "inference"),
        "closure_reason": evidence_claim("merged"),
        "files_changed": ["src/example.js"],
        "test_evidence": [evidence_claim("Unit test added")],
        "pattern_ids": pattern_ids if pattern_ids is not None else [],
        "evidence_links": ["https://example.invalid/evidence"],
        "evidence_manifest": {"files": {"pages_complete": True}},
        "license_spdx": "MIT",
        "provenance_mode": "independent-reimplementation",
        "confidence": confidence(),
        "superseded_by": None,
    }


def pattern_projection(revision, pattern_id="PAT-001", pr_ids=("PR-001", "PR-002")):
    return {
        "pattern_id": pattern_id,
        "description": "Keep derived values synchronized",
        "generated_by": {
            "name": "analyzing-open-source-pr-patterns",
            "revision": revision,
        },
        "evidence_pr_ids": list(pr_ids),
        "applicability": ["A constant and its type describe the same values"],
        "counterconditions": ["The values are intentionally independent"],
        "search_clues": ["duplicated union and array literals"],
        "expected_tests": ["schema and type values remain aligned"],
        "maintainer_judgment_required": ["public API compatibility"],
        "source_licenses": [{"pr_id": pr_id, "spdx_id": "MIT"} for pr_id in pr_ids],
        "provenance_mode": "independent-reimplementation",
        "confidence": {
            "level": "medium",
            "evidence": [pr_id + ' "' + QUOTE + '"' for pr_id in pr_ids]
            + ["Selected local evidence"],
            "limitations": ["Full upstream payload is unavailable"],
        },
        "superseded_by": None,
    }


def analysis_output(input_corpus, revision, existing=None, pattern_id="PAT-001"):
    """Build a valid output; it carries one pattern when two resolved records exist."""
    records = []
    existing_records = {}
    if existing is not None:
        for record in existing.get("records", []):
            identity = record.get("pull_request_node_id") or record["pull_request"]["url"]
            existing_records[identity] = record

    evidence = [
        record["pr_id"]
        for record in input_corpus["records"]
        if record.get("identity_status") == "resolved" and record.get("pr_id")
    ]
    with_pattern = len(evidence) >= 2
    for input_record in input_corpus["records"]:
        record = copy.deepcopy(input_record)
        cited = with_pattern and record.get("pr_id") in evidence
        projection = analysis_projection([pattern_id] if cited else [])
        identity = record.get("pull_request_node_id") or record["pull_request"]["url"]
        old_record = existing_records.get(identity)
        if old_record is not None:
            history = copy.deepcopy(old_record["analysis_history"])
        else:
            history = copy.deepcopy(record.get("analysis_history", []))
        snapshot = {
            "revision": revision,
            "generated_at": "2026-09-04T12:00:00Z",
            "evidence_manifest": copy.deepcopy(projection["evidence_manifest"]),
            "conclusion": copy.deepcopy(projection),
        }
        record["analysis"] = projection
        record["analysis_history"] = history + [snapshot]
        records.append(record)

    pattern = pattern_projection(revision, pattern_id, tuple(evidence))
    old_patterns = [] if existing is None else existing.get("patterns", [])
    old_pattern = next(
        (item for item in old_patterns if item.get("pattern_id") == pattern_id),
        None,
    )
    pattern_history = (
        copy.deepcopy(old_pattern["pattern_history"])
        if old_pattern is not None
        else []
    )
    pattern["pattern_history"] = pattern_history + [
        {
            "revision": revision,
            "generated_at": "2026-09-04T12:00:00Z",
            "conclusion": copy.deepcopy(pattern),
        }
    ]
    return {
        "schema_version": "1.0.0",
        "generated_by": copy.deepcopy(input_corpus["generated_by"]),
        "analysis_generated_by": {
            "name": "analyzing-open-source-pr-patterns",
            "revision": revision,
        },
        "records": records,
        "patterns": [pattern] if with_pattern else [],
        "limitations": ["Selected evidence only", LEDGER],
    }


class ValidateCorpusTests(unittest.TestCase):
    def run_paths(self, current_path=None, *arguments):
        command = ["python3", str(SCRIPT)]
        if current_path is not None:
            command.append(str(current_path))
        command.extend(str(argument) for argument in arguments)
        return subprocess.run(command, capture_output=True, text=True)

    def run_validator(self, current, existing=None):
        with tempfile.TemporaryDirectory() as directory:
            current_path = Path(directory) / "current.json"
            with current_path.open("w", encoding="utf-8") as stream:
                json.dump(current, stream)
            command = ["python3", str(SCRIPT), str(current_path)]
            if existing is not None:
                existing_path = Path(directory) / "existing.json"
                with existing_path.open("w", encoding="utf-8") as stream:
                    json.dump(existing, stream)
                command.extend(["--existing", str(existing_path)])
            return subprocess.run(command, capture_output=True, text=True)

    def run_analysis_validator(self, current, output, existing_analysis=None):
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            current_path = directory_path / "current.json"
            output_path = directory_path / "output.json"
            current_path.write_text(json.dumps(current), encoding="utf-8")
            output_path.write_text(json.dumps(output), encoding="utf-8")
            command = [
                "python3",
                str(SCRIPT),
                str(current_path),
                "--analysis-output",
                str(output_path),
            ]
            if existing_analysis is not None:
                existing_path = directory_path / "existing-analysis.json"
                existing_path.write_text(
                    json.dumps(existing_analysis), encoding="utf-8"
                )
                command.extend(["--existing-analysis", str(existing_path)])
            return subprocess.run(command, capture_output=True, text=True)

    def current_revision(self):
        result = self.run_paths(None, "--print-revision")
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

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

    def test_existing_rejects_source_metadata_rewrite(self):
        previous_record = resolved_record()
        previous_record["sources"][0]["kind"] = "tracker-comments"
        previous_record["sources"][0]["run_key"] = "run-1"
        current_record = copy.deepcopy(previous_record)
        current_record["sources"][0]["kind"] = "search-api"

        result = self.run_validator(
            corpus([current_record]), corpus([previous_record])
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("source metadata changed", result.stderr)

    def test_existing_rejects_source_metadata_number_changed_to_boolean(self):
        previous_record = resolved_record()
        previous_record["sources"][0]["page_count"] = 1
        current_record = copy.deepcopy(previous_record)
        current_record["sources"][0]["page_count"] = True

        result = self.run_validator(
            corpus([current_record]), corpus([previous_record])
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("source metadata changed", result.stderr)

    def test_existing_rejects_source_reorder(self):
        previous_record = resolved_record()
        previous_record["sources"].append(
            {"source_key": "source-b", "observations": [{"value": "first"}]}
        )
        current_record = copy.deepcopy(previous_record)
        current_record["sources"].reverse()

        result = self.run_validator(
            corpus([current_record]), corpus([previous_record])
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("source_key order is not an exact prefix", result.stderr)

    def test_existing_rejects_source_inserted_before_existing_sources(self):
        previous_record = resolved_record()
        current_record = copy.deepcopy(previous_record)
        current_record["sources"].insert(
            0,
            {"source_key": "source-new", "observations": [{"value": "new"}]},
        )

        result = self.run_validator(
            corpus([current_record]), corpus([previous_record])
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("source_key order is not an exact prefix", result.stderr)

    def test_malformed_utf8_is_a_concise_json_read_error(self):
        with tempfile.TemporaryDirectory() as directory:
            current_path = Path(directory) / "invalid.json"
            current_path.write_bytes(b'{"schema_version":"1.0.0","records":[]\xff}')

            result = self.run_paths(current_path)

        self.assertEqual(result.returncode, 1)
        self.assertIn("could not be read as JSON", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_revision_is_stable_shaped_and_sensitive_to_skill_content(self):
        first = self.current_revision()
        second = self.current_revision()
        self.assertRegex(first, r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(first, second)

        with tempfile.TemporaryDirectory() as directory:
            copied_skill = Path(directory) / "analyzing-open-source-pr-patterns"
            shutil.copytree(SKILL_DIR, copied_skill)
            copied_script = copied_skill / "scripts" / "validate_corpus.py"
            copied_command = ["python3", str(copied_script), "--print-revision"]
            copied_before = subprocess.run(
                copied_command, capture_output=True, text=True
            )
            self.assertEqual(copied_before.returncode, 0, copied_before.stderr)
            self.assertEqual(copied_before.stdout.strip(), first)

            skill_path = copied_skill / "SKILL.md"
            skill_path.write_text(
                skill_path.read_text(encoding="utf-8") + "\nRevision sensitivity.\n",
                encoding="utf-8",
            )
            copied_after = subprocess.run(
                copied_command, capture_output=True, text=True
            )

        self.assertEqual(copied_after.returncode, 0, copied_after.stderr)
        self.assertRegex(copied_after.stdout.strip(), r"^sha256:[0-9a-f]{64}$")
        self.assertNotEqual(copied_after.stdout.strip(), first)

    def test_valid_strict_analysis_output_exits_zero(self):
        current = corpus(two_records() + [unresolved_record()])
        output = analysis_output(current, self.current_revision())

        result = self.run_analysis_validator(current, output)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Validated analysis output", result.stdout)

    def test_analysis_output_rejects_wrong_repository_and_license_field_types(self):
        current = corpus(two_records())
        revision = self.current_revision()
        cases = []

        wrong_repository = analysis_output(current, revision)
        wrong_repository["records"][0]["repository"] = "example/repo"
        cases.append((wrong_repository, "normalized field repository changed"))

        wrong_source_licenses = analysis_output(current, revision)
        wrong_source_licenses["patterns"][0]["source_licenses"] = ["MIT"]
        cases.append((wrong_source_licenses, "source_licenses[0] must be an object"))

        for output, message in cases:
            with self.subTest(message=message):
                result = self.run_analysis_validator(current, output)
                self.assertEqual(result.returncode, 1)
                self.assertIn(message, result.stderr)

    def test_analysis_output_rejects_normalized_number_changed_to_boolean(self):
        record = resolved_record()
        record["repository"]["numeric_marker"] = 1
        current = corpus([record])
        output = analysis_output(current, self.current_revision())
        output["records"][0]["repository"]["numeric_marker"] = True

        result = self.run_analysis_validator(current, output)

        self.assertEqual(result.returncode, 1)
        self.assertIn("normalized field repository changed", result.stderr)

    def test_analysis_output_rejects_copied_metadata_number_changed_to_boolean(self):
        current = corpus([resolved_record()])
        current["generated_by"]["numeric_marker"] = 1
        output = analysis_output(current, self.current_revision())
        output["generated_by"]["numeric_marker"] = True

        result = self.run_analysis_validator(current, output)

        self.assertEqual(result.returncode, 1)
        self.assertIn("generated_by must exactly copy", result.stderr)

    def test_analysis_output_rejects_missing_or_mismatched_current_snapshot(self):
        current = corpus([resolved_record()])
        revision = self.current_revision()
        cases = []

        missing_snapshot = analysis_output(current, revision)
        missing_snapshot["records"][0]["analysis_history"].pop()
        cases.append((missing_snapshot, "must append exactly one current snapshot"))

        mismatched_snapshot = analysis_output(current, revision)
        mismatched_snapshot["records"][0]["analysis_history"][-1]["conclusion"][
            "motivation"
        ]["value"] = "Different conclusion"
        cases.append((mismatched_snapshot, "conclusion must equal current analysis"))

        for output, message in cases:
            with self.subTest(message=message):
                result = self.run_analysis_validator(current, output)
                self.assertEqual(result.returncode, 1)
                self.assertIn(message, result.stderr)

    def test_analysis_output_rejects_snapshot_number_changed_to_boolean(self):
        current = corpus([resolved_record()])
        output = analysis_output(current, self.current_revision())
        output["records"][0]["analysis"]["evidence_manifest"] = {
            "files": {"numeric_marker": 1}
        }
        snapshot = output["records"][0]["analysis_history"][-1]
        snapshot["evidence_manifest"] = {"files": {"numeric_marker": True}}
        snapshot["conclusion"]["evidence_manifest"] = {
            "files": {"numeric_marker": True}
        }

        result = self.run_analysis_validator(current, output)

        self.assertEqual(result.returncode, 1)
        self.assertIn("evidence_manifest must equal current analysis", result.stderr)

    def test_analysis_output_preserves_existing_pattern_history_prefix(self):
        current = corpus(two_records())
        revision = self.current_revision()
        previous = analysis_output(current, revision)

        valid_next = analysis_output(current, revision, existing=previous)
        valid_result = self.run_analysis_validator(current, valid_next, previous)
        self.assertEqual(valid_result.returncode, 0, valid_result.stderr)

        cases = []
        missing_pattern = copy.deepcopy(valid_next)
        missing_pattern["patterns"] = []
        cases.append((missing_pattern, "existing pattern was removed"))

        rewritten_prefix = copy.deepcopy(valid_next)
        rewritten_prefix["patterns"][0]["pattern_history"][0]["revision"] = (
            "sha256:" + "0" * 64
        )
        cases.append((rewritten_prefix, "pattern_history is not an exact prefix"))

        for output, message in cases:
            with self.subTest(message=message):
                result = self.run_analysis_validator(current, output, previous)
                self.assertEqual(result.returncode, 1)
                self.assertIn(message, result.stderr)

    def test_analysis_output_preserves_legacy_pattern_history_item_exactly(self):
        current = corpus(two_records())
        revision = self.current_revision()
        legacy_item = {"revision": "old", "conclusion": "preserve me"}
        previous = {
            "schema_version": "1.0.0",
            "records": [
                {
                    "pattern_id": "PAT-009",
                    "description": "Existing pattern identity",
                    "pattern_history": [copy.deepcopy(legacy_item)],
                }
            ],
        }
        output = analysis_output(current, revision, pattern_id="PAT-009")
        pattern = pattern_projection(revision, pattern_id="PAT-009")
        pattern["pattern_history"] = [
            copy.deepcopy(legacy_item),
            {
                "revision": revision,
                "generated_at": "2026-09-04T12:00:00Z",
                "conclusion": copy.deepcopy(pattern),
            },
        ]
        output["patterns"] = [pattern]

        result = self.run_analysis_validator(current, output, previous)

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_analysis_output_preserves_existing_record_history_prefix(self):
        current = corpus([resolved_record()])
        revision = self.current_revision()
        previous = analysis_output(current, revision)
        output = analysis_output(current, revision, existing=previous)
        output["records"][0]["analysis_history"][0]["revision"] = (
            "sha256:" + "0" * 64
        )

        result = self.run_analysis_validator(current, output, previous)

        self.assertEqual(result.returncode, 1)
        self.assertIn("analysis_history is not an exact prefix", result.stderr)

    def test_existing_analysis_preserves_unresolved_history_when_identity_resolves(self):
        url = "https://github.com/example/repo/pull/7"
        revision = self.current_revision()
        previous_input = corpus([unresolved_record(url)])
        previous = analysis_output(previous_input, revision)

        current_record = resolved_record(pr_id="PR-007", node_id="node-007")
        current_record["pull_request"]["url"] = url
        current_record.pop("analysis_history")
        current = corpus([current_record])
        output = analysis_output(current, revision, existing=previous)
        current_snapshot = output["records"][0]["analysis_history"][-1]
        output["records"][0]["analysis_history"] = copy.deepcopy(
            previous["records"][0]["analysis_history"]
        ) + [current_snapshot]

        result = self.run_analysis_validator(current, output, previous)

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_existing_analysis_rejects_ambiguous_unresolved_to_resolved_match(self):
        url = "https://github.com/example/repo/pull/7"
        revision = self.current_revision()
        previous_input = corpus([unresolved_record(url)])
        previous = analysis_output(previous_input, revision)

        first = resolved_record(pr_id="PR-007", node_id="node-007")
        second = resolved_record(pr_id="PR-008", node_id="node-008")
        for record in (first, second):
            record["pull_request"]["url"] = url
            record.pop("analysis_history")
        current = corpus([first, second])
        output = analysis_output(current, revision, existing=previous)
        current_snapshot = output["records"][0]["analysis_history"][-1]
        output["records"][0]["analysis_history"] = copy.deepcopy(
            previous["records"][0]["analysis_history"]
        ) + [current_snapshot]

        result = self.run_analysis_validator(current, output, previous)

        self.assertEqual(result.returncode, 1)
        self.assertEqual(
            result.stderr,
            "existing analyzed record has ambiguous same-URL matches: URL "
            + url
            + "\n",
        )
        self.assertNotIn("Traceback", result.stderr)

    def test_analysis_output_rejects_history_number_changed_to_boolean(self):
        current = corpus([resolved_record()])
        revision = self.current_revision()
        previous = analysis_output(current, revision)
        previous["records"][0]["analysis_history"][-1]["numeric_marker"] = 1
        output = analysis_output(current, revision, existing=previous)
        output["records"][0]["analysis_history"][-2]["numeric_marker"] = True

        result = self.run_analysis_validator(current, output, previous)

        self.assertEqual(result.returncode, 1)
        self.assertIn("analysis_history is not an exact prefix", result.stderr)

    def test_output_without_extraction_ledger_is_rejected(self):
        # #183: a serialization script emitted patterns [] with no trace of extraction.
        current = corpus(two_records())
        revision = self.current_revision()
        cases = []

        missing = analysis_output(current, revision)
        missing["patterns"] = []
        for record in missing["records"]:
            record["analysis"]["pattern_ids"] = []
            record["analysis_history"][-1]["conclusion"]["pattern_ids"] = []
        missing["limitations"] = ["Selected evidence only"]
        cases.append(missing)

        duplicated = analysis_output(current, revision)
        duplicated["limitations"].append(LEDGER)
        cases.append(duplicated)

        empty = analysis_output(current, revision)
        empty["limitations"] = ["pattern-extraction:  "]
        cases.append(empty)

        for output in cases:
            with self.subTest(limitations=output["limitations"]):
                result = self.run_analysis_validator(current, output)
                self.assertEqual(result.returncode, 1)
                self.assertIn("exactly one nonempty 'pattern-extraction:' entry", result.stderr)

    def test_recorded_empty_extraction_is_valid(self):
        current = corpus([resolved_record()])
        output = analysis_output(current, self.current_revision())

        result = self.run_analysis_validator(current, output)

        self.assertEqual(output["patterns"], [])
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_current_pattern_needs_two_distinct_evidence_prs(self):
        current = corpus(two_records())
        output = analysis_output(current, self.current_revision())
        pattern = output["patterns"][0]
        pattern["evidence_pr_ids"] = ["PR-001", "PR-001"]
        pattern["confidence"]["evidence"] = ['PR-001 "' + QUOTE + '"']
        pattern["source_licenses"] = [{"pr_id": "PR-001", "spdx_id": "MIT"}]
        pattern["pattern_history"][-1]["conclusion"] = {
            key: value for key, value in pattern.items() if key != "pattern_history"
        }
        second = output["records"][1]
        second["analysis"]["pattern_ids"] = []
        second["analysis_history"][-1]["conclusion"]["pattern_ids"] = []

        result = self.run_analysis_validator(current, output)

        self.assertEqual(result.returncode, 1)
        self.assertIn("PAT-001 must cite at least two distinct evidence PRs", result.stderr)

    def test_pattern_quotes_must_be_verbatim_in_their_evidence_record(self):
        current = corpus(two_records())
        revision = self.current_revision()
        cases = [
            ('PR-002 "The schema constant ... drifted apart"', "quote is not verbatim in PR-002"),
            ('PR-002 "Keep derived values synchronized in the url: line"', "quote is not verbatim in PR-002"),
            ('PR-002 "keep both lists"', "quote must be 20-300 characters"),
            ('PR-003 "' + QUOTE + '"', "quotes PR-003 outside evidence_pr_ids"),
        ]
        for replacement, message in cases:
            with self.subTest(message=message):
                output = analysis_output(current, revision)
                pattern = output["patterns"][0]
                pattern["confidence"]["evidence"][1] = replacement
                pattern["pattern_history"][-1]["conclusion"]["confidence"] = copy.deepcopy(
                    pattern["confidence"]
                )
                result = self.run_analysis_validator(current, output)
                self.assertEqual(result.returncode, 1)
                self.assertIn(message, result.stderr)
                self.assertIn("evidence PR-002 has no verified verbatim quote", result.stderr)

    def test_pattern_quote_ignores_html_comments_and_whitespace_only(self):
        current = corpus(two_records())
        output = analysis_output(current, self.current_revision())
        pattern = output["patterns"][0]
        pattern["confidence"]["evidence"][1] = 'PR-002 "so keep both lists synchronized."'
        pattern["pattern_history"][-1]["conclusion"]["confidence"] = copy.deepcopy(
            pattern["confidence"]
        )

        result = self.run_analysis_validator(current, output)

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_pattern_and_record_links_must_agree(self):
        current = corpus(two_records() + [resolved_record(pr_id="PR-003", node_id="node-003")])
        revision = self.current_revision()
        cases = []

        missing_backlink = analysis_output(current, revision)
        missing_backlink["records"][1]["analysis"]["pattern_ids"] = []
        missing_backlink["records"][1]["analysis_history"][-1]["conclusion"]["pattern_ids"] = []
        cases.append((missing_backlink, "PR-002.analysis.pattern_ids must list PAT-001"))

        extra_listing = analysis_output(current, revision)
        extra_listing["patterns"][0]["evidence_pr_ids"] = ["PR-001", "PR-002"]
        extra_listing["patterns"][0]["confidence"]["evidence"] = [
            'PR-001 "' + QUOTE + '"', 'PR-002 "' + QUOTE + '"'
        ]
        extra_listing["patterns"][0]["source_licenses"] = extra_listing["patterns"][0][
            "source_licenses"
        ][:2]
        extra_listing["patterns"][0]["pattern_history"][-1]["conclusion"] = {
            key: value
            for key, value in extra_listing["patterns"][0].items()
            if key != "pattern_history"
        }
        cases.append((extra_listing, "PR-003.analysis.pattern_ids lists PAT-001 without being its evidence"))

        unknown_pattern = analysis_output(current, revision)
        unknown_pattern["records"][0]["analysis"]["pattern_ids"].append("PAT-404")
        unknown_pattern["records"][0]["analysis_history"][-1]["conclusion"]["pattern_ids"].append(
            "PAT-404"
        )
        cases.append((unknown_pattern, "PR-001.analysis.pattern_ids lists unknown PAT-404"))

        unknown_evidence = analysis_output(current, revision)
        unknown_evidence["patterns"][0]["evidence_pr_ids"].append("PR-404")
        unknown_evidence["patterns"][0]["pattern_history"][-1]["conclusion"][
            "evidence_pr_ids"
        ].append("PR-404")
        cases.append((unknown_evidence, "evidence PR-404 is not an analyzed record"))

        for output, message in cases:
            with self.subTest(message=message):
                result = self.run_analysis_validator(current, output)
                self.assertEqual(result.returncode, 1)
                self.assertIn(message, result.stderr)

    def test_existing_pattern_may_be_superseded_only_by_a_current_pattern(self):
        current = corpus(two_records())
        revision = self.current_revision()
        legacy = {"revision": "old", "conclusion": "single-PR pattern"}
        previous = analysis_output(current, revision)
        previous["patterns"].append({"pattern_id": "PAT-002", "pattern_history": [legacy]})

        def superseded_output(successor):
            output = analysis_output(current, revision, existing=previous)
            old = pattern_projection(revision, pattern_id="PAT-002", pr_ids=("PR-001",))
            old["confidence"]["evidence"] = ["Legacy single-PR observation"]
            old["superseded_by"] = successor
            old["pattern_history"] = [
                copy.deepcopy(legacy),
                {"revision": revision, "generated_at": "2026-09-04T12:00:00Z",
                 "conclusion": copy.deepcopy(old)},
            ]
            output["patterns"].append(old)
            return output

        result = self.run_analysis_validator(current, superseded_output("PAT-001"), previous)
        self.assertEqual(result.returncode, 0, result.stderr)
        for successor in ("PAT-404", "PAT-002"):
            with self.subTest(successor=successor):
                result = self.run_analysis_validator(current, superseded_output(successor), previous)
                self.assertEqual(result.returncode, 1)
                self.assertIn("PAT-002.superseded_by must name a current pattern", result.stderr)

    def test_new_pattern_cannot_be_superseded(self):
        current = corpus(two_records())
        revision = self.current_revision()
        output = analysis_output(current, revision)
        new = pattern_projection(revision, pattern_id="PAT-002", pr_ids=("PR-001",))
        new["superseded_by"] = "PAT-001"
        new["pattern_history"] = [
            {"revision": revision, "generated_at": "2026-09-04T12:00:00Z",
             "conclusion": copy.deepcopy(new)}
        ]
        output["patterns"].append(new)

        result = self.run_analysis_validator(current, output)

        self.assertEqual(result.returncode, 1)
        self.assertIn("PAT-002 is new and cannot be superseded", result.stderr)

    def test_pattern_quote_comes_from_one_source_text_of_the_public_pr(self):
        records = two_records()
        records[1]["pull_request"]["url"] = "https://github.com/example/repo/pull/2"
        records[1]["evidence_snapshot"] = {
            "body_excerpt": "Short body.",
            "changed_files": [{"path": "lib/a.js", "change_excerpt": "+  const fixable = null; // report only from now"}],
            "commits": [{"message": "fix: stop rewriting reordered promise chains\n\nDetails"}],
            "reviews": [{"excerpt": "Please keep the rule report-only for safety reasons."}],
            "linked_issues": [
                {"url": "https://github.com/example/repo/issues/9", "title": "Autofix changes runtime semantics badly"},
                {"url": "https://github.com/private/tracker/issues/1", "title": "Private tracker issue title text"},
            ],
        }
        current = corpus(records)
        revision = self.current_revision()
        cases = [
            ("const fixable = null; // report only", 0),
            ("stop rewriting reordered promise chains", 0),
            ("keep the rule report-only for safety", 0),
            ("Autofix changes runtime semantics badly", 0),
            ("Private tracker issue title text", 1),
            ("Keep derived values synchronized Short body.", 1),
        ]
        for quote, expected in cases:
            with self.subTest(quote=quote):
                output = analysis_output(current, revision)
                pattern = output["patterns"][0]
                pattern["confidence"]["evidence"][1] = 'PR-002 "' + quote + '"'
                pattern["pattern_history"][-1]["conclusion"]["confidence"] = copy.deepcopy(
                    pattern["confidence"]
                )
                result = self.run_analysis_validator(current, output)
                self.assertEqual(result.returncode, expected, result.stderr)
                if expected:
                    self.assertIn("quote is not verbatim in PR-002", result.stderr)

    def test_existing_analysis_requires_analysis_output(self):
        with tempfile.TemporaryDirectory() as directory:
            existing_path = Path(directory) / "existing.json"
            existing_path.write_text("{}", encoding="utf-8")
            result = self.run_paths(
                Path(directory) / "current.json",
                "--existing-analysis",
                existing_path,
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn("--existing-analysis requires --analysis-output", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
