"""Check Spec and Plan revision symmetry without mutating source artifacts."""

import argparse
import difflib
import hashlib
import json
from pathlib import Path
import re
import sys


ID_PATTERNS = {
    "requirements": r"R\d+\.\d+",
    "acceptance_criteria": r"AC-\d+",
    "decisions": r"D\d+",
    "tasks": r"T\d+",
    "commands": r"CMD-\d+",
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def without_spans(text):
    """Mask inline code while retaining positions for judgement extraction."""
    return re.sub(r"``.*?``|`[^`]*`", lambda match: " " * len(match.group()), text)


def token_list(text):
    text = text.replace("`", "")
    return [
        part for part in text.split()
        if re.fullmatch(r"CMD-\d+", part)
        or re.fullmatch(r"test_\w+", part)
        or re.fullmatch(r"[\w./-]+\.[A-Za-z0-9]+", part)
    ]


def judgement_means(ac_text):
    masked = without_spans(ac_text)
    matches = list(re.finditer(r"\[(실행|문서)\]", masked))
    if not matches:
        return []
    marker = matches[-1]
    if marker.group(1) == "실행":
        remainder = ac_text[marker.end():]
        match = re.search(r"\(([^)]*)\)", remainder)
        return token_list(match.group(1)) if match else []
    return token_list(ac_text[marker.end():])


def _fenced_lines(lines):
    in_fence = False
    for number, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            yield number, line, True
        else:
            yield number, line, in_fence


def parse_document(text):
    """Parse policy identifiers and the Spec requirement traceability table."""
    lines = text.splitlines()
    result = {
        "lines": lines,
        "requirements": {}, "acceptance_criteria": {}, "decisions": {},
        "tasks": {}, "commands": {}, "references": {}, "trace_rows": [],
    }
    trace_section = False
    for number, line, fenced in _fenced_lines(lines):
        if fenced:
            continue
        if re.match(r"^##\s+", line):
            trace_section = bool(re.search(r"traceability|추적", line, re.I))
        definitions = (
            ("requirements", re.match(r"^- \*\*(R\d+\.\d+)\*\*", line)),
            ("acceptance_criteria", re.match(r"^- \*\*(AC-\d+)\*\*", line)),
            ("decisions", re.match(r"^### (D\d+)\.", line)),
            ("tasks", re.match(r"^### (T\d+)\.", line)),
        )
        for collection, match in definitions:
            if match:
                result[collection].setdefault(match.group(1), []).append({"line": number, "text": line})
        if "|" in line:
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            command = next((cell for cell in cells[:2] if re.fullmatch(r"CMD-\d+", cell)), None)
            if command:
                result["commands"].setdefault(command, []).append({"line": number, "text": line})
            if trace_section and cells and re.fullmatch(r"R\d+\.\d+", cells[0]):
                result["trace_rows"].append({
                    "requirement": cells[0],
                    "acceptance_criteria": re.findall(r"AC-\d+", line),
                    "line": number, "text": line,
                })
        masked = without_spans(line)
        for pattern in ID_PATTERNS.values():
            for token in re.findall(rf"\b{pattern}\b", masked):
                result["references"].setdefault(token, []).append(number)
    return result


def parse_plan(text):
    document = parse_document(text)
    rows = []
    task_bodies = {}
    active_task = None
    in_traceability = False
    for number, line, fenced in _fenced_lines(document["lines"]):
        if fenced:
            continue
        heading = re.match(r"^### (T\d+)\.", line)
        if heading:
            active_task = heading.group(1)
            task_bodies[active_task] = []
        elif re.match(r"^##\s+|^###\s+", line):
            active_task = None
        elif active_task is not None:
            task_bodies[active_task].append((number, line))
        if line.startswith("|") and re.search(r"\bCriterion\b", line, re.I) and re.search(r"\bTask\b", line, re.I):
            in_traceability = True
            continue
        if in_traceability and line.startswith("|"):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if cells and re.fullmatch(r"AC-\d+", cells[0]):
                task_match = re.search(r"\bT\d+\b", cells[1]) if len(cells) > 1 else None
                rows.append({"acceptance_criterion": cells[0], "task": task_match.group() if task_match else "", "verification": cells[2] if len(cells) > 2 else "", "line": number})
        elif in_traceability and not line.startswith("|"):
            in_traceability = False
    targets = {}
    for task, body in task_bodies.items():
        targets[task] = []
        for number, line in body:
            match = re.search(r"대상 AC:\s*(.*)", line)
            if match:
                targets[task].extend(re.findall(r"AC-\d+", match.group(1)))
            for span in re.findall(r"``(.*?)``|`([^`]*)`", line):
                for command in re.findall(r"\bCMD-\d+\b", "".join(span)):
                    document["references"].setdefault(command, []).append(number)
    document["plan_rows"] = rows
    document["task_bodies"] = task_bodies
    document["task_targets"] = targets
    return document


def cell(kind, key, ok, detail="", line=None):
    return {"kind": kind, "key": key, "status": "ok" if ok else "empty", "detail": detail, "line": line}


def spec_cells(document):
    requirements = document["requirements"]
    criteria = document["acceptance_criteria"]
    if not requirements or not criteria:
        return [cell("문법 미충족", "spec", False, "요구사항 또는 AC 정의가 없습니다")]
    cells = []
    rows_by_requirement = {}
    rows_by_criterion = {}
    for row in document["trace_rows"]:
        rows_by_requirement.setdefault(row["requirement"], []).append(row)
        for ac in row["acceptance_criteria"]:
            rows_by_criterion.setdefault(ac, []).append(row)
    for requirement, definitions in requirements.items():
        rows = rows_by_requirement.get(requirement, [])
        cells.append(cell("R→추적행", requirement, bool(rows), "추적표 행 없음", definitions[0]["line"]))
        defined = [ac for row in rows for ac in row["acceptance_criteria"] if ac in criteria]
        cells.append(cell("R→AC", requirement, bool(defined), "정의된 AC 없음", definitions[0]["line"]))
        for row in rows:
            invalid = [ac for ac in row["acceptance_criteria"] if ac not in criteria]
            cells.append(cell("추적행 AC 존재", requirement, not invalid, ", ".join(invalid), row["line"]))
    for row in document["trace_rows"]:
        cells.append(cell("추적행→R", row["requirement"], row["requirement"] in requirements, "정의 없는 요구사항", row["line"]))
    cells.append(cell("R 수=추적 행 수", "spec", len(requirements) == len(document["trace_rows"]), f"{len(requirements)} / {len(document['trace_rows'])}"))
    for ac, definitions in criteria.items():
        cells.append(cell("AC→R", ac, ac in rows_by_criterion, "추적표 행 없음", definitions[0]["line"]))
        means = judgement_means(definitions[0]["text"])
        cells.append(cell("AC→판정수단", ac, bool(means), "판정 수단 없음", definitions[0]["line"]))
        commands = [token for token in means if token.startswith("CMD-")]
        if commands:
            missing = [command for command in commands if command not in document["commands"]]
            cells.append(cell("AC→CMD 존재", ac, not missing, ", ".join(missing), definitions[0]["line"]))
    numbers = sorted(int(ac.split("-")[1]) for ac in criteria)
    cells.append(cell("AC 번호 연속", "spec", numbers == list(range(1, len(numbers) + 1)), "번호 공백"))
    for collection in (requirements, criteria):
        for identifier, definitions in collection.items():
            if len(definitions) > 1:
                cells.append(cell("중복 정의", identifier, False, f"{len(definitions)}회", definitions[0]["line"]))
    known = set(requirements) | set(criteria) | set(document["decisions"]) | set(document["commands"])
    for token, lines in document["references"].items():
        if token not in known and not token.startswith("T"):
            cells.append(cell("참조 무결성", token, False, f"{len(lines)}회", lines[0]))
    return cells


def plan_cells(plan, spec):
    if not plan["tasks"] or not plan["plan_rows"]:
        return [cell("문법 미충족", "plan", False, "태스크 또는 추적표 AC 행이 없습니다")]
    cells = []
    spec_acs = set(spec["acceptance_criteria"])
    rows_by_ac = {}
    for row in plan["plan_rows"]:
        rows_by_ac.setdefault(row["acceptance_criterion"], []).append(row)
    for ac in sorted(spec_acs):
        cells.append(cell("Spec AC→Plan 추적행", ac, ac in rows_by_ac, "Plan 추적표 행 없음"))
    for ac in sorted(rows_by_ac):
        rows = rows_by_ac[ac]
        cells.append(cell("Plan 추적행→Spec AC", ac, ac in spec_acs, "Spec AC 정의 없음", rows[0]["line"]))
        for row in rows:
            task = row["task"]
            valid_task = bool(re.fullmatch(r"T\d+", task))
            cells.append(cell("AC→태스크", ac, valid_task, "Task 셀이 비었거나 T ID가 아님", row["line"]))
            cells.append(cell("태스크 존재", task or ac, valid_task and task in plan["tasks"], "태스크 없음", row["line"]))
            targets = plan["task_targets"].get(task, [])
            cells.append(cell("추적행→태스크 대상 AC", ac, ac in targets, "대상 AC 목록 없음", row["line"]))
            means = token_list(row["verification"])
            missing_commands = [item for item in means if item.startswith("CMD-") and item not in plan["commands"]]
            if any(item.startswith("CMD-") for item in means):
                cells.append(cell("추적행 CMD 존재", ac, not missing_commands, ", ".join(missing_commands), row["line"]))
            if task in plan["task_bodies"]:
                ac_lines = [
                    line.replace("`", "")
                    for _, line in plan["task_bodies"][task]
                    if re.search(rf"\b{re.escape(ac)}\b", line.replace("`", ""))
                ]
                missing = [item for item in means if not any(item in line for line in ac_lines)]
                cells.append(cell("AC 등장 행에 판정수단 동반", ac, not missing, ", ".join(missing), row["line"]))
    for task in sorted(plan["task_targets"]):
        targets = plan["task_targets"][task]
        assigned = {row["acceptance_criterion"] for row in plan["plan_rows"] if row["task"] == task}
        for ac in targets:
            cells.append(cell("태스크 대상 AC→추적행", ac, ac in assigned, "다른 태스크에 배정됨", plan["tasks"][task][0]["line"]))
    known = set(plan["tasks"]) | set(plan["commands"]) | set(spec["requirements"]) | set(spec["acceptance_criteria"]) | set(spec["decisions"])
    for token, lines in plan["references"].items():
        if token not in known:
            cells.append(cell("참조 무결성", token, False, f"{len(lines)}회", lines[0]))
    return cells


def _rows_by_ac(document):
    rows = {}
    for row in document["trace_rows"]:
        for ac in row["acceptance_criteria"]:
            rows.setdefault(ac, []).append(row["requirement"])
    return rows


def _changed_lines(base_lines, current_lines):
    changed = set()
    removed = set()
    for tag, start, end, current_start, current_end in difflib.SequenceMatcher(
        None, base_lines, current_lines, autojunk=False
    ).get_opcodes():
        if tag in {"insert", "replace"}:
            changed.update(range(current_start + 1, current_end + 1))
        if tag in {"delete", "replace"}:
            removed.update(range(start + 1, end + 1))
    return changed, removed


def _requirement_for_line(document, line_number):
    for row in document["trace_rows"]:
        if row["line"] == line_number:
            return {row["requirement"]}
    for requirement, definitions in document["requirements"].items():
        if any(item["line"] == line_number for item in definitions):
            return {requirement}
    by_ac = _rows_by_ac(document)
    for ac, definitions in document["acceptance_criteria"].items():
        if any(item["line"] == line_number for item in definitions):
            return set(by_ac.get(ac, []))
    definitions = sorted(
        (item["line"], requirement)
        for requirement, entries in document["requirements"].items()
        for item in entries
    )
    preceding = [requirement for number, requirement in definitions if number <= line_number]
    return {preceding[-1]} if preceding else set()


def _task_for_line(plan, line_number):
    for task, entries in plan["task_bodies"].items():
        if any(number == line_number for number, _ in entries):
            return task
    for task, definitions in plan["tasks"].items():
        if any(item["line"] == line_number for item in definitions):
            return task
    return None


def _requirements_for_plan_line(plan, spec, line_number):
    by_ac = _rows_by_ac(spec)
    for row in plan["plan_rows"]:
        if row["line"] == line_number:
            return set(by_ac.get(row["acceptance_criterion"], []))
    task = _task_for_line(plan, line_number)
    if task:
        return {
            requirement
            for ac in plan["task_targets"].get(task, [])
            for requirement in by_ac.get(ac, [])
        }
    return set()


def touched_requirements(artifact, base, current, spec, base_spec=None):
    changed, _ = _changed_lines(base["lines"], current["lines"])
    touched = set()
    if artifact == "spec":
        for number in changed:
            touched.update(_requirement_for_line(current, number))
    else:
        for number in changed:
            touched.update(_requirements_for_plan_line(current, spec, number))
    removed_ids = []
    collections = ("requirements", "acceptance_criteria") if artifact == "spec" else ("tasks", "commands")
    for collection in collections:
        for identifier in base[collection]:
            if identifier not in current[collection]:
                removed_ids.append(identifier)
                if artifact == "spec":
                    for definition in base[collection][identifier]:
                        touched.update(_requirement_for_line(base, definition["line"]))
    return sorted(touched), sorted(removed_ids)


def ripple_rows(artifact, requirements, spec, plan=None):
    spec_by_ac = _rows_by_ac(spec)
    rows = []
    cells = []
    for requirement in requirements:
        acs = []
        for row in spec["trace_rows"]:
            if row["requirement"] == requirement:
                acs.extend(row["acceptance_criteria"])
        acs = list(dict.fromkeys(acs))
        commands = []
        for ac in acs:
            for definition in spec["acceptance_criteria"].get(ac, []):
                commands.extend(judgement_means(definition["text"]))
        plan_rows = tasks = None
        if plan is not None:
            plan_rows = []
            tasks = []
            for row in plan["plan_rows"]:
                if row["acceptance_criterion"] in acs:
                    plan_rows.append(row["line"])
                    if row["task"]:
                        tasks.append(row["task"])
                    commands.extend(token_list(row["verification"]))
            plan_rows = list(dict.fromkeys(plan_rows))
            tasks = list(dict.fromkeys(tasks))
        commands = list(dict.fromkeys(commands))
        row = {
            "requirement": requirement,
            "acceptance_criteria": acs,
            "plan_rows": plan_rows,
            "tasks": tasks,
            "commands": commands,
        }
        rows.append(row)
        invalid = not acs or not commands
        if plan is not None:
            invalid = invalid or not plan_rows or not tasks
        if invalid:
            cells.append(cell("파급표", requirement, False, "판정 대상이 비어 있습니다"))
    return rows, cells


NOTE_HEADER = "| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |"
CODE3_RULE = "`함께 바뀐 항목` 셋째 열에서 `ripple[].acceptance_criteria` 의 각 AC ID 가 단어 경계로 등장하고, 그 등장 중 하나 이상의 바로 뒤 괄호가 `일치`/`모순` 으로 시작하면 충족; 빠진 AC 는 `<R>/<AC>`, 토큰 없는 AC 는 `<R>/<AC>/판정` 을 missing_rows 에"


def note_result(path, round_number, ripple):
    result = {
        "required": round_number is not None and round_number >= 2,
        "path": str(path.resolve()) if path else None,
        "section_found": False,
        "missing_rows": [],
        "blank_cells": [],
    }
    if not result["required"]:
        return result
    if path is None or not path.is_file():
        return result
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return result
    heading = f"## 라운드 {round_number} 개정"
    try:
        start = lines.index(heading)
    except ValueError:
        return result
    section = []
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        section.append(line)
    if NOTE_HEADER not in section:
        result["missing_rows"] = [item["requirement"] for item in ripple]
        return result
    result["section_found"] = True
    header_index = section.index(NOTE_HEADER)
    table = {}
    blank_requirement_rows = []
    for line in section[header_index + 2:]:
        if not line.startswith("|"):
            break
        values = [value.strip() for value in line.strip().strip("|").split("|")]
        if len(values) == 5:
            table[values[0]] = values
            if not values[0] or values[0] in {"-", "—"}:
                blank_requirement_rows.append(values)
    labels = ("요구사항", "해소 finding", "함께 바뀐 항목", "상호작용 판정", "치환 근거")
    for item in ripple:
        values = table.get(item["requirement"])
        if values is None:
            if blank_requirement_rows:
                for label, value in zip(labels, blank_requirement_rows[0]):
                    if not value.strip() or value.strip() in {"-", "—"}:
                        result["blank_cells"].append(f"{item['requirement']}/{label}")
            result["missing_rows"].append(item["requirement"])
            continue
        for label, value in zip(labels, values):
            if not value.strip() or value.strip() in {"-", "—"}:
                result["blank_cells"].append(f"{item['requirement']}/{label}")
        for ac in item["acceptance_criteria"]:
            if not re.search(rf"\b{re.escape(ac)}\b", values[2]):
                result["missing_rows"].append(f"{item['requirement']}/{ac}")
            elif not re.search(
                rf"\b{re.escape(ac)}\b\s*\(\s*(?:일치|모순)", values[2]
            ):
                result["missing_rows"].append(f"{item['requirement']}/{ac}/판정")
    return result


def _load_path(value, label):
    path = Path(value).resolve()
    try:
        return path, path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"{label} 읽기 실패: {exc}") from exc


def render(payload):
    print("# 빈 칸")
    print("| 종류 | 키 | 상태 | 상세 | 행 |")
    for item in payload["cells"]:
        if item["status"] == "empty":
            print(f"| {item['kind']} | {item['key']} | empty | {item['detail']} | {item['line'] or ''} |")
    print("# 파급표")
    print("| 요구사항 | 판정 AC | Plan 추적행 | 태스크 | 판정 명령/테스트 |")
    for item in payload["ripple"]:
        values = [item["acceptance_criteria"], item["plan_rows"], item["tasks"], item["commands"]]
        values = [", ".join(map(str, value)) if value else "**빈 칸**" for value in values]
        print(f"| {item['requirement']} | {values[0]} | {values[1]} | {values[2]} | {values[3]} |")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", required=True, choices=("spec", "plan"))
    parser.add_argument("--current", required=True)
    parser.add_argument("--spec")
    parser.add_argument("--state")
    parser.add_argument("--base")
    parser.add_argument("--notes")
    parser.add_argument("--out")
    args = parser.parse_args(argv)
    try:
        if args.artifact == "plan" and not args.spec:
            raise ValueError("plan에는 --spec이 필요합니다")
        if args.state and args.base:
            raise ValueError("--state와 --base를 함께 쓸 수 없습니다")
        current_path, current_text = _load_path(args.current, "--current")
        spec_path = spec_text = None
        if args.spec:
            spec_path, spec_text = _load_path(args.spec, "--spec")
        base_path = None
        base_text = None
        round_number = None
        if args.base:
            base_path, base_text = _load_path(args.base, "--base")
        if args.notes:
            _load_path(args.notes, "--notes")
        if args.state:
            state_path, state_text = _load_path(args.state, "--state")
            try:
                state = json.loads(state_text)
                prior_round = state["rounds"][args.artifact]
            except (KeyError, TypeError, json.JSONDecodeError) as exc:
                raise ValueError(f"--state 파싱 실패: {exc}") from exc
            round_number = prior_round + 1
            if prior_round >= 1:
                base_path = state_path.parent / "snapshots" / f"{args.artifact}-r{prior_round}.md"
                base_path, base_text = _load_path(base_path, "스냅숏")
                reviews = state.get("reviews", {}).get(args.artifact)
                if not isinstance(reviews, list) or not reviews:
                    raise ValueError("스냅숏에 대응하는 리뷰가 없습니다")
                if digest(base_path) != reviews[-1].get("artifact_digest"):
                    raise ValueError("스냅숏 digest가 직전 리뷰와 다릅니다")
        document = parse_document(current_text) if args.artifact == "spec" else parse_plan(current_text)
        companion = parse_document(spec_text) if spec_text is not None else document
        cells = spec_cells(document) if args.artifact == "spec" else plan_cells(document, companion)
        base_document = None
        if base_text is not None:
            base_document = parse_document(base_text) if args.artifact == "spec" else parse_plan(base_text)
        touched = []
        removed = []
        ripple = []
        if base_document is not None:
            touched, removed = touched_requirements(
                args.artifact, base_document, document, companion
            )
            ripple, ripple_cells = ripple_rows(
                args.artifact,
                touched,
                companion,
                document if args.artifact == "plan" else None,
            )
            cells.extend(ripple_cells)
        notes_path = Path(args.notes).resolve() if args.notes else current_path.parent / f"{args.artifact}-revision-notes.md"
        notes = note_result(notes_path, round_number, ripple)
        empty_cells = sum(item["status"] == "empty" for item in cells)
        passed = (
            empty_cells == 0
            and not notes["missing_rows"]
            and not notes["blank_cells"]
            and (not notes["required"] or notes["section_found"])
        )
        payload = {
            "artifact": args.artifact, "round": round_number,
            "base_digest": digest(base_path) if base_path else None,
            "current_digest": digest(current_path),
            "spec_digest": digest(spec_path) if spec_path else None,
            "cells": cells, "empty_cells": empty_cells,
            "touched_requirements": touched, "removed_ids": removed, "ripple": ripple,
            "notes": notes,
            "passed": passed,
        }
        if args.out:
            Path(args.out).resolve().write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        render(payload)
        return 0 if payload["passed"] else 1
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
