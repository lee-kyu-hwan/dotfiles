import hashlib
import json
import os
from pathlib import Path
import runpy
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

    def write_strict_registry(self, *, usage_contract="none"):
        registry = Path(self.temporary.name) / f"strict-{usage_contract}.toml"
        config_home = Path(self.temporary.name) / "strict-codex-home"
        config_home.mkdir(exist_ok=True)
        registry.write_text(
            textwrap.dedent(
                f"""
                schema_version = 2
                contract_id = "orchestrator-permission-profiles-v2"
                task_bindings = []
                session_bindings = []

                [[accounts]]
                alias = "codex-strict"
                provider = "codex"
                auth_kind = "consumer"
                config_home = "{config_home}"
                allowed_scopes = [{{ kind = "directory", value = "{ROOT}" }}]
                identity_enrollment_policy = "explicit_only"
                identity_contract = "unavailable"
                usage_contract = "{usage_contract}"

                [[workspace_directory_mappings]]
                root = "{ROOT}"
                provider = "codex"
                account_profile = "codex-strict"
                priority = 100

                [legacy_records]
                """
            ),
            encoding="utf-8",
        )
        return registry

    def write_strict_claude_registry(self, *, inactive_duplicate=False):
        registry = Path(self.temporary.name) / "strict-claude.toml"
        selected_home = Path(self.temporary.name) / "claude-selected-home"
        other_home = Path(self.temporary.name) / "claude-other-home"
        inactive_home = Path(self.temporary.name) / "claude-inactive-home"
        for path in (selected_home, other_home, inactive_home):
            path.mkdir(exist_ok=True)
        registry.write_text(
            textwrap.dedent(
                f"""
                schema_version = 2
                contract_id = "orchestrator-permission-profiles-v2"
                task_bindings = []
                session_bindings = []

                [[accounts]]
                alias = "claude-selected"
                provider = "claude"
                auth_kind = "consumer"
                config_home_mode = "explicit"
                config_home = "{selected_home}"
                allowed_scopes = [{{ kind = "directory", value = "{ROOT}" }}]
                identity_enrollment_policy = "explicit_only"
                identity_contract = "claude_auth_status_v1"
                usage_contract = "none"

                [[accounts]]
                alias = "claude-other"
                provider = "claude"
                auth_kind = "consumer"
                config_home_mode = "explicit"
                config_home = "{other_home}"
                allowed_scopes = [{{ kind = "directory", value = "{ROOT}" }}]
                identity_enrollment_policy = "explicit_only"
                identity_contract = "claude_auth_status_v1"
                usage_contract = "none"

                [[accounts]]
                alias = "claude-inactive"
                provider = "claude"
                auth_kind = "consumer"
                config_home_mode = "explicit"
                config_home = "{inactive_home}"
                allowed_scopes = [{{ kind = "directory", value = "{ROOT}" }}]
                enabled = {str(not inactive_duplicate).lower()}
                identity_enrollment_policy = "explicit_only"
                identity_contract = "claude_auth_status_v1"
                usage_contract = "none"

                [[workspace_directory_mappings]]
                root = "{ROOT}"
                provider = "claude"
                account_profile = "claude-selected"
                priority = 100

                [legacy_records]
                """
            ),
            encoding="utf-8",
        )
        return registry

    @staticmethod
    def claude_digest_line(official):
        canonical = {
            "schema_version": 2,
            "identity_contract": "claude_auth_status_v1",
            "provider": "claude",
            "auth_method": official["authMethod"],
            "org_id": official["orgId"],
            "subscription_type": official["subscriptionType"],
        }
        encoded = json.dumps(
            canonical, ensure_ascii=False, separators=(",", ":"), sort_keys=True
        ).encode("utf-8")
        return b"v2:" + hashlib.sha256(encoded).hexdigest().encode("ascii") + b"\n"

    def write_owner_digest(self, path, data):
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        path.parent.chmod(0o700)
        path.write_bytes(data)
        path.chmod(0o600)

    def make_claude_status_provider(self, official):
        bin_directory = Path(self.temporary.name) / "claude-bin"
        bin_directory.mkdir(exist_ok=True)
        executable = bin_directory / "claude"
        executable.write_text(
            f"#!{sys.executable}\nimport json\nprint({json.dumps(official)!r})\n",
            encoding="utf-8",
        )
        executable.chmod(0o700)
        self.environment["PATH"] = os.pathsep.join(
            (str(bin_directory), self.environment["PATH"])
        )

    def strict_claude_status(self, registry, *extra_arguments):
        return self.run_cli(
            "status",
            "--registry",
            str(registry),
            "--provider",
            "claude",
            "--role-profile",
            "general",
            "--account-profile",
            "claude-selected",
            "--verifier",
            str(ROOT / "dot_local/libexec/executable_ai-session-verify-claude"),
            *extra_arguments,
        )

    def strict_claude_launch(self, registry, *program, extra_arguments=()):
        return self.run_cli(
            "launch",
            "--registry",
            str(registry),
            "--provider",
            "claude",
            "--role-profile",
            "general",
            "--role-contract",
            "orchestrator-permission-profiles-v2",
            "--account-profile",
            "claude-selected",
            "--verifier",
            str(ROOT / "dot_local/libexec/executable_ai-session-verify-claude"),
            *extra_arguments,
            "--",
            *program,
        )

    def strict_payload(self, **changes):
        payload = {
            "provider": "codex",
            "account_profile": "codex-strict",
            "login_status": "logged_in",
            "identity_status": "unavailable",
            "usage_status": "usage_unknown",
            "cost_limit_status": "not_applicable",
        }
        payload.update(changes)
        return payload

    def strict_status(self, registry, verifier, *extra_arguments):
        return self.run_cli(
            "status",
            "--registry",
            str(registry),
            "--provider",
            "codex",
            "--role-profile",
            "general",
            "--verifier",
            str(verifier),
            *extra_arguments,
        )

    def strict_launch(self, registry, verifier, *program, extra_arguments=()):
        return self.run_cli(
            "launch",
            "--registry",
            str(registry),
            "--provider",
            "codex",
            "--role-profile",
            "general",
            "--role-contract",
            "orchestrator-permission-profiles-v2",
            "--verifier",
            str(verifier),
            *extra_arguments,
            "--",
            *program,
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

    def test_admission_precedence_and_dual_consent(self):
        marker = Path(self.temporary.name) / "provider-started"
        provider = (
            sys.executable,
            "-c",
            "import os; from pathlib import Path; "
            f"Path({str(marker)!r}).write_text(os.environ['AI_USAGE_ADMISSION_STATUS'])",
        )
        for usage_contract in ("none", "provider_status"):
            for accepted in (False, True):
                with self.subTest(surface="status", contract=usage_contract, accepted=accepted):
                    registry = self.write_strict_registry(usage_contract=usage_contract)
                    verifier = self.make_verifier(self.strict_payload())
                    flags = ("--accept-usage-unknown",) if accepted else ()
                    result = self.strict_status(registry, verifier, *flags)
                    self.assertEqual(0 if usage_contract == "none" and accepted else 3, result.returncode)
                    status = json.loads(result.stdout)
                    self.assertEqual(
                        "ready" if usage_contract == "none" and accepted else "usage_unknown",
                        status["status"],
                    )
                    self.assertEqual("usage_unknown", status["usage_status"])

                with self.subTest(surface="launch", contract=usage_contract, accepted=accepted):
                    marker.unlink(missing_ok=True)
                    verifier = self.make_verifier(self.strict_payload())
                    flags = ("--accept-usage-unknown",) if accepted else ()
                    result = self.strict_launch(
                        registry, verifier, *provider, extra_arguments=flags
                    )
                    allowed = usage_contract == "none" and accepted
                    self.assertEqual(0 if allowed else 3, result.returncode, result.stderr)
                    self.assertEqual(allowed, marker.exists())
                    if allowed:
                        self.assertEqual("usage_unknown", marker.read_text(encoding="utf-8"))
                        records = [
                            json.loads(line)
                            for line in result.stderr.splitlines()
                            if line.startswith("{")
                        ]
                        self.assertEqual("account_binding", records[-1]["event"])
                        self.assertEqual(
                            "usage_unknown", records[-1]["usage_admission_status"]
                        )

        marker.unlink(missing_ok=True)
        registry = self.write_strict_registry()
        verifier = self.make_verifier(self.strict_payload())
        misplaced = self.strict_launch(
            registry,
            verifier,
            sys.executable,
            "-c",
            "print('should-not-start')",
            "--accept-usage-unknown",
        )
        self.assertEqual(3, misplaced.returncode)
        self.assertNotIn("should-not-start", misplaced.stdout)

    def test_duplicate_mapping_admission(self):
        official = {
            "loggedIn": True,
            "authMethod": "claude.ai",
            "orgId": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
            "subscriptionType": "pro",
        }
        self.make_claude_status_provider(official)
        registry = self.write_strict_claude_registry()
        identity_root = Path(self.temporary.name) / "synthetic-identity-root"
        self.environment["AI_SESSION_SYNTHETIC_TEST"] = "1"
        self.environment["AI_SESSION_IDENTITY_ROOT"] = str(identity_root)
        digest = self.claude_digest_line(official)
        selected = identity_root / "claude/claude-selected.sha256"
        other = identity_root / "claude/claude-other.sha256"
        self.write_owner_digest(selected, digest)
        self.write_owner_digest(other, digest)

        default_selected = (
            self.home
            / ".local/share/ai-account-profiles/identities/claude/claude-selected.sha256"
        )
        self.write_owner_digest(default_selected, digest)
        self.environment["AI_SESSION_SYNTHETIC_TEST"] = "0"
        production_ignores_override = self.strict_claude_status(
            registry, "--accept-usage-unknown"
        )
        self.assertEqual(0, production_ignores_override.returncode)
        self.assertEqual("ready", json.loads(production_ignores_override.stdout)["status"])
        self.environment["AI_SESSION_SYNTHETIC_TEST"] = "1"

        status = self.strict_claude_status(
            registry, "--accept-usage-unknown"
        )
        self.assertEqual(3, status.returncode, status.stderr)
        status_payload = json.loads(status.stdout)
        self.assertEqual("duplicate_mapping", status_payload["status"])
        self.assertEqual("duplicate_mapping", status_payload["identity_status"])
        self.assertEqual([], status_payload["commands"])

        marker = Path(self.temporary.name) / "duplicate-provider-started"
        launch = self.strict_claude_launch(
            registry,
            sys.executable,
            "-c",
            f"from pathlib import Path; Path({str(marker)!r}).touch()",
            extra_arguments=("--accept-usage-unknown",),
        )
        self.assertEqual(3, launch.returncode, launch.stderr)
        self.assertFalse(marker.exists())
        launch_records = [json.loads(line) for line in launch.stderr.splitlines()]
        self.assertEqual("duplicate_mapping", launch_records[-1]["status"])

        other.write_bytes(b"a" * 64 + b"\n")
        other.chmod(0o600)
        legacy = self.strict_claude_status(
            registry, "--accept-usage-unknown"
        )
        self.assertEqual(0, legacy.returncode, legacy.stderr)
        self.assertEqual("ready", json.loads(legacy.stdout)["status"])

        other.unlink()
        missing = self.strict_claude_status(
            registry, "--accept-usage-unknown"
        )
        self.assertEqual(0, missing.returncode, missing.stderr)

        self.write_owner_digest(other, digest)
        other.chmod(0o644)
        unsafe = self.strict_claude_status(
            registry, "--accept-usage-unknown"
        )
        self.assertEqual(3, unsafe.returncode)
        self.assertEqual("blocked_verifier", json.loads(unsafe.stdout)["status"])

        other.unlink()
        inactive = identity_root / "claude/claude-inactive.sha256"
        self.write_owner_digest(inactive, digest)
        inactive_registry = self.write_strict_claude_registry(inactive_duplicate=True)
        ignored = self.strict_claude_status(
            inactive_registry, "--accept-usage-unknown"
        )
        self.assertEqual(0, ignored.returncode, ignored.stderr)
        self.assertEqual("ready", json.loads(ignored.stdout)["status"])

        self.environment["AI_OTHER_ACTIVE_CLAUDE_IDENTITY_DIGEST_FILES"] = "malformed"
        spoofed = self.strict_claude_status(
            inactive_registry, "--accept-usage-unknown"
        )
        self.assertEqual(0, spoofed.returncode, spoofed.stderr)
        self.assertFalse(
            digest.decode("ascii").strip() in spoofed.stdout + spoofed.stderr
        )

    def test_unavailable_identity_admission(self):
        registry = self.write_strict_registry()
        ready = self.strict_status(
            registry,
            self.make_verifier(self.strict_payload()),
            "--accept-usage-unknown",
        )
        forged = self.strict_status(
            registry,
            self.make_verifier(self.strict_payload(identity_status="matched")),
            "--accept-usage-unknown",
        )
        self.assertEqual(0, ready.returncode, ready.stderr)
        self.assertEqual("unavailable", json.loads(ready.stdout)["identity_status"])
        self.assertEqual(3, forged.returncode)
        self.assertEqual("blocked_verifier", json.loads(forged.stdout)["status"])

    def test_admission_fail_closed_exceptions(self):
        registry = self.write_strict_registry()
        cases = (
            ({"login_status": "not_logged_in"}, "login_required"),
            ({"identity_status": "identity_drift"}, "identity_drift"),
            ({"identity_status": "not_enrolled"}, "enrollment_required"),
            ({"identity_status": "identity_unverifiable"}, "identity_unverifiable"),
            ({"identity_status": "duplicate_mapping"}, "duplicate_mapping"),
            ({"cost_limit_status": "unknown"}, "blocked_verifier"),
            ({"usage_status": "blocked_usage"}, "blocked_usage"),
        )
        for changes, expected in cases:
            with self.subTest(changes=changes):
                result = self.strict_status(
                    registry,
                    self.make_verifier(self.strict_payload(**changes)),
                    "--accept-usage-unknown",
                )
                self.assertEqual(3, result.returncode)
                self.assertEqual(expected, json.loads(result.stdout)["status"])

    def test_status_to_launch_failure_mapping(self):
        registry = self.write_strict_registry()
        cases = (
            ({"login_status": "not_logged_in"}, "login_required", "not_logged_in"),
            ({"identity_status": "not_enrolled"}, "enrollment_required", "blocked_verifier"),
            ({"identity_status": "identity_drift"}, "identity_drift", "identity_drift"),
            ({"identity_status": "identity_unverifiable"}, "identity_unverifiable", "identity_unverifiable"),
            ({"identity_status": "duplicate_mapping"}, "duplicate_mapping", "duplicate_mapping"),
            ({"usage_status": "blocked_usage"}, "blocked_usage", "blocked_usage"),
        )
        for changes, facade_status, launch_status in cases:
            with self.subTest(changes=changes):
                verifier = self.make_verifier(self.strict_payload(**changes))
                status_result = self.strict_status(registry, verifier)
                launch_result = self.strict_launch(
                    registry, verifier, sys.executable, "-c", "print('started')"
                )
                self.assertEqual(facade_status, json.loads(status_result.stdout)["status"])
                records = [json.loads(line) for line in launch_result.stderr.splitlines() if line.startswith("{")]
                self.assertEqual(launch_status, records[-1]["status"])

    def test_blocked_verifier_launch_reasons_are_distinct(self):
        launcher = runpy.run_path(str(LAUNCHER), run_name="ai_session_test_module")
        decision_type = launcher["AdmissionDecision"]
        to_error = launcher["decision_to_launch_error"]
        messages = {
            reason: str(to_error(decision_type(
                login_status="unknown",
                identity_status="unknown",
                usage_status="usage_unknown",
                cost_limit_status="unknown",
                public_status="blocked_verifier",
                exit_code=3,
                admitted=False,
                failure_reason=reason,
            )))
            for reason in (
                "login_contract", "identity_contract", "cost_enforcement", "cost_contract"
            )
        }
        self.assertEqual(4, len(set(messages.values())))
        self.assertTrue(all("fixture-private" not in message for message in messages.values()))

    def test_status_is_read_only(self):
        registry = self.write_strict_registry()
        verifier_count = Path(self.temporary.name) / "verifier-count"
        verifier = Path(self.temporary.name) / "counting-verifier"
        verifier.write_text(
            textwrap.dedent(
                f"""\
                #!{sys.executable}
                import json
                from pathlib import Path
                path = Path({str(verifier_count)!r})
                path.write_text(str(int(path.read_text()) + 1) if path.exists() else "1")
                print(json.dumps({self.strict_payload()!r}))
                """
            ),
            encoding="utf-8",
        )
        verifier.chmod(0o700)
        before = registry.read_bytes()
        result = self.strict_status(registry, verifier, "--accept-usage-unknown")
        rejected_program = self.strict_status(registry, verifier, "unexpected-program")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertNotEqual(0, rejected_program.returncode)
        self.assertEqual("1", verifier_count.read_text())
        self.assertEqual(before, registry.read_bytes())

    def test_status_schema_exit_and_commands(self):
        registry = self.write_strict_registry()
        cases = (
            ({}, False, "usage_unknown", 3, "retry_with_usage_consent"),
            ({}, True, "ready", 0, None),
            ({"login_status": "not_logged_in"}, False, "login_required", 3, "provider_login_foreground"),
            ({"identity_status": "not_enrolled"}, False, "enrollment_required", 3, "identity_enroll_foreground"),
            ({"identity_status": "identity_drift"}, False, "identity_drift", 3, "inspect_identity_foreground"),
            ({"identity_status": "identity_unverifiable"}, False, "identity_unverifiable", 3, None),
            ({"identity_status": "duplicate_mapping"}, False, "duplicate_mapping", 3, None),
            ({"usage_status": "blocked_usage"}, False, "blocked_usage", 3, None),
        )
        top_fields = {
            "schema_version", "event", "provider", "account_profile", "status",
            "login_status", "identity_status", "usage_status", "cost_limit_status", "commands",
        }
        for changes, accepted, expected_status, exit_code, command_id in cases:
            with self.subTest(status=expected_status):
                flags = ("--accept-usage-unknown",) if accepted else ()
                result = self.strict_status(
                    registry, self.make_verifier(self.strict_payload(**changes)), *flags
                )
                self.assertEqual(exit_code, result.returncode, result.stderr)
                payload = json.loads(result.stdout)
                self.assertEqual(top_fields, set(payload))
                self.assertEqual(expected_status, payload["status"])
                self.assertEqual(
                    [] if command_id is None else [{
                        "command_id": command_id,
                        "provider": "codex",
                        "account_profile": "codex-strict",
                    }],
                    payload["commands"],
                )

        missing = self.run_cli(
            "status", "--registry", str(Path(self.temporary.name) / "missing.toml"),
            "--provider", "codex", "--role-profile", "general",
            "--verifier", str(self.make_verifier(self.strict_payload())),
        )
        self.assertEqual(2, missing.returncode)
        self.assertIsNone(json.loads(missing.stdout)["account_profile"])

    def test_status_blocked_binding_and_policy_exact_json(self):
        registry = self.write_strict_registry()
        verifier = self.make_verifier(self.strict_payload())
        blocked_binding = self.run_cli(
            "status", "--registry", str(registry), "--provider", "codex",
            "--role-profile", "general", "--account-profile", "missing-profile",
            "--verifier", str(verifier),
        )

        claude_registry = self.write_strict_claude_registry()
        selected_home = Path(self.temporary.name) / "claude-selected-home"
        (selected_home / "settings.json").write_text("not-json", encoding="utf-8")
        blocked_policy = self.run_cli(
            "status", "--registry", str(claude_registry), "--provider", "claude",
            "--role-profile", "general", "--account-profile", "claude-selected",
            "--verifier", str(verifier),
        )

        expected_base = {
            "schema_version": 1,
            "event": "profile_status",
            "login_status": "unknown",
            "identity_status": "unknown",
            "usage_status": "usage_unknown",
            "cost_limit_status": "unknown",
            "commands": [],
        }
        for result, provider, account_profile, status in (
            (blocked_binding, "codex", None, "blocked_binding"),
            (blocked_policy, "claude", "claude-selected", "blocked_policy"),
        ):
            with self.subTest(status=status):
                self.assertEqual(4, result.returncode)
                self.assertEqual("", result.stderr)
                self.assertEqual(
                    {
                        **expected_base,
                        "provider": provider,
                        "account_profile": account_profile,
                        "status": status,
                    },
                    json.loads(result.stdout),
                )

    def test_status_redaction(self):
        sentinel = "fixture-private-sentinel"
        registry = self.write_strict_registry()
        verifier = self.make_verifier(stderr=sentinel)
        result = self.strict_status(registry, verifier)
        self.assertEqual(3, result.returncode)
        self.assertNotIn(sentinel, result.stdout + result.stderr)
        self.assertEqual("blocked_verifier", json.loads(result.stdout)["status"])

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
        deployed_source = deployed_registry.read_text(encoding="utf-8")

        for provider, legacy_profile in (
            ("codex", "codex-dotfiles"),
            ("claude", "claude-dotfiles"),
        ):
            with self.subTest(provider=provider):
                self.assertIn(
                    f"{legacy_profile} = '''[accounts.{legacy_profile}]",
                    deployed_source,
                )
                result = self.run_cli(
                    "select",
                    "--registry",
                    str(deployed_registry),
                    "--provider",
                    provider,
                    "--role-profile",
                    "general",
                    "--account-profile",
                    legacy_profile,
                )
                self.assertEqual(4, result.returncode)
                self.assertEqual("", result.stdout)
                self.assertIn("blocked_binding", result.stderr)

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
