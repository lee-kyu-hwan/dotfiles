---
name: pr-review-toolkit-pr-test-analyzer
description: Use when reviewing a pull request or code diff for behavioral test coverage, critical gaps, edge cases, and test quality.
---

# PR Review Toolkit: PR Test Analyzer

Analyze only; do not modify files.

## Required workflow

1. Resolve `~/.codex/pr-review-toolkit-claude/agents/pr-test-analyzer.md`.
2. If it is missing or unreadable, stop and report: `Claude pr-review-toolkit source is unavailable. Install or update pr-review-toolkit@claude-plugins-official in Claude Code, then retry.`
3. Read the entire upstream file before reviewing.
4. Ignore Claude-only frontmatter as runtime configuration, but follow the body’s role, rating scale, prioritization rules, and output format.
5. Review the exact diff, PR, commit range, or files supplied by the caller.
6. Use `AGENTS.md` as project guidance when present; otherwise use `CLAUDE.md` or another repository instruction file that actually exists.
7. Report behavioral gaps and brittle tests with file and line references. Do not add or edit tests.
