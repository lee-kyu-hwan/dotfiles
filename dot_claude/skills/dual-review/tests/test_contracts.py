import ast
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest


SKILL_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))


def managed_target(source: str) -> str:
    prefix = "dot_claude/skills/"
    if not source.startswith(prefix):
        raise ValueError("skill source required")
    return "~/.claude/skills/" + source[len(prefix):]


class PackagingContractTests(unittest.TestCase):
    def test_arguments(self):
        import review_state
        self.assertEqual(review_state.parse_arguments([], "parent"), {"base": "parent", "rounds": 2})
        self.assertEqual(review_state.parse_arguments(["--base=main", "--rounds", "1"], "parent"), {"base": "main", "rounds": 1})
        with self.assertRaises(ValueError):
            review_state.parse_arguments(["--rounds", "3"], "parent")

    def test_snapshot_uses_parent_only_for_an_omitted_base_and_matches_git(self):
        import review_state
        def git(root, *arguments):
            return subprocess.check_output(["git", *arguments], cwd=root, text=True).strip()
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            subprocess.check_call(["git", "init", "-q"], cwd=root)
            subprocess.check_call(["git", "config", "user.email", "fixture@example.test"], cwd=root)
            subprocess.check_call(["git", "config", "user.name", "Fixture"], cwd=root)
            (root / "changed.py").write_text("first\nold\n", encoding="utf-8")
            subprocess.check_call(["git", "add", "changed.py"], cwd=root)
            subprocess.check_call(["git", "commit", "-qm", "first"], cwd=root)
            first = git(root, "rev-parse", "HEAD")
            (root / "changed.py").write_text("first\nnew\n", encoding="utf-8")
            (root / "added.py").write_text("added\n", encoding="utf-8")
            subprocess.check_call(["git", "add", "changed.py", "added.py"], cwd=root)
            subprocess.check_call(["git", "commit", "-qm", "second"], cwd=root)
            snapshot, parsed = review_state.snapshot_from_repository(root, [])
            self.assertEqual(parsed, {"base": first, "rounds": 2})
            self.assertEqual(snapshot["base_sha"], git(root, "rev-parse", "HEAD^"))
            self.assertEqual(snapshot["head_sha"], git(root, "rev-parse", "HEAD"))
            self.assertEqual(snapshot["files"], git(root, "diff", "--name-only", first, "HEAD").splitlines())
            self.assertEqual(snapshot["diff"], subprocess.check_output(["git", "diff", "--unified=0", first, "HEAD"], cwd=root, text=True))
            self.assertEqual(snapshot["line_ranges"], {"added.py": [[1, 1]], "changed.py": [[2, 2]]})
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            subprocess.check_call(["git", "init", "-q"], cwd=root)
            subprocess.check_call(["git", "config", "user.email", "fixture@example.test"], cwd=root)
            subprocess.check_call(["git", "config", "user.name", "Fixture"], cwd=root)
            (root / "only.py").write_text("only\n", encoding="utf-8")
            subprocess.check_call(["git", "add", "only.py"], cwd=root)
            subprocess.check_call(["git", "commit", "-qm", "initial"], cwd=root)
            head = git(root, "rev-parse", "HEAD")
            snapshot, parsed = review_state.snapshot_from_repository(root, ["--base", head])
            self.assertEqual(parsed["base"], head)
            self.assertEqual(snapshot["base_sha"], head)
            self.assertEqual(snapshot["head_sha"], head)
            self.assertEqual(snapshot["files"], [])

    def test_independence(self):
        import review_state
        started = set()
        class Adapter:
            def __init__(self, expected): self.expected = expected; self.dispatched = []
            def start(self, source, prompt):
                self.assertEqual(source, self.expected); self.dispatched.append(prompt); started.add(source); return prompt
            def read(self, handle):
                self.assertEqual(started, {"claude", "codex"})
                return {"status": "ok", "payload": {"verdict": "ok", "summary": "", "findings": [], "next_steps": []}}
            def assertEqual(self, left, right):
                if left != right: raise AssertionError(f"{left!r} != {right!r}")
        with tempfile.TemporaryDirectory() as temporary_directory:
            adapters = {"claude": Adapter("claude"), "codex": Adapter("codex")}
            snapshot = {"base_sha": "base", "head_sha": "head", "files": ["a.py"], "diff": "diff payload"}
            result = review_state.execute_round_zero(pathlib.Path(temporary_directory), snapshot, adapters)
            run_dir = pathlib.Path(result["run_dir"])
            prompts = {source: (run_dir / f"round0-{source}.prompt").read_text() for source in ("claude", "codex")}
        self.assertEqual(set(prompts), {"claude", "codex"})
        constructed = review_state.build_round_zero_prompts(snapshot)
        for source in ("claude", "codex"):
            self.assertEqual(constructed[source].encode(), adapters[source].dispatched[0].encode())
            self.assertEqual(constructed[source].encode(), prompts[source].encode())
        self.assertNotIn("claude output", prompts["codex"].lower())
        self.assertNotIn("codex output", prompts["claude"].lower())
        self.assertEqual(result["events"][:2], ["started:claude", "started:codex"])
    def test_packaging_contract(self):
        required_paths = [
            "SKILL.md",
            "references/operation.md",
            "references/verification.md",
            "schemas/.gitkeep",
            "scripts/.gitkeep",
            "templates/report.md",
            "tests/test_contracts.py",
        ]
        for relative_path in required_paths:
            self.assertTrue((SKILL_ROOT / relative_path).is_file(), relative_path)

        frontmatter = (SKILL_ROOT / "SKILL.md").read_text().split("---", 2)[1]
        keys = {line.split(":", 1)[0] for line in frontmatter.splitlines() if ":" in line}
        self.assertTrue(
            {
                "name", "version", "description", "argument-hint",
                "disable-model-invocation", "model", "effort",
            }.issubset(keys)
        )
        self.assertEqual(
            managed_target("dot_claude/skills/dual-review/SKILL.md"),
            "~/.claude/skills/dual-review/SKILL.md",
        )
        operation = (SKILL_ROOT / "references/operation.md").read_text()
        self.assertIn("Claude Code 2.1.263", operation)
        for flag in ("-p", "--no-session-persistence", "--permission-mode plan", "--permission-prompts none", "--allowedTools Read,Glob,Grep", "--agent <role>", "--output-format json", "--json-schema <schema>"):
            self.assertIn(flag, operation)
        self.assertIn("stdin", operation)
        self.assertIn("dot_claude/skills/dual-review/SKILL.md", operation)
        self.assertIn("~/.claude/skills/dual-review/SKILL.md", operation)
        verification = (SKILL_ROOT / "references/verification.md").read_text()
        self.assertIn("not configured", verification)

    def test_reviewer_contract(self):
        operation = (SKILL_ROOT / "references/operation.md").read_text()
        expected_roles = {
            "pr-review-toolkit:code-reviewer", "pr-test-analyzer",
            "comment-analyzer", "silent-failure-hunter", "type-design-analyzer",
        }
        self.assertTrue(all(role in operation for role in expected_roles))
        import review_state
        allowed = {"-C", "--sandbox", "--ephemeral", "--model", "-c", "--output-schema", "--output-last-message", "--json"}
        command = review_state.build_codex_command("/repository")
        used_flags = {part for part in command if part.startswith("-")}
        self.assertTrue(used_flags.issubset(allowed))
        self.assertEqual(command[command.index("--sandbox") + 1], "read-only")
        self.assertEqual(review_state.CLAUDE_PRODUCERS, (
            "pr-review-toolkit:code-reviewer", "pr-test-analyzer", "comment-analyzer",
            "silent-failure-hunter", "type-design-analyzer",
        ))
        common = ("claude", "-p", "--no-session-persistence", "--permission-mode", "plan", "--permission-prompts", "none", "--allowedTools", "Read,Glob,Grep")
        producer = review_state.build_claude_command("pr-test-analyzer")
        critique = review_state.build_claude_command(schema_name="critique.schema.json")
        synthesis_command = review_state.build_claude_command(schema_name="synthesis.schema.json")
        self.assertEqual(producer, common + ("--agent", "pr-test-analyzer"))
        self.assertEqual(critique, common + ("--output-format", "json", "--json-schema", (SKILL_ROOT / "schemas/critique.schema.json").read_text(encoding="utf-8")))
        self.assertEqual(synthesis_command, common + ("--output-format", "json", "--json-schema", (SKILL_ROOT / "schemas/synthesis.schema.json").read_text(encoding="utf-8")))
        for command in (producer, critique, synthesis_command):
            flags = [part for part in command if part.startswith("-")]
            self.assertEqual(len(flags), len(set(flags)), command)
        self.assertNotIn("--fresh-context", synthesis_command)
        with self.assertRaises(TypeError):
            review_state.build_claude_command(fresh=True)
        _, critique_adapter, synthesis_adapter = review_state.live_adapters("/repository")
        critique_codex = critique_adapter.command_builder("codex", pathlib.Path("/tmp/last-message"))
        self.assertIn("critique.schema.json", " ".join(critique_codex))
        self.assertEqual(critique_adapter.command_builder("claude", pathlib.Path("/tmp/unused")), critique)
        self.assertEqual(synthesis_adapter.command_builder("fresh-claude", pathlib.Path("/tmp/unused")), synthesis_command)

    def test_schema_contract(self):
        reviewer = json.loads((SKILL_ROOT / "schemas/reviewer.schema.json").read_text())
        expected = {"source", "original_id", "severity", "title", "body", "file", "line_start", "line_end", "finding_confidence", "recommendation"}
        self.assertEqual(set(reviewer["properties"]["findings"]["items"]["required"]), expected)
        self.assertEqual(reviewer["properties"]["findings"]["items"]["properties"]["severity"]["enum"], ["critical", "high", "medium", "low"])

    def test_critique_contract(self):
        critique = json.loads((SKILL_ROOT / "schemas/critique.schema.json").read_text())
        self.assertEqual(set(critique["required"]), {"critiques"})
        entry = critique["properties"]["critiques"]["items"]
        self.assertEqual(set(entry["required"]), {"finding_id", "verdict", "evidence", "new_findings"})
        self.assertEqual(entry["properties"]["verdict"]["enum"], ["유지", "반증됨", "미검증"])
        evidence = entry["properties"]["evidence"]["items"]
        self.assertEqual(set(evidence["required"]), {"file", "line_start", "line_end"})

    def test_synthesis_contract(self):
        synthesis = json.loads((SKILL_ROOT / "schemas/synthesis.schema.json").read_text())
        decision = synthesis["properties"]["decisions"]["items"]
        self.assertEqual(set(decision["required"]), {"classification", "decision_confidence", "rationale", "group_a_finding_ids", "group_b_finding_ids", "claims"})
        self.assertEqual(set(decision["properties"]["classification"]["enum"]), {"합의", "불일치", "단일 출처"})
        self.assertEqual(decision["properties"]["decision_confidence"]["minimum"], 0)
        self.assertEqual(decision["properties"]["decision_confidence"]["maximum"], 1)
        self.assertTrue({"rationale", "group_a_finding_ids", "group_b_finding_ids"}.issubset(decision["required"]))
        self.assertIn("Fresh Claude", (SKILL_ROOT / "references/operation.md").read_text())
        import review_state
        _, _, synthesis_adapter = review_state.live_adapters("/repository")
        command = synthesis_adapter.command_builder("fresh-claude", pathlib.Path("/tmp/unused"))
        self.assertNotIn("codex", command)
        self.assertNotIn("exec", command)
        finding = {"severity": "low", "finding_confidence": .8, "file": "x.py", "line_start": 1, "line_end": 1, "title": "finding", "body": "detail", "recommendation": "fix"}
        class Reviewer:
            def start(self, source, prompt): return source
            def read(self, source): return {"status": "ok", "payload": {"verdict": "ok", "summary": "", "findings": [finding], "next_steps": []}}
        class Synthesizer:
            def start(self, source, prompt): self.prompt = prompt; return prompt
            def read(self, prompt):
                groups = {item["group"]: item["finding_id"] for item in json.loads(prompt)["anonymous_view"]["findings"]}
                return {"status": "ok", "payload": {"decisions": [{"classification": "합의", "decision_confidence": .5, "rationale": "same", "group_a_finding_ids": [groups["A"]], "group_b_finding_ids": [groups["B"]], "claims": {"A": "a", "B": "b"}}]}}
        synthesis = Synthesizer()
        with tempfile.TemporaryDirectory() as temporary_directory:
            review_state.run_dual_review(pathlib.Path(temporary_directory), {"base_sha": "a", "head_sha": "b", "files": ["x.py"]}, {"claude": Reviewer(), "codex": Reviewer()}, synthesis_adapter=synthesis, requested_rounds=1)
        prompt = json.loads(synthesis.prompt)
        self.assertEqual(set(prompt), {"contract", "anonymous_view"})
        self.assertEqual(set(prompt["anonymous_view"]), {"findings", "critiques", "candidate_issues"})

    def test_no_mutation_contract(self):
        import review_state
        source_text = "\n".join(review_state.scan_source_texts(SKILL_ROOT).values())
        blocked = ["gh" + " pr review", "gh" + " pr comment", "gh" + " api"]
        automatic_mutations = ["chez" + "moi apply", "git" + " apply", "sed" + " -i"]
        with tempfile.TemporaryDirectory() as temporary_directory:
            forbidden = pathlib.Path(temporary_directory) / "tokens.txt"
            forbidden.write_text("\n".join(blocked))
            self.assertTrue(forbidden.is_file())
        self.assertTrue(all(token not in source_text for token in blocked + ["code" + "-simplifier"] + automatic_mutations))
        scripts = list((SKILL_ROOT / "scripts").glob("*.py"))
        self.assertGreaterEqual(len(scripts), 1)
        standard_library = set(sys.stdlib_module_names) | {"__future__"}
        for script in scripts:
            imports = ast.parse(script.read_text())
            imported_roots = []
            for node in ast.walk(imports):
                if isinstance(node, ast.Import):
                    imported_roots.extend(alias.name.split(".", 1)[0] for alias in node.names)
                if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    imported_roots.append(node.module.split(".", 1)[0])
            self.assertTrue(all(name in standard_library for name in imported_roots), imported_roots)

    def test_no_mutation_contract_ignores_binary_fixture(self):
        import review_state
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = pathlib.Path(temporary_directory)
            (root / "source.py").write_text("import json\n")
            (root / ".gitkeep").write_text("kept\n")
            (root / "ignored.pyc").write_bytes(b"\x00\xff")
            self.assertEqual(review_state.scan_source_texts(root), {".gitkeep": "kept\n", "source.py": "import json\n"})

    def test_deterministic_boundaries_execute_production_helpers(self):
        import review_state
        skill = (SKILL_ROOT / "SKILL.md").read_text()
        self.assertIn("scripts/review_state.py", skill)
        self.assertNotIn("def ", skill)
        prompts = review_state.build_round_zero_prompts({"base_sha": "a", "head_sha": "b", "files": ["a.py"], "diff": ""})
        self.assertEqual(prompts["claude"], review_state.build_round_zero_prompts({"base_sha": "a", "head_sha": "b", "files": ["a.py"], "diff": ""})["claude"])
        self.assertEqual(review_state.select_termination_reason({"round_cap", "no_new_high"}), "no_new_high")
        for name in (
            "build_round_zero_prompts", "execute_round_zero", "write_terminal_run_artifacts",
            "normalize_reviewer_findings", "derive_finding_id", "validate_and_record_critique",
            "advance_critique_rounds", "select_termination_reason", "assign_anonymous_groups",
            "sort_and_shuffle_findings", "render_report",
        ):
            self.assertTrue(callable(getattr(review_state, name, None)), name)


if __name__ == "__main__":
    unittest.main()
