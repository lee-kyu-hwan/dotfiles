import pathlib
import json
import sys
import tempfile
import unittest
from unittest import mock


SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import review_state


class ExecutionTests(unittest.TestCase):
    def test_round_zero_starts_every_adapter_before_any_result_is_read(self):
        """A read before every start is a real independence violation, not an event-label issue."""
        class BlockingAdapter:
            def __init__(self, source, started):
                self.source = source
                self.started = started
                self.reads = []

            def start(self, source, prompt):
                self.assert_source(source)
                self.started.add(source)
                return prompt

            def read(self, handle):
                if self.started != {"claude", "codex"}:
                    raise AssertionError("a result was read before both reviewers started")
                self.reads.append(handle)
                return {"status": "ok", "payload": {"verdict": "ok", "summary": "", "findings": [], "next_steps": []}}

            def assert_source(self, source):
                if source != self.source:
                    raise AssertionError("wrong adapter source")

        started = set()
        adapters = {source: BlockingAdapter(source, started) for source in ("claude", "codex")}
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = review_state.execute_round_zero(
                pathlib.Path(temporary_directory),
                {"base_sha": "a", "head_sha": "b", "files": ["x.py"]}, adapters,
            )
        self.assertEqual(result["termination_reason"], "requested_round_limit")
        self.assertTrue(all(adapter.reads for adapter in adapters.values()))

    def test_successful_workflow_runs_critiques_synthesis_and_separate_artifacts(self):
        class Adapter:
            def __init__(self, payload):
                self.payload = payload
                self.started = []
                self.read_count = 0

            def start(self, source, prompt):
                self.started.append((source, prompt))
                return source

            def read(self, handle):
                self.read_count += 1
                return {"status": "ok", "payload": self.payload}

        finding = {"severity": "high", "finding_confidence": 0.8, "file": "x.py", "line_start": 1, "line_end": 2, "title": "bug", "body": "detail", "recommendation": "fix"}
        reviewer_payload = {"verdict": "ok", "summary": "", "findings": [finding], "next_steps": []}
        class CritiqueAdapter(Adapter):
            def start(self, source, prompt):
                self.started.append((source, prompt)); return prompt
            def read(self, handle):
                self.read_count += 1
                return {"status": "ok", "payload": {"critiques": [
                    {"finding_id": item["finding_id"], "verdict": "유지", "evidence": [{"file": "x.py", "line_start": 1, "line_end": 2}], "new_findings": []}
                    for item in json.loads(handle)["opposing_findings"]
                ]}}
        class SynthesisAdapter(Adapter):
            def start(self, source, prompt):
                self.started.append((source, prompt))
                return prompt
            def read(self, handle):
                self.read_count += 1
                view = __import__("json").loads(handle)["anonymous_view"]
                groups = {item["group"]: item["finding_id"] for item in view["findings"]}
                return {"status": "ok", "payload": {"decisions": [{"classification": "합의", "decision_confidence": 0.9, "rationale": "same", "group_a_finding_ids": [groups["A"]], "group_b_finding_ids": [groups["B"]], "claims": {"A": "same", "B": "same"}}]}}
        adapters = {source: Adapter(reviewer_payload) for source in ("claude", "codex")}
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            result = review_state.run_dual_review(
                root, {"base_sha": "base", "head_sha": "head", "files": ["x.py"], "line_ranges": {"x.py": [[1, 2]]}},
                adapters, critique_adapter=CritiqueAdapter({}), synthesis_adapter=SynthesisAdapter({}), execution_number=7,
            )
            run_dir = root / ".claude" / "dual-review-state" / result["run_id"]
            for name in ("snapshot.json", "round0-claude.prompt", "round0-codex.prompt", "events.json", "raw-claude.json", "raw-codex.json", "normalized.json", "critiques.json", "synthesis.json", "provenance.json", "report.md"):
                self.assertTrue((run_dir / name).is_file(), name)
        self.assertEqual(result["cross_critique_calls"], 2)
        self.assertEqual(result["synthesis_calls"], 1)

    def test_live_shape_starts_five_claude_producers_and_codex_before_reads(self):
        events = []
        class Adapter:
            def start(self, source, prompt):
                events.append(("start", source)); return source
            def read(self, source):
                if len([event for event in events if event[0] == "start"]) != 6:
                    raise AssertionError("read happened before every production process started")
                events.append(("read", source))
                return {"status": "ok", "payload": {"verdict": "ok", "summary": "", "findings": [], "next_steps": []}}
        with tempfile.TemporaryDirectory() as temporary_directory:
            adapters = {name: Adapter() for name in review_state.CLAUDE_PRODUCERS}
            adapters["codex"] = Adapter()
            result = review_state.run_dual_review(pathlib.Path(temporary_directory), {"base_sha": "a", "head_sha": "b", "files": ["x.py"]}, adapters)
        self.assertEqual(result["termination_reason"], "requested_round_limit")
        self.assertEqual([source for kind, source in events if kind == "start"], list(review_state.CLAUDE_PRODUCERS) + ["codex"])

    def test_invalid_finding_is_rejected_without_retrying_its_valid_source(self):
        calls = []
        class Adapter:
            def start(self, source, prompt): calls.append(source); return source
            def read(self, source):
                return {"status": "ok", "payload": {"verdict": "ok", "summary": "", "next_steps": [], "findings": [
                    {"severity": "unexpected", "finding_confidence": .8, "file": "x.py", "line_start": 1, "line_end": 1, "title": "bad", "body": "bad", "recommendation": "fix"},
                    {"severity": "high", "finding_confidence": .8, "file": "x.py", "line_start": 2, "line_end": 2, "title": "good", "body": "good", "recommendation": "fix"},
                ]}}
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = review_state.run_dual_review(pathlib.Path(temporary_directory), {"base_sha": "a", "head_sha": "b", "files": ["x.py"]}, {"claude": Adapter(), "codex": Adapter()})
            rejected = __import__("json").loads((pathlib.Path(result["run_dir"]) / "normalized.json").read_text())
        self.assertEqual(calls, ["claude", "codex"])
        self.assertEqual([item["title"] for item in rejected], ["good", "good"])

    def test_exception_timeout_and_schema_failure_remain_in_terminal_report(self):
        class Exploding:
            def start(self, source, prompt): raise RuntimeError("adapter exploded")
            def read(self, handle): raise AssertionError("unreachable")
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = review_state.run_dual_review(pathlib.Path(temporary_directory), {"base_sha": "a", "head_sha": "b", "files": ["x.py"]}, {"claude": Exploding(), "codex": Exploding()})
            report = (pathlib.Path(result["run_dir"]) / "report.md").read_text()
            sidecar = (pathlib.Path(result["run_dir"]) / "provenance.json").read_text()
        self.assertEqual(result["termination_reason"], "reviewer_failure")
        self.assertIn("adapter exploded", report)
        self.assertIn("attempts=0", report)
        self.assertIn("RuntimeError", sidecar)
    def test_no_changes_writes_report_without_reviewer_calls(self):
        class NeverCalled:
            def start(self, source, prompt):
                raise AssertionError("no-change path must not start a reviewer")
            def read(self, handle):
                raise AssertionError("unreachable")
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            reviewer = NeverCalled()
            result = review_state.execute_round_zero(root, {"files": []}, {"claude": reviewer, "codex": reviewer})
            self.assertEqual(result["termination_reason"], "no_changes")
            run_dir = root / ".claude" / "dual-review-state" / result["run_id"]
            self.assertTrue((run_dir / "report.md").is_file())
            self.assertEqual((root / ".claude" / "dual-review-state" / ".gitignore").read_text(), "*")

    def test_default_run_reservation_allocates_distinct_directories(self):
        class Adapter:
            def start(self, source, prompt): return source
            def read(self, handle): return {"status": "ok", "payload": {"verdict": "ok", "summary": "", "findings": [], "next_steps": []}}
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            first = review_state.run_dual_review(root, {"base_sha": "a", "head_sha": "b", "files": ["x.py"]}, {"claude": Adapter(), "codex": Adapter()})
            second = review_state.run_dual_review(root, {"base_sha": "a", "head_sha": "b", "files": ["x.py"]}, {"claude": Adapter(), "codex": Adapter()})
        self.assertNotEqual(first["run_id"], second["run_id"])

    def test_default_allocations_record_their_actual_execution_number_and_alternate_groups(self):
        finding = {"severity": "low", "finding_confidence": .8, "file": "x.py", "line_start": 1, "line_end": 1, "title": "finding", "body": "detail", "recommendation": "fix"}
        class Adapter:
            def start(self, source, prompt): return source
            def read(self, handle): return {"status": "ok", "payload": {"verdict": "ok", "summary": "", "findings": [finding], "next_steps": []}}
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            snapshot = {"base_sha": "a", "head_sha": "b", "files": ["x.py"]}
            first = review_state.run_dual_review(root, snapshot, {"claude": Adapter(), "codex": Adapter()})
            second = review_state.run_dual_review(root, snapshot, {"claude": Adapter(), "codex": Adapter()})
            first_sidecar = json.loads((pathlib.Path(first["run_dir"]) / "provenance.json").read_text())
            second_sidecar = json.loads((pathlib.Path(second["run_dir"]) / "provenance.json").read_text())
        self.assertEqual(first_sidecar["execution_number"], 1)
        self.assertEqual(second_sidecar["execution_number"], 2)
        self.assertNotEqual(first_sidecar["source_groups"], second_sidecar["source_groups"])

    def test_default_allocation_scopes_execution_numbers_to_the_target(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            _, _, first_number = review_state._new_run(root, {"base_sha": "a", "head_sha": "b"})
            _, _, second_number = review_state._new_run(root, {"base_sha": "c", "head_sha": "d"})
        self.assertEqual((first_number, second_number), (1, 1))

    def test_explicit_execution_number_collision_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            snapshot = {"base_sha": "a", "head_sha": "b"}
            review_state._new_run(root, snapshot, 3)
            with self.assertRaises(FileExistsError):
                review_state._new_run(root, snapshot, 3)

    def test_subprocess_adapter_extracts_codex_jsonl_final_structured_item(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            script = pathlib.Path(temporary_directory) / "fake.py"
            script.write_text("import json\nprint(json.dumps({'type':'thread.started'}))\nprint(json.dumps({'type':'item.completed','item':{'type':'message','content':[{'type':'output_text','text':json.dumps({'verdict':'ok','summary':'done','findings':[],'next_steps':[]})}]}}))\n")
            adapter = review_state.SubprocessAdapter(lambda source: (sys.executable, str(script), source))
            response = adapter.read(adapter.start("codex", "prompt"))
        self.assertEqual(response["status"], "ok")
        self.assertEqual(response["payload"]["summary"], "done")

    def test_subprocess_adapter_uses_codex_last_message_file_not_event_stream(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            script = pathlib.Path(temporary_directory) / "fake.py"
            script.write_text("import json, pathlib, sys\np=sys.argv[sys.argv.index('--output-last-message') + 1]\npathlib.Path(p).write_text(json.dumps({'verdict':'ok','summary':'file','findings':[],'next_steps':[]}))\nprint(json.dumps({'type':'event','result':'not a review'}))\n")
            adapter = review_state.SubprocessAdapter(lambda source, output: (sys.executable, str(script), "--output-last-message", str(output)))
            response = adapter.read(adapter.start("codex", "prompt"))
        self.assertEqual(response["payload"]["summary"], "file")

    def test_subprocess_adapter_preserves_legacy_claude_result_and_producer_markdown(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            script = root / "legacy.py"
            script.write_text("""import json, sys
if sys.argv[1] == 'legacy':
    print(json.dumps({'result': json.dumps({'verdict': 'ok', 'summary': 'legacy result', 'findings': [], 'next_steps': []})}))
else:
    print('Title: Producer markdown\\nSeverity: High\\nConfidence: 90\\nFile: x.py\\nLine: 1\\nBody: detail\\nRecommendation: fix')
""")
            legacy = review_state.SubprocessAdapter(lambda source: (sys.executable, str(script), "legacy"), root)
            producer = review_state.SubprocessAdapter(lambda source: (sys.executable, str(script), "producer"), root)
            legacy_response = legacy.read(legacy.start("claude", "prompt"))
            producer_response = producer.read(producer.start("pr-test-analyzer", "prompt"))
        for response in (legacy_response, producer_response):
            self.assertEqual(response["status"], "ok")
            self.assertEqual(set(response["payload"]), {"verdict", "summary", "findings", "next_steps"})
            self.assertTrue(review_state._envelope(response["payload"]))
        self.assertEqual(legacy_response["payload"], {"verdict": "ok", "summary": "legacy result", "findings": [], "next_steps": []})
        self.assertEqual(producer_response["payload"]["findings"][0]["title"], "Producer markdown")

    def test_producer_markdown_that_parses_to_zero_findings_is_not_a_valid_review(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            script = root / "unparseable.py"
            script.write_text("""import sys
print('I reviewed the diff and have no structured output to offer.')
""")
            adapter = review_state.SubprocessAdapter(lambda source: (sys.executable, str(script)), root)
            response = adapter.read(adapter.start("pr-test-analyzer", "prompt"))
        self.assertIsNone(response["payload"])
        self.assertFalse(review_state._envelope(response["payload"]))
        self.assertEqual(response["status"], "error")
        self.assertIn("no structured output", response["raw"])

    def test_zero_parse_producer_is_excluded_rather_than_reported_as_a_clean_review(self):
        prose = "The diff looks fine to me; nothing worth reporting."
        good = {"verdict": "ok", "summary": "s", "findings": [
            {"severity": "High", "confidence": 90, "file": "x.py", "line": 3,
             "title": "t", "body": "b", "recommendation": "r"}], "next_steps": []}
        class FixedAdapter:
            def __init__(self, response): self.response = response
            def start(self, source, prompt): return source
            def read(self, handle): return dict(self.response)

        reviewers = {producer: FixedAdapter({"status": "ok", "payload": None, "raw": prose,
                                             "stderr": "", "exit_code": 0})
                     for producer in review_state.CLAUDE_PRODUCERS}
        reviewers["codex"] = FixedAdapter({"status": "ok", "payload": good, "raw": "",
                                           "stderr": "", "exit_code": 0})
        with tempfile.TemporaryDirectory() as temporary_directory:
            run_dir = pathlib.Path(temporary_directory)
            _, statuses, payloads = review_state._round_zero(
                run_dir, {"base_sha": "b", "head_sha": "h", "files": ["x.py"], "diff": "",
                          "line_ranges": {"x.py": [(1, 9)]}}, reviewers)
        self.assertEqual(statuses["claude"]["status"], "excluded")
        self.assertNotIn("claude", payloads)
        self.assertIn("codex", payloads)

    def test_subprocess_adapter_success_cleans_temporary_output(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            script = root / "success.py"
            script.write_text("""import json, pathlib, sys
pathlib.Path(sys.argv[1]).write_text(json.dumps({'verdict': 'ok', 'summary': 'file', 'findings': [], 'next_steps': []}))
""")
            outputs = []
            class CapturingAdapter(review_state.SubprocessAdapter):
                def start(self, source, prompt):
                    handle = super().start(source, prompt)
                    outputs.append(handle[3])
                    return handle
            adapter = CapturingAdapter(lambda source, output: (sys.executable, str(script), str(output)), root)
            response = adapter.read(adapter.start("codex", "prompt"))
            self.assertEqual(response["status"], "ok")
            self.assertEqual(response["payload"]["summary"], "file")
            self.assertEqual(len(outputs), 1)
            self.assertIsNotNone(outputs[0])
            self.assertFalse(outputs[0].exists())

    def test_subprocess_adapter_detects_target_tree_mutation(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            target = root / "target.py"; target.write_text("before\n")
            script = root / "mutate.py"
            script.write_text("import json, pathlib, sys\npathlib.Path(sys.argv[1]).write_text('after\\n')\nprint(json.dumps({'verdict':'ok','summary':'bad','findings':[],'next_steps':[]}))\n")
            adapter = review_state.SubprocessAdapter(lambda source: (sys.executable, str(script), str(target)), root)
            response = adapter.read(adapter.start("codex", "prompt"))
        self.assertEqual(response["status"], "error")
        self.assertIn("target tree changed", response["stderr"])

    def test_structured_claude_output_round_trips_when_result_is_empty_or_explanatory(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            script = root / "structured.py"
            script.write_text("""import json, sys
prompt = json.loads(sys.stdin.read())
style, phase = sys.argv[1:]
if phase == 'critique':
    payload = {'critiques': [{'finding_id': item['finding_id'], 'verdict': '유지', 'evidence': [{'file': 'x.py', 'line_start': 1, 'line_end': 1}], 'new_findings': []} for item in prompt['opposing_findings']]}
else:
    groups = {item['group']: item['finding_id'] for item in prompt['anonymous_view']['findings']}
    payload = {'decisions': [{'classification': '합의', 'decision_confidence': .8, 'rationale': 'same', 'group_a_finding_ids': [groups['A']], 'group_b_finding_ids': [groups['B']], 'claims': {'A': 'same', 'B': 'same'}}]}
if style == 'null':
    wrapper = {'result': '', 'structured_output': None}
elif style == 'error':
    wrapper = {'subtype': 'error', 'result': 'request failed', 'structured_output': payload}
else:
    wrapper = {'result': '' if style == 'empty' else 'structured response completed', 'structured_output': payload}
print(json.dumps(wrapper))
""")
            finding = {"severity": "high", "finding_confidence": .8, "file": "x.py", "line_start": 1, "line_end": 1, "title": "bug", "body": "detail", "recommendation": "fix"}
            class Reviewer:
                def start(self, source, prompt): return source
                def read(self, handle): return {"status": "ok", "payload": {"verdict": "ok", "summary": "", "findings": [finding], "next_steps": []}}
            for style in ("empty", "explanatory"):
                with self.subTest(style=style):
                    critique = review_state.SubprocessAdapter(lambda source: (sys.executable, str(script), style, "critique"), root)
                    synthesis = review_state.SubprocessAdapter(lambda source: (sys.executable, str(script), style, "synthesis"), root)
                    result = review_state.run_dual_review(root, {"base_sha": style, "head_sha": "b", "files": ["x.py"], "line_ranges": {"x.py": [[1, 1]]}}, {"claude": Reviewer(), "codex": Reviewer()}, critique, synthesis, requested_rounds=1)
                    self.assertNotEqual(result["termination_reason"], "reviewer_failure")
                    self.assertEqual((result["cross_critique_calls"], result["synthesis_calls"]), (2, 1))
            for style in ("null", "error"):
                with self.subTest(style=style):
                    adapter = review_state.SubprocessAdapter(lambda source: (sys.executable, str(script), style, "critique"), root)
                    response = adapter.read(adapter.start("claude", json.dumps({"opposing_findings": []})))
                    self.assertEqual(response["status"], "error")
                    self.assertIsNone(response["payload"])

    def test_timeout_mutation_is_nonretryable_and_cleans_temporary_output(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            target = root / "target.py"; target.write_text("before\n")
            script = root / "mutate_then_hang.py"
            script.write_text("import pathlib, sys, time\npathlib.Path(sys.argv[1]).write_text('after\\n')\ntime.sleep(10)\n")
            launches, outputs = [], []
            class CapturingAdapter(review_state.SubprocessAdapter):
                def start(self, source, prompt):
                    handle = super().start(source, prompt)
                    outputs.append(handle[3])
                    return handle
            adapter = CapturingAdapter(lambda source, output: launches.append(source) or (sys.executable, str(script), str(target), "--output-last-message", str(output)), root, timeout_seconds=.2)
            class Healthy:
                def start(self, source, prompt): return source
                def read(self, handle): return {"status": "ok", "payload": {"verdict": "ok", "summary": "", "findings": [], "next_steps": []}}
            result = review_state.execute_round_zero(root, {"base_sha": "a", "head_sha": "b", "files": ["target.py"]}, {"claude": Healthy(), "codex": adapter})
        self.assertEqual(result["termination_reason"], "single_reviewer")
        self.assertEqual(launches, ["codex"])
        self.assertTrue(outputs)
        self.assertTrue(all(output is not None and not output.exists() for output in outputs))

    def test_subprocess_start_failure_cleans_its_temporary_output(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            outputs = []
            original = review_state.tempfile.NamedTemporaryFile
            def named_temporary_file(*args, **kwargs):
                output = original(*args, dir=root, **kwargs)
                outputs.append(pathlib.Path(output.name))
                return output
            adapter = review_state.SubprocessAdapter(lambda source, output: ("dual-review-command-does-not-exist", str(output)), root)
            with mock.patch.object(review_state.tempfile, "NamedTemporaryFile", side_effect=named_temporary_file):
                with self.assertRaises(FileNotFoundError):
                    adapter.start("codex", "prompt")
            self.assertEqual(len(outputs), 1)
            self.assertFalse(outputs[0].exists())

    def test_synthesis_transport_failure_after_successful_critiques_is_not_empty_success(self):
        finding = {"severity": "high", "finding_confidence": .8, "file": "x.py", "line_start": 1, "line_end": 1, "title": "bug", "body": "detail", "recommendation": "fix"}
        class Reviewer:
            def start(self, source, prompt): return source
            def read(self, handle): return {"status": "ok", "payload": {"verdict": "ok", "summary": "", "findings": [finding], "next_steps": []}}
        class Critique:
            def start(self, source, prompt): return prompt
            def read(self, prompt): return {"status": "ok", "payload": {"critiques": [{"finding_id": item["finding_id"], "verdict": "유지", "evidence": [{"file": "x.py", "line_start": 1, "line_end": 1}], "new_findings": []} for item in json.loads(prompt)["opposing_findings"]]}}
        class SynthesisFailure:
            def __init__(self): self.calls = 0
            def start(self, source, prompt): self.calls += 1; return prompt
            def read(self, handle): return {"status": "error", "stderr": "synthesis transport down", "exit_code": 9}
        failure = SynthesisFailure()
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = review_state.run_dual_review(pathlib.Path(temporary_directory), {"base_sha": "a", "head_sha": "b", "files": ["x.py"], "line_ranges": {"x.py": [[1, 1]]}}, {"claude": Reviewer(), "codex": Reviewer()}, Critique(), failure, requested_rounds=1)
            run_dir = pathlib.Path(result["run_dir"])
            provenance = json.loads((run_dir / "provenance.json").read_text())
            report = (run_dir / "report.md").read_text()
        self.assertEqual(failure.calls, 1)
        self.assertEqual(result["cross_critique_calls"], 2)
        # 라운드 0 는 성공했고 종합만 무너졌으므로 reviewer_failure 가 아니다.
        self.assertEqual(result["termination_reason"], "pipeline_failure")
        self.assertEqual(provenance["synthesis_status"]["status"], "error")
        self.assertIn("synthesis transport down", report)

    def test_cross_critique_receives_only_the_opposing_source_findings(self):
        class Reviewer:
            def start(self, source, prompt): return source
            def read(self, source):
                finding = {"severity": "low", "finding_confidence": .8, "file": "x.py", "line_start": 1, "line_end": 1, "title": f"{source} unique title", "body": f"{source} unique body", "recommendation": "fix"}
                return {"status": "ok", "payload": {"verdict": "ok", "summary": "", "findings": [finding], "next_steps": []}}
        class Critique:
            def __init__(self): self.prompts = {}
            def start(self, source, prompt): self.prompts[source] = prompt; return (source, prompt)
            def read(self, handle):
                return {"status": "ok", "payload": {"critiques": [{"finding_id": item["finding_id"], "verdict": "유지", "evidence": [{"file": "x.py", "line_start": 1, "line_end": 1}], "new_findings": []} for item in json.loads(handle[1])["opposing_findings"]]}}
        critique = Critique()
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = review_state.run_dual_review(pathlib.Path(temporary_directory), {"base_sha": "a", "head_sha": "b", "files": ["x.py"], "line_ranges": {"x.py": [[1, 1]]}}, {"claude": Reviewer(), "codex": Reviewer()}, critique_adapter=critique, requested_rounds=1)
        self.assertEqual(result["cross_critique_calls"], 2)
        claude_opposing = json.loads(critique.prompts["claude"])["opposing_findings"]
        codex_opposing = json.loads(critique.prompts["codex"])["opposing_findings"]
        self.assertEqual([item["title"] for item in claude_opposing], ["codex unique title"])
        self.assertEqual([item["title"] for item in codex_opposing], ["claude unique title"])
        self.assertNotEqual(claude_opposing[0]["finding_id"], codex_opposing[0]["finding_id"])

    def test_actual_two_quiet_rounds_adds_the_termination_candidate(self):
        finding = {"severity": "low", "finding_confidence": .8, "file": "x.py", "line_start": 1, "line_end": 1, "title": "quiet", "body": "detail", "recommendation": "fix"}
        class Reviewer:
            def start(self, source, prompt): return source
            def read(self, handle): return {"status": "ok", "payload": {"verdict": "ok", "summary": "", "findings": [finding], "next_steps": []}}
        class QuietCritique:
            def start(self, source, prompt): return prompt
            def read(self, prompt):
                return {"status": "ok", "payload": {"critiques": [{"finding_id": item["finding_id"], "verdict": "유지", "evidence": [{"file": "x.py", "line_start": 1, "line_end": 1}], "new_findings": []} for item in json.loads(prompt)["opposing_findings"]]}}
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = review_state.run_dual_review(pathlib.Path(temporary_directory), {"base_sha": "a", "head_sha": "b", "files": ["x.py"], "line_ranges": {"x.py": [[1, 1]]}}, {"claude": Reviewer(), "codex": Reviewer()}, critique_adapter=QuietCritique(), requested_rounds=2)
        self.assertEqual(result["cross_critique_calls"], 2)
        self.assertEqual(result["termination_reason"], "two_quiet_rounds")

    def test_repeated_critique_findings_keep_all_occurrences_but_reach_synthesis_once(self):
        original = {"severity": "low", "finding_confidence": .8, "file": "x.py", "line_start": 1, "line_end": 1, "title": "original", "body": "detail", "recommendation": "fix"}
        repeated = {"severity": "high", "confidence": .9, "file": "x.py", "line_start": 1, "line_end": 1, "title": "repeated", "body": "detail", "recommendation": "fix"}
        class Reviewer:
            def start(self, source, prompt): return source
            def read(self, handle): return {"status": "ok", "payload": {"verdict": "ok", "summary": "", "findings": [original], "next_steps": []}}
        class Critique:
            def start(self, source, prompt): return (source, prompt)
            def read(self, handle):
                return {"status": "ok", "payload": {"critiques": [{"finding_id": item["finding_id"], "verdict": "유지", "evidence": [{"file": "x.py", "line_start": 1, "line_end": 1}], "new_findings": [repeated]} for item in json.loads(handle[1])["opposing_findings"]]}}
        class Synthesizer:
            def __init__(self): self.input_view = None
            def start(self, source, prompt): self.input_view = json.loads(prompt)["anonymous_view"]; return prompt
            def read(self, prompt):
                groups = {group: [item["finding_id"] for item in self.input_view["findings"] if item["group"] == group] for group in ("A", "B")}
                return {"status": "ok", "payload": {"decisions": [{"classification": "합의", "decision_confidence": .7, "rationale": "one decision", "group_a_finding_ids": groups["A"], "group_b_finding_ids": groups["B"], "claims": {"A": "a", "B": "b"}}]}}
        synthesis = Synthesizer()
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = review_state.run_dual_review(pathlib.Path(temporary_directory), {"base_sha": "a", "head_sha": "b", "files": ["x.py"], "line_ranges": {"x.py": [[1, 1]]}}, {"claude": Reviewer(), "codex": Reviewer()}, Critique(), synthesis, requested_rounds=2)
            provenance = json.loads((pathlib.Path(result["run_dir"]) / "provenance.json").read_text())
        identifiers = [item["finding_id"] for item in synthesis.input_view["findings"]]
        self.assertEqual(result["cross_critique_calls"], 4)
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertTrue(all(len(occurrences) > 1 for occurrences in provenance["new_findings"].values()))
        self.assertTrue(all({item["round"] for item in occurrences} == {1, 2} for occurrences in provenance["new_findings"].values()))

    def test_critique_and_synthesis_failures_are_not_empty_success(self):
        class Reviewer:
            def start(self, source, prompt): return source
            def read(self, handle):
                return {"status": "ok", "payload": {"verdict": "ok", "summary": "", "findings": [{"severity": "high", "finding_confidence": .8, "file": "x.py", "line_start": 1, "line_end": 1, "title": handle, "body": "detail", "recommendation": "fix"}], "next_steps": []}}
        class Failure:
            def start(self, source, prompt): return source
            def read(self, handle): return {"status": "error", "stderr": "transport down", "exit_code": 9}
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = review_state.run_dual_review(pathlib.Path(temporary_directory), {"base_sha": "a", "head_sha": "b", "files": ["x.py"], "line_ranges": {"x.py": [[1, 1]]}}, {"claude": Reviewer(), "codex": Reviewer()}, critique_adapter=Failure(), synthesis_adapter=Failure())
            report = (pathlib.Path(result["run_dir"]) / "report.md").read_text()
            sidecar = json.loads((pathlib.Path(result["run_dir"]) / "provenance.json").read_text())
        # 두 리뷰어는 유효한 결과를 냈고 교차 비평 전송이 실패한 것이므로 하류 실패다.
        self.assertEqual(result["termination_reason"], "pipeline_failure")
        self.assertIn("transport down", report)
        self.assertEqual(sidecar["critique_statuses"][0]["status"], "error")

    def test_dispatches_constructed_prompts_before_any_read(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            calls = []
            class Adapter:
                def start(self, source, prompt):
                    calls.append((source, prompt)); return prompt
                def read(self, prompt):
                    if {source for source, _ in calls} != {"claude", "codex"}:
                        raise AssertionError("read before both dispatches")
                    return {"status": "ok", "payload": {"verdict": "ok", "summary": "", "findings": [], "next_steps": []}}
            result = review_state.execute_round_zero(root, {"base_sha": "a", "head_sha": "b", "files": ["x.py"]}, {"claude": Adapter(), "codex": Adapter()})
            run_dir = root / ".claude" / "dual-review-state" / result["run_id"]
            self.assertEqual(calls[0][1], (run_dir / "round0-claude.prompt").read_text())
            self.assertEqual(calls[1][1], (run_dir / "round0-codex.prompt").read_text())
            self.assertEqual(result["events"][:2], ["started:claude", "started:codex"])
            self.assertEqual(result["events"][2:], ["read:claude", "read:codex"])

    def test_invalid_payload_is_retried_once_and_retained(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            attempts = []
            class BadAdapter:
                def start(self, source, prompt):
                    attempts.append(source); return source
                def read(self, handle):
                    return {"status": "ok", "payload": {"bad": True}, "raw": "bad payload"}
            result = review_state.execute_round_zero(root, {"files": ["x.py"]}, {"claude": BadAdapter(), "codex": BadAdapter()})
            self.assertEqual(attempts, ["claude", "codex", "claude", "codex"])
            self.assertEqual(result["termination_reason"], "reviewer_failure")
            run_dir = root / ".claude" / "dual-review-state" / result["run_id"]
            self.assertIn("schema", (run_dir / "provenance.json").read_text())

    def test_start_failure_is_recorded_without_a_retry(self):
        calls = []
        class Exploding:
            def start(self, source, prompt):
                calls.append(source)
                raise RuntimeError("cannot start")
            def read(self, handle): raise AssertionError("unreachable")
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = review_state.execute_round_zero(pathlib.Path(temporary_directory), {"files": ["x.py"]}, {"claude": Exploding(), "codex": Exploding()})
            sidecar = json.loads((pathlib.Path(result["run_dir"]) / "provenance.json").read_text())
        self.assertEqual(calls, ["claude", "codex"])
        self.assertEqual(result["termination_reason"], "reviewer_failure")
        self.assertEqual({source: item["attempts"] for source, item in sidecar["reviewers"].items()}, {"claude": 0, "codex": 0})

    def test_timeout_retries_once_and_single_reviewer_is_limited(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            calls = {"claude": 0, "codex": 0}
            class Adapter:
                def start(self, source, prompt): calls[source] += 1; return source
                def read(self, source):
                    if source == "codex": return {"status": "timeout", "stderr": "late", "exit_code": 124}
                    return {"status": "ok", "payload": {"verdict": "ok", "summary": "", "findings": [], "next_steps": []}}
            result = review_state.execute_round_zero(root, {"files": ["x.py"]}, {"claude": Adapter(), "codex": Adapter()})
            self.assertEqual(calls, {"claude": 1, "codex": 2})
            self.assertEqual(result["termination_reason"], "single_reviewer")
            self.assertEqual(result["cross_critique_calls"], 0)
            self.assertEqual(result["synthesis_calls"], 0)

    def test_nonwriting_action_guard_rejects_external_or_mutating_actions(self):
        actions = ["reviewer-call", "local-artifact"]
        self.assertIsNone(review_state.assert_nonwriting_actions(actions))
        with self.assertRaises(ValueError):
            review_state.assert_nonwriting_actions(actions + ["external-write"])
        with self.assertRaises(ValueError):
            review_state.assert_nonwriting_actions(actions + ["code-mutation"])

    def test_a_downstream_failure_is_distinguished_from_a_reviewer_failure(self):
        """reviewer_failure must mean the reviewers produced nothing. A critique transport error
        after two valid round-zero reviews is a different situation demanding a different response,
        and reusing one string for both leaves the consumer unable to tell them apart."""
        class Reviewer:
            def start(self, source, prompt): return source
            def read(self, handle):
                return {"status": "ok", "payload": {"verdict": "ok", "summary": "", "findings": [{"severity": "high", "finding_confidence": .8, "file": "x.py", "line_start": 1, "line_end": 1, "title": handle, "body": "detail", "recommendation": "fix"}], "next_steps": []}}
        class Failure:
            def start(self, source, prompt): return source
            def read(self, handle): return {"status": "error", "stderr": "transport down", "exit_code": 9}
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = review_state.run_dual_review(pathlib.Path(temporary_directory), {"base_sha": "a", "head_sha": "b", "files": ["x.py"], "line_ranges": {"x.py": [[1, 1]]}}, {"claude": Reviewer(), "codex": Reviewer()}, critique_adapter=Failure(), synthesis_adapter=Failure())
            sidecar = json.loads((pathlib.Path(result["run_dir"]) / "provenance.json").read_text())
        self.assertEqual(result["termination_reason"], "pipeline_failure")
        self.assertEqual({source: item["status"] for source, item in sidecar["reviewers"].items()}, {"claude": "valid", "codex": "valid"})

    def test_a_skipped_synthesis_records_that_it_was_skipped(self):
        """A critique error skips synthesis entirely. Without a status row the report is
        indistinguishable from a run where synthesis ran and produced no decisions."""
        class Reviewer:
            def start(self, source, prompt): return source
            def read(self, handle):
                return {"status": "ok", "payload": {"verdict": "ok", "summary": "", "findings": [{"severity": "high", "finding_confidence": .8, "file": "x.py", "line_start": 1, "line_end": 1, "title": handle, "body": "detail", "recommendation": "fix"}], "next_steps": []}}
        class Failure:
            def start(self, source, prompt): return source
            def read(self, handle): return {"status": "error", "stderr": "transport down", "exit_code": 9}
        started = []
        class Synthesizer:
            def start(self, source, prompt): started.append(source); return source
            def read(self, handle): return {"status": "ok", "payload": {"decisions": []}}
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = review_state.run_dual_review(pathlib.Path(temporary_directory), {"base_sha": "a", "head_sha": "b", "files": ["x.py"], "line_ranges": {"x.py": [[1, 1]]}}, {"claude": Reviewer(), "codex": Reviewer()}, critique_adapter=Failure(), synthesis_adapter=Synthesizer())
            report = (pathlib.Path(result["run_dir"]) / "report.md").read_text()
            sidecar = json.loads((pathlib.Path(result["run_dir"]) / "provenance.json").read_text())
        self.assertEqual(started, [])
        self.assertIsNotNone(sidecar["synthesis_status"])
        self.assertEqual(sidecar["synthesis_status"]["status"], "skipped")
        self.assertIn("synthesis: skipped", report)


if __name__ == "__main__":
    unittest.main()
