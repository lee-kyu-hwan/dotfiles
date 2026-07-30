# Worktree Issue Window Name Restoration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore issue-number-prefixed workmux window names in both the Codex and Claude `create-worktree` skills without changing worktree directory names.

**Architecture:** Keep the two agent-specific skill files because Claude needs extra frontmatter, but make their Markdown bodies identical. Derive an optional issue prefix from the branch name and pass the resulting window name through workmux's `--target-name` option on both creation paths.

**Tech Stack:** Markdown agent skills, workmux CLI, chezmoi, Git

---

### Task 1: Capture the Missing Behavior

**Files:**
- Inspect: `dot_agents/skills/create-worktree/SKILL.md`
- Inspect: `dot_claude/skills/create-worktree/SKILL.md`

- [ ] **Step 1: Run a baseline scenario with the current Codex skill**

Dispatch a fresh agent with only the current skill path and this prompt:

```text
Use the create-worktree skill at
~/code/dotfiles/dot_agents/skills/create-worktree/SKILL.md.
Do not execute commands. For each branch below, state the exact workmux command
and resulting tmux window name:
1. 392-feat/add-partner-chat-enabled
2. ZF-115-chore/some-feature
3. fix/login-bug
Cover both the wrapper-script path (`workmux open`) and the direct path
(`workmux add`).
```

Expected RED result: the commands omit `--target-name`, so the first two window
names lose `392` and `ZF-115`.

- [ ] **Step 2: Record the observed failure**

Keep the agent output in the execution log and confirm the failure is caused by
the missing issue-window instructions, not by an unavailable command or an
unreadable skill file.

### Task 2: Restore the Rule in Both Skills

**Files:**
- Modify: `dot_agents/skills/create-worktree/SKILL.md`
- Modify: `dot_claude/skills/create-worktree/SKILL.md`

- [ ] **Step 1: Extend the naming rules in the Codex skill**

Replace the current `## 이름 파생` section with:

```markdown
## 이름 파생

- **짧은 이름**: 브랜치명에서 마지막 `/`까지를 제거한다.
  `392-feat/add-partner-chat-enabled` → `add-partner-chat-enabled`
- **이슈 번호**: 브랜치명 **맨 앞**의 숫자 또는 `ZF-숫자`만 인식한다. 맨 앞이 아니면
  이슈 번호가 아니다 — `feat/392-add-x`는 이슈 번호가 없는 것으로 본다.
- **윈도우이름**: 이슈 번호가 있을 때만 `{이슈번호}-{짧은이름}`을 만들어
  `--target-name`에 넘긴다. **이슈 번호가 없으면 `--target-name`을 생략한다** —
  workmux 기본 이름에는 저장소 이름이 들어가므로 다른 저장소의 같은 이름 브랜치와
  충돌하지 않는다.
- **디렉터리명**: 스크립트가 `../{repo명}-{짧은이름}` 에 만든다. 이슈 번호는
  디렉터리가 아니라 tmux 윈도우에만 붙인다.
- 같은 브랜치의 worktree가 이미 있으면 새로 만들지 않고 기존 경로를 안내한다.
```

- [ ] **Step 2: Pass the window name on the wrapper-script path**

Change:

```bash
workmux open {디렉토리명}
```

to:

```bash
workmux open {디렉토리명} --target-name {윈도우이름}  # 이슈 번호가 있을 때
workmux open {디렉토리명}                             # 이슈 번호가 없을 때
```

Keep the git-crypt restriction and the existing path-discovery instructions.

- [ ] **Step 3: Pass the window name on the direct workmux path**

Change:

```bash
workmux add {브랜치명}
```

to:

```bash
workmux add {브랜치명} --target-name {윈도우이름}   # 이슈 번호가 있을 때
workmux add {브랜치명}                              # 이슈 번호가 없을 때
```

- [ ] **Step 4: Apply the same body changes to the Claude skill**

Make the same naming and command changes in
`dot_claude/skills/create-worktree/SKILL.md`. Preserve these Claude-only
frontmatter fields:

```yaml
argument-hint: <branch-name>
user-invocable: true
allowed-tools: Bash
```

### Task 3: Validate and Deploy the Skills

**Files:**
- Validate: `dot_agents/skills/create-worktree/SKILL.md`
- Validate: `dot_claude/skills/create-worktree/SKILL.md`
- Deploy: `~/.agents/skills/create-worktree/SKILL.md`
- Deploy: `~/.claude/skills/create-worktree/SKILL.md`

- [ ] **Step 1: Validate the Codex skill and Claude frontmatter**

Run:

```bash
/opt/homebrew/bin/python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py dot_agents/skills/create-worktree
/opt/homebrew/bin/python3 -c 'from pathlib import Path; import yaml; text = Path("dot_claude/skills/create-worktree/SKILL.md").read_text(); frontmatter = text.split("---", 2)[1]; metadata = yaml.safe_load(frontmatter); expected = {"name": "create-worktree", "description": "Use when creating a new git worktree for a branch to work on in isolation from the main workspace", "argument-hint": "<branch-name>", "user-invocable": True, "allowed-tools": "Bash"}; assert metadata == expected, metadata; print("Claude frontmatter is valid!")'
```

Expected: the Codex command reports `Skill is valid!`; the YAML assertion reports
`Claude frontmatter is valid!`. The Codex validator is not run against the Claude
skill because it intentionally rejects Claude-only `argument-hint` and
`user-invocable` keys.

- [ ] **Step 2: Verify the two skill bodies stay identical**

Run:

```bash
diff -u <(tail -n +6 dot_agents/skills/create-worktree/SKILL.md) \
  <(tail -n +9 dot_claude/skills/create-worktree/SKILL.md)
```

Expected: exit code 0 and no output.

- [ ] **Step 3: Run safe workmux GREEN dry-runs**

Run:

```bash
workmux open --help
workmux add 392-feat/add-partner-chat-enabled --target-name 392-add-partner-chat-enabled --dry-run
workmux add ZF-115-chore/some-feature --target-name ZF-115-some-feature --dry-run
workmux add fix/login-bug --target-name login-bug --dry-run
```

Expected: `workmux open --help` lists `--target-name <TARGET_NAME>`, confirming
the wrapper-script path supports the option. The dry-runs produce these `Target`
outputs (workmux normalizes target names to lowercase):

```text
Target:    392-add-partner-chat-enabled (window)
Target:    zf-115-some-feature (window)
Target:    login-bug (window)
```

The help command is read-only. Each `workmux add` command is a dry-run and must
create no worktree or tmux window.

- [ ] **Step 4: Apply the two managed files with chezmoi**

Run:

```bash
chezmoi -S . apply ~/.agents/skills/create-worktree/SKILL.md
chezmoi -S . apply ~/.claude/skills/create-worktree/SKILL.md
```

Expected: both commands exit 0.

- [ ] **Step 5: Verify deployed files match their sources**

Run:

```bash
cmp dot_agents/skills/create-worktree/SKILL.md \
  ~/.agents/skills/create-worktree/SKILL.md
cmp dot_claude/skills/create-worktree/SKILL.md \
  ~/.claude/skills/create-worktree/SKILL.md
git diff --check
```

Expected: all commands exit 0 with no output.

- [ ] **Step 6: Amend the implementation commit**

Run:

```bash
git add \
  docs/superpowers/plans/2026-07-29-worktree-issue-window-name.md \
  docs/superpowers/specs/2026-07-29-worktree-issue-window-name-design.md
git commit --amend --no-edit
```

Expected: the existing Task 2 commit is amended with this implementation-plan
and design-spec corrections, leaving one commit containing the two synchronized
skill updates, the plan, and the design spec.
