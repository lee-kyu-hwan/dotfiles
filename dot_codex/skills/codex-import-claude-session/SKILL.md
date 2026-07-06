---
name: codex-import-claude-session
description: Use when Codex needs to continue from a Claude Code conversation, import a Claude transcript JSONL, recover from /codex:transfer failing to identify the current Claude transcript, or create a resumable Codex thread from ~/.claude/projects.
---

# Codex Import Claude Session

## Overview

Import Claude Code session history into Codex from the Codex side. Use this when Claude's
`/codex:transfer` cannot see `CODEX_COMPANION_TRANSCRIPT_PATH`, or when the user gives a
Claude transcript JSONL path and wants Codex to resume that context.

## Workflow

1. Identify the intended workspace root. Use the current working directory unless the user names
   another repo or worktree.
2. Find the Claude transcript:
   - Prefer a user-provided `.jsonl` path.
   - Otherwise run `scripts/import-claude-session.mjs --list --cwd <workspace>` and choose the
     newest candidate for that workspace.
3. Import it with `scripts/import-claude-session.mjs --cwd <workspace>` or with
   `--source <path>` when the candidate is explicit.
4. Report the `Codex session ID` and `codex resume <session-id>` command exactly.

## Script

Run from this skill directory:

```bash
node scripts/import-claude-session.mjs --cwd /path/to/workspace --list
node scripts/import-claude-session.mjs --cwd /path/to/workspace
node scripts/import-claude-session.mjs --cwd /path/to/workspace --source /path/to/session.jsonl
```

Useful flags:

| Flag | Use |
| --- | --- |
| `--list` | Print candidate Claude JSONL transcripts without importing. |
| `--source <path>` | Import this exact Claude transcript. |
| `--cwd <path>` | Resolve the Claude project and Codex import workspace. |
| `--json` | Emit machine-readable output. |
| `--dry-run` | Show the command that would run. |
| `--plugin-root <path>` | Use a specific Claude Codex plugin root. |

The script shells out to the Claude plugin's `codex-companion.mjs transfer --source ...`.
If no plugin root is supplied, it uses the newest installed
`~/.claude/plugins/cache/openai-codex/codex/*/scripts/codex-companion.mjs`.

## Common Failures

| Symptom | Meaning | Action |
| --- | --- | --- |
| `Could not identify the current Claude transcript` | Claude did not export `CODEX_COMPANION_TRANSCRIPT_PATH`. | Use `--list`, then retry with `--source`. |
| `Claude session source must be a JSONL file` | The selected path is not a transcript. | Choose a `~/.claude/projects/**/<uuid>.jsonl` file. |
| `Codex CLI is not installed` | The companion script cannot call Codex. | Run `/codex:setup` in Claude or install/login to Codex locally. |
| No candidates found | The workspace path does not match a Claude project directory. | Pass the exact transcript with `--source`. |

## Guardrails

- Do not import arbitrary files outside `~/.claude/projects`; the companion script rejects them.
- If multiple candidates exist, choose the newest only when it is clearly in the requested
  workspace directory. Otherwise show candidates and ask the user which one to import.
- Do not edit Claude transcript files. They are source history artifacts.
