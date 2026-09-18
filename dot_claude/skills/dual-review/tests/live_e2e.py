#!/usr/bin/env python3
"""Opt-in, read-only landing-noindex end-to-end verification helper."""
import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys


PRODUCERS = (
    "pr-review-toolkit:code-reviewer",
    "pr-test-analyzer",
    "comment-analyzer",
    "silent-failure-hunter",
    "type-design-analyzer",
    "codex",
)


class E2EFailure(RuntimeError):
    pass


def require(condition, message):
    if not condition:
        raise E2EFailure(message)


def git(repository, *arguments):
    return subprocess.check_output(["git", *arguments], cwd=repository)


def file_digests(root):
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def write_json(path, value):
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8"
    )


def parse_options(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--logical-base", required=True)
    parser.add_argument("--expected-branch", required=True)
    parser.add_argument("--expected-files", required=True, type=int)
    parser.add_argument("--expected-diff-bytes", required=True, type=int)
    parser.add_argument("--preserve-run", required=True)
    parser.add_argument("--review-state-script", required=True)
    parser.add_argument("--evidence-dir", required=True)
    return parser.parse_args(argv)


def collect_preconditions(options):
    repository = pathlib.Path(options.repository).resolve()
    state_root = repository / ".claude/dual-review-state"
    preserve_run = state_root / options.preserve_run
    branch = git(repository, "branch", "--show-current").decode().strip()
    before_status = git(repository, "status", "--porcelain")
    changed_files = git(
        repository, "diff", "--name-only", f"{options.logical_base}...HEAD"
    ).decode().splitlines()
    diff = git(repository, "diff", "--unified=0", f"{options.logical_base}...HEAD")
    # The target base passed to the product is the exact `git merge-base` result.
    base_sha = git(repository, "merge-base", options.logical_base, "HEAD").strip()
    before_head = git(repository, "rev-parse", "HEAD").strip()
    prefix = hashlib.sha256(base_sha + b"\0" + before_head).hexdigest()[:16]
    run_pattern = re.compile(re.escape(prefix) + r"-(\d{6})$")
    existing_numbers = [
        int(match.group(1))
        for path in state_root.iterdir()
        if path.is_dir() and (match := run_pattern.fullmatch(path.name))
    ] if state_root.is_dir() else []
    next_execution = max(existing_numbers, default=0) + 1
    expected_run_id = f"{prefix}-{next_execution:06d}"
    preserved_digests = file_digests(preserve_run) if preserve_run.is_dir() else None
    return {
        "repository": str(repository),
        "branch": branch,
        "before_status_hex": before_status.hex(),
        "changed_files": changed_files,
        "diff_bytes": len(diff),
        "base_sha": base_sha.decode(),
        "before_head": before_head.decode(),
        "prefix": prefix,
        "existing_max": max(existing_numbers, default=0),
        "next_execution": next_execution,
        "expected_run_id": expected_run_id,
        "preserve_run": str(preserve_run),
        "preserved_digests": preserved_digests,
    }, before_head, before_status


def validate_preconditions(options, pre):
    mismatches = []
    if pre["branch"] != options.expected_branch:
        mismatches.append(f"branch={pre['branch']!r}")
    if bytes.fromhex(pre["before_status_hex"]):
        mismatches.append("porcelain status is not clean")
    if len(pre["changed_files"]) != options.expected_files:
        mismatches.append(f"files={len(pre['changed_files'])}")
    if pre["diff_bytes"] != options.expected_diff_bytes:
        mismatches.append(f"diff_bytes={pre['diff_bytes']}")
    if pre["preserved_digests"] is None:
        mismatches.append("preserve_run does not exist")
    require(not mismatches, "precondition mismatch; review was not started: " + "; ".join(mismatches))


def validate_events(run_dir):
    events = json.loads((run_dir / "events.json").read_text(encoding="utf-8"))
    starts = {producer: events.index(f"started:{producer}") for producer in PRODUCERS}
    reads = {producer: events.index(f"read:{producer}") for producer in PRODUCERS}
    require(max(starts.values()) < min(reads.values()), "six-producer start-before-read failed")
    return events


def validate_producers(run_dir):
    claude = json.loads((run_dir / "raw-claude.json").read_text(encoding="utf-8"))
    codex = json.loads((run_dir / "raw-codex.json").read_text(encoding="utf-8"))
    records = claude["raw"] + codex["raw"]
    require(len(records) == 6, "expected six producer raw records")
    for record in records:
        require(record.get("valid") is True, f"invalid producer: {record.get('producer')}")
        findings = (record.get("payload") or {}).get("findings")
        require(isinstance(findings, list), f"missing structured findings: {record.get('producer')}")
        if record.get("producer") != "codex" and not findings:
            require(
                record.get("explicit_no_findings") is True,
                f"Claude producer lacked explicit_no_findings: {record.get('producer')}",
            )
    return records


def validate_phase(run_dir, result):
    provenance = json.loads((run_dir / "provenance.json").read_text(encoding="utf-8"))
    critique_statuses = provenance.get("critique_statuses", [])
    successful_directions = {
        item.get("source") for item in critique_statuses if item.get("status") == "ok"
    }
    require({"claude", "codex"}.issubset(successful_directions), "both critique directions must succeed")
    require(result.get("cross_critique_calls", 0) >= 2, "cross_critique_calls must cover both directions")
    require(result.get("synthesis_calls") == 1, "synthesis_calls must equal one")
    require(provenance.get("synthesis_status", {}).get("status") == "ok", "synthesis phase failed")
    require((run_dir / "report.md").is_file(), "report.md is missing")
    return provenance


def run(options):
    repository = pathlib.Path(options.repository).resolve()
    evidence_dir = pathlib.Path(options.evidence_dir).resolve()
    evidence_dir.mkdir(parents=True, exist_ok=True)
    pre, before_head, before_status = collect_preconditions(options)
    write_json(evidence_dir / "live-e2e-pre.json", pre)
    validate_preconditions(options, pre)

    command = [
        sys.executable,
        str(pathlib.Path(options.review_state_script).resolve()),
        "--execution-number",
        str(pre["next_execution"]),
        "--base",
        pre["base_sha"],
        "--rounds",
        "2",
    ]
    completed = subprocess.run(
        command, cwd=repository, stdin=subprocess.DEVNULL, capture_output=True, text=True
    )
    (evidence_dir / "live-e2e.stdout.txt").write_text(completed.stdout, encoding="utf-8")
    (evidence_dir / "live-e2e.stderr.txt").write_text(completed.stderr, encoding="utf-8")
    write_json(evidence_dir / "live-e2e-command.json", command)

    after_head = git(repository, "rev-parse", "HEAD").strip()
    after_status = git(repository, "status", "--porcelain")
    preserve_run = pathlib.Path(pre["preserve_run"])
    preserved_after = file_digests(preserve_run) if preserve_run.is_dir() else None
    post = {
        "exit_code": completed.returncode,
        "after_head": after_head.decode(),
        "after_status_hex": after_status.hex(),
        "preserved_digests": preserved_after,
    }
    write_json(evidence_dir / "live-e2e-post.json", post)
    require(before_head == after_head, "product HEAD changed")
    require(before_status == after_status, "product porcelain changed")
    require(pre["preserved_digests"] == preserved_after, "preserve-run files changed")
    require(completed.returncode == 0, f"review_state.py exited {completed.returncode}")

    output_lines = [line for line in completed.stdout.splitlines() if line.strip()]
    require(output_lines, "review_state.py did not emit a result")
    result = json.loads(output_lines[-1])
    require(result.get("run_id") == pre["expected_run_id"], "unexpected next run ID")
    run_dir = repository / ".claude/dual-review-state" / pre["expected_run_id"]
    require(run_dir.is_dir(), "expected run directory is missing")
    events = validate_events(run_dir)
    producers = validate_producers(run_dir)
    provenance = validate_phase(run_dir, result)
    summary = {
        "run_id": pre["expected_run_id"],
        "events": events,
        "producer_count": len(producers),
        "termination_reason": result.get("termination_reason"),
        "cross_critique_calls": result.get("cross_critique_calls"),
        "synthesis_calls": result.get("synthesis_calls"),
        "synthesis_status": provenance.get("synthesis_status"),
    }
    write_json(evidence_dir / "live-e2e-summary.json", summary)
    return summary


def main(argv=None):
    try:
        summary = run(parse_options(argv))
    except (E2EFailure, OSError, subprocess.SubprocessError, ValueError, json.JSONDecodeError) as exc:
        print(f"live E2E failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
