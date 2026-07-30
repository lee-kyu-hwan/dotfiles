# Codex PR Review Toolkit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose Claude Code's official `pr-review-toolkit` behavior in Codex through seven directly managed skills whose review criteria stay linked to the Claude source.

**Architecture:** Deploy one orchestrator and six specialist wrappers through the repository's existing Codex-only `dot_codex/skills` convention. Keep a chezmoi-managed symlink from `~/.codex/pr-review-toolkit-claude` to Claude's stable official-marketplace path, and have every wrapper load its full upstream prompt at invocation time.

**Tech Stack:** Markdown Codex skills, Claude Code plugin prompts, chezmoi templates and symlinks, Git, Codex CLI

## Global Constraints

- Use direct skills under `~/.codex/skills`; do not create a Codex plugin, marketplace, or plugin cache entry.
- Treat `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/pr-review-toolkit` as the single source of review criteria.
- Do not copy Claude reviewer criteria into the Codex wrappers.
- Do not deploy the toolkit skills or upstream symlink when `.machine_type` is `server`.
- Default `all` reviews are read-only and exclude `code-simplifier`.
- Run `code-simplifier` only when the user explicitly requests both simplification and code modification.
- Never replace missing Claude source files with an embedded or improvised prompt.
- Never allow callers to override the fixed Claude upstream root.
- Prefer `AGENTS.md` over `CLAUDE.md` when selecting project instructions.
- Treat every checkbox Step as a fresh shell; do not rely on variables from another Step.
- Use `superpowers:writing-skills` and `skill-creator` while authoring and validating the seven skills.

---

### Task 1: Add the Claude Source Symlink and Machine Exclusions

**Files:**
- Create: `dot_codex/symlink_pr-review-toolkit-claude.tmpl`
- Modify: `.chezmoiignore`

**Interfaces:**
- Consumes: chezmoi data keys `.chezmoi.homeDir` and `.machine_type`
- Produces: `~/.codex/pr-review-toolkit-claude`, the stable upstream root used by all seven skills

- [ ] **Step 1: Confirm the managed symlink and exclusions are absent**

Run:

```bash
test -f dot_codex/symlink_pr-review-toolkit-claude.tmpl
rg -n 'pr-review-toolkit' .chezmoiignore
```

Expected RED result: both commands exit 1 because neither the symlink source nor
the server exclusions exist.

- [ ] **Step 2: Add the chezmoi symlink source**

Create `dot_codex/symlink_pr-review-toolkit-claude.tmpl` with exactly:

```gotemplate
{{ .chezmoi.homeDir }}/.claude/plugins/marketplaces/claude-plugins-official/plugins/pr-review-toolkit
```

- [ ] **Step 3: Exclude the toolkit from server machines**

Add a separate block after the existing macOS-only server block in
`.chezmoiignore`:

```text
{{ if eq .machine_type "server" }}
# server: Claude Code 공식 플러그인 의존 항목 제외
.codex/skills/pr-review-toolkit
.codex/skills/pr-review-toolkit-*
.codex/pr-review-toolkit-claude
{{ end }}
```

- [ ] **Step 4: Verify template rendering and target mapping**

Run:

```bash
chezmoi -S "$PWD" execute-template \
  --file dot_codex/symlink_pr-review-toolkit-claude.tmpl
chezmoi -S "$PWD" target-path \
  dot_codex/symlink_pr-review-toolkit-claude.tmpl
chezmoi -S "$PWD" \
  --override-data '{"machine_type":"server"}' \
  execute-template --file .chezmoiignore |
  rg '^\.(codex/skills/pr-review-toolkit|codex/pr-review-toolkit-claude)'
```

Expected:

```text
/Users/lee-kyu-hwan/.claude/plugins/marketplaces/claude-plugins-official/plugins/pr-review-toolkit
/Users/lee-kyu-hwan/.codex/pr-review-toolkit-claude
.codex/skills/pr-review-toolkit
.codex/skills/pr-review-toolkit-*
.codex/pr-review-toolkit-claude
```

The first path may have a different home prefix on another non-server machine.

- [ ] **Step 5: Commit the symlink and machine rules**

```bash
git add .chezmoiignore dot_codex/symlink_pr-review-toolkit-claude.tmpl
git commit -m "feat(skills): Claude PR 리뷰 원본 링크 추가"
```

---

### Task 2: Create the Six Specialist Skill Wrappers

**Files:**
- Create: `dot_codex/skills/pr-review-toolkit-comment-analyzer/SKILL.md`
- Create: `dot_codex/skills/pr-review-toolkit-pr-test-analyzer/SKILL.md`
- Create: `dot_codex/skills/pr-review-toolkit-silent-failure-hunter/SKILL.md`
- Create: `dot_codex/skills/pr-review-toolkit-type-design-analyzer/SKILL.md`
- Create: `dot_codex/skills/pr-review-toolkit-code-reviewer/SKILL.md`
- Create: `dot_codex/skills/pr-review-toolkit-code-simplifier/SKILL.md`

**Interfaces:**
- Consumes: the upstream root produced by Task 1 and an explicit review scope from the caller
- Produces: six independently discoverable Codex skills named by their frontmatter

- [ ] **Step 1: Verify all six skill validators fail before creation**

Run:

```bash
for review_skill in \
  pr-review-toolkit-comment-analyzer \
  pr-review-toolkit-pr-test-analyzer \
  pr-review-toolkit-silent-failure-hunter \
  pr-review-toolkit-type-design-analyzer \
  pr-review-toolkit-code-reviewer \
  pr-review-toolkit-code-simplifier
do
  /opt/homebrew/bin/python3 \
    ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
    "dot_codex/skills/$review_skill"
done
```

Expected RED result: every invocation exits non-zero because its skill directory
does not exist.

- [ ] **Step 2: Create the comment analyzer wrapper**

Create `dot_codex/skills/pr-review-toolkit-comment-analyzer/SKILL.md`:

```markdown
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
4. Ignore Claude-only frontmatter as runtime configuration, but follow the body’s role, criteria, severity rules, and output format.
5. Review the exact diff, PR, commit range, or files supplied by the caller.
6. Use `AGENTS.md` as project guidance when present; otherwise use `CLAUDE.md` or another repository instruction file that actually exists.
7. Return findings with file and line references. Do not edit comments, documentation, or code.
```

- [ ] **Step 3: Create the test analyzer wrapper**

Create `dot_codex/skills/pr-review-toolkit-pr-test-analyzer/SKILL.md`:

```markdown
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
```

- [ ] **Step 4: Create the silent-failure wrapper**

Create `dot_codex/skills/pr-review-toolkit-silent-failure-hunter/SKILL.md`:

```markdown
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
```

- [ ] **Step 5: Create the type-design wrapper**

Create `dot_codex/skills/pr-review-toolkit-type-design-analyzer/SKILL.md`:

```markdown
---
name: pr-review-toolkit-type-design-analyzer
description: Use when reviewing new or modified types for encapsulation, invariant expression, usefulness, and invariant enforcement.
---

# PR Review Toolkit: Type Design Analyzer

Analyze only; do not modify files.

## Required workflow

1. Resolve `~/.codex/pr-review-toolkit-claude/agents/type-design-analyzer.md`.
2. If it is missing or unreadable, stop and report: `Claude pr-review-toolkit source is unavailable. Install or update pr-review-toolkit@claude-plugins-official in Claude Code, then retry.`
3. Read the entire upstream file before reviewing.
4. Ignore Claude-only frontmatter as runtime configuration, but follow the body’s four rating dimensions, design principles, and output format.
5. Review the exact diff, PR, commit range, types, or files supplied by the caller.
6. Use `AGENTS.md` as project guidance when present; otherwise use `CLAUDE.md` or another repository instruction file that actually exists.
7. Return ratings and actionable findings with file and line references. Do not edit type definitions.
```

- [ ] **Step 6: Create the general code-review wrapper**

Create `dot_codex/skills/pr-review-toolkit-code-reviewer/SKILL.md`:

```markdown
---
name: pr-review-toolkit-code-reviewer
description: Use after code changes or before a pull request to review the selected diff for high-confidence bugs, project-rule violations, and significant quality issues.
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
```

- [ ] **Step 7: Create the explicit code-simplifier wrapper**

Create `dot_codex/skills/pr-review-toolkit-code-simplifier/SKILL.md`:

```markdown
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
```

- [ ] **Step 8: Validate all specialist skills**

Run:

```bash
for review_skill in \
  pr-review-toolkit-comment-analyzer \
  pr-review-toolkit-pr-test-analyzer \
  pr-review-toolkit-silent-failure-hunter \
  pr-review-toolkit-type-design-analyzer \
  pr-review-toolkit-code-reviewer \
  pr-review-toolkit-code-simplifier
do
  /opt/homebrew/bin/python3 \
    ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
    "dot_codex/skills/$review_skill"
done
```

Expected GREEN result: each invocation prints `Skill is valid!` and the loop
exits 0.

- [ ] **Step 9: Verify specialist names match the upstream agent set**

Run:

```bash
diff -u \
  <(find ~/.claude/plugins/marketplaces/claude-plugins-official/plugins/pr-review-toolkit/agents \
      -maxdepth 1 -type f -name '*.md' -exec basename {} .md \; | sort) \
  <(find dot_codex/skills -maxdepth 1 -type d -name 'pr-review-toolkit-*' \
      -exec basename {} \; | sed 's/^pr-review-toolkit-//' | sort)
```

Expected: exit code 0 and no output. The two sets are:

```text
code-reviewer
code-simplifier
comment-analyzer
pr-test-analyzer
silent-failure-hunter
type-design-analyzer
```

- [ ] **Step 10: Verify all six wrappers use the exact recovery message**

Run:

```bash
review_recovery_message='Claude pr-review-toolkit source is unavailable. Install or update pr-review-toolkit@claude-plugins-official in Claude Code, then retry.'
test "$(
  rg -l -F "$review_recovery_message" \
    dot_codex/skills/pr-review-toolkit-*/SKILL.md |
    wc -l | tr -d ' '
)" -eq 6
test "$(
  rg -o -F "$review_recovery_message" \
    dot_codex/skills/pr-review-toolkit-*/SKILL.md |
    wc -l | tr -d ' '
)" -eq 6
```

Expected: exit code 0. The message appears in six files and exactly six times.
The variable is declared and consumed in this Step only.

- [ ] **Step 11: Commit the specialist wrappers**

```bash
git add \
  dot_codex/skills/pr-review-toolkit-comment-analyzer/SKILL.md \
  dot_codex/skills/pr-review-toolkit-pr-test-analyzer/SKILL.md \
  dot_codex/skills/pr-review-toolkit-silent-failure-hunter/SKILL.md \
  dot_codex/skills/pr-review-toolkit-type-design-analyzer/SKILL.md \
  dot_codex/skills/pr-review-toolkit-code-reviewer/SKILL.md \
  dot_codex/skills/pr-review-toolkit-code-simplifier/SKILL.md
git commit -m "feat(skills): PR 전문 리뷰어 추가"
```

---

### Task 3: Create the Comprehensive Review Orchestrator

**Files:**
- Create: `dot_codex/skills/pr-review-toolkit/SKILL.md`

**Interfaces:**
- Consumes: a user-selected review scope and optional aspects `comments`, `tests`, `errors`, `types`, `code`, `simplify`, `all`, `parallel`
- Produces: one prioritized read-only review report, or an explicitly authorized simplification change

- [ ] **Step 1: Verify orchestrator validation fails before creation**

Run:

```bash
/opt/homebrew/bin/python3 \
  ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  dot_codex/skills/pr-review-toolkit
```

Expected RED result: non-zero exit because the skill directory does not exist.

- [ ] **Step 2: Create the orchestrator skill**

Create `dot_codex/skills/pr-review-toolkit/SKILL.md`:

```markdown
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
```

- [ ] **Step 3: Validate the orchestrator**

Run:

```bash
/opt/homebrew/bin/python3 \
  ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  dot_codex/skills/pr-review-toolkit
```

Expected GREEN result: `Skill is valid!`.

- [ ] **Step 4: Verify the orchestrator contains every safety and routing rule**

Run:

```bash
rg -n \
  'Default `all` never includes|explicitly authorizes code modification|Do not use an embedded|gh pr view|parallel sub-agents|AGENTS.md|analysis-only reviewers|Never dispatch|review context|NUL-safe exact|bounded path-level manifests|one metadata record per Git-reported path|review_changed_path|old and new Git modes|staged object ID|worktree state signature|regular file content SHA-256|exact symlink target digest|checked-out gitlink worktree OID|absent or unavailable marker|deletion or other file-type marker|never include diff hunks|affected path|no filesystem writes|comparison has passed' \
  dot_codex/skills/pr-review-toolkit/SKILL.md

if rg -n \
  'mktemp|snapshot (directory|file)|cleanup trap|retain their complete stdout|human-readable raw (unstaged|staged) diff|Keep the raw outputs|raw status, unstaged diff, staged diff' \
  dot_codex/skills/pr-review-toolkit/SKILL.md
then
  exit 1
fi
```

Expected: all safety, routing, phase-separation, exact-fingerprint, and bounded
path-diagnostic expressions match, then the negative gate exits 0 with no
output. The inner read-only skill contains no filesystem-backed baseline
requirement and does not retain complete diff stdout.

- [ ] **Step 5: Commit the orchestrator**

```bash
git add dot_codex/skills/pr-review-toolkit/SKILL.md
git commit -m "feat(skills): Codex PR 종합 리뷰 추가"
```

---

### Task 4: Validate and Deploy the Managed Skills

**Files:**
- Validate: `.chezmoiignore`
- Validate: `dot_codex/symlink_pr-review-toolkit-claude.tmpl`
- Validate: `dot_codex/skills/pr-review-toolkit*/SKILL.md`
- Deploy: `~/.codex/pr-review-toolkit-claude`
- Deploy: `~/.codex/skills/pr-review-toolkit*/SKILL.md`

**Interfaces:**
- Consumes: all source files from Tasks 1–3
- Produces: live Codex skill directories and a resolving upstream symlink

- [ ] **Step 1: Validate all seven source skills**

Run:

```bash
for review_skill_dir in \
  dot_codex/skills/pr-review-toolkit \
  dot_codex/skills/pr-review-toolkit-comment-analyzer \
  dot_codex/skills/pr-review-toolkit-pr-test-analyzer \
  dot_codex/skills/pr-review-toolkit-silent-failure-hunter \
  dot_codex/skills/pr-review-toolkit-type-design-analyzer \
  dot_codex/skills/pr-review-toolkit-code-reviewer \
  dot_codex/skills/pr-review-toolkit-code-simplifier
do
  /opt/homebrew/bin/python3 \
    ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
    "$review_skill_dir"
done
git show --check --oneline HEAD~3..HEAD
```

Expected: seven `Skill is valid!` lines, then the three implementation commit
summaries with no whitespace-error output.

- [ ] **Step 2: Recheck upstream-to-wrapper parity**

Run:

```bash
test "$(
  find ~/.claude/plugins/marketplaces/claude-plugins-official/plugins/pr-review-toolkit/commands \
    -maxdepth 1 -type f -name '*.md' -exec basename {} \;
)" = "review-pr.md"

diff -u \
  <(find ~/.claude/plugins/marketplaces/claude-plugins-official/plugins/pr-review-toolkit/agents \
      -maxdepth 1 -type f -name '*.md' -exec basename {} .md \; | sort) \
  <(find dot_codex/skills -maxdepth 1 -type d -name 'pr-review-toolkit-*' \
      -exec basename {} \; | sed 's/^pr-review-toolkit-//' | sort)
```

Expected: both commands exit 0 with no output.

- [ ] **Step 3: Preview only the exact managed targets**

Run:

```bash
chezmoi -S "$PWD" diff --parent-dirs \
  "$HOME/.codex/pr-review-toolkit-claude" \
  "$HOME/.codex/skills/pr-review-toolkit" \
  "$HOME/.codex/skills/pr-review-toolkit-comment-analyzer" \
  "$HOME/.codex/skills/pr-review-toolkit-pr-test-analyzer" \
  "$HOME/.codex/skills/pr-review-toolkit-silent-failure-hunter" \
  "$HOME/.codex/skills/pr-review-toolkit-type-design-analyzer" \
  "$HOME/.codex/skills/pr-review-toolkit-code-reviewer" \
  "$HOME/.codex/skills/pr-review-toolkit-code-simplifier"
```

Expected: the diff contains one new symlink and seven new skill directories. It
does not contain `~/.codex/config.toml`, marketplace state, or unrelated files.
All eight targets are literal arguments; this Step defines no state consumed by
the next Step.

- [ ] **Step 4: Apply only the exact managed targets**

Run:

```bash
chezmoi -S "$PWD" apply --parent-dirs \
  "$HOME/.codex/pr-review-toolkit-claude" \
  "$HOME/.codex/skills/pr-review-toolkit" \
  "$HOME/.codex/skills/pr-review-toolkit-comment-analyzer" \
  "$HOME/.codex/skills/pr-review-toolkit-pr-test-analyzer" \
  "$HOME/.codex/skills/pr-review-toolkit-silent-failure-hunter" \
  "$HOME/.codex/skills/pr-review-toolkit-type-design-analyzer" \
  "$HOME/.codex/skills/pr-review-toolkit-code-reviewer" \
  "$HOME/.codex/skills/pr-review-toolkit-code-simplifier"
```

Expected: exit code 0. `--parent-dirs` creates missing `.codex/skills`
ancestors on a new machine without applying unrelated sibling files. If the
workspace sandbox rejects writes under the home directory, rerun this exact
command with escalated permission; do not remove any literal target.

- [ ] **Step 5: Verify deployed files and symlink**

Run:

```bash
for review_skill in \
  pr-review-toolkit \
  pr-review-toolkit-comment-analyzer \
  pr-review-toolkit-pr-test-analyzer \
  pr-review-toolkit-silent-failure-hunter \
  pr-review-toolkit-type-design-analyzer \
  pr-review-toolkit-code-reviewer \
  pr-review-toolkit-code-simplifier
do
  cmp \
    "dot_codex/skills/$review_skill/SKILL.md" \
    "$HOME/.codex/skills/$review_skill/SKILL.md"
done

test -L "$HOME/.codex/pr-review-toolkit-claude"
test "$(
  readlink "$HOME/.codex/pr-review-toolkit-claude"
)" = "$HOME/.claude/plugins/marketplaces/claude-plugins-official/plugins/pr-review-toolkit"
test -r "$HOME/.codex/pr-review-toolkit-claude/commands/review-pr.md"
```

Expected: every command exits 0 with no output.

- [ ] **Step 6: Verify server rendering excludes every toolkit target**

Run:

```bash
chezmoi -S "$PWD" \
  --override-data '{"machine_type":"server"}' \
  ignored |
  rg '^\.(codex/skills/pr-review-toolkit|codex/pr-review-toolkit-claude)'
```

Expected: the orchestrator directory, six specialist directories, and upstream
symlink appear in the ignored output.

- [ ] **Step 7: Verify recovery-message parity and the fixed upstream root**

Run:

```bash
review_recovery_message='Claude pr-review-toolkit source is unavailable. Install or update pr-review-toolkit@claude-plugins-official in Claude Code, then retry.'
test "$(
  rg -l -F "$review_recovery_message" \
    dot_codex/skills/pr-review-toolkit*/SKILL.md |
    wc -l | tr -d ' '
)" -eq 7
test "$(
  rg -o -F "$review_recovery_message" \
    dot_codex/skills/pr-review-toolkit*/SKILL.md |
    wc -l | tr -d ' '
)" -eq 7

if rg -n \
  'alternate upstream|different root|source-path validation|provides a different root' \
  dot_codex/skills/pr-review-toolkit*/SKILL.md
then
  exit 1
fi
```

Expected: exit code 0 with no output. The exact recovery message appears once in
each of the seven skills and no skill permits an upstream-root override.

---

### Task 5: Run Fresh-Session Behavioral Smoke Tests

**Files:**
- Read: deployed `~/.codex/skills/pr-review-toolkit*/SKILL.md`
- Read: deployed `~/.codex/pr-review-toolkit-claude`
- Test: current repository commit range without modifying it

**Interfaces:**
- Consumes: the live deployment from Task 4
- Produces: deterministic deployment evidence plus an informational fresh-process discovery smoke test and a read-only parallel-review smoke test

- [ ] **Step 1: Deterministically verify deployed directories and names**

Run:

```bash
set -e
for expected_review_skill in \
  pr-review-toolkit \
  pr-review-toolkit-comment-analyzer \
  pr-review-toolkit-pr-test-analyzer \
  pr-review-toolkit-silent-failure-hunter \
  pr-review-toolkit-type-design-analyzer \
  pr-review-toolkit-code-reviewer \
  pr-review-toolkit-code-simplifier
do
  review_skill_file="$HOME/.codex/skills/$expected_review_skill/SKILL.md"
  test -f "$review_skill_file"
  rg -q -x -F -- "name: $expected_review_skill" "$review_skill_file"
done
```

Expected: exit code 0. This is the deterministic discovery-path gate.

- [ ] **Step 2: Run an informational fresh-process discovery smoke test**

Run:

```bash
review_skill_list_file=$(mktemp -t pr-review-toolkit-skills)
trap 'test ! -e "$review_skill_list_file" || unlink "$review_skill_list_file"' EXIT HUP INT TERM

codex exec \
  --ephemeral \
  --sandbox read-only \
  -C "$PWD" \
  --output-last-message "$review_skill_list_file" \
  'List every available skill whose name starts with pr-review-toolkit. Include each full skill name and do not invoke the skills.' ||
  review_discovery_exit=$?

if test "${review_discovery_exit:-0}" -ne 0
then
  print -r -- "Informational discovery smoke exited ${review_discovery_exit}."
else
  for expected_review_skill in \
    pr-review-toolkit \
    pr-review-toolkit-comment-analyzer \
    pr-review-toolkit-pr-test-analyzer \
    pr-review-toolkit-silent-failure-hunter \
    pr-review-toolkit-type-design-analyzer \
    pr-review-toolkit-code-reviewer \
    pr-review-toolkit-code-simplifier
  do
    if ! rg -q -F -- "$expected_review_skill" "$review_skill_list_file"
    then
      print -r -- "Informational discovery smoke omitted: $expected_review_skill"
    fi
  done
fi

unlink "$review_skill_list_file"
trap - EXIT HUP INT TERM
```

Expected: normally each name appears somewhere in the model response. A
non-zero Codex exit or omitted name is printed as informational output and does
not replace the deterministic Step 1 gate.

- [ ] **Step 3: Run a parallel two-reviewer aggregation smoke test**

Run:

```bash
set -e
review_snapshot_dir=$(mktemp -d -t pr-review-toolkit-snapshot)
review_cleanup_snapshot() {
  test ! -e "$review_snapshot_dir" || rm -rf -- "$review_snapshot_dir"
}
trap review_cleanup_snapshot EXIT HUP INT TERM

review_write_untracked_manifest() {
  review_paths_file=$1
  review_manifest_file=$2
  while IFS= read -r -d '' review_untracked_path
  do
    printf '%s\0' "$review_untracked_path"
    shasum -a 256 < "$review_untracked_path"
  done < "$review_paths_file" > "$review_manifest_file"
}

review_capture_snapshot() {
  review_snapshot_prefix=$1
  git rev-parse HEAD > "$review_snapshot_dir/$review_snapshot_prefix.head"
  git status --porcelain=v1 -z > "$review_snapshot_dir/$review_snapshot_prefix.status"
  git diff --binary > "$review_snapshot_dir/$review_snapshot_prefix.unstaged.diff"
  git diff --cached --binary > "$review_snapshot_dir/$review_snapshot_prefix.staged.diff"
  git ls-files --others --exclude-standard -z \
    > "$review_snapshot_dir/$review_snapshot_prefix.untracked.paths"
  review_write_untracked_manifest \
    "$review_snapshot_dir/$review_snapshot_prefix.untracked.paths" \
    "$review_snapshot_dir/$review_snapshot_prefix.untracked.manifest"
  for review_snapshot_artifact in \
    head status unstaged.diff staged.diff untracked.paths untracked.manifest
  do
    shasum -a 256 < \
      "$review_snapshot_dir/$review_snapshot_prefix.$review_snapshot_artifact" \
      > "$review_snapshot_dir/$review_snapshot_prefix.$review_snapshot_artifact.sha256"
  done
}

review_list_nul_paths() {
  review_paths_file=$1
  while IFS= read -r -d '' review_untracked_path
  do
    print -r -- "$review_untracked_path"
  done < "$review_paths_file"
}

review_capture_snapshot before
review_output_file="$review_snapshot_dir/review-output.md"

codex exec \
  --ephemeral \
  --sandbox read-only \
  -C "$PWD" \
  --output-last-message "$review_output_file" \
  '$pr-review-toolkit Review HEAD~3..HEAD using only code and comments in parallel. Do not modify files.'

rg -n '^# PR Review Summary$' "$review_output_file"
rg -n '^## (Critical Issues|Important Issues|Suggestions|Strengths|Recommended Action)$' \
  "$review_output_file"
review_capture_snapshot after

review_snapshot_mismatch=0
for review_snapshot_artifact in \
  head status unstaged.diff staged.diff untracked.paths untracked.manifest
do
  if ! cmp -s \
    "$review_snapshot_dir/before.$review_snapshot_artifact.sha256" \
    "$review_snapshot_dir/after.$review_snapshot_artifact.sha256"
  then
    print -r -- "Review baseline fingerprint mismatch: $review_snapshot_artifact"
  fi
  if ! cmp -s \
    "$review_snapshot_dir/before.$review_snapshot_artifact" \
    "$review_snapshot_dir/after.$review_snapshot_artifact"
  then
    review_snapshot_mismatch=1
    print -r -- "Review baseline mismatch: $review_snapshot_artifact"
    case "$review_snapshot_artifact" in
      status)
        print -r -- 'Before status paths:'
        tr '\0' '\n' < "$review_snapshot_dir/before.status"
        print -r -- 'After status paths:'
        tr '\0' '\n' < "$review_snapshot_dir/after.status"
        ;;
      unstaged.diff|staged.diff)
        git diff --no-index -- \
          "$review_snapshot_dir/before.$review_snapshot_artifact" \
          "$review_snapshot_dir/after.$review_snapshot_artifact" || true
        ;;
      untracked.paths|untracked.manifest)
        print -r -- 'Before untracked paths:'
        review_list_nul_paths "$review_snapshot_dir/before.untracked.paths"
        print -r -- 'After untracked paths:'
        review_list_nul_paths "$review_snapshot_dir/after.untracked.paths"
        ;;
    esac
  fi
done
test "$review_snapshot_mismatch" -eq 0
```

Expected: the report contains the aggregate title and all five sections. The
before/after `mktemp -d` artifacts for HEAD, NUL-delimited status, unstaged
binary diff, staged binary diff, untracked NUL paths, and the path-level
untracked content manifest all pass `cmp -s`. The SHA-256 artifact files are
available as equality gates, but the raw artifacts remain available for a
mismatch diagnostic that prints affected paths. Every snapshot variable,
comparison, and cleanup trap is declared in this one Step; NUL data flows only
through files and pipes, while the trap removes only its exact temporary
directory. These temporary artifacts belong to the outer smoke harness, not to
the inner `codex exec --sandbox read-only` skill contract.

- [ ] **Step 4: Confirm the final branch state**

Run:

```bash
git status --short
git log -6 --oneline
```

Expected: `git status --short` is empty, and the three implementation commits
from Tasks 1–3 appear above the design-and-plan correction commit.

---

## Rollback Procedure

Use this only immediately after completing this plan, while the three
implementation commits from Tasks 1–3 are still `HEAD`, `HEAD~1`, and `HEAD~2`.
The procedure moves deployed files to a recoverable backup before reverting
their source commits.

```bash
set -e
review_rollback_dir="$HOME/.codex/rollback/pr-review-toolkit"
test ! -e "$review_rollback_dir"

for review_deployed_target in \
  "$HOME/.codex/pr-review-toolkit-claude" \
  "$HOME/.codex/skills/pr-review-toolkit" \
  "$HOME/.codex/skills/pr-review-toolkit-comment-analyzer" \
  "$HOME/.codex/skills/pr-review-toolkit-pr-test-analyzer" \
  "$HOME/.codex/skills/pr-review-toolkit-silent-failure-hunter" \
  "$HOME/.codex/skills/pr-review-toolkit-type-design-analyzer" \
  "$HOME/.codex/skills/pr-review-toolkit-code-reviewer" \
  "$HOME/.codex/skills/pr-review-toolkit-code-simplifier"
do
  test -e "$review_deployed_target" || test -L "$review_deployed_target"
done

mkdir -p "$review_rollback_dir"
mv \
  "$HOME/.codex/pr-review-toolkit-claude" \
  "$HOME/.codex/skills/pr-review-toolkit" \
  "$HOME/.codex/skills/pr-review-toolkit-comment-analyzer" \
  "$HOME/.codex/skills/pr-review-toolkit-pr-test-analyzer" \
  "$HOME/.codex/skills/pr-review-toolkit-silent-failure-hunter" \
  "$HOME/.codex/skills/pr-review-toolkit-type-design-analyzer" \
  "$HOME/.codex/skills/pr-review-toolkit-code-reviewer" \
  "$HOME/.codex/skills/pr-review-toolkit-code-simplifier" \
  "$review_rollback_dir/"

git revert --no-commit HEAD HEAD~1 HEAD~2
git commit -m "revert: Codex PR 리뷰 툴킷 제거"
```

Expected: Codex no longer discovers the toolkit, the source changes are
reverted in one commit, and the eight deployed targets remain recoverable under
`~/.codex/rollback/pr-review-toolkit`.
