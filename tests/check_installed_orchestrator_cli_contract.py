#!/opt/homebrew/bin/python3
"""Help-only installed CLI release gate for orchestrator role launchers."""

from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tomllib


ROOT = Path(__file__).resolve().parents[1]
ROLE_MANIFEST = ROOT / "dot_config/ai-session/roles.toml"
FROZEN_EVIDENCE = (
    ROOT
    / "docs/development/2026-09-15-103-orchestrator-permission-profiles-2"
    / "authoritative-inputs.md"
)
EXPECTED_VERSIONS = {"codex": "0.154.0", "claude": "2.1.272"}
EXPECTED_RANGES = {
    "codex": ">=0.154.0,<0.155.0",
    "claude": ">=2.1.269,<2.2.0",
}
EXPECTED_REQUIRED = {
    "codex": ["--model", "--sandbox", "--ask-for-approval"],
    "claude": ["--append-system-prompt", "--settings", "--plugin-dir"],
}
EXPECTED_FORBIDDEN = {
    "codex": ["--dangerously-bypass-approvals-and-sandbox", "--full-auto"],
    "claude": ["--append-system-prompt-file", "--plugin-url"],
}


def version_tuple(value: str) -> tuple[int, int, int]:
    match = re.search(r"(?<![0-9])(\d+)\.(\d+)\.(\d+)(?![0-9])", value)
    if match is None:
        raise ValueError("installed CLI version output is invalid")
    return tuple(int(part) for part in match.groups())


def range_bounds(value: str) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    match = re.fullmatch(
        r">=(\d+)\.(\d+)\.(\d+),<(\d+)\.(\d+)\.(\d+)", value
    )
    if match is None:
        raise ValueError("role manifest CLI range is invalid")
    parts = tuple(int(part) for part in match.groups())
    return parts[:3], parts[3:]


def help_advertises(help_text: str, option: str) -> bool:
    return re.search(
        rf"(?<![A-Za-z0-9_-]){re.escape(option)}(?![A-Za-z0-9_-])",
        help_text,
    ) is not None


def probe(provider: str) -> tuple[str, str]:
    executable = shutil.which(provider)
    if executable is None:
        raise RuntimeError(f"{provider} CLI is not installed")
    outputs = []
    for argument in ("--version", "--help"):
        result = subprocess.run(
            [executable, argument],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(f"{provider} {argument} failed")
        outputs.append(result.stdout + result.stderr)
    return outputs[0], outputs[1]


def main() -> int:
    if os.environ.get("AI_SESSION_CLI_PROBE_MODE") != "help-only":
        print("installed CLI gate requires AI_SESSION_CLI_PROBE_MODE=help-only", file=sys.stderr)
        return 1
    try:
        with ROLE_MANIFEST.open("rb") as stream:
            manifest = tomllib.load(stream)
        evidence = FROZEN_EVIDENCE.read_text(encoding="utf-8")
        for provider, expected_version in EXPECTED_VERSIONS.items():
            contracts = [
                {
                    "cli_version_range": role[provider].get("cli_version_range"),
                    "cli_required_options": role[provider].get("cli_required_options"),
                    "cli_forbidden_options": role[provider].get("cli_forbidden_options"),
                }
                for role in manifest["roles"].values()
            ]
            first = contracts[0]
            if any(contract != first for contract in contracts[1:]):
                raise ValueError(f"{provider} CLI contract differs by role")
            if first != {
                "cli_version_range": EXPECTED_RANGES[provider],
                "cli_required_options": EXPECTED_REQUIRED[provider],
                "cli_forbidden_options": EXPECTED_FORBIDDEN[provider],
            }:
                raise ValueError(f"{provider} CLI policy differs from the approved contract")
            if expected_version not in evidence:
                raise ValueError(f"{provider} frozen version evidence is missing")
            version_output, help_output = probe(provider)
            installed_version = version_tuple(version_output)
            if installed_version != version_tuple(expected_version):
                raise ValueError(f"{provider} installed version differs from frozen evidence")
            lower, upper = range_bounds(first["cli_version_range"])
            if not lower <= installed_version < upper:
                raise ValueError(f"{provider} installed version is outside the approved range")
            required = first["cli_required_options"]
            if any(not help_advertises(help_output, option) for option in required):
                raise ValueError(f"{provider} required help option is missing")
            if provider == "claude" and help_advertises(
                help_output, "--append-system-prompt-file"
            ):
                raise ValueError("Claude unsupported prompt-file surface changed")
        print("installed orchestrator CLI help-only contract: ok")
        return 0
    except (OSError, RuntimeError, subprocess.SubprocessError, ValueError) as error:
        print(f"installed orchestrator CLI help-only contract: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
