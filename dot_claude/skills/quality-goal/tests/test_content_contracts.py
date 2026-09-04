import re
import sys
import unittest
from pathlib import Path


REFERENCE_DIR = Path(__file__).resolve().parent.parent / "references"
SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from validate_review import REQUIRED_CHECKS  # noqa: E402


def read_reference(name):
    return (REFERENCE_DIR / name).read_text(encoding="utf-8")


class RoutingRulesContentTests(unittest.TestCase):
    def test_routing_rules_contract(self):
        text = read_reference("routing-rules.md")
        lower = text.casefold()

        self.assertRegex(lower, r"--mode.{0,200}(unknown|invalid).{0,200}(reject|stop)")
        self.assertIn("--mode=auto|light|standard|strict", text)
        self.assertRegex(
            lower,
            r"(?:unknown|invalid).{0,400}(?:reject|stop).{0,400}"
            r"without creating any state",
        )
        self.assertIn("no `.claude/quality-state/` directory", lower)
        self.assertRegex(
            lower,
            r"(?:risk scan|risk assessment|risk check).{0,200}"
            r"(?:before|prior).{0,200}(?:size estimation|size estimate|estimation)",
        )
        self.assertRegex(lower, r"explicit.{0,160}(higher|equal).{0,160}accept")
        self.assertRegex(
            lower,
            r"explicit.{0,240}(lower|downgrade).{0,240}"
            r"(?:trigger|reason).{0,240}(confirmation|confirm).{0,240}"
            r"(?:silent downgrade|silently downgrade).{0,80}never|"
            r"never.{0,80}(?:silent downgrade|silently downgrade)",
        )
        self.assertRegex(
            lower,
            r"auto.{0,300}strict.{0,300}(?:any|one).{0,100}strict trigger",
        )
        self.assertRegex(
            lower,
            r"auto.{0,500}(?:cross[- ]layer|interface).{0,160}standard",
        )
        self.assertRegex(
            lower,
            r"light.{0,300}(?:only when all|when all conditions|all light conditions)",
        )
        self.assertRegex(lower, r"uncertain.{0,120}higher mode")
        self.assertRegex(
            lower,
            r"selected mode.{0,200}(?:concrete )?evidence.{0,200}"
            r"(?:before continuing|before proceed|continue)",
        )

        for term in (
            "authentication",
            "authorization",
            "tenancy",
            "tenant isolation",
            "payment",
            "settlement",
            "refund",
            "coupon",
            "points",
            "personally identifiable information",
            "secrets",
            "security controls",
            "migration",
            "backfill",
            "destructive operation",
            "difficult rollback",
            "public or external api",
            "webhook",
            "queue",
            "idempotency",
            "concurrency",
            "production infrastructure",
            "broad customer impact",
        ):
            with self.subTest(term=term):
                self.assertIn(term, lower)

        for term in (
            "localized",
            "unambiguous",
            "no public api",
            "schema",
            "cross-service",
            "permission",
            "production operation change",
            "existing targeted verification",
        ):
            with self.subTest(light_condition=term):
                self.assertIn(term, lower)
        self.assertRegex(lower, r"light.{0,500}(?:none of|no).{0,100}strict")
        light_section = text.split("## Light conditions", 1)[1].split("## Standard conditions", 1)[0]
        self.assertEqual(len(re.findall(r"(?m)^- ", light_section)), 5)
        self.assertNotIn("No production change is included.", text)

        for term in (
            "multiple files",
            "modules",
            "layers",
            "user flow",
            "internal api",
            "state transition",
            "async",
            "shared component",
            "new dependency",
            "non-trivial interface",
            "alternatives",
            "non-goals",
            "acceptance criteria",
        ):
            with self.subTest(standard_condition=term):
                self.assertIn(term, lower)


class BrainstormingPolicyContentTests(unittest.TestCase):
    def test_brainstorming_policy_contract(self):
        text = read_reference("brainstorming-policy.md")
        lower = text.casefold()

        self.assertIn("inspect", lower)
        self.assertIn("repository conventions", lower)
        self.assertIn("materially necessary", lower)
        self.assertIn("one at a time", lower)
        self.assertRegex(lower, r"2\s*(?:–|-)\s*3|two or three")
        self.assertIn("approach", lower)
        self.assertRegex(lower, r"recommend(?:s|ed)?")
        for term in (
            "scope",
            "non-goals",
            "acceptance criteria",
            "interfaces",
            "error cases",
            "testability",
            "independent subsystems",
            "implementation",
            "materially ambiguous",
        ):
            with self.subTest(term=term):
                self.assertIn(term, lower)
        self.assertRegex(lower, r"never.{0,120}implementation|implementation.{0,120}never")
        self.assertIn("adapted", lower)
        self.assertRegex(lower, r"must not.{0,100}(invoke|modify)")
        self.assertIn("bundled brainstorming skill", lower)


class PlanningPolicyContentTests(unittest.TestCase):
    def test_planning_policy_contract(self):
        text = read_reference("planning-policy.md")
        lower = text.casefold()

        self.assertRegex(
            lower,
            r"every.{0,100}spec.{0,160}acceptance criter(?:ion|ia).{0,160}"
            r"(?:implementation )?task.{0,160}verification",
        )
        self.assertIn("exact files", lower)
        self.assertIn("interface contracts", lower)
        self.assertIn("when knowable", lower)
        self.assertIn("independently testable tasks", lower)
        self.assertIn("test-first", lower)
        self.assertIn("behavior changes", lower)
        self.assertRegex(lower, r"approved plan.{0,220}(?:user-authorized exception|exception)")
        self.assertIn("concrete commands", lower)
        self.assertIn("expected outcomes", lower)
        self.assertRegex(lower, r"plans? must not.{0,220}placeholder.{0,100}add appropriate tests")
        self.assertIn("rollback", lower)
        self.assertIn("failure handling", lower)
        self.assertIn("traceability table", lower)
        self.assertRegex(lower, r"hands?.{0,100}approved plan.{0,100}codex")
        self.assertRegex(lower, r"must not.{0,100}(invoke|modify)")
        self.assertIn("bundled writing-plans skill", lower)


class SpecRubricContentTests(unittest.TestCase):
    def test_spec_rubric_contract(self):
        text = read_reference("spec-rubric.md")
        lower = text.casefold()
        weight_rows = (
            ("15", ("problem", "scope", "non-goals")),
            ("20", ("requirement", "clarity")),
            ("25", ("acceptance criteria", "testability")),
            ("20", ("architecture", "interfaces", "data flow")),
            ("20", ("feasibility", "failure", "risk")),
        )
        lines = lower.splitlines()
        for weight, categories in weight_rows:
            self.assertTrue(
                any(weight in line and all(category in line for category in categories) for line in lines),
                f"weight {weight} is not adjacent to {categories}",
            )
        self.assertRegex(lower, r"(?:total|sum).{0,40}100|100.{0,40}(?:total|sum)")
        self.assertIn("85", lower)
        for gate_key in (
            "required_sections",
            "material_decisions_resolved",
            "acceptance_criteria_objective",
        ):
            self.assertIn(f"`{gate_key}`", text)
        for term in (
            "zero critical/high",
            "zero unresolved material decisions",
            "objectively verifiable acceptance criteria",
            "critical",
            "high",
            "medium",
            "low",
            "stable finding",
            "ids stay stable across rounds",
            "round 1",
            "full review",
            "open findings",
            "regressions",
            "new_blocker_evidence",
        ):
            with self.subTest(term=term):
                self.assertIn(term, lower)
        self.assertIn("`SPEC-`", text)
        self.assertRegex(lower, r"(?:later rounds|rounds after round 1).{0,220}(?:open findings|regressions)")
        self.assertEqual(
            ["3"],
            re.findall(r"after round (\d+) without a passing gate", lower),
        )
        self.assertRegex(lower, r"needs_redesign")

    def test_rubric_pass_gate_keys_match_required_checks_exactly(self):
        rubric_names = {
            "spec": "spec-rubric.md",
            "plan": "plan-rubric.md",
            "code": "code-rubric.md",
        }
        for artifact, rubric_name in rubric_names.items():
            with self.subTest(artifact=artifact):
                text = read_reference(rubric_name)
                pass_gate = text.split("## Pass gate", 1)[1].split("\n## ", 1)[0]
                gate_keys = set(re.findall(r"`([^`]+)`", pass_gate))
                self.assertEqual(REQUIRED_CHECKS[artifact], gate_keys)


class PlanRubricContentTests(unittest.TestCase):
    def test_plan_rubric_contract(self):
        text = read_reference("plan-rubric.md")
        lower = text.casefold()
        weight_rows = (
            ("25", ("traceability",)),
            ("20", ("ordering", "boundaries", "dependencies")),
            ("15", ("file", "interface", "precision")),
            ("25", ("tests", "deterministic verification")),
            ("15", ("failure", "rollout", "rollback", "risk")),
        )
        lines = lower.splitlines()
        for weight, categories in weight_rows:
            self.assertTrue(
                any(weight in line and all(category in line for category in categories) for line in lines),
                f"weight {weight} is not adjacent to {categories}",
            )
        self.assertRegex(lower, r"(?:total|sum).{0,40}100|100.{0,40}(?:total|sum)")
        self.assertIn("85", lower)
        for gate_key in (
            "required_sections",
            "traceability_complete",
            "placeholders_absent",
        ):
            self.assertIn(f"`{gate_key}`", text)
        for term in (
            "zero critical/high",
            "every acceptance criterion",
            "placeholder",
        ):
            with self.subTest(term=term):
                self.assertIn(term, lower)
        self.assertRegex(lower, r"every acceptance criterion.{0,180}(?:maps|map).{0,120}(?:task|verification)")
        self.assertRegex(lower, r"placeholders_absent.{0,120}placeholder text is absent")
        self.assertEqual(
            ["2"],
            re.findall(r"after round (\d+) without a passing gate", lower),
        )
        self.assertRegex(lower, r"needs_redesign")


class CodeRubricContentTests(unittest.TestCase):
    def test_code_rubric_contract(self):
        text = read_reference("code-rubric.md")
        lower = text.casefold()

        self.assertIn("score", lower)
        self.assertIn("observability", lower)
        self.assertIn("advisory", lower)
        self.assertRegex(lower, r"## advisory scoring dimensions")
        for dimension_term in ("correctness", "scope", "evidence"):
            with self.subTest(scoring_dimension=dimension_term):
                self.assertIn(dimension_term, lower)
        self.assertRegex(lower, r"(?:never|cannot|can never).{0,120}override.{0,160}(?:deterministic|critical/high)")
        for gate_key in (
            "required_commands_passed",
            "acceptance_criteria_met",
            "unrelated_changes_absent",
            "documentation_current",
        ):
            self.assertIn(f"`{gate_key}`", text)
        for term in (
            "all approved verification commands",
            "exit successfully",
            "zero critical/high",
            "acceptance_criteria_met",
            "evidence",
            "no unrelated changes",
            "documentation_current",
            "deterministic failures",
            "never waivable",
        ):
            with self.subTest(term=term):
                self.assertIn(term, lower)
        self.assertIn("`CODE-`", text)
        self.assertRegex(lower, r"(?:reviewer|review).{0,80}(?:never waivable|cannot waive)")
        self.assertEqual(
            ["3"],
            re.findall(r"after round (\d+) without a passing gate", lower),
        )
        self.assertRegex(lower, r"needs_redesign")


class ModelRoutingContentTests(unittest.TestCase):
    def test_model_routing_contract(self):
        text = read_reference("model-routing.md")
        lower = text.casefold()

        route_patterns = (
            r"\|?\s*orchestrator\s*\|\s*inherit\s*\|\s*high\s*\|?",
            r"\|?\s*fresh reviewer\s*\|\s*opus\s*\|\s*high\s*\|?",
            r"\|?\s*codex light[+/]standard\s*\|\s*gpt-5\.6-terra\s*\|\s*high\s*\|?",
            r"\|?\s*codex strict\s*\|\s*gpt-5\.6-sol\s*\|\s*high\s*\|?",
            r"\|?\s*bounded redesign only\s*\|\s*gpt-5\.6-sol\s*\|\s*xhigh\s*\|?",
        )
        for pattern in route_patterns:
            with self.subTest(route=pattern):
                self.assertRegex(lower, pattern)

        self.assertRegex(text, r"(?m)^\s*codex\s+exec\b")
        for term in (
            "-C",
            "--sandbox workspace-write",
            "--ephemeral",
            "--output-schema",
            "--output-last-message",
            "--json",
        ):
            with self.subTest(command_option=term):
                self.assertIn(term, text)
        self.assertRegex(text, r"\s-\s*<")
        self.assertIn("exit code", lower)
        self.assertIn("blocked_model_unavailable", lower)
        self.assertRegex(lower, r"blocked_model_unavailable.{0,100}status_reason.{0,100}not a stage")
        self.assertRegex(lower, r"awaiting.{0,180}current stage")
        self.assertRegex(lower, r"declines.{0,100}cannot be reached.{0,220}terminal.{0,100}blocked")
        self.assertRegex(lower, r"approved substitution.{0,180}report.{0,180}continues.{0,120}current stage")
        self.assertRegex(lower, r"(?:forbid|must not|never).{0,100}silent fallback|silent fallback.{0,100}(?:forbid|must not|never)")
        self.assertIn("explicit user approval", lower)
        self.assertIn("recorded in the report", lower)
        self.assertIn("substitute model", lower)
        self.assertRegex(lower, r"sol/xhigh route.{0,220}(?:failed high-risk implementation|needs_redesign).{0,160}bounded redesign")
        self.assertIn("--sandbox read-only", lower)
        self.assertIn('model_reasoning_effort="low"', lower)
        self.assertIn("one-line prompt", lower)
        self.assertRegex(lower, r"failed preflight.{0,180}unavailable-model recovery path")
        self.assertIn("task state directory that the repository should ignore", lower)
        for term in ("prompt", "result", "event", "paths"):
            with self.subTest(state_path=term):
                self.assertIn(term, lower)

        prohibition = re.compile(r"(?:금지|않는다|never|forbid|prohibited)", re.IGNORECASE)
        forbidden_patterns = (
            r"--skip-git-repo-check",
            r"--full-auto",
            r"--yolo",
            r"sandbox[ -]bypass",
        )
        for forbidden_pattern in forbidden_patterns:
            matching_lines = [
                line
                for line in text.splitlines()
                if re.search(forbidden_pattern, line, re.IGNORECASE)
            ]
            self.assertTrue(matching_lines, f"missing prohibited token: {forbidden_pattern}")
            for line in matching_lines:
                self.assertFalse(
                    re.match(r"\s*codex\s", line, re.IGNORECASE),
                    f"prohibited token appears in runnable command: {line}",
                )
                self.assertRegex(line, prohibition, f"no prohibition context: {line}")


class CrossDocumentContentTests(unittest.TestCase):
    def test_reference_documents_contain_no_unfinished_markers(self):
        marker_pattern = re.compile(
            r"\b(?:" + "T" + "[B]D|" + "T" + "[O]DO" + r")\b",
            re.IGNORECASE,
        )
        document_paths = list(REFERENCE_DIR.glob("*.md"))
        document_paths.extend((REFERENCE_DIR.parent / "templates").glob("*.md"))
        for path in sorted(document_paths):
            content = path.read_text(encoding="utf-8")
            self.assertIsNone(marker_pattern.search(content), str(path))


class TemplateContentContractTests(unittest.TestCase):
    TEMPLATE_DIR = REFERENCE_DIR.parent / "templates"

    def assert_shared_template_contract(self, path):
        text = path.read_text(encoding="utf-8")
        header = "\n".join(text.splitlines()[:40])
        for token in (
            "{{TASK_ID}}",
            "{{MODE}}",
            "{{STATUS}}",
            "{{CREATED_AT}}",
            "{{UPDATED_AT}}",
            "{{GOAL}}",
        ):
            with self.subTest(metadata_token=token):
                self.assertIn(token, header)

        valid_variable = re.compile(r"\{\{[A-Z0-9_]+\}\}")
        for token in re.findall(r"\{\{[^{}\n]*\}\}", text):
            self.assertRegex(token, valid_variable.pattern, str(path))
        self.assertIsNone(
            re.search(r"(?<!\{)\{[A-Z0-9_]+\}(?!\})", text),
            str(path),
        )

    def assert_strict_only_contract(self, text):
        lower = text.casefold()
        start_marker = "<!-- strict-only:start -->"
        end_marker = "<!-- strict-only:end -->"
        self.assertEqual(lower.count(start_marker), 1)
        self.assertEqual(lower.count(end_marker), 1)
        start = lower.index(start_marker)
        end = lower.index(end_marker)
        self.assertLess(start, end)
        strict_block = lower[start + len(start_marker) : end]
        strict_sections = (
            ("threat and trust boundaries", r"threat.{0,100}trust boundar"),
            ("authorization and tenant isolation", r"authorization.{0,140}tenant isolation"),
            ("migration/compatibility/rollback", r"migration.{0,180}compatib.{0,180}rollback"),
            ("failure recovery and observability", r"failure recover.{0,140}observab"),
            ("high-risk end-to-end verification", r"high-risk.{0,120}(?:end-to-end|e2e).{0,120}verif"),
            ("no production mutation confirmation", r"no production mutation.{0,120}confirmation"),
        )
        for label, pattern in strict_sections:
            self.assertRegex(strict_block, pattern, f"missing strict-only coverage: {label}")
        self.assertRegex(lower, r"inapplicable.{0,160}(?:remove|delete)")
        self.assertRegex(lower, r"inapplicable.{0,220}(?:not applicable|n/a).{0,160}(?:reason|rationale)")
        self.assertRegex(lower, r"(?:before|prior to) review")

    def test_spec_template_contract(self):
        path = self.TEMPLATE_DIR / "spec.md"
        self.assert_shared_template_contract(path)
        text = path.read_text(encoding="utf-8")
        for heading in (
            "Problem and context",
            "Goals",
            "Non-goals",
            "Requirements",
            "Acceptance criteria",
            "Architecture",
            "Interfaces and data flow",
            "Failure behavior",
            "Security and risk",
            "Test strategy",
            "Decisions",
        ):
            with self.subTest(heading=heading):
                self.assertRegex(text, rf"(?m)^#{{1,3}}\s+.*{re.escape(heading)}.*$")
        self.assert_strict_only_contract(text)

    def test_plan_template_contract(self):
        path = self.TEMPLATE_DIR / "plan.md"
        self.assert_shared_template_contract(path)
        text = path.read_text(encoding="utf-8")
        for heading in (
            "Spec link",
            "Global constraints",
            "File map",
            "Task dependencies",
            "Tasks",
            "Verification commands",
            "Rollout and rollback",
            "Acceptance-criteria traceability",
        ):
            with self.subTest(heading=heading):
                self.assertRegex(text, rf"(?m)^#{{1,3}}\s+.*{re.escape(heading)}.*$")
        self.assert_strict_only_contract(text)

    def test_report_template_contract(self):
        path = self.TEMPLATE_DIR / "report.md"
        self.assert_shared_template_contract(path)
        text = path.read_text(encoding="utf-8")
        for heading in (
            "Classification",
            "Review history",
            "Blocking-finding resolutions",
            "Plan approval",
            "Changed files",
            "Verification evidence",
            "Remaining advisory findings",
            "Final status",
        ):
            with self.subTest(heading=heading):
                self.assertRegex(text, rf"(?m)^#{{1,3}}\s+.*{re.escape(heading)}.*$")
        lower = text.casefold()
        self.assertRegex(lower, r"missing verification category.{0,180}not configured")
        self.assertRegex(lower, r"not configured.{0,180}(?:repository evidence|evidence consulted)")
        self.assertRegex(lower, r"never.{0,80}(?:reported|marked).{0,80}passed")
        self.assertRegex(lower, r"every.{0,100}executed command.{0,160}exit code.{0,160}(?:concise )?output evidence")


class CodexResultSchemaContractTests(unittest.TestCase):
    SCHEMA_PATH = REFERENCE_DIR.parent / "schemas" / "codex-result.schema.json"

    def test_codex_result_schema_contract(self):
        import json

        schema = json.loads(self.SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(schema["type"], "object")
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(
            set(schema["required"]),
            {"status", "summary", "changed_files", "commands", "plan_deviations", "remaining_concerns"},
        )

        self.assertEqual(set(schema["properties"]["status"]["enum"]), {"completed", "blocked", "needs_plan_change"})

        changed_files = schema["properties"]["changed_files"]
        self.assertEqual(changed_files["type"], "array")
        self.assertEqual(changed_files["items"]["type"], "string")
        path_pattern = changed_files["items"].get("pattern")
        self.assertIsNotNone(path_pattern)
        compiled_path_pattern = re.compile(path_pattern)
        for valid_path in ("src/a.py", ".gitignore", ".claude/x.json"):
            with self.subTest(valid_path=valid_path):
                self.assertIsNotNone(compiled_path_pattern.match(valid_path))
        for invalid_path in ("/abs", "~/y", "./x", "../etc/passwd"):
            with self.subTest(invalid_path=invalid_path):
                self.assertIsNone(compiled_path_pattern.match(invalid_path))
        for lookaround in ("(?=", "(?!", "(?<=", "(?<!"):
            with self.subTest(lookaround=lookaround):
                self.assertNotIn(lookaround, path_pattern)

        # The structured-output API rejects uniqueItems anywhere in this schema.
        def assert_no_unique_items(value):
            if isinstance(value, dict):
                self.assertNotIn("uniqueItems", value)
                for child in value.values():
                    assert_no_unique_items(child)
            elif isinstance(value, list):
                for child in value:
                    assert_no_unique_items(child)

        assert_no_unique_items(schema)

        commands = schema["properties"]["commands"]
        self.assertEqual(commands["type"], "array")
        command_items = commands["items"]
        self.assertEqual(command_items["type"], "object")
        self.assertFalse(command_items["additionalProperties"])
        self.assertEqual(set(command_items["required"]), {"command", "exit_code", "result"})
        self.assertEqual(command_items["properties"]["exit_code"]["type"], "integer")

        for field in ("plan_deviations", "remaining_concerns"):
            with self.subTest(field=field):
                self.assertEqual(schema["properties"][field]["type"], "array")
                self.assertEqual(schema["properties"][field]["items"]["type"], "string")


def find_repo_root(start):
    for directory in (start.parent, *start.parents):
        if (directory / "dot_claude").is_dir():
            return directory
    raise AssertionError(f"could not find repository root from {start}")


def parse_yaml_frontmatter(text):
    lines = text.splitlines()
    fences = [index for index, line in enumerate(lines) if line.strip() == "---"]
    if len(fences) < 2 or fences[0] != 0:
        raise AssertionError("expected YAML frontmatter fenced by --- lines")

    values = {}
    for line in lines[fences[0] + 1 : fences[1]]:
        if not line.strip():
            continue
        key, separator, value = line.partition(":")
        if not separator:
            raise AssertionError(f"invalid frontmatter line: {line}")
        values[key.strip()] = value.strip()
    return values, "\n".join(lines[fences[1] + 1 :])


QUALITY_REVIEWER_AGENT_PATH = (
    find_repo_root(Path(__file__).resolve())
    / "dot_claude" / "agents" / "quality-reviewer.md"
)


def read_quality_reviewer_agent():
    if not QUALITY_REVIEWER_AGENT_PATH.is_file():
        raise AssertionError(f"missing agent file: {QUALITY_REVIEWER_AGENT_PATH}")
    return QUALITY_REVIEWER_AGENT_PATH.read_text(encoding="utf-8")


class QualityReviewerAgentContentTests(unittest.TestCase):
    AGENT_PATH = QUALITY_REVIEWER_AGENT_PATH

    def read_agent(self):
        return read_quality_reviewer_agent()

    def test_frontmatter_contract(self):
        frontmatter, _ = parse_yaml_frontmatter(self.read_agent())
        self.assertEqual(frontmatter["name"], "quality-reviewer")
        self.assertEqual(frontmatter["tools"].strip(), "Read, Grep, Glob")
        self.assertEqual(frontmatter["model"], "opus")
        self.assertEqual(frontmatter["effort"], "high")
        self.assertEqual(frontmatter["maxTurns"], "24")
        self.assertTrue(frontmatter["description"].strip())
        self.assertNotIn("memory", frontmatter)
        for forbidden_tool in ("Edit", "Write", "Bash", "Agent", "Task", "WebFetch"):
            with self.subTest(forbidden_tool=forbidden_tool):
                self.assertNotIn(forbidden_tool, frontmatter["tools"].strip())

    def test_references_and_output_contract(self):
        _, body = parse_yaml_frontmatter(self.read_agent())
        self.assertNotIn("${CLAUDE_SKILL_DIR}", body)
        for reference in ("spec-rubric.md", "plan-rubric.md", "code-rubric.md"):
            with self.subTest(reference=reference):
                self.assertRegex(body, rf"references/{re.escape(reference)}")
        self.assertRegex(body, r"schemas/review\.schema\.json")

        lower = body.casefold()
        self.assertRegex(lower, r"exactly\s+one\s+json\s+object")
        self.assertRegex(lower, r"no\s+markdown\s+fences")
        self.assertRegex(lower, r"no\s+surrounding\s+prose")
        self.assertRegex(
            lower,
            r"(?:blocked.{0,240}missing\s+(?:artifact|rubric|evidence)|"
            r"missing\s+(?:artifact|rubric|evidence).{0,240}blocked).{0,80}json",
        )
        self.assertIn("the json is the deliverable", lower)
        self.assertIn("produced as the final output", lower)
        self.assertIn("not verified", lower)
        self.assertIn("with the reason", lower)
        self.assertIn("stopping without emitting the json is never acceptable", lower)
        self.assertIn(
            "if any applicable gate condition or rubric item could not be verified, "
            "the verdict must not be `pass`; return `revise` with "
            "`required_next_action` naming the unverified condition and what would settle it.",
            lower,
        )

    def test_blocked_payload_rules_are_explicit(self):
        _, body = parse_yaml_frontmatter(self.read_agent())
        self.assertRegex(
            body,
            r"Echo `artifact` and\s+`round` exactly as supplied by the orchestrator",
        )
        self.assertRegex(
            body,
            r"Set `score` to `0`, `verdict` to `BLOCKED`, `blockers` to `\[\]`,"
            r" and `findings`\s+to `\[\]`",
        )
        self.assertRegex(
            body,
            r"`required_next_action` must be null for PASS and non-null for REVISE and BLOCKED",
        )

    def test_round_and_finding_identity_contract(self):
        _, body = parse_yaml_frontmatter(self.read_agent())
        lower = body.casefold()
        self.assertRegex(lower, r"round\s*1.{0,220}full\s+review")
        self.assertRegex(
            lower,
            r"(?:later\s+rounds|rounds\s+after\s+round\s*1).{0,240}"
            r"(?:prior\s+open\s+finding\s+ids|open\s+finding\s+ids).{0,240}regression",
        )
        self.assertRegex(lower, r"new\s+blocker.{0,180}new_blocker_evidence")
        self.assertRegex(lower, r"new_blocker_evidence.{0,100}(?:non-empty|required|must)" )
        self.assertRegex(lower, r"finding\s+ids?.{0,160}stable.{0,160}materially\s+identical")
        for namespace in ("SPEC-", "PLAN-", "CODE-"):
            with self.subTest(namespace=namespace):
                self.assertIn(namespace.casefold(), lower)
        self.assertRegex(lower, r"(?:namespaced|namespace).{0,120}(?:artifact|artifacts)")

    def test_reviewer_safety_and_fresh_invocation_contract(self):
        _, body = parse_yaml_frontmatter(self.read_agent())
        lower = body.casefold()
        self.assertRegex(lower, r"never.{0,100}(?:edit|modify).{0,100}files")
        self.assertRegex(
            lower,
            r"never.{0,220}severity.{0,220}(?:target\s+score|reach\s+a?\s*target\s+score)",
        )
        self.assertRegex(lower, r"never.{0,120}(?:expose|reveal).{0,120}hidden\s+reasoning")
        self.assertRegex(lower, r"each\s+invocation\s+starts\s+fresh")
        self.assertRegex(lower, r"orchestrator.{0,120}never\s+resumes.{0,120}prior\s+reviewer\s+context")

    def test_agent_contains_no_unfinished_markers(self):
        marker_pattern = re.compile(
            r"\b(?:" + "T" + "[B]D|" + "T" + "[O]DO" + r")\b",
            re.IGNORECASE,
        )
        self.assertIsNone(marker_pattern.search(self.read_agent()), str(self.AGENT_PATH))


class QualityGoalSkillContentTests(unittest.TestCase):
    SKILL_PATH = REFERENCE_DIR.parent / "SKILL.md"

    def read_skill(self):
        self.assertTrue(
            self.SKILL_PATH.is_file(),
            f"missing orchestrator skill file: {self.SKILL_PATH}",
        )
        return self.SKILL_PATH.read_text(encoding="utf-8")

    def test_structured_prior_and_unverified_retry_contract(self):
        _, body = parse_yaml_frontmatter(self.read_skill())
        lower = body.casefold()
        self.assertRegex(
            lower,
            r"build `open_findings` from\s+the prior review json at "
            r"`reviews\[artifact\]\[\*\]\.path`",
        )
        self.assertRegex(
            lower,
            r"send each open finding's\s+id, severity, description, evidence location,\s+"
            r"required resolution, and the\s+orchestrator's resolution claim and resolution evidence",
        )
        self.assertRegex(
            lower,
            r"send confirmed\s+resolutions as ids only in `resolved_finding_ids`",
        )
        self.assertRegex(
            lower,
            r"well-formed unverified revise \(`verdict == revise`, `blockers == \[\]`, and\s+"
            r"any evidence has `verified == false`\)[\s\S]{0,220}does not consume a round: "
            r"relaunch on the same round",
        )
        self.assertRegex(
            lower,
            r"at most two discarded reviews are allowed \(one free retry\); after `exhausted`,\s+"
            r"register the report then transition to blocked with\s+`reviewer_unverified_persists`",
        )
        self.assertRegex(
            lower,
            r"record that outcome as a reviewer capability\s+limit, not a code or design failure",
        )
        self.assertRegex(
            lower,
            r"evidence paths for each unverified condition and the discarded review's\s+"
            r"full non-blocking findings\. on round 2\+, include those findings in prior\s+"
            r"`open_findings`",
        )
        self.assertRegex(lower, r"do not revise the artifact or workspace during this retry")

    def test_reviewer_records_verified_evidence_and_reuses_prior_ids(self):
        _, body = parse_yaml_frontmatter(read_quality_reviewer_agent())
        lower = body.casefold()
        self.assertRegex(
            lower,
            r"on later rounds.{0,260}each supplied open finding is resolved and "
            r"record that determination in evidence; reuse its id when a new finding restates it",
        )
        self.assertRegex(
            lower,
            r"every evidence item, including the single blocked-payload item, must include "
            r"`verified`\. use `verified == false` when a condition was not verified and put "
            r"the reason in its `claim`",
        )

    @staticmethod
    def normalize(text):
        return " ".join(text.casefold().split())

    def test_frontmatter_contract(self):
        frontmatter, _ = parse_yaml_frontmatter(self.read_skill())
        expected = {
            "name": "quality-goal",
            "version": "4.1.0",
            "description": "Use when the user explicitly requests a quality-gated, documented software change workflow.",
            "argument-hint": "[--mode=auto|light|standard|strict] <goal>",
            "disable-model-invocation": "true",
            "model": "inherit",
            "effort": "high",
        }
        self.assertEqual(set(frontmatter), set(expected))
        for key, expected_value in expected.items():
            actual_value = frontmatter[key].strip()
            if (
                key == "argument-hint"
                and len(actual_value) >= 2
                and actual_value[0] == actual_value[-1]
                and actual_value[0] in "'\""
            ):
                actual_value = actual_value[1:-1]
            with self.subTest(frontmatter_key=key):
                self.assertEqual(actual_value, expected_value)

    def test_issue_reference_detection_contract(self):
        _, body = parse_yaml_frontmatter(self.read_skill())
        normalized = self.normalize(body)
        self.assertIn("#<number>", normalized)
        self.assertIn("github issue url", normalized)
        self.assertIn("gh issue view", normalized)
        self.assertRegex(normalized, r"read it before classifying")
        self.assertIn("--json title,body,labels,comments", normalized)
        self.assertRegex(normalized, r"full issue url.{0,120}derive.{0,60}--repo")
        self.assertIn("read-only", normalized)

    def test_intake_preflight_contract(self):
        _, body = parse_yaml_frontmatter(self.read_skill())
        normalized = self.normalize(body)
        self.assertRegex(
            normalized,
            r"at intake.{0,140}git repository.{0,100}codex cli responds",
        )
        self.assertRegex(
            normalized,
            r"use the preflight block in model-routing\.md.{0,160}"
            r"exact codex model.{0,100}before implementation",
        )
        routing = read_reference("model-routing.md")
        preflight_match = re.search(
            r"(?ms)^## Preflight\b.*?(?=\n## |\Z)",
            routing,
        )
        self.assertIsNotNone(
            preflight_match,
            "model-routing.md must contain a clearly labelled preflight block",
        )
        preflight = self.normalize(preflight_match.group(0))
        command_match = re.search(r"```bash\s+(.*?)```", preflight_match.group(0), re.DOTALL)
        self.assertIsNotNone(command_match, "preflight block must contain a shell command")
        command = command_match.group(1)
        command_lower = command.casefold()
        for parameter in (
            "--sandbox read-only",
            "--ephemeral",
            '--model "$codex_model"',
            r'-c "model_reasoning_effort=\"low\""',
        ):
            with self.subTest(preflight_parameter=parameter):
                self.assertIn(parameter, command_lower)
        self.assertIn("-C", command)
        self.assertIn("one-line prompt", preflight)
        self.assertRegex(
            preflight,
            r"exit code 0.{0,80}non-empty model reply",
        )
        self.assertRegex(command, r"(?m)^codex\s+exec\b")
        self.assertNotIn("--output-schema", command)
        self.assertNotIn("--output-last-message", command)

    def test_state_root_matches_fingerprint_exclusion_contract(self):
        _, body = parse_yaml_frontmatter(self.read_skill())
        normalized = self.normalize(body)
        self.assertIn(
            "the state root passed to `quality_state.py init --root` is always "
            "`<project_root>/.claude/quality-state`, because the workspace "
            "fingerprint excludes exactly that path; a different location "
            "re-enters the fingerprint and makes the workflow invalidate its "
            "own verification.",
            normalized,
        )

    def test_runtime_state_ignore_advisory_contract(self):
        _, body = parse_yaml_frontmatter(self.read_skill())
        normalized = self.normalize(body)
        self.assertIn("at intake, verify", normalized)
        self.assertIn("check whether", normalized)
        self.assertIn("git check-ignore", normalized)
        self.assertIn(".claude/quality-state/", normalized)
        self.assertRegex(
            normalized,
            r"not ignored.{0,180}git status.{0,120}committed by accident",
        )
        self.assertIn("!.claude/", normalized)
        self.assertRegex(
            normalized,
            r"negation pattern.{0,160}re-enable",
        )
        self.assertIn("earlier `.claude` rule", normalized)
        self.assertIn("offer to add the ignore rule", normalized)
        self.assertRegex(
            normalized,
            r"do not add it unilaterally.{0,180}\.gitignore.{0,100}approved change scope",
        )
        self.assertRegex(normalized, r"follow-up in the report")
        self.assertRegex(
            normalized,
            r"fingerprint already excludes the directory regardless.{0,120}hygiene rather than correctness",
        )

    def test_issue_requirement_input_contract(self):
        _, body = parse_yaml_frontmatter(self.read_skill())
        normalized = self.normalize(body)
        self.assertRegex(normalized, r"title.{0,80}body.{0,80}comments.{0,100}requirement input")
        self.assertRegex(normalized, r"issue number.{0,100}specific claim")
        self.assertRegex(normalized, r"every factual claim.{0,140}repository")
        self.assertIn("stale", normalized)

    def test_issue_goal_normalization_contract(self):
        _, body = parse_yaml_frontmatter(self.read_skill())
        normalized = self.normalize(body)
        self.assertRegex(normalized, r"quality_state\.py init.{0,180}goal_key")
        self.assertRegex(normalized, r"goal_key.{0,100}task_id.{0,160}durable document directory")
        self.assertRegex(normalized, r"reference.{0,100}too thin.{0,180}issue number.{0,120}one-line summary")
        self.assertRegex(normalized, r"never.{0,100}(?:omit|without).{0,100}issue number")
        self.assertIn("collide", normalized)
        self.assertRegex(normalized, r"show the user.{0,100}enriched goal")

    def test_issue_labels_are_classification_evidence_contract(self):
        _, body = parse_yaml_frontmatter(self.read_skill())
        normalized = self.normalize(body)
        self.assertRegex(normalized, r"labels?.{0,100}(?:additional )?classification evidence")
        self.assertRegex(normalized, r"labels?.{0,120}quoted.{0,100}printed reasons")
        self.assertRegex(normalized, r"labels?.{0,120}never replace.{0,100}risk scan")
        self.assertRegex(normalized, r"missing or wrong label.{0,100}never lowers the mode")
        self.assertIn("scan result stands", normalized)

    def test_issue_content_is_untrusted_data_contract(self):
        _, body = parse_yaml_frontmatter(self.read_skill())
        normalized = self.normalize(body)
        self.assertRegex(normalized, r"issue body or comment.{0,100}data.{0,100}not instructions")
        for term in ("change the mode", "waive a gate", "skip the approval", "alter loop limits", "destructive or external action"):
            with self.subTest(untrusted_effect=term):
                self.assertIn(term, normalized)
        self.assertRegex(normalized, r"asks for any of that.{0,120}open question.{0,120}normal rules")

    def test_issue_reading_has_no_mutation_contract(self):
        _, body = parse_yaml_frontmatter(self.read_skill())
        normalized = self.normalize(body)
        self.assertRegex(normalized, r"reading is allowed.{0,80}writing is not")
        for term in ("post a comment", "edit the body", "change labels", "assignees", "projects", "state", "open or close"):
            with self.subTest(issue_mutation=term):
                self.assertIn(term, normalized)
        self.assertIn("user's actions", normalized)

    def test_issue_unavailable_requires_pasted_requirements_contract(self):
        _, body = parse_yaml_frontmatter(self.read_skill())
        normalized = self.normalize(body)
        self.assertRegex(normalized, r"gh.{0,20}is missing")
        self.assertIn("unauthenticated", normalized)
        self.assertRegex(normalized, r"issue cannot be read.{0,100}(?:say so|ask).{0,100}paste the requirements")
        self.assertRegex(normalized, r"do not guess.{0,120}issue")
        self.assertRegex(normalized, r"never silently proceed.{0,100}terse goal")

    def test_skill_size_and_state_names_contract(self):
        text = self.read_skill()
        _, body = parse_yaml_frontmatter(text)
        self.assertLess(len(text.splitlines()), 500)
        for state in (
            "INTAKE",
            "CLASSIFIED",
            "SPEC_REVIEW",
            "SPEC_PASSED",
            "PLAN_REVIEW",
            "PLAN_PASSED",
            "AWAITING_PLAN_APPROVAL",
            "IMPLEMENTING",
            "CODE_REVIEW",
            "COMPLETED",
            "BLOCKED",
            "NEEDS_REDESIGN",
            "CANCELLED",
        ):
            with self.subTest(state=state):
                self.assertIn(state, body)

    def test_review_round_limits_and_reviewer_isolation_contract(self):
        _, body = parse_yaml_frontmatter(self.read_skill())
        lower = body.casefold()
        for stage, limit in (("spec", 3), ("plan", 2), ("code", 3)):
            with self.subTest(stage=stage):
                self.assertRegex(
                    lower,
                    rf"\b{stage}\b.{{0,240}}(?:at most|max(?:imum)?|limit(?:ed)?).{{0,80}}"
                    rf"{limit}.{{0,30}}round",
                )
        self.assertRegex(
            lower,
            r"every\s+review(?:\s+round)?s?.{0,180}"
            r"(?:launch|invoke|call|start|use).{0,80}(?:new|fresh).{0,80}quality-reviewer",
        )
        self.assertRegex(
            lower,
            r"(?:never|must not|do not).{0,100}(?:resume|continue).{0,120}"
            r"(?:a\s+)?prior.{0,100}reviewer(?:\s+context)?",
        )

    def test_completion_guards_verification_integrity_contract(self):
        _, body = parse_yaml_frontmatter(self.read_skill())
        lower = self.normalize(body)
        self.assertRegex(
            lower,
            r"approve-plan\s+refuses\s+to\s+approve\s+plan\s+content.{0,160}"
            r"digest\s+recorded\s+by\s+its\s+passing\s+plan\s+review",
        )
        self.assertRegex(
            lower,
            r"light\s+has\s+no\s+such\s+review\s+digest.{0,160}"
            r"light\s+never\s+reviews\s+its\s+compact\s+plan",
        )
        self.assertRegex(
            lower,
            r"record-verification\s+refuses\s+a\s+verification\s+path.{0,120}"
            r"not\s+an\s+existing\s+regular\s+file",
        )
        self.assertRegex(
            lower,
            r"code_review\s*->\s*completed\s+refuses\s+unless\s+the\s+verified\s+"
            r"workspace\s+fingerprint\s+equals\s+the\s+artifact\s+digest\s+of\s+the\s+"
            r"last\s+passing\s+code\s+review",
        )

    def test_passed_transition_guard_contract(self):
        _, body = parse_yaml_frontmatter(self.read_skill())
        lower = self.normalize(body)
        for artifact in ("spec", "plan"):
            with self.subTest(artifact=artifact):
                self.assertRegex(
                    lower,
                    rf"(?:refus|reject)\w*\s+{artifact}_review -> {artifact}_passed"
                    rf".{{0,200}}(?:passing|pass).{{0,120}}review",
                )
        self.assertRegex(
            lower,
            r"light.{0,240}(?:exempt|no reviewer round|without a review)",
        )

    def test_reviewer_launch_mode_contract(self):
        _, body = parse_yaml_frontmatter(self.read_skill())
        lower = self.normalize(body)
        self.assertRegex(
            lower,
            r"(?:never|must not|do not).{0,80}(?:give|assign|pass|supply).{0,60}"
            r"name.{0,120}review(?:er)?",
        )
        self.assertRegex(
            lower,
            r"named.{0,160}(?:teammate|in_process_teammate)",
        )
        self.assertRegex(
            lower,
            r"(?:teammate|named).{0,200}final\s+message.{0,120}"
            r"(?:not\s+returned|never\s+returned|is\s+not\s+delivered)",
        )
        self.assertRegex(
            lower,
            r"read-only.{0,200}(?:no\s+other\s+(?:way|channel)|"
            r"only\s+(?:delivery\s+)?channel)",
        )

    def test_prior_supply_rule_contract(self):
        _, body = parse_yaml_frontmatter(self.read_skill())
        lower = body.casefold()
        self.assertRegex(lower, r"round\s*(?:>=|≥)\s*2.{0,180}--prior")
        self.assertRegex(
            lower,
            r"(?:--prior.{0,100}always.{0,30}(?:supplied|provided)|"
            r"always.{0,100}--prior.{0,30}(?:supplied|provided))",
        )
        self.assertRegex(
            lower,
            r"(?:explicitly\s+)?empty.{0,100}open_finding_ids.{0,80}list",
        )

    def test_codex_command_and_flag_safety_contract(self):
        text = self.read_skill()
        _, body = parse_yaml_frontmatter(text)
        lower = body.casefold()
        self.assertRegex(lower, r"model-routing\.md")
        self.assertRegex(lower, r"\bcodex\s+exec\b")

        prohibition = re.compile(r"(?:금지|않는다|never|forbid|prohibited)", re.IGNORECASE)
        forbidden_patterns = (
            r"--skip-git-repo-check",
            r"--full-auto",
            r"--yolo",
            r"sandbox[ -]bypass",
        )
        for forbidden_pattern in forbidden_patterns:
            matching_lines = [
                line
                for line in text.splitlines()
                if re.search(forbidden_pattern, line, re.IGNORECASE)
            ]
            for line in matching_lines:
                with self.subTest(forbidden_flag=forbidden_pattern, line=line):
                    self.assertFalse(
                        re.match(r"\s*codex\s", line, re.IGNORECASE),
                        f"prohibited token appears in runnable command: {line}",
                    )
                    self.assertRegex(line, prohibition, f"no prohibition context: {line}")

        safe_flags = {
            "-C",
            "--sandbox",
            "--ephemeral",
            "--model",
            "-c",
            "--output-schema",
            "--output-last-message",
            "--json",
        }
        self.assertNotIn("```", text)
        routing_text = read_reference("model-routing.md")
        code_blocks = re.findall(r"```[^\n]*\n(.*?)```", routing_text, re.DOTALL)
        self.assertTrue(
            any(re.search(r"\bcodex\s+exec\b", block, re.IGNORECASE) for block in code_blocks),
            "model-routing.md must contain the runnable Codex template",
        )
        for block in code_blocks:
            if not re.search(r"\bcodex\s+exec\b", block, re.IGNORECASE):
                continue
            for line in block.splitlines():
                if prohibition.search(line):
                    continue
                for flag in re.findall(r"(?<!\w)(--?[A-Za-z][A-Za-z0-9-]*)", line):
                    with self.subTest(runnable_flag=flag):
                        self.assertIn(flag, safe_flags)

    def test_single_final_approval_gate_contract(self):
        _, body = parse_yaml_frontmatter(self.read_skill())
        normalized = self.normalize(body)
        self.assertRegex(normalized, r"ask\s+exactly\s+once")
        self.assertRegex(normalized, r"no\s+other\s+user\s+approval\s+gates?")
        self.assertRegex(
            normalized,
            r"clarifying\s+questions?.{0,60}not\s+approval\s+gates?",
        )
        self.assertRegex(
            normalized,
            r"(?:approval.{0,100}immediately\s+before\s+implementation|"
            r"immediately\s+before\s+implementation.{0,100}approval)",
        )

    def test_malformed_review_recovery_contract(self):
        _, body = parse_yaml_frontmatter(self.read_skill())
        normalized = self.normalize(body)
        self.assertRegex(normalized, r"retry.{0,80}once")
        self.assertIn("record-review-error", normalized)
        self.assertRegex(
            normalized,
            r"second.{0,120}(?:failure|malformed|invalid).{0,120}blocked",
        )

    def test_model_unavailability_contract(self):
        _, body = parse_yaml_frontmatter(self.read_skill())
        normalized = self.normalize(body)
        self.assertIn("blocked_model_unavailable", normalized)
        self.assertRegex(normalized, r"never\s+silently\s+substitute")
        self.assertRegex(
            normalized,
            r"(?:reviewer.{0,180}(?:model\s+)?(?:failure|unavailable|cannot\s+launch)|"
            r"(?:failure|unavailable).{0,180}reviewer).{0,180}"
            r"blocked_reviewer_model_unavailable",
        )
        self.assertRegex(
            normalized,
            r"blocked_reviewer_model_unavailable.{0,180}"
            r"(?:without|never).{0,80}(?:change|changing).{0,80}models?",
        )

    def test_safety_prohibition_contract(self):
        _, body = parse_yaml_frontmatter(self.read_skill())
        normalized = self.normalize(body)
        self.assertRegex(
            normalized,
            r"(?:never|must\s+not|does\s+not)\s+(?:automatically\s+)?"
            r"(?:commit|commits).{0,120}(?:push|pushes).{0,120}"
            r"(?:merge|merges).{0,120}(?:deploy|deploys).{0,200}"
            r"(?:production|credential)",
        )
        self.assertRegex(normalized, r"(?:production\s+mutation|mutat\w+\s+production)")
        self.assertRegex(normalized, r"(?:access|expose|read|handle).{0,40}credentials?")

    def test_supporting_links_and_skill_dir_contract(self):
        _, body = parse_yaml_frontmatter(self.read_skill())
        for reference in (
            "references/routing-rules.md",
            "references/brainstorming-policy.md",
            "references/planning-policy.md",
            "references/spec-rubric.md",
            "references/plan-rubric.md",
            "references/code-rubric.md",
            "references/model-routing.md",
            "templates/spec.md",
            "templates/plan.md",
            "templates/report.md",
            "schemas/review.schema.json",
            "schemas/codex-result.schema.json",
            "scripts/quality_state.py",
            "scripts/validate_review.py",
        ):
            with self.subTest(reference=reference):
                self.assertIn(reference, body)
        self.assertIn("quality-reviewer", body)
        self.assertIn("${CLAUDE_SKILL_DIR}", body)

    def test_state_discipline_contract(self):
        _, body = parse_yaml_frontmatter(self.read_skill())
        normalized = self.normalize(body)
        self.assertRegex(
            normalized,
            r"every\s+durable\s+transition.{0,120}quality_state\.py",
        )
        self.assertRegex(
            normalized,
            r"never\s+infer(?:ring)?\s+(?:a\s+)?passed\s+stage.{0,120}"
            r"conversation\s+memory",
        )
        self.assertRegex(normalized, r"artifact.{0,80}sha-?256.{0,80}digest")
        self.assertRegex(normalized, r"resume\s+only.{0,100}select-resume")
        self.assertRegex(
            normalized,
            r"select-resume.{0,140}(?:summary|summarize|show).{0,100}user",
        )
        self.assertRegex(normalized, r"absolute\s+paths?.{0,120}set-artifact")
        self.assertRegex(normalized, r"absolute\s+paths?.{0,120}approvals?")

    def test_artifact_layout_contract(self):
        _, body = parse_yaml_frontmatter(self.read_skill())
        normalized = self.normalize(body)
        self.assertIn("docs/development/", normalized)
        self.assertRegex(
            normalized,
            r"docs/development/.{0,120}(?:yyyy-mm-dd|date).{0,120}slug",
        )
        self.assertRegex(
            normalized,
            r"deterministic.{0,120}(?:numeric|number).{0,120}suffix.{0,120}collision",
        )
        self.assertRegex(
            normalized,
            r"light.{0,240}(?:only|creates\s+only).{0,120}"
            r"(?:durable\s+)?report",
        )
        self.assertIn(".claude/quality-state/<task-id>/compact-plan.md", normalized)
        self.assertRegex(normalized, r"compact\s+plan.{0,120}(?:persist|stored|durable)")

    def test_light_normal_path_uses_direct_approval_edge_contract(self):
        _, body = parse_yaml_frontmatter(self.read_skill())
        light_path_match = re.search(
            r"(?ms)^Light normal path:.*?(?=\n\nLight rework paths)",
            body,
        )
        self.assertIsNotNone(
            light_path_match,
            "SKILL.md must anchor the light normal path in its named paragraph",
        )
        light_path = light_path_match.group(0)
        normalized_light_path = self.normalize(light_path)
        self.assertRegex(
            normalized_light_path,
            r"light\s+normal\s+path:.*?classified\s*→\s*"
            r"awaiting_plan_approval\s+directly",
        )
        self.assertIn("AWAITING_PLAN_APPROVAL", light_path)
        self.assertRegex(
            normalized_light_path,
            r"set-artifact\s+--kind\s+compact_plan.{0,100}absolute\s+path",
        )
        compact_plan_sentence = next(
            (
                sentence
                for sentence in re.split(r"(?<=[.!?])\s+", normalized_light_path)
                if "set-artifact --kind compact_plan" in sentence
            ),
            None,
        )
        self.assertIsNotNone(
            compact_plan_sentence,
            "the light normal path must name its compact-plan registration sentence",
        )
        self.assertNotIn("plan_passed", compact_plan_sentence or "")

    def test_terminal_report_is_registered_before_transition_contract(self):
        _, body = parse_yaml_frontmatter(self.read_skill())
        normalized = self.normalize(body)
        self.assertRegex(
            normalized,
            r"render\s+report\.md\s+from\s+templates/report\.md.{0,180}"
            r"register\s+it\s+with\s+set-artifact\s+--kind\s+report\s+"
            r"\(absolute\s+path\)\s+before\s+transitioning\s+into\s+"
            r"(?:completed|blocked|needs_redesign|cancelled)",
        )

    def test_terminal_report_registration_ordering_contract(self):
        _, body = parse_yaml_frontmatter(self.read_skill())
        terminal_start = body.index("### Terminal")
        terminal_end = body.index("\n## ", terminal_start)
        terminal = self.normalize(body[terminal_start:terminal_end])
        d1 = self.normalize(
            "When the review you are about to record is expected to end the workflow, "
            "because it is the last allowed round without a PASS or it repeats a blocking "
            "finding ID from an earlier round, render report.md and register it with "
            "set-artifact --kind report before calling record-review, while the stage is "
            "still non-terminal."
        )
        d2 = self.normalize(
            "Because record-review and record-review-error transition into NEEDS_REDESIGN "
            "or BLOCKED on their own, set-artifact --kind report is also accepted after the "
            "state is already terminal; register the report there when the terminal transition "
            "has already happened. No other artifact kind may be registered once the state is "
            "terminal."
        )
        d3 = self.normalize(
            "When a helper has already transitioned automatically, register the report in "
            "the terminal state as the Terminal section describes."
        )
        terminal_rows = [
            line
            for line in body.splitlines()
            if line.startswith("| COMPLETED, BLOCKED, NEEDS_REDESIGN, CANCELLED |")
        ]

        self.assertIn(d1, terminal)
        self.assertIn(d2, terminal)
        self.assertEqual(1, len(terminal_rows))
        self.assertIn(d3, self.normalize(terminal_rows[0]))

    def test_post_codex_independent_verification_contract(self):
        _, body = parse_yaml_frontmatter(self.read_skill())
        normalized = self.normalize(body)
        self.assertRegex(
            normalized,
            r"compare.{0,120}(?:actual\s+)?git\s+changes.{0,120}changed_files",
        )
        self.assertRegex(
            normalized,
            r"preserv\w*.{0,100}initial.{0,100}dirty\s+paths?",
        )
        self.assertRegex(
            normalized,
            r"target(?:ed)?\s+tests.*full\s+(?:suite|tests?).*type\s+check.*"
            r"lint.*build.*(?:required\s+)?(?:e2e|end-to-end).*manual",
        )
        self.assertRegex(
            normalized,
            r"(?:missing|absent).{0,100}(?:categor(?:y|ies)|checks?).{0,160}not\s+configured",
        )
        self.assertRegex(
            normalized,
            r"not\s+configured.{0,160}(?:never|not).{0,80}passed",
        )
        self.assertRegex(
            normalized,
            r"strict.{0,220}(?:cannot|must\s+not|requires?).{0,160}"
            r"high-risk.{0,120}(?:verification\s+path|e2e|end-to-end)",
        )

    def test_scope_change_invalidates_downstream_contract(self):
        _, body = parse_yaml_frontmatter(self.read_skill())
        normalized = self.normalize(body)
        self.assertRegex(
            normalized,
            r"scope\s+change.{0,120}after\s+approval.{0,180}"
            r"invalidat\w*.{0,180}(?:affected\s+)?(?:spec|plan).{0,100}"
            r"digest.{0,180}downstream\s+verification.{0,180}"
            r"(?:return|go\s+back).{0,180}earliest\s+affected\s+review\s+stage",
        )

    def test_skill_contains_no_unfinished_markers(self):
        marker_pattern = re.compile(
            r"\b(?:" + "T" + "[B]D|" + "T" + "[O]DO" + r")\b",
            re.IGNORECASE,
        )
        self.assertIsNone(marker_pattern.search(self.read_skill()), str(self.SKILL_PATH))


class QualityStateGitignoreContentTests(unittest.TestCase):
    REPO_ROOT = find_repo_root(Path(__file__).resolve())
    GITIGNORE_PATH = REPO_ROOT / ".gitignore"

    def test_runtime_state_ignore_rule_preserves_existing_entries(self):
        lines = self.GITIGNORE_PATH.read_text(encoding="utf-8").splitlines()
        self.assertIn(
            ".claude/quality-state/",
            lines,
            f"missing runtime state ignore line: {self.GITIGNORE_PATH}",
        )
        for existing_entry in (".env", ".DS_Store", "__pycache__/"):
            with self.subTest(existing_entry=existing_entry):
                self.assertIn(existing_entry, lines)


if __name__ == "__main__":
    unittest.main()
