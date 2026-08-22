---
name: pr-review-toolkit-code-reviewer
description: Use only for a code-quality-only review of the selected diff — high-confidence bugs, project-rule violations, and significant quality issues. For a comprehensive review that also covers tests, comments, error handling, and type design, use pr-review-toolkit instead.
---

# PR Review Toolkit: Code Reviewer

Analyze only; do not modify files.

## Required workflow

1. Resolve `~/.codex/pr-review-toolkit-claude/agents/code-reviewer.md`.
2. If it is missing or unreadable, stop and report: `Claude pr-review-toolkit source is unavailable. Install or update pr-review-toolkit@claude-plugins-official in Claude Code, then retry.`
3. Read the entire upstream file before reviewing.
4. Ignore Claude-only frontmatter as runtime configuration, but follow the body’s confidence threshold, review criteria, and output format.
5. Review the exact diff, PR, commit range, or files supplied by the caller.
6. Replace the upstream assumption that project rules live in `CLAUDE.md`: use `AGENTS.md` when present, otherwise use `CLAUDE.md` or another repository instruction file that actually exists.
7. Return only findings that satisfy the upstream confidence threshold, with file and line references. Do not edit code.
