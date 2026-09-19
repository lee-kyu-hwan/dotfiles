import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_DIR / "scripts"
FIX_QUOTE = "Stop autofixing reordered then calls because the fix changes runtime semantics"
SAFE_QUOTE = "the fixer was removed since it cannot preserve the original behaviour safely"


def pr_record(pr_id, repository, number, body, title=None, files=None, reviews=None, timeline=None):
    title = title or "Change " + str(number)
    return {
        "identity_status": "resolved",
        "record_key": "github-pr:node-" + str(number),
        "pr_id": pr_id,
        "pull_request_node_id": "node-" + str(number),
        "repository": {"full_name": repository, "node_id": "repo-" + repository},
        "pull_request": {
            "number": number,
            "url": "https://github.com/" + repository + "/pull/" + str(number),
            "title": title,
            "normalized_state": "merged",
            "created_at": "2026-08-01T00:00:00Z",
            "closed_at": "2026-08-02T00:00:00Z",
            "changed_files_count": len(files or []),
            "commits_count": 1,
            "labels": [],
        },
        "author": {"login": "contributor", "normalized_role": "contributor"},
        "sources": [{"source_key": "recent-closed", "observations": [{"run_id": "run-1"}]}],
        "state_history": [{"state": "merged"}],
        "evidence_snapshot": {
            "body_excerpt": body,
            "changed_files": files or [],
            "commits": [{"message": title + "\n\nDetails"}],
            "issue_comments": [],
            "reviews": reviews or [],
            "review_comments": [],
            "timeline_events": timeline or [],
            "linked_issues": [],
            "partial_categories": [],
        },
    }


def fixture_corpus():
    return {
        "schema_version": "1.0.0",
        "generated_by": {"name": "fixture-collector", "revision": "fixture-v1"},
        "records": [
            pr_record(
                "PR-001",
                "acme/plugin-a",
                10,
                "<!-- template hint -->\r\n" + FIX_QUOTE + ".",
                files=[
                    {"path": "package-lock.json", "status": "modified", "additions": 1,
                     "deletions": 1, "change_excerpt": "LOCKFILE-CONTENT"},
                    {"path": "lib/rules/prefer-catch.js", "status": "modified", "additions": 1,
                     "deletions": 3, "change_excerpt": "@@ -1,3 +1,1 @@\n-  fixable: 'code',\n+  fixable: null,"},
                ],
                timeline=[
                    {"kind": "cross-referenced", "author": "someone", "excerpt": "PRIVATE-XREF-TITLE",
                     "source": {"issue": {"html_url": "https://github.com/private/repo/issues/1"}}},
                    {"kind": "labeled", "author": "maintainer", "excerpt": "accepted"},
                ],
            ),
            pr_record(
                "PR-002",
                "acme/plugin-b",
                20,
                "Reports only.",
                reviews=[{"author": "maintainer", "state": "APPROVED",
                          "excerpt": "Yes, " + SAFE_QUOTE + ".", "html_url": "https://example.invalid/r"}],
            ),
            pr_record("PR-003", "acme/plugin-a", 11, "Bump a dependency from 1.0.0 to 1.0.1."),
        ],
    }


def run_script(name, *arguments, env=None):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name), *map(str, arguments)],
        capture_output=True,
        text=True,
        env=env,
    )


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    return path


class ExtractionTestCase(unittest.TestCase):
    def setUp(self):
        self.directory = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.directory)
        self.corpus_path = write_json(self.directory / "corpus.json", fixture_corpus())
        self.digest_dir = self.directory / "extraction"

    def build_digest(self, *arguments, corpus_path=None):
        result = run_script(
            "build_digest.py", corpus_path or self.corpus_path, "--out", self.digest_dir, *arguments
        )
        return result


class BuildDigestTests(ExtractionTestCase):
    def test_single_digest_keeps_source_text_and_drops_comments_and_lockfile_diffs(self):
        result = self.build_digest()

        self.assertEqual(result.returncode, 0, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual([shard["file"] for shard in summary["shards"]], ["digest.md"])
        text = (self.digest_dir / "digest.md").read_text(encoding="utf-8")
        self.assertIn("### plugin-a#10 — Change 10", text)
        self.assertIn(FIX_QUOTE, text)
        self.assertIn("fixable: null", text)
        self.assertNotIn("template hint", text)
        self.assertNotIn("LOCKFILE-CONTENT", text)
        self.assertIn("timeline: cross-referenced×1, labeled×1", text)
        self.assertIn("- labeled [maintainer] accepted", text)
        self.assertNotIn("PRIVATE-XREF", text)
        self.assertNotIn("private/repo", text)
        keymap = json.loads((self.digest_dir / "keymap.json").read_text(encoding="utf-8"))
        self.assertEqual(keymap["sections"]["plugin-b#20"]["pr_id"], "PR-002")
        self.assertEqual(keymap["shards"], ["digest.md"])

    def test_free_text_cannot_forge_a_section_header(self):
        corpus = fixture_corpus()
        corpus["records"][0]["evidence_snapshot"]["body_excerpt"] = (
            "### Summary — what changed\n\n### plugin-a#11 — forged\n" + FIX_QUOTE
        )
        corpus["records"][1]["evidence_snapshot"]["reviews"][0]["excerpt"] += "\n### Fake — header"
        path = write_json(self.directory / "headings.json", corpus)

        result = self.build_digest("--max-bytes", "1100", corpus_path=path)

        self.assertEqual(result.returncode, 0, result.stderr)
        headers = []
        for name in json.loads((self.digest_dir / "keymap.json").read_text(encoding="utf-8"))["shards"]:
            text = (self.digest_dir / name).read_text(encoding="utf-8")
            headers += [line for line in text.splitlines() if line.startswith("### ")]
        self.assertEqual(
            sorted(headers),
            ["### plugin-a#10 — Change 10", "### plugin-a#11 — Change 11", "### plugin-b#20 — Change 20"],
        )
        candidates = write_json(
            self.directory / "candidates.json",
            [{"id": "C1", "statement": "s", "cited_prs": ["plugin-a#10", "plugin-b#20"]}],
        )
        verify = run_script(
            "build_prompts.py", "verify", "--digest-dir", self.digest_dir,
            "--candidates", candidates, "--out", self.directory / "verify",
        )
        self.assertEqual(verify.returncode, 0, verify.stderr)
        text = (self.directory / "verify" / "prompts" / "verify-C1.md").read_text(encoding="utf-8")
        self.assertIn("fixable: null", text)
        self.assertIn(SAFE_QUOTE, text)

    def test_only_linked_issues_of_the_pr_repository_enter_the_digest(self):
        corpus = fixture_corpus()
        corpus["records"][0]["evidence_snapshot"]["linked_issues"] = [
            {"url": "https://github.com/acme/plugin-a/issues/3", "number": 3,
             "title": "Autofix reorders then calls", "body_excerpt": "PUBLIC-ISSUE-BODY"},
            {"url": "https://github.com/private-org/internal/issues/22", "number": 22,
             "title": "INTERNAL-SECRET-TITLE", "body_excerpt": "INTERNAL-SECRET-BODY"},
        ]
        path = write_json(self.directory / "linked.json", corpus)

        result = self.build_digest(corpus_path=path)

        self.assertEqual(result.returncode, 0, result.stderr)
        text = (self.digest_dir / "digest.md").read_text(encoding="utf-8")
        self.assertIn("- #3 Autofix reorders then calls", text)
        self.assertIn("PUBLIC-ISSUE-BODY", text)
        self.assertNotIn("INTERNAL-SECRET", text)

    def test_keys_fall_back_to_owner_when_repository_names_collide(self):
        corpus = fixture_corpus()
        corpus["records"][1]["repository"]["full_name"] = "other/plugin-a"
        corpus["records"][1]["pull_request"]["url"] = "https://github.com/other/plugin-a/pull/20"
        path = write_json(self.directory / "collide.json", corpus)

        result = self.build_digest(corpus_path=path)

        self.assertEqual(result.returncode, 0, result.stderr)
        keymap = json.loads((self.digest_dir / "keymap.json").read_text(encoding="utf-8"))
        self.assertEqual(
            sorted(keymap["sections"]),
            ["acme/plugin-a#10", "acme/plugin-a#11", "other/plugin-a#20"],
        )

    def test_over_budget_digest_is_sharded_across_repositories_not_by_repository(self):
        corpus = fixture_corpus()
        corpus["records"].append(pr_record("PR-004", "acme/plugin-a", 12, "x" * 600))
        corpus["records"].append(pr_record("PR-005", "acme/plugin-b", 21, "y" * 600))
        path = write_json(self.directory / "large.json", corpus)
        self.digest_dir.mkdir()
        (self.digest_dir / "digest.md").write_text("stale", encoding="utf-8")

        result = self.build_digest("--max-bytes", "2400", corpus_path=path)

        self.assertEqual(result.returncode, 0, result.stderr)
        shards = json.loads(result.stdout)["shards"]
        self.assertGreater(len(shards), 1)
        self.assertFalse((self.digest_dir / "digest.md").exists())
        keys = [key for shard in shards for key in shard["keys"]]
        self.assertEqual(sorted(keys), sorted(set(keys)))
        self.assertEqual(len(keys), 5)
        first = shards[0]["keys"]
        self.assertEqual({key.split("#")[0] for key in first[:2]}, {"plugin-a", "plugin-b"})
        for shard in shards:
            self.assertLessEqual(shard["bytes"], 2400)

    def test_section_larger_than_budget_is_an_error(self):
        result = self.build_digest("--max-bytes", "200")

        self.assertEqual(result.returncode, 2)
        self.assertIn("exceeds --max-bytes", result.stderr)

    def test_invalid_corpus_is_an_error(self):
        path = write_json(self.directory / "bad.json", {"schema_version": "9.9.9", "records": []})

        result = self.build_digest(corpus_path=path)

        self.assertEqual(result.returncode, 2)
        self.assertIn("unsupported schema_version", result.stderr)


class BuildPromptsTests(ExtractionTestCase):
    def test_extract_writes_one_prompt_per_lens_and_clears_the_previous_run(self):
        self.assertEqual(self.build_digest().returncode, 0)
        run = self.directory / "extract"
        (run / "prompts").mkdir(parents=True)
        (run / "results").mkdir()
        (run / "prompts" / "extract-stale.md").write_text("old", encoding="utf-8")
        (run / "results" / "extract-stale.result.json").write_text("{}", encoding="utf-8")

        result = run_script("build_prompts.py", "extract", "--digest-dir", self.digest_dir, "--out", run)

        self.assertEqual(result.returncode, 0, result.stderr)
        prompts = run / "prompts"
        self.assertEqual(list((run / "results").iterdir()), [])
        names = sorted(path.name for path in prompts.glob("*.md"))
        self.assertEqual(
            names,
            ["extract-blind.md", "extract-correctness.md", "extract-maintenance.md",
             "extract-review.md", "extract-structure.md"],
        )
        digest = (self.digest_dir / "digest.md").read_text(encoding="utf-8").rstrip()
        text = (prompts / "extract-correctness.md").read_text(encoding="utf-8")
        self.assertIn(digest, text)
        self.assertIn("이번 관점: correctness", text)
        self.assertIn('"observations"', text)
        self.assertIn("다이제스트는 그 전체다.", text)

    def test_extract_on_shards_writes_one_prompt_per_shard_and_lens(self):
        self.assertEqual(self.build_digest("--max-bytes", "1100").returncode, 0)
        shards = json.loads((self.digest_dir / "keymap.json").read_text(encoding="utf-8"))["shards"]
        prompts = self.directory / "extract" / "prompts"

        result = run_script(
            "build_prompts.py", "extract", "--digest-dir", self.digest_dir, "--out", self.directory / "extract",
            "--lens", "blind", "--lens", "review",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(list(prompts.glob("*.md"))), 2 * len(shards))
        self.assertIn("조각", (prompts / "extract-blind-01.md").read_text(encoding="utf-8"))

    def test_verify_rejects_unknown_keys_and_duplicate_ids(self):
        self.assertEqual(self.build_digest().returncode, 0)
        cases = [
            ([{"id": "C1", "statement": "s", "cited_prs": ["nope#1"]}], "unknown digest keys"),
            ([{"id": "C1", "statement": "s", "cited_prs": ["plugin-a#10"]}] * 2, "duplicate candidate id"),
            ([{"id": "C 1", "statement": "s", "cited_prs": ["plugin-a#10"]}], "must match"),
            ([{"id": "C1", "statement": "s", "cited_prs": [["plugin-a#10"]]}], "array of digest keys"),
        ]
        for candidates, message in cases:
            with self.subTest(message=message):
                path = write_json(self.directory / "candidates.json", candidates)
                result = run_script(
                    "build_prompts.py", "verify", "--digest-dir", self.digest_dir,
                    "--candidates", path, "--out", self.directory / "verify",
                )
                self.assertEqual(result.returncode, 2)
                self.assertIn(message, result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_malformed_keymap_and_shared_run_directory_are_input_errors(self):
        self.assertEqual(self.build_digest().returncode, 0)
        run = self.directory / "run"
        self.assertEqual(
            run_script("build_prompts.py", "extract", "--digest-dir", self.digest_dir, "--out", run).returncode, 0
        )
        candidates = write_json(
            self.directory / "candidates.json",
            [{"id": "C1", "statement": "s", "cited_prs": ["plugin-a#10", "plugin-b#20"]}],
        )

        shared = run_script(
            "build_prompts.py", "verify", "--digest-dir", self.digest_dir, "--candidates", candidates, "--out", run
        )
        write_json(self.digest_dir / "keymap.json", [])
        broken = run_script(
            "build_prompts.py", "extract", "--digest-dir", self.digest_dir, "--out", self.directory / "other"
        )

        self.assertEqual(shared.returncode, 2)
        self.assertIn("use a separate run directory", shared.stderr)
        self.assertTrue(any((run / "prompts").glob("extract-*.md")))
        self.assertEqual(broken.returncode, 2)
        self.assertIn("not a build_digest.py keymap", broken.stderr)

    def test_sharded_verify_prompt_carries_cited_sections_and_a_title_index(self):
        self.assertEqual(self.build_digest("--max-bytes", "1100").returncode, 0)
        candidates = write_json(
            self.directory / "candidates.json",
            [{"id": "C1", "statement": "Remove unsafe fixers", "cited_prs": ["plugin-a#10", "plugin-b#20"]}],
        )

        result = run_script(
            "build_prompts.py", "verify", "--digest-dir", self.digest_dir,
            "--candidates", candidates, "--out", self.directory / "verify",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        text = (self.directory / "verify" / "prompts" / "verify-C1.md").read_text(encoding="utf-8")
        self.assertIn(FIX_QUOTE, text)
        self.assertIn(SAFE_QUOTE, text)
        self.assertIn("- plugin-a#11 — Change 11 (merged)", text)
        self.assertNotIn("Bump a dependency", text)
        self.assertIn('"id": "C1"', text)


class CheckExtractionTests(ExtractionTestCase):
    def check(self, *results):
        paths = [write_json(self.directory / ("result-" + str(index) + ".json"), result)
                 for index, result in enumerate(results)]
        return run_script("check_extraction.py", self.corpus_path, *paths)

    def test_quotes_must_be_verbatim_source_text(self):
        result = self.check({"observations": [
            {"pr": "plugin-a#10", "quote": FIX_QUOTE.replace(" because", "\n   because")},
            {"pr": "plugin-a#10", "quote": "Stop autofixing reordered ... runtime semantics"},
            {"pr": "plugin-a#10", "quote": "url: https://github.com/acme/plugin-a/pull/10"},
            {"pr": "plugin-b#20", "quote": "[maintainer · APPROVED]"},
            {"pr": "plugin-a#10", "quote": "fixable: null"},
            {"pr": "plugin-z#99", "quote": FIX_QUOTE},
        ]})

        self.assertEqual(result.returncode, 1)
        report = json.loads(result.stdout)
        self.assertEqual(report["totals"], {"verified": 1, "total": 6})
        reasons = [failure["reason"] for failure in report["files"][0]["failures"]]
        self.assertEqual(reasons, ["not-verbatim", "not-verbatim", "not-verbatim", "length", "unknown-key"])
        self.assertEqual(report["verified_evidence"][0]["pr_id"], "PR-001")

    def test_extraction_pattern_is_grounded_only_by_two_verified_supporting_prs(self):
        result = self.check({"patterns": [
            {"title": "grounded", "evidence": [
                {"pr": "plugin-a#10", "role": "supports", "quote": FIX_QUOTE},
                {"pr": "plugin-b#20", "role": "supports", "quote": SAFE_QUOTE},
            ]},
            {"title": "one bad quote", "evidence": [
                {"pr": "plugin-a#10", "role": "supports", "quote": FIX_QUOTE},
                {"pr": "plugin-b#20", "role": "supports", "quote": "reworded: " + SAFE_QUOTE},
            ]},
            {"title": "counterexample only", "evidence": [
                {"pr": "plugin-a#10", "role": "supports", "quote": FIX_QUOTE},
                {"pr": "plugin-b#20", "role": "counterexample", "quote": SAFE_QUOTE},
            ]},
        ]})

        report = json.loads(result.stdout)["files"][0]
        self.assertEqual(report["kind"], "extraction")
        self.assertEqual([pattern["grounded"] for pattern in report["patterns"]], [True, False, False])
        self.assertEqual(report["patterns"][0]["repositories"], 2)

    def test_verification_counts_only_verified_checks_that_hold(self):
        result = self.check({
            "id": "C1",
            "verdict": "supported",
            "evidence_checks": [
                {"pr": "plugin-a#10", "holds": True, "quote": FIX_QUOTE},
                {"pr": "plugin-b#20", "holds": False, "quote": SAFE_QUOTE},
            ],
            "counterexamples": [],
        })

        self.assertEqual(result.returncode, 0, result.stderr)
        verification = json.loads(result.stdout)["files"][0]["verification"]
        self.assertEqual(verification["prs"], ["plugin-a#10"])
        self.assertFalse(verification["grounded"])

    def test_malformed_result_shapes_are_reported_not_crashed(self):
        result = self.check(
            {"patterns": [{"title": "odd", "evidence": 3}, "not an object"]},
            {"evidence_checks": [{"pr": ["plugin-a#10"], "holds": True, "quote": FIX_QUOTE}, 7]},
            [{"pr": "plugin-a#10", "quote": None}],
        )

        self.assertEqual(result.returncode, 1)
        self.assertNotIn("Traceback", result.stderr)
        files = json.loads(result.stdout)["files"]
        self.assertEqual(files[0]["patterns"], [{"title": "odd", "prs": [], "repositories": 0, "grounded": False}])
        self.assertEqual([failure["reason"] for failure in files[1]["failures"]], ["unknown-key"])
        self.assertEqual([failure["reason"] for failure in files[2]["failures"]], ["empty-quote"])

    def test_unreadable_result_is_an_input_error(self):
        broken = self.directory / "broken.json"
        broken.write_text("{", encoding="utf-8")

        result = run_script("check_extraction.py", self.corpus_path, broken)

        self.assertEqual(result.returncode, 2)
        self.assertNotIn("Traceback", result.stderr)


class WithoutAgyTests(ExtractionTestCase):
    """The analyzer must run end to end on a machine without agy (#183)."""

    def test_pipeline_produces_a_validated_pattern_with_no_agy_on_path(self):
        empty_bin = self.directory / "bin"
        empty_bin.mkdir()
        env = dict(os.environ, PATH=str(empty_bin), PYTHONDONTWRITEBYTECODE="1")
        self.assertIsNone(shutil.which("agy", path=env["PATH"]))

        digest = run_script("build_digest.py", self.corpus_path, "--out", self.digest_dir, env=env)
        self.assertEqual(digest.returncode, 0, digest.stderr)
        prompts = run_script(
            "build_prompts.py", "extract", "--digest-dir", self.digest_dir,
            "--out", self.directory / "extract", env=env,
        )
        self.assertEqual(prompts.returncode, 0, prompts.stderr)

        # A tool-less sub-agent or the coordinator answers the prompt file.
        answer = write_json(self.directory / "extract" / "results" / "extract-blind.result.json", {"lens": "blind", "patterns": [
            {"title": "Drop unsafe fixers", "evidence": [
                {"pr": "plugin-a#10", "role": "supports", "quote": FIX_QUOTE},
                {"pr": "plugin-b#20", "role": "supports", "quote": SAFE_QUOTE},
            ]},
        ], "observations": [], "rejected": []})
        check = run_script("check_extraction.py", self.corpus_path, answer, env=env)
        self.assertEqual(check.returncode, 0, check.stderr)
        verified = json.loads(check.stdout)["verified_evidence"]

        revision = run_script("validate_corpus.py", "--print-revision", env=env).stdout.strip()
        output = analysis_output(fixture_corpus(), revision, verified)
        output_path = write_json(self.directory / "analysis.json", output)
        validation = run_script(
            "validate_corpus.py", self.corpus_path, "--analysis-output", output_path, env=env
        )
        self.assertEqual(validation.returncode, 0, validation.stderr)


def analysis_output(corpus, revision, verified):
    """Assemble a strict output whose one pattern carries the verified quotes."""
    generator = {"name": "analyzing-open-source-pr-patterns", "revision": revision}
    evidence_ids = sorted({item["pr_id"] for item in verified})
    pattern = {
        "pattern_id": "PAT-001",
        "description": "Remove a fixer that cannot preserve semantics and report instead.",
        "generated_by": generator,
        "evidence_pr_ids": evidence_ids,
        "applicability": ["rules that rewrite code"],
        "counterconditions": ["the rewrite is provably equivalent"],
        "search_clues": ["fixable: 'code'"],
        "expected_tests": ["invalid case keeps output: null"],
        "maintainer_judgment_required": ["whether a partial fixer is acceptable"],
        "source_licenses": [{"pr_id": pr_id, "spdx_id": "MIT"} for pr_id in evidence_ids],
        "provenance_mode": "independent-reimplementation",
        "confidence": {
            "level": "medium",
            "evidence": [item["pr_id"] + ' "' + item["quote"] + '"' for item in verified],
            "limitations": ["fixture"],
        },
        "superseded_by": None,
    }
    records = []
    for input_record in corpus["records"]:
        record = copy.deepcopy(input_record)
        claim = {"value": "Observed", "basis": "fact", "evidence_links": []}
        projection = {
            "change_summary": claim,
            "motivation": claim,
            "review_judgment": claim,
            "closure_reason": {"value": None, "basis": "unknown", "evidence_links": []},
            "files_changed": [],
            "test_evidence": [],
            "pattern_ids": ["PAT-001"] if record["pr_id"] in evidence_ids else [],
            "evidence_links": [],
            "evidence_manifest": {},
            "license_spdx": "MIT",
            "provenance_mode": "independent-reimplementation",
            "confidence": {"level": "low", "evidence": [], "limitations": []},
            "superseded_by": None,
        }
        record["analysis"] = projection
        record["analysis_history"] = [{
            "revision": revision,
            "generated_at": "2026-09-19T00:00:00Z",
            "evidence_manifest": {},
            "conclusion": copy.deepcopy(projection),
        }]
        records.append(record)
    pattern["pattern_history"] = [
        {"revision": revision, "generated_at": "2026-09-19T00:00:00Z", "conclusion": copy.deepcopy(pattern)}
    ]
    return {
        "schema_version": "1.0.0",
        "generated_by": copy.deepcopy(corpus["generated_by"]),
        "analysis_generated_by": generator,
        "records": records,
        "patterns": [pattern],
        "limitations": ["pattern-extraction: 1 lens; executor none (answered in-session)"],
    }


if __name__ == "__main__":
    unittest.main()
