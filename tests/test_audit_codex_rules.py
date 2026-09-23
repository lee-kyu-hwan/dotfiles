"""Regression tests for the read-only Codex rule inventory."""

from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "dot_local/bin/executable_audit-codex-rules"
loader = SourceFileLoader("audit_codex_rules", str(SCRIPT))
spec = spec_from_loader(loader.name, loader)
assert spec is not None
audit = module_from_spec(spec)
loader.exec_module(audit)


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


if __name__ == "__main__":
    unittest.main()
