# Quality Goal Specification

- Task ID: 20260917T002844Z-111-프로필별-실경로-smoke의-기본-claude-설정-호환성-결함-f76eb54a
- Mode: strict
- Status: SPEC_REVIEW
- Created: 2026-09-17
- Updated: 2026-09-17
- Source goal: #111 프로필별 실경로 smoke의 기본 Claude 설정 호환성 결함(profile1 blocked_policy·profile2 enrollment_required)을 안전하게 해결한다

## Problem and context

직전 #111 실행과 draft PR #124의 산출물은 완료 상태이며 유지 대상이다. 후속 실경로 smoke에서 `~/code/profile1/111-account-profile-smoke`는 `claude-profile1`을 정상 선택했지만, `ai-session status --provider claude --role-profile general --accept-usage-unknown`이 `blocked_policy`와 exit 4를 반환했다. 같은 절차로 `~/code/profile2/111-account-profile-smoke`는 `claude-profile2`를 선택한 뒤 `enrollment_required`와 `identity_enroll_foreground`, exit 3을 반환했다. 전자는 실환경 결함이고 후자는 명시적 identity enrollment 전의 설계된 정상 상태다. 재현 전문은 `.claude/quality-state/20260917T002844Z-111-프로필별-실경로-smoke의-기본-claude-설정-호환성-결함-f76eb54a/evidence/repro-baseline.txt`에 있다.

결함의 직접 원인은 `dot_local/bin/executable_ai-session:104-108,995-1041`의 설정 prescan이다. `claude-profile1`은 `dot_config/ai-session/accounts.toml:18-26`에서 `config_home_mode = "provider_default"`이므로 사용자 본인의 `~/.claude`가 선택된다. 이 prescan의 `BENIGN_CLAUDE_SETTING_TYPES`는 `$schema`, `spinnerTipsEnabled`, `theme`만 허용한다. 아래 **실측 16개 키 fixture 계약**은 실제 설정 값을 제외하고 키 이름과 JSON 타입만 고정한다. 이 중 allowlist와 이름·타입이 모두 일치하는 키는 `theme`(string) 하나이며, 나머지 15개는 비허용 키다. `status`와 `launch`가 같은 prescan을 호출하므로 정상 사용자 설정을 가진 profile1은 첫 비허용 키에서 차단되어 admission에 도달할 수 없다.

| 키 | JSON 타입 |
|---|---|
| `env` | object |
| `permissions` | object |
| `model` | string |
| `hooks` | object |
| `statusLine` | object |
| `enabledPlugins` | object |
| `extraKnownMarketplaces` | object |
| `language` | string |
| `alwaysThinkingEnabled` | boolean |
| `effortLevel` | string |
| `modelSettings` | object |
| `skipWorkflowUsageWarning` | boolean |
| `theme` | string |
| `skipAutoPermissionPrompt` | boolean |
| `autoMode` | object |
| `mcpServers` | object |

prescan은 임의 완화 대상이 아니다. `dot_local/libexec/executable_ai-session-verify-claude:44-54`와 `dot_local/libexec/executable_ai-session-enroll-identity:122-140`의 비대화형 인증 조회는 현재 `claude auth status --json`을 설정 소스 차단 없이 실행한다. user/project/local settings의 `hooks`, `mcpServers`, `env`, `permissions`가 이 과정에 개입할 가능성을 fail-closed로 막기 위해 prescan이 존재한다. 한편 `dot_local/bin/executable_ai-role-session:1046-1060`이 만드는 실제 Claude role 명령은 이미 `--settings <검토된 합성 설정> --setting-sources ""`를 사용하지만, 같은 파일의 project/account-home prescan과 account launcher의 prescan이 그 명령보다 먼저 정상 사용자 설정을 차단한다.

설치된 Claude Code 2.1.274의 읽기 전용 probe에서 exact argv `claude --setting-sources '' --strict-mcp-config auth status --json`은 exit 0이었고, baseline `claude auth status --json`과 같은 JSON 키 집합을 반환했다. 실제 argv와 결과는 `.claude/quality-state/20260917T002844Z-111-프로필별-실경로-smoke의-기본-claude-설정-호환성-결함-f76eb54a/evidence/probe-argv.txt`에 있다. 다른 후보 플래그의 결과는 같은 evidence 디렉터리의 `probe-flags.txt`에 있다. 다만 `canonical_identity()`가 쓰는 `authMethod`, `subscriptionType`, UUID `orgId` 값의 동일성은 아직 증명되지 않았으므로 이 변경의 별도 읽기 전용 판정 항목으로 둔다.

저장소는 chezmoi source이며 지금은 `chezmoi apply`를 실행하지 않는다. 구현과 검증은 실행 권한이 없는 source를 `/opt/homebrew/bin/python3.14`로 직접 실행하고, 임시 home·`AI_SESSION_SYNTHETIC_TEST=1`·`AI_SESSION_IDENTITY_ROOT`를 이용해 실제 사용자 설정, identity 저장소, 실행 중 세션을 변경하지 않아야 한다. 기존 baseline은 `tests/test_ai_session.py` 29개와 `tests/test_orchestrator_profiles.py` 92개가 모두 통과한다.

## Goals

1. 정상적인 기본 `~/.claude` 설정을 가진 Mac에서도 `claude-profile1`의 `status`와 검토된 role `launch`가 설정 키 자체 때문에 `blocked_policy`로 차단되지 않게 한다.
2. verifier, 명시적 enrollment, role launch에서 실행되는 Claude 프로세스가 미검토 user/project/local settings의 `hooks`, `mcpServers`, `env`, `permissions`를 로드하거나 실행하지 못하게 코드로 강제한다.
3. baseline과 하드닝된 인증 조회가 canonical identity 입력값을 동일하게 제공함을 비밀 없는 읽기 전용 판정으로 확인한다.
4. `claude-profile2`의 사전 enrollment 상태를 유지하고, 사용자가 전경에서 명시적으로 enrollment한 뒤 `ready`에 도달하는 절차를 구현 회귀 테스트와 운영 문서로 증명한다.
5. 기존 121개 테스트를 보존하고, 호환성 완화와 보안 속성이 동시에 성립하는 회귀 테스트를 추가한다.

## Non-goals

- `claude-profile2`의 identity enrollment, 브라우저 로그인 또는 account 전환을 자동 실행하지 않는다. 이 동작은 사용자가 선택한 전경 절차다.
- `~/.claude` 또는 profile별 account home의 설정, credential, token, session, identity 파일을 수정·이동·복사·rename·symlink하지 않는다.
- `#118`이 소유한 create-worktree 작업 경로 생성 backend, resolver, TUI 흐름 또는 관련 경로를 변경하지 않는다.
- `claude-profile1`의 `config_home_mode = "provider_default"`와 profile별 workspace mapping을 변경하지 않는다.
- consumer 계정 간 자동 fallback, ranking, rotation, 사용량 기반 선택 또는 실행 중 account hot-swap을 도입하지 않는다.
- `BENIGN_CLAUDE_SETTING_TYPES`에 `hooks`, `mcpServers`, `env`, `permissions` 등의 위험 키를 추가해 통과시키지 않는다.
- Claude의 OAuth·Keychain 동작을 재구현하거나 `--bare`를 사용하지 않는다. `--bare`는 OAuth와 Keychain을 읽지 않아 consumer 로그인 판정 계약을 깨뜨린다.
- `chezmoi apply`, 실제 모델 호출, login/logout, git write 명령, commit/push, PR merge를 이 작업의 구현·판정 과정에서 실행하지 않는다.
- OAuth token, API key, 이메일, account ID 원문, orgId 원문, canonical identity 원문 또는 전체 digest를 저장소·문서·로그·테스트 fixture에 기록하지 않는다.
- 직전 실행의 `docs/development/2026-09-16-111-profile-onboarding/**` 산출물을 고치지 않는다.

## Requirements

- **R1.1** Claude verifier와 명시적 identity enrollment helper가 실행하는 모든 비대화형 공식 인증 조회는 exact argv `claude --setting-sources "" --strict-mcp-config auth status --json`을 이 순서 그대로 사용해야 한다. 기존 10초 timeout, captured stdout/stderr, `close_fds=True`, empty `pass_fds`, nonzero·timeout·malformed JSON fail-closed, redacted six-field verifier 출력 계약은 유지한다. raw stdout/stderr 또는 identity 원문은 출력하거나 저장하지 않는다. [근거: `dot_local/libexec/executable_ai-session-verify-claude:44-54`; `dot_local/libexec/executable_ai-session-enroll-identity:122-140`; `probe-argv.txt`]
- **R1.2** 검토된 Claude role launch의 최종 provider argv는 exact one `--setting-sources ""`와 `--strict-mcp-config`를 포함하고, digest 검증된 `--settings`만 추가 설정으로 허용해야 한다. 모든 Claude role의 `dot_config/ai-session/roles.toml` `cli_required_options`, `verify_provider_cli_contract()`의 Claude expected required list, `tests/check_installed_orchestrator_cli_contract.py`의 `EXPECTED_REQUIRED["claude"]`는 exact ordered list `--append-system-prompt`, `--settings`, `--plugin-dir`, `--setting-sources`, `--strict-mcp-config`로 일치해야 한다. 지원 범위 `>=2.1.269,<2.2.0` 안이라도 설치본의 help가 두 하드닝 플래그 중 하나를 광고하지 않으면 provider exec 전에 public `blocked_cli_contract`, exit 4로 닫아야 한다. caller가 `--settings`, `--setting-sources`, `--strict-mcp-config`, `--mcp-config`를 중복·재정의하거나 내부 admitted 명령을 위조하면 provider exec 전에 `blocked_policy` 또는 `blocked_contract`로 닫혀야 한다. [근거: `dot_local/bin/executable_ai-role-session:741-793,1004-1060,1271-1336`; `dot_config/ai-session/roles.toml`; `tests/check_installed_orchestrator_cli_contract.py`]
- **R1.3** 기존 prescan을 우회하는 조건은 실행될 Claude argv가 R1.1 또는 R1.2의 하드닝 계약을 충족한다고 그 argv를 만드는 실행 경계에서 코드로 강제하는 경우로 제한한다. `status` 경로는 `provider=claude`이고 기존 absolute regular non-symlink executable 검사를 통과한 trusted `--verifier` seam을 통해 호출될 때 `ai-session` 자체가 Claude argv를 만들지 않으므로 selected Claude home prescan을 수행하지 않으며, 그 verifier 내부가 R1.1 argv를 강제해야 한다. strict role launch와 admitted role exec에는 R1.2 조건을 적용하고, legacy·임의 provider command·향후 direct Claude 경로는 기존 prescan 또는 명시적 거부로 fail-closed한다. `--verifier`는 기존 trusted executable dependency-injection seam이며 adapter 자체를 비신뢰 코드로부터 sandbox하는 authorization interface가 아니다. allowlist 확장이나 provider-default home만의 무조건 제외는 허용하지 않는다. [근거: `dot_local/bin/executable_ai-session:995-1041,1221-1259,1515-1518,1557-1560`; `dot_local/bin/executable_ai-role-session:965-1017,1271-1336`]
- **R1.4** 설치된 Claude Code 2.1.274에서 baseline 인증 조회와 R1.1의 하드닝 조회는 `loggedIn`, `authMethod`, `subscriptionType`, UUID로 정규화한 `orgId` 값이 동일해야 한다. 비교는 메모리에서만 수행하고 safe boolean과 exit code만 노출한다. 값 불일치, 필드 누락, 타입 오류, UUID 오류는 판정 실패이며 identity를 `matched`나 `ready`로 승격하지 않는다. fixture에서도 두 경로의 canonical digest와 verifier 상태가 동일함을 확인한다. [근거: `dot_local/libexec/ai_session_identity.py:31-53`; `probe-flags.txt`]
- **R2.1** Problem and context의 **실측 16개 키 fixture 계약**과 정확히 같은 키 이름·JSON 타입을 가진 임시 `CLAUDE_CONFIG_DIR/settings.json` 아래에서, 유효한 합성 로그인·identity·usage 입력을 받은 `claude-profile1` source `status`는 `--accept-usage-unknown`과 함께 `ready`, exit 0을 반환해야 한다. fixture에는 실제 사용자 설정 값을 복사하지 않는다. 설정 내용 때문에 `blocked_policy`가 되지 않아야 하며 실제 사용자 home이나 identity root를 읽거나 쓰지 않는다. [근거: `repro-baseline.txt`; `dot_config/ai-session/accounts.toml:18-26`]
- **R2.2** 같은 격리 fixture에서 검토된 `claude-profile1` role launch는 account admission과 role dispatch를 통과해 fake provider를 정확히 한 번 실행해야 한다. 최종 argv는 R1.2를 만족하고 sentinel hook·MCP·env 주입은 발생하지 않으며, 실제 Claude 모델, login, tmux, chezmoi를 호출하지 않는다. [근거: `dot_local/bin/executable_ai-session:1501-1544`; `dot_local/bin/executable_ai-role-session:1386-1480`]
- **R2.3** `claude-profile2`는 enrollment file이 없는 격리 fixture에서 계속 `enrollment_required`, `identity_status="not_enrolled"`, `identity_enroll_foreground`, exit 3을 반환해야 한다. 사용자가 전경에서 `executable_ai-session-enroll-identity`를 한 번 명시적으로 실행하면 host-local 임시 identity root에만 v2 digest가 생성되고, 새 `status --accept-usage-unknown` 호출은 `ready`, exit 0이 되어야 한다. backend가 helper를 자동 호출하거나 다른 profile의 설정·credential·identity를 복사하면 안 된다. [근거: `repro-baseline.txt`; `dot_local/libexec/executable_ai-session-enroll-identity:213-273`]
- **R3.1** 보안 회귀 fixture는 임시 Claude home의 `settings.json`에 sentinel을 쓰는 hook과 `mcpServers`, `env`, `permissions`를 넣어야 한다. 같은 fake Claude를 하드닝 플래그 없이 호출하는 negative control은 sentinel을 생성하고, R1.1·R1.2 경로는 sentinel·MCP child·주입 env를 모두 생성하지 않아야 한다. negative control과 production path는 실제 사용자 home과 네트워크를 사용하지 않는다. [근거: `dot_local/bin/executable_ai-session:995-1041`; `dot_local/bin/executable_ai-role-session:965-1002`]
- **R3.2** 기존 `tests/test_ai_session.py` 29개와 `tests/test_orchestrator_profiles.py` 92개가 `/opt/homebrew/bin/python3.14`에서 계속 통과해야 하며, verifier·enrollment argv, profile1 status·launch, profile2 enrollment lifecycle, sentinel negative control, 미하드닝 fail-closed, CLI required-option 계약, 문서 계약, live identity projection에 대한 회귀 테스트를 추가한다. 기본 격리 테스트는 `AI_SESSION_SYNTHETIC_TEST=1`, `AI_SESSION_IDENTITY_ROOT`, 임시 디렉터리와 fake executable을 사용하고 실제 사용자 설정·identity·세션을 변경하지 않는다. 단, enrollment argv 회귀는 `AI_SESSION_SYNTHETIC_TEST`와 `AI_SESSION_SYNTHETIC_STATUS_JSON`을 unset한 subprocess 분기를 사용하고 PATH 선두에 주입한 fake `claude`를 실제로 한 번 실행해 argv를 캡처한다. live projection 한 건만 명시적 opt-in으로 실제 `claude auth status --json`을 읽기 전용 호출하며 값은 출력·저장하지 않는다.
- **R3.3** `docs/session-account-profiles.md`와 `docs/orchestrator-permission-profiles.md`는 설정 격리 계약, profile1 호환성, profile2의 `status → 전경 enrollment helper → 새 status → ready` exact 명령·status·exit·사용자 확인·복구 경계를 문서화해야 한다. 변경 범위는 `dot_local/bin/executable_ai-session`, `dot_local/bin/executable_ai-role-session`, `dot_local/libexec/executable_ai-session-verify-claude`, `dot_local/libexec/executable_ai-session-enroll-identity`, `dot_config/ai-session/roles.toml`, `tests/test_ai_session.py`, `tests/test_orchestrator_profiles.py`, `tests/check_installed_orchestrator_cli_contract.py`, `docs/session-account-profiles.md`, `docs/orchestrator-permission-profiles.md`로 제한하며 `accounts.toml`의 provider-default 설계, `#118` 소유 경로, credential·identity 원문은 변경하지 않는다.

## Acceptance criteria

- **AC-1** fake `claude`가 기록한 verifier argv가 exact `claude --setting-sources "" --strict-mcp-config auth status --json`이고 호출 횟수가 1이며, timeout·FD·redaction 계약이 유지된다. [실행] (CMD-2 `test_settings_compat_verifier_argv`)
- **AC-2** explicit enrollment helper는 `AI_SESSION_SYNTHETIC_TEST`와 `AI_SESSION_SYNTHETIC_STATUS_JSON`을 unset해 합성 status 분기를 사용하지 않고, PATH 선두의 fake `claude` subprocess를 실제로 한 번 실행해 AC-1과 같은 exact 인증 조회 argv를 캡처하며 합성 identity root 밖에 파일을 만들지 않는다. [실행] (CMD-2 `test_settings_compat_enrollment_argv`)
- **AC-3** 네 Claude role의 생성 argv가 exact one `--setting-sources ""`, exact one `--strict-mcp-config`, 검토된 `--settings`를 가지며 caller override와 forged admitted argv는 provider 실행 전에 거부된다. [실행] (CMD-2 `test_settings_compat_role_launch_argv`)
- **AC-4** 하드닝 계약이 없거나 중복·오염된 argv를 가진 legacy·임의 launch fixture는 기존 위험 settings 아래에서 child 실행 없이 fail-closed하고, `BENIGN_CLAUDE_SETTING_TYPES`에 위험 키가 추가되지 않는다. [실행] (CMD-1 `test_settings_compat_unhardened_route_fail_closed`)
- **AC-5** opt-in live probe가 baseline `claude auth status --json`과 exact-order 하드닝 argv `claude --setting-sources "" --strict-mcp-config auth status --json`을 각각 실행하고 canonical 네 필드를 메모리에서 비교해 동일할 때만 exit 0을 반환하며 unittest 출력에 필드 값, 이메일, orgId, digest가 나타나지 않는다. [실행] (CMD-4 `test_settings_compat_live_identity_projection`)
- **AC-6** 임시 provider-default home의 `settings.json`이 Problem and context의 실측 16개 키 fixture 계약과 키 집합·각 JSON 타입이 정확히 같아도 profile1 `status --accept-usage-unknown`은 합성 matched identity에서 `ready`, exit 0이고 `blocked_policy`가 아니다. [실행] (CMD-1 `test_settings_compat_profile1_status`)
- **AC-7** Problem and context의 실측 16개 키 fixture 계약과 키 집합·각 JSON 타입이 정확히 같은 `settings.json`을 사용하는 strict profile1 role launch는 fake Claude를 정확히 한 번 실행하고 최종 argv가 하드닝 계약을 만족하며 `blocked_policy`를 내지 않는다. [실행] (CMD-2 `test_settings_compat_profile1_launch_e2e`)
- **AC-8** 격리된 profile2 lifecycle은 첫 status에서 `enrollment_required`/exit 3, 명시적 helper에서 `enrolled`/exit 0, 두 번째 status에서 `ready`/exit 0을 순서대로 보이고 helper 자동 호출과 profile 간 파일 복사가 0회다. [실행] (CMD-2 `test_settings_compat_profile2_enrollment_to_ready`)
- **AC-9** 두 운영 문서의 profile2 절은 다음 항목을 문자 단위로 동일하게 포함한다: exact status 명령 `ai-session status --provider claude --role-profile general --accept-usage-unknown`, exact helper 명령 `ai-session-enroll-identity --registry "${HOME}/.config/ai-session/accounts.toml" --provider claude --account-profile claude-profile2`, 순서 `status → 사용자 확인 → helper → 새 status`, 결과 `enrollment_required`/exit 3 → `enrolled`/exit 0 → `ready`/exit 0, 경계 문구 `backend는 login·enrollment·fallback·profile 간 설정/credential/identity 복사를 자동 실행하지 않는다.` 두 파일에는 이 profile2 운영 계약 block이 byte-identical해야 한다. [문서] docs/session-account-profiles.md docs/orchestrator-permission-profiles.md
- **AC-10** sentinel fixture의 unhardened negative control은 sentinel을 생성하지만 hardened verifier와 enrollment 경로는 sentinel, MCP child, 설정 기반 env capture를 하나도 생성하지 않는다. [실행] (CMD-2 `test_settings_compat_auth_status_sentinel`)
- **AC-11** strict role launch의 hardened provider 경로도 같은 sentinel, MCP child, 설정 기반 env capture를 하나도 생성하지 않고 fake provider의 정상 capture만 생성한다. [실행] (CMD-2 `test_settings_compat_role_launch_sentinel`)
- **AC-12** 이번 변경에 추가된 모든 `test_settings_compat_*` 회귀 테스트가 실제 사용자 home·identity root·네트워크·모델을 사용하지 않는 기본 모드에서 통과한다. [실행] (CMD-1 및 CMD-2 `test_settings_compat_`)
- **AC-13** `tests/test_ai_session.py` 전체가 기존 29개를 포함해 failure/error 없이 통과한다. [실행] (CMD-3 `tests/test_ai_session.py`)
- **AC-14** `tests/test_orchestrator_profiles.py` 전체가 기존 92개를 포함해 failure/error 없이 통과하며 live probe는 opt-in이 없으면 외부 CLI를 호출하지 않는다. [실행] (CMD-5 `tests/test_orchestrator_profiles.py`)
- **AC-15** 회귀 검사가 R3.3의 exact 변경 범위에 `dot_config/ai-session/roles.toml`과 `tests/check_installed_orchestrator_cli_contract.py`를 포함해 허용하고 그 밖의 파일 변경을 거부하며, `accounts.toml`의 profile1 provider-default와 profile2 explicit home, `#118` 소유 경로, 직전 완료 산출물, 실제 credential/settings/identity가 보존되고 secret·identity 원문이 diff나 출력에 없음을 확인한다. [실행] (CMD-2 `test_settings_compat_scope_and_secret_hygiene`)
- **AC-16** 하나의 교차 회귀 시나리오에서 Problem and context의 실측 16개 키 fixture 계약과 키 집합·각 JSON 타입이 정확히 같고 위험 키가 있는 settings를 그대로 둔 채 profile1 status와 role launch가 성공하며, 동시에 verifier·enrollment·role provider 어느 경로에서도 sentinel hook·MCP·env 주입이 발생하지 않아 호환성 목표와 보안 속성이 함께 성립한다. [실행] (CMD-2 `test_settings_compat_cross_regression`)
- **AC-17** 모든 Claude role manifest, `verify_provider_cli_contract()`, 설치 계약 checker의 required-option 목록이 R1.2의 exact ordered list로 일치하고, 지원 범위 안의 fake Claude help에서 `--setting-sources` 또는 `--strict-mcp-config` 하나를 각각 제거한 두 경우 모두 provider 호출 0회, public `blocked_cli_contract`, exit 4가 된다. [실행] (CMD-2 `test_settings_compat_claude_required_options`)
- **AC-18** 두 운영 문서의 byte-identical 설정 격리 block이 exact 문구 `profile1 provider-default 설정은 보존한다.`와 `verifier·enrollment·role provider는 --setting-sources "" --strict-mcp-config로 user/project/local settings와 비검토 MCP를 로드하지 않는다.`를 포함하고, AC-9의 profile2 block까지 모두 존재함을 회귀 검사가 확인한다. [실행] (CMD-2 `test_settings_compat_documentation_contract`)

## Requirements traceability

This table maps every requirement to acceptance criteria and the judgement method that proves the mapping.

| Requirement | Acceptance criteria | Judgement method |
|---|---|---|
| R1.1 | AC-1, AC-2 | CMD-2의 exact argv·호출 횟수·redaction 회귀 |
| R1.2 | AC-3, AC-17 | CMD-2의 role별 최종 argv·override/forgery 거부와 CLI required-option fail-closed 회귀 |
| R1.3 | AC-4, AC-16 | CMD-1의 미하드닝 fail-closed와 CMD-2의 교차 회귀 |
| R1.4 | AC-5 | CMD-4의 opt-in 읽기 전용 live projection 비교 |
| R2.1 | AC-6 | CMD-1의 격리된 profile1 status 회귀 |
| R2.2 | AC-7 | CMD-2의 격리된 strict role launch E2E |
| R2.3 | AC-8, AC-9 | CMD-2의 합성 lifecycle과 두 운영 문서의 exact profile2 block 점검 |
| R3.1 | AC-10, AC-11 | CMD-2의 negative control 및 status/enrollment/launch sentinel 검사 |
| R3.2 | AC-12, AC-13, AC-14 | CMD-1·CMD-2 targeted 회귀와 CMD-3·CMD-5 전체 suite |
| R3.3 | AC-9, AC-15, AC-18 | CMD-2의 scope·secret hygiene·문서 byte 동일성 회귀와 exact profile2 문서 판정 |

## Architecture

권고 구조는 설정 파일의 내용을 신뢰 판정하는 대신, **실행되는 Claude 프로세스의 설정 입력면을 닫는 것**을 신뢰 경계로 삼는다.

1. `executable_ai-session-verify-claude`와 `executable_ai-session-enroll-identity`는 같은 비대화형 인증 조회 argv를 사용한다. `--setting-sources ""`가 user/project/local settings source를 끄고 `--strict-mcp-config`가 다른 MCP 구성을 배제한다.
2. `executable_ai-role-session`은 digest 검증된 합성 `--settings`를 명시적으로 공급하면서 user/project/local source와 비검토 MCP를 차단한다. `roles.toml`, 런타임 expected list, 설치 계약 checker는 두 차단 option을 동일한 required-option 목록으로 선언하고, 런타임 help probe가 미광고 option을 provider exec 전에 차단한다. model, effort, reviewed plugins, append prompt, permission/sandbox 합성 검증은 기존 계약대로 유지한다.
3. `executable_ai-session`과 role launch의 admitted 경계는 “profile1인가” 또는 “provider-default인가”로 prescan을 건너뛰지 않는다. trusted verifier adapter는 자기 subprocess argv를 R1.1로 고정하고, strict role path는 provider argv를 R1.2로 생성·재검증한다. 그 보장을 갖지 않는 legacy·임의 provider 경로는 기존 prescan 또는 명시적 거부를 유지한다.
4. admission, identity digest, usage dual consent, status schema와 exit code는 변경하지 않는다. 설정 로딩 차단은 admission 앞의 실행 안전성이고, identity·usage 판정은 그 뒤의 기존 계정 안전성이다.

관련 책임은 다음과 같다.

| Component | Responsibility |
|---|---|
| `dot_local/libexec/executable_ai-session-verify-claude` | 하드닝된 공식 auth status 실행, redacted six-field adapter |
| `dot_local/libexec/executable_ai-session-enroll-identity` | 사용자 전경 명시 호출에서 같은 하드닝 조회 후 host-local digest 기록 |
| `dot_local/bin/executable_ai-role-session` | 검토된 합성 settings와 차단 플래그를 가진 최종 Claude argv 생성·검증 |
| `dot_local/bin/executable_ai-session` | account 선택, 하드닝된 경로 판별, prescan fallback, admission과 status/launch 결과 |
| `dot_config/ai-session/roles.toml` | 모든 Claude role의 지원 CLI 범위와 required-option 계약 |
| `tests/test_ai_session.py` | account launcher의 compatibility·fail-closed 단위 계약 |
| `tests/test_orchestrator_profiles.py` | verifier/enrollment/role argv, sentinel, profile lifecycle, source E2E |
| `tests/check_installed_orchestrator_cli_contract.py` | 설치본 help와 manifest required-option 계약의 동기화 검사 |

## Interfaces and data flow

`status` 흐름은 `real cwd → account selection → child environment → hardened verifier → canonical identity 비교 → usage/cost admission → profile_status JSON`이다. 기존 `--verifier` 인자는 trusted executable을 주입하는 seam으로 유지하며, production Claude adapter가 자기 subprocess argv를 exact 하드닝 계약으로 고정하기 때문에 prescan을 대체한다. 로컬 공격자가 임의 verifier executable을 제공하는 경우는 기존 단일 사용자 CLI의 신뢰 경계 밖이며 새 authorization 문제로 확장하지 않는다. `status`는 registry, settings, identity, account home, worktree, tmux를 쓰지 않는다.

`launch` 흐름은 `role entrypoint → reviewed role policy/settings 검증 → hardened provider argv 생성 → ai-session account selection/admission → admitted role boundary에서 hardened argv 재확인 → Claude exec`이다. account launcher와 admitted role boundary 중 어느 한쪽에서도 하드닝을 확인할 수 없으면 exec하지 않는다. 사용자 settings의 존재나 키 집합은 최종 argv에 포함되지 않는다.

profile2의 전경 흐름은 `status(enrollment_required) → 사용자가 descriptor 확인 → ai-session-enroll-identity 명시 실행 → hardened auth status → v2 digest atomic write → 새 status(ready)`다. enrollment helper만 승인된 identity root에 쓰며 status와 launch는 enrollment를 생성·갱신하지 않는다.

verifier의 public stdout은 기존 exact fields `provider`, `account_profile`, `login_status`, `identity_status`, `usage_status`, `cost_limit_status`인 compact JSON 한 줄이다. status stdout과 launch stderr record도 기존 schema를 유지한다. raw Claude JSON은 subprocess 메모리 밖으로 전달하지 않고 canonical identity는 `authMethod`, normalized UUID `orgId`, `subscriptionType`만 사용한다.

## Failure behavior

- 하드닝 argv가 누락·중복·재정의되거나 trusted role structure와 맞지 않으면 Claude child를 시작하지 않고 `blocked_policy` 또는 `blocked_contract`로 닫는다.
- 설치된 Claude가 지원 버전 범위 안이어도 help에서 `--setting-sources`나 `--strict-mcp-config`를 광고하지 않으면 role launcher는 provider를 시작하지 않고 public `blocked_cli_contract`, exit 4로 닫는다.
- hardened `auth status`가 nonzero, timeout, malformed JSON, 필드 타입 오류를 내면 verifier는 raw output 없이 `unknown`/`identity_unverifiable`을 반환하고 기존 admission이 `blocked_verifier` 계열로 처리한다.
- live identity projection 값이 baseline과 다르면 배포 판정은 즉시 실패한다. 값을 로그로 진단하지 않고 필드 이름과 mismatch boolean만 허용한다.
- profile1에서 설정 키 때문에 `blocked_policy`가 재발하면 compatibility 실패다. 이를 해결하기 위해 allowlist를 넓히지 않고 최종 argv 하드닝과 route 판별을 수정한다.
- profile2의 `enrollment_required`는 오류가 아니다. helper 실패·중복 mapping·identity 불일치는 각각 기존 `blocked_verifier`·`duplicate_mapping`·`identity_drift` 계약을 유지하며 자동 재시도나 overwrite를 하지 않는다.
- sentinel, MCP child 또는 설정 기반 env capture가 하나라도 생기면 보안 판정 실패이며 이후 status/launch 성공 여부와 관계없이 중단한다.

## Security and risk

가장 큰 위험은 compatibility를 위해 provider-default home을 신뢰하거나 allowlist를 넓혀 위험 설정을 실제 Claude process에 노출하는 것이다. 이 Spec은 파일 내용의 “정상성” 대신 process argv의 설정 source 차단을 강제한다. `hooks`, `mcpServers`, `env`, `permissions`는 정상 사용자 설정일 수 있지만 verifier와 검토된 role launch에는 untrusted input이다.

두 번째 위험은 플래그 존재만 검사하고 뒤쪽 duplicate option이나 내부 admitted argv 위조로 재정의하는 것이다. 따라서 exact one, 값, 순서, 허용된 추가 설정 source, caller override 거부를 함께 판정한다. `--strict-mcp-config`는 `--setting-sources ""`와 함께 쓰며 한쪽만으로 하드닝 계약을 충족했다고 보지 않는다.

세 번째 위험은 하드닝된 auth status가 다른 identity 값을 반환하는 것이다. 키 집합 동일성만으로 충분하지 않으므로 실제 설치본의 canonical projection 값 동일성을 메모리에서 비교한다. 비교 출력은 boolean과 exit만 허용해 이메일·orgId·digest 유출을 막는다.

실제 사용자 home과 identity 저장소는 테스트의 신뢰 대상도 fixture도 아니다. 기본 회귀는 임시 디렉터리와 fake executable만 사용한다. opt-in live probe는 두 auth status 명령을 읽기 전용으로 실행할 뿐 login, enrollment, settings write, model call을 하지 않는다.

## Test strategy

테스트는 먼저 fake Claude가 argv를 캡처하고, 하드닝 플래그가 없을 때만 임시 settings의 hook을 실행하는 negative-control fixture를 만든다. 이 fixture로 verifier, enrollment helper, strict role launch의 최종 경계를 검사한다. profile1과 profile2 E2E는 임시 registry/home/identity root와 합성 auth JSON만 사용한다. 결함 주입 시 테스트가 실제로 실패함을 negative control로 보인 뒤 production path의 sentinel 부재를 판정한다.

### 판정 명령 표

| ID | 명령 | 통과 조건 |
|---|---|---|
| CMD-1 | `/opt/homebrew/bin/python3.14 -m unittest tests.test_ai_session.AiSessionCliTests.test_settings_compat_unhardened_route_fail_closed tests.test_ai_session.AiSessionCliTests.test_settings_compat_profile1_status` | 명시된 account launcher compatibility·미하드닝 fail-closed 테스트 2개가 모두 실행·통과하고 실제 home·network·provider 호출이 0회다. |
| CMD-2 | `/opt/homebrew/bin/python3.14 -m unittest tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_verifier_argv tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_enrollment_argv tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_role_launch_argv tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_profile1_launch_e2e tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_profile2_enrollment_to_ready tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_auth_status_sentinel tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_role_launch_sentinel tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_scope_and_secret_hygiene tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_cross_regression tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_claude_required_options tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_documentation_contract` | 명시된 verifier·enrollment·role launch·profile lifecycle·sentinel·scope/secret·CLI option·문서 교차 회귀 11개가 모두 실행·통과한다. |
| CMD-3 | `/opt/homebrew/bin/python3.14 tests/test_ai_session.py` | 기존 29개를 포함한 전체 suite가 failure/error 없이 exit 0이다. |
| CMD-4 | `AI_SESSION_LIVE_CLAUDE_AUTH_PROBE=1 /opt/homebrew/bin/python3.14 -m unittest tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_live_identity_projection` | baseline argv가 exact `claude auth status --json`, hardened argv가 exact `claude --setting-sources "" --strict-mcp-config auth status --json` 순서로 실행되고, canonical projection 값이 같으며 출력에 값이 노출되지 않고 exit 0이다. |
| CMD-5 | `/opt/homebrew/bin/python3.14 tests/test_orchestrator_profiles.py` | 기존 92개를 포함한 전체 suite가 failure/error 없이 exit 0이고 opt-in live probe는 skip된다. |

CMD-1, CMD-2, CMD-3, CMD-5는 source tree만 실행하고 실제 `~/.claude`, `~/.local/share/ai-account-profiles`, 실행 중 세션을 변경하지 않는다. CMD-4만 설치된 `claude` CLI를 읽기 전용으로 두 번 호출하며 stdout을 파일에 저장하거나 값으로 출력하지 않는다. 어떤 명령도 model prompt, login/logout, enrollment write, chezmoi, tmux, git write를 실행하지 않는다.

교차 회귀는 compatibility와 security를 따로 성공시키는 데 그치지 않는다. 같은 위험 settings fixture에서 status/launch 성공과 sentinel·MCP·env 주입 부재를 한 테스트가 함께 assert해야 한다. 전체 suite는 기존 상태·exit·redaction·no-fallback·identity isolation 계약의 회귀를 담당한다.

## Decisions

### D1. 호출 자체에서 설정 source를 차단하고 확인된 경로만 prescan에서 제외한다

대안 A를 채택한다. verifier뿐 아니라 같은 공식 auth status를 호출하는 enrollment helper에도 `--setting-sources "" --strict-mcp-config`를 적용하고, role launcher의 기존 `--setting-sources ""`에는 `--strict-mcp-config`와 exact-argv 검증을 더한다. prescan은 삭제하는 일반 규칙이 아니라 하드닝이 같은 exec 경계에서 증명된 경로에만 좁힌다. 이 방식은 정상 사용자 settings를 보존하면서 실행 프로세스가 그 settings를 입력으로 받지 않는 속성을 fixture와 최종 argv로 증명할 수 있다.

### D2. provider-default home만 prescan에서 제외하지 않는다

대안 B는 채택하지 않는다. 사용자 본인의 `~/.claude`도 검증 프로세스 관점에서는 untrusted이고 `hooks`, `mcpServers`, `env`, `permissions`를 포함할 수 있다. 반대로 explicit profile home에도 같은 위험 키가 있을 수 있으므로 home mode는 보안 신뢰도를 나타내지 않는다. 경계는 home 종류가 아니라 실제 child argv의 source 차단 여부다.

### D3. 설정 allowlist를 확장하지 않는다

대안 C는 채택하지 않는다. 위험 키를 allowlist에 넣으면 verifier와 launch가 그 값을 로드할 가능성을 그대로 둔 채 검사만 통과하므로 목표 2와 정면으로 충돌한다. 정상 사용자 설정의 호환성은 파일을 benign으로 선언해서가 아니라 그 파일을 해당 process가 읽지 않게 해서 해결한다.

### D4. `--safe-mode`, `--restricted`, `--bare`는 주 계약으로 사용하지 않는다

`--safe-mode`와 `--restricted`는 auth status probe에는 동작했지만 role session의 plugin, instruction, tool, permission 동작까지 넓게 바꾼다. `--bare`는 OAuth와 Keychain을 읽지 않아 consumer identity 계약을 깨뜨린다. 필요한 경계에 직접 대응하는 `--setting-sources "" --strict-mcp-config`를 공통 계약으로 선택하고, reviewed `--settings`와 plugin/instruction 정책은 유지한다.

### D5. profile2 enrollment는 사용자 전경의 명시적 단계로 유지한다

`enrollment_required`와 `identity_enroll_foreground`는 setup backend가 실행할 명령이 아니라 사용자에게 제공하는 descriptor다. 문서는 exact helper 명령과 재검증 순서를 제공하되 자동 실행·browser interaction·account fallback을 추가하지 않는다.

### D6. 하드닝 플래그를 Claude CLI required-option 계약에 편입한다

SPEC-003의 선택지 (a)를 채택한다. 지원 버전 범위를 좁히거나 미광고 option을 provider exec 실패까지 미루는 대신, 모든 Claude role manifest와 `verify_provider_cli_contract()` 및 설치 계약 checker의 required-option 목록에 `--setting-sources`, `--strict-mcp-config`를 추가한다. 이 방식은 범위 안의 어떤 설치본이라도 실제 help 광고를 런타임에 확인하며, 하나라도 없으면 관측 가능한 `blocked_cli_contract`/exit 4와 provider 실행 0회로 닫는다. 현재 2.1.274의 exact argv 성공은 `probe-argv.txt`와 CMD-4로 별도 확인한다.

<!-- strict-only:start -->

This block is required only for strict work. Any inapplicable subsection must be removed for non-strict work; within strict work, mark it as not applicable with a reason before review.

### Threat and trust boundaries

신뢰되는 입력은 Git에서 검토된 registry, role manifest, Claude verifier/enrollment adapter, digest 검증된 합성 settings/instruction/plugin, trusted caller가 `--verifier`로 주입한 executable, Claude Code 2.1.274의 광고된 CLI option, exact argv builder와 validator다. untrusted 입력은 user/project/local settings, caller provider arguments, verifier/provider stdout·stderr, account home, current auth state와 enrollment 전 identity다.

주요 위협은 settings hook 명령 실행, MCP server 기동, env/permission 주입, duplicate option으로 하드닝 무효화, forged admitted command, raw auth JSON 유출, 다른 profile identity overwrite다. 통제는 source 차단 플래그 두 개, exact-one argv 검증, caller override 거부, 미확인 경로의 prescan/fail-closed, captured/redacted adapter, explicit-only enrollment, 임시 fixture와 sentinel negative control이다.

trust boundary는 세 곳이다. 첫째 verifier/enrollment helper가 Claude CLI를 exec하는 지점, 둘째 role launcher가 provider argv를 만드는 지점, 셋째 admitted role process가 최종 Claude를 exec하는 지점이다. 각 경계가 독립적으로 하드닝을 확인하며 앞 단계의 환경 flag 하나만 신뢰하지 않는다.

### Authorization and tenant isolation

account authorization은 기존 directory mapping과 binding generation을 그대로 사용한다. `~/code/profile1`은 `claude-profile1`, `~/code/profile2`는 `claude-profile2`에만 매핑되며 이 변경은 선택 우선순위나 scope를 바꾸지 않는다. profile1의 provider-default와 profile2의 explicit home은 서로 복사·symlink하지 않는다.

identity enrollment write 권한은 사용자가 명시적으로 호출한 helper와 선택된 profile의 host-local digest 경로에만 있다. status와 launch에는 enrollment write 권한이 없고, profile2 enrollment가 profile1 digest 또는 account home을 쓰는 테스트는 실패해야 한다. 동일 조직 컨텍스트 duplicate mapping, identity drift와 usage dual-consent는 기존 fail-closed admission을 유지한다.

실제 OS multi-tenant authorization 변경은 해당 없음이다. 이 저장소의 tenant 경계는 로컬 account profile과 그 credential/identity home이며, 새 네트워크 service·사용자 role·ACL을 만들지 않기 때문이다.

### Migration, compatibility, and rollback

registry schema, enrollment file schema, status JSON, launch record, account alias와 home layout은 바뀌지 않으므로 data migration이나 backfill은 없다. 모든 Claude role manifest, 런타임 expected list, 설치 계약 checker에 두 차단 option을 required로 함께 배포하고 Claude Code 2.1.274에서 exact argv와 canonical projection 동일성을 확인한 뒤 적용한다. 지원 범위 안이라도 설치 CLI가 option을 광고하지 않으면 런타임 help probe가 provider exec 전에 `blocked_cli_contract`/exit 4로 닫고, live projection이 다르면 배포하지 않는다.

rollback trigger는 live projection 불일치, sentinel 생성, duplicate option 우회, 기존 121개 회귀, profile2 lifecycle 실패다. rollback은 코드와 문서 변경을 되돌리고 rollout을 중단하는 것이며 사용자 settings·credential·identity를 변경하지 않는다. allowlist 확장으로 rollback하거나 하드닝 없이 prescan만 제거하는 상태는 허용하지 않는다. enrollment file format이 변하지 않아 rollback 시 data 변환은 없다.

### Failure recovery and observability

운영자는 public status와 exit code로 복구한다. profile1의 예상 성공은 `ready`/0이고, profile2의 미등록 정상 상태는 `enrollment_required`/3과 `identity_enroll_foreground`다. CLI required option 미광고는 `blocked_cli_contract`/4, argv 구조 하드닝 계약 오류는 `blocked_policy|blocked_contract`, auth schema 오류는 `blocked_verifier|identity_unverifiable`, 기존 identity·usage 오류는 기존 상태를 유지한다.

새 persistent metric·trace·alert backend는 해당 없음이다. 로컬 CLI/chezmoi 저장소이고 외부 운영 service가 없기 때문이다. 대신 판정 신호는 exact argv capture, child call count, sentinel/MCP/env capture 부재, compact public JSON, unittest exit다. 로그에는 profile alias, public status, safe boolean만 허용하고 raw stdout/stderr, email, orgId, account ID, digest, private home path를 넣지 않는다.

### High-risk end-to-end verification

고위험 경로는 위험 settings가 존재하는 provider-default profile1에서 status와 strict role launch를 수행하는 격리 E2E다. CMD-2의 negative control이 먼저 sentinel을 생성해 fixture의 결함 탐지 능력을 증명해야 한다. 이어 같은 settings를 바꾸지 않은 production path에서 status ready, provider 1회 exec, exact 하드닝 argv, sentinel·MCP child·env capture 0개를 동시에 확인한다. profile2는 별도 lifecycle에서 enrollment 전/명시 helper/재상태의 세 단계를 확인한다.

CMD-4는 실제 설치본에서 canonical projection 동일성을 읽기 전용으로 확인한다. 중단 조건은 projection mismatch, raw 값 출력, sentinel 생성, provider 중복 실행, `blocked_policy` 재발, 자동 enrollment, 실제 사용자 파일 변경, 기존 suite 실패 중 하나다. 모든 조건이 통과하기 전에는 high-risk verification을 PASS로 기록하지 않는다.

### No production mutation confirmation

자동 workflow에는 production mutation이 없다. `chezmoi apply`, 실제 login/logout, 브라우저 OAuth, identity enrollment, 모델 호출, tmux/session 조작, git write, commit/push/merge를 실행하지 않는다. 합성 enrollment는 임시 `AI_SESSION_IDENTITY_ROOT`에만 기록하고 종료 후 폐기한다. 유일한 live 동작인 CMD-4는 `claude auth status --json` 두 조합의 읽기 전용 메모리 비교이며 출력 값이나 파일을 남기지 않는다.

<!-- strict-only:end -->
