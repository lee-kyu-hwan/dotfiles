# Orchestrator permission profiles: operator guide

This document is the operating and migration contract for the role launchers,
account selection, admission checks, and turn-status reporting introduced by
issue #103. It describes the checked-in source contract. Deployment, provider
authentication, identity enrollment, and live process changes remain explicit
operator actions outside this repository workflow.

## Role and file map

Role policy and account policy are orthogonal. Changing a role must not change
the selected account, and changing an account must not change the role's model,
effort, permissions, instructions, settings, Skill policy, or leader capability.

| Role | Operating purpose | Capability boundary |
| --- | --- | --- |
| `general` | A normal provider session | Observability only; Codex uses workspace-write with on-request approval |
| `orchestrator` | A workgroup coordinator | Dispatch and multi-agent capability; no lease writes |
| `feature-orchestrator` | A quality-goal feature coordinator | Quality-goal and bounded delegation capability; no lease writes |
| `global-orchestrator` | Global active, reviewer, or standby operation | Active requires an external lease proof; reviewer and standby are read-only, observability-only, and cannot dispatch or write leases |

| Source | Single responsibility |
| --- | --- |
| `dot_config/ai-session/accounts.toml` | Active account aliases, directory-only scopes and mappings, home modes, binding generation, and opaque legacy evidence |
| `dot_config/ai-session/roles.toml` | Role schema, CLI ranges, model/effort, permissions, capabilities, and trusted artifact digests |
| `dot_config/ai-session/skill-policies.toml` | Versioned allow/deny intersection and deny-first capability policy |
| `dot_claude/settings.json` | Secret-free common composition input; `.chezmoiignore` keeps it out of every Claude account home |
| `dot_config/ai-session/claude/*.settings.json` | Reviewed common-plus-role composed settings passed as one settings document |
| `dot_config/ai-session/instructions/*` | Versioned additive instructions selected by provider and role |
| `dot_local/bin/executable_ai-role-session` | Role validation, trusted artifact checks, final provider arguments, and one-exec dispatch |
| `dot_local/bin/executable_ai-session` | Account selection, stored binding checks, admission, permission paths, public records, and provider exec |
| `dot_local/libexec/executable_ai-session-verify-*` | Provider-specific official status adapters with strict redacted output |
| `dot_local/libexec/ai_session_identity.py` | Shared canonical identity projection and digest comparison |
| `dot_local/libexec/executable_ai-session-enroll-identity` | Explicit host-local enrollment helper; never an automatic launch step |
| `dot_local/bin/symlink_ai-{codex,claude}*` | The eight provider-by-role public entrypoints |

## Normalized real-path selection and alias/home mode

At launch, selection uses filesystem-resolved `os.getcwd()` exactly once. It
does not select from inherited `PWD`, a symlink surface, Git remote,
owner/repository, organization, or Git common-dir. The strict priority is
`explicit option -> stored task/session binding -> longest directory mapping -> Codex-only provider default`.
Equal-priority ambiguity, a stale stored generation, a stored/mapped mismatch,
or a real-path contradiction fails closed without ranking, rotation, or
fallback.

The active aliases are:

- `codex-default`: the only selectable Codex account for real paths below
  `~/code`; it uses the already-existing provider-default home.
- `claude-profile1`: selected below `~/code/profile1`; its home mode is
  `explicit`.
- `claude-profile2`: selected below `~/code/profile2`; its home mode is
  `explicit`.

For both explicit Claude aliases only the reviewed private child environment
receives the configured neutral home as `CLAUDE_CONFIG_DIR`. A `claude` started
directly outside the launcher still uses `~/.claude` and is not selected by this
contract. The launcher keeps supporting `config_home_mode = "provider_default"`,
but that mode makes the user's `~/.claude/settings.json` and
`~/.claude/settings.local.json` pre-scan inputs: a home whose settings carry
keys beyond the benign allowlist returns
`blocked_policy` (exit 4) for launch and status. That is why `claude-profile1`
moved to an explicit home instead of weakening the pre-scan.

Claude paths outside both reviewed roots return `blocked_contract`. Adding a
root or account requires a separately reviewed registry-source change before
launch. Provider-default selection outside the reviewed roots is not a Claude
fallback. An explicit or stored choice still has to match the current real
directory's directory-only allowed scope.

Profile separation is account-selection policy; it is not repository security isolation.
Account roots select an account but do not grant access to repositories.

## Model pins and availability

The role manifest pins the final provider arguments. General, workgroup, and
feature Codex roles use `gpt-5.6-sol` at medium effort; global Codex uses
`gpt-6-astra` at high effort. General, workgroup, and feature Claude roles use
`opus[1m]` at high effort; global Claude uses `claude-fable-5-1`, with the
manifest-recorded elevated effort for sustained global coordination.

A pin and a compatible help surface prove configuration compatibility, not
model availability, quota, or admission. Offline `--version`/`--help` checks
must never become a network or model probe. If the provider rejects a pinned
model, its exit is preserved; the wrapper does not substitute a model,
provider, or account.

## Claude usage_unknown operator response

The reviewed Claude adapter has an official authentication-status contract but
no reviewed machine-readable usage/quota contract. A logged-in fixture therefore
produces `usage_unknown`, which is fail closed by default. Admission opens only
when the selected account declares `usage_contract = "none"` and that exact
`status` or `launch` invocation includes `--accept-usage-unknown`. Either
condition alone remains blocked. The admitted decision keeps `usage_unknown` in
the verifier payload, status JSON, provider environment, and public records.
The operator must not infer usage from login, scrape a TUI, call a private
endpoint, relay raw output, or try another consumer account. This is a **no
fallback** rule.

## Permission and common-dir boundary

The account root is only a selection boundary. A write-capable launch may grant
exactly the `resolved worktree and the exact absolute Git common-dir` verified
by Git. It must not grant the opposite profile root, an account root, a wildcard,
an untrusted add-dir, unrestricted access, `danger-full-access`, or
`bypassPermissions`. An external common-dir is either admitted as that exact
path after integrity checks or rejected in favor of a destination-root separate
clone and handoff.

Before admission, Git must confirm the worktree top level, the absolute
common-dir, the git-dir relationship, and that the current real directory is
inside the resolved worktree. The launcher rejects stale `PWD` rather than
using it for selection, authorization, or registry updates.

## Exact environment scrub

The verifier and provider environments begin by removing this exact parent
environment set:

- `CODEX_HOME`
- `CLAUDE_CONFIG_DIR`
- `CODEX_API_KEY`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `ANTHROPIC_AUTH_TOKEN`
- `CLAUDE_CODE_OAUTH_TOKEN`
- `CLAUDE_CODE_USE_BEDROCK`
- `CLAUDE_CODE_USE_VERTEX`
- `CLAUDE_CODE_USE_FOUNDRY`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_SESSION_TOKEN`
- `GOOGLE_APPLICATION_CREDENTIALS`
- `CLOUD_ML_REGION`
- `ANTHROPIC_VERTEX_PROJECT_ID`
- `ANTHROPIC_FOUNDRY_RESOURCE`
- `ANTHROPIC_FOUNDRY_API_KEY`
- `AI_COST_LIMIT_USD`

After scrubbing, only the selected Codex home or the selected explicit Claude
home may be reintroduced in the private child environment. Provider-default
Claude mode leaves its home variable absent. Common settings cannot recreate a
scrubbed key or introduce the other provider/profile home.

## Stdio and TTY ownership

The dispatcher performs account-independent preflight, creates one-shot
capability state where required, and execs `ai-session launch` exactly once.
It does not close, duplicate, pipe, or relay the terminal streams: `stdin, stdout, and stderr remain attached to the provider`.
The binding and startup records are written to inherited stderr before the
provider exec; after exec, stderr belongs to the provider. Only the verifier
uses captured, redacted I/O with closed file descriptors and no passed FDs.

## Leader lease and roles

Global active admission requires a valid external lease proof and a host-local
exclusive lock for the normalized scope. The lock FD remains in the single exec
chain for the provider lifetime. A second active owner in the same scope, or an
expired/mismatched proof, returns `blocked_leader_conflict`; different scopes
remain independent. The launcher neither issues nor renews lease generations.

Global reviewer and standby modes are read-only and cannot acquire the active
lock, dispatch children, increase a generation, or write a lease. A takeover
requires matching previous-owner, process, generation, and fresh external proof
facts; invalid evidence leaves the existing owner and proof unchanged.

## Verifier and identity

The selected provider verifier runs before the provider with the selected
home-mode environment, a ten-second timeout, closed FDs, and an exact six-field
redacted result. Codex consumes only reviewed official fields. Claude consumes
official authentication status and does not invent usage evidence. No verifier
may launch the provider or try a fallback account.

Claude identity is the schema 2 `claude_auth_status_v1` canonical projection of
official `authMethod`, UUID `orgId`, and `subscriptionType`. It excludes email,
display name, token, path, and usage. Enrollment is explicit and host-local as
`v2:<64 lowercase hex>` plus LF; legacy v1 input is `stale_enrollment` and is
never rewritten automatically. Codex declares `identity_contract =
"unavailable"`, does not read a digest, and preserves `unavailable` rather than
promoting it to matched. Public records and diagnostics contain neither raw
identity nor its digest.

## Trusted settings, effective sources, and workmux

Claude receives `trusted composed settings`: a reviewed, versioned,
digest-verified merge of the secret-free common layer and the role layer,
passed through one `--settings` argument. Role denies win. Only reviewed local
plugin directories are admitted. Project, local, or account-home settings with
policy-bearing keys are untrusted `effective sources` and are blocked before
provider execution; only the manifest's exact benign keys are tolerated.

Any selected account home must leave its `settings.json` and
`settings.local.json` absent, empty, or
limited to the exact benign allowlist (`$schema`, `spinnerTipsEnabled`, and
`theme`). Both active Claude aliases use explicit neutral homes, so the user's
`~/.claude/settings.json` (which contains `env`, `permissions`, and `hooks` on
this machine) is not a pre-scan input. A registry that points a
`provider_default` alias at such a home fails closed under R4.5 until that
content moves into the reviewed common composition layer. The launcher does not
digest-exempt, rewrite, delete, or otherwise modify the account-home file.

The common hooks restore workmux observability without copying account-home
settings:

| Event | Window status |
| --- | --- |
| `PermissionRequest` | `waiting` |
| `Notification` with `permission_prompt` or `elicitation_dialog` | `waiting` |
| `PostToolUse` | `working` |
| `UserPromptSubmit` | `working` |
| `Stop` | `done` |

Dashboard, sidebar, status, and wait views expose the same turn state. The
workmux hook is observability-only; it cannot add dispatch or lease-write
capability, including in reviewer or standby mode.

## Mixed deployment

The role launcher and strict registry share the contract token
`orchestrator-permission-profiles-v2`. The registry header is `schema_version = 2`
and `contract_id = "orchestrator-permission-profiles-v2"`. An old binary with a new registry and a
new role launcher with an old registry both fail as `blocked_contract` before
verifier or provider execution. The reviewed launcher, registry, settings,
instructions, and policies are deployed as one compatible set and apply only to
new processes. Existing processes are not rebound during a partial deployment.
The deprecated full-auto config remains byte-preserved and is not a role-policy
source or launcher dependency.

## Cross-profile move

A cross-profile move is an explicit rebind and new execution generation, never
a live rename or account switch:

1. Stop the provider, launcher, workers, watchers, and every writer.
2. Preserve dirty tracked/untracked Git state and quality-goal state in an
   in-repository handoff.
3. For a linked worktree only, run `git worktree move OLD NEW`.
4. Verify `git worktree list --porcelain`, the top level, the absolute
   common-dir, and `git status --short`; preserve the old registry bytes if any
   check disagrees.
5. Atomically update real worktree path, account profile, and a monotonically
   newer positive binding generation.
6. Recompute the new process's write root, exact common-dir permission, sandbox,
   workmux/tmux cwd, and watcher targets, then start only from the verified
   destination handoff.

Main worktrees and linked worktrees containing submodules use a destination-root
separate clone plus handoff unless a separate repair procedure is reviewed.
There is no transparent cross-profile `/resume`: verified Git state and the
in-repository handoff are the resume unit. Any old cwd, `PWD`, generation, or
watch target blocks the new process.

## Legacy migration generation

The shipped legacy records are opaque, byte-preserved migration evidence. They
are not active aliases, mappings, defaults, explicit/stored candidates,
admission inputs, or verifier candidates. An old-alias stored binding is
`blocked_binding` and requires explicit rebind; it is never silently translated.

Migration occurs only after implementation verification in a separate
generation: stop every referencing process, create the handoff, perform any
required official login and identity admission as a separately authorized
operator action, and atomically switch to the new binding generation. A legacy
record, alias, or home can be removed only by a separately approved operation
after both process and binding reference counts are verified as zero.

## No authentication copy and no hot swap

Do not copy, sync, snapshot, rename, symlink, or delete authentication files,
credential directories, account homes, transcripts, settings, or plugin state
between profiles. Restore common behavior through reviewed secret-free settings
composition and reviewed local plugins. Never change a running process's home
environment, account, cwd, or binding generation. Migration and rebind always
hand off to a new process.

## Workspace layout owned by #95

The launcher relies on, but does not create, this workspace layout:

- canonical repository at `~/code/<repo>`;
- work paths at `~/code/<workspace-profile>/<repo>/<task>`;
- `no sessions/ or epic directories in the path`; and
- `only the final task directory is a worktree`.

The canonical repository is not cloned once per profile, and display/session
names are not path identifiers. Creating this layout belongs to #95 and is a non-goal here.
Issue #103 only consumes the normalized real path produced by that layout.

## #94/#95 registration follow-up

The shipped registry currently carries linkage fields, but
`task_bindings and session_bindings are account-binding metadata consumed from the #94/#95 common registration contracts`.
They carry account-selection and generation facts; they do not establish a
second authoritative task/session registry. If #94 or #95 later defines a single authoritative store, these fields move into it rather than being duplicated.
Until then, this issue consumes the common registration contract and does not
implement or modify either issue's registry ownership.

## Operator recovery

Every recovery starts by preserving the failure record and correcting reviewed
input or external state. Retry only in a new process. Never auto-retry by
changing model, provider, account, root, role, or policy.

| Status | Operator response |
| --- | --- |
| `blocked_contract` | Repair the reviewed registry/launcher contract or deploy the compatible source set together; do not start the verifier/provider first. |
| `blocked_role_schema` | Correct the role manifest's required fields, role-parent facts, or leader-mode contract and re-run preflight. |
| `blocked_policy` | Remove an untrusted override or correct the reviewed instruction/settings/Skill/plugin digest and policy source. |
| `blocked_permission` | Re-establish Git integrity and the exact resolved-worktree/common-dir grant; never widen to a root or wildcard. |
| `blocked_cli_contract` | Install or select a separately reviewed compatible CLI whose version and advertised options satisfy the manifest; help does not prove model availability. |
| `blocked_binding` | Reconcile the current real path, directory mapping, stored account, and positive generation atomically, then explicitly rebind in a new process. |
| `blocked_leader_conflict` | Keep the existing owner/proof unchanged; retry only with valid fresh external proof after the conflicting owner is resolved. |
| `not_logged_in` | Use the provider's official operator login path outside this automated workflow, then run fresh admission without account fallback. |
| `identity_drift` | Verify the intended official stable identity and perform separately authorized explicit enrollment only when appropriate; do not overwrite evidence automatically. |
| `blocked_verifier` | Repair the reviewed adapter, strict result, enrollment-file type/mode/owner, or stable identity contract without exposing raw output. |
| `usage_unknown` | Keep the default block, or make the current invocation's explicit dual-consent decision when the account declares `none`; never infer, scrape, or fall back. |
| `blocked_usage` | Resolve capacity for the already bound account or wait, then start a new session; do not rotate or fall back to another consumer account. |
| Provider model rejection | Preserve the provider exit, establish the pinned model's availability through an approved operator path, and retry without silent substitution. |

Move failure preserves old registry bytes plus Git and handoff state and never
publishes a partial generation. A nonzero legacy process/binding reference or
an old-path reference stops migration. Public records remain strict one-line
`account_binding`, `role_startup`, or `launch_failure` JSON without credentials,
raw verifier output, identity values, digests, or private home paths.

## Read-only account status facade

`ai-session status` reuses selection, Claude home pre-scan, verifier execution,
and the immutable admission decision without entering provider exec or any
write path. It emits one compact `profile_status` JSON line with exact fields
`schema_version`, `event`, `provider`, `account_profile`, `status`,
`login_status`, `identity_status`, `usage_status`, `cost_limit_status`, and
`commands`. A selection-time failure uses a null account alias.

Ready exits 0. Recognized non-ready admission states exit 3,
`blocked_contract` exits 2, and `blocked_binding|blocked_policy` exit 4. Command
descriptors have only `command_id`, `provider`, and `account_profile`.

| Public status | Command ID |
| --- | --- |
| `login_required` | `provider_login_foreground` |
| `enrollment_required` | `identity_enroll_foreground` |
| `identity_drift` | `inspect_identity_foreground` |
| `usage_unknown` with account contract `none` | `retry_with_usage_consent` |
| `ready`, `blocked_verifier`, `identity_unverifiable`, `duplicate_mapping`, `blocked_usage`, `blocked_contract`, `blocked_binding`, `blocked_policy` | none |

The backend returns instructions for **human-only foreground recovery** and
does not perform login, enrollment, browser interaction, retries, or account
switching.

## Status and launch failure mapping

Status preserves capability detail while launch keeps its established public
failure vocabulary. The mapping is one-to-one at the shared admission decision.

| Status facade `status` | Launch failure record `status` | Exit | Behavior |
| --- | --- | ---: | --- |
| `ready` | none | 0 | Status returns JSON; launch alone proceeds to provider exec. |
| `login_required` | `not_logged_in` | 3 | Foreground login may be considered by the operator. |
| `enrollment_required` | `blocked_verifier` | 3 | Missing or stale enrollment stays detailed only in status. |
| `blocked_verifier` | `blocked_verifier` | 3 | Fail closed. |
| `identity_drift` | `identity_drift` | 3 | Preserve drift. |
| `identity_unverifiable` | `identity_unverifiable` | 3 | Required official identity fields cannot be verified; commands stay empty. |
| `duplicate_mapping` | `duplicate_mapping` | 3 | Another active Claude profile has the same organization-context digest; commands stay empty. |
| `usage_unknown` | `usage_unknown` | 3 | Applies when exact dual consent is absent. |
| `blocked_usage` | `blocked_usage` | 3 | Fail closed. |
| `blocked_contract` | `blocked_contract` | 2 | Registry or compatible-set failure. |
| `blocked_binding` | `blocked_binding` | 4 | Binding failure. |
| `blocked_policy` | `blocked_policy` | 4 | Policy failure. |

## Profile2 private assets

No source asset is deployed into the profile2 home. The former public allowlist
of regular non-symlink mirrors of `agents/quality-reviewer.md` and
`skills/quality-goal/**` was removed in #138 because no launch path reads it
after the role launcher freeze; the canonical skill lives only in
`dot_claude/skills/quality-goal`. A temporary `.chezmoiremove` deletes the two
deployed paths by literal name. Profile2 settings, `.claude.json`, credentials,
tokens, sessions, projects, history, backups, file-history, debug, todos, plans,
plugins, identity source, and account material stay private. Account-home input
is never a trusted policy source.

`matched` means the enrollment has the same organization context. It does not
prove personal identity. The canonical input excludes email, so the same email
with a different `orgId` is allowed, while different emails with the same three
canonical fields collide. The email HMAC design is discarded; no email digest,
salt, or key is generated. Registry-derived duplicate comparison uses the same
identity root for the selected profile and all other active Claude profiles.
같은 조직의 서로 다른 사용자는 구분할 수 없다.

The rollout retains a **Keychain manual gate** after automated verification. A
human runs both Claude profiles concurrently in separate foreground panes and
records only PASS/FAIL and time after read-only organization-context checks.
The backend does not perform that action.

## #118 one-way status dependency

The integration order is `#118 create-worktree backend -> resolved profile/worktree result -> ai-session status -> foreground operator action`.
The #118 success result remains authoritative for its own JSON schema.
This code consumes only its provider, public account alias, and resolved real
worktree as status selection input. The TUI may consider launch or a recovery
action only when status is ready일 때만; it does not add a fallback resolver.

After #118 merges, rebase and manually compare these shared files:

- `tests/test_orchestrator_profiles.py`
- `dot_config/ai-session/accounts.toml`
- `.chezmoiignore`
- `docs/session-account-profiles.md`

The create-worktree skills, #118 development artifacts, profile path resolver,
and workmux creation adapter remain owned by #118.

The installed-contract checker retains Claude `2.1.272` while the measured
installation is `2.1.273`; this version mismatch is an accepted risk and the
checker is not a judgment command for this change. Pre-commit runner
availability is not a judgment command either.

## Status semantics

`waiting`, `working`, and `done` report agent-turn observability across workmux
status, dashboard, sidebar, and wait surfaces. The exact meaning is
`done = agent-turn-ended, not issue-complete`. These status surfaces are not authority or issue-completion signals.
They do not approve a change, prove verification, transfer ownership, end a
quality-goal, or authorize deployment, migration, merge, or issue closure.
