import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ZSHRC_TEMPLATE = ROOT / "dot_zshrc.tmpl"
PROFILE1_SOURCE = ROOT / "dot_local/share/private_ai-account-profiles/private_claude/private_profile1"
BLOCK_START = "# >>> claude-profile1 >>>"
BLOCK_END = "# <<< claude-profile1 <<<"
PROFILE2_START = "# >>> claude-profile2 >>>"
PROFILE2_END = "# <<< claude-profile2 <<<"
PROFILE1_HOME = Path(".local/share/ai-account-profiles/claude/profile1")

FAKE_CLAUDE = textwrap.dedent(
    """\
    #!{python}
    import json, os, stat, sys
    record = {{"argv": sys.argv[1:], "config_dir": os.environ.get("CLAUDE_CONFIG_DIR")}}
    for argument in sys.argv[1:]:
        if argument.startswith("--mcp-config="):
            path = argument.split("=", 1)[1]
            record["mcp_path"] = path
            record["mcp_mode"] = stat.S_IMODE(os.stat(path).st_mode)
            with open(path, encoding="utf-8") as handle:
                record["mcp"] = json.load(handle)
    with open(os.environ["FAKE_CLAUDE_RECORD"], "w", encoding="utf-8") as handle:
        json.dump(record, handle)
    sys.exit(int(os.environ.get("FAKE_CLAUDE_EXIT", "0")))
    """
)


def zshrc_block(start_marker: str, end_marker: str) -> str:
    text = ZSHRC_TEMPLATE.read_text(encoding="utf-8")
    start = text.index(start_marker)
    end = text.index(end_marker, start) + len(end_marker)
    return text[start:end] + "\n"


def launcher_block() -> str:
    return zshrc_block(BLOCK_START, BLOCK_END) + zshrc_block(PROFILE2_START, PROFILE2_END)


@unittest.skipUnless(shutil.which("zsh"), "zsh is required")
class ClaudeProfile1LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.bin = self.root / "bin"
        self.bin.mkdir()
        fake = self.bin / "claude"
        fake.write_text(FAKE_CLAUDE.format(python=sys.executable), encoding="utf-8")
        fake.chmod(0o755)
        (self.bin / "python3").symlink_to(sys.executable)
        self.block = self.root / "claude-profile1.zsh"
        self.block.write_text(launcher_block(), encoding="utf-8")
        self.record = self.root / "record.json"

    def tearDown(self):
        self.temporary.cleanup()

    def write_default_home(self, *, settings=True, claude_json=None):
        if settings:
            (self.home / ".claude").mkdir(exist_ok=True)
            (self.home / ".claude/settings.json").write_text('{"theme": "dark"}', encoding="utf-8")
        if claude_json is not None:
            (self.home / ".claude.json").write_text(claude_json, encoding="utf-8")

    def run_launcher(self, *arguments, exit_code=0, command="claude-profile1", inherited_config_dir=None):
        environment = {
            "HOME": str(self.home),
            "PATH": f"{self.bin}:/usr/bin:/bin",
            "FAKE_CLAUDE_RECORD": str(self.record),
            "FAKE_CLAUDE_EXIT": str(exit_code),
        }
        if inherited_config_dir is not None:
            environment["CLAUDE_CONFIG_DIR"] = inherited_config_dir
        script = f'source "$1"; shift; {command} "$@"'
        result = subprocess.run(
            ["zsh", "-f", "-c", script, "zsh", str(self.block), *arguments],
            env=environment,
            text=True,
            capture_output=True,
            timeout=30,
        )
        record = json.loads(self.record.read_text(encoding="utf-8")) if self.record.exists() else None
        return result, record

    def test_shares_settings_and_only_mcp_servers(self):
        servers = {
            "playwright": {"type": "stdio", "command": "npx", "args": ["@playwright/mcp@latest"]},
            "figma": {"type": "http", "url": "https://mcp.figma.com/mcp"},
        }
        claude_json = json.dumps({"oauthAccount": {"emailAddress": "secret@example.com"}, "mcpServers": servers})
        self.write_default_home(claude_json=claude_json)

        result, record = self.run_launcher("hello world", "-p")

        self.assertEqual(0, result.returncode, result.stderr)
        profile1 = self.home / PROFILE1_HOME
        self.assertEqual(str(profile1), record["config_dir"])
        self.assertEqual(
            [
                f"--settings={self.home / '.claude/settings.json'}",
                f"--mcp-config={profile1 / '.shared-mcp.json'}",
                "hello world",
                "-p",
            ],
            record["argv"],
        )
        self.assertEqual({"mcpServers": servers}, record["mcp"])
        self.assertNotIn("oauthAccount", json.dumps(record["mcp"]))
        self.assertEqual(0o600, record["mcp_mode"])
        self.assertEqual(0o700, stat.S_IMODE(profile1.stat().st_mode))

    def test_shared_options_use_equals_form(self):
        self.write_default_home(claude_json=json.dumps({"mcpServers": {"x": {"type": "http", "url": "https://x"}}}))

        _, record = self.run_launcher("prompt right after shared options")

        shared = [argument for argument in record["argv"] if argument.startswith("--")]
        self.assertEqual(2, len(shared))
        self.assertTrue(all("=" in argument for argument in shared))
        self.assertEqual("prompt right after shared options", record["argv"][-1])

    def test_skips_mcp_when_claude_json_is_missing_empty_or_invalid(self):
        for label, claude_json in (
            ("missing", None),
            ("no servers", json.dumps({"oauthAccount": {}})),
            ("empty servers", json.dumps({"mcpServers": {}})),
            ("invalid json", "{not json"),
            ("non-object", json.dumps(["mcpServers"])),
        ):
            with self.subTest(case=label):
                (self.home / ".claude.json").unlink(missing_ok=True)
                self.record.unlink(missing_ok=True)
                self.write_default_home(claude_json=claude_json)

                result, record = self.run_launcher("-p")

                self.assertEqual(0, result.returncode, result.stderr)
                self.assertFalse(any(a.startswith("--mcp-config") for a in record["argv"]))
                self.assertEqual(f"--settings={self.home / '.claude/settings.json'}", record["argv"][0])

    def test_skips_settings_when_default_settings_are_missing(self):
        self.write_default_home(settings=False)

        _, record = self.run_launcher("-p")

        self.assertEqual(["-p"], record["argv"])

    def test_propagates_claude_exit_code(self):
        self.write_default_home()

        result, _ = self.run_launcher("-p", exit_code=7)

        self.assertEqual(7, result.returncode)

    def test_rewrites_existing_mcp_file_with_private_mode(self):
        self.write_default_home(claude_json=json.dumps({"mcpServers": {"new": {"type": "http", "url": "https://new"}}}))
        profile1 = self.home / PROFILE1_HOME
        profile1.mkdir(parents=True)
        stale = profile1 / ".shared-mcp.json"
        stale.write_text('{"mcpServers": {"old": {}}}', encoding="utf-8")
        stale.chmod(0o644)

        _, record = self.run_launcher("-p")

        self.assertEqual({"mcpServers": {"new": {"type": "http", "url": "https://new"}}}, record["mcp"])
        self.assertEqual(0o600, record["mcp_mode"])

    def test_does_not_modify_default_home_files(self):
        claude_json = json.dumps({"oauthAccount": {"id": "x"}, "mcpServers": {"a": {"type": "http", "url": "https://a"}}})
        self.write_default_home(claude_json=claude_json)
        before = {
            path: path.read_bytes()
            for path in (self.home / ".claude.json", self.home / ".claude/settings.json")
        }

        self.run_launcher("-p")

        for path, content in before.items():
            self.assertEqual(content, path.read_bytes(), path)


    def test_profile2_is_plain_claude_on_default_home(self):
        self.write_default_home(claude_json=json.dumps({"mcpServers": {"a": {"type": "http", "url": "https://a"}}}))

        result, record = self.run_launcher("hello", "-p", command="claude-profile2")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(["hello", "-p"], record["argv"])
        self.assertIsNone(record["config_dir"])
        self.assertFalse((self.home / ".local/share/ai-account-profiles/claude/profile2").exists())

    def test_profile2_clears_inherited_config_dir(self):
        self.write_default_home()

        _, record = self.run_launcher(
            "-p",
            command="claude-profile2",
            inherited_config_dir=str(self.home / PROFILE1_HOME),
        )

        self.assertIsNone(record["config_dir"])

    def test_profile2_propagates_claude_exit_code(self):
        self.write_default_home()

        result, _ = self.run_launcher("-p", exit_code=5, command="claude-profile2")

        self.assertEqual(5, result.returncode)

    def test_profile1_ignores_inherited_config_dir(self):
        self.write_default_home()

        _, record = self.run_launcher("-p", inherited_config_dir="/tmp/some-other-home")

        self.assertEqual(str(self.home / PROFILE1_HOME), record["config_dir"])


class ClaudeProfile1SharedSourceTests(unittest.TestCase):
    def test_skills_agents_workflows_are_symlinks_to_default_home(self):
        for name in ("skills", "agents", "workflows"):
            with self.subTest(name=name):
                source = PROFILE1_SOURCE / f"symlink_{name}.tmpl"
                self.assertEqual(
                    "{{ .chezmoi.homeDir }}/.claude/" + name,
                    source.read_text(encoding="utf-8").strip(),
                )
        self.assertEqual(
            {"symlink_agents.tmpl", "symlink_skills.tmpl", "symlink_workflows.tmpl"},
            {path.name for path in PROFILE1_SOURCE.iterdir()},
        )

    def test_chezmoiignore_keeps_shared_entries_managed_and_generated_mcp_ignored(self):
        ignores = {
            line.strip()
            for line in (ROOT / ".chezmoiignore").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith(("#", "{{"))
        }
        prefix = ".local/share/ai-account-profiles/claude/profile1"
        self.assertIn(f"{prefix}/.shared-mcp.json", ignores)
        for name in ("skills", "agents", "workflows"):
            with self.subTest(name=name):
                self.assertFalse(any(rule.startswith(f"{prefix}/{name}") for rule in ignores))


if __name__ == "__main__":
    unittest.main()
