---
name: pr-review-toolkit-code-simplifier
description: Use only when the user explicitly asks to modify recently changed code for clarity and maintainability while preserving behavior.
---

# PR Review Toolkit: Code Simplifier

This is the only mutating specialist in the toolkit. Do not trigger it from a
default or read-only review.

## Required workflow

1. Confirm the user explicitly requested both simplification and code modification. Otherwise stop and offer analysis-only suggestions.
2. Resolve `~/.codex/pr-review-toolkit-claude/agents/code-simplifier.md`.
3. If it is missing or unreadable, stop and report: `Claude pr-review-toolkit source is unavailable. Install or update pr-review-toolkit@claude-plugins-official in Claude Code, then retry.`
4. Read the entire upstream file before making changes.
5. Ignore Claude-only frontmatter as runtime configuration, but follow the body’s behavior-preservation and clarity rules.
6. Limit edits to the exact diff, commit range, or files supplied by the caller.
7. Replace hard-coded upstream project conventions with `AGENTS.md` when present, otherwise `CLAUDE.md` or another repository instruction file that actually exists.
8. Run focused tests or static checks for the edited files and report every changed file.
