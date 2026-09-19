import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "check_quotes.py"

SOURCE = """\
### n#553 — feat: add rule
body:
Yeah, I removed the autofixer.   Its harder
to implement safely than I thought

### promise#637 — fix: avoid unsafe autofix
body:
stop autofixing `then(onFulfilled, onRejected)`
### Reviewed changes
this heading is part of promise#637, not a new section
"""


class CheckQuotesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root / "digest.md"
        self.source.write_text(SOURCE)

    def tearDown(self):
        self.tmp.cleanup()

    def check(self, result, *extra):
        path = self.root / "result.json"
        path.write_text(json.dumps(result, ensure_ascii=False))
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--source", str(self.source),
             "--section-regex", r"^### ([a-z-]+#\d+) — ", str(path), *extra],
            capture_output=True, text=True, timeout=30)
        return proc, json.loads(proc.stdout) if proc.stdout.strip() else None

    def test_nested_quotes_verified_with_whitespace_normalized(self):
        proc, report = self.check({
            "patterns": [{"evidence": [
                {"pr": "n#553", "quote": "I removed the autofixer. Its harder to implement safely"},
                {"pr": "promise#637", "quote": "stop autofixing `then(onFulfilled, onRejected)`"},
            ]}],
            "observations": [{"pr": "promise#637", "quote": "this heading is part of promise#637"}],
        })
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(report["files"][0]["verified"], 3)
        self.assertEqual(report["files"][0]["total"], 3)

    def test_quote_from_another_section_fails(self):
        proc, report = self.check({"evidence": [{"pr": "promise#637", "quote": "I removed the autofixer"}]})
        self.assertEqual(proc.returncode, 1)
        failure = report["files"][0]["failures"][0]
        self.assertEqual(failure["key"], "promise#637")
        self.assertEqual(failure["reason"], "not-found")
        self.assertEqual(failure["path"], "$.evidence[0]")

    def test_paraphrased_quote_fails(self):
        proc, report = self.check({"evidence": [{"pr": "n#553", "quote": "I removed the auto-fixer because it is hard"}]})
        self.assertEqual(proc.returncode, 1)

    def test_unknown_key_and_empty_quote_fail(self):
        proc, report = self.check({"evidence": [{"pr": "n#999", "quote": "Yeah"}, {"pr": "n#553", "quote": ""}]})
        self.assertEqual(proc.returncode, 1)
        reasons = sorted(f["reason"] for f in report["files"][0]["failures"])
        self.assertEqual(reasons, ["empty-quote", "unknown-key"])

    def test_custom_field_names(self):
        proc, report = self.check({"items": [{"source": "n#553", "excerpt": "Yeah, I removed"}]},
                                  "--key-field", "source", "--quote-field", "excerpt")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(report["files"][0]["verified"], 1)

    def test_objects_without_quote_field_are_ignored(self):
        proc, report = self.check({"pr": "n#553", "note": "no quote here", "patterns": []})
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(report["files"][0]["total"], 0)

    def test_regex_without_group_is_usage_error(self):
        path = self.root / "r.json"
        path.write_text("{}")
        proc = subprocess.run([sys.executable, str(SCRIPT), "--source", str(self.source),
                               "--section-regex", "^### ", str(path)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 2)


if __name__ == "__main__":
    unittest.main()
