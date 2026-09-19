#!/usr/bin/env python3
"""Build the reading digest that pattern-extraction workers share.

The digest is built mechanically from one validated normalized corpus: no model
and no network. Each PR becomes one section headed `### <key> — <title>`, where
the key is `<repository name>#<number>`, or `<owner>/<name>#<number>` when two
repositories share a name.

When every section fits in --max-bytes, the digest is one file and every worker
reads all of it; work is split by lens, never by repository. Otherwise sections
are interleaved across repositories and packed into shards, so every shard mixes
repositories and the candidate synthesis step recovers cross-shard recurrence.

Writes digest.md (or digest-01.md, ...) and keymap.json under --out and prints a
JSON summary. Exit 0 on success, 2 on invalid input.
"""

import argparse
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from validate_corpus import (  # noqa: E402
    DISCUSSION_CATEGORIES,
    HTML_COMMENT,
    _validate_document,
    own_repository_issues,
)

DEFAULT_MAX_BYTES = 160_000
BODY_LIMIT = 1500
FILE_EXCERPT_LIMIT = 900
FILES_WITH_EXCERPT = 20
COMMIT_LIMIT = 160
DISCUSSION_LIMIT = 700
DISCUSSION_ITEMS = 30
# Cross-reference events, and linked issues outside the PR's repository (the
# collector derives them from cross-references), are left out: authenticated
# snapshots can reach private repositories, and the digest is sent to model services.
TIMELINE_EXCERPT_KINDS = ("closed", "merged", "reopened", "labeled")
TIMELINE_LIMIT = 200
LINKED_ISSUE_LIMIT = 600
LOCKFILES = (
    "package-lock.json",
    "npm-shrinkwrap.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lock",
    "Cargo.lock",
    "Gemfile.lock",
    "composer.lock",
    "poetry.lock",
    "uv.lock",
    "go.sum",
)
PULL_URL = re.compile(r"https://github\.com/([^/\s]+/[^/\s]+)/pull/(\d+)")


class DigestError(ValueError):
    pass


def excerpt(text, limit):
    """Readable excerpt: HTML comments dropped, blank runs collapsed, long text cut."""
    if not isinstance(text, str):
        return ""
    text = HTML_COMMENT.sub("", text).replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if len(text) <= limit:
        return text
    return text[:limit] + " …[+" + str(len(text) - limit) + " chars]"


def _items(value):
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _repository_and_number(record):
    repository = record.get("repository") if isinstance(record.get("repository"), dict) else {}
    pull_request = record.get("pull_request") if isinstance(record.get("pull_request"), dict) else {}
    full_name, number = repository.get("full_name"), pull_request.get("number")
    match = PULL_URL.match(pull_request.get("url") or "")
    if not isinstance(full_name, str) or "/" not in full_name:
        full_name = match.group(1) if match else None
    if not isinstance(number, int) or isinstance(number, bool):
        number = int(match.group(2)) if match else None
    if full_name is None or number is None:
        raise DigestError(
            "record has no repository name and PR number: " + str(pull_request.get("url"))
        )
    return full_name, number


def section_keys(records):
    """Return one stable key per record, in record order."""
    located = [_repository_and_number(record) for record in records]
    owners_by_name = {}
    for full_name, _ in located:
        owners_by_name.setdefault(full_name.split("/")[-1].lower(), set()).add(full_name.lower())
    keys = []
    for full_name, number in located:
        name = full_name.split("/")[-1]
        prefix = name if len(owners_by_name[name.lower()]) == 1 else full_name
        keys.append(prefix + "#" + str(number))
    duplicates = sorted({key for key in keys if keys.count(key) > 1})
    if duplicates:
        raise DigestError("two records share a digest key: " + ", ".join(duplicates))
    return keys


def records_by_key(corpus):
    records = corpus["records"]
    return dict(zip(section_keys(records), records))


def _date(value):
    return value[:10] if isinstance(value, str) else "-"


def _author(value):
    if isinstance(value, dict):
        login = value.get("login") or "unknown"
        role = value.get("normalized_role") or value.get("association")
        return login + (" (" + role + ")" if role else "")
    return str(value or "unknown")


def _indent(text, prefix="  "):
    """Indent every line of free text so only section headers start a line with `### `."""
    return prefix + text.replace("\n", "\n" + prefix)


def render_section(key, record):
    pull_request = record.get("pull_request") if isinstance(record.get("pull_request"), dict) else {}
    snapshot = record.get("evidence_snapshot") if isinstance(record.get("evidence_snapshot"), dict) else {}
    full_name, _ = _repository_and_number(record)
    lines = [
        "### " + key + " — " + excerpt(pull_request.get("title"), 300).replace("\n", " "),
        "url: " + str(pull_request.get("url")),
        "repository: " + full_name + " · pr_id: " + str(record.get("pr_id")),
        "state: "
        + str(pull_request.get("normalized_state"))
        + " · author: "
        + _author(record.get("author"))
        + " · created "
        + _date(pull_request.get("created_at"))
        + " · closed "
        + _date(pull_request.get("closed_at"))
        + " · files "
        + str(pull_request.get("changed_files_count"))
        + " · commits "
        + str(pull_request.get("commits_count"))
        + " · labels "
        + json.dumps(pull_request.get("labels") or [], ensure_ascii=False),
        "",
        "body:",
        _indent(excerpt(snapshot.get("body_excerpt"), BODY_LIMIT) or "(empty)"),
        "",
        "changed_files:",
    ]
    shown = 0
    for changed in _items(snapshot.get("changed_files")):
        path = str(changed.get("path"))
        lines.append(
            "- " + path + " (" + str(changed.get("status")) + " +"
            + str(changed.get("additions")) + "/-" + str(changed.get("deletions")) + ")"
        )
        if shown < FILES_WITH_EXCERPT and not path.endswith(LOCKFILES):
            text = excerpt(changed.get("change_excerpt"), FILE_EXCERPT_LIMIT)
            if text:
                lines.append(_indent(text))
                shown += 1
    lines.append("commits:")
    for commit in _items(snapshot.get("commits")):
        message = commit.get("message") if isinstance(commit.get("message"), str) else ""
        lines.append("- " + excerpt(message.split("\n", 1)[0], COMMIT_LIMIT))
    for category in DISCUSSION_CATEGORIES[:3]:
        items = _items(snapshot.get(category))
        lines.append(category + ":")
        for item in items[:DISCUSSION_ITEMS]:
            marker = str(item.get("author"))
            if category == "reviews":
                marker += " · " + str(item.get("state"))
            if category == "review_comments":
                marker += " @ " + str(item.get("path"))
            text = excerpt(item.get("excerpt"), DISCUSSION_LIMIT)
            lines.append(
                "- [" + marker + "] " + _indent(text, "    ").lstrip() + "  <" + str(item.get("html_url")) + ">"
            )
        if len(items) > DISCUSSION_ITEMS:
            lines.append("- …(+" + str(len(items) - DISCUSSION_ITEMS) + " more)")
    events = _items(snapshot.get("timeline_events"))
    counts = {}
    for event in events:
        counts[str(event.get("kind"))] = counts.get(str(event.get("kind")), 0) + 1
    lines.append("timeline: " + ", ".join(kind + "×" + str(count) for kind, count in counts.items()))
    for event in events:
        text = excerpt(event.get("excerpt"), TIMELINE_LIMIT)
        if event.get("kind") in TIMELINE_EXCERPT_KINDS and text:
            lines.append(
                "- " + str(event.get("kind")) + " [" + str(event.get("author")) + "] "
                + _indent(text, "    ").lstrip()
            )
    issues = own_repository_issues(record)
    if issues:
        lines.append("linked_issues:")
        for issue in issues:
            title = excerpt(issue.get("title"), 300).replace("\n", " ")
            lines.append("- #" + str(issue.get("number")) + " " + title)
            body = excerpt(issue.get("body_excerpt"), LINKED_ISSUE_LIMIT)
            if body:
                lines.append(_indent(body))
    partial = snapshot.get("partial_categories")
    if partial:
        lines.append("partial_categories: " + json.dumps(partial, ensure_ascii=False))
    return "\n".join(lines)


def _interleave_by_repository(keys, records):
    queues = {}
    for key, record in zip(keys, records):
        queues.setdefault(_repository_and_number(record)[0], []).append(key)
    order = []
    while any(queues.values()):
        for queue in queues.values():
            if queue:
                order.append(queue.pop(0))
    return order


def plan_shards(keys, records, sections, max_bytes):
    """Return shard key lists. One shard when everything fits in max_bytes."""
    size = {key: len(sections[key].encode("utf-8")) + 2 for key in keys}
    too_large = [key for key in keys if size[key] > max_bytes]
    if too_large:
        raise DigestError(
            "a PR section exceeds --max-bytes " + str(max_bytes) + ": " + ", ".join(too_large)
        )
    if sum(size.values()) <= max_bytes:
        return [list(keys)]
    shards, current, used = [], [], 0
    for key in _interleave_by_repository(keys, records):
        if current and used + size[key] > max_bytes:
            shards.append(current)
            current, used = [], 0
        current.append(key)
        used += size[key]
    shards.append(current)
    return shards


def build(corpus_path, out_dir, max_bytes=DEFAULT_MAX_BYTES):
    try:
        corpus = json.loads(Path(corpus_path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DigestError("corpus could not be read as JSON: " + str(error))
    errors = _validate_document(corpus, "current")
    if errors:
        raise DigestError("; ".join(errors))
    records = corpus["records"]
    if not records:
        raise DigestError("corpus has no records to digest")
    keys = section_keys(records)
    sections = {key: render_section(key, record) for key, record in zip(keys, records)}
    shards = plan_shards(keys, records, sections, max_bytes)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for stale in out_dir.glob("digest*.md"):
        stale.unlink()
    names = ["digest.md"] if len(shards) == 1 else [
        "digest-" + str(index).zfill(2) + ".md" for index in range(1, len(shards) + 1)
    ]
    shard_of = {}
    summary_shards = []
    for name, shard in zip(names, shards):
        text = "\n\n".join(sections[key] for key in shard) + "\n"
        (out_dir / name).write_text(text, encoding="utf-8")
        summary_shards.append({"file": name, "bytes": len(text.encode("utf-8")), "keys": shard})
        for key in shard:
            shard_of[key] = name
    keymap = {
        "corpus": str(Path(corpus_path).resolve()),
        "max_bytes": max_bytes,
        "section_regex": "^### (\\S+) — ",
        "shards": names,
        "sections": {},
    }
    for key, record in zip(keys, records):
        pull_request = record.get("pull_request") if isinstance(record.get("pull_request"), dict) else {}
        keymap["sections"][key] = {
            "pr_id": record.get("pr_id"),
            "record_key": record.get("record_key"),
            "url": pull_request.get("url"),
            "repository": _repository_and_number(record)[0],
            "state": pull_request.get("normalized_state"),
            "title": pull_request.get("title"),
            "shard": shard_of[key],
        }
    (out_dir / "keymap.json").write_text(
        json.dumps(keymap, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    return {
        "records": len(records),
        "repositories": len({section["repository"] for section in keymap["sections"].values()}),
        "bytes": sum(shard["bytes"] for shard in summary_shards),
        "max_bytes": max_bytes,
        "shards": summary_shards,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("current", help="validated normalized corpus JSON")
    parser.add_argument("--out", required=True, help="directory for digest files and keymap.json")
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=DEFAULT_MAX_BYTES,
        help="largest digest one worker reads (UTF-8 bytes); above it the digest is sharded",
    )
    args = parser.parse_args(argv)
    if args.max_bytes <= 0:
        parser.error("--max-bytes must be positive")
    try:
        summary = build(args.current, args.out, args.max_bytes)
    except DigestError as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
