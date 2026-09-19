import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "agy_fanout.py"

# 프롬프트 안의 MODE=<이름> 으로 동작을 고르는 가짜 agy.
# 호출마다 argv·cwd·cwd 안의 파일 목록을 로그에 남기고, 모드별 시도 횟수를 상태 파일로 센다.
FAKE_AGY = textwrap.dedent(
    """\
    #!/usr/bin/env python3
    import json, os, re, sys, time
    argv = sys.argv[1:]
    prompt = argv[argv.index("-p") + 1]
    mode = re.search(r"MODE=([a-z-]+)", prompt).group(1)
    state = os.environ["FAKE_AGY_STATE"]
    counter = os.path.join(state, "count-" + mode)
    n = int(open(counter).read()) + 1 if os.path.exists(counter) else 1
    open(counter, "w").write(str(n))
    with open(os.path.join(state, "calls.jsonl"), "a") as log:
        log.write(json.dumps({"argv": argv, "cwd": os.getcwd(), "cwd_files": os.listdir(os.getcwd())}) + "\\n")
    usage = {"input_tokens": 100, "output_tokens": 10, "thinking_tokens": 4, "cache_read_tokens": 50, "total_tokens": 110}
    status, response = "SUCCESS", ""
    if mode == "ok-json":
        response = "```json\\n{\\"a\\": 1}\\n```"
    elif mode == "empty-then-ok":
        response = "" if n == 1 else "{\\"b\\": 2}"
    elif mode == "always-empty":
        response = ""
    elif mode == "bad-json":
        response = "not json at all"
    elif mode == "text":
        response = "plain answer"
    elif mode == "error":
        status = "ERROR"
    elif mode == "sleep":
        time.sleep(5)
    print(json.dumps({"conversation_id": "c-" + mode, "status": status, "response": response,
                      "duration_seconds": 1.0, "num_turns": 1, "usage": usage}))
    """
)


class FanoutHarness(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.bin = root / "bin"
        self.bin.mkdir()
        fake = self.bin / "agy"
        fake.write_text(FAKE_AGY)
        fake.chmod(0o755)
        self.state = root / "state"
        self.state.mkdir()
        self.prompts = root / "prompts"
        self.prompts.mkdir()
        self.out = root / "out"

    def tearDown(self):
        self.tmp.cleanup()

    def prompt(self, name, mode):
        path = self.prompts / f"{name}.md"
        path.write_text(f"task {name}\nMODE={mode}\n")
        return path

    def run_fanout(self, *args):
        env = dict(os.environ, PATH=f"{self.bin}{os.pathsep}{os.environ['PATH']}", FAKE_AGY_STATE=str(self.state))
        return subprocess.run([sys.executable, str(SCRIPT), "--out", str(self.out), *map(str, args)],
                              capture_output=True, text=True, env=env, timeout=60)

    def calls(self):
        return [json.loads(line) for line in (self.state / "calls.jsonl").read_text().splitlines()]

    def summary(self):
        return json.loads((self.out / "summary.json").read_text())


class ExtractJsonTest(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(SCRIPT.parent))
        import agy_fanout
        self.extract = agy_fanout.extract_json

    def tearDown(self):
        sys.path.remove(str(SCRIPT.parent))

    def test_code_fence(self):
        self.assertEqual(self.extract('```json\n{"a": [1, 2]}\n```'), {"a": [1, 2]})

    def test_prose_around_object(self):
        self.assertEqual(self.extract('결과는 다음과 같다.\n{"a": 1}\n이상.'), {"a": 1})

    def test_braces_inside_strings(self):
        self.assertEqual(self.extract('{"q": "a } b { c", "n": {"x": "\\"}"}}'), {"q": "a } b { c", "n": {"x": '"}'}})

    def test_skips_invalid_candidate(self):
        self.assertEqual(self.extract('{not json} then {"ok": true}'), {"ok": True})

    def test_no_object(self):
        self.assertIsNone(self.extract("no json here"))


class FanoutTest(FanoutHarness):
    def test_parallel_success_writes_result_and_summary(self):
        proc = self.run_fanout(self.prompt("one", "ok-json"), self.prompt("two", "ok-json"), "--expect-json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads((self.out / "one.result.json").read_text()), {"a": 1})
        summary = self.summary()
        self.assertEqual([j["name"] for j in summary["jobs"]], ["one", "two"])
        self.assertTrue(all(j["ok"] for j in summary["jobs"]))
        self.assertEqual(summary["totals"]["input_tokens"], 200)
        self.assertEqual(summary["totals"]["cache_read_tokens"], 100)
        self.assertEqual(summary["totals"]["total_tokens"], 220)

    def test_default_invocation_flags(self):
        self.run_fanout(self.prompt("one", "ok-json"), "--expect-json")
        argv = self.calls()[0]["argv"]
        self.assertEqual(argv[argv.index("--model") + 1], "gemini-3.1-pro-low")
        self.assertEqual(argv[argv.index("--output-format") + 1], "json")
        self.assertIn("--disable-slash-commands", argv)
        self.assertNotIn("--json-schema", argv)
        self.assertNotIn("--conversation", argv)
        self.assertNotIn("--continue", argv)

    def test_runs_in_empty_directory_outside_caller(self):
        self.run_fanout(self.prompt("one", "ok-json"), "--expect-json")
        call = self.calls()[0]
        self.assertNotEqual(os.path.realpath(call["cwd"]), os.path.realpath(os.getcwd()))
        self.assertEqual(call["cwd_files"], [])

    def test_empty_response_is_retried(self):
        proc = self.run_fanout(self.prompt("one", "empty-then-ok"), "--expect-json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        job = self.summary()["jobs"][0]
        self.assertEqual(len(job["attempts"]), 2)
        self.assertTrue(job["attempts"][0]["empty_response"])
        self.assertEqual(json.loads((self.out / "one.result.json").read_text()), {"b": 2})

    def test_persistent_empty_response_fails(self):
        proc = self.run_fanout(self.prompt("one", "always-empty"), self.prompt("two", "ok-json"), "--expect-json")
        self.assertEqual(proc.returncode, 1)
        jobs = {j["name"]: j for j in self.summary()["jobs"]}
        self.assertFalse(jobs["one"]["ok"])
        self.assertEqual(len(jobs["one"]["attempts"]), 2)
        self.assertTrue(jobs["two"]["ok"])
        self.assertFalse((self.out / "one.result.json").exists())

    def test_unparseable_json_is_retried_then_fails(self):
        proc = self.run_fanout(self.prompt("one", "bad-json"), "--expect-json", "--retries", "2")
        self.assertEqual(proc.returncode, 1)
        job = self.summary()["jobs"][0]
        self.assertEqual(len(job["attempts"]), 3)
        self.assertFalse(job["attempts"][-1]["json_ok"])

    def test_text_mode_keeps_plain_response(self):
        proc = self.run_fanout(self.prompt("one", "text"))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual((self.out / "one.result.txt").read_text(), "plain answer")

    def test_error_status_fails(self):
        proc = self.run_fanout(self.prompt("one", "error"), "--retries", "0")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(self.summary()["jobs"][0]["attempts"][0]["status"], "ERROR")

    def test_timeout_is_recorded(self):
        proc = self.run_fanout(self.prompt("one", "sleep"), "--timeout", "1", "--retries", "0")
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(self.summary()["jobs"][0]["attempts"][0]["status"], "TIMEOUT")

    def test_duplicate_prompt_names_are_rejected(self):
        other = self.prompts / "sub"
        other.mkdir()
        (other / "one.md").write_text("MODE=ok-json")
        proc = self.run_fanout(self.prompt("one", "ok-json"), other / "one.md")
        self.assertEqual(proc.returncode, 2)
        self.assertFalse((self.state / "calls.jsonl").exists())

    def test_oversized_prompt_is_rejected_before_calling(self):
        big = self.prompts / "big.md"
        big.write_text("MODE=ok-json\n" + "가" * 400_000)
        proc = self.run_fanout(big)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("argv", proc.stderr)
        self.assertFalse((self.state / "calls.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
