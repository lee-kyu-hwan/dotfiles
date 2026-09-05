"""Deterministic primitives for collecting recently closed pull requests."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
import json
import re
import subprocess
import threading
import time as clock_time
from typing import Any, Callable, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


RFC3339_TIMESTAMP = re.compile(
    r"\A\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)\Z"
)
HTTP_STATUS = re.compile(r"\AHTTP(?:/[^ ]+)?\s+(\d{3})(?:\s|\Z)", re.IGNORECASE)
API_VERSION = "2026-03-10"
MAX_RETRIES = 3
MAX_RATE_LIMIT_WAIT_SECONDS = 5 * 60
_MISSING = object()


@dataclass(frozen=True)
class Interval:
    start_at: str
    end_at: str
    timezone: str
    input_mode: dict[str, object]
    as_of: str
    last_day_partial: bool


@dataclass(frozen=True)
class ApiResponse:
    """A sanitized, parsed response returned by GitHub's REST API."""

    status: int
    headers: dict[str, str]
    payload: object


class BudgetExhausted(RuntimeError):
    """Raised before an attempt that would exceed the global request budget."""


@dataclass
class RequestBudget:
    """A run-global count of API attempts, including retries."""

    limit: int
    consumed: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.limit, int) or isinstance(self.limit, bool) or self.limit <= 0:
            raise ValueError("request budget must be a positive integer")

    def consume(self) -> None:
        if self.consumed >= self.limit:
            raise BudgetExhausted("request budget exhausted")
        self.consumed += 1


class ApiFailure(RuntimeError):
    """A safe API failure suitable for manifest recording and classification."""

    def __init__(
        self,
        message: str,
        *,
        status: Optional[int] = None,
        endpoint: Optional[str] = None,
        diagnostics: str = "",
    ) -> None:
        safe_message = _redact_diagnostics(message) or "GitHub API failure"
        super().__init__(safe_message)
        self.status = status
        self.endpoint = endpoint
        self.diagnostics = _redact_diagnostics(diagnostics)


class GhApiClient:
    """A serial, read-only ``gh api`` transport with bounded retries."""

    def __init__(
        self,
        *,
        api_version: str = API_VERSION,
        budget: RequestBudget,
        runner: Callable[..., Any] = subprocess.run,
        sleeper: Callable[[float], None] = clock_time.sleep,
        clock: Callable[[], float] = clock_time.time,
    ) -> None:
        if not isinstance(api_version, str) or re.fullmatch(r"\d{4}-\d{2}-\d{2}", api_version) is None:
            raise ValueError("api_version must be YYYY-MM-DD")
        try:
            date.fromisoformat(api_version)
        except ValueError as error:
            raise ValueError("api_version must be a calendar date") from error
        self.api_version = api_version
        self.budget = budget
        self._runner = runner
        self._sleeper = sleeper
        self._clock = clock
        self._lock = threading.RLock()

    def get_json(
        self,
        endpoint: str,
        params: Optional[dict[str, object]] = None,
        *,
        cached_payload: object = _MISSING,
        cached_etag: Optional[str] = None,
    ) -> ApiResponse:
        """Fetch one JSON response, conditionally reusing exact cached evidence."""
        if not isinstance(endpoint, str) or not endpoint.startswith("/"):
            raise ValueError("endpoint must be an absolute GitHub API path")
        if params is not None and "per_page" in params:
            raise ValueError("per_page is fixed at 100")
        if cached_etag is not None and not isinstance(cached_etag, str):
            raise ValueError("cached_etag must be a string")

        with self._lock:
            return self._get_json_serial(
                endpoint,
                params=params,
                cached_payload=cached_payload,
                cached_etag=cached_etag,
            )

    def global_preflight(self) -> dict[str, str]:
        """Verify gh, authentication, and requested API version before collection."""
        with self._lock:
            client_version = self._gh_version()
            user = self.get_json("/user")
            if not isinstance(user.payload, dict) or not isinstance(user.payload.get("login"), str):
                raise ApiFailure("authenticated user response has no login", status=user.status, endpoint="/user")
            versions = self.get_json("/versions")
            supported_versions = _versions_from_payload(versions.payload)
            if self.api_version not in supported_versions:
                raise ApiFailure(
                    "configured GitHub API version is unsupported",
                    status=versions.status,
                    endpoint="/versions",
                )
            return {
                "login": user.payload["login"],
                "client_version": client_version,
                "api_version": self.api_version,
            }

    def _get_json_serial(
        self,
        endpoint: str,
        *,
        params: Optional[dict[str, object]],
        cached_payload: object,
        cached_etag: Optional[str],
    ) -> ApiResponse:
        command = self._api_command(endpoint, params, cached_etag)
        for attempt in range(MAX_RETRIES + 1):
            self.budget.consume()
            try:
                completed = self._runner(
                    command,
                    capture_output=True,
                    text=True,
                    check=False,
                    shell=False,
                )
            except (OSError, subprocess.SubprocessError) as error:
                failure = ApiFailure(
                    "GitHub CLI transport failed",
                    endpoint=endpoint,
                    diagnostics=str(error),
                )
                if attempt == MAX_RETRIES:
                    raise failure
                self._sleeper(_transport_backoff(attempt))
                continue

            diagnostics = _redact_diagnostics(getattr(completed, "stderr", ""))
            try:
                status, headers, body = _parse_included_response(getattr(completed, "stdout", ""))
            except ValueError as error:
                failure = ApiFailure(
                    "GitHub CLI returned no parseable HTTP response",
                    endpoint=endpoint,
                    diagnostics=diagnostics,
                )
                if attempt == MAX_RETRIES or getattr(completed, "returncode", 1) == 0:
                    raise failure from error
                self._sleeper(_transport_backoff(attempt))
                continue

            if status == 304:
                if (
                    cached_payload is _MISSING
                    or cached_etag is None
                    or headers.get("etag") != cached_etag
                ):
                    raise ApiFailure(
                        "304 response has no matching cached payload and ETag",
                        status=status,
                        endpoint=endpoint,
                        diagnostics=diagnostics,
                    )
                return ApiResponse(status=status, headers=headers, payload=cached_payload)

            if 200 <= status < 300:
                try:
                    payload = json.loads(body)
                except (TypeError, json.JSONDecodeError) as error:
                    raise ApiFailure(
                        "GitHub API returned malformed JSON",
                        status=status,
                        endpoint=endpoint,
                        diagnostics=diagnostics,
                    ) from error
                return ApiResponse(status=status, headers=headers, payload=payload)

            message = _response_message(body)
            failure = ApiFailure(
                message or "GitHub API request failed",
                status=status,
                endpoint=endpoint,
                diagnostics=diagnostics,
            )
            if not _is_retryable(status, headers, message) or attempt == MAX_RETRIES:
                raise failure
            self._sleeper(_retry_delay(status, headers, attempt, self._clock))

        raise AssertionError("bounded retry loop must return or raise")

    def _api_command(
        self,
        endpoint: str,
        params: Optional[dict[str, object]],
        cached_etag: Optional[str],
    ) -> list[str]:
        command = [
            "gh",
            "api",
            "--method",
            "GET",
            "--include",
            "-H",
            "Accept: application/vnd.github+json",
            "-H",
            f"X-GitHub-Api-Version: {self.api_version}",
        ]
        if cached_etag is not None:
            command.extend(["-H", f"If-None-Match: {cached_etag}"])
        command.append(endpoint)
        effective_params: dict[str, object] = {"per_page": 100}
        if params is not None:
            effective_params.update(params)
        for name, value in effective_params.items():
            command.extend(["-f", f"{name}={value}"])
        return command

    def _gh_version(self) -> str:
        try:
            completed = self._runner(
                ["gh", "--version"],
                capture_output=True,
                text=True,
                check=False,
                shell=False,
            )
        except (OSError, subprocess.SubprocessError) as error:
            raise ApiFailure("GitHub CLI is unavailable", diagnostics=str(error)) from error
        output = getattr(completed, "stdout", "")
        match = re.search(r"\bgh version ([^\s]+)", output)
        if getattr(completed, "returncode", 1) != 0 or match is None:
            raise ApiFailure(
                "GitHub CLI version check failed",
                diagnostics=getattr(completed, "stderr", ""),
            )
        return match.group(1)


def resolve_interval(
    *,
    start_at: Optional[str],
    end_at: Optional[str],
    start_date: Optional[str],
    end_date: Optional[str],
    recent_days: Optional[int],
    timezone_name: str,
    as_of: Optional[str],
) -> Interval:
    """Resolve one requested interval into whole-second UTC bounds."""
    input_timezone = _timezone(timezone_name)
    mode = _interval_mode(start_at, end_at, start_date, end_date, recent_days)

    if mode == "timestamps":
        if as_of is not None:
            raise ValueError("as_of is only valid with recent_days")
        start = _parse_timestamp(start_at, "start_at")
        end = _parse_timestamp(end_at, "end_at")
        input_mode: dict[str, object] = {"start_at": start_at, "end_at": end_at}
        last_day_partial = False
        resolved_as_of = end
    elif mode == "dates":
        if as_of is not None:
            raise ValueError("as_of is only valid with recent_days")
        local_start = _parse_date(start_date, "start_date")
        local_end = _parse_date(end_date, "end_date") + timedelta(days=1)
        start = datetime.combine(local_start, time.min, input_timezone)
        end = datetime.combine(local_end, time.min, input_timezone)
        input_mode = {"start_date": start_date, "end_date": end_date}
        last_day_partial = False
        resolved_as_of = end.astimezone(timezone.utc)
    else:
        if (
            not isinstance(recent_days, int)
            or isinstance(recent_days, bool)
            or recent_days <= 0
        ):
            raise ValueError("recent_days must be a positive integer")
        current = (
            _parse_timestamp(as_of, "as_of") if as_of is not None else datetime.now(timezone.utc)
        ).astimezone(input_timezone)
        local_start = current.date() - timedelta(days=recent_days - 1)
        start = datetime.combine(local_start, time.min, input_timezone)
        end = current
        input_mode = {"recent_days": recent_days}
        last_day_partial = True
        resolved_as_of = current.astimezone(timezone.utc)

    start = _whole_second(start)
    end = _whole_second(end)
    if start >= end:
        raise ValueError("start_at must be earlier than end_at")

    return Interval(
        start_at=_utc_string(start),
        end_at=_utc_string(end),
        timezone=timezone_name,
        input_mode=input_mode,
        as_of=_utc_string(resolved_as_of),
        last_day_partial=last_day_partial,
    )


def build_closed_query(repository: str, interval: Interval, outcome: str) -> str:
    """Build one Search API qualifier for a UTC half-open closed interval."""
    if outcome not in {"all", "merged", "closed-unmerged"}:
        raise ValueError("outcome must be all, merged, or closed-unmerged")

    start = _parse_timestamp(interval.start_at, "interval.start_at")
    end = _parse_timestamp(interval.end_at, "interval.end_at")
    if start >= end:
        raise ValueError("interval.start_at must be earlier than interval.end_at")

    qualifiers = [
        f"repo:{repository}",
        "is:pr",
        "is:closed",
        f"closed:{_utc_string(start)}..{_utc_string(end - timedelta(seconds=1))}",
    ]
    if outcome == "merged":
        qualifiers.append("is:merged")
    elif outcome == "closed-unmerged":
        qualifiers.append("-is:merged")
    return " ".join(qualifiers)


def migrate_manifest_v1(document: dict[str, object]) -> dict[str, object]:
    """Project a v1 fixture manifest into the v2 envelope without data loss."""
    if document.get("schema_version") != "1.0.0":
        raise ValueError("only manifest schema_version 1.0.0 can be migrated")

    legacy_document = deepcopy(document)
    legacy_runs = legacy_document.pop("runs", None)
    if not isinstance(legacy_runs, list):
        raise ValueError("manifest 1.0.0 runs must be a list")

    generated_by = legacy_document.pop("generated_by", None)
    legacy_document.pop("schema_version")
    records = [_migrate_run(run) for run in legacy_runs]
    migrated: dict[str, object] = {
        "schema_version": "2.0.0",
        "generated_by": generated_by,
        "records": records,
    }
    if legacy_document:
        migrated["legacy_payload"] = legacy_document
    return migrated


def classify_repository_failure(*, status: Optional[int]) -> str:
    """Map only demonstrated repository failures to safe public outcomes."""
    if status == 401:
        return "unauthorized"
    if status == 404:
        return "not-found-or-inaccessible"
    if status == 403:
        return "forbidden"
    return "failed"


@dataclass(frozen=True)
class SearchPartition:
    """Immutable evidence for one final Search API interval partition."""

    repository: str
    interval: tuple[str, str]
    query: str
    total_count: Optional[int]
    returned_count: int
    pagination_complete: bool
    incomplete_results: bool
    completion_state: str
    failure: Optional[str]


@dataclass(frozen=True)
class RepositorySearchResult:
    """Search candidates and fair per-repository selection accounting."""

    repository: str
    preflight: dict[str, object]
    preflight_outcome: str
    collection_status: str
    partitions: tuple[SearchPartition, ...]
    hits: tuple[dict[str, object], ...]
    selected_hits: tuple[dict[str, object], ...]
    overflow_hits: tuple[dict[str, object], ...]
    matched_count: int
    selected_count: int
    excluded_by_cap: int
    warnings: tuple[str, ...]


def collect_repository_hits(
    client: Any,
    repository: str,
    interval: Interval,
    outcome: str,
    max_per_repository: int,
) -> RepositorySearchResult:
    """Collect one repository's ordered search candidates without hydration.

    Search's 1,000-result and incompleteness signals are resolved by recursively
    splitting UTC whole-second partitions. Only safe, fully paginated leaves
    contribute candidates. The returned overflow remains ordered so hydration
    can later replace a stale outcome-indexed candidate without another search.
    """
    if not isinstance(repository, str) or not repository:
        raise ValueError("repository must be a non-empty owner/name string")
    if not isinstance(max_per_repository, int) or isinstance(max_per_repository, bool) or max_per_repository <= 0:
        raise ValueError("max_per_repository must be a positive integer")
    if outcome not in {"all", "merged", "closed-unmerged"}:
        raise ValueError("outcome must be all, merged, or closed-unmerged")

    try:
        preflight_response = client.get_json("/repos/{0}".format(repository))
        preflight_payload = _response_payload(preflight_response, "repository preflight")
        if not isinstance(preflight_payload, dict):
            raise ValueError("repository preflight payload must be an object")
    except BudgetExhausted:
        return _empty_repository_search_result(
            repository,
            "partial",
            "partial",
            "request budget exhausted before repository preflight",
        )
    except ApiFailure as failure:
        status = classify_repository_failure(status=failure.status)
        return _empty_repository_search_result(repository, status, status, str(failure))
    except ValueError as error:
        return _empty_repository_search_result(repository, "failed", "failed", str(error))

    partitions: list[SearchPartition] = []
    safe_hits: list[dict[str, object]] = []
    warnings: list[str] = []
    partial = False
    stopped = False

    root_start = _parse_timestamp(interval.start_at, "interval.start_at")
    root_end = _parse_timestamp(interval.end_at, "interval.end_at")

    def fail_partition(
        start: datetime,
        end: datetime,
        query: str,
        total_count: Optional[int],
        returned_count: int,
        incomplete_results: bool,
        failure: str,
    ) -> None:
        nonlocal partial
        partial = True
        partitions.append(
            SearchPartition(
                repository=repository,
                interval=(_utc_string(start), _utc_string(end)),
                query=query,
                total_count=total_count,
                returned_count=returned_count,
                pagination_complete=False,
                incomplete_results=incomplete_results,
                completion_state="failed",
                failure=failure,
            )
        )

    def collect_partition(start: datetime, end: datetime) -> None:
        nonlocal stopped
        if stopped:
            return
        partition_interval = _partition_interval(interval, start, end)
        query = build_closed_query(repository, partition_interval, outcome)
        try:
            first_payload = _response_payload(
                client.get_json("/search/issues", {"q": query, "page": 1}),
                "search response",
            )
            total_count, incomplete_results, first_items = _search_response(first_payload)
        except BudgetExhausted:
            stopped = True
            fail_partition(start, end, query, None, 0, False, "request budget exhausted")
            return
        except (ApiFailure, ValueError) as error:
            fail_partition(start, end, query, None, 0, False, str(error))
            return

        unsafe = total_count >= 1000 or incomplete_results
        if unsafe:
            if end - start <= timedelta(seconds=1):
                fail_partition(
                    start,
                    end,
                    query,
                    total_count,
                    len(first_items),
                    incomplete_results,
                    "unsafe one-second search partition",
                )
                return
            midpoint = start + timedelta(seconds=int((end - start).total_seconds()) // 2)
            collect_partition(start, midpoint)
            collect_partition(midpoint, end)
            return

        items = list(first_items)
        if len(items) > total_count:
            fail_partition(
                start,
                end,
                query,
                total_count,
                len(items),
                incomplete_results,
                "search page exceeded advertised total_count",
            )
            return
        page = 1
        while len(items) < total_count:
            page += 1
            try:
                page_payload = _response_payload(
                    client.get_json("/search/issues", {"q": query, "page": page}),
                    "search response",
                )
                page_total_count, page_incomplete, page_items = _search_response(page_payload)
            except BudgetExhausted:
                stopped = True
                fail_partition(
                    start, end, query, total_count, len(items), incomplete_results,
                    "request budget exhausted",
                )
                return
            except (ApiFailure, ValueError) as error:
                fail_partition(start, end, query, total_count, len(items), incomplete_results, str(error))
                return
            items.extend(page_items)
            if page_total_count != total_count:
                fail_partition(
                    start,
                    end,
                    query,
                    total_count,
                    len(items),
                    page_incomplete,
                    "search total_count changed from {0} to {1} during pagination".format(
                        total_count, page_total_count
                    ),
                )
                return
            if len(items) > total_count:
                fail_partition(
                    start,
                    end,
                    query,
                    total_count,
                    len(items),
                    page_incomplete,
                    "search pages exceeded advertised total_count",
                )
                return
            if page_incomplete or not page_items:
                fail_partition(
                    start,
                    end,
                    query,
                    total_count,
                    len(items),
                    page_incomplete,
                    "search pagination did not return every advertised result",
                )
                return

        partitions.append(
            SearchPartition(
                repository=repository,
                interval=(_utc_string(start), _utc_string(end)),
                query=query,
                total_count=total_count,
                returned_count=len(items),
                pagination_complete=True,
                incomplete_results=False,
                completion_state="complete",
                failure=None,
            )
        )
        safe_hits.extend(_exact_partition_hits(items, start, end, warnings))

    collect_partition(root_start, root_end)
    hits = _deduplicated_ordered_hits(safe_hits)
    selected_hits = hits[:max_per_repository]
    overflow_hits = hits[max_per_repository:]
    matched_count = len(hits)
    selected_count = len(selected_hits)
    collection_status = "partial" if partial else ("no-results" if not hits else "collected")
    return RepositorySearchResult(
        repository=repository,
        preflight=deepcopy(preflight_payload),
        preflight_outcome="collected",
        collection_status=collection_status,
        partitions=tuple(partitions),
        hits=tuple(hits),
        selected_hits=tuple(selected_hits),
        overflow_hits=tuple(overflow_hits),
        matched_count=matched_count,
        selected_count=selected_count,
        excluded_by_cap=len(overflow_hits),
        warnings=tuple(warnings),
    )


_LIST_PAGE_SIZE = 100
_FILES_LIMIT = 3000
_PULL_COMMITS_LIMIT = 250


def hydrate_pull_request(
    *,
    client: Any,
    repository: str,
    search_hit: dict[str, object],
    repository_metadata: dict[str, object],
    license_cache: dict[str, object],
    captured_at: str,
) -> dict[str, object]:
    """Collect one PR's raw, category-separated evidence without inference.

    A successful search identity remains usable when an individual evidence
    endpoint is unavailable.  Endpoint failures are therefore represented in
    that category's completeness metadata rather than raised after identity is
    established.  Text from GitHub is copied as untrusted data only.
    """
    if not isinstance(repository, str) or not repository:
        raise ValueError("repository must be a non-empty owner/name string")
    if not isinstance(search_hit, dict):
        raise ValueError("search_hit must be an object")
    if not isinstance(repository_metadata, dict):
        raise ValueError("repository_metadata must be an object")
    if not isinstance(license_cache, dict):
        raise ValueError("license_cache must be a dictionary")
    if not isinstance(captured_at, str) or not captured_at:
        raise ValueError("captured_at must be a non-empty timestamp string")

    number = search_hit.get("number")
    if not isinstance(number, int) or isinstance(number, bool) or number <= 0:
        raise ValueError("search_hit must contain a positive pull-request number")
    root = "/repos/{0}".format(repository)
    pull_endpoint = root + "/pulls/{0}".format(number)
    core_payload: dict[str, object] = {}
    core_warning: Optional[str] = None
    core_etag: Optional[str] = None
    try:
        response = client.get_json(pull_endpoint)
        payload = _response_payload(response, "pull request response")
        if not isinstance(payload, dict):
            raise ValueError("pull request response payload must be an object")
        core_payload = deepcopy(payload)
        core_etag = _response_etag(response)
        if _pull_request_details(payload, number, pull_endpoint)["normalized_state"] == "unknown":
            core_warning = "pull request response has no authoritative state"
    except (ApiFailure, BudgetExhausted, ValueError, TypeError, KeyError) as error:
        core_warning = _hydration_warning(error)

    node_id = _first_nonempty_string(core_payload.get("node_id"), search_hit.get("node_id"))
    repository_node_id = _first_nonempty_string(
        repository_metadata.get("node_id"),
        _nested_value(core_payload, "base", "repo", "node_id"),
    )
    identity_status = "resolved" if node_id is not None and repository_node_id is not None else "unresolved"
    pull_url = _first_nonempty_string(
        core_payload.get("html_url"),
        search_hit.get("html_url"),
        _nested_value(search_hit, "pull_request", "html_url"),
    )
    if pull_url is None:
        pull_url = "https://github.com/{0}/pull/{1}".format(repository, number)

    body_meta = _completeness(
        endpoint="GET " + pull_endpoint,
        pages_complete=core_warning is None,
        returned_count=1 if core_warning is None else 0,
        known_limit=None,
        captured_at=captured_at,
        page_count=1 if core_warning is None else 0,
        etag=core_etag,
        warnings=[] if core_warning is None else [core_warning],
    )
    details = _pull_request_details(core_payload, number, pull_url)
    category_results: dict[str, tuple[list[object], dict[str, object]]] = {}
    for category, endpoint, known_limit in (
        ("files", pull_endpoint + "/files", _FILES_LIMIT),
        ("commits", pull_endpoint + "/commits", _PULL_COMMITS_LIMIT),
        ("issue_comments", root + "/issues/{0}/comments".format(number), None),
        ("reviews", pull_endpoint + "/reviews", None),
        ("review_comments", pull_endpoint + "/comments", None),
        ("timeline", root + "/issues/{0}/timeline".format(number), None),
    ):
        category_results[category] = _hydrate_list_category(
            client=client,
            endpoint=endpoint,
            category=category,
            known_limit=known_limit,
            captured_at=captured_at,
            maximum_items=_FILES_LIMIT if category == "files" else _PULL_COMMITS_LIMIT if category == "commits" else None,
        )

    files, files_meta = category_results["files"]
    if len(files) >= _FILES_LIMIT:
        files_meta["pages_complete"] = False
        files_meta["warnings"].append("GitHub pull-request files endpoint is capped at 3000 files")
    expected_files = details["changed_files_count"]
    if not isinstance(expected_files, int) or isinstance(expected_files, bool):
        files_meta["pages_complete"] = False
        files_meta["warnings"].append("pull request has no authoritative changed_files count")
    elif len(files) != expected_files:
        files_meta["pages_complete"] = False
        files_meta["warnings"].append("returned files do not match the authoritative pull-request changed_files count")
    if any(not isinstance(item, dict) or not isinstance(item.get("patch"), str) for item in files):
        files_meta["pages_complete"] = False
        files_meta["warnings"].append("one or more changed files has no complete patch text")

    commits, commits_meta = category_results["commits"]
    expected_commits = details["commits_count"]
    if not isinstance(expected_commits, int) or isinstance(expected_commits, bool) or expected_commits < 0:
        commits_meta["pages_complete"] = False
        commits_meta["warnings"].append("pull request has no authoritative integer commits count")
    elif len(commits) >= _PULL_COMMITS_LIMIT and not _first_nonempty_string(details["head_sha"]):
        commits_meta["pages_complete"] = False
        commits_meta["warnings"].append("repository commit fallback requires the authoritative PR head SHA")
    elif (
        commits_meta["pages_complete"]
        and isinstance(expected_commits, int)
        and not isinstance(expected_commits, bool)
        and expected_commits >= _PULL_COMMITS_LIMIT
        and len(commits) >= _PULL_COMMITS_LIMIT
    ):
        fallback_endpoint = root + "/commits"
        fallback, fallback_meta = _hydrate_list_category(
            client=client,
            endpoint=fallback_endpoint,
            category="commits",
            known_limit=None,
            captured_at=captured_at,
            extra_params={"sha": details["head_sha"]},
            maximum_items=expected_commits,
        )
        commits_meta["fallback_endpoint"] = "GET " + fallback_endpoint
        commits_meta["fallback_page_count"] = fallback_meta["page_count"]
        commits_meta["fallback_etag"] = fallback_meta["etag"]
        commits_meta["fallback_completeness"] = deepcopy(fallback_meta)
        if fallback_meta["pages_complete"] and _commits_reconcile(commits, fallback, details["head_sha"], details["base_sha"], expected_commits):
            commits = fallback
            commits_meta["returned_count"] = len(commits)
            commits_meta["warnings"].extend(fallback_meta["warnings"])
        else:
            commits_meta["pages_complete"] = False
            commits_meta["warnings"].extend(fallback_meta["warnings"])
            commits_meta["warnings"].append(
                "repository commit fallback did not reconcile authoritative count and head ancestry"
            )
    if (
        commits_meta["pages_complete"]
        and isinstance(expected_commits, int)
        and not isinstance(expected_commits, bool)
        and len(commits) != expected_commits
    ):
        commits_meta["pages_complete"] = False
        commits_meta["warnings"].append(
            "returned commits do not match the authoritative pull-request commit count"
        )

    issue_comments, issue_meta = category_results["issue_comments"]
    reviews, reviews_meta = category_results["reviews"]
    review_comments, review_comments_meta = category_results["review_comments"]
    timeline, timeline_meta = category_results["timeline"]
    license, license_meta = _hydrate_license(
        client=client,
        repository=repository,
        cache=license_cache,
        captured_at=captured_at,
    )
    linked_issues = _linked_issues(timeline)
    linked_meta = _completeness(
        endpoint="GET " + root + "/issues/{0}/timeline (cross-referenced issue observations)".format(number),
        pages_complete=bool(timeline_meta["pages_complete"]),
        returned_count=len(linked_issues),
        known_limit=None,
        captured_at=captured_at,
        page_count=timeline_meta["page_count"],
        etag=timeline_meta["etag"],
        warnings=list(timeline_meta["warnings"]),
        attempted_pages=timeline_meta["attempted_pages"],
        page_etags=deepcopy(timeline_meta["page_etags"]),
    )
    completeness = {
        "pull_request_body": body_meta,
        "files": files_meta,
        "commits": commits_meta,
        "issue_comments": issue_meta,
        "reviews": reviews_meta,
        "review_comments": review_comments_meta,
        "timeline": timeline_meta,
        "license": license_meta,
        "linked_issues": linked_meta,
    }
    partial_categories = [
        category for category, metadata in completeness.items()
        if not metadata["pages_complete"]
    ]
    return {
        "identity_status": identity_status,
        "record_key": "github-pr:{0}".format(node_id) if identity_status == "resolved" else None,
        "pr_id": None,
        "pull_request_node_id": node_id,
        "repository": {
            "full_name": _first_nonempty_string(repository_metadata.get("full_name"), repository) or repository,
            "node_id": repository_node_id,
            "repository_aliases": [],
        },
        "pull_request": details,
        "author": _author(core_payload),
        "license": license,
        "sources": [],
        "state_history": _state_history(details),
        "hydration_status": "partial" if partial_categories else "complete",
        "evidence_snapshot": {
            "body_excerpt": core_payload.get("body") if isinstance(core_payload.get("body"), str) else None,
            "changed_files": [_file_evidence(item) for item in files],
            "commits": [_commit_evidence(item) for item in commits],
            "issue_comments": [_discussion_evidence(item) for item in issue_comments],
            "reviews": [_discussion_evidence(item) for item in reviews],
            "review_comments": [_discussion_evidence(item) for item in review_comments],
            "timeline_events": [_discussion_evidence(item) for item in timeline],
            "linked_issues": linked_issues,
            "partial_categories": partial_categories,
            "completeness": completeness,
        },
    }


def _hydrate_list_category(
    *, client: Any, endpoint: str, known_limit: Optional[int], captured_at: str, category: str,
    extra_params: Optional[dict[str, object]] = None, maximum_items: Optional[int] = None,
) -> tuple[list[object], dict[str, object]]:
    """Read consecutive 100-item pages and contain malformed endpoint data."""
    items: list[object] = []
    raw_count = 0
    page = 0
    attempted_pages = 0
    successful_pages = 0
    page_etags: list[dict[str, object]] = []
    etag: Optional[str] = None
    warnings: list[str] = []
    complete = True
    try:
        while maximum_items is None or raw_count < maximum_items:
            page += 1
            attempted_pages += 1
            params: dict[str, object] = {"page": page}
            if extra_params:
                params.update(extra_params)
            response = client.get_json(endpoint, params)
            payload = _response_payload(response, "list endpoint response")
            if not isinstance(payload, list):
                raise ValueError("list endpoint response payload must be an array")
            etag = _response_etag(response)
            successful_pages += 1
            page_etags.append({"page": page, "etag": etag})
            bounded_payload = payload if maximum_items is None else payload[:maximum_items - raw_count]
            raw_count += len(bounded_payload)
            for item in bounded_payload:
                if _valid_hydration_item(category, item):
                    items.append(deepcopy(item))
                else:
                    complete = False
                    warnings.append("{0} endpoint returned a malformed item".format(category))
            if maximum_items is not None and raw_count >= maximum_items:
                break
            link_header = getattr(response, "headers", {}).get("link", "") if isinstance(getattr(response, "headers", {}), dict) else ""
            if isinstance(link_header, str) and 'rel="next"' in link_header:
                continue
            if len(payload) < _LIST_PAGE_SIZE:
                break
    except (ApiFailure, BudgetExhausted, ValueError, TypeError, KeyError) as error:
        complete = False
        warnings.append(_hydration_warning(error))
    return items, _completeness(
        endpoint="GET " + endpoint,
        pages_complete=complete,
        returned_count=len(items),
        known_limit=known_limit,
        captured_at=captured_at,
        page_count=successful_pages,
        etag=etag,
        warnings=warnings,
        attempted_pages=attempted_pages,
        page_etags=page_etags,
    )


def _valid_hydration_item(category: str, item: object) -> bool:
    if not isinstance(item, dict):
        return False
    if category in {"issue_comments", "reviews", "review_comments", "timeline"}:
        for key in ("body", "created_at", "updated_at", "submitted_at", "commit_id", "commit_url", "original_commit_id", "diff_hunk", "side", "start_side", "html_url"):
            if item.get(key) is not None and not isinstance(item[key], str):
                return False
        for key in ("line", "original_line", "start_line", "original_start_line", "position", "original_position"):
            if item.get(key) is not None and (not isinstance(item[key], int) or isinstance(item[key], bool)):
                return False
        for key in ("user", "actor", "source"):
            if item.get(key) is not None and not isinstance(item[key], dict):
                return False
        for key in ("user", "actor"):
            login = _nested_value(item, key, "login")
            if login is not None and not isinstance(login, str):
                return False
    if category == "files":
        return bool(_first_nonempty_string(item.get("filename"))) and bool(_first_nonempty_string(item.get("status")))
    if category == "commits":
        return (
            bool(_first_nonempty_string(item.get("sha")))
            and isinstance(item.get("parents"), list)
            and all(isinstance(parent, dict) and _first_nonempty_string(parent.get("sha")) for parent in item["parents"])
            and isinstance(_nested_value(item, "commit", "message"), str)
        )
    if category in {"issue_comments", "reviews", "review_comments"}:
        if not isinstance(item.get("id"), int) or isinstance(item.get("id"), bool) or item["id"] <= 0:
            return False
        if "body" not in item or (item["body"] is not None and not isinstance(item["body"], str)):
            return False
        if category == "reviews":
            return bool(_first_nonempty_string(item.get("state")))
        if category == "review_comments":
            return bool(_first_nonempty_string(item.get("path")))
        return True
    if category == "timeline":
        return bool(_first_nonempty_string(item.get("event")))
    return True


def _hydrate_license(*, client: Any, repository: str, cache: dict[str, object], captured_at: str) -> tuple[dict[str, object], dict[str, object]]:
    cached = cache.get(repository, _MISSING)
    if cached is not _MISSING:
        if not isinstance(cached, tuple) or len(cached) != 2:
            raise ValueError("license cache entry has an invalid shape")
        return deepcopy(cached[0]), deepcopy(cached[1])
    endpoint = "/repos/{0}/license".format(repository)
    license_value: dict[str, object] = {"spdx_id": None, "evidence_url": None, "observed_via": "GET " + endpoint}
    try:
        response = client.get_json(endpoint)
        payload = _response_payload(response, "license response")
        if not isinstance(payload, dict):
            raise ValueError("license response payload must be an object")
        license_payload = payload.get("license")
        if isinstance(license_payload, dict) and isinstance(license_payload.get("spdx_id"), str):
            license_value["spdx_id"] = license_payload["spdx_id"]
        if isinstance(payload.get("html_url"), str):
            license_value["evidence_url"] = payload["html_url"]
        metadata = _completeness("GET " + endpoint, True, 1, None, captured_at, 1, _response_etag(response), [])
    except (ApiFailure, BudgetExhausted, ValueError, TypeError, KeyError) as error:
        metadata = _completeness("GET " + endpoint, False, 0, None, captured_at, 0, None, [_hydration_warning(error)])
    cache[repository] = (deepcopy(license_value), deepcopy(metadata))
    return license_value, metadata


def _completeness(endpoint: str, pages_complete: bool, returned_count: int, known_limit: Optional[int], captured_at: str, page_count: int, etag: Optional[str], warnings: list[str], attempted_pages: Optional[int] = None, page_etags: Optional[list[dict[str, object]]] = None) -> dict[str, object]:
    return {"endpoint": endpoint, "pages_complete": pages_complete, "returned_count": returned_count, "known_limit": known_limit, "captured_at": captured_at, "page_count": page_count, "attempted_pages": page_count if attempted_pages is None else attempted_pages, "etag": etag, "page_etags": [] if page_etags is None else page_etags, "warnings": warnings}


def _response_etag(response: object) -> Optional[str]:
    headers = getattr(response, "headers", None)
    value = headers.get("etag") if isinstance(headers, dict) else None
    return value if isinstance(value, str) else None


def _hydration_warning(error: BaseException) -> str:
    return _redact_diagnostics(str(error)) or error.__class__.__name__


def _first_nonempty_string(*values: object) -> Optional[str]:
    return next((value for value in values if isinstance(value, str) and value), None)


def _nested_value(value: object, *keys: str) -> object:
    current = value
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _pull_request_details(payload: dict[str, object], number: int, url: str) -> dict[str, object]:
    merged_at = payload.get("merged_at") if isinstance(payload.get("merged_at"), str) else None
    state = payload.get("state")
    valid_merge_observation = "merged_at" in payload
    if payload.get("merged_at") is not None:
        try:
            _parse_timestamp(merged_at, "merged_at")
        except ValueError:
            valid_merge_observation = False
    normalized_state = "unknown"
    if valid_merge_observation:
        normalized_state = "merged" if merged_at is not None else "closed-unmerged" if state == "closed" else "open" if state == "open" else "unknown"
    else:
        merged_at = None
    return {"number": number, "url": url, "title": payload.get("title") if isinstance(payload.get("title"), str) else None, "normalized_state": normalized_state, "closure_reason": "merged" if merged_at is not None else "unknown", "created_at": payload.get("created_at") if isinstance(payload.get("created_at"), str) else None, "closed_at": payload.get("closed_at") if isinstance(payload.get("closed_at"), str) else None, "merged_at": merged_at, "updated_at": payload.get("updated_at") if isinstance(payload.get("updated_at"), str) else None, "base_sha": _nested_value(payload, "base", "sha"), "head_sha": _nested_value(payload, "head", "sha"), "merge_sha": payload.get("merge_commit_sha") if isinstance(payload.get("merge_commit_sha"), str) else None, "labels": [label["name"] for label in payload.get("labels", []) if isinstance(label, dict) and isinstance(label.get("name"), str)] if isinstance(payload.get("labels", []), list) else [], "changed_files_count": payload.get("changed_files") if isinstance(payload.get("changed_files"), int) and not isinstance(payload.get("changed_files"), bool) else None, "commits_count": payload.get("commits") if isinstance(payload.get("commits"), int) and not isinstance(payload.get("commits"), bool) else None}


def _author(payload: dict[str, object]) -> dict[str, object]:
    raw = payload.get("author_association")
    association = raw if isinstance(raw, str) else "unknown"
    if association in {"OWNER", "MEMBER", "COLLABORATOR"}:
        role = "upstream-maintainer"
    elif association in {"CONTRIBUTOR", "FIRST_TIME_CONTRIBUTOR", "FIRST_TIMER"}:
        role = "contributor"
    else:
        role = "unknown"
    user = payload.get("user") if isinstance(payload.get("user"), dict) else {}
    return {"login": user.get("login") if isinstance(user.get("login"), str) else None, "node_id": user.get("node_id") if isinstance(user.get("node_id"), str) else None, "association": association, "normalized_role": role}


def _state_history(details: dict[str, object]) -> list[dict[str, object]]:
    if details["normalized_state"] == "unknown":
        return []
    observed_at = details["updated_at"] or details["created_at"]
    if details["normalized_state"] != "open":
        observed_at = details["merged_at"] or details["closed_at"] or observed_at
    return [{"state": details["normalized_state"], "observed_at": observed_at, "authority": "GitHub pull request", "evidence_url": details["url"]}]


def _file_evidence(item: object) -> dict[str, object]:
    value = item if isinstance(item, dict) else {}
    return {"path": value.get("filename") if isinstance(value.get("filename"), str) else None, "status": value.get("status") if isinstance(value.get("status"), str) else None, "additions": value.get("additions") if isinstance(value.get("additions"), int) and not isinstance(value.get("additions"), bool) else None, "deletions": value.get("deletions") if isinstance(value.get("deletions"), int) and not isinstance(value.get("deletions"), bool) else None, "change_excerpt": value.get("patch") if isinstance(value.get("patch"), str) else None}


def _commit_evidence(item: object) -> dict[str, object]:
    value = item if isinstance(item, dict) else {}
    commit = value.get("commit") if isinstance(value.get("commit"), dict) else {}
    parents = value.get("parents") if isinstance(value.get("parents"), list) else []
    return {"sha": value.get("sha") if isinstance(value.get("sha"), str) else None, "parents": [parent["sha"] for parent in parents if isinstance(parent, dict) and isinstance(parent.get("sha"), str)], "message": commit.get("message") if isinstance(commit.get("message"), str) else None, "author": deepcopy(commit.get("author")) if isinstance(commit.get("author"), dict) else None}


def _discussion_evidence(item: object) -> dict[str, object]:
    value = item if isinstance(item, dict) else {}
    user = value.get("user") if isinstance(value.get("user"), dict) else {}
    evidence = {
        "kind": _first_nonempty_string(value.get("event"), value.get("state")) or "observed",
        "author": _first_nonempty_string(user.get("login"), _nested_value(value, "actor", "login")),
        "source": deepcopy(value.get("source")) if isinstance(value.get("source"), dict) else None,
        "excerpt": value.get("body") if isinstance(value.get("body"), str) else None,
    }
    for key in ("path", "diff_hunk", "state", "submitted_at", "created_at", "updated_at", "commit_id", "original_commit_id", "commit_url", "html_url", "side", "start_side"):
        evidence[key] = value.get(key) if isinstance(value.get(key), str) else None
    for key in ("id", "line", "original_line", "start_line", "original_start_line", "position", "original_position"):
        evidence[key] = value.get(key) if isinstance(value.get(key), int) and not isinstance(value.get(key), bool) else None
    return evidence


def _linked_issues(timeline: list[object]) -> list[dict[str, object]]:
    observed: list[dict[str, object]] = []
    seen: set[tuple[object, object]] = set()
    for event in timeline:
        if not isinstance(event, dict) or event.get("event") != "cross-referenced":
            continue
        issue = _nested_value(event, "source", "issue")
        if not isinstance(issue, dict) or "pull_request" in issue:
            continue
        url = _first_nonempty_string(issue.get("html_url"), issue.get("url"))
        node_id = issue.get("node_id") if isinstance(issue.get("node_id"), str) else None
        key = (url, node_id)
        if url is None or key in seen:
            continue
        seen.add(key)
        observed.append({"url": url, "node_id": node_id, "number": issue.get("number") if isinstance(issue.get("number"), int) and not isinstance(issue.get("number"), bool) else None, "title": issue.get("title") if isinstance(issue.get("title"), str) else None, "body_excerpt": issue.get("body") if isinstance(issue.get("body"), str) else None})
    return observed


def _commits_reconcile(pull_commits: list[object], fallback: list[object], head_sha: object, base_sha: object, expected_count: int) -> bool:
    fallback_ids = [item.get("sha") for item in fallback if isinstance(item, dict) and isinstance(item.get("sha"), str)]
    pull_ids = [item.get("sha") for item in pull_commits if isinstance(item, dict) and isinstance(item.get("sha"), str)]
    if len(fallback) != expected_count or len(fallback_ids) != expected_count or not isinstance(head_sha, str) or not isinstance(base_sha, str):
        return False
    if not fallback_ids or fallback_ids[0] != head_sha or base_sha in fallback_ids or len(set(fallback_ids)) != expected_count or len(pull_ids) != len(pull_commits):
        return False
    if list(reversed(fallback_ids))[:len(pull_ids)] != pull_ids:
        return False
    for index, item in enumerate(fallback):
        if not isinstance(item, dict) or not isinstance(item.get("parents"), list):
            return False
        if index + 1 < len(fallback_ids):
            if fallback_ids[index + 1] not in [parent.get("sha") for parent in item["parents"] if isinstance(parent, dict)]:
                return False
        elif base_sha not in [parent.get("sha") for parent in item["parents"] if isinstance(parent, dict)]:
            return False
    return True


def _empty_repository_search_result(
    repository: str,
    preflight_outcome: str,
    collection_status: str,
    warning: str,
) -> RepositorySearchResult:
    return RepositorySearchResult(
        repository=repository,
        preflight={},
        preflight_outcome=preflight_outcome,
        collection_status=collection_status,
        partitions=(),
        hits=(),
        selected_hits=(),
        overflow_hits=(),
        matched_count=0,
        selected_count=0,
        excluded_by_cap=0,
        warnings=(warning,),
    )


def _response_payload(response: object, context: str) -> object:
    payload = getattr(response, "payload", _MISSING)
    if payload is _MISSING:
        raise ValueError("{0} has no parsed payload".format(context))
    return payload


def _search_response(payload: object) -> tuple[int, bool, list[dict[str, object]]]:
    if not isinstance(payload, dict):
        raise ValueError("search response payload must be an object")
    total_count = payload.get("total_count")
    incomplete_results = payload.get("incomplete_results")
    items = payload.get("items")
    if not isinstance(total_count, int) or isinstance(total_count, bool) or total_count < 0:
        raise ValueError("search response total_count must be a non-negative integer")
    if not isinstance(incomplete_results, bool):
        raise ValueError("search response incomplete_results must be a boolean")
    if not isinstance(items, list) or not all(isinstance(item, dict) for item in items):
        raise ValueError("search response items must be a list of objects")
    return total_count, incomplete_results, [deepcopy(item) for item in items]


def _partition_interval(source: Interval, start: datetime, end: datetime) -> Interval:
    return Interval(
        start_at=_utc_string(start),
        end_at=_utc_string(end),
        timezone=source.timezone,
        input_mode=deepcopy(source.input_mode),
        as_of=source.as_of,
        last_day_partial=source.last_day_partial,
    )


def _exact_partition_hits(
    items: list[dict[str, object]],
    start: datetime,
    end: datetime,
    warnings: list[str],
) -> list[dict[str, object]]:
    accepted: list[dict[str, object]] = []
    for item in items:
        node_id = item.get("node_id")
        closed_at = item.get("closed_at")
        number = item.get("number")
        if not isinstance(node_id, str) or not node_id or not isinstance(number, int) or isinstance(number, bool):
            warnings.append("search hit without a usable node_id or pull-request number was excluded")
            continue
        try:
            closed_at_value = _parse_timestamp(closed_at, "search hit closed_at")
        except ValueError:
            warnings.append("search hit with an invalid closed_at timestamp was excluded")
            continue
        if start <= closed_at_value < end:
            accepted.append(deepcopy(item))
    return accepted


def _deduplicated_ordered_hits(items: list[dict[str, object]]) -> list[dict[str, object]]:
    unique: dict[str, dict[str, object]] = {}
    for item in items:
        node_id = item["node_id"]
        if node_id not in unique:
            unique[node_id] = item

    def sort_key(item: dict[str, object]) -> tuple[float, int, str]:
        closed_at = _parse_timestamp(item["closed_at"], "search hit closed_at")
        return (-closed_at.timestamp(), -item["number"], item["node_id"])

    return sorted(unique.values(), key=sort_key)


def _parse_included_response(output: object) -> tuple[int, dict[str, str], str]:
    """Select the final HTTP block emitted by ``gh api --include``."""
    if not isinstance(output, str):
        raise ValueError("included response is not text")
    lines = output.splitlines()
    blocks: list[tuple[int, dict[str, str], int]] = []
    index = 0
    while index < len(lines):
        match = HTTP_STATUS.match(lines[index])
        if match is None:
            index += 1
            continue
        status = int(match.group(1))
        index += 1
        headers: dict[str, str] = {}
        while index < len(lines) and lines[index].strip():
            name, separator, value = lines[index].partition(":")
            if separator:
                normalized_name = name.strip().lower()
                if normalized_name and not _sensitive_header(normalized_name):
                    headers[normalized_name] = value.strip()
            index += 1
        if index < len(lines):
            index += 1
        blocks.append((status, headers, index))
    if not blocks:
        raise ValueError("included response has no HTTP status block")
    status, headers, body_start = blocks[-1]
    return status, headers, "\n".join(lines[body_start:])


def _is_retryable(status: int, headers: dict[str, str], message: str) -> bool:
    if status == 429 or 500 <= status <= 599:
        return True
    if status != 403:
        return False
    return (
        "retry-after" in headers
        or "x-ratelimit-reset" in headers
        or "rate limit" in message.lower()
    )


def _retry_delay(
    status: int,
    headers: dict[str, str],
    attempt: int,
    now: Callable[[], float],
) -> float:
    if status in {403, 429}:
        retry_after = _positive_number(headers.get("retry-after"))
        if retry_after is not None:
            return min(retry_after, MAX_RATE_LIMIT_WAIT_SECONDS)
        reset_at = _positive_number(headers.get("x-ratelimit-reset"))
        if reset_at is not None:
            return min(max(0.0, reset_at - now()), MAX_RATE_LIMIT_WAIT_SECONDS)
        return min(60 * (2**attempt), MAX_RATE_LIMIT_WAIT_SECONDS)
    return _transport_backoff(attempt)


def _transport_backoff(attempt: int) -> float:
    return min(float(2**attempt), 30.0)


def _positive_number(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _response_message(body: str) -> str:
    try:
        payload = json.loads(body)
    except (TypeError, json.JSONDecodeError):
        return ""
    if isinstance(payload, dict) and isinstance(payload.get("message"), str):
        return payload["message"]
    return ""


def _versions_from_payload(payload: object) -> list[str]:
    if isinstance(payload, list):
        return [value for value in payload if isinstance(value, str)]
    if isinstance(payload, dict) and isinstance(payload.get("versions"), list):
        return [value for value in payload["versions"] if isinstance(value, str)]
    return []


def _sensitive_header(name: str) -> bool:
    lowered = name.lower()
    return (
        "authorization" in lowered
        or "token" in lowered
        or "cookie" in lowered
        or lowered == "if-none-match"
    )


def _redact_diagnostics(value: object) -> str:
    if not isinstance(value, str):
        return ""
    without_secret_headers = re.sub(
        r"(?im)^.*(?:authorization|token|cookie|if-none-match)[^\r\n]*[\r\n]?", "", value
    )
    without_bearer = re.sub(r"(?i)\bbearer\s+\S+", "<credential>", without_secret_headers)
    return re.sub(r"\b(?:gh[pousr]_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+)\b", "<credential>", without_bearer)


def _migrate_run(run: object) -> dict[str, object]:
    if not isinstance(run, dict):
        raise ValueError("manifest 1.0.0 runs must contain objects")

    legacy_run = deepcopy(run)
    record: dict[str, object] = {
        "run_id": legacy_run.pop("run_key", None),
        "collection_method": legacy_run.pop("kind", None),
        "completed_at": legacy_run.pop("captured_at", None),
        "api_version": legacy_run.pop("github_api_version", None),
        "client_version": legacy_run.pop("github_cli_version", None),
        "started_at": None,
        "collection_status": "partial",
        "migration_warnings": [
            "Legacy manifest has no start time, request fingerprint, or canonical completeness result; migrated run is partial."
        ],
    }
    if "warnings" in legacy_run:
        record["warnings"] = legacy_run.pop("warnings")
    if legacy_run:
        record["legacy_payload"] = legacy_run
    return record


def _timezone(timezone_name: str) -> ZoneInfo:
    try:
        return ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, TypeError) as error:
        raise ValueError(f"invalid timezone: {timezone_name}") from error


def _interval_mode(
    start_at: Optional[str],
    end_at: Optional[str],
    start_date: Optional[str],
    end_date: Optional[str],
    recent_days: Optional[int],
) -> str:
    timestamps_supplied = start_at is not None or end_at is not None
    dates_supplied = start_date is not None or end_date is not None
    complete_modes = [
        start_at is not None and end_at is not None,
        start_date is not None and end_date is not None,
        recent_days is not None,
    ]
    if sum(complete_modes) != 1 or (timestamps_supplied and not complete_modes[0]) or (
        dates_supplied and not complete_modes[1]
    ):
        raise ValueError("select exactly one complete interval mode")
    return ("timestamps", "dates", "recent_days")[complete_modes.index(True)]


def _parse_timestamp(value: Optional[str], field: str) -> datetime:
    """Accept `YYYY-MM-DDTHH:MM:SS[.fraction](Z|+HH:MM|-HH:MM)` only.

    Numeric offset hours must be 00--23 and minutes must be 00--59.
    """
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an RFC 3339 timestamp")
    if RFC3339_TIMESTAMP.fullmatch(value) is None:
        raise ValueError(f"{field} must be an RFC 3339 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{field} must be an RFC 3339 timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include a timezone offset")
    return _whole_second(parsed).astimezone(timezone.utc)


def _parse_date(value: Optional[str], field: str) -> date:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO 8601 date")
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"{field} must be an ISO 8601 date") from error


def _whole_second(value: datetime) -> datetime:
    return value.replace(microsecond=0)


def _utc_string(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
