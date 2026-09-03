"""Validate quality-goal reviews and evaluate their artifact gates."""

import argparse
import json
from pathlib import Path
import sys


ARTIFACTS = {"spec", "plan", "code"}
VERDICTS = {"PASS", "REVISE", "BLOCKED"}
SEVERITIES = {"Critical", "High", "Medium", "Low"}
HARD_SEVERITIES = {"Critical", "High"}
SCORE_THRESHOLD = 85
REQUIRED_FIELDS = (
    "artifact", "round", "score", "verdict",
    "blockers", "findings", "evidence", "required_next_action",
)

REQUIRED_CHECKS = {
    "spec": {
        "required_sections",
        "material_decisions_resolved",
        "acceptance_criteria_objective",
    },
    "plan": {
        "required_sections",
        "traceability_complete",
        "placeholders_absent",
    },
    "code": {
        "required_commands_passed",
        "acceptance_criteria_met",
        "unrelated_changes_absent",
        "documentation_current",
    },
}


FINDING_FIELDS = (
    "id",
    "severity",
    "description",
    "evidence_location",
    "rubric_item",
    "required_resolution",
    "new_blocker_evidence",
)
EVIDENCE_FIELDS = ("claim", "location", "verified")
EVIDENCE_STRING_FIELDS = ("claim", "location")
PRIOR_FIELDS = ("open_finding_ids", "open_findings", "resolved_finding_ids")
OPEN_FINDING_FIELDS = (
    "id", "severity", "description", "evidence_location",
    "required_resolution", "resolution_claim", "resolution_evidence",
)
OPEN_FINDING_STRING_FIELDS = (
    "id", "severity", "description", "evidence_location", "required_resolution",
)


def _is_integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _is_non_empty_string(value):
    return isinstance(value, str) and bool(value.strip())


def _unknown_keys(mapping, allowed):
    return sorted(
        (key for key in mapping if key not in allowed),
        key=lambda key: str(key),
    )


def _format_key(key):
    return repr(key)


def _prior_open_finding_ids(prior, errors):
    if prior is None:
        return []
    if not isinstance(prior, dict):
        errors.append("prior must be a dict")
        return []
    if "open_finding_ids" not in prior:
        errors.append("prior is missing required field: open_finding_ids")
        return []
    for key in _unknown_keys(prior, set(PRIOR_FIELDS)):
        errors.append(f"prior has unknown field: {_format_key(key)}")

    open_ids = prior["open_finding_ids"]
    if not isinstance(open_ids, list):
        errors.append("prior.open_finding_ids must be a list")
        return []

    valid_ids = []
    seen_ids = set()
    for index, finding_id in enumerate(open_ids):
        if not isinstance(finding_id, str):
            errors.append(
                f"prior.open_finding_ids[{index}] must be a string"
            )
        else:
            valid_ids.append(finding_id)
            if finding_id in seen_ids:
                errors.append(f"duplicate prior.open_finding_ids entry: {finding_id!r}")
            seen_ids.add(finding_id)

    open_findings = prior.get("open_findings")
    if open_findings is not None:
        if not isinstance(open_findings, list):
            errors.append("prior.open_findings must be a list")
        else:
            finding_ids = set()
            for index, finding in enumerate(open_findings):
                prefix = f"prior.open_findings[{index}]"
                if not isinstance(finding, dict):
                    errors.append(f"{prefix} must be a dict")
                    continue
                for field in OPEN_FINDING_FIELDS:
                    if field not in finding:
                        errors.append(f"{prefix} missing required field: {field}")
                for key in _unknown_keys(finding, set(OPEN_FINDING_FIELDS)):
                    errors.append(f"{prefix} has unknown field: {_format_key(key)}")
                for field in OPEN_FINDING_STRING_FIELDS:
                    if field in finding and not _is_non_empty_string(finding[field]):
                        errors.append(f"{prefix}.{field} must be a non-empty string")
                if "severity" in finding and finding["severity"] not in SEVERITIES:
                    errors.append(f"{prefix}.severity must be one of: Critical, High, Low, Medium")
                for field in ("resolution_claim", "resolution_evidence"):
                    if field in finding and finding[field] is not None and not isinstance(finding[field], str):
                        errors.append(f"{prefix}.{field} must be a string or null")
                finding_id = finding.get("id")
                if isinstance(finding_id, str):
                    if finding_id in finding_ids:
                        errors.append(f"duplicate prior open finding ID: {finding_id!r}")
                    finding_ids.add(finding_id)
            for finding_id in valid_ids:
                if finding_id not in finding_ids:
                    errors.append(f"prior.open_finding_ids entry missing from open_findings: {finding_id!r}")

    resolved_ids = prior.get("resolved_finding_ids")
    if resolved_ids is not None:
        if not isinstance(resolved_ids, list):
            errors.append("prior.resolved_finding_ids must be a list")
        else:
            seen_resolved = set()
            for index, finding_id in enumerate(resolved_ids):
                if not isinstance(finding_id, str):
                    errors.append(f"prior.resolved_finding_ids[{index}] must be a string")
                    continue
                if finding_id in seen_resolved:
                    errors.append(f"duplicate prior.resolved_finding_ids entry: {finding_id!r}")
                seen_resolved.add(finding_id)
                if finding_id in valid_ids:
                    errors.append(f"prior resolved finding overlaps open finding: {finding_id!r}")
    return valid_ids


def validate_review(payload, expected_artifact=None, prior=None):
    """Return human-readable validation errors for a review payload."""
    if not isinstance(payload, dict):
        return ["payload must be a dict"]

    errors = []
    for field in REQUIRED_FIELDS:
        if field not in payload:
            errors.append(f"missing required field: {field}")
    for key in _unknown_keys(payload, set(REQUIRED_FIELDS)):
        errors.append(f"unknown top-level field: {_format_key(key)}")

    artifact = payload.get("artifact")
    artifact_valid = isinstance(artifact, str) and artifact in ARTIFACTS
    if not artifact_valid:
        errors.append("artifact must be one of: code, plan, spec")
    elif expected_artifact is not None and artifact != expected_artifact:
        errors.append(
            f"artifact {artifact!r} does not match expected artifact "
            f"{expected_artifact!r}"
        )

    review_round = payload.get("round")
    round_valid = _is_integer(review_round)
    if not round_valid:
        errors.append("round must be an integer")
    elif review_round < 1:
        errors.append("round must be at least 1")

    score = payload.get("score")
    score_valid = _is_integer(score)
    if not score_valid:
        errors.append("score must be an integer")
    elif not 0 <= score <= 100:
        errors.append("score must be between 0 and 100")

    verdict = payload.get("verdict")
    if not isinstance(verdict, str) or verdict not in VERDICTS:
        errors.append("verdict must be one of: BLOCKED, PASS, REVISE")

    blockers = payload.get("blockers")
    blockers_valid = isinstance(blockers, list)
    if not blockers_valid:
        errors.append("blockers must be a list of strings")
    else:
        blocker_ids = set()
        for index, blocker_id in enumerate(blockers):
            if not isinstance(blocker_id, str):
                errors.append(f"blockers[{index}] must be a string")
            elif blocker_id in blocker_ids:
                errors.append(f"duplicate blocker ID: {blocker_id!r}")
            else:
                blocker_ids.add(blocker_id)

    findings = payload.get("findings")
    findings_valid = isinstance(findings, list)
    if not findings_valid:
        errors.append("findings must be a list of objects")

    findings_by_id = {}
    finding_ids = set()
    if findings_valid:
        for index, finding in enumerate(findings):
            prefix = f"findings[{index}]"
            if not isinstance(finding, dict):
                errors.append(f"{prefix} must be a dict")
                continue

            missing_fields = [
                field for field in FINDING_FIELDS if field not in finding
            ]
            for field in missing_fields:
                errors.append(f"{prefix} missing required field: {field}")
            for key in _unknown_keys(finding, set(FINDING_FIELDS)):
                errors.append(
                    f"{prefix} has unknown field: {_format_key(key)}"
                )

            if "id" in finding:
                finding_id = finding["id"]
                if not _is_non_empty_string(finding_id):
                    errors.append(
                        f"{prefix}.id must be a non-empty string"
                    )
                elif finding_id in finding_ids:
                    errors.append(f"duplicate finding ID: {finding_id!r}")
                else:
                    finding_ids.add(finding_id)
                if isinstance(finding_id, str):
                    findings_by_id.setdefault(finding_id, finding)

            if "severity" in finding:
                severity = finding["severity"]
                if not isinstance(severity, str) or severity not in SEVERITIES:
                    errors.append(
                        f"{prefix}.severity must be one of: "
                        "Critical, High, Low, Medium"
                    )

            for field in (
                "description",
                "evidence_location",
                "rubric_item",
                "required_resolution",
            ):
                if field in finding and not _is_non_empty_string(finding[field]):
                    errors.append(
                        f"{prefix}.{field} must be a non-empty string"
                    )

            if "new_blocker_evidence" in finding:
                new_evidence = finding["new_blocker_evidence"]
                if new_evidence is not None and not isinstance(new_evidence, str):
                    errors.append(
                        f"{prefix}.new_blocker_evidence must be a string or null"
                    )

    finding_blocker_lookup = findings_by_id
    if blockers_valid:
        for index, blocker_id in enumerate(blockers):
            if not isinstance(blocker_id, str):
                continue
            finding = finding_blocker_lookup.get(blocker_id)
            if finding is None:
                errors.append(
                    f"blockers[{index}] does not resolve to a finding: "
                    f"{blocker_id!r}"
                )
            elif (
                not isinstance(finding.get("severity"), str)
                or finding["severity"] not in HARD_SEVERITIES
            ):
                errors.append(
                    f"blocker {blocker_id!r} must resolve to a Critical or "
                    "High finding"
                )

    evidence = payload.get("evidence")
    evidence_valid = isinstance(evidence, list)
    if not evidence_valid:
        errors.append("evidence must be a list of objects")
    else:
        seen_evidence = []
        for index, item in enumerate(evidence):
            prefix = f"evidence[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} must be a dict")
                continue

            for field in EVIDENCE_FIELDS:
                if field not in item:
                    errors.append(f"{prefix} missing required field: {field}")
            for key in _unknown_keys(item, set(EVIDENCE_FIELDS)):
                errors.append(f"{prefix} has unknown field: {_format_key(key)}")

            for field in EVIDENCE_STRING_FIELDS:
                if field in item and not _is_non_empty_string(item[field]):
                    errors.append(
                        f"{prefix}.{field} must be a non-empty string"
                    )
            if "verified" in item and not isinstance(item["verified"], bool):
                errors.append(f"{prefix}.verified must be a boolean")

            if item in seen_evidence:
                errors.append(f"duplicate evidence entry at {prefix}")
            else:
                seen_evidence.append(item)

    required_next_action = payload.get("required_next_action")
    if required_next_action is not None and not isinstance(required_next_action, str):
        errors.append("required_next_action must be a string or null")

    if verdict == "PASS":
        if "required_next_action" in payload and required_next_action is not None:
            errors.append("PASS reviews must have no required_next_action")
        if evidence_valid and any(
            item.get("verified") is False for item in evidence if isinstance(item, dict)
        ):
            errors.append("PASS reviews must not contain unverified evidence")

    if round_valid and review_round >= 2:
        if prior is None:
            errors.append("prior is required for round >= 2")
            prior_ids = []
        else:
            prior_ids = _prior_open_finding_ids(prior, errors)
        if blockers_valid:
            for index, blocker_id in enumerate(blockers):
                if not isinstance(blocker_id, str) or blocker_id in prior_ids:
                    continue
                finding = finding_blocker_lookup.get(blocker_id)
                if finding is None:
                    continue
                if not _is_non_empty_string(finding.get("new_blocker_evidence")):
                    errors.append(
                        f"new blocker {blocker_id!r} at blockers[{index}] requires "
                        "non-empty new_blocker_evidence"
                    )

    return errors


def evaluate_gate(payload, checks, expected_artifact=None, prior=None):
    """Validate a review and return its deterministic gate decision."""
    errors = validate_review(payload, expected_artifact, prior)
    if errors:
        raise ValueError("; ".join(errors))
    if not isinstance(checks, dict):
        raise ValueError("checks must be a dict of booleans")

    check_errors = []
    for key, value in checks.items():
        if not isinstance(value, bool):
            check_errors.append(f"check {key!r} must be a boolean")
    if check_errors:
        raise ValueError("; ".join(check_errors))

    artifact = payload["artifact"]
    reasons = []
    if artifact in {"spec", "plan"} and payload["score"] < SCORE_THRESHOLD:
        reasons.append(f"score_below_{SCORE_THRESHOLD}")
    if payload["verdict"] != "PASS":
        reasons.append("verdict_not_pass")
    if payload["blockers"]:
        reasons.append("blockers_present")
    if any(
        finding["severity"] in HARD_SEVERITIES
        for finding in payload["findings"]
    ):
        reasons.append("critical_or_high_finding")

    for key in sorted(REQUIRED_CHECKS[artifact]):
        if key not in checks:
            reasons.append(f"missing_check:{key}")
        elif not checks[key]:
            if key == "required_commands_passed":
                reasons.append("required_commands_failed")
            else:
                reasons.append(f"check_failed:{key}")

    return {
        "passed": len(reasons) == 0,
        "artifact": artifact,
        "reasons": reasons,
    }


def _load_json(path, label):
    try:
        with Path(path).open(encoding="utf-8") as stream:
            return json.load(stream)
    except OSError as exc:
        raise ValueError(f"unable to read {label} {path!s}: {exc}") from exc
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON in {label} {path!s}: {exc}") from exc


def _write_json(value):
    json.dump(value, sys.stdout, separators=(",", ":"))
    sys.stdout.write("\n")


def _write_diagnostic(error):
    print(f"error: {error}", file=sys.stderr)


def _build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--input", required=True, dest="input_path")
    validate_parser.add_argument(
        "--artifact",
        choices=sorted(ARTIFACTS),
        default=None,
    )
    validate_parser.add_argument("--prior", dest="prior_path")

    gate_parser = subparsers.add_parser("gate")
    gate_parser.add_argument("--input", required=True, dest="input_path")
    gate_parser.add_argument("--checks", required=True, dest="checks_path")
    gate_parser.add_argument(
        "--artifact",
        choices=sorted(ARTIFACTS),
        default=None,
    )
    gate_parser.add_argument("--prior", dest="prior_path")
    return parser


def _run_validate(args):
    try:
        payload = _load_json(args.input_path, "review input")
        prior = None
        if args.prior_path is not None:
            prior = _load_json(args.prior_path, "prior input")
        errors = validate_review(payload, args.artifact, prior)
    except ValueError as exc:
        _write_diagnostic(exc)
        _write_json({"valid": False, "errors": [str(exc)]})
        return 2

    _write_json({"valid": not errors, "errors": errors})
    return 0 if not errors else 2


def _run_gate(args):
    review = None
    try:
        review = _load_json(args.input_path, "review input")
        checks = _load_json(args.checks_path, "checks input")
        prior = None
        if args.prior_path is not None:
            prior = _load_json(args.prior_path, "prior input")
        decision = evaluate_gate(review, checks, args.artifact, prior)
    except ValueError as exc:
        _write_diagnostic(exc)
        artifact = None
        if isinstance(review, dict) and isinstance(review.get("artifact"), str):
            artifact = review["artifact"]
        _write_json({"passed": False, "artifact": artifact, "errors": [str(exc)]})
        return 2

    _write_json(decision)
    return 0 if decision["passed"] else 3


def main(argv=None):
    """Run the review validator or gate CLI."""
    args = _build_parser().parse_args(argv)
    if args.command == "validate":
        return _run_validate(args)
    return _run_gate(args)


if __name__ == "__main__":
    raise SystemExit(main())
