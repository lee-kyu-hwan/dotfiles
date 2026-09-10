"""Finite, result-first supervision for one already-assembled Codex argv."""

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import uuid


ACTIVITY_STALL_SECONDS = 600
ACTIVITY_STALL_MIN_SECONDS = 480
ACTIVITY_STALL_MAX_SECONDS = 600
EXIT_COLLECT_WAIT_SECONDS = 5
ABORT_GRACE_SECONDS = 60
REAP_GRACE_SECONDS = 60
# Five minutes gives a residual process its normal 60-second grace without
# delaying the next quality-goal stage indefinitely.
REAP_WAIT_CAP_SECONDS = 300
WATCHDOG_RESTART_BUDGET = 1


@dataclass(frozen=True)
class WatchdogSettings:
    start_deadline_seconds: float = 60
    activity_stall_seconds: float = ACTIVITY_STALL_SECONDS
    hard_timeout_seconds: float = 900
    poll_interval_seconds: float = 1
    exit_collect_wait_seconds: float = EXIT_COLLECT_WAIT_SECONDS
    abort_grace_seconds: float = ABORT_GRACE_SECONDS
    reap_grace_seconds: float = REAP_GRACE_SECONDS
    reap_wait_cap_seconds: float = REAP_WAIT_CAP_SECONDS
    preflight_grace_seconds: float = 5


@dataclass
class ExecutionOutcome:
    status: str
    record: dict
    process: subprocess.Popen | None = None


class BaseRevisionError(ValueError):
    """The requested preservation baseline cannot be used by this checkout."""


def _utcnow():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _atomic_json(path, value):
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _stream_size(path):
    try:
        return path.stat().st_size
    except FileNotFoundError:
        return 0


def _pid_is_live(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


def _owned_group(process, pgid):
    """Verify only the group created for this Popen instance, never by name."""
    if process.pid != pgid or not _pid_is_live(process.pid):
        return False
    try:
        return os.getpgid(process.pid) == pgid
    except ProcessLookupError:
        # The process exited after kill(pid, 0); ownership cannot be proven.
        return False


def _wait_for_exit(process, seconds, *, monotonic_clock=time.monotonic, sleep=time.sleep):
    deadline = monotonic_clock() + seconds
    while monotonic_clock() < deadline:
        code = process.poll()
        if code is not None:
            return code
        sleep(min(0.01, max(0, deadline - monotonic_clock())))
    return process.poll()


def _signal_owned_group(process, pgid, grace_seconds, cap_seconds, *, monotonic_clock=time.monotonic, sleep=time.sleep):
    """Signal one verified group while bounding both grace and post-kill waits."""
    result = {"attempted": False, "signals": [], "outcome": "not_needed", "candidate": True, "pgid": pgid}
    if not _owned_group(process, pgid):
        result["outcome"] = "ownership_refused"
        return result, [process.pid] if _pid_is_live(process.pid) else []
    result["attempted"] = True
    try:
        os.killpg(pgid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        result["outcome"] = "signal_failed"
        return result, [process.pid] if _pid_is_live(process.pid) else []
    result["signals"].append("SIGTERM")
    started = monotonic_clock()
    cap_deadline = started + max(0, cap_seconds)
    grace_deadline = min(started + max(0, grace_seconds), cap_deadline)
    while monotonic_clock() < grace_deadline:
        if process.poll() is not None:
            result["outcome"] = "terminated"
            return result, []
        sleep(min(0.01, max(0, grace_deadline - monotonic_clock())))
    if process.poll() is not None:
        result["outcome"] = "terminated"
        return result, []
    if monotonic_clock() >= cap_deadline:
        result["outcome"] = "cap_exceeded"
        return result, [process.pid]
    try:
        os.killpg(pgid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        result["outcome"] = "signal_failed"
        return result, [process.pid] if _pid_is_live(process.pid) else []
    result["signals"].append("SIGKILL")
    _wait_for_exit(process, max(0, cap_deadline - monotonic_clock()), monotonic_clock=monotonic_clock, sleep=sleep)
    result["outcome"] = "killed" if process.poll() is not None else "cap_exceeded"
    return result, [] if process.poll() is not None else [process.pid]


def _capture_command(argv, cwd):
    completed = subprocess.run(argv, cwd=cwd, capture_output=True, check=False)
    if completed.returncode:
        raise subprocess.CalledProcessError(
            completed.returncode, argv, output=completed.stdout, stderr=completed.stderr,
        )
    return completed.stdout


def _resolve_base_revision(project_root, base_revision):
    """Resolve the diff baseline before launching a child that might need aborting."""
    root = Path(project_root)
    command = ["git", "rev-parse", "--verify", str(base_revision)]
    try:
        completed = subprocess.run(command, cwd=root, capture_output=True, check=False)
    except OSError as error:
        raise BaseRevisionError(
            f"invalid --base-revision {base_revision!r}: cannot inspect {root}: {error}"
        ) from error
    if completed.returncode or not completed.stdout.strip():
        detail = completed.stderr.decode("utf-8", "replace").strip()
        raise BaseRevisionError(
            f"invalid --base-revision {base_revision!r} for project root {root}: {detail or 'unresolvable revision'}"
        )
    return completed.stdout.decode("utf-8", "strict").strip()


def preserve_bundle(*, execution_dir, project_root, base_revision, events_path, stderr_path):
    """Create the abort-only evidence bundle before any process signal."""
    root = Path(project_root)
    if not root.is_dir() or subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"], cwd=root, capture_output=True, check=False
    ).returncode:
        raise OSError(f"project root is not a git checkout: {root}")
    bundle = execution_dir / "preservation"
    bundle.mkdir(exist_ok=False)
    (bundle / "tracked.patch").write_bytes(_capture_command(["git", "diff", "--binary"], root))
    (bundle / "staged.patch").write_bytes(_capture_command(["git", "diff", "--binary", "--cached", base_revision], root))
    listed = _capture_command(["git", "ls-files", "--others", "--exclude-standard", "-z"], root)
    (bundle / "untracked.manifest.nul").write_bytes(listed)
    archive = bundle / "untracked-content"
    archive.mkdir()
    members = []
    for encoded_path in filter(None, listed.split(b"\0")):
        relative = Path(os.fsdecode(encoded_path))
        source = root / relative
        if not source.is_file():
            raise OSError(f"untracked file unavailable for preservation: {relative}")
        destination = archive / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        data = source.read_bytes()
        destination.write_bytes(data)
        members.append({"path": relative.as_posix(), "kind": "untracked", "sha256": hashlib.sha256(data).hexdigest()})
    captured = bundle / "captured-streams"
    captured.mkdir()
    for source in (events_path, stderr_path):
        destination = captured / source.name
        destination.write_bytes(source.read_bytes() if source.exists() else b"")
        members.append({"path": destination.relative_to(bundle).as_posix(), "kind": "stream", "sha256": hashlib.sha256(destination.read_bytes()).hexdigest()})
    metadata = {"base_revision": base_revision, "members": sorted(members, key=lambda member: member["path"])}
    encoded = json.dumps(metadata, sort_keys=True, separators=(",", ":")).encode("utf-8")
    (bundle / "metadata.json").write_bytes(encoded + b"\n")
    (bundle / "fingerprint.txt").write_text(hashlib.sha256(encoded).hexdigest() + "\n", encoding="ascii")
    return bundle


def _result_validation(path, validator):
    if not path.exists():
        return "not_run", False
    try:
        valid = bool(validator(path)) if validator else bool(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError, json.JSONDecodeError):
        valid = False
    return ("passed" if valid else "mismatch"), valid


def apply_restart_budget(record, initial_budget=WATCHDOG_RESTART_BUDGET):
    """The parent-side, deterministic budget decision; the wrapper never restarts."""
    initial = max(0, int(initial_budget))
    candidate = bool(record.get("restart_candidate"))
    consumed = 1 if candidate else 0
    remaining = max(0, initial - consumed)
    decision = {
        "retry_budget_initial": initial,
        "retry_budget_remaining": remaining,
        "retry_consumed": consumed,
        "restart_attempted": candidate and remaining > 0,
        "restart_stopped": candidate and remaining == 0,
    }
    record.update(decision)
    if "report_payload" in record:
        record["report_payload"].update(decision)
    record_path = record.get("execution_record_path")
    if record_path:
        _atomic_json(Path(record_path), record)
    return decision


def run_execution(
    *, child_argv, execution_dir, project_root, base_revision, result_path,
    events_path, stderr_path, stdin_path=None, validate_result=None, settings=WatchdogSettings(),
    monotonic_clock=time.monotonic, sleep=time.sleep, register_process=None,
):
    """Run one child argv and return its record without deciding a restart."""
    project_root = Path(project_root)
    base_revision = _resolve_base_revision(project_root, base_revision)
    execution_dir = Path(execution_dir)
    execution_dir.mkdir(parents=True, exist_ok=True)
    events_path, stderr_path = Path(events_path), Path(stderr_path)
    events_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.parent.mkdir(parents=True, exist_ok=True)
    events_path.touch(exist_ok=True)
    stderr_path.touch(exist_ok=True)
    result_path = Path(result_path) if result_path else None
    started_at = _utcnow()
    started = monotonic_clock()
    with events_path.open("wb") as events, stderr_path.open("wb") as stderr:
        stdin = Path(stdin_path).open("rb") if stdin_path else None
        try:
            process = subprocess.Popen(
                child_argv, cwd=execution_dir, stdin=stdin, stdout=events, stderr=stderr, start_new_session=True,
            )
        finally:
            if stdin is not None:
                stdin.close()
    if register_process is not None:
        register_process(process)
    pgid = process.pid
    record = {
        "execution_id": execution_dir.name or uuid.uuid4().hex,
        "execution_dir": str(execution_dir), "argv": list(child_argv), "pid": process.pid, "pgid": pgid,
        "execution_record_path": str(execution_dir / "execution-record.json"),
        "started_at": started_at, "ended_at": None, "elapsed_s": None, "child_exit_code": "unknown",
        "result_exists": False, "result_schema_validation": "not_run", "started": False,
        "watchdog_reason": None, "signals": [], "preservation_bundle": None, "preservation_status": "not_needed",
        "abort": {"attempted": False, "signals": [], "outcome": "not_needed", "candidate": False, "pgid": None},
        "reap": {"attempted": False, "signals": [], "outcome": "not_needed", "candidate": False, "pgid": None},
        "preflight_termination": {"attempted": False, "signals": [], "outcome": "not_needed", "candidate": False, "pgid": None},
        "residual_pids": [], "restart_candidate": False, "restart_reason": None,
        "retry_budget_initial": None, "retry_budget_remaining": None, "retry_consumed": 0,
        "restart_attempted": False, "restart_stopped": False,
        "poll_order": ["result", "pid", "activity"],
        "ownership": {"recorded_pid": process.pid, "recorded_pgid": pgid},
    }
    prior_sizes = (_stream_size(events_path), _stream_size(stderr_path))
    last_activity = started
    status = "failed"
    while True:
        now = monotonic_clock()
        # Result -> recorded pid -> stream activity is intentionally fixed.
        if result_path and result_path.exists():
            # A result found at the final abort recheck wins over a stale timer.
            record["watchdog_reason"] = None
            record["result_exists"] = True
            code = _wait_for_exit(
                process, settings.exit_collect_wait_seconds, monotonic_clock=monotonic_clock, sleep=sleep,
            )
            record["child_exit_code"] = code if code is not None else "unknown"
            validation, valid = _result_validation(result_path, validate_result)
            record["result_schema_validation"] = validation
            if valid and (code == 0 or code is None):
                status = "completed"
                if _pid_is_live(process.pid):
                    reap, residual = _signal_owned_group(
                        process, pgid, settings.reap_grace_seconds, settings.reap_wait_cap_seconds,
                        monotonic_clock=monotonic_clock, sleep=sleep,
                    )
                    record["reap"], record["residual_pids"] = reap, residual
                    record["signals"].extend(reap["signals"])
                break
            record["watchdog_reason"] = "result_unaccepted"
            record["preservation_status"] = "not_created_no_abort"
            record["restart_candidate"] = True
            record["restart_reason"] = "result_unaccepted"
            break
        code = process.poll()
        if code is not None:
            record["child_exit_code"] = code
            if result_path is None:
                has_activity = bool(_stream_size(events_path) or _stream_size(stderr_path))
                has_reply = bool(_stream_size(events_path))
                record["started"] = has_activity
                status = "completed" if code == 0 and has_reply else "failed"
                record["watchdog_reason"] = None if status == "completed" else "preflight_failed"
                break
            record["watchdog_reason"] = "child_exited_no_result"
            record["restart_candidate"] = bool(result_path)
            record["restart_reason"] = record["watchdog_reason"] if result_path else None
            break
        current_sizes = (_stream_size(events_path), _stream_size(stderr_path))
        activity = current_sizes != prior_sizes
        prior_sizes = current_sizes
        if activity:
            last_activity = now
            record["started"] = True
        if not record["started"] and now - started >= settings.start_deadline_seconds:
            record["watchdog_reason"] = "start_deadline"
        elif record["started"] and now - last_activity >= settings.activity_stall_seconds:
            record["watchdog_reason"] = "activity_stall"
        elif now - started >= settings.hard_timeout_seconds:
            record["watchdog_reason"] = "hard_timeout"
        if record["watchdog_reason"]:
            if result_path is None:
                preflight, residual = _signal_owned_group(
                    process, pgid, settings.preflight_grace_seconds,
                    settings.preflight_grace_seconds + .2,
                    monotonic_clock=monotonic_clock, sleep=sleep,
                )
                preflight["candidate"] = True
                record["preflight_termination"], record["residual_pids"] = preflight, residual
                record["signals"].extend(preflight["signals"])
                status = "failed"
                break
            # A final result check wins the race with an abort decision.
            if result_path and result_path.exists():
                continue
            try:
                bundle = preserve_bundle(execution_dir=execution_dir, project_root=project_root, base_revision=base_revision, events_path=events_path, stderr_path=stderr_path)
                record["preservation_bundle"] = str(bundle)
                record["preservation_status"] = "created"
            except (OSError, subprocess.SubprocessError):
                record["watchdog_reason"] = "preservation_failed"
                record["preservation_status"] = "failed"
                break
            abort, residual = _signal_owned_group(
                process, pgid, settings.abort_grace_seconds, settings.abort_grace_seconds + 0.2,
                monotonic_clock=monotonic_clock, sleep=sleep,
            )
            abort["candidate"] = True
            record["abort"], record["residual_pids"] = abort, residual
            record["signals"].extend(abort["signals"])
            record["restart_candidate"] = True
            record["restart_reason"] = record["watchdog_reason"]
            break
        sleep(settings.poll_interval_seconds)
    record["ended_at"] = _utcnow()
    record["elapsed_s"] = round(monotonic_clock() - started, 6)
    record["report_payload"] = {
        key: record[key] for key in (
            "execution_id", "pid", "pgid", "started_at", "ended_at", "elapsed_s", "child_exit_code",
            "result_exists", "result_schema_validation", "started", "watchdog_reason", "signals",
            "preservation_bundle", "preservation_status", "abort", "reap", "preflight_termination", "residual_pids", "retry_budget_initial",
            "retry_budget_remaining", "retry_consumed", "restart_attempted", "restart_stopped",
        )
    }
    _atomic_json(Path(record["execution_record_path"]), record)
    return ExecutionOutcome(status=status, record=record, process=process)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--base-revision", required=True)
    parser.add_argument("--execution-dir", required=True)
    parser.add_argument("--events-path", required=True)
    parser.add_argument("--stderr-path", required=True)
    parser.add_argument("--result-path")
    parser.add_argument("--stdin-path")
    parser.add_argument("child_argv", nargs=argparse.REMAINDER)
    arguments = parser.parse_args(argv)
    child_argv = arguments.child_argv[1:] if arguments.child_argv[:1] == ["--"] else arguments.child_argv
    if not child_argv:
        parser.error("child argv after -- is required")
    try:
        outcome = run_execution(
            child_argv=child_argv, execution_dir=arguments.execution_dir, project_root=arguments.project_root,
            base_revision=arguments.base_revision, result_path=arguments.result_path, events_path=arguments.events_path,
            stderr_path=arguments.stderr_path, stdin_path=arguments.stdin_path,
        )
    except BaseRevisionError as error:
        parser.exit(2, f"watchdog initialization failed: {error}\n")
    print(json.dumps(outcome.record, ensure_ascii=False))
    return 0 if outcome.status == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
