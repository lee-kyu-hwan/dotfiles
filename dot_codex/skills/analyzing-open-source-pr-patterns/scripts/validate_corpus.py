#!/usr/bin/env python3
"""Validate normalized pull-request corpus files and their append-only updates."""

import argparse
import json
import sys


SUPPORTED_SCHEMA_VERSION = "1.0.0"


def _is_nonempty_string(value):
    return isinstance(value, str) and bool(value.strip())


def _record_url(record):
    pull_request = record.get("pull_request")
    if not isinstance(pull_request, dict):
        return None
    return pull_request.get("url")


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

        if not _is_nonempty_string(_record_url(record)):
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

    return errors


def _is_prefix(previous, current):
    return len(previous) <= len(current) and current[: len(previous)] == previous


def _compare_documents(previous, current):
    errors = []
    current_records = current.get("records", [])
    by_node = {
        record.get("pull_request_node_id"): record
        for record in current_records
        if isinstance(record, dict) and record.get("identity_status") == "resolved"
    }
    by_url = {
        _record_url(record): record
        for record in current_records
        if isinstance(record, dict) and _is_nonempty_string(_record_url(record))
    }

    for index, old_record in enumerate(previous.get("records", [])):
        if not isinstance(old_record, dict):
            continue
        old_status = old_record.get("identity_status")
        if old_status == "resolved":
            identity = old_record.get("pull_request_node_id")
            current_record = by_node.get(identity)
            identity_description = "pull_request_node_id " + str(identity)
        else:
            identity = _record_url(old_record)
            current_record = by_url.get(identity)
            identity_description = "URL " + str(identity)
        if current_record is None:
            errors.append(
                "existing.records[" + str(index) + "] was removed (" + identity_description + ")"
            )
            continue

        old_pr_id = old_record.get("pr_id")
        if old_pr_id is not None and current_record.get("pr_id") != old_pr_id:
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
            new_sources_by_key = {
                source.get("source_key"): source
                for source in new_sources
                if isinstance(source, dict)
            }
            for source in old_sources:
                if not isinstance(source, dict):
                    continue
                source_key = source.get("source_key")
                new_source = new_sources_by_key.get(source_key)
                if new_source is None:
                    errors.append(
                        identity_description
                        + " source_key removed: "
                        + str(source_key)
                    )
                    continue
                old_observations = source.get("observations")
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


def _load(path, label):
    try:
        with open(path) as stream:
            return json.load(stream), []
    except (OSError, json.JSONDecodeError) as error:
        return None, [label + " could not be read as JSON: " + str(error)]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate a normalized PR corpus")
    parser.add_argument("current", help="current corpus JSON file")
    parser.add_argument("--existing", help="previous corpus JSON file")
    args = parser.parse_args(argv)

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

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    count = len(current["records"])
    suffix = " against existing corpus" if args.existing else ""
    print("Validated " + str(count) + " records (schema 1.0.0)" + suffix + ".")
    return 0


if __name__ == "__main__":
    sys.exit(main())
