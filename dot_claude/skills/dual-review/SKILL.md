---
name: dual-review
version: 1.2.0
description: Run independent read-only reviews, cross-critique them, and render a local report.
argument-hint: "[--base <ref>] [--rounds 1|2]"
disable-model-invocation: true
model: claude
effort: high
---

# Dual review

Parse the requested target, then invoke `scripts/review_state.py` from the target
repository. Its `main()` entrypoint resolves the base and diff snapshot, starts the
five Claude producers and the read-only Codex process before reading any result,
runs cross critique and fresh-Claude synthesis, and writes separated run artifacts.
Do not alter the constructed round-zero prompt strings before dispatch.

Use these five Claude finding producers only: `pr-review-toolkit:code-reviewer`,
`pr-test-analyzer`, `comment-analyzer`, `silent-failure-hunter`, and
`type-design-analyzer`. Use the reviewer schema for the Codex
read-only command. A fresh Claude context, not Codex, synthesizes the anonymous view.

Use [operation.md](references/operation.md) for invocation boundaries and
[verification.md](references/verification.md) for local checks.
