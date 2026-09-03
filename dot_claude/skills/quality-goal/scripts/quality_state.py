"""State machine and deterministic helpers for the quality-goal workflow."""

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import unicodedata

from validate_review import validate_review


ALLOWED_TRANSITIONS = {
    "INTAKE": {"CLASSIFIED", "BLOCKED", "CANCELLED"},
    "CLASSIFIED": {
        "SPEC_REVIEW",
        "AWAITING_PLAN_APPROVAL",
        "BLOCKED",
        "CANCELLED",
    },
    "SPEC_REVIEW": {
        "SPEC_PASSED",
        "NEEDS_REDESIGN",
        "BLOCKED",
        "CANCELLED",
    },
    "SPEC_PASSED": {"PLAN_REVIEW", "BLOCKED", "CANCELLED"},
    "PLAN_REVIEW": {
        "PLAN_PASSED",
        "NEEDS_REDESIGN",
        "BLOCKED",
        "CANCELLED",
    },
    "PLAN_PASSED": {"AWAITING_PLAN_APPROVAL", "BLOCKED", "CANCELLED"},
    "AWAITING_PLAN_APPROVAL": {
        "IMPLEMENTING",
        "SPEC_REVIEW",
        "PLAN_REVIEW",
        "BLOCKED",
        "CANCELLED",
    },
    "IMPLEMENTING": {
        "CODE_REVIEW",
        "SPEC_REVIEW",
        "PLAN_REVIEW",
        "NEEDS_REDESIGN",
        "BLOCKED",
        "CANCELLED",
    },
    "CODE_REVIEW": {
        "IMPLEMENTING",
        "COMPLETED",
        "SPEC_REVIEW",
        "PLAN_REVIEW",
        "NEEDS_REDESIGN",
        "BLOCKED",
        "CANCELLED",
    },
}

TERMINAL_STATES = {"COMPLETED", "BLOCKED", "NEEDS_REDESIGN", "CANCELLED"}
ROUND_LIMITS = {"spec": 3, "plan": 2, "code": 3}

_REQUESTED_MODES = {"auto", "light", "standard", "strict"}
_CLASSIFIED_MODES = {"light", "standard", "strict"}
_ARTIFACT_KEYS = {"spec", "plan", "compact_plan", "report"}
STATE_DIR_RELATIVE = ".claude/quality-state"
_REVIEW_STAGES = {
    "spec": "SPEC_REVIEW",
    "plan": "PLAN_REVIEW",
    "code": "CODE_REVIEW",
}


class StateError(Exception):
    """Base error for invalid quality-goal state or input data."""


class TransitionError(StateError):
    """An invalid state-machine edge or bounded-loop condition."""


class ApprovalMismatchError(TransitionError):
    """The approved plan no longer matches the current plan artifact."""


class GitError(StateError):
    """The workspace cannot be fingerprinted as a usable Git repository."""


class FilesystemError(StateError):
    """A filesystem operation prevented an atomic state update."""


def _require_state(state):
    if not isinstance(state, dict):
        raise StateError("state must be a dict")
    return state


def _require_active(state):
    state = _require_state(state)
    stage = state.get("stage")
    if isinstance(stage, str) and stage in TERMINAL_STATES:
        raise TransitionError(f"terminal state is immutable: {stage}")
    return state


def _timestamp(value=None):
    if value is None:
        value = datetime.now(timezone.utc)
    if not isinstance(value, datetime):
        raise StateError("timestamp must be an aware datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise StateError("timestamp must be an aware datetime")
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _now_timestamp():
    return _timestamp()


def normalize_goal(goal):
    """Normalize a goal for matching and stable identifiers."""
    if not isinstance(goal, str):
        raise StateError("goal must be a string")
    normalized = unicodedata.normalize("NFKC", goal)
    return " ".join(normalized.split()).casefold()


def goal_key(goal):
    """Return the SHA-256 key for a normalized goal."""
    return hashlib.sha256(normalize_goal(goal).encode("utf-8")).hexdigest()


def _goal_slug(normalized_goal):
    slug = re.sub(r"[^\w]+", "-", normalized_goal, flags=re.UNICODE)
    slug = slug.strip("-")[:40].strip("-")
    return slug or "goal"


def new_state(
    goal,
    requested_mode,
    project_root,
    artifact_dir,
    task_id=None,
    now=None,
):
    """Create a schema-version-one state at the INTAKE stage."""
    if not isinstance(requested_mode, str) or requested_mode not in _REQUESTED_MODES:
        raise StateError(f"invalid requested mode: {requested_mode!r}")
    if not isinstance(goal, str) or not goal.strip():
        raise StateError("goal must not be empty")
    if not isinstance(artifact_dir, (str, os.PathLike)):
        raise StateError("artifact_dir must be a string or PathLike")
    artifact_dir = str(artifact_dir)
    if not artifact_dir:
        raise StateError("artifact_dir must not be empty")

    normalized_goal = normalize_goal(goal)
    timestamp = _timestamp(now)
    if task_id is None:
        timestamp_compact = timestamp.replace("-", "").replace(":", "")
        task_id = (
            f"{timestamp_compact}-{_goal_slug(normalized_goal)}-"
            f"{goal_key(goal)[:8]}"
        )
    elif not isinstance(task_id, str) or not task_id:
        raise StateError("task_id must be a non-empty string")

    return {
        "schema_version": 1,
        "task_id": task_id,
        "goal": goal,
        "goal_key": goal_key(goal),
        "requested_mode": requested_mode,
        "mode": None,
        "classification_reasons": [],
        "stage": "INTAKE",
        "project_root": str(Path(project_root).resolve()),
        "artifact_dir": artifact_dir,
        "base_revision": None,
        "initial_dirty_paths": [],
        "artifacts": {
            "spec": None,
            "plan": None,
            "compact_plan": None,
            "report": None,
        },
        "artifact_digests": {
            "spec": None,
            "plan": None,
            "compact_plan": None,
            "report": None,
        },
        "rounds": {"spec": 0, "plan": 0, "code": 0},
        "reviews": {"spec": [], "plan": [], "code": []},
        "open_finding_ids": {"spec": [], "plan": [], "code": []},
        "review_validation_retry": None,
        "review_unverified_retry": None,
        "plan_approval": None,
        "verification": {
            "path": None,
            "workspace_fingerprint": None,
            "valid": False,
        },
        "status_reason": None,
        "created_at": timestamp,
        "updated_at": timestamp,
    }


def save_state(path, state):
    """Atomically write state JSON beside the destination and replace it."""
    destination = Path(path)
    temporary_path = None
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(destination.parent),
            delete=False,
        ) as temporary:
            temporary_path = temporary.name
            json.dump(state, temporary, ensure_ascii=False, indent=2)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, destination)
    except (TypeError, ValueError, UnicodeError) as exc:
        raise StateError(f"state is not JSON serializable: {exc}") from exc
    except OSError as exc:
        raise FilesystemError(f"unable to save state {destination}: {exc}") from exc
    finally:
        if temporary_path is not None:
            try:
                Path(temporary_path).unlink()
            except FileNotFoundError:
                pass
            except OSError:
                pass


def load_state(path):
    """Load a JSON object from a state path."""
    source = Path(path)
    try:
        with source.open(encoding="utf-8") as stream:
            value = json.load(stream)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise StateError(f"unable to load state {source}: {exc}") from exc
    if not isinstance(value, dict):
        raise StateError(f"state {source} must contain a JSON object")
    if type(value.get("schema_version")) is not int or value["schema_version"] != 1:
        raise StateError(f"state {source} must have schema_version 1")
    return value


def classify(state, mode, reasons):
    """Classify an INTAKE state and move it to CLASSIFIED."""
    state = _require_state(state)
    if state.get("stage") != "INTAKE":
        raise StateError("only INTAKE states can be classified")
    if not isinstance(mode, str) or mode not in _CLASSIFIED_MODES:
        raise StateError(f"invalid classification mode: {mode!r}")
    if (
        not isinstance(reasons, list)
        or not reasons
        or any(not isinstance(reason, str) or not reason.strip() for reason in reasons)
    ):
        raise StateError("classification reasons must be non-empty strings")

    state["mode"] = mode
    state["classification_reasons"] = list(reasons)
    state["stage"] = "CLASSIFIED"
    state["updated_at"] = _now_timestamp()
    return state


def set_artifact(state, kind, path):
    """Bind an existing regular file to one of the workflow artifacts."""
    state = _require_active(state)
    if not isinstance(kind, str) or kind not in _ARTIFACT_KEYS:
        raise StateError(f"invalid artifact kind: {kind!r}")
    if (
        not isinstance(path, (str, os.PathLike))
        or not str(path).strip()
    ):
        raise StateError("artifact path must be a non-empty string or PathLike")

    try:
        artifact_path = Path(path)
        is_regular_file = artifact_path.is_file()
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        raise StateError(f"artifact path is not a regular file: {path!s}") from exc
    if not is_regular_file:
        raise StateError(f"artifact path is not a regular file: {path!s}")

    artifacts = state.get("artifacts")
    if not isinstance(artifacts, dict):
        raise StateError("artifacts must be an object")
    artifacts[kind] = str(path)
    state["updated_at"] = _now_timestamp()
    return state


def _file_digest(path):
    try:
        contents = Path(path).read_bytes()
    except (OSError, UnicodeError, TypeError) as exc:
        raise StateError(f"unable to read file {path!s}: {exc}") from exc
    return hashlib.sha256(contents).hexdigest()


def _mode_appropriate_artifact(state):
    mode = state.get("mode")
    if not isinstance(mode, str) or mode not in _CLASSIFIED_MODES:
        raise StateError("a classified mode is required before implementation")
    artifact_key = "compact_plan" if mode == "light" else "plan"
    artifacts = state.get("artifacts")
    if not isinstance(artifacts, dict):
        raise StateError("artifacts must be an object")
    return artifact_key, artifacts.get(artifact_key)


def _resolved_path(value):
    if not isinstance(value, (str, os.PathLike)) or not str(value).strip():
        return None
    try:
        return Path(value).resolve()
    except (OSError, RuntimeError, TypeError):
        return None


def _raise_plan_approval_mismatch(state, message, cause=None):
    verification = state.get("verification")
    if not isinstance(verification, dict):
        raise StateError("verification must be an object")
    state["plan_approval"] = None
    verification["valid"] = False
    state["stage"] = "CLASSIFIED" if state["mode"] == "light" else "PLAN_REVIEW"
    state["updated_at"] = _now_timestamp()
    error = ApprovalMismatchError(message)
    if cause is None:
        raise error
    raise error from cause


def _validate_transition_request(state, target, reason):
    current = state.get("stage")
    if not isinstance(current, str) or current not in ALLOWED_TRANSITIONS:
        raise TransitionError(f"state at {current!r} has no outgoing transitions")
    if not isinstance(target, str):
        raise TransitionError(f"invalid transition target: {target!r}")
    if target == "CLASSIFIED":
        raise TransitionError("CLASSIFIED can only be reached through classify")
    if target not in ALLOWED_TRANSITIONS[current]:
        raise TransitionError(f"invalid transition: {current} -> {target}")
    if target in {"BLOCKED", "NEEDS_REDESIGN", "CANCELLED"}:
        if not isinstance(reason, str) or not reason.strip():
            raise StateError(f"a reason is required to enter {target}")
    if current == "CLASSIFIED" and target == "AWAITING_PLAN_APPROVAL":
        if state.get("mode") != "light":
            raise TransitionError(
                "CLASSIFIED -> AWAITING_PLAN_APPROVAL requires light mode"
            )
    if current == "CLASSIFIED" and target == "SPEC_REVIEW":
        if state.get("mode") not in {"standard", "strict"}:
            raise TransitionError(
                "CLASSIFIED -> SPEC_REVIEW requires standard or strict mode"
            )
    if (current, target) in {
        ("SPEC_REVIEW", "SPEC_PASSED"),
        ("PLAN_REVIEW", "PLAN_PASSED"),
    }:
        artifact = "spec" if current == "SPEC_REVIEW" else "plan"
        # Light carries no reviewer round for its compact Plan, so its
        # documented IMPLEMENTING -> PLAN_REVIEW -> PLAN_PASSED rework path
        # has no review to require.
        if not (artifact == "plan" and state.get("mode") == "light"):
            rounds = state.get("rounds")
            reviews = state.get("reviews")
            open_finding_ids = state.get("open_finding_ids")
            artifact_reviews = (
                reviews.get(artifact) if isinstance(reviews, dict) else None
            )
            last_review = (
                artifact_reviews[-1]
                if isinstance(artifact_reviews, list) and artifact_reviews
                else None
            )
            if (
                not isinstance(rounds, dict)
                or not isinstance(rounds.get(artifact), int)
                or isinstance(rounds.get(artifact), bool)
                or rounds[artifact] < 1
                or not isinstance(last_review, dict)
                or last_review.get("verdict") != "PASS"
                or last_review.get("blockers") != []
                or not isinstance(open_finding_ids, dict)
                or open_finding_ids.get(artifact) != []
            ):
                raise TransitionError(
                    f"{current} -> {target} requires a passing final "
                    f"{artifact} review with no open findings"
                )
    if current == "CODE_REVIEW" and target == "COMPLETED":
        rounds = state.get("rounds")
        reviews = state.get("reviews")
        open_finding_ids = state.get("open_finding_ids")
        verification = state.get("verification")
        code_reviews = reviews.get("code") if isinstance(reviews, dict) else None
        last_review = code_reviews[-1] if isinstance(code_reviews, list) and code_reviews else None
        reviewed_digest = (
            last_review.get("artifact_digest")
            if isinstance(last_review, dict)
            else None
        )
        verified_fingerprint = (
            verification.get("workspace_fingerprint")
            if isinstance(verification, dict)
            else None
        )
        if (
            not isinstance(rounds, dict)
            or not isinstance(rounds.get("code"), int)
            or isinstance(rounds.get("code"), bool)
            or rounds["code"] < 1
            or not isinstance(last_review, dict)
            or last_review.get("verdict") != "PASS"
            or last_review.get("blockers") != []
            or not isinstance(open_finding_ids, dict)
            or open_finding_ids.get("code") != []
            or not isinstance(verification, dict)
            or verification.get("valid") is not True
            or not isinstance(reviewed_digest, str)
            or not reviewed_digest
            or reviewed_digest != verified_fingerprint
        ):
            raise TransitionError(
                "CODE_REVIEW -> COMPLETED requires a passing final review, "
                "no open findings, and verification tied to the reviewed "
                "code state"
            )


def _validate_implementing_guard(state):
    mode = state.get("mode")
    if not isinstance(mode, str) or mode not in _CLASSIFIED_MODES:
        raise StateError("a classified mode is required before implementation")

    approval = state.get("plan_approval")
    if approval is None:
        raise TransitionError("current plan approval is required for IMPLEMENTING")
    if not isinstance(approval, dict):
        raise StateError("plan_approval must be an object")
    approval_path = approval.get("path")
    approved_digest = approval.get("digest")
    if not isinstance(approval_path, str) or not approval_path.strip():
        raise StateError("plan_approval.path must be a non-empty string")
    if not isinstance(approved_digest, str) or not approved_digest:
        raise StateError("plan_approval.digest must be a non-empty string")

    _, current_artifact_path = _mode_appropriate_artifact(state)
    if (
        _resolved_path(approval_path) is None
        or _resolved_path(current_artifact_path) is None
        or _resolved_path(approval_path) != _resolved_path(current_artifact_path)
    ):
        _raise_plan_approval_mismatch(state, "approved plan path mismatch")

    try:
        current_digest = _file_digest(approval_path)
    except StateError as exc:
        _raise_plan_approval_mismatch(
            state,
            "approved plan digest mismatch: approved file is missing or unreadable",
            exc,
        )
    if current_digest != approved_digest:
        _raise_plan_approval_mismatch(state, "approved plan digest mismatch")


def transition(state, target, reason=None):
    """Validate and apply one allowed state-machine transition."""
    state = _require_state(state)
    _validate_transition_request(state, target, reason)
    if target == "IMPLEMENTING":
        _validate_implementing_guard(state)

    state["stage"] = target
    if target in {"BLOCKED", "NEEDS_REDESIGN", "CANCELLED"}:
        state["status_reason"] = reason
    state["updated_at"] = _now_timestamp()
    return state


def approve_plan(state, plan_path, approved_at):
    """Record the digest and timestamp of the user-approved plan."""
    state = _require_state(state)
    if state.get("stage") != "AWAITING_PLAN_APPROVAL":
        raise StateError("plan approval is only valid at AWAITING_PLAN_APPROVAL")
    if (
        not isinstance(approved_at, str)
        or re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", approved_at)
        is None
    ):
        raise StateError("approved_at must be an RFC3339 UTC timestamp")
    artifact_key, artifact_path = _mode_appropriate_artifact(state)
    if _resolved_path(artifact_path) is None:
        raise StateError("the mode-appropriate plan artifact must be set")
    if _resolved_path(plan_path) != _resolved_path(artifact_path):
        raise StateError("plan approval path must match the current plan artifact")
    digest = _file_digest(plan_path)
    if artifact_key == "plan":
        artifact_digests = state.get("artifact_digests")
        reviewed_digest = (
            artifact_digests.get("plan")
            if isinstance(artifact_digests, dict)
            else None
        )
        if not isinstance(reviewed_digest, str) or not reviewed_digest:
            raise StateError(
                "the plan must have a recorded passing review digest "
                "before approval"
            )
        if digest != reviewed_digest:
            raise StateError(
                "plan approval content does not match the reviewed plan "
                "digest"
            )
    state["plan_approval"] = {
        "path": str(plan_path),
        "digest": digest,
        "approved_at": approved_at,
    }
    state["updated_at"] = _now_timestamp()
    return state


def _load_review(path):
    source = Path(path)
    try:
        with source.open(encoding="utf-8") as stream:
            review = json.load(stream)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise StateError(f"unable to load review {source}: {exc}") from exc
    if not isinstance(review, dict):
        raise StateError(f"review {source} must contain a JSON object")
    return review


def record_review(state, review_path, artifact_digest):
    """Validate and record one review round for the current artifact stage."""
    state = _require_state(state)
    if (
        not isinstance(artifact_digest, str)
        or re.fullmatch(r"[0-9a-f]{64}", artifact_digest) is None
    ):
        raise StateError("artifact_digest must be a lowercase SHA-256 hexdigest")
    review = _load_review(review_path)
    artifact = review.get("artifact")
    expected_stage = _REVIEW_STAGES.get(artifact) if isinstance(artifact, str) else None
    if expected_stage is None:
        raise StateError(f"unknown review artifact: {artifact!r}")
    if state.get("stage") != expected_stage:
        raise StateError(
            f"review for {artifact} requires stage {expected_stage}, "
            f"got {state.get('stage')}"
        )

    rounds = state.get("rounds")
    if not isinstance(rounds, dict) or not isinstance(rounds.get(artifact), int):
        raise StateError(f"state rounds missing {artifact}")
    expected_round = rounds[artifact] + 1

    retry = state.get("review_unverified_retry")
    if isinstance(retry, dict) and retry.get("artifact") == artifact and retry.get("round") == expected_round:
        if retry.get("artifact_digest") != artifact_digest:
            raise StateError("unverified review retry artifact digest mismatch")

    if artifact in {"spec", "plan"}:
        artifacts = state.get("artifacts")
        if not isinstance(artifacts, dict):
            raise StateError("state artifacts storage is malformed")
        artifact_path = artifacts.get(artifact)
        if artifact_path is not None and _file_digest(artifact_path) != artifact_digest:
            raise StateError(f"{artifact} artifact digest mismatch")

    if review.get("round") != expected_round:
        raise StateError(
            f"review round must be {expected_round}, got {review.get('round')!r}"
        )
    if expected_round > ROUND_LIMITS[artifact]:
        raise TransitionError(f"review round limit exhausted for {artifact}")

    prior = None
    if expected_round >= 2:
        open_finding_ids = state.get("open_finding_ids")
        if (
            not isinstance(open_finding_ids, dict)
            or not isinstance(open_finding_ids.get(artifact), list)
        ):
            raise StateError(f"state open_finding_ids missing {artifact}")
        prior = {"open_finding_ids": list(open_finding_ids[artifact])}
    try:
        validation_errors = validate_review(
            review,
            expected_artifact=artifact,
            prior=prior,
        )
    except Exception as exc:
        raise StateError(f"review validation failed: {exc}") from exc
    if validation_errors:
        message = "; ".join(str(error) for error in validation_errors)
        raise StateError(f"review validation failed: {message}")

    reviews = state.get("reviews")
    open_finding_ids = state.get("open_finding_ids")
    artifact_digests = state.get("artifact_digests")
    if (
        not isinstance(reviews, dict)
        or not isinstance(reviews.get(artifact), list)
        or not isinstance(open_finding_ids, dict)
        or not isinstance(artifact_digests, dict)
    ):
        raise StateError("state review storage is malformed")

    earlier_blockers = {
        blocker
        for recorded_review in reviews[artifact]
        if isinstance(recorded_review, dict)
        for blocker in recorded_review.get("blockers", [])
    }
    blockers = list(review["blockers"])
    verdict = review["verdict"]
    recorded_review = {
        "round": review["round"],
        "path": str(review_path),
        "artifact_digest": artifact_digest,
        "verdict": verdict,
        "blockers": blockers,
    }

    rounds[artifact] = expected_round
    reviews[artifact].append(recorded_review)
    open_finding_ids[artifact] = list(blockers)
    artifact_digests[artifact] = artifact_digest
    state["review_validation_retry"] = None
    state["review_unverified_retry"] = None
    state["updated_at"] = _now_timestamp()

    recurring = next((blocker for blocker in blockers if blocker in earlier_blockers), None)
    if recurring is not None:
        state["stage"] = "NEEDS_REDESIGN"
        state["status_reason"] = f"RECURRING_BLOCKING_FINDING:{recurring}"
    elif expected_round == ROUND_LIMITS[artifact] and (
        verdict != "PASS" or blockers
    ):
        state["stage"] = "NEEDS_REDESIGN"
        state["status_reason"] = f"REVIEW_LIMIT_EXHAUSTED:{artifact}"
    return state


def record_review_unverified(state, review_path, artifact_digest):
    """Record a bounded no-round-cost retry for unverified REVISE evidence."""
    state = _require_state(state)
    if not isinstance(artifact_digest, str) or re.fullmatch(r"[0-9a-f]{64}", artifact_digest) is None:
        raise StateError("artifact_digest must be a lowercase SHA-256 hexdigest")
    review = _load_review(review_path)
    artifact = review.get("artifact")
    expected_stage = _REVIEW_STAGES.get(artifact) if isinstance(artifact, str) else None
    if expected_stage is None:
        raise StateError(f"unknown review artifact: {artifact!r}")
    if state.get("stage") != expected_stage:
        raise StateError(f"review for {artifact} requires stage {expected_stage}, got {state.get('stage')}")
    if artifact in {"spec", "plan"}:
        artifacts = state.get("artifacts")
        if not isinstance(artifacts, dict):
            raise StateError("state artifacts storage is malformed")
        artifact_path = artifacts.get(artifact)
        if artifact_path is not None and _file_digest(artifact_path) != artifact_digest:
            raise StateError(f"{artifact} artifact digest mismatch")
    rounds = state.get("rounds")
    if not isinstance(rounds, dict) or not isinstance(rounds.get(artifact), int):
        raise StateError(f"state rounds missing {artifact}")
    expected_round = rounds[artifact] + 1
    if review.get("round") != expected_round:
        raise StateError(f"review round must be {expected_round}, got {review.get('round')!r}")
    if expected_round > ROUND_LIMITS[artifact]:
        raise TransitionError(f"review round limit exhausted for {artifact}")
    prior = None
    if expected_round >= 2:
        open_finding_ids = state.get("open_finding_ids")
        if not isinstance(open_finding_ids, dict) or not isinstance(open_finding_ids.get(artifact), list):
            raise StateError(f"state open_finding_ids missing {artifact}")
        prior = {"open_finding_ids": list(open_finding_ids[artifact])}
    validation_errors = validate_review(review, expected_artifact=artifact, prior=prior)
    if validation_errors:
        raise StateError(f"review validation failed: {'; '.join(str(error) for error in validation_errors)}")
    if not (review["verdict"] == "REVISE" and not review["blockers"] and any(item.get("verified") is False for item in review["evidence"])):
        raise StateError("review is not an unverified REVISE")
    retry = state.get("review_unverified_retry")
    if isinstance(retry, dict) and retry.get("artifact") == artifact and retry.get("round") == expected_round:
        if retry.get("artifact_digest") != artifact_digest:
            raise StateError("unverified review retry artifact digest mismatch")
        if retry.get("attempts") == 2:
            raise TransitionError("REVIEWER_UNVERIFIED_PERSISTS")
        attempts = 2
        exhausted = True
        claims = list(retry.get("unverified_claims", []))
        paths = list(retry.get("discarded_reviews", []))
    else:
        attempts = 1
        exhausted = False
        claims = []
        paths = []
    claims.extend(item["claim"] for item in review["evidence"] if item.get("verified") is False)
    paths.append(str(review_path))
    state["review_unverified_retry"] = {
        "artifact": artifact, "round": expected_round, "attempts": attempts,
        "exhausted": exhausted, "artifact_digest": artifact_digest,
        "unverified_claims": claims, "discarded_reviews": paths,
    }
    state["updated_at"] = _now_timestamp()
    return state


def record_review_validation_failure(state, artifact, round_number, errors):
    """Record one malformed review response, blocking after the retry."""
    state = _require_active(state)
    if not isinstance(artifact, str) or artifact not in ROUND_LIMITS:
        raise StateError(f"unknown review artifact: {artifact!r}")
    if state.get("stage") != _REVIEW_STAGES[artifact]:
        raise StateError(
            f"review validation failure for {artifact} requires stage "
            f"{_REVIEW_STAGES[artifact]}"
        )
    if type(round_number) is not int or not 1 <= round_number <= ROUND_LIMITS[artifact]:
        raise StateError(
            f"review round must be an integer from 1 to {ROUND_LIMITS[artifact]}"
        )
    if (
        not isinstance(errors, list)
        or not errors
        or any(not isinstance(error, str) or not error.strip() for error in errors)
    ):
        raise StateError("review validation errors must be non-empty strings")
    retry = state.get("review_validation_retry")
    if (
        isinstance(retry, dict)
        and retry.get("artifact") == artifact
        and retry.get("round") == round_number
    ):
        state["review_validation_retry"] = {
            "artifact": artifact,
            "round": round_number,
            "attempts": 2,
            "errors": list(errors),
        }
        state["stage"] = "BLOCKED"
        state["status_reason"] = "REVIEW_OUTPUT_INVALID"
    else:
        state["review_validation_retry"] = {
            "artifact": artifact,
            "round": round_number,
            "attempts": 1,
            "errors": list(errors),
        }
    state["updated_at"] = _now_timestamp()
    return state


def _git_run(project_root, *arguments):
    command = ["git", "-C", str(project_root), *arguments]
    try:
        result = subprocess.run(command, capture_output=True)
    except OSError as exc:
        raise GitError(f"BLOCKED_NOT_GIT: {exc}") from exc
    if result.returncode != 0:
        stderr = result.stderr
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        raise GitError(f"BLOCKED_NOT_GIT: {stderr}")
    return result.stdout


def _frame(digest, label: str, payload: bytes):
    digest.update(f"{label}:{len(payload)}:".encode("utf-8"))
    digest.update(payload)


def _filesystem_error(path, exc):
    return FilesystemError(f"unable to read untracked path {path!s}: {exc}")


def _is_state_path(relative_path):
    return relative_path == STATE_DIR_RELATIVE or relative_path.startswith(
        f"{STATE_DIR_RELATIVE}/"
    )


def _warn_for_nonstandard_state_root(state_root, project_root):
    resolved_state_root = Path(state_root).resolve()
    resolved_project_root = Path(project_root).resolve()
    canonical_state_root = resolved_project_root / STATE_DIR_RELATIVE
    try:
        resolved_state_root.relative_to(resolved_project_root)
    except ValueError:
        return
    if resolved_state_root == canonical_state_root:
        return
    print(
        f"warning: --root {resolved_state_root} resolves inside the project root "
        f"but is not the canonical state root {canonical_state_root}; state files "
        "re-enter the workspace fingerprint.",
        file=sys.stderr,
    )


def _read_untracked_value(digest, path, relative_path, include_path=True):
    relative_bytes = os.fsencode(relative_path)
    if include_path:
        _frame(digest, "path", relative_bytes)
    try:
        file_stat = os.lstat(path)
    except (OSError, UnicodeError, TypeError) as exc:
        raise _filesystem_error(path, exc) from exc

    if stat.S_ISLNK(file_stat.st_mode):
        try:
            link_target = os.readlink(path)
        except (OSError, UnicodeError, TypeError) as exc:
            raise _filesystem_error(path, exc) from exc
        _frame(digest, "symlink", os.fsencode(link_target))
    elif stat.S_ISREG(file_stat.st_mode):
        try:
            contents = Path(path).read_bytes()
        except (OSError, UnicodeError, TypeError) as exc:
            raise _filesystem_error(path, exc) from exc
        _frame(digest, "file", contents)
    else:
        _frame(digest, "special", b"")


def _walk_untracked_directory(digest, root, relative_path):
    top = root / relative_path

    def onerror(error):
        path = error.filename or top
        raise _filesystem_error(path, error)

    for current, dirnames, filenames in os.walk(
        top,
        followlinks=False,
        onerror=onerror,
    ):
        dirnames.sort()
        filenames.sort()
        symlink_directories = []
        for dirname in list(dirnames):
            path = Path(current) / dirname
            relative = os.path.relpath(path, root)
            if _is_state_path(relative):
                dirnames.remove(dirname)
                continue
            try:
                file_stat = os.lstat(path)
            except (OSError, UnicodeError, TypeError) as exc:
                raise _filesystem_error(path, exc) from exc
            if stat.S_ISLNK(file_stat.st_mode):
                dirnames.remove(dirname)
                symlink_directories.append(path)
        for path in symlink_directories:
            relative = os.path.relpath(path, root)
            if _is_state_path(relative):
                continue
            _read_untracked_value(digest, path, relative)
        for filename in filenames:
            path = Path(current) / filename
            relative = os.path.relpath(path, root)
            if _is_state_path(relative):
                continue
            _read_untracked_value(digest, path, relative)


def _status_paths(status_output):
    paths = []
    entries = status_output.split(b"\0")
    index = 0
    while index < len(entries):
        entry = entries[index]
        index += 1
        if not entry:
            continue
        status = entry[:2]
        path = entry[3:]
        if b"R" in status or b"C" in status:
            if index < len(entries) and entries[index]:
                index += 1
        if path:
            paths.append(os.fsdecode(path))
    return sorted(paths)


def capture_workspace_baseline(state):
    """Capture the committed revision and dirty paths at workflow start."""
    state = _require_active(state)
    if state.get("stage") not in {"INTAKE", "CLASSIFIED"}:
        raise TransitionError(
            "workspace baseline capture is only valid at INTAKE or CLASSIFIED"
        )
    project_root = state.get("project_root")
    base_revision = os.fsdecode(_git_run(project_root, "rev-parse", "HEAD")).strip()
    dirty_paths = _status_paths(_git_run(project_root, "status", "--porcelain", "-z"))
    state["base_revision"] = base_revision
    state["initial_dirty_paths"] = dirty_paths
    state["updated_at"] = _now_timestamp()
    return state


def compute_workspace_fingerprint(project_root):
    """Hash Git HEAD, tracked diffs, and sorted untracked file contents."""
    root = Path(project_root)
    digest = hashlib.sha256()
    try:
        head = _git_run(root, "rev-parse", "HEAD")
    except GitError as exc:
        try:
            inside_work_tree = _git_run(root, "rev-parse", "--is-inside-work-tree")
        except GitError:
            raise
        if os.fsdecode(inside_work_tree).strip() != "true":
            raise
        raise GitError("BLOCKED_NOT_GIT: repository has no commit") from exc
    _frame(digest, "head", head)
    _frame(
        digest,
        "diff",
        _git_run(
            root,
            "diff",
            "--binary",
            "--no-ext-diff",
            "HEAD",
            "--",
            f":(exclude){STATE_DIR_RELATIVE}",
        ),
    )
    _frame(
        digest,
        "cached-diff",
        _git_run(
            root,
            "diff",
            "--cached",
            "--binary",
            "--no-ext-diff",
            "HEAD",
            "--",
            f":(exclude){STATE_DIR_RELATIVE}",
        ),
    )
    untracked_output = _git_run(
        root,
        "ls-files",
        "--others",
        "--exclude-standard",
        "-z",
        "--",
        f":(exclude){STATE_DIR_RELATIVE}",
    )
    untracked_paths = sorted(
        path_bytes for path_bytes in untracked_output.split(b"\0") if path_bytes
    )
    for path_bytes in untracked_paths:
        path = os.fsdecode(path_bytes)
        if _is_state_path(path):
            continue
        _frame(digest, "path", path_bytes)
        if path.endswith("/"):
            _frame(digest, "dir", path_bytes)
            _walk_untracked_directory(digest, root, path)
        else:
            _read_untracked_value(digest, root / path, path, include_path=False)
    return digest.hexdigest()


def record_verification(state, verification_path, workspace_fingerprint):
    """Record valid verification evidence for one workspace fingerprint."""
    state = _require_active(state)
    if state.get("stage") not in {"IMPLEMENTING", "CODE_REVIEW"}:
        raise StateError("verification is only valid during IMPLEMENTING or CODE_REVIEW")
    if (
        not isinstance(verification_path, (str, os.PathLike))
        or not str(verification_path).strip()
    ):
        raise StateError(
            "verification_path must be a non-empty string or PathLike"
        )
    if (
        not isinstance(workspace_fingerprint, str)
        or re.fullmatch(r"[0-9a-f]{64}", workspace_fingerprint) is None
    ):
        raise StateError(
            "workspace_fingerprint must be a lowercase SHA-256 hexdigest"
        )
    try:
        is_regular_file = Path(verification_path).is_file()
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        raise StateError(
            f"verification path is not a regular file: {verification_path!s}"
        ) from exc
    if not is_regular_file:
        raise StateError(
            f"verification path is not a regular file: {verification_path!s}"
        )
    state["verification"] = {
        "path": str(verification_path),
        "workspace_fingerprint": workspace_fingerprint,
        "valid": True,
    }
    state["updated_at"] = _now_timestamp()
    return state


def invalidate_stale_verification(state, workspace_fingerprint):
    """Invalidate verification only when a currently valid fingerprint is stale."""
    state = _require_active(state)
    if (
        not isinstance(workspace_fingerprint, str)
        or re.fullmatch(r"[0-9a-f]{64}", workspace_fingerprint) is None
    ):
        raise StateError(
            "workspace_fingerprint must be a lowercase SHA-256 hexdigest"
        )
    verification = state.get("verification")
    if not isinstance(verification, dict):
        raise StateError("verification must be an object")
    if (
        verification.get("valid")
        and verification.get("workspace_fingerprint") != workspace_fingerprint
    ):
        verification["valid"] = False
        state["updated_at"] = _now_timestamp()
    return state


def select_resume_candidate(state_root, goal, project_root):
    """Return the newest matching non-terminal state path, if any."""
    desired_goal_key = goal_key(goal)
    desired_project_root = str(Path(project_root).resolve())

    def parse_timestamp(value):
        if not isinstance(value, str):
            return None
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def created_key(value):
        parsed = parse_timestamp(value)
        if parsed is not None:
            return (0, parsed)
        return (1, value if isinstance(value, str) else str(value))

    candidates = []
    for state_path in Path(state_root).glob("*/state.json"):
        try:
            state = load_state(state_path)
        except StateError:
            continue
        if state.get("goal_key") != desired_goal_key:
            continue
        if state.get("project_root") != desired_project_root:
            continue
        if state.get("stage") in TERMINAL_STATES:
            continue
        updated_at = parse_timestamp(state.get("updated_at"))
        if updated_at is None:
            continue
        candidates.append(
            (
                updated_at,
                created_key(state.get("created_at")),
                str(state.get("task_id", "")),
                state_path,
            )
        )
    if not candidates:
        return None
    return max(candidates, key=lambda candidate: candidate[:3])[3]


class _CleanExit(Exception):
    """Argparse completed a successful help action."""


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise StateError(message)

    def exit(self, status=0, message=None):
        if status == 0:
            raise _CleanExit()
        if message:
            raise StateError(message.strip())
        raise StateError(f"argument parsing exited with status {status}")


def _build_parser():
    parser = _ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--root", required=True)
    init_parser.add_argument("--goal", required=True)
    init_parser.add_argument("--requested-mode", required=True)
    init_parser.add_argument("--project-root", required=True)
    init_parser.add_argument("--artifact-dir", required=True)
    init_parser.add_argument("--task-id")

    classify_parser = subparsers.add_parser("classify")
    classify_parser.add_argument("--state", required=True)
    classify_parser.add_argument("--mode", required=True)
    classify_parser.add_argument("--reasons", required=True)

    artifact_parser = subparsers.add_parser("set-artifact")
    artifact_parser.add_argument("--state", required=True)
    artifact_parser.add_argument(
        "--kind",
        required=True,
        choices=("spec", "plan", "compact_plan", "report"),
    )
    artifact_parser.add_argument("--path", required=True)

    show_parser = subparsers.add_parser("show")
    show_parser.add_argument("--state", required=True)

    transition_parser = subparsers.add_parser("transition")
    transition_parser.add_argument("--state", required=True)
    transition_parser.add_argument("--to", required=True)
    transition_parser.add_argument("--reason")

    review_parser = subparsers.add_parser("record-review")
    review_parser.add_argument("--state", required=True)
    review_parser.add_argument("--review", required=True)
    review_parser.add_argument("--artifact-digest", required=True)

    unverified_review_parser = subparsers.add_parser("record-review-unverified")
    unverified_review_parser.add_argument("--state", required=True)
    unverified_review_parser.add_argument("--review", required=True)
    unverified_review_parser.add_argument("--artifact-digest", required=True)

    review_error_parser = subparsers.add_parser("record-review-error")
    review_error_parser.add_argument("--state", required=True)
    review_error_parser.add_argument("--artifact", required=True)
    review_error_parser.add_argument("--round", required=True, type=int)
    review_error_parser.add_argument("--errors", required=True)

    approval_parser = subparsers.add_parser("approve-plan")
    approval_parser.add_argument("--state", required=True)
    approval_parser.add_argument("--plan", required=True)
    approval_parser.add_argument("--approved-at", required=True)

    resume_parser = subparsers.add_parser("select-resume")
    resume_parser.add_argument("--root", required=True)
    resume_parser.add_argument("--goal", required=True)
    resume_parser.add_argument("--project-root", required=True)

    fingerprint_parser = subparsers.add_parser("fingerprint")
    fingerprint_parser.add_argument("--project-root", required=True)

    baseline_parser = subparsers.add_parser("capture-baseline")
    baseline_parser.add_argument("--state", required=True)

    verification_parser = subparsers.add_parser("record-verification")
    verification_parser.add_argument("--state", required=True)
    verification_parser.add_argument("--path", required=True)
    verification_parser.add_argument("--fingerprint", required=True)

    invalidate_verification_parser = subparsers.add_parser(
        "invalidate-verification"
    )
    invalidate_verification_parser.add_argument("--state", required=True)
    invalidate_verification_parser.add_argument("--fingerprint", required=True)

    return parser


def _read_json_list(path, label):
    source = Path(path)
    try:
        with source.open(encoding="utf-8") as stream:
            value = json.load(stream)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise StateError(f"unable to load {label} {source}: {exc}") from exc
    if not isinstance(value, list):
        raise StateError(f"{label} must contain a JSON list")
    return value


def _write_json(value):
    json.dump(value, sys.stdout, ensure_ascii=False, separators=(",", ":"))
    sys.stdout.write("\n")


def _mutating_result(state_path, operation):
    state = load_state(state_path)
    snapshot = copy.deepcopy(state)
    try:
        result = operation(state)
    except ApprovalMismatchError as error:
        if state != snapshot:
            try:
                save_state(state_path, state)
            except StateError as save_error:
                print(f"error: {save_error}", file=sys.stderr)
                raise error from save_error
        raise
    except StateError:
        raise
    save_state(state_path, result)
    _write_json(result)


def main(argv=None):
    """Run the quality-state CLI and return its process exit code."""
    try:
        args = _build_parser().parse_args(argv)

        if args.command == "init":
            state = new_state(
                args.goal,
                args.requested_mode,
                args.project_root,
                args.artifact_dir,
                task_id=args.task_id,
            )
            _warn_for_nonstandard_state_root(args.root, args.project_root)
            state_path = Path(args.root) / state["task_id"] / "state.json"
            if state_path.exists():
                raise FilesystemError(f"state already exists: {state_path}")
            save_state(state_path, state)
            _write_json(state)
        elif args.command == "classify":
            reasons = _read_json_list(args.reasons, "classification reasons")
            _mutating_result(
                args.state,
                lambda state: classify(state, args.mode, reasons),
            )
        elif args.command == "set-artifact":
            _mutating_result(
                args.state,
                lambda state: set_artifact(state, args.kind, args.path),
            )
        elif args.command == "show":
            _write_json(load_state(args.state))
        elif args.command == "transition":
            _mutating_result(
                args.state,
                lambda state: transition(state, args.to, args.reason),
            )
        elif args.command == "record-review":
            _mutating_result(
                args.state,
                lambda state: record_review(
                    state,
                    args.review,
                    args.artifact_digest,
                ),
            )
        elif args.command == "record-review-unverified":
            _mutating_result(
                args.state,
                lambda state: record_review_unverified(
                    state, args.review, args.artifact_digest,
                ),
            )
        elif args.command == "record-review-error":
            errors = _read_json_list(args.errors, "review errors")
            _mutating_result(
                args.state,
                lambda state: record_review_validation_failure(
                    state,
                    args.artifact,
                    args.round,
                    errors,
                ),
            )
        elif args.command == "approve-plan":
            _mutating_result(
                args.state,
                lambda state: approve_plan(
                    state,
                    args.plan,
                    args.approved_at,
                ),
            )
        elif args.command == "select-resume":
            candidate = select_resume_candidate(
                args.root,
                args.goal,
                args.project_root,
            )
            _write_json({"match": str(candidate) if candidate is not None else None})
        elif args.command == "fingerprint":
            _write_json(
                {"fingerprint": compute_workspace_fingerprint(args.project_root)}
            )
        elif args.command == "capture-baseline":
            _mutating_result(args.state, capture_workspace_baseline)
        elif args.command == "record-verification":
            _mutating_result(
                args.state,
                lambda state: record_verification(
                    state,
                    args.path,
                    args.fingerprint,
                ),
            )
        elif args.command == "invalidate-verification":
            _mutating_result(
                args.state,
                lambda state: invalidate_stale_verification(
                    state,
                    args.fingerprint,
                ),
            )
        return 0
    except _CleanExit:
        return 0
    except (GitError, FilesystemError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 4
    except TransitionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3
    except StateError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
