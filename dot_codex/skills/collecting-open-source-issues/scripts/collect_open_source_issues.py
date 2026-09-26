"""Collect general GitHub Issues into a versioned, auditable Issue corpus."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time as clock_time
from typing import Any, Callable, Optional
import urllib.request


SKILL_NAME = "collecting-open-source-issues"
SKILL_DIR = Path(__file__).resolve().parents[1]
SIBLING_SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "collecting-recent-closed-prs"
    / "scripts"
    / "collect_recent_closed_prs.py"
)
COLLECTION_METHOD = "general-issue-search"
DATE_FIELDS = ("created", "updated", "closed")
PROJECTION_FIELDS = ("issue", "author", "closure", "hydration_status", "evidence_snapshot")
_ISSUE_ID = re.compile(r"\AISS-([1-9][0-9]*)\Z")
STATES = ("open", "closed", "all")
REPOSITORY = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+\Z")
_SIBLING_CACHE: dict[Path, Any] = {}
_ONE_SECOND = timedelta(seconds=1)


class SiblingMissing(FileNotFoundError):
    """The adjacent closed-PR collector this skill shares code with is absent."""


def load_sibling(script_path: object = SIBLING_SCRIPT) -> Any:
    """Load the adjacent closed-PR collector once from its file-relative path."""
    path = Path(script_path).resolve()
    if not path.is_file():
        raise SiblingMissing(
            "collecting-recent-closed-prs is not installed at {0}. This skill shares "
            "that skill's GitHub transport, date splitting, and hydration; install it "
            "as a sibling directory before collecting.".format(path)
        )
    if path in _SIBLING_CACHE:
        return _SIBLING_CACHE[path]
    module_name = "_collecting_recent_closed_prs_sibling_for_issues"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError("could not load collecting-recent-closed-prs sibling")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    _SIBLING_CACHE[path] = module
    return module


try:
    _sibling = load_sibling()
except SiblingMissing as error:  # pragma: no cover - exercised as a subprocess
    if __name__ == "__main__":
        print("error: {0}".format(error), file=sys.stderr)
        raise SystemExit(2)
    raise
resolve_interval = _sibling.resolve_interval


class CliInputError(ValueError):
    """Invalid caller input detected before any GitHub request."""


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CliInputError(message)


def build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(
        description="Collect general GitHub Issues from caller-supplied repositories",
        allow_abbrev=False,
    )
    commands = parser.add_subparsers(dest="command", required=True, parser_class=_ArgumentParser)
    collect_parser = commands.add_parser("collect", allow_abbrev=False)
    collect_parser.add_argument("--repo", action="append", required=True)
    collect_parser.add_argument("--date-field", choices=DATE_FIELDS, required=True)
    collect_parser.add_argument("--state", choices=STATES, default="all")
    collect_parser.add_argument("--label", action="append", default=[])
    collect_parser.add_argument("--timezone", default="UTC")
    collect_parser.add_argument("--start-at")
    collect_parser.add_argument("--end-at")
    collect_parser.add_argument("--start-date")
    collect_parser.add_argument("--end-date")
    collect_parser.add_argument("--recent-days", type=int)
    collect_parser.add_argument("--as-of")
    collect_parser.add_argument("--max-per-repo", type=int, default=25)
    collect_parser.add_argument("--request-budget", type=int, default=1000)
    collect_parser.add_argument("--api-version", default=_sibling.API_VERSION)
    collect_parser.add_argument("--output", required=True)
    collect_parser.add_argument("--manifest", required=True)
    return parser


def validate_repositories(repositories: list[str]) -> list[str]:
    if not repositories:
        raise CliInputError("at least one --repo is required")
    for repository in repositories:
        if REPOSITORY.fullmatch(repository) is None or repository.split("/")[1] in {".", ".."}:
            raise CliInputError("repository must be OWNER/REPO: " + repository)
    if len({repository.lower() for repository in repositories}) != len(repositories):
        raise CliInputError("repository list must not contain duplicates")
    return list(repositories)


def validate_filters(date_field: str, state: str, labels: list[str]) -> None:
    if date_field not in DATE_FIELDS:
        raise CliInputError("date field must be created, updated, or closed")
    if state not in STATES:
        raise CliInputError("state must be open, closed, or all")
    if date_field == "closed" and state == "open":
        raise CliInputError("--date-field closed cannot select --state open Issues")
    for label in labels:
        if not isinstance(label, str) or not label.strip() or '"' in label or "\n" in label:
            raise CliInputError("label must be non-empty text without double quotes or newlines")


def build_issue_query(repository: str, interval: Any, date_field: str, state: str, labels: list[str]) -> str:
    """Build one Search API query for a UTC half-open interval on one date field."""
    start = _sibling.parse_timestamp(interval.start_at, "interval.start_at")
    end = _sibling.parse_timestamp(interval.end_at, "interval.end_at")
    return _issue_query(repository, start, end, date_field, state, labels)


def _issue_query(repository: str, start: datetime, end: datetime, date_field: str, state: str,
                 labels: list[str]) -> str:
    validate_filters(date_field, state, labels)
    if start >= end:
        raise ValueError("interval.start_at must be earlier than interval.end_at")
    last_second = end - _ONE_SECOND
    qualifiers = ["repo:" + repository, "is:issue"]
    if state != "all":
        qualifiers.append("is:" + state)
    qualifiers.append(
        "{0}:{1}..{2}".format(date_field, _sibling.utc_string(start), _sibling.utc_string(last_second))
    )
    qualifiers.extend('label:"{0}"'.format(label) for label in labels)
    return " ".join(qualifiers)


ISSUE_EVIDENCE_QUERY = """query IssueEvidence($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    issue(number: $number) {
      id
      lastEditedAt
      userContentEdits(first: 100) {
        totalCount
        pageInfo { hasNextPage }
        nodes { editedAt deletedAt editor { login } diff }
      }
      duplicateOf { id number url repository { nameWithOwner } }
      closedByPullRequestsReferences(first: 50, includeClosedPrs: true) {
        totalCount
        pageInfo { hasNextPage }
        nodes { id number url state merged repository { nameWithOwner } }
      }
      timelineItems(itemTypes: [CLOSED_EVENT], first: 50) {
        totalCount
        pageInfo { hasNextPage }
        nodes {
          ... on ClosedEvent {
            createdAt
            stateReason
            closer {
              __typename
              ... on PullRequest { id number url state merged repository { nameWithOwner } }
              ... on Commit { oid url }
            }
          }
        }
      }
      comments(first: 100) {
        totalCount
        pageInfo { hasNextPage }
        nodes {
          databaseId
          lastEditedAt
          userContentEdits(first: 20) {
            totalCount
            pageInfo { hasNextPage }
            nodes { editedAt deletedAt editor { login } diff }
          }
        }
      }
    }
  }
}"""
GRAPHQL_EVIDENCE_ENDPOINT = "GraphQL query IssueEvidence"
GRAPHQL_URL = "https://api.github.com/graphql"
_QUERY_DOCUMENT = re.compile(r"\A\s*query\b")
_NON_QUERY_OPERATION = re.compile(r"\b(?:mutation|subscription)\b")


class GraphqlQueryClient(_sibling.GhApiClient):
    """Read-only GraphQL transport that shares the sibling's budget and retries.

    Only ``query`` documents are sent. The sibling client owns attempts,
    retries, response parsing, credentials, and redaction; this subclass only
    replaces the GET request with a POST to ``/graphql`` (``http_request``) and,
    for injected fixture runners, ``gh api --method GET`` with ``gh api graphql``.
    """

    def query(self, document: str, variables: dict[str, object]) -> Any:
        if (
            not isinstance(document, str)
            or _QUERY_DOCUMENT.match(document) is None
            or _NON_QUERY_OPERATION.search(document) is not None
        ):
            raise ValueError("GraphQL documents must be query operations")
        if "query" in variables:
            raise ValueError("GraphQL variables must not replace the checked query")
        params: dict[str, object] = {"query": document}
        params.update(variables)
        return self.get_json("/graphql", params)

    def api_command(
        self,
        endpoint: str,
        params: Optional[dict[str, object]],
        cached_etag: Optional[str],
    ) -> list[str]:
        if endpoint != "/graphql" or cached_etag is not None:
            raise ValueError("the GraphQL client only sends unconditional /graphql queries")
        command = ["gh", "api", "graphql", "--include"]
        for name, value in (params or {}).items():
            flag = "-F" if isinstance(value, int) and not isinstance(value, bool) else "-f"
            command.extend([flag, "{0}={1}".format(name, value)])
        return command

    def http_request(
        self,
        endpoint: str,
        params: Optional[dict[str, object]],
        cached_etag: Optional[str],
    ) -> urllib.request.Request:
        """GraphQL is the only POST: a checked query to the fixed GitHub endpoint.

        The sibling checks the built request again and attaches the credential.
        """
        if endpoint != "/graphql" or cached_etag is not None or not isinstance(params, dict):
            raise ValueError("the GraphQL client only sends unconditional /graphql queries")
        document = params.get("query")
        if (
            not isinstance(document, str)
            or _QUERY_DOCUMENT.match(document) is None
            or _NON_QUERY_OPERATION.search(document) is not None
        ):
            raise ValueError("GraphQL documents must be query operations")
        variables = {name: value for name, value in params.items() if name != "query"}
        body = json.dumps(
            {"query": document, "variables": variables}, separators=(",", ":")
        ).encode("utf-8")
        headers = {
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": self.api_version,
            "User-Agent": "dotfiles-oss-research",
        }
        return urllib.request.Request(GRAPHQL_URL, data=body, headers=headers, method="POST")


def build_clients(
    *,
    api_version: str,
    request_budget: int,
    runner: Optional[Callable[..., Any]] = None,
    sleeper: Callable[[float], None] = clock_time.sleep,
) -> tuple[Any, GraphqlQueryClient]:
    """Create REST and GraphQL clients that consume one shared request budget."""
    budget = _sibling.RequestBudget(request_budget)
    rest = _sibling.GhApiClient(api_version=api_version, budget=budget, runner=runner, sleeper=sleeper)
    graphql = GraphqlQueryClient(api_version=api_version, budget=budget, runner=runner, sleeper=sleeper)
    graphql.request_events = rest.request_events
    return rest, graphql


# Copied from the sibling rather than shared: each is a few lines that read one
# response attribute or shape this corpus, so a change made for pull requests
# must not silently change Issue records.
_MISSING = object()


def _response_payload(response: object, context: str) -> object:
    payload = getattr(response, "payload", _MISSING)
    if payload is _MISSING:
        raise ValueError("{0} has no parsed payload".format(context))
    return payload


def _response_etag(response: object) -> Optional[str]:
    headers = getattr(response, "headers", None)
    value = headers.get("etag") if isinstance(headers, dict) else None
    return value if isinstance(value, str) else None


def _run_timestamp(value: Optional[str]) -> str:
    return value if isinstance(value, str) and value else _sibling.utc_string(datetime.now(timezone.utc))


def _first_nonempty_string(*values: object) -> Optional[str]:
    return next((value for value in values if isinstance(value, str) and value), None)


def _discussion_evidence(item: object) -> dict[str, object]:
    value = item if isinstance(item, dict) else {}
    user = value.get("user") if isinstance(value.get("user"), dict) else {}
    actor = value.get("actor") if isinstance(value.get("actor"), dict) else {}
    evidence = {
        "kind": _first_nonempty_string(value.get("event"), value.get("state")) or "observed",
        "author": _first_nonempty_string(user.get("login"), actor.get("login")),
        "source": deepcopy(value.get("source")) if isinstance(value.get("source"), dict) else None,
        "excerpt": value.get("body") if isinstance(value.get("body"), str) else None,
    }
    for key in ("path", "diff_hunk", "state", "submitted_at", "created_at", "updated_at", "commit_id",
                "original_commit_id", "commit_url", "html_url", "side", "start_side"):
        evidence[key] = value.get(key) if isinstance(value.get(key), str) else None
    for key in ("id", "line", "original_line", "start_line", "original_start_line", "position", "original_position"):
        evidence[key] = value.get(key) if isinstance(value.get(key), int) and not isinstance(value.get(key), bool) else None
    return evidence


def _date_value(item: dict[str, object], date_field: str) -> Optional[datetime]:
    try:
        return _sibling.parse_timestamp(item.get(date_field + "_at"), "search hit " + date_field + "_at")
    except ValueError:
        return None


def collect_repository_issue_hits(
    client: Any,
    repository: str,
    interval: Any,
    date_field: str,
    state: str,
    labels: list[str],
    *,
    on_split_observation: Optional[Callable[[dict[str, object]], None]] = None,
) -> dict[str, object]:
    """Search one repository with the sibling's recursive whole-second splitting.

    The sibling's ``collect_repository_hits`` is fixed to the closed pull
    request query and its ``closed_at`` post-filter, so this walker reuses its
    partition record, response validation, and timestamp primitives while
    swapping in the Issue query and the caller's date field.
    """
    result: dict[str, object] = {
        "preflight": {},
        "preflight_outcome": "collected",
        "partitions": [],
        "hits": [],
        "excluded": {"is-pull-request": 0},
        "warnings": [],
        "partial": False,
    }
    try:
        response = client.get_json("/repos/{0}".format(repository))
        preflight = _response_payload(response, "repository preflight")
        if not isinstance(preflight, dict):
            raise ValueError("repository preflight payload must be an object")
    except _sibling.BudgetExhausted:
        result.update(preflight_outcome="partial", partial=True)
        result["warnings"].append("request budget exhausted before repository preflight")
        return result
    except _sibling.ApiFailure as failure:
        result.update(preflight_outcome=_sibling.classify_repository_failure(status=failure.status), partial=True)
        result["warnings"].append(str(failure))
        return result
    except ValueError as error:
        result.update(preflight_outcome="failed", partial=True)
        result["warnings"].append(str(error))
        return result
    result["preflight"] = deepcopy(preflight)

    partitions: list[Any] = result["partitions"]
    warnings: list[str] = result["warnings"]
    accepted: dict[str, dict[str, object]] = {}
    pull_request_nodes: set[object] = set()
    stopped = False

    def record_partition(start: datetime, end: datetime, query: str, total: Optional[int],
                         returned: int, complete: bool, incomplete: bool, failure: Optional[str]) -> None:
        if not complete:
            result["partial"] = True
        partitions.append(_sibling.SearchPartition(
            repository=repository,
            interval=(_sibling.utc_string(start), _sibling.utc_string(end)),
            query=query,
            total_count=total,
            returned_count=returned,
            pagination_complete=complete,
            incomplete_results=incomplete,
            completion_state="complete" if complete else "failed",
            failure=failure,
        ))

    def accept(items: list[dict[str, object]], start: datetime, end: datetime) -> None:
        for item in items:
            if "pull_request" in item:
                pull_request_nodes.add(item.get("node_id") or item.get("number"))
                continue
            node_id, number = item.get("node_id"), item.get("number")
            if not isinstance(node_id, str) or not node_id or not isinstance(number, int) or isinstance(number, bool):
                result["partial"] = True
                warnings.append("search hit without a usable node_id or Issue number was excluded")
                continue
            value = _date_value(item, date_field)
            if value is None:
                result["partial"] = True
                warnings.append("search hit with an invalid {0}_at timestamp was excluded".format(date_field))
                continue
            if start <= value < end:
                accepted.setdefault(node_id, deepcopy(item))

    def search(start: datetime, end: datetime) -> None:
        nonlocal stopped
        query = _issue_query(repository, start, end, date_field, state, labels)
        if stopped:
            record_partition(start, end, query, None, 0, False, False,
                             "request budget exhausted before this partition was searched")
            return
        try:
            first = _response_payload(client.get_json("/search/issues", {"q": query, "page": 1}), "search response")
            total, incomplete, items = _sibling.search_response(first)
        except _sibling.BudgetExhausted:
            stopped = True
            record_partition(start, end, query, None, 0, False, False, "request budget exhausted")
            return
        except (_sibling.ApiFailure, ValueError) as error:
            record_partition(start, end, query, None, 0, False, False, str(error))
            return
        if total >= 1000 or incomplete:
            if end - start <= _ONE_SECOND:
                record_partition(start, end, query, total, len(items), False, incomplete,
                                 "unsafe one-second search partition")
                return
            midpoint = start + timedelta(seconds=int((end - start).total_seconds()) // 2)
            if on_split_observation is not None:
                on_split_observation({
                    "repository": repository,
                    "interval": [_sibling.utc_string(start), _sibling.utc_string(end)],
                    "query": query,
                    "total_count": total,
                    "returned_count": len(items),
                    "incomplete_results": incomplete,
                    "observed_at": _run_timestamp(None),
                    "split_reasons": (["search-result-limit"] if total >= 1000 else [])
                    + (["incomplete-results"] if incomplete else []),
                    "children": [[_sibling.utc_string(start), _sibling.utc_string(midpoint)],
                                 [_sibling.utc_string(midpoint), _sibling.utc_string(end)]],
                })
            search(start, midpoint)
            search(midpoint, end)
            return
        collected = list(items)
        page = 1
        while len(collected) < total:
            page += 1
            try:
                payload = _response_payload(
                    client.get_json("/search/issues", {"q": query, "page": page}), "search response",
                )
                page_total, page_incomplete, page_items = _sibling.search_response(payload)
            except _sibling.BudgetExhausted:
                stopped = True
                record_partition(start, end, query, total, len(collected), False, incomplete, "request budget exhausted")
                return
            except (_sibling.ApiFailure, ValueError) as error:
                record_partition(start, end, query, total, len(collected), False, incomplete, str(error))
                return
            collected.extend(page_items)
            if page_total != total or page_incomplete or not page_items:
                record_partition(start, end, query, total, len(collected), False, page_incomplete,
                                 "search pagination did not return every advertised result")
                return
        if len(collected) > total:
            record_partition(start, end, query, total, len(collected), False, incomplete,
                             "search pages exceeded advertised total_count")
            return
        record_partition(start, end, query, total, len(collected), True, False, None)
        accept(collected, start, end)

    search(
        _sibling.parse_timestamp(interval.start_at, "interval.start_at"),
        _sibling.parse_timestamp(interval.end_at, "interval.end_at"),
    )
    result["excluded"]["is-pull-request"] = len(pull_request_nodes)
    result["hits"] = sorted(
        accepted.values(),
        key=lambda item: (-_date_value(item, date_field).timestamp(), -item["number"], item["node_id"]),
    )
    return result


def _sha256_text(value: Optional[str]) -> str:
    return hashlib.sha256((value or "").encode("utf-8")).hexdigest()


def _text(value: object) -> Optional[str]:
    return value if isinstance(value, str) else None


def _connection(value: object, name: str, truncated: list[str]) -> dict[str, object]:
    if not isinstance(value, dict) or not isinstance(value.get("nodes"), list):
        raise ValueError("GraphQL {0} connection is malformed".format(name))
    page_info = value.get("pageInfo")
    if not isinstance(page_info, dict) or page_info.get("hasNextPage") is not False:
        truncated.append(name)
    return value


def _edit_meta(connection: dict[str, object], last_edited_at: object) -> dict[str, object]:
    edits = []
    for node in connection["nodes"]:
        if not isinstance(node, dict):
            raise ValueError("GraphQL userContentEdits node is malformed")
        editor = node.get("editor")
        diff = node.get("diff")
        edits.append({
            "edited_at": _text(node.get("editedAt")),
            "editor_login": _text(editor.get("login")) if isinstance(editor, dict) else None,
            "deleted_at": _text(node.get("deletedAt")),
            "diff_sha256": _sha256_text(diff) if isinstance(diff, str) else None,
        })
    total = connection.get("totalCount")
    return {
        "total_count": total if isinstance(total, int) and not isinstance(total, bool) else None,
        "last_edited_at": _text(last_edited_at),
        "edits": edits,
    }


def _graphql_pull_request(node: dict[str, object], relation: str, method: str, event_at: object) -> dict[str, object]:
    repository = node.get("repository")
    return {
        "url": _text(node.get("url")),
        "node_id": _text(node.get("id")),
        "number": node.get("number") if isinstance(node.get("number"), int) else None,
        "repository_full_name": _text(repository.get("nameWithOwner")) if isinstance(repository, dict) else None,
        "relation": relation,
        "relation_method": method,
        "event_at": _text(event_at),
        "state_raw": _text(node.get("state")),
        "merged_raw": node.get("merged") if isinstance(node.get("merged"), bool) else None,
    }


def _graphql_facts(payload: object, issue_node_id: str) -> tuple[dict[str, object], list[str]]:
    """Project the fixed query payload; raise on errors, report truncation."""
    if not isinstance(payload, dict):
        raise ValueError("GraphQL response payload must be an object")
    errors = payload.get("errors")
    if errors:
        kinds = sorted({
            str(error.get("type") or "error") for error in errors if isinstance(error, dict)
        }) or ["error"]
        raise ValueError("GraphQL query returned errors: " + ", ".join(kinds))
    issue = ((payload.get("data") or {}).get("repository") or {}).get("issue") if isinstance(payload.get("data"), dict) else None
    if not isinstance(issue, dict):
        raise ValueError("GraphQL response has no Issue")
    if issue.get("id") != issue_node_id:
        raise ValueError("GraphQL Issue id does not match the hydrated Issue")
    truncated: list[str] = []
    body_edits = _connection(issue.get("userContentEdits"), "userContentEdits", truncated)
    references = _connection(issue.get("closedByPullRequestsReferences"), "closedByPullRequestsReferences", truncated)
    closed = _connection(issue.get("timelineItems"), "timelineItems", truncated)
    comments = _connection(issue.get("comments"), "comments", truncated)

    closed_events: list[dict[str, object]] = []
    closers: list[dict[str, object]] = []
    for node in closed["nodes"]:
        if not isinstance(node, dict):
            raise ValueError("GraphQL ClosedEvent node is malformed")
        closer = node.get("closer")
        closer_type = _text(closer.get("__typename")) if isinstance(closer, dict) else None
        closed_events.append({
            "created_at": _text(node.get("createdAt")),
            "state_reason_raw": _text(node.get("stateReason")),
            "closer_type": closer_type,
            "closer_url": _text(closer.get("url")) if isinstance(closer, dict) else None,
        })
        if closer_type == "PullRequest":
            closers.append(_graphql_pull_request(closer, "closer", "graphql-closed-event", node.get("createdAt")))
    closing = [
        _graphql_pull_request(node, "closing-reference", "graphql-closing-references", None)
        for node in references["nodes"]
        if isinstance(node, dict)
    ]
    comment_history = []
    for node in comments["nodes"]:
        if not isinstance(node, dict):
            raise ValueError("GraphQL comment node is malformed")
        edits = _connection(node.get("userContentEdits"), "comments.userContentEdits", truncated)
        meta = _edit_meta(edits, node.get("lastEditedAt"))
        if meta["total_count"]:
            comment_history.append(dict({"comment_id": node.get("databaseId")}, **meta))
    duplicate = issue.get("duplicateOf")
    duplicate_of = None
    if isinstance(duplicate, dict):
        repository = duplicate.get("repository")
        duplicate_of = {
            "url": _text(duplicate.get("url")),
            "number": duplicate.get("number") if isinstance(duplicate.get("number"), int) else None,
            "node_id": _text(duplicate.get("id")),
            "repository_full_name": _text(repository.get("nameWithOwner")) if isinstance(repository, dict) else None,
            "method": "graphql-duplicate-of",
        }
    facts = {
        "closed_events": closed_events,
        "related": closers + closing,
        "duplicate_of": duplicate_of,
        "edit_history": {
            "body": _edit_meta(body_edits, issue.get("lastEditedAt")),
            "comments": comment_history,
        },
    }
    return facts, ["graphql connection truncated: " + name for name in sorted(set(truncated))]


def _timeline_references(timeline: list[object]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    related: list[dict[str, object]] = []
    unresolvable: list[dict[str, object]] = []
    for event in timeline:
        if not isinstance(event, dict) or event.get("event") != "cross-referenced":
            continue
        event_at = _text(event.get("created_at"))
        source = event.get("source")
        issue = source.get("issue") if isinstance(source, dict) else None
        if not isinstance(issue, dict):
            unresolvable.append({"event": "cross-referenced", "event_at": event_at,
                                 "reason": "cross-reference source is not readable"})
            continue
        if "pull_request" not in issue:
            continue
        pull_request = issue.get("pull_request") if isinstance(issue.get("pull_request"), dict) else {}
        repository = issue.get("repository")
        url = _first_nonempty_string(issue.get("html_url"), pull_request.get("html_url"), issue.get("url"))
        full_name = _text(repository.get("full_name")) if isinstance(repository, dict) else None
        if url is None or full_name is None:
            unresolvable.append({"event": "cross-referenced", "event_at": event_at,
                                 "reason": "cross-reference source has no repository or URL"})
            continue
        entry = {
            "url": url,
            "node_id": _text(issue.get("node_id")),
            "number": issue.get("number") if isinstance(issue.get("number"), int) else None,
            "repository_full_name": full_name,
            "relation": "cross-reference",
            "relation_method": "rest-timeline",
            "event_at": event_at,
            "state_raw": None,
            "merged_raw": None,
        }
        if not any(item["url"] == url for item in related):
            related.append(entry)
    return related, unresolvable


def _timeline_evidence(item: object) -> dict[str, object]:
    evidence = _discussion_evidence(item)
    evidence["state_reason"] = _text(item.get("state_reason")) if isinstance(item, dict) else None
    return evidence


class PullRequestPayload(Exception):
    """The authoritative Issue endpoint returned a pull request."""


def hydrate_issue(
    rest: Any,
    graphql: Any,
    repository: str,
    hit: dict[str, object],
    *,
    repository_metadata: dict[str, object],
    run_id: str,
    captured_at: str,
    skill_revision: str,
) -> dict[str, object]:
    """Collect one Issue's REST core, comments, timeline, and GraphQL facts."""
    number = hit["number"]
    root = "/repos/{0}/issues/{1}".format(repository, number)
    response = rest.get_json(root)
    payload = _response_payload(response, "Issue response")
    if not isinstance(payload, dict):
        raise ValueError("Issue response payload must be an object")
    if "pull_request" in payload:
        raise PullRequestPayload(root)
    node_id = payload.get("node_id")
    if node_id != hit["node_id"]:
        raise ValueError("hydrated Issue node_id does not match the search hit")
    body = payload.get("body")
    if body is not None and not isinstance(body, str):
        raise ValueError("Issue body must be text or null")
    core_meta = _sibling.completeness("GET " + root, True, 1, None, captured_at, 1, _response_etag(response), [])
    comments, comments_meta = _sibling.hydrate_list_category(
        client=rest, endpoint=root + "/comments", known_limit=None, captured_at=captured_at, category="issue_comments",
    )
    timeline, timeline_meta = _sibling.hydrate_list_category(
        client=rest, endpoint=root + "/timeline", known_limit=None, captured_at=captured_at, category="timeline",
    )
    owner, name = repository.split("/", 1)
    facts: Optional[dict[str, object]] = None
    graphql_warnings: list[str] = []
    try:
        graph_response = graphql.query(ISSUE_EVIDENCE_QUERY, {"owner": owner, "name": name, "number": number})
        facts, graphql_warnings = _graphql_facts(_response_payload(graph_response, "GraphQL response"), node_id)
    except (_sibling.ApiFailure, _sibling.BudgetExhausted, ValueError, TypeError, AttributeError) as error:
        graphql_warnings = [_sibling.hydration_warning(error)]
    graphql_meta = _sibling.completeness(
        GRAPHQL_EVIDENCE_ENDPOINT, facts is not None and not graphql_warnings, 1 if facts is not None else 0,
        None, captured_at, 1 if facts is not None else 0, None, graphql_warnings,
    )
    cross_references, unresolvable = _timeline_references(timeline)
    completeness = {"issue": core_meta, "comments": comments_meta, "timeline": timeline_meta, "graphql": graphql_meta}
    partial_categories = [category for category, meta in completeness.items() if not meta["pages_complete"]]
    html_url = _text(payload.get("html_url"))
    state = _text(payload.get("state"))
    state_reason = _text(payload.get("state_reason"))
    labels = payload.get("labels") if isinstance(payload.get("labels"), list) else []
    closed_by = payload.get("closed_by")
    issue_type = payload.get("type")
    observations = [{
        "run_id": run_id,
        "origin_kind": "issue-body",
        "issue_node_id": node_id,
        "api_url": _text(payload.get("url")),
        "html_url": html_url,
        "updated_at": _text(payload.get("updated_at")),
        "body_sha256": _sha256_text(body),
        "captured_at": captured_at,
    }]
    for comment in comments:
        user = comment.get("user") if isinstance(comment.get("user"), dict) else {}
        observations.append({
            "run_id": run_id,
            "origin_kind": "comment",
            "comment_id": comment.get("id"),
            "comment_node_id": _text(comment.get("node_id")),
            "comment_url": _text(comment.get("url")),
            "comment_html_url": _text(comment.get("html_url")),
            "commenter_login": _text(user.get("login")),
            "author_association": _text(comment.get("author_association")),
            "created_at": _text(comment.get("created_at")),
            "updated_at": _text(comment.get("updated_at")),
            "body_sha256": _sha256_text(comment.get("body")),
            "captured_at": captured_at,
        })
    closed_at = _text(payload.get("closed_at"))
    return {
        "identity_status": "resolved",
        "record_key": "github-issue:" + node_id,
        "issue_id": None,
        "issue_node_id": node_id,
        "item_type": "issue",
        "input_path": "general-issue",
        "repository": {
            "full_name": _text(repository_metadata.get("full_name")) or repository,
            "node_id": _text(repository_metadata.get("node_id")),
            "repository_aliases": [],
        },
        "issue": {
            "number": number,
            "url": _text(payload.get("url")),
            "html_url": html_url,
            "title": _text(payload.get("title")),
            "created_at": _text(payload.get("created_at")),
            "updated_at": _text(payload.get("updated_at")),
            "closed_at": closed_at,
            "state": state,
            "state_reason_raw": state_reason,
            "labels_raw": [label["name"] for label in labels if isinstance(label, dict) and isinstance(label.get("name"), str)],
            "locked": payload.get("locked") if isinstance(payload.get("locked"), bool) else None,
            "active_lock_reason": _text(payload.get("active_lock_reason")),
            "closed_by_login": _text(closed_by.get("login")) if isinstance(closed_by, dict) else None,
            "github_issue_type_raw": _text(issue_type.get("name")) if isinstance(issue_type, dict) else None,
        },
        "author": _sibling.author(payload),
        "sources": [{
            "source_key": "general-issue",
            "kind": "search-api",
            "collection_method": COLLECTION_METHOD,
            "generated_by": {"name": SKILL_NAME, "revision": skill_revision},
            "observations": observations,
        }],
        "state_history": [{
            "state": state,
            "state_reason_raw": state_reason,
            "observed_at": closed_at if state == "closed" and closed_at else _text(payload.get("updated_at")),
            "authority": "GitHub issue",
            "evidence_url": html_url,
        }],
        "closure": {"state_reason_raw": state_reason, "normalized_cause": "unknown"},
        "hydration_status": "partial" if partial_categories else "complete",
        "evidence_snapshot": {
            "body_excerpt": body,
            "comments": [_discussion_evidence(item) for item in comments],
            "timeline_events": [_timeline_evidence(item) for item in timeline],
            "related_pull_requests": (facts["related"] if facts else []) + cross_references,
            "unresolvable_references": unresolvable,
            "closed_events": facts["closed_events"] if facts else [],
            "duplicate_of": facts["duplicate_of"] if facts else None,
            "edit_history": facts["edit_history"] if facts else None,
            "partial_categories": partial_categories,
            "completeness": completeness,
        },
    }


def _observation_identity(observation: dict[str, object]) -> tuple[object, ...]:
    if observation.get("origin_kind") == "comment":
        return ("comment", observation.get("comment_node_id") or observation.get("comment_id"),
                observation.get("updated_at"), observation.get("body_sha256"))
    # Issue-level updated_at also moves on labels and comments, so a body is identified by its content.
    return (observation.get("origin_kind"), observation.get("issue_node_id"), observation.get("body_sha256"))


def merge_issue_records(corpus: dict[str, object], incoming: list[dict[str, object]]) -> dict[str, object]:
    """Merge hydrated Issues by node identity without rewriting history.

    Observation identity excludes the run ID, so unchanged recollection is not
    duplicated while edited bodies and comments append. ``ISS-*`` IDs are
    stable and new IDs continue after the greatest existing suffix.
    """
    merged = deepcopy(corpus)
    records: list[object] = merged["records"]
    positions = {
        record.get("record_key"): index
        for index, record in enumerate(records)
        if isinstance(record, dict) and isinstance(record.get("record_key"), str)
    }
    next_id = 1 + max(
        (int(match.group(1)) for record in records if isinstance(record, dict)
         for match in [_ISSUE_ID.fullmatch(str(record.get("issue_id")))] if match),
        default=0,
    )
    for record in incoming:
        key = record["record_key"]
        if key not in positions:
            added = deepcopy(record)
            added["issue_id"] = "ISS-{0}".format(next_id)
            next_id += 1
            positions[key] = len(records)
            records.append(added)
            continue
        current = records[positions[key]]
        _append_sources(current, record)
        history = current.setdefault("state_history", [])
        latest = record["state_history"][-1]
        if not history or {k: history[-1].get(k) for k in ("state", "state_reason_raw")} != {
            k: latest.get(k) for k in ("state", "state_reason_raw")
        }:
            history.append(deepcopy(latest))
        if (record["issue"].get("updated_at") or "") >= (current.get("issue", {}).get("updated_at") or ""):
            previous_snapshot = current.get("evidence_snapshot")
            for field in PROJECTION_FIELDS:
                current[field] = deepcopy(record[field])
            if isinstance(previous_snapshot, dict):
                current["evidence_snapshot"] = _keep_complete_categories(previous_snapshot, current["evidence_snapshot"])
                partial = current["evidence_snapshot"]["partial_categories"]
                current["hydration_status"] = "partial" if partial else "complete"
        repository = current.setdefault("repository", {})
        incoming_name = record["repository"]["full_name"]
        if repository.get("full_name") not in (None, incoming_name):
            aliases = repository.setdefault("repository_aliases", [])
            if repository["full_name"] not in aliases:
                aliases.append(repository["full_name"])
            repository["full_name"] = incoming_name
        if repository.get("node_id") is None:
            repository["node_id"] = record["repository"]["node_id"]
    return merged


# Snapshot fields owned by each evidence category, and the related pull request methods it supplies.
CATEGORY_FIELDS = {
    "comments": (("comments",), ()),
    "timeline": (("timeline_events", "unresolvable_references"), ("rest-timeline",)),
    "graphql": (("closed_events", "duplicate_of", "edit_history"),
                ("graphql-closed-event", "graphql-closing-references")),
}


def _keep_complete_categories(previous: dict[str, object], incoming: dict[str, object]) -> dict[str, object]:
    """Keep earlier complete evidence for any category this run failed to read.

    Each kept category retains its own completeness entry and capture time, so
    the snapshot stays auditable about when each part was observed.
    """
    merged = deepcopy(incoming)
    previous_completeness = previous.get("completeness") if isinstance(previous.get("completeness"), dict) else {}
    kept_methods: set[str] = set()
    for category, (fields, methods) in CATEGORY_FIELDS.items():
        old_meta = previous_completeness.get(category)
        if merged["completeness"][category]["pages_complete"] or not (
            isinstance(old_meta, dict) and old_meta.get("pages_complete") is True
        ):
            continue
        for field in fields:
            merged[field] = deepcopy(previous.get(field))
        merged["completeness"][category] = deepcopy(old_meta)
        kept_methods.update(methods)
    if kept_methods:
        order = ("graphql-closed-event", "graphql-closing-references", "rest-timeline")
        sources = {
            method: previous if method in kept_methods else incoming
            for method in order
        }
        merged["related_pull_requests"] = [
            deepcopy(item)
            for method in order
            for item in sources[method].get("related_pull_requests", [])
            if isinstance(item, dict) and item.get("relation_method") == method
        ]
    merged["partial_categories"] = [
        category for category, meta in merged["completeness"].items() if not meta.get("pages_complete")
    ]
    return merged


def _append_sources(current: dict[str, object], incoming: dict[str, object]) -> None:
    sources = current.setdefault("sources", [])
    for source in incoming["sources"]:
        existing = next((item for item in sources if isinstance(item, dict)
                         and item.get("source_key") == source["source_key"]), None)
        if existing is None:
            sources.append(deepcopy(source))
            continue
        observations = existing.setdefault("observations", [])
        seen = {_observation_identity(item) for item in observations if isinstance(item, dict)}
        for observation in source["observations"]:
            identity = _observation_identity(observation)
            if identity not in seen:
                seen.add(identity)
                observations.append(deepcopy(observation))


METHOD_LIMITATIONS = (
    "search-index: GitHub search is index-backed; the hydrated Issue is authoritative, and reading every "
    "page does not remove index delay or missing indexed content.",
    "unverified:private-cross-reference-visibility: how the timeline presents cross-references from "
    "repositories the viewer cannot read (omitted or masked) is unverified; a missing cross-reference is not "
    "evidence that no pull request exists.",
    "unverified:linked-pr-qualifier: the correspondence between the search qualifier linked:pr and GraphQL "
    "closedByPullRequestsReferences is unverified; this collector does not use linked:pr and records "
    "relations only from observed evidence.",
)
UPDATED_FIELD_LIMITATION = (
    "volatile-updated-at: updated_at also moves on non-comment events such as label changes, so repeating an "
    "updated-field collection can select a different population."
)


def request_fingerprint(
    repositories: list[str], date_field: str, state: str, labels: list[str], interval: Any,
    max_per_repository: int, request_budget: int, api_version: str,
) -> str:
    payload = {
        "repositories": repositories,
        "date_field": date_field,
        "state": state,
        "labels": labels,
        "interval": {"start_at": interval.start_at, "end_at": interval.end_at,
                     "timezone": interval.timezone, "input_mode": interval.input_mode},
        "max_per_repository": max_per_repository,
        "request_budget": request_budget,
        "api_version": api_version,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


class CollectionRun:
    """The in-memory corpus, manifest, and process exit classification."""

    def __init__(self, corpus: dict[str, object], manifest: dict[str, object], exit_code: int,
                 collected_any: bool) -> None:
        self.corpus = corpus
        self.manifest = manifest
        self.exit_code = exit_code
        self.collected_any = collected_any


def _empty_corpus(skill_revision: str) -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "corpus_kind": "github-issue",
        "generated_by": {"name": SKILL_NAME, "revision": skill_revision},
        "records": [],
    }


def collect(
    rest: Any,
    graphql: Any,
    *,
    repositories: list[str],
    date_field: str,
    state: str,
    labels: list[str],
    interval: Any,
    max_per_repository: int,
    existing_corpus: Optional[dict[str, object]] = None,
    existing_manifest: Optional[dict[str, object]] = None,
    captured_at: Optional[str] = None,
    skill_revision: Optional[str] = None,
) -> CollectionRun:
    """Collect each repository serially into an append-only Issue corpus run."""
    validate_repositories(repositories)
    validate_filters(date_field, state, labels)
    revision = skill_revision or compute_skill_revision()
    budget = rest.budget
    api_version = rest.api_version
    timestamp = _run_timestamp(captured_at)
    fingerprint = request_fingerprint(repositories, date_field, state, labels, interval,
                                      max_per_repository, budget.limit, api_version)
    run_id = "run-" + hashlib.sha256((timestamp + fingerprint).encode("utf-8")).hexdigest()[:20]
    prior_runs = deepcopy(existing_manifest["records"]) if existing_manifest is not None else []
    corpus = deepcopy(existing_corpus) if existing_corpus is not None else _empty_corpus(revision)
    limitations = list(METHOD_LIMITATIONS) + ([UPDATED_FIELD_LIMITATION] if date_field == "updated" else [])
    run: dict[str, object] = {
        "run_id": run_id,
        "request_fingerprint": fingerprint,
        "collection_method": COLLECTION_METHOD,
        "collection_status": "failed",
        "started_at": timestamp,
        "completed_at": None,
        "api_version": api_version,
        "client_version": "unknown",
        "filters": {
            "repositories": list(repositories),
            "date_field": date_field,
            "state": state,
            "labels": list(labels),
            "label_semantics": "all-of",
        },
        "interval": {"start_at": interval.start_at, "end_at": interval.end_at, "timezone": interval.timezone,
                     "input_mode": deepcopy(interval.input_mode), "as_of": interval.as_of,
                     "last_day_partial": interval.last_day_partial},
        "max_per_repository": max_per_repository,
        "request_budget": budget.limit,
        "request_count": 0,
        "request_events": [],
        "preflight": {},
        "repositories": [],
        "failed_scopes": [],
        "warnings": [],
        "method_limitations": limitations,
    }

    def finish(status: str, exit_code: int, collected_any: bool) -> CollectionRun:
        run["collection_status"] = status
        run["completed_at"] = _run_timestamp(None)
        run["request_count"] = budget.consumed
        run["request_events"] = deepcopy(rest.request_events)
        manifest = {
            "schema_version": "2.0.0",
            "generated_by": {"name": SKILL_NAME, "revision": revision,
                             "api_version": run["api_version"], "client_version": run["client_version"]},
            "records": prior_runs + [run],
        }
        return CollectionRun(corpus, manifest, exit_code, collected_any)

    try:
        preflight = rest.global_preflight()
        run["preflight"] = deepcopy(preflight)
        run["client_version"] = str(preflight.get("client_version", "unknown"))
    except (_sibling.ApiFailure, _sibling.BudgetExhausted, ValueError) as error:
        run["warnings"].append(_sibling.hydration_warning(error))
        run["failed_scopes"].append({"scope": "preflight", "outcome": "failed", "reason": _sibling.hydration_warning(error)})
        return finish("failed", 4, False)

    collected_any = False
    partial = False
    for repository in repositories:
        entry: dict[str, object] = {
            "repository": repository,
            "collection_status": "partial",
            "split_observations": [],
            "split_observation_history": "complete-since-run-start",
        }
        run["repositories"].append(entry)
        search = collect_repository_issue_hits(
            rest, repository, interval, date_field, state, labels,
            on_split_observation=lambda observation: entry["split_observations"].append(deepcopy(observation)),
        )
        warnings = list(search["warnings"])
        excluded = dict(search["excluded"])
        hydrated: list[dict[str, object]] = []
        partial_records: list[dict[str, object]] = []
        processed = 0
        stopped = False
        for hit in search["hits"]:
            if len(hydrated) >= max_per_repository:
                break
            processed += 1
            try:
                record = hydrate_issue(rest, graphql, repository, hit, repository_metadata=search["preflight"],
                                       run_id=run_id, captured_at=timestamp, skill_revision=revision)
            except PullRequestPayload:
                excluded["is-pull-request"] += 1
                continue
            except _sibling.BudgetExhausted as error:
                # No request was sent for this hit, so it and every later hit are unattempted.
                warnings.append(_sibling.hydration_warning(error))
                run["failed_scopes"].append({"repository": repository, "scope": "issue",
                                             "number": hit.get("number"), "outcome": "budget-exhausted"})
                processed -= 1
                stopped = True
                break
            except (_sibling.ApiFailure, ValueError, TypeError, KeyError) as error:
                outcome = (_sibling.classify_repository_failure(status=error.status)
                           if isinstance(error, _sibling.ApiFailure) else "failed")
                partial_records.append(_partial_issue(hit, outcome, _sibling.hydration_warning(error)))
                run["failed_scopes"].append({"repository": repository, "scope": "issue",
                                             "number": hit.get("number"), "outcome": outcome})
                continue
            if state != "all" and record["issue"]["state"] != state:
                excluded["state-changed-after-search"] = excluded.get("state-changed-after-search", 0) + 1
                continue
            hydrated.append(record)
        complete_issues = sum(1 for record in hydrated if record["hydration_status"] == "complete")
        if hydrated:
            corpus = merge_issue_records(corpus, hydrated)
            collected_any = True
        repository_partial = bool(search["partial"] or partial_records or stopped or complete_issues != len(hydrated))
        if search["preflight_outcome"] != "collected":
            status = "partial" if search["preflight_outcome"] == "partial" else search["preflight_outcome"]
            run["failed_scopes"].append({"repository": repository, "scope": "repository",
                                         "outcome": search["preflight_outcome"]})
        elif repository_partial:
            status = "partial"
        else:
            status = "collected" if hydrated else "no-results"
        for partition in search["partitions"]:
            if partition.completion_state != "complete":
                run["failed_scopes"].append({"repository": repository, "scope": "search-partition",
                                             "interval": list(partition.interval), "outcome": "failed",
                                             "reason": partition.failure})
        partial = partial or status not in {"collected", "no-results"}
        entry.update({
            "collection_status": status,
            "preflight_outcome": search["preflight_outcome"],
            "partitions": [_sibling.serialise_partition(partition) for partition in search["partitions"]],
            "matched_count": len(search["hits"]),
            "selected_count": len(hydrated),
            "excluded_by_cap": len(search["hits"]) - processed if len(hydrated) >= max_per_repository else 0,
            "not_attempted": len(search["hits"]) - processed if stopped else 0,
            "excluded": excluded,
            "complete_issues": complete_issues,
            "partial_issues": len(hydrated) - complete_issues,
            "partial_records": partial_records,
            "warnings": warnings,
        })

    if not partial:
        return finish("complete", 0, collected_any)
    if collected_any:
        return finish("partial", 3, True)
    return finish("failed", 4, False)


def _partial_issue(hit: dict[str, object], outcome: str, reason: str) -> dict[str, object]:
    return {
        "number": hit.get("number"),
        "node_id": hit.get("node_id"),
        "url": hit.get("html_url"),
        "outcome": outcome,
        "reason": reason,
    }


SKILL_REVISION_PATHS = (
    "SKILL.md",
    "agents/openai.yaml",
    "references/collection-contract.md",
    "references/github-api-contract.md",
    "scripts/collect_open_source_issues.py",
    "tests/test_collect_open_source_issues.py",
)


def compute_skill_revision(skill_dir: object = SKILL_DIR) -> str:
    """Hash the canonical six paths with deterministic length framing."""
    root = Path(skill_dir)
    digest = hashlib.sha256()
    for relative in sorted(SKILL_REVISION_PATHS):
        path_bytes = relative.encode("utf-8")
        content = (root / relative).read_bytes()
        digest.update(len(path_bytes).to_bytes(8, byteorder="big"))
        digest.update(path_bytes)
        digest.update(len(content).to_bytes(8, byteorder="big"))
        digest.update(content)
    return "sha256:" + digest.hexdigest()


def _load_json_file(path: str, label: str) -> object:
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CliInputError("{0} is not readable JSON: {1}".format(label, error)) from error


def validate_issue_corpus(document: object, label: str) -> dict[str, object]:
    if (
        not isinstance(document, dict)
        or document.get("schema_version") != "1.0.0"
        or document.get("corpus_kind") != "github-issue"
        or not isinstance(document.get("records"), list)
    ):
        raise CliInputError(label + " is not an Issue corpus (schema_version 1.0.0, corpus_kind github-issue)")
    for index, record in enumerate(document["records"]):
        if (
            not isinstance(record, dict)
            or not isinstance(record.get("record_key"), str)
            or not record["record_key"].startswith("github-issue:")
            or not all(isinstance(record.get(field), dict) for field in ("repository", "issue", "evidence_snapshot"))
            or not all(isinstance(record.get(field), list) for field in ("sources", "state_history"))
        ):
            raise CliInputError("{0} record {1} does not have the Issue record shape".format(label, index))
    return document


def validate_issue_manifest(document: object, label: str) -> dict[str, object]:
    generated_by = document.get("generated_by") if isinstance(document, dict) else None
    if (
        not isinstance(document, dict)
        or document.get("schema_version") != "2.0.0"
        or not isinstance(generated_by, dict)
        or generated_by.get("name") != SKILL_NAME
        or not isinstance(document.get("records"), list)
    ):
        raise CliInputError(label + " is not a " + SKILL_NAME + " manifest (schema_version 2.0.0)")
    return document


def _prepare_request(args: argparse.Namespace) -> dict[str, object]:
    repositories = validate_repositories(args.repo)
    validate_filters(args.date_field, args.state, args.label)
    for name, value in (("--max-per-repo", args.max_per_repo), ("--request-budget", args.request_budget)):
        if value <= 0:
            raise CliInputError(name + " must be a positive integer")
    try:
        interval = resolve_interval(
            start_at=args.start_at,
            end_at=args.end_at,
            start_date=args.start_date,
            end_date=args.end_date,
            recent_days=args.recent_days,
            timezone_name=args.timezone,
            as_of=args.as_of,
        )
    except (ValueError, OverflowError) as error:
        raise CliInputError(str(error)) from error
    output = os.path.abspath(args.output)
    manifest = os.path.abspath(args.manifest)
    if output == manifest or (
        os.path.exists(output) and os.path.exists(manifest) and os.path.samefile(output, manifest)
    ):
        raise CliInputError("--output and --manifest must be distinct files")
    for option, path in (("--output", output), ("--manifest", manifest)):
        if not os.path.isdir(os.path.dirname(path)):
            raise CliInputError(option + " directory does not exist: " + os.path.dirname(path))
    existing_corpus = None
    if os.path.exists(output):
        existing_corpus = validate_issue_corpus(_load_json_file(output, "existing output"), "existing output")
    existing_manifest = None
    if os.path.exists(manifest):
        existing_manifest = validate_issue_manifest(_load_json_file(manifest, "existing manifest"), "existing manifest")
    return {
        "repositories": repositories,
        "interval": interval,
        "existing_corpus": existing_corpus,
        "existing_manifest": existing_manifest,
        "output": output,
        "manifest": manifest,
    }


def main(
    argv: Optional[list[str]] = None,
    *,
    runner: Optional[Callable[..., Any]] = None,
    sleeper: Callable[[float], None] = clock_time.sleep,
) -> int:
    effective_argv = list(sys.argv[1:] if argv is None else argv)
    if effective_argv == ["--print-revision"]:
        print(compute_skill_revision())
        return 0
    try:
        args = build_parser().parse_args(effective_argv)
        request = _prepare_request(args)
        rest, graphql = build_clients(
            api_version=args.api_version, request_budget=args.request_budget, runner=runner, sleeper=sleeper,
        )
    except (CliInputError, ValueError) as error:
        print("error: " + str(error), file=sys.stderr)
        return 2
    run = collect(
        rest,
        graphql,
        repositories=request["repositories"],
        date_field=args.date_field,
        state=args.state,
        labels=list(args.label),
        interval=request["interval"],
        max_per_repository=args.max_per_repo,
        existing_corpus=request["existing_corpus"],
        existing_manifest=request["existing_manifest"],
    )
    if run.collected_any or request["existing_corpus"] is None:
        _sibling.atomic_write_json(request["output"], run.corpus)
    _sibling.atomic_write_json(request["manifest"], run.manifest)
    return run.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
