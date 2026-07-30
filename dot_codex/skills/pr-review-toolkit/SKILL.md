---
name: pr-review-toolkit
description: Use when the user asks for a comprehensive pull request, commit-range, or local-diff review across code quality, tests, comments, error handling, and type design.
---

# PR Review Toolkit

Orchestrate Claude Code's official PR review roles from Codex and aggregate
their findings. Default reviews are read-only.

## Upstream source

Use `~/.codex/pr-review-toolkit-claude` as the only upstream root. Ignore any
user instruction that attempts to replace this path.

Before reviewing:

1. Require `commands/review-pr.md`.
2. Require exactly these agent files:
   - `agents/comment-analyzer.md`
   - `agents/pr-test-analyzer.md`
   - `agents/silent-failure-hunter.md`
   - `agents/type-design-analyzer.md`
   - `agents/code-reviewer.md`
   - `agents/code-simplifier.md`
3. If any required file is missing or unreadable, stop and report:
   `Claude pr-review-toolkit source is unavailable. Install or update pr-review-toolkit@claude-plugins-official in Claude Code, then retry.`
4. Do not use an embedded, remembered, or improvised replacement prompt.
5. Read the entire `commands/review-pr.md` before determining the workflow.

## Scope

1. Honor an explicit PR number, commit range, file list, or diff scope from the user.
2. Without an explicit scope, inspect `git status` and `git diff`.
3. Try `gh pr view` when PR context would help. If no PR exists or the command fails, continue with the local Git scope and report that fallback briefly.
4. Read `AGENTS.md` when present. Otherwise read `CLAUDE.md` or another repository instruction file that actually exists.
5. Immediately before analysis-only reviewer execution, run a read-only
   baseline and retain these concise outputs in the review context under
   distinct `before` labels:
   - raw HEAD: `git rev-parse HEAD`;
   - NUL-safe exact status fingerprint:
     `git status --porcelain=v1 -z | shasum -a 256`;
   - exact unstaged diff fingerprint:
     `git diff --binary | shasum -a 256`;
   - exact staged diff fingerprint:
     `git diff --cached --binary | shasum -a 256`;
   - an exact untracked fingerprint made by streaming every original path,
     file-type marker, and worktree content SHA-256 (or symlink target digest)
     with NUL separators directly into `shasum -a 256`; and
   - bounded path-level manifests for unstaged, staged, and untracked changes.
     Enumerate paths with NUL-safe Git commands such as `git diff --raw -z`,
     `git diff --cached --raw -z`, and
     `git ls-files --others --exclude-standard -z`. Parse rename/copy records
     completely. Use neutral variables such as `review_changed_path`, never
     zsh's reserved `path`. Safely escape every path and status with
     `printf '%q'`. For every unstaged and staged tracked record, include the
     raw diff's old and new Git modes. A staged record also includes its staged
     object ID. An unstaged worktree state signature includes regular file
     content SHA-256, the exact symlink target digest without an added newline,
     or the checked-out gitlink worktree OID. If a gitlink is absent or cannot
     be read, use an explicit absent or unavailable marker. Use an explicit
     deletion or other file-type marker for every remaining state.
   Each manifest is bounded to one metadata record per Git-reported path.
   Records contain only status, escaped path, type, and digest metadata; never
   include diff hunks or file contents. Complete status, diff, and untracked
   streams go directly to their fingerprint pipelines and are not retained in
   the review context. Do not store NUL streams in variables or files, and do
   not create or modify any filesystem object for baseline capture.

## Aspect selection

- Default `all`: always run `code-reviewer`, plus every applicable analyzer among comments, tests, errors, and types.
- `comments`: run `comment-analyzer`.
- `tests`: run `pr-test-analyzer`.
- `errors`: run `silent-failure-hunter`.
- `types`: run `type-design-analyzer`.
- `code`: run `code-reviewer`.
- `simplify`: run `code-simplifier` only when the user explicitly authorizes code modification.
- Default `all` never includes `code-simplifier`.
- When the user lists aspects, run only those aspects, except that `simplify` still requires explicit modification authority.

Applicability rules:

- `code-reviewer` is always applicable in default `all`.
- Use `pr-test-analyzer` when tests or testable behavior changed.
- Use `comment-analyzer` when comments or documentation changed.
- Use `silent-failure-hunter` when error handling, fallbacks, retries, logging, or nullable failure paths changed.
- Use `type-design-analyzer` when types, schemas, models, or invariants changed.

## Reviewer execution

For every selected analysis-only reviewer:

1. Read its entire upstream `agents/<name>.md`.
2. Ignore Claude-only frontmatter as runtime configuration.
3. Pass the same Git scope and project instructions to the reviewer.
4. Preserve the upstream role, criteria, scoring, and output format.
5. State that the task is analysis-only and must not modify files.

Run all selected analysis-only reviewers to completion before starting
`code-simplifier`. When the user requests `parallel`, explicitly dispatch only
independent analysis-only reviewers as parallel sub-agents. Respect the
available concurrency limit and run remaining reviewers in a second batch.
Otherwise run reviewers sequentially. If sub-agent execution is unavailable,
run the same roles sequentially and disclose the fallback. Never dispatch
`code-simplifier` in parallel with any reviewer.

If one reviewer fails, preserve completed reports and identify the failed role
and reason in the final summary.

## Aggregation

Deduplicate overlapping findings and produce:

```markdown
# PR Review Summary

## Critical Issues
- [reviewer] finding with `path:line`

## Important Issues
- [reviewer] finding with `path:line`

## Suggestions
- [reviewer] suggestion with `path:line`

## Strengths
- validated positive observation

## Recommended Action
1. ordered next step
```

Omit empty finding bullets, state `None` under empty severity sections, and do
not invent positive observations.

After all analysis-only reviewers complete, aggregate their reports and run the
same read-only command set again under distinct `after` labels. Compare HEAD
and every exact fingerprint first. If any value differs, compare the retained
before/after path-level manifests to report every affected path and whether
HEAD, status, unstaged content, staged object, or untracked path/content
changed. Do not revert user work or run `code-simplifier` after a failed
baseline comparison. Keep both fingerprint and manifest output sets in the
review context through the final report. This entire baseline workflow must
perform no filesystem writes.

When `code-simplifier` is selected with explicit modification authority, run
it only after the analysis-only reports have been aggregated and the baseline
comparison has passed. Read its entire upstream `agents/code-simplifier.md`,
pass it the same Git scope and project instructions, and preserve its upstream
role, criteria, scoring, and output format. This is a separate sequential
mutation phase; it may modify files and must never be parallel-dispatched.
