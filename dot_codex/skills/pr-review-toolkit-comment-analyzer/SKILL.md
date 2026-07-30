---
name: pr-review-toolkit-comment-analyzer
description: Use when reviewing changed code comments or documentation for accuracy, maintainability, misleading claims, or comment rot.
---

# PR Review Toolkit: Comment Analyzer

Analyze only; do not modify files.

## Required workflow

1. Resolve `~/.codex/pr-review-toolkit-claude/agents/comment-analyzer.md`.
2. If it is missing or unreadable, stop and report: `Claude pr-review-toolkit source is unavailable. Install or update pr-review-toolkit@claude-plugins-official in Claude Code, then retry.`
3. Read the entire upstream file before reviewing.
4. Ignore Claude-only frontmatter as runtime configuration, but follow the body’s role, criteria, and output format.
5. Review the exact diff, PR, commit range, or files supplied by the caller.
6. Use `AGENTS.md` as project guidance when present; otherwise use `CLAUDE.md` or another repository instruction file that actually exists.
7. Return findings with file and line references. Do not edit comments, documentation, or code.
