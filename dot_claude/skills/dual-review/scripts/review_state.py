"""Deterministic, read-only boundaries for local independent dual review."""
import argparse
import hashlib
import json
import random
import re
import subprocess
import tempfile
from pathlib import Path

TERMINATION_REASONS = ("no_changes", "reviewer_failure", "single_reviewer", "abstraction_drift", "two_quiet_rounds", "requested_round_limit", "no_new_high", "round_cap")
CLAUDE_PRODUCERS = ("pr-review-toolkit:code-reviewer", "pr-test-analyzer", "comment-analyzer", "silent-failure-hunter", "type-design-analyzer")
MASKED_PRODUCERS = tuple(sorted({name for item in CLAUDE_PRODUCERS for name in (item, item.split(":", 1)[-1])}))
PUBLIC_FINDING_FIELDS = ("finding_id", "group", "severity", "title", "body", "file", "line_start", "line_end", "finding_confidence", "recommendation")


def parse_arguments(arguments, parent_base):
    result, index = {"base": parent_base, "rounds": 2}, 0
    while index < len(arguments):
        item = arguments[index]
        if item.startswith("--base="):
            result["base"] = item.split("=", 1)[1]
        elif item == "--base" and index + 1 < len(arguments):
            index += 1; result["base"] = arguments[index]
        elif item.startswith("--rounds="):
            result["rounds"] = int(item.split("=", 1)[1])
        elif item == "--rounds" and index + 1 < len(arguments):
            index += 1; result["rounds"] = int(arguments[index])
        else:
            raise ValueError("invalid dual-review arguments")
        index += 1
    if not result["base"] or result["rounds"] not in (1, 2):
        raise ValueError("base and rounds must be valid")
    return result


def make_run_id(base_sha, head_sha, execution_number):
    target = hashlib.sha256(f"{base_sha}\0{head_sha}".encode()).hexdigest()[:16]
    return f"{target}-{int(execution_number):06d}"


def build_round_zero_prompts(snapshot):
    target = "base=%s\nhead=%s\nfiles:\n%s\ndiff:\n%s" % (snapshot.get("base_sha", ""), snapshot.get("head_sha", ""), "\n".join(snapshot.get("files", [])), snapshot.get("diff", ""))
    return {
        "claude": "Independently review this target. Return labeled findings only: one finding per block, with Title: first, one bare Label: value per line, and Body: and Recommendation: last. Every block must label Title, Severity, Confidence, File, Line, Body, and Recommendation. Severity must be one of: "
                  + ", ".join(SEVERITY_BY_WORD) + ".\n" + target,
        "codex": "Independently review this target. Return one JSON object conforming exactly to the supplied reviewer schema.\n" + target,
    }


def build_codex_command(repository_root, schema_name="reviewer.schema.json", output_path=None):
    schema = Path(__file__).resolve().parents[1] / "schemas" / schema_name
    command = ["codex", "exec", "-C", str(Path(repository_root)), "--sandbox", "read-only", "--output-schema", str(schema), "--json"]
    if output_path is not None:
        command.extend(("--output-last-message", str(output_path)))
    return tuple(command)


def build_claude_command(producer=None, schema_name=None):
    # Every invocation is a new non-persistent process; no unsupported fresh flag is needed.
    command = ["claude", "-p", "--no-session-persistence", "--permission-mode", "plan", "--permission-prompts", "none", "--allowedTools", "Read,Glob,Grep"]
    if producer: command.extend(("--agent", producer))
    if schema_name:
        schema = (Path(__file__).resolve().parents[1] / "schemas" / schema_name).read_text(encoding="utf-8")
        command.extend(("--output-format", "json", "--json-schema", schema))
    return tuple(command)


def derive_finding_id(group_label, original_id, file, line_start, line_end, title, body):
    parts = []
    for value in (group_label, original_id, file, str(line_start), str(line_end), title, body):
        raw = str(value).encode("utf-8")
        parts.append(str(len(raw)).encode("ascii") + b":" + raw)
    return "fid_" + hashlib.sha256(b"\0".join(parts)).hexdigest()


def _markdown_records(markdown):
    records = []
    labels = r"(?:#{1,6}[ \t]+)?(?:\*\*)?(?P<label>title|severity|confidence|file|line|line_start|line_end|body|recommendation)(?:[ \t]*:\*\*|\*\*[ \t]*:|[ \t]*:)[ \t]*(?P<value>.*)$"
    matches = list(re.finditer(rf"(?im)^{labels}", markdown))
    titles = [match for match in matches if match.group("label").lower() == "title"]
    scalar_labels = {"severity", "confidence", "file", "line", "line_start", "line_end"}
    for index, title in enumerate(titles):
        block_end = titles[index + 1].start() if index + 1 < len(titles) else len(markdown)
        block = markdown[title.end():block_end]
        block_labels = list(re.finditer(rf"(?im)^{labels}", block))
        record = {"title": title.group("value").strip()}
        body = next((match for match in block_labels if match.group("label").lower() == "body"), None)
        recommendation = next((match for match in block_labels if match.group("label").lower() == "recommendation" and (body is None or match.start() > body.start())), None)
        metadata = [match for match in block_labels if match.group("label").lower() in scalar_labels and (body is None or match.start() < body.start())]
        body_end = recommendation.start() if recommendation else len(block)
        if body:
            late_metadata = [match for match in block_labels if body.end() <= match.start() < body_end and match.group("label").lower() in scalar_labels]
            late_start = next((match.start() for match in late_metadata if match.group("label").lower() == "severity"), None)
            if late_start is not None:
                metadata.extend(match for match in late_metadata if match.start() >= late_start)
                body_end = late_start
            record["body"] = block[body.start("value"):body_end].strip()
        for match in metadata:
            label = match.group("label").lower()
            record.setdefault(label, match.group("value").strip())
        if recommendation:
            record["recommendation"] = block[recommendation.start("value"):].strip()
        if "line" in record:
            record["line_start"] = record["line_end"] = record["line"]
        records.append(record)
    return records


# The one vocabulary: normalization admits exactly these words and the round-zero prompt
# advertises exactly these words, so a producer can never guess one that would be dropped.
SEVERITY_BY_WORD = {"critical": "critical", "important": "high", "high": "high", "medium": "medium", "low": "low", "minor": "low", "trivial": "low"}


def _severity(value):
    if value is None or not str(value).strip():
        return "medium"
    return SEVERITY_BY_WORD.get(str(value).strip().lower())


def _source_for(producer, source):
    return source or ("claude" if producer in CLAUDE_PRODUCERS else "codex" if producer == "codex" else producer)


def normalize_reviewer_findings(producer, raw_findings, group_label, source=None):
    """Reject only bad individual records, after consuming their stable ordinal."""
    records = _markdown_records(raw_findings) if isinstance(raw_findings, str) else list(raw_findings or [])
    findings, rejected = [], []
    for ordinal, raw in enumerate(records, 1):
        original_id = f"producer={producer};ordinal={ordinal}"
        if not isinstance(raw, dict):
            rejected.append({"original_id": original_id, "reason": "record is not an object", "raw": raw}); continue
        raw_confidence = raw.get("finding_confidence", raw.get("confidence"))
        raw_file, raw_start, raw_end = raw.get("file"), raw.get("line_start"), raw.get("line_end")
        numeric_confidence = isinstance(raw_confidence, (int, float)) and not isinstance(raw_confidence, bool)
        integer_lines = all(isinstance(value, int) and not isinstance(value, bool) for value in (raw_start, raw_end))
        strict_raw_types = producer.startswith("cross-critique:")
        if strict_raw_types and (not isinstance(raw_file, str) or not raw_file.strip() or not numeric_confidence or not integer_lines):
            rejected.append({"original_id": original_id, "reason": "invalid finding field types", "raw": raw}); continue
        try:
            confidence = float(raw_confidence)
            if confidence > 1: confidence /= 100
            start, end = (raw_start, raw_end) if strict_raw_types else (int(raw_start), int(raw_end))
        except (TypeError, ValueError):
            confidence, start, end = -1, 0, 0
        file = raw_file.strip() if strict_raw_types else str(raw_file or "")
        severity = _severity(raw.get("severity"))
        text_values = (raw.get("title"), raw.get("body"), raw.get("recommendation"))
        valid = severity in {"critical", "high", "medium", "low"} and 0 <= confidence <= 1 and file and not file.startswith("/") and ".." not in Path(file).parts and start >= 1 and start <= end and all(isinstance(item, str) and item.strip() for item in text_values)
        if not valid:
            rejected.append({"original_id": original_id, "reason": "invalid finding fields", "raw": raw}); continue
        body = "Finding body: " + " ".join(raw["body"].split())
        finding = {"source": _source_for(producer, source), "producer": producer, "original_id": original_id, "severity": severity, "title": raw["title"].strip(), "body": body, "file": file, "line_start": start, "line_end": end, "finding_confidence": confidence, "recommendation": raw["recommendation"].strip()}
        finding["finding_id"] = derive_finding_id(group_label, original_id, file, start, end, finding["title"], body)
        findings.append(finding)
    return findings, rejected


def _valid_location(item, changed_files, line_ranges):
    if not isinstance(item, dict): return False
    file, start, end = item.get("file"), item.get("line_start"), item.get("line_end")
    if not isinstance(file, str) or not file or file.startswith("/") or ".." in Path(file).parts or file not in changed_files: return False
    if not isinstance(start, int) or not isinstance(end, int) or start < 1 or end < start: return False
    ranges = (line_ranges or {}).get(file)
    return bool(ranges) and any(first <= start <= end <= last for first, last in ranges)


def validate_and_record_critique(payload, changed_files, round_number, reviewer, group_label, provenance, line_ranges=None):
    payload = payload if isinstance(payload, dict) else {}
    evidence = payload.get("evidence") if isinstance(payload.get("evidence"), list) else []
    valid_evidence = bool(evidence) and all(_valid_location(item, changed_files, line_ranges) for item in evidence)
    verdict = payload.get("verdict") if payload.get("verdict") in {"유지", "반증됨", "미검증"} else "미검증"
    if not valid_evidence: verdict = "미검증"
    record = {"finding_id": payload.get("finding_id", ""), "verdict": verdict, "evidence": evidence, "round": round_number, "reviewer": reviewer}
    new_findings, rejected = normalize_reviewer_findings("cross-critique:" + reviewer, payload.get("new_findings", []), group_label, reviewer)
    occurrences = provenance.setdefault("new_findings", {})
    for item in new_findings:
        occurrences.setdefault(item["finding_id"], []).append({"round": round_number, "reviewer": reviewer, "original_id": item["original_id"]})
    if rejected: provenance.setdefault("rejected_findings", []).extend(rejected)
    return record, new_findings


def advance_critique_rounds(claude_valid, codex_valid, requested_rounds, new_high_counts):
    if not claude_valid or not codex_valid: return []
    return [1, 2] if requested_rounds == 2 and new_high_counts and new_high_counts[0] > 0 else [1]


def select_termination_reason(candidates):
    for reason in TERMINATION_REASONS:
        if reason in candidates: return reason
    raise ValueError("at least one termination candidate is required")


def is_abstraction_drift(new_finding_files, changed_files):
    return bool(new_finding_files) and sum(item not in changed_files for item in new_finding_files) / len(new_finding_files) > .5


def assign_anonymous_groups(run_id, execution_number, sources):
    sources = set(sources)
    if not sources.issubset({"claude", "codex"}): raise ValueError("anonymous groups require reviewer sources")
    target = run_id.rsplit("-", 1)[0]
    labels = ("A", "B") if hashlib.sha256(target.encode("utf-8")).digest()[0] & 1 else ("B", "A")
    if not int(execution_number) % 2:
        labels = tuple(reversed(labels))
    return {source: labels[index] for index, source in enumerate(("claude", "codex")) if source in sources}


def sort_and_shuffle_findings(findings, seed):
    findings = sorted(findings, key=lambda item: item["finding_id"].encode("ascii"))
    random.Random(seed).shuffle(findings)
    return findings


def _redaction(token): return "<redacted:" + hashlib.sha256(token.encode()).hexdigest()[:12] + ">"


def _mask(value, forbidden, masks, path="$"):
    if isinstance(value, str):
        for token in sorted(set(forbidden), key=lambda token: (-len(token), token)):
            if token and token in value:
                replacement = _redaction(token); value = value.replace(token, replacement)
                masks.append({"path": path, "token": token, "replacement": replacement, "reason": "anonymous-view"})
        return value
    if isinstance(value, list): return [_mask(item, forbidden, masks, f"{path}[{index}]") for index, item in enumerate(value)]
    if isinstance(value, dict): return {key: _mask(item, forbidden, masks, f"{path}.{key}") for key, item in value.items()}
    return value


def _candidate_issues(findings):
    groups = []
    for finding in sorted(findings, key=lambda item: (item["file"], item["line_start"], item["line_end"], item["finding_id"])):
        for group in groups:
            if group["file"] == finding["file"] and finding["line_start"] <= group["line_end"] and finding["line_end"] >= group["line_start"]:
                group["finding_ids"].append(finding["finding_id"]); group["line_start"] = min(group["line_start"], finding["line_start"]); group["line_end"] = max(group["line_end"], finding["line_end"]); break
        else:
            groups.append({"file": finding["file"], "line_start": finding["line_start"], "line_end": finding["line_end"], "finding_ids": [finding["finding_id"]]})
    return groups


def build_anonymous_view(run_id, execution_number, findings, critiques, producer_names=(), source_groups=None):
    # source_groups carries every source that produced a valid review, including one that
    # produced zero findings. Deriving the map from the findings alone would drop that source
    # and leave the report with an unrestorable group label (Spec R7.2).
    groups = dict(source_groups) if source_groups else assign_anonymous_groups(run_id, execution_number, [item["source"] for item in findings])
    if not {item["source"] for item in findings}.issubset(groups): raise ValueError("finding source is absent from the anonymous group map")
    seed = hashlib.sha256(f"{run_id}\0{execution_number}".encode()).hexdigest()
    sidecar = {"seed": seed, "execution_number": execution_number, "source_groups": groups, "findings": {}, "masks": []}
    forbidden = list(MASKED_PRODUCERS) + list(producer_names) + [item["original_id"] for item in findings]
    public, public_id_by_original = [], {}
    for item in findings:
        group = groups[item["source"]]
        identifier = derive_finding_id(group, item["original_id"], item["file"], item["line_start"], item["line_end"], item["title"], item["body"])
        if item.get("finding_id"):
            public_id_by_original[item["finding_id"]] = identifier
        sidecar["findings"][identifier] = {"source": item["source"], "producer": item.get("producer", ""), "original_id": item["original_id"], "group": group}
        record = {key: item[key] for key in PUBLIC_FINDING_FIELDS if key in item and key not in {"finding_id", "group"}}
        record.update({"finding_id": identifier, "group": group}); public.append(_mask(record, forbidden, sidecar["masks"], "$.findings"))
    safe_critiques = []
    for item in critiques:
        record = {key: item[key] for key in ("finding_id", "verdict", "evidence") if key in item}
        record["finding_id"] = public_id_by_original.get(record.get("finding_id"), record.get("finding_id"))
        safe_critiques.append(record)
    view = {"findings": sort_and_shuffle_findings(public, seed), "critiques": _mask(safe_critiques, forbidden, sidecar["masks"], "$.critiques")}
    view["candidate_issues"] = _candidate_issues(view["findings"])
    return view, sidecar


def normalize_synthesis_decisions(decisions, manifest=None, *, refuted_ids=None):
    refuted = set(refuted_ids or ())
    normalized = []
    for decision in decisions:
        if not isinstance(decision, dict) or decision.get("classification") not in {"합의", "불일치", "단일 출처"}: raise ValueError("unknown synthesis classification")
        confidence = decision.get("decision_confidence")
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1: raise ValueError("decision confidence out of range")
        if not isinstance(decision.get("rationale"), str) or not decision["rationale"].strip(): raise ValueError("synthesis rationale is required")
        a, b = list(decision.get("group_a_finding_ids", [])), list(decision.get("group_b_finding_ids", []))
        if not all(isinstance(item, str) for item in a + b): raise ValueError("finding ids must be strings")
        if manifest and (not set(a).issubset(manifest.get("A", set())) or not set(b).issubset(manifest.get("B", set()))): raise ValueError("finding id is absent from anonymous group")
        if decision["classification"] == "합의" and (not a or not b): raise ValueError("two-source decision needs both groups")
        if decision["classification"] == "불일치":
            # R6.4 gives 불일치 two shapes: conflicting claims, which cite both groups, and a
            # valid refutation, which reaches the synthesizer as a critique verdict rather than
            # as a counterpart finding — so the refuting group has no finding_id to cite.
            if not a and not b: raise ValueError("two-source decision needs both groups")
            if (not a or not b) and not refuted.intersection(a + b): raise ValueError("one-sided disagreement needs a refuted finding")
        if decision["classification"] == "단일 출처" and bool(a) == bool(b): raise ValueError("single-source decision needs exactly one group")
        claims = decision.get("claims")
        if not isinstance(claims, dict) or set(claims) != {"A", "B"} or not all(isinstance(claims[group], str) for group in claims):
            raise ValueError("synthesis claims must contain A and B strings")
        result = dict(decision); result["group_a_finding_ids"], result["group_b_finding_ids"] = sorted(a), sorted(b); normalized.append(result)
    if manifest is not None:
        expected = set(manifest.get("A", set())) | set(manifest.get("B", set()))
        actual = [identifier for item in normalized for identifier in item["group_a_finding_ids"] + item["group_b_finding_ids"]]
        if set(actual) != expected or len(actual) != len(set(actual)):
            raise ValueError("synthesis decisions must cover every finding exactly once")
    return normalized


def assert_nonwriting_actions(actions):
    if {"external-write", "code-mutation"}.intersection(actions): raise ValueError("dual-review actions must remain local and read-only")


def scan_source_texts(root):
    """Read only textual source files; binary cache files never enter contracts."""
    allowed = {".md", ".py", ".json"}
    root = Path(root)
    return {str(path.relative_to(root)): path.read_text(encoding="utf-8") for path in sorted(root.rglob("*")) if path.is_file() and (path.suffix in allowed or path.name == ".gitkeep")}


def tree_fingerprint(repo_root):
    root = Path(repo_root)
    digest = hashlib.sha256()
    ignored = {".git", ".claude/dual-review-state", "__pycache__"}
    for path in sorted(root.rglob("*")):
        relative = str(path.relative_to(root))
        if not path.is_file() or any(relative == item or relative.startswith(item + "/") for item in ignored):
            continue
        encoded = relative.encode("utf-8")
        digest.update(str(len(encoded)).encode("ascii") + b":" + encoded + b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def _state_root(repo_root):
    root = Path(repo_root) / ".claude" / "dual-review-state"; root.mkdir(parents=True, exist_ok=True)
    (root / ".gitignore").write_text("*", encoding="utf-8"); return root


def _new_run(repo_root, snapshot, execution_number=None):
    root = _state_root(repo_root)
    if execution_number is not None:
        run_id = make_run_id(snapshot.get("base_sha", ""), snapshot.get("head_sha", ""), execution_number)
        run_dir = root / run_id
        run_dir.mkdir()
        return run_id, run_dir, execution_number
    else:
        target = make_run_id(snapshot.get("base_sha", ""), snapshot.get("head_sha", ""), 0).rsplit("-", 1)[0]
        existing = [int(path.name.rsplit("-", 1)[1]) for path in root.glob(target + "-*") if path.is_dir() and re.fullmatch(re.escape(target) + r"-\d{6}", path.name)]
        execution_number = max(existing, default=0) + 1
    while True:
        run_id = make_run_id(snapshot.get("base_sha", ""), snapshot.get("head_sha", ""), execution_number)
        run_dir = root / run_id
        try:
            run_dir.mkdir()
            return run_id, run_dir, execution_number
        except FileExistsError:
            execution_number += 1


def _envelope(payload):
    return isinstance(payload, dict) and isinstance(payload.get("verdict"), str) and isinstance(payload.get("summary"), str) and isinstance(payload.get("findings"), list) and isinstance(payload.get("next_steps"), list)


def _error(exc): return {"status": "error", "stderr": f"{type(exc).__name__}: {exc}", "exit_code": None, "payload": None, "raw": ""}


def _start(adapter, source, prompt):
    if adapter is None or not hasattr(adapter, "start") or not hasattr(adapter, "read"): raise TypeError("review adapter must provide start and read")
    return adapter.start(source, prompt)


def _read(adapter, handle):
    try: response = adapter.read(handle)
    except Exception as exc: return _error(exc)
    return response if isinstance(response, dict) else _error(TypeError("adapter response is not an object"))


def _call(adapter, source, prompt):
    try: handle = _start(adapter, source, prompt)
    except Exception as exc: return _error(exc)
    return _read(adapter, handle)


def _raw(response): return response.get("raw", json.dumps(response, sort_keys=True, ensure_ascii=False))


def _round_zero(run_dir, snapshot, reviewers):
    prompts, events, handles, responses = build_round_zero_prompts(snapshot), [], {}, {}
    for source in ("claude", "codex"): (run_dir / f"round0-{source}.prompt").write_text(prompts[source], encoding="utf-8")
    producer_mode = all(producer in reviewers for producer in CLAUDE_PRODUCERS)
    tasks = [(producer, "claude", prompts["claude"]) for producer in CLAUDE_PRODUCERS] + [("codex", "codex", prompts["codex"])] if producer_mode else [(source, source, prompts[source]) for source in ("claude", "codex")]
    assert_nonwriting_actions(("reviewer-call", "local-artifact"))
    # Start every adapter before a single response is read. This is the actual gate.
    for task, source, prompt in tasks:
        try: handles[task] = _start(reviewers.get(task), task, prompt); events.append(f"started:{task}")
        except Exception as exc: responses[task] = _error(exc); events.append(f"start-failed:{task}")
    for task, _, _ in tasks:
        if task in handles: events.append(f"read:{task}"); responses[task] = _read(reviewers[task], handles[task])
    statuses, payloads = {}, {}
    for source in ("claude", "codex"):
        source_tasks = [task for task, task_source, _ in tasks if task_source == source]
        records, valid_payloads = [], []
        for task in source_tasks:
            response = responses.get(task, _error(RuntimeError("reviewer did not start"))); raws, attempts = [_raw(response)], 0
            if response.get("status") == "timeout" or (response.get("status") == "ok" and not _envelope(response.get("payload"))):
                attempts = 1; response = _call(reviewers.get(task), task, prompts[source]); raws.append(_raw(response))
            valid = response.get("status") == "ok" and _envelope(response.get("payload"))
            records.append({"producer": task, "valid": valid, "reason": "" if valid else ("schema violation" if response.get("status") == "ok" else response.get("status", "error")), "attempts": attempts, "stderr": response.get("stderr", ""), "exit_code": response.get("exit_code"), "raw": raws, "payload": response.get("payload") if valid else None})
            if valid: valid_payloads.append((task, response["payload"]))
        valid = bool(valid_payloads)
        statuses[source] = {"status": "valid" if valid else "excluded", "reason": "" if valid else next((record["reason"] for record in records if record["reason"]), "all producers failed"), "attempts": sum(record["attempts"] for record in records), "stderr": "\n".join(record["stderr"] for record in records if record["stderr"]), "exit_code": next((record["exit_code"] for record in records if record["exit_code"] is not None), None), "raw": records}
        if valid: payloads[source] = valid_payloads
        (run_dir / f"raw-{source}.json").write_text(json.dumps(statuses[source], ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")
        if producer_mode and source == "claude":
            for record in records:
                name = record["producer"].replace(":", "-")
                (run_dir / f"raw-{name}.json").write_text(json.dumps(record, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")
    (run_dir / "events.json").write_text(json.dumps(events, ensure_ascii=False, indent=2), encoding="utf-8")
    return events, statuses, payloads


def _canonical(value):
    if isinstance(value, dict): return tuple((key, _canonical(item)) for key, item in sorted(value.items()))
    if isinstance(value, list): return tuple(sorted((_canonical(item) for item in value), key=repr))
    return value


def render_report(state, provenance_path=None):
    provenance = json.loads(Path(provenance_path).read_text(encoding="utf-8")) if provenance_path else state.get("provenance", {})
    def restore(value):
        if isinstance(value, str):
            for mask in provenance.get("masks", []):
                value = value.replace(mask["replacement"], mask["token"])
        elif isinstance(value, list):
            return [restore(item) for item in value]
        elif isinstance(value, dict):
            return {key: restore(item) for key, item in value.items()}
        return value
    if state["termination_reason"] not in TERMINATION_REASONS: raise ValueError("unknown termination reason")
    template = (Path(__file__).resolve().parents[1] / "templates" / "report.md").read_text(encoding="utf-8")
    headings = re.findall(r"^## (.+)$", template, re.MULTILINE)
    target = state.get("target", {}); source_map = provenance.get("findings", {})
    source_by_group = {group: source for source, group in provenance.get("source_groups", {}).items()}
    def source_of(group):
        # Fail closed: a bare group label in the deliverable is an anonymization leak, not a
        # cosmetic gap, so an unrestorable label stops the render instead of printing "A".
        if group not in source_by_group: raise ValueError("anonymous group has no restored source")
        return source_by_group[group]
    def relabel(value):
        # The synthesizer only ever saw A/B, so it may quote those labels back inside free text.
        if isinstance(value, str):
            return re.sub(r"(?<![0-9A-Za-z_])([AB])=", lambda m: source_of(m.group(1)) + "=", value)
        if isinstance(value, list): return [relabel(item) for item in value]
        if isinstance(value, dict): return {key: relabel(item) for key, item in value.items()}
        return value
    def source_ids(item, group):
        return f"{source_of(group)}={','.join(sorted(item.get(f'group_{group.lower()}_finding_ids', [])))}"
    def restored_claims(item):
        return {source_of(group): relabel(claim) for group, claim in item.get("claims", {}).items()}
    data = {
        "Target": [f"- base: {target.get('base_sha', '')}", f"- head: {target.get('head_sha', '')}"] + [f"- file: {item}" for item in sorted(target.get("files", []))],
        "Termination reason": [state["termination_reason"]],
        "Reviewer status": [f"- {source}: {item.get('status', 'unknown')}; reason={item.get('reason', '')}; attempts={item.get('attempts', 0)}; stderr={item.get('stderr', '')}; exit={item.get('exit_code', '')}" for source, item in sorted(state.get("reviewers", {}).items())],
        "Findings": [f"- {item.get('finding_id', '')} ({source_map.get(item.get('finding_id', ''), {}).get('source', 'unknown')}): {item.get('title', '')} — {item.get('body', '')}" for item in sorted(state.get("findings", []), key=lambda item: item.get("finding_id", ""))],
        "Critiques": [f"- {item.get('finding_id', '')}: {item.get('verdict', '')}; evidence=" + ", ".join(f"{e.get('file', '')}:{e.get('line_start', '')}-{e.get('line_end', '')}" for e in sorted(item.get("evidence", []), key=_canonical)) for item in sorted(state.get("critiques", []), key=_canonical)],
        "버려진 finding": [f"- {item.get('original_id', '')}: {item.get('reason', '')}" for item in sorted(provenance.get("rejected_findings", []), key=_canonical)],
        "Synthesis": [], "두 리뷰어가 갈린 지점": []}
    synthesis = sorted(restore(state.get("synthesis", [])), key=_canonical)
    data["Synthesis"] = [f"- {item.get('classification', '')}: confidence={item.get('decision_confidence', '')}; {source_ids(item, 'A')}; {source_ids(item, 'B')}; {relabel(item.get('rationale', ''))}" for item in synthesis]
    for item in synthesis:
        if item.get("classification") == "불일치":
            ids = set(item.get("group_a_finding_ids", []) + item.get("group_b_finding_ids", []))
            evidence = ", ".join(
                f"{critique.get('finding_id', '')}:{critique.get('verdict', '')}:" + ",".join(
                    f"{item.get('file', '')}:{item.get('line_start', '')}-{item.get('line_end', '')}"
                    for item in sorted(critique.get("evidence", []), key=_canonical)
                )
                for critique in sorted(state.get("critiques", []), key=_canonical) if critique.get("finding_id") in ids
            )
            data["두 리뷰어가 갈린 지점"].append(f"- {source_ids(item, 'A')}; {source_ids(item, 'B')}; claims={json.dumps(restored_claims(item), ensure_ascii=False, sort_keys=True)}; evidence={evidence}")
    output = ["# Dual review report", ""]
    for heading in headings: output.extend(("## " + heading, *data.get(heading, []), ""))
    return "\n".join(output)


def write_terminal_run_artifacts(run_dir, termination_reason, reviewer_statuses, details=None):
    if termination_reason not in TERMINATION_REASONS: raise ValueError("unknown termination reason")
    details = details or {}; run_dir = Path(run_dir); path = run_dir / "provenance.json"
    path.write_text(json.dumps({"reviewers": reviewer_statuses, "termination_reason": termination_reason, "details": details}, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")
    (run_dir / "report.md").write_text(render_report({"target": details.get("target", {}), "termination_reason": termination_reason, "reviewers": reviewer_statuses}, path), encoding="utf-8")


def _call_status(response, phase, source, attempts=0):
    return {
        "phase": phase, "source": source, "status": response.get("status", "error"),
        "reason": "" if response.get("status") == "ok" else response.get("status", "error"),
        "attempts": attempts, "stderr": response.get("stderr", ""), "exit_code": response.get("exit_code"),
    }


def _critique_payloads(response, expected_ids):
    payload = response.get("payload") if response.get("status") == "ok" else None
    items = payload.get("critiques") if isinstance(payload, dict) else None
    if not isinstance(items, list):
        raise ValueError("critique response must contain a critiques array")
    ids = [item.get("finding_id") for item in items if isinstance(item, dict)]
    if len(ids) != len(items) or set(ids) != set(expected_ids) or len(set(ids)) != len(ids):
        raise ValueError("critique response must map every requested finding exactly once")
    return items


def run_dual_review(repo_root, snapshot, reviewers, critique_adapter=None, synthesis_adapter=None, execution_number=None, requested_rounds=2):
    run_id, run_dir, allocated_execution_number = _new_run(repo_root, snapshot, execution_number)
    (run_dir / "snapshot.json").write_text(json.dumps(snapshot, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")
    if not snapshot.get("files"):
        write_terminal_run_artifacts(run_dir, "no_changes", {}, {"target": snapshot})
        return {"run_id": run_id, "run_dir": str(run_dir), "termination_reason": "no_changes", "events": [], "reviewers": {}, "cross_critique_calls": 0, "synthesis_calls": 0}
    events, statuses, payloads = _round_zero(run_dir, snapshot, reviewers)
    if len(payloads) != 2:
        reason = "reviewer_failure" if not payloads else "single_reviewer"; write_terminal_run_artifacts(run_dir, reason, statuses, {"target": snapshot, "events": events})
        return {"run_id": run_id, "run_dir": str(run_dir), "termination_reason": reason, "events": events, "reviewers": statuses, "cross_critique_calls": 0, "synthesis_calls": 0}
    groups = assign_anonymous_groups(run_id, allocated_execution_number, payloads)
    findings, rejected = [], []
    for source, produced_payloads in payloads.items():
        for producer, payload in produced_payloads:
            accepted, refused = normalize_reviewer_findings(producer, payload["findings"], groups[source], source); findings.extend(accepted); rejected.extend(refused)
    provenance = {"reviewers": statuses, "findings": {}, "rejected_findings": rejected, "critique_statuses": [], "synthesis_status": None}; critiques, all_findings, critique_calls = [], list(findings), 0
    completed_rounds, round_high_counts = [], []
    drift_detected = False
    pipeline_failed = False
    if critique_adapter:
        requested = advance_critique_rounds("claude" in payloads, "codex" in payloads, requested_rounds, round_high_counts)
        index = 0
        while index < len(requested):
            round_number = requested[index]; completed_rounds.append(round_number); before = len(all_findings); round_findings = list(all_findings)
            for reviewer, opposing_source in (("claude", "codex"), ("codex", "claude")):
                opposing = [item for item in round_findings if item["source"] == opposing_source]
                prompt = json.dumps({"contract": "Return one critiques array item for every requested finding_id, each with verdict, evidence, and new_findings.", "round": round_number, "opposing_findings": opposing, "diff": snapshot.get("diff", "")}, ensure_ascii=False)
                response = _call(critique_adapter, reviewer, prompt)
                status = _call_status(response, "critique", reviewer)
                try:
                    items = _critique_payloads(response, [item["finding_id"] for item in opposing])
                except ValueError as exc:
                    status.update({"status": "error", "reason": str(exc), "stderr": (status["stderr"] + "\n" + str(exc)).strip()})
                    pipeline_failed = True
                    items = []
                provenance["critique_statuses"].append(status)
                for payload in items:
                    critique, new_items = validate_and_record_critique(payload, set(snapshot["files"]), round_number, reviewer, groups[reviewer], provenance, snapshot.get("line_ranges"))
                    critiques.append(critique)
                    known_ids = {item["finding_id"] for item in all_findings}
                    for item in new_items:
                        if item["finding_id"] not in known_ids:
                            all_findings.append(item)
                            known_ids.add(item["finding_id"])
                critique_calls += 1
            if pipeline_failed: break
            new_high = sum(item["severity"] in {"high", "critical"} for item in all_findings[before:]); round_high_counts.append(new_high)
            if is_abstraction_drift([item["file"] for item in all_findings[before:]], set(snapshot["files"])):
                drift_detected = True
                break
            requested = advance_critique_rounds("claude" in payloads, "codex" in payloads, requested_rounds, round_high_counts)
            index += 1
    view, anonymous = build_anonymous_view(run_id, allocated_execution_number, all_findings, critiques, source_groups=groups); provenance.update(anonymous)
    manifest = {group: {key for key, item in anonymous["findings"].items() if item["group"] == group} for group in ("A", "B")}
    synthesis, synthesis_calls = [], 0
    if synthesis_adapter and not pipeline_failed:
        (run_dir / "synthesis-input.json").write_text(json.dumps(view, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")
        prompt = json.dumps({"contract": "Candidate issues are source-neutral assistance only: decide same-defect boundaries yourself and may merge or split them. Classification rules: same issue with both claims maintained or unverified is 합의; conflicting claims or valid refutation is 불일치; an issue from only one group is 단일 출처. Return decisions that cover every finding_id exactly once. Each decision must include classification, decision_confidence, rationale, group_a_finding_ids, group_b_finding_ids, and claims with A and B strings.", "anonymous_view": view}, ensure_ascii=False)
        response = _call(synthesis_adapter, "fresh-claude", prompt)
        status = _call_status(response, "synthesis", "fresh-claude")
        if response.get("status") == "ok" and isinstance(response.get("payload"), dict):
            try:
                synthesis = normalize_synthesis_decisions(response["payload"].get("decisions", []), manifest, refuted_ids={item.get("finding_id") for item in view.get("critiques", []) if item.get("verdict") == "반증됨"}); synthesis_calls = 1
            except (TypeError, ValueError) as exc:
                status.update({"status": "error", "reason": str(exc), "stderr": (status["stderr"] + "\n" + f"{type(exc).__name__}: {exc}").strip()})
                pipeline_failed = True
        else:
            pipeline_failed = True
        provenance["synthesis_status"] = status
    for name, value in (("normalized.json", all_findings), ("critiques.json", critiques), ("synthesis.json", synthesis)):
        (run_dir / name).write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")
    original_high = sum(item["severity"] in {"high", "critical"} for item in findings)
    candidates = set()
    if pipeline_failed: candidates.add("reviewer_failure")
    if completed_rounds and completed_rounds[-1] == 2: candidates.add("round_cap")
    elif critique_adapter is None or requested_rounds == 1: candidates.add("requested_round_limit")
    elif round_high_counts and round_high_counts[-1] == 0: candidates.add("no_new_high")
    else: candidates.add("requested_round_limit")
    if original_high == 0 and round_high_counts and round_high_counts[0] == 0: candidates.add("two_quiet_rounds")
    if drift_detected: candidates.add("abstraction_drift")
    reason = select_termination_reason(candidates); provenance_path = run_dir / "provenance.json"
    provenance_path.write_text(json.dumps(provenance, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")
    report_statuses = dict(statuses)
    report_statuses.update({f"critique:{item['source']}": item for item in provenance["critique_statuses"]})
    if provenance["synthesis_status"]: report_statuses["synthesis"] = provenance["synthesis_status"]
    state = {"target": snapshot, "termination_reason": reason, "reviewers": report_statuses, "findings": all_findings, "critiques": critiques, "synthesis": synthesis}
    (run_dir / "report.md").write_text(render_report(state, provenance_path), encoding="utf-8")
    return {"run_id": run_id, "run_dir": str(run_dir), "termination_reason": reason, "events": events, "reviewers": statuses, "cross_critique_calls": critique_calls, "synthesis_calls": synthesis_calls}


def execute_round_zero(repo_root, snapshot, reviewers):
    return run_dual_review(repo_root, snapshot, reviewers, requested_rounds=1)


def _last_jsonl_payload(stdout):
    """Recover the final structured message from a Codex JSONL event stream."""
    for line in reversed(stdout.splitlines()):
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if _envelope(item):
            return item
        for candidate in (item.get("payload") if isinstance(item, dict) else None, item.get("result") if isinstance(item, dict) else None):
            if isinstance(candidate, dict) and _envelope(candidate):
                return candidate
        if isinstance(item, dict) and isinstance(item.get("item"), dict):
            for content in item["item"].get("content", []):
                text = content.get("text") if isinstance(content, dict) else None
                if isinstance(text, str):
                    try:
                        candidate = json.loads(text)
                    except json.JSONDecodeError:
                        continue
                    if _envelope(candidate):
                        return candidate
    return None


def _claude_payload(stdout):
    try:
        item = json.loads(stdout)
    except json.JSONDecodeError:
        return None
    if not isinstance(item, dict) or item.get("subtype") == "error" or item.get("is_error") is True:
        return None
    if "structured_output" in item:
        return item["structured_output"] if isinstance(item["structured_output"], dict) else None
    if isinstance(item.get("result"), str):
        try:
            payload = json.loads(item["result"])
        except json.JSONDecodeError:
            return None
        return payload if isinstance(payload, dict) else None
    return item


class SubprocessAdapter:
    """A process adapter that physically separates process start from result read."""
    def __init__(self, command_builder, repository_root=None, timeout_seconds=300):
        self.command_builder = command_builder
        self.repository_root = Path(repository_root) if repository_root else None
        self.timeout_seconds = timeout_seconds
    def start(self, source, prompt):
        assert_nonwriting_actions(("reviewer-call", "local-artifact"))
        output_path = None
        try:
            try:
                with tempfile.NamedTemporaryFile(prefix="dual-review-", suffix=".json", delete=False) as output:
                    output_path = Path(output.name)
                command = self.command_builder(source, output_path)
            except TypeError:
                if output_path:
                    output_path.unlink(missing_ok=True)
                output_path = None
                command = self.command_builder(source)
            before = tree_fingerprint(self.repository_root) if self.repository_root else None
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return process, prompt, source, output_path, before
        except Exception:
            if output_path:
                output_path.unlink(missing_ok=True)
            raise
    def read(self, handle):
        process, prompt, source, output_path, before = handle
        stdout, stderr, timed_out = "", "", False
        try:
            try:
                stdout, stderr = process.communicate(prompt, timeout=self.timeout_seconds)
            except subprocess.TimeoutExpired:
                timed_out = True
                process.kill()
                stdout, stderr = process.communicate()
            if before is not None and tree_fingerprint(self.repository_root) != before:
                return {"status": "error", "stderr": "target tree changed during read-only review", "exit_code": process.returncode, "payload": None, "raw": stdout}
            if timed_out:
                return {"status": "timeout", "stderr": stderr, "exit_code": 124, "payload": None, "raw": stdout}
            payload = None
            if output_path and output_path.exists():
                try: payload = json.loads(output_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError: payload = None
            if payload is None and source == "codex":
                payload = _last_jsonl_payload(stdout)
            if payload is None and source not in CLAUDE_PRODUCERS:
                payload = _claude_payload(stdout)
            if payload is None and source in CLAUDE_PRODUCERS:
                # A producer whose output parses to zero blocks is an ingestion failure, not an
                # empty review: leaving payload None makes the envelope check exclude the source
                # instead of reporting a successful review with no findings (Spec R8.1).
                records = _markdown_records(stdout)
                payload = {"verdict": "ok", "summary": "", "findings": records, "next_steps": []} if records else None
            return {"status": "ok" if process.returncode == 0 and payload is not None else "error", "stderr": stderr, "exit_code": process.returncode, "payload": payload, "raw": stdout}
        finally:
            if output_path:
                output_path.unlink(missing_ok=True)


def snapshot_from_repository(repo_root, arguments):
    has_explicit_base = any(item == "--base" or item.startswith("--base=") for item in arguments)
    parent = None if has_explicit_base else subprocess.check_output(["git", "rev-parse", "HEAD^"], cwd=repo_root, text=True).strip()
    parsed = parse_arguments(arguments, parent)
    base = subprocess.check_output(["git", "rev-parse", parsed["base"]], cwd=repo_root, text=True).strip(); head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_root, text=True).strip()
    files = subprocess.check_output(["git", "diff", "--name-only", base, head], cwd=repo_root, text=True).splitlines(); diff = subprocess.check_output(["git", "diff", "--unified=0", base, head], cwd=repo_root, text=True)
    ranges, current = {}, None
    for line in diff.splitlines():
        if line.startswith("+++ b/"): current = line[6:]; ranges.setdefault(current, [])
        match = re.match(r"^@@ -[^ ]+ \+(\d+)(?:,(\d+))? @@", line)
        if current and match and int(match.group(2) or "1") > 0:
            start, count = int(match.group(1)), int(match.group(2) or "1"); ranges[current].append([start, start + count - 1])
    return {"base_sha": base, "head_sha": head, "files": files, "diff": diff, "line_ranges": ranges}, parsed


def live_adapters(repository_root):
    process = SubprocessAdapter(lambda source, output: build_codex_command(repository_root, "reviewer.schema.json", output) if source == "codex" else build_claude_command(source), repository_root)
    reviewers = {producer: process for producer in CLAUDE_PRODUCERS}; reviewers["codex"] = process
    critique = SubprocessAdapter(lambda source, output: build_codex_command(repository_root, "critique.schema.json", output) if source == "codex" else build_claude_command(schema_name="critique.schema.json"), repository_root)
    synthesis = SubprocessAdapter(lambda source, output: build_claude_command(schema_name="synthesis.schema.json"), repository_root)
    return reviewers, critique, synthesis


def main(argv=None):
    parser = argparse.ArgumentParser(); parser.add_argument("--execution-number", type=int); options, arguments = parser.parse_known_args(argv)
    snapshot, parsed = snapshot_from_repository(Path.cwd(), arguments); reviewers, critique, synthesis = live_adapters(Path.cwd())
    print(json.dumps(run_dual_review(Path.cwd(), snapshot, reviewers, critique, synthesis, options.execution_number, parsed["rounds"]), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__": main()
