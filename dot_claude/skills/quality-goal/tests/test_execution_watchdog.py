"""Behavioral coverage for the per-execution Codex watchdog wrapper."""

import json
import hashlib
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import unittest
import uuid
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import execution_watchdog
from execution_watchdog import (
    ABORT_GRACE_SECONDS,
    ACTIVITY_STALL_SECONDS,
    EXIT_COLLECT_WAIT_SECONDS,
    REAP_GRACE_SECONDS,
    REAP_WAIT_CAP_SECONDS,
    WatchdogSettings,
    apply_restart_budget,
    run_execution,
)


PYTHON = sys.executable
SKILL_DIRECTORY = Path(__file__).resolve().parents[1]
SKILL_BYTES_AT_SUITE_START = (SKILL_DIRECTORY / "SKILL.md").read_bytes()
TEST_STATE_ROOT = Path("/private/tmp") / ".claude" / "quality-state"


def tearDownModule():
    """Prove this suite leaves no test state or fixture writes in the skill tree."""
    directory_residue = subprocess.run(
        [
            "find", str(SKILL_DIRECTORY), "-type", "d", "(", "-name", ".claude",
            "-o", "-name", ".watchdog-*", ")", "-print",
        ],
        capture_output=True, text=True, check=False,
    )
    fixture_residue = subprocess.run(
        ["find", str(SKILL_DIRECTORY), "-name", ".watchdog-*", "-print"],
        capture_output=True, text=True, check=False,
    )
    leftovers = "\n".join(filter(None, (
        directory_residue.stdout.strip(), fixture_residue.stdout.strip(),
    )))
    if directory_residue.returncode or fixture_residue.returncode or leftovers:
        raise AssertionError(f"skill directory test-state residue: {leftovers}")
    if (SKILL_DIRECTORY / "SKILL.md").read_bytes() != SKILL_BYTES_AT_SUITE_START:
        raise AssertionError("SKILL.md changed while the watchdog suite ran")
    test_roots = subprocess.run(
        ["find", str(TEST_STATE_ROOT), "-maxdepth", "1", "-type", "d", "-name", "watchdog-test-*", "-print"],
        capture_output=True, text=True, check=False,
    )
    if test_roots.returncode or test_roots.stdout.strip():
        raise AssertionError(f"watchdog test-directory residue: {test_roots.stdout.strip()}")


class WatchdogProcessTestCase(unittest.TestCase):
    """Uses recorded process groups; cleanup never searches by process name."""

    def setUp(self):
        self._handles = []
        self._owned_pgids = []
        self._directories = []
        self.addCleanup(self._cleanup)  # Must be registered before anything is made.

    def _cleanup(self):
        for process in reversed(self._handles):
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except (ProcessLookupError, PermissionError):
                    continue
                try:
                    process.wait(timeout=0.2)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except (ProcessLookupError, PermissionError):
                        pass
                    process.wait(timeout=1)
        for pgid in reversed(self._owned_pgids):
            try:
                os.killpg(pgid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                continue
            time.sleep(0.02)
            try:
                os.killpg(pgid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
        for directory in reversed(self._directories):
            shutil.rmtree(directory, ignore_errors=True)

    def directory(self):
        test_root = TEST_STATE_ROOT / f"watchdog-test-{uuid.uuid4().hex}"
        directory = test_root / f"execution-{uuid.uuid4().hex}"
        directory.mkdir(parents=True)
        self._directories.append(test_root)
        return directory

    def preservation_project(self, execution_dir):
        """Create a disposable tracked checkout within this test's execution directory."""
        project_root = execution_dir / "project"
        project_root.mkdir()
        tracked = project_root / "tracked.txt"
        tracked.write_bytes(b"tracked watchdog bytes\n")
        for argv in (
            ["git", "init"],
            ["git", "config", "user.email", "watchdog@example.invalid"],
            ["git", "config", "user.name", "Watchdog fixture"],
            ["git", "add", tracked.name],
            ["git", "commit", "-m", "fixture"],
        ):
            subprocess.run(argv, cwd=project_root, capture_output=True, check=True)
        return project_root, tracked

    def start_decoy(self, script="import time; time.sleep(30)", *, argv=None, cwd=None):
        process = subprocess.Popen(
            argv or [PYTHON, "-c", script], start_new_session=True,
            cwd=cwd or self.directory(),
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        self._handles.append(process)
        ledger = os.environ.get("WATCHDOG_CLEANUP_PID_LEDGER")
        if ledger:
            with open(ledger, "a", encoding="utf-8") as stream:
                stream.write(f"{process.pid}\n")
        return process

    def run_child(self, script, *, result=True, validator=None, settings=None, project_root=None,
                  execution_dir=None, stdin_text=None, monotonic_clock=None, sleep=None):
        directory = execution_dir or self.directory()
        result_path = directory / "result.json" if result else None
        stdin_path = None
        if stdin_text is not None:
            stdin_path = directory / "prompt.txt"
            stdin_path.write_text(stdin_text, encoding="utf-8")
        outcome = run_execution(
            child_argv=[PYTHON, "-c", script],
            execution_dir=directory,
            project_root=project_root or Path.cwd(),
            base_revision="HEAD",
            result_path=result_path,
            events_path=directory / "events.jsonl",
            stderr_path=directory / "stderr.log",
            validate_result=validator,
            stdin_path=stdin_path,
            register_process=self._handles.append,
            monotonic_clock=monotonic_clock or time.monotonic,
            sleep=sleep or time.sleep,
            settings=settings or WatchdogSettings(
                start_deadline_seconds=0.08,
                activity_stall_seconds=0.08,
                hard_timeout_seconds=0.25,
                poll_interval_seconds=0.01,
                exit_collect_wait_seconds=0.08,
                abort_grace_seconds=0.03,
                reap_grace_seconds=0.03,
                reap_wait_cap_seconds=0.08,
            ),
        )
        self._owned_pgids.extend(outcome.record["residual_pids"])
        return outcome, directory

    def test_invocation_transports_implementation_author_readiness_and_preflight(self):
        for form, result in (("implementation", True), ("author", True), ("readiness", True), ("preflight", False)):
            with self.subTest(form=form):
                script = (
                    "import json,pathlib,sys; prompt=sys.stdin.read(); print(prompt); "
                    "print('error', file=sys.stderr); "
                    + ("pathlib.Path('result.json').write_text(json.dumps({'ok': True}))" if result else "")
                )
                outcome, directory = self.run_child(
                    script, result=result, validator=(lambda path: True) if result else None,
                    stdin_text=f"{form} prompt\n",
                )
                self.assertEqual("completed", outcome.status)
                self.assertEqual([PYTHON, "-c", script], outcome.record["argv"])
                self.assertEqual(f"{form} prompt\n\n", (directory / "events.jsonl").read_text())
                self.assertIn("error", (directory / "stderr.log").read_text())
                self.assertFalse((Path.cwd() / "result.json").exists())

    def test_cli_transports_prompt_file_to_child_stdin(self):
        directory = self.directory()
        prompt = directory / "prompt.txt"
        prompt.write_text("a prompt from the orchestrator\n", encoding="utf-8")
        script = "import sys; print(sys.stdin.read(), end='')"
        completed = subprocess.run(
            [
                PYTHON, str(Path(execution_watchdog.__file__).resolve()),
                "--project-root", str(Path.cwd()), "--base-revision", "HEAD",
                "--execution-dir", str(directory), "--events-path", str(directory / "events.jsonl"),
                "--stderr-path", str(directory / "stderr.log"), "--stdin-path", str(prompt),
                "--", PYTHON, "-c", script,
            ],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual("a prompt from the orchestrator\n", (directory / "events.jsonl").read_text())

    def test_execution_artifacts_use_unique_state_directory_not_tmp(self):
        outcome, directory = self.run_child("print('reply')", result=False)
        self.assertEqual(directory, Path(outcome.record["execution_dir"]))
        state_root = TEST_STATE_ROOT
        self.assertTrue(directory.is_relative_to(state_root))
        for artifact in (directory / "execution-record.json", directory / "events.jsonl", directory / "stderr.log"):
            self.assertTrue(artifact.exists())
            self.assertTrue(artifact.is_relative_to(directory))

    def test_preflight_accepts_stderr_activity_and_nonempty_reply(self):
        outcome, _ = self.run_child("import sys; print('reply'); print('activity', file=sys.stderr)", result=False)
        self.assertEqual("completed", outcome.status)
        self.assertTrue(outcome.record["started"])

    def test_preflight_rejects_stderr_only_but_accepts_stdout_reply_with_stderr_progress(self):
        stderr_only, _ = self.run_child("import sys; print('progress', file=sys.stderr)", result=False)
        self.assertEqual("failed", stderr_only.status)
        self.assertEqual("preflight_failed", stderr_only.record["watchdog_reason"])
        reply, _ = self.run_child("import sys; print('reply'); print('progress', file=sys.stderr)", result=False)
        self.assertEqual("completed", reply.status)
        self.assertTrue(reply.record["started"])

    def test_start_deadline_records_no_output_reason(self):
        outcome, _ = self.run_child("import time; time.sleep(1)", result=False)
        self.assertEqual("start_deadline", outcome.record["watchdog_reason"])

    def test_missing_streams_trigger_stall_and_hard_timeout_reasons(self):
        settings = WatchdogSettings(start_deadline_seconds=0.15, activity_stall_seconds=0.03, hard_timeout_seconds=0.2, poll_interval_seconds=0.01, exit_collect_wait_seconds=0.02, abort_grace_seconds=0.01, reap_grace_seconds=0.01, reap_wait_cap_seconds=0.02)
        outcome, _ = self.run_child("import sys,time; print('started'); sys.stdout.flush(); time.sleep(1)", result=False, settings=settings)
        self.assertEqual("activity_stall", outcome.record["watchdog_reason"])
        settings = WatchdogSettings(start_deadline_seconds=1, activity_stall_seconds=1, hard_timeout_seconds=0.03, poll_interval_seconds=0.01, exit_collect_wait_seconds=0.02, abort_grace_seconds=0.01, reap_grace_seconds=0.01, reap_wait_cap_seconds=0.02)
        outcome, _ = self.run_child("import time; time.sleep(1)", result=False, settings=settings)
        self.assertEqual("hard_timeout", outcome.record["watchdog_reason"])

    def test_named_watchdog_settings_allow_short_fixture_values(self):
        self.assertEqual(600, ACTIVITY_STALL_SECONDS)
        self.assertEqual(5, EXIT_COLLECT_WAIT_SECONDS)
        self.assertEqual(60, ABORT_GRACE_SECONDS)
        self.assertEqual(60, REAP_GRACE_SECONDS)
        self.assertGreaterEqual(REAP_WAIT_CAP_SECONDS, REAP_GRACE_SECONDS)
        self.assertLess(EXIT_COLLECT_WAIT_SECONDS, ABORT_GRACE_SECONDS)

    def test_existing_valid_result_is_accepted_without_abort(self):
        outcome, directory = self.run_child("import json,pathlib; pathlib.Path('result.json').write_text(json.dumps({'ok': True}))", validator=lambda path: True)
        self.assertEqual("completed", outcome.status)
        self.assertFalse(outcome.record["abort"]["attempted"])
        self.assertTrue((directory / "result.json").exists())

    def test_result_created_before_final_abort_recheck_wins(self):
        settings = WatchdogSettings(start_deadline_seconds=.2, activity_stall_seconds=.2, hard_timeout_seconds=.4, poll_interval_seconds=.01, exit_collect_wait_seconds=.08, abort_grace_seconds=.03, reap_grace_seconds=.03, reap_wait_cap_seconds=.08)
        outcome, _ = self.run_child("import json,pathlib,time; time.sleep(.04); pathlib.Path('result.json').write_text(json.dumps({'ok': True})); time.sleep(.02)", validator=lambda path: True, settings=settings)
        self.assertEqual("completed", outcome.status)
        self.assertFalse(outcome.record["abort"]["attempted"])
        self.assertIsNone(outcome.record["watchdog_reason"])

    def test_accepted_result_with_live_owned_child_is_reap_candidate(self):
        outcome, _ = self.run_child("import json,pathlib,time; pathlib.Path('result.json').write_text(json.dumps({'ok': True})); time.sleep(1)", validator=lambda path: True)
        self.assertEqual("completed", outcome.status)
        self.assertTrue(outcome.record["reap"]["candidate"])

    def test_first_poll_result_and_terminal_paths_return_within_bounds(self):
        started = time.monotonic()
        outcome, _ = self.run_child("import json,pathlib; pathlib.Path('result.json').write_text(json.dumps({'ok': True}))", validator=lambda path: True)
        self.assertEqual("completed", outcome.status)
        self.assertLess(time.monotonic() - started, 0.3)

    def test_result_exit_schema_decision_matrix_and_natural_exit(self):
        matrix = ((0, True, "completed"), (1, True, "failed"), (0, False, "failed"))
        for exit_code, valid, expected in matrix:
            with self.subTest(exit_code=exit_code, valid=valid):
                outcome, _ = self.run_child(f"import json,pathlib,sys; pathlib.Path('result.json').write_text(json.dumps({{'ok': True}})); sys.exit({exit_code})", validator=lambda path, valid=valid: valid)
                self.assertEqual(expected, outcome.status)

    def test_preflight_failure_never_consumes_restart_budget(self):
        outcome, _ = self.run_child("import sys; sys.exit(1)", result=False)
        self.assertFalse(outcome.record["restart_candidate"])

    def test_dead_recorded_pid_without_result_records_five_facts_immediately(self):
        started = time.monotonic()
        outcome, _ = self.run_child("pass")
        self.assertEqual("failed", outcome.status)
        self.assertEqual(0, outcome.record["child_exit_code"])
        self.assertFalse(outcome.record["result_exists"])
        self.assertEqual("not_run", outcome.record["result_schema_validation"])
        self.assertIsNone(outcome.record["preservation_bundle"])
        self.assertEqual("child_exited_no_result", outcome.record["watchdog_reason"])
        self.assertLess(time.monotonic() - started, 1)

    def test_poll_order_is_result_pid_then_activity_without_name_lookup(self):
        outcome, _ = self.run_child("pass")
        self.assertEqual(["result", "pid", "activity"], outcome.record["poll_order"])

    def test_result_then_exit_within_collect_wait_is_success_without_budget_use(self):
        outcome, _ = self.run_child("import json,pathlib,time; pathlib.Path('result.json').write_text(json.dumps({'ok': True})); time.sleep(.02)", validator=lambda path: True)
        self.assertEqual("completed", outcome.status)
        self.assertEqual(0, outcome.record["retry_consumed"])

    def test_valid_result_with_unknown_exit_after_collect_wait_is_success(self):
        outcome, _ = self.run_child("import json,pathlib,time; pathlib.Path('result.json').write_text(json.dumps({'ok': True})); time.sleep(1)", validator=lambda path: True)
        self.assertEqual("completed", outcome.status)
        self.assertEqual("unknown", outcome.record["child_exit_code"])

    def test_cleanup_after_forced_harness_failure_and_sigint(self):
        child = self.start_decoy()
        decoy = self.start_decoy()
        self.assertIsNone(child.poll())
        self.assertIsNone(decoy.poll())
        # Cleanup is invoked explicitly to model a failing/interrupted harness.
        self._cleanup()
        self.assertIsNotNone(child.poll())
        self.assertIsNotNone(decoy.poll())


class WatchdogAbortAndReapTestCase(WatchdogProcessTestCase):
    def test_invalid_base_revision_fails_before_child_launch(self):
        directory = self.directory()
        project_root, _ = self.preservation_project(directory)
        child_started = directory / "child-started"
        completed = subprocess.run(
            [
                PYTHON, str(Path(execution_watchdog.__file__).resolve()),
                "--project-root", str(project_root), "--base-revision", "not-a-revision",
                "--execution-dir", str(directory), "--events-path", str(directory / "events.jsonl"),
                "--stderr-path", str(directory / "stderr.log"), "--",
                PYTHON, "-c", f"import pathlib; pathlib.Path({str(child_started)!r}).write_text('started')",
            ],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(2, completed.returncode)
        self.assertIn("invalid --base-revision", completed.stderr)
        self.assertFalse(child_started.exists())

    def test_abort_preserves_diff_events_stderr_and_fingerprint_before_sigterm(self):
        directory = self.directory()
        project_root, tracked = self.preservation_project(directory)
        original_tracked = tracked.read_bytes()
        tracked.write_bytes(original_tracked + b"\n# watchdog preservation fixture\n")
        untracked = project_root / f".watchdog-untracked-{uuid.uuid4().hex}.txt"
        untracked_bytes = b"untracked watchdog bytes\x00\xff\n"
        untracked.write_bytes(untracked_bytes)
        signal_order = []
        original_preserve = execution_watchdog.preserve_bundle

        def preserve_then_record(**kwargs):
            bundle = original_preserve(**kwargs)
            signal_order.append("preserved")
            return bundle

        original_killpg = execution_watchdog.os.killpg

        def record_signal(pgid, signal_number):
            signal_order.append(signal.Signals(signal_number).name)
            return original_killpg(pgid, signal_number)

        with mock.patch.object(execution_watchdog, "preserve_bundle", preserve_then_record), \
             mock.patch.object(execution_watchdog.os, "killpg", record_signal):
            outcome, directory = self.run_child(
                "import sys,time; print('event'); sys.stdout.flush(); print('stderr', file=sys.stderr, flush=True); time.sleep(2)",
                project_root=project_root, execution_dir=directory,
            )
        bundle = Path(outcome.record["preservation_bundle"])
        self.assertIn(b"watchdog preservation fixture", (bundle / "tracked.patch").read_bytes())
        self.assertTrue((bundle / "staged.patch").exists())
        self.assertIn(untracked.name.encode() + b"\0", (bundle / "untracked.manifest.nul").read_bytes())
        archived = bundle / "untracked-content" / untracked.name
        self.assertEqual(untracked_bytes, archived.read_bytes())
        self.assertEqual(hashlib.sha256(untracked_bytes).hexdigest(), next(
            member["sha256"] for member in json.loads((bundle / "metadata.json").read_text())["members"]
            if member["path"] == f"{untracked.name}" and member["kind"] == "untracked"
        ))
        self.assertEqual(b"event\n", (bundle / "captured-streams" / "events.jsonl").read_bytes())
        self.assertEqual(b"stderr\n", (bundle / "captured-streams" / "stderr.log").read_bytes())
        metadata = json.loads((bundle / "metadata.json").read_text())
        expected_base = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"], cwd=project_root,
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        self.assertEqual(expected_base, metadata["base_revision"])
        canonical = json.dumps(metadata, sort_keys=True, separators=(",", ":")).encode("utf-8")
        self.assertEqual(hashlib.sha256(canonical).hexdigest() + "\n", (bundle / "fingerprint.txt").read_text())
        self.assertTrue(outcome.record["abort"]["attempted"])
        self.assertEqual("preserved", signal_order[0])
        self.assertIn("SIGTERM", signal_order)
        self.assertLess(signal_order.index("preserved"), signal_order.index("SIGTERM"))
        self.assertTrue((directory / "events.jsonl").exists())

    def test_preservation_failure_prevents_all_abort_signals(self):
        directory = self.directory()
        project_root, _ = self.preservation_project(directory)
        untracked = project_root / f".watchdog-unreadable-{uuid.uuid4().hex}.txt"
        untracked.write_bytes(b"cannot archive this")
        untracked.chmod(0)
        original_read_bytes = Path.read_bytes

        def unavailable_source(path):
            if path == untracked:
                raise PermissionError("fixture makes this enumerated untracked path unavailable")
            return original_read_bytes(path)

        with mock.patch.object(Path, "read_bytes", unavailable_source):
            outcome, _ = self.run_child(
                "import time; time.sleep(2)", project_root=project_root, execution_dir=directory,
            )
        self.assertFalse(outcome.record["abort"]["attempted"])
        self.assertEqual("preservation_failed", outcome.record["watchdog_reason"])
        self.assertEqual([], outcome.record["signals"])
        self.assertEqual([], outcome.record["abort"]["signals"])

    def test_failed_git_diff_prevents_all_abort_signals(self):
        actual_run = execution_watchdog.subprocess.run

        def git_diff_fails(argv, *args, **kwargs):
            if argv[:2] == ["git", "rev-parse"]:
                return actual_run(argv, *args, **kwargs)
            return subprocess.CompletedProcess(argv, 128, b"", b"bad revision")

        with mock.patch.object(
            execution_watchdog.subprocess, "run", side_effect=git_diff_fails,
        ):
            outcome, _ = self.run_child("import time; time.sleep(2)")
        self.assertEqual("preservation_failed", outcome.record["watchdog_reason"])
        self.assertEqual([], outcome.record["signals"])
        self.assertEqual([], outcome.record["abort"]["signals"])

    def test_abort_refuses_unowned_pgid_and_never_uses_name_lookup(self):
        decoy = self.start_decoy()
        process = self.start_decoy()
        result, residual = execution_watchdog._signal_owned_group(process, decoy.pid, .01, .02)
        self.assertEqual("ownership_refused", result["outcome"])
        self.assertFalse(result["attempted"])
        self.assertEqual([process.pid], residual)
        self.assertIsNone(decoy.poll())

    def test_abort_kills_owned_child_but_not_same_command_decoy(self):
        script = "import time; time.sleep(2)"
        decoy = self.start_decoy(argv=[PYTHON, "-c", script])
        outcome, _ = self.run_child(script)
        self.assertTrue(outcome.record["abort"]["attempted"])
        self.assertIsNone(decoy.poll())
        self.assertNotIn(decoy.pid, outcome.record["residual_pids"])
        self.assertNotIn(decoy.pid, outcome.record["signals"])

    def test_abort_records_five_recovery_facts_and_consumes_one_budget(self):
        outcome, _ = self.run_child("import time; time.sleep(1)")
        decision = apply_restart_budget(outcome.record, 1)
        self.assertEqual(1, decision["retry_consumed"])
        self.assertTrue(decision["restart_stopped"])
        self.assertEqual(1, outcome.record["retry_budget_initial"])
        self.assertEqual(0, outcome.record["retry_budget_remaining"])
        self.assertEqual(1, outcome.record["report_payload"]["retry_consumed"])
        persisted = json.loads(Path(outcome.record["execution_record_path"]).read_text(encoding="utf-8"))
        self.assertEqual(1, persisted["retry_budget_initial"])

    def test_execution_record_and_report_payload_include_required_distinct_fields(self):
        outcome, _ = self.run_child("pass")
        self.assertRegex(outcome.record["execution_id"], r"^execution-")
        self.assertEqual(outcome.record["pid"], outcome.record["pgid"])
        self.assertRegex(outcome.record["started_at"], r"Z$")
        self.assertRegex(outcome.record["ended_at"], r"Z$")
        self.assertGreaterEqual(outcome.record["elapsed_s"], 0)
        self.assertEqual("not_needed", outcome.record["abort"]["outcome"])
        self.assertEqual("not_needed", outcome.record["reap"]["outcome"])
        self.assertEqual([], outcome.record["residual_pids"])
        self.assertIsNot(outcome.record["abort"], outcome.record["reap"])
        payload = outcome.record["report_payload"]
        self.assertEqual({
            "execution_id", "pid", "pgid", "started_at", "ended_at", "elapsed_s", "child_exit_code",
            "result_exists", "result_schema_validation", "started", "watchdog_reason", "signals",
            "preservation_bundle", "preservation_status", "abort", "reap", "preflight_termination",
            "residual_pids", "retry_budget_initial", "retry_budget_remaining", "retry_consumed",
            "restart_attempted", "restart_stopped",
        }, set(payload))
        self.assertIsNot(payload["abort"], payload["reap"])
        self.assertEqual(outcome.record["execution_id"], payload["execution_id"])

    def test_parent_restart_budget_is_consumed_once_and_stops_at_zero(self):
        record = {"restart_candidate": True, "retry_consumed": 0}
        first = apply_restart_budget(record, 1)
        self.assertEqual(0, first["retry_budget_remaining"])
        self.assertTrue(first["restart_stopped"])
        second = apply_restart_budget(record, 0)
        self.assertTrue(second["restart_stopped"])
        self.assertFalse(second["restart_attempted"])

    def test_sigterm_ignoring_abort_uses_abort_grace_then_sigkill(self):
        outcome, _ = self.run_child("import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(1)")
        signals = outcome.record["abort"]["signals"]
        self.assertEqual(["SIGTERM", "SIGKILL"], signals)

    def test_result_present_unaccepted_records_five_recovery_facts_and_budget(self):
        for script, validator, expected_exit, expected_validation in (
            ("import json,pathlib,sys; pathlib.Path('result.json').write_text(json.dumps({'ok': True})); sys.exit(1)", lambda path: True, 1, "passed"),
            ("import json,pathlib; pathlib.Path('result.json').write_text(json.dumps({'ok': True}))", lambda path: False, 0, "mismatch"),
        ):
            with self.subTest(expected_validation=expected_validation):
                outcome, _ = self.run_child(script, validator=validator)
                self.assertFalse(outcome.record["abort"]["attempted"])
                self.assertTrue(outcome.record["restart_candidate"])
                self.assertEqual(expected_exit, outcome.record["child_exit_code"])
                self.assertTrue(outcome.record["result_exists"])
                self.assertEqual(expected_validation, outcome.record["result_schema_validation"])
                self.assertIsNone(outcome.record["preservation_bundle"])
                self.assertEqual("not_created_no_abort", outcome.record["preservation_status"])
                self.assertEqual("result_unaccepted", outcome.record["watchdog_reason"])
                decision = apply_restart_budget(outcome.record, 2)
                self.assertEqual(1, decision["retry_consumed"])
                self.assertEqual(1, decision["retry_budget_remaining"])
                self.assertTrue(decision["restart_attempted"])
                self.assertFalse(decision["restart_stopped"])

    def test_reap_kills_owned_residual_child_but_not_same_command_decoy(self):
        script = "import json,pathlib,time; pathlib.Path('result.json').write_text(json.dumps({'ok': True})); time.sleep(2)"
        decoy = self.start_decoy(argv=[PYTHON, "-c", script])
        outcome, _ = self.run_child(script, validator=lambda path: True)
        self.assertTrue(outcome.record["reap"]["attempted"])
        self.assertIsNone(decoy.poll())
        self.assertNotIn(decoy.pid, outcome.record["residual_pids"])
        self.assertNotIn(decoy.pid, outcome.record["signals"])

    def test_accepted_result_records_reap_only_and_keeps_budget(self):
        outcome, _ = self.run_child("import json,pathlib,time; pathlib.Path('result.json').write_text(json.dumps({'ok': True})); time.sleep(1)", validator=lambda path: True)
        self.assertFalse(outcome.record["abort"]["attempted"])
        self.assertEqual(0, outcome.record["retry_consumed"])

    def test_reap_sends_sigterm_before_sigkill(self):
        outcome, _ = self.run_child("import json,pathlib,signal,time; pathlib.Path('result.json').write_text(json.dumps({'ok': True})); signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(1)", validator=lambda path: True)
        self.assertEqual(["SIGTERM", "SIGKILL"], outcome.record["reap"]["signals"])

    def test_reap_escalates_to_sigkill_and_records_outcome(self):
        outcome, _ = self.run_child("import json,pathlib,signal,time; pathlib.Path('result.json').write_text(json.dumps({'ok': True})); signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(1)", validator=lambda path: True)
        self.assertEqual("killed", outcome.record["reap"]["outcome"])

    def test_reap_wait_cap_records_residual_and_returns_accepted_result(self):
        class Clock:
            now = 0
            def monotonic(self): return self.now
            def sleep(self, seconds): self.now += seconds
        clock = Clock()
        child = self.start_decoy()
        sent = []
        with mock.patch.object(execution_watchdog.os, "killpg", side_effect=lambda pgid, sig: sent.append(signal.Signals(sig).name)):
            result, residual = execution_watchdog._signal_owned_group(
                child, child.pid, .02, .05, monotonic_clock=clock.monotonic, sleep=clock.sleep,
            )
        self.assertEqual("cap_exceeded", result["outcome"])
        self.assertEqual(["SIGTERM", "SIGKILL"], sent)
        self.assertEqual([child.pid], residual)

    def test_reap_failure_is_not_abort_and_never_consumes_budget(self):
        settings = WatchdogSettings(start_deadline_seconds=.05, activity_stall_seconds=.05, hard_timeout_seconds=.2, poll_interval_seconds=.01, exit_collect_wait_seconds=.01, abort_grace_seconds=.01, reap_grace_seconds=.2, reap_wait_cap_seconds=.02)
        outcome, _ = self.run_child("import json,pathlib,signal,time; pathlib.Path('result.json').write_text(json.dumps({'ok': True})); signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(1)", validator=lambda path: True, settings=settings)
        self.assertFalse(outcome.record["abort"]["attempted"])
        self.assertEqual(0, outcome.record["retry_consumed"])

    def test_watchdog_uses_subprocess_and_monotonic_clock_without_external_timeout(self):
        source = Path(__file__).resolve().parents[1] / "scripts" / "execution_watchdog.py"
        text = source.read_text(encoding="utf-8")
        self.assertIn("subprocess.Popen", text)
        self.assertIn("time.monotonic", text)
        self.assertNotIn('"timeout"', text)
        self.assertNotIn('"gtimeout"', text)
