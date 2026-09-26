"""Regression tests for the read-only Codex rule inventory."""

from contextlib import redirect_stderr, redirect_stdout
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
import io
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "dot_local/bin/executable_audit-codex-rules"
loader = SourceFileLoader("audit_codex_rules", str(SCRIPT))
spec = spec_from_loader(loader.name, loader)
assert spec is not None
audit = module_from_spec(spec)
loader.exec_module(audit)

SECRET = "ghp_regressionSECRETtoken0123456789"
SENSITIVE_RULES = (
    f'prefix_rule(pattern=["gh", "api", "-H", "Authorization: token {SECRET}"], decision="allow")\n'
    'prefix_rule(pattern=["gh", "issue", "create"], decision="allow")\n'
    'prefix_rule(pattern=["git", "push"], decision="allow")\n'
    'prefix_rule(pattern=["gh", "pr", "merge"], decision="prompt")\n'
    'prefix_rule(pattern=["gh", "issue", "list"], decision="allow")\n'
)


def run_main(argv):
    stdout, stderr = io.StringIO(), io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = audit.main(argv)
    return code, stdout.getvalue(), stderr.getvalue()


class CodexRuleAuditTests(unittest.TestCase):
    def test_generic_api_and_write_commands_are_not_treated_as_reads(self):
        cases = {
            ("gh", "api"): "github-api-generic",
            ("gh", "issue", "create"): "github-write",
            ("gh", "pr", "review"): "github-write",
            ("gh", "repo", "fork"): "github-write",
            ("git", "push"): "git-push",
            ("git", "-C", "/some/repo", "push"): "git-push",
            ("/bin/zsh", "-lc", "gh issue create"): "shell-or-env",
            ("env", "GH_TOKEN=x", "gh", "api"): "shell-or-env",
            ("gh", "issue", "list"): "github-read",
            ("gh", "run", "view"): "github-read",
        }
        for pattern, expected in cases.items():
            with self.subTest(pattern=pattern):
                self.assertEqual(audit.classify(list(pattern)), expected)

    def test_unknown_rule_shape_fails_instead_of_disappearing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rules"
            path.write_text('prefix_rule(pattern=["gh", "api"], decision="allow")\n')
            rows = audit.parse_rules(path)
            self.assertEqual(rows[0]["category"], "github-api-generic")
            path.write_text('prefix_rule(pattern=["gh"], decision="allow", extra=True)\n')
            with self.assertRaises(ValueError):
                audit.parse_rules(path)

    def test_non_string_decision_is_an_invalid_rule_not_a_traceback(self):
        decisions = ('["allow"]', '{"allow": 1}', "None", "1", '("allow",)')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rules"
            for decision in decisions:
                with self.subTest(decision=decision):
                    path.write_text(f'prefix_rule(pattern=["gh"], decision={decision})\n')
                    with self.assertRaisesRegex(ValueError, "invalid rule at line 1"):
                        audit.parse_rules(path)
                    code, stdout, stderr = run_main([str(path)])
                    self.assertEqual(code, 2)
                    self.assertEqual(stdout, "")
                    self.assertIn("Codex rules audit failed: invalid rule at line 1", stderr)
                    self.assertNotIn("Traceback", stderr)

    def test_unhashable_literal_is_an_invalid_rule(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rules"
            path.write_text('prefix_rule(pattern=["gh"], decision={["allow"]})\n')
            code, _, stderr = run_main([str(path)])
            self.assertEqual(code, 2)
            self.assertIn("invalid rule at line 1", stderr)

    def test_default_output_has_counts_but_no_rule_text(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rules"
            path.write_text(SENSITIVE_RULES)
            code, stdout, stderr = run_main([str(path)])
        self.assertEqual((code, stderr), (0, ""))
        # 카테고리 이름(git-push 등)은 집계로 남고, pattern 원소 문자열은 나가지 않는다.
        for text in (SECRET, "Authorization", '"pattern"', '"gh"', '"create"'):
            with self.subTest(text=text):
                self.assertNotIn(text, stdout)
        summary = json.loads(stdout)
        self.assertEqual(summary["total"], 5)
        self.assertEqual(summary["decisions"], {"allow": 4, "prompt": 1})
        self.assertIs(summary["raw_rules_included"], False)
        self.assertEqual(summary["direct_github_write_or_push_allow"], {
            "total": 3,
            "categories": {"github-api-generic": 1, "github-write": 1, "git-push": 1},
        })
        self.assertNotIn("rules", summary)
        self.assertNotIn("direct_github_write_or_push_allow_rules", summary)

    def test_json_flag_is_an_explicit_opt_in_to_raw_rules_with_warning(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rules"
            path.write_text(SENSITIVE_RULES)
            code, stdout, _ = run_main(["--json", str(path)])
        self.assertEqual(code, 0)
        summary = json.loads(stdout)
        self.assertIs(summary["raw_rules_included"], True)
        self.assertIn("토큰", summary["warning"])
        self.assertEqual(len(summary["rules"]), 5)
        self.assertEqual(
            [row["line"] for row in summary["direct_github_write_or_push_allow_rules"]],
            [1, 2, 3],
        )
        self.assertIn(SECRET, summary["rules"][0]["pattern"][3])


if __name__ == "__main__":
    unittest.main()
