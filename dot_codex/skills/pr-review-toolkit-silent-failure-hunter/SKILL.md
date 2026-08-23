---
name: pr-review-toolkit-silent-failure-hunter
description: Use when reviewing changed error handling, catch blocks, fallbacks, retries, logging, or code that may suppress failures.
---

# PR Review Toolkit: Silent Failure Hunter

Analyze only; do not modify files.

## Required workflow

1. Resolve `~/.codex/pr-review-toolkit-claude/agents/silent-failure-hunter.md`.
2. If it is missing or unreadable, stop and report: `Claude pr-review-toolkit source is unavailable. Install or update pr-review-toolkit@claude-plugins-official in Claude Code, then retry.`
3. Read the entire upstream file before reviewing.
4. Ignore Claude-only frontmatter as runtime configuration, but follow the body’s error-handling principles, severity rules, and output format.
5. Review the exact diff, PR, commit range, or files supplied by the caller.
6. Use `AGENTS.md` as project guidance when present; otherwise use `CLAUDE.md` or another repository instruction file that actually exists. Treat upstream references to project-specific logging APIs as applicable only when those APIs exist in the current repository.
7. Return findings with file and line references. Do not edit error handling or logging.
