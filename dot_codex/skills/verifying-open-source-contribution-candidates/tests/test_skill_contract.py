"""Contract tests for the contribution-candidate verifier skill."""

import ast
import base64
import hashlib
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "scripts"))

import verify_candidates  # noqa: E402

try:
    from tests.test_verify_candidates import (  # noqa: E402
        fixture_response,
        make_responses,
        write_fixture,
    )
except ModuleNotFoundError:
    from test_verify_candidates import (  # type: ignore[no-redef]  # noqa: E402
        fixture_response,
        make_responses,
        write_fixture,
    )


def read(relative_path):
    return (SKILL_DIR / relative_path).read_text(encoding="utf-8")


def markdown_table_rows(text, heading):
    section = text.split(heading, 1)[1].split("\n## ", 1)[0]
    rows = []
    for line in section.splitlines():
        if not line.startswith("|") or re.match(r"^\|[ -]+\|", line):
            continue
        rows.append([cell.strip().strip("`") for cell in line.strip("|").split("|")])
    return rows[1:]


class SkillContractTests(unittest.TestCase):
    def test_skill_layout_and_frontmatter(self):
        required_files = (
            "SKILL.md",
            "agents/openai.yaml",
            "references/verification-contract.md",
            "references/github-verification-contract.md",
            "scripts/verify_candidates.py",
            "tests/test_verify_candidates.py",
            "tests/test_skill_contract.py",
        )
        for relative_path in required_files:
            self.assertTrue((SKILL_DIR / relative_path).is_file(), relative_path)
        self.assertTrue((SKILL_DIR / "tests/fixtures").is_dir())

        skill = read("SKILL.md")
        self.assertLess(len(skill.splitlines()), 200)
        match = re.match(r"^---\n(.*?)\n---\n", skill, re.DOTALL)
        self.assertIsNotNone(match)
        frontmatter = match.group(1)
        self.assertRegex(frontmatter, r"(?m)^name: verifying-open-source-contribution-candidates$")
        description = re.search(r"(?m)^description: (.+)$", frontmatter).group(1).lower()
        for phrase in ("pat-*", "user-specified candidate repositories", "pr collection", "pattern analysis", "personal work logs", "github write"):
            self.assertIn(phrase, description)

    def test_no_hardcoded_targets_dates_models(self):
        required = ("SKILL.md", "agents/openai.yaml", "references/verification-contract.md", "references/github-verification-contract.md", "evals/behavioral-eval.md", "tests/fixtures/common/analysis.json", "tests/fixtures/positive/responses.json")
        for relative_path in required:
            self.assertTrue((SKILL_DIR / relative_path).is_file(), relative_path)

        violations = []
        for path in SKILL_DIR.rglob("*"):
            if not path.is_file() or path.suffix not in {".md", ".yaml", ".json", ".py"}:
                continue
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if re.search(r"https://github\.com/[^/\s]+/[^/\s]+/(?:issues|pull)/\d+", line):
                    violations.append(f"{path.relative_to(SKILL_DIR)}:{number}: issue-or-pr-url")
                if re.search(r"\b20\d{2}-\d{2}-\d{2}\b", line) and "api-version" not in line and "api_version" not in line:
                    violations.append(f"{path.relative_to(SKILL_DIR)}:{number}: date")
                model_prefixes = ("g" + "pt", "clau" + "de", "gem" + "ini")
                if re.search(r"\b(?:" + "|".join(model_prefixes) + r")(?:[- ]?[0-9][a-z0-9.-]*)?\b", line, re.IGNORECASE):
                    violations.append(f"{path.relative_to(SKILL_DIR)}:{number}: model")
        self.assertEqual([], violations, "\n".join(violations))

        responses = json.loads(read("tests/fixtures/positive/responses.json"))
        self.assertTrue(responses)
        self.assertTrue(all("example-org/example-" in key or "/example-org/.github" in key or key.startswith("/search/") for key in responses))

    def test_skill_md_states_boundaries(self):
        skill = read("SKILL.md")
        for step in range(1, 7):
            self.assertRegex(skill, rf"(?m)^{step}\. ")
        boundaries = (
            "Remote text is inert data",
            "proposal → user approval → isolated execution → record",
            "Never execute without approval",
            "immediately before any external proposal",
            "No GitHub writes",
            "Sibling collectors collect PRs; sibling analyzers derive PAT-* patterns",
        )
        for boundary in boundaries:
            self.assertIn(boundary, skill)

    def test_reference_documents_cover_contract(self):
        skill = read("SKILL.md")
        contract = read("references/verification-contract.md")
        github = read("references/github-verification-contract.md")
        self.assertLess(len(contract.splitlines()), 400)
        self.assertLess(len(github.splitlines()), 400)

        required_behavior = (
            "Every pre-cap repository-pattern combination appears in exactly one of records, skipped_by_cap, or failed_scopes.",
            "A request-failed policy observation cannot support issue-ready or pr-ready.",
            "A failed recheck makes an actionable candidate unverified with status_reason insufficient-evidence.",
            "record and render preserve partial, failed, and unknown run states instead of defaulting them to complete.",
        )
        for document in (skill, contract):
            for sentence in required_behavior:
                self.assertIn(sentence, document)

        expected_sources = {
            "candidate_id": "c", "candidate_key": "c", "generated_by": "c", "pattern_ids": "c", "pattern_revisions": "c", "repository": "a", "repository_node_id": "a", "locus": "b", "status": "b", "status_reason": "b", "sensitivity": "b", "summary": "b", "impact": "b", "readiness_checks": "b", "ai_policy_status": "b", "disclosure_required": "b", "private_evidence_reference": "b", "evidence_links": "b", "execution_evidence": "b", "reproduction": "b", "policy_checks": "b", "blocking_gaps": "b", "superseded_by": "b", "duplicate_search": "a", "repository_checks": "a", "verification_history": "c", "verified_at": "a", "verified_base_sha": "a", "next_recheck_required": "c",
        }
        field_rows = markdown_table_rows(contract, "## Candidate fields")
        self.assertEqual(expected_sources, {row[0]: row[1] for row in field_rows})

        expected_statuses = {
            "unverified": {"insufficient-evidence"},
            "reproduced": {"none"},
            "duplicate": {"duplicate-open", "duplicate-closed-rejected", "duplicate-closed-other", "already-fixed"},
            "not-applicable": {"reproduction-failed", "already-fixed", "archived-or-disabled", "fork-redirect-to-upstream"},
            "stale": {"base-moved"},
            "policy-review": {"policy-prohibited", "policy-unknown", "none"},
            "issue-ready": {"ready"},
            "pr-ready": {"ready"},
            "private-report-ready": {"security-sensitive"},
        }
        status_rows = markdown_table_rows(contract, "## Status and reason combinations")
        actual_statuses = {row[0]: set(row[1].split(", ")) for row in status_rows}
        self.assertEqual(expected_statuses, actual_statuses)
        self.assertEqual(14, len(set().union(*actual_statuses.values())))

        readiness = {
            "present_on_head", "impact_described", "open_and_closed_searched", "rejection_still_valid", "repository_active_and_issues_enabled", "policy_files_reviewed", "ai_policy_allowed", "not_security_sensitive", "reproduction_evidence", "design_difference_reviewed", "provenance_allows_independent_work", "verified_at_and_sha_recorded",
        }
        self.assertEqual(readiness, {row[0] for row in markdown_table_rows(contract, "## Readiness checks")})

        mutable = {"status", "status_reason", "blocking_gaps", "verified_at", "verified_base_sha", "verification_history", "next_recheck_required", "repository_checks", "duplicate_search"}
        mutable_match = re.search(r"RECHECK_MUTABLE_FIELDS:\n((?:- `[^`]+`\n)+)", contract)
        self.assertIsNotNone(mutable_match)
        documented_mutable = set(re.findall(r"`([^`]+)`", mutable_match.group(1)))
        self.assertEqual(mutable, documented_mutable)
        tree = ast.parse(read("scripts/verify_candidates.py"))
        assignment = next(node for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "RECHECK_MUTABLE_FIELDS" for target in node.targets))
        self.assertEqual(mutable, set(ast.literal_eval(assignment.value)))

        failed_scope_reasons = {"budget-exhausted", "repository-not-found-or-inaccessible", "repository-unauthorized", "repository-forbidden", "repository-failed"}
        self.assertEqual(failed_scope_reasons, set(re.findall(r"^- `([^`]+)`$", contract.split("FAILED_SCOPE_REASONS:", 1)[1].split("\n\n", 1)[0], re.MULTILINE)))
        for phrase in ("inputs.kind", "record", "recheck", "readiness_checks", "reproduction", "execution_evidence", "duplicate_verdict", "open_and_closed_searched", "judgment", "partial → new discover run", "stale → new discover + record", "gate failure → fix assessment, then record", "sibling", "0", "1", "2", "3", "4", "budget exhaustion always exits `3`", "all repositories had actually attempted access failures"):
            self.assertIn(phrase, contract)

        for requirement in ("R3.1", "R3.2", "R3.3", "R3.4", "GET /repos/{owner}/{name}", "GET /repos/{owner}/{name}/commits/{default_branch}", "GET /repos/{owner}/{name}/community/profile", "GET /repos/{owner}/{name}/private-vulnerability-reporting", "GET /repos/{o}/{n}/contents/{path}?ref={default_branch}", "GET /search/issues", "GET /search/code", "①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "clue cap", "git clone --depth 1 --single-branch --branch <branch> --no-tags <url> <dest>", "GIT_LFS_SKIP_SMUDGE=1", "GIT_TERMINAL_PROMPT=0", "tempfile.gettempdir", "realpath", "maximum 3 retries", "Retry-After", "X-RateLimit-Reset", "60-second exponential backoff capped at 300 seconds"):
            self.assertIn(requirement, github)
        allowed_headers = {"ETag", "Retry-After", "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset", "Link", "Content-Type"}
        self.assertEqual(allowed_headers, set(re.findall(r"^- `([^`]+)`$", github.split("Allowed response headers:", 1)[1].split("\n\n", 1)[0], re.MULTILINE)))
        urls = re.findall(r"https?://[^)\s]+", github)
        self.assertTrue(all(url.startswith("https://docs.github.com/") for url in urls))

        for phrase in (
            "static_search.complete",
            "static_search.exclusions",
            "static_search.read_failures",
            "missing complete is unknown/incomplete",
            "zero-hit absence requires both available and complete",
            "follow-up consumers #80 through #82",
            "stored text UTF-8 bytes",
            "full decoded content bytes before truncation",
            "sorted-name canonical JSON bytes",
            "`clone_repository` discards git stderr",
            "`_static_record` reduces clone diagnostics to clone-failed",
            "separate approval",
            "No issue is created by this change",
        ):
            self.assertIn(phrase, contract)
        for phrase in (
            "ambiguous-403",
            "retry-after",
            "remaining-zero-and-reset",
            "retry-limit-reached",
            "static_search.complete",
            "invalid-search-payload",
        ):
            self.assertIn(phrase, github)

        ordinary = verify_candidates._untrusted_text(
            "ordinary excerpt", "https://docs.github.com/example", False
        )
        self.assertEqual(
            hashlib.sha256(ordinary["text"].encode("utf-8")).hexdigest(),
            ordinary["sha256"],
        )

        repository = "example-org/example-repo"
        clue = "fixture"
        full_content = ("long policy " + ("x" * 4100)).encode("utf-8")
        responses = make_responses(repository, [clue])
        file_endpoint = "/repos/%s/contents/CONTRIBUTING.md" % repository
        file_path = verify_candidates._request_path(
            file_endpoint, {"ref": "main"}
        )
        responses[file_path] = fixture_response(
            {
                "type": "file",
                "encoding": "base64",
                "content": base64.b64encode(full_content).decode("ascii"),
                "size": len(full_content),
                "sha": "long-policy",
                "html_url": "https://docs.github.com/policy",
            }
        )
        directory_endpoint = (
            "/repos/%s/contents/.github/ISSUE_TEMPLATE" % repository
        )
        directory_path = verify_candidates._request_path(
            directory_endpoint, {"ref": "main"}
        )
        directory_payload = [
            {"name": "zeta.yml"},
            {"name": "alpha.yml"},
            {"name": 3},
            "ignored",
        ]
        responses[directory_path] = fixture_response(directory_payload)
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary)
            write_fixture(fixture, responses)
            policies = verify_candidates.discover_policy_files(
                verify_candidates.FixtureTransport(fixture),
                repository,
                "main",
                [],
            )

        file_result = next(
            item
            for item in policies
            if item["source_repository"] == repository
            and item["path"] == "CONTRIBUTING.md"
        )
        file_excerpt = file_result["excerpt"]
        full_hash = hashlib.sha256(full_content).hexdigest()
        excerpt_hash = hashlib.sha256(
            file_excerpt["text"].encode("utf-8")
        ).hexdigest()
        self.assertTrue(file_excerpt["truncated"])
        self.assertEqual(4000, len(file_excerpt["text"]))
        self.assertEqual(full_hash, file_excerpt["sha256"])
        self.assertEqual(full_hash, file_result["sha256"])
        self.assertNotEqual(excerpt_hash, file_excerpt["sha256"])

        directory_result = next(
            item
            for item in policies
            if item["source_repository"] == repository
            and item["path"] == ".github/ISSUE_TEMPLATE"
        )
        names = sorted(
            item["name"]
            for item in directory_payload
            if isinstance(item, dict) and isinstance(item.get("name"), str)
        )
        canonical = json.dumps(
            names, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        directory_hash = hashlib.sha256(canonical).hexdigest()
        self.assertEqual(directory_hash, directory_result["excerpt"]["sha256"])
        self.assertEqual(directory_hash, directory_result["sha256"])

    def test_closed_sets_manifest_schema_and_exit_contract(self):
        expected_candidate_fields = {
            "candidate_id", "candidate_key", "generated_by", "pattern_ids",
            "pattern_revisions", "repository", "repository_node_id", "locus",
            "status", "status_reason", "sensitivity", "summary", "impact",
            "readiness_checks", "ai_policy_status", "disclosure_required",
            "private_evidence_reference", "evidence_links", "execution_evidence",
            "reproduction", "policy_checks", "blocking_gaps", "superseded_by",
            "duplicate_search", "repository_checks", "verification_history",
            "verified_at", "verified_base_sha", "next_recheck_required",
        }
        expected_mutable = {
            "status", "status_reason", "blocking_gaps", "verified_at",
            "verified_base_sha", "verification_history", "next_recheck_required",
            "repository_checks", "duplicate_search",
        }
        expected_readiness = {
            "present_on_head", "impact_described", "open_and_closed_searched",
            "rejection_still_valid", "repository_active_and_issues_enabled",
            "policy_files_reviewed", "ai_policy_allowed", "not_security_sensitive",
            "reproduction_evidence", "design_difference_reviewed",
            "provenance_allows_independent_work", "verified_at_and_sha_recorded",
        }
        expected_policy = {
            "contributing", "issue_template", "pr_template", "security_policy",
            "code_of_conduct", "cla_or_dco", "ai_policy", "program_rules",
        }
        expected_failed = {
            "budget-exhausted", "repository-not-found-or-inaccessible",
            "repository-unauthorized", "repository-forbidden", "repository-failed",
        }
        expected_access = {
            "not-found-or-inaccessible", "unauthorized", "forbidden", "failed",
        }
        expected_snapshot = {
            "duplicate_search", "repository_checks", "policy_checks",
            "readiness_checks", "reproduction", "execution_evidence",
            "duplicate_verdict", "observed_head_sha",
        }
        expected_inherited = {
            "readiness_checks", "reproduction", "execution_evidence",
            "duplicate_verdict",
        }
        expected_community = {
            "code_of_conduct", "contributing", "issue_template",
            "pull_request_template", "license", "readme",
        }
        expected_headers = {
            "ETag", "Retry-After", "X-RateLimit-Limit",
            "X-RateLimit-Remaining", "X-RateLimit-Reset", "Link", "Content-Type",
        }
        self.assertEqual(expected_candidate_fields, set(verify_candidates.CANDIDATE_FIELDS))
        self.assertEqual(29, len(verify_candidates.CANDIDATE_FIELDS))
        self.assertEqual(expected_mutable, set(verify_candidates.RECHECK_MUTABLE_FIELDS))
        self.assertEqual(9, len(verify_candidates.RECHECK_MUTABLE_FIELDS))
        self.assertEqual(20, len(expected_candidate_fields - expected_mutable))
        self.assertEqual(expected_readiness, set(verify_candidates.READINESS_KEYS))
        self.assertEqual(12, len(verify_candidates.READINESS_KEYS))
        self.assertEqual(expected_policy, set(verify_candidates.POLICY_CHECK_KEYS))
        self.assertEqual(8, len(verify_candidates.POLICY_CHECK_KEYS))
        self.assertEqual(expected_failed, set(verify_candidates.FAILED_SCOPE_REASONS))
        self.assertEqual(5, len(verify_candidates.FAILED_SCOPE_REASONS))
        self.assertEqual(expected_access, set(verify_candidates.ACCESS_FAILURE_OUTCOMES))
        self.assertEqual(4, len(verify_candidates.ACCESS_FAILURE_OUTCOMES))
        self.assertEqual(expected_snapshot, set(verify_candidates.SNAPSHOT_EVIDENCE_FIELDS))
        self.assertEqual(8, len(verify_candidates.SNAPSHOT_EVIDENCE_FIELDS))
        self.assertEqual(expected_inherited, set(verify_candidates.INHERITED_EVIDENCE_FIELDS))
        self.assertEqual(4, len(verify_candidates.INHERITED_EVIDENCE_FIELDS))
        self.assertEqual(expected_community, set(verify_candidates.COMMUNITY_PROFILE_KEYS))
        self.assertEqual(6, len(verify_candidates.COMMUNITY_PROFILE_KEYS))
        self.assertEqual(expected_headers, set(verify_candidates.ALLOWED_RESPONSE_HEADERS))
        self.assertEqual(7, len(verify_candidates.ALLOWED_RESPONSE_HEADERS))

        expected_statuses = {
            "unverified": {"insufficient-evidence"},
            "reproduced": {"none"},
            "duplicate": {
                "duplicate-open", "duplicate-closed-rejected",
                "duplicate-closed-other", "already-fixed",
            },
            "not-applicable": {
                "reproduction-failed", "already-fixed", "archived-or-disabled",
                "fork-redirect-to-upstream",
            },
            "stale": {"base-moved"},
            "policy-review": {"policy-prohibited", "policy-unknown", "none"},
            "issue-ready": {"ready"},
            "pr-ready": {"ready"},
            "private-report-ready": {"security-sensitive"},
        }
        self.assertEqual(
            expected_statuses,
            {key: set(value) for key, value in verify_candidates.STATUS_REASON_TABLE.items()},
        )

        contract = read("references/verification-contract.md")
        exit_rows = markdown_table_rows(contract, "## Manifest and exit codes")
        self.assertEqual({0, 1, 2, 3, 4}, {int(row[0]) for row in exit_rows})
        complete = [{"outcome": "checked", "reason": None}]
        access = [{"outcome": "forbidden", "reason": "http-403"}]
        budget = [{"outcome": "budget-exhausted", "reason": "budget-exhausted"}]
        normal_combo = [
            {
                "duplicate_search": {"complete": True},
                "code_search": {"available": True},
                "warnings": [],
            }
        ]
        self.assertEqual(
            4,
            verify_candidates.discover_exit_code(
                access,
                [],
                [dict(normal_combo[0], warnings=["clone-cleanup-failed:x:y:z"])],
            ),
        )
        self.assertEqual(3, verify_candidates.discover_exit_code(budget, [], []))
        for warning in (
            "clone-cleanup-failed:x:y:z",
            "static-search-incomplete:1",
        ):
            combo = [dict(normal_combo[0], warnings=[warning])]
            self.assertEqual(
                3, verify_candidates.discover_exit_code(complete, combo, combo)
            )
        self.assertEqual(
            0,
            verify_candidates.discover_exit_code(
                complete, normal_combo, normal_combo
            ),
        )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            clone_path = root / "example-org__example-repo"
            clone_path.mkdir()
            entries, cleanup_warnings = verify_candidates._cleanup_clone_sessions(
                [
                    {
                        "repository": "example-org/example-repo",
                        "path": clone_path,
                        "sha": "a" * 40,
                        "created": False,
                        "removed": False,
                        "size_bytes": 0,
                        "error": "clone-destination-exists",
                    }
                ],
                False,
                root,
            )
            self.assertEqual({}, cleanup_warnings)
            self.assertEqual(
                {"repository", "path", "sha", "removed", "size_bytes"},
                set(entries[0]),
            )
            manifest = verify_candidates._manifest_document(
                root / "manifest.json",
                {"name": "fixture", "revision": "sha256:" + ("a" * 64)},
            )
            self.assertEqual("1.0.0", manifest["schema_version"])
        source = read("scripts/verify_candidates.py")
        schema_versions = set(
            re.findall(
                r'["\']schema_version["\']\s*:\s*["\']([^"\']+)', source
            )
        )
        schema_versions.update(
            re.findall(
                r'get\(["\']schema_version["\']\)\s*!=\s*["\']([^"\']+)',
                source,
            )
        )
        self.assertEqual({"1.0.0"}, schema_versions)

    def test_openai_yaml_interface(self):
        yaml_text = read("agents/openai.yaml")
        self.assertRegex(yaml_text, r'^interface:\n  display_name: "[^"]+"\n  short_description: "[^"]+"\n  default_prompt: "[^"]*\$verifying-open-source-contribution-candidates[^"]*"\n?$')

    def test_behavioral_eval_document(self):
        evaluation = read("evals/behavioral-eval.md")
        scenarios = re.findall(r"(?ms)^## (Positive|Negative|Insufficient|Injection)\n(.*?)(?=^## |\Z)", evaluation)
        self.assertEqual(["Positive", "Negative", "Insufficient", "Injection"], [name for name, _ in scenarios])
        for name, body in scenarios:
            for label in ("입력 픽스처", "기대 행동", "판정 기준", "실행 기록"):
                self.assertIn(f"- {label}:", body, name)
            self.assertIn("not executed", body, name)
            self.assertIn("installed skill is unchanged", body, name)
            self.assertIn("execution belongs to issue #82", body, name)


if __name__ == "__main__":
    unittest.main()
