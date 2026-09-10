"""Deterministic primitives for verifying contribution candidates."""

from __future__ import annotations

import argparse
import base64
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple
from urllib.parse import quote_plus, urlencode


DEFAULT_API_VERSION = "2026-03-10"  # api_version default
MAX_RETRIES = 3
MAX_RETRY_DELAY_SECONDS = 300.0
REPOSITORY_PATTERN = re.compile(r"\A[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
PATTERN_ID_PATTERN = re.compile(r"\APAT-\d+\Z")
REVISION_PATTERN = re.compile(r"\Asha256:[0-9a-f]{64}\Z")
TOKEN_PATTERNS = (
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
)
_UNPARSEABLE_PAYLOAD = object()

REVISION_PATHS = (
    "SKILL.md",
    "agents/openai.yaml",
    "references/verification-contract.md",
    "references/github-verification-contract.md",
    "scripts/verify_candidates.py",
    "tests/test_verify_candidates.py",
    "tests/test_skill_contract.py",
)

RECHECK_MUTABLE_FIELDS = (
    "status",
    "status_reason",
    "blocking_gaps",
    "verified_at",
    "verified_base_sha",
    "verification_history",
    "next_recheck_required",
    "repository_checks",
    "duplicate_search",
)

DISCOVER_STAGES = (
    "repository",
    "head",
    "community_profile",
    "private_vulnerability_reporting",
    "upstream_repository",
    "policy_files",
    "duplicate_search",
    "code_search",
)

POLICY_PATHS = (
    "CONTRIBUTING.md",
    ".github/CONTRIBUTING.md",
    "docs/CONTRIBUTING.md",
    "SECURITY.md",
    ".github/SECURITY.md",
    "docs/SECURITY.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE",
    "CODE_OF_CONDUCT.md",
    ".github/CODE_OF_CONDUCT.md",
)

COMMUNITY_PROFILE_KEYS = (
    "code_of_conduct",
    "contributing",
    "issue_template",
    "pull_request_template",
    "license",
    "readme",
)

FAILED_SCOPE_REASONS = (
    "budget-exhausted",
    "repository-not-found-or-inaccessible",
    "repository-unauthorized",
    "repository-forbidden",
    "repository-failed",
)

POLICY_KEYWORD_PATTERNS = (
    ("CLA", re.compile(r"\bclas?\b", re.IGNORECASE)),
    ("DCO", re.compile(r"\bdcos?\b", re.IGNORECASE)),
    ("Signed-off-by", re.compile(r"\bsigned-off-by\b", re.IGNORECASE)),
    (
        "Developer Certificate",
        re.compile(r"\bdeveloper certificate\b", re.IGNORECASE),
    ),
    (
        "Contributor License",
        re.compile(r"\bcontributor license\b", re.IGNORECASE),
    ),
)

ACCESS_FAILURE_OUTCOMES = (
    "not-found-or-inaccessible",
    "unauthorized",
    "forbidden",
    "failed",
)

SEARCH_INDEX_LIMITATION = (
    "GitHub search index delay can omit recently created or updated matches."
)

ALLOWED_RESPONSE_HEADERS = (
    "ETag",
    "Retry-After",
    "X-RateLimit-Limit",
    "X-RateLimit-Remaining",
    "X-RateLimit-Reset",
    "Link",
    "Content-Type",
)
_HEADER_NAMES = {name.lower(): name for name in ALLOWED_RESPONSE_HEADERS}

ANALYSIS_ENVELOPE_FIELDS = {
    "schema_version",
    "generated_by",
    "analysis_generated_by",
    "records",
    "patterns",
    "limitations",
}
PATTERN_FIELDS = {
    "pattern_id",
    "description",
    "search_clues",
    "applicability",
    "counterconditions",
    "expected_tests",
    "maintainer_judgment_required",
    "provenance_mode",
    "source_licenses",
    "confidence",
    "superseded_by",
    "pattern_history",
}

CANDIDATE_FIELDS = (
    "candidate_id", "candidate_key", "generated_by", "pattern_ids",
    "pattern_revisions", "repository", "repository_node_id", "locus",
    "status", "status_reason", "sensitivity", "summary", "impact",
    "readiness_checks", "ai_policy_status", "disclosure_required",
    "private_evidence_reference", "evidence_links", "execution_evidence",
    "reproduction", "policy_checks", "blocking_gaps", "superseded_by",
    "duplicate_search", "repository_checks", "verification_history",
    "verified_at", "verified_base_sha", "next_recheck_required",
)

STATUS_REASON_TABLE = {
    "unverified": ("insufficient-evidence",),
    "reproduced": ("none",),
    "duplicate": (
        "duplicate-open", "duplicate-closed-rejected",
        "duplicate-closed-other", "already-fixed",
    ),
    "not-applicable": (
        "reproduction-failed", "already-fixed", "archived-or-disabled",
        "fork-redirect-to-upstream",
    ),
    "stale": ("base-moved",),
    "policy-review": ("policy-prohibited", "policy-unknown", "none"),
    "issue-ready": ("ready",),
    "pr-ready": ("ready",),
    "private-report-ready": ("security-sensitive",),
}

READINESS_KEYS = (
    "present_on_head", "impact_described", "open_and_closed_searched",
    "rejection_still_valid", "repository_active_and_issues_enabled",
    "policy_files_reviewed", "ai_policy_allowed", "not_security_sensitive",
    "reproduction_evidence", "design_difference_reviewed",
    "provenance_allows_independent_work", "verified_at_and_sha_recorded",
)

POLICY_CHECK_KEYS = (
    "contributing", "issue_template", "pr_template", "security_policy",
    "code_of_conduct", "cla_or_dco", "ai_policy", "program_rules",
)

POLICY_CHECK_PATHS = {
    "contributing": (
        "CONTRIBUTING.md",
        ".github/CONTRIBUTING.md",
        "docs/CONTRIBUTING.md",
    ),
    "issue_template": (".github/ISSUE_TEMPLATE",),
    "pr_template": (".github/PULL_REQUEST_TEMPLATE.md",),
    "security_policy": (
        "SECURITY.md",
        ".github/SECURITY.md",
        "docs/SECURITY.md",
    ),
    "code_of_conduct": (
        "CODE_OF_CONDUCT.md",
        ".github/CODE_OF_CONDUCT.md",
    ),
    "cla_or_dco": tuple(POLICY_PATHS),
    "ai_policy": tuple(POLICY_PATHS),
}

ASSESSMENT_FIELDS = {
    "pattern_id", "repository", "locus", "status", "status_reason",
    "sensitivity", "summary", "impact", "readiness_checks",
    "duplicate_verdict", "ai_policy_status", "disclosure_required",
    "private_evidence_reference", "evidence_links", "execution_evidence",
    "reproduction", "policy_checks", "blocking_gaps", "superseded_by",
}

SNAPSHOT_FIELDS = {
    "verification_id", "revision", "verified_at", "verified_base_sha",
    "status", "status_reason", "sensitivity", "evidence", "inputs",
}

SNAPSHOT_EVIDENCE_FIELDS = {
    "duplicate_search", "repository_checks", "policy_checks",
    "readiness_checks", "reproduction", "execution_evidence",
    "duplicate_verdict", "observed_head_sha",
}

INHERITED_EVIDENCE_FIELDS = (
    "readiness_checks", "reproduction", "execution_evidence",
    "duplicate_verdict",
)

READY_STATUSES = ("issue-ready", "pr-ready", "private-report-ready")
ACTIONABLE_STATUSES = (
    "reproduced", "issue-ready", "pr-ready", "private-report-ready",
)


class CliInputError(ValueError):
    """A safe, single-line command input error."""


class ChildCommandError(RuntimeError):
    """Raised when a child command violates the read-only allowlist."""


class BudgetExhausted(RuntimeError):
    """Raised before an attempt that would exceed the request budget."""


class CloneError(RuntimeError):
    """Raised when a read-only clone operation cannot be completed."""


@dataclass(frozen=True)
class ApiResponse:
    """A parsed response containing only persistable response headers."""

    status: int
    headers: Dict[str, str]
    payload: object


@dataclass
class RequestBudget:
    """A run-global count of request attempts, including retries."""

    limit: int
    consumed: int = 0

    def __post_init__(self) -> None:
        if isinstance(self.limit, bool) or not isinstance(self.limit, int) or self.limit <= 0:
            raise ValueError("request budget must be a positive integer")
        if isinstance(self.consumed, bool) or not isinstance(self.consumed, int):
            raise ValueError("consumed request count must be an integer")
        if self.consumed < 0 or self.consumed > self.limit:
            raise ValueError("consumed request count is outside the budget")

    @property
    def remaining(self) -> int:
        return self.limit - self.consumed

    def consume(self) -> None:
        if self.consumed >= self.limit:
            raise BudgetExhausted("request budget exhausted")
        self.consumed += 1


def compute_revision(skill_dir: Optional[Path] = None) -> str:
    """Return the framed SHA-256 revision for the seven contract files."""
    root = skill_dir if skill_dir is not None else Path(__file__).resolve().parents[1]
    digest = hashlib.sha256()
    for relative_path in sorted(REVISION_PATHS):
        path_bytes = relative_path.encode("utf-8")
        content = (root / relative_path).read_bytes()
        digest.update(len(path_bytes).to_bytes(8, "big"))
        digest.update(path_bytes)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return "sha256:" + digest.hexdigest()


def redact(text: str) -> Tuple[str, List[str]]:
    """Redact supported token shapes and return any resulting warning keys."""
    if not isinstance(text, str):
        raise TypeError("redact expects text")
    redacted = text
    found = False
    for pattern in TOKEN_PATTERNS:
        redacted, replacements = pattern.subn("[REDACTED]", redacted)
        found = found or replacements > 0
    warnings = ["secret-like-string-redacted"] if found else []
    return redacted, warnings


def _redacted_json(value: object) -> Tuple[str, List[str]]:
    serialized = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    return redact(serialized)


def _has_secret_like_string(value: object) -> bool:
    unused, warnings = redact(json.dumps(value, ensure_ascii=False))
    del unused
    return bool(warnings)


def write_json_atomic(path: Path, value: object) -> None:
    """Write UTF-8 JSON with a trailing newline by atomic replacement."""
    destination = Path(path)
    temporary_path = None
    serialized, unused_warnings = _redacted_json(value)
    del unused_warnings
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(destination.parent),
            prefix=".%s." % destination.name,
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(serialized)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(str(temporary_path), str(destination))
    except Exception:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass
        raise


def write_text_atomic(path: Path, text: str) -> None:
    """Write redacted UTF-8 text with a trailing newline by atomic replacement."""
    destination = Path(path)
    temporary_path = None
    serialized, unused_warnings = redact(text)
    del unused_warnings
    if not serialized.endswith("\n"):
        serialized += "\n"
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(destination.parent),
            prefix=".%s." % destination.name,
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(serialized)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(str(temporary_path), str(destination))
    except Exception:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass
        raise


def _write_stderr(message: object) -> None:
    rendered, warnings = redact(str(message).replace("\n", " "))
    if warnings and "secret-like-string-redacted" not in rendered:
        rendered += " [secret-like-string-redacted]"
    print(rendered, file=sys.stderr)


def _child_env() -> Dict[str, str]:
    """Build the environment used only for a read-only clone child."""
    child = os.environ.copy()
    child["GIT_LFS_SKIP_SMUDGE"] = "1"
    child["GIT_TERMINAL_PROMPT"] = "0"
    return child


def run_child(
    command: Sequence[str],
    *,
    runner: Callable[..., Any] = subprocess.run,
    env: Optional[Dict[str, str]] = None,
) -> Any:
    """Run an allowlisted read-only child command without a working directory."""
    arguments = list(command)
    if not arguments or arguments[0] not in {"gh", "git"}:
        raise ChildCommandError("child executable must be gh or git")
    if arguments[0] == "gh":
        if len(arguments) < 5 or arguments[1] != "api":
            raise ChildCommandError("gh child command must use the api subcommand")
        try:
            method_index = arguments.index("--method")
        except ValueError as error:
            raise ChildCommandError("gh api child command must declare GET") from error
        if method_index + 1 >= len(arguments) or arguments[method_index + 1] != "GET":
            raise ChildCommandError("gh api child command must declare GET")
    else:
        allowed = False
        if len(arguments) >= 2 and arguments[1] in {"clone", "rev-parse", "ls-remote"}:
            allowed = True
        if len(arguments) >= 4 and arguments[1] == "-C" and arguments[3] == "rev-parse":
            allowed = True
        if not allowed:
            raise ChildCommandError("git child command is not read-only allowlisted")
    keyword_arguments = {
        "capture_output": True,
        "text": True,
        "check": False,
        "shell": False,
    }
    if env is not None:
        keyword_arguments["env"] = env
    return runner(arguments, **keyword_arguments)


def clone_repository(
    runner: Callable[..., Any], url: str, dest: Path, branch: str
) -> str:
    """Create one shallow clone and return its checked-out commit SHA."""
    destination = str(dest)
    environment = _child_env()
    clone_command = [
        "git",
        "clone",
        "--depth",
        "1",
        "--single-branch",
        "--branch",
        branch,
        "--no-tags",
        url,
        destination,
    ]
    completed = run_child(clone_command, runner=runner, env=environment)
    if getattr(completed, "returncode", 1) != 0:
        raise CloneError("git clone failed")
    head_command = ["git", "-C", destination, "rev-parse", "HEAD"]
    completed = run_child(head_command, runner=runner, env=environment)
    if getattr(completed, "returncode", 1) != 0:
        raise CloneError("git rev-parse failed")
    sha = str(getattr(completed, "stdout", "")).strip().lower()
    if re.fullmatch(r"[0-9a-f]{40}", sha) is None:
        raise CloneError("git rev-parse returned an invalid SHA")
    return sha


def _execution_surface(relative_path: str) -> bool:
    name = relative_path.rsplit("/", 1)[-1].lower()
    if name in {"package.json", "makefile", "dockerfile", "containerfile"}:
        return True
    return re.fullmatch(r"compose.*\.ya?ml", name) is not None


def _clone_relative_path(root: Path, path: object) -> str:
    if not isinstance(path, (str, os.PathLike)):
        return "."
    try:
        relative = Path(path).relative_to(root)
    except ValueError:
        return "."
    return relative.as_posix() or "."


def static_search(dest: Path, clues: Sequence[str]) -> Dict[str, object]:
    """Read regular clone files and find case-insensitive clue substrings."""
    root = Path(dest)
    lowered_clues = [(clue, clue.lower()) for clue in clues]
    hits = []  # type: List[Dict[str, object]]
    execution_surfaces = []  # type: List[str]
    skipped_files = 0
    exclusions = {"symlink": 0, "oversize": 0, "binary": 0}
    read_failures = []  # type: List[Dict[str, str]]

    def record_walk_failure(error: OSError) -> None:
        read_failures.append(
            {
                "path": _clone_relative_path(root, error.filename),
                "operation": "walk",
            }
        )

    for directory, directory_names, file_names in os.walk(
        str(root), onerror=record_walk_failure
    ):
        directory_names[:] = sorted(
            name for name in directory_names if name != ".git"
        )
        for file_name in sorted(file_names):
            path = Path(directory) / file_name
            relative_path = path.relative_to(root).as_posix()
            if _execution_surface(relative_path):
                execution_surfaces.append(relative_path)
            if path.is_symlink():
                skipped_files += 1
                exclusions["symlink"] += 1
                continue
            try:
                size = path.stat().st_size
            except OSError:
                skipped_files += 1
                read_failures.append(
                    {"path": relative_path, "operation": "stat"}
                )
                continue
            if size > 4 * 1024 * 1024:
                skipped_files += 1
                exclusions["oversize"] += 1
                continue
            try:
                content = path.read_bytes()
            except OSError:
                skipped_files += 1
                read_failures.append(
                    {"path": relative_path, "operation": "read"}
                )
                continue
            if b"\x00" in content:
                skipped_files += 1
                exclusions["binary"] += 1
                continue
            lowered_path = relative_path.lower()
            for clue, lowered_clue in lowered_clues:
                if lowered_clue in lowered_path:
                    hits.append({"path": relative_path, "line": 0, "clue": clue})
            text = content.decode("utf-8", errors="replace")
            for line_number, line in enumerate(text.splitlines(), 1):
                lowered_line = line.lower()
                for clue, lowered_clue in lowered_clues:
                    if lowered_clue in lowered_line:
                        hits.append(
                            {
                                "path": relative_path,
                                "line": line_number,
                                "clue": clue,
                            }
                        )
    return {
        "available": True,
        "hits": hits,
        "execution_surfaces": sorted(execution_surfaces),
        "skipped_files": skipped_files,
        "clone_sha": None,
        "error": None,
        "complete": not read_failures,
        "exclusions": exclusions,
        "read_failures": read_failures,
    }


def _directory_size(path: Path) -> int:
    total = 0
    if not path.exists():
        return total
    for directory, directory_names, file_names in os.walk(str(path)):
        directory_names.sort()
        for file_name in file_names:
            try:
                total += (Path(directory) / file_name).stat().st_size
            except OSError:
                continue
    return total


def _request_path(endpoint: str, params: Optional[Dict[str, object]]) -> str:
    if not isinstance(endpoint, str) or not endpoint.startswith("/"):
        raise ValueError("endpoint must be an absolute GitHub API path")
    if not params:
        return endpoint
    query = urlencode(params, doseq=True, quote_via=quote_plus, safe="/:")
    separator = "&" if "?" in endpoint else "?"
    return endpoint + separator + query


def _sanitize_headers(headers: Dict[str, str]) -> Dict[str, str]:
    sanitized = {}
    for name, value in headers.items():
        canonical = _HEADER_NAMES.get(name.lower())
        if canonical is not None:
            sanitized[canonical] = str(value).strip()
    return sanitized


def _parse_included_response(output: str) -> Tuple[int, Dict[str, str], str]:
    normalized = output.replace("\r\n", "\n")
    lines = normalized.split("\n")
    starts = [
        index
        for index, line in enumerate(lines)
        if re.match(r"\AHTTP(?:/[^ ]+)?\s+\d{3}(?:\s|\Z)", line, re.IGNORECASE)
    ]
    if not starts:
        raise ValueError("gh api returned no included HTTP status")
    start = starts[-1]
    status_match = re.match(
        r"\AHTTP(?:/[^ ]+)?\s+(\d{3})(?:\s|\Z)", lines[start], re.IGNORECASE
    )
    if status_match is None:
        raise ValueError("gh api returned an invalid HTTP status")
    headers = {}
    body_start = len(lines)
    for index in range(start + 1, len(lines)):
        line = lines[index]
        if line == "":
            body_start = index + 1
            break
        if ":" in line:
            name, value = line.split(":", 1)
            headers[name.strip()] = value.strip()
    body = "\n".join(lines[body_start:])
    return int(status_match.group(1)), _sanitize_headers(headers), body


def _payload_from_body(body: str) -> object:
    try:
        return json.loads(body)
    except (TypeError, json.JSONDecodeError):
        return _UNPARSEABLE_PAYLOAD


def _retry_delay(
    headers: Dict[str, str], attempt: int, clock: Callable[[], float]
) -> float:
    retry_after = headers.get("Retry-After")
    if retry_after is not None:
        try:
            parsed_retry_after = float(retry_after)
            if math.isfinite(parsed_retry_after):
                return min(MAX_RETRY_DELAY_SECONDS, max(0.0, parsed_retry_after))
        except ValueError:
            pass
    reset = headers.get("X-RateLimit-Reset")
    if reset is not None:
        try:
            parsed_reset = float(reset)
            if math.isfinite(parsed_reset):
                return min(
                    MAX_RETRY_DELAY_SECONDS,
                    max(0.0, parsed_reset - clock()),
                )
        except ValueError:
            pass
    return min(MAX_RETRY_DELAY_SECONDS, 60.0 * (2 ** attempt))


def _nonnegative_finite_number(value: object) -> Optional[float]:
    if not isinstance(value, str):
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    if not math.isfinite(parsed) or parsed < 0:
        return None
    return parsed


def _retryable(status: int, headers: Dict[str, str]) -> Tuple[bool, str]:
    if status == 403:
        if _nonnegative_finite_number(headers.get("Retry-After")) is not None:
            return True, "retry-after"
        reset = _nonnegative_finite_number(headers.get("X-RateLimit-Reset"))
        if headers.get("X-RateLimit-Remaining") == "0" and reset is not None:
            return True, "remaining-zero-and-reset"
        return False, "ambiguous-403"
    if status == 429:
        return True, "http-429"
    if 500 <= status <= 599:
        return True, "http-5xx"
    return False, "not-retryable"


class GhApiClient:
    """A serial read-only GitHub CLI adapter with bounded retries."""

    def __init__(
        self,
        runner: Callable[..., Any] = subprocess.run,
        sleeper: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.time,
        *,
        budget: Optional[RequestBudget] = None,
        api_version: str = DEFAULT_API_VERSION,
    ) -> None:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", api_version) is None:
            raise ValueError("api_version must use YYYY-MM-DD")
        self.runner = runner
        self.sleeper = sleeper
        self.clock = clock
        self.budget = budget if budget is not None else RequestBudget(300)
        self.api_version = api_version
        self.request_events = []  # type: List[Dict[str, object]]

    def get_json(
        self, endpoint: str, params: Optional[Dict[str, object]] = None
    ) -> ApiResponse:
        request_path = _request_path(endpoint, params)
        command = [
            "gh",
            "api",
            "--method",
            "GET",
            "-H",
            "X-GitHub-Api-Version: %s" % self.api_version,
            "--include",
            request_path,
        ]
        for attempt in range(MAX_RETRIES + 1):
            self.budget.consume()
            event = {
                "path": request_path,
                "attempt": attempt + 1,
                "status": None,
                "headers": {},
            }
            self.request_events.append(event)
            try:
                completed = run_child(command, runner=self.runner)
                status, headers, body = _parse_included_response(
                    str(getattr(completed, "stdout", ""))
                )
                event["status"] = status
                event["headers"] = headers
                response = ApiResponse(status, headers, _payload_from_body(body))
            except (OSError, subprocess.SubprocessError, ValueError) as error:
                event["error"] = "transport-error"
                if attempt == MAX_RETRIES:
                    event["retry_decision"] = "return"
                    event["retry_reason"] = "retry-limit-reached"
                    return ApiResponse(
                        599,
                        {},
                        {"message": "transport-error", "detail": str(error)},
                    )
                delay = min(MAX_RETRY_DELAY_SECONDS, 60.0 * (2 ** attempt))
                event["retry_decision"] = "retry"
                event["retry_reason"] = "transport-error"
                event["retry_delay"] = delay
                self.sleeper(delay)
                continue
            retryable, retry_reason = _retryable(response.status, response.headers)
            if not retryable or attempt == MAX_RETRIES:
                event["retry_decision"] = "return"
                event["retry_reason"] = (
                    "retry-limit-reached" if retryable else retry_reason
                )
                return response
            delay = _retry_delay(response.headers, attempt, self.clock)
            event["retry_decision"] = "retry"
            event["retry_reason"] = retry_reason
            event["retry_delay"] = delay
            self.sleeper(delay)
        raise AssertionError("bounded retry loop must return")


class FixtureTransport:
    """An offline response transport backed by a responses.json mapping."""

    def __init__(
        self,
        fixture_dir: Path,
        *,
        budget: Optional[RequestBudget] = None,
        sleeper: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.fixture_dir = Path(fixture_dir)
        response_path = self.fixture_dir / "responses.json"
        try:
            loaded = json.loads(response_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError("fixture responses.json is unreadable: %s" % error) from error
        if not isinstance(loaded, dict):
            raise ValueError("fixture responses.json must contain an object")
        self.responses = loaded
        self.budget = budget if budget is not None else RequestBudget(300)
        self.sleeper = sleeper
        self.clock = clock
        self.request_events = []  # type: List[Dict[str, object]]

    def get_json(
        self, endpoint: str, params: Optional[Dict[str, object]] = None
    ) -> ApiResponse:
        request_path = _request_path(endpoint, params)
        raw = self.responses.get(request_path)
        sequence = raw if isinstance(raw, list) else None
        for attempt in range(MAX_RETRIES + 1):
            self.budget.consume()
            selected = sequence[min(attempt, len(sequence) - 1)] if sequence else raw
            if not isinstance(selected, dict):
                response = ApiResponse(
                    599,
                    {},
                    {"message": "fixture-missing", "path": request_path},
                )
            else:
                status = selected.get("status")
                headers = selected.get("headers")
                if isinstance(status, bool) or not isinstance(status, int):
                    raise ValueError(
                        "fixture status must be an integer for %s" % request_path
                    )
                if not isinstance(headers, dict):
                    raise ValueError(
                        "fixture headers must be an object for %s" % request_path
                    )
                response = ApiResponse(
                    status,
                    _sanitize_headers(
                        {str(key): str(value) for key, value in headers.items()}
                    ),
                    selected.get("payload"),
                )
            event = {
                "path": request_path,
                "attempt": attempt + 1,
                "status": response.status,
                "headers": response.headers,
            }
            self.request_events.append(event)
            retryable, retry_reason = _retryable(response.status, response.headers)
            if not retryable or attempt == MAX_RETRIES:
                event["retry_decision"] = "return"
                event["retry_reason"] = (
                    "retry-limit-reached" if retryable else retry_reason
                )
                return response
            delay = _retry_delay(response.headers, attempt, self.clock)
            event["retry_decision"] = "retry"
            event["retry_reason"] = retry_reason
            event["retry_delay"] = delay
            self.sleeper(delay)
        raise AssertionError("bounded fixture retry loop must return")


def _is_string_list(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def validate_analysis_envelope(value: object) -> List[str]:
    """Return ordered contract violations for an enriched analysis input."""
    if not isinstance(value, dict):
        return ["$: expected an object"]
    actual_fields = set(value)
    missing = sorted(ANALYSIS_ENVELOPE_FIELDS - actual_fields)
    if missing:
        return ["$: missing field %s" % missing[0]]
    extra = sorted(actual_fields - ANALYSIS_ENVELOPE_FIELDS)
    if extra:
        return ["$: unsupported field %s" % extra[0]]
    if value.get("schema_version") != "1.0.0":
        return ["$.schema_version: unsupported schema version"]
    for name in ("generated_by", "analysis_generated_by"):
        if not isinstance(value.get(name), dict):
            return ["$.%s: expected an object" % name]
    if not isinstance(value.get("records"), list):
        return ["$.records: expected an array"]
    if not isinstance(value.get("patterns"), list):
        return ["$.patterns: expected an array"]
    if not _is_string_list(value.get("limitations")):
        return ["$.limitations: expected an array of strings"]

    seen = set()
    for index, pattern in enumerate(value["patterns"]):
        location = "$.patterns[%d]" % index
        if not isinstance(pattern, dict):
            return [location + ": expected an object"]
        missing_pattern = sorted(PATTERN_FIELDS - set(pattern))
        if missing_pattern:
            return [location + ": missing field " + missing_pattern[0]]
        pattern_id = pattern.get("pattern_id")
        if not isinstance(pattern_id, str) or PATTERN_ID_PATTERN.fullmatch(pattern_id) is None:
            return [location + ".pattern_id: expected PAT-<n>"]
        if pattern_id in seen:
            return [location + ".pattern_id: duplicate pattern ID"]
        seen.add(pattern_id)
        if not isinstance(pattern.get("description"), str):
            return [location + ".description: expected a string"]
        for name in (
            "search_clues",
            "applicability",
            "counterconditions",
            "expected_tests",
            "maintainer_judgment_required",
        ):
            if not _is_string_list(pattern.get(name)):
                return [location + ".%s: expected an array of strings" % name]
        if not isinstance(pattern.get("provenance_mode"), str):
            return [location + ".provenance_mode: expected a string"]
        if not isinstance(pattern.get("source_licenses"), list):
            return [location + ".source_licenses: expected an array"]
        if not isinstance(pattern.get("confidence"), dict):
            return [location + ".confidence: expected an object"]
        superseded_by = pattern.get("superseded_by")
        if superseded_by is not None and (
            not isinstance(superseded_by, str)
            or PATTERN_ID_PATTERN.fullmatch(superseded_by) is None
        ):
            return [location + ".superseded_by: expected null or PAT-<n>"]
        history = pattern.get("pattern_history")
        if not isinstance(history, list) or not history:
            return [location + ".pattern_history: expected at least one item"]
        last = history[-1]
        if not isinstance(last, dict):
            return [location + ".pattern_history[-1]: expected an object"]
        revision = last.get("revision")
        if not isinstance(revision, str) or REVISION_PATTERN.fullmatch(revision) is None:
            return [location + ".pattern_history[-1].revision: expected sha256 revision"]
    return []


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliInputError(message)


def _positive_integer(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("expected a positive integer") from error
    if parsed <= 0:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(prog="verify_candidates.py")
    parser.add_argument("--print-revision", action="store_true")
    subparsers = parser.add_subparsers(dest="command", parser_class=_ArgumentParser)

    discover = subparsers.add_parser("discover")
    discover.add_argument("--analysis", required=True)
    discover.add_argument("--repo", action="append", required=True)
    discover.add_argument("--pattern", action="append", default=[])
    discover.add_argument("--output", required=True)
    discover.add_argument("--manifest", required=True)
    discover.add_argument("--max-candidates-per-repo", type=_positive_integer, default=5)
    discover.add_argument("--max-candidates-total", type=_positive_integer, default=20)
    discover.add_argument("--request-budget", type=_positive_integer, default=300)
    discover.add_argument("--api-version", default=DEFAULT_API_VERSION)
    discover.add_argument("--allow-clone", action="store_true")
    discover.add_argument("--clone-root")
    discover.add_argument("--keep-clone", action="store_true")
    discover.add_argument("--max-clues-per-pattern", type=_positive_integer, default=5)
    discover.add_argument("--fixture-dir")

    record = subparsers.add_parser("record")
    record.add_argument("--discovery", required=True)
    record.add_argument("--assessment", required=True)
    record.add_argument("--candidates")
    record.add_argument("--output", required=True)
    record.add_argument("--manifest", required=True)
    record.add_argument("--markdown-output")
    record.add_argument("--program-rules")
    record.add_argument("--replace", action="store_true")

    recheck = subparsers.add_parser("recheck")
    recheck.add_argument("--candidates", required=True)
    recheck.add_argument("--output", required=True)
    recheck.add_argument("--manifest", required=True)
    recheck.add_argument("--candidate", action="append", default=[])
    recheck.add_argument("--markdown-output")
    recheck.add_argument("--request-budget", type=_positive_integer, default=300)
    recheck.add_argument("--fixture-dir")

    render = subparsers.add_parser("render")
    render.add_argument("--candidates", required=True)
    render.add_argument("--manifest")
    render.add_argument("--output", required=True)

    validate = subparsers.add_parser("validate")
    validate.add_argument("--candidates", required=True)
    validate.add_argument("--existing")
    return parser


def _validate_discover_arguments(arguments: argparse.Namespace) -> None:
    repositories = arguments.repo
    for repository in repositories:
        if REPOSITORY_PATTERN.fullmatch(repository) is None:
            raise CliInputError("repo must use owner/name syntax: %s" % repository)
    if len(repositories) != len(set(repositories)):
        raise CliInputError("repo values must not contain duplicates")
    for pattern_id in arguments.pattern:
        if PATTERN_ID_PATTERN.fullmatch(pattern_id) is None:
            raise CliInputError("pattern must use PAT-<n> syntax: %s" % pattern_id)
    if arguments.clone_root is not None and not arguments.allow_clone:
        raise CliInputError("clone-root requires --allow-clone")
    if arguments.keep_clone and not arguments.allow_clone:
        raise CliInputError("keep-clone requires --allow-clone")
    if arguments.allow_clone:
        if arguments.clone_root is None:
            arguments.clone_root = tempfile.mkdtemp(prefix="verify-candidates-")
        clone_root = os.path.realpath(arguments.clone_root)
        temporary_root = os.path.realpath(tempfile.gettempdir())
        try:
            inside_temporary = (
                clone_root != temporary_root
                and os.path.commonpath((clone_root, temporary_root)) == temporary_root
            )
        except ValueError:
            inside_temporary = False
        if not inside_temporary:
            raise CliInputError(
                "clone-root must resolve below the temporary area %s" % temporary_root
            )
        arguments.clone_root = clone_root


def _read_analysis(path: str) -> Dict[str, object]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CliInputError("analysis: unable to read JSON: %s" % error) from error
    violations = validate_analysis_envelope(value)
    if violations:
        raise CliInputError(violations[0])
    return value


def _validate_selected_patterns(
    analysis: Dict[str, object], selected: Sequence[str]
) -> None:
    patterns = {
        pattern["pattern_id"]: pattern
        for pattern in analysis["patterns"]
        if isinstance(pattern, dict)
    }
    for pattern_id in selected:
        pattern = patterns.get(pattern_id)
        if pattern is None:
            raise CliInputError("pattern not found in analysis: %s" % pattern_id)
        if pattern.get("superseded_by") is not None:
            raise CliInputError("pattern is superseded and cannot be selected: %s" % pattern_id)


def _utc_observation(clock: Callable[[], float]) -> str:
    observed = datetime.fromtimestamp(clock(), timezone.utc)
    return observed.isoformat().replace("+00:00", "Z")


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _untrusted_text(text: str, source_url: str, truncated: bool) -> Dict[str, object]:
    return {
        "text": text,
        "sha256": _sha256_bytes(text.encode("utf-8")),
        "source_url": source_url,
        "truncated": truncated,
        "untrusted": True,
    }


def _fixture_missing(response: ApiResponse) -> bool:
    return (
        response.status == 599
        and isinstance(response.payload, dict)
        and response.payload.get("message") == "fixture-missing"
    )


def _append_response_warning(
    warnings: List[str], response: ApiResponse, request_path: str
) -> None:
    if _fixture_missing(response):
        warning = "fixture-missing:%s" % request_path
    else:
        warning = "request-failed:%s:http-%s" % (request_path, response.status)
        if response.status == 403:
            retryable, retry_reason = _retryable(response.status, response.headers)
            if retryable:
                warning += ":rate-limit:retry-limit-reached"
            else:
                warning += ":permission-denied:%s" % retry_reason
    if warning not in warnings:
        warnings.append(warning)


def _append_invalid_payload_warning(
    warnings: List[str], request_path: str, payload_kind: str
) -> None:
    warning = "request-failed:%s:invalid-%s-payload" % (
        request_path,
        payload_kind,
    )
    if warning not in warnings:
        warnings.append(warning)


def _valid_search_payload(payload: object) -> bool:
    return (
        isinstance(payload, dict)
        and isinstance(payload.get("total_count"), int)
        and not isinstance(payload.get("total_count"), bool)
        and isinstance(payload.get("incomplete_results"), bool)
        and isinstance(payload.get("items"), list)
    )


def _safe_search_clue(clue: object) -> bool:
    return (
        isinstance(clue, str)
        and '"' not in clue
        and "\\" not in clue
        and all(ord(character) >= 32 and ord(character) != 127 for character in clue)
    )


def _trusted_duplicate_query(repository: str, query: object) -> bool:
    if not isinstance(query, str):
        return False
    match = re.fullmatch(
        r'repo:%s "([^"\\\r\n]*)" is:(issue|pr) is:(open|closed)'
        % re.escape(repository),
        query,
    )
    return match is not None and _safe_search_clue(match.group(1))


def _repository_failure(
    status: int, headers: Optional[Dict[str, str]] = None
) -> Tuple[str, str, str]:
    if status == 404:
        return (
            "not-found-or-inaccessible",
            "http-404",
            "repository-not-found-or-inaccessible",
        )
    if status == 401:
        return "unauthorized", "http-401", "repository-unauthorized"
    if status == 403:
        retryable, _ = _retryable(status, headers or {})
        if retryable:
            return "failed", "transport-or-5xx", "repository-failed"
        return "forbidden", "http-403", "repository-forbidden"
    return "failed", "transport-or-5xx", "repository-failed"


def _community_profile_files(payload: object) -> Dict[str, bool]:
    files = payload.get("files") if isinstance(payload, dict) else None
    if not isinstance(files, dict):
        files = {}
    return {name: files.get(name) is not None for name in COMMUNITY_PROFILE_KEYS}


def _repository_checks(payload: Dict[str, object]) -> Dict[str, object]:
    license_value = payload.get("license")
    license_spdx = None
    if isinstance(license_value, dict) and isinstance(
        license_value.get("spdx_id"), str
    ):
        license_spdx = license_value["spdx_id"]
    return {
        "node_id": payload.get("node_id") if isinstance(payload.get("node_id"), str) else "",
        "full_name": (
            payload.get("full_name") if isinstance(payload.get("full_name"), str) else ""
        ),
        "archived": payload.get("archived") is True,
        "disabled": payload.get("disabled") is True,
        "fork": payload.get("fork") is True,
        "has_issues": payload.get("has_issues") is True,
        "default_branch": (
            payload.get("default_branch")
            if isinstance(payload.get("default_branch"), str)
            else ""
        ),
        "pushed_at": (
            payload.get("pushed_at") if isinstance(payload.get("pushed_at"), str) else ""
        ),
        "visibility": (
            payload.get("visibility")
            if isinstance(payload.get("visibility"), str)
            else ""
        ),
        "license_spdx": license_spdx,
        "community_profile_files": {name: False for name in COMMUNITY_PROFILE_KEYS},
        "private_vulnerability_reporting": None,
    }


def _decode_policy_payload(payload: object) -> Tuple[bytes, int, str]:
    if isinstance(payload, dict):
        encoded = payload.get("content")
        if payload.get("encoding") == "base64" and isinstance(encoded, str):
            content = base64.b64decode(encoded.encode("ascii"), validate=False)
        else:
            content = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        size = payload.get("size")
        reported_size = size if isinstance(size, int) and not isinstance(size, bool) else len(content)
        url = payload.get("html_url")
        return content, reported_size, url if isinstance(url, str) else ""
    content = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return content, len(content), ""


def _policy_result(
    source_repository: str,
    policy_path: str,
    request_path: str,
    response: ApiResponse,
    warnings: List[str],
) -> Dict[str, object]:
    if response.status == 404:
        return {
            "path": policy_path,
            "source_repository": source_repository,
            "status": "absent",
            "found": False,
            "sha256": None,
            "size": None,
            "entry_count": None,
            "excerpt": None,
            "truncated": False,
            "url": None,
            "keyword_hits": [],
        }
    if not 200 <= response.status < 300:
        _append_response_warning(warnings, response, request_path)
        return {
            "path": policy_path,
            "source_repository": source_repository,
            "status": "request-failed",
            "found": False,
            "sha256": None,
            "size": None,
            "entry_count": None,
            "excerpt": None,
            "truncated": False,
            "url": None,
            "keyword_hits": [],
        }
    if isinstance(response.payload, list):
        names = sorted(
            item["name"]
            for item in response.payload
            if isinstance(item, dict) and isinstance(item.get("name"), str)
        )
        content = json.dumps(
            names, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        decoded = "\n".join(names)
        excerpt_text = decoded[:4000]
        truncated = len(decoded) > len(excerpt_text)
        keyword_hits = [
            label for label, pattern in POLICY_KEYWORD_PATTERNS if pattern.search(decoded)
        ]
        excerpt = _untrusted_text(excerpt_text, request_path, truncated)
        excerpt["sha256"] = _sha256_bytes(content)
        return {
            "path": policy_path,
            "source_repository": source_repository,
            "status": "found",
            "found": True,
            "sha256": _sha256_bytes(content),
            "size": None,
            "entry_count": len(names),
            "excerpt": excerpt,
            "truncated": truncated,
            "url": request_path,
            "keyword_hits": keyword_hits,
        }
    if (
        not isinstance(response.payload, dict)
        or response.payload.get("encoding") != "base64"
        or not isinstance(response.payload.get("content"), str)
    ):
        _append_invalid_payload_warning(warnings, request_path, "policy")
        return {
            "path": policy_path,
            "source_repository": source_repository,
            "status": "request-failed",
            "found": False,
            "sha256": None,
            "size": None,
            "entry_count": None,
            "excerpt": None,
            "truncated": False,
            "url": None,
            "keyword_hits": [],
        }
    content, size, url = _decode_policy_payload(response.payload)
    decoded = content.decode("utf-8", errors="replace")
    excerpt_text = decoded[:4000]
    truncated = len(decoded) > len(excerpt_text)
    keyword_hits = [
        label for label, pattern in POLICY_KEYWORD_PATTERNS if pattern.search(decoded)
    ]
    excerpt = _untrusted_text(excerpt_text, url or request_path, truncated)
    excerpt["sha256"] = _sha256_bytes(content)
    return {
        "path": policy_path,
        "source_repository": source_repository,
        "status": "found",
        "found": True,
        "sha256": _sha256_bytes(content),
        "size": size,
        "entry_count": None,
        "excerpt": excerpt,
        "truncated": truncated,
        "url": url or request_path,
        "keyword_hits": keyword_hits,
    }


def discover_policy_files(
    client: object,
    repository: str,
    default_branch: str,
    warnings: List[str],
) -> List[Dict[str, object]]:
    owner = repository.split("/", 1)[0]
    results = []
    for source_repository in (repository, owner + "/.github"):
        for policy_path in POLICY_PATHS:
            endpoint = "/repos/%s/contents/%s" % (source_repository, policy_path)
            params = {"ref": default_branch}
            response = client.get_json(endpoint, params)
            request_path = _request_path(endpoint, params)
            results.append(
                _policy_result(
                    source_repository, policy_path, request_path, response, warnings
                )
            )
    return results


def discover_repository(
    client: object,
    repository: str,
    state: Optional[Dict[str, object]] = None,
) -> Dict[str, object]:
    if state is None:
        state = {
            "repository": repository,
            "outcome": "checked",
            "reason": None,
            "stages_completed": [],
            "head_sha": None,
            "repository_checks": None,
            "upstream_checks": None,
            "policy_files": [],
            "warnings": [],
        }
    else:
        state["outcome"] = "checked"
        state["reason"] = None
    warnings = state["warnings"]
    endpoint = "/repos/" + repository
    response = client.get_json(endpoint)
    if not 200 <= response.status < 300 or not isinstance(response.payload, dict):
        outcome, reason, failed_reason = _repository_failure(
            response.status, response.headers
        )
        state["outcome"] = outcome
        state["reason"] = reason
        state["failed_scope_reason"] = failed_reason
        _append_response_warning(warnings, response, endpoint)
        return state

    checks = _repository_checks(response.payload)
    state["repository_checks"] = checks
    state["stages_completed"].append("repository")
    default_branch = checks["default_branch"]

    head_endpoint = "/repos/%s/commits/%s" % (repository, default_branch)
    head_response = client.get_json(head_endpoint)
    head_payload = head_response.payload
    if (
        200 <= head_response.status < 300
        and isinstance(head_payload, dict)
        and isinstance(head_payload.get("sha"), str)
        and re.fullmatch(r"[0-9a-fA-F]{40}", head_payload["sha"]) is not None
    ):
        state["head_sha"] = head_payload["sha"].lower()
        state["stages_completed"].append("head")
    else:
        _append_response_warning(warnings, head_response, head_endpoint)

    community_endpoint = "/repos/%s/community/profile" % repository
    community_response = client.get_json(community_endpoint)
    community_payload = community_response.payload
    if (
        200 <= community_response.status < 300
        and isinstance(community_payload, dict)
        and isinstance(community_payload.get("files"), dict)
    ):
        checks["community_profile_files"] = _community_profile_files(
            community_payload
        )
        state["stages_completed"].append("community_profile")
    elif 200 <= community_response.status < 300:
        _append_invalid_payload_warning(
            warnings, community_endpoint, "community-profile"
        )
    else:
        _append_response_warning(warnings, community_response, community_endpoint)

    pvr_endpoint = "/repos/%s/private-vulnerability-reporting" % repository
    pvr_response = client.get_json(pvr_endpoint)
    if 200 <= pvr_response.status < 300 and isinstance(pvr_response.payload, dict):
        enabled = pvr_response.payload.get("enabled")
        checks["private_vulnerability_reporting"] = (
            enabled if isinstance(enabled, bool) else None
        )
        state["stages_completed"].append("private_vulnerability_reporting")
    else:
        _append_response_warning(warnings, pvr_response, pvr_endpoint)

    parent = response.payload.get("parent")
    if checks["fork"] and isinstance(parent, dict):
        parent_name = parent.get("full_name")
        if isinstance(parent_name, str) and REPOSITORY_PATTERN.fullmatch(parent_name):
            upstream_endpoint = "/repos/" + parent_name
            upstream_response = client.get_json(upstream_endpoint)
            if 200 <= upstream_response.status < 300 and isinstance(
                upstream_response.payload, dict
            ):
                state["upstream_checks"] = _repository_checks(
                    upstream_response.payload
                )
                state["stages_completed"].append("upstream_repository")
            else:
                _append_response_warning(
                    warnings, upstream_response, upstream_endpoint
                )

    state["policy_files"] = discover_policy_files(
        client, repository, default_branch, warnings
    )
    state["stages_completed"].append("policy_files")
    return state


def _issue_item(item: object) -> Optional[Dict[str, object]]:
    if not isinstance(item, dict):
        return None
    url = item.get("html_url") if isinstance(item.get("html_url"), str) else ""
    title = item.get("title") if isinstance(item.get("title"), str) else ""
    return {
        "number": item.get("number"),
        "title": _untrusted_text(title, url, False),
        "state": item.get("state"),
        "html_url": url,
        "created_at": item.get("created_at"),
        "closed_at": item.get("closed_at"),
        "pull_request": isinstance(item.get("pull_request"), dict),
        "state_reason": item.get("state_reason"),
    }


def discover_duplicate_search(
    client: object,
    repository: str,
    clues: Sequence[str],
    max_clues: int,
    warnings: List[str],
) -> Dict[str, object]:
    used = list(clues[:max_clues])
    queries = []
    complete = True
    for clue in used:
        if not _safe_search_clue(clue):
            complete = False
            warning = "unsafe-search-clue-rejected"
            if warning not in warnings:
                warnings.append(warning)
            continue
        for kind in ("issue", "pr"):
            for state in ("open", "closed"):
                query = 'repo:%s "%s" is:%s is:%s' % (
                    repository,
                    clue,
                    kind,
                    state,
                )
                response = client.get_json("/search/issues", {"q": query})
                payload_valid = _valid_search_payload(response.payload)
                payload = response.payload if payload_valid else {}
                succeeded = 200 <= response.status < 300 and payload_valid
                incomplete = payload.get("incomplete_results") is True
                if 200 <= response.status < 300 and not payload_valid:
                    complete = False
                    _append_invalid_payload_warning(
                        warnings,
                        _request_path("/search/issues", {"q": query}),
                        "search",
                    )
                elif not succeeded:
                    complete = False
                    _append_response_warning(
                        warnings,
                        response,
                        _request_path("/search/issues", {"q": query}),
                    )
                if incomplete:
                    complete = False
                raw_items = payload.get("items") if isinstance(payload.get("items"), list) else []
                items = []
                for raw_item in raw_items:
                    item = _issue_item(raw_item)
                    if item is not None:
                        items.append(item)
                queries.append(
                    {
                        "q": query,
                        "total_count": payload.get("total_count") if succeeded else None,
                        "incomplete_results": incomplete if succeeded else True,
                        "items": items,
                    }
                )
    return {
        "queries": queries,
        "complete": complete,
        "unused_clues": list(clues[len(used):]),
        "method_limitations": [SEARCH_INDEX_LIMITATION],
    }


def discover_code_search(
    client: object,
    repository: str,
    clues: Sequence[str],
    max_clues: int,
    warnings: List[str],
) -> Dict[str, object]:
    used = list(clues[:max_clues])
    available = True
    hits = []
    queries = []
    for clue in used:
        if not _safe_search_clue(clue):
            available = False
            warning = "unsafe-search-clue-rejected"
            if warning not in warnings:
                warnings.append(warning)
            continue
        query = 'repo:%s "%s"' % (repository, clue)
        response = client.get_json("/search/code", {"q": query})
        payload_valid = _valid_search_payload(response.payload)
        payload = response.payload if payload_valid else {}
        succeeded = 200 <= response.status < 300 and payload_valid
        request_path = _request_path("/search/code", {"q": query})
        if 200 <= response.status < 300 and not payload_valid:
            available = False
            _append_invalid_payload_warning(warnings, request_path, "search")
        elif not succeeded:
            available = False
            _append_response_warning(warnings, response, request_path)
        queries.append(
            {
                "q": query,
                "total_count": payload.get("total_count") if succeeded else None,
            }
        )
        if succeeded:
            raw_items = payload.get("items") if isinstance(payload.get("items"), list) else []
            for item in raw_items:
                if not isinstance(item, dict):
                    continue
                path = item.get("path")
                url = item.get("html_url")
                if isinstance(path, str) and isinstance(url, str):
                    hits.append({"path": path, "html_url": url, "clue": clue})
    return {"available": available, "queries": queries, "hits": hits}


def _selected_patterns(
    analysis: Dict[str, object], selected_ids: Sequence[str]
) -> List[Dict[str, object]]:
    patterns = [item for item in analysis["patterns"] if isinstance(item, dict)]
    if selected_ids:
        by_id = {item["pattern_id"]: item for item in patterns}
        return [by_id[pattern_id] for pattern_id in selected_ids]
    return [item for item in patterns if item.get("superseded_by") is None]


def _cap_combinations(
    repositories: Sequence[str],
    patterns: Sequence[Dict[str, object]],
    per_repo_cap: int,
    total_cap: int,
) -> Tuple[List[Tuple[str, Dict[str, object]]], List[Dict[str, str]]]:
    selected = []
    skipped = []
    for repository in repositories:
        for index, pattern in enumerate(patterns):
            pattern_id = str(pattern["pattern_id"])
            if index >= per_repo_cap:
                skipped.append(
                    {
                        "repository": repository,
                        "pattern_id": pattern_id,
                        "reason": "per-repo-cap",
                    }
                )
            elif len(selected) >= total_cap:
                skipped.append(
                    {
                        "repository": repository,
                        "pattern_id": pattern_id,
                        "reason": "total-cap",
                    }
                )
            else:
                selected.append((repository, pattern))
    return selected, skipped


def discover_exit_code(
    repositories: Sequence[Dict[str, object]],
    records: Sequence[Dict[str, object]],
    combos: Sequence[Dict[str, object]],
) -> int:
    del records
    if repositories and all(
        item.get("outcome") in ACCESS_FAILURE_OUTCOMES for item in repositories
    ):
        return 4
    repository_partial = any(
        item.get("outcome") in ACCESS_FAILURE_OUTCOMES
        or item.get("reason") == "budget-exhausted"
        for item in repositories
    )
    combination_partial = any(
        not item.get("duplicate_search", {}).get("complete", False)
        or not item.get("code_search", {}).get("available", False)
        or ("head_sha" in item and item.get("head_sha") is None)
        or any(
            isinstance(warning, str)
            and warning.startswith(("request-failed:", "fixture-missing:"))
            for warning in item.get("warnings", [])
        )
        or any(
            isinstance(warning, str)
            and warning.startswith("static-search-incomplete:")
            for warning in item.get("warnings", [])
        )
        or any(
            isinstance(warning, str)
            and warning.startswith("clone-cleanup-failed:")
            for warning in item.get("warnings", [])
        )
        for item in combos
    )
    return 3 if repository_partial or combination_partial else 0


def _manifest_document(path: Path, generated_by: Dict[str, str]) -> Dict[str, object]:
    if not path.exists():
        return {"schema_version": "1.0.0", "generated_by": generated_by, "runs": []}
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CliInputError("manifest: unable to read JSON: %s" % error) from error
    if (
        not isinstance(document, dict)
        or document.get("schema_version") != "1.0.0"
        or not isinstance(document.get("runs"), list)
    ):
        raise CliInputError("manifest: expected schema_version 1.0.0 and runs array")
    return document


def _public_repository_run(state: Dict[str, object]) -> Dict[str, object]:
    return {
        "repository": state["repository"],
        "outcome": state["outcome"],
        "reason": state["reason"],
        "stages_completed": list(state["stages_completed"]),
        "head_sha": state["head_sha"],
    }


def _failed_scope(
    repository: str, pattern: Dict[str, object], reason: str
) -> Dict[str, str]:
    if reason not in FAILED_SCOPE_REASONS:
        raise ValueError("unsupported failed scope reason")
    return {
        "repository": repository,
        "pattern_id": str(pattern["pattern_id"]),
        "reason": reason,
    }


def _validate_discover_partition(
    universe: Sequence[Tuple[str, str]],
    selected: Sequence[Tuple[str, Dict[str, object]]],
    records: Sequence[Dict[str, object]],
    skipped_by_cap: Sequence[Dict[str, object]],
    failed_scopes: Sequence[Dict[str, object]],
) -> None:
    universe_keys = set(universe)
    selected_keys = {
        (repository, str(pattern["pattern_id"])) for repository, pattern in selected
    }
    sections = []
    for items in (records, skipped_by_cap, failed_scopes):
        keys = [
            (str(item.get("repository")), str(item.get("pattern_id")))
            for item in items
        ]
        if len(keys) != len(set(keys)):
            raise CliInputError("discover partition invariant violated")
        sections.append(set(keys))
    record_keys, skipped_keys, failed_keys = sections
    if (
        not record_keys.isdisjoint(skipped_keys)
        or not record_keys.isdisjoint(failed_keys)
        or not skipped_keys.isdisjoint(failed_keys)
        or record_keys | skipped_keys | failed_keys != universe_keys
        or record_keys | failed_keys != selected_keys
        or skipped_keys != universe_keys - selected_keys
    ):
        raise CliInputError("discover partition invariant violated")


def _fixture_repository_sources(fixture_dir: Optional[str]) -> Dict[str, str]:
    if fixture_dir is None:
        return {}
    path = Path(fixture_dir) / "repositories.json"
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CliInputError("fixture repositories.json is unreadable: %s" % error) from error
    if not isinstance(value, dict):
        raise CliInputError("fixture repositories.json must contain an object")
    sources = {}
    for repository, source in value.items():
        if not isinstance(repository, str) or not isinstance(source, str):
            raise CliInputError("fixture repositories.json keys and values must be strings")
        if source.startswith("file://"):
            sources[repository] = source
        elif os.path.isabs(source):
            sources[repository] = source
        else:
            raise CliInputError(
                "fixture repository source must be an absolute path or file URL: %s"
                % repository
            )
    return sources


def _clone_source(
    repository: str, fixture_sources: Dict[str, str], fixture_mode: bool
) -> str:
    if fixture_mode:
        source = fixture_sources.get(repository)
        if source is None:
            raise CloneError("fixture repository source is missing")
        return source
    return "https://github.com/%s.git" % repository


def _create_clone_session(
    repository: str,
    branch: str,
    clone_root: str,
    fixture_sources: Dict[str, str],
    fixture_mode: bool,
    runner: Callable[..., Any],
) -> Dict[str, object]:
    owner, name = repository.split("/", 1)
    root = Path(clone_root)
    root.mkdir(parents=True, exist_ok=True)
    destination = root / (owner + "__" + name)
    session = {
        "repository": repository,
        "path": destination,
        "sha": None,
        "created": False,
        "removed": False,
        "size_bytes": 0,
        "error": None,
    }
    existed_before = os.path.lexists(str(destination))
    if existed_before:
        session["error"] = "clone-destination-exists"
        return session
    try:
        source = _clone_source(repository, fixture_sources, fixture_mode)
        session["sha"] = clone_repository(runner, source, destination, branch)
    except CloneError as error:
        session["error"] = str(error)
    finally:
        session["created"] = not existed_before and os.path.lexists(str(destination))
    return session


def _cleanup_clone_sessions(
    sessions: Sequence[Dict[str, object]], keep_clone: bool, clone_root: object
) -> Tuple[List[Dict[str, object]], Dict[str, List[str]]]:
    entries = []
    cleanup_warnings = {}  # type: Dict[str, List[str]]
    if not sessions:
        return entries, cleanup_warnings
    root = Path(clone_root).resolve()
    for session in sessions:
        repository = session.get("repository")
        repository_text = repository if isinstance(repository, str) else "unknown"
        path = session.get("path")
        path_text = str(path) if isinstance(path, (str, os.PathLike)) else "unknown"
        if isinstance(path, Path):
            session["size_bytes"] = _directory_size(path)
        else:
            session["size_bytes"] = 0
        if session.get("created") is True and not keep_clone:
            deletion_attempted = False
            try:
                if not isinstance(path, Path):
                    raise TypeError("clone session path must be a Path")
                if not isinstance(repository, str) or REPOSITORY_PATTERN.fullmatch(
                    repository
                ) is None:
                    raise ValueError("clone session repository is invalid")
                owner, name = repository.split("/", 1)
                expected_path = root / (owner + "__" + name)
                if path != expected_path or path == root:
                    raise ValueError("clone session path is outside its ownership")
                deletion_attempted = True
                shutil.rmtree(str(path))
            except Exception as error:
                error_class = type(error).__name__
                if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", error_class) is None:
                    error_class = "Exception"
                warning = "clone-cleanup-failed:%s:%s:%s" % (
                    repository_text,
                    path_text,
                    error_class,
                )
                cleanup_warnings.setdefault(repository_text, []).append(warning)
            finally:
                if deletion_attempted:
                    session["removed"] = not os.path.lexists(str(path))
        entries.append(
            {
                "repository": repository_text,
                "path": path_text,
                "sha": session.get("sha"),
                "removed": session.get("removed") is True,
                "size_bytes": session["size_bytes"],
            }
        )
    return entries, cleanup_warnings


def _static_record(
    session: Dict[str, object], clues: Sequence[str], warnings: List[str]
) -> Dict[str, object]:
    if session["error"] is not None or session["sha"] is None:
        if "clone-failed" not in warnings:
            warnings.append("clone-failed")
        return {
            "available": False,
            "hits": [],
            "execution_surfaces": [],
            "skipped_files": 0,
            "clone_sha": session["sha"],
            "error": session["error"],
            "complete": False,
            "exclusions": {"symlink": 0, "oversize": 0, "binary": 0},
            "read_failures": [],
        }
    result = static_search(session["path"], clues)
    result["clone_sha"] = session["sha"]
    # A walk failure is also an incomplete observation, even without a file count.
    if result["read_failures"]:
        warning = "static-search-incomplete:%d" % len(result["read_failures"])
        if warning not in warnings:
            warnings.append(warning)
    return result


def _evidence_status(remote_hits: bool, static_hits: bool) -> str:
    if remote_hits and static_hits:
        return "remote+static"
    if remote_hits:
        return "remote-only"
    if static_hits:
        return "static-only"
    return "none"


def _record_from_remote(
    repository_state: Dict[str, object],
    pattern: Dict[str, object],
    duplicate_search: Dict[str, object],
    code_search: Dict[str, object],
    observed_at: str,
) -> Dict[str, object]:
    history = pattern["pattern_history"]
    revision = history[-1]["revision"]
    remote_hit = bool(code_search["hits"])
    return {
        "pattern_id": pattern["pattern_id"],
        "pattern_revision": revision,
        "repository": repository_state["repository"],
        "repository_node_id": repository_state["repository_checks"]["node_id"],
        "head_sha": repository_state["head_sha"],
        "observed_at": observed_at,
        "repository_checks": repository_state["repository_checks"],
        "upstream_checks": repository_state["upstream_checks"],
        "policy_files": repository_state["policy_files"],
        "duplicate_search": duplicate_search,
        "code_search": code_search,
        "static_search": {
            "available": False,
            "hits": [],
            "execution_surfaces": [],
            "skipped_files": 0,
            "clone_sha": None,
            "error": "clone-not-requested",
            "complete": False,
            "exclusions": {"symlink": 0, "oversize": 0, "binary": 0},
            "read_failures": [],
        },
        "evidence_status": "remote-only" if remote_hit else "none",
        "warnings": list(repository_state["warnings"]),
    }


def run_discover(
    arguments: argparse.Namespace,
    analysis: Dict[str, object],
    *,
    runner: Callable[..., Any],
    sleeper: Callable[[float], None],
    clock: Callable[[], float],
) -> int:
    started_at = _utc_observation(clock)
    budget = RequestBudget(arguments.request_budget)
    if arguments.fixture_dir:
        try:
            client = FixtureTransport(
                Path(arguments.fixture_dir),
                budget=budget,
                sleeper=sleeper,
                clock=clock,
            )
        except ValueError as error:
            raise CliInputError(str(error)) from error
    else:
        client = GhApiClient(
            runner=runner,
            sleeper=sleeper,
            clock=clock,
            budget=budget,
            api_version=arguments.api_version,
        )

    patterns = _selected_patterns(analysis, arguments.pattern)
    universe = [
        (repository, str(pattern["pattern_id"]))
        for repository in arguments.repo
        for pattern in patterns
    ]
    selected_combinations, skipped_by_cap = _cap_combinations(
        arguments.repo,
        patterns,
        arguments.max_candidates_per_repo,
        arguments.max_candidates_total,
    )
    combinations_by_repository = {}  # type: Dict[str, List[Dict[str, object]]]
    for repository, pattern in selected_combinations:
        combinations_by_repository.setdefault(repository, []).append(pattern)

    repository_states = []  # type: List[Dict[str, object]]
    failed_scopes = []  # type: List[Dict[str, str]]
    records = []  # type: List[Dict[str, object]]
    exhausted = False
    for repository in arguments.repo:
        patterns_for_repository = combinations_by_repository.get(repository, [])
        if exhausted:
            state = {
                "repository": repository,
                "outcome": "budget-exhausted",
                "reason": "budget-exhausted",
                "stages_completed": [],
                "head_sha": None,
                "repository_checks": None,
                "upstream_checks": None,
                "policy_files": [],
                "warnings": [],
            }
            repository_states.append(state)
            failed_scopes.extend(
                _failed_scope(repository, pattern, "budget-exhausted")
                for pattern in patterns_for_repository
            )
            continue
        state = {
            "repository": repository,
            "outcome": "budget-exhausted",
            "reason": "budget-exhausted",
            "stages_completed": [],
            "head_sha": None,
            "repository_checks": None,
            "upstream_checks": None,
            "policy_files": [],
            "warnings": [],
        }
        try:
            state = discover_repository(client, repository, state)
        except BudgetExhausted:
            exhausted = True
            if state["stages_completed"]:
                state["outcome"] = "checked"
            else:
                state["outcome"] = "budget-exhausted"
            state["reason"] = "budget-exhausted"
            repository_states.append(state)
            failed_scopes.extend(
                _failed_scope(repository, pattern, "budget-exhausted")
                for pattern in patterns_for_repository
            )
            continue
        repository_states.append(state)
        if state["outcome"] in ACCESS_FAILURE_OUTCOMES:
            failed_scopes.extend(
                _failed_scope(repository, pattern, str(state["failed_scope_reason"]))
                for pattern in patterns_for_repository
            )

    fixture_sources = (
        _fixture_repository_sources(arguments.fixture_dir)
        if arguments.allow_clone and arguments.fixture_dir
        else {}
    )
    clone_sessions = {}  # type: Dict[str, Dict[str, object]]
    clone_entries = []  # type: List[Dict[str, object]]
    cleanup_warnings = {}  # type: Dict[str, List[str]]
    state_by_repository = {
        str(state["repository"]): state for state in repository_states
    }
    try:
        if not exhausted:
            for combination_index, (repository, pattern) in enumerate(selected_combinations):
                state = state_by_repository[repository]
                if state["outcome"] in ACCESS_FAILURE_OUTCOMES:
                    continue
                warnings = list(state["warnings"])
                clues = pattern.get("search_clues")
                if not isinstance(clues, list):
                    clues = []
                used_clues = clues[:arguments.max_clues_per_pattern]
                try:
                    duplicate = discover_duplicate_search(
                        client,
                        repository,
                        clues,
                        arguments.max_clues_per_pattern,
                        warnings,
                    )
                    code_search = discover_code_search(
                        client,
                        repository,
                        clues,
                        arguments.max_clues_per_pattern,
                        warnings,
                    )
                except BudgetExhausted:
                    exhausted = True
                    state["reason"] = "budget-exhausted"
                    for remaining_repository, remaining_pattern in selected_combinations[
                        combination_index:
                    ]:
                        remaining_state = state_by_repository[remaining_repository]
                        if remaining_state["outcome"] in ACCESS_FAILURE_OUTCOMES:
                            continue
                        remaining_state["reason"] = "budget-exhausted"
                        scope = _failed_scope(
                            remaining_repository, remaining_pattern, "budget-exhausted"
                        )
                        if scope not in failed_scopes:
                            failed_scopes.append(scope)
                    break
                state_with_warnings = dict(state)
                state_with_warnings["warnings"] = warnings
                record = _record_from_remote(
                    state_with_warnings,
                    pattern,
                    duplicate,
                    code_search,
                    _utc_observation(clock),
                )
                checks = state["repository_checks"]
                remote_hits = bool(code_search["hits"])
                clone_allowed = (
                    arguments.allow_clone
                    and isinstance(checks, dict)
                    and checks.get("archived") is False
                    and checks.get("disabled") is False
                    and (remote_hits or not code_search["available"])
                )
                if clone_allowed:
                    session = clone_sessions.get(repository)
                    if session is None:
                        session = _create_clone_session(
                            repository,
                            str(checks["default_branch"]),
                            arguments.clone_root,
                            fixture_sources,
                            arguments.fixture_dir is not None,
                            runner,
                        )
                        clone_sessions[repository] = session
                    static_result = _static_record(session, used_clues, warnings)
                    record["static_search"] = static_result
                    clone_sha = static_result["clone_sha"]
                    if (
                        clone_sha is not None
                        and record["head_sha"] is not None
                        and clone_sha != record["head_sha"]
                        and "head-moved-during-run" not in warnings
                    ):
                        warnings.append("head-moved-during-run")
                    record["warnings"] = warnings
                    record["evidence_status"] = _evidence_status(
                        remote_hits, bool(static_result["hits"])
                    )
                records.append(record)
    finally:
        clone_entries, cleanup_warnings = _cleanup_clone_sessions(
            list(clone_sessions.values()), arguments.keep_clone, arguments.clone_root
        )

    for record in records:
        for warning in cleanup_warnings.get(str(record["repository"]), []):
            if warning not in record["warnings"]:
                record["warnings"].append(warning)

    if exhausted:
        attributed = {
            (str(item["repository"]), str(item["pattern_id"]))
            for item in records + failed_scopes
        }
        for repository, pattern in selected_combinations:
            key = (repository, str(pattern["pattern_id"]))
            if key in attributed:
                continue
            failed_scopes.append(
                _failed_scope(repository, pattern, "budget-exhausted")
            )
            attributed.add(key)
            state_by_repository[repository]["reason"] = "budget-exhausted"

    _validate_discover_partition(
        universe,
        selected_combinations,
        records,
        skipped_by_cap,
        failed_scopes,
    )

    public_repositories = [_public_repository_run(state) for state in repository_states]
    exit_code = discover_exit_code(public_repositories, records, records)
    status = {0: "complete", 3: "partial", 4: "failed"}[exit_code]
    generated_by = {
        "name": "verifying-open-source-contribution-candidates",
        "revision": compute_revision(),
    }
    analysis_path = Path(arguments.analysis)
    analysis_sha256 = _sha256_bytes(analysis_path.read_bytes())
    inputs = {
        "analysis_sha256": analysis_sha256,
        "pattern_ids": [pattern["pattern_id"] for pattern in patterns],
        "repositories": list(arguments.repo),
        "request_budget": arguments.request_budget,
        "allow_clone": arguments.allow_clone,
        "api_version": arguments.api_version,
    }
    method_limitations = [SEARCH_INDEX_LIMITATION]
    warnings = []
    for state in repository_states:
        for warning in state["warnings"]:
            if warning not in warnings:
                warnings.append(warning)
    for record in records:
        for warning in record["warnings"]:
            if warning not in warnings:
                warnings.append(warning)
    discovery = {
        "schema_version": "1.0.0",
        "generated_by": generated_by,
        "inputs": inputs,
        "records": records,
        "skipped_by_cap": skipped_by_cap,
        "failed_scopes": failed_scopes,
        "method_limitations": method_limitations,
        "status": status,
    }
    completed_at = _utc_observation(clock)
    manifest_path = Path(arguments.manifest)
    manifest = _manifest_document(manifest_path, generated_by)
    run = {
        "run_id": "RUN-%03d" % (len(manifest["runs"]) + 1),
        "command": "discover",
        "started_at": started_at,
        "completed_at": completed_at,
        "inputs": inputs,
        "budget": {
            "request_limit": arguments.request_budget,
            "requests_consumed": budget.consumed,
            "per_repo_cap": arguments.max_candidates_per_repo,
            "total_cap": arguments.max_candidates_total,
        },
        "repositories": public_repositories,
        "clones": clone_entries,
        "failed_scopes": failed_scopes,
        "retry_events": list(client.request_events),
        "method_limitations": method_limitations,
        "warnings": warnings,
        "status": status,
        "outcome": "discovered" if records else "no-candidates",
    }
    if _has_secret_like_string([discovery, run]):
        if "secret-like-string-redacted" not in warnings:
            warnings.append("secret-like-string-redacted")
        for record in records:
            record_warnings = record.get("warnings")
            if isinstance(record_warnings, list) and "secret-like-string-redacted" not in record_warnings:
                record_warnings.append("secret-like-string-redacted")
        run["warnings"] = warnings
    manifest["runs"].append(run)
    write_json_atomic(Path(arguments.output), discovery)
    write_json_atomic(manifest_path, manifest)
    print("%s: discovered %d candidate combinations" % (status, len(records)))
    return exit_code


def _read_json_file(path: str, label: str) -> Dict[str, object]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CliInputError("%s: unable to read JSON: %s" % (label, error)) from error
    if not isinstance(value, dict):
        raise CliInputError("%s: expected an object" % label)
    return value


def _file_sha256(path: str) -> str:
    try:
        return _sha256_bytes(Path(path).read_bytes())
    except OSError as error:
        raise CliInputError("unable to read file %s: %s" % (path, error)) from error


def _validate_discovery_document(discovery: Dict[str, object]) -> None:
    if discovery.get("schema_version") != "1.0.0":
        raise CliInputError("discovery: unsupported contract")
    inputs = discovery.get("inputs")
    if not isinstance(inputs, dict) or not isinstance(
        inputs.get("repositories"), list
    ):
        raise CliInputError("discovery.inputs.repositories: expected array")
    if discovery.get("status") not in ("complete", "partial", "failed"):
        raise CliInputError("discovery.status: unsupported")
    if not isinstance(discovery.get("method_limitations"), list):
        raise CliInputError("discovery.method_limitations: expected array")

    required_record_fields = {
        "pattern_id",
        "pattern_revision",
        "repository",
        "repository_node_id",
        "head_sha",
        "observed_at",
        "duplicate_search",
        "repository_checks",
    }
    for section in ("records", "skipped_by_cap", "failed_scopes"):
        items = discovery.get(section)
        if not isinstance(items, list):
            raise CliInputError("discovery.%s: expected array" % section)
        for index, item in enumerate(items):
            location = "discovery.%s[%d]" % (section, index)
            if not isinstance(item, dict):
                raise CliInputError(location + ": expected object")
            if not isinstance(item.get("repository"), str) or not item["repository"]:
                raise CliInputError(location + ".repository: expected string")
            if not isinstance(item.get("pattern_id"), str) or not item["pattern_id"]:
                raise CliInputError(location + ".pattern_id: expected string")
            if section == "records":
                missing = required_record_fields - set(item)
                if missing:
                    raise CliInputError(
                        location + ".%s: missing" % sorted(missing)[0]
                    )
                node_id = item.get("repository_node_id")
                if not isinstance(node_id, str) or not node_id:
                    raise CliInputError(
                        location + ".repository_node_id: expected non-empty string"
                    )


def _is_rfc3339_utc(value: object) -> bool:
    if not isinstance(value, str) or not value.endswith("Z"):
        return False
    try:
        datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return False
    return True


def _candidate_key(pattern_id: str, repository_node_id: str, locus: str) -> str:
    material = "%s\n%s\n%s" % (pattern_id, repository_node_id, locus)
    return _sha256_bytes(material.encode("utf-8"))


def _assessment_shape_violations(assessment: object, location: str) -> List[str]:
    violations = []
    if not isinstance(assessment, dict):
        return [location + ": expected an object"]
    allowed = ASSESSMENT_FIELDS | {"verified_at", "verified_base_sha"}
    for name in sorted(ASSESSMENT_FIELDS - set(assessment)):
        violations.append(location + "." + name + ": missing")
    for name in sorted(set(assessment) - allowed):
        violations.append(location + "." + name + ": unsupported")
    for name in ("pattern_id", "repository", "locus", "status", "status_reason", "sensitivity", "summary", "impact", "ai_policy_status"):
        if name in assessment and not isinstance(assessment.get(name), str):
            violations.append(location + "." + name + ": expected string")
    if not _is_string_list(assessment.get("evidence_links")):
        violations.append(location + ".evidence_links: expected string array")
    if not _is_string_list(assessment.get("blocking_gaps")):
        violations.append(location + ".blocking_gaps: expected string array")
    if assessment.get("disclosure_required") not in (True, False, None):
        violations.append(location + ".disclosure_required: expected boolean or null")
    if assessment.get("private_evidence_reference") is not None and not isinstance(
        assessment.get("private_evidence_reference"), str
    ):
        violations.append(location + ".private_evidence_reference: expected string or null")
    superseded_by = assessment.get("superseded_by")
    if superseded_by is not None and (
        not isinstance(superseded_by, str)
        or re.fullmatch(r"CAN-\d{3,}", superseded_by) is None
    ):
        violations.append(location + ".superseded_by: expected null or CAN-<n>")
    return violations


def _read_assessment(path: str) -> Dict[str, object]:
    value = _read_json_file(path, "assessment")
    if set(value) != {"schema_version", "discovery_sha256", "assessments"}:
        raise CliInputError("assessment: expected schema_version, discovery_sha256, assessments")
    if value.get("schema_version") != "1.0.0":
        raise CliInputError("assessment.schema_version: unsupported schema version")
    if not isinstance(value.get("discovery_sha256"), str):
        raise CliInputError("assessment.discovery_sha256: expected string")
    assessments = value.get("assessments")
    if not isinstance(assessments, list):
        raise CliInputError("assessment.assessments: expected array")
    violations = []
    for index, assessment in enumerate(assessments):
        violations.extend(
            _assessment_shape_violations(assessment, "assessment.assessments[%d]" % index)
        )
    if violations:
        raise CliInputError("; ".join(violations))
    return value


def _policy_sha_values(discovery_record: Dict[str, object]) -> Dict[str, set]:
    by_path = {}  # type: Dict[str, set]
    for item in discovery_record.get("policy_files", []):
        if not isinstance(item, dict) or item.get("found") is not True:
            continue
        path = item.get("path")
        sha256 = item.get("sha256")
        if isinstance(path, str) and isinstance(sha256, str):
            by_path.setdefault(path, set()).add(sha256)
    return by_path


def _policy_request_failure_keys(
    repository: object, policy_files: object
) -> set:
    if not isinstance(repository, str) or not isinstance(policy_files, list):
        return set()
    owner = repository.split("/", 1)[0]
    source_repositories = {repository, owner + "/.github"}
    failed_paths = {
        item.get("path")
        for item in policy_files
        if isinstance(item, dict)
        and item.get("source_repository") in source_repositories
        and item.get("status") == "request-failed"
    }
    return {
        key
        for key, paths in POLICY_CHECK_PATHS.items()
        if failed_paths.intersection(paths)
    }


def _assessment_gate_violations(
    assessment: Dict[str, object],
    discovery_record: Dict[str, object],
    program_rules_sha256: Optional[str],
) -> List[str]:
    violations = []
    status = assessment.get("status")
    reason = assessment.get("status_reason")
    if status not in STATUS_REASON_TABLE or reason not in STATUS_REASON_TABLE.get(status, ()):
        violations.append("status_reason: unsupported status and reason combination")

    readiness = assessment.get("readiness_checks")
    if not isinstance(readiness, dict):
        violations.append("readiness_checks: expected object")
        readiness = {}
    for key in READINESS_KEYS:
        check = readiness.get(key)
        if not isinstance(check, dict):
            violations.append("readiness_checks.%s" % key)
            continue
        if set(check) != {"result", "evidence_links", "note"}:
            violations.append("readiness_checks.%s" % key)
            continue
        result = check.get("result")
        links = check.get("evidence_links")
        if result not in ("confirmed", "not-confirmed", "not-applicable"):
            violations.append("readiness_checks.%s" % key)
        if not _is_string_list(links):
            violations.append("readiness_checks.%s.evidence_links" % key)
        if not isinstance(check.get("note"), str):
            violations.append("readiness_checks.%s.note" % key)
        if result == "confirmed" and (not isinstance(links, list) or not links):
            violations.append("readiness_checks.%s.evidence_links" % key)
        if status in ("issue-ready", "pr-ready"):
            allowed_not_applicable = key == "rejection_still_valid" and result == "not-applicable"
            if result != "confirmed" and not allowed_not_applicable:
                violations.append("readiness_checks.%s" % key)
    for key in sorted(set(readiness) - set(READINESS_KEYS)):
        violations.append("readiness_checks.%s: unsupported" % key)

    checks = discovery_record.get("repository_checks")
    checks = checks if isinstance(checks, dict) else {}
    if status in ("issue-ready", "pr-ready") and (
        checks.get("archived") is True or checks.get("disabled") is True
    ):
        violations.append("archived-or-disabled")
    if status == "issue-ready" and checks.get("has_issues") is False:
        violations.append("has_issues")
    duplicate = discovery_record.get("duplicate_search")
    duplicate = duplicate if isinstance(duplicate, dict) else {}
    open_check = readiness.get("open_and_closed_searched")
    open_confirmed = isinstance(open_check, dict) and open_check.get("result") == "confirmed"
    policy_review = readiness.get("policy_files_reviewed")
    policy_review_confirmed = (
        isinstance(policy_review, dict)
        and policy_review.get("result") == "confirmed"
    )
    if (
        status in ("issue-ready", "pr-ready")
        and policy_review_confirmed
        and _policy_request_failure_keys(
            discovery_record.get("repository"),
            discovery_record.get("policy_files"),
        )
    ):
        violations.append("policy_files_reviewed: request-failed policy observation")
    if duplicate.get("complete") is not True and open_confirmed:
        violations.append("open_and_closed_searched")
    if assessment.get("sensitivity") == "security-sensitive" and status in ("issue-ready", "pr-ready"):
        violations.append("sensitivity")
    if assessment.get("ai_policy_status") in ("unknown", "prohibited") and status in ("issue-ready", "pr-ready"):
        violations.append("ai_policy_status")
    if assessment.get("ai_policy_status") == "allowed-with-disclosure" and assessment.get("disclosure_required") is None:
        violations.append("disclosure_required")
    if discovery_record.get("evidence_status") == "none" and status in ("reproduced", "issue-ready", "pr-ready"):
        violations.append("evidence_status")
    verdict = assessment.get("duplicate_verdict")
    if not isinstance(verdict, dict) or set(verdict) != {"matched_items", "judgment"} or not _is_string_list(verdict.get("matched_items")) or not isinstance(verdict.get("judgment"), str):
        violations.append("duplicate_verdict")
    elif open_confirmed and not verdict["judgment"].strip():
        violations.append("duplicate_verdict.judgment")

    execution = assessment.get("execution_evidence")
    if execution is not None:
        if not isinstance(execution, dict):
            violations.append("execution_evidence")
        else:
            execution_fields = {
                "approval", "command", "isolation", "runtime", "network_policy",
                "exit_code", "output_location", "output_excerpt",
            }
            if set(execution) != execution_fields:
                violations.append("execution_evidence.fields")
            approval = execution.get("approval")
            if not isinstance(approval, dict):
                violations.append("execution_evidence.approval")
            else:
                if set(approval) != {"granted_by", "granted_at", "scope"}:
                    violations.append("execution_evidence.approval.fields")
                if approval.get("granted_by") != "user":
                    violations.append("execution_evidence.approval.granted_by")
                if not _is_rfc3339_utc(approval.get("granted_at")):
                    violations.append("execution_evidence.approval.granted_at")
                scope = approval.get("scope")
                command = execution.get("command")
                if not isinstance(scope, str) or not isinstance(command, str) or command not in scope:
                    violations.append("execution_evidence.approval.scope")
            for name in ("command", "isolation", "runtime", "network_policy", "output_location"):
                if not isinstance(execution.get(name), str):
                    violations.append("execution_evidence.%s" % name)
            if isinstance(execution.get("exit_code"), bool) or not isinstance(execution.get("exit_code"), int):
                violations.append("execution_evidence.exit_code")
            if execution.get("output_excerpt") is not None and not isinstance(execution.get("output_excerpt"), str):
                violations.append("execution_evidence.output_excerpt")
    reproduction = assessment.get("reproduction")
    if not isinstance(reproduction, dict) or set(reproduction) != {"method", "evidence_links", "public_steps"}:
        violations.append("reproduction")
    elif reproduction.get("method") not in ("static", "executed", "none"):
        violations.append("reproduction.method")
    elif reproduction.get("method") == "executed" and execution is None:
        violations.append("execution_evidence")
    if isinstance(reproduction, dict):
        if not _is_string_list(reproduction.get("evidence_links")):
            violations.append("reproduction.evidence_links")
        public_steps = reproduction.get("public_steps")
        if public_steps is not None and not _is_string_list(public_steps):
            violations.append("reproduction.public_steps")

    policy_checks = assessment.get("policy_checks")
    if not isinstance(policy_checks, dict) or set(policy_checks) != set(POLICY_CHECK_KEYS):
        violations.append("policy_checks")
        policy_checks = {}
    discovered_shas = _policy_sha_values(discovery_record)
    for key in POLICY_CHECK_KEYS:
        item = policy_checks.get(key)
        if not isinstance(item, dict) or set(item) != {"found", "source", "sha256", "assessment", "evidence_links"}:
            violations.append("policy_checks.%s" % key)
            continue
        if item.get("found") not in (True, False, None):
            violations.append("policy_checks.%s.found" % key)
        if item.get("source") is not None and not isinstance(item.get("source"), str):
            violations.append("policy_checks.%s.source" % key)
        if item.get("sha256") is not None and (
            not isinstance(item.get("sha256"), str)
            or re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) is None
        ):
            violations.append("policy_checks.%s.sha256" % key)
        if not isinstance(item.get("assessment"), str):
            violations.append("policy_checks.%s.assessment" % key)
        if not _is_string_list(item.get("evidence_links")):
            violations.append("policy_checks.%s.evidence_links" % key)
        if item.get("found") is True and key != "program_rules":
            allowed_shas = set()
            for path in POLICY_CHECK_PATHS.get(key, ()):
                allowed_shas.update(discovered_shas.get(path, set()))
            if item.get("sha256") not in allowed_shas:
                violations.append("policy_checks.%s.sha256" % key)
    program = policy_checks.get("program_rules")
    if isinstance(program, dict):
        if program_rules_sha256 is None:
            if program.get("found") is not None:
                violations.append("policy_checks.program_rules.found")
        elif program.get("found") not in (True, False):
            violations.append("policy_checks.program_rules.found")
        elif program.get("sha256") != program_rules_sha256:
            violations.append("policy_checks.program_rules.sha256")

    if discovery_record.get("head_sha") is None and (
        status != "unverified" or reason != "insufficient-evidence"
    ):
        violations.append("head_sha")
    if "verified_at" in assessment and assessment.get("verified_at") != discovery_record.get("observed_at"):
        violations.append("verified_at")
    if "verified_base_sha" in assessment and assessment.get("verified_base_sha") != discovery_record.get("head_sha"):
        violations.append("verified_base_sha")

    if status == "private-report-ready":
        private_reference = assessment.get("private_evidence_reference")
        security_policy = policy_checks.get("security_policy") if isinstance(policy_checks, dict) else None
        if assessment.get("sensitivity") != "security-sensitive":
            violations.append("private-report-ready.sensitivity")
        if not isinstance(private_reference, str) or not private_reference.strip():
            violations.append("private_evidence_reference")
        if not ((isinstance(security_policy, dict) and security_policy.get("found") is True) or checks.get("private_vulnerability_reporting") is True):
            violations.append("private-report-ready.reporting-channel")
        if isinstance(execution, dict) and execution.get("output_excerpt") is not None:
            violations.append("execution_evidence.output_excerpt")
        if isinstance(reproduction, dict) and reproduction.get("public_steps") is not None:
            violations.append("reproduction.public_steps")
        if isinstance(private_reference, str) and private_reference:
            if any(private_reference in link for link in assessment.get("evidence_links", []) if isinstance(link, str)):
                violations.append("evidence_links.private_evidence_reference")
            if private_reference in str(assessment.get("summary", "")):
                violations.append("summary.private_evidence_reference")
    return violations


def _empty_readiness() -> Dict[str, object]:
    return {
        key: {"result": "not-confirmed", "evidence_links": [], "note": "assessment missing"}
        for key in READINESS_KEYS
    }


def _empty_policy_checks() -> Dict[str, object]:
    return {
        key: {"found": None, "source": None, "sha256": None, "assessment": "assessment missing", "evidence_links": []}
        for key in POLICY_CHECK_KEYS
    }


def _missing_assessment(discovery_record: Dict[str, object]) -> Dict[str, object]:
    return {
        "pattern_id": discovery_record["pattern_id"], "repository": discovery_record["repository"],
        "locus": "", "status": "unverified", "status_reason": "insufficient-evidence",
        "sensitivity": "normal", "summary": "Assessment missing", "impact": "",
        "readiness_checks": _empty_readiness(),
        "duplicate_verdict": {"matched_items": [], "judgment": "not assessed"},
        "ai_policy_status": "unknown", "disclosure_required": None,
        "private_evidence_reference": None, "evidence_links": [],
        "execution_evidence": None,
        "reproduction": {"method": "none", "evidence_links": [], "public_steps": None},
        "policy_checks": _empty_policy_checks(), "blocking_gaps": ["assessment-missing"],
        "superseded_by": None,
    }


def _snapshot(
    candidate_id: str,
    record: Dict[str, object],
    assessment: Dict[str, object],
    history_length: int,
    discovery_sha256: str,
    assessment_sha256: str,
) -> Dict[str, object]:
    return {
        "verification_id": "VER-%s-%d" % (candidate_id, history_length + 1),
        "revision": compute_revision(),
        "verified_at": record.get("observed_at"),
        "verified_base_sha": record.get("head_sha"),
        "status": assessment["status"],
        "status_reason": assessment["status_reason"],
        "sensitivity": assessment["sensitivity"],
        "evidence": {
            "duplicate_search": json.loads(json.dumps(record.get("duplicate_search"))),
            "repository_checks": json.loads(json.dumps(record.get("repository_checks"))),
            "policy_checks": json.loads(json.dumps(assessment["policy_checks"])),
            "readiness_checks": json.loads(json.dumps(assessment["readiness_checks"])),
            "reproduction": json.loads(json.dumps(assessment["reproduction"])),
            "execution_evidence": json.loads(json.dumps(assessment["execution_evidence"])),
            "duplicate_verdict": json.loads(json.dumps(assessment["duplicate_verdict"])),
            "observed_head_sha": record.get("head_sha"),
        },
        "inputs": {
            "kind": "record", "discovery_sha256": discovery_sha256,
            "assessment_sha256": assessment_sha256,
        },
    }


def _candidate_document(path: Optional[str]) -> Dict[str, object]:
    generated_by = {"name": "verifying-open-source-contribution-candidates", "revision": compute_revision()}
    if path is None:
        return {"schema_version": "1.0.0", "generated_by": generated_by, "records": []}
    value = _read_json_file(path, "candidates")
    violations = validate_candidates_document(value)
    if violations:
        raise CliInputError("candidates: " + "; ".join(violations))
    return value


def validate_candidates_document(
    value: object, existing: Optional[Dict[str, object]] = None
) -> List[str]:
    violations = []
    if not isinstance(value, dict):
        return ["$: expected object"]
    if set(value) != {"schema_version", "generated_by", "records"}:
        violations.append("$: expected schema_version, generated_by, records")
    if value.get("schema_version") != "1.0.0":
        violations.append("$.schema_version: unsupported")
    records = value.get("records")
    if not isinstance(records, list):
        return violations + ["$.records: expected array"]
    ids = []
    keys = []
    for index, record in enumerate(records):
        location = "$.records[%d]" % index
        if not isinstance(record, dict):
            violations.append(location + ": expected object")
            continue
        if set(record) != set(CANDIDATE_FIELDS):
            violations.append(location + ": candidate fields mismatch")
            continue
        candidate_id = record.get("candidate_id")
        ids.append(candidate_id)
        keys.append(record.get("candidate_key"))
        if not isinstance(candidate_id, str) or re.fullmatch(r"CAN-\d{3,}", candidate_id) is None:
            violations.append(location + ".candidate_id")
        pattern_ids = record.get("pattern_ids")
        if not isinstance(pattern_ids, list) or len(pattern_ids) != 1 or not isinstance(pattern_ids[0], str):
            violations.append(location + ".pattern_ids")
        elif record.get("candidate_key") != _candidate_key(pattern_ids[0], str(record.get("repository_node_id")), str(record.get("locus"))):
            violations.append(location + ".candidate_key")
        elif PATTERN_ID_PATTERN.fullmatch(pattern_ids[0]) is None:
            violations.append(location + ".pattern_ids")
        revisions = record.get("pattern_revisions")
        if not isinstance(revisions, dict) or not isinstance(pattern_ids, list) or set(revisions) != set(pattern_ids):
            violations.append(location + ".pattern_revisions")
        elif any(not isinstance(item, str) or REVISION_PATTERN.fullmatch(item) is None for item in revisions.values()):
            violations.append(location + ".pattern_revisions")
        if not isinstance(record.get("repository"), str) or REPOSITORY_PATTERN.fullmatch(record["repository"]) is None:
            violations.append(location + ".repository")
        if not isinstance(record.get("repository_node_id"), str) or not record["repository_node_id"]:
            violations.append(location + ".repository_node_id")
        if not isinstance(record.get("locus"), str):
            violations.append(location + ".locus")
        for name in ("summary", "impact", "sensitivity", "ai_policy_status"):
            if not isinstance(record.get(name), str):
                violations.append(location + "." + name)
        if record.get("ai_policy_status") not in ("allowed", "allowed-with-disclosure", "prohibited", "unknown"):
            violations.append(location + ".ai_policy_status")
        if record.get("disclosure_required") not in (True, False, None):
            violations.append(location + ".disclosure_required")
        if not _is_string_list(record.get("evidence_links")):
            violations.append(location + ".evidence_links")
        if not _is_string_list(record.get("blocking_gaps")):
            violations.append(location + ".blocking_gaps")
        status = record.get("status")
        if status not in STATUS_REASON_TABLE or record.get("status_reason") not in STATUS_REASON_TABLE.get(status, ()):
            violations.append(location + ".status_reason")
        if not _is_rfc3339_utc(record.get("verified_at")):
            violations.append(location + ".verified_at")
        base_sha = record.get("verified_base_sha")
        if base_sha is not None and (not isinstance(base_sha, str) or re.fullmatch(r"[0-9a-f]{40}", base_sha) is None):
            violations.append(location + ".verified_base_sha")
        if base_sha is None and (
            record.get("status") != "unverified"
            or record.get("status_reason") != "insufficient-evidence"
        ):
            violations.append(location + ".verified_base_sha: null requires unverified")
        history = record.get("verification_history")
        if not isinstance(history, list) or not history:
            violations.append(location + ".verification_history")
            continue
        for history_index, snapshot in enumerate(history):
            snapshot_location = "%s.verification_history[%d]" % (location, history_index)
            if not isinstance(snapshot, dict) or set(snapshot) != SNAPSHOT_FIELDS:
                violations.append(snapshot_location + ": snapshot fields mismatch")
                continue
            expected_id = "VER-%s-%d" % (candidate_id, history_index + 1)
            if snapshot.get("verification_id") != expected_id:
                violations.append(snapshot_location + ".verification_id")
            if not isinstance(snapshot.get("revision"), str) or REVISION_PATTERN.fullmatch(snapshot["revision"]) is None:
                violations.append(snapshot_location + ".revision")
            if not _is_rfc3339_utc(snapshot.get("verified_at")):
                violations.append(snapshot_location + ".verified_at")
            snapshot_sha = snapshot.get("verified_base_sha")
            if snapshot_sha is not None and (
                not isinstance(snapshot_sha, str)
                or re.fullmatch(r"[0-9a-f]{40}", snapshot_sha) is None
            ):
                violations.append(snapshot_location + ".verified_base_sha")
            snapshot_status = snapshot.get("status")
            if snapshot_status not in STATUS_REASON_TABLE or snapshot.get("status_reason") not in STATUS_REASON_TABLE.get(snapshot_status, ()):
                violations.append(snapshot_location + ".status_reason")
            evidence = snapshot.get("evidence")
            if not isinstance(evidence, dict) or set(evidence) != SNAPSHOT_EVIDENCE_FIELDS:
                violations.append(snapshot_location + ".evidence")
            inputs = snapshot.get("inputs")
            if not isinstance(inputs, dict) or set(inputs) != {"kind", "discovery_sha256", "assessment_sha256"}:
                violations.append(snapshot_location + ".inputs")
            elif inputs.get("kind") == "record":
                if not all(isinstance(inputs.get(name), str) and re.fullmatch(r"[0-9a-f]{64}", inputs[name]) for name in ("discovery_sha256", "assessment_sha256")):
                    violations.append(snapshot_location + ".inputs.record")
            elif inputs.get("kind") == "recheck":
                if inputs.get("discovery_sha256") is not None or inputs.get("assessment_sha256") is not None:
                    violations.append(snapshot_location + ".inputs.recheck")
                if history_index == 0:
                    violations.append(snapshot_location + ": recheck cannot be first")
                elif isinstance(evidence, dict) and isinstance(history[history_index - 1], dict):
                    previous_evidence = history[history_index - 1].get("evidence", {})
                    for name in INHERITED_EVIDENCE_FIELDS:
                        if evidence.get(name) != previous_evidence.get(name):
                            violations.append(snapshot_location + ".evidence." + name)
            else:
                violations.append(snapshot_location + ".inputs.kind")
        latest = history[-1]
        if isinstance(latest, dict):
            for name in ("status", "status_reason", "verified_at", "verified_base_sha"):
                if record.get(name) != latest.get(name):
                    violations.append(location + "." + name + ": differs from latest snapshot")
        if record.get("next_recheck_required") != (record.get("status") in READY_STATUSES):
            violations.append(location + ".next_recheck_required")
    if len(ids) != len(set(ids)):
        violations.append("$.records: duplicate candidate_id")
    if len(keys) != len(set(keys)):
        violations.append("$.records: duplicate candidate_key")
    id_set = set(ids)
    for index, record in enumerate(records):
        if isinstance(record, dict):
            target = record.get("superseded_by")
            if target is not None and (target not in id_set or target == record.get("candidate_id")):
                violations.append("$.records[%d].superseded_by" % index)
    if existing is not None and isinstance(existing.get("records"), list):
        current_by_id = {item.get("candidate_id"): item for item in records if isinstance(item, dict)}
        for prior in existing["records"]:
            if not isinstance(prior, dict):
                continue
            current = current_by_id.get(prior.get("candidate_id"))
            if current is None:
                violations.append("existing candidate missing: %s" % prior.get("candidate_id"))
                continue
            old_history = prior.get("verification_history")
            new_history = current.get("verification_history")
            if not isinstance(old_history, list) or not isinstance(new_history, list) or new_history[:len(old_history)] != old_history:
                violations.append("existing history changed: %s" % prior.get("candidate_id"))
            if current.get("candidate_key") != prior.get("candidate_key"):
                violations.append("existing candidate key changed: %s" % prior.get("candidate_id"))
            if isinstance(old_history, list) and isinstance(new_history, list):
                tail = new_history[len(old_history):]
                if tail and all(
                    isinstance(snapshot, dict)
                    and isinstance(snapshot.get("inputs"), dict)
                    and snapshot["inputs"].get("kind") == "recheck"
                    for snapshot in tail
                ):
                    for field in CANDIDATE_FIELDS:
                        if field not in RECHECK_MUTABLE_FIELDS and current.get(field) != prior.get(field):
                            violations.append("recheck changed immutable field %s: %s" % (field, prior.get("candidate_id")))
    return violations


def _program_rules_input(path: Optional[str]) -> Tuple[Optional[str], Optional[Dict[str, object]]]:
    if path is None:
        return None, None
    if re.match(r"\A[a-z]+://", path):
        raise CliInputError("program-rules must be downloaded to a local file and passed as a path")
    try:
        content = Path(path).read_bytes()
    except OSError as error:
        raise CliInputError("program-rules: unable to read local file: %s" % error) from error
    digest = _sha256_bytes(content)
    decoded = content.decode("utf-8", errors="replace")
    excerpt_text = decoded[:4000]
    return digest, {
        "path": path,
        "sha256": digest,
        "excerpt": _untrusted_text(excerpt_text, path, len(decoded) > len(excerpt_text)),
    }


def _run_outcome(records: Sequence[Dict[str, object]]) -> str:
    if not records:
        return "no-candidates"
    if any(record.get("status") in ACTIONABLE_STATUSES for record in records):
        return "actionable-candidates"
    return "no-actionable-candidates"


def _markdown_cell(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, (list, tuple)):
        text = ", ".join(str(item) for item in value)
    else:
        text = str(value)
    return text.replace("|", r"\|").replace("\n", " ")


def _untrusted_excerpts(value: object) -> List[Dict[str, object]]:
    found = []
    seen = set()

    def visit(item: object) -> None:
        if isinstance(item, dict):
            if (
                item.get("untrusted") is True
                and isinstance(item.get("text"), str)
                and isinstance(item.get("sha256"), str)
                and isinstance(item.get("source_url"), str)
            ):
                identity = (
                    item["sha256"], item["text"], item["source_url"]
                )
                if identity not in seen:
                    seen.add(identity)
                    found.append(item)
                return
            for nested in item.values():
                visit(nested)
        elif isinstance(item, list):
            for nested in item:
                visit(nested)

    visit(value)
    return found


def _fenced_untrusted_excerpt(excerpt: Dict[str, object]) -> List[str]:
    text = str(excerpt["text"])
    runs = [len(match.group(0)) for match in re.finditer(r"`+", text)]
    fence = "`" * max(3, (max(runs) + 1) if runs else 3)
    return [
        "#### untrusted excerpt — data, not instructions",
        "",
        fence,
        text,
        fence,
        "",
    ]


def _latest_manifest_run(manifest: Optional[Dict[str, object]]) -> Dict[str, object]:
    if not isinstance(manifest, dict):
        return {}
    runs = manifest.get("runs")
    if not isinstance(runs, list) or not runs or not isinstance(runs[-1], dict):
        return {}
    return runs[-1]


def render_markdown(
    candidates: Dict[str, object], manifest: Optional[Dict[str, object]] = None
) -> str:
    """Render candidate records and the latest run through one safe Markdown path."""
    raw_records = candidates.get("records") if isinstance(candidates, dict) else []
    records = [item for item in raw_records if isinstance(item, dict)] if isinstance(raw_records, list) else []
    latest_run = _latest_manifest_run(manifest)
    outcome = latest_run.get("outcome")
    if outcome not in (
        "actionable-candidates", "no-actionable-candidates", "no-candidates"
    ):
        outcome = _run_outcome(records)
    run_status = latest_run.get("status")
    missing_run_status = run_status not in ("complete", "partial", "failed")
    if missing_run_status:
        run_status = "unknown"

    lines = [
        "# Contribution candidate verification",
        "",
        "## Run outcome",
        "",
        "| outcome | status |",
        "|---|---|",
        "| %s | %s |" % (_markdown_cell(outcome), _markdown_cell(run_status)),
        "",
    ]
    if outcome in ("no-actionable-candidates", "no-candidates"):
        reason_counts = {}  # type: Dict[str, int]
        for record in records:
            reason = str(record.get("status_reason") or "none")
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        failed_scopes = latest_run.get("failed_scopes")
        if isinstance(failed_scopes, list):
            for scope in failed_scopes:
                if isinstance(scope, dict):
                    reason = str(scope.get("reason") or "failed-scope")
                    reason_counts[reason] = reason_counts.get(reason, 0) + 1
        if not reason_counts:
            reason_counts["no-records"] = 1
        lines.extend(["| reason | count |", "|---|---:|"])
        for reason in sorted(reason_counts):
            lines.append(
                "| %s | %d |" % (_markdown_cell(reason), reason_counts[reason])
            )
        lines.append("")

    status_counts = {}  # type: Dict[str, int]
    for record in records:
        status = str(record.get("status") or "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    lines.extend([
        "## Status summary",
        "",
        "| status | count |",
        "|---|---:|",
    ])
    ordered_statuses = list(STATUS_REASON_TABLE)
    ordered_statuses.extend(
        sorted(status for status in status_counts if status not in STATUS_REASON_TABLE)
    )
    for status in ordered_statuses:
        count = status_counts.get(status, 0)
        if count:
            lines.append("| %s | %d |" % (_markdown_cell(status), count))
    if not status_counts:
        lines.append("| none | 0 |")
    lines.append("")

    warning_values = []
    if missing_run_status:
        warning_values.append("run status evidence unavailable")
    raw_warnings = latest_run.get("warnings")
    if isinstance(raw_warnings, list):
        warning_values.extend(str(item) for item in raw_warnings)
    if _has_secret_like_string([candidates, manifest]):
        warning_values.append("secret-like-string-redacted")
    warning_values = list(dict.fromkeys(warning_values))
    failed_scopes = latest_run.get("failed_scopes")
    failed_scopes = failed_scopes if isinstance(failed_scopes, list) else []
    lines.extend(["## Warnings and failed scopes", ""])
    lines.append("- Run status: `%s`" % run_status)
    if warning_values:
        for warning in warning_values:
            lines.append("- Warning: `%s`" % _markdown_cell(warning))
    else:
        lines.append("- Warnings: none")
    if failed_scopes:
        lines.extend(["", "| repository | pattern_id | reason |", "|---|---|---|"])
        for scope in failed_scopes:
            if isinstance(scope, dict):
                lines.append(
                    "| %s | %s | %s |"
                    % (
                        _markdown_cell(scope.get("repository")),
                        _markdown_cell(scope.get("pattern_id")),
                        _markdown_cell(scope.get("reason")),
                    )
                )
    else:
        lines.append("- Failed scopes: none")
    lines.append("")

    for record in records:
        candidate_id = _markdown_cell(record.get("candidate_id"))
        lines.extend([
            "## Candidate %s" % candidate_id,
            "",
            "| field | value |",
            "|---|---|",
            "| candidate_id | %s |" % candidate_id,
            "| status | %s / %s |"
            % (
                _markdown_cell(record.get("status")),
                _markdown_cell(record.get("status_reason")),
            ),
            "| repository | %s |" % _markdown_cell(record.get("repository")),
            "| verified_base_sha | %s |"
            % _markdown_cell(record.get("verified_base_sha")),
            "| verified_at | %s |" % _markdown_cell(record.get("verified_at")),
            "",
            "### Evidence links",
            "",
        ])
        evidence_links = record.get("evidence_links")
        if isinstance(evidence_links, list) and evidence_links:
            lines.extend("- %s" % str(link) for link in evidence_links)
        else:
            lines.append("- none")
        lines.extend(["", "### Blocking gaps", ""])
        blocking_gaps = record.get("blocking_gaps")
        if isinstance(blocking_gaps, list) and blocking_gaps:
            lines.extend(["| gap |", "|---|"])
            for gap in blocking_gaps:
                lines.append("| %s |" % _markdown_cell(gap))
        else:
            lines.append("- none")
        readiness = record.get("readiness_checks")
        unconfirmed = []
        if isinstance(readiness, dict):
            unconfirmed = [
                key
                for key in READINESS_KEYS
                if isinstance(readiness.get(key), dict)
                and readiness[key].get("result") == "not-confirmed"
            ]
        lines.extend(["", "### Unconfirmed readiness checks", ""])
        if unconfirmed:
            lines.extend("- `%s`" % key for key in unconfirmed)
        else:
            lines.append("- none")
        if record.get("status") in READY_STATUSES:
            lines.extend([
                "",
                "> 실제 제안 직전 `recheck` 필수 — verified_at: `%s`, verified_base_sha: `%s`"
                % (
                    _markdown_cell(record.get("verified_at")),
                    _markdown_cell(record.get("verified_base_sha")),
                ),
            ])
        excerpts = _untrusted_excerpts(record.get("duplicate_search"))
        if excerpts:
            lines.extend(["", "### Untrusted excerpts", ""])
            for excerpt in excerpts:
                lines.extend(_fenced_untrusted_excerpt(excerpt))
        lines.append("")

    lines.extend(["## Execution evidence summary", ""])
    if not records:
        lines.append("- No candidate execution evidence.")
    for record in records:
        lines.extend(["### %s" % _markdown_cell(record.get("candidate_id")), ""])
        if record.get("sensitivity") == "security-sensitive":
            lines.append("비공개 참조로 분리됨")
            lines.append("")
            continue
        reproduction = record.get("reproduction")
        method = reproduction.get("method") if isinstance(reproduction, dict) else "none"
        execution = record.get("execution_evidence")
        lines.append("- Reproduction method: `%s`" % _markdown_cell(method))
        if isinstance(execution, dict):
            lines.append("- Command: `%s`" % _markdown_cell(execution.get("command")))
            lines.append("- Isolation: `%s`" % _markdown_cell(execution.get("isolation")))
            lines.append("- Exit code: `%s`" % _markdown_cell(execution.get("exit_code")))
        else:
            lines.append("- Execution evidence: none")
        lines.append("")

    rendered = "\n".join(lines).rstrip() + "\n"
    redacted, redaction_warnings = redact(rendered)
    if redaction_warnings and "secret-like-string-redacted" not in redacted:
        redacted += "\n- Warning: `secret-like-string-redacted`\n"
    return redacted


def run_record(arguments: argparse.Namespace, *, clock: Callable[[], float]) -> int:
    output_path = Path(arguments.output)
    if arguments.candidates is not None and output_path.resolve() == Path(arguments.candidates).resolve() and not arguments.replace:
        raise CliInputError("--replace is required when output equals candidates")
    discovery = _read_json_file(arguments.discovery, "discovery")
    _validate_discovery_document(discovery)
    assessment_document = _read_assessment(arguments.assessment)
    discovery_sha256 = _file_sha256(arguments.discovery)
    assessment_sha256 = _file_sha256(arguments.assessment)
    if assessment_document["discovery_sha256"] != discovery_sha256:
        raise CliInputError("assessment.discovery_sha256 does not match discovery")
    program_rules_sha256, program_rules_input = _program_rules_input(arguments.program_rules)

    discovery_by_combo = {}
    for record in discovery["records"]:
        if isinstance(record, dict):
            discovery_by_combo[(record.get("pattern_id"), record.get("repository"))] = record
    forbidden_combos = set()
    for section in ("skipped_by_cap", "failed_scopes"):
        for item in discovery.get(section, []):
            if isinstance(item, dict):
                forbidden_combos.add((item.get("pattern_id"), item.get("repository")))

    assessed_by_combo = {}  # type: Dict[Tuple[object, object], List[Dict[str, object]]]
    seen_keys = set()
    gate_violations = []
    for index, assessment in enumerate(assessment_document["assessments"]):
        combo = (assessment.get("pattern_id"), assessment.get("repository"))
        record = discovery_by_combo.get(combo)
        if record is None or combo in forbidden_combos:
            gate_violations.append("assessments[%d]: combination is absent, skipped, or failed" % index)
            continue
        key = _candidate_key(str(assessment["pattern_id"]), str(record.get("repository_node_id")), str(assessment["locus"]))
        if key in seen_keys:
            gate_violations.append("assessments[%d]: duplicate candidate_key" % index)
        seen_keys.add(key)
        assessed_by_combo.setdefault(combo, []).append(assessment)
        for violation in _assessment_gate_violations(assessment, record, program_rules_sha256):
            gate_violations.append("assessments[%d].%s" % (index, violation))
    if gate_violations:
        raise CliInputError("; ".join(gate_violations))

    candidates = _candidate_document(arguments.candidates)
    existing_records = list(candidates["records"])
    by_key = {record["candidate_key"]: record for record in existing_records}
    max_id = 0
    for record in existing_records:
        match = re.fullmatch(r"CAN-(\d+)", str(record.get("candidate_id")))
        if match is not None:
            max_id = max(max_id, int(match.group(1)))
    generated_by = {"name": "verifying-open-source-contribution-candidates", "revision": compute_revision()}
    new_records = []
    updated_keys = set()
    for combo, discovery_record in discovery_by_combo.items():
        assessments = assessed_by_combo.get(combo)
        if not assessments:
            assessments = [_missing_assessment(discovery_record)]
        for assessment in assessments:
            key = _candidate_key(str(assessment["pattern_id"]), str(discovery_record["repository_node_id"]), str(assessment["locus"]))
            prior = by_key.get(key)
            if prior is None:
                max_id += 1
                candidate_id = "CAN-%03d" % max_id
                history = []
            else:
                candidate_id = prior["candidate_id"]
                history = json.loads(json.dumps(prior["verification_history"]))
            snapshot = _snapshot(candidate_id, discovery_record, assessment, len(history), discovery_sha256, assessment_sha256)
            history.append(snapshot)
            candidate = {
                "candidate_id": candidate_id,
                "candidate_key": key,
                "generated_by": generated_by,
                "pattern_ids": [assessment["pattern_id"]],
                "pattern_revisions": {assessment["pattern_id"]: discovery_record["pattern_revision"]},
                "repository": discovery_record["repository"],
                "repository_node_id": discovery_record["repository_node_id"],
                "locus": assessment["locus"],
                "status": assessment["status"],
                "status_reason": assessment["status_reason"],
                "sensitivity": assessment["sensitivity"],
                "summary": assessment["summary"],
                "impact": assessment["impact"],
                "readiness_checks": json.loads(json.dumps(assessment["readiness_checks"])),
                "ai_policy_status": assessment["ai_policy_status"],
                "disclosure_required": assessment["disclosure_required"],
                "private_evidence_reference": assessment["private_evidence_reference"],
                "evidence_links": list(assessment["evidence_links"]),
                "execution_evidence": json.loads(json.dumps(assessment["execution_evidence"])),
                "reproduction": json.loads(json.dumps(assessment["reproduction"])),
                "policy_checks": json.loads(json.dumps(assessment["policy_checks"])),
                "blocking_gaps": list(assessment["blocking_gaps"]),
                "superseded_by": assessment["superseded_by"],
                "duplicate_search": json.loads(json.dumps(discovery_record["duplicate_search"])),
                "repository_checks": json.loads(json.dumps(discovery_record["repository_checks"])),
                "verification_history": history,
                "verified_at": discovery_record["observed_at"],
                "verified_base_sha": discovery_record["head_sha"],
                "next_recheck_required": assessment["status"] in READY_STATUSES,
            }
            new_records.append(candidate)
            updated_keys.add(key)
    replacements = {record["candidate_key"]: record for record in new_records}
    output_records = [
        replacements.get(record["candidate_key"], record)
        for record in existing_records
    ]
    output_records.extend(
        record for record in new_records if record["candidate_key"] not in by_key
    )
    id_set = {record["candidate_id"] for record in output_records}
    supersession_violations = []
    for record in output_records:
        target = record.get("superseded_by")
        if target is not None and (target not in id_set or target == record["candidate_id"]):
            supersession_violations.append("%s.superseded_by" % record["candidate_id"])
    if supersession_violations:
        raise CliInputError("; ".join(supersession_violations))
    result = {"schema_version": "1.0.0", "generated_by": generated_by, "records": output_records}
    violations = validate_candidates_document(result, candidates if arguments.candidates else None)
    if violations:
        raise CliInputError("candidate output invalid: " + "; ".join(violations))

    manifest_path = Path(arguments.manifest)
    manifest = _manifest_document(manifest_path, generated_by)
    now = _utc_observation(clock)
    ordered_repositories = []
    for discovery_record in discovery["records"]:
        repository = discovery_record.get("repository")
        if repository not in ordered_repositories:
            ordered_repositories.append(repository)
    inputs = {
        "discovery_sha256": discovery_sha256,
        "assessment_sha256": assessment_sha256,
        "program_rules": program_rules_input,
    }
    run = {
        "run_id": "RUN-%03d" % (len(manifest["runs"]) + 1), "command": "record",
        "started_at": now, "completed_at": now, "inputs": inputs,
        "budget": {"request_limit": 0, "requests_consumed": 0, "per_repo_cap": None, "total_cap": None},
        "repositories": [],
        "clones": [], "failed_scopes": list(discovery.get("failed_scopes", [])),
        "retry_events": [], "method_limitations": list(discovery.get("method_limitations", [])),
        "warnings": [], "status": discovery["status"], "outcome": _run_outcome(output_records),
    }
    ordered_repositories = list(discovery["inputs"]["repositories"])
    records_by_repository = {}
    for discovery_record in discovery["records"]:
        records_by_repository.setdefault(discovery_record["repository"], []).append(
            discovery_record
        )
        for warning in discovery_record.get("warnings", []):
            if isinstance(warning, str) and warning not in run["warnings"]:
                run["warnings"].append(warning)
    failed_by_repository = {}
    for scope in discovery["failed_scopes"]:
        failed_by_repository.setdefault(scope["repository"], []).append(scope["reason"])
    failure_outcomes = {
        "repository-not-found-or-inaccessible": "not-found-or-inaccessible",
        "repository-unauthorized": "unauthorized",
        "repository-forbidden": "forbidden",
        "repository-failed": "failed",
    }
    for repository in ordered_repositories:
        repository_records = records_by_repository.get(repository, [])
        reasons = failed_by_repository.get(repository, [])
        reason = None
        outcome = "checked"
        if "budget-exhausted" in reasons:
            reason = "budget-exhausted"
            outcome = "checked" if repository_records else "budget-exhausted"
        elif reasons:
            reason = reasons[0]
            outcome = failure_outcomes.get(reason, "failed")
        run["repositories"].append(
            {
                "repository": repository,
                "outcome": outcome,
                "reason": reason,
                "stages_completed": ["record"] if repository_records else [],
                "head_sha": (
                    repository_records[0].get("head_sha")
                    if repository_records
                    else None
                ),
            }
        )
    if _has_secret_like_string([result, run]):
        run["warnings"].append("secret-like-string-redacted")
    manifest["runs"].append(run)
    write_json_atomic(output_path, result)
    write_json_atomic(manifest_path, manifest)
    if arguments.markdown_output:
        write_text_atomic(
            Path(arguments.markdown_output), render_markdown(result, manifest)
        )
    print("complete: recorded %d candidates" % len(output_records))
    return 0


def run_validate(arguments: argparse.Namespace) -> int:
    try:
        candidates = _read_json_file(arguments.candidates, "candidates")
        existing = _read_json_file(arguments.existing, "existing") if arguments.existing else None
    except CliInputError as error:
        _write_stderr("validation: %s" % error)
        return 1
    violations = []
    if existing is not None:
        violations.extend(
            "existing: " + violation
            for violation in validate_candidates_document(existing)
        )
    violations.extend(validate_candidates_document(candidates, existing))
    if violations:
        for violation in violations:
            _write_stderr("validation: %s" % violation)
        return 1
    print("valid")
    return 0


def run_render(arguments: argparse.Namespace) -> int:
    candidates = _read_json_file(arguments.candidates, "candidates")
    violations = validate_candidates_document(candidates)
    if violations:
        raise CliInputError("candidates: " + "; ".join(violations))
    manifest = (
        _read_json_file(arguments.manifest, "manifest")
        if arguments.manifest is not None
        else None
    )
    write_text_atomic(
        Path(arguments.output), render_markdown(candidates, manifest)
    )
    print("complete: rendered %d candidates" % len(candidates["records"]))
    return 0


def _duplicate_urls(duplicate_search: object) -> set:
    urls = set()
    if not isinstance(duplicate_search, dict):
        return urls
    for query in duplicate_search.get("queries", []):
        if not isinstance(query, dict):
            continue
        for item in query.get("items", []):
            if isinstance(item, dict) and isinstance(item.get("html_url"), str):
                urls.add(item["html_url"])
    return urls


def _recheck_duplicate_search(
    client: object,
    repository: str,
    previous: Dict[str, object],
    warnings: List[str],
) -> Dict[str, object]:
    queries = []
    complete = True
    for previous_query in previous.get("queries", []):
        if not isinstance(previous_query, dict) or not isinstance(previous_query.get("q"), str):
            complete = False
            continue
        query = previous_query["q"]
        if not _trusted_duplicate_query(repository, query):
            complete = False
            warning = "unsafe-stored-query-rejected"
            if warning not in warnings:
                warnings.append(warning)
            continue
        response = client.get_json("/search/issues", {"q": query})
        request_path = _request_path("/search/issues", {"q": query})
        payload_valid = _valid_search_payload(response.payload)
        payload = response.payload if payload_valid else {}
        succeeded = 200 <= response.status < 300 and payload_valid
        incomplete = payload.get("incomplete_results") is True
        if 200 <= response.status < 300 and not payload_valid:
            complete = False
            _append_invalid_payload_warning(warnings, request_path, "search")
        elif not succeeded:
            complete = False
            _append_response_warning(warnings, response, request_path)
        if incomplete:
            complete = False
        items = []
        raw_items = payload.get("items") if isinstance(payload.get("items"), list) else []
        for raw_item in raw_items:
            item = _issue_item(raw_item)
            if item is not None:
                items.append(item)
        queries.append(
            {
                "q": query,
                "total_count": payload.get("total_count") if succeeded else None,
                "incomplete_results": incomplete if succeeded else True,
                "items": items,
            }
        )
    return {
        "queries": queries,
        "complete": complete,
        "unused_clues": list(previous.get("unused_clues", [])),
        "method_limitations": [SEARCH_INDEX_LIMITATION],
    }


def _reobserved_policy_checks(
    previous: Dict[str, object], policy_files: Sequence[Dict[str, object]]
) -> Dict[str, object]:
    current_by_path = {}  # type: Dict[str, List[str]]
    failed_paths = set()
    for item in policy_files:
        if item.get("found") is True and isinstance(item.get("sha256"), str):
            current_by_path.setdefault(str(item.get("path")), []).append(item["sha256"])
        if item.get("status") == "request-failed":
            failed_paths.add(str(item.get("path")))
    result = json.loads(json.dumps(previous))
    for key, paths in POLICY_CHECK_PATHS.items():
        item = result.get(key)
        if not isinstance(item, dict):
            continue
        if failed_paths.intersection(paths):
            item.update(
                {
                    "found": None,
                    "source": None,
                    "sha256": None,
                    "assessment": "recheck observation failed",
                    "evidence_links": [],
                }
            )
            continue
        if item.get("found") is not True:
            continue
        available = []
        for path in paths:
            available.extend(current_by_path.get(path, []))
        previous_sha = item.get("sha256")
        if previous_sha in available:
            item["found"] = True
            item["sha256"] = previous_sha
        elif available:
            item["found"] = True
            item["sha256"] = available[0]
        else:
            item["found"] = False
            item["sha256"] = None
    return result


def _policy_signature(policy_checks: object) -> Tuple[Tuple[str, object, object], ...]:
    if not isinstance(policy_checks, dict):
        return tuple()
    return tuple(
        (key, value.get("found"), value.get("sha256"))
        for key, value in sorted(policy_checks.items())
        if isinstance(value, dict)
    )


def _recheck_snapshot(
    record: Dict[str, object],
    repository_checks: Dict[str, object],
    duplicate_search: Dict[str, object],
    policy_checks: Dict[str, object],
    observed_head_sha: Optional[str],
) -> Dict[str, object]:
    previous = record["verification_history"][-1]
    previous_evidence = previous["evidence"]
    history_length = len(record["verification_history"])
    evidence = {
        "duplicate_search": json.loads(json.dumps(duplicate_search)),
        "repository_checks": json.loads(json.dumps(repository_checks)),
        "policy_checks": json.loads(json.dumps(policy_checks)),
        "observed_head_sha": observed_head_sha,
    }
    for name in INHERITED_EVIDENCE_FIELDS:
        evidence[name] = json.loads(json.dumps(previous_evidence[name]))
    return {
        "verification_id": "VER-%s-%d" % (record["candidate_id"], history_length + 1),
        "revision": compute_revision(),
        "verified_at": record["verified_at"],
        "verified_base_sha": record["verified_base_sha"],
        "status": record["status"],
        "status_reason": record["status_reason"],
        "sensitivity": record["sensitivity"],
        "evidence": evidence,
        "inputs": {"kind": "recheck", "discovery_sha256": None, "assessment_sha256": None},
    }


def _failed_recheck_duplicate_search() -> Dict[str, object]:
    return {
        "queries": [],
        "complete": False,
        "unused_clues": [],
        "method_limitations": [SEARCH_INDEX_LIMITATION],
    }


def _failed_recheck_policy_checks() -> Dict[str, object]:
    return {
        key: {
            "found": None,
            "source": None,
            "sha256": None,
            "assessment": "recheck observation failed",
            "evidence_links": [],
        }
        for key in POLICY_CHECK_KEYS
    }


def _block_failed_recheck(record: Dict[str, object]) -> None:
    if record.get("status") not in ACTIONABLE_STATUSES:
        return
    previous = record["verification_history"][-1]
    previous_evidence = previous["evidence"]
    duplicate_search = _failed_recheck_duplicate_search()
    evidence = {
        "duplicate_search": json.loads(json.dumps(duplicate_search)),
        "repository_checks": None,
        "policy_checks": _failed_recheck_policy_checks(),
        "observed_head_sha": None,
    }
    for name in INHERITED_EVIDENCE_FIELDS:
        evidence[name] = json.loads(json.dumps(previous_evidence[name]))
    record["status"] = "unverified"
    record["status_reason"] = "insufficient-evidence"
    gaps = list(record["blocking_gaps"])
    if "recheck-failed" not in gaps:
        gaps.append("recheck-failed")
    record["blocking_gaps"] = gaps
    record["next_recheck_required"] = False
    record["repository_checks"] = None
    record["duplicate_search"] = json.loads(json.dumps(duplicate_search))
    record["verification_history"].append(
        {
            "verification_id": "VER-%s-%d"
            % (record["candidate_id"], len(record["verification_history"]) + 1),
            "revision": compute_revision(),
            "verified_at": record["verified_at"],
            "verified_base_sha": record["verified_base_sha"],
            "status": record["status"],
            "status_reason": record["status_reason"],
            "sensitivity": record["sensitivity"],
            "evidence": evidence,
            "inputs": {
                "kind": "recheck",
                "discovery_sha256": None,
                "assessment_sha256": None,
            },
        }
    )


def _append_recheck_failure_warning(
    warnings: List[str], record: Dict[str, object], reason: str
) -> None:
    if "recheck-failed" not in warnings:
        warnings.append("recheck-failed")
    warning = "recheck-failed:%s:%s:%s" % (
        record["candidate_id"],
        record["repository"],
        reason,
    )
    if warning not in warnings:
        warnings.append(warning)


def _recheck_repository(
    client: object,
    record: Dict[str, object],
    observed_at: str,
) -> Tuple[Optional[Dict[str, object]], Dict[str, object], List[str]]:
    repository = record["repository"]
    warnings = []  # type: List[str]
    endpoint = "/repos/" + repository
    response = client.get_json(endpoint)
    if not 200 <= response.status < 300 or not isinstance(response.payload, dict):
        _append_response_warning(warnings, response, endpoint)
        return None, {
            "repository": repository,
            "outcome": _repository_failure(response.status, response.headers)[0],
            "reason": _repository_failure(response.status, response.headers)[1],
            "stages_completed": [],
            "head_sha": None,
        }, warnings
    checks = _repository_checks(response.payload)
    previous_checks = record.get("repository_checks")
    if isinstance(previous_checks, dict):
        checks["community_profile_files"] = json.loads(
            json.dumps(previous_checks.get("community_profile_files", checks["community_profile_files"]))
        )
        checks["private_vulnerability_reporting"] = previous_checks.get("private_vulnerability_reporting")
    stages = ["repository"]
    head_endpoint = "/repos/%s/commits/%s" % (repository, checks["default_branch"])
    head_response = client.get_json(head_endpoint)
    head_payload = head_response.payload if isinstance(head_response.payload, dict) else {}
    observed_head = head_payload.get("sha")
    if not (200 <= head_response.status < 300 and isinstance(observed_head, str) and re.fullmatch(r"[0-9a-fA-F]{40}", observed_head)):
        _append_response_warning(warnings, head_response, head_endpoint)
        return None, {
            "repository": repository, "outcome": "checked", "reason": "transport-or-5xx",
            "stages_completed": stages, "head_sha": None,
        }, warnings
    observed_head = observed_head.lower()
    stages.append("head")
    duplicate = _recheck_duplicate_search(
        client, repository, record["duplicate_search"], warnings
    )
    stages.append("duplicate_search")
    if duplicate.get("complete") is not True:
        return None, {
            "repository": repository,
            "outcome": "checked",
            "reason": "transport-or-5xx",
            "stages_completed": stages,
            "head_sha": observed_head,
        }, warnings
    policy_files = discover_policy_files(client, repository, checks["default_branch"], warnings)
    stages.append("policy_files")
    if _policy_request_failure_keys(repository, policy_files):
        return None, {
            "repository": repository,
            "outcome": "checked",
            "reason": "transport-or-5xx",
            "stages_completed": stages,
            "head_sha": observed_head,
        }, warnings
    previous_policy = record["verification_history"][-1]["evidence"]["policy_checks"]
    policy_checks = _reobserved_policy_checks(previous_policy, policy_files)
    observation = {
        "observed_at": observed_at,
        "observed_head_sha": observed_head,
        "repository_checks": checks,
        "duplicate_search": duplicate,
        "policy_checks": policy_checks,
    }
    return observation, {
        "repository": repository, "outcome": "checked", "reason": None,
        "stages_completed": stages, "head_sha": observed_head,
    }, warnings


def run_recheck(
    arguments: argparse.Namespace,
    *,
    runner: Callable[..., Any],
    sleeper: Callable[[float], None],
    clock: Callable[[], float],
) -> int:
    candidates = _candidate_document(arguments.candidates)
    selected_ids = list(arguments.candidate)
    if len(selected_ids) != len(set(selected_ids)):
        raise CliInputError("candidate values must not contain duplicates")
    by_id = {record["candidate_id"]: record for record in candidates["records"]}
    for candidate_id in selected_ids:
        if re.fullmatch(r"CAN-\d{3,}", candidate_id) is None or candidate_id not in by_id:
            raise CliInputError("candidate not found: %s" % candidate_id)
    selected_set = set(selected_ids) if selected_ids else set(by_id)
    budget = RequestBudget(arguments.request_budget)
    if arguments.fixture_dir:
        try:
            client = FixtureTransport(Path(arguments.fixture_dir), budget=budget, sleeper=sleeper, clock=clock)
        except ValueError as error:
            raise CliInputError(str(error)) from error
    else:
        client = GhApiClient(runner=runner, sleeper=sleeper, clock=clock, budget=budget)
    started_at = _utc_observation(clock)
    output_records = []
    repositories = []
    warnings = []
    partial = False
    exhausted = False
    for source in candidates["records"]:
        record = json.loads(json.dumps(source))
        if record["candidate_id"] not in selected_set:
            output_records.append(record)
            continue
        if exhausted:
            partial = True
            if not any(item["repository"] == record["repository"] for item in repositories):
                repositories.append({"repository": record["repository"], "outcome": "budget-exhausted", "reason": "budget-exhausted", "stages_completed": [], "head_sha": None})
            _block_failed_recheck(record)
            _append_recheck_failure_warning(
                warnings, record, "budget-exhausted-before-start"
            )
            output_records.append(record)
            continue
        try:
            observation, repository_run, candidate_warnings = _recheck_repository(client, record, _utc_observation(clock))
        except BudgetExhausted:
            exhausted = True
            partial = True
            repository_run = {"repository": record["repository"], "outcome": "budget-exhausted", "reason": "budget-exhausted", "stages_completed": [], "head_sha": None}
            observation = None
            candidate_warnings = ["recheck-failed", "budget-exhausted"]
        if not any(item["repository"] == repository_run["repository"] for item in repositories):
            repositories.append(repository_run)
        for warning in candidate_warnings:
            if warning not in warnings:
                warnings.append(warning)
        if observation is None:
            partial = True
            _block_failed_recheck(record)
            _append_recheck_failure_warning(
                warnings, record, str(repository_run["reason"])
            )
            output_records.append(record)
            continue
        if candidate_warnings or observation["duplicate_search"].get("complete") is not True:
            partial = True
        previous_snapshot = record["verification_history"][-1]
        previous_duplicate = previous_snapshot["evidence"]["duplicate_search"]
        previous_policy = previous_snapshot["evidence"]["policy_checks"]
        record["verified_at"] = observation["observed_at"]
        record["repository_checks"] = observation["repository_checks"]
        record["duplicate_search"] = observation["duplicate_search"]
        gaps = list(record["blocking_gaps"])
        if record["verified_base_sha"] is None:
            record["status"] = "unverified"
            record["status_reason"] = "insufficient-evidence"
            if "base-sha-unknown" not in gaps:
                gaps.append("base-sha-unknown")
        elif observation["observed_head_sha"] != record["verified_base_sha"]:
            record["status"] = "stale"
            record["status_reason"] = "base-moved"
        else:
            new_urls = _duplicate_urls(observation["duplicate_search"]) - _duplicate_urls(previous_duplicate)
            policy_changed = _policy_signature(observation["policy_checks"]) != _policy_signature(previous_policy)
            if new_urls:
                record["status"] = "policy-review"
                record["status_reason"] = "none"
                if "duplicate-search-changed" not in gaps:
                    gaps.append("duplicate-search-changed")
            if policy_changed:
                record["status"] = "policy-review"
                record["status_reason"] = "none"
                if "policy-files-changed" not in gaps:
                    gaps.append("policy-files-changed")
        record["blocking_gaps"] = gaps
        record["next_recheck_required"] = record["status"] in READY_STATUSES
        snapshot = _recheck_snapshot(
            record, observation["repository_checks"], observation["duplicate_search"],
            observation["policy_checks"], observation["observed_head_sha"],
        )
        record["verification_history"].append(snapshot)
        output_records.append(record)

    result = {
        "schema_version": "1.0.0",
        "generated_by": {"name": "verifying-open-source-contribution-candidates", "revision": compute_revision()},
        "records": output_records,
    }
    violations = validate_candidates_document(result, candidates)
    if violations:
        raise CliInputError("recheck output invalid: " + "; ".join(violations))
    completed_at = _utc_observation(clock)
    manifest_path = Path(arguments.manifest)
    manifest = _manifest_document(manifest_path, result["generated_by"])
    status = "partial" if partial else "complete"
    run = {
        "run_id": "RUN-%03d" % (len(manifest["runs"]) + 1), "command": "recheck",
        "started_at": started_at, "completed_at": completed_at,
        "inputs": {"candidate_ids": selected_ids or [record["candidate_id"] for record in candidates["records"]]},
        "budget": {"request_limit": arguments.request_budget, "requests_consumed": budget.consumed, "per_repo_cap": None, "total_cap": None},
        "repositories": repositories, "clones": [], "failed_scopes": [],
        "retry_events": list(client.request_events), "method_limitations": [SEARCH_INDEX_LIMITATION],
        "warnings": warnings, "status": status, "outcome": _run_outcome(output_records),
    }
    if _has_secret_like_string([result, run]):
        if "secret-like-string-redacted" not in warnings:
            warnings.append("secret-like-string-redacted")
        run["warnings"] = warnings
    manifest["runs"].append(run)
    write_json_atomic(Path(arguments.output), result)
    write_json_atomic(manifest_path, manifest)
    if arguments.markdown_output:
        write_text_atomic(
            Path(arguments.markdown_output), render_markdown(result, manifest)
        )
    print("%s: rechecked %d candidates" % (status, len(selected_set)))
    return 3 if partial else 0


def _stub(command: str) -> int:
    _write_stderr("%s is not implemented yet" % command)
    return 2


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    runner: Callable[..., Any] = subprocess.run,
    sleeper: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.time,
) -> int:
    """Parse the verifier interface and execute implemented operations."""
    parser = build_parser()
    try:
        arguments = parser.parse_args(list(argv) if argv is not None else None)
        if arguments.print_revision:
            print(compute_revision())
            return 0
        if arguments.command is None:
            raise CliInputError("a subcommand is required")
        if arguments.command == "discover":
            _validate_discover_arguments(arguments)
            analysis = _read_analysis(arguments.analysis)
            _validate_selected_patterns(analysis, arguments.pattern)
            return run_discover(
                arguments,
                analysis,
                runner=runner,
                sleeper=sleeper,
                clock=clock,
            )
        elif arguments.command == "record":
            if arguments.program_rules is not None and re.match(
                r"\A[a-z]+://", arguments.program_rules
            ):
                raise CliInputError(
                    "program-rules: 파일로 내려받아 local path를 주십시오 (downloaded local file required)"
                )
            return run_record(arguments, clock=clock)
        elif arguments.command == "validate":
            return run_validate(arguments)
        elif arguments.command == "recheck":
            return run_recheck(
                arguments,
                runner=runner,
                sleeper=sleeper,
                clock=clock,
            )
        elif arguments.command == "render":
            return run_render(arguments)
        return _stub(arguments.command)
    except (CliInputError, ChildCommandError) as error:
        _write_stderr("error: %s" % error)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
