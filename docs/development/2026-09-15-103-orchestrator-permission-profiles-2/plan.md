# Quality Goal Implementation Plan

- Task ID: 103-orchestrator-permission-profiles-2
- Mode: strict
- Status: PLAN_REVIEW
- Created: 2026-09-15
- Updated: 2026-09-15
- Source goal: GitHub issue #103의 Codex·Claude 계층별 오케스트레이터 모델·권한 profile을 normalized real worktree path 기반 account 선택 정책으로 재설계한다.

## Spec link

- Approved Spec: `/Users/lee-kyu-hwan/code/dotfiles__worktrees/103-chore-orchestrator-permission-profiles/docs/development/2026-09-15-103-orchestrator-permission-profiles-2/spec.md`
- SHA-256: `db0eb8f69f2dd601c6a0a2012c7017bbc6a829c6a8b6f38ef89abdd2656d012f`
- 이 Plan은 위 digest의 55개 acceptance criterion과 `CMD-1`–`CMD-23`만 구현·판정 기준으로 사용한다.

## Global constraints

- 구현 기준 revision은 `fcfb47ee2a0514518d150554ee491aae87d26d52`다. 변경은 아래 File map의 create/modify 항목과 이 quality-goal 산출물로 제한한다. 초기 dirty path가 있으면 보존하고 작업 diff에 섞지 않는다.
- 모든 task body와 판정 표의 Python 명령은 `/opt/homebrew/bin/python3` 3.14를 명시한다. system interpreter 3.9.6은 `unittest.TestCase.enterContext`가 없어 거짓 실패를 만들므로 사용하지 않는다.
- 실제 login, logout, auth, status, usage, network, model probe를 실행하지 않는다. identity enrollment를 실행하지 않고 실제 credential, Keychain, account home 또는 `~/.local/share/ai-account-profiles/**`를 읽지 않는다.
- authentication file, credential directory, account home, transcript 또는 plugin state를 copy, sync, snapshot, symlink, rename하지 않는다. 삭제·Trash도 하지 않는다.
- 구현과 검증 중 `chezmoi apply`를 실행하지 않는다. source-to-target 판정은 temp synthetic fixture render만 사용한다.
- 현재 또는 실제 pane, tmux session/window, provider/launcher/worker/watcher process를 start, signal, restart, kill, resume, rebind하거나 environment를 변경하지 않는다. fake executable과 temp synthetic process만 허용한다.
- commit, push, PR, merge, deploy와 그 밖의 Git write를 하지 않는다. issue #94와 #95는 외부 contract로만 다루며 수정하지 않는다.
- changed-path allowlist는 role/account launcher와 symlink, `accounts.toml`, `roles.toml`, `skill-policies.toml`, Claude common/composed settings, additive instructions, provider verifier/shared identity helper, `tests/test_ai_session.py`, `tests/test_orchestrator_profiles.py`, installed-CLI checker, orchestrator E2E fixtures, `docs/orchestrator-permission-profiles.md`로 한정한다.
- `dot_claude/skills/create-worktree/**`, `dot_config/workmux/**`, `dot_tmux.conf.tmpl`, `dot_zshrc.tmpl`은 기준 revision 대비 byte-identical이어야 한다. `dot_codex/private_full_auto.config.toml`도 deprecated non-role compatibility artifact로 byte-identical하고 새 launcher에서 unreferenced여야 한다.
- deployed `[accounts.claude-dotfiles]`와 `[accounts.codex-dotfiles]` record의 원래 bytes는 registry 안의 opaque, non-mappable, non-selectable legacy evidence로 byte-identical하게 보존한다. legacy alias/home을 hot rename·rebind하거나 active candidate로 승격하지 않는다.
- account 선택은 launch 시 filesystem-resolved `os.getcwd()` real path에 한 번만 bind한다. inherited `PWD`, symlink surface, remote, owner/repository, organization은 후보나 순위에 사용하지 않는다. explicit → stored binding → longest directory mapping → Codex-only provider default와 same-priority conflict/no-fallback을 유지한다.
- account root는 selection boundary일 뿐 permission boundary가 아니다. write grant는 검증된 resolved worktree와 exact absolute Git common-dir만 허용하고 opposite profile root 전체, wildcard/add-dir, unrestricted, `danger-full-access`, `bypassPermissions`를 금지한다.
- tests는 temp Git/worktree, synthetic homes, fake provider/verifier/CLI/workmux, PTY와 sentinel만 사용한다. installed binary 접근은 help-only `CMD-9`의 `--version`/`--help`로 제한하며 model availability나 usage admission 근거로 확대하지 않는다.
- test-first 순서를 지킨다. 각 task는 이름이 명시된 test를 먼저 작성하거나 기존 test의 assertion을 먼저 새 계약으로 바꾸고, 그 test가 실제로 수집되었으며 task에 적힌 `AssertionError` 또는 명시 오류로 실패하는 것을 관찰한 뒤에만 source 구현을 추가한다. 모든 `CMD-<n>` 행에 이름이 지정된 selector는 반드시 어느 한 task의 선작성 test로 생성하고 그 task의 focused green으로 실행한다. `unittest -k`가 `Ran 0 tests`로 exit 0한 결과는 red evidence로 인정하지 않으며, 명명된 selector 하나라도 해당 run에서 `Ran 0 tests`로 확인되면 green evidence로도 인정하지 않는다. 구현 뒤 동일한 focused selector를 재실행해 exit 0을 기록한다. 실패가 예상 원인과 다르거나 sentinel이 실제 경계를 건드리면 구현을 중단하고 fixture/contract를 바로잡는다.

## File map

| 경로 | 상태 | 단일 책임과 영향 interface |
|---|---|---|
| `dot_config/ai-session/accounts.toml` | modify | path account mapping, directory-only allowed scopes, Claude home mode, positive binding generation, active three-alias topology와 두 opaque legacy record의 source of truth |
| `dot_config/ai-session/roles.toml` | create | strict role schema, provider CLI ranges/options, 네 role model/effort/permission/capability, benign config allowlist와 trusted artifact digest |
| `dot_config/ai-session/skill-policies.toml` | create | versioned Skill/plugin allow/deny, task overlay intersection, reviewer/standby deny-first capability policy |
| `dot_claude/settings.json` | create | credential·identity·account-home path가 없는 secret-free Claude common settings와 일곱 hook event source |
| `dot_config/ai-session/claude/general.settings.json` | create | common layer를 병합한 Claude general single-settings target |
| `dot_config/ai-session/claude/orchestrator.settings.json` | create | common layer를 병합한 Claude orchestrator single-settings target |
| `dot_config/ai-session/claude/feature-orchestrator.settings.json` | create | common layer를 병합한 Claude feature-orchestrator single-settings target |
| `dot_config/ai-session/claude/global-orchestrator.settings.json` | create | common layer와 global deny/permission을 병합한 Claude global single-settings target |
| `dot_config/ai-session/instructions/codex-general.md` | create | Codex general additive developer instruction bytes/version/hash |
| `dot_config/ai-session/instructions/codex-orchestrator.md` | create | Codex orchestrator additive developer instruction bytes/version/hash |
| `dot_config/ai-session/instructions/codex-feature-orchestrator.md` | create | Codex quality-goal feature additive developer instruction bytes/version/hash |
| `dot_config/ai-session/instructions/codex-global-orchestrator.md` | create | Codex global additive developer instruction bytes/version/hash |
| `dot_config/ai-session/instructions/claude-general.md` | create | Claude general single additive prompt bytes/version/hash |
| `dot_config/ai-session/instructions/claude-orchestrator.md` | create | Claude workgroup orchestrator single additive prompt bytes/version/hash |
| `dot_config/ai-session/instructions/claude-feature-orchestrator.md` | create | Claude quality-goal feature single additive prompt bytes/version/hash |
| `dot_config/ai-session/instructions/claude-global-orchestrator.md` | create | Claude global single additive prompt bytes/version/hash |
| `dot_local/bin/executable_ai-role-session` | create | argv[0] role/provider dispatch, role/task/parent/leader preflight, settings/instruction/Skill verification, final argv와 one-exec admitted phase |
| `dot_local/bin/symlink_ai-codex` | create | general Codex entrypoint symlink to `ai-role-session` |
| `dot_local/bin/symlink_ai-codex-orchestrator` | create | Codex workgroup orchestrator entrypoint symlink |
| `dot_local/bin/symlink_ai-codex-feature-orchestrator` | create | Codex quality-goal feature entrypoint symlink |
| `dot_local/bin/symlink_ai-codex-global-orchestrator` | create | Codex global entrypoint symlink |
| `dot_local/bin/symlink_ai-claude` | create | general Claude entrypoint symlink |
| `dot_local/bin/symlink_ai-claude-orchestrator` | create | Claude workgroup orchestrator entrypoint symlink |
| `dot_local/bin/symlink_ai-claude-feature-orchestrator` | create | Claude quality-goal feature entrypoint symlink |
| `dot_local/bin/symlink_ai-claude-global-orchestrator` | create | Claude global entrypoint symlink |
| `dot_local/bin/executable_ai-session` | modify | v1 compatibility plus strict registry parsing, real-path priority selection, authorization, verifier classification, scrubbed child env와 public record의 single source of truth |
| `dot_local/libexec/executable_ai-session-verify-codex` | create | official Codex status adapter command builder, timeout, six-field redacted result |
| `dot_local/libexec/executable_ai-session-verify-claude` | create | official Claude auth-status adapter와 `not_logged_in`/`usage_unknown` evidence |
| `dot_local/libexec/executable_ai-session-enroll-identity` | create | explicit host-local enrollment interface; production invocation 없이 synthetic atomic-file tests만 제공 |
| `dot_local/libexec/ai_session_identity.py` | create | verifier와 enrollment helper가 공유하는 canonical projection, normalization, digest parser |
| `tests/test_ai_session.py` | modify | `test_deployed_registry_selects_provider_specific_dotfiles_profiles`만 replaced deployed-registry contract로 갱신하고 나머지 direct-caller assertion, exit 2/3, verifier timeout/env, no-fallback 회귀는 그대로 보존 |
| `tests/test_orchestrator_profiles.py` | create | `CMD-1`–`CMD-8`, `CMD-10`–`CMD-23`의 portable unit/integration/PTY/move/workmux contracts |
| `tests/check_installed_orchestrator_cli_contract.py` | create | `CMD-9` 전용 installed version/help-only release gate |
| `tests/fixtures/orchestrator-profiles/e2e/**` | create | temp two-root Git/worktree, synthetic registries/homes, fake provider/verifier/CLI/workmux, hostile/benign config, lease/FD/PTY/sentinel evidence |
| `docs/orchestrator-permission-profiles.md` | create | role/file map, 운영 recovery, path/home/permission/settings/leader/move/legacy/status semantics contract |
| `docs/claude-settings-reference.json` | inspect-only | common Claude settings, plugin, existing Notification/PostToolUse/Stop/UserPromptSubmit hook shape와 변경 없이 presence/digest 검사할 `SubagentStop`·`TaskCompleted` command/status bytes reference |
| `dot_codex/hooks.json` | inspect-only | PermissionRequest/working/done workmux hook command shape reference |
| `docs/development/2026-09-15-103-orchestrator-permission-profiles/installed-cli-contract-evidence.md` | inspect-only | `CMD-9`가 비교하는 frozen Codex 0.154.0/Claude 2.1.272 help-only evidence |
| `dot_codex/private_full_auto.config.toml` | inspect-only | byte-preserved deprecated non-role artifact; role manifest/dispatcher reference가 없어야 함 |
| `dot_claude/skills/create-worktree/**` | inspect-only | 기준 revision 대비 byte-preservation target |
| `dot_config/workmux/**` | inspect-only | fake workmux로만 관측할 byte-preservation target |
| `dot_tmux.conf.tmpl` | inspect-only | 기준 revision 대비 byte-preservation target |
| `dot_zshrc.tmpl` | inspect-only | 기존 PATH 계약을 유지하는 byte-preservation target |

## Task dependencies

- `T1`은 fixture skeleton과 ownership/entrypoint contract를 만들며 모든 후속 task가 사용한다.
- `T2`는 active registry/path binding interface를 만들고 `T3`–`T12`의 account context를 제공한다. `T3`의 role manifest와 dispatcher interface는 `T4`–`T6`, `T8`–`T12`가 소비한다.
- `T4`와 `T5`는 각각 Claude settings 및 instruction/public-record interfaces를 완성한다. `T5`는 capability를 소비하지 않고 binding/failure record, instruction과 stdio chain까지만 만든다. `T6`이 leader/Skill capability, one-shot capability 소비, final startup facts와 role/account orthogonality를 완성하므로 실행 순서는 `T4` → `T5` → `T6`이다.
- `T6`의 leader/Skill capability와 `T7`의 verifier/identity parser는 각각 선행 interface만 소비해 fixture로 개발한 뒤 dispatcher→selector→verifier single-exec chain에서 합친다.
- `T8`은 `T2`, `T4`, `T7` 뒤에 home-mode와 exact scrub을 다섯 surface에서 연결한다. `T9`은 `T2`와 `T3` 뒤에 selection root와 write boundary를 분리한다.
- `T10`은 `T2`의 generation binding과 `T9`의 exact common-dir contract를 소비한다. 실제 worktree/process는 건드리지 않고 temp linked-worktree fixture만 이동한다.
- `T11`은 `T2`의 active/legacy parser와 `T10`의 migration generation gate 뒤에 legacy protection을 고정한다. 원래 legacy record bytes를 수정하지 않는다.
- `T12`는 `T4`의 trusted composed settings와 `T6`의 observability-only capability를 소비한다. fake workmux 외의 pane/session/process에는 접근하지 않는다.
- `T13`은 launcher/manifest가 안정된 뒤 CLI range와 mixed-deployment compatibility를 닫고, `T14`는 구현된 계약을 운영 문서에 직렬화한다.
- `T15`는 `T1`–`T14` 이후 complete File map ownership test를 추가하고 changed-path/preservation, sensitive/no-live-action sentinel, network-denied E2E, portable/full suite를 순서대로 실행한다. 어떤 final gate도 선행 targeted failure를 대신하지 않는다. 각 task의 green은 그 task보다 앞선 산출물만 소비하며, 뒤 task가 만드는 파일을 요구하는 full command는 해당 criterion을 최종 소유한 뒤 task에서만 실행한다.

## Tasks

### T1. Fixture skeleton, strict ownership, roles and eight entrypoints

대상 AC: AC-2 (CMD-1), AC-3 (CMD-1)

1. 테스트 선작성과 실패 확인: `tests/test_orchestrator_profiles.py`에 `test_role_manifest`, `test_launcher_entrypoints`를 먼저 작성하고 source 존재·정확한 role/target을 명시적으로 assert한다. focused `CMD-1` command `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_role_manifest -k test_launcher_entrypoints`를 실행해 두 test가 수집되고 `AssertionError: roles.toml is required before role dispatch`로 실패함을 관찰한다. `Ran 0 tests`는 실패 증거가 아니다.
2. 최소 구현: `tests/test_orchestrator_profiles.py`에 기존 `TemporaryDirectory`, subprocess capture, fake executable helper style를 따르는 fixture base와 네 role/여덟 argv[0] case를 만든다. `roles.toml`, `skill-policies.toml`, `executable_ai-role-session`, 여덟 `symlink_ai-*` source를 strict schema와 단일 dispatcher ownership까지만 추가하고 selector/verifier parsing이 wrapper에 중복되지 않음을 검사한다.
3. 통과 확인: 같은 focused `CMD-1` command가 네 role 이름과 여덟 symlink target/provider/role을 확인하며 exit 0인지 기록한다. complete File map ownership은 모든 파일이 존재한 뒤 `T15`가 `test_file_ownership`과 full `CMD-1`로 판정한다.

### T2. Path-only account registry and selection engine

대상 AC: AC-10 (CMD-4), AC-11 (CMD-4), AC-12 (CMD-4), AC-14 (CMD-4)

1. 테스트 선작성과 실패 확인: `test_account_registry_schema`, `test_real_path_account_selection`, `test_allowed_scope_kind_contract`, `test_no_account_fallback`을 먼저 작성해 `accounts.toml`의 strict active/legacy schema와 deployed v1 registry의 directory mapping schema를 assert한다. focused `CMD-1` selector `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_account_registry_schema`를 실행해 test가 수집되고 `AssertionError: accounts.toml strict schema is missing`으로 실패함을 관찰하고, focused `CMD-4` command `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_real_path_account_selection -k test_allowed_scope_kind_contract -k test_no_account_fallback`를 실행해 세 test가 수집되고 `AssertionError: workspace_directory_mappings is required`로 실패함을 관찰한 뒤에만 구현한다.
2. 최소 구현: `accounts.toml`과 `executable_ai-session`을 strict active `accounts`/`workspace_directory_mappings`/task-session binding/generation 및 opaque `legacy_records` schema로 확장한다. filesystem-resolved cwd, path-component ancestor, unique longest root, explicit→stored→directory→Codex-only default, directory-only authorization, outside-Claude-root/ambiguity/stale surface failure를 selector 하나에서 구현한다. remote/common-dir는 selection에서 제거하고 integrity field로만 유지한다.
3. 통과 확인: 같은 focused `CMD-1` selector가 strict active/legacy account registry schema를 확인하고, 같은 focused `CMD-4` command가 `~/code/**`→`codex-default`, profile1/profile2/outside matrix, same-remote different-root, reserved full-alias rule, non-directory schema rejection, no re-selection/ranking/fallback을 모두 확인하며 각각 exit 0인지 기록한다. `test_role_account_orthogonality`는 `T6`, child environment tests는 `T8`에서 각 선행 구현 뒤 추가한다.

### T3. Codex role matrix, permission policy and project-config pre-scan

대상 AC: AC-5 (CMD-2), AC-16 (CMD-2), AC-17 (CMD-2 CMD-11)

1. 테스트 선작성과 실패 확인: `test_codex_policy`, `test_codex_project_config_prescan`을 먼저 작성해 pinned matrix와 hostile config의 pre-exec denial을 assert한다. `CMD-2` exact command `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_codex_policy -k test_codex_project_config_prescan`를 실행해 두 test가 수집되고 `AssertionError: Codex role policy is missing`으로 실패함을 관찰한 뒤에만 구현한다.
2. 최소 구현: `roles.toml`에 네 Codex policy를 고정하고 dispatcher가 final `--model`, effort, approval, legacy sandbox, exact work root와 additive instruction override를 만든다. repository root→real cwd의 regular non-symlink TOML chain을 읽어 exact benign key만 허용하고 policy/unknown key, beta mixing, tail override, unrestricted/bypass/add-dir를 pre-exec `blocked_policy|blocked_permission`으로 닫는다.
3. 통과 확인: 같은 `CMD-2` command가 네 role capture, benign/hostile chain, provider 0회, no fallback을 확인하며 exit 0인지 기록한다. `CMD-11` exact command `AI_SESSION_E2E_NETWORK=deny /opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_high_risk_e2e`의 통합 판정은 E2E test를 선작성하는 `T15`에서만 실행한다.

### T4. Claude policy and trusted common/composed settings

대상 AC: AC-6 (CMD-3), AC-19 (CMD-18), AC-49 (CMD-18 CMD-3)

1. 테스트 선작성과 실패 확인: `CMD-3`/`CMD-18`에 이름 난 Claude policy, composition, digest, source, plugin, untrusted-settings tests를 먼저 작성해 composed targets와 trust-source를 assert한다. `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_claude_policy -k test_claude_settings_prescan`와 `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_claude_settings_composition -k test_claude_settings_digest -k test_effective_setting_sources -k test_claude_plugin_policy -k test_claude_untrusted_settings_prescan`를 실행해 test가 수집되고 `AssertionError: trusted composed settings are missing`으로 실패함을 관찰한 뒤에만 구현한다.
2. 최소 구현: `dot_claude/settings.json`과 네 `claude/*.settings.json`에 secret-free common layer, dontAsk/fail-closed sandbox, role deny 우선, reviewed local plugin과 일곱 hook event source를 구조 병합한다. exact-transition 대상은 `Stop`, 두 `Notification` case, `PostToolUse`, `UserPromptSubmit`, `PermissionRequest`이며 `SubagentStop`과 `TaskCompleted`는 reviewed `docs/claude-settings-reference.json`의 command/status bytes를 변경 없이 유지하고 presence/digest만 검사하여 exact-transition assertion set에서는 제외한다. dispatcher는 regular non-symlink JSON을 read-once/version/SHA-256 검증해 single `--settings`, repeatable local `--plugin-dir`만 전달하고 `--plugin-url`/launch write를 금지한다. discovered account/project/local settings는 empty 또는 `$schema`, `spinnerTipsEnabled`, `theme`만 허용한다.
3. 통과 확인: 같은 `CMD-3`과 `CMD-18` commands가 네 model/effort, Fable elevation reason, exact digest/effective sources, role deny, benign/hostile settings, provider 0회와 no precedence assumption을 확인하며 각각 exit 0인지 기록한다.

### T5. Additive instructions, public records and single-exec stdio

대상 AC: AC-9 (CMD-5), AC-20 (CMD-5), AC-23 (CMD-5)

1. 테스트 선작성과 실패 확인: `CMD-5`의 binding/failure, task-parent, instruction, PTY, new-process/no-mutation tests를 먼저 작성해 instruction digest와 unchanged FD identity를 assert한다. `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_binding_record -k test_task_parent_binding -k test_instruction_hash -k test_stdio_tty_inheritance -k test_new_process_only -k test_no_current_pane_mutation`를 실행해 test가 수집되고 `AssertionError: reviewed instruction digest is missing`으로 실패함을 관찰한 뒤에만 구현한다.
2. 최소 구현: 여덟 instruction file과 manifest hash/version을 추가하고 dispatcher가 UTF-8/NUL/symlink/digest를 read-once 검증한다. Codex는 developer instruction, Claude는 single `--append-system-prompt` value만 사용한다. `ai-session`의 `account_binding`, admitted phase의 capability-independent `role_startup` fields와 모든 `launch_failure`를 sorted compact one-line JSON으로 inherited stderr에 직접 쓰고 provider로 single exec한다. one-shot capability 생성·소비와 Skill/leader startup facts는 아직 참조하지 않고 `T6`이 추가한다. resume/continue/session-ID를 pre-exec 거부한다.
3. 통과 확인: 같은 focused `CMD-5` command가 capability-independent binding/failure field/type/generation, alternate instruction path 거부, provider stderr ownership, stdin/stdout/stderr `isatty`와 FD identity, current pid/env/state byte 불변을 확인하며 exit 0인지 기록한다. final startup Skill/leader fields는 `T6` 전에는 요구하지 않는다.

### T6. Leader lease, Skill policy and reviewer/standby denial

대상 AC: AC-21 (CMD-4 CMD-5), AC-24 (CMD-6), AC-25 (CMD-6), AC-31 (CMD-6 CMD-8), AC-32 (CMD-8 CMD-12), AC-51 (CMD-6)

1. 테스트 선작성과 실패 확인: `CMD-6` tests와 `test_skill_policy`, `test_full_auto_compatibility`, `test_role_account_orthogonality`, final `test_startup_record`를 먼저 작성해 leader/Skill facts가 account 변화에도 동일함을 assert한다. `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_global_leader -k test_lock_fd_inheritance -k test_reviewer_standby -k test_takeover -k test_role_account_orthogonality -k test_startup_record`와 focused `CMD-8` command `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_skill_policy -k test_full_auto_compatibility`를 실행해 test가 수집되고 `AssertionError: one-shot leader capability is missing`으로 실패함을 관찰한 뒤에만 구현한다.
2. 최소 구현: `roles.toml`과 `skill-policies.toml`에 strict lease proof, normalized-scope lock, active/reviewer/standby capability와 allow∩overlay minus deny를 추가한다. dispatcher가 account-independent one-shot capability와 lock을 만들고 `ai-session`은 authorization/admission 뒤 required contract token으로 admitted phase에 전달하며, admitted phase가 capability를 한 번 소비·close한다. global active lock FD만 provider lifetime까지 상속하고 verifier에는 어떤 capability/lock FD도 넘기지 않는다. reviewer/standby의 dispatch, multi-agent, lease-write, lock을 실행 권한에서 제거하며 workmux는 observability-only로 남긴다. final startup record의 Skill/leader facts와 role/account orthogonality를 여기서 완성한다. `private_full_auto.config.toml`은 읽지 않고 byte-preserved/unreferenced assertion만 둔다.
3. 통과 확인: 같은 `CMD-6`, focused `CMD-8`, focused `CMD-4`/`CMD-5` selectors가 same-scope race 한 승자, different-scope/reacquire, verifier FD 부재, invalid takeover 무변경, deny-first policy ID/count, full-auto unreferenced, final startup facts와 account 변화에도 동일한 role policy bytes를 확인하며 exit 0인지 기록한다.

### T7. Provider verifiers, shared identity and unique failure classifier

대상 AC: AC-7 (CMD-7 CMD-8), AC-26 (CMD-7 CMD-17), AC-27 (CMD-7), AC-28 (CMD-7 CMD-15), AC-29 (CMD-8)

1. 테스트 선작성과 실패 확인: `CMD-7` tests와 `test_failure_status`를 먼저 작성해 strict six-field payload와 precedence를 assert한다. `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_live_verifier -k test_account_status_precedence -k test_identity_canonicalization -k test_identity_enrollment -k test_verifier_redaction`와 focused `CMD-8` command `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_failure_status`를 실행해 test가 수집되고 `AssertionError: verifier must return six redacted fields`로 실패함을 관찰한 뒤에만 구현한다.
2. 최소 구현: 두 provider verifier와 `ai_session_identity.py`를 strict six-field, 10초 timeout, captured/redacted I/O, `close_fds=True`, empty `pass_fds`로 구현한다. NFC/trim/case/control, sorted compact JSON, SHA-256+LF canonicalizer를 공유하고 enrollment helper는 synthetic invocation에서만 owner 0700/0600 regular non-symlink fsync+atomic replace를 수행한다. `ai-session` 한 곳에서 exit 2/3 분류와 `not_logged_in`→`identity_drift`→`blocked_verifier`→`usage_unknown`→`blocked_usage` precedence를 적용한다.
3. 통과 확인: 같은 `CMD-7`과 focused `CMD-8` commands가 Claude unlogged/logged 분류, provider/fallback 0회, canonical fixtures, atomic-failure old digest preservation, redaction, unique status/exit와 model rejection passthrough를 확인하며 exit 0인지 기록한다.

### T8. Claude home modes and exact credential environment scrub

대상 AC: AC-13 (CMD-17), AC-15 (CMD-4)

1. 테스트 선작성과 실패 확인: `CMD-17` tests와 `test_child_environment`, `test_exact_credential_scrub`을 먼저 작성해 다섯 surface와 exact 19-key removal을 assert한다. `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_claude_config_home_modes -k test_claude_default_env_unset -k test_claude_explicit_env -k test_verifier_provider_environments -k test_child_environment -k test_exact_credential_scrub`를 실행해 test가 수집되고 `AssertionError: provider-default Claude must not export CLAUDE_CONFIG_DIR`로 실패함을 관찰한 뒤에만 구현한다.
2. 최소 구현: parent env에서 Spec의 exact 19-key scrub set을 먼저 제거하고 selected Codex home 또는 explicit Claude home만 verifier/admitted/provider private child에 조건부 재도입한다. `claude-profile1`은 source/target/argv/verifier/provider 다섯 surface 모두 `CLAUDE_CONFIG_DIR` key와 default-home literal export가 없게 하고 `claude-profile2`만 exact absolute non-symlink neutral profile2 path를 받게 한다. invalid mode/path/symlink는 pre-exec `blocked_contract`다.
3. 통과 확인: 같은 `CMD-17`과 `CMD-4` commands가 다섯 surface, exact scrub, opposite-provider key 부재, synthetic explicit env와 no fallback을 확인하며 exit 0인지 기록한다.

### T9. Worktree/common-dir permission boundary

대상 AC: AC-36 (CMD-20), AC-37 (CMD-20 CMD-21)

1. 테스트 선작성과 실패 확인: `test_account_root_permission_separation`, `test_exact_git_common_dir_permission`, `test_no_opposite_root_grant`를 먼저 작성해 exact two-path allow set을 assert한다. focused `CMD-20` command `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_account_root_permission_separation -k test_exact_git_common_dir_permission -k test_no_opposite_root_grant`를 실행해 test가 수집되고 `AssertionError: account root must not be a write grant`로 실패함을 관찰한 뒤에만 구현한다.
2. 최소 구현: `ai-session`이 selection 뒤 Git integrity를 검사하고 write-capable role의 allow set을 resolved worktree와 `git rev-parse --path-format=absolute --git-common-dir` exact path로만 만든다. whole profile root, wildcard/add-dir, unverified cross-root metadata를 거부하고 external common-dir를 exact 허용할 수 없는 case는 destination-root separate clone+handoff recovery로 fail closed한다. dispatcher는 role/write-need 입력과 required contract token만 전달하며 authorization 결정이나 grant construction을 하지 않는다. stale `PWD`와 shutdown-proof enforcement는 move protocol을 완성하는 `T10`의 `ai-session` path에서 추가한다.
3. 통과 확인: 같은 focused `CMD-20` command가 two-path allow set, opposite-root grant 0과 linked external common-dir judgement를 확인하며 exit 0인지 기록한다. stale-PWD와 shutdown-proof 판정은 `T10`이 해당 test를 선작성·구현한 뒤 full `CMD-20`으로 닫는다.

### T10. Cross-profile move and atomic rebind protocol

대상 AC: AC-38 (CMD-20 CMD-21), AC-39 (CMD-21), AC-40 (CMD-21), AC-41 (CMD-21), AC-42 (CMD-21), AC-43 (CMD-21 CMD-15), AC-44 (CMD-21)

1. 테스트 선작성과 실패 확인: `CMD-21` tests와 `test_stale_pwd_rejected`를 먼저 작성해 missing shutdown proof와 stale `PWD`가 registry update 전에 거부됨을 assert한다. `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_cross_profile_move_shutdown -k test_git_worktree_move_and_verify -k test_stale_binding_block -k test_binding_generation_rebind -k test_move_handoff -k test_separate_clone_alternative -k test_stale_pwd_rejected`를 temp fixture에서 실행해 test가 수집되고 `AssertionError: shutdown proof is required before rebind`로 실패함을 관찰한 뒤에만 구현한다.
2. 최소 구현: temp linked-worktree fixture에 provider/workers/watchers/writers shutdown proof와 dirty tracked/untracked 및 in-repository quality-state handoff를 요구한다. `ai-session`이 real cwd와 inherited `PWD` 불일치를 selection/registry update 전에 `blocked_binding`으로 닫고 shutdown proof를 검증한다. dispatcher는 move inputs와 contract token만 전달하고 stale-path/authorization 결정을 하지 않는다. linked worktree만 fixture `git worktree move` 후 list/top-level/common-dir/status 네 결과를 검증하고 path/profile/new positive generation을 atomic bytes로 publish한다. main/submodule과 cross-root denial은 separate clone+handoff로 닫고 새 process 전 write root/common-dir/sandbox/workmux/tmux/watcher targets를 new real path로 재계산한다.
3. 통과 확인: full `CMD-20` command `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_account_root_permission_separation -k test_exact_git_common_dir_permission -k test_no_opposite_root_grant -k test_stale_pwd_rejected`와 `CMD-21` command가 partial/stale binding에서 old registry 보존과 provider 0회, dirty state 보존, destination-profile new-process-only handoff, old cwd/PWD/watch reference 0, transcript/credential/plugin/home copy·symlink·hot swap 0회를 확인하며 각각 exit 0인지 기록한다.

### T11. Shipped active topology and legacy-record migration gates

대상 AC: AC-45 (CMD-22 CMD-15), AC-46 (CMD-22), AC-55 (CMD-22)

1. 테스트 선작성과 실패 확인: `CMD-22` tests를 먼저 작성하고 기존 `tests/test_ai_session.py::AiSessionCliTests.test_deployed_registry_selects_provider_specific_dotfiles_profiles`의 assertion을 새 deployed contract로 먼저 갱신한다. 이 이름은 v1 registry contract test의 이력을 보존하되, 새 expectation은 두 legacy record bytes가 남아 있어도 `codex-dotfiles`와 `claude-dotfiles`가 active selection 후보가 아니며 각 alias의 explicit request가 `blocked_binding`으로 거부되는 것이다. `/opt/homebrew/bin/python3 -m unittest -v tests.test_ai_session.AiSessionCliTests.test_deployed_registry_selects_provider_specific_dotfiles_profiles`와 `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_legacy_alias_home_protection -k test_codex_default_existing_home -k test_legacy_records_non_selectable -k test_old_alias_binding_blocked -k test_migration_generation_gate -k test_legacy_zero_reference_removal`를 실행해 test가 수집되고 기존 deployed registry 때문에 `AssertionError: legacy aliases must be non-selectable`로 실패함을 관찰한 뒤에만 구현한다.
2. 최소 구현: shipped active declarations를 `codex-default`, `claude-profile1`, `claude-profile2` 정확히 세 개와 required directory mappings/home modes로 제한하고 `defaults`/`scope_bindings` table을 제거한다. 두 deployed record 원문 bytes는 opaque `legacy_records` evidence로 보존해 parser·mapping·explicit/stored/default·verifier 후보에서 배제한다. old alias binding은 silent mapping 없이 `blocked_binding`으로 만들고 separate migration generation, shutdown/handoff, synthetic official admission proof와 per-record zero-process/zero-binding removal gate를 fixture contract로 추가한다. `tests/test_ai_session.py`에서는 위 한 v1 deployed-registry test의 기대만 교체하고 파일의 나머지 test와 assertion은 수정하지 않는다.
3. 통과 확인: 같은 두 commands가 active topology, `~/.codex` reuse, neutral profile2 home, two legacy byte spans, 두 explicit old-alias request의 pre-verifier `blocked_binding`, no home read/create/move/login/rename/rebind/copy/symlink/delete를 확인하며 exit 0인지 기록한다. 이어 `/opt/homebrew/bin/python3 -m unittest -v tests/test_ai_session.py`로 변경 대상 test 외 기존 suite의 나머지 assertion이 그대로 통과함을 확인한다.

### T12. Agent-turn workmux hooks and all status surfaces

대상 AC: AC-18 (CMD-3 CMD-18 CMD-19), AC-47 (CMD-19), AC-48 (CMD-18 CMD-15), AC-50 (CMD-19), AC-52 (CMD-19), AC-53 (CMD-23)

1. 테스트 선작성과 실패 확인: `CMD-19`/`CMD-23` tests를 먼저 작성해 direct PermissionRequest transition, active-work non-stale state와 four-surface agreement를 assert한다. `AI_SESSION_E2E_NETWORK=deny /opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_workmux_event_transitions -k test_permission_request_waiting -k test_no_stale_done_during_active_work -k test_no_running_process_mutation`와 `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_workmux_status_surface -k test_workmux_dashboard_surface -k test_workmux_sidebar_surface -k test_workmux_wait_surface`를 실행해 test가 수집되고 `AssertionError: PermissionRequest must transition directly to waiting`으로 실패함을 관찰한 뒤에만 구현한다.
2. 최소 구현: trusted common settings에 Stop→done, 두 Notification case→waiting, PostToolUse/UserPromptSubmit→working, PermissionRequest→direct waiting을 정확히 구성하고 existing notification hooks를 보존한다. `SubagentStop`과 `TaskCompleted`는 `T4`가 reviewed reference에서 유지한 command/status bytes를 변경하지 않고 composition presence/digest 대상으로 남기며 R11.1/CMD-19의 exact-transition assertion set에는 넣지 않는다. synthetic separate config home과 call-recording fake workmux로 event sequence와 status/dashboard/sidebar/wait를 구현하되 settings/account home을 copy·sync·snapshot·symlink하지 않고 hook에 secret/identity/home path를 넣지 않는다.
3. 통과 확인: 같은 `CMD-19`와 `CMD-23` commands 및 `CMD-3`, `CMD-18` exact commands `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_claude_policy -k test_claude_settings_prescan`와 `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_claude_settings_composition -k test_claude_settings_digest -k test_effective_setting_sources -k test_claude_plugin_policy -k test_claude_untrusted_settings_prescan`가 일곱 event source의 composition, exact transition, active-work stale done 부재, trusted-source-only hooks, real pane/session/window/process mutation 0과 동일 turn state를 확인하며 exit 0인지 기록한다.

### T13. CLI compatibility, mixed deployment and direct-caller regression

대상 AC: AC-8 (CMD-9 CMD-16), AC-33 (CMD-8 CMD-13)

1. 테스트 선작성과 실패 확인: `test_portable_cli_contract`, `test_registry_contract_mixed_deployment`를 먼저 작성해 range와 양방향 token mismatch denial을 assert한다. `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_portable_cli_contract`와 `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_registry_contract_mixed_deployment`를 실행해 test가 수집되고 `AssertionError: registry contract token is required`로 실패함을 관찰한 뒤에만 구현한다.
2. 최소 구현: manifest에 Codex `>=0.154.0,<0.155.0`, Claude `>=2.1.269,<2.2.0`, required/forbidden options를 strict하게 넣고 fake lower/in-range/upper/missing-option fixtures를 추가한다. dispatcher가 required registry contract token을 전달해 old-binary/new-registry와 new-binary/old-registry를 `blocked_contract`로 닫되, `T11`에서 명시적으로 교체한 deployed-registry selection expectation 외 direct v1 `ai-session select|launch` JSON, exit 2/3, timeout/env/no-fallback behavior와 assertion은 유지한다. installed checker는 frozen evidence와 version/help만 비교한다.
3. 통과 확인: 같은 `CMD-16`과 focused `CMD-8` commands가 exit 0인지 기록하고 focused `CMD-13` command `/opt/homebrew/bin/python3 -m unittest -v tests/test_ai_session.py`로 updated deployed-registry contract test를 포함한 direct compatibility suite가 통과하는지 확인한다. `tests/test_ai_session.py`에서 `T11`이 명시한 한 test 외 나머지 assertion은 그대로여야 한다. 아직 작성되지 않은 `T14`/`T15` tests를 포함하는 full `CMD-13`과 `CMD-9`는 `T15` final gate에서만 실행한다.

### T14. Operator and migration documentation

대상 AC: AC-34 (CMD-8), AC-54 (CMD-8)

1. 테스트 선작성과 실패 확인: `test_documentation_contract`를 먼저 작성해 required headings와 exact phrases를 assert한다. focused `CMD-8` command `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_documentation_contract`를 실행해 test가 수집되고 `AssertionError: operator recovery heading is missing`으로 실패함을 관찰한 뒤에만 문서를 작성한다.
2. 최소 구현: `docs/orchestrator-permission-profiles.md`에 role/file map, real-path selection와 alias/home mode, model pin 대 availability, Claude `usage_unknown` operator response, exact permission/common-dir/scrub, stdio/TTY, leader, verifier/identity, trusted settings/effective sources/workmux, mixed deployment, cross-profile move, legacy separate generation, no-auth-copy/no-hot-swap와 status별 recovery를 기록한다. exact phrase `done = agent-turn-ended, not issue-complete`와 모든 status surface가 authority 또는 issue-completion signal이 아니라는 문구를 포함한다.
3. 통과 확인: 같은 `CMD-8` command가 문서와 이미 구현된 failure/mixed/Skill/full-auto contracts를 함께 확인하며 exit 0인지 기록한다.

### T15. Preservation, sensitive-boundary and full high-risk gates

대상 AC: AC-1 (CMD-12), AC-4 (CMD-1), AC-22 (CMD-5 CMD-15), AC-30 (CMD-15), AC-35 (CMD-9 CMD-10 CMD-11 CMD-12 CMD-13 CMD-14 CMD-15 CMD-16 CMD-17 CMD-18 CMD-19 CMD-20 CMD-21 CMD-22)

1. 테스트 선작성과 실패 확인: `test_file_ownership`, final `test_startup_record` sensitive-field assertions, `test_sensitive_data_hygiene`, `test_no_auth_copy_or_symlink`, `test_legacy_home_preservation`, `test_no_unrestricted_path`, `test_changed_path_allowlist`, `test_path_selection_regression`, `test_high_risk_e2e`, `test_chezmoi_fixture_render`를 먼저 작성해 complete File map, final public records, sentinels, allowlist와 #111 explicit→stored→longest-directory→Codex-only-default/conflict/no-fallback regression matrix를 assert한다. focused `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_file_ownership -k test_startup_record -k test_sensitive_data_hygiene -k test_no_auth_copy_or_symlink -k test_legacy_home_preservation -k test_no_unrestricted_path -k test_changed_path_allowlist -k test_high_risk_e2e -k test_chezmoi_fixture_render`를 실행해 test가 수집되고 `AssertionError: complete File map ownership has not been verified`로 실패함을 관찰하며, focused `CMD-12` selector `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_path_selection_regression`를 실행해 test가 수집되고 `AssertionError: selection priority regression matrix is incomplete`로 실패함을 관찰한 뒤에만 final fixture를 구현한다. `Ran 0 tests`는 red가 아니며 preserved-path diff가 nonzero이면 해당 path를 수정하지 않고 중단한다.
2. 최소 구현: tests/fixtures에 real auth/status/login/logout/usage/network/model/enrollment/account-home/current-process/production access, provider preflight bypass, credential/home copy·sync·snapshot·symlink·rename/delete, sensitive public output, unrestricted/opposite-root grant가 접근 즉시 실패하는 sentinels를 완성한다. changed-path allowlist와 base byte checks를 추가하고 실제 deployed home string은 registry/render target 및 permitted private synthetic-env assertion 외 disclosure surface에서 금지한다. fixture render, network-denied E2E, preservation/regression, portable suite와 discovery/diff-check를 연결하되 source 외 대상과 frozen evidence를 수정하지 않는다.
3. 통과 확인: focused `CMD-12` selector `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_path_selection_regression`가 #111 selection priority/conflict/no-fallback matrix를 확인해 exit 0인지 먼저 기록한다. 이어 full `CMD-1`, final public-record `CMD-5`와 표에 정의된 exact `CMD-15`, `CMD-12`, `CMD-10`, `CMD-11`, `CMD-13`, `CMD-14`, `CMD-16`, `CMD-17`, `CMD-18`, `CMD-19`, `CMD-20`, `CMD-21`, `CMD-22`, `CMD-23`, 마지막 help-only `CMD-9`를 이 순서로 실행해 모두 exit 0인지 기록한다. 이 시점에는 `T1`–`T14` 산출물이 모두 존재하므로 complete ownership과 full command 어느 것도 뒤 task에 의존하지 않는다. 어느 sentinel 또는 gate가 실패하면 deployment를 진행하지 않고 Rollout and rollback의 pre-task snapshot으로 복구한다.

## Verification commands

실행 순서는 targeted tests, relevant full suite, installed release gate, high-risk end-to-end, whitespace check다. 각 단계가 exit 0일 때만 다음 단계로 진행하며, 마지막 `CMD-14`는 전체 discovery 뒤 `git diff --check`를 수행한다.

실행 가능한 판정 명령 표는 다음과 같다. 각 `CMD-<n>` 은 이 표의 행으로 정의되며 추적표와 태스크 본문의 참조는 모두 이 표에서 해석된다.

| ID | 명령 | 통과 조건 |
|---|---|---|
| CMD-1 | `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_role_manifest -k test_account_registry_schema -k test_launcher_entrypoints -k test_file_ownership` | 네 role, strict registry와 ownership, 여덟 symlink와 단일 dispatcher가 확인되고 exit 0이다. |
| CMD-2 | `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_codex_policy -k test_codex_project_config_prescan` | Codex role matrix와 config pre-scan의 허용·거부 case가 모두 통과하고 exit 0이다. |
| CMD-3 | `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_claude_policy -k test_claude_settings_prescan` | Claude role/settings policy, Fable elevation 사유, no-fallback이 확인되고 exit 0이다. |
| CMD-4 | `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_real_path_account_selection -k test_allowed_scope_kind_contract -k test_role_account_orthogonality -k test_child_environment -k test_exact_credential_scrub -k test_no_account_fallback` | real-path selection, directory-only authorization, role/account 직교성, exact scrub와 no-fallback이 확인되고 exit 0이다. |
| CMD-5 | `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_startup_record -k test_binding_record -k test_task_parent_binding -k test_instruction_hash -k test_stdio_tty_inheritance -k test_new_process_only -k test_no_current_pane_mutation` | strict records, instruction digest, PTY/stdio identity와 new-process-only 계약이 확인되고 exit 0이다. |
| CMD-6 | `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_global_leader -k test_lock_fd_inheritance -k test_reviewer_standby -k test_takeover` | leader race/FD lifetime, reviewer·standby deny와 takeover fail-closed가 확인되고 exit 0이다. |
| CMD-7 | `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_live_verifier -k test_account_status_precedence -k test_identity_canonicalization -k test_identity_enrollment -k test_verifier_redaction` | verifier, status precedence, canonical identity, synthetic enrollment와 redaction이 확인되고 exit 0이다. |
| CMD-8 | `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_failure_status -k test_registry_contract_mixed_deployment -k test_skill_policy -k test_full_auto_compatibility -k test_documentation_contract` | failure classifier, mixed deployment, Skill policy, preservation과 문서 계약이 확인되고 exit 0이다. |
| CMD-10 | `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_chezmoi_fixture_render` | temp synthetic source가 예상 target bytes/mode/symlink로 render되고 실제 home/apply 접근 없이 exit 0이다. |
| CMD-15 | `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_sensitive_data_hygiene -k test_no_auth_copy_or_symlink -k test_legacy_home_preservation -k test_no_unrestricted_path` | 공개 surface의 민감정보가 0건이고 auth/home/legacy mutation 및 unrestricted grant sentinel이 0회이며 exit 0이다. |
| CMD-16 | `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_portable_cli_contract` | portable CLI range와 option 경계 및 `blocked_cli_contract` case가 통과하고 exit 0이다. |
| CMD-17 | `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_claude_config_home_modes -k test_claude_default_env_unset -k test_claude_explicit_env -k test_verifier_provider_environments` | 다섯 home-mode surface와 verifier/provider exact environment가 확인되고 exit 0이다. |
| CMD-18 | `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_claude_settings_composition -k test_claude_settings_digest -k test_effective_setting_sources -k test_claude_plugin_policy -k test_claude_untrusted_settings_prescan` | composed settings digest, trusted sources/plugin 및 untrusted settings 차단이 확인되고 exit 0이다. |
| CMD-19 | `AI_SESSION_E2E_NETWORK=deny /opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_workmux_event_transitions -k test_permission_request_waiting -k test_no_stale_done_during_active_work -k test_no_running_process_mutation` | fake workmux exact transition, stale `done` 부재와 실제 process mutation 0건이 확인되고 exit 0이다. |
| CMD-20 | `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_account_root_permission_separation -k test_exact_git_common_dir_permission -k test_no_opposite_root_grant -k test_stale_pwd_rejected` | write root가 worktree와 exact common-dir로 제한되고 stale PWD/opposite-root grant가 차단되어 exit 0이다. |
| CMD-21 | `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_cross_profile_move_shutdown -k test_git_worktree_move_and_verify -k test_stale_binding_block -k test_binding_generation_rebind -k test_move_handoff -k test_separate_clone_alternative` | temp move의 shutdown, Git 검증, atomic generation, handoff와 separate-clone 대안이 확인되고 exit 0이다. |
| CMD-22 | `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_legacy_alias_home_protection -k test_codex_default_existing_home -k test_legacy_records_non_selectable -k test_old_alias_binding_blocked -k test_migration_generation_gate -k test_legacy_zero_reference_removal` | active topology, byte-preserved legacy evidence와 separate-generation removal gate가 확인되고 exit 0이다. |
| CMD-23 | `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_workmux_status_surface -k test_workmux_dashboard_surface -k test_workmux_sidebar_surface -k test_workmux_wait_surface` | fake status/dashboard/sidebar/wait가 동일 turn-state를 보고하고 exit 0이다. |
| CMD-12 | `git diff --exit-code fcfb47ee2a0514518d150554ee491aae87d26d52 -- dot_claude/skills/create-worktree dot_config/workmux dot_tmux.conf.tmpl dot_zshrc.tmpl && /opt/homebrew/bin/python3 -m unittest -v tests/test_ai_session.py && /opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_changed_path_allowlist -k test_no_account_fallback -k test_path_selection_regression` | preserved paths의 diff가 0이고 replaced deployed-registry expectation을 포함한 direct-caller 및 changed-path/selection regression이 통과해 exit 0이다. |
| CMD-13 | `/opt/homebrew/bin/python3 -m unittest -v tests/test_ai_session.py tests/test_orchestrator_profiles.py` | 전체 portable selector/role suite와 replaced deployed-registry expectation을 포함한 direct compatibility가 통과하고 exit 0이다. |
| CMD-9 | `AI_SESSION_CLI_PROBE_MODE=help-only /opt/homebrew/bin/python3 tests/check_installed_orchestrator_cli_contract.py` | installed Codex/Claude version/help가 frozen evidence와 일치하고 auth/network/model probe 없이 exit 0이다. |
| CMD-11 | `AI_SESSION_E2E_NETWORK=deny /opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_high_risk_e2e` | network-denied high-risk matrix와 모든 no-live-action sentinel이 통과하고 exit 0이다. |
| CMD-14 | `/opt/homebrew/bin/python3 -m unittest discover -s tests -p 'test_*.py' -v && git diff --check` | repository unittest discovery와 최종 whitespace check가 모두 exit 0이다. |

## Rollout and rollback

1. `T1` 전에 project root에서 아래 command block을 실행해 정확한 task-owned path set의 pre-task tracked diff와 pre-existing untracked bytes를 `/private/tmp` snapshot에 보존하고 printed `QG_ROLLBACK_ROOT`를 implementation record에 남긴다. recovery source는 base revision 자체가 아니라 base revision에 `pre-task.patch`와 `pre-task-untracked.tar`를 다시 적용한 pre-task workspace bytes다. 그 뒤 tests/fixtures와 strict manifests/settings/instructions를 먼저 추가하고 selector·verifier·dispatcher, symlink entrypoint와 운영 문서를 연결한다.

```sh
QG_PROJECT_ROOT=/Users/lee-kyu-hwan/code/dotfiles__worktrees/103-chore-orchestrator-permission-profiles
QG_BASE=fcfb47ee2a0514518d150554ee491aae87d26d52
QG_ROLLBACK_ROOT="$(mktemp -d /private/tmp/issue-103-rollback.XXXXXX)"
QG_PATHS=(
  dot_config/ai-session/accounts.toml dot_config/ai-session/roles.toml dot_config/ai-session/skill-policies.toml
  dot_claude/settings.json
  dot_config/ai-session/claude/general.settings.json dot_config/ai-session/claude/orchestrator.settings.json
  dot_config/ai-session/claude/feature-orchestrator.settings.json dot_config/ai-session/claude/global-orchestrator.settings.json
  dot_config/ai-session/instructions/codex-general.md dot_config/ai-session/instructions/codex-orchestrator.md
  dot_config/ai-session/instructions/codex-feature-orchestrator.md dot_config/ai-session/instructions/codex-global-orchestrator.md
  dot_config/ai-session/instructions/claude-general.md dot_config/ai-session/instructions/claude-orchestrator.md
  dot_config/ai-session/instructions/claude-feature-orchestrator.md dot_config/ai-session/instructions/claude-global-orchestrator.md
  dot_local/bin/executable_ai-role-session dot_local/bin/symlink_ai-codex dot_local/bin/symlink_ai-codex-orchestrator
  dot_local/bin/symlink_ai-codex-feature-orchestrator dot_local/bin/symlink_ai-codex-global-orchestrator
  dot_local/bin/symlink_ai-claude dot_local/bin/symlink_ai-claude-orchestrator
  dot_local/bin/symlink_ai-claude-feature-orchestrator dot_local/bin/symlink_ai-claude-global-orchestrator
  dot_local/bin/executable_ai-session dot_local/libexec/executable_ai-session-verify-codex
  dot_local/libexec/executable_ai-session-verify-claude dot_local/libexec/executable_ai-session-enroll-identity
  dot_local/libexec/ai_session_identity.py tests/test_ai_session.py tests/test_orchestrator_profiles.py
  tests/check_installed_orchestrator_cli_contract.py tests/fixtures/orchestrator-profiles
  docs/orchestrator-permission-profiles.md
)
cd "$QG_PROJECT_ROOT"
git diff --binary --full-index "$QG_BASE" -- "${QG_PATHS[@]}" > "$QG_ROLLBACK_ROOT/pre-task.patch"
git ls-files --others --exclude-standard -- "${QG_PATHS[@]}" > "$QG_ROLLBACK_ROOT/pre-task-untracked.list"
tar -cpf "$QG_ROLLBACK_ROOT/pre-task-untracked.tar" -T "$QG_ROLLBACK_ROOT/pre-task-untracked.list"
git ls-tree -r --name-only "$QG_BASE" -- "${QG_PATHS[@]}" > "$QG_ROLLBACK_ROOT/base-tracked.list"
/opt/homebrew/bin/python3 -c 'import sys; print(sys.argv[1])' "$QG_ROLLBACK_ROOT"
```
2. 자동 workflow는 repository source만 검증하며 `chezmoi apply`, deploy, login/auth/status/usage, model probe, identity enrollment 또는 실제 pane/process 조작을 실행하지 않는다. `CMD-10`은 temp synthetic render만 허용한다.
3. compatibility 기간에는 `T11`에서 교체한 deployed-registry selection expectation 외 v1 direct `ai-session` behavior와 양방향 mixed-deployment가 유지되고, deployed `claude-dotfiles`와 `codex-dotfiles` record bytes는 opaque legacy evidence로 byte-preserved, non-selectable, non-mappable 상태를 유지한다. 현재 실행 중인 pane/process는 rebind·restart하지 않으며 새 정책은 새 process에서만 관측한다.
4. monitoring evidence는 strict one-line `account_binding`, `role_startup`, `launch_failure`의 schema/generation/status, fake workmux turn-state, verifier six-field result, leader conflict와 sentinel count다. 공개 evidence에 config-home/credential/raw identity/provider output이 나타나거나 fallback/retry, stale `done`, unexpected provider invocation, preserved-byte diff가 나타나면 rollout을 중단한다.
5. rollback trigger는 어느 verification command의 nonzero exit, changed-path allowlist 이탈, mixed/direct compatibility 실패, legacy byte drift, permission grant 확대, stale binding/generation, 실제 resource 접근 sentinel 또는 public disclosure다. 이때 새 process 시작을 중지하고 running pane/process에는 손대지 않은 채, item 1에서 기록한 동일 shell의 `QG_PROJECT_ROOT`, `QG_BASE`, `QG_ROLLBACK_ROOT`, `QG_PATHS`를 사용해 아래 exact commands로 task-owned paths만 pre-task bytes로 복구한다. base bytes만 복원하는 것이 아니라 saved tracked diff와 saved pre-existing untracked archive까지 재적용한다.

```sh
cd "$QG_PROJECT_ROOT"
git restore --source="$QG_BASE" --worktree --pathspec-from-file="$QG_ROLLBACK_ROOT/base-tracked.list"
git clean -fd -- "${QG_PATHS[@]}"
[ ! -s "$QG_ROLLBACK_ROOT/pre-task.patch" ] || git apply "$QG_ROLLBACK_ROOT/pre-task.patch"
tar -xpf "$QG_ROLLBACK_ROOT/pre-task-untracked.tar" -C "$QG_PROJECT_ROOT"
git diff --check
```

초기 dirty path로 기록된 `.claude/profile-migration/`와 `docs/development/2026-09-15-103-orchestrator-permission-profiles/`는 `QG_PATHS`, snapshot manifest와 모든 rollback pathspec에 포함하지 않으며 어떤 rollback에서도 revert, delete 또는 clean하지 않는다. `docs/development/2026-09-15-103-orchestrator-permission-profiles-2/plan.md`와 `spec.md`도 implementation rollback path가 아니다. credential/account home과 legacy home은 rollback 대상이 아니며 읽거나 copy·rename·delete하지 않는다. 복구 후 read-only `git diff --name-only "$QG_BASE" -- "${QG_PATHS[@]}"`와 snapshot manifest를 비교해 pre-task path state를 확인한다.
6. legacy alias/home transition은 이 implementation rollout과 분리된 나중 migration generation에서만 한다. 먼저 `CMD-22`로 alias별 zero-process/zero-binding reference와 shutdown/handoff 및 필요한 synthetic official admission proof를 확인하고, zero-reference evidence가 없으면 제거를 거부한다. evidence가 완전할 때만 atomic new binding을 publish하며 실패하면 old registry bytes/generation을 유지하고 새 process를 시작하지 않는다.

## Acceptance-criteria traceability

| Criterion | Task | Verification command | Expected outcome |
|---|---|---|---|
| AC-1 | T15 | CMD-12 | Preserved target diff가 0이고 changed-path allowlist와 selection priority/no-fallback regression이 통과한다. |
| AC-2 | T1 | CMD-1 | 여덟 symlink가 단일 dispatcher와 정확한 provider/role을 가리킨다. |
| AC-3 | T1 | CMD-1 | schema/startup/fixture에 정확히 네 role만 존재하고 두 orchestrator role이 구분된다. |
| AC-4 | T15 | CMD-1 | 모든 산출물 생성 뒤 file ownership이 file map과 일치하고 wrapper의 selector/verifier parser 중복이 0건이다. |
| AC-5 | T3 | CMD-2 | 네 Codex role의 model/effort/permission capture가 정확하고 fallback이 0회다. |
| AC-6 | T4 | CMD-3 | 네 Claude role과 Fable elevation 사유가 정확하고 fallback이 0회다. |
| AC-7 | T7 | CMD-7 CMD-8 | default route와 status precedence가 고정되고 모든 automatic fallback이 거부된다. |
| AC-8 | T13 | CMD-9 CMD-16 | Installed help-only contract와 portable version/option boundary가 모두 통과한다. |
| AC-9 | T5 | CMD-5 | Resume 계열 입력은 pre-exec 거부되고 현재 pane/process/session bytes는 변하지 않는다. |
| AC-10 | T2 | CMD-4 | Filesystem real path의 unique longest ancestor만 선택되고 모호한 case는 pre-exec 차단된다. |
| AC-11 | T2 | CMD-4 | 모든 Codex role은 `codex-default`와 기존 `~/.codex`만 자동 선택하며 추가 home 동작은 0회다. |
| AC-12 | T2 | CMD-4 | 두 Claude root가 각 profile로 선택되고 밖은 차단되며 selectable alias 규칙이 통과한다. |
| AC-13 | T8 | CMD-17 | 다섯 surface의 provider-default home assignment가 0건이고 explicit profile2 path만 정확히 전달된다. |
| AC-14 | T2 | CMD-4 | Selection priority와 directory-only scope가 통과하고 remote/organization 재선택은 0회다. |
| AC-15 | T8 | CMD-4 | Exact 19-key scrub 뒤 선택된 home만 private child environment에 조건부 재도입된다. |
| AC-16 | T3 | CMD-2 | Codex role별 model/effort/approval/sandbox/write-root가 정확하고 unrestricted grant가 0건이다. |
| AC-17 | T3 | CMD-2 CMD-11 | Hostile Codex config와 override tail이 provider 전 차단되고 benign chain만 허용된다. |
| AC-18 | T12 | CMD-3 CMD-18 CMD-19 | Trusted composed settings, 일곱 event source와 exact workmux transitions가 통과하고 실제 process mutation은 0회다. |
| AC-19 | T4 | CMD-18 | Effective sources는 exact composed digest와 reviewed local plugin만 신뢰한다. |
| AC-20 | T5 | CMD-5 | Instruction bytes/version/hash와 단일 additive interface가 일치하고 invalid source는 pre-exec 실패한다. |
| AC-21 | T6 | CMD-4 CMD-5 | Skill/leader capability가 포함된 최종 policy bytes가 account 변화에도 동일하고 task/direct-parent matrix가 통과한다. |
| AC-22 | T15 | CMD-5 CMD-15 | 최종 public records가 stable one-line JSON이고 sensitive field와 marker가 0건임을 full hygiene gate가 판정한다. |
| AC-23 | T5 | CMD-5 | PTY/stdio FD identity가 dispatcher 전후 동일하고 provider가 stderr를 직접 소유한다. |
| AC-24 | T6 | CMD-6 | Same-scope active 하나만 lock을 보유하며 isolation과 post-exit reacquire가 통과한다. |
| AC-25 | T6 | CMD-6 | Reviewer/standby mutation capability가 0이고 invalid takeover는 상태를 보존한 채 차단된다. |
| AC-26 | T7 | CMD-7 CMD-17 | Verifier가 exact environment/official command/six-field/redaction을 지키고 provider fallback은 0회다. |
| AC-27 | T7 | CMD-7 | Identity canonicalization과 SHA-256+LF가 재현되고 unstable identity는 fail closed한다. |
| AC-28 | T7 | CMD-7 CMD-15 | Synthetic enrollment의 mode/atomicity/parser가 통과하고 실제 enrollment와 민감 노출은 0회다. |
| AC-29 | T7 | CMD-8 | Failure status/exit precedence가 유일하며 retry/reclassification/fallback은 0회다. |
| AC-30 | T15 | CMD-15 | 공개 surface의 real config-home·credential·identity/provider output이 0건이고 live sentinel 접근도 0회다. |
| AC-31 | T6 | CMD-6 CMD-8 | Skill/plugin deny-first intersection과 reviewer/standby deny가 통과하고 workmux는 observability-only다. |
| AC-32 | T6 | CMD-8 CMD-12 | Skill policy identity/count와 pre-exec 오류가 판정되고 full-auto artifact가 byte-identical/unreferenced다. |
| AC-33 | T13 | CMD-8 CMD-13 | 명시적으로 교체한 deployed-registry expectation 외 v1 direct compatibility와 양방향 mixed deployment가 통과하고 현재 process 상태가 보존된다. |
| AC-34 | T14 | CMD-8 | 운영 문서가 요구된 모든 heading, recovery 및 exact contract phrase를 포함한다. |
| AC-35 | T15 | CMD-9 CMD-10 CMD-11 CMD-12 CMD-13 CMD-14 CMD-15 CMD-16 CMD-17 CMD-18 CMD-19 CMD-20 CMD-21 CMD-22 | Applicable release/render/E2E/full/hygiene/move/legacy gates가 모두 exit 0이고 production mutation은 0회다. |
| AC-36 | T9 | CMD-20 | Write allow set은 resolved worktree와 exact common-dir 두 path뿐이다. |
| AC-37 | T9 | CMD-20 CMD-21 | External common-dir를 exact 판정하고 cross-root deny는 separate clone+handoff로 fail closed한다. |
| AC-38 | T10 | CMD-20 CMD-21 | `ai-session`이 stale PWD와 shutdown proof 없는 move를 selection/update 전에 차단한다. |
| AC-39 | T10 | CMD-21 | Move는 모든 writer shutdown과 dirty/quality-state handoff를 요구하며 hot swap은 0회다. |
| AC-40 | T10 | CMD-21 | Linked worktree만 move되고 main/submodule은 대안 없이는 거부된다. |
| AC-41 | T10 | CMD-21 | 네 Git post-move 결과와 tracked/untracked state가 보존된다. |
| AC-42 | T10 | CMD-21 | Binding은 atomic positive generation으로 갱신되고 partial/stale case에서 old registry가 보존된다. |
| AC-43 | T10 | CMD-21 CMD-15 | Destination의 새 process만 시작되고 resume/hot-swap/home copy가 0회다. |
| AC-44 | T10 | CMD-21 | 모든 path/watch target이 새 real path로 재계산되고 stale reference는 시작 전에 차단된다. |
| AC-45 | T11 | CMD-22 CMD-15 | Shipped Claude topology가 정확하고 legacy record는 byte-preserved/non-selectable이며 home mutation은 0회다. |
| AC-46 | T11 | CMD-22 | Legacy migration은 separate generation과 zero-reference proof 없이는 거부된다. |
| AC-47 | T12 | CMD-19 | R11.1의 five event kinds/six exact cases가 required state로 매핑되고 SubagentStop/TaskCompleted는 reviewed reference bytes 그대로 유지된다. |
| AC-48 | T12 | CMD-18 CMD-15 | 모든 profile이 digest-verified single settings를 받고 secret/home replication은 0건이다. |
| AC-49 | T4 | CMD-18 CMD-3 | Hooks는 trusted composed document에서만 유입되고 untrusted hooks는 provider 전에 차단된다. |
| AC-50 | T12 | CMD-19 | Active work는 `working`이며 활동 중 stale `done` 보고가 0건이다. |
| AC-51 | T6 | CMD-6 | Status hook은 observability-only이고 dispatch/lease-write grant가 0건이다. |
| AC-52 | T12 | CMD-19 | Synthetic separate home/fake workmux가 transitions를 판정하고 실제 tmux/process mutation은 0건이다. |
| AC-53 | T12 | CMD-23 | Status, dashboard, sidebar, wait가 동일 turn-state를 보고한다. |
| AC-54 | T14 | CMD-8 | 문서가 exact `done` phrase와 status surface 비권한·비완료 의미를 포함한다. |
| AC-55 | T11 | CMD-22 | Selectable Codex는 `codex-default` 하나이고 old alias는 silent mapping 없이 pre-verifier 차단된다. |

<!-- strict-only:start -->

### Threat and trust boundaries

- `CMD-4`, `CMD-17`, `CMD-20`은 untrusted inherited environment, symlink/PWD surface, account-root breadth와 project metadata가 selection·credential·permission boundary를 넓히지 않음을 증명해야 한다. 성공 evidence는 exact scrub, real-path binding, directory-only scope와 worktree+exact-common-dir allow set이다.
- `CMD-2`, `CMD-3`, `CMD-18`은 repository/account/project/local config와 plugin source를 untrusted로 취급하고 exact benign allowlist 밖의 key/hook/plugin을 provider 전에 차단해야 한다. provider invocation sentinel은 0회여야 한다.
- `CMD-5`, `CMD-7`, `CMD-15`은 public stderr/log/artifact/document와 verifier/provider private child environment의 경계를 판정해야 한다. 공개 surface의 config-home, credential, raw identity/digest/provider output은 0건이고 permitted synthetic private-env capture만 exact path를 가진다.
- `CMD-6`은 global active lock capability가 한 provider에만 상속되고 verifier/reviewer/standby에는 lock·dispatch·lease-write capability가 없음을 FD와 sentinel evidence로 증명해야 한다.
- `CMD-21`, `CMD-22`는 current process, old binding, legacy alias/home과 destination process 사이의 generation boundary를 검증해야 한다. shutdown/zero-reference/atomic binding proof가 없으면 새 process 전 `blocked_binding`이어야 한다.

### Authorization and tenant isolation

- 허용 — profile1 real root의 Claude launch: `CMD-4` exact command `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_real_path_account_selection -k test_allowed_scope_kind_contract -k test_role_account_orthogonality -k test_child_environment -k test_exact_credential_scrub -k test_no_account_fallback`; `claude-profile1` 하나만 선택되고 verifier/provider는 provider-default home key 없이 admitted된다.
- 허용 — profile2 real root의 Claude launch: 같은 `CMD-4`; `claude-profile2` 하나만 선택되고 opposite profile/account bytes나 권한은 유입되지 않는다.
- 허용 — `~/code/**` Codex launch: 같은 `CMD-4`; `codex-default`와 `~/.codex`만 선택되고 다른 Codex home ranking/fallback은 0회다.
- 거부 — Claude root 밖, equal-priority/ambiguous/non-normalizable/stale surface 또는 non-directory scope: 같은 `CMD-4`; verifier/provider invocation 0회와 `blocked_contract` 또는 `blocked_binding`이 exact fixture expectation과 일치한다.
- 거부 — opposite account-root grant, wildcard/add-dir 또는 stale inherited PWD: `CMD-20` exact command `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_account_root_permission_separation -k test_exact_git_common_dir_permission -k test_no_opposite_root_grant -k test_stale_pwd_rejected`; grant/update/provider sentinel 0회이며 fail-closed status가 일치한다.
- 거부 — old `claude-dotfiles`/`codex-dotfiles` alias의 explicit 또는 stored binding: `CMD-22` exact command `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_legacy_alias_home_protection -k test_codex_default_existing_home -k test_legacy_records_non_selectable -k test_old_alias_binding_blocked -k test_migration_generation_gate -k test_legacy_zero_reference_removal`; provider/verifier 전 `blocked_binding`, silent alias mapping 0회, legacy bytes 불변이다.
- 거부 — reviewer/standby dispatch·lease-write·lock 및 second same-scope global active: `CMD-6` exact command `/opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_global_leader -k test_lock_fd_inheritance -k test_reviewer_standby -k test_takeover`; capability mutation 0회이며 각각 policy denial 또는 `blocked_leader_conflict`다.

### Migration, compatibility, and rollback

- Review 전 `CMD-8`, `CMD-13`으로 old-binary/new-registry와 new-binary/old-registry의 `blocked_contract`, 교체 대상 한 test 외 기존 v1 JSON/exit behavior 및 current-process byte preservation을 증명한다.
- Source rollout과 legacy migration을 분리한다. 구현 generation에서는 active 세 alias만 추가하고 두 legacy record bytes를 그대로 둔다. `CMD-22`의 zero-process/zero-binding, shutdown/handoff, required synthetic admission proof가 모두 통과한 나중 generation만 atomic binding transition 후보가 된다.
- `CMD-12`의 preserved diff, `CMD-15`의 no-copy/no-symlink/no-home-mutation, `CMD-21`의 old-registry preservation 중 하나라도 실패하면 migration과 새 process start를 금지한다.
- Rollback은 running pane/process를 재시작·rebind하지 않고 reviewed source set을 함께 이전 source bytes로 되돌린다. binding publish 실패는 old bytes와 generation을 유지하며 credential/account home/legacy home은 rollback 중에도 읽거나 이동·복사·삭제하지 않는다.

### Failure recovery and observability

- `CMD-8`은 exit 2/3/4, unique status precedence, provider model-rejection passthrough와 retry/reclassification/fallback 0회를 evidence로 남긴다. 예상 status가 다르면 provider를 재시도하지 않고 rollout을 중단한다.
- `CMD-5`와 `CMD-15`은 각 failure가 exact one-line `launch_failure` JSON 한 줄만 공개하고 stable fields/type/generation을 가지며 sensitive field가 0건임을 판정한다.
- `CMD-6`은 second leader conflict와 invalid takeover 후 기존 process/proof/generation 불변 및 post-exit reacquire를 증명한다. lock/lease 상태가 모호하면 새 leader를 시작하지 않는다.
- `CMD-19`와 `CMD-23`은 fake workmux의 exact transition과 네 surface의 동일 turn-state를 evidence로 남긴다. stale `done` 또는 surface divergence는 rollback trigger이며 authority/issue completion으로 해석하지 않는다.

### High-risk end-to-end verification

Review 전 exact command `AI_SESSION_E2E_NETWORK=deny /opt/homebrew/bin/python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_high_risk_e2e` (`CMD-11`)가 exit 0이어야 한다. Evidence에는 여덟 launcher의 path/account×role capture, hostile config의 pre-exec denial, exact scrubbed environment, TTY/FD preservation, single global leader, verifier isolation, no-fallback 결과와 provider/auth/login/logout/status/usage/network/model/enrollment/account-home/current-process/production sentinel 접근 0회가 모두 포함되어야 한다.

### No production mutation confirmation

자동 workflow의 production mutation은 0건이다. `CMD-10`은 temp synthetic render만 수행하고 `chezmoi apply`를 실행하지 않으며, `CMD-7`, `CMD-11`, `CMD-15`, `CMD-19`, `CMD-21`, `CMD-22`의 evidence는 실제 credential/account home, login/logout/auth/status/usage, network/model probe, enrollment, pane/tmux/process, legacy home에 대한 read/write/start/signal/restart/rebind/copy/symlink/rename/delete가 모두 0회임을 보여야 한다. Commit, push, PR, merge와 issue #94/#95 mutation도 이 Plan의 실행 범위에 없다.

<!-- strict-only:end -->
