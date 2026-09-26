"""Check the OSS worker's fixed tool surface without contacting a provider."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "dot_local/bin/executable_oss-research-worker"


class OSSResearchWorkerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.worktree = self.root / "worktree"
        self.worktree.mkdir()
        subprocess.run(["git", "init", "-q", str(self.worktree)], check=True)
        self.prompt = self.worktree / "task.txt"
        self.prompt.write_text("Read the local corpus and summarize it.", encoding="utf-8")
        binary = self.root / "bin"
        binary.mkdir()
        fake = binary / "claude"
        fake.write_text(
            "#!/usr/bin/env python3\n"
            "import json,os,sys\n"
            "with open(os.environ['CAPTURE_FILE'],'w') as stream:\n"
            " json.dump({'argv':sys.argv[1:],"
            "'config':os.environ.get('CLAUDE_CONFIG_DIR'),"
            "'github_token':os.environ.get('GH_TOKEN'),"
            "'ssh_agent':os.environ.get('SSH_AUTH_SOCK')},stream)\n",
            encoding="utf-8",
        )
        fake.chmod(0o755)
        self.capture = self.root / "capture.json"
        self.environment = os.environ.copy()
        self.environment["PATH"] = f"{binary}:{self.environment['PATH']}"
        self.environment["CAPTURE_FILE"] = str(self.capture)
        self.environment["CLAUDE_CONFIG_DIR"] = "/inherited/home/must/be/scrubbed"
        self.environment["GH_TOKEN"] = "must-be-scrubbed"
        self.environment["SSH_AUTH_SOCK"] = "/inherited/agent.sock"

    def launch(self, profile="claude-profile1", prompt=None):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--profile", profile,
             "--prompt-file", str(prompt or self.prompt)],
            cwd=self.worktree, env=self.environment,
            capture_output=True, text=True,
        )

    def test_profile1_has_only_local_read_tools(self):
        result = self.launch()
        self.assertEqual(result.returncode, 0, result.stderr)
        captured = json.loads(self.capture.read_text())
        argv = captured["argv"]
        self.assertEqual(argv[argv.index("--tools") + 1], "Read,Glob,Grep")
        self.assertEqual(argv[argv.index("--allowedTools") + 1], "Read,Glob,Grep")
        self.assertEqual(argv[argv.index("--permission-mode") + 1], "dontAsk")
        self.assertEqual(argv[argv.index("--permission-prompts") + 1], "none")
        for required in ("--safe-mode", "--restricted", "--strict-mcp-config",
                         "--no-chrome", "--disable-slash-commands"):
            self.assertIn(required, argv)
        self.assertEqual(argv[-1], self.prompt.read_text())
        self.assertEqual(
            captured["config"],
            str(Path.home() / ".local/share/ai-account-profiles/claude/profile1"),
        )
        self.assertIsNone(captured["github_token"])
        self.assertIsNone(captured["ssh_agent"])

    def test_profile2_removes_inherited_profile1_home(self):
        result = self.launch("claude-profile2")
        self.assertEqual(result.returncode, 0, result.stderr)
        captured = json.loads(self.capture.read_text())
        self.assertIsNone(captured["config"])
        self.assertIsNone(captured["github_token"])

    def test_prompt_outside_worktree_is_rejected_before_provider_start(self):
        outside = self.root / "outside.txt"
        outside.write_text("Read only")
        result = self.launch(prompt=outside)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.capture.exists())

    def test_prompt_symlink_is_rejected_before_provider_start(self):
        link = self.worktree / "linked.txt"
        link.symlink_to(self.prompt)
        result = self.launch(prompt=link)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.capture.exists())


if __name__ == "__main__":
    unittest.main()
