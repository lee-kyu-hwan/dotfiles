"""Assert that protected SKILL.md sections match a base revision."""

import re
import subprocess
import sys
from pathlib import Path


PRESERVED_SECTIONS = (
    "### Plan",
    "### Approval",
    "### Implementation",
    "### Code review",
    "## Independent verification",
    "## Safety rules",
    "## Review invocation contract",
    "## Codex invocation contract",
)
SKILL_PATH = "dot_claude/skills/quality-goal/SKILL.md"


def _sections(contents):
    chunks = re.split(rb"(?=^#{2,3} )", contents, flags=re.MULTILINE)
    return {
        chunk.splitlines()[0]: chunk
        for chunk in chunks
        if chunk.startswith((b"## ", b"### "))
    }


def _base_contents(revision):
    result = subprocess.run(
        ["git", "show", f"{revision}:{SKILL_PATH}"],
        check=True,
        capture_output=True,
    )
    return result.stdout


def main(argv=None):
    revision = (argv or sys.argv[1:])[0]
    base_sections = _sections(_base_contents(revision))
    current_sections = _sections(Path(SKILL_PATH).read_bytes())
    for name in PRESERVED_SECTIONS:
        encoded_name = name.encode("utf-8")
        assert base_sections.get(encoded_name) == current_sections.get(encoded_name), name
    print("보존 대상 절 불변")


if __name__ == "__main__":
    main()
