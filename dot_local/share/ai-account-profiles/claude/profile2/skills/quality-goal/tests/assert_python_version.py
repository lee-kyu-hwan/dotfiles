"""Require the Python version used by deterministic checks."""

import sys


def is_supported(version_info):
    """Return whether a version tuple supports the quality-goal test suite."""
    return tuple(version_info[:2]) >= (3, 12)


if __name__ == "__main__":
    raise SystemExit(0 if is_supported(sys.version_info) else 1)
