import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "dot_local/bin/executable_ai-session"


REGISTRY = """
version = 1

[accounts.codex-default]
provider = "codex"
auth_kind = "consumer"
config_home = "~/.local/share/ai-account-profiles/codex/default"
allowed_scopes = ["organization:acme"]

[accounts.codex-repo]
provider = "codex"
auth_kind = "consumer"
config_home = "~/.local/share/ai-account-profiles/codex/repo"
allowed_scopes = ["repository:acme/widgets"]

[accounts.codex-task]
provider = "codex"
auth_kind = "consumer"
config_home = "~/.local/share/ai-account-profiles/codex/task"
allowed_scopes = ["repository:acme/widgets"]

[accounts.codex-explicit]
provider = "codex"
auth_kind = "consumer"
config_home = "~/.local/share/ai-account-profiles/codex/explicit"
allowed_scopes = ["repository:acme/widgets"]

[accounts.claude-repo]
provider = "claude"
auth_kind = "organization"
config_home = "~/.local/share/ai-account-profiles/claude/repo"
allowed_scopes = ["repository:acme/widgets"]

[accounts.codex-payg]
provider = "codex"
auth_kind = "api_payg"
config_home = "~/.local/share/ai-account-profiles/codex/payg"
allowed_scopes = ["repository:acme/widgets"]
enabled = true
max_cost_usd = 12.5

[defaults]
codex = "codex-default"

[[scope_bindings]]
kind = "organization"
value = "acme"
provider = "codex"
account_profile = "codex-default"

[[scope_bindings]]
kind = "repository"
value = "acme/widgets"
provider = "codex"
account_profile = "codex-repo"
"""


class AiSessionCliTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name) / "home"
        self.home.mkdir()
        self.registry = Path(self.temporary.name) / "accounts.toml"
        self.registry.write_text(textwrap.dedent(REGISTRY), encoding="utf-8")
        self.environment = {
            **os.environ,
            "HOME": str(self.home),
            "PYTHONDONTWRITEBYTECODE": "1",
        }

    def run_cli(self, *arguments):
        return subprocess.run(
            [sys.executable, str(LAUNCHER), *arguments],
            cwd=ROOT,
            env=self.environment,
            text=True,
            capture_output=True,
        )

    def select(self, *arguments):
        return self.run_cli(
            "select",
            "--registry",
            str(self.registry),
            "--provider",
            "codex",
            "--role-profile",
            "general",
            "--repository",
            "acme/widgets",
            "--organization",
            "acme",
            *arguments,
        )

    def make_verifier(self, payload=None, *, exit_code=0, stderr=""):
        path = Path(self.temporary.name) / f"verifier-{len(list(Path(self.temporary.name).glob('verifier-*')))}"
        serialized = json.dumps(payload) if payload is not None else "not-json"
        path.write_text(
            textwrap.dedent(
                f"""\
                #!{sys.executable}
                import sys
                print({serialized!r})
                print({stderr!r}, file=sys.stderr)
                raise SystemExit({exit_code})
                """
            ),
            encoding="utf-8",
        )
        path.chmod(0o700)
        return path

    def verifier_payload(self, **changes):
        payload = {
            "provider": "codex",
            "account_profile": "codex-explicit",
            "login_status": "logged_in",
            "identity_status": "matched",
            "usage_status": "sufficient",
            "cost_limit_status": "not_applicable",
        }
        payload.update(changes)
        return payload

    def launch(self, verifier, *command, extra_arguments=()):
        (self.home / ".local/share/ai-account-profiles/codex/explicit").mkdir(parents=True, exist_ok=True)
        return self.run_cli(
            "launch",
            "--registry",
            str(self.registry),
            "--provider",
            "codex",
            "--role-profile",
            "general",
            "--repository",
            "acme/widgets",
            "--account-profile",
            "codex-explicit",
            "--verifier",
            str(verifier),
            *extra_arguments,
            "--",
            *command,
        )

    def assert_selected(self, result, profile, source, role="general"):
        self.assertEqual(0, result.returncode, result.stderr)
        binding = json.loads(result.stdout)
        self.assertEqual(profile, binding["account_profile"])
        self.assertEqual(source, binding["selection_source"])
        self.assertEqual("codex", binding["provider"])
        self.assertEqual(role, binding["role_profile"])
        self.assertNotIn("config_home", binding)

    def test_explicit_profile_wins_over_task_scope_and_default(self):
        binding_file = Path(self.temporary.name) / "bindings.json"
        binding_file.write_text(
            json.dumps(
                {
                    "version": 1,
                    "bindings": [
                        {
                            "kind": "task",
                            "id": "111",
                            "provider": "codex",
                            "account_profile": "codex-task",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        result = self.select(
            "--account-profile",
            "codex-explicit",
            "--task-id",
            "111",
            "--binding-file",
            str(binding_file),
        )

        self.assert_selected(result, "codex-explicit", "explicit")
        self.assertEqual("repository:acme/widgets", json.loads(result.stdout)["account_scope"])

    def test_task_and_epic_disagreement_at_same_priority_fails_closed(self):
        binding_file = Path(self.temporary.name) / "bindings.json"
        binding_file.write_text(
            json.dumps(
                {
                    "version": 1,
                    "bindings": [
                        {
                            "kind": "task",
                            "id": "111",
                            "provider": "codex",
                            "account_profile": "codex-task",
                        },
                        {
                            "kind": "epic",
                            "id": "67",
                            "provider": "codex",
                            "account_profile": "codex-repo",
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )

        result = self.select(
            "--task-id",
            "111",
            "--epic-id",
            "67",
            "--binding-file",
            str(binding_file),
        )

        self.assertEqual(2, result.returncode)
        self.assertIn("같은 우선순위", result.stderr)
        self.assertEqual("", result.stdout)

    def test_repository_scope_is_more_specific_than_organization(self):
        result = self.select()

        self.assert_selected(result, "codex-repo", "scope:repository")

    def test_different_profiles_at_same_scope_specificity_fail_closed(self):
        with self.registry.open("a", encoding="utf-8") as stream:
            stream.write(
                textwrap.dedent(
                    """

                    [[scope_bindings]]
                    kind = "repository"
                    value = "acme/widgets"
                    provider = "codex"
                    account_profile = "codex-task"
                    """
                )
            )

        result = self.select()

        self.assertEqual(2, result.returncode)
        self.assertIn("같은 우선순위", result.stderr)

    def test_selected_profile_must_allow_the_current_scope(self):
        result = self.select(
            "--repository",
            "outside/repository",
            "--organization",
            "outside",
            "--account-profile",
            "codex-explicit",
        )

        self.assertEqual(2, result.returncode)
        self.assertIn("scope", result.stderr)

    def test_profile_provider_must_match_requested_provider(self):
        result = self.select("--account-profile", "claude-repo")

        self.assertEqual(2, result.returncode)
        self.assertIn("provider", result.stderr)

    def test_provider_default_is_used_only_after_other_sources(self):
        result = self.run_cli(
            "select",
            "--registry",
            str(self.registry),
            "--provider",
            "codex",
            "--role-profile",
            "orchestrator",
            "--organization",
            "acme",
        )

        self.assert_selected(result, "codex-default", "scope:organization", role="orchestrator")

        default_only_registry = Path(self.temporary.name) / "default-only.toml"
        default_only_registry.write_text(
            textwrap.dedent(REGISTRY).split("[[scope_bindings]]", 1)[0],
            encoding="utf-8",
        )
        default_result = self.run_cli(
            "select",
            "--registry",
            str(default_only_registry),
            "--provider",
            "codex",
            "--role-profile",
            "orchestrator",
            "--organization",
            "acme",
        )
        self.assert_selected(default_result, "codex-default", "default", role="orchestrator")

    def test_payg_requires_explicit_selection_and_a_bounded_cost(self):
        implicit_binding = Path(self.temporary.name) / "payg-bindings.json"
        implicit_binding.write_text(
            json.dumps(
                {
                    "version": 1,
                    "bindings": [
                        {
                            "kind": "task",
                            "id": "111",
                            "provider": "codex",
                            "account_profile": "codex-payg",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        implicit = self.select(
            "--task-id",
            "111",
            "--binding-file",
            str(implicit_binding),
            "--cost-limit-usd",
            "5",
        )
        missing_limit = self.select("--account-profile", "codex-payg")
        excessive_limit = self.select(
            "--account-profile",
            "codex-payg",
            "--cost-limit-usd",
            "13",
        )
        allowed = self.select(
            "--account-profile",
            "codex-payg",
            "--cost-limit-usd",
            "5",
        )

        for result in (implicit, missing_limit, excessive_limit):
            self.assertEqual(2, result.returncode, result.stderr)
            self.assertIn("PAYG", result.stderr)
        self.assert_selected(allowed, "codex-payg", "explicit")

    def test_payg_rejects_non_finite_registry_and_requested_cost_limits(self):
        for raw_limit in ("nan", "inf", "-inf"):
            with self.subTest(requested_limit=raw_limit):
                result = self.select(
                    "--account-profile",
                    "codex-payg",
                    f"--cost-limit-usd={raw_limit}",
                )
                self.assertEqual(2, result.returncode, result.stderr)
                self.assertIn("PAYG", result.stderr)

        for raw_limit in ("nan", "inf", "-inf"):
            with self.subTest(registry_limit=raw_limit):
                registry = Path(self.temporary.name) / f"non-finite-{raw_limit}.toml"
                registry.write_text(
                    textwrap.dedent(REGISTRY).replace(
                        "max_cost_usd = 12.5", f"max_cost_usd = {raw_limit}"
                    ),
                    encoding="utf-8",
                )
                result = self.run_cli(
                    "select",
                    "--registry",
                    str(registry),
                    "--provider",
                    "codex",
                    "--role-profile",
                    "general",
                    "--repository",
                    "acme/widgets",
                    "--account-profile",
                    "codex-payg",
                    "--cost-limit-usd",
                    "5",
                )
                self.assertEqual(2, result.returncode, result.stderr)
                self.assertIn("PAYG", result.stderr)

    def test_launch_rejects_not_logged_in_identity_drift_and_usage_denials(self):
        cases = (
            ({"login_status": "not_logged_in"}, "미로그인"),
            ({"identity_status": "identity_drift"}, "identity drift"),
            ({"identity_status": "unknown"}, "identity"),
            ({"usage_status": "usage_unknown"}, "usage_unknown"),
            ({"usage_status": "blocked_usage"}, "blocked_usage"),
        )
        for changes, expected_error in cases:
            with self.subTest(changes=changes):
                verifier = self.make_verifier(self.verifier_payload(**changes))
                result = self.launch(verifier, sys.executable, "-c", "print('started')")
                self.assertEqual(3, result.returncode, result.stderr)
                self.assertIn(expected_error, result.stderr)
                self.assertNotIn("started", result.stdout)

    def test_launch_requires_an_existing_non_symlink_config_home(self):
        verifier = self.make_verifier(self.verifier_payload())
        result = self.run_cli(
            "launch",
            "--registry",
            str(self.registry),
            "--provider",
            "codex",
            "--role-profile",
            "general",
            "--repository",
            "acme/widgets",
            "--account-profile",
            "codex-explicit",
            "--verifier",
            str(verifier),
            "--",
            sys.executable,
            "-c",
            "print('started')",
        )

        self.assertEqual(3, result.returncode)
        self.assertIn("config_home", result.stderr)
        self.assertEqual("", result.stdout)

    def test_launch_rejects_a_symlinked_config_home(self):
        real_home = Path(self.temporary.name) / "real-account-home"
        real_home.mkdir()
        profile_home = self.home / ".local/share/ai-account-profiles/codex/explicit"
        profile_home.parent.mkdir(parents=True)
        profile_home.symlink_to(real_home, target_is_directory=True)
        verifier = self.make_verifier(self.verifier_payload())

        result = self.run_cli(
            "launch",
            "--registry",
            str(self.registry),
            "--provider",
            "codex",
            "--role-profile",
            "general",
            "--repository",
            "acme/widgets",
            "--account-profile",
            "codex-explicit",
            "--verifier",
            str(verifier),
            "--",
            sys.executable,
            "-c",
            "print('started')",
        )

        self.assertNotEqual(0, result.returncode)
        self.assertIn("config_home", result.stderr)
        self.assertEqual("", result.stdout)

    def test_launch_rejects_malformed_or_mismatched_verifier_results_without_leaking_output(self):
        malformed = self.make_verifier(stderr="private-marker")
        extra_field = self.make_verifier(
            {**self.verifier_payload(), "unexpected": "private-marker"}
        )
        wrong_provider = self.make_verifier(self.verifier_payload(provider="claude"))
        wrong_profile = self.make_verifier(
            self.verifier_payload(account_profile="codex-repo")
        )

        for verifier in (malformed, extra_field, wrong_provider, wrong_profile):
            with self.subTest(verifier=verifier.name):
                result = self.launch(verifier, sys.executable, "-c", "print('started')")
                self.assertEqual(3, result.returncode, result.stderr)
                self.assertIn("verifier", result.stderr)
                self.assertNotIn("private-marker", result.stderr)
                self.assertEqual("", result.stdout)

    def test_launch_execs_once_with_fixed_codex_home_and_independent_role_profile(self):
        verifier = self.make_verifier(self.verifier_payload())
        child = Path(self.temporary.name) / "fake-child"
        changed_directory = Path(self.temporary.name) / "changed-directory"
        changed_directory.mkdir()
        child.write_text(
            textwrap.dedent(
                f"""\
                #!{sys.executable}
                import json
                import os
                os.chdir({str(changed_directory)!r})
                print(json.dumps({{
                    "provider": os.environ.get("AI_PROVIDER"),
                    "role_profile": os.environ.get("AI_ROLE_PROFILE"),
                    "account_profile": os.environ.get("AI_ACCOUNT_PROFILE"),
                    "account_scope": os.environ.get("AI_ACCOUNT_SCOPE"),
                    "selection_source": os.environ.get("AI_SELECTION_SOURCE"),
                    "usage_status": os.environ.get("AI_USAGE_ADMISSION_STATUS"),
                    "binding_generation": os.environ.get("AI_BINDING_GENERATION"),
                    "codex_home": os.environ.get("CODEX_HOME"),
                    "claude_config_dir": os.environ.get("CLAUDE_CONFIG_DIR"),
                    "cwd": os.getcwd(),
                }}, sort_keys=True))
                """
            ),
            encoding="utf-8",
        )
        child.chmod(0o700)
        self.environment["CODEX_HOME"] = "/should/not/survive"
        self.environment["CLAUDE_CONFIG_DIR"] = "/should/not/leak"

        result = self.launch(verifier, str(child))

        self.assertEqual(0, result.returncode, result.stderr)
        launched = json.loads(result.stdout)
        self.assertEqual("codex", launched["provider"])
        self.assertEqual("general", launched["role_profile"])
        self.assertEqual("codex-explicit", launched["account_profile"])
        self.assertEqual("repository:acme/widgets", launched["account_scope"])
        self.assertEqual("explicit", launched["selection_source"])
        self.assertEqual("sufficient", launched["usage_status"])
        self.assertEqual("1", launched["binding_generation"])
        self.assertEqual(
            str((self.home / ".local/share/ai-account-profiles/codex/explicit").resolve()),
            launched["codex_home"],
        )
        self.assertIsNone(launched["claude_config_dir"])
        self.assertEqual(str(changed_directory.resolve()), launched["cwd"])
        self.assertIn("usage_admission_status=sufficient", result.stderr)

    def test_launch_uses_claude_config_dir_for_claude_provider(self):
        verifier = self.make_verifier(
            self.verifier_payload(provider="claude", account_profile="claude-repo")
        )
        command = (
            sys.executable,
            "-c",
            "import json,os; print(json.dumps({'claude': os.getenv('CLAUDE_CONFIG_DIR'), 'codex': os.getenv('CODEX_HOME')}))",
        )
        (self.home / ".local/share/ai-account-profiles/claude/repo").mkdir(
            parents=True, exist_ok=True
        )

        result = self.run_cli(
            "launch",
            "--registry",
            str(self.registry),
            "--provider",
            "claude",
            "--role-profile",
            "feature-orchestrator",
            "--repository",
            "acme/widgets",
            "--account-profile",
            "claude-repo",
            "--verifier",
            str(verifier),
            "--",
            *command,
        )

        self.assertEqual(0, result.returncode, result.stderr)
        launched = json.loads(result.stdout)
        self.assertEqual(
            str((self.home / ".local/share/ai-account-profiles/claude/repo").resolve()),
            launched["claude"],
        )
        self.assertIsNone(launched["codex"])

    def test_payg_launch_requires_verifier_to_confirm_cost_limit_enforcement(self):
        payg_home = self.home / ".local/share/ai-account-profiles/codex/payg"
        payg_home.mkdir(parents=True)
        child = (sys.executable, "-c", "import os; print(os.environ['AI_COST_LIMIT_USD'])")
        unbounded = self.make_verifier(
            self.verifier_payload(account_profile="codex-payg")
        )
        bounded = self.make_verifier(
            self.verifier_payload(
                account_profile="codex-payg",
                cost_limit_status="enforced",
            )
        )

        common = (
            "launch",
            "--registry",
            str(self.registry),
            "--provider",
            "codex",
            "--role-profile",
            "general",
            "--repository",
            "acme/widgets",
            "--account-profile",
            "codex-payg",
            "--cost-limit-usd",
            "5",
        )
        rejected = self.run_cli(*common, "--verifier", str(unbounded), "--", *child)
        allowed = self.run_cli(*common, "--verifier", str(bounded), "--", *child)

        self.assertEqual(3, rejected.returncode)
        self.assertIn("비용 한도", rejected.stderr)
        self.assertEqual("", rejected.stdout)
        self.assertEqual(0, allowed.returncode, allowed.stderr)
        self.assertEqual("5\n", allowed.stdout)

    def test_deployed_registry_selects_provider_specific_dotfiles_profiles(self):
        deployed_registry = ROOT / "dot_config/ai-session/accounts.toml"

        for provider, expected_profile in (
            ("codex", "codex-dotfiles"),
            ("claude", "claude-dotfiles"),
        ):
            with self.subTest(provider=provider):
                result = self.run_cli(
                    "select",
                    "--registry",
                    str(deployed_registry),
                    "--provider",
                    provider,
                    "--role-profile",
                    "general",
                    "--repository",
                    "lee-kyu-hwan/dotfiles",
                )
                self.assertEqual(0, result.returncode, result.stderr)
                selected = json.loads(result.stdout)
                self.assertEqual(expected_profile, selected["account_profile"])
                self.assertEqual("scope:repository", selected["selection_source"])

    def test_registry_rejects_sensitive_or_unrecognized_profile_fields_without_echoing_values(self):
        with self.registry.open("a", encoding="utf-8") as stream:
            stream.write(
                textwrap.dedent(
                    """

                    [accounts.codex-explicit.identity]
                    email = "fixture-sensitive-value"
                    """
                )
            )

        result = self.select()

        self.assertEqual(2, result.returncode)
        self.assertIn("허용되지 않은 필드", result.stderr)
        self.assertNotIn("fixture-sensitive-value", result.stderr)

    def test_longest_matching_directory_scope_wins_without_prefix_confusion(self):
        directory_registry = Path(self.temporary.name) / "directories.toml"
        directory_registry.write_text(
            textwrap.dedent(
                f"""
                version = 1

                [accounts.broad]
                provider = "codex"
                auth_kind = "consumer"
                config_home = "{self.home}/profiles/broad"
                allowed_scopes = ["directory:{self.home}/code"]

                [accounts.narrow]
                provider = "codex"
                auth_kind = "consumer"
                config_home = "{self.home}/profiles/narrow"
                allowed_scopes = ["directory:{self.home}/code/project"]

                [[scope_bindings]]
                kind = "directory"
                value = "{self.home}/code"
                provider = "codex"
                account_profile = "broad"

                [[scope_bindings]]
                kind = "directory"
                value = "{self.home}/code/project"
                provider = "codex"
                account_profile = "narrow"
                """
            ),
            encoding="utf-8",
        )

        selected = self.run_cli(
            "select",
            "--registry",
            str(directory_registry),
            "--provider",
            "codex",
            "--role-profile",
            "general",
            "--directory",
            str(self.home / "code/project/subdirectory"),
        )
        sibling = self.run_cli(
            "select",
            "--registry",
            str(directory_registry),
            "--provider",
            "codex",
            "--role-profile",
            "general",
            "--directory",
            str(self.home / "code/project-a"),
        )
        outside = self.run_cli(
            "select",
            "--registry",
            str(directory_registry),
            "--provider",
            "codex",
            "--role-profile",
            "general",
            "--directory",
            str(self.home / "code-other"),
        )

        self.assertEqual(0, selected.returncode, selected.stderr)
        self.assertEqual("narrow", json.loads(selected.stdout)["account_profile"])
        self.assertEqual(0, sibling.returncode, sibling.stderr)
        self.assertEqual("broad", json.loads(sibling.stdout)["account_profile"])
        self.assertEqual(2, outside.returncode)
        self.assertIn("선택 가능한", outside.stderr)


if __name__ == "__main__":
    unittest.main()
