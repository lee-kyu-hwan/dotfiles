"""Opt-in probes for the production structured-output model commands."""
import importlib.util
import json
import os
import pathlib
import sys
import unittest


SKILL_ROOT = pathlib.Path(__file__).resolve().parents[1]
LIVE_ENABLED = os.environ.get("DUAL_REVIEW_LIVE_API") == "1"


def _load_review_state():
    path = SKILL_ROOT / "scripts/review_state.py"
    spec = importlib.util.spec_from_file_location("dual_review_live_review_state", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_evidence(root, name, command, response):
    destination = root / name
    destination.mkdir(parents=True, exist_ok=False)
    (destination / "command.json").write_text(
        json.dumps(list(command), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (destination / "stdout.txt").write_text(response.get("raw", ""), encoding="utf-8")
    (destination / "stderr.txt").write_text(response.get("stderr", ""), encoding="utf-8")
    (destination / "result.json").write_text(
        json.dumps(response, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8"
    )


@unittest.skipUnless(LIVE_ENABLED, "set DUAL_REVIEW_LIVE_API=1 to run model probes")
class ProductionSchemaLiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        evidence = os.environ.get("DUAL_REVIEW_EVIDENCE_DIR")
        if not evidence:
            raise RuntimeError("DUAL_REVIEW_EVIDENCE_DIR is required for live probes")
        cls.evidence_root = pathlib.Path(evidence)
        cls.evidence_root.mkdir(parents=True, exist_ok=True)
        cls.review_state = _load_review_state()

    def _call(self, name, source, command_builder, prompt):
        commands = []

        def recording_builder(called_source, output_path):
            command = tuple(command_builder(called_source, output_path))
            commands.append(command)
            return command

        adapter = self.review_state.SubprocessAdapter(
            recording_builder, repository_root=SKILL_ROOT, timeout_seconds=300
        )
        handle = adapter.start(source, prompt)
        self.assertEqual(len(commands), 1)
        self.assertFalse(handle[2].exists(), "prompt must already be unlinked after stdin handoff")
        self.assertIsNone(handle[0].stdin, "the child must receive a finite regular-file stdin")
        response = adapter.read(handle)
        _write_evidence(self.evidence_root, name, commands[0], response)
        return commands[0], response

    def _assert_success(self, name, command, response, expected_key):
        self.assertEqual(response.get("status"), "ok", f"{name}: {response}")
        self.assertIsInstance(response.get("payload"), dict, f"{name}: {response}")
        self.assertIn(expected_key, response["payload"], f"{name}: {response}")
        if command[0] == "codex":
            self.assertEqual(command[-1], "-")

    def _call_claude_with_schema_diagnostic(self, name, schema_name, prompt, expected_key):
        canonical = self.review_state.build_claude_command(schema_name=schema_name)
        command, response = self._call(name, "claude", lambda _source, _output: canonical, prompt)
        if response.get("status") == "ok":
            self._assert_success(name, command, response, expected_key)
            return
        diagnostic_text = (response.get("stderr", "") + "\n" + response.get("raw", "")).lower()
        if "schema" not in diagnostic_text:
            self.fail(f"{name} failed for a reason other than schema rejection: {response}")

        retry_schema = json.loads(canonical[canonical.index("--json-schema") + 1])
        retry_schema.pop("$schema", None)
        retry_command = list(canonical)
        retry_command[retry_command.index("--json-schema") + 1] = json.dumps(
            retry_schema, ensure_ascii=False, separators=(",", ":")
        )
        _, retry = self._call(
            name + "-without-root-schema",
            "claude",
            lambda _source, _output: tuple(retry_command),
            prompt,
        )
        if retry.get("status") == "ok":
            (self.evidence_root / (name + "-diagnosis.json")).write_text(
                json.dumps({"diagnosis": "shared_schema_root_annotation_must_be_removed"}, indent=2),
                encoding="utf-8",
            )
            self.fail(f"{name}: $schema-only retry succeeded; update all shared schemas and rerun all gates")
        (self.evidence_root / (name + "-diagnosis.json")).write_text(
            json.dumps(
                {"reason": "CLAUDE_SCHEMA_INCOMPATIBLE", "status": "NEEDS_REDESIGN"},
                indent=2,
            ),
            encoding="utf-8",
        )
        self.fail(f"{name}: CLAUDE_SCHEMA_INCOMPATIBLE; $schema-only retry also failed")

    def test_production_structured_output_schemas(self):
        codex_reviewer = lambda _source, output: self.review_state.build_codex_command(
            SKILL_ROOT, "reviewer.schema.json", output
        )
        command, response = self._call(
            "codex-reviewer",
            "codex",
            codex_reviewer,
            "Return a valid reviewer result with verdict ok, a short summary, no findings, and no next steps.",
        )
        self._assert_success("codex-reviewer", command, response, "findings")

        codex_critique = lambda _source, output: self.review_state.build_codex_command(
            SKILL_ROOT, "critique.schema.json", output
        )
        command, response = self._call(
            "codex-critique",
            "codex",
            codex_critique,
            "Return a valid critique result with an empty critiques array.",
        )
        self._assert_success("codex-critique", command, response, "critiques")

        self._call_claude_with_schema_diagnostic(
            "claude-critique",
            "critique.schema.json",
            "Return a valid critique result with an empty critiques array.",
            "critiques",
        )
        self._call_claude_with_schema_diagnostic(
            "claude-synthesis",
            "synthesis.schema.json",
            "Return a valid synthesis result with an empty decisions array.",
            "decisions",
        )


if __name__ == "__main__":
    unittest.main()
