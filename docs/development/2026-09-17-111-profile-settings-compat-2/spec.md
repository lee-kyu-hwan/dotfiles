# Quality Goal Specification

- Task ID: 20260917T020220Z-111-프로필별-실경로-smoke-설정-호환성-결함을-방향-b-온디스크-c3bd8e26
- Mode: strict
- Status: SPEC_REVIEW
- Created: 2026-09-17
- Updated: 2026-09-17
- Source goal: #111 프로필별 실경로 smoke 설정 호환성 결함을 방향 B(온디스크 fixture 불변, 테스트 내부 fake CLI 생성)로 해결한다

## Problem and context

GitHub 이슈 #111의 실경로 smoke에서 `~/code/profile1/111-account-profile-smoke`는 `claude-profile1`을 정상 선택하지만, `ai-session status --provider claude --role-profile general --verifier <verify-claude> --accept-usage-unknown`이 `{"status":"blocked_policy"}`와 exit 4를 반환한다. 이것이 해결할 실환경 결함이다. 같은 절차에서 `~/code/profile2/111-account-profile-smoke`가 반환하는 `enrollment_required`와 exit 3은 명시적 identity enrollment 전의 설계된 정상 상태이며 결함이 아니다. 재현 전문은 `.claude/quality-state/20260917T002844Z-111-프로필별-실경로-smoke의-기본-claude-설정-호환성-결함-f76eb54a/evidence/repro-baseline.txt`에 있다.

직접 원인은 `dot_local/bin/executable_ai-session:104-108,995-1041`의 설정 prescan이다. `claude-profile1`은 `dot_config/ai-session/accounts.toml:18-26`에서 `config_home_mode = "provider_default"`이므로 사용자 본인의 `~/.claude`가 선택된다. `BENIGN_CLAUDE_SETTING_TYPES`는 `$schema`(string), `spinnerTipsEnabled`(boolean), `theme`(string)만 허용하고, `validate_untrusted_claude_settings()`는 그 밖의 키를 `blocked_policy`로 거부한다. `status()`(`:1555-1583`, prescan `:1558-1559`)와 `launch()`(`:1500-1552`, prescan `:1517`)가 모두 이를 호출한다.

아래 **실측 16개 키 fixture 계약**은 실제 설정 값을 제외하고 키 이름과 JSON 타입만 고정한다. 이 중 현재 allowlist와 이름·타입이 모두 일치하는 키는 `theme` 하나뿐이다.

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

prescan은 삭제할 수 있는 중복 검사가 아니다. `dot_local/libexec/executable_ai-session-verify-claude:44-56`의 `_official_status()`와 `dot_local/libexec/executable_ai-session-enroll-identity:122-142`의 `_identity_status()` 비합성 분기는 현재 `claude auth status --json`을 설정 source 차단 없이 실행한다. user/project/local settings의 `hooks`, `mcpServers`, `env`, `permissions`가 이 과정에 개입하는 것을 fail-closed로 막는 것이 prescan의 보안 목적이다. 반면 `dot_local/bin/executable_ai-role-session:1046-1060`의 role 명령은 이미 digest 검증된 `--settings`와 `--setting-sources ""`를 사용하지만 `--strict-mcp-config`는 아직 없다.

설치된 Claude Code 2.1.274의 읽기 전용 probe에서 exact argv `claude --setting-sources '' --strict-mcp-config auth status --json`은 exit 0이었고 baseline `claude auth status --json`과 같은 JSON 키 집합을 반환했다. 증거는 같은 quality-state evidence 디렉터리의 `probe-argv.txt`와 `probe-flags.txt`에 있다. 다만 `dot_local/libexec/ai_session_identity.py:31-53`의 `canonical_identity()`가 투영하는 `loggedIn`, `authMethod`, `subscriptionType`, UUID 정규화 `orgId`의 **값** 동일성은 아직 증명되지 않았으므로 별도 읽기 전용 판정이 필요하다.

직전 strict 실행은 Spec 라운드 2를 93점으로 통과했지만 Plan 라운드 2에서 신규 Critical finding이 확인되어 `NEEDS_REDESIGN`으로 끝났다. 보존 산출물은 `docs/development/2026-09-17-111-profile-settings-compat/`에 있다. 이번 재설계가 닫아야 하는 세 결함과 추적 관계는 다음과 같다.

| 이전 finding | 결함 | 이번 Spec의 해소 |
|---|---|---|
| `PLAN-001` | `tests/test_orchestrator_profiles.py:164-192`의 `make_fake_executable()`이 Claude `--help`를 3-option으로 먼저 가로채므로 5-option 런타임 계약이 기존 테스트를 차단한다. | R1.2와 R3.2가 helper의 Claude help 광고를 5-option으로 동기화하고, AC-14·AC-17이 기존 portable 계약과 전체 suite에서 판정한다. |
| `PLAN-002` | 기존 `test_portable_cli_contract`의 `:5130-5132`가 Claude required option을 3-option 리터럴로 단언한다. | R3.2가 리터럴을 exact ordered 5-option으로 동기화하고, AC-14·AC-17이 그 결과를 판정한다. |
| `PLAN-007` | 실제 테스트 범위가 `:5108-5235`인데 이전 Plan은 `:5108-5142`만 보아 `:5191-5210`의 온디스크 in-range fixture 사용을 누락했다. 5-option 계약 뒤 그 Claude 케이스는 결정적으로 exit 4가 된다. | 사용자가 선택한 방향 B에 따라 R3.2·R3.3이 Claude in-range만 테스트 파일 내부 fake CLI로 전환하고 codex 및 실패군 fixture는 보존한다. AC-14·AC-15·AC-19가 동작·범위·fixture bytes를 함께 판정한다. |

저장소는 chezmoi source다. `chezmoi apply` 없이 실행 권한이 없는 source를 `/opt/homebrew/bin/python3.14`로 직접 검증한다. 기존 baseline은 `tests/test_ai_session.py` 29개와 `tests/test_orchestrator_profiles.py` 92개가 모두 통과한다. `tests/check_installed_orchestrator_cli_contract.py`의 live help-only 실행은 변경 전부터 설치본 2.1.274와 동결 증거 2.1.272의 불일치로 exit 1이며, 이는 이번 변경의 회귀가 아니다.

## Goals

1. 정상 기본 `~/.claude` 설정을 가진 Mac에서도 `claude-profile1`의 `status`와 검토된 role `launch`가 설정 키 자체 때문에 `blocked_policy`로 차단되지 않게 한다.
2. verifier, enrollment helper, role launch에서 실행되는 Claude 프로세스가 미검토 user/project/local settings의 `hooks`, `mcpServers`, `env`, `permissions`를 로드하거나 실행하지 못하게 코드로 강제한다. allowlist는 확장하지 않는다.
3. baseline과 하드닝된 인증 조회가 canonical identity 입력값을 동일하게 제공함을 비밀 없는 읽기 전용 판정으로 확인한다.
4. `claude-profile2`의 사전 enrollment 상태를 유지하고, 사용자가 전경에서 명시적으로 enrollment한 뒤 `ready`에 도달하는 절차를 회귀 테스트와 운영 문서로 증명한다.
5. R3.2가 명시적으로 재정의한 세 테스트만 새 기대값으로 통과시키고 나머지 baseline 기대값을 불변으로 유지하며, `tests/fixtures/**`의 bytes를 보존한 채 portable CLI 계약의 Claude in-range 케이스만 테스트 내부 fake CLI로 안전하게 전환한다.

## Non-goals

- `tests/check_installed_orchestrator_cli_contract.py`의 `EXPECTED_VERSIONS` 또는 `docs/development/2026-09-15-103-orchestrator-permission-profiles-2/authoritative-inputs.md:81`의 동결 버전 문자열을 갱신하지 않는다. `AI_SESSION_CLI_PROBE_MODE=help-only /opt/homebrew/bin/python3.14 tests/check_installed_orchestrator_cli_contract.py`는 변경 전부터 `claude installed version differs from frozen evidence`, exit 1이며 이 script를 이번 작업의 배포 게이트로 사용하지 않는다. 이번 작업은 `EXPECTED_REQUIRED["claude"]`만 5-option으로 동기화한다.
- `claude-profile2` identity enrollment, 브라우저 로그인, logout 또는 account 전환을 자동 실행하지 않는다.
- `~/.claude`, `~/.local/share/ai-account-profiles/**`, `~/.config/ai-session/**`의 설정·credential·token·session·identity를 수정·이동·복사·rename·symlink하지 않는다.
- `claude-profile1`의 `config_home_mode = "provider_default"`와 profile별 workspace mapping을 변경하지 않는다.
- consumer 계정 간 자동 fallback, ranking, rotation, 사용량 기반 선택 또는 실행 중 account hot-swap을 도입하지 않는다.
- `BENIGN_CLAUDE_SETTING_TYPES`에 `hooks`, `mcpServers`, `env`, `permissions` 또는 다른 새 키를 추가하지 않는다.
- `--safe-mode`나 `--restricted`를 주 계약으로 사용하지 않고 `--bare`를 사용하지 않는다. 앞의 두 플래그는 role의 plugin·instruction·tool·permission 동작을 넓게 바꾸며, `--bare`는 OAuth와 Keychain을 읽지 않아 consumer identity 계약을 깨뜨린다.
- `tests/fixtures/**`, 대기 중인 #118 소유 경로, `dot_config/ai-session/accounts.toml`, 직전 실행 보존 산출물 `docs/development/2026-09-17-111-profile-settings-compat/`을 수정하지 않는다.
- `chezmoi apply`, 실제 모델 호출, login/logout, 실제 identity enrollment, tmux/session 조작, git write, commit/push, PR merge를 구현·판정 과정에서 실행하지 않는다.
- OAuth token, API key, 이메일, account ID 원문, `orgId` 원문, canonical identity 원문 또는 전체 digest를 저장소·문서·로그·fixture에 기록하지 않는다.

## Requirements

- **R1.1** Claude verifier와 명시적 identity enrollment helper가 실행하는 모든 비대화형 공식 인증 조회는 exact argv `claude --setting-sources "" --strict-mcp-config auth status --json`을 이 순서 그대로 사용해야 한다. 기존 10초 timeout, captured stdout/stderr, `close_fds=True`, empty `pass_fds`, nonzero·timeout·malformed JSON fail-closed, redacted six-field verifier 출력 계약은 유지한다. raw stdout/stderr 또는 identity 원문은 출력하거나 저장하지 않는다. [근거: `dot_local/libexec/executable_ai-session-verify-claude:44-56`; `dot_local/libexec/executable_ai-session-enroll-identity:122-142`; `probe-argv.txt`]
- **R1.2** 검토된 Claude role launch의 최종 provider argv는 exact one `--setting-sources ""`와 exact one `--strict-mcp-config`를 포함하고 digest 검증된 `--settings`만 추가 설정으로 허용해야 한다. 모든 Claude role의 manifest, `verify_provider_cli_contract()`의 expected required list, 설치 계약 checker의 `EXPECTED_REQUIRED["claude"]`는 exact ordered list `--append-system-prompt`, `--settings`, `--plugin-dir`, `--setting-sources`, `--strict-mcp-config`로 일치해야 한다. 지원 범위 `>=2.1.269,<2.2.0` 안이라도 help가 두 하드닝 플래그 중 하나를 광고하지 않으면 provider session exec 전에 public `blocked_cli_contract`, exit 4로 닫아야 한다. caller의 `--settings`, `--setting-sources`, `--strict-mcp-config`, `--mcp-config` 중복·재정의와 forged admitted argv는 provider session exec 전에 `blocked_policy` 또는 `blocked_contract`로 거부한다. [근거: `dot_local/bin/executable_ai-role-session:57-70,741-793,1004-1060,1271-1336`; `dot_config/ai-session/roles.toml`; `tests/check_installed_orchestrator_cli_contract.py:27-30`]
- **R1.3** prescan 우회는 실행될 Claude argv가 R1.1 또는 R1.2의 하드닝 계약을 충족한다고 같은 exec 경계에서 코드로 증명되는 경우로 제한하며, 네 호출 지점의 최종 상태는 다음과 같다. (1) `executable_ai-session:1517`의 `launch()` selected-home prescan은 **조건부 skip**이다. `binding.provider == "claude"`, strict registry, 유효한 `ROLE_CONTRACT_ID`, `AI_ROLE_ADMITTED=1`, trusted `executable_ai-role-session --admitted` command shape, metadata의 Claude provider 일치, 내포된 최종 provider argv의 R1.2 exact-one 검증을 모두 같은 경계에서 통과할 때만 skip한다. 그 밖의 legacy·임의 command는 prescan을 유지하고 malformed admitted command는 `blocked_contract`로 provider·verifier exec 전에 거부한다. (2) `executable_ai-session:1558-1559`의 `status()` selected-home prescan도 **조건부 skip**이다. `provider=claude`이고 `--verifier`가 기존 absolute·regular·non-symlink·executable 검사를 먼저 모두 통과한 trusted dependency-injection seam일 때만 skip하며, 그 외 direct·untrusted 경로는 prescan 또는 명시적 거부를 유지한다. production verifier는 내부에서 R1.1을 강제한다. (3) `executable_ai-role-session:1016`의 `claude_command()` project prescan은 **무조건 유지**해 repository의 `.claude/settings.json`과 `.claude/settings.local.json`에 위험 키가 있으면 기존처럼 `blocked_policy`로 닫는다. (4) `executable_ai-role-session:1303-1304`의 `admitted_main()` selected-home prescan 호출은 **제거**하고, `os.execvpe` 직전에 metadata provider 일치와 최종 Claude argv의 R1.2 exact-one·빈 setting sources·digest-verified settings 계약을 의무 재검증한다. 실패 시 `blocked_contract`로 provider session exec 0회를 보장하며 prescan 성공을 fallback으로 사용하지 않는다. home mode만으로 우회하거나 allowlist를 확장해서는 안 된다. [근거: `dot_local/bin/executable_ai-session:995-1042,1221-1266,1500-1583`; `dot_local/bin/executable_ai-role-session:985-1017,1271-1336`; `tests/test_orchestrator_profiles.py:2059-2178`]
- **R1.4** 설치된 Claude Code 2.1.274에서 baseline 인증 조회와 R1.1의 하드닝 조회는 `loggedIn`, `authMethod`, `subscriptionType`, UUID로 정규화한 `orgId` 값이 동일해야 한다. 비교는 메모리에서만 수행하고 safe boolean과 exit code만 노출한다. 값 불일치, 필드 누락, 타입 오류, UUID 오류는 판정 실패이며 identity를 `matched`나 `ready`로 승격하지 않는다. fixture에서도 두 경로의 canonical digest와 verifier 상태가 동일해야 한다. [근거: `dot_local/libexec/ai_session_identity.py:31-53`; `probe-flags.txt`]
- **R2.1** Problem and context의 실측 16개 키 fixture 계약과 정확히 같은 키 이름·JSON 타입을 가진 임시 `CLAUDE_CONFIG_DIR/settings.json` 아래에서, 유효한 합성 login·identity·usage 입력을 받은 `claude-profile1` source `status --accept-usage-unknown`은 `ready`, exit 0을 반환해야 한다. fixture에는 실제 사용자 값을 복사하지 않으며 설정 내용 때문에 `blocked_policy`가 되어서는 안 된다. 실제 사용자 home이나 identity root를 읽거나 쓰지 않는다. [근거: `repro-baseline.txt`; `dot_config/ai-session/accounts.toml:18-26`]
- **R2.2** 같은 격리 fixture에서 검토된 `claude-profile1` role launch는 account admission과 role dispatch를 통과해 fake provider session을 정확히 한 번 실행해야 한다. 최종 argv는 R1.2를 만족하고 sentinel hook·MCP child·env·permission 주입은 발생하지 않아야 하며 실제 Claude 모델, login, tmux, chezmoi를 호출하지 않는다. [근거: `dot_local/bin/executable_ai-session:1500-1552`; `dot_local/bin/executable_ai-role-session:1386-1480`]
- **R2.3** `claude-profile2`는 enrollment file이 없는 격리 fixture에서 exact status 명령 `ai-session status --registry "${HOME}/.config/ai-session/accounts.toml" --provider claude --role-profile general --verifier "${HOME}/.local/libexec/ai-session-verify-claude" --accept-usage-unknown`으로 계속 `enrollment_required`, `identity_status="not_enrolled"`, `identity_enroll_foreground`, exit 3을 반환해야 한다. 사용자가 전경에서 exact helper 명령 `ai-session-enroll-identity --registry "${HOME}/.config/ai-session/accounts.toml" --provider claude --account-profile claude-profile2`를 한 번 명시적으로 실행하면 host-local 임시 identity root에만 v2 digest가 생성되고 같은 exact status 명령을 새로 실행했을 때 `ready`, exit 0이 되어야 한다. `${HOME}`는 POSIX shell이 실행 전에 현재 사용자의 absolute home으로 확장하며, registry는 absolute file path, verifier는 absolute regular non-symlink executable path가 되어야 한다. helper에는 parser가 받는 세 옵션 외의 status 전용 옵션을 전달하지 않는다. backend가 helper를 자동 호출하거나 다른 profile의 설정·credential·identity를 복사해서는 안 된다. [근거: `repro-baseline.txt`; `dot_local/bin/executable_ai-session:933-945,2139-2142`; `dot_local/libexec/executable_ai-session-enroll-identity:213-273,240-245`]
- **R3.1** 보안 회귀 fixture는 임시 Claude home의 `settings.json`에 sentinel을 쓰는 hook과 `mcpServers`, `env`, `permissions`를 넣어야 한다. 같은 fake Claude를 하드닝 플래그 없이 호출하는 negative control은 sentinel을 생성해야 하고, R1.1·R1.2 경로는 sentinel·MCP child·설정 기반 env capture를 하나도 생성하지 않아야 한다. negative control과 production path는 실제 사용자 home과 네트워크를 사용하지 않는다. [근거: `dot_local/bin/executable_ai-session:995-1042`; `dot_local/bin/executable_ai-role-session:965-1001`]
- **R3.2** baseline의 기존 기대값 중 명시적으로 재정의하는 테스트는 정확히 `test_claude_untrusted_settings_prescan`, `test_claude_official_status_contract`, `test_portable_cli_contract` 세 개뿐이다. `tests/test_ai_session.py` baseline 29개는 모두 불변이고, `tests/test_orchestrator_profiles.py` baseline 92개 중 이 세 테스트의 아래 명시 지점 외 모든 기존 기대값도 불변이다. `test_claude_untrusted_settings_prescan`(`tests/test_orchestrator_profiles.py:2059-2178`)은 project-settings 5개 subtest를 계속 차단하되 두 account-home subtest의 위험 settings 기대값을 R1.3·AC-20으로 바꾼다. `test_claude_official_status_contract`(`:2985-3015`, 특히 `:3014`)는 exact argv를 AC-1과 동일하게 바꾸고 `call["open_fds"] == []`는 유지한다. `test_portable_cli_contract`(`:5108-5235`) 전체가 실제 수정 범위다. `:164-192`의 `make_fake_executable()`은 provider별 help 분기로 바꿔 codex help 문자열 `--model --sandbox --ask-for-approval --append-system-prompt --settings --plugin-dir`와 required 세 옵션 광고를 그대로 유지하고, Claude help는 exact ordered five `--append-system-prompt --settings --plugin-dir --setting-sources --strict-mcp-config`를 광고한다. Claude `--version` 문자열은 `2.1.272 (Claude Code)` 그대로 불변이고 `:5130-5132`의 Claude required-option 리터럴도 같은 five로 동기화한다. `:5163-5170`의 lower·upper·missing-option 케이스는 codex와 claude 모두 기존 온디스크 fixture와 `blocked_cli_contract`/4/`selector_capture` 미생성을 유지한다. `:5191-5210`의 in-range 케이스는 codex만 온디스크 fixture를 계속 사용하고 Claude는 test-local five-option fake CLI를 사용하며 둘 다 exit 0과 `--role-contract` token 검증을 유지한다. `:5212-5235` installed-checker는 exit 0과 probe log exact four lines를 유지한다. 기본 테스트는 임시 directory, PATH 선두 fake executable, `AI_SESSION_SYNTHETIC_TEST=1`, `AI_SESSION_IDENTITY_ROOT`를 사용한다. 단 enrollment argv 회귀는 두 synthetic 환경변수를 unset한 실제 subprocess 분기에서 fake `claude`를 정확히 한 번 실행해 argv를 캡처한다. [근거: `tests/test_orchestrator_profiles.py:164-192,2059-2178,2985-3015,5108-5235`; `tests/check_installed_orchestrator_cli_contract.py:22,27-30,110-119`; `tests/fixtures/orchestrator-profiles/cli/executable_fake-cli-in-range:6-9`]
- **R3.3** 운영 문서 두 개는 설정 격리, profile1 호환성, profile2의 R2.3과 byte-identical한 exact status·helper 명령 및 `${HOME}` 치환 규칙, `status → 사용자 확인 → 전경 enrollment helper → 새 status → ready` status·exit·복구 경계를 문서화한다. 변경 가능 범위는 정확히 `dot_local/bin/executable_ai-session`, `dot_local/bin/executable_ai-role-session`, `dot_local/libexec/executable_ai-session-verify-claude`, `dot_local/libexec/executable_ai-session-enroll-identity`, `dot_config/ai-session/roles.toml`, `tests/test_ai_session.py`, `tests/test_orchestrator_profiles.py`, `tests/check_installed_orchestrator_cli_contract.py`, `docs/session-account-profiles.md`, `docs/orchestrator-permission-profiles.md`의 10개 파일이다. scope checker의 비교 대상은 `git status --porcelain` 경로 중 prefix 제외 집합 `docs/development/2026-09-17-111-profile-settings-compat-2/`, `docs/development/2026-09-17-111-profile-settings-compat/`, `.claude/quality-state/`에 속하지 않는 모든 경로이며, 그 나머지는 위 허용 집합의 부분집합이어야 한다. `dot_config/ai-session/accounts.toml`, `tests/fixtures/**`, #118 소유 경로와 직전 실행 산출물은 변경 금지다. [근거: 새 workflow state의 `initial_dirty_paths`; `.gitignore:25`; 직전 Plan G7; 사용자 선택 방향 B]

## Acceptance criteria

- **AC-1** fake `claude`가 기록한 verifier argv가 exact `claude --setting-sources "" --strict-mcp-config auth status --json`이고 호출 횟수가 1이며 timeout·FD·redaction 계약이 유지된다. 기존 `test_claude_official_status_contract`도 `call["argv"]`를 `[str(self.bin_dir / "claude"), "--setting-sources", "", "--strict-mcp-config", "auth", "status", "--json"]`과 exact-equal로 판정하고 기존 `call["open_fds"] == []`를 유지한다. [실행] (CMD-2 `test_settings_compat_verifier_argv` 및 `test_claude_official_status_contract`)
- **AC-2** explicit enrollment helper는 `AI_SESSION_SYNTHETIC_TEST`와 `AI_SESSION_SYNTHETIC_STATUS_JSON`을 unset해 합성 분기를 사용하지 않고 PATH 선두의 fake `claude` subprocess를 실제로 정확히 한 번 실행해 AC-1과 같은 exact argv를 캡처하며 임시 identity root 밖에 파일을 만들지 않는다. [실행] (CMD-2 `test_settings_compat_enrollment_argv`)
- **AC-3** 네 Claude role의 생성 argv가 exact one `--setting-sources ""`, exact one `--strict-mcp-config`, digest 검증된 `--settings`를 가지며 caller override와 forged admitted argv가 provider session exec 전에 거부된다. [실행] (CMD-2 `test_settings_compat_role_launch_argv`)
- **AC-4** 하드닝 계약이 없거나 중복·오염된 argv를 가진 legacy·임의 launch fixture는 위험 settings 아래에서 child 실행 없이 fail-closed하고 `BENIGN_CLAUDE_SETTING_TYPES`에 위험 키나 새 키가 추가되지 않는다. [실행] (CMD-1 `test_settings_compat_unhardened_route_fail_closed`)
- **AC-5** opt-in live probe가 baseline `claude auth status --json`과 exact-order 하드닝 argv를 각각 읽기 전용으로 실행하고 canonical 네 필드를 메모리에서 비교해 동일할 때만 exit 0을 반환하며 출력에 필드 값, 이메일, `orgId`, identity 또는 digest가 나타나지 않는다. [실행] (CMD-4 `test_settings_compat_live_identity_projection`)
- **AC-6** 임시 provider-default home의 settings가 실측 16개 키 fixture 계약과 키 집합·각 JSON 타입이 정확히 같아도 profile1 `status --accept-usage-unknown`은 합성 matched identity에서 `ready`, exit 0이고 `blocked_policy`가 아니다. [실행] (CMD-1 `test_settings_compat_profile1_status`)
- **AC-7** 같은 16개 키 fixture를 사용하는 strict profile1 role launch는 fake Claude provider session을 정확히 한 번 실행하고 최종 argv가 하드닝 계약을 만족하며 `blocked_policy`를 내지 않는다. [실행] (CMD-2 `test_settings_compat_profile1_launch_e2e`)
- **AC-8** 격리된 profile2 lifecycle은 exact status 명령 `ai-session status --registry "${HOME}/.config/ai-session/accounts.toml" --provider claude --role-profile general --verifier "${HOME}/.local/libexec/ai-session-verify-claude" --accept-usage-unknown`을 첫 번째와 두 번째 status에 동일하게 사용하고, 그 사이에는 exact helper 명령 `ai-session-enroll-identity --registry "${HOME}/.config/ai-session/accounts.toml" --provider claude --account-profile claude-profile2`만 사용한다. 결과는 `enrollment_required`/exit 3 → `enrolled`/exit 0 → `ready`/exit 0 순서이고 helper 자동 호출과 profile 간 파일 복사는 0회다. 테스트 fixture에서는 `${HOME}`를 임시 absolute home으로 치환하고 registry file 및 regular non-symlink executable verifier의 absolute path를 넘긴다. [실행] (CMD-2 `test_settings_compat_profile2_enrollment_to_ready`)
- **AC-9** 두 운영 문서의 profile2 절은 AC-8과 byte-for-byte 동일한 exact status 명령 `ai-session status --registry "${HOME}/.config/ai-session/accounts.toml" --provider claude --role-profile general --verifier "${HOME}/.local/libexec/ai-session-verify-claude" --accept-usage-unknown`과 exact helper 명령 `ai-session-enroll-identity --registry "${HOME}/.config/ai-session/accounts.toml" --provider claude --account-profile claude-profile2`, 순서 `status → 사용자 확인 → helper → 새 status`, 결과 `enrollment_required`/exit 3 → `enrolled`/exit 0 → `ready`/exit 0, 경계 문구 `backend는 login·enrollment·fallback·profile 간 설정/credential/identity 복사를 자동 실행하지 않는다.`를 포함하며 두 파일의 profile2 운영 계약 block은 byte-identical하다. `${HOME}`는 POSIX shell이 실행 전에 absolute 사용자 home으로 확장하고 registry는 `${HOME}/.config/ai-session/accounts.toml`, verifier는 executable `${HOME}/.local/libexec/ai-session-verify-claude`로 치환한다는 규칙도 같은 block에 포함한다. helper에는 `--registry`, `--provider`, `--account-profile`만 전달한다. [문서] docs/session-account-profiles.md docs/orchestrator-permission-profiles.md
- **AC-10** sentinel fixture의 unhardened negative control은 sentinel을 생성하지만 hardened verifier와 enrollment 경로는 sentinel, MCP child, 설정 기반 env capture를 하나도 생성하지 않는다. [실행] (CMD-2 `test_settings_compat_auth_status_sentinel`)
- **AC-11** strict role launch의 hardened provider 경로도 같은 sentinel, MCP child, 설정 기반 env capture를 하나도 생성하지 않고 fake provider의 정상 capture만 생성한다. [실행] (CMD-2 `test_settings_compat_role_launch_sentinel`)
- **AC-12** 이번 변경에 추가된 모든 `test_settings_compat_*` 회귀 테스트가 실제 사용자 home·identity root·network·model·실행 중 session을 사용하지 않는 기본 모드에서 통과한다. [실행] (CMD-1 및 CMD-2 `test_settings_compat_`)
- **AC-13** R3.2의 명시적 재정의 목록에는 `tests/test_ai_session.py` 테스트가 없으므로 baseline 29개의 기존 기대값은 전부 불변이고, 추가 회귀를 포함한 파일 전체가 failure/error 없이 통과한다. [실행] (CMD-3 `tests/test_ai_session.py`)
- **AC-14** baseline `tests/test_orchestrator_profiles.py` 92개 중 R3.2에서 명시적으로 재정의한 `test_claude_untrusted_settings_prescan`, `test_claude_official_status_contract`, `test_portable_cli_contract`만 각각 AC-20, AC-1, 이 AC의 새 기대값을 사용하고, 나머지 기존 테스트의 기대값은 불변이다. `test_portable_cli_contract`의 여섯 실패 케이스는 그대로이고, codex in-range는 온디스크 fixture, Claude in-range만 test-local five-option fake CLI를 사용해 둘 다 exit 0과 `--role-contract` token을 검증한다. installed-checker 하위 구간은 exit 0이고 probe log가 exact `codex --version`, `codex --help`, `claude --version`, `claude --help` 네 줄이어야 한다. 이어 추가 회귀를 포함한 파일 전체가 failure/error 없이 통과하며 live probe는 opt-in 없이는 외부 CLI를 호출하지 않는다. [실행] (CMD-2 `test_portable_cli_contract` 및 CMD-5 `tests/test_orchestrator_profiles.py`)
- **AC-15** scope 회귀 검사는 `git status --porcelain` 경로에서 R3.3의 세 prefix를 제외한 비교 집합이 정확한 10개 허용 파일 집합의 부분집합인지 판정하고, 그 밖의 경로가 하나라도 있으면 실패한다. R3.2의 세 기존 테스트 재정의는 이미 허용된 `tests/test_orchestrator_profiles.py` 한 파일 안에서만 이루어지며 scope를 넓히지 않는다. 또한 `dot_config/ai-session/accounts.toml`의 provider-default/explicit-home 계약, #118 소유 경로, 직전 실행 산출물 5개가 보존됨을 확인한다. 직전 산출물 tree는 relative POSIX path와 NUL 및 각 file bytes SHA-256을 정렬 결합한 사전 SHA-256 `7782f035ca0594bc1c295a9cbfc1a748f7528142d46fc881889ef94024e9d631`과 같아야 하고 secret·identity 원문이 diff나 출력에 없어야 한다. [실행] (CMD-2 `test_settings_compat_scope_and_secret_hygiene`)
- **AC-16** 하나의 교차 회귀 시나리오에서 임시 provider-default account home의 실측 16개 키와 위험 키가 있는 동일 settings를 그대로 둔 채 profile1 status가 `ready`/exit 0이고 role provider session이 정확히 한 번 성공하며, 동시에 verifier·enrollment·role provider 어느 경로에서도 sentinel hook·MCP child·env·permission 주입이 발생하지 않아 호환성 해소와 보안 속성이 함께 성립한다. repository project `.claude/settings*.json`은 이 성공 fixture에 만들지 않으며 그 별도 차단 계약은 AC-20이 판정한다. [실행] (CMD-2 `test_settings_compat_cross_regression`)
- **AC-17** 네 Claude role manifest, `verify_provider_cli_contract()`, 설치 계약 checker, `make_fake_executable()`의 Claude help 기본값, `test_portable_cli_contract`의 expected literal이 R1.2의 5-option 계약과 일치한다. helper의 Claude `--version`은 exact `2.1.272 (Claude Code)`, Claude `--help`는 다섯 required option 전부, codex `--help`는 기존 exact 문자열과 최소 required `--model`, `--sandbox`, `--ask-for-approval`을 광고한다. 지원 범위 안의 fake Claude help에서 `--setting-sources` 또는 `--strict-mcp-config` 하나를 각각 제거한 두 경우에는 `claude --version`과 `claude --help` probe만 허용되고 provider session exec는 0회이며 public `blocked_cli_contract`, exit 4가 된다. installed-checker는 이 helper로 exit 0이어야 한다. [실행] (CMD-2 `test_settings_compat_claude_required_options` 및 `test_portable_cli_contract`)
- **AC-18** 두 운영 문서의 byte-identical 설정 격리 block은 exact 문구 `profile1 provider-default 설정은 보존한다.`와 `verifier·enrollment·role provider는 --setting-sources "" --strict-mcp-config로 user/project/local settings와 비검토 MCP를 로드하지 않는다.`를 포함하고 AC-9의 profile2 block도 존재한다. [실행] (CMD-2 `test_settings_compat_documentation_contract`)
- **AC-19** `tests/fixtures/orchestrator-profiles/**`의 7개 파일은 R3.2의 세 기존 테스트 재정의와 무관하게 파일명과 bytes가 모두 사전 상태와 동일해야 한다. relative POSIX path와 NUL 및 각 file bytes SHA-256을 정렬 결합한 tree SHA-256은 `21471ff031b82da9d25b8a10b9d195eadfdd26c30a27761ef4b253b6b2a9e128`이고, 파일 추가·삭제·rename·내용 변경은 모두 실패한다. [실행] (CMD-2 `test_settings_compat_fixture_bytes_unchanged`)
- **AC-20** 기존 `test_claude_untrusted_settings_prescan`의 project-settings 구간은 `hooks`, `permissions`, `env`, `enabledPlugins`, `mcpServers` 각각에 대해 계속 exit 4, 마지막 status `blocked_policy`, `ai-session` dispatch 0회를 단언한다. provider-default `claude-profile1`과 explicit-home `claude-profile2` account-home 구간은 `{"theme":"dark"}` 대조군이 기존처럼 exit 0, verifier 1회, provider session 1회이고, 이어 exact `{"hooks":{}}`로 바꾼 경우는 기존 exit 4 기대를 exit 0, verifier 1회, provider session 1회로 재정의한다. 같은 두 account-home subtest는 sentinel hook·MCP child·env·permission capture가 가능한 위험 fixture도 실행해 최종 provider argv가 R1.2를 만족하고 provider session은 정확히 1회인 반면 sentinel·MCP child·설정 기반 env·permission 주입은 모두 0회임을 함께 단언한다. 어느 성공 경로도 `blocked_policy` record를 내지 않고 실제 user home·network·model을 사용하지 않는다. [실행] (CMD-2 `test_claude_untrusted_settings_prescan`)

## Requirements traceability

This table maps every requirement to acceptance criteria and the judgement method that proves the mapping.

| Requirement | Acceptance criteria | Judgement method |
|---|---|---|
| R1.1 | AC-1, AC-2 | CMD-2의 신규·기존 official-status verifier와 비합성 enrollment exact argv, 호출 횟수, empty FD, redaction 회귀 |
| R1.2 | AC-3, AC-17 | CMD-2의 최종 role argv·override/forgery 거부와 5-option CLI fail-closed 회귀 |
| R1.3 | AC-4, AC-16, AC-20 | CMD-1의 미하드닝 fail-closed, CMD-2의 네 prescan 지점 결과와 기존 테스트의 project 차단/account-home 하드닝 성공 교차 회귀 |
| R1.4 | AC-5 | CMD-4의 opt-in 읽기 전용 live canonical projection 비교 |
| R2.1 | AC-6, AC-16 | CMD-1의 profile1 status와 CMD-2의 동일 fixture 교차 회귀 |
| R2.2 | AC-7, AC-16 | CMD-2의 strict role launch E2E와 동일 fixture 교차 회귀 |
| R2.3 | AC-8, AC-9 | CMD-2의 격리 lifecycle과 두 운영 문서의 exact profile2 block |
| R3.1 | AC-10, AC-11, AC-16 | CMD-2의 negative control 및 verifier·enrollment·role sentinel 검사 |
| R3.2 | AC-1, AC-12, AC-13, AC-14, AC-17, AC-19, AC-20 | CMD-1·CMD-2의 세 기존 테스트 재정의와 targeted 회귀, CMD-3·CMD-5의 나머지 기대값 불변 전체 suite, fixture tree digest |
| R3.3 | AC-9, AC-15, AC-18, AC-19 | CMD-2의 exact scope·보존·secret hygiene·문서·fixture 불변 판정 |

## Architecture

설정 파일의 내용을 더 넓게 신뢰하지 않고 **실행되는 Claude 프로세스의 설정 입력면을 닫는 것**을 신뢰 경계로 삼는다.

1. `executable_ai-session-verify-claude`와 `executable_ai-session-enroll-identity`는 같은 exact 비대화형 auth argv를 사용한다. `--setting-sources ""`는 user/project/local settings source를 끄고 `--strict-mcp-config`는 명시되지 않은 MCP 구성을 배제한다.
2. `executable_ai-role-session`은 digest 검증된 합성 `--settings`를 명시적으로 공급하고 두 차단 option을 exact-one으로 생성·검증한다. manifest, 런타임 expected list, 설치 checker는 같은 5-option 계약을 선언한다. model, effort, reviewed plugin, append prompt, permission/sandbox 합성 검증은 유지한다.
3. account launcher와 role launcher는 profile 이름이나 home mode를 신뢰 근거로 삼지 않는다. status의 trusted verifier와 strict admitted-role의 내포 argv를 해당 exec 경계에서 검증한 경우에만 selected-home prescan을 건너뛴다. role command 생성 시 repository project prescan은 유지하고, admitted 최종 경계의 selected-home prescan은 R1.2 재검증으로 교체한다. 나머지는 기존 prescan 또는 명시적 거부를 유지한다.
4. portable CLI 테스트의 계약 데이터는 test code에서 5-option으로 동기화하되 온디스크 fixture는 immutable input으로 취급한다. lower·upper·missing-option 및 codex in-range는 기존 파일을 그대로 사용하고, 계약 확장과 의미가 충돌하는 Claude in-range만 임시 test-local executable로 대체한다.
5. admission, identity digest, usage dual consent, status schema, exit code, registry schema와 account home layout은 바꾸지 않는다.

| Component | Responsibility |
|---|---|
| `dot_local/libexec/executable_ai-session-verify-claude` | 하드닝된 공식 auth status 실행과 redacted six-field adapter |
| `dot_local/libexec/executable_ai-session-enroll-identity` | 사용자 전경 호출에서 같은 하드닝 조회 후 선택된 임시/host-local identity root에 digest 기록 |
| `dot_local/bin/executable_ai-role-session` | 검토된 합성 settings와 차단 flag를 가진 최종 Claude argv 생성·재검증 |
| `dot_local/bin/executable_ai-session` | account 선택, 하드닝 경로 판별, prescan fallback, admission, status/launch 결과 |
| `dot_config/ai-session/roles.toml` | 모든 Claude role의 지원 CLI 범위와 5-option required 계약 |
| `tests/test_ai_session.py` | account launcher compatibility와 미하드닝 fail-closed 단위 계약 |
| `tests/test_orchestrator_profiles.py` | argv·sentinel·lifecycle·portable CLI·scope·fixture 불변·문서·source E2E |
| `tests/fixtures/orchestrator-profiles/**` | byte-immutable legacy portable/E2E input; 수정 대상이 아님 |
| 두 운영 문서 | 사용자에게 설정 격리와 profile2 explicit enrollment 절차를 제공 |

## Interfaces and data flow

`status` 흐름은 `real cwd → account selection → child environment → trusted hardened verifier → canonical identity comparison → usage/cost admission → profile_status JSON`이다. 기존 `--verifier`는 absolute·regular·non-symlink·executable 검사 뒤 사용하는 trusted dependency-injection seam이다. production adapter가 자기 subprocess argv를 R1.1로 고정하므로 그 경로에서는 selected home prescan을 대체한다. `status`는 registry, settings, identity, account home, worktree 또는 session을 쓰지 않는다.

`launch` 흐름은 `role entrypoint → project .claude prescan → reviewed role policy/settings 검증 → CLI version/help probe → hardened provider argv 생성 → ai-session의 trusted admitted-command shape 및 내포 argv 검증 → account selection/admission → admitted role boundary의 최종 argv 재검증 → Claude provider session exec`이다. project prescan은 위험 project settings를 계속 차단한다. 두 selected-home 지점은 뒤의 검증이 성공한 strict admitted route에서만 우회되며, account launcher와 admitted role 경계 어느 쪽에서든 하드닝을 증명할 수 없으면 session exec하지 않는다. CLI contract 판정을 위한 `claude --version`과 `claude --help`는 허용되는 read-only probe이며 provider session exec 계수에 포함하지 않는다.

profile2 전경 흐름은 `status(enrollment_required) → 사용자 descriptor 확인 → enrollment helper 명시 실행 → hardened auth status → v2 digest atomic write → 새 status(ready)`다. helper만 선택된 identity root에 쓸 수 있고 status·launch는 enrollment를 생성하거나 갱신하지 않는다.

portable CLI 테스트는 실패군에서 기존 fixture를 PATH에 복사하고, in-range에서는 codex만 기존 fixture를 복사한다. Claude in-range는 `tests/test_orchestrator_profiles.py`의 임시 directory에 5-option fake executable을 생성한다. 양쪽 성공 경로는 같은 `selector_capture`와 `--role-contract` assertion으로 수렴한다. fixture source tree에는 쓰지 않는다.

verifier public stdout은 기존 exact fields `provider`, `account_profile`, `login_status`, `identity_status`, `usage_status`, `cost_limit_status`인 compact JSON 한 줄을 유지한다. raw Claude JSON은 subprocess 메모리 밖으로 전달하지 않고 canonical identity는 필요한 네 필드만 비교한다.

## Failure behavior

- 하드닝 argv가 누락·중복·재정의되거나 trusted role structure와 맞지 않으면 Claude provider session을 시작하지 않고 `blocked_policy` 또는 `blocked_contract`로 닫는다.
- 지원 version 범위 안이어도 help가 `--setting-sources`나 `--strict-mcp-config`를 광고하지 않으면 read-only version/help probe 뒤 public `blocked_cli_contract`, exit 4로 닫고 provider session exec는 0회다.
- hardened auth status가 nonzero, timeout, malformed JSON 또는 field/type/UUID 오류를 내면 raw output 없이 기존 fail-closed verifier 상태로 처리한다.
- live canonical projection이 다르면 배포 판정을 실패시킨다. 값은 출력하지 않고 field-name과 safe boolean, exit code만 허용한다.
- profile1의 selected account-home 설정 key 때문에 `status` 또는 검증된 role launch에 `blocked_policy`가 재발하면 compatibility 실패다. repository project `.claude/settings*.json`의 위험 키가 `blocked_policy`인 것은 유지되는 별도 보안 계약이다. allowlist 확장으로 복구하지 않는다.
- profile2의 `enrollment_required`는 오류가 아니다. helper 실패·duplicate mapping·identity drift는 기존 계약을 유지하고 자동 retry나 overwrite를 하지 않는다.
- sentinel, MCP child, 설정 기반 env/permission capture가 하나라도 생기면 status나 launch의 다른 성공 여부와 무관하게 보안 판정 실패다.
- 온디스크 fixture의 파일명·bytes가 하나라도 달라지거나 scope 비교 집합에 허용되지 않은 경로가 나타나면 구현 판정은 실패한다. fixture를 갱신해 테스트를 맞추는 복구는 금지한다.
- 설치 checker의 기존 `EXPECTED_VERSIONS` 불일치 exit 1은 이번 변경의 실패 신호가 아니다. required-option 동기화와 live identity projection은 별도 판정으로 닫는다.

## Security and risk

가장 큰 위험은 compatibility를 위해 provider-default home을 신뢰하거나 allowlist를 넓혀 위험 설정을 실제 Claude process에 노출하는 것이다. 이 Spec은 파일의 정상성 대신 child argv의 설정 source 차단을 강제한다. 정상 사용자 설정에 존재하더라도 `hooks`, `mcpServers`, `env`, `permissions`는 verifier와 reviewed role process 관점에서 untrusted input이다.

두 번째 위험은 flag 존재만 검사하고 duplicate option이나 forged admitted argv로 뒤에서 재정의하는 것이다. exact-one, 빈 `--setting-sources` 값, digest 검증 `--settings`, caller override 거부와 두 exec 경계 재검증을 함께 요구한다.

세 번째 위험은 auth hardening이 다른 identity를 보거나 raw 값을 누출하는 것이다. 실제 설치본의 canonical projection 값을 메모리에서 비교하고 boolean/exit만 노출한다. 기본 회귀는 임시 home과 fake executable을 사용한다.

네 번째 위험은 테스트 계약 확장 중 공유 fixture 의미를 바꿔 대기 중인 #118과 충돌하거나 기존 실패군의 탐지 의미를 약화하는 것이다. fixture tree digest와 exact scope를 동결하고 Claude in-range만 test-local fake로 분기해 그 위험을 제거한다.

## Test strategy

test-first의 필수 positive control은 먼저 `test_settings_compat_profile1_status`를 작성해 실측 16개 키와 위험 설정이 있는 임시 provider-default home, trusted verifier seam, 합성 matched identity에서 `ready`/exit 0과 not-`blocked_policy`를 assert하는 것이다. 현재 구현은 `status()`가 prescan을 무조건 호출하므로 이 테스트가 구현 전 확정적으로 `blocked_policy`/exit 4로 실패해야 한다. 이 Red 결과를 기록하지 않으면 해당 test-first 증거는 성립하지 않는다.

보안 fixture는 하드닝 flag가 없을 때 sentinel을 실제 생성하는 negative control을 먼저 통과시켜 탐지 능력을 증명한다. 이어 같은 settings를 바꾸지 않고 verifier, 비합성 enrollment subprocess, strict role launch를 실행해 sentinel·MCP·env/permission capture가 0인지 검사한다. enrollment argv 테스트는 두 synthetic 환경변수를 unset하고 PATH 선두 fake Claude를 한 번 실제 실행해야 한다.

portable CLI 회귀는 기존 `test_portable_cli_contract` 전체를 targeted 실행한다. 실패군 여섯 개와 codex in-range는 온디스크 fixture를 그대로 사용하고 Claude in-range만 test-local fake를 쓴다. 별도 fixture 불변 테스트는 사전 tree digest를 계산해 새 파일, 삭제, rename, byte 변경을 모두 탐지한다. 이 두 판정을 함께 통과해야 방향 B가 성립한다.

기존 테스트 재정의 회귀는 `test_claude_untrusted_settings_prescan`에서 project-settings 다섯 차단과 selected account-home 두 profile의 하드닝 성공을 동시에 판정하고, `test_claude_official_status_contract`에서 AC-1 exact argv와 empty FD를 판정하며, `test_portable_cli_contract`에서 five-option·test-local Claude in-range·installed-checker 네 probe를 함께 판정한다. 이 셋의 변경은 같은 테스트 파일 안에만 있고 AC-15의 10-file scope, AC-19의 fixture byte 불변, 직전 산출물 불변을 완화하지 않는다.

### 판정 명령 표

| ID | 명령 | 통과 조건 |
|---|---|---|
| CMD-1 | `/opt/homebrew/bin/python3.14 -m unittest tests.test_ai_session.AiSessionCliTests.test_settings_compat_unhardened_route_fail_closed tests.test_ai_session.AiSessionCliTests.test_settings_compat_profile1_status` | account launcher의 미하드닝 fail-closed와 16-key profile1 status compatibility 테스트가 모두 통과하고 실제 home·network·provider 호출은 0회다. |
| CMD-2 | `/opt/homebrew/bin/python3.14 -m unittest tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_verifier_argv tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_enrollment_argv tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_role_launch_argv tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_profile1_launch_e2e tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_profile2_enrollment_to_ready tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_auth_status_sentinel tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_role_launch_sentinel tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_scope_and_secret_hygiene tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_cross_regression tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_claude_required_options tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_documentation_contract tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_fixture_bytes_unchanged tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_claude_untrusted_settings_prescan tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_claude_official_status_contract tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_portable_cli_contract` | verifier·enrollment·role launch·lifecycle·sentinel·scope·cross-regression·CLI option·문서·fixture 불변과 세 기존 테스트 재정의 targeted 테스트 15개가 모두 실행·통과한다. |
| CMD-3 | `/opt/homebrew/bin/python3.14 tests/test_ai_session.py` | 기존 29개를 포함한 전체 suite가 failure/error 없이 exit 0이다. |
| CMD-4 | `AI_SESSION_LIVE_CLAUDE_AUTH_PROBE=1 /opt/homebrew/bin/python3.14 -m unittest tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_live_identity_projection` | baseline과 exact-order hardened argv의 canonical projection이 같고 값이 출력·저장되지 않으며 exit 0이다. |
| CMD-5 | `/opt/homebrew/bin/python3.14 tests/test_orchestrator_profiles.py` | 기존 92개를 포함한 전체 suite가 failure/error 없이 exit 0이고 opt-in live probe는 skip된다. |

CMD-1, CMD-2, CMD-3, CMD-5는 source tree, 임시 directory와 fake executable만 사용하고 실제 `~/.claude`, `~/.local/share/ai-account-profiles/`, 실행 중 session을 변경하지 않는다. CMD-4만 설치된 Claude CLI의 auth status를 두 번 읽기 전용 호출하며 stdout 값을 파일에 저장하거나 출력하지 않는다. 어떤 명령도 model prompt, login/logout, 실제 enrollment, browser, chezmoi, tmux 또는 git write를 실행하지 않는다.

교차 회귀는 compatibility와 security를 별도 성공으로만 판정하지 않는다. 동일한 selected account-home 위험 settings fixture에서 status/launch 성공과 sentinel·MCP·env/permission 주입 부재를 AC-16의 한 테스트에서 동시에 assert한다. AC-20은 project-settings 차단 불변과 account-home 성공 재정의를 같은 기존 테스트에서 교차 확인한다. 전체 suite는 R3.2의 세 명시적 재정의를 제외한 기존 status/exit/redaction/no-fallback/identity isolation 기대값의 회귀를 담당한다.

## Decisions

### D1. child argv에서 설정 source를 차단하고 증명된 경로만 prescan에서 제외한다

verifier와 enrollment helper의 auth status에 `--setting-sources "" --strict-mcp-config`를 적용하고 role launcher의 기존 `--setting-sources ""`에는 `--strict-mcp-config`와 exact-one 재검증을 더한다. status와 strict account-launch의 selected-home prescan만 해당 exec 경계의 trusted seam·admitted command 검증 뒤 조건부 skip하고, `claude_command()`의 project prescan은 유지한다. `admitted_main()`의 selected-home prescan은 제거하되 같은 최종 exec 경계의 mandatory R1.2 재검증으로 대체한다. 이는 정상 account-home settings를 수정하지 않으면서 해당 process가 settings를 읽지 않는 속성을 검증하고 위험 project settings의 기존 차단도 보존하는 채택안이다.

### D2. provider-default home만 무조건 신뢰하는 대안은 기각한다

사용자 본인의 `~/.claude`도 검증 process 관점에서는 untrusted이고 explicit home에도 같은 위험 키가 있을 수 있다. home mode는 security 신뢰도를 나타내지 않는다. 경계는 home 종류가 아니라 실제 child argv의 source 차단 여부다.

### D3. allowlist 확장 대안은 기각한다

위험 키를 allowlist에 넣으면 verifier와 launch가 그 값을 로드할 가능성을 둔 채 검사만 통과하므로 Goal 2와 충돌한다. compatibility는 파일을 benign으로 선언하지 않고 process 입력에서 제외해 해결한다.

### D4. broad mode flag와 bare mode는 기각한다

`--safe-mode`와 `--restricted`는 auth probe에서 동작했지만 role의 plugin·instruction·tool·permission 동작을 넓게 바꾼다. `--bare`는 OAuth와 Keychain을 읽지 않아 consumer identity 판정 계약을 깨뜨린다. 필요한 source와 MCP 경계에 직접 대응하는 두 flag만 채택한다.

### D5. profile2 enrollment는 사용자 전경의 명시적 단계로 유지한다

`enrollment_required`와 `identity_enroll_foreground`는 setup backend가 실행할 명령이 아니라 사용자에게 제공하는 descriptor다. 문서는 exact helper 명령과 재검증 순서를 제공하지만 자동 실행, browser interaction, fallback을 추가하지 않는다.

### D6. hardening flag를 portable CLI required-option 계약에 편입한다

지원 version 범위를 좁히거나 미광고 option을 provider session 실패까지 미루지 않는다. 모든 Claude manifest, 런타임 expected list와 설치 checker required 목록에 두 option을 추가하고 runtime help probe가 미광고 installation을 session exec 전에 차단한다. 이때 “provider 호출 0회”는 provider **session exec 0회**를 뜻하며 필수 read-only `--version`·`--help` probe는 허용한다. 이 정의로 직전 비차단 finding `SPEC-008`을 닫는다.

### D7. 방향 B로 온디스크 fixture를 보존하고 테스트 내부 fake CLI를 사용한다

fixture를 5-option으로 수정하는 방향 A를 기각한다. 대기 중인 #118이 `tests/fixtures/orchestrator-profiles/**`의 의미와 bytes 보존을 전제로 하므로 교차 작업 충돌 위험이 있다. 방향 B는 provider별 helper help 분기와 expected literal을 5-option으로 동기화해 `PLAN-001`·`PLAN-002`를 닫고, `test_portable_cli_contract:5191-5210`의 Claude in-range만 test-local fake로 전환해 `PLAN-007`을 닫는다. codex help, 실패군 여섯 개, codex in-range fixture 기대값과 installed-checker 네 probe는 그대로다. R3.2의 다른 두 기존 테스트 재정의도 `tests/test_orchestrator_profiles.py` 안에만 있어 AC-14의 동작 판정, AC-15의 scope 판정, AC-19의 byte 판정을 모두 통과해야 하며 fixture 불변과 account-home 성공 전환을 완화하지 않는다.

### D8. scope checker의 비교 집합과 제외 집합을 Spec에서 확정한다

비교 집합은 R3.3에 적은 `git status --porcelain` 경로에서 새 산출물, 직전 보존 산출물, quality-state prefix를 제외한 전부다. 나머지는 10개 허용 파일의 부분집합이어야 한다. 제외된 직전 산출물은 별도 frozen tree digest로 보존을 판정한다. 이 결정으로 직전 비차단 finding `SPEC-007`을 닫는다.

### D9. 설치 checker의 기존 version mismatch를 이번 배포 gate에서 분리한다

직접 실행 실패는 `EXPECTED_VERSIONS["claude"]="2.1.272"`와 설치본 2.1.274를 exact-equality 비교하기 때문이며 변경 전 증거가 있다. 이 작업은 required-option 상수만 갱신한다. 설치본 동작은 CMD-4와 CMD-2의 fake help fail-closed가 판정하며 frozen version evidence 갱신은 별도 작업이다.

<!-- strict-only:start -->

This block is required only for strict work. Any inapplicable subsection must be removed for non-strict work; within strict work, mark it as not applicable with a reason before review.

### Threat and trust boundaries

신뢰 입력은 검토된 registry·role manifest·adapter source, digest 검증된 합성 settings/instruction/plugin, 기존 검사를 통과한 trusted verifier seam, exact argv builder/validator다. untrusted 입력은 user/project/local settings, caller provider arguments, verifier/provider stdout·stderr, account home 내용, 현재 auth state와 enrollment 전 identity다. 온디스크 test fixture는 실행 의미를 검증하는 immutable input이지 production trust source는 아니다.

주요 위협은 settings hook 명령 실행, MCP server 기동, env/permission 주입, duplicate option에 의한 hardening 무효화, forged admitted command, raw auth JSON 유출, 다른 profile identity overwrite, 테스트 fixture 의미 변경으로 인한 false pass다. 통제는 두 차단 flag, exact-one argv 검사, caller override 거부, 미확인 경로의 prescan/fail-closed, captured/redacted adapter, explicit-only enrollment, sentinel negative control, immutable fixture digest다.

trust boundary는 verifier/enrollment helper의 Claude exec, role launcher의 provider argv 생성, admitted role process의 최종 provider session exec 세 곳이다. 각 경계는 앞 단계 환경 flag 하나를 신뢰하지 않고 자기 책임의 hardening을 강제한다.

### Authorization and tenant isolation

account authorization은 기존 directory mapping과 binding generation을 유지한다. `~/code/profile1`은 `claude-profile1`, `~/code/profile2`는 `claude-profile2`에만 매핑되며 selection priority나 scope를 바꾸지 않는다. profile1 provider-default와 profile2 explicit home 사이에 파일 복사·rename·symlink를 허용하지 않는다.

identity enrollment write 권한은 사용자가 명시 호출한 helper와 선택된 profile의 host-local identity digest 경로에만 있다. status와 launch에는 enrollment write 권한이 없다. profile2 enrollment가 profile1 digest나 account home에 쓰면 테스트는 실패해야 한다. duplicate mapping, identity drift와 usage dual consent의 기존 fail-closed admission을 유지한다.

새 network service, OS user role 또는 ACL을 만들지 않으므로 별도 OS multi-tenant migration은 해당하지 않는다. 이 작업의 tenant 경계는 local account profile과 그 credential/identity home이다.

### Migration, compatibility, and rollback

registry schema, enrollment schema, public status JSON, launch record, account alias와 home layout은 바뀌지 않아 data migration이나 backfill이 없다. 모든 Claude role manifest, runtime expected list, 설치 checker required list와 test helper를 5-option으로 함께 맞춘다. Claude Code 2.1.274에서 exact auth argv와 canonical projection 동일성을 확인하기 전에는 rollout하지 않는다.

rollback trigger는 live projection mismatch, sentinel/MCP/env/permission capture, duplicate option 우회, fixture tree digest mismatch, scope 위반, R3.2에서 재정의하지 않은 baseline 기대값의 회귀, 세 재정의 테스트의 새 기대값 실패, profile2 lifecycle 실패다. rollback은 허용 10개 파일의 task 변경을 되돌리고 rollout을 중단하는 것이다. 사용자 settings·credential·identity, 온디스크 fixture와 보존 산출물은 건드리지 않는다. allowlist 확장이나 hardening 없는 prescan 제거 상태로 rollback하지 않는다.

### Failure recovery and observability

운영 신호는 public status와 exit code다. profile1 성공은 `ready`/0이고 profile2 미등록 정상 상태는 `enrollment_required`/3과 `identity_enroll_foreground`다. CLI option 미지원은 `blocked_cli_contract`/4, 미하드닝·오염 argv는 `blocked_policy` 또는 `blocked_contract`로 관측한다.

테스트 신호는 exact argv capture, version/help probe와 provider session exec의 분리 계수, sentinel/MCP/env/permission capture 부재, fixture/보존 산출물 tree digest, compact JSON과 unittest exit다. 새 persistent metric·trace·alert backend는 local CLI 저장소이므로 해당하지 않는다. 로그에는 profile alias, public status와 safe boolean만 허용하고 raw stdout/stderr, email, `orgId`, account ID, identity와 digest는 넣지 않는다.

### High-risk end-to-end verification

고위험 경로는 위험 settings가 있는 provider-default profile1의 status와 strict role launch를 수행하는 격리 E2E다.

1. 구현 전 positive control이 현재 prescan 때문에 `blocked_policy`/4로 실패함을 기록한다.
2. unhardened negative control이 sentinel을 생성해 fixture 탐지 능력을 증명한다. 이 단계가 실패하면 뒤 판정은 무효다.
3. 같은 selected account-home settings를 바꾸지 않은 production path에서 AC-16이 status `ready`/0, provider session exec 1회, exact hardened argv, sentinel·MCP·env/permission capture 0회를 한 테스트에서 동시에 확인한다. AC-20은 별도로 project-settings 위험 키의 기존 차단과 두 account-home 유형의 새 성공·주입 0회를 함께 확인한다.
4. profile2 lifecycle, portable CLI 여덟 case와 installed-checker 네 probe, fixture tree digest와 exact scope를 확인한다.
5. CMD-4가 설치본 canonical projection 동일성을 값 비노출로 확인하고 CMD-3·CMD-5가 기존 suite를 보존한다.

중단 조건은 projection mismatch, raw 값 노출, sentinel/MCP/env/permission capture, provider 중복 session exec, `blocked_policy` 재발, 자동 enrollment, fixture 또는 사용자 파일 변경, scope 위반, 기존 suite 실패 중 하나다. 전부 통과하기 전에는 high-risk verification을 PASS로 기록하지 않는다.

### No production mutation confirmation

자동 workflow에는 production mutation이 없다. `chezmoi apply`, 실제 login/logout, browser OAuth, 실제 identity enrollment, model 호출, tmux/session 조작, git write, commit/push/merge를 실행하지 않는다. 합성 enrollment는 임시 `AI_SESSION_IDENTITY_ROOT`에만 기록하고 폐기한다. 유일한 live 동작 CMD-4는 auth status 두 조합을 읽기 전용으로 메모리 비교하며 값이나 파일을 남기지 않는다. `tests/fixtures/**`, 실제 Claude home, profile별 credential home과 직전 산출물은 모든 자동 판정에서 불변이다.

<!-- strict-only:end -->
