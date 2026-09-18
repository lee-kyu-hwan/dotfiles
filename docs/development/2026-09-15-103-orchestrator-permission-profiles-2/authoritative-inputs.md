# Authoritative inputs for the account-workspace-directory redesign

This document records the authoritative requirement inputs for execution `20260915T045020Z-103-account-workspace-directory-기반-codex-0b1ffbac`. The issue bodies for #103 and #111 were updated on 2026-09-15 and the user confirmed that those updates are themselves the authoritative input. Nothing here was inferred from a credential file, an account home, or a live provider call.

## Prior execution, preserved as evidence

The previous execution `20260915T004047Z-103-codex-claude-계층별-오케스트레이터-모델-권한-프로필과-edc860c6` is terminal with stage `NEEDS_REDESIGN` and reason `REQUIREMENTS_REDESIGN:ACCOUNT_WORKSPACE_DIRECTORY_POLICY`. Its Spec (`56efae02…`), revision notes (`91ea5b17…`), five readiness attempts, revision checks, watchdog preservation bundles and report remain byte-preserved under `docs/development/2026-09-15-103-orchestrator-permission-profiles/` and `.claude/quality-state/20260915T004047Z-…-edc860c6/`. That Spec consumed 2 of 3 allowed formal rounds; the remaining round was deliberately not spent on it. Those files are read-only prior evidence for this execution.

Three still-valid findings carry forward from that execution and must be satisfied by the new Spec: `SPEC-009` (persist installed-CLI version/help evidence, separate pinned model identifiers from provider availability, define the Claude `usage_unknown` block and operator response), `SPEC-010` (define provider-child stdio/TTY ownership and limit byte relay to pre-exec public records), and `SPEC-011` (enumerate the exact credential/auth-route environment scrub set).

## What the redesign replaces

The previous Spec selected accounts from repository identity: a normalized Git remote plus `git rev-parse --git-common-dir` bound a source checkout and its linked worktrees to one `owner/name`, with canonical directory mapping only as a defense-in-depth fallback. Both updated issues invert this.

- #111: the workspace-directory section "이 절은 아래의 repository/organization 중심 예시보다 우선하는 초기 운영 정책이다", and `work`/`personal` are for Git identity only, never for account selection.
- #103: "Git remote/common-dir는 Git 무결성 검증에만 사용하고 account를 선택하지 않는다."

## Initial account policy

| provider | real workspace path | initial account profile |
|---|---|---|
| Codex | `~/code/**` | the single existing `codex-default`. Additional Codex account homes may be declared but are never selected automatically. |
| Claude | `~/code/profile1/**` | `claude-profile1`, pinned to the provider-default config home. |
| Claude | `~/code/profile2/**` | `claude-profile2`, pinned to its own separate `CLAUDE_CONFIG_DIR`. |
| Claude | outside both roots | fail closed, unconditionally, under the initial policy. |

Selection uses the normalized real worktree path, not the symlink surface path, and picks exactly one longest real ancestor directory mapping. GitHub `owner/repository`, Git remote and organization are not account-selection signals in the initial deployment. A source checkout and a linked worktree that share a Git remote select different Claude profiles when they sit under different account roots.

The account binds once when the provider process starts and stays fixed until it exits. Neither `cd`, nor a usage change, nor a Git remote change re-selects it. When the bound account reaches a limit the session stops as `blocked_usage`; automatic ranking, fallback or rotation between consumer accounts is prohibited.

The outside-both-roots case is unconditional in the initial policy: #103 states "초기 정책에서 두 root 밖의 Claude 자동 선택은 fail closed한다". Widening the mapping later is a reviewed Spec and registry revision that ships a new mapping, never a runtime escape hatch that a launcher may take while the initial policy is deployed. No requirement, acceptance criterion, architecture statement, failure-behavior clause or authorization clause may describe an in-policy exception for a path outside the two declared roots.

Selection priority stays explicit option → stored task/session binding → longest account workspace directory mapping → provider default, and the provider-default step is initially allowed for Codex only. An explicit option or a stored binding may never bypass the current real directory's `allowed_scopes`; a mismatch requires the rebind procedure rather than a guess.

## Logical alias policy

Logical aliases are fixed as `claude-profile1` and `claude-profile2`. Names that mean a default, a repository, or a Git identity — `default`, `dotfiles`, `work`, `personal` — are not used as account aliases. The final separate home is likewise neutral: `~/.local/share/ai-account-profiles/claude/profile2`.

`claude-profile1` is the provider-default/unset mode: the launcher must not export `CLAUDE_CONFIG_DIR` for it. `claude-profile2` is the explicit separated-home mode and exports its exact absolute path. This preserves the earlier `USER-CLAUDE-DEFAULT-UNSET` correction, which the user established by observing that an explicit `CLAUDE_CONFIG_DIR=~/.claude` makes Claude resolve a different path and report logged out, while an unset variable reports the existing default account logged in.

## Legacy runtime protection

The currently running `claude-dotfiles` alias and the `~/.local/share/ai-account-profiles/claude/dotfiles` home are legacy runtime state, not the new registry target. This execution must not hot rename or rebind them, and an issue-body update alone changes nothing about a running process.

The transition happens only in a separate migration generation after implementation and verification are complete: stop the existing processes, create a handoff, verify official login and identity admission in the new alias and home, and switch the binding as a new generation. The credential home is never renamed while in use and never copied or symlinked to another home. The legacy alias is removed only after the count of processes and bindings referencing it is verified to be zero.

## Account root is a selection boundary, not a permission boundary

A local Git 2.55.0 probe on a temporary repository established the following. No real user worktree was moved.

- Moving a linked worktree with both dirty tracked files and untracked files between profile roots using `git worktree move` preserved both kinds of change and updated the path in `git worktree list`. Moving a main worktree was refused by Git with exit 128.
- After the move, the linked worktree's common-dir remained in the **previous** main repository's `.git`, outside the destination account root.
- In a separate live-cwd probe, a process that had the worktree as its cwd before the move reported the new path from `os.getcwd()` while its inherited `PWD` still held the old `profile1` path.

Two contract consequences follow.

1. The account directory is the account **selection** boundary and is separate from the filesystem **permission** boundary. When Git writes are required, only the resolved worktree and the exact common-dir path are added to the permission set. The opposite account root is never implicitly granted in whole. An operator who does not want that cross-root access creates a separate clone under the destination profile root and hands off to it instead.
2. A live process can report two different paths for itself after a move, so writers and launchers must be stopped before a cross-profile move, and a stale inherited `PWD` must never be used for account re-selection or registry update.

## Cross-profile move contract

Moving a worktree to a different account root is an explicit account rebind and a new execution generation, not a rename.

1. Stop the existing Claude process, workers, watchers and file writers first, and build a handoff that preserves Git state, untracked files and quality-goal state. The `CLAUDE_CONFIG_DIR` of a running process is never changed.
2. Use `git worktree move OLD NEW` for a linked worktree. Main worktrees and linked worktrees containing submodules are not supported by that command; those need a separate clone plus handoff, or a reviewed `git worktree repair` procedure.
3. Verify with `git worktree list --porcelain`, `git rev-parse --show-toplevel`, `git rev-parse --path-format=absolute --git-common-dir` and `git status --short`. When the linked worktree's common-dir remains outside the destination account root, the launcher judges that explicitly rather than ignoring it.
4. Update the #94/#95 registry's worktree path, account profile and `binding_generation` atomically. When a stored account and the new directory mapping disagree, stop as `blocked_binding` instead of silently choosing one.
5. Start a new process under the destination root's Claude profile and continue from the handoff. Session history, credentials and plugin state from another `CLAUDE_CONFIG_DIR` are never copied or symlinked, and the same process is never hot-swapped.
6. Recompute the launcher write root, the exact Git common-dir permission, the sandbox, the workmux/tmux cwd and the watcher targets to the new real path, and confirm no process still points at the old path.

Claude session transcripts live under `CLAUDE_CONFIG_DIR` keyed by absolute working path, so a transparent `/resume` of an existing conversation after a cross-profile move must not be assumed. The resume unit is verified Git state plus an in-repository handoff; the previous account home's transcript stays in that profile.

## Settings isolation, carried forward

`CLAUDE_CONFIG_DIR` separation isolates user settings, hooks, permissions, plugin enablement and plugin state, not only authentication. The user observed that a separated profile's `settings.json` held only a theme while `~/.claude/settings.json` held `Notification`, `PermissionRequest`, `PostToolUse`, `Stop`, `SubagentStop`, `TaskCompleted` and `UserPromptSubmit` hooks plus `enabledPlugins`, `env` and `permissions`; sessions started under the separated profile answered normally but disappeared from `workmux status`.

The restoration contract is composition, never replication: a secret-free, chezmoi-managed common layer merged with the role layer into one reviewed, digest-verified document supplied through the officially advertised `--settings` surface, with reviewed local `--plugin-dir` only and the network-fetching `--plugin-url` forbidden. Authentication files, whole account homes and credential directories are never copied, synced, snapshotted or symlinked. Completion must include an effective-setting-sources judgement and a fake-`workmux` hook smoke test that mutates no running pane, session or process.

## Installed CLI evidence

The installed CLI transcripts remain valid and are preserved at `docs/development/2026-09-15-103-orchestrator-permission-profiles/installed-cli-contract-evidence.md`: Codex `codex-cli 0.154.0`, Claude Code `2.1.272`, the supported `--append-system-prompt <value>` with no advertised `--append-system-prompt-file`, the auth-status help exposing authentication status only with no usage/quota contract, and the `--settings` / `--setting-sources` / `--plugin-dir` / `--plugin-url` / `--bare` composition surface. Offline help proves neither model availability nor usage admission.

## Out of scope for this execution

No real login or logout, no auth/status/usage command, no network or model probe, no identity enrollment, no credential or account-home read, no copy/sync/snapshot/symlink of any authentication material, no `chezmoi apply`, no current pane or session mutation, no legacy alias or home rename, no deletion, and no work on issues #94 or #95 beyond consuming their registry contract.

## Observed workmux hook semantics (2026-09-15 user measurement)

The user reported the following from the live configuration. This workflow did not read any account home or credential file to obtain it.

The default account's `~/.claude/settings.json` carries these workmux window-status hooks:

| event | workmux status |
|---|---|
| `Stop` | `done` |
| `Notification` with `permission_prompt` | `waiting` |
| `Notification` with `elicitation_dialog` | `waiting` |
| `PostToolUse` | `working` |
| `UserPromptSubmit` | `working` |

The `PermissionRequest` event currently carries only a Ghostty notification and does **not** directly update workmux to `waiting`. That is a gap in the current configuration, not a behaviour to preserve.

The legacy `profile2` settings carry no hooks at all. The observed consequence is stronger than the earlier "disappears from `workmux status`" report: this pane remained stale at `done` while it was actively working. The user corrected the current pane's state to `working` externally; this workflow did not change it and must not restart or signal any running pane.

`done` means the **agent turn ended**, not that the issue is complete. The Spec and the operating documentation must state this explicitly, because a status dashboard read as issue completion would be wrong.

Required contract additions:

1. Every account profile, not only the separated one, gets the secret-free common hooks restored through the composition path already described above. No account home is copied or symlinked to achieve it.
2. `PermissionRequest` gains a direct `waiting` update rather than relying on `Notification` alone.
3. `Notification` keeps `waiting` for both `permission_prompt` and `elicitation_dialog`.
4. `Stop` maps to `done`, and `PostToolUse` and `UserPromptSubmit` map to `working`.
5. Verification runs under a separate synthetic `CLAUDE_CONFIG_DIR` with a fake `workmux` executable and asserts the exact per-event state transition for each event above, including the previously missing `PermissionRequest` → `waiting` transition and the absence of a stale `done` while work is in progress.
6. The smoke coverage spans the workmux `status`, dashboard, sidebar and wait surfaces, not only `status`.
7. The documentation records the `done` = agent-turn-end semantics.
