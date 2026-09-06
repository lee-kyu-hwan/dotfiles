import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "revision_check.py"
FIXTURE_DIR = Path(__file__).parent / "fixtures" / "revision-check"
sys.path.insert(0, str(SCRIPT.parent))

from validate_review import validate_revision_check


"""The canonical complete fixtures are exercised through file reads below."""

SPEC_COMPLETE_OLD = """# Spec
## Requirements
- **R1.1** First requirement.
- **R1.2** Second requirement.
- **R2.1** Third requirement.
- **R3.1** Fourth requirement.
## Acceptance criteria
- **AC-1** First. [문서] `docs/one.md`
- **AC-2** Second. [실행] (CMD-1 -k test_alpha)
- **AC-3** Third. [문서] `docs/three.md`
- **AC-4** Fourth. [실행] (CMD-1 -k test_beta)
- **AC-5** Fifth. [문서] `docs/five.md`
- **AC-6** Sixth. [문서] `docs/six.md`
- **AC-7** Seventh. [문서] `docs/seven.md`
- **AC-8** Eighth. [문서] `docs/eight.md`
### D1. First decision
### D2. Second decision
## Requirements traceability
| Requirement | Criteria |
| --- | --- |
| R1.1 | AC-1, AC-2 |
| R1.2 | AC-3, AC-4 |
| R2.1 | AC-5, AC-6 |
| R3.1 | AC-7, AC-8 |
## Verification commands
| CMD-1 | tests |
| CMD-2 | more tests |
"""

PLAN_COMPLETE_OLD = """# Plan
## Tasks
### T1. First
대상 AC: AC-1, AC-2
AC-1 `docs/one.md`
AC-2 `CMD-1` `test_alpha`
### T2. Second
대상 AC: AC-3, AC-4, AC-5
AC-3 `docs/three.md`
AC-4 `CMD-1` `test_beta`
AC-5 `docs/five.md`
### T3. Third
대상 AC: AC-6, AC-7, AC-8
AC-6 `docs/six.md`
AC-7 `docs/seven.md`
AC-8 `docs/eight.md`
## Verification commands
| CMD-1 | test command |
| command | CMD-2 | second command |
## Acceptance-criteria traceability
| Criterion | Task | Verification command | Expected outcome |
| --- | --- | --- | --- |
| AC-1 | T1 | `docs/one.md` | ok |
| AC-2 | T1 | `CMD-1` `test_alpha` | ok |
| AC-3 | T2 | `docs/three.md` | ok |
| AC-4 | T2 | `CMD-1` `test_beta` | ok |
| AC-5 | T2 | `docs/five.md` | ok |
| AC-6 | T3 | `docs/six.md` | ok |
| AC-7 | T3 | `docs/seven.md` | ok |
| AC-8 | T3 | `docs/eight.md` | ok |
"""

SPEC_COMPLETE = (FIXTURE_DIR / "spec-complete.md").read_text(encoding="utf-8")
PLAN_COMPLETE = (FIXTURE_DIR / "plan-complete.md").read_text(encoding="utf-8")

NOTE_HEADER = "| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |"


class RevisionCheckTests(unittest.TestCase):
    def write(self, directory, name, text):
        path = Path(directory) / name
        path.write_text(text, encoding="utf-8")
        return path

    def run_check(self, artifact, current, *, spec=None, extra=(), cwd=None):
        command = [sys.executable, str(SCRIPT), "--artifact", artifact, "--current", str(current)]
        if spec is not None:
            command.extend(("--spec", str(spec)))
        command.extend(extra)
        return subprocess.run(command, capture_output=True, text=True, cwd=cwd)

    def output(self, result, path):
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        return json.loads(Path(path).read_text(encoding="utf-8"))

    def test_cli_exit_codes_and_usage(self):
        with tempfile.TemporaryDirectory() as directory:
            spec = self.write(directory, "spec.md", SPEC_COMPLETE)
            output = Path(directory) / "result.json"
            self.assertEqual(self.run_check("spec", spec, extra=("--out", str(output))).returncode, 0)
            broken = self.write(directory, "broken.md", SPEC_COMPLETE.replace("| R3.1 | AC-7, AC-8 |\n", ""))
            result = self.run_check("spec", broken, extra=("--out", str(output)))
            self.assertEqual(result.returncode, 1)
            self.assertFalse(json.loads(output.read_text())["passed"])
            plan = self.write(directory, "plan.md", PLAN_COMPLETE)
            invalid_current = Path(directory) / "invalid-current.md"
            invalid_current.write_bytes(b"\xff")
            invalid_spec = Path(directory) / "invalid-spec.md"
            invalid_spec.write_bytes(b"\xff")
            base_directory = Path(directory) / "base-directory"
            notes_directory = Path(directory) / "notes-directory"
            base_directory.mkdir()
            notes_directory.mkdir()
            corrupt_state = self.write(directory, "corrupt-state.json", "{")
            snapshot_state = self.write(directory, "snapshot-state.json", json.dumps({"rounds": {"spec": 1}, "reviews": {"spec": []}}))
            cases = (
                ("plan", spec, None, ()),
                ("spec", Path(directory) / "missing.md", None, ()),
                ("plan", plan, Path(directory) / "missing-spec.md", ()),
                ("spec", spec, None, ("--state", str(Path(directory) / "missing-state.json"))),
                ("spec", spec, None, ("--base", str(Path(directory) / "missing-base.md"))),
                ("spec", spec, None, ("--base", str(base_directory))),
                ("spec", spec, None, ("--notes", str(Path(directory) / "missing-notes.md"))),
                ("spec", spec, None, ("--notes", str(notes_directory))),
                ("spec", invalid_current, None, ()),
                ("plan", plan, invalid_spec, ()),
                ("spec", spec, None, ("--state", str(corrupt_state))),
                ("spec", spec, None, ("--state", str(corrupt_state), "--base", str(spec))),
                ("spec", spec, None, ("--state", str(snapshot_state))),
            )
            for number, (artifact, current, companion, extra) in enumerate(cases):
                failure_out = Path(directory) / f"failure-{number}.json"
                command = self.run_check(artifact, current, spec=companion, extra=(*extra, "--out", str(failure_out)))
                self.assertEqual(command.returncode, 2, command.stderr)
                self.assertFalse(failure_out.exists())
            relative = self.run_check("spec", Path("spec.md"), extra=("--out", "relative.json"), cwd=directory)
            self.assertEqual(0, relative.returncode, relative.stderr)
            self.assertTrue((Path(directory) / "relative.json").is_file())

    def test_output_matches_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            spec = self.write(directory, "spec.md", SPEC_COMPLETE)
            output = Path(directory) / "out.json"
            payload = self.output(self.run_check("spec", spec, extra=("--out", str(output))), output)
            self.assertEqual([], validate_revision_check(payload))
            self.assertEqual(payload["round"], None)
            self.assertEqual(payload["current_digest"], hashlib.sha256(spec.read_bytes()).hexdigest())
            self.assertIsNone(payload["spec_digest"])
            self.assertEqual(set(payload), {"artifact", "round", "base_digest", "current_digest", "spec_digest", "cells", "empty_cells", "touched_requirements", "removed_ids", "ripple", "notes", "passed"})
            revision_payload = {
                **payload,
                "ripple": [{"requirement": "R1.1", "acceptance_criteria": [], "plan_rows": None, "tasks": None, "commands": []}],
            }
            variants = (
                {**revision_payload, "unexpected": True},
                {**revision_payload, "cells": [{**payload["cells"][0], "status": "invalid"}, *payload["cells"][1:]]},
                {**revision_payload, "cells": [{key: value for key, value in payload["cells"][0].items() if key != "key"}, *payload["cells"][1:]]},
                {**revision_payload, "ripple": [{**revision_payload["ripple"][0], "unexpected": True}]},
                *({**revision_payload, "notes": {key: value for key, value in payload["notes"].items() if key != field}} for field in ("required", "path", "section_found", "missing_rows", "blank_cells")),
            )
            for variant in variants:
                with self.subTest(variant=variant):
                    self.assertTrue(validate_revision_check(variant))
            snapshots = Path(directory) / "snapshots"
            snapshots.mkdir()
            self.write(snapshots, "spec-r1.md", SPEC_COMPLETE)
            state = self.write(directory, "state.json", json.dumps({
                "rounds": {"spec": 1},
                "reviews": {"spec": [{"artifact_digest": hashlib.sha256(SPEC_COMPLETE.encode()).hexdigest()}]},
            }))
            state_output = Path(directory) / "state-output.json"
            state_result = self.run_check("spec", spec, extra=("--state", str(state), "--out", str(state_output)))
            self.assertEqual(1, state_result.returncode)
            self.assertEqual(2, json.loads(state_output.read_text(encoding="utf-8"))["round"])
            plan = self.write(directory, "plan.md", PLAN_COMPLETE)
            plan_output = Path(directory) / "plan-output.json"
            plan_payload = self.output(self.run_check("plan", plan, spec=spec, extra=("--out", str(plan_output))), plan_output)
            self.assertEqual(hashlib.sha256(spec.read_bytes()).hexdigest(), plan_payload["spec_digest"])

    def test_id_grammar_ignores_code_blocks(self):
        import revision_check

        with tempfile.TemporaryDirectory() as directory:
            text = SPEC_COMPLETE.replace("[실행] (CMD-1 -k test_alpha)", "`[실행] (CMD-7 -k hidden)`") + "\n```\n- **AC-999** R9.99 D99 T99 CMD-99\n```\n`AC-998` `CMD-98` `D98` `T98` ``R8.88 AC-997``\n"
            spec = self.write(directory, "spec.md", text)
            output = Path(directory) / "out.json"
            result = self.run_check("spec", spec, extra=("--out", str(output)))
            self.assertEqual(1, result.returncode)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertFalse(any(cell["kind"] == "참조 무결성" for cell in payload["cells"]))
            self.assertTrue(any(cell["kind"] == "AC→판정수단" and cell["key"] == "AC-2" and cell["status"] == "empty" for cell in payload["cells"]))
            parsed = revision_check.parse_document(text)
            for identifier in ("AC-999", "AC-998", "AC-997", "R9.99", "R8.88", "D99", "D98", "T98", "CMD-99", "CMD-98"):
                self.assertNotIn(identifier, set().union(*(
                    set(parsed[name]) for name in ("requirements", "acceptance_criteria", "decisions", "tasks", "commands")
                )), identifier)
            self.assertNotIn("T99", parsed["tasks"])
            self.assertNotIn("T99", parsed["references"])

    def test_missing_spec_traceability_marks_every_requirement_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            for name, text in (
                ("no-section", SPEC_COMPLETE.replace("## Requirements traceability", "## Mapping")),
                ("no-rows", "\n".join(line for line in SPEC_COMPLETE.splitlines() if not line.startswith("| R"))),
            ):
                spec = self.write(directory, f"{name}.md", text)
                output = Path(directory) / f"{name}.json"
                result = self.run_check("spec", spec, extra=("--out", str(output)))
                payload = json.loads(output.read_text())
                self.assertEqual(1, result.returncode)
                self.assertEqual(4, sum(cell["kind"] == "R→추적행" and cell["status"] == "empty" for cell in payload["cells"]))
            for heading in ("## Requirements traceability", "## 요구사항 추적표"):
                spec = self.write(directory, "heading.md", SPEC_COMPLETE.replace("## Requirements traceability", heading))
                output = Path(directory) / "heading.json"
                self.assertEqual(0, self.run_check("spec", spec, extra=("--out", str(output))).returncode)
                self.assertFalse(any(cell["kind"] == "R→추적행" and cell["status"] == "empty" for cell in json.loads(output.read_text())["cells"]))

    def test_check_is_read_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec = self.write(root, "spec.md", SPEC_COMPLETE)
            plan = self.write(root, "plan.md", PLAN_COMPLETE)
            base = self.write(root, "base.md", SPEC_COMPLETE)
            notes = self.write(root, "spec-revision-notes.md", "## 라운드 2 개정\n")
            state = self.write(root, "state.json", json.dumps({"rounds": {"spec": 0}, "reviews": {"spec": []}}))
            snapshots = root / "snapshots"
            snapshots.mkdir()
            snapshot = self.write(snapshots, "spec-r1.md", SPEC_COMPLETE)
            before = {
                path.relative_to(root): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in root.rglob("*") if path.is_file()
            }
            output = root / "out.json"
            self.assertEqual(0, self.run_check("spec", spec, extra=("--base", str(base), "--notes", str(notes), "--out", str(output))).returncode)
            self.assertEqual(0, self.run_check("plan", plan, spec=spec, extra=("--out", str(output))).returncode)
            after = {
                path.relative_to(root): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in root.rglob("*") if path.is_file() and path != output
            }
            self.assertEqual(before, after)
            self.assertEqual({output.relative_to(root)}, {path.relative_to(root) for path in root.rglob("*") if path.is_file()} - set(before))
            source = SCRIPT.read_text(encoding="utf-8")
            for forbidden in ("subprocess", "socket", "urllib", "http"):
                self.assertNotRegex(source, rf"(?m)^\s*(?:import|from)\s+{forbidden}\b")

    def test_requirement_without_trace_row_or_ac_is_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            no_row = self.write(directory, "no-row.md", SPEC_COMPLETE.replace("| R3.1 | AC-7, AC-8 |\n", ""))
            no_ac = self.write(directory, "no-ac.md", SPEC_COMPLETE.replace("| R3.1 | AC-7, AC-8 |", "| R3.1 |"))
            unknown_ac = self.write(directory, "unknown-ac.md", SPEC_COMPLETE.replace("| R3.1 | AC-7, AC-8 |", "| R3.1 | AC-999 |"))
            for spec, kind in ((no_row, "R→추적행"), (no_ac, "R→AC"), (unknown_ac, "추적행 AC 존재")):
                output = Path(directory) / f"{spec.stem}.json"
                self.run_check("spec", spec, extra=("--out", str(output)))
                self.assertTrue(any(cell["kind"] == kind and cell["status"] == "empty" for cell in json.loads(output.read_text())["cells"]))

    def test_ghost_trace_row_and_count_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            spec = self.write(directory, "spec.md", SPEC_COMPLETE.replace("## Verification commands", "| R9.9 | AC-7 |\n## Verification commands"))
            output = Path(directory) / "out.json"
            self.run_check("spec", spec, extra=("--out", str(output)))
            cells = json.loads(output.read_text())["cells"]
            self.assertTrue(any(cell["kind"] == "추적행→R" and cell["status"] == "empty" for cell in cells))
            self.assertTrue(any(cell["kind"] == "R 수=추적 행 수" and cell["status"] == "empty" for cell in cells))

    def test_orphan_ac_and_missing_means(self):
        import revision_check

        with tempfile.TemporaryDirectory() as directory:
            spec = self.write(directory, "spec.md", SPEC_COMPLETE.replace("- **AC-8** Eighth. [문서] `docs/eight.md`", "- **AC-8** Eighth.").replace(", AC-8", ""))
            output = Path(directory) / "out.json"
            self.run_check("spec", spec, extra=("--out", str(output)))
            cells = json.loads(output.read_text())["cells"]
            self.assertTrue(any(cell["kind"] == "AC→R" and cell["key"] == "AC-8" and cell["status"] == "empty" for cell in cells))
            self.assertTrue(any(cell["kind"] == "AC→판정수단" and cell["key"] == "AC-8" and cell["status"] == "empty" for cell in cells))
            self.assertFalse(any(cell["kind"] == "AC→CMD 존재" and cell["key"] == "AC-8" for cell in cells))
            self.assertEqual([], revision_check.judgement_means("[문서] § 판정"))
            self.assertEqual(
                ["docs/last.md"],
                revision_check.judgement_means("[문서] `docs/first.md` [문서] `docs/last.md`"),
            )

    def test_execution_ac_requires_cmd_row(self):
        with tempfile.TemporaryDirectory() as directory:
            spec = self.write(directory, "spec.md", SPEC_COMPLETE.replace("CMD-1 -k test_alpha", "CMD-9 -k test_alpha"))
            output = Path(directory) / "out.json"
            self.run_check("spec", spec, extra=("--out", str(output)))
            self.assertTrue(any(cell["kind"] == "AC→CMD 존재" and cell["status"] == "empty" for cell in json.loads(output.read_text())["cells"]))

    def test_ac_numbering_gap_and_duplicate_definition(self):
        with tempfile.TemporaryDirectory() as directory:
            spec = self.write(directory, "spec.md", SPEC_COMPLETE.replace("- **AC-3**", "- **AC-4**", 1))
            output = Path(directory) / "out.json"
            self.run_check("spec", spec, extra=("--out", str(output)))
            cells = json.loads(output.read_text())["cells"]
            self.assertTrue(any(cell["kind"] == "AC 번호 연속" and cell["status"] == "empty" for cell in cells))
            duplicate = self.write(directory, "duplicate.md", SPEC_COMPLETE + "- **AC-8** duplicate. [문서] `docs/eight.md`\n")
            self.run_check("spec", duplicate, extra=("--out", str(output)))
            self.assertTrue(any(
                cell["kind"] == "중복 정의" and cell["key"] == "AC-8" and cell["status"] == "empty"
                for cell in json.loads(output.read_text())["cells"]
            ))
            for identifier, definition in (
                ("R1.1", "- **R1.1** First requirement."),
                ("AC-3", "- **AC-3** Third. [문서] `docs/three.md`"),
            ):
                duplicate = self.write(
                    directory,
                    f"duplicate-{identifier}.md",
                    SPEC_COMPLETE.replace(definition, f"{definition}\n{definition}"),
                )
                self.run_check("spec", duplicate, extra=("--out", str(output)))
                self.assertTrue(any(
                    cell["kind"] == "중복 정의" and cell["key"] == identifier and cell["status"] == "empty"
                    for cell in json.loads(output.read_text())["cells"]
                ), identifier)

    def test_dangling_reference_is_empty_cell(self):
        with tempfile.TemporaryDirectory() as directory:
            spec = self.write(directory, "spec.md", SPEC_COMPLETE + "\nAC-77 D9 R7.7 CMD-9\nAC-77\n")
            output = Path(directory) / "out.json"
            self.run_check("spec", spec, extra=("--out", str(output)))
            cells = json.loads(output.read_text())["cells"]
            dangling = [cell for cell in cells if cell["kind"] == "참조 무결성" and cell["status"] == "empty"]
            self.assertEqual({"AC-77", "D9", "R7.7", "CMD-9"}, {cell["key"] for cell in dangling})
            ac = next(cell for cell in dangling if cell["key"] == "AC-77")
            self.assertIn("2", ac["detail"])
            self.assertEqual(spec.read_text(encoding="utf-8").splitlines().index("AC-77 D9 R7.7 CMD-9") + 1, ac["line"])

    def test_id_grammar_recognizes_all_definition_forms(self):
        import revision_check

        for fixture in (
            "spec-complete.md", "plan-complete.md", "plan-plan06-shape.md",
            "spec-revision-notes-round2.md", "spec-revision-notes-no-round2.md",
        ):
            self.assertTrue((FIXTURE_DIR / fixture).read_text(encoding="utf-8"))
        document = revision_check.parse_document(SPEC_COMPLETE)
        plan = revision_check.parse_plan(PLAN_COMPLETE)
        self.assertEqual(4, len(document["requirements"]))
        self.assertEqual(8, len(document["acceptance_criteria"]))
        self.assertEqual(2, len(document["decisions"]))
        self.assertEqual(3, len(plan["tasks"]))
        self.assertEqual(2, len(document["commands"]))
        self.assertEqual(2, len(plan["commands"]))
        self.assertEqual(4, len(document["trace_rows"]))
        self.assertIn("CMD-1", plan["commands"])
        self.assertIn("CMD-2", plan["commands"])
        command_rows = [
            [cell.strip() for cell in line.strip().strip("|").split("|")]
            for line in PLAN_COMPLETE.splitlines() if line.startswith("|") and "CMD-" in line
        ]
        self.assertTrue(any(row[0] == "CMD-1" for row in command_rows))
        self.assertTrue(any(len(row) > 1 and row[1] == "CMD-2" for row in command_rows))

    def test_plan_ac_set_equals_spec(self):
        with tempfile.TemporaryDirectory() as directory:
            spec = self.write(directory, "spec.md", SPEC_COMPLETE)
            plan = self.write(directory, "plan.md", PLAN_COMPLETE.replace("| AC-8 |", "| AC-9 |"))
            output = Path(directory) / "out.json"
            self.run_check("plan", plan, spec=spec, extra=("--out", str(output)))
            kinds = {item["kind"] for item in json.loads(output.read_text())["cells"] if item["status"] == "empty"}
            self.assertIn("Spec AC→Plan 추적행", kinds)
            self.assertIn("Plan 추적행→Spec AC", kinds)

    def test_task_target_list_symmetry(self):
        with tempfile.TemporaryDirectory() as directory:
            spec = self.write(directory, "spec.md", SPEC_COMPLETE)
            plan = self.write(directory, "plan.md", PLAN_COMPLETE.replace("대상 AC: AC-1, AC-2", "대상 AC: AC-2"))
            output = Path(directory) / "out.json"
            self.run_check("plan", plan, spec=spec, extra=("--out", str(output)))
            cells = json.loads(output.read_text())["cells"]
            self.assertTrue(any(item["kind"] == "추적행→태스크 대상 AC" and item["key"] == "AC-1" and item["status"] == "empty" for item in cells))
            for name, text, kind in (
                ("reverse", PLAN_COMPLETE.replace("대상 AC: AC-1, AC-2", "대상 AC: AC-1, AC-2, AC-9"), "태스크 대상 AC→추적행"),
                ("unknown", PLAN_COMPLETE.replace("| AC-1 | T1 |", "| AC-1 | T9 |"), "태스크 존재"),
                ("blank", PLAN_COMPLETE.replace("| AC-1 | T1 |", "| AC-1 |  |"), "AC→태스크"),
            ):
                candidate = self.write(directory, f"{name}.md", text)
                self.run_check("plan", candidate, spec=spec, extra=("--out", str(output)))
                self.assertTrue(any(item["kind"] == kind and item["status"] == "empty" for item in json.loads(output.read_text())["cells"]), name)
            no_task_id = self.write(directory, "no-task-id.md", PLAN_COMPLETE.replace("| AC-2 | T1 |", "| AC-2 | 나중에 |"))
            self.run_check("plan", no_task_id, spec=spec, extra=("--out", str(output)))
            self.assertTrue(any(
                item["kind"] == "AC→태스크" and item["key"] == "AC-2" and item["status"] == "empty"
                for item in json.loads(output.read_text())["cells"]
            ))

    def test_same_line_rule_catches_plan_06_shape(self):
        with tempfile.TemporaryDirectory() as directory:
            spec = self.write(directory, "spec.md", SPEC_COMPLETE)
            plan = FIXTURE_DIR / "plan-plan06-shape.md"
            output = Path(directory) / "out.json"
            self.run_check("plan", plan, spec=spec, extra=("--out", str(output)))
            self.assertTrue(any(
                item["kind"] == "AC 등장 행에 판정수단 동반"
                and item["key"] == "AC-1"
                and item["status"] == "empty"
                and "spec.md" in item["detail"]
                for item in json.loads(output.read_text())["cells"]
            ))

    def test_last_task_section_ends_at_next_level_two_heading(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = (Path(__file__).parent / "fixtures" / "revision-check" / "plan-plan06-shape.md").read_text(encoding="utf-8")
            last_task = fixture.replace(
                "# PLAN-06 fixture\n\nThe traceability evidence is deliberately not co-located with its AC line.\n",
                "### T3. PLAN-06 shape\n대상 AC: AC-6, AC-7, AC-8\nAC-6 `docs/six.md`\nAC-7 `docs/seven.md`\nAC-8 `docs/quality-goal-maintenance.md`\nspec.md elsewhere\n",
            )
            plan_text = PLAN_COMPLETE.replace(
                "### T3. Third\n대상 AC: AC-6, AC-7, AC-8\nAC-6 `docs/six.md`\nAC-7 `docs/seven.md`\nAC-8 `docs/eight.md`\n",
                last_task,
            ).replace("| AC-8 | T3 | `docs/eight.md` |", "| AC-8 | T3 | `spec.md` |")
            spec = self.write(directory, "spec.md", SPEC_COMPLETE)
            plan = self.write(directory, "plan.md", plan_text)
            output = Path(directory) / "out.json"
            result = self.run_check("plan", plan, spec=spec, extra=("--out", str(output)))
            cells = json.loads(output.read_text(encoding="utf-8"))["cells"]
            self.assertEqual(1, result.returncode)
            self.assertTrue(any(
                item["kind"] == "AC 등장 행에 판정수단 동반"
                and item["key"] == "AC-8"
                and item["status"] == "empty"
                and "spec.md" in item["detail"]
                for item in cells
            ))

    def test_same_line_rule_accepts_colocated_means(self):
        with tempfile.TemporaryDirectory() as directory:
            spec = self.write(directory, "spec.md", SPEC_COMPLETE)
            plan = self.write(directory, "plan.md", PLAN_COMPLETE)
            output = Path(directory) / "out.json"
            self.assertEqual(0, self.run_check("plan", plan, spec=spec, extra=("--out", str(output))).returncode)
            self.assertTrue(any(item["kind"] == "AC 등장 행에 판정수단 동반" and item["status"] == "ok" for item in json.loads(output.read_text())["cells"]))
            partial = self.write(directory, "partial.md", PLAN_COMPLETE.replace("AC-1 `docs/one.md`", "AC-10 `docs/one.md`"))
            self.run_check("plan", partial, spec=spec, extra=("--out", str(output)))
            self.assertTrue(any(
                item["kind"] == "AC 등장 행에 판정수단 동반"
                and item["key"] == "AC-1"
                and item["status"] == "empty"
                for item in json.loads(output.read_text())["cells"]
            ))
            colocated = self.write(
                directory,
                "colocated.md",
                PLAN_COMPLETE.replace("AC-2 `CMD-1` `test_alpha`", "AC-2 `CMD-2 -k test_alpha`").replace(
                    "| AC-2 | T1 | `CMD-1` `test_alpha` |", "| AC-2 | T1 | `CMD-2 -k test_alpha` |"
                ),
            )
            self.assertEqual(0, self.run_check("plan", colocated, spec=spec, extra=("--out", str(output))).returncode)
            for token in ("CMD-2", "test_alpha"):
                missing = self.write(directory, f"missing-{token}.md", colocated.read_text(encoding="utf-8").replace(token, "other", 1))
                self.run_check("plan", missing, spec=spec, extra=("--out", str(output)))
                cell = next(item for item in json.loads(output.read_text())["cells"] if item["kind"] == "AC 등장 행에 판정수단 동반" and item["key"] == "AC-2" and item["status"] == "empty")
                self.assertIn(token, cell["detail"])

    def test_plan_cmd_and_reference_integrity(self):
        with tempfile.TemporaryDirectory() as directory:
            spec = self.write(directory, "spec.md", SPEC_COMPLETE)
            plan = self.write(
                directory,
                "plan.md",
                PLAN_COMPLETE.replace(
                    "AC-2 `CMD-1` `test_alpha`",
                    "AC-2 `CMD-1` `test_alpha`\nTask-only command reference `CMD-7`",
                ).replace("| AC-2 | T1 | `CMD-1` `test_alpha` |", "| AC-2 | T1 | `CMD-8` `test_alpha` |") + "\nT12 AC-66 R6.6 D6\n",
            )
            output = Path(directory) / "out.json"
            self.run_check("plan", plan, spec=spec, extra=("--out", str(output)))
            cells = json.loads(output.read_text())["cells"]
            kinds = {item["kind"] for item in cells if item["status"] == "empty"}
            self.assertIn("추적행 CMD 존재", kinds)
            self.assertIn("참조 무결성", kinds)
            self.assertTrue(any(
                item["kind"] == "참조 무결성"
                and item["key"] == "CMD-7"
                and item["status"] == "empty"
                for item in cells
            ))
            self.assertEqual(
                {"CMD-7", "T12", "AC-66", "R6.6", "D6"},
                {item["key"] for item in cells if item["kind"] == "참조 무결성" and item["status"] == "empty"},
            )

    def test_definition_floor_blocks_empty_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            spec = self.write(directory, "spec.md", SPEC_COMPLETE)
            plan = self.write(directory, "plan.md", PLAN_COMPLETE)
            cases = (
                ("spec", self.write(directory, "no-requirements.md", "\n".join(line for line in SPEC_COMPLETE.splitlines() if not line.startswith("- **R"))), None),
                ("spec", self.write(directory, "no-ac.md", "\n".join(line for line in SPEC_COMPLETE.splitlines() if not line.startswith("- **AC-"))), None),
                ("plan", self.write(directory, "no-tasks.md", "\n".join(line for line in PLAN_COMPLETE.splitlines() if not line.startswith("### T"))), spec),
                ("plan", self.write(directory, "no-trace.md", "\n".join(line for line in PLAN_COMPLETE.splitlines() if not line.startswith("| AC-"))), spec),
            )
            for artifact, current, companion in cases:
                output = Path(directory) / f"{artifact}.json"
                result = self.run_check(artifact, current, spec=companion, extra=("--out", str(output)))
                payload = json.loads(output.read_text())
                self.assertEqual(1, result.returncode)
                self.assertEqual(1, sum(item["kind"] == "문법 미충족" and item["status"] == "empty" for item in payload["cells"]))
                self.assertFalse(payload["passed"])
            invalid = self.write(directory, "invalid-with-notes.md", "\n".join(line for line in SPEC_COMPLETE.splitlines() if not line.startswith("- **AC-")))
            snapshot_dir = Path(directory) / "snapshots"
            snapshot_dir.mkdir(exist_ok=True)
            snapshot = self.write(snapshot_dir, "spec-r1.md", invalid.read_text(encoding="utf-8"))
            state = self.write(directory, "state-with-notes.json", json.dumps({
                "rounds": {"spec": 1},
                "reviews": {"spec": [{"artifact_digest": hashlib.sha256(snapshot.read_bytes()).hexdigest()}]},
            }))
            notes = self.write(directory, "complete-notes.md", "## 라운드 2 개정\n\n" + NOTE_HEADER + "\n| --- | --- | --- | --- | --- |\n")
            output = Path(directory) / "invalid-with-notes.json"
            result = self.run_check("spec", invalid, extra=("--state", str(state), "--notes", str(notes), "--out", str(output)))
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(1, result.returncode)
            self.assertTrue(payload["notes"]["section_found"])
            self.assertFalse(payload["passed"])

    def test_verification_cell_reads_inside_code_spans(self):
        with tempfile.TemporaryDirectory() as directory:
            spec = self.write(directory, "spec.md", SPEC_COMPLETE)
            plan = self.write(directory, "plan.md", PLAN_COMPLETE.replace("| CMD-1 | test command |", "| CMD-9 | test command |"))
            output = Path(directory) / "out.json"
            self.run_check("plan", plan, spec=spec, extra=("--out", str(output)))
            self.assertTrue(any(item["kind"] == "추적행 CMD 존재" and item["status"] == "empty" for item in json.loads(output.read_text())["cells"]))
            only_code = PLAN_COMPLETE.replace(
                "AC-1 `docs/one.md`",
                "AC-1 `CMD-7` `docs/quality-goal-maintenance.md`",
            ).replace(
                "| AC-1 | T1 | `docs/one.md` | ok |",
                "| AC-1 | T1 | `CMD-7` `docs/quality-goal-maintenance.md` § 판정 | ok |",
            )
            missing = self.write(directory, "only-code-missing.md", only_code)
            self.run_check("plan", missing, spec=spec, extra=("--out", str(output)))
            cells = json.loads(output.read_text(encoding="utf-8"))["cells"]
            self.assertTrue(any(item["kind"] == "추적행 CMD 존재" and item["key"] == "AC-1" and item["status"] == "empty" for item in cells))
            present = self.write(directory, "only-code-present.md", only_code.replace("| CMD-1 | test command |", "| CMD-7 | test command |"))
            self.run_check("plan", present, spec=spec, extra=("--out", str(output)))
            cells = json.loads(output.read_text(encoding="utf-8"))["cells"]
            self.assertTrue(any(item["kind"] == "추적행 CMD 존재" and item["key"] == "AC-1" and item["status"] == "ok" for item in cells))
            import revision_check
            tokens = revision_check.token_list("`CMD-7` `docs/quality-goal-maintenance.md` § 판정")
            self.assertEqual(["CMD-7", "docs/quality-goal-maintenance.md"], tokens)
            self.assertNotIn("§", tokens)
            self.assertNotIn("판정", tokens)

class RevisionDiffTests(RevisionCheckTests):
    def state_file(self, directory, artifact, prior_round, base):
        snapshot_dir = Path(directory) / "snapshots"
        snapshot_dir.mkdir(exist_ok=True)
        snapshot = snapshot_dir / f"{artifact}-r{prior_round}.md"
        snapshot.write_text(base, encoding="utf-8")
        value = {
            "rounds": {"spec": 0, "plan": 0, "code": 0},
            "reviews": {"spec": [], "plan": [], "code": []},
            "artifacts": {"spec": None, "plan": None},
        }
        value["rounds"][artifact] = prior_round
        value["reviews"][artifact] = [{"artifact_digest": hashlib.sha256(snapshot.read_bytes()).hexdigest()}]
        return self.write(directory, "state.json", json.dumps(value))

    def payload_with_base(self, directory, artifact, current, base, *, spec=None, state=False, notes=None):
        output = Path(directory) / "out.json"
        extra = ["--out", str(output)]
        if state:
            extra += ["--state", str(self.state_file(directory, artifact, 1, base))]
        else:
            base_path = self.write(directory, "base.md", base)
            extra += ["--base", str(base_path)]
        if notes is not None:
            extra += ["--notes", str(notes)]
        result = self.run_check(artifact, current, spec=spec, extra=tuple(extra))
        return result, json.loads(output.read_text(encoding="utf-8"))

    def test_stdout_prints_ripple_and_empty_cell_tables(self):
        with tempfile.TemporaryDirectory() as directory:
            current = self.write(directory, "spec.md", SPEC_COMPLETE.replace("First.", "Changed.").replace("[문서] `docs/one.md`", ""))
            result, payload = self.payload_with_base(directory, "spec", current, SPEC_COMPLETE)
            lines = [line for line in result.stdout.splitlines() if line.strip()]
            self.assertTrue(all(line.startswith(("#", "|")) for line in lines))
            self.assertIn("| 종류 | 키 | 상태 | 상세 | 행 |", lines)
            self.assertIn("| 요구사항 | 판정 AC | Plan 추적행 | 태스크 | 판정 명령/테스트 |", lines)
            cell_rows = {
                tuple(value.strip() for value in line.strip("|").split("|"))
                for line in lines[lines.index("| 종류 | 키 | 상태 | 상세 | 행 |") + 1:lines.index("# 파급표")]
            }
            expected_cells = {
                (item["kind"], item["key"], "empty", item["detail"], str(item["line"] or ""))
                for item in payload["cells"] if item["status"] == "empty"
            }
            self.assertEqual(expected_cells, cell_rows)
            ripple_rows = {
                tuple(value.strip() for value in line.strip("|").split("|"))
                for line in lines[lines.index("| 요구사항 | 판정 AC | Plan 추적행 | 태스크 | 판정 명령/테스트 |") + 1:]
            }
            expected_ripple = {
                (item["requirement"], ", ".join(item["acceptance_criteria"]), "**빈 칸**", "**빈 칸**", ", ".join(item["commands"]))
                for item in payload["ripple"]
            }
            self.assertEqual(expected_ripple, ripple_rows)
            self.assertIn("**빈 칸**", result.stdout)
            self.assertEqual(["R1.1"], payload["touched_requirements"])

    def test_base_snapshot_located_and_digest_checked(self):
        with tempfile.TemporaryDirectory() as directory:
            for artifact, source, current_text in (
                ("spec", SPEC_COMPLETE, SPEC_COMPLETE.replace("First.", "Changed.")),
                ("plan", PLAN_COMPLETE, PLAN_COMPLETE.replace("AC-1 `docs/one.md`", "AC-1 `docs/changed.md`")),
            ):
                with self.subTest(artifact=artifact):
                    current = self.write(directory, f"{artifact}.md", current_text)
                    spec = self.write(directory, "companion-spec.md", SPEC_COMPLETE)
                    result, payload = self.payload_with_base(directory, artifact, current, source, spec=spec if artifact == "plan" else None, state=True)
                    self.assertEqual(1, result.returncode)
                    self.assertEqual(2, payload["round"])
                    self.assertEqual(hashlib.sha256(source.encode()).hexdigest(), payload["base_digest"])
                    state = Path(directory) / "state.json"
                    snapshot = Path(directory) / "snapshots" / f"{artifact}-r1.md"
                    snapshot.write_text("wrong\n", encoding="utf-8")
                    self.assertEqual(2, self.run_check(artifact, current, spec=spec if artifact == "plan" else None, extra=("--state", str(state))).returncode)
                    snapshot.unlink()
                    self.assertEqual(2, self.run_check(artifact, current, spec=spec if artifact == "plan" else None, extra=("--state", str(state))).returncode)
            current = self.write(directory, "round-three.md", SPEC_COMPLETE.replace("First.", "Changed."))
            state = self.state_file(directory, "spec", 1, SPEC_COMPLETE)
            payload = json.loads(state.read_text())
            payload["rounds"]["spec"] = 2
            snapshot = Path(directory) / "snapshots" / "spec-r2.md"
            snapshot.write_text(SPEC_COMPLETE, encoding="utf-8")
            payload["reviews"]["spec"] = [{"artifact_digest": hashlib.sha256(snapshot.read_bytes()).hexdigest()}]
            state.write_text(json.dumps(payload), encoding="utf-8")
            output = Path(directory) / "round-three.json"
            self.assertEqual(1, self.run_check("spec", current, extra=("--state", str(state), "--out", str(output))).returncode)
            self.assertEqual(3, json.loads(output.read_text())["round"])

    def test_round_one_has_no_base_and_no_notes_requirement(self):
        with tempfile.TemporaryDirectory() as directory:
            for artifact, text in (("spec", SPEC_COMPLETE), ("plan", PLAN_COMPLETE)):
                with self.subTest(artifact=artifact):
                    current = self.write(directory, f"{artifact}.md", text)
                    spec = self.write(directory, "companion.md", SPEC_COMPLETE)
                    state = self.write(directory, f"{artifact}-state.json", json.dumps({"rounds": {artifact: 0}}))
                    output = Path(directory) / f"{artifact}-out.json"
                    result = self.run_check(artifact, current, spec=spec if artifact == "plan" else None, extra=("--state", str(state), "--out", str(output)))
                    payload = json.loads(output.read_text())
                    self.assertEqual(0, result.returncode)
                    self.assertEqual(1, payload["round"])
                    self.assertIsNone(payload["base_digest"])
                    self.assertEqual([], payload["touched_requirements"])
                    self.assertFalse(payload["notes"]["required"])

    def test_touched_requirements_from_diff_spec(self):
        with tempfile.TemporaryDirectory() as directory:
            cases = (
                (SPEC_COMPLETE.replace("Third requirement.", "Changed requirement."), ["R2.1"]),
                (SPEC_COMPLETE.replace("Fifth.", "Changed."), ["R2.1"]),
                (SPEC_COMPLETE.replace("| R3.1 | AC-7, AC-8 |", "| R3.1 | AC-7 |"), ["R3.1"]),
                (SPEC_COMPLETE.replace("- **R3.1** Fourth requirement.", "- **R3.1** Fourth requirement.\nInserted R3 detail."), ["R3.1"]),
            )
            for text, expected in cases:
                current = self.write(directory, "spec.md", text)
                _, payload = self.payload_with_base(directory, "spec", current, SPEC_COMPLETE)
                self.assertEqual(expected, payload["touched_requirements"])
            expanded = SPEC_COMPLETE.replace("- **R3.1** Fourth requirement.\n", "- **R3.1** Fourth requirement.\n- **R4.2** Removable requirement.\n").replace("- **AC-8** Eighth. [문서] `docs/eight.md`", "- **AC-8** Eighth. [문서] `docs/eight.md`\n- **AC-9** Removable. [문서] `docs/nine.md`")
            removed = self.write(directory, "removed.md", expanded.replace("- **R4.2** Removable requirement.\n", "").replace("- **AC-9** Removable. [문서] `docs/nine.md`\n", ""))
            _, removed_payload = self.payload_with_base(directory, "spec", removed, expanded)
            self.assertEqual({"R4.2", "AC-9"}, set(removed_payload["removed_ids"]))
            self.assertIn("R4.2", removed_payload["touched_requirements"])
            removed = self.write(directory, "removed-ac.md", SPEC_COMPLETE.replace("- **AC-8** Eighth. [문서] `docs/eight.md`\n", ""))
            _, removed_payload = self.payload_with_base(directory, "spec", removed, SPEC_COMPLETE)
            self.assertIn("AC-8", removed_payload["removed_ids"])

    def test_touched_requirements_from_diff_plan(self):
        with tempfile.TemporaryDirectory() as directory:
            spec = self.write(directory, "spec.md", SPEC_COMPLETE)
            current = self.write(directory, "plan.md", PLAN_COMPLETE.replace("| AC-7 | T3 | `docs/seven.md` | ok |", "| AC-7 | T3 | `docs/changed.md` | ok |"))
            _, payload = self.payload_with_base(directory, "plan", current, PLAN_COMPLETE, spec=spec)
            self.assertEqual(["R3.1"], payload["touched_requirements"])
            current = self.write(directory, "task-change.md", PLAN_COMPLETE.replace("AC-3 `docs/three.md`", "AC-3 `docs/changed.md`"))
            _, payload = self.payload_with_base(directory, "plan", current, PLAN_COMPLETE, spec=spec)
            self.assertEqual({"R1.2", "R2.1"}, set(payload["touched_requirements"]))
            current = self.write(directory, "t3-change.md", PLAN_COMPLETE.replace("AC-7 `docs/seven.md`", "AC-7 `docs/changed.md`"))
            _, payload = self.payload_with_base(directory, "plan", current, PLAN_COMPLETE, spec=spec)
            self.assertEqual({"R2.1", "R3.1"}, set(payload["touched_requirements"]))
            removed = self.write(directory, "removed-plan.md", PLAN_COMPLETE.replace("### T3. Third\n\n대상 AC: AC-6, AC-7, AC-8\nAC-6 `docs/six.md`\nAC-7 `docs/seven.md`\nAC-8 `docs/eight.md`\n\n", "").replace("| command | CMD-2 | second command |\n", ""))
            _, payload = self.payload_with_base(directory, "plan", removed, PLAN_COMPLETE, spec=spec)
            self.assertEqual({"T3", "CMD-2"}, set(payload["removed_ids"]))

    def test_ripple_row_per_touched_requirement_with_empty_marking(self):
        with tempfile.TemporaryDirectory() as directory:
            current = self.write(directory, "spec.md", SPEC_COMPLETE.replace("First.", "Changed."))
            _, payload = self.payload_with_base(directory, "spec", current, SPEC_COMPLETE)
            self.assertEqual(1, len(payload["ripple"]))
            self.assertEqual("R1.1", payload["ripple"][0]["requirement"])
            self.assertIsNone(payload["ripple"][0]["plan_rows"])
            self.assertEqual(["AC-1", "AC-2"], payload["ripple"][0]["acceptance_criteria"])
            self.assertEqual(["docs/one.md", "CMD-1", "test_alpha"], payload["ripple"][0]["commands"])
            plan = self.write(directory, "plan.md", PLAN_COMPLETE.replace("AC-7 `docs/seven.md`", "AC-7 `docs/changed.md`"))
            spec = self.write(directory, "companion.md", SPEC_COMPLETE)
            _, plan_payload = self.payload_with_base(directory, "plan", plan, PLAN_COMPLETE, spec=spec)
            self.assertEqual([
                {
                    "requirement": "R2.1", "acceptance_criteria": ["AC-5", "AC-6"],
                    "plan_rows": [38, 39], "tasks": ["T2", "T3"],
                    "commands": ["docs/five.md", "docs/six.md"],
                },
                {
                    "requirement": "R3.1", "acceptance_criteria": ["AC-7", "AC-8"],
                    "plan_rows": [40, 41], "tasks": ["T3"],
                    "commands": ["docs/seven.md", "docs/eight.md"],
                },
            ], plan_payload["ripple"])
            no_ac = SPEC_COMPLETE.replace("| R1.1 | AC-1, AC-2 |", "| R1.1 |")
            no_plan_rows = "\n".join(line for line in PLAN_COMPLETE.splitlines() if not line.startswith("| AC-1 |") and not line.startswith("| AC-2 |"))
            no_tasks = PLAN_COMPLETE.replace("| AC-1 | T1 |", "| AC-1 |  |").replace("| AC-2 | T1 |", "| AC-2 |  |")
            no_commands_spec = SPEC_COMPLETE.replace("[문서] `docs/one.md`", "").replace("[실행] (CMD-1 -k test_alpha)", "")
            no_commands = PLAN_COMPLETE.replace("`docs/one.md`", "").replace("`CMD-1` `test_alpha`", "")
            cases = (
                ("no-ac", "spec", no_ac.replace("First requirement.", "Changed requirement."), no_ac, None, "acceptance_criteria", []),
                ("no-plan-rows", "plan", no_plan_rows.replace("AC-1 `docs/one.md`", "AC-1 `docs/changed.md`"), no_plan_rows, spec, "plan_rows", []),
                ("no-tasks", "plan", no_tasks.replace("AC-1 `docs/one.md`", "AC-1 `docs/changed.md`"), no_tasks, spec, "tasks", []),
                ("no-commands", "plan", no_commands.replace("AC-1 \n", "AC-1 changed\n"), no_commands, self.write(directory, "no-commands-spec.md", no_commands_spec), "commands", []),
            )
            for name, artifact, current_text, base_text, companion, field, expected in cases:
                with self.subTest(empty=field):
                    current_path = self.write(directory, f"{name}.md", current_text)
                    result, empty_payload = self.payload_with_base(
                        directory, artifact, current_path, base_text, spec=companion,
                    )
                    self.assertEqual(1, result.returncode)
                    self.assertEqual(expected, empty_payload["ripple"][0][field])
                    self.assertTrue(any(cell["kind"] == "파급표" and cell["status"] == "empty" for cell in empty_payload["cells"]))
            document_only = SPEC_COMPLETE.replace("| R1.1 | AC-1, AC-2 |", "| R1.1 | AC-1 |").replace("| R1.2 | AC-3, AC-4 |", "| R1.2 | AC-2, AC-3, AC-4 |").replace("[문서] `docs/one.md`", "[문서] `docs/x.md`")
            current = self.write(directory, "document-only.md", document_only.replace("First requirement.", "Changed requirement."))
            result, document_payload = self.payload_with_base(directory, "spec", current, document_only)
            self.assertEqual(0, result.returncode)
            self.assertEqual(["docs/x.md"], document_payload["ripple"][0]["commands"])
            self.assertFalse(any(cell["kind"] == "파급표" for cell in document_payload["cells"]))

    def test_notes_section_required_from_round_two(self):
        with tempfile.TemporaryDirectory() as directory:
            current = self.write(directory, "spec.md", SPEC_COMPLETE.replace("First.", "Changed."))
            result, payload = self.payload_with_base(directory, "spec", current, SPEC_COMPLETE, state=True)
            self.assertEqual(1, result.returncode)
            self.assertTrue(payload["notes"]["required"])
            self.assertFalse(payload["notes"]["section_found"])
            self.assertFalse(payload["passed"])
            self.assertEqual(str(Path(directory, "spec-revision-notes.md").resolve()), payload["notes"]["path"])
            wrong_heading = self.write(directory, "spec-revision-notes.md", "## 라운드 3 개정\n")
            result, payload = self.payload_with_base(directory, "spec", current, SPEC_COMPLETE, state=True, notes=wrong_heading)
            self.assertEqual(1, result.returncode)
            self.assertFalse(payload["notes"]["section_found"])
            self.assertFalse(payload["passed"])
            custom = self.write(directory, "custom.md", "## 라운드 2 개정\n\n" + NOTE_HEADER + "\n| --- | --- | --- | --- | --- |\n| R1.1 | finding | AC-1(일치), AC-2(일치) | interaction | reason |\n")
            _, payload = self.payload_with_base(directory, "spec", current, SPEC_COMPLETE, state=True, notes=custom)
            self.assertEqual(str(custom.resolve()), payload["notes"]["path"])
            plan = self.write(directory, "plan.md", PLAN_COMPLETE.replace("| AC-1 | T1 | `docs/one.md` | ok |", "| AC-1 | T1 | `docs/one.md` | changed |"))
            spec = self.write(directory, "companion.md", SPEC_COMPLETE)
            result, plan_payload = self.payload_with_base(directory, "plan", plan, PLAN_COMPLETE, spec=spec, state=True)
            self.assertEqual(1, result.returncode)
            self.assertTrue(plan_payload["notes"]["required"])
            self.assertTrue(plan_payload["notes"]["path"].endswith("plan-revision-notes.md"))
            self.assertFalse(plan_payload["passed"])
            plan_notes = self.write(directory, "plan-revision-notes.md", "## 라운드 2 개정\n\n" + NOTE_HEADER + "\n| --- | --- | --- | --- | --- |\n| R1.1 | finding | AC-1(일치), AC-2(일치) | interaction | reason |\n")
            result, plan_payload = self.payload_with_base(directory, "plan", plan, PLAN_COMPLETE, spec=spec, state=True, notes=plan_notes)
            self.assertEqual(0, result.returncode)
            self.assertTrue(plan_payload["notes"]["section_found"])
            state = self.state_file(directory, "spec", 1, SPEC_COMPLETE)
            state_value = json.loads(state.read_text(encoding="utf-8"))
            state_value["rounds"]["spec"] = 2
            round_two = self.write(Path(directory) / "snapshots", "spec-r2.md", SPEC_COMPLETE)
            state_value["reviews"]["spec"] = [{"artifact_digest": hashlib.sha256(round_two.read_bytes()).hexdigest()}]
            state.write_text(json.dumps(state_value), encoding="utf-8")
            output = Path(directory) / "round-three.json"
            result = self.run_check("spec", current, extra=("--state", str(state), "--out", str(output)))
            self.assertEqual(1, result.returncode)
            round_three = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(3, round_three["round"])
            self.assertFalse(round_three["notes"]["section_found"])
            self.assertFalse(round_three["passed"])
            spec_notes = self.write(directory, "spec-revision-notes.md", "## 라운드 3 개정\n\n" + NOTE_HEADER + "\n| --- | --- | --- | --- | --- |\n| R1.1 | finding | AC-1(일치), AC-2(일치) | interaction | reason |\n")
            result = self.run_check("spec", current, extra=("--state", str(state), "--notes", str(spec_notes), "--out", str(output)))
            self.assertEqual(0, result.returncode)
            self.assertTrue(json.loads(output.read_text(encoding="utf-8"))["notes"]["section_found"])

    def test_notes_table_header_and_row_coverage(self):
        code3_rule = "`함께 바뀐 항목` 셋째 열에서 `ripple[].acceptance_criteria` 의 각 AC ID 가 단어 경계로 등장하고, 그 등장 중 하나 이상의 바로 뒤 괄호가 `일치`/`모순` 으로 시작하면 충족; 빠진 AC 는 `<R>/<AC>`, 토큰 없는 AC 는 `<R>/<AC>/판정` 을 missing_rows 에"
        import revision_check
        self.assertEqual(code3_rule, revision_check.CODE3_RULE)
        policy = (SCRIPT.parent.parent / "references" / "revision-check-policy.md").read_text(encoding="utf-8")
        self.assertIn(code3_rule, policy)
        with tempfile.TemporaryDirectory() as directory:
            current = self.write(directory, "spec.md", SPEC_COMPLETE.replace("First.", "Changed."))
            notes = self.write(directory, "notes.md", "## 라운드 2 개정\n\n" + NOTE_HEADER + "\n| --- | --- | --- | --- | --- |\n| R1.1 | finding | AC-1(일치 — related), AC-2(모순 — related) | interaction sentence | 근거 |\n")
            _, payload = self.payload_with_base(directory, "spec", current, SPEC_COMPLETE, state=True, notes=notes)
            self.assertEqual([], payload["notes"]["missing_rows"])
            for header, row, expected in (
                (NOTE_HEADER.replace("상호작용 판정", "판정"), "| R1.1 | finding | AC-1(일치), AC-2(모순) | interaction | 근거 |", "R1.1"),
                (NOTE_HEADER, "| R1.1 | finding | AC-1(일치), AC-2 | interaction | 근거 |", "R1.1/AC-2/판정"),
                (NOTE_HEADER, "| R1.1 | finding | AC-1(일치) | interaction | 근거 |", "R1.1/AC-2"),
                (NOTE_HEADER, "| R1.1 | finding | AC-10(일치) | interaction | 근거 |", "R1.1/AC-1"),
            ):
                path = self.write(directory, "broken-notes.md", f"## 라운드 2 개정\n\n{header}\n| --- | --- | --- | --- | --- |\n{row}\n")
                _, malformed = self.payload_with_base(directory, "spec", current, SPEC_COMPLETE, state=True, notes=path)
                self.assertIn(expected, malformed["notes"]["missing_rows"])

    def test_notes_blank_cell_is_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            current = self.write(directory, "spec.md", SPEC_COMPLETE.replace("First.", "Changed."))
            valid = ["R1.1", "finding", "AC-1(일치), AC-2(모순)", "interaction", "reason"]
            for index, label in enumerate(("요구사항", "해소 finding", "함께 바뀐 항목", "상호작용 판정", "치환 근거")):
                for blank in ("", "   ", "-", "—"):
                    row = valid.copy()
                    row[index] = blank
                    notes = self.write(directory, "notes.md", "## 라운드 2 개정\n\n" + NOTE_HEADER + "\n| --- | --- | --- | --- | --- |\n| " + " | ".join(row) + " |\n")
                    _, payload = self.payload_with_base(directory, "spec", current, SPEC_COMPLETE, state=True, notes=notes)
                    self.assertIn(f"R1.1/{label}", payload["notes"]["blank_cells"])
            notes = self.write(directory, "notes.md", "## 라운드 2 개정\n\n" + NOTE_HEADER + "\n| --- | --- | --- | --- | --- |\n| " + " | ".join(valid) + " |\n")
            _, payload = self.payload_with_base(directory, "spec", current, SPEC_COMPLETE, state=True, notes=notes)
            self.assertEqual([], payload["notes"]["blank_cells"])

    def test_notes_failure_sets_passed_false_and_exit_one(self):
        with tempfile.TemporaryDirectory() as directory:
            current = self.write(directory, "spec.md", SPEC_COMPLETE.replace("First.", "Changed."))
            result, payload = self.payload_with_base(directory, "spec", current, SPEC_COMPLETE, state=True)
            self.assertEqual(1, result.returncode)
            self.assertFalse(payload["passed"])
            self.assertTrue(all(item["status"] == "ok" for item in payload["cells"]))
            blank = self.write(directory, "notes.md", "## 라운드 2 개정\n\n" + NOTE_HEADER + "\n| --- | --- | --- | --- | --- |\n| R1.1 | finding | AC-1(일치), AC-2(모순) | - | reason |\n")
            result, payload = self.payload_with_base(directory, "spec", current, SPEC_COMPLETE, state=True, notes=blank)
            self.assertEqual(1, result.returncode)
            self.assertFalse(payload["passed"])
            self.assertTrue(all(item["status"] == "ok" for item in payload["cells"]))
            result, payload = self.payload_with_base(directory, "spec", current, SPEC_COMPLETE)
            self.assertEqual(0, result.returncode)
            self.assertTrue(payload["passed"])

    def test_standalone_base_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            current = self.write(directory, "spec.md", SPEC_COMPLETE.replace("First.", "Changed."))
            result, payload = self.payload_with_base(directory, "spec", current, SPEC_COMPLETE)
            self.assertEqual(0, result.returncode)
            self.assertIsNone(payload["round"])
            self.assertFalse(payload["notes"]["required"])
            self.assertEqual(hashlib.sha256(SPEC_COMPLETE.encode()).hexdigest(), payload["base_digest"])
            self.assertEqual(["R1.1"], payload["touched_requirements"])
            import quality_state
            state = quality_state.new_state("goal", "standard", directory, directory)
            state["stage"] = "SPEC_REVIEW"
            state["rounds"]["spec"] = 1
            review = self.write(directory, "review.json", json.dumps({
                "artifact": "spec", "round": 2, "score": 92, "verdict": "PASS", "blockers": [], "findings": [], "evidence": [{"claim": "ok", "location": "x", "verified": True}], "required_next_action": None,
            }))
            check = self.write(directory, "check.json", json.dumps(payload))
            with self.assertRaisesRegex(quality_state.StateError, "revision check round mismatch"):
                quality_state.record_review(state, review, "a" * 64, revision_check_path=check)


if __name__ == "__main__":
    unittest.main()
