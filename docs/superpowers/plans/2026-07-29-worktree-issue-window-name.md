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
/Users/lee-kyu-hwan/code/dotfiles/dot_agents/skills/create-worktree/SKILL.md.
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

- **짧은 이름**: 브랜치명에서 `*/` 앞 prefix를 제거한다.
  `392-feat/add-partner-chat-enabled` → `add-partner-chat-enabled`
- **이슈 번호**: 브랜치명 선두의 숫자 또는 `ZF-숫자`를 사용한다.
  `392-feat/...` → `392`, `ZF-115-chore/...` → `ZF-115`. 없으면 생략한다.
- **윈도우 이름**: 이슈 번호가 있으면 `{이슈번호}-{짧은이름}`, 없으면 짧은
  이름을 그대로 사용한다.
  `392-add-partner-chat-enabled`, `ZF-115-some-feature`, `login-bug`
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
workmux open {디렉토리명} --target-name {윈도우이름}
```

Keep the git-crypt restriction and the existing path-discovery instructions.

- [ ] **Step 3: Pass the window name on the direct workmux path**

Change:

```bash
workmux add {브랜치명}
```

to:

```bash
workmux add {브랜치명} --target-name {윈도우이름}
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
- Deploy: `/Users/lee-kyu-hwan/.agents/skills/create-worktree/SKILL.md`
- Deploy: `/Users/lee-kyu-hwan/.claude/skills/create-worktree/SKILL.md`

- [ ] **Step 1: Validate both skill directories**

Run:

```bash
python3 /Users/lee-kyu-hwan/.codex/skills/.system/skill-creator/scripts/quick_validate.py dot_agents/skills/create-worktree
python3 /Users/lee-kyu-hwan/.codex/skills/.system/skill-creator/scripts/quick_validate.py dot_claude/skills/create-worktree
```

Expected: both commands report `Skill is valid!`.

- [ ] **Step 2: Verify the two skill bodies stay identical**

Run:

```bash
diff -u <(tail -n +6 dot_agents/skills/create-worktree/SKILL.md) \
  <(tail -n +9 dot_claude/skills/create-worktree/SKILL.md)
```

Expected: exit code 0 and no output.

- [ ] **Step 3: Run the GREEN scenario**

Dispatch a fresh agent with the same prompt from Task 1, but point it at each
updated skill in separate runs.

Expected:

```text
392-feat/add-partner-chat-enabled → 392-add-partner-chat-enabled
ZF-115-chore/some-feature → ZF-115-some-feature
fix/login-bug → login-bug
```

Every `workmux open` and `workmux add` command must include the matching
`--target-name`.

- [ ] **Step 4: Apply the two managed files with chezmoi**

Run:

```bash
chezmoi apply /Users/lee-kyu-hwan/.agents/skills/create-worktree/SKILL.md
chezmoi apply /Users/lee-kyu-hwan/.claude/skills/create-worktree/SKILL.md
```

Expected: both commands exit 0.

- [ ] **Step 5: Verify deployed files match their sources**

Run:

```bash
cmp dot_agents/skills/create-worktree/SKILL.md \
  /Users/lee-kyu-hwan/.agents/skills/create-worktree/SKILL.md
cmp dot_claude/skills/create-worktree/SKILL.md \
  /Users/lee-kyu-hwan/.claude/skills/create-worktree/SKILL.md
git diff --check
```

Expected: all commands exit 0 with no output.

- [ ] **Step 6: Commit the implementation**

Run:

```bash
git add \
  dot_agents/skills/create-worktree/SKILL.md \
  dot_claude/skills/create-worktree/SKILL.md \
  docs/superpowers/plans/2026-07-29-worktree-issue-window-name.md
git commit -m "fix(skills): worktree window issue 번호 복원"
```

Expected: one commit containing the two synchronized skill updates and this
implementation plan.
