"""Collect synthetic or caller-owned tracker Issue pull request submissions."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any, Callable, Optional
from urllib.parse import parse_qs, urlparse


SKILL_NAME = "collecting-curated-contribution-prs"
COLLECTION_METHOD = "tracker-issue-comments"
SKILL_DIR = Path(__file__).resolve().parents[1]
SIBLING_SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "collecting-recent-closed-prs"
    / "scripts"
    / "collect_recent_closed_prs.py"
)
SKILL_REVISION_PATHS = (
    "SKILL.md",
    "agents/openai.yaml",
    "references/collection-contract.md",
    "references/github-rest-contract.md",
    "scripts/collect_curated_contribution_prs.py",
    "tests/test_collect_curated_contribution_prs.py",
)
REPOSITORY = re.compile(r"\A[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
PULL_REQUEST_URL = re.compile(
    r"https://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)/pull/([1-9][0-9]*)"
)
URL_SPAN = re.compile(r"https?://[^\s<>()\[\]{}]+", re.IGNORECASE)
REFERENCE_EXCLUSION_KEYWORDS = {
    "en": ("example", "examples", "notice", "notices", "announcement"),
    "ko": ("예시", "공지"),
}
_SIBLING_CACHE: dict[Path, Any] = {}


class CollectionRun:
    """The in-memory corpus, manifest, and process exit classification."""

    def __init__(self, corpus: dict[str, object], manifest: dict[str, object], exit_code: int) -> None:
        self.corpus = corpus
        self.manifest = manifest
        self.exit_code = exit_code


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


def load_sibling(script_path: object = SIBLING_SCRIPT) -> Any:
    """Load the adjacent collector once from its file-relative path."""
    path = Path(script_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    if path in _SIBLING_CACHE:
        return _SIBLING_CACHE[path]
    module_name = "_collecting_recent_closed_prs_sibling"
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collect pull request submissions from a caller-supplied tracker Issue",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--print-revision",
        action="store_true",
        help="print the packaged skill revision and exit",
    )
    commands = parser.add_subparsers(dest="command")
    collect_parser = commands.add_parser("collect")
    collect_parser.add_argument("--tracker-repo", required=True)
    collect_parser.add_argument("--issue", required=True, type=int)
    collect_parser.add_argument("--max-prs", required=True, type=int)
    collect_parser.add_argument("--request-budget", required=True, type=int)
    collect_parser.add_argument("--output", required=True)
    collect_parser.add_argument("--manifest", required=True)
    collect_parser.add_argument("--existing-corpus")
    collect_parser.add_argument("--existing-manifest")
    collect_parser.add_argument("--resume-run-id")
    return parser


def normalize_repository(value: object) -> str:
    """Return a canonical repository name after validating both path segments."""
    if not isinstance(value, str) or REPOSITORY.fullmatch(value) is None:
        raise ValueError("repository must be OWNER/REPO")
    owner, repository = value.split("/")
    if owner in {".", ".."} or repository in {".", ".."}:
        raise ValueError("repository must be OWNER/REPO")
    return value.lower()


def validate_cli_args(args: argparse.Namespace) -> None:
    try:
        normalize_repository(args.tracker_repo)
    except ValueError:
        raise ValueError("tracker repository must be OWNER/REPO")
    for name in ("issue", "max_prs", "request_budget"):
        value = getattr(args, name)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValueError(name.replace("_", " ") + " must be a positive integer")
    output = Path(args.output).resolve()
    manifest = Path(args.manifest).resolve()
    aliases = output == manifest
    if output.exists() and manifest.exists():
        aliases = aliases or os.path.samefile(output, manifest)
    if aliases:
        raise ValueError("corpus output and manifest output must be different paths")
    for label, destination in (("corpus output", output), ("manifest output", manifest)):
        if not destination.parent.is_dir():
            raise ValueError(label + " parent directory does not exist")
        if destination.exists() and not destination.is_file():
            raise ValueError(label + " must name a regular file")
        if not os.access(destination.parent, os.W_OK):
            raise ValueError(label + " parent directory is not writable")
    has_corpus = args.existing_corpus is not None
    has_manifest = args.existing_manifest is not None
    if has_corpus != has_manifest:
        raise ValueError("existing corpus and existing manifest must be supplied together")
    if args.resume_run_id is not None and not (has_corpus and has_manifest):
        raise ValueError("resume requires existing corpus and existing manifest")
    if args.resume_run_id is not None and not args.resume_run_id.strip():
        raise ValueError("resume run ID must be non-empty")


def _response_payload(response: object, label: str) -> object:
    if not hasattr(response, "payload"):
        raise ValueError(label + " has no payload")
    return getattr(response, "payload")


def _header(response: object, name: str) -> dict[str, object]:
    headers = getattr(response, "headers", None)
    if headers is None:
        return {"state": "absent", "value": None}
    if not isinstance(headers, dict):
        return {"state": "unsupported-container", "value": None}
    for key, value in headers.items():
        if isinstance(key, str) and key.lower() == name.lower() and isinstance(value, str):
            has_next = re.search(
                r"(?:^|;)\s*rel\s*=\s*[\"']?next[\"']?\s*(?:;|$)",
                value,
                re.IGNORECASE,
            ) is not None
            has_terminal_relation = re.search(
                r"(?:^|;)\s*rel\s*=\s*[\"']?(?:prev|first)[\"']?\s*(?:;|$)",
                value,
                re.IGNORECASE,
            ) is not None
            return {
                "state": (
                    "present-terminal" if not has_next and has_terminal_relation else "present-next"
                ),
                "value": value,
            }
    return {"state": "absent", "value": None}


def validate_next_link(link_header: str, comments_endpoint: str, current_page: int) -> dict[str, object]:
    """Parse and validate one authoritative ``rel=next`` comment URL."""
    result: dict[str, object] = {
        "next_url": None,
        "parsed_next_page": None,
        "link_validation": "invalid",
        "link_failure_reason": "malformed Link rel=next",
    }
    if not isinstance(link_header, str):
        return result
    next_url = None
    for part in link_header.split(","):
        if re.search(r"(?:^|;)\s*rel\s*=\s*[\"']?next[\"']?\s*(?:;|$)", part, re.IGNORECASE):
            match = re.search(r"<([^>]+)>", part)
            if match is not None:
                next_url = match.group(1)
            break
    result["next_url"] = next_url
    if next_url is None:
        return result
    try:
        parsed = urlparse(next_url)
        query = parse_qs(parsed.query, keep_blank_values=True, strict_parsing=True)
    except ValueError:
        return result
    if parsed.scheme != "https" or parsed.netloc != "api.github.com":
        result["link_failure_reason"] = "next URL must use https://api.github.com"
        return result
    if parsed.path != comments_endpoint or parsed.fragment:
        result["link_failure_reason"] = "next URL comments endpoint mismatch"
        return result
    if set(query) - {"page", "per_page"}:
        result["link_failure_reason"] = "next URL has unsupported pagination query"
        return result
    if len(query.get("page", [])) != 1 or not query["page"][0].isdigit():
        result["link_failure_reason"] = "next URL requires one numeric page"
        return result
    page = int(query["page"][0])
    result["parsed_next_page"] = page
    if page != current_page + 1:
        result["link_failure_reason"] = "next URL page is not current page plus one"
        return result
    if "per_page" in query and query["per_page"] != ["100"]:
        result["link_failure_reason"] = "next URL per_page must be 100"
        return result
    result["link_validation"] = "valid"
    result["link_failure_reason"] = None
    return result


def collect_issue_thread(client: Any, tracker_repo: str, issue_number: int) -> dict[str, object]:
    """Collect an Issue and Link-authorized comment pages in database-ID order."""
    issue_endpoint = "/repos/{0}/issues/{1}".format(tracker_repo, issue_number)
    comments_endpoint = issue_endpoint + "/comments"
    issue = _response_payload(client.get_json(issue_endpoint), "tracker Issue response")
    if not isinstance(issue, dict):
        raise ValueError("tracker Issue response payload must be an object")

    comments: list[dict[str, object]] = []
    pages: list[dict[str, object]] = []
    failed_scopes: list[dict[str, object]] = []
    previous_id: Optional[int] = None
    page = 1
    while True:
        try:
            response = client.get_json(comments_endpoint, params={"page": page})
        except Exception as error:
            failed_scopes.append({
                "kind": "pagination",
                "endpoint": comments_endpoint,
                "page": page,
                "reason": str(error),
            })
            break
        payload = _response_payload(response, "tracker comments response")
        if not isinstance(payload, list) or not all(isinstance(item, dict) for item in payload):
            failed_scopes.append({
                "kind": "pagination",
                "endpoint": comments_endpoint,
                "page": page,
                "reason": "comments payload must be an array of objects",
            })
            break

        identifiers: list[int] = []
        order_error = None
        for item in payload:
            identifier = item.get("id")
            if not isinstance(identifier, int) or isinstance(identifier, bool):
                order_error = "comment database ID must be an integer"
                break
            if previous_id is not None and identifier <= previous_id:
                order_error = "comment database IDs are not strictly increasing"
                break
            identifiers.append(identifier)
            previous_id = identifier

        link_result = _header(response, "link")
        link = link_result["value"]
        provenance: dict[str, object] = {
            "endpoint": comments_endpoint,
            "requested_page": page,
            "next_url": None,
            "parsed_next_page": None,
            "link_state": link_result["state"],
            "link_validation": (
                "terminal"
                if link_result["state"] == "present-terminal"
                else "unsupported"
                if link_result["state"] == "unsupported-container"
                else "absent"
            ),
            "link_failure_reason": None,
            "comment_id_min": min(identifiers) if identifiers else None,
            "comment_id_max": max(identifiers) if identifiers else None,
            "comment_count": len(identifiers),
        }
        if link_result["state"] == "present-next":
            provenance.update(validate_next_link(link, comments_endpoint, page))
        pages.append(provenance)
        if order_error is not None:
            failed_scopes.append({
                "kind": "comment-order",
                "endpoint": comments_endpoint,
                "page": page,
                "reason": order_error,
            })
            break
        comments.extend(deepcopy(payload))
        if link_result["state"] == "unsupported-container":
            failed_scopes.append({
                "kind": "header-container",
                "endpoint": comments_endpoint,
                "page": page,
                "reason": "unsupported response headers container",
            })
            break
        if link_result["state"] in {"absent", "present-terminal"}:
            break
        if provenance["link_validation"] != "valid":
            failed_scopes.append({
                "kind": "pagination-link",
                "endpoint": comments_endpoint,
                "page": page,
                "next_url": provenance["next_url"],
                "reason": provenance["link_failure_reason"],
            })
            break
        page = int(provenance["parsed_next_page"])

    return {
        "issue": deepcopy(issue),
        "comments": comments,
        "pages": pages,
        "failed_scopes": failed_scopes,
    }


def _body_hash(body: object) -> str:
    if not isinstance(body, str):
        raise ValueError("tracker body must be a string")
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def issue_observation(issue: dict[str, object], run_id: str) -> dict[str, object]:
    return {
        "run_id": run_id,
        "origin_kind": "issue-body",
        "issue_node_id": issue.get("node_id"),
        "issue_url": issue.get("url"),
        "api_url": issue.get("url"),
        "html_url": issue.get("html_url"),
        "updated_at": issue.get("updated_at"),
        "body_sha256": _body_hash(issue.get("body")),
    }


def comment_observation(comment: dict[str, object], run_id: str) -> dict[str, object]:
    user = comment.get("user") if isinstance(comment.get("user"), dict) else {}
    return {
        "run_id": run_id,
        "origin_kind": "comment",
        "comment_id": comment.get("id"),
        "comment_node_id": comment.get("node_id"),
        "comment_url": comment.get("url"),
        "comment_html_url": comment.get("html_url"),
        "commenter_login": user.get("login"),
        "tracker_author_association": comment.get("author_association"),
        "created_at": comment.get("created_at"),
        "updated_at": comment.get("updated_at"),
        "body_sha256": _body_hash(comment.get("body")),
    }


def _reference_classification_basis(body: str, match_start: int) -> Optional[dict[str, str]]:
    line_start = body.rfind("\n", 0, match_start) + 1
    same_line_prefix = body[line_start:match_start].strip()
    previous_line = ""
    if line_start > 0:
        previous_end = line_start - 1
        previous_start = body.rfind("\n", 0, previous_end) + 1
        previous_line = body[previous_start:previous_end].strip()

    for label_scope, label in (
        ("same-line-prefix", same_line_prefix),
        ("previous-line", previous_line),
    ):
        evaluated_label = URL_SPAN.sub("", label).strip()
        folded = evaluated_label.casefold()
        for language, keywords in REFERENCE_EXCLUSION_KEYWORDS.items():
            for keyword in keywords:
                if language == "en":
                    matched = re.search(
                        r"(?<![A-Za-z])" + re.escape(keyword) + r"(?![A-Za-z])",
                        folded,
                    )
                else:
                    matched = re.match(
                        re.escape(keyword) + r"(?=$|[:：\-–—])",
                        folded,
                    )
                if matched:
                    return {
                        "matched_keyword": keyword,
                        "label_scope": label_scope,
                        "evaluated_label": evaluated_label,
                    }
    return None


def extract_references(
    issue: dict[str, object],
    comments: list[dict[str, object]],
    *,
    run_id: str,
) -> list[dict[str, object]]:
    """Extract inert PR URL evidence in Issue-then-comment encounter order."""
    origins: list[tuple[str, dict[str, object]]] = [("issue-body", issue)]
    origins.extend(("comment", comment) for comment in comments)
    references: list[dict[str, object]] = []
    for kind, origin in origins:
        body = origin.get("body")
        if not isinstance(body, str):
            continue
        observation = (
            issue_observation(origin, run_id)
            if kind == "issue-body"
            else comment_observation(origin, run_id)
        )
        for match in PULL_REQUEST_URL.finditer(body):
            classification_basis = _reference_classification_basis(body, match.start())
            reference = {
                "identity": (match.group(1).lower(), int(match.group(2))),
                "url": match.group(0),
                "classification": (
                    "excluded-example-or-notice" if classification_basis is not None else "submission"
                ),
                "observation": deepcopy(observation),
            }
            if classification_basis is not None:
                reference["classification_basis"] = classification_basis
            references.append(reference)
    return references


def select_references(references: list[dict[str, object]], *, max_prs: int) -> dict[str, object]:
    grouped: dict[tuple[str, int], dict[str, object]] = {}
    order: list[tuple[str, int]] = []
    exclusions: list[dict[str, object]] = []
    warnings: list[str] = []
    failed_scopes: list[dict[str, object]] = []
    for reference in references:
        if reference.get("classification") != "submission":
            exclusions.append(deepcopy(reference))
            continue
        identity = reference.get("identity")
        if not (
            isinstance(identity, tuple)
            and len(identity) == 2
            and isinstance(identity[0], str)
            and isinstance(identity[1], int)
        ):
            continue
        try:
            repository = normalize_repository(identity[0])
        except ValueError:
            exclusions.append({
                "classification": "excluded-invalid-repository",
                "reason": "invalid repository identity",
                "observation": deepcopy(reference.get("observation")),
            })
            warnings.append("reference-identity: invalid repository identity excluded")
            failed_scopes.append({
                "kind": "reference-identity",
                "reason": "invalid repository identity",
            })
            continue
        identity = (repository, identity[1])
        if identity not in grouped:
            grouped[identity] = {"identity": identity, "references": []}
            order.append(identity)
        grouped[identity]["references"].append(deepcopy(reference))
    matched = [grouped[identity] for identity in order]
    return {
        "matched_count": len(matched),
        "selected_count": min(len(matched), max_prs),
        "excluded_by_cap": max(0, len(matched) - max_prs),
        "selected": matched[:max_prs],
        "cap_exclusions": matched[max_prs:],
        "reference_exclusions": exclusions,
        "warnings": warnings,
        "failed_scopes": failed_scopes,
    }


def _tracker_source_key(issue_node_id: object) -> str:
    if not isinstance(issue_node_id, str) or not issue_node_id:
        raise ValueError("tracker Issue requires a node ID")
    return "tracker-issue:" + hashlib.sha256(issue_node_id.encode("utf-8")).hexdigest()[:24]


def attach_tracker_source(
    record: dict[str, object],
    issue: dict[str, object],
    observations: list[dict[str, object]],
    *,
    skill_revision: str,
) -> dict[str, object]:
    """Append explicit tracker evidence without changing authoritative PR role."""
    output = deepcopy(record)
    sources = output.setdefault("sources", [])
    if not isinstance(sources, list):
        raise ValueError("hydrated record sources must be an array")
    sources.append({
        "source_key": _tracker_source_key(issue.get("node_id")),
        "collection_method": COLLECTION_METHOD,
        "tracker": {
            "issue_node_id": issue.get("node_id"),
            "issue_number": issue.get("number"),
            "api_url": issue.get("url"),
            "html_url": issue.get("html_url"),
        },
        "generated_by": {"name": SKILL_NAME, "revision": skill_revision},
        "observations": deepcopy(observations),
    })
    return output


def _curated_content_identity(observation: object) -> Optional[tuple[object, object, object]]:
    """Return the run-independent identity of one tracker content version."""
    if not isinstance(observation, dict):
        return None
    origin_kind = observation.get("origin_kind")
    if origin_kind == "comment" or observation.get("comment_node_id") is not None:
        node_id = observation.get("comment_node_id")
    elif origin_kind == "issue-body" or observation.get("issue_node_id") is not None:
        node_id = observation.get("issue_node_id")
    else:
        return None
    updated_at = observation.get("updated_at")
    body_sha256 = observation.get("body_sha256")
    if not all(isinstance(value, str) and value for value in (node_id, updated_at, body_sha256)):
        return None
    return node_id, updated_at, body_sha256


def _matching_existing_record(
    existing_corpus: Optional[dict[str, object]], incoming_record: dict[str, object]
) -> Optional[dict[str, object]]:
    if not isinstance(existing_corpus, dict) or not isinstance(existing_corpus.get("records"), list):
        return None
    node_id = incoming_record.get("pull_request_node_id")
    if isinstance(node_id, str) and node_id:
        return next((
            record
            for record in existing_corpus["records"]
            if isinstance(record, dict) and record.get("pull_request_node_id") == node_id
        ), None)

    pull_request = incoming_record.get("pull_request")
    incoming_url = pull_request.get("url") if isinstance(pull_request, dict) else None
    if incoming_record.get("identity_status") != "resolved" and isinstance(incoming_url, str):
        matches = []
        for record in existing_corpus["records"]:
            if not isinstance(record, dict) or record.get("identity_status") == "resolved":
                continue
            existing_pull_request = record.get("pull_request")
            existing_url = (
                existing_pull_request.get("url")
                if isinstance(existing_pull_request, dict)
                else None
            )
            if existing_url == incoming_url:
                matches.append(record)
        if len(matches) == 1:
            return matches[0]
    return None


def deduplicate_tracker_observations(
    existing_corpus: Optional[dict[str, object]], incoming_records: list[dict[str, object]]
) -> list[dict[str, object]]:
    """Remove unchanged tracker content before the sibling run-based merge."""
    output = deepcopy(incoming_records)
    seen_by_record_source: dict[tuple[object, object], set[tuple[object, object, object]]] = {}
    for incoming in output:
        node_id = incoming.get("pull_request_node_id")
        pull_request = incoming.get("pull_request")
        pull_request_url = pull_request.get("url") if isinstance(pull_request, dict) else None
        record_identity = (
            ("node", node_id)
            if isinstance(node_id, str) and node_id
            else ("url", pull_request_url)
        )
        existing_record = _matching_existing_record(existing_corpus, incoming)
        incoming_sources = incoming.get("sources")
        if not isinstance(incoming_sources, list):
            continue
        for source in incoming_sources:
            if not isinstance(source, dict):
                continue
            source_key = source.get("source_key")
            if not isinstance(source_key, str) or not source_key.startswith("tracker-issue:"):
                continue
            seen_key = (record_identity, source_key)
            seen = seen_by_record_source.setdefault(seen_key, set())
            if existing_record is not None and not seen:
                existing_sources = existing_record.get("sources")
                if isinstance(existing_sources, list):
                    existing_source = next((
                        value for value in existing_sources
                        if isinstance(value, dict) and value.get("source_key") == source_key
                    ), None)
                    if isinstance(existing_source, dict) and isinstance(existing_source.get("observations"), list):
                        seen.update(
                            identity
                            for identity in map(_curated_content_identity, existing_source["observations"])
                            if identity is not None
                        )
            observations = source.get("observations")
            if not isinstance(observations, list):
                continue
            filtered: list[object] = []
            for observation in observations:
                identity = _curated_content_identity(observation)
                if identity is not None and identity in seen:
                    continue
                filtered.append(deepcopy(observation))
                if identity is not None:
                    seen.add(identity)
            source["observations"] = filtered
    return output


def _hydration_failure_categories(record: dict[str, object]) -> list[str]:
    categories: list[str] = []
    evidence = record.get("evidence_snapshot")
    partial = evidence.get("partial_categories") if isinstance(evidence, dict) else None
    if isinstance(partial, list):
        categories.extend(
            category for category in partial
            if isinstance(category, str) and category and category not in categories
        )
    if record.get("identity_status") != "resolved" and "identity" not in categories:
        categories.append("identity")
    if record.get("hydration_status") != "complete" and not categories:
        categories.append("hydration")
    return categories


def canonicalize_curated_state_history(
    record: dict[str, object], *, captured_at: Optional[str] = None
) -> dict[str, object]:
    """Build authoritative state events only from run-independent PR facts."""
    output = deepcopy(record)
    pull_request = output.get("pull_request")
    if not isinstance(pull_request, dict):
        return output
    state = pull_request.get("normalized_state")
    if state not in {"open", "merged", "closed-unmerged"}:
        failure_categories = _hydration_failure_categories(output)
        if state == "unknown" and failure_categories:
            output["state_history"] = [{
                "state": "unknown",
                "authority": "GitHub access failure",
                "evidence_url": pull_request.get("url"),
                "failure_basis": {
                    "kind": "hydration",
                    "endpoint_categories": failure_categories,
                },
            }]
        return output
    if state == "open":
        observed_at = pull_request.get("updated_at") or pull_request.get("created_at")
    else:
        observed_at = (
            pull_request.get("merged_at")
            or pull_request.get("closed_at")
            or pull_request.get("updated_at")
            or pull_request.get("created_at")
        )
    output["state_history"] = [{
        "state": state,
        "observed_at": observed_at,
        "authority": "GitHub pull request",
        "evidence_url": pull_request.get("url"),
    }]
    return output


def request_fingerprint(
    tracker_repo: str,
    issue_number: int,
    max_prs: int,
    request_budget: int,
    api_version: str,
) -> str:
    payload = {
        "api_version": api_version,
        "issue_number": issue_number,
        "max_prs": max_prs,
        "request_budget": request_budget,
        "tracker_repository": tracker_repo.lower(),
    }
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _base_run_record(
    *,
    run_id: str,
    fingerprint: str,
    tracker_repo: str,
    issue_number: int,
    status: str,
    captured_at: str,
    api_version: str,
    generator: dict[str, object],
    max_prs: int,
    request_budget: int,
    request_count: int = 0,
    request_events: Optional[list[object]] = None,
    started_at: Optional[str] = None,
    client_version: Optional[str] = None,
    preflight: Optional[dict[str, object]] = None,
) -> dict[str, object]:
    """Create the common manifest fields shared by every run outcome."""
    return {
        "run_id": run_id,
        "request_fingerprint": fingerprint,
        "collection_method": COLLECTION_METHOD,
        "tracker": {"repository": tracker_repo, "issue_number": issue_number},
        "collection_status": status,
        "started_at": started_at or captured_at,
        "completed_at": captured_at,
        "checkpoint": False,
        "api_version": api_version,
        "client_version": client_version,
        "skill": deepcopy(generator),
        "max_prs": max_prs,
        "request_budget": request_budget,
        "request_count": request_count,
        "request_events": deepcopy(request_events or []),
        "comment_pages": [],
        "reference_counts": {
            "matched": 0,
            "selected": 0,
            "excluded_by_cap": 0,
            "excluded_examples_or_notices": 0,
        },
        "cap_exclusions": [],
        "reference_exclusions": [],
        "hydration_outcomes": [],
        "warnings": [],
        "failed_scopes": [],
        "preflight": deepcopy(preflight),
    }


def _warnings_for_failed_scopes(
    failed_scopes: list[dict[str, object]], existing: Optional[list[str]] = None
) -> list[str]:
    """Return sanitized, kind-addressable diagnostics for structured gaps."""
    warnings = list(existing or [])
    safe_reasons = {
        "preflight": "GitHub preflight failed",
        "issue": "tracker Issue collection failed",
        "pagination": "comment pagination failed",
        "pagination-link": "comment pagination Link was rejected",
        "comment-order": "comment ordering validation failed",
        "header-container": "unsupported response headers container",
        "reference-identity": "invalid repository identity excluded",
        "tracker-payload": "tracker payload validation failed",
        "hydration": "pull request hydration was incomplete",
        "budget": "request budget was exhausted",
        "processing": "post-request collection processing failed",
    }
    for scope in failed_scopes:
        kind = scope.get("kind")
        if not isinstance(kind, str) or not kind:
            kind = "collection"
        if any(kind in warning for warning in warnings):
            continue
        warnings.append(f"{kind}: {safe_reasons.get(kind, 'collection gap recorded')}")
    return warnings


def validate_existing_manifest(
    document: object, tracker_repo: str, issue_number: int
) -> dict[str, object]:
    if not isinstance(document, dict) or document.get("schema_version") != "2.0.0":
        raise ValueError("existing manifest requires schema_version 2.0.0")
    generator = document.get("generated_by")
    if not isinstance(generator, dict) or generator.get("name") != SKILL_NAME:
        raise ValueError("existing manifest was not generated by collecting-curated-contribution-prs")
    records = document.get("records")
    if not isinstance(records, list) or not all(isinstance(record, dict) for record in records):
        raise ValueError("existing manifest records must be an array of objects")
    identity = {"repository": tracker_repo.lower(), "issue_number": issue_number}
    for record in records:
        if record.get("collection_method") != COLLECTION_METHOD:
            raise ValueError("existing manifest collection method mismatch")
        if record.get("tracker") != identity:
            raise ValueError("existing manifest tracker identity mismatch")
    return document


def _validate_complete_resume_corpus(
    prior: dict[str, object], existing_corpus: dict[str, object]
) -> None:
    """Require every successful prior hydration outcome to have one corpus record."""
    outcomes = prior.get("hydration_outcomes")
    records = existing_corpus.get("records")
    if outcomes is None:
        outcomes = []
    if not isinstance(outcomes, list) or not isinstance(records, list):
        raise ValueError("complete resume requires hydration outcomes and corpus records")
    for outcome in outcomes:
        if not isinstance(outcome, dict) or outcome.get("status") not in {"collected", "partial"}:
            continue
        repository = outcome.get("repository")
        number = outcome.get("number")
        try:
            normalized_repository = normalize_repository(repository)
        except ValueError as error:
            raise ValueError("complete resume hydration identity is invalid") from error
        if not isinstance(number, int) or isinstance(number, bool) or number <= 0:
            raise ValueError("complete resume hydration identity is invalid")
        matches = []
        for record in records:
            if not isinstance(record, dict):
                continue
            record_repository = record.get("repository")
            pull_request = record.get("pull_request")
            full_name = (
                record_repository.get("full_name")
                if isinstance(record_repository, dict)
                else None
            )
            record_number = (
                pull_request.get("number") if isinstance(pull_request, dict) else None
            )
            if (
                isinstance(full_name, str)
                and full_name.lower() == normalized_repository
                and record_number == number
            ):
                matches.append(record)
        if len(matches) != 1:
            raise ValueError("complete resume corpus does not match hydration outcomes")
        expected_node = outcome.get("pull_request_node_id")
        if (
            isinstance(expected_node, str)
            and expected_node
            and matches[0].get("pull_request_node_id") != expected_node
        ):
            raise ValueError("complete resume corpus pull request identity mismatch")


def _manifest_records(
    history: list[object], record: dict[str, object], resume_run_id: Optional[str]
) -> list[object]:
    copied = deepcopy(history)
    if resume_run_id is None:
        copied.append(deepcopy(record))
        return copied
    matches = [index for index, value in enumerate(copied) if isinstance(value, dict) and value.get("run_id") == resume_run_id]
    if len(matches) != 1:
        raise ValueError("resume run ID must identify exactly one manifest run")
    copied[matches[0]] = deepcopy(record)
    return copied


def _json_bytes(document: object) -> bytes:
    return (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _write_temporary(destination: Path, content: bytes) -> Path:
    handle = tempfile.NamedTemporaryFile("wb", dir=destination.parent, delete=False)
    try:
        handle.write(content)
        handle.close()
        return Path(handle.name)
    except BaseException:
        handle.close()
        try:
            Path(handle.name).unlink()
        except OSError:
            pass
        raise


def _restore_destination(destination: Path, previous: Optional[bytes]) -> None:
    if previous is None:
        try:
            destination.unlink()
        except FileNotFoundError:
            pass
        return
    temporary = _write_temporary(destination, previous)
    try:
        os.replace(temporary, destination)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def persist_outputs(
    corpus_path: object,
    corpus: object,
    manifest_path: object,
    manifest: object,
    *,
    replacer: Callable[[object, object], None] = os.replace,
) -> None:
    """Stage both JSON documents and preserve destinations on replacement failure."""
    corpus_destination = Path(corpus_path).resolve()
    manifest_destination = Path(manifest_path).resolve()
    if corpus_destination == manifest_destination:
        raise ValueError("corpus output and manifest output must be different paths")
    corpus_content = _json_bytes(corpus)
    manifest_content = _json_bytes(manifest)
    old_corpus = corpus_destination.read_bytes() if corpus_destination.exists() else None
    old_manifest = manifest_destination.read_bytes() if manifest_destination.exists() else None
    corpus_temporary: Optional[Path] = None
    manifest_temporary: Optional[Path] = None
    staging_complete = False
    try:
        corpus_temporary = _write_temporary(corpus_destination, corpus_content)
        manifest_temporary = _write_temporary(manifest_destination, manifest_content)
        staging_complete = True
        replacer(corpus_temporary, corpus_destination)
        corpus_temporary = None
        replacer(manifest_temporary, manifest_destination)
        manifest_temporary = None
    except BaseException:
        if staging_complete:
            _restore_destination(corpus_destination, old_corpus)
            _restore_destination(manifest_destination, old_manifest)
        raise
    finally:
        for temporary in (corpus_temporary, manifest_temporary):
            if temporary is not None:
                try:
                    temporary.unlink()
                except FileNotFoundError:
                    pass


def _default_hydrator(
    sibling: Any,
    client: Any,
    repository: str,
    number: int,
    captured_at: str,
    repository_metadata_cache: dict[str, dict[str, object]],
    license_cache: dict[str, object],
) -> dict[str, object]:
    normalized_repository = normalize_repository(repository)
    if normalized_repository not in repository_metadata_cache:
        metadata_response = client.get_json("/repos/" + normalized_repository)
        metadata = _response_payload(metadata_response, "repository response")
        if not isinstance(metadata, dict):
            raise ValueError("repository response payload must be an object")
        repository_metadata_cache[normalized_repository] = deepcopy(metadata)
    return sibling.hydrate_pull_request(
        client=client,
        repository=normalized_repository,
        search_hit={
            "number": number,
            "html_url": "https://github.com/{0}/pull/{1}".format(normalized_repository, number),
        },
        repository_metadata=deepcopy(repository_metadata_cache[normalized_repository]),
        license_cache=license_cache,
        captured_at=captured_at,
    )


def _timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def collect(
    client: Any,
    tracker_repo: str,
    issue_number: int,
    *,
    max_prs: int,
    request_budget: int,
    existing_corpus: Optional[dict[str, object]] = None,
    existing_manifest: Optional[dict[str, object]] = None,
    resume_run_id: Optional[str] = None,
    output: Optional[object] = None,
    manifest_output: Optional[object] = None,
    skill_revision: Optional[str] = None,
    timestamp: Optional[str] = None,
    hydrator: Optional[Callable[[Any, str, int, str], dict[str, object]]] = None,
) -> CollectionRun:
    """Collect, normalize, merge, and classify one tracker Issue run."""
    sibling = load_sibling()
    revision = skill_revision or compute_skill_revision()
    generator = {"name": SKILL_NAME, "revision": revision}
    if existing_corpus is not None:
        sibling.merge_corpus(
            existing_corpus,
            {
                "schema_version": "1.0.0",
                "generated_by": deepcopy(generator),
                "records": [],
            },
            source_policy="explicit-only",
        )
    normalized_repo = tracker_repo.lower()
    api_version = getattr(client, "api_version", sibling.API_VERSION)
    fingerprint = request_fingerprint(normalized_repo, issue_number, max_prs, request_budget, api_version)
    captured_at = timestamp or _timestamp()
    prior_records: list[object] = []
    prior: Optional[dict[str, object]] = None
    if existing_manifest is not None:
        validate_existing_manifest(existing_manifest, normalized_repo, issue_number)
        prior_records = deepcopy(existing_manifest["records"])
    if resume_run_id is not None:
        if existing_corpus is None or existing_manifest is None:
            raise ValueError("resume requires existing corpus and existing manifest")
        matches = [
            value for value in prior_records
            if isinstance(value, dict) and value.get("run_id") == resume_run_id
        ]
        if len(matches) != 1:
            raise ValueError("resume run ID must identify exactly one manifest run")
        prior = matches[0]
        if prior.get("request_fingerprint") != fingerprint:
            raise ValueError("resume request fingerprint mismatch")
        if prior.get("collection_status") == "complete":
            _validate_complete_resume_corpus(prior, existing_corpus)
        consumed = prior.get("request_count")
        if not isinstance(consumed, int) or isinstance(consumed, bool) or consumed < 0:
            raise ValueError("resume request count must be a nonnegative integer")
        budget = getattr(client, "budget", None)
        if budget is not None:
            budget.consumed = max(getattr(budget, "consumed", 0), consumed)
        if prior.get("collection_status") == "complete":
            reused = deepcopy(prior)
            reused["checkpoint_reused"] = True
            reused["resumed_at"] = captured_at
            manifest = deepcopy(existing_manifest)
            manifest["records"] = _manifest_records(prior_records, reused, resume_run_id)
            corpus = deepcopy(existing_corpus)
            if output is not None and manifest_output is not None:
                persist_outputs(output, corpus, manifest_output, manifest)
            return CollectionRun(corpus, manifest, 0)

    run_id = resume_run_id or "run-{0}-{1:04d}".format(fingerprint[7:19], len(prior_records) + 1)
    base_corpus = deepcopy(existing_corpus) if existing_corpus is not None else {
        "schema_version": "1.0.0",
        "generated_by": deepcopy(generator),
        "records": [],
    }
    failed_scopes: list[dict[str, object]] = []
    warnings: list[str] = []
    preflight: Optional[dict[str, object]] = None
    try:
        preflight_value = client.global_preflight()
        preflight = deepcopy(preflight_value) if isinstance(preflight_value, dict) else {}
    except Exception as error:
        failed_scopes.append({"kind": "preflight", "reason": str(error)})
        warnings = _warnings_for_failed_scopes(failed_scopes, warnings)
        failed_record = _base_run_record(
            run_id=run_id,
            fingerprint=fingerprint,
            tracker_repo=normalized_repo,
            issue_number=issue_number,
            status="failed",
            captured_at=captured_at,
            api_version=api_version,
            generator=generator,
            max_prs=max_prs,
            request_budget=request_budget,
            request_count=getattr(getattr(client, "budget", None), "consumed", 0),
            request_events=getattr(client, "request_events", []),
        )
        failed_record["failed_scopes"] = failed_scopes
        manifest = {
            "schema_version": "2.0.0",
            "generated_by": deepcopy(generator),
            "records": _manifest_records(prior_records, failed_record, resume_run_id),
        }
        return CollectionRun(base_corpus, manifest, 4)

    try:
        thread = collect_issue_thread(client, normalized_repo, issue_number)
    except Exception as error:
        thread = {"issue": None, "comments": [], "pages": [], "failed_scopes": [{"kind": "issue", "reason": str(error)}]}
    failed_scopes.extend(deepcopy(thread["failed_scopes"]))
    if any(scope.get("kind") == "header-container" for scope in thread["failed_scopes"]):
        warnings.append("header-container: unsupported response headers container")
    inventory = {"matched_count": 0, "selected_count": 0, "excluded_by_cap": 0, "selected": [], "cap_exclusions": [], "reference_exclusions": [], "warnings": [], "failed_scopes": []}
    if isinstance(thread.get("issue"), dict):
        try:
            references = extract_references(thread["issue"], thread["comments"], run_id=run_id)
            inventory = select_references(references, max_prs=max_prs)
            failed_scopes.extend(deepcopy(inventory["failed_scopes"]))
            warnings.extend(inventory["warnings"])
        except ValueError as error:
            failed_scopes.append({"kind": "tracker-payload", "reason": str(error)})

    selected_records: list[dict[str, object]] = []
    hydration_outcomes: list[dict[str, object]] = []
    repository_metadata_cache: dict[str, dict[str, object]] = {}
    license_cache: dict[str, object] = {}
    effective_hydrator = hydrator or (
        lambda active_client, repository, number, observed_at: _default_hydrator(
            sibling,
            active_client,
            repository,
            number,
            observed_at,
            repository_metadata_cache,
            license_cache,
        )
    )
    for selected_index, selected in enumerate(inventory["selected"]):
        repository, number = selected["identity"]
        try:
            hydrated = effective_hydrator(client, repository, number, captured_at)
            observations = [reference["observation"] for reference in selected["references"]]
            prepared = attach_tracker_source(
                canonicalize_curated_state_history(hydrated, captured_at=captured_at),
                thread["issue"],
                observations,
                skill_revision=revision,
            )
            selected_records.append(prepared)
            failure_categories = _hydration_failure_categories(prepared)
            if failure_categories:
                hydration_outcomes.append({
                    "repository": repository,
                    "number": number,
                    "status": "partial",
                    "endpoint_categories": failure_categories,
                })
                failed_scopes.append({
                    "kind": "hydration",
                    "repository": repository,
                    "number": number,
                    "endpoint_categories": failure_categories,
                    "reason": "hydrated record has incomplete identity or evidence",
                })
            else:
                hydration_outcomes.append({"repository": repository, "number": number, "status": "collected"})
        except Exception as error:
            kind = (
                "budget"
                if isinstance(error, sibling.BudgetExhausted)
                else "hydration"
            )
            failed_scopes.append({
                "kind": kind,
                "repository": repository,
                "number": number,
                "reason": str(error),
            })
            hydration_outcomes.append({"repository": repository, "number": number, "status": "failed"})
            if kind == "budget":
                for unvisited in inventory["selected"][selected_index + 1:]:
                    unvisited_repository, unvisited_number = unvisited["identity"]
                    hydration_outcomes.append({
                        "repository": unvisited_repository,
                        "number": unvisited_number,
                        "status": "not-attempted",
                    })
                break

    if selected_records:
        selected_records = deduplicate_tracker_observations(existing_corpus, selected_records)
        incoming = {
            "schema_version": "1.0.0",
            "generated_by": deepcopy(generator),
            "records": selected_records,
        }
        corpus = sibling.merge_corpus(base_corpus if existing_corpus is not None else None, incoming, source_policy="explicit-only")
    else:
        corpus = base_corpus
    warnings = _warnings_for_failed_scopes(failed_scopes, warnings)
    usable_records = bool(selected_records)
    status = "complete" if not failed_scopes else "partial" if usable_records else "failed"
    exit_code = 0 if status == "complete" else 3 if status == "partial" else 4
    record = _base_run_record(
        run_id=run_id,
        fingerprint=fingerprint,
        tracker_repo=normalized_repo,
        issue_number=issue_number,
        status=status,
        captured_at=captured_at,
        api_version=api_version,
        generator=generator,
        max_prs=max_prs,
        request_budget=request_budget,
        request_count=getattr(getattr(client, "budget", None), "consumed", 0),
        request_events=getattr(client, "request_events", []),
        started_at=prior.get("started_at", captured_at) if prior is not None else captured_at,
        client_version=preflight.get("client_version") if isinstance(preflight, dict) else None,
        preflight=preflight,
    )
    record.update({
        "comment_pages": deepcopy(thread["pages"]),
        "reference_counts": {
            "matched": inventory["matched_count"],
            "selected": inventory["selected_count"],
            "excluded_by_cap": inventory["excluded_by_cap"],
            "excluded_examples_or_notices": len(inventory["reference_exclusions"]),
        },
        "cap_exclusions": deepcopy(inventory["cap_exclusions"]),
        "reference_exclusions": deepcopy(inventory["reference_exclusions"]),
        "hydration_outcomes": hydration_outcomes,
        "warnings": warnings,
        "failed_scopes": failed_scopes,
    })
    manifest = {
        "schema_version": "2.0.0",
        "generated_by": deepcopy(generator),
        "records": _manifest_records(prior_records, record, resume_run_id),
    }
    if output is not None and manifest_output is not None and status != "failed":
        persist_outputs(output, corpus, manifest_output, manifest)
    return CollectionRun(corpus, manifest, exit_code)


def main(
    argv: Optional[list[str]] = None,
    *,
    sibling_script: object = SIBLING_SCRIPT,
    client_factory: Optional[Callable[..., Any]] = None,
) -> int:
    effective_argv = list(sys.argv[1:] if argv is None else argv)
    args: Optional[argparse.Namespace] = None
    client: Any = None
    sibling: Any = None
    prior_records: list[object] = []
    try:
        parser = build_parser()
        args = parser.parse_args(effective_argv)
        if args.print_revision:
            if args.command is not None:
                parser.error("--print-revision cannot be combined with a subcommand")
            print(compute_skill_revision())
            return 0
        if args.command is None:
            parser.error("the following arguments are required: command")
        validate_cli_args(args)
        try:
            sibling = load_sibling(sibling_script)
        except FileNotFoundError as error:
            print(
                "error: collecting-recent-closed-prs sibling script not found: "
                + os.fspath(error.args[0]),
                file=sys.stderr,
            )
            return 2
        existing_corpus = None
        existing_manifest = None
        if args.existing_corpus is not None:
            try:
                with open(args.existing_corpus, encoding="utf-8") as handle:
                    existing_corpus = json.load(handle)
                with open(args.existing_manifest, encoding="utf-8") as handle:
                    existing_manifest = json.load(handle)
            except (OSError, json.JSONDecodeError) as error:
                raise ValueError("could not read existing JSON inputs: " + str(error)) from error
            validate_existing_manifest(existing_manifest, args.tracker_repo.lower(), args.issue)
            prior_records = deepcopy(existing_manifest["records"])
        budget = sibling.RequestBudget(args.request_budget)
        factory = client_factory or sibling.GhApiClient
        client = factory(budget=budget)
        run = collect(
            client,
            args.tracker_repo,
            args.issue,
            max_prs=args.max_prs,
            request_budget=args.request_budget,
            existing_corpus=existing_corpus,
            existing_manifest=existing_manifest,
            resume_run_id=args.resume_run_id,
            output=args.output,
            manifest_output=args.manifest,
        )
        if run.exit_code == 4 and args.manifest:
            sibling.atomic_write_json(args.manifest, run.manifest)
        return run.exit_code
    except ValueError as error:
        request_count = getattr(getattr(client, "budget", None), "consumed", 0)
        if args is not None and sibling is not None and isinstance(request_count, int) and request_count > 0:
            captured_at = _timestamp()
            revision = compute_skill_revision()
            generator = {"name": SKILL_NAME, "revision": revision}
            normalized_repo = args.tracker_repo.lower()
            api_version = getattr(client, "api_version", sibling.API_VERSION)
            failed_record = _base_run_record(
                run_id="run-processing-failed",
                fingerprint=request_fingerprint(
                    normalized_repo,
                    args.issue,
                    args.max_prs,
                    args.request_budget,
                    api_version,
                ),
                tracker_repo=normalized_repo,
                issue_number=args.issue,
                status="failed",
                captured_at=captured_at,
                api_version=api_version,
                generator=generator,
                max_prs=args.max_prs,
                request_budget=args.request_budget,
                request_count=request_count,
                request_events=getattr(client, "request_events", []),
            )
            failed_record["failed_scopes"] = [{
                "kind": "processing",
                "reason": "post-request collection processing failed",
            }]
            failed_record["warnings"] = _warnings_for_failed_scopes(
                failed_record["failed_scopes"]
            )
            failed_manifest = {
                "schema_version": "2.0.0",
                "generated_by": deepcopy(generator),
                "records": _manifest_records(
                    prior_records, failed_record, args.resume_run_id
                ),
            }
            try:
                sibling.atomic_write_json(args.manifest, failed_manifest)
            except OSError as persistence_error:
                print("error: output persistence failed: " + str(persistence_error), file=sys.stderr)
                return 4
            print("error: post-request collection processing failed", file=sys.stderr)
            return 4
        print("error: " + str(error), file=sys.stderr)
        return 2
    except OSError as error:
        print("error: output persistence failed: " + str(error), file=sys.stderr)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
