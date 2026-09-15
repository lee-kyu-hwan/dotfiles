import json
import hashlib
import os
import pty
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import textwrap
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]
ROLE_MANIFEST = ROOT / "dot_config/ai-session/roles.toml"
SKILL_POLICY_MANIFEST = ROOT / "dot_config/ai-session/skill-policies.toml"
ROLE_DISPATCHER = ROOT / "dot_local/bin/executable_ai-role-session"
ACCOUNT_REGISTRY = ROOT / "dot_config/ai-session/accounts.toml"
ACCOUNT_SELECTOR = ROOT / "dot_local/bin/executable_ai-session"
CLAUDE_COMMON_SETTINGS = ROOT / "dot_claude/settings.json"
CLAUDE_SETTINGS_ROOT = ROOT / "dot_config/ai-session/claude"
CLAUDE_SETTINGS_REFERENCE = ROOT / "docs/claude-settings-reference.json"
INSTRUCTION_ROOT = ROOT / "dot_config/ai-session/instructions"
CLI_FIXTURE_ROOT = ROOT / "tests/fixtures/orchestrator-profiles/cli"
INSTALLED_CLI_CHECKER = ROOT / "tests/check_installed_orchestrator_cli_contract.py"
REGISTRY_CONTRACT = "orchestrator-permission-profiles-v1"
BASE_REVISION = "fcfb47ee2a0514518d150554ee491aae87d26d52"
E2E_FIXTURE_ROOT = ROOT / "tests/fixtures/orchestrator-profiles/e2e"
LIVE_ACTION_SENTINEL = E2E_FIXTURE_ROOT / "executable_fail-on-live-action"


def source_artifact_path(target_path):
    """Map a deployed-home manifest path to its chezmoi source fixture."""
    relative = Path(target_path)
    if relative.parts[:1] == (".config",):
        return ROOT / "dot_config" / Path(*relative.parts[1:])
    if relative.parts[:1] == (".claude",):
        return ROOT / "dot_claude" / Path(*relative.parts[1:])
    return ROOT / relative

T15_ALLOWED_FILES = {
    ".chezmoiignore",
    "dot_config/ai-session/accounts.toml",
    "dot_config/ai-session/roles.toml",
    "dot_config/ai-session/skill-policies.toml",
    "dot_claude/settings.json",
    "dot_config/ai-session/claude/general.settings.json",
    "dot_config/ai-session/claude/orchestrator.settings.json",
    "dot_config/ai-session/claude/feature-orchestrator.settings.json",
    "dot_config/ai-session/claude/global-orchestrator.settings.json",
    "dot_config/ai-session/instructions/codex-general.md",
    "dot_config/ai-session/instructions/codex-orchestrator.md",
    "dot_config/ai-session/instructions/codex-feature-orchestrator.md",
    "dot_config/ai-session/instructions/codex-global-orchestrator.md",
    "dot_config/ai-session/instructions/claude-general.md",
    "dot_config/ai-session/instructions/claude-orchestrator.md",
    "dot_config/ai-session/instructions/claude-feature-orchestrator.md",
    "dot_config/ai-session/instructions/claude-global-orchestrator.md",
    "dot_local/bin/executable_ai-role-session",
    "dot_local/bin/executable_ai-session",
    "dot_local/bin/symlink_ai-codex",
    "dot_local/bin/symlink_ai-codex-orchestrator",
    "dot_local/bin/symlink_ai-codex-feature-orchestrator",
    "dot_local/bin/symlink_ai-codex-global-orchestrator",
    "dot_local/bin/symlink_ai-claude",
    "dot_local/bin/symlink_ai-claude-orchestrator",
    "dot_local/bin/symlink_ai-claude-feature-orchestrator",
    "dot_local/bin/symlink_ai-claude-global-orchestrator",
    "dot_local/libexec/executable_ai-session-verify-codex",
    "dot_local/libexec/executable_ai-session-verify-claude",
    "dot_local/libexec/executable_ai-session-enroll-identity",
    "dot_local/libexec/ai_session_identity.py",
    "tests/test_ai_session.py",
    "tests/test_orchestrator_profiles.py",
    "tests/check_installed_orchestrator_cli_contract.py",
    "docs/orchestrator-permission-profiles.md",
}
T15_ALLOWED_PREFIXES = (
    "tests/fixtures/orchestrator-profiles/",
    "docs/development/2026-09-15-103-orchestrator-permission-profiles-2/",
)
INITIAL_DIRTY_PREFIXES = (
    ".claude/profile-migration/",
    "docs/development/2026-09-15-103-orchestrator-permission-profiles/",
)
PRESERVED_PATHS = (
    "dot_claude/skills/create-worktree",
    "dot_config/workmux",
    "dot_tmux.conf.tmpl",
    "dot_zshrc.tmpl",
)

LEGACY_CODEX_RECORD = """[accounts.codex-dotfiles]
provider = "codex"
auth_kind = "consumer"
config_home = "~/.local/share/ai-account-profiles/codex/dotfiles"
allowed_scopes = ["repository:lee-kyu-hwan/dotfiles"]

"""
LEGACY_CLAUDE_RECORD = """[accounts.claude-dotfiles]
provider = "claude"
auth_kind = "consumer"
config_home = "~/.local/share/ai-account-profiles/claude/dotfiles"
allowed_scopes = ["repository:lee-kyu-hwan/dotfiles"]

"""

ROLES = (
    "general",
    "orchestrator",
    "feature-orchestrator",
    "global-orchestrator",
)
ENTRYPOINTS = {
    "ai-codex": ("codex", "general"),
    "ai-codex-orchestrator": ("codex", "orchestrator"),
    "ai-codex-feature-orchestrator": ("codex", "feature-orchestrator"),
    "ai-codex-global-orchestrator": ("codex", "global-orchestrator"),
    "ai-claude": ("claude", "general"),
    "ai-claude-orchestrator": ("claude", "orchestrator"),
    "ai-claude-feature-orchestrator": ("claude", "feature-orchestrator"),
    "ai-claude-global-orchestrator": ("claude", "global-orchestrator"),
}


class OrchestratorProfileFixture(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.bin_dir = Path(self.temporary.name) / "bin"
        self.bin_dir.mkdir()
        self.environment = {
            **os.environ,
            "PATH": os.pathsep.join((str(self.bin_dir), os.environ.get("PATH", ""))),
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        isolated_home = Path(self.temporary.name) / "home"
        isolated_home.mkdir()
        self.environment["HOME"] = str(isolated_home)
        self.environment.pop("CLAUDE_CONFIG_DIR", None)

    def make_fake_executable(self, name, body):
        executable = self.bin_dir / name
        cli_probe = ""
        if name in {"codex", "claude"}:
            version = "codex-cli 0.154.0" if name == "codex" else "2.1.272 (Claude Code)"
            cli_probe = textwrap.dedent(
                f"""
                import os
                from pathlib import Path
                import sys
                if sys.argv[1:] in (["--version"], ["--help"]):
                    probe_log = os.environ.get("AI_TEST_CLI_PROBE_LOG")
                    if probe_log:
                        with Path(probe_log).open("a", encoding="utf-8") as stream:
                            stream.write({name!r} + " " + sys.argv[1] + "\\n")
                if sys.argv[1:] == ["--version"]:
                    print({version!r})
                    raise SystemExit(0)
                if sys.argv[1:] == ["--help"]:
                    print("--model --sandbox --ask-for-approval --append-system-prompt --settings --plugin-dir")
                    raise SystemExit(0)
                """
            )
        executable.write_text(
            f"#!{sys.executable}\n{cli_probe}{textwrap.dedent(body)}\n",
            encoding="utf-8",
        )
        executable.chmod(0o700)
        return executable

    def run_entrypoint(self, name, *arguments, cwd=ROOT, environment=None):
        entrypoint = self.bin_dir / name
        entrypoint.unlink(missing_ok=True)
        entrypoint.symlink_to(ROLE_DISPATCHER)
        child_environment = dict(environment or self.environment)
        preserve_pwd = child_environment.pop("AI_TEST_PRESERVE_STALE_PWD", None) == "1"
        if not preserve_pwd:
            child_environment["PWD"] = str(Path(cwd).resolve())
        return subprocess.run(
            [str(entrypoint), *arguments],
            cwd=cwd,
            env=child_environment,
            text=True,
            capture_output=True,
        )

    def reviewed_instructions(self):
        with ROLE_MANIFEST.open("rb") as stream:
            manifest = tomllib.load(stream)
        instructions = {}
        for role in ROLES:
            for provider in ("codex", "claude"):
                policy = manifest["roles"][role][provider]
                path_value = policy.get("instruction_path")
                digest = policy.get("instruction_sha256")
                version = policy.get("instruction_version")
                path = source_artifact_path(path_value) if isinstance(path_value, str) else None
                self.assertTrue(
                    path is not None
                    and path.is_file()
                    and isinstance(digest, str)
                    and version == 1,
                    "reviewed instruction digest is missing",
                )
                data = path.read_bytes()
                self.assertEqual(digest, hashlib.sha256(data).hexdigest())
                self.assertNotIn(b"\0", data)
                instructions[(provider, role)] = data.decode("utf-8")
        return instructions

    def install_source_ai_session(self):
        self.make_fake_executable(
            "ai-session",
            f"""
            import os
            import sys
            os.execv({sys.executable!r}, [{sys.executable!r}, {str(ACCOUNT_SELECTOR)!r}, *sys.argv[1:]])
            """,
        )

    def prepare_admitted_codex_launch(self):
        self.reviewed_instructions()
        registry, code_root, _, _ = self.write_strict_registry()
        subprocess.run(
            ["git", "init", "-q", str(code_root / "other")],
            check=True,
            text=True,
            capture_output=True,
        )
        (Path(self.temporary.name) / "homes/codex").mkdir(parents=True)
        verifier = self.make_fake_executable(
            "fixture-verifier",
            """
            import json
            print(json.dumps({
                "provider": "codex",
                "account_profile": "codex-default",
                "login_status": "logged_in",
                "identity_status": "matched",
                "usage_status": "sufficient",
                "cost_limit_status": "not_applicable",
            }, sort_keys=True))
            """,
        )
        self.install_source_ai_session()
        provider_capture = Path(self.temporary.name) / "provider.json"
        self.make_fake_executable(
            "codex",
            """
            import json
            import os
            from pathlib import Path
            import sys
            fds = {}
            for descriptor in (0, 1, 2):
                stat_result = os.fstat(descriptor)
                fds[str(descriptor)] = {
                    "isatty": os.isatty(descriptor),
                    "device": stat_result.st_dev,
                    "inode": stat_result.st_ino,
                    "rdevice": stat_result.st_rdev,
                }
            Path(os.environ["AI_TEST_PROVIDER_CAPTURE"]).write_text(json.dumps({
                "argv": sys.argv,
                "fds": fds,
                "pid": os.getpid(),
            }, sort_keys=True), encoding="utf-8")
            os.write(2, b"provider-stderr-owned\\n")
            """,
        )
        environment = {
            **self.environment,
            "AI_TEST_PROVIDER_CAPTURE": str(provider_capture),
            "PWD": str((code_root / "other").resolve()),
        }
        arguments = (
            "--registry",
            str(registry),
            "--verifier",
            str(verifier),
            "--",
            "fixture prompt",
        )
        return code_root / "other", environment, provider_capture, arguments

    def role_binding_arguments(self, role):
        if role == "orchestrator":
            return ("--task-id", "fixture-workgroup", "--parent-task-id", "none")
        if role == "feature-orchestrator":
            return (
                "--task-id", "fixture-quality-goal",
                "--parent-task-id", "fixture-workgroup",
            )
        return ()

    def public_records(self, stderr):
        lines = stderr.splitlines()
        records = []
        for line in lines:
            if line.startswith("{"):
                record = json.loads(line)
                self.assertEqual(
                    line,
                    json.dumps(
                        record,
                        ensure_ascii=False,
                        separators=(",", ":"),
                        sort_keys=True,
                    ),
                )
                records.append(record)
        return records

    def write_strict_registry(
        self,
        *,
        allowed_kind="directory",
        ambiguous=False,
        forbidden_alias=False,
        task_binding=False,
        codex_mapping=True,
    ):
        root = Path(self.temporary.name)
        code_root = root / "code"
        profile1_root = code_root / "profile1"
        profile2_root = code_root / "profile2"
        for path in (profile1_root / "project", profile2_root / "project", code_root / "other"):
            path.mkdir(parents=True, exist_ok=True)
        registry = root / "accounts.toml"
        task_bindings = "[]"
        if task_binding:
            task_bindings = (
                '[{ id = "task-2", provider = "claude", '
                'account_profile = "claude-profile2", '
                f'workspace_root = "{profile2_root / "project"}", binding_generation = 7 }}]'
            )
        extra_mapping = ""
        if ambiguous:
            extra_mapping = textwrap.dedent(
                f"""
                [[workspace_directory_mappings]]
                root = "{profile2_root}"
                provider = "claude"
                account_profile = "claude-profile1"
                priority = 100
                """
            )
        codex_alias = "default" if forbidden_alias else "codex-default"
        codex_mapping_block = ""
        if codex_mapping:
            codex_mapping_block = textwrap.dedent(
                f"""
                [[workspace_directory_mappings]]
                root = "{code_root}"
                provider = "codex"
                account_profile = "{codex_alias}"
                priority = 100
                """
            )
        registry.write_text(
            textwrap.dedent(
                f"""
                schema_version = 1
                contract_id = "orchestrator-permission-profiles-v1"
                task_bindings = {task_bindings}
                session_bindings = []

                [[accounts]]
                alias = "{codex_alias}"
                provider = "codex"
                auth_kind = "consumer"
                config_home = "{root}/homes/codex"
                allowed_scopes = [{{ kind = "{allowed_kind}", value = "{code_root}" }}]
                identity_enrollment_policy = "explicit_only"

                [[accounts]]
                alias = "claude-profile1"
                provider = "claude"
                auth_kind = "consumer"
                config_home_mode = "provider_default"
                allowed_scopes = [{{ kind = "directory", value = "{profile1_root}" }}]
                identity_enrollment_policy = "explicit_only"

                [[accounts]]
                alias = "claude-profile2"
                provider = "claude"
                auth_kind = "consumer"
                config_home_mode = "explicit"
                config_home = "{root}/homes/claude/profile2"
                allowed_scopes = [{{ kind = "directory", value = "{profile2_root}" }}]
                identity_enrollment_policy = "explicit_only"

                {codex_mapping_block}

                [[workspace_directory_mappings]]
                root = "{profile1_root}"
                provider = "claude"
                account_profile = "claude-profile1"
                priority = 100

                [[workspace_directory_mappings]]
                root = "{profile2_root}"
                provider = "claude"
                account_profile = "claude-profile2"
                priority = 100
                {extra_mapping}

                [legacy_records]
                codex-dotfiles = '''{LEGACY_CODEX_RECORD}'''
                claude-dotfiles = '''{LEGACY_CLAUDE_RECORD}'''
                """
            ),
            encoding="utf-8",
        )
        return registry, code_root, profile1_root, profile2_root

    def select_account(self, registry, provider, cwd, *arguments):
        return subprocess.run(
            [
                sys.executable,
                str(ACCOUNT_SELECTOR),
                "select",
                "--registry",
                str(registry),
                "--provider",
                provider,
                "--role-profile",
                "general",
                *arguments,
            ],
            cwd=cwd,
            env=self.environment,
            text=True,
            capture_output=True,
        )

    def load_claude_settings(self):
        paths = {
            role: CLAUDE_SETTINGS_ROOT / f"{role}.settings.json"
            for role in ROLES
        }
        self.assertTrue(
            CLAUDE_COMMON_SETTINGS.is_file()
            and all(path.is_file() for path in paths.values()),
            "trusted composed settings are missing",
        )
        return (
            json.loads(CLAUDE_COMMON_SETTINGS.read_text(encoding="utf-8")),
            {
                role: json.loads(path.read_text(encoding="utf-8"))
                for role, path in paths.items()
            },
        )

    def make_git_repository(self):
        repository = Path(self.temporary.name) / "repository"
        repository.mkdir(exist_ok=True)
        subprocess.run(
            ["git", "init", "-q", str(repository)],
            check=True,
            text=True,
            capture_output=True,
        )
        return repository


class OrchestratorProfileContractTests(OrchestratorProfileFixture):
    def test_file_ownership(self):
        expected_files = {
            "dot_config/ai-session/accounts.toml",
            "dot_config/ai-session/roles.toml",
            "dot_config/ai-session/skill-policies.toml",
            "dot_claude/settings.json",
            *{
                f"dot_config/ai-session/claude/{role}.settings.json"
                for role in ROLES
            },
            *{
                f"dot_config/ai-session/instructions/{provider}-{role}.md"
                for provider in ("codex", "claude")
                for role in ROLES
            },
            "dot_local/bin/executable_ai-role-session",
            "dot_local/bin/executable_ai-session",
            *{f"dot_local/bin/symlink_{entrypoint}" for entrypoint in ENTRYPOINTS},
            "dot_local/libexec/executable_ai-session-verify-codex",
            "dot_local/libexec/executable_ai-session-verify-claude",
            "dot_local/libexec/executable_ai-session-enroll-identity",
            "dot_local/libexec/ai_session_identity.py",
            "tests/test_ai_session.py",
            "tests/test_orchestrator_profiles.py",
            "tests/check_installed_orchestrator_cli_contract.py",
            "tests/fixtures/orchestrator-profiles/cli/executable_fake-ai-session-v1",
            "tests/fixtures/orchestrator-profiles/cli/executable_fake-cli-in-range",
            "tests/fixtures/orchestrator-profiles/cli/executable_fake-cli-lower",
            "tests/fixtures/orchestrator-profiles/cli/executable_fake-cli-missing-option",
            "tests/fixtures/orchestrator-profiles/cli/executable_fake-cli-upper",
            "tests/fixtures/orchestrator-profiles/e2e/executable_fake-workmux",
            "tests/fixtures/orchestrator-profiles/e2e/executable_fail-on-live-action",
            "docs/orchestrator-permission-profiles.md",
        }
        self.assertTrue(all((ROOT / path).is_file() for path in expected_files))
        inspect_only = {
            "docs/claude-settings-reference.json",
            "dot_codex/hooks.json",
            "dot_codex/private_full_auto.config.toml",
            "docs/development/2026-09-15-103-orchestrator-permission-profiles/installed-cli-contract-evidence.md",
        }
        self.assertTrue(all((ROOT / path).is_file() for path in inspect_only))
        self.assertTrue(all((ROOT / path).exists() for path in PRESERVED_PATHS))
        for entrypoint in ENTRYPOINTS:
            self.assertEqual(
                "ai-role-session",
                (ROOT / f"dot_local/bin/symlink_{entrypoint}").read_text(
                    encoding="utf-8"
                ).strip(),
            )
        selector_source = ACCOUNT_SELECTOR.read_text(encoding="utf-8")
        dispatcher_source = ROLE_DISPATCHER.read_text(encoding="utf-8")
        self.assertIn("def select_strict_account", selector_source)
        self.assertIn("def classify_verifier_payload", selector_source)
        self.assertNotIn("def select_strict_account", dispatcher_source)
        self.assertNotIn("def classify_verifier_payload", dispatcher_source)

    def test_changed_path_allowlist(self):
        tracked = subprocess.run(
            ["git", "diff", "--name-only", BASE_REVISION, "--"],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        ).stdout.splitlines()
        untracked = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        ).stdout.splitlines()
        changed = set(tracked) | set(untracked)
        task_changes = {
            path for path in changed
            if not path.startswith(INITIAL_DIRTY_PREFIXES)
        }
        unexpected = {
            path for path in task_changes
            if path not in T15_ALLOWED_FILES
            and not path.startswith(T15_ALLOWED_PREFIXES)
        }
        self.assertEqual(set(), unexpected)
        for path in PRESERVED_PATHS:
            with self.subTest(path=path):
                preserved = subprocess.run(
                    ["git", "diff", "--quiet", BASE_REVISION, "--", path],
                    cwd=ROOT,
                )
                self.assertEqual(0, preserved.returncode)

    def test_path_selection_regression(self):
        registry, code_root, profile1_root, profile2_root = self.write_strict_registry(
            task_binding=True
        )
        explicit = self.select_account(
            registry,
            "claude",
            profile2_root / "project",
            "--task-id", "task-2",
            "--account-profile", "claude-profile2",
        )
        stored = self.select_account(
            registry,
            "claude",
            profile2_root / "project",
            "--task-id", "task-2",
        )
        directory = self.select_account(
            registry, "claude", profile1_root / "project"
        )
        self.assertEqual("explicit", json.loads(explicit.stdout)["selection_source"])
        self.assertEqual("stored_binding", json.loads(stored.stdout)["selection_source"])
        self.assertEqual(
            "workspace_directory_mapping",
            json.loads(directory.stdout)["selection_source"],
        )

        default_registry, default_root, _, _ = self.write_strict_registry(
            codex_mapping=False
        )
        provider_default = self.select_account(
            default_registry, "codex", default_root / "other"
        )
        self.assertEqual(0, provider_default.returncode, provider_default.stderr)
        self.assertEqual(
            "provider_default",
            json.loads(provider_default.stdout)["selection_source"],
        )

        conflict_registry, _, _, conflicting_root = self.write_strict_registry(
            ambiguous=True
        )
        conflict = self.select_account(
            conflict_registry, "claude", conflicting_root / "project"
        )
        outside = self.select_account(registry, "claude", code_root / "other")
        self.assertEqual(2, conflict.returncode)
        self.assertIn("blocked_contract", conflict.stderr)
        self.assertEqual(2, outside.returncode)
        self.assertIn("blocked_contract", outside.stderr)

    def test_account_registry_schema(self):
        with ACCOUNT_REGISTRY.open("rb") as stream:
            registry = tomllib.load(stream)

        self.assertEqual(
            {
                "schema_version",
                "contract_id",
                "accounts",
                "workspace_directory_mappings",
                "task_bindings",
                "session_bindings",
                "legacy_records",
            },
            set(registry),
            "accounts.toml strict schema is missing",
        )
        self.assertEqual(1, registry["schema_version"])
        self.assertEqual("orchestrator-permission-profiles-v1", registry["contract_id"])
        self.assertNotIn("defaults", registry)
        self.assertNotIn("scope_bindings", registry)

        accounts = {account["alias"]: account for account in registry["accounts"]}
        self.assertEqual(
            {"codex-default", "claude-profile1", "claude-profile2"},
            set(accounts),
        )
        self.assertEqual("~/.codex", accounts["codex-default"]["config_home"])
        self.assertEqual("provider_default", accounts["claude-profile1"]["config_home_mode"])
        self.assertNotIn("config_home", accounts["claude-profile1"])
        self.assertEqual("explicit", accounts["claude-profile2"]["config_home_mode"])
        self.assertEqual(
            "~/.local/share/ai-account-profiles/claude/profile2",
            accounts["claude-profile2"]["config_home"],
        )
        reserved = {"default", "dotfiles", "work", "personal"}
        self.assertFalse(set(accounts) & reserved)
        self.assertIn("codex-default", accounts)
        for account in accounts.values():
            self.assertTrue(account["allowed_scopes"])
            self.assertEqual(
                {"directory"},
                {scope["kind"] for scope in account["allowed_scopes"]},
            )

        self.assertIsInstance(registry["task_bindings"], list)
        self.assertIsInstance(registry["session_bindings"], list)
        self.assertEqual(
            {"codex-dotfiles", "claude-dotfiles"},
            set(registry["legacy_records"]),
        )
        self.assertEqual(LEGACY_CODEX_RECORD, registry["legacy_records"]["codex-dotfiles"])
        self.assertEqual(LEGACY_CLAUDE_RECORD, registry["legacy_records"]["claude-dotfiles"])

    def test_real_path_account_selection(self):
        with ACCOUNT_REGISTRY.open("rb") as stream:
            self.assertIn(
                "workspace_directory_mappings",
                tomllib.load(stream),
                "workspace_directory_mappings is required",
            )
        registry, code_root, profile1_root, profile2_root = self.write_strict_registry(
            task_binding=True
        )

        codex = self.select_account(registry, "codex", code_root / "other")
        self.assertEqual(0, codex.returncode, codex.stderr)
        self.assertEqual("codex-default", json.loads(codex.stdout)["account_profile"])

        profile1 = self.select_account(
            registry,
            "claude",
            profile1_root / "project",
            "--repository",
            "same/remote",
        )
        profile2 = self.select_account(
            registry,
            "claude",
            profile2_root / "project",
            "--repository",
            "same/remote",
        )
        self.assertEqual(0, profile1.returncode, profile1.stderr)
        self.assertEqual(0, profile2.returncode, profile2.stderr)
        self.assertEqual("claude-profile1", json.loads(profile1.stdout)["account_profile"])
        self.assertEqual("claude-profile2", json.loads(profile2.stdout)["account_profile"])

        surface = Path(self.temporary.name) / "profile2-surface"
        surface.symlink_to(profile2_root / "project", target_is_directory=True)
        through_surface = self.select_account(registry, "claude", surface)
        self.assertEqual(0, through_surface.returncode, through_surface.stderr)
        self.assertEqual("claude-profile2", json.loads(through_surface.stdout)["account_profile"])

        stored = self.select_account(
            registry,
            "claude",
            profile2_root / "project",
            "--task-id",
            "task-2",
        )
        self.assertEqual(0, stored.returncode, stored.stderr)
        stored_binding = json.loads(stored.stdout)
        self.assertEqual("stored_binding", stored_binding["selection_source"])
        self.assertEqual(7, stored_binding["binding_generation"])

        outside = self.select_account(registry, "claude", code_root / "other")
        self.assertEqual(2, outside.returncode)
        self.assertIn("blocked_contract", outside.stderr)

    def test_allowed_scope_kind_contract(self):
        with ACCOUNT_REGISTRY.open("rb") as stream:
            self.assertIn(
                "workspace_directory_mappings",
                tomllib.load(stream),
                "workspace_directory_mappings is required",
            )
        invalid_registry, code_root, _, _ = self.write_strict_registry(
            allowed_kind="repository"
        )
        invalid = self.select_account(invalid_registry, "codex", code_root / "other")
        self.assertEqual(2, invalid.returncode)
        self.assertIn("blocked_contract", invalid.stderr)

        forbidden_registry, code_root, _, _ = self.write_strict_registry(
            forbidden_alias=True
        )
        forbidden = self.select_account(forbidden_registry, "codex", code_root / "other")
        self.assertEqual(2, forbidden.returncode)
        self.assertIn("blocked_contract", forbidden.stderr)

    def test_no_account_fallback(self):
        with ACCOUNT_REGISTRY.open("rb") as stream:
            self.assertIn(
                "workspace_directory_mappings",
                tomllib.load(stream),
                "workspace_directory_mappings is required",
            )
        registry, _, _, profile2_root = self.write_strict_registry(ambiguous=True)
        ambiguous = self.select_account(registry, "claude", profile2_root / "project")
        self.assertEqual(2, ambiguous.returncode)
        self.assertIn("blocked_contract", ambiguous.stderr)

        unknown = self.select_account(
            registry,
            "claude",
            profile2_root / "project",
            "--account-profile",
            "missing-profile",
        )
        self.assertEqual(4, unknown.returncode)
        self.assertIn("blocked_binding", unknown.stderr)

        legacy = self.select_account(
            registry,
            "claude",
            profile2_root / "project",
            "--account-profile",
            "claude-dotfiles",
        )
        self.assertEqual(4, legacy.returncode)
        self.assertIn("blocked_binding", legacy.stderr)

        stale_surface = self.select_account(
            registry,
            "claude",
            profile2_root / "project",
            "--directory",
            str(Path(self.temporary.name) / "stale-worktree"),
        )
        self.assertEqual(4, stale_surface.returncode)
        self.assertIn("blocked_binding", stale_surface.stderr)

    def test_role_manifest(self):
        self.assertTrue(
            ROLE_MANIFEST.is_file(),
            "roles.toml is required before role dispatch",
        )
        with ROLE_MANIFEST.open("rb") as stream:
            manifest = tomllib.load(stream)

        self.assertEqual({"schema_version", "roles"}, set(manifest))
        self.assertEqual(1, manifest["schema_version"])
        self.assertEqual(set(ROLES), set(manifest["roles"]))
        for role in ROLES:
            self.assertIsInstance(manifest["roles"][role], dict)

        self.assertTrue(
            SKILL_POLICY_MANIFEST.is_file(),
            "skill-policies.toml is required before role dispatch",
        )
        with SKILL_POLICY_MANIFEST.open("rb") as stream:
            skill_policies = tomllib.load(stream)
        self.assertEqual({"schema_version", "policies"}, set(skill_policies))
        self.assertEqual(1, skill_policies["schema_version"])
        self.assertIsInstance(skill_policies["policies"], dict)

    def test_launcher_entrypoints(self):
        self.assertTrue(
            ROLE_DISPATCHER.is_file(),
            "ai-role-session is required before launcher dispatch",
        )
        dispatcher_source = ROLE_DISPATCHER.read_text(encoding="utf-8")
        for duplicated_parser in ("tomllib", "load_registry", "parse_scope", "run_verifier"):
            self.assertNotIn(duplicated_parser, dispatcher_source)

        self.make_fake_executable(
            "ai-session",
            "import json, sys\nprint(json.dumps(sys.argv[1:]))",
        )
        repository = self.make_git_repository()
        for entrypoint, (provider, role) in ENTRYPOINTS.items():
            with self.subTest(entrypoint=entrypoint):
                source = ROOT / f"dot_local/bin/symlink_{entrypoint}"
                self.assertTrue(source.is_file(), f"{source.name} is required")
                self.assertEqual("ai-role-session\n", source.read_text(encoding="utf-8"))

                result = self.run_entrypoint(
                    entrypoint,
                    *self.role_binding_arguments(role),
                    "--fixture-argument",
                    cwd=repository,
                )
                self.assertEqual(0, result.returncode, result.stderr)
                command = json.loads(result.stdout)
                self.assertEqual(
                    ["launch", "--provider", provider, "--role-profile", role],
                    command[:5],
                )
                self.assertIn("--admitted", command)
                first_separator = command.index("--", 6)
                self.assertEqual(
                    provider,
                    command[command.index("--", first_separator + 1) + 1],
                )

    def test_codex_policy(self):
        with ROLE_MANIFEST.open("rb") as stream:
            manifest = tomllib.load(stream)
        policies = {
            role: manifest["roles"][role].get("codex")
            for role in ROLES
        }
        self.assertTrue(
            all(isinstance(policy, dict) and policy for policy in policies.values()),
            "Codex role policy is missing",
        )

        expected = {
            "general": {
                "model": "gpt-5.6-sol",
                "effort": "medium",
                "approval": "on-request",
                "sandbox": "workspace-write",
                "write_root": "resolved_worktree",
            },
            "orchestrator": {
                "model": "gpt-5.6-sol",
                "effort": "medium",
                "approval": "never",
                "sandbox": "workspace-write",
                "write_root": "resolved_worktree",
            },
            "feature-orchestrator": {
                "model": "gpt-5.6-sol",
                "effort": "medium",
                "approval": "never",
                "sandbox": "workspace-write",
                "write_root": "resolved_worktree",
            },
            "global-orchestrator": {
                "model": "gpt-6-astra",
                "effort": "high",
                "approval": "never",
                "sandbox": "workspace-write",
                "write_root": "verified_control_or_worktree",
            },
        }
        for role, policy in policies.items():
            with self.subTest(role=role):
                self.assertEqual(expected[role], {
                    key: policy[key]
                    for key in expected[role]
                })
                self.assertEqual(1, policy["instruction_version"])

        repository = Path(self.temporary.name) / "repository"
        repository.mkdir()
        subprocess.run(
            ["git", "init", "-q", str(repository)],
            check=True,
            text=True,
            capture_output=True,
        )
        self.make_fake_executable(
            "ai-session",
            "import json, sys\nprint(json.dumps(sys.argv[1:]))",
        )
        for entrypoint, (provider, role) in ENTRYPOINTS.items():
            if provider != "codex":
                continue
            with self.subTest(entrypoint=entrypoint):
                result = self.run_entrypoint(
                    entrypoint,
                    *self.role_binding_arguments(role),
                    "fixture prompt",
                    cwd=repository,
                )
                self.assertEqual(0, result.returncode, result.stderr)
                command = json.loads(result.stdout)
                provider_command = command[command.index("--", command.index("--") + 1) + 1:]
                policy = policies[role]
                self.assertEqual("codex", provider_command[0])
                self.assertEqual(policy["model"], provider_command[provider_command.index("--model") + 1])
                self.assertEqual(
                    f'model_reasoning_effort="{policy["effort"]}"',
                    provider_command[provider_command.index("-c") + 1],
                )
                self.assertEqual(
                    policy["approval"],
                    provider_command[provider_command.index("--ask-for-approval") + 1],
                )
                self.assertEqual(
                    policy["sandbox"],
                    provider_command[provider_command.index("--sandbox") + 1],
                )
                self.assertEqual(
                    str(repository.resolve()),
                    provider_command[provider_command.index("-C") + 1],
                )
                self.assertIn(
                    f'developer_instructions="{self.reviewed_instructions()[(provider, role)]}"',
                    provider_command,
                )
                self.assertEqual("fixture prompt", provider_command[-1])
                joined = "\0".join(provider_command)
                for forbidden in (
                    "danger-full-access",
                    "bypassPermissions",
                    "--add-dir",
                    "--dangerously-bypass-approvals-and-sandbox",
                ):
                    self.assertNotIn(forbidden, joined)

        call_count = Path(self.temporary.name) / "call-count"
        no_fallback_environment = {
            **self.environment,
            "AI_SESSION_TEST_CALL_COUNT": str(call_count),
        }
        self.make_fake_executable(
            "ai-session",
            """
            import os
            from pathlib import Path
            import sys
            counter = Path(os.environ["AI_SESSION_TEST_CALL_COUNT"])
            counter.write_text(counter.read_text() + "1" if counter.exists() else "1")
            raise SystemExit(37)
            """,
        )
        rejected = self.run_entrypoint(
            "ai-codex-global-orchestrator",
            "fixture prompt",
            cwd=repository,
            environment=no_fallback_environment,
        )
        self.assertEqual(37, rejected.returncode)
        self.assertEqual("1", call_count.read_text(encoding="utf-8"))

    def test_codex_project_config_prescan(self):
        with ROLE_MANIFEST.open("rb") as stream:
            manifest = tomllib.load(stream)
        policies = [manifest["roles"][role].get("codex") for role in ROLES]
        self.assertTrue(
            all(isinstance(policy, dict) and policy for policy in policies),
            "Codex role policy is missing",
        )
        self.assertEqual(
            [
                "notice.fast_default_opt_out",
                "tui.status_line",
                "tui.status_line_use_colors",
            ],
            manifest["roles"]["general"]["codex"]["benign_project_config_keys"],
        )

        repository = Path(self.temporary.name) / "repository"
        working_directory = repository / "packages" / "app"
        working_directory.mkdir(parents=True)
        subprocess.run(
            ["git", "init", "-q", str(repository)],
            check=True,
            text=True,
            capture_output=True,
        )
        root_config = repository / ".codex" / "config.toml"
        nested_config = repository / "packages" / ".codex" / "config.toml"
        root_config.parent.mkdir()
        nested_config.parent.mkdir()
        root_config.write_text(
            '[tui]\nstatus_line = ["model", "current-dir"]\n'
            "status_line_use_colors = true\n",
            encoding="utf-8",
        )
        nested_config.write_text(
            "# nested benign override\n[notice]\nfast_default_opt_out = true\n",
            encoding="utf-8",
        )
        call_count = Path(self.temporary.name) / "call-count"
        environment = {
            **self.environment,
            "AI_SESSION_TEST_CALL_COUNT": str(call_count),
        }
        self.make_fake_executable(
            "ai-session",
            """
            import json
            import os
            from pathlib import Path
            import sys
            counter = Path(os.environ["AI_SESSION_TEST_CALL_COUNT"])
            counter.write_text(counter.read_text() + "1" if counter.exists() else "1")
            print(json.dumps(sys.argv[1:]))
            """,
        )

        benign = self.run_entrypoint(
            "ai-codex",
            "fixture prompt",
            cwd=working_directory,
            environment=environment,
        )
        self.assertEqual(0, benign.returncode, benign.stderr)
        self.assertEqual("1", call_count.read_text(encoding="utf-8"))

        hostile_configs = (
            ('model = "different-model"\n', "blocked_policy"),
            ("[tui]\nunknown_key = true\n", "blocked_policy"),
            ("[features]\nweb_search = true\n", "blocked_policy"),
            ('sandbox_mode = "danger-full-access"\n', "blocked_permission"),
        )
        for config, status in hostile_configs:
            with self.subTest(config=config):
                root_config.write_text(config, encoding="utf-8")
                blocked = self.run_entrypoint(
                    "ai-codex",
                    "fixture prompt",
                    cwd=working_directory,
                    environment=environment,
                )
                self.assertEqual(4, blocked.returncode)
                self.assertIn(status, blocked.stderr)
                self.assertEqual("1", call_count.read_text(encoding="utf-8"))

        root_config.write_text("# comment only\n", encoding="utf-8")
        symlink_target = repository / "hostile.toml"
        symlink_target.write_text('model = "different-model"\n', encoding="utf-8")
        nested_config.unlink()
        nested_config.symlink_to(symlink_target)
        symlinked = self.run_entrypoint(
            "ai-codex",
            "fixture prompt",
            cwd=working_directory,
            environment=environment,
        )
        self.assertEqual(4, symlinked.returncode)
        self.assertIn("blocked_policy", symlinked.stderr)
        self.assertEqual("1", call_count.read_text(encoding="utf-8"))

        nested_config.unlink()
        nested_config.write_text("# comment only\n", encoding="utf-8")
        hostile_arguments = (
            (("--model", "different-model"), "blocked_policy"),
            (("--add-dir", str(repository.parent)), "blocked_permission"),
            (("--dangerously-bypass-approvals-and-sandbox",), "blocked_permission"),
        )
        for arguments, status in hostile_arguments:
            with self.subTest(arguments=arguments):
                blocked = self.run_entrypoint(
                    "ai-codex",
                    *arguments,
                    cwd=working_directory,
                    environment=environment,
                )
                self.assertEqual(4, blocked.returncode)
                self.assertIn(status, blocked.stderr)
                self.assertEqual("1", call_count.read_text(encoding="utf-8"))

    def test_claude_policy(self):
        self.load_claude_settings()
        with ROLE_MANIFEST.open("rb") as stream:
            manifest = tomllib.load(stream)
        policies = {role: manifest["roles"][role].get("claude") for role in ROLES}
        self.assertTrue(
            all(isinstance(policy, dict) and policy for policy in policies.values()),
            "Claude role policy is missing",
        )
        expected = {
            "general": ("opus[1m]", "high"),
            "orchestrator": ("opus[1m]", "high"),
            "feature-orchestrator": ("opus[1m]", "high"),
            "global-orchestrator": ("claude-fable-5-1", "medium"),
        }
        for role, policy in policies.items():
            with self.subTest(role=role):
                self.assertEqual(expected[role], (policy["model"], policy["effort"]))
                self.assertEqual(1, policy["settings_version"])
        global_policy = policies["global-orchestrator"]
        self.assertEqual("high", global_policy["elevated_effort"])
        self.assertEqual(
            "global orchestration requires sustained cross-workgroup reasoning",
            global_policy["elevation_reason"],
        )

        repository = self.make_git_repository()
        self.make_fake_executable(
            "ai-session",
            "import json, sys\nprint(json.dumps(sys.argv[1:]))",
        )
        for entrypoint, (provider, role) in ENTRYPOINTS.items():
            if provider != "claude":
                continue
            with self.subTest(entrypoint=entrypoint):
                result = self.run_entrypoint(
                    entrypoint,
                    *self.role_binding_arguments(role),
                    "fixture prompt",
                    cwd=repository,
                )
                self.assertEqual(0, result.returncode, result.stderr)
                command = json.loads(result.stdout)
                provider_command = command[command.index("--", command.index("--") + 1) + 1:]
                policy = policies[role]
                self.assertEqual("claude", provider_command[0])
                self.assertEqual(policy["model"], provider_command[provider_command.index("--model") + 1])
                effective_effort = policy.get("elevated_effort", policy["effort"])
                self.assertEqual(
                    effective_effort,
                    provider_command[provider_command.index("--effort") + 1],
                )
                self.assertEqual("fixture prompt", provider_command[-1])

        call_count = Path(self.temporary.name) / "claude-call-count"
        environment = {
            **self.environment,
            "AI_SESSION_TEST_CALL_COUNT": str(call_count),
        }
        self.make_fake_executable(
            "ai-session",
            """
            import os
            from pathlib import Path
            counter = Path(os.environ["AI_SESSION_TEST_CALL_COUNT"])
            counter.write_text(counter.read_text() + "1" if counter.exists() else "1")
            raise SystemExit(38)
            """,
        )
        rejected = self.run_entrypoint(
            "ai-claude-global-orchestrator",
            cwd=repository,
            environment=environment,
        )
        self.assertEqual(38, rejected.returncode)
        self.assertEqual("1", call_count.read_text(encoding="utf-8"))

    def test_binding_record(self):
        cwd, environment, provider_capture, arguments = self.prepare_admitted_codex_launch()
        result = self.run_entrypoint("ai-codex", *arguments, cwd=cwd, environment=environment)
        self.assertEqual(0, result.returncode, result.stderr)
        records = self.public_records(result.stderr)
        self.assertEqual(["account_binding", "role_startup"], [item["event"] for item in records])
        self.assertEqual(
            {
                "schema_version", "event", "provider", "role_profile",
                "account_profile", "account_scope", "selection_source",
                "selection_reason", "usage_admission_status", "binding_generation",
            },
            set(records[0]),
        )
        self.assertEqual(
            {
                "schema_version", "event", "cwd", "repository", "provider",
                "model", "effort", "role_profile", "manifest_id", "settings_id",
                "permission_engine", "permission_mode", "instruction_version",
                "instruction_sha256", "leader_mode", "task_id", "direct_parent_id",
                "skill_policy_id", "active_skill_count", "account_profile",
                "account_scope", "selection_source", "selection_reason",
                "usage_admission_status", "binding_generation", "dispatch_allowed",
                "lease_write_allowed",
            },
            set(records[1]),
        )
        self.assertGreater(records[0]["binding_generation"], 0)
        self.assertNotIn(str(Path(self.temporary.name) / "homes/codex"), result.stderr)
        self.assertNotIn("identity", result.stderr.lower())
        self.assertTrue(provider_capture.is_file())
        self.assertTrue(result.stderr.endswith("provider-stderr-owned\n"))

        broken_registry = Path(self.temporary.name) / "broken.toml"
        broken_registry.write_text("schema_version = 999\n", encoding="utf-8")
        failed = self.run_entrypoint(
            "ai-codex",
            "--registry", str(broken_registry),
            "--verifier", arguments[3],
            "--",
            cwd=cwd,
            environment=environment,
        )
        self.assertEqual(2, failed.returncode)
        failure_records = self.public_records(failed.stderr)
        self.assertEqual(1, len(failure_records))
        self.assertEqual(
            {
                "schema_version", "event", "status", "exit_code", "provider",
                "role_profile", "account_profile", "account_scope", "selection_source",
                "selection_reason", "usage_admission_status",
            },
            set(failure_records[0]),
        )
        self.assertEqual("launch_failure", failure_records[0]["event"])
        self.assertEqual("blocked_contract", failure_records[0]["status"])
        self.assertNotIn("999", failed.stderr)

        provider_capture.unlink()
        self.make_fake_executable(
            "fixture-verifier",
            """
            import json
            print(json.dumps({
                "provider": "codex",
                "account_profile": "codex-default",
                "login_status": "not_logged_in",
                "identity_status": "unknown",
                "usage_status": "usage_unknown",
                "cost_limit_status": "not_applicable",
            }, sort_keys=True))
            """,
        )
        admission_failed = self.run_entrypoint(
            "ai-codex", *arguments, cwd=cwd, environment=environment
        )
        self.assertEqual(3, admission_failed.returncode)
        admission_record = self.public_records(admission_failed.stderr)[0]
        self.assertEqual("not_logged_in", admission_record["status"])
        self.assertEqual("codex-default", admission_record["account_profile"])
        self.assertEqual("workspace_directory_mapping", admission_record["selection_source"])
        self.assertFalse(provider_capture.exists())

    def test_task_parent_binding(self):
        cwd, environment, _, arguments = self.prepare_admitted_codex_launch()
        result = self.run_entrypoint(
            "ai-codex-orchestrator",
            "--task-id", "workgroup-17",
            "--parent-task-id", "none",
            *arguments,
            cwd=cwd,
            environment=environment,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        startup = self.public_records(result.stderr)[1]
        self.assertEqual("workgroup-17", startup["task_id"])
        self.assertEqual("none", startup["direct_parent_id"])

        for entrypoint, extra in (
            ("ai-codex", ("--task-id", "unexpected")),
            ("ai-codex-orchestrator", ()),
            ("ai-codex-feature-orchestrator", ("--task-id", "quality-goal-17")),
        ):
            with self.subTest(entrypoint=entrypoint):
                blocked = self.run_entrypoint(
                    entrypoint,
                    *extra,
                    *arguments,
                    cwd=cwd,
                    environment=environment,
                )
                self.assertEqual(4, blocked.returncode)
                record = self.public_records(blocked.stderr)
                self.assertEqual("blocked_binding", record[0]["status"])

    def test_instruction_hash(self):
        instructions = self.reviewed_instructions()
        repository = self.make_git_repository()
        self.make_fake_executable("ai-session", "import json, sys\nprint(json.dumps(sys.argv[1:]))")
        for entrypoint, (provider, role) in ENTRYPOINTS.items():
            with self.subTest(entrypoint=entrypoint):
                result = self.run_entrypoint(
                    entrypoint,
                    *self.role_binding_arguments(role),
                    "fixture prompt",
                    cwd=repository,
                )
                self.assertEqual(0, result.returncode, result.stderr)
                command = json.loads(result.stdout)
                provider_command = command[command.index("--", command.index("--") + 1) + 1:]
                expected = instructions[(provider, role)]
                if provider == "codex":
                    self.assertIn(f'developer_instructions="{expected}"', provider_command)
                    self.assertNotIn("model_instructions_file", "\0".join(provider_command))
                else:
                    self.assertEqual(1, provider_command.count("--append-system-prompt"))
                    position = provider_command.index("--append-system-prompt")
                    self.assertEqual(expected, provider_command[position + 1])
                    joined = "\0".join(provider_command)
                    for forbidden in (
                        "--append-system-prompt-file", "--agent", "--system-prompt-file"
                    ):
                        self.assertNotIn(forbidden, joined)

        copied_root = Path(self.temporary.name) / "copied-project"
        copied_dispatcher = copied_root / "dot_local/bin/executable_ai-role-session"
        copied_dispatcher.parent.mkdir(parents=True)
        shutil.copy2(ROLE_DISPATCHER, copied_dispatcher)
        copied_config = copied_root / "dot_config/ai-session"
        shutil.copytree(ROOT / "dot_config/ai-session", copied_config)
        copied_manifest = copied_config / "roles.toml"
        original_manifest = copied_manifest.read_text(encoding="utf-8")
        copied_instruction = copied_config / "instructions/codex-general.md"
        original_instruction = copied_instruction.read_bytes()
        original_digest = hashlib.sha256(original_instruction).hexdigest()
        call_count = Path(self.temporary.name) / "invalid-instruction-call-count"
        invalid_environment = {
            **self.environment,
            "AI_SESSION_TEST_CALL_COUNT": str(call_count),
        }
        self.make_fake_executable(
            "ai-session",
            """
            import os
            from pathlib import Path
            Path(os.environ["AI_SESSION_TEST_CALL_COUNT"]).write_text("called", encoding="utf-8")
            """,
        )
        copied_entrypoint = self.bin_dir / "ai-codex"
        for case in ("invalid_utf8", "nul", "digest", "version", "symlink"):
            with self.subTest(case=case):
                copied_entrypoint.unlink(missing_ok=True)
                copied_entrypoint.symlink_to(copied_dispatcher)
                copied_manifest.write_text(original_manifest, encoding="utf-8")
                copied_instruction.unlink(missing_ok=True)
                copied_instruction.write_bytes(original_instruction)
                if case == "invalid_utf8":
                    invalid_data = b"\xff"
                    copied_instruction.write_bytes(invalid_data)
                    copied_manifest.write_text(
                        original_manifest.replace(
                            original_digest, hashlib.sha256(invalid_data).hexdigest(), 1
                        ),
                        encoding="utf-8",
                    )
                elif case == "nul":
                    invalid_data = b"instruction\0bytes"
                    copied_instruction.write_bytes(invalid_data)
                    copied_manifest.write_text(
                        original_manifest.replace(
                            original_digest, hashlib.sha256(invalid_data).hexdigest(), 1
                        ),
                        encoding="utf-8",
                    )
                elif case == "digest":
                    copied_instruction.write_bytes(original_instruction + b"changed")
                elif case == "version":
                    copied_manifest.write_text(
                        original_manifest.replace("instruction_version = 1", "instruction_version = 2", 1),
                        encoding="utf-8",
                    )
                else:
                    replacement = copied_instruction.with_name("replacement.md")
                    replacement.write_bytes(original_instruction)
                    copied_instruction.unlink()
                    copied_instruction.symlink_to(replacement)
                blocked = subprocess.run(
                    [str(copied_entrypoint), "fixture prompt"],
                    cwd=repository,
                    env=invalid_environment,
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(4, blocked.returncode)
                self.assertEqual("blocked_policy", self.public_records(blocked.stderr)[0]["status"])
                self.assertFalse(call_count.exists())

    def test_stdio_tty_inheritance(self):
        cwd, environment, provider_capture, arguments = self.prepare_admitted_codex_launch()
        entrypoint = self.bin_dir / "ai-codex"
        entrypoint.symlink_to(ROLE_DISPATCHER)
        master, slave = pty.openpty()
        slave_stat = os.fstat(slave)
        process = subprocess.Popen(
            [str(entrypoint), *arguments],
            cwd=cwd,
            env=environment,
            stdin=slave,
            stdout=slave,
            stderr=slave,
            close_fds=True,
        )
        os.close(slave)
        chunks = []
        while True:
            try:
                chunk = os.read(master, 4096)
            except OSError:
                break
            if not chunk:
                break
            chunks.append(chunk)
        os.close(master)
        self.assertEqual(0, process.wait())
        output = b"".join(chunks).decode("utf-8").replace("\r\n", "\n")
        capture = json.loads(provider_capture.read_text(encoding="utf-8"))
        self.assertEqual(process.pid, capture["pid"])
        for descriptor in ("0", "1", "2"):
            self.assertTrue(capture["fds"][descriptor]["isatty"])
            self.assertEqual(slave_stat.st_rdev, capture["fds"][descriptor]["rdevice"])
        self.assertIn("provider-stderr-owned\n", output)
        self.assertLess(output.index('"event":"role_startup"'), output.index("provider-stderr-owned"))

    def test_new_process_only(self):
        self.reviewed_instructions()
        repository = self.make_git_repository()
        call_count = Path(self.temporary.name) / "provider-count"
        environment = {**self.environment, "AI_SESSION_TEST_CALL_COUNT": str(call_count)}
        self.make_fake_executable(
            "ai-session",
            """
            import os
            from pathlib import Path
            counter = Path(os.environ["AI_SESSION_TEST_CALL_COUNT"])
            counter.write_text("called", encoding="utf-8")
            """,
        )
        for arguments in (("--resume",), ("--continue",), ("--session-id", "old-session")):
            with self.subTest(arguments=arguments):
                result = self.run_entrypoint(
                    "ai-codex", *arguments, cwd=repository, environment=environment
                )
                self.assertEqual(4, result.returncode)
                records = self.public_records(result.stderr)
                self.assertEqual("blocked_binding", records[0]["status"])
                self.assertFalse(call_count.exists())

    def test_no_current_pane_mutation(self):
        cwd, environment, provider_capture, arguments = self.prepare_admitted_codex_launch()
        sentinel = Path(self.temporary.name) / "current-state"
        sentinel.write_bytes(b"unchanged-state\n")
        before_environment = os.environ.copy()
        parent_pid = os.getpid()
        result = self.run_entrypoint("ai-codex", *arguments, cwd=cwd, environment=environment)
        self.assertEqual(0, result.returncode, result.stderr)
        capture = json.loads(provider_capture.read_text(encoding="utf-8"))
        self.assertNotEqual(parent_pid, capture["pid"])
        self.assertEqual(b"unchanged-state\n", sentinel.read_bytes())
        self.assertEqual(before_environment, os.environ)

    def prepare_workmux_harness(self):
        fixture = (
            ROOT
            / "tests/fixtures/orchestrator-profiles/e2e/executable_fake-workmux"
        )
        if not fixture.is_file():
            raise AssertionError(
                "PermissionRequest must transition directly to waiting"
            )
        workmux = self.bin_dir / "workmux"
        workmux.symlink_to(fixture)
        config_home = Path(self.temporary.name) / "separate-claude-config"
        config_home.mkdir()
        state = Path(self.temporary.name) / "workmux-turn-state"
        state.write_text("done\n", encoding="utf-8")
        calls = Path(self.temporary.name) / "workmux-calls.jsonl"
        calls.write_text("", encoding="utf-8")
        sentinel = Path(self.temporary.name) / "real-session-sentinel"
        sentinel.write_bytes(b"unchanged\n")
        environment = {
            **self.environment,
            "AI_SESSION_E2E_NETWORK": "deny",
            "AI_TEST_WORKMUX_CALLS": str(calls),
            "AI_TEST_WORKMUX_STATE": str(state),
            "CLAUDE_CONFIG_DIR": str(config_home),
            "TMUX": "",
        }
        self.assertEqual(fixture.resolve(), Path(shutil.which("workmux", path=environment["PATH"])).resolve())
        self.assertEqual([], list(config_home.iterdir()))
        return environment, state, calls, sentinel

    def run_workmux_event(self, settings, event, environment, matcher=None):
        commands = []
        for group in settings["hooks"][event]:
            group_matcher = group.get("matcher")
            if group_matcher is not None and matcher not in group_matcher.split("|"):
                continue
            commands.extend(
                hook["command"]
                for hook in group["hooks"]
                if hook.get("type") == "command"
                and hook.get("command", "").startswith("workmux ")
            )
        self.assertEqual(
            1,
            len(commands),
            f"{event} must have exactly one applicable workmux transition",
        )
        result = subprocess.run(
            commands[0].split(),
            cwd=environment["CLAUDE_CONFIG_DIR"],
            env=environment,
            text=True,
            capture_output=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        return Path(environment["AI_TEST_WORKMUX_STATE"]).read_text(
            encoding="utf-8"
        ).strip()

    def assert_workmux_surface(self, surface):
        _, composed = self.load_claude_settings()
        environment, _, calls, sentinel = self.prepare_workmux_harness()
        self.assertEqual(
            "working",
            self.run_workmux_event(
                composed["general"], "UserPromptSubmit", environment
            ),
        )
        result = subprocess.run(
            ["workmux", surface],
            cwd=environment["CLAUDE_CONFIG_DIR"],
            env=environment,
            text=True,
            capture_output=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual("working", report["turn_state"])
        self.assertFalse(report["issue_complete"])
        self.assertEqual(surface, report["surface"])
        self.assertEqual(b"unchanged\n", sentinel.read_bytes())
        self.assertEqual(2, len(calls.read_text(encoding="utf-8").splitlines()))

    def test_workmux_event_transitions(self):
        _, composed = self.load_claude_settings()
        environment, _, calls, sentinel = self.prepare_workmux_harness()
        expected = (
            ("Stop", None, "done"),
            ("Notification", "permission_prompt", "waiting"),
            ("Notification", "elicitation_dialog", "waiting"),
            ("PostToolUse", None, "working"),
            ("UserPromptSubmit", None, "working"),
            ("PermissionRequest", None, "waiting"),
        )
        for role, settings in composed.items():
            for event, matcher, status in expected:
                with self.subTest(role=role, event=event, matcher=matcher):
                    self.assertEqual(
                        status,
                        self.run_workmux_event(
                            settings, event, environment, matcher=matcher
                        ),
                    )
        records = [
            json.loads(line)
            for line in calls.read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(24, len(records))
        self.assertTrue(
            all(record["argv"][0] == "set-window-status" for record in records)
        )
        self.assertEqual(b"unchanged\n", sentinel.read_bytes())

    def test_permission_request_waiting(self):
        _, composed = self.load_claude_settings()
        environment, _, _, _ = self.prepare_workmux_harness()
        for role, settings in composed.items():
            with self.subTest(role=role):
                self.assertEqual(
                    "waiting",
                    self.run_workmux_event(
                        settings, "PermissionRequest", environment
                    ),
                    "PermissionRequest must transition directly to waiting",
                )

    def test_no_stale_done_during_active_work(self):
        _, composed = self.load_claude_settings()
        environment, _, _, _ = self.prepare_workmux_harness()
        settings = composed["feature-orchestrator"]
        self.assertEqual("done", self.run_workmux_event(settings, "Stop", environment))
        self.assertEqual(
            "working",
            self.run_workmux_event(settings, "UserPromptSubmit", environment),
        )
        status = subprocess.run(
            ["workmux", "status"],
            cwd=environment["CLAUDE_CONFIG_DIR"],
            env=environment,
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual("working", json.loads(status.stdout)["turn_state"])
        self.assertNotEqual("done", json.loads(status.stdout)["turn_state"])

    def test_no_running_process_mutation(self):
        common, _ = self.load_claude_settings()
        environment, _, calls, sentinel = self.prepare_workmux_harness()
        before_environment = os.environ.copy()
        parent_pid = os.getpid()
        for event, matcher in (
            ("Stop", None),
            ("Notification", "permission_prompt"),
            ("Notification", "elicitation_dialog"),
            ("PostToolUse", None),
            ("UserPromptSubmit", None),
            ("PermissionRequest", None),
        ):
            self.run_workmux_event(common, event, environment, matcher=matcher)
        records = [
            json.loads(line)
            for line in calls.read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(6, len(records))
        self.assertTrue(all(record["pid"] != parent_pid for record in records))
        self.assertTrue(
            all(record["argv"][0] == "set-window-status" for record in records)
        )
        self.assertEqual(b"unchanged\n", sentinel.read_bytes())
        self.assertEqual(before_environment, os.environ)

    def test_workmux_status_surface(self):
        self.assert_workmux_surface("status")

    def test_workmux_dashboard_surface(self):
        self.assert_workmux_surface("dashboard")

    def test_workmux_sidebar_surface(self):
        self.assert_workmux_surface("sidebar")

    def test_workmux_wait_surface(self):
        self.assert_workmux_surface("wait")

    def test_claude_settings_prescan(self):
        self.load_claude_settings()
        repository = self.make_git_repository()
        project_settings = repository / ".claude" / "settings.json"
        local_settings = repository / ".claude" / "settings.local.json"
        project_settings.parent.mkdir()
        project_settings.write_text(
            json.dumps({"$schema": "https://example.invalid/schema.json", "theme": "dark"}),
            encoding="utf-8",
        )
        local_settings.write_text(
            json.dumps({"spinnerTipsEnabled": False}),
            encoding="utf-8",
        )
        call_count = Path(self.temporary.name) / "claude-prescan-count"
        environment = {
            **self.environment,
            "AI_SESSION_TEST_CALL_COUNT": str(call_count),
        }
        environment.pop("CLAUDE_CONFIG_DIR", None)
        self.make_fake_executable(
            "ai-session",
            """
            import json
            import os
            from pathlib import Path
            import sys
            counter = Path(os.environ["AI_SESSION_TEST_CALL_COUNT"])
            counter.write_text(counter.read_text() + "1" if counter.exists() else "1")
            print(json.dumps(sys.argv[1:]))
            """,
        )
        benign = self.run_entrypoint(
            "ai-claude",
            cwd=repository,
            environment=environment,
        )
        self.assertEqual(0, benign.returncode, benign.stderr)
        self.assertEqual("1", call_count.read_text(encoding="utf-8"))

        hostile_values = (
            {"hooks": {}},
            {"permissions": {}},
            {"env": {}},
            {"enabledPlugins": {}},
            {"model": "different-model"},
            {"unknownPolicy": True},
        )
        for hostile in hostile_values:
            with self.subTest(hostile=hostile):
                local_settings.write_text(json.dumps(hostile), encoding="utf-8")
                blocked = self.run_entrypoint(
                    "ai-claude",
                    cwd=repository,
                    environment=environment,
                )
                self.assertEqual(4, blocked.returncode)
                self.assertIn("blocked_policy", blocked.stderr)
                self.assertEqual("1", call_count.read_text(encoding="utf-8"))

    def test_claude_settings_composition(self):
        common, composed = self.load_claude_settings()
        reference = json.loads(CLAUDE_SETTINGS_REFERENCE.read_text(encoding="utf-8"))
        self.assertEqual(
            {
                "Notification",
                "PermissionRequest",
                "PostToolUse",
                "Stop",
                "SubagentStop",
                "TaskCompleted",
                "UserPromptSubmit",
            },
            set(common["hooks"]),
        )
        for event in ("SubagentStop", "TaskCompleted"):
            expected = json.loads(
                json.dumps(reference["hooks"][event]).replace(
                    "{{ .chezmoi.homeDir }}/.local/bin/ai-agent-ghostty-notify",
                    "ai-agent-ghostty-notify",
                )
            )
            self.assertEqual(expected, common["hooks"][event])
        permission_commands = [
            hook["command"]
            for group in common["hooks"]["PermissionRequest"]
            for hook in group["hooks"]
        ]
        self.assertIn("workmux set-window-status waiting", permission_commands)
        self.assertEqual("dontAsk", common["permissions"]["defaultMode"])
        self.assertTrue(common["sandbox"]["enabled"])
        self.assertFalse(common["sandbox"]["autoAllowBashIfSandboxed"])
        for surface_name, settings in {"common": common, **composed}.items():
            for event, groups in settings["hooks"].items():
                for group in groups:
                    for hook in group["hooks"]:
                        if hook.get("type") != "command":
                            continue
                        with self.subTest(surface=surface_name, event=event, hook=hook):
                            command = hook.get("command")
                            self.assertIsInstance(command, str)
                            self.assertNotIn("{{", command)
                            self.assertNotIn("}}", command)
                            self.assertIn(
                                command.split()[0],
                                {"workmux", "ai-agent-ghostty-notify"},
                                "every command hook must use a literal deployed launcher",
                            )
        for role, settings in composed.items():
            with self.subTest(role=role):
                self.assertEqual(common["hooks"], settings["hooks"])
                self.assertEqual("dontAsk", settings["permissions"]["defaultMode"])
                self.assertTrue(settings["sandbox"]["enabled"])
                self.assertFalse(settings["sandbox"]["autoAllowBashIfSandboxed"])
                self.assertFalse(
                    set(settings["permissions"].get("allow", ()))
                    & set(settings["permissions"].get("deny", ()))
                )

        encoded = json.dumps(composed, sort_keys=True)
        for forbidden in (
            "apiKeyHelper",
            "accountId",
            "CLAUDE_CONFIG_DIR",
            "ANTHROPIC_API_KEY",
            "CLAUDE_CODE_OAUTH_TOKEN",
            "token",
            "credential",
            "~/.claude",
            "ai-account-profiles",
        ):
            self.assertNotIn(forbidden, encoded)

    def test_claude_settings_digest(self):
        self.load_claude_settings()
        with ROLE_MANIFEST.open("rb") as stream:
            manifest = tomllib.load(stream)
        for role in ROLES:
            with self.subTest(role=role):
                policy = manifest["roles"][role]["claude"]
                common_path = CLAUDE_COMMON_SETTINGS
                self.assertFalse(common_path.is_symlink())
                self.assertTrue(common_path.is_file())
                common = json.loads(common_path.read_text(encoding="utf-8"))
                canonical_common = json.dumps(
                    common,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                ).encode("utf-8")
                self.assertEqual(
                    policy["common_settings_sha256"],
                    hashlib.sha256(canonical_common).hexdigest(),
                )
                path = source_artifact_path(policy["settings_path"])
                self.assertFalse(path.is_symlink())
                self.assertTrue(path.is_file())
                self.assertEqual(
                    policy["settings_sha256"],
                    hashlib.sha256(path.read_bytes()).hexdigest(),
                )

    def test_effective_setting_sources(self):
        _, composed = self.load_claude_settings()
        repository = self.make_git_repository()
        self.make_fake_executable(
            "ai-session",
            "import json, sys\nprint(json.dumps(sys.argv[1:]))",
        )
        for entrypoint, (provider, role) in ENTRYPOINTS.items():
            if provider != "claude":
                continue
            with self.subTest(entrypoint=entrypoint):
                result = self.run_entrypoint(
                    entrypoint,
                    *self.role_binding_arguments(role),
                    cwd=repository,
                )
                self.assertEqual(0, result.returncode, result.stderr)
                command = json.loads(result.stdout)
                provider_command = command[command.index("--", command.index("--") + 1) + 1:]
                self.assertEqual(1, provider_command.count("--settings"))
                settings_value = provider_command[provider_command.index("--settings") + 1]
                self.assertEqual(
                    str(source_artifact_path(
                        f".config/ai-session/claude/{role}.settings.json"
                    ).resolve()),
                    settings_value,
                )
                self.assertEqual(composed[role], json.loads(Path(settings_value).read_text()))
                self.assertEqual(1, provider_command.count("--setting-sources"))
                self.assertEqual(
                    "",
                    provider_command[provider_command.index("--setting-sources") + 1],
                )

    def test_claude_plugin_policy(self):
        self.load_claude_settings()
        with ROLE_MANIFEST.open("rb") as stream:
            manifest = tomllib.load(stream)
        repository = self.make_git_repository()
        self.make_fake_executable(
            "ai-session",
            "import json, sys\nprint(json.dumps(sys.argv[1:]))",
        )
        for entrypoint, (provider, role) in ENTRYPOINTS.items():
            if provider != "claude":
                continue
            with self.subTest(entrypoint=entrypoint):
                plugin_paths = manifest["roles"][role]["claude"]["plugin_dirs"]
                self.assertTrue(plugin_paths)
                for plugin_path in plugin_paths:
                    source_plugin_path = source_artifact_path(plugin_path)
                    resolved = source_plugin_path.resolve()
                    self.assertTrue(resolved.is_dir())
                    self.assertFalse(source_plugin_path.is_symlink())
                    self.assertTrue(resolved.is_relative_to(ROOT))
                result = self.run_entrypoint(
                    entrypoint,
                    *self.role_binding_arguments(role),
                    cwd=repository,
                )
                self.assertEqual(0, result.returncode, result.stderr)
                command = json.loads(result.stdout)
                provider_command = command[command.index("--", command.index("--") + 1) + 1:]
                self.assertEqual(len(plugin_paths), provider_command.count("--plugin-dir"))
                self.assertNotIn("--plugin-url", provider_command)
                self.assertEqual(1, provider_command.count("--setting-sources"))
                self.assertEqual(
                    "",
                    provider_command[provider_command.index("--setting-sources") + 1],
                )

        for arguments in (
            ("--plugin-url", "https://example.invalid/plugin"),
            ("--plugin-dir", str(repository)),
            ("--settings", "{}"),
            ("--setting-sources", "project"),
        ):
            with self.subTest(arguments=arguments):
                blocked = self.run_entrypoint("ai-claude", *arguments, cwd=repository)
                self.assertEqual(4, blocked.returncode)
                self.assertIn("blocked_policy", blocked.stderr)

    def test_claude_untrusted_settings_prescan(self):
        self.load_claude_settings()
        repository = self.make_git_repository()
        settings_directory = repository / ".claude"
        settings_directory.mkdir()
        project_settings = settings_directory / "settings.json"
        call_count = Path(self.temporary.name) / "claude-untrusted-count"
        environment = {
            **self.environment,
            "AI_SESSION_TEST_CALL_COUNT": str(call_count),
        }
        self.make_fake_executable(
            "ai-session",
            """
            import os
            from pathlib import Path
            counter = Path(os.environ["AI_SESSION_TEST_CALL_COUNT"])
            counter.write_text(counter.read_text() + "1" if counter.exists() else "1")
            """,
        )
        for policy_key in ("hooks", "permissions", "env", "enabledPlugins", "mcpServers"):
            with self.subTest(policy_key=policy_key):
                project_settings.write_text(json.dumps({policy_key: {}}), encoding="utf-8")
                blocked = self.run_entrypoint(
                    "ai-claude-feature-orchestrator",
                    *self.role_binding_arguments("feature-orchestrator"),
                    cwd=repository,
                    environment=environment,
                )
                self.assertEqual(4, blocked.returncode)
                self.assertIn("blocked_policy", blocked.stderr)
                self.assertFalse(call_count.exists())

        self.install_source_ai_session()
        registry, _, profile1_root, profile2_root = self.write_strict_registry()
        explicit_home = Path(self.temporary.name) / "homes/claude/profile2"
        explicit_home.mkdir(parents=True)
        default_home_root = Path(self.temporary.name) / "provider-default-root"
        default_account_home = default_home_root / ".claude"
        default_account_home.mkdir(parents=True)
        verifier = self.make_fake_executable(
            "selected-home-verifier",
            """
            import json
            import os
            from pathlib import Path
            Path(os.environ["AI_TEST_VERIFIER_CALLED"]).write_text("called")
            print(json.dumps({
                "provider": "claude",
                "account_profile": os.environ["AI_ACCOUNT_PROFILE"],
                "login_status": "logged_in",
                "identity_status": "matched",
                "usage_status": "sufficient",
                "cost_limit_status": "not_applicable",
            }, sort_keys=True))
            """,
        )
        self.make_fake_executable(
            "claude",
            """
            from pathlib import Path
            import os
            Path(os.environ["AI_TEST_PROVIDER_CALLED"]).write_text("called")
            """,
        )
        for profile, cwd, account_home in (
            ("claude-profile1", profile1_root / "project", default_account_home),
            ("claude-profile2", profile2_root / "project", explicit_home),
        ):
            with self.subTest(profile=profile, source="selected-account-home"):
                subprocess.run(
                    ["git", "init", "-q", str(cwd)],
                    check=True,
                    text=True,
                    capture_output=True,
                )
                provider_called = Path(self.temporary.name) / f"{profile}-provider-called"
                verifier_called = Path(self.temporary.name) / f"{profile}-verifier-called"
                launch_environment = {
                    **self.environment,
                    "HOME": str(default_home_root),
                    "AI_TEST_PROVIDER_CALLED": str(provider_called),
                    "AI_TEST_VERIFIER_CALLED": str(verifier_called),
                }
                launch_environment.pop("CLAUDE_CONFIG_DIR", None)
                (account_home / "settings.json").write_text(
                    json.dumps({"theme": "dark"}), encoding="utf-8"
                )
                benign = self.run_entrypoint(
                    "ai-claude",
                    "--registry", str(registry),
                    "--verifier", str(verifier),
                    "--",
                    "fixture prompt",
                    cwd=cwd,
                    environment=launch_environment,
                )
                self.assertEqual(0, benign.returncode, benign.stderr)
                self.assertTrue(verifier_called.is_file())
                self.assertTrue(provider_called.is_file())
                verifier_called.unlink()
                provider_called.unlink()

                (account_home / "settings.json").write_text(
                    json.dumps({"hooks": {}}), encoding="utf-8"
                )
                blocked = self.run_entrypoint(
                    "ai-claude",
                    "--registry", str(registry),
                    "--verifier", str(verifier),
                    "--",
                    "fixture prompt",
                    cwd=cwd,
                    environment=launch_environment,
                )
                self.assertEqual(4, blocked.returncode, blocked.stderr)
                records = self.public_records(blocked.stderr)
                self.assertEqual("blocked_policy", records[-1]["status"])
                self.assertFalse(verifier_called.exists())
                self.assertFalse(provider_called.exists())

    def require_t6_capability_contract(self):
        with ROLE_MANIFEST.open("rb") as stream:
            manifest = tomllib.load(stream)
        global_policy = manifest["roles"]["global-orchestrator"]
        self.assertIn(
            "active_capabilities",
            global_policy,
            "one-shot leader capability is missing",
        )
        return manifest

    def write_lease_proof(
        self,
        *,
        scope,
        leader_id="leader-fixture",
        provider="codex",
        generation=1,
        direct_parent="none",
    ):
        import time

        proof = Path(self.temporary.name) / f"lease-{hashlib.sha256(scope.encode()).hexdigest()}.json"
        proof.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "scope": scope,
                    "leader_id": leader_id,
                    "provider": provider,
                    "generation": generation,
                    "expires_at": int(time.time()) + 120,
                    "direct_parent": direct_parent,
                },
                separators=(",", ":"),
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        return proof

    def global_leader_arguments(self, scope, proof, *, mode="active", leader_id="leader-fixture"):
        return (
            "--leader-mode", mode,
            "--leader-scope", scope,
            "--leader-id", leader_id,
            "--lease-proof", str(proof),
        )

    def test_global_leader(self):
        self.require_t6_capability_contract()
        import time

        repository = self.make_git_repository()
        scope = f"global:test-{Path(self.temporary.name).name}"
        proof = self.write_lease_proof(scope=scope)
        ready = Path(self.temporary.name) / "leader-ready"
        release = Path(self.temporary.name) / "leader-release"
        self.make_fake_executable(
            "ai-session",
            """
            import os
            from pathlib import Path
            import time
            Path(os.environ["AI_TEST_LEADER_READY"]).write_text("ready", encoding="utf-8")
            release = Path(os.environ["AI_TEST_LEADER_RELEASE"])
            deadline = time.monotonic() + 10
            while not release.exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            raise SystemExit(0 if release.exists() else 98)
            """,
        )
        environment = {
            **self.environment,
            "AI_TEST_LEADER_READY": str(ready),
            "AI_TEST_LEADER_RELEASE": str(release),
        }
        entrypoint = self.bin_dir / "ai-codex-global-orchestrator"
        entrypoint.symlink_to(ROLE_DISPATCHER)
        first = subprocess.Popen(
            [str(entrypoint), *self.global_leader_arguments(scope, proof)],
            cwd=repository,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        deadline = time.monotonic() + 5
        while not ready.exists() and first.poll() is None and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertTrue(ready.exists(), first.stderr.read() if first.poll() is not None else "")

        conflict = self.run_entrypoint(
            "ai-codex-global-orchestrator",
            *self.global_leader_arguments(scope, proof),
            cwd=repository,
            environment=environment,
        )
        self.assertEqual(4, conflict.returncode)
        self.assertEqual(
            "blocked_leader_conflict",
            self.public_records(conflict.stderr)[0]["status"],
        )

        other_scope = f"{scope}:other"
        other_proof = self.write_lease_proof(scope=other_scope)
        other_ready = Path(self.temporary.name) / "other-ready"
        other_release = Path(self.temporary.name) / "other-release"
        other_release.write_text("release", encoding="utf-8")
        other = self.run_entrypoint(
            "ai-codex-global-orchestrator",
            *self.global_leader_arguments(other_scope, other_proof),
            cwd=repository,
            environment={
                **environment,
                "AI_TEST_LEADER_READY": str(other_ready),
                "AI_TEST_LEADER_RELEASE": str(other_release),
            },
        )
        self.assertEqual(0, other.returncode, other.stderr)

        release.write_text("release", encoding="utf-8")
        _, first_stderr = first.communicate(timeout=5)
        self.assertEqual(0, first.returncode, first_stderr)
        reacquired = self.run_entrypoint(
            "ai-codex-global-orchestrator",
            *self.global_leader_arguments(scope, proof),
            cwd=repository,
            environment=environment,
        )
        self.assertEqual(0, reacquired.returncode, reacquired.stderr)

    def test_lock_fd_inheritance(self):
        self.require_t6_capability_contract()
        cwd, environment, provider_capture, arguments = self.prepare_admitted_codex_launch()
        scope = f"global:fd-{Path(self.temporary.name).name}"
        proof = self.write_lease_proof(scope=scope)
        verifier_capture = Path(self.temporary.name) / "verifier-fds.json"
        environment = {
            **environment,
            "AI_TEST_VERIFIER_CAPTURE": str(verifier_capture),
        }
        self.make_fake_executable(
            "fixture-verifier",
            """
            import json
            import os
            from pathlib import Path
            open_fds = []
            for descriptor in range(3, 64):
                try:
                    os.fstat(descriptor)
                except OSError:
                    continue
                open_fds.append(descriptor)
            Path(os.environ["AI_TEST_VERIFIER_CAPTURE"]).write_text(
                json.dumps(open_fds), encoding="utf-8"
            )
            print(json.dumps({
                "provider": "codex",
                "account_profile": "codex-default",
                "login_status": "logged_in",
                "identity_status": "matched",
                "usage_status": "sufficient",
                "cost_limit_status": "not_applicable",
            }, sort_keys=True))
            """,
        )
        self.make_fake_executable(
            "codex",
            """
            import json
            import os
            from pathlib import Path
            open_fds = []
            for descriptor in range(3, 64):
                try:
                    os.fstat(descriptor)
                except OSError:
                    continue
                open_fds.append(descriptor)
            Path(os.environ["AI_TEST_PROVIDER_CAPTURE"]).write_text(
                json.dumps({"open_fds": open_fds}), encoding="utf-8"
            )
            """,
        )
        result = self.run_entrypoint(
            "ai-codex-global-orchestrator",
            *self.global_leader_arguments(scope, proof),
            *arguments,
            cwd=cwd,
            environment=environment,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual([], json.loads(verifier_capture.read_text(encoding="utf-8")))
        provider_fds = json.loads(provider_capture.read_text(encoding="utf-8"))["open_fds"]
        self.assertEqual(1, len(provider_fds), provider_fds)

    def test_reviewer_standby(self):
        self.require_t6_capability_contract()
        repository = self.make_git_repository()
        capture = Path(self.temporary.name) / "reviewer-standby.jsonl"
        self.make_fake_executable(
            "ai-session",
            """
            import json
            import os
            from pathlib import Path
            import sys
            open_fds = []
            for descriptor in range(3, 64):
                try:
                    os.fstat(descriptor)
                except OSError:
                    continue
                open_fds.append(descriptor)
            path = Path(os.environ["AI_TEST_ROLE_CAPTURE"])
            with path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps({
                    "argv": sys.argv[1:],
                    "internal_env": sorted(
                        key for key in os.environ
                        if "CAPABILITY" in key or "LEASE_WRITE" in key or "LOCK_FD" in key
                    ),
                    "open_fds": open_fds,
                }, sort_keys=True) + "\\n")
            """,
        )
        for mode in ("reviewer", "standby"):
            result = self.run_entrypoint(
                "ai-codex-global-orchestrator",
                "--leader-mode", mode,
                "--leader-scope", "global:read-only",
                "--leader-id", f"{mode}-fixture",
                cwd=repository,
                environment={**self.environment, "AI_TEST_ROLE_CAPTURE": str(capture)},
            )
            self.assertEqual(0, result.returncode, result.stderr)
        records = [json.loads(line) for line in capture.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(2, len(records))
        for record in records:
            joined = "\0".join(record["argv"])
            self.assertNotIn("capability", joined.lower())
            self.assertNotIn("lock-fd", joined.lower())
            self.assertEqual([], record["internal_env"])
            self.assertEqual([], record["open_fds"])

    def test_takeover(self):
        self.require_t6_capability_contract()
        repository = self.make_git_repository()
        scope = f"global:takeover-{Path(self.temporary.name).name}"
        proof = self.write_lease_proof(scope=scope, direct_parent="previous-owner")
        original_proof = proof.read_bytes()
        sentinel = Path(self.temporary.name) / "existing-owner-state"
        sentinel.write_bytes(b"owner-alive\n")
        called = Path(self.temporary.name) / "takeover-called"
        self.make_fake_executable(
            "ai-session",
            """
            import os
            from pathlib import Path
            Path(os.environ["AI_TEST_TAKEOVER_CALLED"]).write_text("called", encoding="utf-8")
            """,
        )
        blocked = self.run_entrypoint(
            "ai-codex-global-orchestrator",
            *self.global_leader_arguments(scope, proof),
            cwd=repository,
            environment={**self.environment, "AI_TEST_TAKEOVER_CALLED": str(called)},
        )
        self.assertEqual(4, blocked.returncode)
        self.assertEqual("blocked_binding", self.public_records(blocked.stderr)[0]["status"])
        self.assertEqual(original_proof, proof.read_bytes())
        self.assertEqual(b"owner-alive\n", sentinel.read_bytes())
        self.assertFalse(called.exists())

    def test_role_account_orthogonality(self):
        self.require_t6_capability_contract()
        repository = self.make_git_repository()
        self.make_fake_executable(
            "ai-session",
            "import json, sys\nprint(json.dumps(sys.argv[1:]))",
        )
        captures = []
        for account in ("codex-default", "codex-secondary"):
            result = self.run_entrypoint(
                "ai-codex-global-orchestrator",
                "--leader-mode", "reviewer",
                "--leader-scope", "global:orthogonal",
                "--leader-id", "reviewer-fixture",
                "--account-profile", account,
                cwd=repository,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            command = json.loads(result.stdout)
            admitted = command[command.index("--") + 1 :]
            metadata = json.loads(admitted[admitted.index("--admitted") + 1])
            provider_command = admitted[admitted.index("--", admitted.index("--admitted") + 1) + 1 :]
            captures.append(
                json.dumps(
                    {"metadata": metadata, "provider_command": provider_command},
                    separators=(",", ":"),
                    sort_keys=True,
                ).encode()
            )
        self.assertEqual(captures[0], captures[1])

    def test_startup_record(self):
        self.require_t6_capability_contract()
        cwd, environment, _, arguments = self.prepare_admitted_codex_launch()
        scope = f"global:startup-{Path(self.temporary.name).name}"
        proof = self.write_lease_proof(scope=scope)
        result = self.run_entrypoint(
            "ai-codex-global-orchestrator",
            *self.global_leader_arguments(scope, proof),
            *arguments,
            cwd=cwd,
            environment=environment,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        startup = self.public_records(result.stderr)[1]
        self.assertEqual("active", startup["leader_mode"])
        self.assertEqual("global-active-v1", startup["skill_policy_id"])
        self.assertEqual(3, startup["active_skill_count"])
        self.assertTrue(startup["dispatch_allowed"])
        self.assertFalse(startup["lease_write_allowed"])
        serialized = json.dumps(startup, sort_keys=True)
        for forbidden_field in (
            "config_home",
            "credential",
            "identity",
            "identity_digest",
            "raw_provider_output",
        ):
            self.assertNotIn(forbidden_field, startup)
        for forbidden_marker in (
            ".local/share/ai-account-profiles/",
            "TOKEN-fixture",
            "private@example.invalid",
            "raw-provider-stderr",
        ):
            self.assertNotIn(forbidden_marker, serialized)

    def test_sensitive_data_hygiene(self):
        cwd, environment, provider_capture, arguments = self.prepare_admitted_codex_launch()
        environment.update({
            "CODEX_API_KEY": "T15-CODEX-CREDENTIAL",
            "OPENAI_API_KEY": "T15-OPENAI-CREDENTIAL",
            "ANTHROPIC_AUTH_TOKEN": "T15-ANTHROPIC-CREDENTIAL",
            "AI_TEST_RAW_IDENTITY": "T15-RAW-IDENTITY",
            "AI_TEST_IDENTITY_DIGEST": "a" * 64,
        })
        scope = f"global:hygiene-{Path(self.temporary.name).name}"
        proof = self.write_lease_proof(scope=scope)
        result = self.run_entrypoint(
            "ai-codex-global-orchestrator",
            *self.global_leader_arguments(scope, proof),
            *arguments,
            cwd=cwd,
            environment=environment,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        failure_repository = self.make_git_repository()
        failure = self.run_entrypoint(
            "ai-codex",
            "--model", "T15-PRIVATE-HOME/T15-RAW-IDENTITY",
            cwd=failure_repository,
            environment=environment,
        )
        self.assertEqual(4, failure.returncode)
        surfaces = (
            result.stdout,
            result.stderr,
            failure.stdout,
            failure.stderr,
            provider_capture.read_text(encoding="utf-8"),
            (ROOT / "docs/orchestrator-permission-profiles.md").read_text(
                encoding="utf-8"
            ),
        )
        for marker in (
            "T15-CODEX-CREDENTIAL",
            "T15-OPENAI-CREDENTIAL",
            "T15-ANTHROPIC-CREDENTIAL",
            "T15-RAW-IDENTITY",
            "a" * 64,
            "~/.local/share/ai-account-profiles/claude/profile2",
        ):
            with self.subTest(marker=marker[:16]):
                self.assertTrue(all(marker not in surface for surface in surfaces))

    def test_no_auth_copy_or_symlink(self):
        registry, code_root, _, _ = self.write_strict_registry()
        synthetic_home = Path(self.temporary.name) / "homes/codex"
        synthetic_home.mkdir(parents=True)
        credential = synthetic_home / "auth.json"
        credential.write_bytes(b"T15 synthetic credential bytes\n")
        before = credential.read_bytes()
        selected = self.select_account(registry, "codex", code_root / "other")
        self.assertEqual(0, selected.returncode, selected.stderr)
        self.assertEqual(before, credential.read_bytes())
        self.assertFalse(credential.is_symlink())
        for entrypoint in ENTRYPOINTS:
            source = ROOT / f"dot_local/bin/symlink_{entrypoint}"
            self.assertEqual("ai-role-session", source.read_text(encoding="utf-8").strip())
        production_sources = (
            ACCOUNT_SELECTOR,
            ROLE_DISPATCHER,
            ROOT / "dot_local/libexec/executable_ai-session-verify-codex",
            ROOT / "dot_local/libexec/executable_ai-session-verify-claude",
            ROOT / "dot_local/libexec/executable_ai-session-enroll-identity",
        )
        source_text = "\n".join(path.read_text(encoding="utf-8") for path in production_sources)
        for forbidden_operation in (
            "shutil.copy",
            "copyfile(",
            "copy2(",
            ".symlink_to(",
            "os.symlink(",
        ):
            self.assertNotIn(forbidden_operation, source_text)

    def test_legacy_home_preservation(self):
        registry_before = ACCOUNT_REGISTRY.read_bytes()
        with ACCOUNT_REGISTRY.open("rb") as stream:
            legacy = tomllib.load(stream)["legacy_records"]
        self.assertEqual(LEGACY_CODEX_RECORD, legacy["codex-dotfiles"])
        self.assertEqual(LEGACY_CLAUDE_RECORD, legacy["claude-dotfiles"])
        registry, code_root, _, _ = self.write_strict_registry()
        result = self.select_account(registry, "codex", code_root / "other")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(registry_before, ACCOUNT_REGISTRY.read_bytes())

    def test_no_unrestricted_path(self):
        with ROLE_MANIFEST.open("rb") as stream:
            manifest = tomllib.load(stream)
        for role in ROLES:
            codex = manifest["roles"][role]["codex"]
            self.assertIn(codex["sandbox"], {"workspace-write", "read-only"})
            self.assertNotIn(codex["write_root"], {"*", "/", "unrestricted"})
            self.assertNotEqual("danger-full-access", codex["sandbox"])
            claude = manifest["roles"][role]["claude"]
            self.assertNotIn("bypassPermissions", claude.values())
        for path in CLAUDE_SETTINGS_ROOT.glob("*.settings.json"):
            settings = json.loads(path.read_text(encoding="utf-8"))
            self.assertNotEqual("bypassPermissions", settings.get("permissions", {}).get("defaultMode"))

    def test_high_risk_e2e(self):
        cwd, environment, provider_capture, arguments = self.prepare_admitted_codex_launch()
        environment["AI_SESSION_E2E_NETWORK"] = "deny"
        live_action_log = Path(self.temporary.name) / "live-actions.jsonl"
        environment["AI_TEST_LIVE_ACTION_LOG"] = str(live_action_log)
        for command in (
            "auth", "status", "usage", "login", "logout", "enroll",
            "ai-session-enroll-identity", "chezmoi", "tmux", "curl", "wget", "ssh",
            "claude",
        ):
            shutil.copy2(LIVE_ACTION_SENTINEL, self.bin_dir / command)
            (self.bin_dir / command).chmod(0o700)
        scope = f"global:e2e-{Path(self.temporary.name).name}"
        proof = self.write_lease_proof(scope=scope)
        result = self.run_entrypoint(
            "ai-codex-global-orchestrator",
            *self.global_leader_arguments(scope, proof),
            *arguments,
            cwd=cwd,
            environment=environment,
        )
        self.assertEqual("deny", environment["AI_SESSION_E2E_NETWORK"])
        self.assertEqual(0, result.returncode, result.stderr)
        capture = json.loads(provider_capture.read_text(encoding="utf-8"))
        self.assertTrue(Path(capture["argv"][0]).is_relative_to(self.bin_dir))
        forbidden_paths = {"auth", "status", "usage", "login", "logout", "enroll"}
        self.assertTrue(forbidden_paths.isdisjoint(capture["argv"]))
        self.assertFalse(live_action_log.exists())
        self.assertEqual(
            ["account_binding", "role_startup"],
            [record["event"] for record in self.public_records(result.stderr)],
        )

    def test_chezmoi_fixture_render(self):
        render_root = Path(self.temporary.name) / "rendered-home"
        target_bin = render_root / ".local/bin"
        target_bin.mkdir(parents=True)
        dispatcher = target_bin / "ai-role-session"
        shutil.copyfile(ROLE_DISPATCHER, dispatcher)
        dispatcher.chmod(0o700)
        for entrypoint in ENTRYPOINTS:
            source = ROOT / f"dot_local/bin/symlink_{entrypoint}"
            target = target_bin / entrypoint
            target.symlink_to(source.read_text(encoding="utf-8").strip())
            self.assertTrue(target.is_symlink())
            self.assertEqual(Path("ai-role-session"), target.readlink())
            self.assertEqual(dispatcher.resolve(), target.resolve())
        self.assertEqual(0o700, dispatcher.stat().st_mode & 0o777)
        self.assertEqual(ROLE_DISPATCHER.read_bytes(), dispatcher.read_bytes())

        target_config = render_root / ".config/ai-session"
        target_config.mkdir(parents=True)
        shutil.copyfile(ROLE_MANIFEST, target_config / "roles.toml")
        shutil.copyfile(SKILL_POLICY_MANIFEST, target_config / "skill-policies.toml")
        shutil.copyfile(ACCOUNT_REGISTRY, target_config / "accounts.toml")
        with ROLE_MANIFEST.open("rb") as stream:
            manifest = tomllib.load(stream)
        deployed_artifacts = set()
        for role in ROLES:
            for provider in ("codex", "claude"):
                policy = manifest["roles"][role][provider]
                deployed_artifacts.add(policy["instruction_path"])
                if provider == "claude":
                    deployed_artifacts.add(policy["settings_path"])
                    for plugin_path in policy["plugin_dirs"]:
                        (render_root / plugin_path).mkdir(parents=True, exist_ok=True)
        active_ignores = {
            line.strip()
            for line in (ROOT / ".chezmoiignore").read_text(
                encoding="utf-8"
            ).splitlines()
            if line.strip() and not line.lstrip().startswith(("#", "{{"))
        }
        self.assertIn(".claude/settings.json", active_ignores)
        for target_name in deployed_artifacts:
            self.assertNotIn(target_name, active_ignores)
            target = render_root / target_name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_artifact_path(target_name), target)

        self.make_fake_executable(
            "ai-session", "import json, sys\nprint(json.dumps(sys.argv[1:]))"
        )
        for provider in ("codex", "claude"):
            self.make_fake_executable(provider, "raise SystemExit(0)")
            entrypoint = target_bin / f"ai-{provider}"
            rendered_environment = {
                **self.environment,
                "HOME": str(render_root),
                "XDG_CONFIG_HOME": str(render_root / ".config"),
                "PATH": os.pathsep.join((str(self.bin_dir), self.environment["PATH"])),
                "PWD": str(self.make_git_repository().resolve()),
            }
            result = subprocess.run(
                [str(entrypoint), "fixture prompt"],
                cwd=rendered_environment["PWD"],
                env=rendered_environment,
                text=True,
                capture_output=True,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            command = json.loads(result.stdout)
            self.assertIn("--admitted", command)
            self.assertIn(provider, command[command.index("--admitted"):])
            provider_command = command[command.index("--", command.index("--") + 1) + 1:]
            self.assertEqual(provider, provider_command[0])
            if provider == "claude":
                settings_path = Path(
                    provider_command[provider_command.index("--settings") + 1]
                )
                plugin_path = Path(
                    provider_command[provider_command.index("--plugin-dir") + 1]
                )
                self.assertTrue(settings_path.is_relative_to(render_root.resolve()))
                self.assertEqual((render_root / ".claude").resolve(), plugin_path)
                self.assertFalse((render_root / ".claude/settings.json").exists())
            registry_index = command.index("--registry")
            self.assertEqual(
                str((target_config / "accounts.toml").resolve()),
                command[registry_index + 1],
            )

        rendered_selector = target_bin / "ai-session"
        shutil.copyfile(ACCOUNT_SELECTOR, rendered_selector)
        rendered_selector.chmod(0o700)
        registry, _, profile1_root, _ = self.write_strict_registry()
        shutil.copyfile(registry, target_config / "accounts.toml")
        provider_capture = Path(self.temporary.name) / "rendered-claude-provider.json"
        verifier = self.make_fake_executable(
            "rendered-home-verifier",
            """
            import json
            import os
            print(json.dumps({
                "provider": "claude",
                "account_profile": os.environ["AI_ACCOUNT_PROFILE"],
                "login_status": "logged_in",
                "identity_status": "matched",
                "usage_status": "sufficient",
                "cost_limit_status": "not_applicable",
            }, sort_keys=True))
            """,
        )
        self.make_fake_executable(
            "claude",
            """
            import json
            import os
            from pathlib import Path
            import sys
            Path(os.environ["AI_TEST_PROVIDER_CAPTURE"]).write_text(
                json.dumps({"argv": sys.argv, "config_home": os.environ.get("CLAUDE_CONFIG_DIR")}),
                encoding="utf-8",
            )
            """,
        )
        provider_default_repository = profile1_root / "project"
        subprocess.run(
            ["git", "init", "-q", str(provider_default_repository)],
            check=True,
            text=True,
            capture_output=True,
        )
        admitted_environment = {
            **self.environment,
            "HOME": str(render_root),
            "XDG_CONFIG_HOME": str(render_root / ".config"),
            "PATH": os.pathsep.join(
                (str(target_bin), str(self.bin_dir), self.environment["PATH"])
            ),
            "PWD": str(provider_default_repository.resolve()),
            "AI_TEST_PROVIDER_CAPTURE": str(provider_capture),
        }
        admitted_environment.pop("CLAUDE_CONFIG_DIR", None)
        admitted = subprocess.run(
            [str(target_bin / "ai-claude"), "--verifier", str(verifier), "--", "fixture prompt"],
            cwd=provider_default_repository,
            env=admitted_environment,
            text=True,
            capture_output=True,
        )
        self.assertEqual(0, admitted.returncode, admitted.stderr)
        self.assertEqual(
            ["account_binding", "role_startup"],
            [record["event"] for record in self.public_records(admitted.stderr)],
        )
        capture = json.loads(provider_capture.read_text(encoding="utf-8"))
        self.assertIsNone(capture["config_home"])
        self.assertEqual("claude", Path(capture["argv"][0]).name)

    def test_dispatcher_blocked_contract_exit_code(self):
        for admitted_environment in (
            self.environment,
            {**self.environment, "AI_ROLE_ADMITTED": "1"},
        ):
            with self.subTest(admitted=admitted_environment.get("AI_ROLE_ADMITTED")):
                result = subprocess.run(
                    [sys.executable, str(ROLE_DISPATCHER), "--admitted"],
                    env=admitted_environment,
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(2, result.returncode, result.stderr)
                record = self.public_records(result.stderr)[-1]
                self.assertEqual("blocked_contract", record["status"])
                self.assertEqual(2, record["exit_code"])

    def test_skill_policy(self):
        manifest = self.require_t6_capability_contract()
        with SKILL_POLICY_MANIFEST.open("rb") as stream:
            skill_manifest = tomllib.load(stream)
        self.assertEqual({"schema_version", "policies"}, set(skill_manifest))
        self.assertEqual(1, skill_manifest["schema_version"])
        policies = skill_manifest["policies"]
        referenced = set()
        for role in ROLES:
            role_policy = manifest["roles"][role]
            for key, value in role_policy.items():
                if key.endswith("skill_policy_id"):
                    referenced.add(value)
        self.assertEqual(referenced, set(policies))
        for policy_id, policy in policies.items():
            with self.subTest(policy_id=policy_id):
                self.assertEqual(
                    {"version", "policy_id", "discovered_catalog", "allow", "task_overlay", "deny", "capabilities", "capability_deny", "status_hook_capabilities"},
                    set(policy),
                )
                self.assertEqual(1, policy["version"])
                self.assertEqual(policy_id, policy["policy_id"])
                active = (
                    set(policy["discovered_catalog"])
                    & set(policy["allow"])
                    & set(policy["task_overlay"])
                ) - set(policy["deny"])
                self.assertNotIn("plugin:network-marketplace", active)
                self.assertEqual(["observability"], policy["status_hook_capabilities"])
                if policy_id in {"global-reviewer-v1", "global-standby-v1"}:
                    self.assertTrue(
                        {"dispatch", "multi-agent", "lease-write"}
                        <= set(policy["capability_deny"])
                    )
                    self.assertTrue(
                        {"skill:dispatching-parallel-agents", "skill:subagent-driven-development"}
                        <= set(policy["deny"])
                    )
                    self.assertEqual({"observability"}, set(policy["capabilities"]))
                    self.assertEqual({"hook:workmux-status"}, active)

    def test_full_auto_compatibility(self):
        self.require_t6_capability_contract()
        relative = "dot_codex/private_full_auto.config.toml"
        baseline = subprocess.run(
            ["git", "show", f"fcfb47ee2a0514518d150554ee491aae87d26d52:{relative}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        ).stdout
        self.assertEqual(baseline, (ROOT / relative).read_bytes())
        for path in (ROLE_MANIFEST, SKILL_POLICY_MANIFEST, ROLE_DISPATCHER, ACCOUNT_SELECTOR):
            self.assertNotIn(
                "private_full_auto.config.toml",
                path.read_text(encoding="utf-8"),
            )

    def require_t7_verifier_contract(self):
        paths = {
            "codex": ROOT / "dot_local/libexec/executable_ai-session-verify-codex",
            "claude": ROOT / "dot_local/libexec/executable_ai-session-verify-claude",
            "enrollment": ROOT / "dot_local/libexec/executable_ai-session-enroll-identity",
            "identity": ROOT / "dot_local/libexec/ai_session_identity.py",
        }
        self.assertTrue(
            all(path.is_file() for path in paths.values()),
            "verifier must return six redacted fields",
        )
        return paths

    def load_identity_module(self, path):
        import importlib.util

        spec = importlib.util.spec_from_file_location("ai_session_identity_fixture", path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        self.addCleanup(sys.modules.pop, spec.name, None)
        spec.loader.exec_module(module)
        return module

    def write_identity_digest(self, identity_module, path, identity):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.parent.chmod(0o700)
        path.write_bytes(identity_module.digest_line(identity))
        path.chmod(0o600)

    def make_official_status_fixture(self, provider):
        capture = Path(self.temporary.name) / f"{provider}-status-capture.json"
        executable = self.make_fake_executable(
            provider,
            """
            import json
            import os
            from pathlib import Path
            import sys
            open_fds = []
            for descriptor in range(3, 64):
                try:
                    os.fstat(descriptor)
                except OSError:
                    continue
                open_fds.append(descriptor)
            Path(os.environ["AI_TEST_STATUS_CAPTURE"]).write_text(json.dumps({
                "argv": sys.argv,
                "codex_home": os.environ.get("CODEX_HOME"),
                "claude_config_dir": os.environ.get("CLAUDE_CONFIG_DIR"),
                "open_fds": open_fds,
            }, sort_keys=True), encoding="utf-8")
            print(os.environ["AI_TEST_STATUS_PAYLOAD"])
            os.write(2, b"raw-provider-stderr TOKEN-fixture config/internal/path\\n")
            """,
        )
        return executable, capture

    def test_live_verifier(self):
        paths = self.require_t7_verifier_contract()
        identity_module = self.load_identity_module(paths["identity"])
        subject_id = "Subject-Case-A"
        identity = {
            "provider": "codex",
            "auth_kind": "consumer",
            "subject_id": subject_id,
        }
        digest_file = Path(self.temporary.name) / "identity/codex-default.sha256"
        self.write_identity_digest(identity_module, digest_file, identity)
        _provider, capture = self.make_official_status_fixture("codex")
        config_home = Path(self.temporary.name) / "selected-codex-home"
        config_home.mkdir()
        environment = {
            **self.environment,
            "AI_ACCOUNT_PROFILE": "codex-default",
            "AI_AUTH_KIND": "consumer",
            "AI_IDENTITY_DIGEST_FILE": str(digest_file),
            "AI_TEST_STATUS_CAPTURE": str(capture),
            "AI_TEST_STATUS_PAYLOAD": json.dumps({
                "logged_in": True,
                "auth_kind": "consumer",
                "subject_id": subject_id,
                "usage_status": "sufficient",
                "email": "private@example.invalid",
            }),
            "CODEX_HOME": str(config_home),
        }
        environment.pop("CLAUDE_CONFIG_DIR", None)
        result = subprocess.run(
            [str(paths["codex"])],
            env=environment,
            text=True,
            capture_output=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(
            {
                "provider", "account_profile", "login_status",
                "identity_status", "usage_status", "cost_limit_status",
            },
            set(payload),
            "verifier must return six redacted fields",
        )
        self.assertEqual(
            ("logged_in", "matched", "sufficient", "not_applicable"),
            (
                payload["login_status"], payload["identity_status"],
                payload["usage_status"], payload["cost_limit_status"],
            ),
        )
        status_capture = json.loads(capture.read_text(encoding="utf-8"))
        self.assertEqual([str(self.bin_dir / "codex"), "doctor", "--json"], status_capture["argv"])
        self.assertEqual(str(config_home), status_capture["codex_home"])
        self.assertIsNone(status_capture["claude_config_dir"])
        self.assertEqual([], status_capture["open_fds"])
        self.assertEqual("", result.stderr)

        insecure_digest = Path(self.temporary.name) / "insecure-identity/codex-default.sha256"
        self.write_identity_digest(identity_module, insecure_digest, identity)
        insecure_digest.parent.chmod(0o755)
        insecure = subprocess.run(
            [str(paths["codex"])],
            env={**environment, "AI_IDENTITY_DIGEST_FILE": str(insecure_digest)},
            text=True,
            capture_output=True,
        )
        self.assertEqual(0, insecure.returncode, insecure.stderr)
        self.assertEqual("unknown", json.loads(insecure.stdout)["identity_status"])

    def test_account_status_precedence(self):
        self.require_t7_verifier_contract()
        registry, _, _, profile2_root = self.write_strict_registry()
        (Path(self.temporary.name) / "homes/claude/profile2").mkdir(parents=True)
        verifier_count = Path(self.temporary.name) / "verifier-count"
        provider_called = Path(self.temporary.name) / "provider-called"
        verifier = self.make_fake_executable(
            "precedence-verifier",
            """
            import os
            from pathlib import Path
            counter = Path(os.environ["AI_TEST_VERIFIER_COUNT"])
            counter.write_text(counter.read_text() + "1" if counter.exists() else "1")
            print(os.environ["AI_TEST_VERIFIER_PAYLOAD"])
            """,
        )
        provider = self.make_fake_executable(
            "never-provider",
            """
            import os
            from pathlib import Path
            Path(os.environ["AI_TEST_PROVIDER_CALLED"]).write_text("called")
            """,
        )
        cases = (
            ({"login_status": "not_logged_in", "identity_status": "identity_drift", "usage_status": "usage_unknown"}, "not_logged_in"),
            ({"login_status": "logged_in", "identity_status": "identity_drift", "usage_status": "usage_unknown"}, "identity_drift"),
            ({"login_status": "logged_in", "identity_status": "unknown", "usage_status": "usage_unknown"}, "blocked_verifier"),
            ({"login_status": "logged_in", "identity_status": "matched", "usage_status": "usage_unknown"}, "usage_unknown"),
            ({"login_status": "logged_in", "identity_status": "matched", "usage_status": "blocked_usage"}, "blocked_usage"),
        )
        for statuses, expected in cases:
            with self.subTest(expected=expected):
                payload = {
                    "provider": "claude",
                    "account_profile": "claude-profile2",
                    "cost_limit_status": "not_applicable",
                    **statuses,
                }
                result = subprocess.run(
                    [
                        sys.executable, str(ACCOUNT_SELECTOR), "launch",
                        "--registry", str(registry),
                        "--provider", "claude",
                        "--role-profile", "general",
                        "--role-contract", "orchestrator-permission-profiles-v1",
                        "--verifier", str(verifier),
                        "--", str(provider),
                    ],
                    cwd=profile2_root / "project",
                    env={
                        **self.environment,
                        "AI_TEST_VERIFIER_COUNT": str(verifier_count),
                        "AI_TEST_VERIFIER_PAYLOAD": json.dumps(payload),
                        "AI_TEST_PROVIDER_CALLED": str(provider_called),
                    },
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(3, result.returncode, result.stderr)
                records = self.public_records(result.stderr)
                self.assertEqual(expected, records[-1]["status"])
                self.assertFalse(provider_called.exists())
        self.assertEqual("1" * len(cases), verifier_count.read_text(encoding="utf-8"))

    def test_identity_canonicalization(self):
        paths = self.require_t7_verifier_contract()
        identity_module = self.load_identity_module(paths["identity"])
        raw = {
            "provider": "  CoDeX\t",
            "auth_kind": " Consumer ",
            "subject_id": "  Case-SensitivE-e\u0301  ",
            "tenant_id": "ignored-for-consumer",
            "email": "excluded@example.invalid",
            "display_name": "Excluded Name",
            "token": "excluded-token",
            "usage": {"remaining": 99},
        }
        expected = (
            '{"auth_kind":"consumer","provider":"codex","schema_version":1,'
            '"subject_id":"Case-SensitivE-é"}'
        ).encode("utf-8")
        self.assertEqual(expected, identity_module.canonical_bytes(raw))
        self.assertEqual(
            hashlib.sha256(expected).hexdigest().encode("ascii") + b"\n",
            identity_module.digest_line(raw),
        )
        organization = {
            "provider": " CLAUDE ",
            "auth_kind": " ORGANIZATION ",
            "subject_id": "Opaque-ID",
            "tenant_id": "Tenant-Case",
        }
        self.assertEqual(
            b'{"auth_kind":"organization","provider":"claude","schema_version":1,'
            b'"subject_id":"Opaque-ID","tenant_id":"Tenant-Case"}',
            identity_module.canonical_bytes(organization),
        )
        for field, value in (
            ("subject_id", "   "),
            ("subject_id", "bad\0value"),
            ("subject_id", "bad\u0007value"),
            ("tenant_id", "\t"),
        ):
            with self.subTest(field=field, value=repr(value)):
                invalid = dict(organization)
                invalid[field] = value
                with self.assertRaises(ValueError):
                    identity_module.canonical_bytes(invalid)
        with self.assertRaises(ValueError):
            identity_module.canonical_bytes({
                "provider": "codex", "auth_kind": "consumer", "email": "only@example.invalid"
            })

    def test_identity_enrollment(self):
        paths = self.require_t7_verifier_contract()
        identity_module = self.load_identity_module(paths["identity"])
        registry, _, _, _ = self.write_strict_registry()
        identity_root = Path(self.temporary.name) / "enrolled-identities"
        subject_id = "Synthetic-Subject-A"
        environment = {
            **self.environment,
            "AI_SESSION_SYNTHETIC_TEST": "1",
            "AI_SESSION_IDENTITY_ROOT": str(identity_root),
            "AI_SESSION_SYNTHETIC_STATUS_JSON": json.dumps({
                "logged_in": True,
                "auth_kind": "consumer",
                "subject_id": subject_id,
            }),
        }
        command = [
            sys.executable, str(paths["enrollment"]),
            "--registry", str(registry),
            "--provider", "codex",
            "--account-profile", "codex-default",
        ]
        enrolled = subprocess.run(command, env=environment, text=True, capture_output=True)
        self.assertEqual(0, enrolled.returncode, enrolled.stderr)
        self.assertEqual(
            {
                "schema_version": 1,
                "event": "enrolled_identity",
                "provider": "codex",
                "account_profile": "codex-default",
                "status": "enrolled",
            },
            json.loads(enrolled.stdout),
        )
        digest_file = identity_root / "codex/codex-default.sha256"
        self.assertEqual(
            identity_module.digest_line({
                "provider": "codex",
                "auth_kind": "consumer",
                "subject_id": subject_id,
            }),
            digest_file.read_bytes(),
        )
        self.assertEqual(0o700, identity_root.stat().st_mode & 0o777)
        self.assertEqual(0o700, digest_file.parent.stat().st_mode & 0o777)
        self.assertEqual(0o600, digest_file.stat().st_mode & 0o777)
        self.assertFalse(digest_file.is_symlink())
        self.assertEqual(os.getuid(), digest_file.parent.stat().st_uid)

        old_digest = digest_file.read_bytes()
        failed = subprocess.run(
            command,
            env={
                **environment,
                "AI_SESSION_SYNTHETIC_STATUS_JSON": json.dumps({
                    "logged_in": True,
                    "auth_kind": "consumer",
                    "subject_id": "Replacement-Subject",
                }),
                "AI_SESSION_TEST_FAIL_BEFORE_REPLACE": "1",
            },
            text=True,
            capture_output=True,
        )
        self.assertEqual(3, failed.returncode)
        self.assertEqual(old_digest, digest_file.read_bytes())
        self.assertNotIn("Replacement-Subject", failed.stdout + failed.stderr)
        self.assertNotIn(old_digest.decode().strip(), failed.stdout + failed.stderr)

        symlink_root = Path(self.temporary.name) / "symlink-identities"
        outside = Path(self.temporary.name) / "identity-outside"
        symlink_root.mkdir(mode=0o700)
        outside.mkdir(mode=0o700)
        (symlink_root / "codex").symlink_to(outside, target_is_directory=True)
        blocked = subprocess.run(
            command,
            env={**environment, "AI_SESSION_IDENTITY_ROOT": str(symlink_root)},
            text=True,
            capture_output=True,
        )
        self.assertEqual(3, blocked.returncode)
        self.assertEqual([], list(outside.iterdir()))

    def test_verifier_redaction(self):
        paths = self.require_t7_verifier_contract()
        identity_module = self.load_identity_module(paths["identity"])
        subject_id = "ACCOUNT-ID-SECRET"
        digest_file = Path(self.temporary.name) / "identity/claude-profile2.sha256"
        self.write_identity_digest(identity_module, digest_file, {
            "provider": "claude",
            "auth_kind": "consumer",
            "subject_id": subject_id,
        })
        _provider, capture = self.make_official_status_fixture("claude")
        private_home = Path(self.temporary.name) / "private-config-home/internal"
        private_home.mkdir(parents=True)
        environment = {
            **self.environment,
            "AI_ACCOUNT_PROFILE": "claude-profile2",
            "AI_AUTH_KIND": "consumer",
            "AI_IDENTITY_DIGEST_FILE": str(digest_file),
            "AI_TEST_STATUS_CAPTURE": str(capture),
            "AI_TEST_STATUS_PAYLOAD": json.dumps({
                "logged_in": True,
                "auth_kind": "consumer",
                "subject_id": subject_id,
                "email": "private@example.invalid",
                "token": "TOKEN-fixture",
                "config_path": str(private_home / "credentials.json"),
            }),
            "CLAUDE_CONFIG_DIR": str(private_home),
        }
        environment.pop("CODEX_HOME", None)
        result = subprocess.run(
            [str(paths["claude"])], env=environment, text=True, capture_output=True
        )
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(
            {
                "provider", "account_profile", "login_status",
                "identity_status", "usage_status", "cost_limit_status",
            },
            set(payload),
            "verifier must return six redacted fields",
        )
        self.assertEqual("usage_unknown", payload["usage_status"])
        public = result.stdout + result.stderr
        for secret in (
            subject_id, "private@example.invalid", "TOKEN-fixture",
            str(private_home), identity_module.digest_line({
                "provider": "claude",
                "auth_kind": "consumer",
                "subject_id": subject_id,
            }).decode().strip(),
            "raw-provider-stderr",
        ):
            self.assertNotIn(secret, public)
        status_capture = json.loads(capture.read_text(encoding="utf-8"))
        self.assertEqual([str(self.bin_dir / "claude"), "auth", "status", "--json"], status_capture["argv"])
        self.assertEqual(str(private_home), status_capture["claude_config_dir"])
        self.assertIsNone(status_capture["codex_home"])

    T8_SCRUB_KEYS = (
        "CODEX_HOME",
        "CLAUDE_CONFIG_DIR",
        "CODEX_API_KEY",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_AUTH_TOKEN",
        "CLAUDE_CODE_OAUTH_TOKEN",
        "CLAUDE_CODE_USE_BEDROCK",
        "CLAUDE_CODE_USE_VERTEX",
        "CLAUDE_CODE_USE_FOUNDRY",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
        "GOOGLE_APPLICATION_CREDENTIALS",
        "CLOUD_ML_REGION",
        "ANTHROPIC_VERTEX_PROJECT_ID",
        "ANTHROPIC_FOUNDRY_RESOURCE",
        "ANTHROPIC_FOUNDRY_API_KEY",
        "AI_COST_LIMIT_USD",
    )

    def t8_parent_environment(self, **extra):
        environment = {
            **self.environment,
            **{key: f"synthetic-parent-{key}" for key in self.T8_SCRUB_KEYS},
            **extra,
        }
        return environment

    def run_t8_selector_launch(self, registry, provider, cwd, environment, suffix):
        verifier_capture = Path(self.temporary.name) / f"{suffix}-verifier.json"
        provider_capture = Path(self.temporary.name) / f"{suffix}-provider.json"
        verifier = self.make_fake_executable(
            f"{suffix}-verifier",
            f"""
            import json
            import os
            from pathlib import Path
            keys = {self.T8_SCRUB_KEYS!r}
            Path(os.environ["AI_TEST_VERIFIER_ENV"]).write_text(json.dumps({{
                key: os.environ[key] for key in keys if key in os.environ
            }}, sort_keys=True), encoding="utf-8")
            print(json.dumps({{
                "provider": os.environ["AI_PROVIDER"],
                "account_profile": os.environ["AI_ACCOUNT_PROFILE"],
                "login_status": "logged_in",
                "identity_status": "matched",
                "usage_status": "sufficient",
                "cost_limit_status": "not_applicable",
            }}, sort_keys=True))
            """,
        )
        provider_executable = self.make_fake_executable(
            f"{suffix}-provider",
            f"""
            import json
            import os
            from pathlib import Path
            keys = {self.T8_SCRUB_KEYS!r}
            Path(os.environ["AI_TEST_PROVIDER_ENV"]).write_text(json.dumps({{
                key: os.environ[key] for key in keys if key in os.environ
            }}, sort_keys=True), encoding="utf-8")
            """,
        )
        result = subprocess.run(
            [
                sys.executable,
                str(ACCOUNT_SELECTOR),
                "launch",
                "--registry",
                str(registry),
                "--provider",
                provider,
                "--role-profile",
                "general",
                "--role-contract",
                "orchestrator-permission-profiles-v1",
                "--verifier",
                str(verifier),
                "--",
                str(provider_executable),
            ],
            cwd=cwd,
            env={
                **environment,
                "AI_TEST_VERIFIER_ENV": str(verifier_capture),
                "AI_TEST_PROVIDER_ENV": str(provider_capture),
            },
            text=True,
            capture_output=True,
        )
        verifier_environment = (
            json.loads(verifier_capture.read_text(encoding="utf-8"))
            if verifier_capture.is_file()
            else None
        )
        provider_environment = (
            json.loads(provider_capture.read_text(encoding="utf-8"))
            if provider_capture.is_file()
            else None
        )
        return result, verifier_environment, provider_environment

    def test_child_environment(self):
        registry, _, profile1_root, _ = self.write_strict_registry()
        default_home = Path(self.temporary.name) / "synthetic-provider-default"
        default_home.mkdir()
        result, verifier_environment, provider_environment = self.run_t8_selector_launch(
            registry,
            "claude",
            profile1_root / "project",
            self.t8_parent_environment(CLAUDE_CONFIG_DIR=str(default_home)),
            "child-environment",
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(
            {},
            verifier_environment,
            "provider-default Claude must not export CLAUDE_CONFIG_DIR",
        )
        self.assertEqual({}, provider_environment)

    def test_exact_credential_scrub(self):
        registry, code_root, _, profile2_root = self.write_strict_registry()
        codex_home = Path(self.temporary.name) / "homes/codex"
        claude_home = Path(self.temporary.name) / "homes/claude/profile2"
        codex_home.mkdir(parents=True)
        claude_home.mkdir(parents=True)
        cases = (
            ("codex", code_root / "other", {"CODEX_HOME": str(codex_home)}),
            ("claude", profile2_root / "project", {"CLAUDE_CONFIG_DIR": str(claude_home)}),
        )
        for provider, cwd, expected in cases:
            with self.subTest(provider=provider):
                result, verifier_environment, provider_environment = self.run_t8_selector_launch(
                    registry,
                    provider,
                    cwd,
                    self.t8_parent_environment(),
                    f"exact-scrub-{provider}",
                )
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual(expected, verifier_environment)
                self.assertEqual(expected, provider_environment)
                self.assertEqual(
                    set(),
                    (set(verifier_environment) | set(provider_environment)) - set(expected),
                )

    def test_claude_default_env_unset(self):
        registry, _, profile1_root, _ = self.write_strict_registry()
        provider_default = Path(self.temporary.name) / "provider-default-home"
        provider_default.mkdir()
        result, verifier_environment, provider_environment = self.run_t8_selector_launch(
            registry,
            "claude",
            profile1_root / "project",
            self.t8_parent_environment(CLAUDE_CONFIG_DIR=str(provider_default)),
            "claude-default",
        )
        self.assertEqual(0, result.returncode, result.stderr)
        for captured in (verifier_environment, provider_environment):
            self.assertNotIn("CLAUDE_CONFIG_DIR", captured)
            self.assertNotIn(str(provider_default), captured.values())
            self.assertNotIn("CODEX_HOME", captured)

    def test_claude_explicit_env(self):
        registry, _, _, profile2_root = self.write_strict_registry()
        explicit_home = Path(self.temporary.name) / "homes/claude/profile2"
        explicit_home.mkdir(parents=True)
        result, verifier_environment, provider_environment = self.run_t8_selector_launch(
            registry,
            "claude",
            profile2_root / "project",
            self.t8_parent_environment(),
            "claude-explicit",
        )
        self.assertEqual(0, result.returncode, result.stderr)
        expected = {"CLAUDE_CONFIG_DIR": str(explicit_home)}
        self.assertEqual(expected, verifier_environment)
        self.assertEqual(expected, provider_environment)

    def test_verifier_provider_environments(self):
        self.reviewed_instructions()
        self.install_source_ai_session()
        registry, _, profile1_root, profile2_root = self.write_strict_registry()
        explicit_home = Path(self.temporary.name) / "homes/claude/profile2"
        explicit_home.mkdir(parents=True)
        provider_default_root = Path(self.temporary.name) / "provider-default-chain-root"
        (provider_default_root / ".claude").mkdir(parents=True)
        for profile, cwd, expected in (
            ("profile1", profile1_root / "project", {}),
            ("profile2", profile2_root / "project", {"CLAUDE_CONFIG_DIR": str(explicit_home)}),
        ):
            with self.subTest(profile=profile):
                subprocess.run(
                    ["git", "init", "-q", str(cwd)],
                    check=True,
                    text=True,
                    capture_output=True,
                )
                verifier_capture = Path(self.temporary.name) / f"{profile}-chain-verifier.json"
                provider_capture = Path(self.temporary.name) / f"{profile}-chain-provider.json"
                verifier = self.make_fake_executable(
                    f"{profile}-chain-verifier",
                    f"""
                    import json
                    import os
                    from pathlib import Path
                    keys = {self.T8_SCRUB_KEYS!r}
                    Path(os.environ["AI_TEST_VERIFIER_ENV"]).write_text(json.dumps({{
                        key: os.environ[key] for key in keys if key in os.environ
                    }}, sort_keys=True), encoding="utf-8")
                    print(json.dumps({{
                        "provider": "claude",
                        "account_profile": os.environ["AI_ACCOUNT_PROFILE"],
                        "login_status": "logged_in",
                        "identity_status": "matched",
                        "usage_status": "sufficient",
                        "cost_limit_status": "not_applicable",
                    }}, sort_keys=True))
                    """,
                )
                self.make_fake_executable(
                    "claude",
                    f"""
                    import json
                    import os
                    from pathlib import Path
                    keys = {self.T8_SCRUB_KEYS!r}
                    Path(os.environ["AI_TEST_PROVIDER_ENV"]).write_text(json.dumps({{
                        key: os.environ[key] for key in keys if key in os.environ
                    }}, sort_keys=True), encoding="utf-8")
                    """,
                )
                environment = self.t8_parent_environment(
                    HOME=str(provider_default_root),
                    AI_TEST_VERIFIER_ENV=str(verifier_capture),
                    AI_TEST_PROVIDER_ENV=str(provider_capture),
                )
                environment.pop("CLAUDE_CONFIG_DIR")
                result = self.run_entrypoint(
                    "ai-claude",
                    "--registry",
                    str(registry),
                    "--verifier",
                    str(verifier),
                    "--",
                    "fixture prompt",
                    cwd=cwd,
                    environment=environment,
                )
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual(
                    expected,
                    json.loads(verifier_capture.read_text(encoding="utf-8")),
                )
                self.assertEqual(
                    expected,
                    json.loads(provider_capture.read_text(encoding="utf-8")),
                )

    def test_claude_config_home_modes(self):
        with ACCOUNT_REGISTRY.open("rb") as stream:
            source_accounts = {
                account["alias"]: account for account in tomllib.load(stream)["accounts"]
            }
        self.assertEqual("provider_default", source_accounts["claude-profile1"]["config_home_mode"])
        self.assertNotIn("config_home", source_accounts["claude-profile1"])
        self.assertEqual("explicit", source_accounts["claude-profile2"]["config_home_mode"])
        self.assertEqual(
            "~/.local/share/ai-account-profiles/claude/profile2",
            source_accounts["claude-profile2"]["config_home"],
        )

        registry, _, profile1_root, profile2_root = self.write_strict_registry()
        with registry.open("rb") as stream:
            rendered_accounts = {
                account["alias"]: account for account in tomllib.load(stream)["accounts"]
            }
        self.assertNotIn("config_home", rendered_accounts["claude-profile1"])
        self.assertEqual(
            str(Path(self.temporary.name) / "homes/claude/profile2"),
            rendered_accounts["claude-profile2"]["config_home"],
        )

        repository = self.make_git_repository()
        self.make_fake_executable("ai-session", "import json, sys\nprint(json.dumps(sys.argv[1:]))")
        launcher_environment = self.t8_parent_environment()
        launcher_environment.pop("CLAUDE_CONFIG_DIR")
        launcher = self.run_entrypoint(
            "ai-claude",
            "fixture prompt",
            cwd=repository,
            environment=launcher_environment,
        )
        self.assertEqual(0, launcher.returncode, launcher.stderr)
        self.assertNotIn("CLAUDE_CONFIG_DIR", "\0".join(json.loads(launcher.stdout)))

        original = registry.read_text(encoding="utf-8")
        invalid_mode = Path(self.temporary.name) / "invalid-mode.toml"
        invalid_mode.write_text(
            original.replace('config_home_mode = "provider_default"', 'config_home_mode = "invalid"', 1),
            encoding="utf-8",
        )
        invalid = self.select_account(invalid_mode, "claude", profile1_root / "project")
        self.assertEqual(2, invalid.returncode)
        self.assertIn("blocked_contract", invalid.stderr)

        missing_home = Path(self.temporary.name) / "missing-home.toml"
        missing_home.write_text(
            original.replace(
                f'config_home = "{Path(self.temporary.name) / "homes/claude/profile2"}"\n',
                "",
                1,
            ),
            encoding="utf-8",
        )
        missing = self.select_account(missing_home, "claude", profile2_root / "project")
        self.assertEqual(2, missing.returncode)
        self.assertIn("blocked_contract", missing.stderr)

        symlink_target = Path(self.temporary.name) / "real-claude-home"
        symlink_target.mkdir()
        symlink_home = Path(self.temporary.name) / "symlink-claude-home"
        symlink_home.symlink_to(symlink_target, target_is_directory=True)
        symlink_registry = Path(self.temporary.name) / "symlink-home.toml"
        symlink_registry.write_text(
            original.replace(
                str(Path(self.temporary.name) / "homes/claude/profile2"),
                str(symlink_home),
                1,
            ),
            encoding="utf-8",
        )
        symlinked = self.select_account(
            symlink_registry,
            "claude",
            profile2_root / "project",
        )
        self.assertEqual(2, symlinked.returncode)
        self.assertIn("blocked_contract", symlinked.stderr)

    def run_permission_boundary_launch(self, registry, cwd):
        self.reviewed_instructions()
        self.install_source_ai_session()
        explicit_home = Path(self.temporary.name) / "homes/claude/profile2"
        explicit_home.mkdir(parents=True, exist_ok=True)
        verifier = self.make_fake_executable(
            "permission-verifier",
            """
            import json
            print(json.dumps({
                "provider": "claude",
                "account_profile": "claude-profile2",
                "login_status": "logged_in",
                "identity_status": "matched",
                "usage_status": "sufficient",
                "cost_limit_status": "not_applicable",
            }, sort_keys=True))
            """,
        )
        capture = Path(self.temporary.name) / "permission-boundary.json"
        capture.unlink(missing_ok=True)
        self.make_fake_executable(
            "claude",
            """
            import json
            import os
            from pathlib import Path
            import sys
            Path(os.environ["AI_TEST_PERMISSION_CAPTURE"]).write_text(json.dumps({
                "argv": sys.argv[1:],
                "common_dir_relation": os.environ.get("AI_SESSION_GIT_COMMON_DIR_RELATION"),
                "write_allow_set": json.loads(os.environ.get("AI_SESSION_WRITE_ALLOW_SET", "[]")),
            }, sort_keys=True), encoding="utf-8")
            """,
        )
        result = self.run_entrypoint(
            "ai-claude",
            "--registry", str(registry),
            "--verifier", str(verifier),
            "--",
            "fixture prompt",
            cwd=cwd,
            environment={
                **self.environment,
                "AI_TEST_PERMISSION_CAPTURE": str(capture),
                "PWD": str(cwd.resolve()),
            },
        )
        captured = (
            json.loads(capture.read_text(encoding="utf-8"))
            if capture.is_file()
            else {"argv": [], "common_dir_relation": None, "write_allow_set": []}
        )
        return result, captured

    def make_external_common_dir_worktree(self):
        registry, _, profile1_root, profile2_root = self.write_strict_registry()
        main_worktree = profile1_root / "main"
        subprocess.run(
            ["git", "init", "-q", str(main_worktree)],
            check=True,
            text=True,
            capture_output=True,
        )
        (main_worktree / "tracked.txt").write_text("fixture\n", encoding="utf-8")
        subprocess.run(
            [
                "git", "-C", str(main_worktree),
                "-c", "user.name=Fixture",
                "-c", "user.email=fixture@example.invalid",
                "add", "tracked.txt",
            ],
            check=True,
            text=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "git", "-C", str(main_worktree),
                "-c", "user.name=Fixture",
                "-c", "user.email=fixture@example.invalid",
                "commit", "-qm", "fixture",
            ],
            check=True,
            text=True,
            capture_output=True,
        )
        linked_worktree = profile2_root / "linked"
        subprocess.run(
            [
                "git", "-C", str(main_worktree), "worktree", "add", "-q",
                "-b", "fixture-linked", str(linked_worktree),
            ],
            check=True,
            text=True,
            capture_output=True,
        )
        self.addCleanup(
            subprocess.run,
            ["git", "-C", str(main_worktree), "worktree", "remove", "--force", str(linked_worktree)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        common_dir = Path(
            subprocess.run(
                [
                    "git", "-C", str(linked_worktree), "rev-parse",
                    "--path-format=absolute", "--git-common-dir",
                ],
                check=True,
                text=True,
                capture_output=True,
            ).stdout.strip()
        ).resolve()
        return registry, profile1_root, profile2_root, linked_worktree.resolve(), common_dir

    def make_cross_profile_move_fixture(self):
        registry, _, profile1_root, profile2_root = self.write_strict_registry()
        main_worktree = profile1_root / "move-main"
        subprocess.run(
            ["git", "init", "-q", str(main_worktree)],
            check=True,
            text=True,
            capture_output=True,
        )
        (main_worktree / "tracked.txt").write_text("base\n", encoding="utf-8")
        subprocess.run(
            [
                "git", "-C", str(main_worktree),
                "-c", "user.name=Fixture",
                "-c", "user.email=fixture@example.invalid",
                "add", "tracked.txt",
            ],
            check=True,
            text=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "git", "-C", str(main_worktree),
                "-c", "user.name=Fixture",
                "-c", "user.email=fixture@example.invalid",
                "commit", "-qm", "fixture",
            ],
            check=True,
            text=True,
            capture_output=True,
        )
        source = profile1_root / "move-source"
        subprocess.run(
            [
                "git", "-C", str(main_worktree), "worktree", "add", "-q",
                "-b", "fixture-move", str(source),
            ],
            check=True,
            text=True,
            capture_output=True,
        )
        destination = profile2_root / "move-destination"
        (source / "tracked.txt").write_text("dirty\n", encoding="utf-8")
        (source / "untracked.txt").write_text("untracked\n", encoding="utf-8")
        state = source / ".Codex/quality-state/fixture/state.json"
        state.parent.mkdir(parents=True)
        state.write_text('{"stage":"IMPLEMENTING"}\n', encoding="utf-8")
        handoff = state.with_name("move-handoff.json")
        handoff.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "worktree": str(source.resolve()),
                    "account_profile": "claude-profile1",
                    "binding_generation": 7,
                    "quality_goal_state": ".Codex/quality-state/fixture/state.json",
                    "required_git_paths": ["tracked.txt", "untracked.txt"],
                    "resume_unit": "verified_git_state_and_in_repository_handoff",
                    "forbidden_state_operations": [],
                },
                sort_keys=True,
            ) + "\n",
            encoding="utf-8",
        )
        shutdown = Path(self.temporary.name) / "shutdown-proof.json"
        shutdown.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "worktree": str(source.resolve()),
                    "stopped": ["launcher", "provider", "watchers", "workers", "writers"],
                    "active_processes": 0,
                },
                sort_keys=True,
            ) + "\n",
            encoding="utf-8",
        )
        registry_text = registry.read_text(encoding="utf-8")
        registry.write_text(
            registry_text.replace(
                "task_bindings = []",
                'task_bindings = [{ id = "fixture-move", provider = "claude", '
                'account_profile = "claude-profile1", '
                f'workspace_root = "{source.resolve()}", binding_generation = 7 }}]',
                1,
            ),
            encoding="utf-8",
        )
        plan_output = Path(self.temporary.name) / "move-result.json"
        return {
            "registry": registry,
            "profile1_root": profile1_root.resolve(),
            "profile2_root": profile2_root.resolve(),
            "main": main_worktree.resolve(),
            "source": source.resolve(),
            "destination": destination.resolve(),
            "shutdown": shutdown,
            "handoff": handoff,
            "plan_output": plan_output,
        }

    def run_cross_profile_move(self, fixture, *extra, shutdown=True):
        command = [
            sys.executable, str(ACCOUNT_SELECTOR), "move-rebind",
            "--registry", str(fixture["registry"]),
            "--provider", "claude",
            "--role-contract", "orchestrator-permission-profiles-v1",
            "--binding-kind", "task",
            "--binding-id", "fixture-move",
            "--old-worktree", str(fixture["source"]),
            "--new-worktree", str(fixture["destination"]),
            "--account-profile", "claude-profile2",
            "--handoff", str(fixture["handoff"]),
            "--common-dir-policy", "allow-exact",
            "--result", str(fixture["plan_output"]),
        ]
        if shutdown:
            command.extend(("--shutdown-proof", str(fixture["shutdown"])))
        command.extend(extra)
        return subprocess.run(
            command,
            cwd=self.temporary.name,
            env={**self.environment, "PWD": self.temporary.name},
            text=True,
            capture_output=True,
        )

    def test_cross_profile_move_shutdown(self):
        help_result = subprocess.run(
            [sys.executable, str(ACCOUNT_SELECTOR), "--help"],
            env=self.environment,
            text=True,
            capture_output=True,
        )
        self.assertIn(
            "move-rebind",
            help_result.stdout,
            "shutdown proof is required before rebind",
        )
        self.assertIn(
            'sys.argv[1] == "move-rebind"',
            ROLE_DISPATCHER.read_text(encoding="utf-8"),
        )
        fixture = self.make_cross_profile_move_fixture()
        old_registry = fixture["registry"].read_bytes()

        result = self.run_cross_profile_move(fixture, shutdown=False)

        self.assertEqual(4, result.returncode, result.stderr)
        self.assertIn("blocked_binding", result.stderr)
        self.assertEqual(old_registry, fixture["registry"].read_bytes())
        self.assertTrue(fixture["source"].is_dir())
        self.assertFalse(fixture["destination"].exists())

    def test_git_worktree_move_and_verify(self):
        fixture = self.make_cross_profile_move_fixture()

        result = self.run_cross_profile_move(fixture)

        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(
            [
                "git worktree list --porcelain",
                "git rev-parse --show-toplevel",
                "git rev-parse --path-format=absolute --git-common-dir",
                "git status --short",
            ],
            list(payload["git_verification"]),
        )
        self.assertTrue(all(payload["git_verification"].values()))
        self.assertFalse(fixture["source"].exists())
        self.assertEqual("dirty\n", (fixture["destination"] / "tracked.txt").read_text())
        self.assertEqual("untracked\n", (fixture["destination"] / "untracked.txt").read_text())
        self.assertIn(" M tracked.txt", payload["git_status_short"])
        self.assertIn("?? untracked.txt", payload["git_status_short"])
        self.assertFalse(Path(payload["git_common_dir"]).is_relative_to(fixture["profile2_root"]))

    def test_stale_binding_block(self):
        fixture = self.make_cross_profile_move_fixture()
        old_registry = fixture["registry"].read_bytes()
        fixture["registry"].write_text(
            old_registry.decode("utf-8").replace(
                'account_profile = "claude-profile1"',
                'account_profile = "claude-profile2"',
                1,
            ),
            encoding="utf-8",
        )
        inconsistent_registry = fixture["registry"].read_bytes()

        result = self.run_cross_profile_move(fixture)

        self.assertEqual(4, result.returncode, result.stderr)
        self.assertIn("blocked_binding", result.stderr)
        self.assertEqual(inconsistent_registry, fixture["registry"].read_bytes())
        self.assertTrue(fixture["source"].is_dir())
        self.assertFalse(fixture["plan_output"].exists())

    def test_binding_generation_rebind(self):
        fixture = self.make_cross_profile_move_fixture()

        result = self.run_cross_profile_move(fixture)

        self.assertEqual(0, result.returncode, result.stderr)
        with fixture["registry"].open("rb") as stream:
            registry = tomllib.load(stream)
        binding = registry["task_bindings"][0]
        self.assertEqual(str(fixture["destination"]), binding["workspace_root"])
        self.assertEqual("claude-profile2", binding["account_profile"])
        self.assertEqual(8, binding["binding_generation"])
        self.assertFalse(list(fixture["registry"].parent.glob(".accounts.toml.*")))

    def test_move_handoff(self):
        fixture = self.make_cross_profile_move_fixture()

        result = self.run_cross_profile_move(fixture)

        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(fixture["plan_output"].read_text(encoding="utf-8"))
        expected_new_path = str(fixture["destination"])
        self.assertEqual(
            {
                "write_root": expected_new_path,
                "sandbox_cwd": expected_new_path,
                "workmux_cwd": expected_new_path,
                "tmux_cwd": expected_new_path,
                "watcher_target": expected_new_path,
            },
            payload["recomputed_targets"],
        )
        self.assertTrue(payload["new_process_only"])
        self.assertEqual("verified_git_state_and_in_repository_handoff", payload["resume_unit"])
        self.assertEqual([], payload["state_operations"])
        serialized = json.dumps(payload, sort_keys=True)
        self.assertNotIn(str(fixture["source"]), serialized)
        for forbidden in ("transcript", "credential", "plugin", "account_home", "hot_swap"):
            self.assertNotIn(forbidden, payload["state_operations"])

    def test_separate_clone_alternative(self):
        fixture = self.make_cross_profile_move_fixture()
        old_registry = fixture["registry"].read_bytes()

        result = self.run_cross_profile_move(
            fixture,
            "--common-dir-policy", "separate-clone",
        )

        self.assertEqual(4, result.returncode, result.stderr)
        self.assertIn("destination-root separate clone and handoff", result.stderr)
        self.assertEqual(old_registry, fixture["registry"].read_bytes())
        self.assertTrue(fixture["source"].is_dir())

        linked_source = fixture["source"]
        fixture["source"] = fixture["main"]
        main_result = self.run_cross_profile_move(fixture)
        self.assertEqual(4, main_result.returncode, main_result.stderr)
        self.assertIn("main worktree", main_result.stderr)

        fixture["source"] = linked_source
        head = subprocess.run(
            ["git", "-C", str(linked_source), "rev-parse", "HEAD"],
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()
        subprocess.run(
            [
                "git", "-C", str(linked_source), "update-index", "--add",
                "--cacheinfo", f"160000,{head},vendor/submodule",
            ],
            check=True,
            text=True,
            capture_output=True,
        )
        submodule_result = self.run_cross_profile_move(fixture)
        self.assertEqual(4, submodule_result.returncode, submodule_result.stderr)
        self.assertIn("submodule-containing linked worktree", submodule_result.stderr)
        self.assertEqual(old_registry, fixture["registry"].read_bytes())

    def test_stale_pwd_rejected(self):
        registry, _, _, profile2_root = self.write_strict_registry()
        cwd = (profile2_root / "project").resolve()
        subprocess.run(
            ["git", "init", "-q", str(cwd)],
            check=True,
            text=True,
            capture_output=True,
        )
        self.install_source_ai_session()
        verifier_called = Path(self.temporary.name) / "stale-verifier-called"
        provider_called = Path(self.temporary.name) / "stale-provider-called"
        verifier = self.make_fake_executable(
            "stale-verifier",
            """
            from pathlib import Path
            import os
            Path(os.environ["AI_TEST_VERIFIER_CALLED"]).write_text("called")
            """,
        )
        self.make_fake_executable(
            "claude",
            """
            from pathlib import Path
            import os
            Path(os.environ["AI_TEST_PROVIDER_CALLED"]).write_text("called")
            """,
        )

        result = self.run_entrypoint(
            "ai-claude",
            "--registry", str(registry),
            "--verifier", str(verifier),
            "--",
            "fixture prompt",
            cwd=cwd,
            environment={
                **self.environment,
                "PWD": str(fixture_old := profile2_root / "old-location"),
                "AI_TEST_PRESERVE_STALE_PWD": "1",
                "AI_TEST_VERIFIER_CALLED": str(verifier_called),
                "AI_TEST_PROVIDER_CALLED": str(provider_called),
            },
        )

        self.assertEqual(str(profile2_root / "old-location"), str(fixture_old))
        self.assertEqual(4, result.returncode, result.stderr)
        failure = self.public_records(result.stderr)[0]
        self.assertEqual("blocked_binding", failure["status"])
        self.assertEqual(4, failure["exit_code"])
        self.assertFalse(verifier_called.exists())
        self.assertFalse(provider_called.exists())

    def test_account_root_permission_separation(self):
        registry, _, _, profile2_root = self.write_strict_registry()
        worktree = (profile2_root / "project").resolve()
        subprocess.run(
            ["git", "init", "-q", str(worktree)],
            check=True,
            text=True,
            capture_output=True,
        )
        common_dir = (worktree / ".git").resolve()

        result, capture = self.run_permission_boundary_launch(registry, worktree)

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(
            [str(worktree), str(common_dir)],
            capture["write_allow_set"],
            "account root must not be a write grant",
        )
        self.assertNotIn(str(profile2_root.resolve()), capture["write_allow_set"])

    def test_exact_git_common_dir_permission(self):
        registry, profile1_root, profile2_root, worktree, common_dir = (
            self.make_external_common_dir_worktree()
        )

        result, capture = self.run_permission_boundary_launch(registry, worktree)

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual([str(worktree), str(common_dir)], capture["write_allow_set"])
        self.assertEqual("external", capture["common_dir_relation"])
        self.assertEqual(1, capture["argv"].count("--add-dir"))
        self.assertEqual(
            str(common_dir),
            capture["argv"][capture["argv"].index("--add-dir") + 1],
        )
        self.assertNotEqual(profile1_root.resolve(), common_dir)
        self.assertFalse(common_dir.is_relative_to(profile2_root.resolve()))

    def test_no_opposite_root_grant(self):
        registry, profile1_root, profile2_root, worktree, common_dir = (
            self.make_external_common_dir_worktree()
        )

        result, capture = self.run_permission_boundary_launch(registry, worktree)

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual([str(worktree), str(common_dir)], capture["write_allow_set"])
        for account_root in (profile1_root.resolve(), profile2_root.resolve()):
            self.assertNotIn(str(account_root), capture["write_allow_set"])
        for granted_path in capture["write_allow_set"]:
            self.assertFalse(any(character in granted_path for character in "*?[]{}"))
        dispatcher_source = ROLE_DISPATCHER.read_text(encoding="utf-8")
        self.assertIn('"--write-need",', dispatcher_source)
        self.assertNotIn("--git-common-dir", dispatcher_source)
        self.assertNotIn("rev-parse", dispatcher_source)

        broad_worktree = (profile2_root / "project").resolve()
        subprocess.run(
            [
                "git", "init", "-q", "--separate-git-dir",
                str(profile1_root.resolve()), str(broad_worktree),
            ],
            check=True,
            text=True,
            capture_output=True,
        )
        blocked, blocked_capture = self.run_permission_boundary_launch(
            registry, broad_worktree
        )
        self.assertEqual(4, blocked.returncode, blocked.stderr)
        self.assertEqual(
            "blocked_permission", self.public_records(blocked.stderr)[0]["status"]
        )
        self.assertEqual([], blocked_capture["write_allow_set"])
        self.assertIn(
            "use a destination-root separate clone and handoff",
            ACCOUNT_SELECTOR.read_text(encoding="utf-8"),
        )

    def run_legacy_migration_gate(
        self,
        registry,
        provider,
        legacy_alias,
        operation,
        proof,
        *,
        target_account=None,
    ):
        proof_path = Path(self.temporary.name) / f"legacy-proof-{len(list(Path(self.temporary.name).glob('legacy-proof-*')))}.json"
        proof_path.write_text(json.dumps(proof, sort_keys=True), encoding="utf-8")
        command = [
            sys.executable,
            str(ACCOUNT_SELECTOR),
            "legacy-migration-gate",
            "--registry",
            str(registry),
            "--provider",
            provider,
            "--legacy-alias",
            legacy_alias,
            "--operation",
            operation,
            "--proof",
            str(proof_path),
        ]
        if target_account is not None:
            command.extend(("--target-account", target_account))
        return subprocess.run(
            command,
            cwd=ROOT,
            env=self.environment,
            text=True,
            capture_output=True,
        )

    def test_legacy_alias_home_protection(self):
        registry_bytes = ACCOUNT_REGISTRY.read_bytes()
        with ACCOUNT_REGISTRY.open("rb") as stream:
            registry = tomllib.load(stream)
        active_aliases = {account["alias"] for account in registry["accounts"]}
        mapped_aliases = {
            mapping["account_profile"]
            for mapping in registry["workspace_directory_mappings"]
        }

        self.assertEqual(
            LEGACY_CODEX_RECORD,
            registry["legacy_records"]["codex-dotfiles"],
        )
        self.assertEqual(
            LEGACY_CLAUDE_RECORD,
            registry["legacy_records"]["claude-dotfiles"],
        )
        self.assertFalse(
            {"codex-dotfiles", "claude-dotfiles"} & active_aliases,
            "legacy aliases must be non-selectable",
        )
        self.assertFalse({"codex-dotfiles", "claude-dotfiles"} & mapped_aliases)
        self.assertNotIn("defaults", registry)
        self.assertNotIn("scope_bindings", registry)
        self.assertEqual(registry_bytes, ACCOUNT_REGISTRY.read_bytes())

    def test_codex_default_existing_home(self):
        with ACCOUNT_REGISTRY.open("rb") as stream:
            registry = tomllib.load(stream)
        accounts = {account["alias"]: account for account in registry["accounts"]}
        codex_accounts = {
            alias: account
            for alias, account in accounts.items()
            if account["provider"] == "codex"
        }

        self.assertEqual({"codex-default"}, set(codex_accounts))
        self.assertEqual("~/.codex", codex_accounts["codex-default"]["config_home"])
        synthetic_registry, code_root, _, _ = self.write_strict_registry()
        result = self.select_account(synthetic_registry, "codex", code_root / "other")
        self.assertEqual(0, result.returncode, result.stderr)
        binding = json.loads(result.stdout)
        self.assertEqual("codex-default", binding["account_profile"])
        self.assertNotIn("config_home", binding)

    def test_legacy_records_non_selectable(self):
        source = ACCOUNT_REGISTRY.read_text(encoding="utf-8")
        cases = (
            (
                "codex",
                source.replace(
                    'alias = "codex-default"', 'alias = "codex-dotfiles"', 1
                ).replace(
                    'account_profile = "codex-default"',
                    'account_profile = "codex-dotfiles"',
                    1,
                ),
            ),
            (
                "claude",
                source.replace(
                    'alias = "claude-profile1"', 'alias = "claude-dotfiles"', 1
                ).replace(
                    'root = "~/code/profile1"', 'root = "~/code"', 1
                ).replace(
                    'account_profile = "claude-profile1"',
                    'account_profile = "claude-dotfiles"',
                    1,
                ),
            ),
        )
        for provider, mutated_source in cases:
            with self.subTest(provider=provider):
                registry = Path(self.temporary.name) / f"{provider}-legacy-active.toml"
                registry.write_text(mutated_source, encoding="utf-8")
                result = self.select_account(registry, provider, ROOT)
                if result.returncode == 0:
                    self.fail("legacy aliases must be non-selectable")
                self.assertEqual(2, result.returncode)
                self.assertEqual("", result.stdout)
                self.assertIn("blocked_contract", result.stderr)

    def test_old_alias_binding_blocked(self):
        registry, code_root, profile1_root, _ = self.write_strict_registry()
        verifier_called = Path(self.temporary.name) / "legacy-verifier-called"
        verifier = self.make_fake_executable(
            "legacy-verifier",
            """
            import os
            from pathlib import Path
            Path(os.environ["AI_TEST_LEGACY_VERIFIER_CALLED"]).write_text("called")
            raise SystemExit(99)
            """,
        )
        cases = (
            ("codex", "codex-dotfiles", code_root / "other"),
            ("claude", "claude-dotfiles", profile1_root / "project"),
        )
        for provider, legacy_alias, cwd in cases:
            with self.subTest(provider=provider, source="explicit"):
                result = subprocess.run(
                    [
                        sys.executable,
                        str(ACCOUNT_SELECTOR),
                        "launch",
                        "--registry",
                        str(registry),
                        "--provider",
                        provider,
                        "--role-profile",
                        "general",
                        "--role-contract",
                        "orchestrator-permission-profiles-v1",
                        "--account-profile",
                        legacy_alias,
                        "--verifier",
                        str(verifier),
                        "--",
                        "/usr/bin/false",
                    ],
                    cwd=cwd,
                    env={
                        **self.environment,
                        "AI_TEST_LEGACY_VERIFIER_CALLED": str(verifier_called),
                    },
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(4, result.returncode)
                self.assertIn("blocked_binding", result.stderr)
                self.assertFalse(verifier_called.exists())

            with self.subTest(provider=provider, source="stored"):
                stored_registry = Path(self.temporary.name) / f"{provider}-old-binding.toml"
                workspace_root = str(cwd.resolve())
                stored_source = registry.read_text(encoding="utf-8").replace(
                    "task_bindings = []",
                    "task_bindings = ["
                    f'{{ id = "old-binding", provider = "{provider}", '
                    f'account_profile = "{legacy_alias}", workspace_root = "{workspace_root}", '
                    "binding_generation = 7 }]",
                    1,
                )
                stored_registry.write_text(stored_source, encoding="utf-8")
                result = self.select_account(
                    stored_registry,
                    provider,
                    cwd,
                    "--task-id",
                    "old-binding",
                )
                self.assertEqual(4, result.returncode)
                self.assertEqual("", result.stdout)
                self.assertIn("blocked_binding", result.stderr)
                self.assertFalse(verifier_called.exists())

    def test_migration_generation_gate(self):
        registry_before = ACCOUNT_REGISTRY.read_bytes()
        proof = {
            "schema_version": 1,
            "legacy_alias": "claude-dotfiles",
            "operation": "rebind",
            "implementation_verified": True,
            "separate_generation": True,
            "current_binding_generation": 11,
            "migration_generation": 12,
            "shutdown": {
                "active_processes": 0,
                "stopped": ["launcher", "provider", "watchers", "workers", "writers"],
            },
            "handoff": {"present": True, "new_process_only": True},
            "official_admission": {
                "synthetic": True,
                "login_status": "logged_in",
                "identity_status": "matched",
            },
            "binding_switch": {
                "atomic": True,
                "account_profile": "claude-profile2",
                "binding_generation": 12,
            },
            "state_operations": [],
        }
        invalid_proofs = (
            {**proof, "implementation_verified": False},
            {**proof, "migration_generation": 11},
            {
                **proof,
                "shutdown": {**proof["shutdown"], "active_processes": 1},
            },
            {
                **proof,
                "shutdown": {**proof["shutdown"], "active_processes": False},
            },
            {
                **proof,
                "shutdown": {**proof["shutdown"], "stopped": None},
            },
            {
                **proof,
                "official_admission": {
                    **proof["official_admission"],
                    "identity_status": "unknown",
                },
            },
            {
                **proof,
                "binding_switch": {**proof["binding_switch"], "atomic": False},
            },
        )
        for invalid_proof in invalid_proofs:
            result = self.run_legacy_migration_gate(
                ACCOUNT_REGISTRY,
                "claude",
                "claude-dotfiles",
                "rebind",
                invalid_proof,
                target_account="claude-profile2",
            )
            self.assertEqual(4, result.returncode)
            self.assertIn("blocked_binding", result.stderr)

        allowed = self.run_legacy_migration_gate(
            ACCOUNT_REGISTRY,
            "claude",
            "claude-dotfiles",
            "rebind",
            proof,
            target_account="claude-profile2",
        )
        self.assertEqual(0, allowed.returncode, allowed.stderr)
        decision = json.loads(allowed.stdout)
        self.assertTrue(decision["gate_passed"])
        self.assertEqual(12, decision["migration_generation"])
        self.assertFalse(decision["mutation_performed"])
        self.assertEqual([], decision["state_operations"])
        self.assertEqual(registry_before, ACCOUNT_REGISTRY.read_bytes())

    def test_legacy_zero_reference_removal(self):
        registry_before = ACCOUNT_REGISTRY.read_bytes()
        for provider, legacy_alias in (
            ("codex", "codex-dotfiles"),
            ("claude", "claude-dotfiles"),
        ):
            proof = {
                "schema_version": 1,
                "legacy_alias": legacy_alias,
                "operation": "remove",
                "implementation_verified": True,
                "separate_generation": True,
                "current_binding_generation": 12,
                "migration_generation": 13,
                "shutdown": {
                    "active_processes": 0,
                    "stopped": ["launcher", "provider", "watchers", "workers", "writers"],
                },
                "handoff": {"present": True, "new_process_only": True},
                "reference_counts": {"processes": 0, "bindings": 0},
                "state_operations": [],
            }
            for reference_kind, invalid_count in (
                ("processes", 1),
                ("bindings", 1),
                ("processes", False),
                ("bindings", False),
            ):
                invalid_proof = {
                    **proof,
                    "reference_counts": {
                        **proof["reference_counts"],
                        reference_kind: invalid_count,
                    },
                }
                blocked = self.run_legacy_migration_gate(
                    ACCOUNT_REGISTRY,
                    provider,
                    legacy_alias,
                    "remove",
                    invalid_proof,
                )
                self.assertEqual(4, blocked.returncode)
                self.assertIn("blocked_binding", blocked.stderr)

            allowed = self.run_legacy_migration_gate(
                ACCOUNT_REGISTRY,
                provider,
                legacy_alias,
                "remove",
                proof,
            )
            self.assertEqual(0, allowed.returncode, allowed.stderr)
            decision = json.loads(allowed.stdout)
            self.assertTrue(decision["gate_passed"])
            self.assertTrue(decision["zero_references_verified"])
            self.assertFalse(decision["mutation_performed"])
            self.assertEqual([], decision["state_operations"])
            self.assertEqual(registry_before, ACCOUNT_REGISTRY.read_bytes())
            with ACCOUNT_REGISTRY.open("rb") as stream:
                self.assertIn(legacy_alias, tomllib.load(stream)["legacy_records"])

    def test_failure_status(self):
        self.require_t7_verifier_contract()
        registry, code_root, _, _ = self.write_strict_registry()
        (Path(self.temporary.name) / "homes/codex").mkdir(parents=True)
        verifier_count = Path(self.temporary.name) / "failure-verifier-count"
        provider_count = Path(self.temporary.name) / "failure-provider-count"
        verifier = self.make_fake_executable(
            "failure-verifier",
            """
            import os
            from pathlib import Path
            counter = Path(os.environ["AI_TEST_VERIFIER_COUNT"])
            counter.write_text(counter.read_text() + "1" if counter.exists() else "1")
            print(os.environ["AI_TEST_VERIFIER_PAYLOAD"])
            """,
        )
        provider = self.make_fake_executable(
            "model-rejected-provider",
            """
            import os
            from pathlib import Path
            counter = Path(os.environ["AI_TEST_PROVIDER_COUNT"])
            counter.write_text(counter.read_text() + "1" if counter.exists() else "1")
            raise SystemExit(int(os.environ.get("AI_TEST_PROVIDER_EXIT", "0")))
            """,
        )
        base_payload = {
            "provider": "codex",
            "account_profile": "codex-default",
            "login_status": "logged_in",
            "identity_status": "matched",
            "usage_status": "sufficient",
            "cost_limit_status": "not_applicable",
        }
        base_command = [
            sys.executable, str(ACCOUNT_SELECTOR), "launch",
            "--registry", str(registry),
            "--provider", "codex",
            "--role-profile", "general",
            "--role-contract", "orchestrator-permission-profiles-v1",
            "--verifier", str(verifier),
            "--", str(provider),
        ]
        common_environment = {
            **self.environment,
            "AI_TEST_VERIFIER_COUNT": str(verifier_count),
            "AI_TEST_PROVIDER_COUNT": str(provider_count),
        }
        rejected = subprocess.run(
            base_command,
            cwd=code_root / "other",
            env={
                **common_environment,
                "AI_TEST_VERIFIER_PAYLOAD": json.dumps(base_payload),
                "AI_TEST_PROVIDER_EXIT": "47",
            },
            text=True,
            capture_output=True,
        )
        self.assertEqual(47, rejected.returncode)
        self.assertEqual("1", verifier_count.read_text(encoding="utf-8"))
        self.assertEqual("1", provider_count.read_text(encoding="utf-8"))

        malformed = Path(self.temporary.name) / "malformed-registry.toml"
        malformed.write_text("schema_version = 999\n", encoding="utf-8")
        contract_failure = subprocess.run(
            [*base_command[:3], "--registry", str(malformed), *base_command[5:]],
            cwd=code_root / "other",
            env={**common_environment, "AI_TEST_VERIFIER_PAYLOAD": json.dumps(base_payload)},
            text=True,
            capture_output=True,
        )
        self.assertEqual(2, contract_failure.returncode)
        self.assertIn("blocked_contract", contract_failure.stderr)
        self.assertEqual("1", verifier_count.read_text(encoding="utf-8"))

        repository = self.make_git_repository()
        self.reviewed_instructions()
        self.make_fake_executable(
            "ai-session",
            "raise SystemExit(99)",
        )
        role_failure = self.run_entrypoint(
            "ai-codex", "--model", "unreviewed-model", cwd=repository
        )
        self.assertEqual(4, role_failure.returncode)
        self.assertEqual("blocked_policy", self.public_records(role_failure.stderr)[0]["status"])
        self.assertEqual("1", provider_count.read_text(encoding="utf-8"))

    def test_portable_cli_contract(self):
        with ROLE_MANIFEST.open("rb") as stream:
            manifest = tomllib.load(stream)
        for role in ROLES:
            self.assertEqual(
                REGISTRY_CONTRACT,
                manifest["roles"][role].get("registry_contract"),
                "registry contract token is required",
            )

        expected_contracts = {
            "codex": {
                "cli_version_range": ">=0.154.0,<0.155.0",
                "cli_required_options": [
                    "--model", "--sandbox", "--ask-for-approval",
                ],
                "cli_forbidden_options": [
                    "--dangerously-bypass-approvals-and-sandbox", "--full-auto",
                ],
            },
            "claude": {
                "cli_version_range": ">=2.1.269,<2.2.0",
                "cli_required_options": [
                    "--append-system-prompt", "--settings", "--plugin-dir",
                ],
                "cli_forbidden_options": [
                    "--append-system-prompt-file", "--plugin-url",
                ],
            },
        }
        for role in ROLES:
            for provider, expected in expected_contracts.items():
                policy = manifest["roles"][role][provider]
                for key, value in expected.items():
                    self.assertEqual(value, policy.get(key))

        self.install_source_ai_session()
        repository = self.make_git_repository()
        selector_capture = Path(self.temporary.name) / "selector-capture.json"
        self.make_fake_executable(
            "ai-session",
            """
            import json
            import os
            from pathlib import Path
            import sys
            Path(os.environ["AI_TEST_SELECTOR_CAPTURE"]).write_text(
                json.dumps(sys.argv[1:]), encoding="utf-8"
            )
            """,
        )
        base_environment = {
            **self.environment,
            "AI_TEST_SELECTOR_CAPTURE": str(selector_capture),
        }
        cases = (
            ("codex", "ai-codex", "executable_fake-cli-lower"),
            ("codex", "ai-codex", "executable_fake-cli-upper"),
            ("codex", "ai-codex", "executable_fake-cli-missing-option"),
            ("claude", "ai-claude", "executable_fake-cli-lower"),
            ("claude", "ai-claude", "executable_fake-cli-upper"),
            ("claude", "ai-claude", "executable_fake-cli-missing-option"),
        )
        for provider, entrypoint, fixture_name in cases:
            with self.subTest(provider=provider, fixture=fixture_name):
                shutil.copy2(CLI_FIXTURE_ROOT / fixture_name, self.bin_dir / provider)
                (self.bin_dir / provider).chmod(0o700)
                selector_capture.unlink(missing_ok=True)
                result = self.run_entrypoint(
                    entrypoint,
                    cwd=repository,
                    environment={
                        **base_environment,
                        "AI_TEST_FAKE_CLI_PROVIDER": provider,
                    },
                )
                self.assertEqual(4, result.returncode)
                self.assertEqual(
                    "blocked_cli_contract",
                    self.public_records(result.stderr)[0]["status"],
                )
                self.assertFalse(selector_capture.exists())

        for provider, entrypoint in (("codex", "ai-codex"), ("claude", "ai-claude")):
            with self.subTest(provider=provider, fixture="in-range"):
                shutil.copy2(
                    CLI_FIXTURE_ROOT / "executable_fake-cli-in-range",
                    self.bin_dir / provider,
                )
                (self.bin_dir / provider).chmod(0o700)
                selector_capture.unlink(missing_ok=True)
                result = self.run_entrypoint(
                    entrypoint,
                    cwd=repository,
                    environment={
                        **base_environment,
                        "AI_TEST_FAKE_CLI_PROVIDER": provider,
                    },
                )
                self.assertEqual(0, result.returncode, result.stderr)
                selector_arguments = json.loads(selector_capture.read_text(encoding="utf-8"))
                token_index = selector_arguments.index("--role-contract")
                self.assertEqual(REGISTRY_CONTRACT, selector_arguments[token_index + 1])

        probe_log = Path(self.temporary.name) / "installed-checker-probes"
        self.make_fake_executable("codex", "raise SystemExit(97)")
        self.make_fake_executable("claude", "raise SystemExit(97)")
        checker = subprocess.run(
            [sys.executable, str(INSTALLED_CLI_CHECKER)],
            cwd=ROOT,
            env={
                **self.environment,
                "AI_SESSION_CLI_PROBE_MODE": "help-only",
                "AI_TEST_CLI_PROBE_LOG": str(probe_log),
            },
            text=True,
            capture_output=True,
        )
        self.assertEqual(0, checker.returncode, checker.stderr)
        self.assertEqual(
            [
                "codex --version",
                "codex --help",
                "claude --version",
                "claude --help",
            ],
            probe_log.read_text(encoding="utf-8").splitlines(),
        )

    def test_registry_contract_mixed_deployment(self):
        with ROLE_MANIFEST.open("rb") as stream:
            manifest = tomllib.load(stream)
        for role in ROLES:
            self.assertEqual(
                REGISTRY_CONTRACT,
                manifest["roles"][role].get("registry_contract"),
                "registry contract token is required",
            )

        strict_registry, code_root, _, _ = self.write_strict_registry()
        verifier_count = Path(self.temporary.name) / "mixed-verifier-count"
        provider_count = Path(self.temporary.name) / "mixed-provider-count"
        verifier = self.make_fake_executable(
            "mixed-verifier",
            """
            import os
            from pathlib import Path
            Path(os.environ["AI_TEST_VERIFIER_COUNT"]).write_text("called", encoding="utf-8")
            """,
        )
        provider = self.make_fake_executable(
            "mixed-provider",
            """
            import os
            from pathlib import Path
            Path(os.environ["AI_TEST_PROVIDER_COUNT"]).write_text("called", encoding="utf-8")
            """,
        )
        environment = {
            **self.environment,
            "AI_TEST_VERIFIER_COUNT": str(verifier_count),
            "AI_TEST_PROVIDER_COUNT": str(provider_count),
        }

        old_selector_new_registry = subprocess.run(
            [
                sys.executable,
                str(CLI_FIXTURE_ROOT / "executable_fake-ai-session-v1"),
                "launch",
                "--registry", str(strict_registry),
                "--provider", "codex",
                "--role-profile", "general",
                "--verifier", str(verifier),
                "--", str(provider),
            ],
            cwd=code_root / "other",
            env=environment,
            text=True,
            capture_output=True,
        )
        self.assertEqual(2, old_selector_new_registry.returncode)
        self.assertIn("blocked_contract", old_selector_new_registry.stderr)

        old_caller_new_registry = subprocess.run(
            [
                sys.executable, str(ACCOUNT_SELECTOR), "launch",
                "--registry", str(strict_registry),
                "--provider", "codex",
                "--role-profile", "general",
                "--verifier", str(verifier),
                "--", str(provider),
            ],
            cwd=code_root / "other",
            env=environment,
            text=True,
            capture_output=True,
        )
        self.assertEqual(2, old_caller_new_registry.returncode)
        self.assertIn("blocked_contract", old_caller_new_registry.stderr)

        old_registry = Path(self.temporary.name) / "old-v1-registry.toml"
        old_registry.write_text(
            textwrap.dedent(
                f"""
                version = 1
                [accounts.codex-default]
                provider = "codex"
                auth_kind = "consumer"
                config_home = "{self.temporary.name}/old-home"
                allowed_scopes = ["repository:acme/widgets"]
                [defaults]
                codex = "codex-default"
                """
            ),
            encoding="utf-8",
        )
        new_selector_old_registry = subprocess.run(
            [
                sys.executable, str(ACCOUNT_SELECTOR), "launch",
                "--registry", str(old_registry),
                "--provider", "codex",
                "--role-profile", "general",
                "--repository", "acme/widgets",
                "--role-contract", REGISTRY_CONTRACT,
                "--verifier", str(verifier),
                "--", str(provider),
            ],
            cwd=ROOT,
            env=environment,
            text=True,
            capture_output=True,
        )
        self.assertEqual(2, new_selector_old_registry.returncode)
        self.assertIn("blocked_contract", new_selector_old_registry.stderr)

        direct_v1 = subprocess.run(
            [
                sys.executable, str(ACCOUNT_SELECTOR), "select",
                "--registry", str(old_registry),
                "--provider", "codex",
                "--role-profile", "general",
                "--repository", "acme/widgets",
            ],
            cwd=ROOT,
            env=environment,
            text=True,
            capture_output=True,
        )
        self.assertEqual(0, direct_v1.returncode, direct_v1.stderr)
        self.assertEqual("codex-default", json.loads(direct_v1.stdout)["account_profile"])
        self.assertFalse(verifier_count.exists())
        self.assertFalse(provider_count.exists())

    def test_documentation_contract(self):
        document_path = ROOT / "docs/orchestrator-permission-profiles.md"
        if not document_path.is_file():
            self.fail("operator recovery heading is missing")
        document = document_path.read_text(encoding="utf-8")

        required_headings = (
            "## Role and file map",
            "## Normalized real-path selection and alias/home mode",
            "## Model pins and availability",
            "## Claude usage_unknown operator response",
            "## Permission and common-dir boundary",
            "## Exact environment scrub",
            "## Stdio and TTY ownership",
            "## Leader lease and roles",
            "## Verifier and identity",
            "## Trusted settings, effective sources, and workmux",
            "## Mixed deployment",
            "## Cross-profile move",
            "## Legacy migration generation",
            "## No authentication copy and no hot swap",
            "## Workspace layout owned by #95",
            "## #94/#95 registration follow-up",
            "## Operator recovery",
            "## Status semantics",
        )
        for heading in required_headings:
            with self.subTest(heading=heading):
                self.assertIn(
                    heading,
                    document,
                    "operator recovery heading is missing"
                    if heading == "## Operator recovery"
                    else f"documentation heading is missing: {heading}",
                )

        required_phrases = (
            "done = agent-turn-ended, not issue-complete",
            "status surfaces are not authority or issue-completion signals",
            "Profile separation is account-selection policy; it is not repository security isolation.",
            "~/code/<repo>",
            "~/code/<workspace-profile>/<repo>/<task>",
            "no sessions/ or epic directories in the path",
            "only the final task directory is a worktree",
            "Creating this layout belongs to #95 and is a non-goal here.",
            "task_bindings and session_bindings are account-binding metadata consumed from the #94/#95 common registration contracts",
            "If #94 or #95 later defines a single authoritative store, these fields move into it rather than being duplicated.",
            "explicit option -> stored task/session binding -> longest directory mapping -> Codex-only provider default",
            "claude-profile1",
            "claude-profile2",
            "codex-default",
            "usage_unknown",
            "resolved worktree and the exact absolute Git common-dir",
            "stdin, stdout, and stderr remain attached to the provider",
            "trusted composed settings",
            "effective sources",
            "blocked_contract",
            "blocked_role_schema",
            "blocked_policy",
            "blocked_permission",
            "blocked_cli_contract",
            "blocked_binding",
            "blocked_leader_conflict",
            "not_logged_in",
            "identity_drift",
            "blocked_verifier",
            "blocked_usage",
        )
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, document)

        scrubbed_variables = (
            "CODEX_HOME",
            "CLAUDE_CONFIG_DIR",
            "CODEX_API_KEY",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "ANTHROPIC_AUTH_TOKEN",
            "CLAUDE_CODE_OAUTH_TOKEN",
            "CLAUDE_CODE_USE_BEDROCK",
            "CLAUDE_CODE_USE_VERTEX",
            "CLAUDE_CODE_USE_FOUNDRY",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "AWS_SESSION_TOKEN",
            "GOOGLE_APPLICATION_CREDENTIALS",
            "CLOUD_ML_REGION",
            "ANTHROPIC_VERTEX_PROJECT_ID",
            "ANTHROPIC_FOUNDRY_RESOURCE",
            "ANTHROPIC_FOUNDRY_API_KEY",
            "AI_COST_LIMIT_USD",
        )
        for variable in scrubbed_variables:
            with self.subTest(variable=variable):
                self.assertIn(f"`{variable}`", document)


if __name__ == "__main__":
    unittest.main()
