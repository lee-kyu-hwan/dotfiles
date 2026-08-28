from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import quality_state
from quality_state import StateError


def run_git(root, *args):
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=True, capture_output=True, text=True,
    )


def make_git_repo(testcase):
    root = Path(testcase.enterContext(tempfile.TemporaryDirectory()))
    run_git(root, "init")
    run_git(root, "config", "user.name", "quality-goal-test")
    run_git(root, "config", "user.email", "quality-goal-test@example.invalid")
    (root / "app.txt").write_text("base\n", encoding="utf-8")
    run_git(root, "add", "app.txt")
    run_git(root, "commit", "-m", "fixture")
    return root


FIXED_NOW = datetime(2026, 8, 25, 12, 34, 56, tzinfo=timezone.utc)
VALID_DIGEST = "a" * 64
VALID_FINGERPRINT = hashlib.sha256(b"valid workspace").hexdigest()
OLD_FINGERPRINT = hashlib.sha256(b"old workspace").hexdigest()
NEW_FINGERPRINT = hashlib.sha256(b"new workspace").hexdigest()


def write_json(directory, name, value):
    path = Path(directory) / name
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def high_finding(finding_id, new_blocker_evidence=None):
    return {
        "id": finding_id,
        "severity": "High",
        "description": "A required quality condition is not satisfied.",
        "evidence_location": "artifact.md#Quality",
        "rubric_item": "Quality condition completeness",
        "required_resolution": "Resolve the quality condition and document evidence.",
        "new_blocker_evidence": new_blocker_evidence,
    }


def valid_review(artifact="plan", round_number=1, verdict="PASS", blockers=None):
    blockers = list(blockers or [])
    evidence = None if round_number == 1 else "The current round provides fresh evidence."
    return {
        "artifact": artifact,
        "round": round_number,
        "score": 92,
        "verdict": verdict,
        "blockers": blockers,
        "findings": [high_finding(blocker, evidence) for blocker in blockers],
        "evidence": [
            {
                "claim": "The reviewed artifact is traceable to its acceptance criteria.",
                "location": "artifact.md#Traceability",
            }
        ],
        "required_next_action": None,
    }


def state_at(stage, mode="standard", project_root=None, goal="Build the quality workflow"):
    state = quality_state.new_state(
        goal,
        "auto",
        project_root or Path.cwd(),
        "artifact-output",
        task_id="test-task",
        now=FIXED_NOW,
    )
    state["stage"] = stage
    state["mode"] = mode
    return state


class ConstantTests(unittest.TestCase):
    def test_transition_terminal_and_round_constants_match_the_contract(self):
        self.assertEqual(
            {
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
            },
            quality_state.ALLOWED_TRANSITIONS,
        )
        self.assertEqual(
            {"COMPLETED", "BLOCKED", "NEEDS_REDESIGN", "CANCELLED"},
            quality_state.TERMINAL_STATES,
        )
        self.assertEqual(
            {"spec": 3, "plan": 2, "code": 3},
            quality_state.ROUND_LIMITS,
        )


class NormalizeGoalTests(unittest.TestCase):
    def test_normalize_goal_applies_nfkc_whitespace_collapse_and_casefold(self):
        goal = "  Ｐａｒｔｎｅｒ\tSWITCH  Straße\n"

        self.assertEqual("partner switch strasse", quality_state.normalize_goal(goal))

    def test_goal_key_matches_equivalent_spellings_but_not_different_goals(self):
        first = "  Ｐａｒｔｎｅｒ\tSWITCH  Straße\n"
        equivalent = "partner   switch   STRASSE"
        different = "partner switch status"

        self.assertEqual(quality_state.goal_key(first), quality_state.goal_key(equivalent))
        self.assertNotEqual(quality_state.goal_key(first), quality_state.goal_key(different))
        self.assertEqual(
            hashlib.sha256(quality_state.normalize_goal(first).encode("utf-8")).hexdigest(),
            quality_state.goal_key(first),
        )


class NewStateTests(unittest.TestCase):
    def test_new_state_has_the_complete_schema_version_one_shape(self):
        project_root = Path("relative-project")
        state = quality_state.new_state(
            "  Ship Ｆｕｌｌ-Width Goal  ",
            "auto",
            project_root,
            "artifact-output",
            now=FIXED_NOW,
        )

        self.assertEqual(
            {
                "schema_version",
                "task_id",
                "goal",
                "goal_key",
                "requested_mode",
                "mode",
                "classification_reasons",
                "stage",
                "project_root",
                "artifact_dir",
                "base_revision",
                "initial_dirty_paths",
                "artifacts",
                "artifact_digests",
                "rounds",
                "reviews",
                "open_finding_ids",
                "review_validation_retry",
                "plan_approval",
                "verification",
                "status_reason",
                "created_at",
                "updated_at",
            },
            set(state),
        )
        self.assertEqual(1, state["schema_version"])
        self.assertEqual("  Ship Ｆｕｌｌ-Width Goal  ", state["goal"])
        self.assertEqual(quality_state.goal_key(state["goal"]), state["goal_key"])
        self.assertEqual("auto", state["requested_mode"])
        self.assertIsNone(state["mode"])
        self.assertEqual([], state["classification_reasons"])
        self.assertEqual("INTAKE", state["stage"])
        self.assertEqual(str(project_root.resolve()), state["project_root"])
        self.assertEqual("artifact-output", state["artifact_dir"])
        self.assertIsNone(state["base_revision"])
        self.assertEqual([], state["initial_dirty_paths"])
        self.assertEqual(
            {"spec": None, "plan": None, "compact_plan": None, "report": None},
            state["artifacts"],
        )
        self.assertEqual(
            {"spec": None, "plan": None, "compact_plan": None, "report": None},
            state["artifact_digests"],
        )
        self.assertEqual({"spec": 0, "plan": 0, "code": 0}, state["rounds"])
        self.assertEqual({"spec": [], "plan": [], "code": []}, state["reviews"])
        self.assertEqual(
            {"spec": [], "plan": [], "code": []},
            state["open_finding_ids"],
        )
        self.assertIsNone(state["review_validation_retry"])
        self.assertIsNone(state["plan_approval"])
        self.assertEqual(
            {"path": None, "workspace_fingerprint": None, "valid": False},
            state["verification"],
        )
        self.assertIsNone(state["status_reason"])
        self.assertEqual("2026-08-25T12:34:56Z", state["created_at"])
        self.assertEqual("2026-08-25T12:34:56Z", state["updated_at"])
        self.assertIn("ship-full-width-goal", state["task_id"])
        self.assertRegex(
            state["task_id"],
            r"^\d{8}T\d{6}Z-[\w-]+-[0-9a-f]{8}$",
        )

    def test_new_state_accepts_pathlike_artifact_dir_and_rejects_empty_or_invalid_values(self):
        state = quality_state.new_state(
            "A valid goal",
            "standard",
            Path.cwd(),
            Path("artifact-output"),
        )

        self.assertEqual("artifact-output", state["artifact_dir"])
        for artifact_dir in ("", 3, None):
            with self.subTest(artifact_dir=artifact_dir):
                with self.assertRaises(StateError):
                    quality_state.new_state(
                        "A valid goal",
                        "standard",
                        Path.cwd(),
                        artifact_dir,
                    )

    def test_new_state_task_id_keeps_unicode_slug_and_goal_key_suffix(self):
        state = quality_state.new_state(
            "한국어 품질 목표",
            "standard",
            Path.cwd(),
            "artifacts",
            now=FIXED_NOW,
        )

        self.assertIn("한국어-품질-목표", state["task_id"])
        self.assertTrue(state["task_id"].endswith(f"-{quality_state.goal_key(state['goal'])[:8]}"))

    def test_new_state_rejects_invalid_requested_modes(self):
        for requested_mode in ("", "unsafe", None):
            with self.subTest(requested_mode=requested_mode):
                with self.assertRaises(StateError):
                    quality_state.new_state(
                        "A valid goal",
                        requested_mode,
                        Path.cwd(),
                        "artifacts",
                    )

    def test_new_state_rejects_empty_or_whitespace_only_goals(self):
        for goal in ("", " \t\n"):
            with self.subTest(goal=repr(goal)):
                with self.assertRaises(StateError):
                    quality_state.new_state(
                        goal,
                        "standard",
                        Path.cwd(),
                        "artifacts",
                    )

    def test_new_state_respects_a_supplied_task_id(self):
        state = quality_state.new_state(
            "A valid goal",
            "strict",
            Path.cwd(),
            "artifacts",
            task_id="provided-task-id",
            now=FIXED_NOW,
        )

        self.assertEqual("provided-task-id", state["task_id"])


class PersistenceTests(unittest.TestCase):
    def test_save_and_load_state_round_trip_without_tmp_siblings(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            state = state_at("CLASSIFIED")
            path = directory / "state.json"

            quality_state.save_state(path, state)

            self.assertEqual(state, quality_state.load_state(path))
            self.assertEqual([], list(directory.glob("*.tmp")))

    def test_load_state_missing_file_raises_state_error(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(StateError):
                quality_state.load_state(Path(directory) / "missing.json")

    def test_load_state_corrupt_json_raises_state_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            path.write_text("{not valid json", encoding="utf-8")

            with self.assertRaises(StateError):
                quality_state.load_state(path)

    def test_load_state_requires_schema_version_one(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            state = state_at("CLASSIFIED")
            missing = write_json(directory, "missing.json", {"stage": "CLASSIFIED"})
            wrong = dict(state)
            wrong["schema_version"] = 2
            wrong_path = write_json(directory, "wrong.json", wrong)

            for path in (missing, wrong_path):
                with self.subTest(path=path):
                    with self.assertRaises(StateError):
                        quality_state.load_state(path)


class ClassifyTests(unittest.TestCase):
    def test_classify_sets_mode_reasons_and_classified_stage(self):
        state = state_at("INTAKE", mode=None)
        reasons = ["existing snapshot can be reused", "scope is limited"]

        result = quality_state.classify(state, "light", reasons)

        self.assertEqual("light", result["mode"])
        self.assertEqual(reasons, result["classification_reasons"])
        self.assertEqual("CLASSIFIED", result["stage"])
        self.assertIsNotNone(result["updated_at"])

    def test_classify_rejects_invalid_modes_and_reasons(self):
        for mode in ("auto", "", "unknown"):
            with self.subTest(mode=mode):
                with self.assertRaises(StateError):
                    quality_state.classify(state_at("INTAKE", mode=None), mode, ["reason"])

        for reasons in ([], ["   "], ["valid", 3]):
            with self.subTest(reasons=reasons):
                with self.assertRaises(StateError):
                    quality_state.classify(state_at("INTAKE", mode=None), "standard", reasons)

    def test_classify_is_rejected_outside_intake(self):
        with self.assertRaises(StateError):
            quality_state.classify(state_at("CLASSIFIED"), "standard", ["reason"])

    def test_direct_intake_to_classified_transition_is_rejected(self):
        state = state_at("INTAKE", mode=None)

        with self.assertRaises(StateError):
            quality_state.transition(state, "CLASSIFIED")


class TransitionTests(unittest.TestCase):
    def test_every_allowed_edge_is_accepted_or_uses_classify_for_classified(self):
        for source, targets in quality_state.ALLOWED_TRANSITIONS.items():
            for target in targets:
                with self.subTest(source=source, target=target):
                    state = state_at(source)
                    reason = "synthetic transition" if target in quality_state.TERMINAL_STATES else None

                    if source == "INTAKE" and target == "CLASSIFIED":
                        result = quality_state.classify(state, "standard", ["synthetic classification"])
                    elif source == "CLASSIFIED" and target == "AWAITING_PLAN_APPROVAL":
                        state = state_at(source, mode="light")
                        result = quality_state.transition(state, target, reason)
                    elif source == "CLASSIFIED" and target == "SPEC_REVIEW":
                        state = state_at(source, mode="standard")
                        result = quality_state.transition(state, target, reason)
                    elif source == "CODE_REVIEW" and target == "COMPLETED":
                        state["rounds"]["code"] = 1
                        state["reviews"]["code"] = [
                            {
                                "verdict": "PASS",
                                "blockers": [],
                                "artifact_digest": VALID_DIGEST,
                            }
                        ]
                        state["open_finding_ids"]["code"] = []
                        state["verification"]["valid"] = True
                        state["verification"]["workspace_fingerprint"] = VALID_DIGEST
                        result = quality_state.transition(state, target, reason)
                    elif (source, target) in {
                        ("SPEC_REVIEW", "SPEC_PASSED"),
                        ("PLAN_REVIEW", "PLAN_PASSED"),
                    }:
                        artifact = "spec" if source == "SPEC_REVIEW" else "plan"
                        state["rounds"][artifact] = 1
                        state["reviews"][artifact] = [{"verdict": "PASS", "blockers": []}]
                        state["open_finding_ids"][artifact] = []
                        result = quality_state.transition(state, target, reason)
                    elif source in {"AWAITING_PLAN_APPROVAL", "CODE_REVIEW"} and target == "IMPLEMENTING":
                        with tempfile.TemporaryDirectory() as directory:
                            plan_path = Path(directory) / "plan.md"
                            plan_path.write_text("approved plan\n", encoding="utf-8")
                            state["artifacts"]["plan"] = str(plan_path)
                            state["artifact_digests"]["plan"] = quality_state._file_digest(plan_path)
                            if source == "CODE_REVIEW":
                                state["stage"] = "AWAITING_PLAN_APPROVAL"
                            quality_state.approve_plan(
                                state,
                                plan_path,
                                "2026-08-25T12:00:00Z",
                            )
                            state["stage"] = source
                            result = quality_state.transition(state, target, reason)
                    else:
                        result = quality_state.transition(state, target, reason)

                    self.assertEqual(target, result["stage"])

    def test_invalid_transition_raises_without_mutating_the_input(self):
        state = state_at("INTAKE")
        before = deepcopy(state)

        with self.assertRaises(StateError):
            quality_state.transition(state, "IMPLEMENTING")

        self.assertEqual(before, state)

    def test_terminal_states_reject_every_possible_outgoing_target(self):
        all_states = set(quality_state.ALLOWED_TRANSITIONS) | set(quality_state.TERMINAL_STATES)

        for terminal in quality_state.TERMINAL_STATES:
            for target in all_states:
                with self.subTest(terminal=terminal, target=target):
                    state = state_at(terminal)
                    before = deepcopy(state)
                    with self.assertRaises(StateError):
                        quality_state.transition(state, target, "terminal transition")
                    self.assertEqual(before, state)

    def test_blocked_redesign_and_cancelled_require_and_store_a_reason(self):
        cases = (
            ("INTAKE", "BLOCKED"),
            ("SPEC_REVIEW", "NEEDS_REDESIGN"),
            ("INTAKE", "CANCELLED"),
        )

        for source, target in cases:
            with self.subTest(source=source, target=target):
                for reason in (None, "   "):
                    with self.assertRaises(StateError):
                        quality_state.transition(state_at(source), target, reason)

                result = quality_state.transition(
                    state_at(source),
                    target,
                    "operator supplied reason",
                )
                self.assertEqual(target, result["stage"])
                self.assertEqual("operator supplied reason", result["status_reason"])

    def test_completed_requires_verification_tied_to_the_reviewed_code_digest(self):
        """The verified workspace fingerprint must match the digest of the
        code that was actually reviewed, not merely be present and valid."""
        state = state_at("CODE_REVIEW")
        state["rounds"]["code"] = 1
        state["reviews"]["code"] = [
            {
                "verdict": "PASS",
                "blockers": [],
                "artifact_digest": "a" * 64,
            }
        ]
        state["open_finding_ids"]["code"] = []
        state["verification"] = {
            "path": "verification.json",
            "workspace_fingerprint": "b" * 64,
            "valid": True,
        }
        before = deepcopy(state)

        with self.assertRaises(quality_state.TransitionError):
            quality_state.transition(state, "COMPLETED")

        self.assertEqual(before, state)

    def test_completed_accepts_verification_matching_the_reviewed_code_digest(self):
        state = state_at("CODE_REVIEW")
        state["rounds"]["code"] = 1
        state["reviews"]["code"] = [
            {
                "verdict": "PASS",
                "blockers": [],
                "artifact_digest": "c" * 64,
            }
        ]
        state["open_finding_ids"]["code"] = []
        state["verification"] = {
            "path": "verification.json",
            "workspace_fingerprint": "c" * 64,
            "valid": True,
        }

        result = quality_state.transition(state, "COMPLETED")

        self.assertEqual("COMPLETED", result["stage"])

    def test_classified_transition_targets_require_the_matching_mode(self):
        for mode, target in (("strict", "AWAITING_PLAN_APPROVAL"), ("light", "SPEC_REVIEW")):
            with self.subTest(mode=mode, target=target):
                state = state_at("CLASSIFIED", mode=mode)
                before = deepcopy(state)

                with self.assertRaises(quality_state.TransitionError):
                    quality_state.transition(state, target)

                self.assertEqual(before, state)

    def test_code_review_completion_requires_all_quality_gates(self):
        cases = (
            {"rounds": {"code": 0}},
            {
                "rounds": {"code": 1},
                "reviews": {"code": [{"verdict": "REVISE", "blockers": []}]},
                "open_finding_ids": {"code": []},
                "verification": {"valid": True},
            },
            {
                "rounds": {"code": 1},
                "reviews": {"code": [{"verdict": "PASS", "blockers": []}]},
                "open_finding_ids": {"code": ["CODE-1"]},
                "verification": {"valid": True},
            },
            {
                "rounds": {"code": 1},
                "reviews": {"code": [{"verdict": "PASS", "blockers": []}]},
                "open_finding_ids": {"code": []},
                "verification": {"valid": False},
            },
        )
        for overrides in cases:
            with self.subTest(overrides=overrides):
                state = state_at("CODE_REVIEW")
                for key, value in overrides.items():
                    state[key].update(value)
                before = deepcopy(state)

                with self.assertRaises(quality_state.TransitionError):
                    quality_state.transition(state, "COMPLETED")

                self.assertEqual(before, state)


class ArtifactTests(unittest.TestCase):
    def test_set_artifact_records_each_supported_existing_regular_file(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            state = state_at("INTAKE", mode=None)

            for kind in ("spec", "plan", "compact_plan", "report"):
                path = directory / f"{kind}.md"
                path.write_text(f"{kind}\n", encoding="utf-8")

                result = quality_state.set_artifact(state, kind, path)

                self.assertIs(result, state)
                self.assertEqual(str(path), result["artifacts"][kind])

    def test_set_artifact_rejects_unknown_or_nonregular_paths_without_mutating(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            existing = directory / "existing.md"
            existing.write_text("artifact\n", encoding="utf-8")
            directory_path = directory / "artifact-directory"
            directory_path.mkdir()

            for kind, path in (
                ("unknown", existing),
                ("spec", directory / "missing.md"),
                ("spec", directory_path),
            ):
                state = state_at("CLASSIFIED")
                before = deepcopy(state)

                with self.assertRaises(StateError):
                    quality_state.set_artifact(state, kind, path)

                self.assertEqual(before, state)


class PlanApprovalGuardTests(unittest.TestCase):
    def test_approve_plan_rejects_content_changed_since_the_passing_review(self):
        """A Plan edited after PLAN_PASSED but before approval, at the same
        path, must not be silently approved with its new content."""
        with tempfile.TemporaryDirectory() as directory:
            plan_path = Path(directory) / "plan.md"
            plan_path.write_text("reviewed plan\n", encoding="utf-8")
            state = state_at("AWAITING_PLAN_APPROVAL", mode="standard")
            state["artifacts"]["plan"] = str(plan_path)
            state["artifact_digests"]["plan"] = quality_state._file_digest(plan_path)
            plan_path.write_text("tampered after review, never reviewed\n", encoding="utf-8")

            with self.assertRaises(StateError):
                quality_state.approve_plan(state, plan_path, "2026-08-25T12:00:00Z")

            self.assertIsNone(state["plan_approval"])

    def test_approve_plan_rejects_when_no_review_digest_was_recorded(self):
        with tempfile.TemporaryDirectory() as directory:
            plan_path = Path(directory) / "plan.md"
            plan_path.write_text("plan\n", encoding="utf-8")
            state = state_at("AWAITING_PLAN_APPROVAL", mode="standard")
            state["artifacts"]["plan"] = str(plan_path)
            self.assertIsNone(state["artifact_digests"]["plan"])

            with self.assertRaises(StateError):
                quality_state.approve_plan(state, plan_path, "2026-08-25T12:00:00Z")

            self.assertIsNone(state["plan_approval"])

    def test_approve_plan_accepts_content_matching_the_passing_review(self):
        with tempfile.TemporaryDirectory() as directory:
            plan_path = Path(directory) / "plan.md"
            plan_path.write_text("reviewed plan\n", encoding="utf-8")
            state = state_at("AWAITING_PLAN_APPROVAL", mode="standard")
            state["artifacts"]["plan"] = str(plan_path)
            state["artifact_digests"]["plan"] = quality_state._file_digest(plan_path)

            result = quality_state.approve_plan(state, plan_path, "2026-08-25T12:00:00Z")

            self.assertEqual(
                quality_state._file_digest(plan_path),
                result["plan_approval"]["digest"],
            )

    def test_light_compact_plan_approval_needs_no_review_digest(self):
        """Light never reviews its compact Plan, so approval has no reviewed
        digest to compare against."""
        with tempfile.TemporaryDirectory() as directory:
            compact_plan = Path(directory) / "compact-plan.md"
            compact_plan.write_text("compact plan\n", encoding="utf-8")
            state = state_at("AWAITING_PLAN_APPROVAL", mode="light")
            state["artifacts"]["compact_plan"] = str(compact_plan)
            self.assertIsNone(state["artifact_digests"]["compact_plan"])

            result = quality_state.approve_plan(state, compact_plan, "2026-08-25T12:00:00Z")

            self.assertIsNotNone(result["plan_approval"])

    def test_approval_must_target_the_current_mode_appropriate_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            plan_path = directory / "plan.md"
            readme_path = directory / "README.md"
            plan_path.write_text("plan\n", encoding="utf-8")
            readme_path.write_text("readme\n", encoding="utf-8")
            state = state_at("AWAITING_PLAN_APPROVAL", mode="standard")
            state["artifacts"]["plan"] = str(plan_path)

            with self.assertRaises(StateError):
                quality_state.approve_plan(
                    state,
                    readme_path,
                    "2026-08-25T12:00:00Z",
                )

            self.assertIsNone(state["plan_approval"])

    def test_repointing_the_current_plan_artifact_is_a_path_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            original = directory / "plan.md"
            replacement = directory / "replacement-plan.md"
            original.write_text("plan\n", encoding="utf-8")
            replacement.write_text("replacement\n", encoding="utf-8")
            state = state_at("AWAITING_PLAN_APPROVAL", mode="standard")
            state["artifacts"]["plan"] = str(original)
            state["artifact_digests"]["plan"] = quality_state._file_digest(original)
            quality_state.approve_plan(state, original, "2026-08-25T12:00:00Z")
            state["stage"] = "CODE_REVIEW"
            state["artifacts"]["plan"] = str(replacement)
            state["verification"]["valid"] = True

            with self.assertRaises(quality_state.ApprovalMismatchError) as context:
                quality_state.transition(state, "IMPLEMENTING")

            self.assertIsInstance(context.exception, quality_state.TransitionError)
            self.assertIsInstance(context.exception, StateError)
            self.assertIn("mismatch", str(context.exception).lower())
            self.assertIsNone(state["plan_approval"])
            self.assertFalse(state["verification"]["valid"])
            self.assertEqual("PLAN_REVIEW", state["stage"])

    def test_missing_approved_plan_is_a_digest_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            plan_path = Path(directory) / "plan.md"
            plan_path.write_text("plan\n", encoding="utf-8")
            state = state_at("AWAITING_PLAN_APPROVAL", mode="standard")
            state["artifacts"]["plan"] = str(plan_path)
            state["artifact_digests"]["plan"] = quality_state._file_digest(plan_path)
            quality_state.approve_plan(state, plan_path, "2026-08-25T12:00:00Z")
            state["verification"]["valid"] = True
            plan_path.unlink()

            with self.assertRaises(quality_state.ApprovalMismatchError) as context:
                quality_state.transition(state, "IMPLEMENTING")

            self.assertIsInstance(context.exception, quality_state.TransitionError)
            self.assertIsInstance(context.exception, StateError)
            message = str(context.exception).lower()
            self.assertIn("digest", message)
            self.assertTrue("mismatch" in message or "missing" in message)
            self.assertIsNone(state["plan_approval"])
            self.assertFalse(state["verification"]["valid"])
            self.assertEqual("PLAN_REVIEW", state["stage"])

    def test_approve_plan_rejects_invalid_timestamp(self):
        with tempfile.TemporaryDirectory() as directory:
            plan_path = Path(directory) / "plan.md"
            plan_path.write_text("plan\n", encoding="utf-8")
            state = state_at("AWAITING_PLAN_APPROVAL", mode="standard")
            state["artifacts"]["plan"] = str(plan_path)

            for approved_at in ("2026-08-25", "2026-8-25T12:00:00Z", None):
                with self.subTest(approved_at=approved_at):
                    with self.assertRaises(StateError):
                        quality_state.approve_plan(state, plan_path, approved_at)

    def test_standard_and_strict_modes_require_a_plan_approval(self):
        for mode in ("standard", "strict"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                plan_path = Path(directory) / "plan.md"
                plan_path.write_text("plan\n", encoding="utf-8")
                state = state_at("AWAITING_PLAN_APPROVAL", mode=mode)
                state["artifacts"]["plan"] = str(plan_path)

                with self.assertRaises(StateError):
                    quality_state.transition(state, "IMPLEMENTING")

    def test_recorded_current_plan_approval_allows_implementing(self):
        with tempfile.TemporaryDirectory() as directory:
            plan_path = Path(directory) / "plan.md"
            plan_path.write_text("approved plan\n", encoding="utf-8")
            state = state_at("AWAITING_PLAN_APPROVAL", mode="standard")
            state["artifacts"]["plan"] = str(plan_path)
            state["artifact_digests"]["plan"] = quality_state._file_digest(plan_path)

            result = quality_state.approve_plan(
                state,
                plan_path,
                "2026-08-25T12:00:00Z",
            )
            transitioned = quality_state.transition(result, "IMPLEMENTING")

            self.assertEqual("IMPLEMENTING", transitioned["stage"])
            self.assertEqual(
                hashlib.sha256(plan_path.read_bytes()).hexdigest(),
                transitioned["plan_approval"]["digest"],
            )

    def test_code_review_reentry_to_implementing_requires_current_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            plan_path = Path(directory) / "plan.md"
            plan_path.write_text("plan\n", encoding="utf-8")
            state = state_at("CODE_REVIEW", mode="standard")
            state["artifacts"]["plan"] = str(plan_path)

            with self.assertRaises(StateError):
                quality_state.transition(state, "IMPLEMENTING")

    def test_approve_plan_is_rejected_at_code_review(self):
        with tempfile.TemporaryDirectory() as directory:
            plan_path = Path(directory) / "plan.md"
            plan_path.write_text("plan\n", encoding="utf-8")
            state = state_at("CODE_REVIEW", mode="standard")
            state["artifacts"]["plan"] = str(plan_path)

            with self.assertRaises(StateError):
                quality_state.approve_plan(state, plan_path, "2026-08-25T12:00:00Z")

    def test_stale_plan_digest_blocks_the_fix_loop_reentry(self):
        with tempfile.TemporaryDirectory() as directory:
            plan_path = Path(directory) / "plan.md"
            plan_path.write_text("approved plan\n", encoding="utf-8")
            state = state_at("CODE_REVIEW", mode="standard")
            state["artifacts"]["plan"] = str(plan_path)
            state["artifact_digests"]["plan"] = quality_state._file_digest(plan_path)
            state["stage"] = "AWAITING_PLAN_APPROVAL"
            quality_state.approve_plan(state, plan_path, "2026-08-25T12:00:00Z")
            state["stage"] = "CODE_REVIEW"
            state["verification"]["valid"] = True
            plan_path.write_text("modified after approval\n", encoding="utf-8")

            with self.assertRaises(StateError):
                quality_state.transition(state, "IMPLEMENTING")

            self.assertIsNone(state["plan_approval"])
            self.assertFalse(state["verification"]["valid"])
            self.assertEqual("PLAN_REVIEW", state["stage"])

    def test_changed_plan_digest_clears_approval_invalidates_verification_and_returns_to_review(self):
        with tempfile.TemporaryDirectory() as directory:
            plan_path = Path(directory) / "plan.md"
            plan_path.write_text("approved plan\n", encoding="utf-8")
            state = state_at("AWAITING_PLAN_APPROVAL", mode="standard")
            state["artifacts"]["plan"] = str(plan_path)
            state["artifact_digests"]["plan"] = quality_state._file_digest(plan_path)
            quality_state.approve_plan(state, plan_path, "2026-08-25T12:00:00Z")
            state["verification"]["valid"] = True
            state["verification"]["workspace_fingerprint"] = OLD_FINGERPRINT
            plan_path.write_text("modified after approval\n", encoding="utf-8")

            with self.assertRaises(quality_state.ApprovalMismatchError) as context:
                quality_state.transition(state, "IMPLEMENTING")

            self.assertIsInstance(context.exception, quality_state.TransitionError)
            self.assertIsInstance(context.exception, StateError)
            self.assertIn("digest", str(context.exception).lower())
            self.assertIn("mismatch", str(context.exception).lower())
            self.assertIsNone(state["plan_approval"])
            self.assertFalse(state["verification"]["valid"])
            self.assertEqual("PLAN_REVIEW", state["stage"])

    def test_light_mode_requires_and_accepts_compact_plan_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            compact_plan = Path(directory) / "compact-plan.md"
            compact_plan.write_text("compact plan\n", encoding="utf-8")

            missing = state_at("AWAITING_PLAN_APPROVAL", mode="light")
            missing["artifacts"]["compact_plan"] = str(compact_plan)
            with self.assertRaises(StateError):
                quality_state.transition(missing, "IMPLEMENTING")

            approved = state_at("AWAITING_PLAN_APPROVAL", mode="light")
            approved["artifacts"]["compact_plan"] = str(compact_plan)
            quality_state.approve_plan(approved, compact_plan, "2026-08-25T12:00:00Z")

            self.assertEqual("IMPLEMENTING", quality_state.transition(approved, "IMPLEMENTING")["stage"])

    def test_changed_compact_plan_digest_returns_light_mode_to_classified(self):
        with tempfile.TemporaryDirectory() as directory:
            compact_plan = Path(directory) / "compact-plan.md"
            compact_plan.write_text("approved compact plan\n", encoding="utf-8")
            state = state_at("AWAITING_PLAN_APPROVAL", mode="light")
            state["artifacts"]["compact_plan"] = str(compact_plan)
            quality_state.approve_plan(state, compact_plan, "2026-08-25T12:00:00Z")
            state["verification"]["valid"] = True
            compact_plan.write_text("changed compact plan\n", encoding="utf-8")

            with self.assertRaises(quality_state.ApprovalMismatchError) as context:
                quality_state.transition(state, "IMPLEMENTING")

            self.assertIsInstance(context.exception, quality_state.TransitionError)
            self.assertIsInstance(context.exception, StateError)
            self.assertIn("digest", str(context.exception).lower())
            self.assertIn("mismatch", str(context.exception).lower())
            self.assertIsNone(state["plan_approval"])
            self.assertFalse(state["verification"]["valid"])
            self.assertEqual("CLASSIFIED", state["stage"])


class RecordReviewTests(unittest.TestCase):
    def test_artifact_digest_must_be_a_lowercase_sha256_hex_digest(self):
        with tempfile.TemporaryDirectory() as directory:
            review_path = write_json(directory, "plan-review.json", valid_review())

            for digest in ("digest", "A" * 64, "a" * 63, None):
                with self.subTest(digest=digest):
                    with self.assertRaises(StateError):
                        quality_state.record_review(
                            state_at("PLAN_REVIEW"),
                            review_path,
                            digest,
                        )

    def test_artifact_digest_must_match_the_current_plan_file_when_recorded(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            plan_path = directory / "plan.md"
            plan_path.write_text("plan\n", encoding="utf-8")
            review_path = write_json(directory, "plan-review.json", valid_review())
            state = state_at("PLAN_REVIEW")
            state["artifacts"]["plan"] = str(plan_path)

            with self.assertRaises(StateError):
                quality_state.record_review(state, review_path, VALID_DIGEST)

            self.assertEqual(0, state["rounds"]["plan"])

    def test_record_review_after_stale_verification_invalidation_is_allowed(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            review_path = write_json(directory, "plan-review.json", valid_review())
            verification_path = directory / "verification.json"
            verification_path.write_text("verification\n", encoding="utf-8")
            state = state_at("CODE_REVIEW")
            quality_state.record_verification(
                state,
                verification_path,
                OLD_FINGERPRINT,
            )
            quality_state.invalidate_stale_verification(state, NEW_FINGERPRINT)
            state["stage"] = "PLAN_REVIEW"

            result = quality_state.record_review(state, review_path, VALID_DIGEST)

            self.assertEqual(1, result["rounds"]["plan"])

    def test_valid_plan_review_increments_only_plan_and_records_blockers_and_digest(self):
        with tempfile.TemporaryDirectory() as directory:
            state = state_at("PLAN_REVIEW")
            review_path = write_json(directory, "plan-review.json", valid_review())
            digest = hashlib.sha256(b"plan-artifact").hexdigest()

            result = quality_state.record_review(state, review_path, digest)

            self.assertEqual(0, result["rounds"]["spec"])
            self.assertEqual(1, result["rounds"]["plan"])
            self.assertEqual(0, result["rounds"]["code"])
            self.assertEqual(
                {
                    "round": 1,
                    "path": str(review_path),
                    "artifact_digest": digest,
                    "verdict": "PASS",
                    "blockers": [],
                },
                result["reviews"]["plan"][0],
            )
            self.assertEqual([], result["open_finding_ids"]["plan"])
            self.assertEqual(digest, result["artifact_digests"]["plan"])
            self.assertIsNone(result["review_validation_retry"])

    def test_review_artifact_or_stage_mismatch_raises_state_error(self):
        with tempfile.TemporaryDirectory() as directory:
            wrong_artifact = write_json(
                directory,
                "wrong-artifact.json",
                valid_review(artifact="spec"),
            )
            state = state_at("PLAN_REVIEW")
            with self.assertRaises(StateError):
                quality_state.record_review(state, wrong_artifact, VALID_DIGEST)

            wrong_stage = write_json(
                directory,
                "wrong-stage.json",
                valid_review(artifact="plan"),
            )
            state = state_at("SPEC_REVIEW")
            with self.assertRaises(StateError):
                quality_state.record_review(state, wrong_stage, VALID_DIGEST)

    def test_review_round_must_be_next_round(self):
        with tempfile.TemporaryDirectory() as directory:
            review_path = write_json(
                directory,
                "round-two.json",
                valid_review(round_number=2),
            )
            state = state_at("PLAN_REVIEW")

            with self.assertRaises(StateError):
                quality_state.record_review(state, review_path, VALID_DIGEST)

            self.assertEqual(0, state["rounds"]["plan"])

    def test_schema_invalid_review_json_raises_state_error(self):
        with tempfile.TemporaryDirectory() as directory:
            review_path = write_json(directory, "invalid.json", {"artifact": "plan"})

            with self.assertRaises(StateError):
                quality_state.record_review(state_at("PLAN_REVIEW"), review_path, VALID_DIGEST)


class RoundLimitTests(unittest.TestCase):
    def test_plan_round_three_is_rejected_after_two_recorded_rounds(self):
        with tempfile.TemporaryDirectory() as directory:
            state = state_at("PLAN_REVIEW")
            for round_number in (1, 2):
                review_path = write_json(
                    directory,
                    f"plan-{round_number}.json",
                    valid_review(artifact="plan", round_number=round_number),
                )
                quality_state.record_review(state, review_path, VALID_DIGEST)

            round_three = write_json(
                directory,
                "plan-3.json",
                valid_review(artifact="plan", round_number=3),
            )
            with self.assertRaises(StateError):
                quality_state.record_review(state, round_three, VALID_DIGEST)
            self.assertEqual(2, state["rounds"]["plan"])

    def test_spec_round_four_is_rejected_after_three_recorded_rounds(self):
        with tempfile.TemporaryDirectory() as directory:
            state = state_at("SPEC_REVIEW")
            for round_number in (1, 2, 3):
                review_path = write_json(
                    directory,
                    f"spec-{round_number}.json",
                    valid_review(artifact="spec", round_number=round_number),
                )
                quality_state.record_review(state, review_path, VALID_DIGEST)

            round_four = write_json(
                directory,
                "spec-4.json",
                valid_review(artifact="spec", round_number=4),
            )
            with self.assertRaises(StateError):
                quality_state.record_review(state, round_four, VALID_DIGEST)
            self.assertEqual(3, state["rounds"]["spec"])

    def test_code_round_four_is_rejected_after_three_recorded_rounds(self):
        with tempfile.TemporaryDirectory() as directory:
            state = state_at("CODE_REVIEW")
            for round_number in (1, 2, 3):
                review_path = write_json(
                    directory,
                    f"code-{round_number}.json",
                    valid_review(artifact="code", round_number=round_number),
                )
                quality_state.record_review(state, review_path, VALID_DIGEST)

            round_four = write_json(
                directory,
                "code-4.json",
                valid_review(artifact="code", round_number=4),
            )
            with self.assertRaises(StateError):
                quality_state.record_review(state, round_four, VALID_DIGEST)
            self.assertEqual(3, state["rounds"]["code"])

    def test_nonpassing_final_spec_round_enters_needs_redesign(self):
        """Rounds 1-2 are REVISE with no blockers so neither the recurring-
        blocker branch nor a premature limit fires before round 3, the
        actual final spec round under the 3-round limit."""
        with tempfile.TemporaryDirectory() as directory:
            state = state_at("SPEC_REVIEW")
            for round_number in (1, 2):
                review_path = write_json(
                    directory,
                    f"spec-{round_number}.json",
                    valid_review(
                        artifact="spec",
                        round_number=round_number,
                        verdict="REVISE",
                    ),
                )
                quality_state.record_review(state, review_path, VALID_DIGEST)
            final = write_json(
                directory,
                "spec-3.json",
                valid_review(
                    artifact="spec",
                    round_number=3,
                    verdict="REVISE",
                    blockers=["SPEC-LIMIT-001"],
                ),
            )

            result = quality_state.record_review(state, final, VALID_DIGEST)

            self.assertEqual("NEEDS_REDESIGN", result["stage"])
            self.assertTrue(result["status_reason"].startswith("REVIEW_LIMIT_EXHAUSTED"))

    def test_nonpassing_code_round_three_enters_needs_redesign_without_round_four(self):
        with tempfile.TemporaryDirectory() as directory:
            state = state_at("CODE_REVIEW")
            for round_number in (1, 2):
                review_path = write_json(
                    directory,
                    f"code-{round_number}.json",
                    valid_review(artifact="code", round_number=round_number),
                )
                quality_state.record_review(state, review_path, VALID_DIGEST)

            third = write_json(
                directory,
                "code-3.json",
                valid_review(
                    artifact="code",
                    round_number=3,
                    verdict="REVISE",
                    blockers=["CODE-LIMIT-001"],
                ),
            )

            result = quality_state.record_review(state, third, VALID_DIGEST)

            self.assertEqual("NEEDS_REDESIGN", result["stage"])
            self.assertTrue(result["status_reason"].startswith("REVIEW_LIMIT_EXHAUSTED"))
            self.assertEqual(3, result["rounds"]["code"])

            fourth = write_json(
                directory,
                "code-4.json",
                valid_review(artifact="code", round_number=4),
            )
            with self.assertRaises(StateError) as context:
                quality_state.record_review(state, fourth, VALID_DIGEST)
            self.assertIn("requires stage CODE_REVIEW", str(context.exception))
            self.assertEqual(3, state["rounds"]["code"])


class RecurringBlockerTests(unittest.TestCase):
    def test_repeated_stable_blocker_enters_needs_redesign_with_the_finding_id(self):
        with tempfile.TemporaryDirectory() as directory:
            state = state_at("PLAN_REVIEW")
            first = write_json(
                directory,
                "plan-1.json",
                valid_review(
                    artifact="plan",
                    verdict="REVISE",
                    blockers=["PLAN-X"],
                ),
            )
            quality_state.record_review(state, first, VALID_DIGEST)
            second = write_json(
                directory,
                "plan-2.json",
                valid_review(
                    artifact="plan",
                    round_number=2,
                    verdict="REVISE",
                    blockers=["PLAN-X"],
                ),
            )

            result = quality_state.record_review(state, second, VALID_DIGEST)

            self.assertEqual("NEEDS_REDESIGN", result["stage"])
            self.assertIn("PLAN-X", result["status_reason"])


class ReviewValidationRetryTests(unittest.TestCase):
    def test_review_validation_failure_requires_valid_artifact_stage_round_and_errors(self):
        invalid_cases = (
            ("unknown", 1, ["error"]),
            ("plan", True, ["error"]),
            ("plan", 0, ["error"]),
            ("plan", 3, ["error"]),
            ("plan", 1, []),
            ("plan", 1, [""]),
            ("plan", 1, ["error", 3]),
        )
        for artifact, round_number, errors in invalid_cases:
            with self.subTest(artifact=artifact, round_number=round_number, errors=errors):
                with self.assertRaises(StateError):
                    quality_state.record_review_validation_failure(
                        state_at("PLAN_REVIEW"),
                        artifact,
                        round_number,
                        errors,
                    )

        with self.assertRaises(StateError):
            quality_state.record_review_validation_failure(
                state_at("SPEC_REVIEW"),
                "plan",
                1,
                ["error"],
            )

    def test_terminal_states_are_immutable_for_active_only_mutators(self):
        for terminal in quality_state.TERMINAL_STATES:
            with self.subTest(terminal=terminal):
                operations = (
                    lambda state: quality_state.record_review_validation_failure(
                        state, "plan", 1, ["error"]
                    ),
                    lambda state: quality_state.record_verification(
                        state, "verification.json", VALID_FINGERPRINT
                    ),
                    lambda state: quality_state.invalidate_stale_verification(
                        state, VALID_FINGERPRINT
                    ),
                    lambda state: quality_state.set_artifact(
                        state, "spec", "missing-artifact.md"
                    ),
                )
                for operation in operations:
                    state = state_at(terminal)
                    before = deepcopy(state)
                    with self.assertRaises(quality_state.TransitionError):
                        operation(state)
                    self.assertEqual(before, state)

    def test_record_verification_is_only_allowed_during_implementation_or_code_review(self):
        state = state_at("INTAKE")
        before = deepcopy(state)

        with self.assertRaises(StateError):
            quality_state.record_verification(
                state, "verification.json", VALID_FINGERPRINT
            )

        self.assertEqual(before, state)

    def test_first_review_validation_failure_is_recorded_and_leaves_stage_unchanged(self):
        state = state_at("PLAN_REVIEW")

        result = quality_state.record_review_validation_failure(
            state,
            "plan",
            1,
            ["missing required field: evidence"],
        )

        self.assertEqual("PLAN_REVIEW", result["stage"])
        self.assertEqual(
            {
                "artifact": "plan",
                "round": 1,
                "attempts": 1,
                "errors": ["missing required field: evidence"],
            },
            result["review_validation_retry"],
        )

    def test_second_failure_for_the_same_review_blocks_the_state(self):
        state = state_at("PLAN_REVIEW")
        quality_state.record_review_validation_failure(state, "plan", 1, ["first"])

        result = quality_state.record_review_validation_failure(
            state,
            "plan",
            1,
            ["second"],
        )

        self.assertEqual(2, result["review_validation_retry"]["attempts"])
        self.assertEqual("BLOCKED", result["stage"])
        self.assertEqual("REVIEW_OUTPUT_INVALID", result["status_reason"])

    def test_malformed_review_json_is_rejected_and_retry_blocks_at_exactly_two_attempts(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            review_path = directory / "malformed-review.json"
            review_path.write_text("{", encoding="utf-8")
            state = state_at("PLAN_REVIEW")

            for expected_attempts in (1, 2):
                with self.assertRaises(StateError) as context:
                    quality_state.record_review(state, review_path, VALID_DIGEST)
                self.assertIn("unable to load review", str(context.exception))

                quality_state.record_review_validation_failure(
                    state,
                    "plan",
                    1,
                    ["review JSON is malformed"],
                )
                self.assertEqual(
                    expected_attempts,
                    state["review_validation_retry"]["attempts"],
                )

            self.assertEqual("BLOCKED", state["stage"])
            self.assertEqual(2, state["review_validation_retry"]["attempts"])

    def test_valid_review_after_one_failure_clears_the_retry_record(self):
        with tempfile.TemporaryDirectory() as directory:
            state = state_at("PLAN_REVIEW")
            quality_state.record_review_validation_failure(state, "plan", 1, ["retry once"])
            review_path = write_json(directory, "valid-plan.json", valid_review())

            result = quality_state.record_review(state, review_path, VALID_DIGEST)

            self.assertIsNone(result["review_validation_retry"])
            self.assertEqual(1, result["rounds"]["plan"])


class FingerprintTests(unittest.TestCase):
    def test_unignored_state_files_do_not_change_fingerprint_but_normal_untracked_files_do(self):
        root = make_git_repo(self)
        baseline = quality_state.compute_workspace_fingerprint(root)
        state_path = root / ".claude" / "quality-state" / "state.json"
        state_path.parent.mkdir(parents=True)

        state_path.write_text('{"version": 1}\n', encoding="utf-8")
        after_state_write = quality_state.compute_workspace_fingerprint(root)
        state_path.write_text('{"version": 2}\n', encoding="utf-8")
        after_state_modification = quality_state.compute_workspace_fingerprint(root)

        normal_path = root / "normal-untracked.txt"
        normal_path.write_text("one\n", encoding="utf-8")
        after_normal_write = quality_state.compute_workspace_fingerprint(root)
        normal_path.write_text("two\n", encoding="utf-8")
        after_normal_modification = quality_state.compute_workspace_fingerprint(root)

        self.assertEqual(baseline, after_state_write)
        self.assertEqual(baseline, after_state_modification)
        self.assertNotEqual(baseline, after_normal_write)
        self.assertNotEqual(after_normal_write, after_normal_modification)

    def test_state_files_are_excluded_when_git_reports_the_untracked_claude_directory(self):
        root = make_git_repo(self)
        claude_root = root / ".claude"
        claude_root.mkdir()
        run_git(claude_root, "init")
        state_path = root / ".claude" / "quality-state" / "state.json"
        state_path.parent.mkdir(parents=True)

        self.assertEqual(
            ".claude/\0",
            run_git(root, "ls-files", "--others", "--exclude-standard", "-z").stdout,
        )
        baseline = quality_state.compute_workspace_fingerprint(root)

        state_path.write_text('{"version": 1}\n', encoding="utf-8")
        after_state_write = quality_state.compute_workspace_fingerprint(root)
        state_path.write_text('{"version": 2}\n', encoding="utf-8")
        after_state_modification = quality_state.compute_workspace_fingerprint(root)

        normal_path = root / ".claude" / "normal-untracked.txt"
        normal_path.write_text("one\n", encoding="utf-8")
        after_normal_write = quality_state.compute_workspace_fingerprint(root)
        normal_path.write_text("two\n", encoding="utf-8")
        after_normal_modification = quality_state.compute_workspace_fingerprint(root)

        self.assertEqual(baseline, after_state_write)
        self.assertEqual(baseline, after_state_modification)
        self.assertNotEqual(baseline, after_normal_write)
        self.assertNotEqual(after_normal_write, after_normal_modification)

    def test_tracked_state_files_are_excluded_from_unstaged_and_staged_diffs(self):
        root = make_git_repo(self)
        state_path = root / ".claude" / "quality-state" / "state.json"
        state_path.parent.mkdir(parents=True)
        state_path.write_text('{"version": 1}\n', encoding="utf-8")
        tracked_non_state_path = root / ".claude" / "tracked-non-state.txt"
        tracked_non_state_path.write_text("base\n", encoding="utf-8")
        run_git(
            root,
            "add",
            ".claude/quality-state/state.json",
            ".claude/tracked-non-state.txt",
        )
        run_git(root, "commit", "-m", "track workflow state")
        baseline = quality_state.compute_workspace_fingerprint(root)

        state_path.write_text('{"version": 2}\n', encoding="utf-8")
        unstaged_state = quality_state.compute_workspace_fingerprint(root)
        run_git(root, "add", ".claude/quality-state/state.json")
        staged_state = quality_state.compute_workspace_fingerprint(root)

        tracked_non_state_path.write_text("changed\n", encoding="utf-8")
        unstaged_non_state = quality_state.compute_workspace_fingerprint(root)
        run_git(root, "add", ".claude/tracked-non-state.txt")
        staged_non_state = quality_state.compute_workspace_fingerprint(root)

        self.assertEqual(baseline, unstaged_state)
        self.assertEqual(baseline, staged_state)
        self.assertNotEqual(baseline, unstaged_non_state)
        self.assertNotEqual(baseline, staged_non_state)

    def test_nested_git_repository_contents_are_hashed_without_following_outside_links(self):
        root = make_git_repo(self)
        inner = root / "nested-repository"
        inner.mkdir()
        run_git(inner, "init")
        run_git(inner, "config", "user.name", "quality-goal-test")
        run_git(inner, "config", "user.email", "quality-goal-test@example.invalid")
        nested_file = inner / "nested.txt"
        nested_file.write_text("one\n", encoding="utf-8")
        run_git(inner, "add", "nested.txt")
        run_git(inner, "commit", "-m", "nested fixture")

        before = quality_state.compute_workspace_fingerprint(root)
        nested_file.write_text("two\n", encoding="utf-8")
        after = quality_state.compute_workspace_fingerprint(root)

        self.assertNotEqual(before, after)

    def test_untracked_existing_and_broken_symlinks_are_hashed_without_reading_targets(self):
        root = make_git_repo(self)
        first_target = root / "first.txt"
        second_target = root / "second.txt"
        first_target.write_text("first\n", encoding="utf-8")
        second_target.write_text("second\n", encoding="utf-8")
        link = root / "link.txt"
        broken = root / "broken.txt"
        link.symlink_to(first_target.name)
        broken.symlink_to("missing-target.txt")

        before = quality_state.compute_workspace_fingerprint(root)
        link.unlink()
        link.symlink_to(second_target.name)
        after = quality_state.compute_workspace_fingerprint(root)

        self.assertNotEqual(before, after)

    def test_untracked_path_framing_distinguishes_foo_bar_from_foob_ar(self):
        root = make_git_repo(self)
        first = root / "foo"
        first.write_text("bar", encoding="utf-8")
        before = quality_state.compute_workspace_fingerprint(root)
        first.rename(root / "foob")
        (root / "foob").write_text("ar", encoding="utf-8")
        after = quality_state.compute_workspace_fingerprint(root)

        self.assertNotEqual(before, after)

    def test_unchanged_git_repository_has_a_deterministic_fingerprint(self):
        root = make_git_repo(self)

        self.assertEqual(
            quality_state.compute_workspace_fingerprint(root),
            quality_state.compute_workspace_fingerprint(root),
        )

    def test_tracked_edits_and_staging_change_the_fingerprint(self):
        root = make_git_repo(self)
        baseline = quality_state.compute_workspace_fingerprint(root)

        (root / "app.txt").write_text("edited\n", encoding="utf-8")
        unstaged = quality_state.compute_workspace_fingerprint(root)
        run_git(root, "add", "app.txt")
        staged = quality_state.compute_workspace_fingerprint(root)

        self.assertNotEqual(baseline, unstaged)
        self.assertNotEqual(unstaged, staged)
        self.assertNotEqual(baseline, staged)

    def test_untracked_addition_and_modification_change_and_reverting_restores_fingerprint(self):
        root = make_git_repo(self)
        baseline = quality_state.compute_workspace_fingerprint(root)
        untracked = root / "new.txt"

        untracked.write_text("one\n", encoding="utf-8")
        added = quality_state.compute_workspace_fingerprint(root)
        untracked.write_text("two\n", encoding="utf-8")
        modified = quality_state.compute_workspace_fingerprint(root)
        untracked.unlink()

        self.assertNotEqual(baseline, added)
        self.assertNotEqual(added, modified)
        self.assertEqual(baseline, quality_state.compute_workspace_fingerprint(root))

    def test_non_git_directory_raises_a_blocked_not_git_state_error(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(StateError) as context:
                quality_state.compute_workspace_fingerprint(Path(directory))

        self.assertTrue(str(context.exception).startswith("BLOCKED_NOT_GIT:"))

    def test_empty_git_repository_reports_that_it_has_no_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_git(root, "init")

            with self.assertRaises(quality_state.GitError) as context:
                quality_state.compute_workspace_fingerprint(root)

        self.assertTrue(str(context.exception).startswith("BLOCKED_NOT_GIT:"))
        self.assertIn("no commit", str(context.exception).lower())


class BaselineTests(unittest.TestCase):
    def test_capture_workspace_baseline_records_head_and_clean_paths(self):
        root = make_git_repo(self)
        state = state_at("INTAKE", project_root=root)

        result = quality_state.capture_workspace_baseline(state)

        expected_head = run_git(root, "rev-parse", "HEAD").stdout.strip()
        self.assertEqual(expected_head, result["base_revision"])
        self.assertEqual([], result["initial_dirty_paths"])

    def test_capture_workspace_baseline_records_tracked_and_untracked_dirty_paths(self):
        root = make_git_repo(self)
        (root / "app.txt").write_text("edited\n", encoding="utf-8")
        (root / "new.txt").write_text("new\n", encoding="utf-8")
        state = state_at("CLASSIFIED", project_root=root)

        result = quality_state.capture_workspace_baseline(state)

        self.assertEqual(["app.txt", "new.txt"], result["initial_dirty_paths"])

    def test_capture_baseline_preserves_initial_dirty_file_bytes_after_task_file_changes(self):
        root = make_git_repo(self)
        dirty_file = root / "app.txt"
        pre_task_bytes = b"user's local edit\n"
        dirty_file.write_bytes(pre_task_bytes)
        state = state_at("INTAKE", project_root=root)

        quality_state.capture_workspace_baseline(state)

        task_file = root / "task-output.txt"
        task_file.write_bytes(b"generated once\n")
        task_file.write_bytes(b"generated twice\n")
        quality_state.compute_workspace_fingerprint(root)

        self.assertEqual(pre_task_bytes, dirty_file.read_bytes())
        self.assertEqual(["app.txt"], state["initial_dirty_paths"])

    def test_capture_workspace_baseline_uses_the_new_path_for_a_rename(self):
        root = make_git_repo(self)
        run_git(root, "mv", "app.txt", "renamed.txt")
        state = state_at("INTAKE", project_root=root)

        result = quality_state.capture_workspace_baseline(state)

        self.assertEqual(["renamed.txt"], result["initial_dirty_paths"])

    def test_capture_workspace_baseline_rejects_non_git_and_terminal_states(self):
        with tempfile.TemporaryDirectory() as directory:
            state = state_at("INTAKE", project_root=Path(directory))
            with self.assertRaises(quality_state.GitError):
                quality_state.capture_workspace_baseline(state)

        state = state_at("COMPLETED", project_root=Path.cwd())
        before = deepcopy(state)
        with self.assertRaises(quality_state.TransitionError):
            quality_state.capture_workspace_baseline(state)
        self.assertEqual(before, state)


class VerificationTests(unittest.TestCase):
    def test_record_verification_sets_the_path_fingerprint_and_valid_flag(self):
        with tempfile.TemporaryDirectory() as directory:
            verification_path = Path(directory) / "verification.json"
            verification_path.write_text("verification\n", encoding="utf-8")
            result = quality_state.record_verification(
                state_at("CODE_REVIEW"),
                verification_path,
                VALID_FINGERPRINT,
            )

        self.assertEqual(
            {
                "path": str(verification_path),
                "workspace_fingerprint": VALID_FINGERPRINT,
                "valid": True,
            },
            result["verification"],
        )

    def test_record_verification_rejects_a_nonexistent_verification_path(self):
        with tempfile.TemporaryDirectory() as directory:
            missing_path = Path(directory) / "never-written.json"
            state = state_at("CODE_REVIEW")
            before = deepcopy(state["verification"])

            with self.assertRaises(StateError):
                quality_state.record_verification(
                    state,
                    missing_path,
                    VALID_FINGERPRINT,
                )

            self.assertEqual(before, state["verification"])

    def test_record_verification_rejects_a_directory_path(self):
        with tempfile.TemporaryDirectory() as directory:
            state = state_at("CODE_REVIEW")

            with self.assertRaises(StateError):
                quality_state.record_verification(
                    state,
                    Path(directory),
                    VALID_FINGERPRINT,
                )

    def test_record_verification_rejects_invalid_inputs_and_leaves_verification_invalid(self):
        invalid_cases = (
            (None, VALID_FINGERPRINT),
            ("", VALID_FINGERPRINT),
            ("verification.json", None),
            ("verification.json", "a" * 63),
            ("verification.json", "A" * 64),
        )

        for verification_path, fingerprint in invalid_cases:
            with self.subTest(
                verification_path=verification_path,
                fingerprint=fingerprint,
            ):
                state = state_at("CODE_REVIEW")
                before = deepcopy(state["verification"])

                with self.assertRaises(StateError):
                    quality_state.record_verification(
                        state,
                        verification_path,
                        fingerprint,
                    )

                self.assertEqual(before, state["verification"])
                self.assertFalse(state["verification"]["valid"])

    def test_stale_verification_is_invalidated_without_touching_spec_review_data(self):
        with tempfile.TemporaryDirectory() as directory:
            verification_path = Path(directory) / "verification.json"
            verification_path.write_text("verification\n", encoding="utf-8")
            state = state_at("CODE_REVIEW")
            state["reviews"]["spec"] = [{"round": 1, "path": "spec-review.json"}]
            state["artifact_digests"]["spec"] = "spec-digest"
            quality_state.record_verification(state, verification_path, OLD_FINGERPRINT)
        reviews_before = deepcopy(state["reviews"]["spec"])
        digest_before = state["artifact_digests"]["spec"]

        result = quality_state.invalidate_stale_verification(state, NEW_FINGERPRINT)

        self.assertFalse(result["verification"]["valid"])
        self.assertEqual(reviews_before, result["reviews"]["spec"])
        self.assertEqual(digest_before, result["artifact_digests"]["spec"])

    def test_matching_verification_fingerprint_is_left_valid(self):
        with tempfile.TemporaryDirectory() as directory:
            verification_path = Path(directory) / "verification.json"
            verification_path.write_text("verification\n", encoding="utf-8")
            state = state_at("CODE_REVIEW")
            quality_state.record_verification(state, verification_path, VALID_FINGERPRINT)
            before = deepcopy(state)

            result = quality_state.invalidate_stale_verification(state, VALID_FINGERPRINT)

            self.assertEqual(before, result)

    def test_invalidate_stale_verification_rejects_malformed_fingerprints(self):
        with tempfile.TemporaryDirectory() as directory:
            verification_path = Path(directory) / "verification.json"
            verification_path.write_text("verification\n", encoding="utf-8")
            for fingerprint in (None, "a" * 63, "A" * 64):
                with self.subTest(fingerprint=fingerprint):
                    state = state_at("CODE_REVIEW")
                    quality_state.record_verification(
                        state,
                        verification_path,
                        VALID_FINGERPRINT,
                    )
                    before = deepcopy(state["verification"])

                    with self.assertRaises(StateError):
                        quality_state.invalidate_stale_verification(state, fingerprint)

                    self.assertEqual(before, state["verification"])


class PassedTransitionGuardTests(unittest.TestCase):
    """SPEC_PASSED and PLAN_PASSED must require a passing recorded review."""

    def record(self, state, directory, artifact, verdict="PASS", blockers=None):
        review_path = write_json(
            directory,
            f"{artifact}-{state['rounds'][artifact] + 1}.json",
            valid_review(
                artifact=artifact,
                round_number=state["rounds"][artifact] + 1,
                verdict=verdict,
                blockers=blockers,
            ),
        )
        return quality_state.record_review(state, review_path, VALID_DIGEST)

    def test_spec_passed_rejects_a_stage_with_no_recorded_review(self):
        state = state_at("SPEC_REVIEW")

        with self.assertRaises(quality_state.TransitionError) as context:
            quality_state.transition(state, "SPEC_PASSED")

        self.assertIn("passing final spec review", str(context.exception))
        self.assertEqual("SPEC_REVIEW", state["stage"])

    def test_spec_passed_rejects_a_non_passing_final_review(self):
        with tempfile.TemporaryDirectory() as directory:
            state = state_at("SPEC_REVIEW")
            self.record(state, directory, "spec", verdict="REVISE")

            with self.assertRaises(quality_state.TransitionError):
                quality_state.transition(state, "SPEC_PASSED")
            self.assertEqual("SPEC_REVIEW", state["stage"])

    def test_spec_passed_rejects_a_passing_review_that_still_lists_blockers(self):
        with tempfile.TemporaryDirectory() as directory:
            state = state_at("SPEC_REVIEW")
            self.record(state, directory, "spec", blockers=["SPEC-OPEN-001"])

            with self.assertRaises(quality_state.TransitionError):
                quality_state.transition(state, "SPEC_PASSED")
            self.assertEqual("SPEC_REVIEW", state["stage"])

    def test_spec_passed_rejects_stale_blockers_even_with_no_open_findings(self):
        """The guard checks the recorded review's blockers independently of
        open_finding_ids, so a state where only one of the two was cleared is
        still refused."""
        state = state_at("SPEC_REVIEW")
        state["rounds"]["spec"] = 1
        state["reviews"]["spec"] = [
            {"verdict": "PASS", "blockers": ["SPEC-STALE-001"]}
        ]
        state["open_finding_ids"]["spec"] = []

        with self.assertRaises(quality_state.TransitionError):
            quality_state.transition(state, "SPEC_PASSED")
        self.assertEqual("SPEC_REVIEW", state["stage"])

    def test_spec_passed_accepts_a_passing_final_review(self):
        with tempfile.TemporaryDirectory() as directory:
            state = state_at("SPEC_REVIEW")
            self.record(state, directory, "spec")

            result = quality_state.transition(state, "SPEC_PASSED")

            self.assertEqual("SPEC_PASSED", result["stage"])

    def test_plan_passed_rejects_a_stage_with_no_recorded_review(self):
        state = state_at("PLAN_REVIEW")

        with self.assertRaises(quality_state.TransitionError) as context:
            quality_state.transition(state, "PLAN_PASSED")

        self.assertIn("passing final plan review", str(context.exception))
        self.assertEqual("PLAN_REVIEW", state["stage"])

    def test_plan_passed_accepts_a_passing_final_review(self):
        with tempfile.TemporaryDirectory() as directory:
            state = state_at("PLAN_REVIEW")
            self.record(state, directory, "plan")

            result = quality_state.transition(state, "PLAN_PASSED")

            self.assertEqual("PLAN_PASSED", result["stage"])

    def test_light_plan_passed_needs_no_review_round(self):
        """SKILL.md gives light no reviewer round for the compact Plan, so its
        documented IMPLEMENTING -> PLAN_REVIEW -> PLAN_PASSED rework path must
        stay open."""
        state = state_at("PLAN_REVIEW", mode="light")

        result = quality_state.transition(state, "PLAN_PASSED")

        self.assertEqual("PLAN_PASSED", result["stage"])
        self.assertEqual(0, result["rounds"]["plan"])

    def test_light_spec_passed_still_requires_a_review(self):
        state = state_at("SPEC_REVIEW", mode="light")

        with self.assertRaises(quality_state.TransitionError):
            quality_state.transition(state, "SPEC_PASSED")


class ResumeSelectionTests(unittest.TestCase):
    def persist_candidate(self, state_root, task_id, state):
        path = Path(state_root) / task_id / "state.json"
        path.parent.mkdir(parents=True)
        quality_state.save_state(path, state)
        return path

    def make_candidate(self, goal, project_root, task_id, updated_at, stage="CLASSIFIED"):
        state = quality_state.new_state(
            goal,
            "standard",
            project_root,
            "artifacts",
            task_id=task_id,
            now=updated_at,
        )
        state["stage"] = stage
        state["mode"] = "standard"
        return state

    def test_select_resume_returns_newest_matching_nonterminal_state(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            state_root = directory / "states"
            state_root.mkdir()
            project_root = directory / "project"
            other_project = directory / "other-project"
            project_root.mkdir()
            other_project.mkdir()
            query_goal = "Build a quality state"

            older_path = self.persist_candidate(
                state_root,
                "older",
                self.make_candidate(
                    "Build a quality state",
                    project_root,
                    "older",
                    FIXED_NOW,
                ),
            )
            newer_path = self.persist_candidate(
                state_root,
                "newer",
                self.make_candidate(
                    "  Ｂｕｉｌｄ   a QUALITY state ",
                    project_root,
                    "newer",
                    FIXED_NOW + timedelta(minutes=1),
                ),
            )
            self.persist_candidate(
                state_root,
                "completed",
                self.make_candidate(
                    query_goal,
                    project_root,
                    "completed",
                    FIXED_NOW + timedelta(minutes=3),
                    stage="COMPLETED",
                ),
            )
            self.persist_candidate(
                state_root,
                "different-goal",
                self.make_candidate(
                    "A different goal",
                    project_root,
                    "different-goal",
                    FIXED_NOW + timedelta(minutes=4),
                ),
            )
            self.persist_candidate(
                state_root,
                "different-project",
                self.make_candidate(
                    query_goal,
                    other_project,
                    "different-project",
                    FIXED_NOW + timedelta(minutes=5),
                ),
            )

            selected = quality_state.select_resume_candidate(
                state_root,
                "  Ｂｕｉｌｄ   a QUALITY state ",
                project_root,
            )

            self.assertEqual(newer_path, selected)
            self.assertNotEqual(older_path, selected)

    def test_select_resume_reuses_passed_spec_at_plan_review_without_duplicate_state(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            state_root = directory / "states"
            state_root.mkdir()
            project_root = make_git_repo(self)
            artifact_dir = directory / "artifacts"
            artifact_dir.mkdir()
            spec_path = artifact_dir / "spec.md"
            spec_path.write_text("passed specification\n", encoding="utf-8")
            review_path = write_json(
                directory,
                "spec-review.json",
                valid_review(artifact="spec"),
            )
            goal = "Build the resumable quality workflow"
            state = quality_state.new_state(
                goal,
                "standard",
                project_root,
                artifact_dir,
                task_id="resume-task",
                now=FIXED_NOW,
            )
            quality_state.classify(state, "standard", ["scope is understood"])
            quality_state.set_artifact(state, "spec", spec_path)
            quality_state.transition(state, "SPEC_REVIEW")
            spec_digest = hashlib.sha256(spec_path.read_bytes()).hexdigest()
            quality_state.record_review(state, review_path, spec_digest)
            quality_state.transition(state, "SPEC_PASSED")
            quality_state.transition(state, "PLAN_REVIEW")
            state_path = self.persist_candidate(state_root, "resume-task", state)

            selected = quality_state.select_resume_candidate(
                state_root,
                "  Ｂｕｉｌｄ   the RESUMABLE quality workflow ",
                project_root,
            )

            self.assertEqual(state_path, selected)
            loaded = quality_state.load_state(selected)
            self.assertEqual("PLAN_REVIEW", loaded["stage"])
            self.assertEqual(state["reviews"]["spec"][0], loaded["reviews"]["spec"][0])
            self.assertEqual(spec_digest, loaded["artifact_digests"]["spec"])
            self.assertEqual([state_path], list(state_root.glob("*/state.json")))

    def test_select_resume_returns_none_when_only_matching_states_are_terminal(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            state_root = directory / "states"
            state_root.mkdir()
            project_root = directory / "project"
            project_root.mkdir()
            state = self.make_candidate(
                "A completed goal",
                project_root,
                "completed",
                FIXED_NOW,
                stage="COMPLETED",
            )
            self.persist_candidate(state_root, "completed", state)

            self.assertIsNone(
                quality_state.select_resume_candidate(
                    state_root,
                    "A completed goal",
                    project_root,
                )
            )

    def test_select_resume_breaks_same_updated_at_ties_by_task_id(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            state_root = directory / "states"
            state_root.mkdir()
            project_root = directory / "project"
            project_root.mkdir()
            for task_id in ("task-z", "task-a"):
                self.persist_candidate(
                    state_root,
                    task_id,
                    self.make_candidate(
                        "A tied goal",
                        project_root,
                        task_id,
                        FIXED_NOW,
                    ),
                )

            selected = quality_state.select_resume_candidate(
                state_root,
                "A tied goal",
                project_root,
            )

            self.assertEqual(state_root / "task-z" / "state.json", selected)

    def test_select_resume_skips_states_with_unparseable_updated_at_or_invalid_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            state_root = directory / "states"
            state_root.mkdir()
            project_root = directory / "project"
            project_root.mkdir()
            invalid_time = self.make_candidate(
                "A resumable goal",
                project_root,
                "invalid-time",
                FIXED_NOW,
            )
            invalid_time["updated_at"] = "not-a-timestamp"
            self.persist_candidate(state_root, "invalid-time", invalid_time)

            invalid_schema = self.make_candidate(
                "A resumable goal",
                project_root,
                "invalid-schema",
                FIXED_NOW + timedelta(minutes=2),
            )
            invalid_schema.pop("schema_version")
            path = state_root / "invalid-schema" / "state.json"
            path.parent.mkdir()
            path.write_text(json.dumps(invalid_schema), encoding="utf-8")

            valid = self.make_candidate(
                "A resumable goal",
                project_root,
                "valid",
                FIXED_NOW + timedelta(minutes=1),
            )
            valid_path = self.persist_candidate(state_root, "valid", valid)

            self.assertEqual(
                valid_path,
                quality_state.select_resume_candidate(
                    state_root,
                    "A resumable goal",
                    project_root,
                ),
            )


class CLITests(unittest.TestCase):
    def invoke_main(self, args):
        output = io.StringIO()
        with redirect_stdout(output):
            result = quality_state.main(args)
        return result, output.getvalue()

    def invoke_main_with_stderr(self, args):
        output = io.StringIO()
        errors = io.StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            result = quality_state.main(args)
        return result, output.getvalue(), errors.getvalue()

    def assert_cli_success(self, args):
        result, output = self.invoke_main(args)
        self.assertEqual(0, result, args)
        return output

    def test_cli_help_returns_zero_after_argparse_prints_help(self):
        result, output = self.invoke_main(["--help"])

        self.assertEqual(0, result)
        self.assertIn("usage:", output)

    def test_cli_init_accepts_explicit_task_id_and_refuses_to_overwrite_it(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            project_root = make_git_repo(self)
            arguments = [
                "init",
                "--root",
                str(directory / "states"),
                "--goal",
                "A unique task",
                "--requested-mode",
                "standard",
                "--project-root",
                str(project_root),
                "--artifact-dir",
                str(directory / "artifacts"),
                "--task-id",
                "explicit-task",
            ]

            first, _ = self.invoke_main(arguments)
            second, _ = self.invoke_main(arguments)

            self.assertEqual(0, first)
            self.assertEqual(4, second)

    def test_cli_init_warns_for_in_repo_nonstandard_state_root_only(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            project_root = make_git_repo(self)
            common = [
                "init",
                "--goal",
                "A unique task",
                "--requested-mode",
                "standard",
                "--project-root",
                str(project_root),
                "--artifact-dir",
                str(directory / "artifacts"),
            ]
            cases = (
                ("standard", project_root / ".claude" / "quality-state", False),
                ("in-repo", project_root / ".claude" / "other-state", True),
                ("out-of-repo", directory / "outside-state", False),
            )

            for task_id, root, should_warn in cases:
                with self.subTest(state_root=root):
                    result, _, errors = self.invoke_main_with_stderr(
                        common
                        + [
                            "--root",
                            str(root),
                            "--task-id",
                            task_id,
                        ]
                    )

                    self.assertEqual(0, result)
                    if should_warn:
                        self.assertIn("warning:", errors)
                        self.assertIn(
                            "state files re-enter the workspace fingerprint",
                            errors,
                        )
                    else:
                        self.assertNotIn("warning:", errors)
                        self.assertNotIn(
                            "state files re-enter the workspace fingerprint",
                            errors,
                        )

    def test_cli_approve_plan_persists_plan_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            plan_path = directory / "plan.md"
            plan_path.write_text("plan\n", encoding="utf-8")
            state_path = directory / "state.json"
            state = state_at("AWAITING_PLAN_APPROVAL", mode="standard")
            state["artifacts"]["plan"] = str(plan_path)
            state["artifact_digests"]["plan"] = quality_state._file_digest(plan_path)
            quality_state.save_state(state_path, state)

            result, _ = self.invoke_main([
                "approve-plan",
                "--state",
                str(state_path),
                "--plan",
                str(plan_path),
                "--approved-at",
                "2026-08-25T12:00:00Z",
            ])

            self.assertEqual(0, result)
            persisted = quality_state.load_state(state_path)
            self.assertEqual(str(plan_path), persisted["plan_approval"]["path"])
            self.assertEqual(
                hashlib.sha256(plan_path.read_bytes()).hexdigest(),
                persisted["plan_approval"]["digest"],
            )

    def test_cli_record_review_error_retries_then_blocks_on_disk(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            state_path = directory / "state.json"
            errors_path = write_json(directory, "errors.json", ["missing evidence"])
            quality_state.save_state(state_path, state_at("PLAN_REVIEW"))
            arguments = [
                "record-review-error",
                "--state",
                str(state_path),
                "--artifact",
                "plan",
                "--round",
                "1",
                "--errors",
                str(errors_path),
            ]

            first, _ = self.invoke_main(arguments)
            first_state = quality_state.load_state(state_path)
            second, _ = self.invoke_main(arguments)
            second_state = quality_state.load_state(state_path)

            self.assertEqual(0, first)
            self.assertEqual(1, first_state["review_validation_retry"]["attempts"])
            self.assertEqual(0, second)
            self.assertEqual("BLOCKED", second_state["stage"])
            self.assertEqual("REVIEW_OUTPUT_INVALID", second_state["status_reason"])

    def test_cli_record_review_round_two_uses_state_held_prior_blockers(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            state_path = directory / "state.json"
            quality_state.save_state(state_path, state_at("PLAN_REVIEW"))
            first_path = write_json(
                directory,
                "plan-review-1.json",
                valid_review(
                    verdict="REVISE",
                    blockers=["PLAN-CARRIED-001"],
                ),
            )
            second_path = write_json(
                directory,
                "plan-review-2.json",
                valid_review(
                    round_number=2,
                    verdict="REVISE",
                    blockers=["PLAN-CARRIED-001"],
                ),
            )

            first, _ = self.invoke_main([
                "record-review",
                "--state",
                str(state_path),
                "--review",
                str(first_path),
                "--artifact-digest",
                VALID_DIGEST,
            ])
            second, _ = self.invoke_main([
                "record-review",
                "--state",
                str(state_path),
                "--review",
                str(second_path),
                "--artifact-digest",
                VALID_DIGEST,
            ])

            persisted = quality_state.load_state(state_path)
            self.assertEqual(0, first)
            self.assertEqual(0, second)
            self.assertEqual(2, persisted["rounds"]["plan"])
            self.assertEqual("NEEDS_REDESIGN", persisted["stage"])

    def test_cli_persists_mutations_before_a_transition_error(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            state_root = directory / "states"
            project_root = make_git_repo(self)
            plan_path = directory / "plan.md"
            plan_path.write_text("approved plan\n", encoding="utf-8")
            result, output = self.invoke_main([
                "init",
                "--root",
                str(state_root),
                "--goal",
                "Persist transition failures",
                "--requested-mode",
                "standard",
                "--project-root",
                str(project_root),
                "--artifact-dir",
                str(directory / "artifacts"),
            ])
            self.assertEqual(0, result)
            state_path = state_root / json.loads(output)["task_id"] / "state.json"
            reasons_path = write_json(directory, "reasons.json", ["scope is understood"])
            self.assertEqual(
                0,
                self.invoke_main([
                    "classify",
                    "--state",
                    str(state_path),
                    "--mode",
                    "standard",
                    "--reasons",
                    str(reasons_path),
                ])[0],
            )
            state = quality_state.load_state(state_path)
            state["artifacts"]["plan"] = str(plan_path)
            state["verification"]["valid"] = True
            # SPEC_PASSED and PLAN_PASSED each require a passing recorded
            # review; this test is about persistence on a later transition
            # error, so seed the minimum state those guards demand.
            for artifact in ("spec", "plan"):
                state["rounds"][artifact] = 1
                state["reviews"][artifact] = [{"verdict": "PASS", "blockers": []}]
                state["open_finding_ids"][artifact] = []
            # approve-plan below also requires a recorded review digest for
            # the plan content it is about to approve.
            state["artifact_digests"]["plan"] = quality_state._file_digest(plan_path)
            quality_state.save_state(state_path, state)
            for target in ("SPEC_REVIEW", "SPEC_PASSED", "PLAN_REVIEW", "PLAN_PASSED", "AWAITING_PLAN_APPROVAL"):
                self.assertEqual(
                    0,
                    self.invoke_main([
                        "transition",
                        "--state",
                        str(state_path),
                        "--to",
                        target,
                    ])[0],
                )
            self.assertEqual(
                0,
                self.invoke_main([
                    "approve-plan",
                    "--state",
                    str(state_path),
                    "--plan",
                    str(plan_path),
                    "--approved-at",
                    "2026-08-25T12:00:00Z",
                ])[0],
            )
            plan_path.write_text("tampered plan\n", encoding="utf-8")

            result, _ = self.invoke_main([
                "transition",
                "--state",
                str(state_path),
                "--to",
                "IMPLEMENTING",
            ])

            persisted = quality_state.load_state(state_path)
            self.assertEqual(3, result)
            self.assertEqual("PLAN_REVIEW", persisted["stage"])
            self.assertIsNone(persisted["plan_approval"])
            self.assertFalse(persisted["verification"]["valid"])

    def test_cli_non_demotion_state_error_leaves_state_file_byte_identical(self):
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "state.json"
            quality_state.save_state(state_path, state_at("INTAKE"))
            before = state_path.read_bytes()

            result, _ = self.invoke_main([
                "transition",
                "--state",
                str(state_path),
                "--to",
                "BLOCKED",
            ])

            self.assertEqual(2, result)
            self.assertEqual(before, state_path.read_bytes())

    def test_cli_light_walk_reaches_completed_using_artifact_and_verification_commands(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            state_root = directory / "state-root"
            artifact_dir = directory / "artifacts"
            artifact_dir.mkdir()
            project_root = make_git_repo(self)
            compact_plan = artifact_dir / "compact-plan.md"
            compact_plan.write_text("compact plan\n", encoding="utf-8")
            verification_path = directory / "verification.json"
            verification_path.write_text("verification\n", encoding="utf-8")
            reasons_path = write_json(directory, "reasons.json", ["scope is understood"])
            code_review_path = write_json(
                directory,
                "code-review.json",
                valid_review(artifact="code"),
            )

            initial = json.loads(self.assert_cli_success([
                "init",
                "--root",
                str(state_root),
                "--goal",
                "Complete a light quality workflow",
                "--requested-mode",
                "light",
                "--project-root",
                str(project_root),
                "--artifact-dir",
                str(artifact_dir),
            ]))
            state_path = state_root / initial["task_id"] / "state.json"

            self.assert_cli_success([
                "capture-baseline",
                "--state",
                str(state_path),
            ])
            self.assert_cli_success([
                "classify",
                "--state",
                str(state_path),
                "--mode",
                "light",
                "--reasons",
                str(reasons_path),
            ])
            self.assert_cli_success([
                "set-artifact",
                "--state",
                str(state_path),
                "--kind",
                "compact_plan",
                "--path",
                str(compact_plan),
            ])
            self.assert_cli_success([
                "transition",
                "--state",
                str(state_path),
                "--to",
                "AWAITING_PLAN_APPROVAL",
            ])
            self.assert_cli_success([
                "approve-plan",
                "--state",
                str(state_path),
                "--plan",
                str(compact_plan),
                "--approved-at",
                "2026-08-25T12:00:00Z",
            ])
            self.assert_cli_success([
                "transition",
                "--state",
                str(state_path),
                "--to",
                "IMPLEMENTING",
            ])
            self.assert_cli_success([
                "transition",
                "--state",
                str(state_path),
                "--to",
                "CODE_REVIEW",
            ])

            fingerprint = json.loads(self.assert_cli_success([
                "fingerprint",
                "--project-root",
                str(project_root),
            ]))["fingerprint"]
            self.assertRegex(fingerprint, r"^[0-9a-f]{64}$")
            self.assert_cli_success([
                "record-verification",
                "--state",
                str(state_path),
                "--path",
                str(verification_path),
                "--fingerprint",
                fingerprint,
            ])
            self.assert_cli_success([
                "record-review",
                "--state",
                str(state_path),
                "--review",
                str(code_review_path),
                "--artifact-digest",
                fingerprint,
            ])
            self.assert_cli_success([
                "transition",
                "--state",
                str(state_path),
                "--to",
                "COMPLETED",
            ])

            self.assertEqual("COMPLETED", quality_state.load_state(state_path)["stage"])

    def test_cli_standard_walk_reaches_completed_using_artifact_and_verification_commands(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            state_root = directory / "state-root"
            artifact_dir = directory / "artifacts"
            artifact_dir.mkdir()
            project_root = make_git_repo(self)
            spec_path = artifact_dir / "spec.md"
            spec_path.write_text("specification\n", encoding="utf-8")
            plan_path = artifact_dir / "plan.md"
            plan_path.write_text("implementation plan\n", encoding="utf-8")
            verification_path = directory / "verification.json"
            verification_path.write_text("verification\n", encoding="utf-8")
            reasons_path = write_json(directory, "reasons.json", ["scope is understood"])
            spec_review_path = write_json(
                directory,
                "spec-review.json",
                valid_review(artifact="spec"),
            )
            plan_review_path = write_json(
                directory,
                "plan-review.json",
                valid_review(artifact="plan"),
            )
            code_review_path = write_json(
                directory,
                "code-review.json",
                valid_review(artifact="code"),
            )

            initial = json.loads(self.assert_cli_success([
                "init",
                "--root",
                str(state_root),
                "--goal",
                "Complete a standard quality workflow",
                "--requested-mode",
                "standard",
                "--project-root",
                str(project_root),
                "--artifact-dir",
                str(artifact_dir),
            ]))
            state_path = state_root / initial["task_id"] / "state.json"

            self.assert_cli_success([
                "capture-baseline",
                "--state",
                str(state_path),
            ])
            self.assert_cli_success([
                "classify",
                "--state",
                str(state_path),
                "--mode",
                "standard",
                "--reasons",
                str(reasons_path),
            ])
            self.assert_cli_success([
                "set-artifact",
                "--state",
                str(state_path),
                "--kind",
                "spec",
                "--path",
                str(spec_path),
            ])
            self.assert_cli_success([
                "transition",
                "--state",
                str(state_path),
                "--to",
                "SPEC_REVIEW",
            ])
            self.assert_cli_success([
                "record-review",
                "--state",
                str(state_path),
                "--review",
                str(spec_review_path),
                "--artifact-digest",
                hashlib.sha256(spec_path.read_bytes()).hexdigest(),
            ])
            self.assert_cli_success([
                "transition",
                "--state",
                str(state_path),
                "--to",
                "SPEC_PASSED",
            ])
            self.assert_cli_success([
                "set-artifact",
                "--state",
                str(state_path),
                "--kind",
                "plan",
                "--path",
                str(plan_path),
            ])
            self.assert_cli_success([
                "transition",
                "--state",
                str(state_path),
                "--to",
                "PLAN_REVIEW",
            ])
            self.assert_cli_success([
                "record-review",
                "--state",
                str(state_path),
                "--review",
                str(plan_review_path),
                "--artifact-digest",
                hashlib.sha256(plan_path.read_bytes()).hexdigest(),
            ])
            self.assert_cli_success([
                "transition",
                "--state",
                str(state_path),
                "--to",
                "PLAN_PASSED",
            ])
            self.assert_cli_success([
                "transition",
                "--state",
                str(state_path),
                "--to",
                "AWAITING_PLAN_APPROVAL",
            ])
            self.assert_cli_success([
                "approve-plan",
                "--state",
                str(state_path),
                "--plan",
                str(plan_path),
                "--approved-at",
                "2026-08-25T12:00:00Z",
            ])
            self.assert_cli_success([
                "transition",
                "--state",
                str(state_path),
                "--to",
                "IMPLEMENTING",
            ])
            self.assert_cli_success([
                "transition",
                "--state",
                str(state_path),
                "--to",
                "CODE_REVIEW",
            ])
            fingerprint = json.loads(self.assert_cli_success([
                "fingerprint",
                "--project-root",
                str(project_root),
            ]))["fingerprint"]
            self.assert_cli_success([
                "record-verification",
                "--state",
                str(state_path),
                "--path",
                str(verification_path),
                "--fingerprint",
                fingerprint,
            ])
            self.assert_cli_success([
                "record-review",
                "--state",
                str(state_path),
                "--review",
                str(code_review_path),
                "--artifact-digest",
                fingerprint,
            ])
            self.assert_cli_success([
                "transition",
                "--state",
                str(state_path),
                "--to",
                "COMPLETED",
            ])

            self.assertEqual("COMPLETED", quality_state.load_state(state_path)["stage"])

    def test_cli_capture_baseline_persists_workspace_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            root = make_git_repo(self)
            state_path = directory / "state.json"
            quality_state.save_state(state_path, state_at("INTAKE", project_root=root))

            result, _ = self.invoke_main([
                "capture-baseline",
                "--state",
                str(state_path),
            ])

            persisted = quality_state.load_state(state_path)
            self.assertEqual(0, result)
            self.assertEqual(run_git(root, "rev-parse", "HEAD").stdout.strip(), persisted["base_revision"])

    def test_cli_end_to_end_sequence_and_exit_codes(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            state_root = directory / "state-root"
            artifact_dir = directory / "artifacts"
            project_root = make_git_repo(self)
            goal = "Build a quality state"

            result, output = self.invoke_main([
                "init",
                "--root",
                str(state_root),
                "--goal",
                goal,
                "--requested-mode",
                "standard",
                "--project-root",
                str(project_root),
                "--artifact-dir",
                str(artifact_dir),
            ])
            self.assertEqual(0, result)
            initial = json.loads(output)
            state_path = state_root / initial["task_id"] / "state.json"
            self.assertTrue(state_path.is_file())

            result, output = self.invoke_main(["show", "--state", str(state_path)])
            self.assertEqual(0, result)
            self.assertEqual(initial, json.loads(output))

            reasons_path = write_json(directory, "reasons.json", ["scope is understood"])
            result, _ = self.invoke_main([
                "classify",
                "--state",
                str(state_path),
                "--mode",
                "standard",
                "--reasons",
                str(reasons_path),
            ])
            self.assertEqual(0, result)

            result, _ = self.invoke_main([
                "transition",
                "--state",
                str(state_path),
                "--to",
                "IMPLEMENTING",
            ])
            self.assertEqual(3, result)

            result, _ = self.invoke_main([
                "transition",
                "--state",
                str(state_path),
                "--to",
                "SPEC_REVIEW",
            ])
            self.assertEqual(0, result)

            spec_review_path = write_json(
                directory,
                "spec-review.json",
                valid_review(artifact="spec"),
            )
            result, _ = self.invoke_main([
                "record-review",
                "--state",
                str(state_path),
                "--review",
                str(spec_review_path),
                "--artifact-digest",
                hashlib.sha256(b"spec-artifact").hexdigest(),
            ])
            self.assertEqual(0, result)

            for target in ("SPEC_PASSED", "PLAN_REVIEW"):
                result, _ = self.invoke_main([
                    "transition",
                    "--state",
                    str(state_path),
                    "--to",
                    target,
                ])
                self.assertEqual(0, result)

            review_path = write_json(directory, "plan-review.json", valid_review())
            artifact_digest = hashlib.sha256(b"plan-artifact").hexdigest()
            result, _ = self.invoke_main([
                "record-review",
                "--state",
                str(state_path),
                "--review",
                str(review_path),
                "--artifact-digest",
                artifact_digest,
            ])
            self.assertEqual(0, result)

            result, output = self.invoke_main([
                "select-resume",
                "--root",
                str(state_root),
                "--goal",
                "  Ｂｕｉｌｄ   a QUALITY state ",
                "--project-root",
                str(project_root),
            ])
            self.assertEqual(0, result)
            self.assertIsNotNone(json.loads(output)["match"])

            result, output = self.invoke_main([
                "fingerprint",
                "--project-root",
                str(project_root),
            ])
            self.assertEqual(0, result)
            self.assertRegex(json.loads(output)["fingerprint"], r"^[0-9a-f]{64}$")

            non_git = directory / "not-a-git-repository"
            non_git.mkdir()
            result, _ = self.invoke_main([
                "fingerprint",
                "--project-root",
                str(non_git),
            ])
            self.assertEqual(4, result)

            result, _ = self.invoke_main([
                "init",
                "--root",
                str(state_root),
                "--goal",
                goal,
                "--requested-mode",
                "invalid",
                "--project-root",
                str(project_root),
                "--artifact-dir",
                str(artifact_dir),
            ])
            self.assertEqual(2, result)


if __name__ == "__main__":
    unittest.main()
