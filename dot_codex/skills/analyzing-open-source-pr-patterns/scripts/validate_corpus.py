#!/usr/bin/env python3
"""Validate normalized PR corpora and strict append-only analysis outputs."""

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys


SUPPORTED_SCHEMA_VERSION = "1.0.0"
ANALYZER_NAME = "analyzing-open-source-pr-patterns"
SKILL_DIR = Path(__file__).resolve().parents[1]
REVISION_PATHS = (
    "SKILL.md",
    "agents/openai.yaml",
    "references/analysis-contract.md",
    "references/data-contract.md",
    "scripts/validate_corpus.py",
    "tests/test_validate_corpus.py",
)
OUTPUT_KEYS = {
    "schema_version",
    "generated_by",
    "analysis_generated_by",
    "records",
    "patterns",
    "limitations",
}
EVIDENCE_CLAIM_KEYS = {"value", "basis", "evidence_links"}
CONFIDENCE_KEYS = {"level", "evidence", "limitations"}
ANALYSIS_KEYS = {
    "change_summary",
    "motivation",
    "review_judgment",
    "closure_reason",
    "files_changed",
    "test_evidence",
    "pattern_ids",
    "evidence_links",
    "evidence_manifest",
    "license_spdx",
    "provenance_mode",
    "confidence",
    "superseded_by",
}
PATTERN_KEYS = {
    "pattern_id",
    "description",
    "generated_by",
    "evidence_pr_ids",
    "applicability",
    "counterconditions",
    "search_clues",
    "expected_tests",
    "maintainer_judgment_required",
    "source_licenses",
    "provenance_mode",
    "confidence",
    "superseded_by",
}
SNAPSHOT_KEYS = {"revision", "generated_at", "evidence_manifest", "conclusion"}
PATTERN_SNAPSHOT_KEYS = {"revision", "generated_at", "conclusion"}


def _is_nonempty_string(value):
    return isinstance(value, str) and bool(value.strip())


def _record_url(record):
    pull_request = record.get("pull_request")
    if not isinstance(pull_request, dict):
        return None
    return pull_request.get("url")


def _record_identity(record):
    if not isinstance(record, dict):
        return None
    if record.get("identity_status") == "resolved":
        node_id = record.get("pull_request_node_id")
        return ("node", node_id) if _is_nonempty_string(node_id) else None
    url = _record_url(record)
    return ("url", url) if _is_nonempty_string(url) else None


def _identity_description(identity):
    if identity is None:
        return "unknown identity"
    label = "pull_request_node_id" if identity[0] == "node" else "URL"
    return label + " " + str(identity[1])


def _is_prefix(previous, current):
    return len(previous) <= len(current) and current[: len(previous)] == previous


def _validate_document(document, label):
    errors = []
    if not isinstance(document, dict):
        return [label + " must be a top-level object"]

    if document.get("schema_version") != SUPPORTED_SCHEMA_VERSION:
        errors.append(
            label
            + " has unsupported schema_version: "
            + repr(document.get("schema_version"))
        )

    records = document.get("records")
    if not isinstance(records, list):
        return errors + [label + ".records must be an array"]

    resolved_nodes = set()
    pr_ids = set()
    unresolved_urls = set()
    for index, record in enumerate(records):
        prefix = label + ".records[" + str(index) + "]"
        if not isinstance(record, dict):
            errors.append(prefix + " must be an object")
            continue

        status = record.get("identity_status")
        if status not in ("resolved", "unresolved"):
            errors.append(prefix + " has unsupported identity_status")

        if not isinstance(record.get("sources"), list) or not record["sources"]:
            errors.append(prefix + ".sources must be a nonempty array")
        else:
            source_keys = set()
            for source_index, source in enumerate(record["sources"]):
                source_prefix = prefix + ".sources[" + str(source_index) + "]"
                if not isinstance(source, dict):
                    errors.append(source_prefix + " must be an object")
                    continue
                source_key = source.get("source_key")
                if not _is_nonempty_string(source_key):
                    errors.append(source_prefix + " requires a nonempty source_key")
                elif source_key in source_keys:
                    errors.append(prefix + " has duplicate source_key: " + source_key)
                else:
                    source_keys.add(source_key)
                if not isinstance(source.get("observations"), list):
                    errors.append(source_prefix + ".observations must be an array")

        if not isinstance(record.get("state_history"), list) or not record["state_history"]:
            errors.append(prefix + ".state_history must be a nonempty array")

        analysis_history = record.get("analysis_history")
        if analysis_history is not None and not isinstance(analysis_history, list):
            errors.append(prefix + ".analysis_history must be an array when present")

        url = _record_url(record)
        if not _is_nonempty_string(url):
            errors.append(prefix + " requires a nonempty pull_request.url")

        if status == "resolved":
            node_id = record.get("pull_request_node_id")
            repository = record.get("repository")
            repository_node_id = (
                repository.get("node_id") if isinstance(repository, dict) else None
            )
            if not _is_nonempty_string(node_id):
                errors.append(prefix + " resolved record requires a nonempty pull_request_node_id")
            elif node_id in resolved_nodes:
                errors.append(prefix + " has duplicate pull_request_node_id: " + node_id)
            else:
                resolved_nodes.add(node_id)
            if not _is_nonempty_string(repository_node_id):
                errors.append(prefix + " resolved record requires a nonempty repository.node_id")
            expected_key = "github-pr:" + node_id if _is_nonempty_string(node_id) else None
            if record.get("record_key") != expected_key:
                errors.append(prefix + " record_key must equal github-pr:<pull_request_node_id>")
            pr_id = record.get("pr_id")
            if pr_id is not None:
                if not _is_nonempty_string(pr_id):
                    errors.append(prefix + " pr_id must be a nonempty string when present")
                elif pr_id in pr_ids:
                    errors.append(prefix + " has duplicate pr_id: " + str(pr_id))
                else:
                    pr_ids.add(pr_id)
        elif status == "unresolved":
            if record.get("pr_id") not in (None, ""):
                errors.append(prefix + " unresolved record must not have pr_id")
            if _is_nonempty_string(url):
                if url in unresolved_urls:
                    errors.append(prefix + " has duplicate unresolved pull_request.url: " + url)
                unresolved_urls.add(url)

    return errors


def _compare_documents(previous, current):
    errors = []
    current_records = current.get("records", [])
    current_by_identity = {
        _record_identity(record): record
        for record in current_records
        if _record_identity(record) is not None
    }

    for index, old_record in enumerate(previous.get("records", [])):
        if not isinstance(old_record, dict):
            continue
        identity = _record_identity(old_record)
        current_record = current_by_identity.get(identity)
        identity_description = _identity_description(identity)
        if current_record is None and identity is not None and identity[0] == "url":
            current_record = next(
                (
                    record
                    for record in current_records
                    if isinstance(record, dict) and _record_url(record) == identity[1]
                ),
                None,
            )
        if current_record is None:
            errors.append(
                "existing.records[" + str(index) + "] was removed (" + identity_description + ")"
            )
            continue

        old_status = old_record.get("identity_status")
        old_pr_id = old_record.get("pr_id")
        if old_status == "resolved" and current_record.get("pr_id") != old_pr_id:
            errors.append(
                "existing.records["
                + str(index)
                + "] pr_id changed from "
                + str(old_pr_id)
                + " to "
                + str(current_record.get("pr_id"))
            )

        old_state_history = old_record.get("state_history")
        new_state_history = current_record.get("state_history")
        if isinstance(old_state_history, list) and isinstance(new_state_history, list):
            if not _is_prefix(old_state_history, new_state_history):
                errors.append(
                    identity_description + " state_history is not an exact prefix of current history"
                )

        old_sources = old_record.get("sources")
        new_sources = current_record.get("sources")
        if isinstance(old_sources, list) and isinstance(new_sources, list):
            old_keys = [
                source.get("source_key") if isinstance(source, dict) else None
                for source in old_sources
            ]
            new_keys = [
                source.get("source_key") if isinstance(source, dict) else None
                for source in new_sources
            ]
            if not _is_prefix(old_keys, new_keys):
                errors.append(
                    identity_description + " source_key order is not an exact prefix"
                )
            for source_index, old_source in enumerate(old_sources):
                if not isinstance(old_source, dict):
                    continue
                source_key = old_source.get("source_key")
                new_source = (
                    new_sources[source_index]
                    if source_index < len(new_sources)
                    and isinstance(new_sources[source_index], dict)
                    and new_sources[source_index].get("source_key") == source_key
                    else None
                )
                if new_source is None:
                    if source_key not in new_keys:
                        errors.append(
                            identity_description + " source_key removed: " + str(source_key)
                        )
                    continue
                old_metadata = {
                    key: value
                    for key, value in old_source.items()
                    if key != "observations"
                }
                new_metadata = {
                    key: value
                    for key, value in new_source.items()
                    if key != "observations"
                }
                if old_metadata != new_metadata:
                    errors.append(
                        identity_description
                        + " source "
                        + str(source_key)
                        + " source metadata changed"
                    )
                old_observations = old_source.get("observations")
                new_observations = new_source.get("observations")
                if isinstance(old_observations, list) and isinstance(new_observations, list):
                    if not _is_prefix(old_observations, new_observations):
                        errors.append(
                            identity_description
                            + " source "
                            + str(source_key)
                            + " observations is not an exact prefix"
                        )

        if "analysis_history" in old_record:
            old_analysis = old_record.get("analysis_history")
            new_analysis = current_record.get("analysis_history")
            if not isinstance(new_analysis, list):
                errors.append(identity_description + " analysis_history was removed")
            elif isinstance(old_analysis, list) and not _is_prefix(old_analysis, new_analysis):
                errors.append(
                    identity_description
                    + " analysis_history is not an exact prefix of current history"
                )

    return errors


def _canonical_revision():
    digest = hashlib.sha256()
    for relative_path in sorted(REVISION_PATHS):
        path_bytes = relative_path.encode("utf-8")
        content = (SKILL_DIR / relative_path).read_bytes()
        digest.update(len(path_bytes).to_bytes(8, byteorder="big"))
        digest.update(path_bytes)
        digest.update(len(content).to_bytes(8, byteorder="big"))
        digest.update(content)
    return "sha256:" + digest.hexdigest()


def _validate_exact_keys(value, expected, prefix, errors):
    if not isinstance(value, dict):
        errors.append(prefix + " must be an object")
        return False
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        details = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if extra:
            details.append("extra " + ", ".join(extra))
        errors.append(prefix + " has invalid fields (" + "; ".join(details) + ")")
        return False
    return True


def _validate_string_list(value, prefix, errors):
    if not isinstance(value, list):
        errors.append(prefix + " must be an array of strings")
        return
    for index, item in enumerate(value):
        if not isinstance(item, str):
            errors.append(prefix + "[" + str(index) + "] must be a string")


def _validate_generated_by(value, expected, prefix, errors):
    if not _validate_exact_keys(value, {"name", "revision"}, prefix, errors):
        return
    if value != expected:
        errors.append(prefix + " must equal the current analysis generator")


def _validate_evidence_claim(value, prefix, errors):
    if not _validate_exact_keys(value, EVIDENCE_CLAIM_KEYS, prefix, errors):
        return
    if value["value"] is not None and not isinstance(value["value"], str):
        errors.append(prefix + ".value must be a string or null")
    if value["basis"] not in ("fact", "inference", "unknown"):
        errors.append(prefix + ".basis is unsupported")
    _validate_string_list(value["evidence_links"], prefix + ".evidence_links", errors)


def _validate_confidence(value, prefix, errors):
    if not _validate_exact_keys(value, CONFIDENCE_KEYS, prefix, errors):
        return
    if value["level"] not in ("high", "medium", "low"):
        errors.append(prefix + ".level is unsupported")
    _validate_string_list(value["evidence"], prefix + ".evidence", errors)
    _validate_string_list(value["limitations"], prefix + ".limitations", errors)


def _validate_projection(value, prefix, errors):
    if not _validate_exact_keys(value, ANALYSIS_KEYS, prefix, errors):
        return
    for field in ("change_summary", "motivation", "review_judgment", "closure_reason"):
        _validate_evidence_claim(value[field], prefix + "." + field, errors)
    _validate_string_list(value["files_changed"], prefix + ".files_changed", errors)
    if not isinstance(value["test_evidence"], list):
        errors.append(prefix + ".test_evidence must be an array")
    else:
        for index, claim in enumerate(value["test_evidence"]):
            _validate_evidence_claim(
                claim, prefix + ".test_evidence[" + str(index) + "]", errors
            )
    _validate_string_list(value["pattern_ids"], prefix + ".pattern_ids", errors)
    if isinstance(value["pattern_ids"], list):
        for index, pattern_id in enumerate(value["pattern_ids"]):
            if not isinstance(pattern_id, str) or not re.fullmatch(r"PAT-.+", pattern_id):
                errors.append(prefix + ".pattern_ids[" + str(index) + "] must be PAT-*")
    _validate_string_list(value["evidence_links"], prefix + ".evidence_links", errors)
    if not isinstance(value["evidence_manifest"], dict):
        errors.append(prefix + ".evidence_manifest must be an object")
    if not isinstance(value["license_spdx"], str):
        errors.append(prefix + ".license_spdx must be a string")
    if value["provenance_mode"] not in (
        "independent-reimplementation",
        "adapted",
        "verbatim",
    ):
        errors.append(prefix + ".provenance_mode is unsupported")
    _validate_confidence(value["confidence"], prefix + ".confidence", errors)
    if value["superseded_by"] is not None and not isinstance(value["superseded_by"], str):
        errors.append(prefix + ".superseded_by must be a string or null")


def _is_rfc3339(value):
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _validate_analysis_snapshot(snapshot, analysis, revision, prefix, errors):
    if not _validate_exact_keys(snapshot, SNAPSHOT_KEYS, prefix, errors):
        return
    if snapshot["revision"] != revision:
        errors.append(prefix + ".revision must equal analysis_generated_by.revision")
    if not _is_rfc3339(snapshot["generated_at"]):
        errors.append(prefix + ".generated_at must be an RFC3339 string")
    if snapshot["evidence_manifest"] != analysis.get("evidence_manifest"):
        errors.append(prefix + ".evidence_manifest must equal current analysis")
    if snapshot["conclusion"] != analysis:
        errors.append(prefix + ".conclusion must equal current analysis")


def _existing_record_map(existing):
    records = existing.get("records", []) if isinstance(existing, dict) else []
    if not isinstance(records, list):
        return {}
    return {
        _record_identity(record): record
        for record in records
        if _record_identity(record) is not None
    }


def _existing_patterns(existing):
    if not isinstance(existing, dict):
        return []
    candidates = []
    if isinstance(existing.get("patterns"), list):
        candidates.extend(existing["patterns"])
    if isinstance(existing.get("records"), list):
        candidates.extend(
            record
            for record in existing["records"]
            if isinstance(record, dict) and _is_nonempty_string(record.get("pattern_id"))
        )
    return candidates


def _validate_output_record(
    input_record,
    output_record,
    previous_record,
    revision,
    prefix,
    errors,
):
    expected_keys = set(input_record) | {"analysis", "analysis_history"}
    if not isinstance(output_record, dict):
        errors.append(prefix + " must be an object")
        return
    if set(output_record) != expected_keys:
        errors.append(prefix + " must preserve normalized fields and add only analysis/history")

    for field, input_value in input_record.items():
        if field in ("analysis", "analysis_history"):
            continue
        if output_record.get(field) != input_value:
            errors.append(prefix + " normalized field " + field + " changed")

    analysis = output_record.get("analysis")
    _validate_projection(analysis, prefix + ".analysis", errors)

    input_history = input_record.get("analysis_history", [])
    if not isinstance(input_history, list):
        input_history = []
    base_history = input_history
    if previous_record is not None:
        previous_history = previous_record.get("analysis_history")
        if not isinstance(previous_history, list):
            errors.append(prefix + " existing analysis_history must be an array")
        else:
            if not _is_prefix(input_history, previous_history):
                errors.append(prefix + " input analysis_history is not a prefix of existing history")
            base_history = previous_history

    output_history = output_record.get("analysis_history")
    if not isinstance(output_history, list):
        errors.append(prefix + ".analysis_history must be an array")
        return
    if len(output_history) != len(base_history) + 1:
        errors.append(prefix + " must append exactly one current snapshot")
    elif not _is_prefix(base_history, output_history):
        errors.append(prefix + " analysis_history is not an exact prefix")
    if output_history:
        _validate_analysis_snapshot(
            output_history[-1],
            analysis if isinstance(analysis, dict) else {},
            revision,
            prefix + ".analysis_history[-1]",
            errors,
        )


def _validate_pattern_projection(value, generator, prefix, errors):
    if not _validate_exact_keys(value, PATTERN_KEYS, prefix, errors):
        return
    if not _is_nonempty_string(value["pattern_id"]) or not re.fullmatch(
        r"PAT-.+", value["pattern_id"]
    ):
        errors.append(prefix + ".pattern_id must be PAT-*")
    if not isinstance(value["description"], str):
        errors.append(prefix + ".description must be a string")
    _validate_generated_by(value["generated_by"], generator, prefix + ".generated_by", errors)
    for field in (
        "evidence_pr_ids",
        "applicability",
        "counterconditions",
        "search_clues",
        "expected_tests",
        "maintainer_judgment_required",
    ):
        _validate_string_list(value[field], prefix + "." + field, errors)
    if isinstance(value["evidence_pr_ids"], list):
        for index, pr_id in enumerate(value["evidence_pr_ids"]):
            if not isinstance(pr_id, str) or not re.fullmatch(r"PR-.+", pr_id):
                errors.append(prefix + ".evidence_pr_ids[" + str(index) + "] must be PR-*")
    source_licenses = value["source_licenses"]
    if not isinstance(source_licenses, list):
        errors.append(prefix + ".source_licenses must be an array")
    else:
        for index, source_license in enumerate(source_licenses):
            source_prefix = prefix + ".source_licenses[" + str(index) + "]"
            if not _validate_exact_keys(
                source_license, {"pr_id", "spdx_id"}, source_prefix, errors
            ):
                continue
            if not _is_nonempty_string(source_license["pr_id"]):
                errors.append(source_prefix + ".pr_id must be a nonempty string")
            if not isinstance(source_license["spdx_id"], str):
                errors.append(source_prefix + ".spdx_id must be a string")
    if value["provenance_mode"] not in (
        "independent-reimplementation",
        "adapted",
        "verbatim",
    ):
        errors.append(prefix + ".provenance_mode is unsupported")
    _validate_confidence(value["confidence"], prefix + ".confidence", errors)
    if value["superseded_by"] is not None and not isinstance(value["superseded_by"], str):
        errors.append(prefix + ".superseded_by must be a string or null")


def _validate_pattern_record(pattern, previous_pattern, generator, revision, prefix, errors):
    if not isinstance(pattern, dict):
        errors.append(prefix + " must be an object")
        return
    expected_keys = PATTERN_KEYS | {"pattern_history"}
    if set(pattern) != expected_keys:
        errors.append(prefix + " has invalid pattern fields")
    projection = {key: pattern.get(key) for key in PATTERN_KEYS}
    _validate_pattern_projection(projection, generator, prefix, errors)

    base_history = []
    if previous_pattern is not None:
        previous_history = previous_pattern.get("pattern_history")
        if not isinstance(previous_history, list):
            errors.append(prefix + " existing pattern_history must be an array")
        else:
            base_history = previous_history
    history = pattern.get("pattern_history")
    if not isinstance(history, list):
        errors.append(prefix + ".pattern_history must be an array")
        return
    if len(history) != len(base_history) + 1:
        errors.append(prefix + " must append exactly one current pattern snapshot")
    elif not _is_prefix(base_history, history):
        errors.append(prefix + " pattern_history is not an exact prefix")
    if history:
        snapshot = history[-1]
        snapshot_prefix = prefix + ".pattern_history[-1]"
        if _validate_exact_keys(
            snapshot, PATTERN_SNAPSHOT_KEYS, snapshot_prefix, errors
        ):
            if snapshot["revision"] != revision:
                errors.append(snapshot_prefix + ".revision must equal current revision")
            if not _is_rfc3339(snapshot["generated_at"]):
                errors.append(snapshot_prefix + ".generated_at must be an RFC3339 string")
            if snapshot["conclusion"] != projection:
                errors.append(snapshot_prefix + ".conclusion must equal current pattern")


def _validate_analysis_output(current, output, existing, revision):
    errors = []
    if not _validate_exact_keys(output, OUTPUT_KEYS, "analysis output", errors):
        if not isinstance(output, dict):
            return errors

    if output.get("schema_version") != SUPPORTED_SCHEMA_VERSION:
        errors.append("analysis output has unsupported schema_version")
    if output.get("generated_by") != current.get("generated_by"):
        errors.append("analysis output.generated_by must exactly copy input generated_by")

    generator = {"name": ANALYZER_NAME, "revision": revision}
    _validate_generated_by(
        output.get("analysis_generated_by"),
        generator,
        "analysis output.analysis_generated_by",
        errors,
    )
    _validate_string_list(output.get("limitations"), "analysis output.limitations", errors)

    input_records = {
        _record_identity(record): record
        for record in current.get("records", [])
        if _record_identity(record) is not None
    }
    previous_records = _existing_record_map(existing)
    output_records = output.get("records")
    output_by_identity = {}
    if not isinstance(output_records, list):
        errors.append("analysis output.records must be an array")
    else:
        for index, record in enumerate(output_records):
            prefix = "analysis output.records[" + str(index) + "]"
            identity = _record_identity(record)
            if identity is None:
                errors.append(prefix + " has no matchable identity")
                continue
            if identity in output_by_identity:
                errors.append(prefix + " duplicates " + _identity_description(identity))
                continue
            output_by_identity[identity] = record
            input_record = input_records.get(identity)
            if input_record is None:
                errors.append(prefix + " does not match an input record")
                continue
            _validate_output_record(
                input_record,
                record,
                previous_records.get(identity),
                revision,
                prefix,
                errors,
            )
    for identity in input_records:
        if identity not in output_by_identity:
            errors.append("analysis output missing input record " + _identity_description(identity))
    for identity in previous_records:
        if identity not in output_by_identity:
            errors.append("existing analyzed record was removed: " + _identity_description(identity))

    previous_patterns = {}
    for pattern in _existing_patterns(existing):
        pattern_id = pattern.get("pattern_id") if isinstance(pattern, dict) else None
        if _is_nonempty_string(pattern_id):
            previous_patterns[pattern_id] = pattern
    patterns = output.get("patterns")
    output_patterns = {}
    if not isinstance(patterns, list):
        errors.append("analysis output.patterns must be an array")
    else:
        for index, pattern in enumerate(patterns):
            prefix = "analysis output.patterns[" + str(index) + "]"
            pattern_id = pattern.get("pattern_id") if isinstance(pattern, dict) else None
            if not _is_nonempty_string(pattern_id):
                errors.append(prefix + " requires a pattern_id")
                continue
            if pattern_id in output_patterns:
                errors.append(prefix + " has duplicate pattern_id: " + pattern_id)
                continue
            output_patterns[pattern_id] = pattern
            _validate_pattern_record(
                pattern,
                previous_patterns.get(pattern_id),
                generator,
                revision,
                prefix,
                errors,
            )
    for pattern_id in previous_patterns:
        if pattern_id not in output_patterns:
            errors.append("existing pattern was removed: " + pattern_id)

    return errors


def _load(path, label):
    try:
        with open(path, encoding="utf-8") as stream:
            return json.load(stream), []
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        return None, [label + " could not be read as JSON: " + str(error)]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate a normalized PR corpus")
    parser.add_argument("current", nargs="?", help="current corpus JSON file")
    parser.add_argument("--existing", help="previous corpus JSON file")
    parser.add_argument("--analysis-output", help="enriched analysis output JSON file")
    parser.add_argument(
        "--existing-analysis", help="previous enriched analysis output JSON file"
    )
    parser.add_argument(
        "--print-revision", action="store_true", help="print the canonical skill revision"
    )
    args = parser.parse_args(argv)

    if args.print_revision:
        if args.current or args.existing or args.analysis_output or args.existing_analysis:
            print("--print-revision must be used alone", file=sys.stderr)
            return 1
        try:
            print(_canonical_revision())
        except OSError as error:
            print("skill revision could not be computed: " + str(error), file=sys.stderr)
            return 1
        return 0

    if args.existing_analysis and not args.analysis_output:
        print("--existing-analysis requires --analysis-output", file=sys.stderr)
        return 1
    if not args.current:
        print("CURRENT is required unless --print-revision is used", file=sys.stderr)
        return 1

    current, errors = _load(args.current, "current")
    if not errors:
        errors.extend(_validate_document(current, "current"))

    previous = None
    if args.existing:
        previous, previous_errors = _load(args.existing, "existing")
        errors.extend(previous_errors)
        if not previous_errors:
            errors.extend(_validate_document(previous, "existing"))
        if not errors and current is not None:
            errors.extend(_compare_documents(previous, current))

    output = None
    existing_analysis = None
    if args.analysis_output:
        output, output_errors = _load(args.analysis_output, "analysis output")
        errors.extend(output_errors)
        if args.existing_analysis:
            existing_analysis, existing_errors = _load(
                args.existing_analysis, "existing analysis"
            )
            errors.extend(existing_errors)
        if not errors:
            try:
                revision = _canonical_revision()
            except OSError as error:
                errors.append("skill revision could not be computed: " + str(error))
            else:
                errors.extend(
                    _validate_analysis_output(
                        current, output, existing_analysis, revision
                    )
                )

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    count = len(current["records"])
    if args.analysis_output:
        print(
            "Validated analysis output for "
            + str(count)
            + " records (schema 1.0.0)."
        )
    else:
        suffix = " against existing corpus" if args.existing else ""
        print("Validated " + str(count) + " records (schema 1.0.0)" + suffix + ".")
    return 0


if __name__ == "__main__":
    sys.exit(main())
