"""Assert that all base quality-goal tests remain present."""

import re
import subprocess
import sys
from pathlib import Path


TEST_PATHS = (
    "dot_claude/skills/quality-goal/tests/test_content_contracts.py",
    "dot_claude/skills/quality-goal/tests/test_quality_state.py",
    "dot_claude/skills/quality-goal/tests/test_validate_review.py",
    "dot_claude/skills/quality-goal/tests/test_revision_check.py",
)


def _test_names(contents):
    return set(re.findall(r"^\s*def (test_\w+)", contents, re.MULTILINE))


def _base_contents(revision, path):
    result = subprocess.run(
        ["git", "show", f"{revision}:{path}"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def main(argv=None):
    revision = (argv or sys.argv[1:])[0]
    missing = set()
    for path in TEST_PATHS:
        missing.update(_test_names(_base_contents(revision, path)) - _test_names(Path(path).read_text(encoding="utf-8")))
    assert not missing, f"missing test names: {sorted(missing)}"
    print("기존 테스트 보존")


if __name__ == "__main__":
    main()
