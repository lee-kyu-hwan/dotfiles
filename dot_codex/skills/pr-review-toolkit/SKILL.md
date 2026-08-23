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

Run check 1 first. Run check 2 **after `## Aspect selection` has determined which
reviewers this run dispatches** — it cannot be evaluated earlier, because the
dispatch set depends on the scope resolved in `## Scope`. The six paths below are
the candidate set, not a required set.

1. Require `commands/review-pr.md`.
2. Require the agent file behind every reviewer this run will dispatch:
   - `agents/comment-analyzer.md`
   - `agents/pr-test-analyzer.md`
   - `agents/silent-failure-hunter.md`
   - `agents/type-design-analyzer.md`
   - `agents/code-reviewer.md`
   - `agents/code-simplifier.md`
   Do not require an agent file this run will not dispatch. Upstream may add
   agent files over time; an unrecognized extra file is not a failure.
3. If a required file is missing or unreadable, stop and report:
   `Claude pr-review-toolkit source is unavailable. Install or update pr-review-toolkit@claude-plugins-official in Claude Code, then retry.`
4. Do not use an embedded, remembered, or improvised replacement prompt.
5. Read `commands/review-pr.md` in full before determining the workflow. It is
   upstream context, not the controlling spec: where it conflicts with this
   document — aspect selection, `code-simplifier` authorization, output format,
   or the baseline requirement — this document takes precedence.

## Scope

1. Honor an explicit PR number, commit range, file list, or diff scope from the user.
2. Without an explicit scope, inspect
   `git --no-optional-locks -c core.fsmonitor=false status` and
   `git --no-optional-locks -c core.fsmonitor=false diff --no-ext-diff --no-textconv`.
3. Try `gh pr view` when PR context would help. If no PR exists or the command fails, continue with the local Git scope and report that fallback briefly.
4. Read `AGENTS.md` when present. Otherwise read `CLAUDE.md` or another repository instruction file that actually exists.
5. Immediately before entering the analysis phase, run a read-only baseline
   and retain these concise outputs in the review context under distinct
   `before` labels:
   - raw HEAD: `git rev-parse HEAD`;
   - NUL-safe exact status fingerprint:
     `git --no-optional-locks -c core.fsmonitor=false status --porcelain=v1 -z | shasum -a 256`;
   - exact unstaged diff fingerprint:
     `git --no-optional-locks -c core.fsmonitor=false diff --no-ext-diff --no-textconv --binary | shasum -a 256`;
   - exact staged diff fingerprint:
     `git --no-optional-locks -c core.fsmonitor=false diff --cached --no-ext-diff --no-textconv --binary | shasum -a 256`;
   - an exact untracked fingerprint made by streaming every original path,
     type/mode metadata, and exactly one alternative: a regular content hash
     (SHA-256), an exact symlink-target hash (SHA-256 of target bytes without
     an added newline), or a deterministic other-type marker. Separate fields
     with NUL bytes and stream them directly into `shasum -a 256`; and
   - bounded path-level manifests for unstaged, staged, and untracked changes.
     Enumerate paths with NUL-safe Git commands such as
     `git --no-optional-locks -c core.fsmonitor=false diff --no-ext-diff --no-textconv --raw -z`,
     `git --no-optional-locks -c core.fsmonitor=false diff --cached --no-ext-diff --no-textconv --raw -z`,
     and `git --no-optional-locks -c core.fsmonitor=false ls-files --others --exclude-standard -z`.
     Parse rename/copy records completely. Use neutral variables such as
     `review_changed_path`, never zsh's reserved `path`. Safely escape every
     path and status with `printf '%q'`. For every unstaged and staged tracked
     record, include the raw diff's old and new Git modes. A staged record also
     includes its staged object ID. An unstaged worktree state signature
     includes regular file content SHA-256, the exact symlink target digest
     without an added newline, or the checked-out gitlink worktree OID. If a
     gitlink is absent or cannot be read, use an explicit absent or unavailable
     marker. Use an explicit deletion or other file-type marker for every
     remaining state.
   Each manifest is bounded to one metadata record per Git-reported path.
   Records contain only status, escaped path, type, and digest metadata; never
   include diff hunks or file contents. Complete status, diff, and untracked
   streams go directly to their fingerprint pipelines and are not retained in
   the review context. Do not store NUL streams in variables or files, and do
   not create or modify any filesystem object for baseline capture.
   Keep `--no-optional-locks` and `-c core.fsmonitor=false` on status,
   `ls-files`, and every diff command, and keep `--no-ext-diff --no-textconv`
   on every diff command.
   These command-local controls prevent configured fsmonitor processes/hooks,
   external diff commands, textconv commands, and optional index refresh
   writes. Do not change repository config or untracked-cache settings.

## Aspect selection

- Default `all`: always run `code-reviewer`, plus every applicable analyzer among comments, tests, errors, and types.
- `comments`: run `comment-analyzer`.
- `tests`: run `pr-test-analyzer`.
- `errors`: run `silent-failure-hunter`.
- `types`: run `type-design-analyzer`.
- `code`: run `code-reviewer`.
- `simplify`: run `code-simplifier` only when the user explicitly authorizes code modification.
- `all` never includes `code-simplifier` — whether it is the default or the user
typed it explicitly. Upstream `commands/review-pr.md` does put `code-simplifier`
in its `all` flow; this document overrides that (see the precedence note above).
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

The analysis phase may contain zero reviewers, including an explicitly
authorized `simplify`-only request. The before baseline still always runs
before entering this phase. When the phase is empty, skip reviewer dispatch and
reviewer-report aggregation. The after baseline still always runs immediately
after the empty phase, and its comparison must pass before the separate
simplifier mutation phase.

If one reviewer fails, preserve completed reports and identify the failed role
and reason in the final summary.

## Aggregation

When the analysis phase contains one or more reviewers, deduplicate overlapping
findings and produce:

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
not invent positive observations. Do not produce this aggregate when the
analysis phase is empty.

After the analysis phase completes—and after aggregation when it contained
reviewers—run the same read-only command set again under distinct `after`
labels. Compare HEAD and every exact fingerprint first. If any value differs,
compare the retained before/after path-level manifests to report every affected
path and whether HEAD, status, unstaged content, staged object, or untracked
path/content changed. Do not revert user work or run `code-simplifier` after a
failed baseline comparison. Keep both fingerprint and manifest output sets in
the review context through the final report. This entire baseline workflow
must perform no filesystem writes.

When `code-simplifier` is selected with explicit modification authority, run
it only after both baseline captures have run and their comparison has passed,
whether the analysis phase had reviewers or not. Read its entire upstream
`agents/code-simplifier.md`, pass it the same Git scope and project
instructions, and preserve its upstream role, criteria, scoring, and output
format. This is a separate sequential mutation phase; it may modify files and
must never be parallel-dispatched.
