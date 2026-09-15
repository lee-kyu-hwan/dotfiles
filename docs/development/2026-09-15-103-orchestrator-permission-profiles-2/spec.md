# Quality Goal Specification

- Task ID: 103-orchestrator-permission-profiles-2
- Mode: strict
- Status: SPEC_REVIEW
- Created: 2026-09-15
- Updated: 2026-09-15
- Source goal: GitHub issue #103의 Codex·Claude 계층별 오케스트레이터 모델·권한 profile을 normalized real worktree path 기반 account 선택 정책으로 재설계한다.

## Problem and context

현재 저장소는 #111에서 `dot_local/bin/executable_ai-session`의 `select|launch`, 비밀이 아닌 account registry, 독립 provider config home, verifier, credential 환경 정리와 consumer account 자동 전환 금지를 마련했지만 실제 provider verifier와 역할별 launcher는 #103 후속으로 남아 있다. frozen predecessor Spec은 네 logical role, 여덟 launcher, role/account 직교 결합, 모델·권한·instruction·Skill 정책, verifier/identity, leader lease, strict public records, stdio/TTY, CLI compatibility와 Claude settings composition의 상세 계약을 정의했다. 그러나 account를 normalized Git remote/common-dir repository identity 중심으로 선택한 전제가 업데이트된 #103/#111의 authoritative input과 충돌하여 이전 execution은 `NEEDS_REDESIGN`으로 종료되었다.

이번 redesign의 선택 축은 normalized real worktree path뿐이다. Codex는 `~/code/**` 전부에서 기존 `codex-default` 하나를 자동 선택한다. 초기 정책의 Claude는 `~/code/profile1/**`에서 provider-default/unset mode의 `claude-profile1`, `~/code/profile2/**`에서 exact separated home을 export하는 `claude-profile2`를 선택하고 두 root 밖에서는 조건 없이 `blocked_contract`로 fail closed한다. 범위 확장은 launcher가 판단하는 runtime 예외가 아니라, launch 전에 새 mapping을 선행 배포하는 별도 reviewed Spec과 registry source 개정이다. GitHub `owner/repository`, remote와 organization은 account 선택 신호가 아니며, remote/common-dir는 오직 Git 무결성 검증에만 쓰인다. 따라서 같은 remote의 두 worktree도 서로 다른 real account root에 있으면 서로 다른 Claude profile을 선택한다.

account root는 선택 경계이지 permission 경계가 아니다. authoritative input에 기록된 Git 2.55.0 임시 probe는 dirty tracked/untracked 상태의 linked worktree move가 보존되지만 common-dir가 이전 root 밖에 남을 수 있고, 이동 전 cwd를 잡은 process는 새 `os.getcwd()`와 오래된 inherited `PWD`를 동시에 가질 수 있음을 보였다. launcher는 resolved worktree와 exact Git common-dir만 필요한 write permission으로 허용하고, cross-profile move는 writer 정지, Git 검증, atomic binding generation 갱신, 새 process handoff와 모든 경로 재계산을 요구해야 한다.

`docs/development/2026-09-15-103-orchestrator-permission-profiles/installed-cli-contract-evidence.md`의 help-only 증거는 계속 유효하다. Codex는 0.154.0, Claude Code는 2.1.272이며 Claude는 단일 `--settings`, repeatable local `--plugin-dir`, `--append-system-prompt`를 광고하지만 `--append-system-prompt-file`은 광고하지 않는다. offline help는 model availability나 usage admission을 증명하지 않는다. 특히 공식 Claude help에 usage/quota contract가 없으므로 로그인 fixture도 별도 official adapter 전까지 `usage_unknown`으로 차단한다. 실제 auth/status/login/logout, network/model probe, account-home 또는 credential read는 이 작업의 증거가 아니다.

현재 실행 중인 `claude-dotfiles` alias와 `~/.local/share/ai-account-profiles/claude/dotfiles` home은 legacy runtime state다. 새 registry target은 logical alias `claude-profile1`, `claude-profile2`와 neutral home `~/.local/share/ai-account-profiles/claude/profile2`를 사용하지만, legacy process/home은 이 구현에서 hot rename·rebind하지 않는다. 전환은 구현 검증 후 별도 migration generation에서 writer 정지, handoff, official login/identity admission 검증과 새 binding generation으로 수행한다.

## Goals

- normalized real worktree path에서 account를 한 번 결정하고 process 종료까지 고정하는 단일 fail-closed selector를 제공한다.
- Codex 전 role을 `codex-default`에 결합하고 Claude를 `claude-profile1|claude-profile2`의 정확한 path/home-mode 정책에 결합하되 role policy는 account와 직교하게 유지한다.
- 네 role과 여덟 launcher의 pinned model, effort, 최소 권한, instruction, Skill/plugin, leader/lease, binding과 public record 계약을 predecessor 수준으로 유지한다.
- account 선택 root와 filesystem permission boundary를 분리하고 resolved worktree 및 exact common-dir 밖의 write grant를 금지한다.
- cross-profile move를 writer shutdown, Git 이동·검증, atomic registry generation, 새 process handoff와 runtime target 재계산을 포함한 명시적 rebind 절차로 만든다.
- Claude home 격리에도 common hooks, reviewed permissions/plugins와 workmux 관측성을 credential 복제 없이 동일하게 복원한다.
- synthetic fixture와 help-only release gate로 path selection, env, settings, verifier, stdio/TTY, leader, move, legacy 보호를 실제 account/network/process mutation 없이 검증한다.

## Non-goals

- #94의 영구 registry 구현이나 #95의 worktree 생성·재사용 자동화를 수행하지 않는다. 두 issue의 registry contract는 소비만 한다.
- repository owner, Git remote, organization 또는 Git identity를 account 선택 축으로 다시 도입하지 않는다.
- 실행 중 process의 account hot swap, `CLAUDE_CONFIG_DIR` 변경, transparent cross-profile `/resume`, transcript/plugin/credential state 이관을 제공하지 않는다.
- 실제 login/logout/auth/status/usage, token refresh, identity enrollment, network/model probe, credential·Keychain·account-home read를 수행하지 않는다.
- authentication file, credential directory, account home, transcript 또는 plugin state를 copy, sync, snapshot, rename 또는 symlink하지 않는다.
- main worktree나 submodule을 포함한 linked worktree를 `git worktree move`로 자동 이동하지 않는다. 별도 clone+handoff 또는 별도 reviewed repair 절차가 필요하다.
- 개인 Mac에 unrestricted, `danger-full-access` 또는 `bypassPermissions` launcher를 제공하지 않는다.
- `chezmoi apply`, current tmux pane/session/process mutation, deletion, commit, push, PR, merge 또는 deploy를 수행하지 않는다.
- #110의 전체 Skill/Plugin inventory와 #98/#99의 multi-host lease 발급·갱신 저장소를 구현하지 않는다.

## Requirements

### 범위, 역할과 파일 책임

- **R1.1** 변경 범위는 role/account launcher, account registry schema와 path binding, role/settings/instruction/Skill policy, provider verifier와 shared identity canonicalizer/enrollment helper, deterministic tests/fixtures 및 운영 문서로 한정한다. `dot_claude/skills/create-worktree/**`, `dot_config/workmux/**`, `dot_tmux.conf.tmpl`, `dot_zshrc.tmpl`은 base revision 대비 byte-for-byte 보존하고 #111의 explicit→stored binding→longest directory→provider default 우선순위, 동순위 충돌과 no-fallback 계약은 path axis로 바꾸어 회귀 없이 유지한다.
- **R1.2** 사용자 진입점은 `ai-codex`, `ai-codex-orchestrator`, `ai-codex-feature-orchestrator`, `ai-codex-global-orchestrator`, `ai-claude`, `ai-claude-orchestrator`, `ai-claude-feature-orchestrator`, `ai-claude-global-orchestrator` 여덟 개이며 모두 chezmoi source에서 단일 `dot_local/bin/executable_ai-role-session` dispatcher를 가리키고 argv[0]만으로 provider와 role을 결정한다.
- **R1.3** logical role은 `general`, `orchestrator`, `feature-orchestrator`, `global-orchestrator` 네 값만 허용한다. `orchestrator`는 tmux workgroup 역할, `feature-orchestrator`는 quality-goal feature 역할로 서로 다르게 직렬화한다.
- **R1.4** `accounts.toml`은 path account mapping·allowed scopes·home mode·binding generation, `roles.toml`은 CLI range와 role policy, `skill-policies.toml`은 Skill/plugin policy, `dot_claude/settings.json`과 per-role Claude JSON은 common/composed settings, instruction files은 reviewed additive bytes, `ai-role-session`은 role preflight/argv, `ai-session`은 registry parse·path selection·authorization·verifier classification·child env·public records, libexec은 provider verifier와 shared identity contract, tests/fixtures는 portable evidence, `docs/orchestrator-permission-profiles.md`는 운영/migration file map을 각각 단일 책임으로 소유한다.

### 모델, provider 경로와 CLI 호환성

- **R2.1** Codex role matrix는 general=`gpt-5.6-sol/medium`, orchestrator=`gpt-5.6-sol/medium`, feature-orchestrator=`gpt-5.6-sol/medium`, global-orchestrator=`gpt-6-astra/high`로 고정한다. model 문자열은 pinned policy identifier이며 provider 거부는 해당 nonzero exit로 끝나고 model/provider/account fallback을 하지 않는다.
- **R2.2** Claude role matrix는 general=`opus[1m]/high`, orchestrator=`opus[1m]/high`, feature-orchestrator=`opus[1m]/high`, global-orchestrator=`claude-fable-5-1/medium`으로 고정한다. global에 명시적 high effort elevation을 허용하되 Fable model pin과 사유를 startup record에 남기며 거부 시 fallback하지 않는다.
- **R2.3** session 기본 provider는 Codex, feature 기본 provider는 Claude다. Claude의 `not_logged_in`은 `usage_unknown`보다 먼저 분류하고 로그인 fixture도 reviewed official usage adapter가 없으면 `usage_unknown`으로 차단한다. Codex feature 대체는 새 process에서 명시적 acknowledgement와 유효 binding을 제공한 경우만 허용하며 자동 대체가 아니다.
- **R2.4** runtime range는 Codex `>=0.154.0,<0.155.0`, Claude Code `>=2.1.269,<2.2.0`이고 현재 Mac의 0.154.0/2.1.272 및 frozen help transcript는 release evidence다. Claude required surface는 `--append-system-prompt`, single `--settings`, repeatable local `--plugin-dir`이며 `--append-system-prompt-file`은 요구하지 않고 `--plugin-url`은 금지한다. range/required option mismatch는 provider 전에 `blocked_cli_contract`/exit 4다.
- **R2.5** 새 role/account/settings는 reviewed source가 별도 explicit deployment된 뒤 시작한 새 process에만 적용한다. wrapper는 resume/continue/session-ID 입력을 거부하고 running pane/process/session, 승인 digest, inherited account binding과 settings를 소급 변경하지 않는다.

### normalized real path account 선택

- **R3.1** account 선택의 directory 입력은 launch 시 `os.getcwd()`와 filesystem resolution으로 얻은 normalized absolute real worktree path이며 symlink surface path와 inherited `PWD`는 후보 계산에 사용하지 않는다. directory mappings 중 정확히 하나의 longest real ancestor를 선택하고 동일 길이·동일 우선순위의 서로 다른 후보, normalization 실패 또는 symlink/real-path 모순은 provider/verifier 전에 fail closed한다.
- **R3.2** Codex는 normalized real path가 `~/code/**` 아래이면 모든 role과 repository에서 selectable account `codex-default` 하나만 자동 선택한다. `codex-default`는 새 account나 새 home이 아니라 기존 Codex account의 logical alias이고, 그 `config_home`은 이미 사용 중인 provider-default Codex home `~/.codex`로 고정한다. 이 work는 Codex home을 생성·이동하거나 login하지 않는다. registry 구조는 이후 추가 Codex account 선언을 허용하되 이 work의 selectable Codex account는 정확히 하나이며, 추가 account는 automatic default/directory mapping/ranking/fallback/rotation 후보가 될 수 없고 `~/code/**` 밖 provider-default 사용도 reviewed policy 없이는 허용하지 않는다.
- **R3.3** 초기 정책의 Claude는 real path `~/code/profile1/**`에서 정확히 `claude-profile1`, `~/code/profile2/**`에서 정확히 `claude-profile2`를 선택하며 두 root 밖에서는 조건 없이 `blocked_contract`로 fail closed한다. 향후 범위 확장은 launch 전에 새 mapping을 선행 배포하는 별도 reviewed Spec과 registry source 개정으로만 한다. 이 work가 도입하는 selectable account alias 중 Claude alias는 정확히 `claude-profile1`, `claude-profile2`다. reserved set `default|dotfiles|work|personal`과의 비교는 selectable alias 전체 문자열에 대한 exact full-alias match이고 substring·component match가 아니므로 `codex-default`는 허용한다. R10.1과 R3.6의 non-selectable legacy record는 selectable alias가 아니므로 이 규칙의 대상이 아니다.
- **R3.4** `claude-profile1`은 `config_home_mode="provider_default"`이고 config-home path field가 없다. chezmoi source, rendered target, launcher argv, verifier environment와 provider environment의 다섯 surface 모두에 `claude-profile1`용 `CLAUDE_CONFIG_DIR` assignment가 0건이어야 하며 provider-default home의 literal path를 exported value로 내보내지 않는다. `claude-profile2`는 `config_home_mode="explicit"`이고 exact absolute non-symlink `~/.local/share/ai-account-profiles/claude/profile2`만 reviewed registry source, rendered configuration target과 scrub 후 verifier/provider private child environment에 둔다. invalid mode/path 조합은 fallback 없이 `blocked_contract`다.
- **R3.5** 선택 priority는 explicit option→stored task/session binding→longest account workspace directory mapping→provider default이며 provider-default 단계는 최초 Codex에만 허용한다. path-based active account schema에서 `allowed_scopes`의 유일한 admissible kind는 `directory`이고 그 value는 normalized absolute real directory다. selectable account에 `repository` 또는 `organization` kind가 하나라도 있거나 다른 kind가 있으면 registry 전체를 provider/verifier 전에 `blocked_contract`로 거부하며 보존하거나 무시하지 않는다. R10.1과 R3.6의 byte-preserved legacy record bytes는 active account schema 밖의 opaque migration evidence라 `allowed_scopes`로 parse·평가되지 않고 mapping·explicit·stored·default 후보가 될 수 없다. explicit/stored profile도 current real directory의 directory-only `allowed_scopes`를 우회할 수 없고 mismatch는 `blocked_binding`과 rebind 절차를 요구한다. GitHub `owner/repository`, remote와 organization은 account 선택 또는 admission 신호가 아니며 Git remote/common-dir는 Git integrity 검증에만 쓴다. 같은 remote의 서로 다른 account root worktree는 서로 다른 Claude profile을 선택한다. account는 provider process 시작 때 한 번 bind되고 `cd`, usage 또는 remote 변경으로 재선택되지 않으며 limit은 `blocked_usage`로 session을 종료하고 consumer account 자동 ranking/fallback/rotation은 없다.
- **R3.6** shipped registry는 deployed `[accounts.codex-dotfiles]` record의 원래 bytes를 R10.1과 같은 opaque, non-mappable, non-selectable legacy record로 보존한다. 이 record가 가리키는 별도 Codex home은 읽거나 이동·복제·login하지 않고 active `accounts`, `workspace_directory_mappings`, explicit/stored/default selection과 verifier 후보에 넣지 않는다. old alias `codex-dotfiles`를 참조하는 stored binding은 `codex-default`로 암묵 치환하지 않고 provider/verifier 전에 `blocked_binding`으로 닫아 explicit rebind를 요구한다. legacy record 제거는 R10.2의 별도 migration generation과 zero-reference precondition을 만족한 뒤에만 가능하다.

### 실제 권한, environment, settings와 instruction

- **R4.1** Codex는 개인 Mac에서 legacy sandbox chain 하나만 사용한다. general은 orchestration capability 없는 `workspace-write/on-request`, orchestrator와 feature-orchestrator는 resolved worktree 하나의 `workspace-write/never`, global active는 검증된 control/worktree root의 `workspace-write/never`, global reviewer/standby는 `read-only/never`이며 model, effort, approval, sandbox와 instruction을 final CLI로 강제한다.
- **R4.2** verifier, admitted phase와 provider child 환경을 만들 때 부모에서 먼저 제거하는 exact scrub set은 `CODEX_HOME`, `CLAUDE_CONFIG_DIR`, `CODEX_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, `CLAUDE_CODE_OAUTH_TOKEN`, `CLAUDE_CODE_USE_BEDROCK`, `CLAUDE_CODE_USE_VERTEX`, `CLAUDE_CODE_USE_FOUNDRY`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `GOOGLE_APPLICATION_CREDENTIALS`, `CLOUD_ML_REGION`, `ANTHROPIC_VERTEX_PROJECT_ID`, `ANTHROPIC_FOUNDRY_RESOURCE`, `ANTHROPIC_FOUNDRY_API_KEY`, `AI_COST_LIMIT_USD`다. 그 뒤 선택된 Codex home 또는 explicit Claude home만 조건부 재도입하고 `claude-profile1`에는 `CLAUDE_CONFIG_DIR`를 두지 않으며 common settings도 scrub key나 반대 provider home을 재생성하지 않는다.
- **R4.3** launcher는 repository root부터 real cwd까지의 각 Codex `.codex/config.toml`을 strict pre-scan하여 model, effort, approval, sandbox, instruction, profile, feature, MCP/plugin/tool/web/add-dir 계열과 unknown key를 `blocked_policy`로 거부한다. empty/comment-only 또는 manifest의 exact benign allowlist `tui.status_line`, `tui.status_line_use_colors`, `notice.fast_default_opt_out`만 허용하고 policy override tail option도 거부한다.
- **R4.4** Claude는 secret-free chezmoi-managed common layer와 role layer를 구조 병합한 하나의 reviewed, versioned, read-once SHA-256 digest-verified regular non-symlink JSON을 single `--settings`로 전달한다. role의 더 좁은 permission/sandbox/Skill/plugin deny가 우선하고 reviewed local plugin만 repeatable `--plugin-dir`로 허용하며 `--plugin-url`, authentication/account-home replication과 launch-time settings write를 금지한다. common layer는 `Notification|PermissionRequest|PostToolUse|Stop|SubagentStop|TaskCompleted|UserPromptSubmit`와 fake-testable `workmux set-window-status waiting|working|done` hooks를 복원한다.
- **R4.5** digest-verified composed target만 trusted input이고 그 밖의 account-home/project/local Claude settings는 untrusted input이다. untrusted object는 empty 또는 exact benign allowlist `$schema`, `spinnerTipsEnabled`, `theme`만 허용하며 permissions, sandbox, hooks, env, model, plugin, marketplace, MCP, auth helper/login mode 또는 unknown key가 있으면 provider 전에 차단한다. launcher는 `--setting-sources` merge precedence를 신뢰 근거로 삼지 않고 completion은 effective-setting-sources judgement와 실제 pane을 건드리지 않는 fake-`workmux` smoke를 요구한다.
- **R4.6** provider별 additive instruction은 reviewed non-secret UTF-8 regular non-symlink bytes를 한 번 읽어 version/SHA-256/NUL을 검증한다. Codex는 값을 `developer_instructions`로, Claude는 동일 bytes를 single `--append-system-prompt` argument로 전달하며 `--append-system-prompt-file`, `model_instructions_file`, `--agent`, `--system-prompt-file`을 대체 경로로 쓰지 않는다.

### binding, stdio/public record와 leader lease

- **R5.1** role과 account는 직교한다. role 변경은 account candidate/priority/home mode를 바꾸지 않고 account 변경은 model, effort, permission, instruction/settings hash, Skill/plugin policy와 leader capability를 바꾸지 않는다. task/direct-parent는 general=`unbound`, orchestrator=workgroup와 none/active-global parent, feature-orchestrator=quality-goal task와 orchestrator parent, global=scope와 parent none 규칙을 strict 검증한다.
- **R5.2** `ai-session`은 selection/admission 성공 시 exact one-line `account_binding` JSON, admitted phase는 provider exec 직전 exact one-line `role_startup` JSON을 inherited stderr에 직접 쓴다. 두 schema는 predecessor의 public fields, positive `binding_generation`, instruction/settings/Skill/leader facts를 유지하고 config-home path, raw identity, credential과 extra field를 금지한다. failure도 strict one-line `launch_failure` JSON과 stable exit/status를 사용한다.
- **R5.3** dispatcher는 account-independent preflight와 one-shot capability FD, global active의 lock FD를 만든 뒤 stdin/stdout/stderr를 close/dup/pipe하지 않고 `ai-session launch`를 현재 process에서 정확히 한 번 exec한다. verifier subprocess만 captured/redacted I/O와 `close_fds=True`, empty `pass_fds`를 쓰며 admitted phase는 capability를 한 번 소비·close하고 provider는 unchanged terminal stdio와 global active lock FD만 상속한다. byte relay 보장은 pre-exec public record가 동일 inherited stderr에 직접 쓰이는 범위이고 provider exec 뒤 stderr는 provider가 소유한다.
- **R5.4** global active는 strict external lease proof와 normalized scope의 host-local exclusive lock을 검증하고 lock FD를 provider process 종료까지 exec chain으로 상속한다. 같은 scope의 두 번째 active, proof mismatch/expiry는 `blocked_leader_conflict`; 다른 scope는 독립이며 이 launcher는 lease generation을 발급·갱신하지 않는다.
- **R5.5** global reviewer/standby는 read-only이고 lock 획득, generation 증가, lease write와 child dispatch capability가 없다. task owner는 direct parent 하나만 가지며 takeover는 previous owner, process state, generation과 새 external proof가 모두 맞을 때만 인정하고 불충분하면 기존 process/proof를 바꾸지 않고 `blocked_binding`이다.

### verifier, identity, 실패와 민감정보 경계

- **R6.1** provider verifier command는 선택 account의 exact scrubbed home-mode environment에서 separately reviewed official status surface만 사용한다. Codex는 redacted official fields를, Claude는 official auth status만 사용하며 Claude usage를 login으로 추측하거나 TUI/private endpoint로 보완하지 않는다. verifier는 10초 timeout, strict six-field result와 redaction을 지키고 provider child, fallback account, capability/lock FD에 접근하지 않는다.
- **R6.2** identity canonical object는 `schema_version=1`, lowercase provider/auth_kind, case-preserved stable subject ID, organization에만 stable tenant ID를 포함한다. string은 UTF-8 NFC, ASCII edge whitespace trim, control/NUL/empty 거부를 적용하고 sorted compact canonical JSON bytes의 lowercase SHA-256 digest와 single LF file format을 쓴다. email/display name/token/path/usage는 제외하며 stable official field가 없으면 fail closed한다.
- **R6.3** explicit host-local enrollment helper와 verifier는 동일 canonicalizer를 공유한다. helper는 official interactive login 후 명시 호출 때만 owner 0700 directory 안의 owner 0600 regular non-symlink digest file을 fsync와 atomic replace로 쓰고 raw identity/path/digest를 출력하지 않으며 verifier는 파일을 만들거나 갱신하지 않는다. missing/mode/type/owner 오류는 `blocked_verifier`, mismatch는 `identity_drift`, helper 실패는 기존 digest를 보존한다.
- **R6.4** `ai-session`은 contract/selection 오류를 exit 2 `blocked_contract`, verifier payload를 `not_logged_in`→`identity_drift`→`blocked_verifier`→`usage_unknown`→`blocked_usage` 순서의 exit 3 stable status로 분류하는 유일한 component다. role/policy/permission/CLI/leader/binding 오류는 dispatcher exit 4의 stable status이며 provider model rejection은 그대로 반환한다. retry, model/provider/account fallback과 wrapper-side 재분류는 없다.
- **R6.5** real deployed config-home path와 그 path에서 파생한 내부·절대 path는 unintended-disclosure surface인 strict public binding/startup/failure JSON, captured test artifact, log, diagnostic, error output와 운영 문서에 포함하지 않는다. 기능상 필요한 reviewed non-secret registry source, rendered configuration target과 verifier/provider에 넘기는 private child environment에서는 selected explicit config-home path를 허용한다. permitted private-child-environment surface 안에서 exact environment 계약을 판정하기 위해 assertion하는 synthetic fixture path와 그 capture는 real deployed path 또는 그 파생값이 아니므로 disclosure prohibition에서 명시적으로 제외한다. credential, token, raw provider output과 actual identity/digest는 이 carve-out 대상이 아니며 disclosure surface에 포함하지 않는다. 실제 account home, credential store, auth/status/usage/login/logout, network/model probe, enrollment, `chezmoi apply`, current pane/process와 production을 읽거나 변경하지 않고 synthetic homes/binaries/status만 사용한다.

### Skill, compatibility, 배포와 검증

- **R7.1** `skill-policies.toml`은 versioned strict allow/deny와 policy ID를 제공하고 common plugin, reviewed local plugin, role policy와 explicit task overlay의 교집합만 활성화하며 deny가 우선한다. global reviewer/standby에서 agent-team, multi-agent, dispatch와 lease-write Skill/tool/plugin/MCP를 제거하고 workmux hook은 observability-only로 유지한다.
- **R7.2** launcher는 active Skill/plugin policy ID와 count를 startup record에 남기고 missing required, deny activation, catalog warning, version/hash/path mismatch와 network plugin URL을 pre-exec 차단한다. `private_full_auto.config.toml`은 byte-preserved deprecated non-role artifact로 남고 새 launcher가 참조하지 않는다.
- **R7.3** role launcher는 required registry contract token으로 old binary/new registry와 new binary/old registry 양방향 partial deployment를 verifier/provider 전에 `blocked_contract`로 막고, 기존 direct v1 caller의 select JSON, exit 2/3, timeout/env와 no-fallback 계약을 유지한다. reviewed launcher/registry/settings set은 별도 explicit deployment 뒤 새 process에만 적용한다.
- **R7.4** `docs/orchestrator-permission-profiles.md`는 exact heading/phrase contract로 role/file map, normalized-real-path selection과 alias/home-mode, model pin 대 availability, Claude `usage_unknown`과 operator response, permission/common-dir boundary, exact scrub, stdio/TTY, leader, verifier/identity, settings/effective sources/workmux, mixed deployment, cross-profile move, legacy migration generation과 no-auth-copy/no-hot-swap 운영 계약을 설명하며 CMD-8의 `test_documentation_contract`가 각 heading/phrase와 operator recovery 절을 결정적으로 검사한다.
- **R7.5** 완료에는 fixture chezmoi render, portable CLI range, path/account-role matrix, high-risk network-denied E2E, base preservation+#111 path-selection regression, portable full suite, repository unittest+`git diff --check`, sensitive-data hygiene, exact Claude home env, settings/effective sources, fake-workmux observability, permission/common-dir, cross-profile move와 legacy protection 판정이 모두 필요하다. 이 Mac release gate만 installed CLI의 `--version`/`--help`를 쓰며 offline help는 model availability/usage admission 증거가 아니다.

### Account root is a selection boundary, not a permission boundary

- **R8.1** account workspace root는 account selection boundary일 뿐 filesystem permission boundary가 아니다. Git write가 필요한 role의 permission set은 normalized resolved worktree path와 `git rev-parse --path-format=absolute --git-common-dir`로 검증한 exact common-dir path만 포함하며 opposite account root 전체와 그 root에 도달하는 wildcard/add-dir grant를 금지한다.
- **R8.2** linked worktree 이동 후 common-dir가 destination account root 밖에 남으면 launcher는 resolved worktree/common-dir의 관계, repository integrity와 requested role write need를 명시적으로 판단해 exact common-dir만 허용하거나 fail closed한다. 이 cross-root access를 원하지 않는 운영자는 destination profile root 아래 separate clone을 만들고 Git state와 handoff를 넘기며 opposite root 전체 권한을 허용하지 않는다.
- **R8.3** launcher/registry는 current `os.getcwd()` real path와 inherited `PWD`를 비교한다. move 전 process의 stale `PWD`는 account selection, re-selection, registry path update에 사용할 수 없고 탐지하면 `blocked_binding`으로 fail closed한다. cross-profile move 전에 provider, launcher, worker, watcher와 writer가 모두 정지되어야 한다.

### Cross-profile move contract

- **R9.1** cross-profile move는 rename이나 hot swap이 아니라 explicit account rebind와 새 execution generation이다. 먼저 Claude/provider process, workers, watchers와 file writers를 정지하고 dirty tracked/untracked Git state와 quality-goal state를 보존하는 in-repository handoff를 만든 뒤에만 이동한다. running process의 `CLAUDE_CONFIG_DIR`는 바꾸지 않는다.
- **R9.2** linked worktree는 `git worktree move OLD NEW`로 이동한다. main worktree와 submodule을 포함한 linked worktree는 이 command의 지원 대상이 아니며 destination root의 separate clone+handoff 또는 별도로 reviewed `git worktree repair` 절차를 사용한다.
- **R9.3** 이동 직후 `git worktree list --porcelain`, `git rev-parse --show-toplevel`, `git rev-parse --path-format=absolute --git-common-dir`, `git status --short`를 모두 실행해 registered path, top-level, exact common-dir, tracked/untracked state를 확인한다. common-dir가 destination root 밖이면 launcher가 이를 명시적으로 판단하고 무시하지 않는다.
- **R9.4** #94/#95 registry의 worktree real path, account profile과 monotonically new positive `binding_generation`은 single atomic update로 함께 바뀐다. stored binding과 destination directory mapping이 다르거나 어느 field/generation이라도 old/new state와 disagreement가 있으면 provider 전에 `blocked_binding`이고 부분 갱신·silent choice·fallback을 하지 않는다.
- **R9.5** registry 검증 뒤 destination root/profile의 새 process에서 handoff로 계속한다. source profile의 transcript, credential, account-home 또는 plugin state를 copy/symlink하지 않고 같은 process를 hot swap하지 않는다. Claude transcript는 `CLAUDE_CONFIG_DIR` 아래 absolute working path로 keyed되므로 cross-profile transparent `/resume`을 가정하지 않으며 resume unit은 verified Git state와 in-repository handoff다.
- **R9.6** 새 process 전에 launcher write root, exact common-dir permission, sandbox, workmux/tmux cwd와 watcher targets를 destination real path로 recompute하고 어떤 process도 old path/PWD/cwd/watch target을 참조하지 않음을 확인한다. 하나라도 stale하면 시작하지 않는다.

### Legacy runtime protection

- **R10.1** shipped registry source는 현재 deployed `[accounts.claude-dotfiles]` entry의 원래 bytes를 opaque, non-mappable, non-selectable legacy record로 보존하고 `~/.local/share/ai-account-profiles/claude/dotfiles` home을 hot rename/rebind, copy, symlink 또는 delete하지 않으며 running process와 binding을 유지한다. legacy provider default와 repository-kind scope binding은 새 schema declaration으로 carry over하지 않고, 새 schema에는 `defaults`와 `scope_bindings` table이 없으며 path mappings가 이를 전부 대체한다. legacy record bytes는 active account parser와 R3.5의 `allowed_scopes` domain 밖의 migration evidence로만 유지되어 directory mapping, explicit/stored/default selection, admission 또는 verifier 후보가 될 수 없고 explicit `claude-dotfiles` 요청은 다른 unmapped alias와 같이 `blocked_binding`으로 거부한다. 새 selectable Claude logical alias는 오직 `claude-profile1|claude-profile2`, 새 separate home은 오직 `~/.local/share/ai-account-profiles/claude/profile2`다.
- **R10.2** legacy에서 새 selectable alias로의 전환은 구현과 verification 후 별도 migration generation에서만 수행한다. 모든 referencing process를 stop하고 handoff를 만든 뒤 필요한 new home에서 official login과 identity admission을 별도 운영 검증하고 binding을 new generation으로 switch한다. credential home은 in-use rename/copy/symlink하지 않으며 `claude-dotfiles`와 `codex-dotfiles` legacy record/alias/home 제거는 각각 referencing process와 binding 수가 모두 0임을 검증한 뒤에만 별도 승인된 작업으로 가능하다.

### Agent-turn status hooks와 session observability

- **R11.1** common hook의 exact event-to-status mapping은 `Stop` → `workmux set-window-status done`, `Notification`의 `permission_prompt`와 `elicitation_dialog` 각각 → `workmux set-window-status waiting`, `PostToolUse`와 `UserPromptSubmit` 각각 → `workmux set-window-status working`, `PermissionRequest` → `workmux set-window-status waiting`이다. 현재 `PermissionRequest`의 desktop notification-only 동작은 보존 대상이 아닌 gap이며 이 work가 direct workmux update를 추가한다.
- **R11.2** secret-free common hook layer는 separated profile뿐 아니라 모든 account profile에 R4.4의 composition path, 즉 reviewed, versioned, digest-verified composed document의 single `--settings` 값으로 복원한다. 이를 위해 account home, credential directory 또는 settings file을 copy, sync, snapshot, symlink하지 않으며 hook command에는 secret, identity 또는 config-home path를 넣지 않는다.
- **R11.3** status hook은 R4.4의 trusted composed document를 통해서만 공급하고 R4.5의 trusted/untrusted boundary를 약화하지 않는다. `hooks` key를 가진 untrusted discovered account-home, project 또는 local settings file은 provider 실행 전에 계속 차단하며 exact benign allowlist는 변경하지 않는다.
- **R11.4** legacy separated profile처럼 hook이 없는 role launch는 active work 중 pane이 `done`에 머무는 silent observability regression을 만들 수 있다. separated config home에서 시작한 role도 turn event에 맞는 transition을 만들고, actively working session을 `done`으로 보고하지 않는다.
- **R11.5** status hook은 Skill/plugin policy상 observability capability일 뿐 dispatch capability나 lease-write capability로 분류되거나 이를 grant할 수 없으며, global reviewer와 standby의 dispatch 및 lease-write deny를 약화하지 않는다.
- **R11.6** deterministic verification은 synthetic separate `CLAUDE_CONFIG_DIR`와 call만 기록하는 fake `workmux` executable로 R11.1의 각 event와 각 case별 exact state transition, 새 `PermissionRequest` → `waiting`, active work 중 stale `done` 부재를 각각 판정한다. 일부 hook의 실행 여부만 확인해서는 안 되며 real pane, tmux session, window 또는 process를 시작, signal, restart, mutate하지 않는다.
- **R11.7** workmux smoke coverage는 `status`뿐 아니라 dashboard, sidebar와 wait surface를 모두 포함한다.
- **R11.8** 운영 문서는 exact phrase `done = agent-turn-ended, not issue-complete`와 status surface 비권한 문구를 포함하여 어떤 status surface도 issue completion으로 해석되지 않게 하며 CMD-8의 `test_documentation_contract`가 두 phrase를 결정적으로 검사한다.

## Acceptance criteria

- **AC-1** changed-path allowlist와 base byte diff가 허용 범위만 보이고 네 preserved target의 diff가 0이며 #111 priority가 explicit→stored binding→longest directory→Codex-only default로 유지되고 conflict/no-fallback regression이 통과한다. [실행] (CMD-12)
- **AC-2** 여덟 launcher symlink가 단일 dispatcher를 가리키며 argv[0]이 정확한 provider/role을 만든다. [실행] (CMD-1)
- **AC-3** 네 role만 schema/startup/fixture에 존재하고 `orchestrator`와 `feature-orchestrator`가 혼동되지 않는다. [실행] (CMD-1)
- **AC-4** registry, role/Skill manifests, common/composed settings, instruction, dispatcher, selector, verifier/identity helper, tests와 documentation의 file ownership이 strict test와 문서 file map에 일치하고 wrapper가 selection/verifier parser를 복제하지 않는다. [실행] (CMD-1)
- **AC-5** 네 Codex launcher capture가 지정 model/effort와 permission policy를 나타내고 offline availability 주장이나 fallback이 없다. [실행] (CMD-2)
- **AC-6** 네 Claude launcher capture가 지정 model/effort를 나타내며 global elevation은 Fable pin과 사유를 유지하고 fallback이 없다. [실행] (CMD-3)
- **AC-7** session=Codex, feature=Claude default route가 고정되고 `not_logged_in`이 `usage_unknown`보다 우선하며 logged-in Claude도 adapter 부재 시 `usage_unknown`이다. explicit acknowledgement 없는 Codex feature 대체와 모든 automatic fallback은 거부된다. [실행] (CMD-7 CMD-8)
- **AC-8** 이 Mac의 help-only gate가 Codex 0.154.0/Claude 2.1.272와 required/forbidden option contract를 확인하고 portable fixtures가 range 경계와 missing option의 `blocked_cli_contract`를 확인한다. help 성공은 model availability나 usage admission으로 판정되지 않는다. [실행] (CMD-9 CMD-16)
- **AC-9** resume/continue/session-ID 입력이 pre-exec 거부되고 새 정책은 새 process fixture에만 보이며 current pane/process/session pid, env, stdio, binding과 state bytes가 변하지 않는다. [실행] (CMD-5)
- **AC-10** symlink surface와 real path가 다른 fixture에서 real path만 사용되고 longest real ancestor 하나만 선택된다. equal-priority/ambiguous/non-normalizable/stale-surface cases는 provider/verifier 0회로 fail closed한다. [실행] (CMD-4)
- **AC-11** `~/code/**`의 모든 Codex role/repository fixture가 selectable `codex-default`만 자동 선택하고 그 declaration의 `config_home`이 기존 provider-default Codex home `~/.codex`와 일치하며 새 Codex home 생성·이동·login과 declared additional Codex homes의 automatic reference/ranking/fallback/rotation은 0이다. [실행] (CMD-4)
- **AC-12** 초기 정책의 Claude role matrix가 real `profile1` root에서 `claude-profile1`, real `profile2` root에서 `claude-profile2`, 두 root 밖에서 조건 없이 `blocked_contract`를 낸다. selectable aliases 전체에 exact full-alias match를 적용했을 때 reserved alias `default|dotfiles|work|personal`은 0건이고 `codex-default`는 허용되며 non-selectable legacy record의 aliases는 검사 대상에서 제외된다. [실행] (CMD-4)
- **AC-13** chezmoi source, rendered target, launcher argv, verifier environment와 provider environment의 다섯 surface 모두에서 `claude-profile1`용 `CLAUDE_CONFIG_DIR` assignment가 0건이고 provider-default home의 literal path가 exported value로 0건이다. verifier/provider private child environment에서 `claude-profile1`은 해당 key가 없고 `claude-profile2`는 exact synthetic absolute neutral profile2 path만 가지며 invalid mode/path/symlink는 pre-exec 차단된다. [실행] (CMD-17)
- **AC-14** explicit/stored/longest-directory/Codex-default priority와 current real directory의 directory-only allowed-scope check가 통과한다. selectable account fixture의 모든 `allowed_scopes` kind는 `directory`이고 `repository`·`organization`·unknown kind를 하나라도 넣은 registry fixture는 verifier/provider 0회인 `blocked_contract`다. same-remote worktrees under profile1/profile2 select different Claude profiles; owner/repository/remote/organization 값의 변경은 selection과 admission 어느 것도 바꾸지 않고 Git remote/common-dir는 integrity-only다. cwd/usage/remote change 후 re-selection은 0이고 limit은 `blocked_usage`로 끝난다. [실행] (CMD-4)
- **AC-15** verifier/admitted/provider capture에서 exact scrub set `CODEX_HOME`, `CLAUDE_CONFIG_DIR`, `CODEX_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, `CLAUDE_CODE_OAUTH_TOKEN`, `CLAUDE_CODE_USE_BEDROCK`, `CLAUDE_CODE_USE_VERTEX`, `CLAUDE_CODE_USE_FOUNDRY`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `GOOGLE_APPLICATION_CREDENTIALS`, `CLOUD_ML_REGION`, `ANTHROPIC_VERTEX_PROJECT_ID`, `ANTHROPIC_FOUNDRY_RESOURCE`, `ANTHROPIC_FOUNDRY_API_KEY`, `AI_COST_LIMIT_USD`가 먼저 모두 제거되고 선택 Codex/explicit Claude home만 조건부 재도입되며 profile1/common env에는 금지 key가 없다. [실행] (CMD-4)
- **AC-16** Codex 네 role의 model/effort/approval/sandbox/write-root matrix가 정확하고 unrestricted/bypass grant가 없다. [실행] (CMD-2)
- **AC-17** repository-root→real-cwd Codex config chain의 policy/unknown key와 override tail은 `blocked_policy`이고 empty/comment-only 및 exact benign config만 허용되며 argv self-compare를 precedence 증거로 쓰지 않는다. [실행] (CMD-2 CMD-11)
- **AC-18** 네 Claude role의 composed settings가 dontAsk와 fail-closed sandbox, reviewed 일곱 hook event/permissions/plugins, role deny 우선을 갖고 단일 `--settings`와 local `--plugin-dir`만 사용하며 secret/auth-home replication, launch write와 `--plugin-url`이 없다. fake `workmux`는 waiting/working/done observability를 capture하고 actual pane/session/process mutation은 0회다. [실행] (CMD-3 CMD-18 CMD-19)
- **AC-19** effective-setting-sources 결과가 exact digest의 composed document와 reviewed local plugin만 trusted로 열거한다. untrusted policy/unknown settings는 차단되고 empty/`$schema`/`spinnerTipsEnabled`/`theme`만 허용되며 `--setting-sources` precedence에 의존하지 않는다. [실행] (CMD-18)
- **AC-20** reviewed instruction의 exact bytes/version/SHA-256이 startup과 argv에 일치하고 Codex developer instruction 및 Claude single additive value만 생성된다. invalid UTF-8/NUL/hash와 alternate file/agent/system-prompt path는 pre-exec 실패다. [실행] (CMD-5)
- **AC-21** role/account orthogonality와 task/direct-parent matrix가 통과하고 account만 바꾼 같은 role의 model/effort/permission/instruction/settings/Skill/leader bytes가 동일하다. [실행] (CMD-4 CMD-5)
- **AC-22** binding/startup/failure record가 event별 exact one-line JSON과 stable field/type/generation을 가지며 config-home, identity, credential, extra field와 sensitive marker가 없다. [실행] (CMD-5 CMD-15)
- **AC-23** PTY fixture에서 dispatcher 전후 provider의 stdin/stdout/stderr `isatty`, FD target/device/inode가 동일하고 outer pipe/capture가 없으며 pre-exec public bytes 뒤 provider stderr는 fake provider가 직접 소유한다. [실행] (CMD-5)
- **AC-24** same-scope global active race에서 하나만 lock FD를 provider 종료까지 보유하고 verifier에는 FD가 없으며 second active는 `blocked_leader_conflict`; different scope와 post-exit reacquire는 성공한다. [실행] (CMD-6)
- **AC-25** reviewer/standby의 dispatch/lease-write/lock capability와 sentinel mutation이 0이고 invalid owner/takeover evidence는 기존 process/proof/generation을 바꾸지 않은 `blocked_binding`이다. [실행] (CMD-6)
- **AC-26** provider verifier builder가 선택 home mode의 exact environment와 reviewed official command만 만들고 timeout/strict six-field/redaction을 지킨다. Claude unlogged/logged fixtures는 각각 `not_logged_in`/`usage_unknown`, provider/fallback sentinel은 0회다. [실행] (CMD-7 CMD-17)
- **AC-27** canonicalization fixtures가 NFC/trim/case/control rules, canonical sorted compact JSON, 64-hex SHA-256+LF를 재현하고 excluded identity fields나 unstable official identity는 fail closed한다. [실행] (CMD-7)
- **AC-28** synthetic enrollment가 owner 0700/0600 regular non-symlink atomic file과 shared parser match를 만들고 failure는 기존 digest를 보존한다. missing/mode/type/owner/mismatch status와 stdout/stderr redaction이 정확하며 actual enrollment는 0회다. [실행] (CMD-7 CMD-15)
- **AC-29** failure fixtures가 unique classifier에서 exit 2/3/4와 required precedence/status를 얻고 wrapper retry/reclassification 및 model/provider/account fallback은 0이며 provider model rejection exit은 보존된다. [실행] (CMD-8)
- **AC-30** strict public binding/startup/failure JSON, captured test artifact, log, diagnostic, error output와 운영 문서에 real deployed config-home path 또는 그 파생 path가 없고, credential과 raw identity/digest/provider output도 해당 disclosure surface에 없다. selected explicit config-home path는 reviewed non-secret registry source, rendered configuration target과 verifier/provider private child environment에만 허용된다. permitted private-child-environment surface의 exact env를 판정하는 synthetic fixture path assertion/capture는 real deployed path prohibition에서 제외되며, real home/auth/status/login/logout/usage/network/model/enrollment/chezmoi/current-process/production sentinel 접근은 0이다. [실행] (CMD-15)
- **AC-31** strict Skill/plugin schema, role/task intersection, deny-first와 global reviewer/standby multi-agent/dispatch/lease deny가 통과하고 workmux hook은 observability capability로만 남는다. [실행] (CMD-6 CMD-8)
- **AC-32** startup의 Skill policy ID/count가 capture와 일치하고 missing/deny/catalog/version/hash/path/network-plugin 오류가 pre-exec 차단되며 `private_full_auto.config.toml`은 byte-identical, unreferenced 상태다. [실행] (CMD-8 CMD-12)
- **AC-33** v1 direct compatibility와 양방향 mixed deployment fixture가 요구 status로 통과하고 reviewed new set 이전/current process 상태는 보존된다. [실행] (CMD-8 CMD-13)
- **AC-34** 운영 문서가 R7.4의 role/file map, normalized-real-path selection과 alias/home-mode, model pin 대 availability, Claude `usage_unknown`과 operator response, permission/common-dir boundary, exact scrub, stdio/TTY, leader, verifier/identity, settings/effective sources/workmux, mixed deployment, cross-profile move, legacy migration generation, no-auth-copy/no-hot-swap 및 operator recovery heading/phrase를 모두 포함한다. [실행] (CMD-8)
- **AC-35** CMD-9부터 CMD-22까지의 applicable release, render, E2E, preservation, portable/full, hygiene, CLI/home/settings/workmux, permission-boundary, move와 legacy checks가 모두 통과하고 실제 auth/network/account-home/process mutation은 없다. [실행] (CMD-9 CMD-10 CMD-11 CMD-12 CMD-13 CMD-14 CMD-15 CMD-16 CMD-17 CMD-18 CMD-19 CMD-20 CMD-21 CMD-22)
- **AC-36** write-capable role fixture의 allow set이 normalized resolved worktree와 exact absolute Git common-dir 두 path로만 구성되고 opposite account root 전체나 도달 가능한 wildcard/add-dir grant는 0이다. [실행] (CMD-20)
- **AC-37** destination root 밖 common-dir linked-worktree fixture가 launcher의 explicit integrity/permission judgement를 거치며 exact common-dir 이외 cross-root grant가 없다. deny-cross-root case는 destination-root separate clone+handoff 대안을 요구하고 fail closed한다. [실행] (CMD-20 CMD-21)
- **AC-38** moved live-cwd fixture에서 real `os.getcwd()`와 stale inherited `PWD` 불일치가 selection/registry update 전에 `blocked_binding`이고 stale PWD 기반 selection/re-selection/update는 0이다. shutdown proof가 없는 writer/watcher/worker/launcher move도 거부된다. [실행] (CMD-20 CMD-21)
- **AC-39** move fixture가 provider/workers/watchers/writers shutdown과 dirty tracked/untracked 및 quality-state handoff를 요구하고 running process env hot swap을 0회로 유지한다. [실행] (CMD-21)
- **AC-40** linked worktree만 `git worktree move` 경로를 통과하고 main worktree/submodule fixture는 separate clone+handoff 또는 explicitly reviewed repair 경로 없이는 거부된다. [실행] (CMD-21)
- **AC-41** post-move fixture가 `git worktree list --porcelain`, `git rev-parse --show-toplevel`, `git rev-parse --path-format=absolute --git-common-dir`, `git status --short` 네 결과와 preserved tracked/untracked state를 확인하며 external common-dir를 무시하지 않는다. [실행] (CMD-21)
- **AC-42** registry path/account/generation이 하나의 atomic update로 새 positive generation에 바뀌고 stored/directory disagreement, partial bytes와 stale generation은 provider 전에 `blocked_binding`이며 old registry가 보존된다. [실행] (CMD-21)
- **AC-43** destination profile의 새 process만 handoff에서 시작하고 transcript/credential/plugin/account-home copy·symlink와 hot swap은 0회다. test/document contract가 transparent cross-profile `/resume` 대신 verified Git state+in-repository handoff를 요구한다. [실행] (CMD-21 CMD-15)
- **AC-44** move 후 write root, exact common-dir, sandbox, workmux/tmux cwd와 watcher target이 new real path로 recompute되고 old cwd/PWD/path/watch reference가 하나라도 남은 fixture는 새 process 시작 전에 차단된다. [실행] (CMD-21)
- **AC-45** checked-in shipped registry fixture의 active declarations는 selectable Claude accounts `claude-profile1`과 `claude-profile2`, 그 두 account의 directory-only scopes, profile1 provider-default/no-path mode, profile2 neutral explicit path 및 두 path mappings를 정확히 포함하고 `defaults`·`scope_bindings` table은 포함하지 않는다. deployed `[accounts.claude-dotfiles]`의 원래 record bytes는 opaque legacy evidence로 byte-identical 보존되지만 active account/mapping/default/binding/verifier 후보 declaration은 0이고, explicit request는 `blocked_binding`이다. legacy alias/home의 rename·rebind·copy·symlink·delete는 0회다. [실행] (CMD-22 CMD-15)
- **AC-46** legacy migration fixture가 implementation verification 이후 separate generation, process shutdown, handoff, 필요한 synthetic official login/identity admission proof와 atomic new binding을 모두 요구한다. in-use home rename/copy/symlink 및 `claude-dotfiles` 또는 `codex-dotfiles`의 nonzero process/binding reference 상태에서 해당 legacy record/alias/home removal은 거부된다. [실행] (CMD-22)
- **AC-47** `Stop`은 `done`, 두 `Notification` case는 각각 `waiting`, `PostToolUse`와 `UserPromptSubmit`은 각각 `working`, `PermissionRequest`는 desktop notification 외에 direct `waiting`으로 exact mapping된다. [실행] (CMD-19)
- **AC-48** 모든 account profile이 reviewed, versioned, digest-verified composed document의 single `--settings`를 통해 secret-free common hooks를 받고 account home, credential directory, settings file의 copy·sync·snapshot·symlink와 hook command의 secret·identity·config-home path가 0건이다. [실행] (CMD-18 CMD-15)
- **AC-49** hooks는 trusted composed document에서만 유입되고 `hooks` key가 있는 untrusted account-home/project/local settings fixture는 provider 전에 차단되며 exact benign allowlist가 유지된다. [실행] (CMD-18 CMD-3)
- **AC-50** separated config home의 role launch가 active work event에서 `working`으로 전환되고 active work 동안 stale `done`을 보고하지 않는다. [실행] (CMD-19)
- **AC-51** status hook은 observability capability로만 분류되고 dispatch 또는 lease-write grant가 0건이며 global reviewer와 standby의 기존 deny가 유지된다. [실행] (CMD-6)
- **AC-52** synthetic separate `CLAUDE_CONFIG_DIR`와 call-recording fake `workmux`가 event별 exact transition, `PermissionRequest` → `waiting`, active work 중 stale `done` 부재를 각각 판정하고 real pane/tmux session/window/process mutation은 0건이다. [실행] (CMD-19)
- **AC-53** workmux smoke가 `status`, dashboard, sidebar와 wait surface를 모두 판정한다. [실행] (CMD-23)
- **AC-54** 운영 문서가 exact phrase `done = agent-turn-ended, not issue-complete`와 status surface가 authority 또는 issue completion signal이 아니라는 phrase를 포함한다. [실행] (CMD-8)
- **AC-55** shipped registry fixture가 selectable Codex declaration을 정확히 `codex-default` 하나와 `config_home="~/.codex"`로 두고 deployed `[accounts.codex-dotfiles]`의 원래 record bytes를 opaque non-mappable/non-selectable legacy evidence로 byte-identical 보존한다. old alias의 active account/mapping/default/verifier 후보는 0이고 old alias stored binding fixture는 silent alias mapping 없이 provider/verifier 전 `blocked_binding`이며 explicit rebind를 요구한다. 새 Codex home 생성·이동·login과 legacy home read/mutation은 0회다. [실행] (CMD-22)

## Requirements traceability

This table maps every requirement to acceptance criteria and the judgement method that proves the mapping.

| Requirement | Acceptance criteria | Judgement method |
|---|---|---|
| R1.1 | AC-1 | CMD-12 |
| R1.2 | AC-2 | CMD-1 |
| R1.3 | AC-3 | CMD-1 |
| R1.4 | AC-4 | CMD-1 |
| R2.1 | AC-5 | CMD-2 |
| R2.2 | AC-6 | CMD-3 |
| R2.3 | AC-7 | CMD-7, CMD-8 |
| R2.4 | AC-8 | CMD-9, CMD-16 |
| R2.5 | AC-9 | CMD-5 |
| R3.1 | AC-10 | CMD-4 |
| R3.2 | AC-11 | CMD-4 |
| R3.3 | AC-12 | CMD-4 |
| R3.4 | AC-13 | CMD-17 |
| R3.5 | AC-14 | CMD-4 |
| R3.6 | AC-55 | CMD-22 |
| R4.1 | AC-16 | CMD-2 |
| R4.2 | AC-15 | CMD-4 |
| R4.3 | AC-17 | CMD-2, CMD-11 |
| R4.4 | AC-18 | CMD-3, CMD-18, CMD-19 |
| R4.5 | AC-19 | CMD-18 |
| R4.6 | AC-20 | CMD-5 |
| R5.1 | AC-21 | CMD-4, CMD-5 |
| R5.2 | AC-22 | CMD-5, CMD-15 |
| R5.3 | AC-23 | CMD-5 |
| R5.4 | AC-24 | CMD-6 |
| R5.5 | AC-25 | CMD-6 |
| R6.1 | AC-26 | CMD-7, CMD-17 |
| R6.2 | AC-27 | CMD-7 |
| R6.3 | AC-28 | CMD-7, CMD-15 |
| R6.4 | AC-29 | CMD-8 |
| R6.5 | AC-30 | CMD-15 |
| R7.1 | AC-31 | CMD-6, CMD-8 |
| R7.2 | AC-32 | CMD-8, CMD-12 |
| R7.3 | AC-33 | CMD-8, CMD-13 |
| R7.4 | AC-34 | CMD-8 |
| R7.5 | AC-35 | CMD-9, CMD-10, CMD-11, CMD-12, CMD-13, CMD-14, CMD-15, CMD-16, CMD-17, CMD-18, CMD-19, CMD-20, CMD-21, CMD-22 |
| R8.1 | AC-36 | CMD-20 |
| R8.2 | AC-37 | CMD-20, CMD-21 |
| R8.3 | AC-38 | CMD-20, CMD-21 |
| R9.1 | AC-39 | CMD-21 |
| R9.2 | AC-40 | CMD-21 |
| R9.3 | AC-41 | CMD-21 |
| R9.4 | AC-42 | CMD-21 |
| R9.5 | AC-43 | CMD-21, CMD-15 |
| R9.6 | AC-44 | CMD-21 |
| R10.1 | AC-45 | CMD-22, CMD-15 |
| R10.2 | AC-46 | CMD-22 |
| R11.1 | AC-47 | CMD-19 |
| R11.2 | AC-48 | CMD-18, CMD-15 |
| R11.3 | AC-49 | CMD-18, CMD-3 |
| R11.4 | AC-50 | CMD-19 |
| R11.5 | AC-51 | CMD-6 |
| R11.6 | AC-52 | CMD-19 |
| R11.7 | AC-53 | CMD-23 |
| R11.8 | AC-54 | CMD-8 |

## Architecture

구성은 non-secret role policy와 secret-bearing account home을 런타임에 직교 결합하는 두 축이다. account 축의 유일한 자동 선택 신호는 launch 시점의 normalized absolute real worktree path다. Codex는 real path가 `~/code/**`의 descendant이면 role과 repository에 관계없이 `codex-default`를 선택한다. 초기 정책의 Claude는 longest-real-ancestor mapping으로 `~/code/profile1/**`를 `claude-profile1`, `~/code/profile2/**`를 `claude-profile2`에 결합하고 두 root 밖에서는 조건 없이 `blocked_contract`로 닫힌다. 새 root는 별도 reviewed Spec과 registry source 개정으로 mapping을 바꾼 뒤 그 개정본을 launch 전에 배포해야 하며, 현재 launcher의 runtime 예외가 아니다. Git remote, organization, `owner/repository`와 common-dir는 후보를 만들거나 순위를 바꾸지 않고, 선택 뒤 worktree 무결성 및 exact permission path를 검증하는 데만 사용한다.

1. 여덟 symlink 진입점은 `argv[0]`으로 provider와 네 logical role 중 하나를 정해 단일 `ai-role-session` dispatcher로 들어간다. dispatcher는 account registry를 재구현하지 않고 `roles.toml`, `skill-policies.toml`, reviewed instruction, Claude common/composed settings, CLI contract와 role/task/parent/leader 입력만 검증한다.
2. dispatcher는 repository root부터 real cwd까지의 Codex project config와 적용 가능한 Claude account-home/project/local settings를 provider보다 먼저 검사한다. exact digest의 composed settings만 trusted이고 discovered configuration은 empty 또는 명시된 benign allowlist 외에는 untrusted다. launcher가 만든 argv를 자기 자신과 비교한 결과는 외부 configuration precedence의 증거가 아니다.
3. global active는 external lease proof와 normalized scope의 host-local exclusive lock을 검증하고 lock FD의 close-on-exec을 해제한다. reviewer/standby는 lock, lease-write, dispatch capability를 받지 않는다. dispatcher는 admitted phase에만 쓸 one-shot capability FD를 별도로 만든다.
4. dispatcher는 stdin/stdout/stderr를 close, dup, pipe 또는 proxy하지 않은 채 `ai-session launch`를 현재 process에서 정확히 한 번 exec한다. `ai-session`은 current `os.getcwd()`를 filesystem으로 resolve하고 symlink surface path와 inherited `PWD`를 선택에서 배제한다. active schema의 directory-only `allowed_scopes`를 먼저 검증하고 repository/organization/unknown kind면 registry contract를 거부한다. explicit option → stored task/session binding → longest real ancestor directory mapping → Codex-only provider default 순으로 한 후보를 고른 뒤 current real directory의 scope, stored binding generation과 Git integrity를 검증한다. legacy records는 후보가 아니며 동일 순위 충돌, stored/derived disagreement, stale `PWD`, invalid home mode 또는 외부 Claude path는 verifier 전에 차단한다.
5. `ai-session`은 exact scrub 후 선택 profile의 home mode로 verifier를 격리 실행한다. `claude-profile1`에는 `CLAUDE_CONFIG_DIR` key가 없고 `claude-profile2`에만 neutral explicit home이 있다. verifier subprocess는 captured/redacted I/O, `close_fds=True`, empty `pass_fds`를 사용해 capability와 lock을 받지 않으며, shared identity parser로 strict six-field result만 만든다. admission status를 분류하는 component는 `ai-session` 하나뿐이다.
6. 성공하면 `ai-session`은 `account_binding`을 inherited stderr에 직접 쓰고 unchanged stdio 및 inherited capability/lock으로 admitted phase를 exec한다. admitted phase는 capability를 한 번 소비·close하고 role policy, instruction/settings digest, effective setting sources, Skill/plugin set과 final argv를 대조한다. 성공 시 `role_startup`을 같은 stderr에 직접 쓴 뒤 provider를 exec한다. provider는 동일 terminal stdin/stdout/stderr를 소유하며 global active일 때 lock FD를 process 종료까지 보유한다.
7. cross-profile move는 이 launch chain 밖의 explicit rebind protocol이다. 모든 writer를 멈추고 handoff를 만든 뒤 linked worktree만 `git worktree move`하고 Git 상태를 검증한다. registry path, account와 `binding_generation`을 atomic하게 갱신한 다음 새 real path에서 새 process를 시작한다. 모든 permission, sandbox, workmux/tmux cwd와 watcher target은 재계산되며 같은 process의 account hot swap이나 transparent `/resume`은 없다.

account workspace root는 selector의 경계일 뿐 sandbox root가 아니다. Git 2.55.0 probe가 보여 준 것처럼 moved linked worktree의 common-dir는 이전 root에 남을 수 있으므로 write-capable role은 resolved worktree와 검증한 exact common-dir만 허용한다. 반대 profile root 전체를 허용하지 않으며, cross-root Git metadata access를 원하지 않으면 destination root의 separate clone과 handoff를 사용한다. common workmux hook layer는 account home 복사가 아니라 reviewed common+role settings composition으로 모든 Claude profile에 복원한다.

## Interfaces and data flow

공개 launcher CLI는 다음 형태다.

```text
ai-codex|ai-claude[-orchestrator|-feature-orchestrator|-global-orchestrator] \
  [--account-profile ALIAS] \
  [--task-id PUBLIC_ID] \
  [--parent-task-id PUBLIC_ID|none] \
  [--binding-file ABSOLUTE_PATH] \
  [--leader-mode active|reviewer|standby] \
  [--leader-scope PUBLIC_SCOPE] \
  [--leader-id PUBLIC_ID] \
  [--lease-proof ABSOLUTE_PATH] \
  [--feature-fallback-contract quality-goal-v1] \
  [--global-effort medium|high] \
  [--verifier ABSOLUTE_PATH] \
  -- [policy를 바꾸지 않는 provider argument]
```

`--account-profile`은 selection priority의 explicit 단계일 뿐 `allowed_scopes`를 우회하지 않는다. resume/continue/session-ID, model/profile/settings/permission/sandbox/add-dir/bypass/fallback과 policy override tail은 거부한다. `--verifier`는 provider별 reviewed target이 기본이며 explicit 값도 absolute executable regular non-symlink file이어야 한다. 내부 role launch는 reviewed registry contract token을 반드시 넘기고 direct v1 `ai-session select|launch`의 기존 JSON, exit 2/3과 no-fallback 계약은 유지한다.

`accounts.toml`의 strict public schema는 top-level `schema_version`, `contract_id`, active `accounts`, `workspace_directory_mappings`, `task_bindings`, `session_bindings`와 byte-preserved opaque `legacy_records`를 가진다. `defaults`와 `scope_bindings` table은 없다. 각 active account는 `alias`, `provider`, `auth_kind`, directory-only `allowed_scopes`, identity enrollment policy를 가지며 Codex account는 검증할 `config_home`, Claude account는 mandatory `config_home_mode`를 가진다. active account의 `allowed_scopes`에 `repository`, `organization` 또는 unknown kind가 있으면 registry 전체가 contract failure다. `legacy_records`는 deployed `[accounts.claude-dotfiles]`와 `[accounts.codex-dotfiles]` 원본 record bytes를 opaque evidence로만 보존하며 active account parser가 field나 scope로 해석하지 않고 어떤 selection/admission/verifier 후보로도 노출하지 않는다. shipped active declarations의 selectable aliases는 정확히 `codex-default`, `claude-profile1`, `claude-profile2`이고, 여기서 “initial Claude aliases는 `claude-profile1|claude-profile2`뿐”은 두 selectable Claude aliases를 뜻해 preserved legacy record를 포함하지 않는다. `codex-default`의 `config_home`은 기존 provider-default Codex home `~/.codex`다. `config_home_mode="provider_default"`는 config-home path field를 금지하고 `config_home_mode="explicit"`는 normalized absolute regular non-symlink `config_home`을 요구한다. 두 Claude active accounts는 각각 provider-default/no-path와 explicit neutral profile2 path다. explicit path는 reviewed non-secret registry source와 rendered configuration target에 존재하고 scrub 후 verifier/provider private child environment로만 흐르며 disclosure surface에는 직렬화되지 않는다. provider-default mode는 source/target/launcher argv/verifier env/provider env 어디에도 `CLAUDE_CONFIG_DIR` assignment나 provider-default home literal exported value를 만들지 않는다. directory mapping은 normalized real `root`, `provider`, `account_profile`, 명시 priority를 가지며 selector는 path-component ancestor 관계와 longest root length로 한 후보만 선택한다. task/session binding은 public binding ID, provider, account profile, bound real worktree path와 positive `binding_generation`을 가지며 stored path/profile/generation은 current derived mapping과 일치해야 한다. old legacy alias를 참조하는 binding은 alias 치환 없이 `blocked_binding`이다. Git remote/common-dir field가 저장되더라도 integrity evidence일 뿐 selection key, rank 또는 admission input이 아니다.

`roles.toml`은 `schema_version`, provider별 semantic CLI range와 required/forbidden help surface, benign-config allowlist, trusted settings/instruction path·version·SHA-256, local plugin path, 그리고 role별 provider, default/alternate route, model, effort, permission engine/mode, Skill policy ID, leader mode와 capability를 가진다. `skill-policies.toml`은 versioned policy ID, allow/deny와 task-overlay intersection을 정의하며 deny가 우선한다. Claude common layer와 role layer는 chezmoi render 시 하나의 secret-free document로 구조 병합되고 read-once digest 검증 뒤 single `--settings`로 전달된다. local plugin은 repeatable `--plugin-dir`만 허용된다.

selection/admission 성공 record의 exact field는 `schema_version`, `event="account_binding"`, `provider`, `role_profile`, `account_profile`, `account_scope`, `selection_source`, `selection_reason`, `usage_admission_status`, `binding_generation`이다. provider 직전 startup record의 exact field는 `schema_version`, `event="role_startup"`, `cwd`, `repository`, `provider`, `model`, `effort`, `role_profile`, `manifest_id`, `settings_id`, `permission_engine`, `permission_mode`, `instruction_version`, `instruction_sha256`, `leader_mode`, `task_id`, `direct_parent_id`, `skill_policy_id`, `active_skill_count`, `account_profile`, `account_scope`, `selection_source`, `selection_reason`, `usage_admission_status`, `binding_generation`, `dispatch_allowed`, `lease_write_allowed`다. failure record의 exact field는 `schema_version`, `event="launch_failure"`, `status`, `exit_code`, `provider`, `role_profile`, `account_profile`, `account_scope`, `selection_source`, `selection_reason`, `usage_admission_status`다. 세 schema는 extra field를 거부하고 sorted compact UTF-8 JSON과 single LF를 사용한다. `schema_version`은 integer 1, `binding_generation`은 positive integer, count는 nonnegative integer, capability field는 boolean이며 적용 불가/selection 전 field만 JSON null이다. config-home path, raw reason/provider output, identity/digest와 credential은 포함하지 않는다.

lease proof는 exact `schema_version`, `scope`, `leader_id`, `provider`, `generation`, `expires_at`, `direct_parent`만 갖는다. lock key는 normalized scope의 SHA-256이고 metadata는 public leader ID, provider, generation, pid, start time뿐이다. verifier result는 기존 strict six-field contract를 지키며 raw output을 부모에 전달하지 않는다.

enrollment interface는 `ai-session-enroll-identity --registry ABSOLUTE_PATH --provider PROVIDER --account-profile PROFILE`이다. registry에서 exact home mode/auth kind를 얻고 official interactive login이 별도 완료된 profile에 운영자가 명시 호출할 때만 shared parser로 canonical digest를 owner 0700 directory의 owner 0600 regular non-symlink file에 fsync+atomic replace한다. 성공 record는 `schema_version`, `event="enrolled_identity"`, `provider`, `account_profile`, `status="enrolled"`; 실패 record는 `schema_version`, `event="identity_enrollment_failure"`, `provider`, `account_profile`, `status="blocked_verifier"`, `exit_code=3`이다. verifier는 enrollment 파일을 만들거나 갱신하지 않는다. 이 Spec의 자동 workflow와 tests는 synthetic output만 사용하고 실제 interface를 호출하지 않는다.

data flow는 `argv[0]/public options + current real cwd` → role preflight → one-shot capability/optional leader lock → single exec의 `ai-session` path selection 및 authorization → scrubbed verifier → `account_binding` → admitted role/settings/Skill validation → `role_startup` → interactive provider exec 순이다. cross-profile move에서는 shutdown proof + Git/handoff state → Git move/verification → atomic path/profile/generation update → recomputed targets → 새 process 순이며 이전 transcript나 credential은 흐르지 않는다.

## Failure behavior

- malformed registry, active account의 non-directory `allowed_scopes`, invalid alias/home-mode/path, ambiguous/non-normalizable real path, 초기 정책에서 Claude normalized real path가 `~/code/profile1/**`와 `~/code/profile2/**` 두 root 모두의 밖인 경우, mixed deployment contract와 selection conflict는 provider/verifier 전에 조건 없이 exit 2 `blocked_contract`다. launcher는 repository/organization scope를 보존·무시·평가하거나 runtime mapping 예외와 lower-priority account를 시도하지 않는다.
- explicit/stored account가 current real directory mapping·allowed scope와 다르거나 stored path/profile/generation이 derived state와 다르면 exit 4 `blocked_binding`이다. stale inherited `PWD`, incomplete atomic rebind, stale generation, missing shutdown proof와 old path/watch reference도 같은 status이며 registry나 process를 변경하지 않는다.
- role manifest/path/hash/settings merge/schema 오류는 exit 4 `blocked_role_schema`; policy-bearing/unknown Codex 또는 Claude config, forbidden tail, digest mismatch와 role-deny 충돌은 `blocked_policy`; unavailable sandbox, whole opposite-root grant, wildcard/add-dir로 반대 root에 도달하는 grant, 검증되지 않은 external common-dir 또는 unsupported cross-root write는 `blocked_permission`이다.
- CLI 부재, version range와 required/forbidden help mismatch는 exit 4 `blocked_cli_contract`이다. help-only 성공은 model availability나 usage admission으로 승격되지 않는다.
- verifier result는 한 classifier에서 `not_logged_in` → `identity_drift` → `blocked_verifier` → `usage_unknown` → `blocked_usage` 순으로 exit 3을 낸다. Claude가 로그인 fixture여도 이 host에는 공식 usage contract가 없어 `usage_unknown`이다. relogin, TUI/private endpoint 추론, retry와 account/provider/model fallback은 복구로 인정하지 않는다.
- identity file missing/mode/type/owner/parser/timeout/malformed 오류는 `blocked_verifier`, enrolled digest mismatch는 `identity_drift`다. verifier는 first-use enrollment나 자동 갱신을 하지 않고 helper 실패는 기존 digest를 보존한다.
- same-scope proof/lock conflict 또는 invalid/expired proof는 exit 4 `blocked_leader_conflict`다. 기존 leader/proof/generation을 유지하며 reviewer/standby로 자동 강등하지 않는다.
- task/parent/owner/takeover 불일치는 `blocked_binding`이며 기존 process/session을 signal하거나 고치지 않는다. provider가 pinned model을 거부하면 provider nonzero exit을 그대로 반환하고 fallback하지 않는다.
- `git worktree move`는 main worktree와 submodule-containing linked worktree에서 거부된다. linked move 뒤 required Git command 중 하나가 불일치하거나 dirty tracked/untracked state가 보존되지 않으면 atomic binding update와 새 process를 시작하지 않는다. external common-dir를 exact path로 허용할 수 없으면 fail closed하고 destination-root separate clone+handoff를 안내한다.
- legacy `claude-dotfiles` 또는 `codex-dotfiles` alias/home에 nonzero process 또는 binding reference가 있으면 rename, rebind, copy, symlink, delete와 removal을 거부한다. legacy record는 selection 후보가 아니고 이를 참조하는 explicit/stored binding은 `blocked_binding`이며, 새 alias 전환은 별도 migration generation과 explicit operator procedure 전에는 일어나지 않는다.
- common hook/settings가 없거나 `PermissionRequest`가 direct `waiting`을 만들지 않거나 active work가 stale `done`이면 deployment gate가 실패한다. status hook 실패가 provider 권한, dispatch 또는 lease-write를 넓히는 fallback은 없다.

모든 pre-exec 실패는 strict `launch_failure` 한 줄을 inherited stderr에 쓰며, binding 뒤 실패는 binding과 failure만 남기고 startup은 쓰지 않는다. 자동 retry는 없다. operator는 public status와 문서화된 원인을 수정한 뒤 새 process로 재시도하며 current pane/process, stored credential과 legacy home을 자동 변경하지 않는다.

## Security and risk

account home, credential store, Keychain, provider raw status와 canonical identity는 민감 trust domain이다. registry, role/Skill manifest, directory mapping, Git metadata, binding, lease proof와 public IDs는 non-secret control data지만 변조되면 account 혼동이나 권한 상승을 만들 수 있어 strict schema, reviewed digest, owner/mode, regular non-symlink, read-once, atomic generation과 fail-closed 검증을 적용한다. inherited environment와 user/account/project/local configuration, tail argv, plugin/MCP discovery, symlink surface path와 `PWD`는 untrusted다.

account root는 credential/account 선택 경계일 뿐 filesystem permission 경계가 아니다. Git 2.55.0 evidence상 linked worktree common-dir가 이전 profile root에 남는 cross-root metadata access가 핵심 위험이다. launcher는 normalized resolved worktree와 `git rev-parse --path-format=absolute --git-common-dir`의 exact path만 role 필요에 따라 허용하고, 반대 account root 전체·wildcard·unrestricted/add-dir grant를 금지한다. 이 예외조차 원하지 않는 operator에게는 destination root separate clone을 요구한다. remote/common-dir는 integrity verification만 수행하고 profile 선택을 바꾸지 않는다.

credential non-replication은 불변이다. authentication file, token, refresh token, credential directory, account home, transcript와 plugin state는 profile 간 copy, sync, snapshot, rename 또는 symlink하지 않는다. common hooks/permissions/plugins는 secret-free reviewed settings composition과 local reviewed plugin으로만 복원한다. exact credential/auth-route scrub set을 부모 환경에서 먼저 제거하고 선택 Codex home 또는 explicit Claude home만 조건부 재도입한다. selected explicit config-home path는 reviewed non-secret registry source, rendered configuration target과 verifier/provider private child environment에 한정한다. strict public JSON, captured test artifacts, logs, diagnostics, error output와 운영 문서에는 real deployed config-home path나 그 파생 path가 없고 raw identity/digest/provider output도 노출하지 않는다. private child environment의 exact 계약을 판정하는 synthetic fixture path assertion/capture만 real deployed path prohibition의 예외다.

권한 위험은 Codex legacy sandbox와 beta profile 혼합, discovered config precedence 추측, sandbox fail-open, role deny를 약화하는 common settings/plugin, reviewer dispatch, duplicate global active와 stale-path rebind다. 통제는 legacy sandbox chain 단독 사용, policy/unknown pre-scan, digest-verified composed settings, local-only plugin, deny-first Skill intersection, external proof+inherited lock, stale `PWD`/generation 차단, single-exec TTY ownership과 high-risk network-denied sentinel matrix다. workmux hook은 observability-only이고 status를 issue completion이나 authority로 사용하지 않는다.

## Test strategy

단위 테스트는 strict registry/role/Skill schema, real-path normalization과 longest ancestor, alias/home-mode invariant, selection priority와 allowed scope, identity canonicalization, environment scrub, public record serialization, status precedence, CLI ranges, config pre-scan, permission path construction, hook mapping과 generation rules를 검사한다. integration test는 temp Git repositories, synthetic account/config homes, fake provider/verifier/CLI/workmux, PTY와 inherited FD probe로 eight-entrypoint matrix, provider-default variable absence, exact explicit home, settings/instruction digest, effective sources, leader race, stdio identity, move/rebind와 legacy protection을 실제 exec 직전까지 판정한다. 고위험 E2E는 network-denied environment에서 provider/auth/enrollment/account-home/current-process 접근 sentinel을 두고 path/account×role, hostile config, external common-dir, cross-profile move, fake workmux surface와 mixed deployment를 함께 실행한다.

모든 filesystem fixture는 temp synthetic home과 separate synthetic config home만 사용한다. 실제 credential/account home, login/auth/status/usage, network/model, identity enrollment와 current pane을 읽거나 변경하지 않는다. fake process assertions는 실재 pane, tmux session/window 또는 provider process를 start, signal, restart, kill, resume하거나 mutate하지 않았음을 확인한다. chezmoi 검증은 fixture source-to-target render일 뿐 `chezmoi apply`가 아니다.

### 판정 명령 표

| ID | 명령 | 통과 조건 |
|---|---|---|
| CMD-1 | `python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_role_manifest -k test_account_registry_schema -k test_launcher_entrypoints -k test_file_ownership` | role/account/Skill registry strict schema, 네 role, 여덟 symlink와 단일 dispatcher, parser 중복 금지 및 file responsibility가 AC-2~AC-4와 일치한다. |
| CMD-2 | `python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_codex_policy -k test_codex_project_config_prescan` | 네 Codex model/effort/approval/legacy-sandbox/write-root matrix, beta 혼합 금지, root→real-cwd config pre-scan, benign allowlist, tail/no-fallback이 AC-5, AC-16, AC-17을 만족한다. |
| CMD-3 | `python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_claude_policy -k test_claude_settings_prescan` | 네 Claude model/effort, Fable elevation reason, dontAsk/fail-closed settings, single settings/local plugin, untrusted settings pre-scan과 no-fallback이 AC-6, AC-18, AC-49를 만족한다. |
| CMD-4 | `python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_real_path_account_selection -k test_allowed_scope_kind_contract -k test_role_account_orthogonality -k test_child_environment -k test_exact_credential_scrub -k test_no_account_fallback` | real path longest-ancestor, Codex single selectable default/existing home, Claude two-root/outside-root, exact selectable-alias rule, directory-only scope와 non-directory registry rejection, remote/organization admission 배제, same-remote 다른 profile, role/account 직교성, exact scrub와 no re-selection/fallback이 AC-10, AC-11, AC-12, AC-14, AC-15, AC-21을 만족한다. AC-13의 다섯 home-mode surface는 CMD-17만 판정한다. |
| CMD-5 | `python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_startup_record -k test_binding_record -k test_task_parent_binding -k test_instruction_hash -k test_stdio_tty_inheritance -k test_new_process_only -k test_no_current_pane_mutation` | exact binding/startup/failure record, positive generation, task/parent, instruction bytes/hash, single-exec PTY/stdio identity, provider stderr ownership과 new-process-only/no-mutation이 AC-9, AC-20~AC-23을 만족한다. |
| CMD-6 | `python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_global_leader -k test_lock_fd_inheritance -k test_reviewer_standby -k test_takeover` | same-scope 단일 active, verifier FD 격리, provider lock lifetime, different-scope/reacquire, reviewer/standby deny와 fail-closed takeover가 AC-24, AC-25, AC-31, AC-51을 만족한다. |
| CMD-7 | `python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_live_verifier -k test_account_status_precedence -k test_identity_canonicalization -k test_identity_enrollment -k test_verifier_redaction` | official-command builder, six-field/timeout/redaction, Claude not-logged-in 우선과 logged-in usage_unknown, shared canonical parser, synthetic atomic enrollment와 identity failures가 AC-7, AC-26~AC-28을 만족한다. |
| CMD-8 | `python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_failure_status -k test_registry_contract_mixed_deployment -k test_skill_policy -k test_full_auto_compatibility -k test_documentation_contract` | unique exit/status classifier, 양방향 mixed deployment, no retry/fallback, Skill deny/intersection과 full_auto preservation을 판정한다. documentation contract는 role/file map, normalized-real-path와 alias/home-mode, model pin/availability, Claude `usage_unknown`/operator response, permission/common-dir, exact scrub, stdio/TTY, leader, verifier/identity, settings/effective sources/workmux, mixed deployment, cross-profile move, legacy migration, no-auth-copy/no-hot-swap, operator recovery의 각 heading/phrase와 exact phrase `done = agent-turn-ended, not issue-complete`, status surface 비권한 phrase를 열거해 검사한다. 이로써 AC-7, AC-29, AC-31~AC-34, AC-54를 만족한다. |
| CMD-9 | `AI_SESSION_CLI_PROBE_MODE=help-only python3 tests/check_installed_orchestrator_cli_contract.py` | 이 Mac의 Codex 0.154.0/Claude 2.1.272 version/help와 required/forbidden surface만 auth/network 없이 판정하고 CLI 부재는 실패하며 model availability/usage admission을 주장하지 않아 AC-8, AC-35를 만족한다. |
| CMD-10 | `python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_chezmoi_fixture_render` | synthetic fixture에서 source가 expected target content, mode와 symlink로 render되고 actual home/apply 없이 AC-35를 만족한다. |
| CMD-11 | `AI_SESSION_E2E_NETWORK=deny python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_high_risk_e2e` | network-denied eight-launcher path/account-role, hostile config, env, TTY, leader, verifier, no-fallback/no-live-action matrix가 AC-17, AC-35를 만족한다. |
| CMD-12 | `git diff --exit-code fcfb47ee2a0514518d150554ee491aae87d26d52 -- dot_claude/skills/create-worktree dot_config/workmux dot_tmux.conf.tmpl dot_zshrc.tmpl && python3 -m unittest -v tests/test_ai_session.py && python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_changed_path_allowlist -k test_no_account_fallback -k test_path_selection_regression` | 네 preserved path의 byte diff가 0이고 changed-path allowlist와 #111 explicit→stored→longest-directory→Codex-default, conflict/no-fallback 회귀가 AC-1, AC-32, AC-35를 만족한다. |
| CMD-13 | `python3 -m unittest -v tests/test_ai_session.py tests/test_orchestrator_profiles.py` | real CLI 없이 전체 portable selector/role suite와 v1 direct compatibility가 AC-33, AC-35를 만족한다. |
| CMD-14 | `python3 -m unittest discover -s tests -p 'test_*.py' -v && git diff --check` | installed release gate를 제외한 repository unittest discovery와 whitespace check가 모두 exit 0으로 AC-35를 만족한다. |
| CMD-15 | `python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_sensitive_data_hygiene -k test_no_auth_copy_or_symlink -k test_legacy_home_preservation -k test_no_unrestricted_path` | strict public binding/startup/failure JSON, captured test artifact, log, diagnostic, error output와 운영 문서에 real deployed config-home path와 그 파생 path가 없고 credential/raw identity·digest·provider output도 노출되지 않는다. selected explicit path는 reviewed non-secret registry source, rendered target과 verifier/provider private child environment에만 존재한다. private-child exact-env를 판정하는 synthetic fixture path assertion/capture는 real-path prohibition에서 제외하며 auth/account-home copy·sync·snapshot·symlink/delete, legacy mutation, unrestricted/bypass와 actual sentinel access가 0이라 AC-22, AC-28, AC-30, AC-35, AC-43, AC-45, AC-48을 만족한다. |
| CMD-16 | `python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_portable_cli_contract` | real CLI 없이 lower/in-range/upper-out/missing-option fixtures와 `blocked_cli_contract`가 AC-8, AC-35를 만족한다. |
| CMD-17 | `python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_claude_config_home_modes -k test_claude_default_env_unset -k test_claude_explicit_env -k test_verifier_provider_environments` | source/target/launcher argv/verifier env/provider env에서 provider-default `CLAUDE_CONFIG_DIR` assignment와 literal home exported value가 각각 0이고, explicit exact neutral path, invalid mode/path/symlink와 verifier/provider exact env가 AC-13, AC-26, AC-35를 만족한다. |
| CMD-18 | `python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_claude_settings_composition -k test_claude_settings_digest -k test_effective_setting_sources -k test_claude_plugin_policy -k test_claude_untrusted_settings_prescan` | read-once common+role composition, digest, role deny, reviewed local plugin, trusted/effective sources, benign allowlist와 no precedence assumption이 AC-18, AC-19, AC-35, AC-48, AC-49를 만족한다. |
| CMD-19 | `AI_SESSION_E2E_NETWORK=deny python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_workmux_event_transitions -k test_permission_request_waiting -k test_no_stale_done_during_active_work -k test_no_running_process_mutation` | separate synthetic config home과 call-recording fake workmux가 exact Stop/Notification/PostToolUse/UserPromptSubmit/PermissionRequest transition, stale-done 부재와 real mutation 0회를 보여 AC-18, AC-35, AC-47, AC-50, AC-52를 만족한다. |
| CMD-20 | `python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_account_root_permission_separation -k test_exact_git_common_dir_permission -k test_no_opposite_root_grant -k test_stale_pwd_rejected` | selection root와 permission set이 분리되고 worktree+exact common-dir만 허용되며 whole opposite-root/wildcard grant와 stale-PWD selection이 없어 AC-35~AC-38을 만족한다. |
| CMD-21 | `python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_cross_profile_move_shutdown -k test_git_worktree_move_and_verify -k test_stale_binding_block -k test_binding_generation_rebind -k test_move_handoff -k test_separate_clone_alternative` | writer shutdown, linked move와 네 Git verification, dirty/untracked 보존, stale PWD/binding block, atomic new generation, recomputed targets, new-process handoff와 main/submodule separate-clone 대안이 AC-35, AC-37~AC-44를 만족한다. |
| CMD-22 | `python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_legacy_alias_home_protection -k test_codex_default_existing_home -k test_legacy_records_non_selectable -k test_old_alias_binding_blocked -k test_migration_generation_gate -k test_legacy_zero_reference_removal` | shipped active registry가 selectable `codex-default`, `claude-profile1`, `claude-profile2`와 required home/mapping만 선언하고 `defaults`/`scope_bindings`가 없음을 검사한다. deployed Claude/Codex record bytes는 opaque legacy evidence로 byte-identical이고 selection/verifier 후보가 아니며 old-alias binding은 `blocked_binding`이다. legacy alias/home hot rename/rebind/copy/symlink/delete가 없고 separate generation 및 각 zero-process/zero-binding removal precondition이 AC-35, AC-45, AC-46, AC-55를 만족한다. |
| CMD-23 | `python3 -m unittest -v tests/test_orchestrator_profiles.py -k test_workmux_status_surface -k test_workmux_dashboard_surface -k test_workmux_sidebar_surface -k test_workmux_wait_surface` | fake workmux의 status, dashboard, sidebar, wait surface가 동일 turn-state를 보고하고 issue completion으로 오해하지 않아 AC-53을 만족한다. |

CMD-9만 installed binaries의 `--version`과 `--help`를 읽고, 근거는 `docs/development/2026-09-15-103-orchestrator-permission-profiles/installed-cli-contract-evidence.md`와 비교한다. 나머지는 synthetic fixtures만 사용한다. CMD-12의 base revision과 pathspec은 R1.1의 preservation 계약을 그대로 판정한다. 어느 command도 real login/logout/auth/status/usage, network/model probe, enrollment, account-home read, `chezmoi apply`, tmux/process mutation 또는 Git write를 수행하지 않는다.

## Decisions

### D1. role 설정 배치와 account 선택 합성

| 안 | 두 축의 독립성 | drift/배포 | 결론 |
|---|---|---|---|
| account home마다 role 설정 복제 | role×account 조합으로 결합된다 | copy마다 policy와 credential 경계가 흔들린다 | 기각 |
| external `roles.toml`/Skill/settings/instruction을 launcher가 읽고 selector 결과와 런타임 합성 | account 후보와 role capability가 서로를 바꾸지 않는다 | non-secret reviewed bytes 한 set만 배포한다 | 선택 |
| role×account provider profile을 미리 생성 | 조합 identity가 selector 의미를 가린다 | 조합 폭발과 재생성 drift가 있다 | 기각 |

role manifest는 account candidate, workspace mapping과 home mode를 소유하지 않고 `accounts.toml`은 model, effort, permission, instruction/settings/Skill/leader policy를 소유하지 않는다. account만 바꾼 같은 role의 effective policy bytes와 role만 바꾼 같은 path의 account 결정은 각각 동일해야 한다.

### D2. Codex permission engine

검증된 legacy `sandbox_mode`/approval chain만 선택한다. beta permission profile과 절대 혼합하지 않으며 개인 Mac에 `danger-full-access`, unrestricted 또는 bypass launcher를 만들지 않는다. beta 전환은 legacy key를 전부 제거하는 별도 migration과 독립 verification 없이는 허용하지 않는다.

### D3. global leader admission

external lease proof와 host-local exclusive lock을 함께 선택한다. proof는 cross-host authority를 나타내고 lock은 같은 host의 중복 active를 막는다. lock FD는 verifier에서 닫고 dispatcher→`ai-session`→admitted phase→provider의 single-exec chain에 상속해 kernel lifetime과 provider lifetime을 맞춘다. 이 launcher는 lease generation을 발급·갱신하지 않으며 reviewer/standby는 proof를 읽기만 한다.

### D4. verifier의 공식 usage boundary

separately reviewed official machine-readable contract만 login/identity/usage admission 근거로 쓴다. `docs/development/2026-09-15-103-orchestrator-permission-profiles/installed-cli-contract-evidence.md`에 따르면 이 host의 Claude Code 2.1.272 help는 auth status만 광고하고 usage/quota field contract가 없다. 따라서 미로그인은 `not_logged_in`이 먼저이고 로그인된 Claude도 `usage_unknown`으로 닫힌다. operator는 relogin, TUI scraping, private endpoint, raw output relay나 다른 consumer account/provider/model fallback으로 이를 우회하지 않고 separately reviewed official usage adapter가 requirements/tests/manifest에 추가된 뒤 새 process로 재시도한다.

### D5. 기존 `full_auto` compatibility artifact

`private_full_auto.config.toml`은 byte-for-byte 보존하고 deprecated non-role artifact로 문서화하며 새 launcher/manifest에서는 참조하지 않는다. 이름만 보고 삭제하거나 새 계층으로 흡수하면 기존 수동 사용을 깨뜨릴 수 있고, 실제 내용은 새 role permission source로 신뢰할 근거가 아니다.

### D6. 신뢰 가능한 effective-config probe가 없는 provider 설정

| 안 | 보안 근거 | 결론 |
|---|---|---|
| expected argv와 launcher argv의 self-comparison | builder가 자기 출력을 확인할 뿐 provider precedence를 증명하지 않는다 | 기각 |
| help에 flag가 있다는 이유로 override/`--setting-sources` precedence를 가정 | 실제 effective policy를 확인하지 못해 silent weakening이 가능하다 | 기각 |
| trusted composed input을 digest 검증하고 applicable untrusted config의 policy/unknown key를 pre-scan | 공식 auth-free probe 없이도 provider 전 fail closed한다 | 선택 |

Codex는 repository root→real cwd chain, Claude는 account-home/project/local candidates를 검사한다. empty/comment-only 또는 exact benign allowlist만 허용한다. 향후 공식 auth-free effective-config/dry probe가 확인되면 별도 Spec에서 범위를 재평가한다.

### D7. CLI compatibility와 installed release gate

| 안 | portable reproducibility | 실제 host evidence | 결론 |
|---|---|---|---|
| 모든 test가 exact installed version 요구 | 낮다 | 강하지만 CLI 없는 host를 깨뜨린다 | 기각 |
| 전부 fixture로 대체 | 높다 | 실제 release binary 증거가 없다 | 기각 |
| manifest semantic range fixture와 별도 help-only installed gate | 높다 | Codex 0.154.0/Claude 2.1.272를 독립 판정한다 | 선택 |

offline help는 required option surface만 증명하고 pinned model availability와 Claude usage admission은 증명하지 않는다.

### D8. identity enrollment와 digest 재현성

| 안 | identity 노출/신뢰 | 결론 |
|---|---|---|
| operator가 raw ID를 복사해 직접 hash | history/stdout 노출과 normalization drift가 있다 | 기각 |
| verifier의 first-use 자동 등록 | 공격 시점 identity를 신뢰하는 fail-open이다 | 기각 |
| host-local helper와 verifier가 shared canonical parser 사용 | raw identity를 출력하지 않고 deterministic digest를 owner-only atomic 저장한다 | 선택 |

canonical object와 normalization/serialization은 R6.2를 단일 계약으로 쓰고 verifier는 enrolled digest를 생성·갱신하지 않는다. 자동 검증은 synthetic identity만 사용한다.

### D9. interactive stdio ownership과 single-exec chain

| 안 | TTY/record/lock | 결론 |
|---|---|---|
| outer stderr pipe와 relay | provider terminal ownership과 public/provider stderr 경계가 바뀐다 | 기각 |
| PTY proxy | signal/window-size/byte transparency와 lock lifetime이 proxy에 의존한다 | 기각 |
| inherited stdio에 records를 직접 쓰는 one-exec chain | terminal identity를 보존하고 lock lifetime을 provider process에 맞춘다 | 선택 |

byte relay 보장은 provider 전 binding/startup/failure bytes에만 적용된다. verifier만 captured subprocess이고 provider exec 뒤 stderr와 exit은 provider 소유다.

### D10. account-selection axis

| 안 | 같은 remote의 다른 root | symlink/move 안정성 | 결론 |
|---|---|---|---|
| normalized Git remote/common-dir repository identity | 같은 repository를 한 account에 묶어 authoritative two-root policy와 충돌한다 | move 뒤 common-dir가 old root에 남아 잘못된 profile을 고를 수 있다 | 기각 |
| user-visible symlink surface path | 보이는 alias에 따라 account가 바뀐다 | symlink와 stale inherited `PWD`에 취약하다 | 기각 |
| `os.getcwd()`의 normalized real worktree path와 longest real ancestor mapping | 같은 remote라도 profile1/profile2 위치에 맞게 선택한다 | filesystem truth를 한 번 bind하고 ambiguity를 차단한다 | 선택 |

Git remote/common-dir는 selection signal에서 강등하여 선택 뒤 integrity verification에만 쓴다. `cd`, usage와 remote change는 이미 시작된 process를 재선택하지 않는다.

### D11. account root와 filesystem permission boundary

| 안 | cross-root metadata risk | 결론 |
|---|---|---|
| destination account root 전체를 write grant | 간단하지만 opposite profile의 unrelated worktree까지 노출한다 | 기각 |
| resolved worktree + exact verified common-dir만 grant | Git 2.55.0 probe의 external common-dir를 지원하면서 최소 범위를 유지한다 | 선택 |
| destination profile root의 separate clone+handoff | cross-root grant가 전혀 없지만 clone/handoff 비용이 있다 | operator가 exact common-dir access를 원하지 않을 때 선택 |

account root는 selection boundary로만 사용한다. exact common-dir조차 role need와 integrity verification을 통과하지 못하면 `blocked_permission`이며 whole-root fallback은 없다.

### D12. cross-profile move와 새 binding generation

cross-profile move를 rename이 아니라 explicit rebind/new execution generation으로 선택한다. Git 2.55.0 probe에서 live process의 `os.getcwd()`는 new path지만 inherited `PWD`는 old path로 남았으므로 provider, worker, watcher와 writer를 먼저 멈춘다. linked worktree move와 네 Git verification 뒤 path/profile/generation을 atomic update하고 새 process의 targets를 전부 재계산한다. Claude transcript가 config home 아래 absolute cwd로 keyed되므로 transparent `/resume`은 가정하지 않고 verified Git state와 in-repository handoff를 resume unit으로 삼는다. main/submodule case와 cross-root metadata grant를 원하지 않는 경우는 separate clone+handoff다.

### D13. neutral aliases와 legacy runtime protection

새 selectable aliases는 `codex-default`, `claude-profile1|claude-profile2`이고 reserved set 비교는 exact full-alias match라 `codex-default`를 허용한다. repository/Git identity/default의 exact reserved alias는 selection axis를 혼동한다. 현재 deployed `claude-dotfiles`와 `codex-dotfiles` record bytes는 opaque non-selectable legacy evidence로 보존되어 alias 규칙과 path/scope selector의 대상이 아니며 hot rename/rebind하지 않는다. 구현 검증 뒤 별도 migration generation에서 shutdown, handoff, 필요한 new-home official login/identity admission, atomic binding switch를 수행하며 각 legacy removal은 process와 binding reference가 모두 0인 경우에만 별도 승인 작업으로 허용한다.

### D14. common hook layer 복원과 turn-state 의미

account-home settings 복제 대신 reviewed common layer와 role layer를 composed single settings document로 공급한다. 이는 config-home 분리로 hooks가 사라져 active pane이 stale `done`에 남는 문제를 profile별 credential 복사 없이 해결한다. `PermissionRequest`는 Notification에 의존하지 않고 직접 `waiting`으로 전환하며 기존 Notification 두 case, working events와 Stop mapping도 유지한다. hook은 observability-only이고 `done`은 issue complete가 아니라 agent turn ended다.

<!-- strict-only:start -->

### Threat and trust boundaries

- 신뢰 입력은 reviewed `accounts.toml` real-directory mappings, role/Skill manifests, exact digest의 common/composed settings와 instruction bytes, manifest range 안의 help surface, canonical identity parser와 external lease issuer proof다.
- 비신뢰 입력은 explicit/stored binding 요청, issue text, symlink surface path, inherited `PWD`/env, Git remote/common-dir, writable project/account settings, provider raw output, tail args, plugin/MCP discovery, binding/lease file와 unknown path다. Git metadata는 account selector에는 비신뢰이며 selection 뒤 integrity evidence로만 제한적으로 사용한다.
- 민감 영역은 provider account home, credential/Keychain, raw identity/usage, transcript와 plugin state다. selected explicit config-home path는 reviewed registry/rendered target에서 private verifier/provider child environment로 이어지는 신뢰 경계 안에서만 허용되고 real deployed path와 그 파생 path는 strict public records, captured test artifacts, logs, diagnostics, error output와 운영 문서에 나오지 않는다. private child environment의 exact contract를 판정하는 synthetic fixture path assertion/capture만 이 real-path prohibition에서 제외한다. credential, raw identity/usage와 provider output은 verifier의 captured/redacted boundary 밖으로 전달되지 않는다.
- 주요 위협은 symlink/stale-PWD로 profile을 바꾸기, stored binding으로 allowed scope를 우회하기, opposite root 전체 grant, external common-dir 무시, mixed deployment, untrusted settings가 model/permission/hooks를 덮기, credential 복제로 hook을 복원하기, reviewer dispatch, duplicate global active, automatic first-use enrollment, legacy hot rename과 stale `done`이다.
- 통제는 normalized real longest-ancestor selection, stored-versus-derived/generation 검증, exact worktree/common-dir permission, strict schemas/digests/modes, exact scrub, policy pre-scan, deny-first capability, official verifier+shared parser, single-exec stdio, proof+lock, fake-workmux and no-mutation sentinels다.

### Authorization and tenant isolation

tenant는 account profile, current real workspace scope, task/direct-parent와 leader scope다. Codex의 initial automatic tenant는 `~/code/**`의 `codex-default` 하나이며 추가 Codex homes와 opaque legacy records는 declaration만으로 automatic 후보가 되지 않는다. 초기 정책의 Claude는 profile1 real root의 provider-default/unset tenant와 profile2 real root의 explicit-home tenant로 분리되고 outside-both-roots는 조건 없이 `blocked_contract`로 닫힌다. 별도 reviewed Spec과 registry source 개정으로 새 mapping을 launch 전에 배포하지 않는 한 running launcher가 이 경계를 완화하는 runtime 예외는 없다. explicit/stored profile도 current real path의 directory-only allowed scope와 derived mapping을 통과해야 하며 mismatch는 `blocked_binding`이다. remote·repository·organization 값은 admission을 결정하지 않는다.

role은 account를 선택하거나 home mode를 바꾸지 않고 account는 model/effort/permission/instruction/settings/Skill/leader capability를 바꾸지 않는다. 한 provider 환경에는 선택 home만 존재하며 반대 provider/profile home은 scrub된다. filesystem write authorization은 tenant root 전체가 아니라 resolved worktree+exact common-dir다. global active만 matching proof scope에서 dispatch하고 reviewer/standby는 read-only, no-dispatch, no-lease-write다. isolation matrix는 모든 role×Codex repositories, 모든 Claude role×profile1/profile2/outside root, same-remote different-root, explicit/stored mismatch, cross-parent, same/different leader scope, external common-dir와 reviewer sentinels를 포함하며 실패 시 다른 tenant로 fallback하지 않는다.

### Migration, compatibility, and rollback

source implementation은 v1 direct caller compatibility를 유지하는 `ai-session`, path-based registry contract, role/Skill manifest, common/composed settings, instruction/verifier/shared identity library, single-exec dispatcher, eight symlinks, tests와 운영 문서를 하나의 reviewed set으로 만든다. old/new binary-registry partial deployment는 양방향 `blocked_contract`다. source-to-target 확인은 fixture render만 사용하고 actual apply는 별도다. CLI compatibility는 manifest ranges와 installed help-only gate로 분리한다.

`claude-dotfiles`와 `codex-dotfiles` 원본 record bytes와 alias/home은 그대로 두되 active selection path는 제공하지 않는다. 새 selectable alias로의 전환은 implementation verification 이후 별도 migration generation에서 writers stop → handoff → 필요한 new home의 official login/identity admission 운영 검증 → atomic path/profile/new generation switch → 새 process 순으로 수행한다. in-use home rename, credential/transcript/plugin copy/symlink와 transparent resume는 없다. 각 legacy record 제거는 zero-process/zero-binding 뒤 별도 승인 작업이며 cross-profile worktree는 linked-only move+Git verification 또는 separate clone+handoff를 사용한다.

rollback trigger는 selector priority/path regression, role/account 결합, invalid home env, permission overgrant, external common-dir mishandling, stale binding/PWD acceptance, hook/effective-source regression, sensitive output, mixed deployment admission, duplicate active 또는 legacy mutation이다. rollback은 reviewed launcher/registry/settings source set을 함께 되돌려 raw provider entrypoint로 복귀하는 별도 source/deployment change이며 running process, credential/account/legacy homes와 Git state는 건드리지 않는다. `private_full_auto.config.toml`과 preserved paths는 byte-identical하게 남는다.

### Failure recovery and observability

관측 신호는 exact one-line binding/startup/failure JSON, stable exit/status, role/settings/instruction/Skill IDs와 hashes, leader scope/generation, positive `binding_generation`, Git verification result와 fake-workmux transition capture다. strict public records, captured test artifacts, logs, diagnostics와 error output에는 config-home path, identity/digest, raw provider output와 credential을 기록하지 않는다. 기능상 필요한 selected explicit path는 reviewed registry/rendered target과 private verifier/provider child environment에만 남는다. `blocked_contract|blocked_role_schema|blocked_policy|blocked_permission|blocked_cli_contract|blocked_binding`은 reviewed input/installation/path/generation을 고친 뒤 새 process로 복구하고 `blocked_leader_conflict`는 기존 owner/proof를 유지한 채 valid external proof 이후 재시도한다.

`not_logged_in|identity_drift|blocked_verifier|usage_unknown|blocked_usage`는 account fallback 없이 해당 official operator path에서만 복구한다. 특히 Claude `usage_unknown`은 relogin으로 해소된다고 가정하지 않고 official adapter가 별도 review될 때까지 차단한다. move failure는 old registry bytes와 Git/handoff state를 보존하고 partial generation을 publish하지 않는다. legacy nonzero references와 stale old-path reference는 migration을 멈춘다. workmux는 waiting/working/done을 모든 surface에 보여 주되 `done`은 agent-turn-end이고 authority나 issue completion signal이 아니다. 자동 retry와 telemetry 전송은 추가하지 않는다.

### High-risk end-to-end verification

E2E는 temp Git source/linked-worktree와 profile1/profile2 roots, separate synthetic Claude config homes, fake Codex/Claude help·status/provider, call-recording fake workmux, hostile/benign configs, strict lease proof, identity digest, PTY 및 capability/lock FD probe로 구성한다. network와 real provider/auth/enrollment/account-home/current-process 경계는 접근 즉시 실패하는 sentinel이다.

순서는 source fixture/render와 CLI range → real-path longest-ancestor/account-role matrix → same-remote different-root 및 outside-root block → home-mode/exact scrub → config/settings/instruction/Skill pre-scan → verifier/status/identity → public record/PTY/single-exec → leader race/reviewer deny → exact common-dir permission → shutdown/move/Git verification/atomic rebind/new handoff와 separate-clone alternative → legacy zero-reference gates → exact workmux event/surface transitions → sensitive/no-mutation checks다. provider child가 preflight failure 뒤 실행되거나 opposite-root whole grant, stale `PWD`/generation, scrub sentinel, credential/home copy, legacy mutation, current pane/session/process action 또는 stale active `done`이 하나라도 관측되면 즉시 실패한다. completion은 CMD-9~CMD-23을 포함한 표의 모든 applicable command exit 0과 capture assertions를 요구한다.

### No production mutation confirmation

자동 workflow는 production, 실제 provider account/credential/identity enrollment, 실제 account/legacy home, current tmux pane/session/window/process, 실제 worktree 이동과 registry target을 읽거나 변경하지 않는다. fake workmux와 move tests는 temp synthetic state만 사용한다. real login/logout/auth/status/usage, network/model probe, `chezmoi apply`, commit/push/PR/merge/deploy, deletion/Trash, lease generation 발급·갱신, credential/account-home/settings/transcript/plugin copy·sync·snapshot·rename·symlink는 수행하지 않는다. future explicit apply, actual cross-profile move, official login/identity admission과 legacy zero-reference removal은 이 automated workflow 밖의 별도 승인 운영 작업이다.

<!-- strict-only:end -->
