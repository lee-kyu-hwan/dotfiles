import ast
import json
import pathlib
import re
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


def assert_strict_schema(testcase, schema, path="$"):
    testcase.assertIn("type", schema, path)
    if "enum" in schema:
        testcase.assertEqual(schema["type"], "string", path)
    if schema["type"] == "object":
        properties = schema.get("properties")
        testcase.assertIsInstance(properties, dict, path)
        testcase.assertTrue(properties, path)
        testcase.assertIs(schema.get("additionalProperties"), False, path)
        testcase.assertEqual(set(schema.get("required", [])), set(properties), path)
        for name, child in properties.items():
            assert_strict_schema(testcase, child, f"{path}.{name}")
    elif schema["type"] == "array":
        testcase.assertIn("items", schema, path)
        assert_strict_schema(testcase, schema["items"], f"{path}[]")


def validates_locally(schema, value):
    expected = schema["type"]
    matches = {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
    }[expected]
    if not matches or ("enum" in schema and value not in schema["enum"]):
        return False
    if expected == "object":
        properties = schema["properties"]
        if set(schema["required"]) - set(value):
            return False
        if schema.get("additionalProperties") is False and set(value) - set(properties):
            return False
        return all(validates_locally(properties[key], item) for key, item in value.items())
    if expected == "array":
        if len(value) < schema.get("minItems", 0):
            return False
        return all(validates_locally(schema["items"], item) for item in value)
    if expected == "string":
        return len(value) >= schema.get("minLength", 0)
    if expected in {"integer", "number"}:
        return value >= schema.get("minimum", value) and value <= schema.get("maximum", value)
    return True


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
            "scripts/review_state.py",
            "schemas/reviewer.schema.json",
            "schemas/critique.schema.json",
            "schemas/synthesis.schema.json",
            "references/operation.md",
            "references/verification.md",
            "templates/report.md",
            "tests/test_contracts.py",
            "tests/test_execution.py",
            "tests/test_critique.py",
            "tests/test_normalization.py",
            "tests/test_reporting.py",
            "tests/test_rounds.py",
            "tests/test_synthesis.py",
            "tests/test_live_api.py",
            "tests/live_e2e.py",
        ]
        for relative_path in required_paths:
            self.assertTrue((SKILL_ROOT / relative_path).is_file(), relative_path)

        for marker in ("schemas/.gitkeep", "scripts/.gitkeep"):
            self.assertFalse((SKILL_ROOT / marker).exists(), marker)

        # Only the chezmoi source tree has the repository-level .chezmoiignore.
        if "dot_claude" in SKILL_ROOT.parts:
            chezmoiignore = (SKILL_ROOT.parents[2] / ".chezmoiignore").read_text(encoding="utf-8")
            patterns = [
                line.strip()
                for line in chezmoiignore.splitlines()
                if line.strip() and not line.lstrip().startswith(("#", "{{"))
            ]
            # What matters is that this skill's bytecode cache is never deployed, not
            # which line says so. A repository-wide pattern satisfies the contract just
            # as a skill-specific one does; pinning the exact string breaks the test
            # when the two are consolidated.
            deployed = pathlib.PurePosixPath(".claude/skills/dual-review/scripts/__pycache__")
            covered = any(
                candidate.full_match(pattern)
                for candidate in (deployed, deployed / "review_state.cpython-314.pyc")
                for pattern in patterns
            )
            self.assertTrue(covered, "no .chezmoiignore pattern covers {0}".format(deployed))

        source_state_prefixes = (
            "after_", "before_", "create_", "dot_", "empty_", "encrypted_",
            "exact_", "executable_", "literal_", "modify_", "once_", "onchange_",
            "private_", "readonly_", "remove_", "run_", "symlink_",
        )
        for path in SKILL_ROOT.rglob("*"):
            relative = path.relative_to(SKILL_ROOT)
            if "__pycache__" in relative.parts:
                continue
            for component in relative.parts:
                self.assertFalse(component.startswith("."), relative)
                self.assertFalse(component.endswith(".tmpl"), relative)
                self.assertFalse(component.startswith(source_state_prefixes), relative)

        frontmatter = (SKILL_ROOT / "SKILL.md").read_text().split("---", 2)[1]
        frontmatter_values = {
            key.strip(): value.strip()
            for line in frontmatter.splitlines() if ":" in line
            for key, value in [line.split(":", 1)]
        }
        keys = {line.split(":", 1)[0] for line in frontmatter.splitlines() if ":" in line}
        self.assertTrue(
            {
                "name", "version", "description", "argument-hint",
                "disable-model-invocation", "model", "effort",
            }.issubset(keys)
        )
        with self.subTest(contract="skill version"):
            self.assertEqual(frontmatter_values["version"], "1.3.0")
        self.assertEqual(frontmatter_values["model"], "opus")
        self.assertEqual(
            managed_target("dot_claude/skills/dual-review/SKILL.md"),
            "~/.claude/skills/dual-review/SKILL.md",
        )
        operation = (SKILL_ROOT / "references/operation.md").read_text()
        self.assertIn("Claude Code 2.1.268", operation)
        self.assertIn("## Claude Code 2.1.268 confirmed capabilities", operation)
        self.assertIn("## Production-emitted flags", operation)
        self.assertIn("## Spec CMD-6 harness-only flags", operation)

        def section_body(title):
            after_heading = operation.split(f"## {title}\n", 1)[1]
            return after_heading.split("\n## ", 1)[0]

        confirmed_capabilities = section_body("Claude Code 2.1.268 confirmed capabilities")
        with self.subTest(contract="confirmed capabilities"):
            for flag in (
                "-p", "--no-session-persistence", "--setting-sources", "--permission-mode",
                "--permission-prompts", "--allowedTools", "--agent", "--output-format", "--json-schema",
            ):
                self.assertIn(flag, confirmed_capabilities)

        production_flags = section_body("Production-emitted flags")
        with self.subTest(contract="production flags"):
            for flag in (
                "-p", "--no-session-persistence", "--permission-mode plan",
                "--permission-prompts none", "--allowedTools Read,Glob,Grep",
                "--agent <role>", "--output-format json", "--json-schema <schema>",
            ):
                self.assertIn(flag, production_flags)
            for harness_only in (
                "--setting-sources project", "--permission-mode default", "Bash(python3:*)",
            ):
                self.assertNotIn(harness_only, production_flags)
            self.assertIn("variable-arity", production_flags)
            self.assertIn("stdin", production_flags)

        harness_only_flags = section_body("Spec CMD-6 harness-only flags")
        with self.subTest(contract="harness-only flags"):
            for flag in (
                "--setting-sources project", "--permission-mode default",
                '--allowedTools "Read,Glob,Grep,Bash(python3:*)"',
            ):
                self.assertIn(flag, harness_only_flags)
            self.assertIn("variable-arity", harness_only_flags)
            self.assertIn("stdin", harness_only_flags)

        with self.subTest(contract="fingerprint scope"):
            for fingerprint_contract in (
                "git-tracked files", "untracked and gitignored changes", "not a Git repository",
                "zero tracked files", "full-tree walk",
            ):
                self.assertIn(fingerprint_contract, operation)
        self.assertIn("stdin", operation)
        self.assertIn("dot_claude/skills/dual-review/SKILL.md", operation)
        self.assertIn("~/.claude/skills/dual-review/SKILL.md", operation)
        verification = (SKILL_ROOT / "references/verification.md").read_text()
        self.assertIn("not configured", verification)
        self.assertIn("Python 3.14.7", verification)
        self.assertIn("DRV-1", verification)
        self.assertIn("Spec CMD-1", verification)
        self.assertNotRegex(verification, r"(?m)^\| CMD-\d+")

    def test_live_api_contract(self):
        path = SKILL_ROOT / "tests/test_live_api.py"
        self.assertTrue(path.is_file(), path)
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        standard_library = set(sys.stdlib_module_names) | {"__future__"}
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                imports.append(node.module.split(".", 1)[0])
        self.assertTrue(all(name in standard_library for name in imports), imports)
        self.assertIn("DUAL_REVIEW_LIVE_API", source)
        self.assertIn("DUAL_REVIEW_EVIDENCE_DIR", source)
        self.assertRegex(source, r"@unittest\.skipUnless\([^\n]*DUAL_REVIEW_LIVE_API")
        for production_name in ("build_codex_command", "build_claude_command", "SubprocessAdapter"):
            self.assertIn(production_name, source)
        for evidence_name in ("command.json", "stdout.txt", "stderr.txt", "result.json"):
            self.assertIn(evidence_name, source)
        self.assertIn('pop("$schema"', source)
        self.assertIn("CLAUDE_SCHEMA_INCOMPATIBLE", source)

    def test_live_e2e_contract(self):
        path = SKILL_ROOT / "tests/live_e2e.py"
        self.assertTrue(path.is_file(), path)
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        standard_library = set(sys.stdlib_module_names) | {"__future__"}
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                imports.append(node.module.split(".", 1)[0])
        self.assertTrue(all(name in standard_library for name in imports), imports)
        required_options = {
            "--repository", "--logical-base", "--expected-branch", "--expected-files",
            "--expected-diff-bytes", "--preserve-run", "--review-state-script", "--evidence-dir",
        }
        self.assertEqual(set(re.findall(r'add_argument\("(--[a-z-]+)"[^\n]*required=True', source)), required_options)
        for boundary in (
            "git merge-base", "--unified=0", "--porcelain", "preserve_run",
            'sha256(base_sha + b"\\0" + before_head)', "max(existing_numbers, default=0) + 1",
            "start-before-read", "explicit_no_findings", "cross_critique_calls",
            "synthesis_calls", "report.md", "before_head == after_head",
            "before_status == after_status", "preserved_digests",
        ):
            self.assertIn(boundary, source)
        self.assertNotIn("-000002", source)

    def test_reviewer_contract(self):
        operation = (SKILL_ROOT / "references/operation.md").read_text()
        expected_roles = {
            "pr-review-toolkit:code-reviewer", "pr-test-analyzer",
            "comment-analyzer", "silent-failure-hunter", "type-design-analyzer",
        }
        self.assertTrue(all(role in operation for role in expected_roles))
        import review_state
        allowed = {"-C", "--sandbox", "--ephemeral", "--model", "-c", "--output-schema", "--output-last-message", "--json", "-"}
        command = review_state.build_codex_command("/repository")
        used_flags = {part for part in command if part.startswith("-")}
        self.assertTrue(used_flags.issubset(allowed))
        reviewer_schema = str(SKILL_ROOT / "schemas/reviewer.schema.json")
        critique_schema = str(SKILL_ROOT / "schemas/critique.schema.json")
        self.assertEqual(command, (
            "codex", "exec", "-C", "/repository", "--sandbox", "read-only",
            "--output-schema", reviewer_schema, "--json", "--model", "gpt-5.6-sol", "-",
        ))
        command_with_output = review_state.build_codex_command(
            "/repository", "critique.schema.json", pathlib.Path("/tmp/last-message")
        )
        self.assertEqual(command_with_output, (
            "codex", "exec", "-C", "/repository", "--sandbox", "read-only",
            "--output-schema", critique_schema, "--json", "--output-last-message",
            "/tmp/last-message", "--model", "gpt-5.6-sol", "-",
        ))
        for codex_command in (command, command_with_output):
            self.assertEqual(codex_command.count("--model"), 1)
            self.assertEqual(codex_command.count("gpt-5.6-sol"), 1)
            self.assertEqual(codex_command.count("-"), 1)
            self.assertEqual(codex_command[-1], "-")
            self.assertNotIn("prompt", codex_command)
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
        assert_strict_schema(self, reviewer)
        expected = {"source", "original_id", "severity", "title", "body", "file", "line_start", "line_end", "finding_confidence", "recommendation"}
        findings = reviewer["properties"]["findings"]
        self.assertNotIn("minItems", findings)
        self.assertTrue(validates_locally(reviewer, {"verdict": "ok", "summary": "", "findings": [], "next_steps": []}))
        self.assertEqual(set(findings["items"]["required"]), expected)
        finding_properties = findings["items"]["properties"]
        self.assertEqual(finding_properties["severity"]["enum"], ["critical", "high", "medium", "low"])
        self.assertEqual((finding_properties["line_start"]["minimum"], finding_properties["line_end"]["minimum"]), (1, 1))
        self.assertEqual((finding_properties["finding_confidence"]["minimum"], finding_properties["finding_confidence"]["maximum"]), (0, 1))

    def test_round_zero_claude_prompt_requires_exclusive_no_findings_marker(self):
        import review_state
        prompt = review_state.build_round_zero_prompts({"files": [], "diff": ""})["claude"]
        self.assertIn("NO_FINDINGS", prompt)
        self.assertIn("stdout", prompt.lower())
        self.assertRegex(prompt, r"(?i)(exact|exactly).*(one|single).*(line|output)")
        self.assertRegex(prompt, r"(?i)(do not|never).*(mix|combine).*(NO_FINDINGS|finding)")

    def test_round_zero_claude_prompt_advertises_confidence_and_literal_label_syntax(self):
        import review_state
        prompt = review_state.build_round_zero_prompts({"files": [], "diff": ""})["claude"]
        self.assertIn("Confidence must be one of:", prompt)
        confidence_instruction = prompt.split("Confidence must be one of:", 1)[1].split(".", 1)[0]
        for word in review_state.CONFIDENCE_BY_WORD:
            self.assertIn(word, confidence_instruction)
        self.assertIn("numeric confidence from 0 to 1 or 0 to 100 is also allowed", prompt)
        self.assertIn("<LabelName>: <value>", prompt)
        self.assertIn("is not the required format", prompt)
        self.assertIn("Do not prefix lines with the literal text `Label:`", prompt)

    def test_critique_contract(self):
        critique = json.loads((SKILL_ROOT / "schemas/critique.schema.json").read_text())
        assert_strict_schema(self, critique)
        self.assertEqual(set(critique["required"]), {"critiques"})
        entry = critique["properties"]["critiques"]["items"]
        self.assertEqual(set(entry["required"]), {"finding_id", "verdict", "evidence", "new_findings"})
        self.assertEqual(entry["properties"]["verdict"]["enum"], ["유지", "반증됨", "미검증"])
        evidence = entry["properties"]["evidence"]["items"]
        self.assertEqual(set(evidence["required"]), {"file", "line_start", "line_end"})
        self.assertEqual(entry["properties"]["evidence"]["minItems"], 1)
        self.assertEqual(evidence["properties"]["file"]["minLength"], 1)
        new_finding = entry["properties"]["new_findings"]["items"]
        expected = {"severity", "title", "body", "file", "line_start", "line_end", "finding_confidence", "recommendation"}
        self.assertEqual(set(new_finding["required"]), expected)
        fixture = {"severity": "high", "title": "title", "body": "body", "file": "x.py", "line_start": 1, "line_end": 2, "finding_confidence": .8, "recommendation": "fix"}
        self.assertTrue(validates_locally(new_finding, fixture))
        for missing in expected:
            self.assertFalse(validates_locally(new_finding, {key: value for key, value in fixture.items() if key != missing}), missing)
        self.assertFalse(validates_locally(new_finding, {**fixture, "unexpected": "value"}))
        self.assertFalse(validates_locally(new_finding, {**fixture, "line_start": "1"}))

    def test_synthesis_contract(self):
        synthesis = json.loads((SKILL_ROOT / "schemas/synthesis.schema.json").read_text())
        assert_strict_schema(self, synthesis)
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
            (root / "notes.md").write_text("notes\n")
            (root / "schema.json").write_text("{}\n")
            (root / ".gitkeep").write_text("ignored\n")
            (root / "ignored.pyc").write_bytes(b"\x00\xff")
            (root / "ignored.bin").write_bytes(b"\x00\xff")
            self.assertEqual(review_state.scan_source_texts(root), {
                "notes.md": "notes\n",
                "schema.json": "{}\n",
                "source.py": "import json\n",
            })

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
