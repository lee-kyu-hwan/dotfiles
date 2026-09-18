# Quality Goal Specification

- Task ID: 20260917T051955Z-111-설정-호환성-결함을-방향-b-verifier-identity-기반-467cbcd9
- Mode: strict
- Status: SPEC_REVIEW
- Created: 2026-09-17
- Updated: 2026-09-17
- Source goal: #111 profile1의 기본 Claude 설정 호환성 결함을 정본 verifier 경로 동일성과 온디스크 fixture 불변 조건 아래에서 해결한다

## Problem and context

GitHub 이슈 #111의 실경로 smoke에서 `~/code/profile1/111-account-profile-smoke`는 `claude-profile1`을 정상 선택하지만 status가 `{"status":"blocked_policy"}`와 exit 4를 반환한다. 실패 재현의 exact `--verifier`는 정본 설치 경로가 아니라 저장소 소스 경로 `/Users/lee-kyu-hwan/code/profile1/dotfiles/111-profile-onboarding/dot_local/libexec/executable_ai-session-verify-claude`였다. 근거는 `.claude/quality-state/20260917T002844Z-111-프로필별-실경로-smoke의-기본-claude-설정-호환성-결함-f76eb54a/evidence/repro.sh:5`의 `VER="$REPO/dot_local/libexec/executable_ai-session-verify-claude"`다. 같은 절차에서 `~/code/profile2/111-account-profile-smoke`가 반환하는 `enrollment_required`와 exit 3은 명시적 identity enrollment 전의 설계된 정상 상태다. 재현 전문은 같은 evidence directory의 `repro-baseline.txt`에 있다.

오케스트레이터가 2026-09-17에 `.claude/quality-state/20260917T051955Z-111-설정-호환성-결함을-방향-b-verifier-identity-기반-467cbcd9/evidence/repro-canonical-verifier.txt`로 두 경로를 대비 측정했다. 정본 `${HOME}/.local/libexec/ai-session-verify-claude`, 즉 `/Users/lee-kyu-hwan/.local/libexec/ai-session-verify-claude`는 실제로 존재하는 regular non-symlink 실행 파일이다. 현재 구현에서는 재현에 쓴 소스 경로와 정본 경로가 모두 `blocked_policy`, exit 4다. 방향 (가) 적용 후에는 문서화된 정본 경로 운영 명령만 `ready`, exit 0으로 전환하고 소스 경로를 포함한 다른 verifier 경로는 의도적으로 `blocked_policy`, exit 4를 유지한다. 따라서 사용자 가시 결함은 운영자가 두 문서의 정본 경로 명령으로 전환하는 것으로 닫히며, 비정본 경로 차단은 보안 설계다.

직접 원인은 `dot_local/bin/executable_ai-session:104-108,995-1041`의 설정 prescan이다. `claude-profile1`은 `dot_config/ai-session/accounts.toml:18-26`에서 `config_home_mode = "provider_default"`이므로 사용자 `~/.claude`가 선택된다. `BENIGN_CLAUDE_SETTING_TYPES`는 `$schema`(string), `spinnerTipsEnabled`(boolean), `theme`(string)만 허용하고, allowlist 밖 키는 `blocked_policy`가 된다. 아래 **실측 16개 키 fixture 계약**은 실제 값을 제외하고 키 이름과 JSON 타입만 고정한다. allowlist와 이름·타입이 모두 일치하는 키는 `theme` 하나뿐이다.

| 키 | JSON 타입 | 키 | JSON 타입 |
|---|---|---|---|
| `env` | object | `effortLevel` | string |
| `permissions` | object | `modelSettings` | object |
| `model` | string | `skipWorkflowUsageWarning` | boolean |
| `hooks` | object | `theme` | string |
| `statusLine` | object | `skipAutoPermissionPrompt` | boolean |
| `enabledPlugins` | object | `autoMode` | object |
| `extraKnownMarketplaces` | object | `mcpServers` | object |
| `language` | string |  |  |
| `alwaysThinkingEnabled` | boolean |  |  |

prescan은 보존해야 할 보안 통제다. `dot_local/libexec/executable_ai-session-verify-claude:44-56`와 `dot_local/libexec/executable_ai-session-enroll-identity:122-142`의 비대화형 인증 조회는 현재 `claude auth status --json`을 설정 source 차단 없이 실행한다. user/project/local settings의 `hooks`, `mcpServers`, `env`, `permissions` 개입을 fail-closed로 막는 것이 prescan의 목적이다. `dot_local/bin/executable_ai-role-session:1046-1060`의 role 명령은 이미 digest 검증된 `--settings`와 `--setting-sources ""`를 사용하지만 `--strict-mcp-config`는 아직 없다.

설치된 Claude Code 2.1.274의 2026-09-17 읽기 전용 probe에서 exact argv `claude --setting-sources '' --strict-mcp-config auth status --json`은 exit 0이었고 baseline과 같은 JSON 키 집합을 반환했다(`probe-argv.txt`, `probe-flags.txt`). 오케스트레이터는 같은 날 설치본 `claude --help`가 `--setting-sources <sources>`와 `--strict-mcp-config`를 모두 광고함도 직접 확인했다. 따라서 fake Claude를 만들지 않고 실제 설치본을 probe하는 `test_claude_settings_prescan`, `test_effective_setting_sources`, `test_claude_plugin_policy`는 required-option이 다섯 개가 된 뒤에도 `blocked_cli_contract`로 바뀌지 않는다. 다만 `dot_local/libexec/ai_session_identity.py:31-53`의 `canonical_identity()`가 투영하는 `loggedIn`, `authMethod`, `subscriptionType`, UUID 정규화 `orgId`의 **값** 동일성은 별도 읽기 전용 opt-in 판정이 필요하다.

앞선 두 strict 실행은 모두 “변경이 깨뜨리는 기존 테스트의 불완전 열거” 때문에 종료됐다. 첫 실행은 Plan에서 온디스크 Claude in-range fixture 의존을 빠뜨려 `PLAN-007` Critical이 됐고, 둘째 실행은 status prescan skip이 `tests/test_ai_session.py:934-976`을 뒤집는 사실을 빠뜨려 `SPEC-001`이 재발했다. 이번 열거는 추정이 아니라 오케스트레이터가 네 축으로 소스를 다시 전수 감사한 결과이며, 증거는 `.claude/quality-state/20260917T051955Z-111-설정-호환성-결함을-방향-b-verifier-identity-기반-467cbcd9/evidence/blast-radius-audit-v2.md`다. R3.2와 AC-15가 그 결과를 동결한다.

저장소는 chezmoi source다. `chezmoi apply` 없이 실행 권한이 없는 source를 `/opt/homebrew/bin/python3.14`로 직접 검증한다. baseline은 `tests/test_ai_session.py` 29개와 `tests/test_orchestrator_profiles.py` 92개, 합계 121개가 통과한다. 설치 계약 checker는 변경 전부터 동결 증거 2.1.272와 설치본 2.1.274의 차이로 `claude installed version differs from frozen evidence`, exit 1이며 이 사전 실패는 이번 회귀가 아니다(`checker-baseline.txt`).

## Goals

1. 정상 기본 `~/.claude` 설정을 가진 Mac에서 두 운영 문서에 byte-identical하게 실린 `${HOME}/.local/libexec/ai-session-verify-claude` 정본 verifier의 exact profile1 status 명령이 `ready`, exit 0에 도달하고, 검토된 role `launch`가 설정 키 때문에 `blocked_policy`로 차단되지 않게 한다.
2. verifier, enrollment helper, role launch의 Claude process가 미검토 user/project/local settings의 `hooks`, `mcpServers`, `env`, `permissions`를 로드하거나 실행하지 못하게 코드로 강제하며 allowlist를 확장하지 않는다.
3. status prescan skip을 해당 provider의 정본 verifier 경로로 좁히고, 정본 verifier의 양성 경로와 임의 주입 verifier의 음성 경로를 같은 위험 settings에서 대비한다.
4. baseline과 하드닝된 인증 조회가 canonical identity 입력값을 동일하게 제공함을 비밀 없는 읽기 전용 판정으로 확인한다.
5. `claude-profile2`의 사전 enrollment 상태와 사용자 전경 enrollment 뒤 `ready`에 도달하는 절차를 회귀 테스트와 운영 문서로 증명한다.
6. 기존 121개 테스트를 보존하되 R3.2의 기존 네 지점만 명시적으로 재정의하고, `tests/fixtures/**`를 바이트 불변으로 유지한다.

## Non-goals

- `tests/check_installed_orchestrator_cli_contract.py`의 `EXPECTED_VERSIONS`와 frozen evidence 버전은 갱신하지 않는다. 이는 별도 이슈 `#126` 범위다. 이번 작업은 `EXPECTED_REQUIRED["claude"]`만 5-option으로 동기화하고 checker의 기존 exit 1을 배포 gate로 쓰지 않는다.
- `claude-profile2` identity enrollment, browser login, logout 또는 account 전환을 자동 실행하지 않는다.
- `~/.claude/settings.json`을 포함한 사용자 설정·credential·token·session·identity를 수정·이동·복사·rename·symlink하지 않는다.
- `claude-profile1`의 `config_home_mode = "provider_default"`와 workspace mapping을 변경하지 않는다.
- consumer 계정 간 자동 fallback, ranking, rotation, 사용량 기반 선택 또는 실행 중 account hot-swap을 도입하지 않는다.
- `BENIGN_CLAUDE_SETTING_TYPES`에 `hooks`, `mcpServers`, `env`, `permissions` 또는 다른 새 키를 추가하지 않는다.
- role 세션에서 배포된 `dot_claude/dot_mcp.json`의 MCP server를 유지하거나 별도 digest 검증 `--mcp-config`로 다시 공급하지 않는다. 이번 보안 경계에서 검토된 role 세션은 MCP server 없이 동작한다.
- verifier 파일 SHA-256을 source 상수로 고정하지 않는다.
- `dot_config/ai-session/accounts.toml`, `tests/fixtures/**`, #118 소유 경로, `docs/development/2026-09-17-111-profile-settings-compat/`, `docs/development/2026-09-17-111-profile-settings-compat-2/`를 수정하지 않는다.
- `chezmoi apply`, 실제 model 호출, 실제 identity enrollment, login/logout, browser, tmux/session 조작, git write, commit/push, PR merge를 구현·판정 과정에서 실행하지 않는다.
- token, API key, 이메일, account ID 원문, `orgId` 원문, canonical identity 원문 또는 전체 identity digest를 저장소·문서·로그·fixture에 기록하지 않는다.

## Requirements

- **R1.1** Claude verifier와 명시적 identity enrollment helper의 모든 비대화형 공식 인증 조회는 exact argv `claude --setting-sources "" --strict-mcp-config auth status --json`을 이 순서 그대로 사용해야 한다. 기존 10초 timeout, captured stdout/stderr, `close_fds=True`, empty `pass_fds`, nonzero·timeout·malformed JSON fail-closed와 redacted six-field verifier 출력 계약을 유지하고 raw stdout/stderr 또는 identity 원문을 출력·저장하지 않는다. [근거: `dot_local/libexec/executable_ai-session-verify-claude:44-56`; `dot_local/libexec/executable_ai-session-enroll-identity:122-142`; `probe-argv.txt`]
- **R1.2** 검토된 Claude role launch의 최종 provider argv는 exact one `--setting-sources ""`, exact one `--strict-mcp-config`, digest 검증된 `--settings`를 가져야 한다. role 세션에는 `--mcp-config`를 공급하지 않으며 배포된 `dot_claude/dot_mcp.json`의 `maestro`를 포함해 MCP server를 0개 시작한다. 이는 비대화형 verifier·enrollment 조회에서 MCP가 불필요하다는 판단과 별개로, role 세션의 사용자 가시 MCP 기능 손실을 보안 결과로 수용한 계약이다. 네 Claude role manifest, `verify_provider_cli_contract()`의 Claude required list, 설치 checker의 `EXPECTED_REQUIRED["claude"]`는 exact ordered list `--append-system-prompt`, `--settings`, `--plugin-dir`, `--setting-sources`, `--strict-mcp-config`로 일치해야 한다. 지원 범위 `>=2.1.269,<2.2.0` 안이어도 help가 두 하드닝 flag 중 하나를 광고하지 않으면 provider session exec 전에 `blocked_cli_contract`, exit 4로 닫는다. caller의 `--settings`, `--setting-sources`, `--strict-mcp-config`, `--mcp-config` 중복·재정의와 forged admitted argv는 provider session exec 전에 `blocked_policy` 또는 `blocked_contract`로 거부한다. [근거: `dot_local/bin/executable_ai-role-session:57-70,741-793,1004-1060,1271-1336`; `dot_config/ai-session/roles.toml`; `dot_claude/dot_mcp.json`; `tests/check_installed_orchestrator_cli_contract.py:27-30`]
- **R1.3** prescan 네 호출 지점의 최종 상태를 다음처럼 고정한다. (1) `executable_ai-session:1517`의 `launch()` selected-home prescan은 provider=claude, strict registry, 유효한 `ROLE_CONTRACT_ID`, `AI_ROLE_ADMITTED=1`, trusted `--admitted` command shape, metadata provider 일치, 내포 최종 provider argv의 R1.2 exact-one 검증을 모두 통과할 때만 skip한다. (2) `executable_ai-session:1558-1559`의 `status()` selected-home prescan은 provider=claude이고 `--verifier`가 기존 절대경로·regular·leaf non-symlink·executable 네 검사와 **해당 provider 정본 경로 동일성**을 모두 통과할 때만 skip한다. 이 skip 술어는 prescan보다 먼저 평가하되 어떤 파일 검사·경로 계산 실패에서도 raise하지 않는다. 실패는 skip 권한만 제거해 prescan을 그대로 실행하며, 위험 settings가 없어서 다음 단계로 진행한 invalid verifier는 뒤의 기존 `verify_admission()`이 `blocked_verifier`로 만든다. 위험 settings와 invalid verifier가 함께 있으면 먼저 실행되는 prescan의 기존 `blocked_policy`, exit 4가 유지된다. 정본 경로 계산의 유일한 source는 `executable_ai-session`의 함수로 두며, `ai-session launch`는 verifier 생략 시 이 함수로 기본값을 채운다. `executable_ai-role-session`은 기본 verifier 경로 문자열을 계산하지 않고 caller가 주지 않았을 때 옵션 자체를 생략한다. 정본 경로의 HOME source는 child `environment` dict나 pwd database가 아니라 현재 `ai-session` 프로세스의 `os.environ["HOME"]`다. HOME은 nonempty absolute path여야 하며 unset·empty·비절대이면 정본을 계산하거나 pwd로 fallback하지 않고 술어를 false로 만들어 prescan을 유지한다. 유효 HOME에서 `${HOME}/.local/libexec/ai-session-verify-{provider}`와 supplied path를 `expanduser` 후 `abspath`/`normpath`로 lexical 정규화해 후행 slash와 `..`를 제거하고 문자열 동일성을 비교하되 `resolve()`는 사용하지 않는다. 이는 다른 symlink spelling이 같은 target으로 해석돼 정본으로 승격되는 일을 막으며, 기존 leaf non-symlink 검사는 별도로 유지한다. 소스 트리 경로를 포함한 다른 verifier는 executable이어도 skip 권한이 없고 위험 settings에서 의도적으로 `blocked_policy`, exit 4를 유지한다. (3) `executable_ai-role-session:1016`의 `claude_command()` project prescan은 무조건 유지한다. (4) `executable_ai-role-session:1303-1304`의 `admitted_main()` selected-home prescan은 제거하고 `os.execvpe` 직전에 metadata provider 일치와 최종 Claude argv의 R1.2 계약을 의무 재검증한다. 실패는 `blocked_contract`, provider session exec 0회다. 그 밖의 legacy·임의 경로는 기존 prescan 또는 명시적 거부로 fail-closed한다. [근거: `dot_local/bin/executable_ai-session:995-1041,1221-1266,1500-1583`; `dot_local/bin/executable_ai-role-session:985-1017,1271-1336,1444-1445`]
- **R1.4** 설치된 Claude Code 2.1.274에서 baseline 인증 조회와 R1.1의 하드닝 조회는 `loggedIn`, `authMethod`, `subscriptionType`, UUID로 정규화한 `orgId` 값이 동일해야 한다. 비교는 메모리에서만 수행하고 safe boolean과 exit code만 노출한다. 값 불일치, 필드 누락, 타입 오류, UUID 오류는 판정 실패이며 identity를 `matched`나 `ready`로 승격하지 않는다. fixture에서도 두 경로의 canonical digest와 verifier 상태가 동일해야 한다. [근거: `dot_local/libexec/ai_session_identity.py:31-53`; `probe-flags.txt`]
- **R2.1** 실측 16개 키 fixture 계약과 정확히 같은 키 이름·JSON 타입을 가진 임시 provider-default Claude home에서, 유효한 합성 login·identity·usage 입력을 사용하고 profile1 mapped cwd에서 exact 운영 명령 `ai-session status --registry "${HOME}/.config/ai-session/accounts.toml" --provider claude --role-profile general --verifier "${HOME}/.local/libexec/ai-session-verify-claude" --accept-usage-unknown`을 실행하면 `ready`, exit 0이고 `blocked_policy`가 아니어야 한다. 같은 위험 settings에서 verifier만 재현의 저장소 소스 경로나 임시 디렉터리의 임의 executable로 바꾸면 prescan을 skip하지 않고 의도적으로 `blocked_policy`, exit 4여야 한다. 두 경로 모두 실제 user home이나 identity root를 읽거나 쓰지 않는다. [근거: `repro.sh:5`; `repro-canonical-verifier.txt`; `tests/test_ai_session.py:83-130,934-976`; `dot_config/ai-session/accounts.toml:18-26`]
- **R2.2** 같은 격리 fixture의 검토된 `claude-profile1` role launch는 account admission과 role dispatch를 통과해 fake provider session을 정확히 한 번 실행해야 한다. 최종 argv는 R1.2를 만족하고 sentinel hook·MCP child·env·permission 주입은 없어야 한다. 배포된 `dot_claude/dot_mcp.json`이 존재해도 role provider session은 MCP server를 시작하지 않으며, 실제 Claude model, login, tmux, chezmoi를 호출하지 않는다. [근거: `dot_local/bin/executable_ai-session:1500-1552`; `dot_local/bin/executable_ai-role-session:1386-1480`; `dot_claude/dot_mcp.json`]
- **R2.3** `claude-profile2`는 enrollment file이 없는 격리 fixture에서 exact status 명령 `ai-session status --registry "${HOME}/.config/ai-session/accounts.toml" --provider claude --role-profile general --verifier "${HOME}/.local/libexec/ai-session-verify-claude" --accept-usage-unknown`으로 `enrollment_required`, `identity_status="not_enrolled"`, `identity_enroll_foreground`, exit 3을 유지해야 한다. 사용자가 exact helper 명령 `ai-session-enroll-identity --registry "${HOME}/.config/ai-session/accounts.toml" --provider claude --account-profile claude-profile2`를 전경에서 한 번 실행하면 임시 identity root에만 v2 digest가 생성되고 새 exact status는 `ready`, exit 0이어야 한다. `${HOME}`는 POSIX shell이 실행 전에 absolute home으로 확장하고 registry는 absolute file, verifier는 absolute regular leaf non-symlink executable이어야 한다. helper에는 parser가 받는 세 option만 전달하며 backend 자동 호출과 profile 간 복사는 금지한다. [근거: `dot_local/bin/executable_ai-session:933-945,2139-2142`; `dot_local/libexec/executable_ai-session-enroll-identity:26-32,213-273`]
- **R3.1** 보안 회귀 fixture는 임시 Claude home의 `settings.json`에 sentinel을 쓰는 hook과 `mcpServers`, `env`, `permissions`를 넣어야 한다. 같은 fake Claude를 하드닝 flag 없이 호출하는 negative control은 sentinel을 생성해야 하고 R1.1·R1.2 경로는 sentinel·MCP child·설정 기반 env/permission capture를 하나도 생성하지 않아야 한다. enrollment argv 회귀는 `AI_SESSION_SYNTHETIC_TEST`와 `AI_SESSION_SYNTHETIC_STATUS_JSON`을 unset한 실제 subprocess 분기에서 PATH 선두 fake Claude를 정확히 한 번 실행해야 한다. [근거: `dot_local/bin/executable_ai-session:995-1041`; `dot_local/bin/executable_ai-role-session:985-1001`; `dot_local/libexec/executable_ai-session-enroll-identity:122-142`]
- **R3.2** 기존 기대값/내용이 바뀌는 **수정 지점**은 아래 **정확히 네 개**다. 이 수정 지점 열거는 `blast-radius-audit-v2.md`의 네 축 소스 전수 재감사 결과이며, 전체 suite 통과의 충분성 근거로 쓰는 **영향받는 테스트 메서드·케이스** 열거와 세는 단위를 혼용하지 않는다.
  1. `test_claude_untrusted_settings_prescan`의 account-home 구간만(`tests/test_orchestrator_profiles.py:2124-2178`) 바뀐다. `{"hooks":{}}`는 exit 4에서 하드닝 argv 성공으로 바뀌고 project 구간(`:2059-2090`)과 `{"theme":"dark"}` 대조군(`:2144`)은 불변이다.
  2. `test_claude_official_status_contract`(`:3014`)의 exact verifier argv만 R1.1로 바뀌며 `:3015`의 `open_fds == []`는 유지된다.
  3. `test_portable_cli_contract`의 Claude 3-option literal(`:5130-5132`)과 Claude in-range fixture 의존(`:5191-5210`)만 바뀐다. lower·upper·missing-option 여섯 case와 codex in-range는 기존 fixture·기대값을 유지하고 Claude in-range만 test-local 5-option fake CLI를 쓴다.
  4. `make_fake_executable` helper(`:183`)의 공유 help literal을 provider별로 나눠 Claude가 다섯 option을 광고하게 한다. `:168`의 `--version` exact `2.1.272 (Claude Code)`는 불변이다.

  R1.2의 5-option 계약 정의만 바꾸고 테스트를 한 줄도 바꾸지 않은 스크래치 공유 클론 실측에서는 `tests/test_ai_session.py` 29개가 그대로 통과했고, `tests/test_orchestrator_profiles.py`는 아래 **8개 메서드 / 10개 케이스**가 실패했다.

  1. `test_portable_cli_contract`: 1케이스.
  2. `test_claude_untrusted_settings_prescan`: 2케이스(`claude-profile1`, `claude-profile2`, 둘 다 `source='selected-account-home'`).
  3. `test_verifier_provider_environments`: 2케이스(`profile1`, `profile2`).
  4. `test_stale_pwd_rejected`: 1케이스.
  5. `test_account_root_permission_separation`: 1케이스.
  6. `test_no_opposite_root_grant`: 1케이스.
  7. `test_exact_git_common_dir_permission`: 1케이스.
  8. `test_chezmoi_fixture_render`: 1케이스.

  실패 원인은 모두 fake Claude의 공유 `--help`가 새 두 option을 광고하지 않아 `verify_provider_cli_contract()`가 앞단 기대보다 먼저 `blocked_cli_contract`/4를 낸 것이다. 수정 지점 4의 `make_fake_executable` 공유 help literal(`tests/test_orchestrator_profiles.py:183`) 한 곳을 고치면 3~8번의 **여섯 메서드가 함께 해소**된다. 이 여섯 메서드, 특히 `test_exact_git_common_dir_permission`과 `test_chezmoi_fixture_render`는 기대값을 고치는 대상이 아니며 helper를 고쳐 원래 상태·exit 기대를 복원하는 대상이다. 충분성 주장은 수정 지점 수가 아니라 이 실측 메서드·케이스 전수와 최종 전체 suite 결과를 근거로 삼는다. 이 열거는 추론이 아니라 `.claude/quality-state/20260917T051955Z-111-설정-호환성-결함을-방향-b-verifier-identity-기반-467cbcd9/evidence/cli-contract-blast-radius-measured.md`의 HEAD `56d65ca`, baseline 29/92 green 뒤 계약 정의만 바꾼 실측 결과다.

  이 8메서드/10케이스는 R1.2 CLI 계약 확장 **한 축만** 적용한 하한선이다. R1.3(2)의 status prescan skip 축으로 영향받는 `test_status_blocked_binding_and_policy_exact_json`(`tests/test_ai_session.py:934-976`)은 경로 동일성 설계 때문에 최종 구현에서는 기존 `blocked_policy`/4를 유지해야 하고, R1.1 verifier argv 하드닝 축으로 영향받는 `test_claude_official_status_contract`(`tests/test_orchestrator_profiles.py:2985-3015`)은 `:3014` exact argv를 R1.1로 바꾸되 `:3015` FD 기대를 유지해야 한다. 따라서 위 단일 축 실측만으로 세 축 구현의 충분성을 주장하지 않는다.

  구현 Plan은 실제 구현 착수 전에 R1.1 argv 하드닝, R1.2 CLI 계약 확장, R1.3(2) prescan skip의 세 축을 모두 적용한 상태를 같은 방식으로 재측정하는 선행 태스크를 둔다. 재측정은 `git clone -s` 스크래치 공유 클론에서 HEAD `56d65ca` baseline 29/92 green을 확인한 뒤 테스트를 편집하지 않고 prospective 세 축만 적용해 두 전체 suite를 실행하며, 실제 worktree·원본 저장소·설치본을 건드리지 않는다. 전체 실패 메서드·케이스와 원인, 원래 기대를 바꾸는 지점과 helper 수정으로 원래 기대가 복원되는 지점을 분리한 결과를 `.claude/quality-state/20260917T051955Z-111-설정-호환성-결함을-방향-b-verifier-identity-기반-467cbcd9/evidence/cli-contract-blast-radius-three-axis-measured.md`에 보존한다. Plan의 수정 지점 충분성 주장과 구현 태스크 범위는 이 세 축 전수 결과를 근거로 갱신해야 하며, 이 evidence가 완성되기 전 실제 worktree 구현을 시작하지 않는다.

  `tests/test_ai_session.py`의 기존 29개는 최종 재정의 대상이 아니며 모두 기대값 불변이다. `make_verifier`(`:114-130`)가 임시 directory의 `verifier-N`을 만들고 `HOME`도 임시 directory(`:83-87`)이므로 기존 `test_status_blocked_binding_and_policy_exact_json`의 주입 verifier는 정본과 같아질 수 없어 `blocked_policy`/exit 4가 유지된다.

  prescan 검사 경로에 파일을 쓰는 지점은 선택 account home의 `tests/test_ai_session.py:945`, `tests/test_orchestrator_profiles.py:2144,2162`와 project의 `tests/test_orchestrator_profiles.py:1818,1819,2064`, 총 여섯 곳이 전부다. `blocked_policy` 단언이 불변인 테스트는 `test_status_blocked_binding_and_policy_exact_json`, `test_codex_project_config_prescan`, `test_instruction_hash`, `test_claude_plugin_policy`, `test_failure_status`, `test_documentation_contract`, `test_claude_settings_prescan` 일곱 개다.

  Claude 전체 argv exact-equality 단언은 `:3014` 하나뿐이다. `:1308,1309,1315`, `:1087,1088,1109`, `:1477`, `:2735`, `:2820`, `:4632`, `:1996-2009`, `:2040-2046`, `:3093-3094`는 위치·개수·원소 또는 Codex 검사라 `--strict-mcp-config` 추가에도 불변이다. 운영 문서 계약 `test_documentation_contract`(`:5361-5460`)와 `test_profile_onboarding_documentation_contract`(`:3839-`)는 `assertIn`만 사용하므로 block 추가에 불변이고, `test_file_ownership`(`:530`)과 `test_118_status_dependency_and_owned_paths`(`:3913`)도 새 파일을 추가하지 않으므로 불변이다. fake Claude 없이 설치본을 probe하는 `test_claude_settings_prescan`, `test_effective_setting_sources`, `test_claude_plugin_policy`는 2026-09-17의 두 flag 광고 실측 때문에 5-option 계약 뒤에도 통과해야 한다. 세 축 사전 재측정으로 영향 전수를 확정한 뒤 기존 121개 테스트 전체와 추가 회귀가 `/opt/homebrew/bin/python3.14`에서 통과해야 한다.
  `tests/fixtures/orchestrator-profiles/**`와 앞선 산출물의 tree digest는 relative path와 file bytes 보존 계약이다. file mode는 digest 범위 밖이다. portable CLI 회귀가 fixture executable을 임시 복사한 뒤 사용 전에 `chmod`하므로 source fixture mode는 실행 행동이나 배포 판정에 쓰이지 않는다. 이 명시는 위 정확히 네 개의 기대값/내용 재정의 목록을 늘리거나 약화하지 않는다.
- **R3.3** 두 운영 문서는 설정 격리, profile1 호환성, profile2 lifecycle을 문서화한다. profile1 block은 profile1 mapped cwd에서 실행할 exact status 명령 `ai-session status --registry "${HOME}/.config/ai-session/accounts.toml" --provider claude --role-profile general --verifier "${HOME}/.local/libexec/ai-session-verify-claude" --accept-usage-unknown`, `ready`/0 결과, 소스 트리 경로를 포함한 다른 verifier가 위험 settings에서 의도적으로 `blocked_policy`/4인 보안 근거를 담고 두 파일에서 byte-identical해야 한다. profile2 block은 R2.3과 byte-identical한 exact status·helper 명령과 `${HOME}` 치환 규칙, `status → 사용자 확인 → 전경 helper → 새 status → ready`의 status·exit·복구 경계를 담는다. 설정 격리 block은 verifier·enrollment의 비대화형 조회에는 MCP가 필요 없어 `--strict-mcp-config`를 쓰며, role 세션은 배포된 `dot_claude/dot_mcp.json`의 server를 포함해 MCP server 없이 동작하는 의도적 호환성 결과임을 운영자에게 알린다. 변경 가능 범위는 정확히 `dot_local/bin/executable_ai-session`, `dot_local/bin/executable_ai-role-session`, `dot_local/libexec/executable_ai-session-verify-claude`, `dot_local/libexec/executable_ai-session-enroll-identity`, `dot_config/ai-session/roles.toml`, `tests/test_ai_session.py`, `tests/test_orchestrator_profiles.py`, `tests/check_installed_orchestrator_cli_contract.py`, `docs/session-account-profiles.md`, `docs/orchestrator-permission-profiles.md`다. scope 비교 대상은 `git status --porcelain` 경로 중 `docs/development/2026-09-17-111-profile-settings-compat-3/`, `docs/development/2026-09-17-111-profile-settings-compat-2/`, `docs/development/2026-09-17-111-profile-settings-compat/`, `.claude/quality-state/` prefix를 제외한 전부이며 나머지는 위 허용 집합의 부분집합이어야 한다. `dot_config/ai-session/accounts.toml`, `tests/fixtures/**`, #118 소유 경로와 앞선 두 실행 산출물은 변경 금지다.

## Acceptance criteria

- **AC-1** verifier fake Claude capture는 exact `claude --setting-sources "" --strict-mcp-config auth status --json`, 호출 1회이며 timeout·FD·redaction 계약을 유지한다. 기존 `test_claude_official_status_contract`도 같은 exact argv와 `open_fds == []`를 단언한다. [실행] (CMD-2 `test_settings_compat_verifier_argv` `test_claude_official_status_contract`)
- **AC-2** enrollment helper는 두 synthetic status 환경변수를 unset하고 PATH 선두 fake Claude subprocess를 실제로 한 번 실행해 AC-1 exact argv를 캡처하며 임시 identity root 밖에 파일을 만들지 않는다. [실행] (CMD-2 `test_settings_compat_enrollment_argv`)
- **AC-3** 네 Claude role의 최종 argv는 exact one `--setting-sources ""`, exact one `--strict-mcp-config`, digest 검증 `--settings`를 갖고 `--mcp-config`는 0개이며, caller override와 forged admitted argv는 provider session exec 전에 거부된다. [실행] (CMD-2 `test_settings_compat_role_launch_argv`)
- **AC-4** 동일한 위험 selected-home settings에서 임시 `${HOME}/.local/libexec/ai-session-verify-claude`에 둔 정본 verifier는 status prescan을 skip해 `blocked_policy`가 아니고, 임시 directory의 `verifier-N` 주입 verifier는 skip하지 않아 exact `blocked_policy`, exit 4다. 두 verifier 모두 기존 네 파일 검사를 통과하도록 만들며 이 대비가 한 테스트에서 성립한다. [실행] (CMD-1 `test_settings_compat_status_canonical_verifier_prescan_gate`)
- **AC-5** `executable_ai-session`만 현재 프로세스의 `os.environ["HOME"]`로 정본 verifier 경로를 계산하고 role launcher에는 기본 경로 literal이 없다. absolute HOME의 `..`·후행 slash 정규화는 정본과 같게 비교되고 symlink spelling·다른 provider·다른 basename은 정본으로 인정되지 않는다. HOME unset·empty·비절대, stat/permission 오류, non-regular·symlink·non-executable verifier에서 skip 술어는 raise하지 않고 false다. 위험 settings와 결합하면 prescan이 먼저 `blocked_policy`/4를 내며, benign settings에서 다음 단계로 간 invalid verifier는 기존 `verify_admission()`의 `blocked_verifier`가 된다. pwd나 child environment fallback은 없고 하드닝 없는 legacy·임의 route는 child 실행 없이 fail-closed하며 allowlist는 불변이다. [실행] (CMD-1 `test_settings_compat_canonical_verifier_path_contract`)
- **AC-6** opt-in live probe는 baseline과 exact-order 하드닝 argv를 각각 읽기 전용 실행해 canonical 네 필드 값을 메모리에서 비교하고 동일할 때만 exit 0이며 출력·파일에 필드 값, 이메일, `orgId`, identity, digest가 없다. [실행] (CMD-4 `test_settings_compat_live_identity_projection`)
- **AC-7** 실측 16개 키와 타입이 정확히 같은 임시 provider-default home에서 정본 verifier를 쓰는 profile1 status는 합성 matched identity에 `ready`, exit 0이고 `blocked_policy`가 아니다. [실행] (CMD-1 `test_settings_compat_profile1_status`)
- **AC-8** 같은 16개 키 fixture의 strict profile1 role launch는 fake provider session을 정확히 한 번 실행하고 최종 argv가 R1.2를 만족하며 `blocked_policy`가 아니다. [실행] (CMD-2 `test_settings_compat_profile1_launch_e2e`)
- **AC-9** 격리 profile2 lifecycle은 R2.3 exact status를 두 번 동일하게 사용하고 그 사이 exact helper만 실행해 `enrollment_required`/3 → `enrolled`/0 → `ready`/0 순서가 되며 helper 자동 호출과 profile 간 복사는 0회다. fixture에서는 `${HOME}`를 임시 absolute home으로 치환한다. [실행] (CMD-2 `test_settings_compat_profile2_enrollment_to_ready`)
- **AC-10** 두 운영 문서의 profile2 block은 R2.3의 exact status·helper 명령, 순서, 세 결과, `${HOME}` 치환 규칙, `backend는 login·enrollment·fallback·profile 간 설정/credential/identity 복사를 자동 실행하지 않는다.`와 `검토된 role 세션은 --mcp-config를 받지 않으며 배포된 dot_claude/dot_mcp.json의 MCP server를 시작하지 않는다.` 문구를 포함하며 두 block이 byte-identical하다. [문서] docs/session-account-profiles.md docs/orchestrator-permission-profiles.md
- **AC-11** unhardened negative control은 sentinel을 생성하지만 hardened verifier와 실제 subprocess enrollment 경로는 sentinel·MCP child·설정 기반 env/permission capture를 하나도 생성하지 않는다. [실행] (CMD-2 `test_settings_compat_auth_status_sentinel`)
- **AC-12** strict role launch는 배포된 `dot_claude/dot_mcp.json`에 `maestro` server가 존재하는 fixture에서도 `--mcp-config` 없이 실행되어 sentinel·MCP child·설정 기반 env/permission capture를 하나도 만들지 않고 fake provider의 정상 capture만 만든다. [실행] (CMD-2 `test_settings_compat_role_launch_sentinel`)
- **AC-13** 모든 신규 `test_settings_compat_*` 기본 회귀는 임시 directory, PATH 선두 fake executable, 합성 identity root를 사용하고 실제 user home·network·model·실행 중 session을 사용하지 않는다. [실행] (CMD-2 `test_settings_compat_isolation_contract`)
- **AC-14** R3.2에 `tests/test_ai_session.py` 기존 테스트 재정의가 없으며 기존 29개 기대값과 `test_status_blocked_binding_and_policy_exact_json`의 `blocked_policy`/4가 유지되고 추가 회귀를 포함한 파일 전체가 통과한다. [실행] (CMD-3 `tests/test_ai_session.py`)
- **AC-15** `blast-radius-audit-v2.md`의 네 축 결과를 동결한 회귀는 기존 기대값/내용 수정 지점을 정확히 네 개로 열거한다: account-home 일부만 바뀌는 `test_claude_untrusted_settings_prescan`, argv만 바뀌고 FD는 유지되는 `test_claude_official_status_contract`, 두 Claude 지점만 바뀌는 `test_portable_cli_contract`, help만 바뀌고 version은 유지되는 `make_fake_executable`. 별도로 R1.2 단일 축 실측의 실패 전수를 `test_portable_cli_contract` 1케이스, `test_claude_untrusted_settings_prescan` 2케이스, `test_verifier_provider_environments` 2케이스, `test_stale_pwd_rejected` 1케이스, `test_account_root_permission_separation` 1케이스, `test_no_opposite_root_grant` 1케이스, `test_exact_git_common_dir_permission` 1케이스, `test_chezmoi_fixture_render` 1케이스의 8메서드/10케이스로 검증한다. 마지막 여섯 메서드는 `make_fake_executable:183`의 공유 Claude help 수정으로 원래 기대가 복원되고 테스트 기대값은 바꾸지 않는다. 같은 회귀는 여섯 settings write 지점, 네 prescan 호출의 R1.3 최종 상태, 일곱 불변 `blocked_policy` 테스트, exact-equality 하나와 나머지 argv 단언 불변, 두 문서 계약과 두 ownership 계약 불변을 R3.2와 동일하게 확인하며, 충분성은 수정 지점 수가 아니라 세 축 사전 재측정 전수와 전체 suite 통과로 판정한다. [실행] (CMD-2 `test_settings_compat_blast_radius_contract` CMD-5 `tests/test_orchestrator_profiles.py`)
- **AC-16** 실제 설치본을 쓰는 기존 `test_claude_settings_prescan`, `test_effective_setting_sources`, `test_claude_plugin_policy`가 5-option 계약 뒤에도 `blocked_cli_contract`로 바뀌지 않고 각각 기존 기대값으로 통과한다. [실행] (CMD-2 `test_claude_settings_prescan` `test_effective_setting_sources` `test_claude_plugin_policy`)
- **AC-17** scope 검사는 R3.3의 네 prefix 제외 집합이 10개 허용 파일의 부분집합인지 판정하고, `accounts.toml`, #118 소유 경로와 앞선 두 실행 산출물의 파일명·bytes가 보존되며 secret·identity 원문이 diff·출력에 없음을 확인한다. 앞선 산출물 tree digest는 relative POSIX path, NUL, 각 file bytes의 SHA-256 hex, NUL을 정렬 결합하는 알고리즘으로 각각 `b0696da4f58eadb344b6c280395e4d5b771d97d6fcaf19a26b50dfc473c0ac39`와 `dab38d7cd26cab3c99c8c4c5c7019c43d0fe375f73baa8c64d2283bd6f827a88`다. 이 digest는 파일명·bytes 계약이며 mode 변경은 범위 밖이다. 보존 산출물은 실행 입력이 아니고 executable fixture mode는 AC-21의 test-local `chmod`가 소유한다. [실행] (CMD-2 `test_settings_compat_scope_and_secret_hygiene`)
- **AC-18** 하나의 교차 회귀에서 동일한 selected-home 16-key 위험 settings를 바꾸지 않은 채 profile1 status `ready`/0과 role provider session 1회가 성공하고, 동시에 verifier·enrollment·role 어느 경로에서도 sentinel·MCP·env·permission 주입이 0회다. [실행] (CMD-2 `test_settings_compat_cross_regression`)
- **AC-19** 네 Claude role manifest, runtime validator, 설치 checker required constant, helper의 Claude help, portable test literal은 exact 5-option이고 helper Claude version은 `2.1.272 (Claude Code)`, codex help·required 3-option은 불변이다. 두 hardening option 각각의 missing-help case는 read-only version/help probe 뒤 provider session exec 0회, `blocked_cli_contract`/4다. Claude in-range만 test-local fake를 사용하고 portable 성공·실패 기대와 installed-checker 네 probe log는 유지된다. [실행] (CMD-2 `test_settings_compat_claude_required_options` `test_portable_cli_contract`)
- **AC-20** 두 운영 문서의 byte-identical 설정 격리 block은 `profile1 provider-default 설정은 보존한다.`, `verifier·enrollment·role provider는 --setting-sources "" --strict-mcp-config로 user/project/local settings와 비검토 MCP를 로드하지 않는다.`, `검토된 role 세션은 --mcp-config를 받지 않으며 배포된 dot_claude/dot_mcp.json의 MCP server를 시작하지 않는다.`를 포함한다. 비대화형 auth 조회의 MCP 불필요 판단과 role 세션의 의도적 MCP 기능 손실을 구분하고, AC-10의 lifecycle block과 함께 기존 문서 계약 테스트도 통과한다. [실행] (CMD-2 `test_settings_compat_documentation_contract` `test_documentation_contract` `test_profile_onboarding_documentation_contract`)
- **AC-21** `tests/fixtures/orchestrator-profiles/**` 7개 파일의 relative path와 bytes는 사전 상태와 같다. AC-17과 같은 tree 알고리즘의 SHA-256은 `8fb61b50e3dbad7c3d8b14d7a3e33535520eedafd6f8aab271b2cc95ad24210d`이며 추가·삭제·rename·내용 변경은 모두 실패다. file mode는 digest와 보존 범위 밖이다. portable CLI test가 fixture executable을 임시 복사한 뒤 사용 전에 필요한 mode로 `chmod`하므로 source mode는 실행 계약에 참여하지 않는다. [실행] (CMD-2 `test_settings_compat_fixture_bytes_unchanged`)
- **AC-22** 기존 `test_claude_untrusted_settings_prescan`은 project의 `hooks`, `permissions`, `env`, `enabledPlugins`, `mcpServers`를 계속 exit 4, `blocked_policy`, dispatch 0회로 차단한다. account-home `{"theme":"dark"}`는 기존 exit 0·verifier 1회·provider session 1회를 유지하고, `{"hooks":{}}`만 하드닝 argv의 exit 0·verifier 1회·provider session 1회로 바뀌며 sentinel·MCP·env·permission 주입은 0회다. [실행] (CMD-2 `test_claude_untrusted_settings_prescan`)
- **AC-23** 두 운영 문서의 profile1 block은 byte-identical하고 R3.3의 exact status 명령을 그대로 포함한다. 회귀는 그 block에서 명령을 추출해 `${HOME}`를 임시 absolute home으로 확장하고 profile1 mapped cwd에서 실행하며, 실측 16-key settings와 합성 matched identity 아래 `ready`, exit 0을 얻는다. 명령의 registry와 verifier option을 생략하거나 정본 verifier 문자열을 바꾸면 테스트가 실패한다. [실행] (CMD-2 `test_settings_compat_profile1_operational_status_command`)
- **AC-24** AC-23과 같은 fixture에서 verifier만 재현에 사용한 저장소 소스 경로 또는 다른 absolute regular leaf non-symlink executable로 바꾸면 두 경로 모두 의도적으로 exact `blocked_policy`, exit 4이고 verifier child는 0회다. 이는 결함 잔존이 아니라 비정본 verifier에 prescan skip 권한을 주지 않는 보안 계약이며 두 운영 문서도 이 결과를 byte-identical하게 알린다. [실행] (CMD-2 `test_settings_compat_profile1_noncanonical_verifier_policy`)
- **AC-25** 구현 변경 전에 `test_settings_compat_status_canonical_verifier_prescan_gate`를 단독 실행한 전사를 `.claude/quality-state/20260917T051955Z-111-설정-호환성-결함을-방향-b-verifier-identity-기반-467cbcd9/evidence/spec-red-canonical-verifier.txt`에 저장한다. 전사는 실행한 exact test 이름, 구현 전 unittest nonzero exit, 정본 positive control의 실제 `blocked_policy`/4와 기대 `ready`/0 불일치, 비정본 negative control의 예상 `blocked_policy`/4 유지, 실행 시각을 포함하고 secret·identity 원문은 포함하지 않는다. 구현 뒤 전사를 덮어쓰지 않으며 CMD-6이 필수 표식을 검증한다. [실행] (CMD-6)
- **AC-26** 구현 Plan은 첫 구현 태스크보다 앞에 R1.1 argv 하드닝, R1.2 CLI 계약 확장, R1.3(2) status prescan skip을 함께 적용한 사전 재측정 태스크를 둔다. 그 태스크는 HEAD `56d65ca`의 `git clone -s` 스크래치 공유 클론에서 baseline 29/92 green을 확인하고, 테스트 무편집 상태로 prospective 세 축을 적용해 두 전체 suite의 모든 실패 메서드·케이스를 수집하며, 실제 worktree·원본 저장소·설치본 무변경과 지정 evidence 보존을 완료해야 다음 구현 태스크로 진행하도록 명시한다. Plan의 영향 범위와 충분성 주장은 이 전수 결과를 입력으로 갱신한다. [문서] docs/development/2026-09-17-111-profile-settings-compat-3/plan.md
- **AC-27** 세 축 사전 재측정 evidence는 스크래치 방식·HEAD·세 축·baseline·테스트 무편집·실제 worktree·원본 저장소·설치본 무변경·두 suite의 전수 요약·메서드/케이스 기반 충분성·실행 시각 표식을 포함하고, 실패가 있으면 모든 메서드와 각 케이스를 이름으로 열거하며 원래 기대 수정과 helper에 의한 원래 기대 복원을 구분한다. 구현 착수 전 CMD-7이 이 evidence를 판정한다. [실행] (CMD-7)

## Requirements traceability

This table maps every requirement to acceptance criteria and the judgement method that proves the mapping.

| Requirement | Acceptance criteria | Judgement method |
|---|---|---|
| R1.1 | AC-1, AC-2 | CMD-2의 verifier·비합성 enrollment exact argv, 호출 수, FD와 redaction 회귀 |
| R1.2 | AC-3, AC-10, AC-12, AC-19, AC-20 | CMD-2의 role argv·override 거부, MCP server 0개, 운영자 고지와 5-option portable CLI fail-closed 회귀 |
| R1.3 | AC-4, AC-5, AC-15, AC-22, AC-23, AC-24, AC-25 | CMD-1의 비치명 정본 술어·HOME 음성 case, CMD-2의 네 prescan 지점·문서화된 정본/비정본 운영 명령, CMD-6의 구현 전 Red 전사 판정 |
| R1.4 | AC-6 | CMD-4의 opt-in 읽기 전용 live canonical projection 비교 |
| R2.1 | AC-4, AC-7, AC-18, AC-23, AC-24, AC-25 | CMD-1의 status 양성/음성, CMD-2의 exact 운영 명령과 비정본 차단, CMD-6의 Red 증거 및 동일 fixture 교차 회귀 |
| R2.2 | AC-8, AC-12, AC-18, AC-20 | CMD-2의 strict role launch, MCP server 0개, 운영자 고지와 compatibility/security 동시 판정 |
| R2.3 | AC-9, AC-10 | CMD-2의 격리 lifecycle과 두 운영 문서의 exact block |
| R3.1 | AC-11, AC-12, AC-13, AC-18 | CMD-2의 negative control, 격리 계약과 auth·role sentinel 검사 |
| R3.2 | AC-1, AC-13, AC-14, AC-15, AC-16, AC-17, AC-19, AC-21, AC-22, AC-26, AC-27 | CMD-2의 수정 지점과 실측 8메서드/10케이스 분리·격리·기존 기대 복원·byte-only tree digest·fixture 판정, CMD-3·CMD-5 전체 suite, Plan의 구현 전 세 축 재측정 태스크와 CMD-7 evidence 판정 |
| R3.3 | AC-10, AC-17, AC-20, AC-21, AC-23, AC-24 | CMD-2의 exact scope·보존·MCP 호환성 고지·profile1 정본 명령·비정본 차단·fixture 불변 판정 |

## Architecture

설정 파일을 더 넓게 신뢰하지 않고 **실행되는 Claude process의 설정 입력면을 닫는 것**을 신뢰 경계로 삼는다.

1. verifier와 enrollment helper는 같은 exact hardened auth argv를 사용한다. `--setting-sources ""`는 user/project/local source를 끄고 `--strict-mcp-config`는 명시되지 않은 MCP 구성을 배제한다.
2. role launcher는 digest 검증된 합성 `--settings`와 두 차단 option을 exact-one으로 생성·검증한다. `--mcp-config`는 공급하지 않아 배포된 MCP server를 시작하지 않는다. manifest, runtime expected list, 설치 checker는 같은 5-option 계약을 선언한다.
3. account launcher가 현재 프로세스의 absolute HOME로 canonical verifier path를 계산하는 유일한 owner다. role launcher는 caller verifier만 전달하며 기본값은 account launcher가 채운다. status의 explicit verifier는 같은 함수가 계산한 canonical path와 lexical-normalized equality를 통과해야 prescan을 skip한다. 술어 실패는 비치명적으로 prescan 유지로 귀결되고 `resolve()`로 symlink alias를 승인하지 않는다.
4. project prescan은 항상 유지한다. strict admitted launch의 selected-home prescan은 내포 argv 검증 뒤에만 skip하고 admitted exec 경계에서 다시 검증한다. 다른 경로는 prescan 또는 거부를 유지한다.
5. portable CLI contract는 test code에서 5-option으로 동기화하되 온디스크 fixture를 immutable input으로 취급한다. Claude in-range만 임시 test-local executable을 쓴다.
6. admission, identity digest, usage dual consent, public status schema, exit code, registry schema와 account home layout은 바뀌지 않는다.

| Component | Responsibility |
|---|---|
| `executable_ai-session-verify-claude` | hardened official auth status와 redacted six-field adapter |
| `executable_ai-session-enroll-identity` | 사용자 전경 호출에서 같은 hardened 조회 후 선택된 임시/host-local identity root에 digest 기록 |
| `executable_ai-session` | canonical verifier path의 단일 source, account 선택, prescan gate, admission, status/launch 결과 |
| `executable_ai-role-session` | 검토된 합성 settings와 차단 flag를 가진 최종 Claude argv 생성·재검증; 기본 verifier path 계산 없음 |
| `roles.toml` 및 설치 checker | 모든 Claude role의 지원 범위와 5-option required contract |
| `tests/test_ai_session.py` | status canonical-path 양성/음성, 기존 29개 기대값 불변 |
| `tests/test_orchestrator_profiles.py` | argv·sentinel·lifecycle·blast radius·portable CLI·scope·fixture·문서 E2E |
| `tests/fixtures/orchestrator-profiles/**` | byte-immutable legacy input; 수정 대상 아님 |
| 두 운영 문서 | 정본 verifier의 exact profile1 status 명령, 비정본 차단, role MCP 기능 결과와 profile2 explicit enrollment 절차 |

## Interfaces and data flow

`status` 흐름은 `real cwd → account selection → 현재 ai-session 프로세스 HOME 유효성 → verifier file 네 검사의 비치명 평가 → normalized canonical path equality → selected-home prescan skip 또는 기존 prescan → verify_admission → hardened verifier → canonical identity → usage/cost admission → profile_status JSON`이다. HOME이나 verifier 검사가 실패하거나 path가 다르면 raise하지 않고 기존 prescan을 실행한다. 위험 settings는 `blocked_policy`/4가 되고, benign settings의 invalid verifier는 뒤의 `verify_admission()`에서 `blocked_verifier`가 된다. status의 `--verifier` required parser 계약은 유지한다. 문서화된 profile1 명령은 profile1 mapped cwd에서 `${HOME}/.local/libexec/ai-session-verify-claude`를 전달하며, 이것이 사용자 가시 전환 경로다.

`launch` 흐름은 `role entrypoint → project prescan → role policy/settings 검증 → CLI version/help probe → hardened provider argv → ai-session launch`다. caller가 verifier를 주면 그대로 전달하고, 없으면 role launcher가 option을 생략해 ai-session이 provider별 canonical path를 채운다. account launcher는 trusted admitted shape와 내포 argv를 검증한 경우에만 selected-home prescan을 skip하고 admission 뒤 `admitted_main()`이 최종 argv를 다시 검증한 다음 provider session을 exec한다. 최종 argv는 `--strict-mcp-config`를 포함하고 `--mcp-config`를 포함하지 않아 role MCP server는 0개다.

profile2 전경 흐름은 `status(enrollment_required) → 사용자 확인 → helper 명시 실행 → hardened auth status → v2 digest atomic write → 새 status(ready)`다. helper만 선택된 identity root에 쓸 수 있고 status·launch는 enrollment를 만들거나 갱신하지 않는다.

verifier public stdout은 기존 exact fields `provider`, `account_profile`, `login_status`, `identity_status`, `usage_status`, `cost_limit_status`의 compact JSON 한 줄을 유지한다. raw Claude JSON은 subprocess 메모리 밖으로 전달하지 않고 canonical identity는 필요한 네 필드만 비교한다.

## Failure behavior

- status verifier가 파일 네 검사나 canonical path equality 중 하나라도 실패하거나 현재 프로세스 HOME이 unset·empty·비절대이면 술어는 예외 없이 false이고 prescan skip 권한이 없다. 위험 selected-home settings는 먼저 기존 `blocked_policy`/4이며, benign settings에서 다음 단계로 간 invalid verifier는 기존 `blocked_verifier` 계약을 따른다.
- role hardened argv가 누락·중복·재정의되거나 trusted admitted structure와 맞지 않으면 provider session을 시작하지 않고 `blocked_policy` 또는 `blocked_contract`로 닫는다.
- 지원 version 범위 안이어도 help가 두 hardening option 중 하나를 광고하지 않으면 read-only probe 뒤 `blocked_cli_contract`/4, provider session exec 0회다.
- hardened auth status가 nonzero, timeout, malformed JSON 또는 field/type/UUID 오류를 내면 raw output 없이 기존 fail-closed verifier 상태로 처리한다.
- live canonical projection이 다르면 배포 판정을 실패시키며 값은 출력하지 않는다.
- 문서화된 정본 profile1 status 명령이 selected-home key 때문에 `blocked_policy`가 되거나 검증 role launch가 차단되면 compatibility 실패다. source tree를 포함한 비정본 verifier의 `blocked_policy`/4와 위험 project settings 차단은 정상 보안 동작이다.
- profile2 `enrollment_required`는 오류가 아니다. helper 실패·duplicate mapping·identity drift는 자동 retry나 overwrite 없이 기존 계약을 유지한다.
- sentinel, MCP child, 설정 기반 env/permission capture가 하나라도 생기면 다른 성공 여부와 무관하게 보안 판정 실패다.
- fixture·보존 산출물 digest 불일치나 허용되지 않은 dirty path는 판정 실패며 fixture 갱신으로 맞추지 않는다.
- 설치 checker의 기존 version mismatch exit 1은 이번 변경의 실패 신호가 아니다. required-option 동기화와 live projection을 별도 판정한다.

## Security and risk

핵심 위험은 compatibility를 이유로 provider-default home을 신뢰하거나 allowlist를 넓히는 것이다. 정상 사용자 파일의 `hooks`, `mcpServers`, `env`, `permissions`도 child process 관점에서는 untrusted input이다. 이 Spec은 source 차단 argv와 exec 직전 검증으로 입력면을 닫는다. 그 결과 role 세션도 배포된 MCP server를 시작하지 않는 사용자 가시 기능 손실을 수용하며 두 운영 문서가 이를 알린다.

status의 임의 executable 주입 seam은 authorization 경계가 아니다. 그렇더라도 그 경로가 prescan skip 권한까지 얻으면 기존 방어를 우회하므로 skip은 현재 프로세스의 유효한 absolute HOME에서 계산한 canonical path에만 부여한다. 모든 사전 검사는 비치명적으로 실패해 prescan을 유지한다. lexical equality와 leaf non-symlink 검사를 함께 써 symlink alias와 임의 absolute executable을 거부한다. `resolve()`는 symlink alias를 canonical target과 같게 만들 수 있어 사용하지 않는다.

duplicate option이나 forged admitted argv가 뒤에서 hardening을 무효화할 위험은 exact-one, 빈 setting sources, digest 검증 settings, caller override 거부와 두 exec 경계 재검증으로 줄인다. auth hardening이 다른 identity를 보거나 raw 값을 노출할 위험은 live canonical projection의 메모리 비교와 safe boolean 출력으로 판정한다.

공유 fixture 변경과 테스트 누락으로 false pass가 생길 위험은 수정 지점 4개와 R1.2 단일 축에서 실제 실패한 8메서드/10케이스를 분리하고, 구현 전 세 축 전수 재측정, 전체 121개 baseline, fixture tree digest를 함께 고정해 줄인다. 단일 축 열거의 근거는 `cli-contract-blast-radius-measured.md`의 실측이며, 수정 지점 수를 suite 충분성의 대리값으로 쓰지 않는다.

## Test strategy

test-first positive control은 먼저 `test_settings_compat_status_canonical_verifier_prescan_gate`와 `test_settings_compat_profile1_status`를 작성하는 것이다. 현재 구현은 canonical path 여부와 관계없이 status selected-home prescan을 호출하므로 정본 verifier 양성 case가 위험 settings에서 `blocked_policy`/4로 반드시 실패해야 한다. 구현 전에는 첫 테스트를 단독 실행하고 exact test 이름, unittest nonzero exit, positive actual `blocked_policy`/4 대 expected `ready`/0, negative actual `blocked_policy`/4, 실행 시각을 AC-25의 고정 evidence 경로에 전사한다. 구현 뒤 이 파일을 덮어쓰지 않는다. 같은 테스트의 임의 주입 verifier 음성 case는 기존처럼 통과해야 control의 판별력을 보인다.

보안 fixture는 hardening flag가 없을 때 sentinel을 실제 생성하는 negative control을 먼저 통과시킨다. 같은 settings를 바꾸지 않고 verifier, 비합성 enrollment subprocess, strict role launch를 실행해 sentinel·MCP·env/permission capture가 0인지 검사한다. enrollment test는 두 synthetic status 환경변수를 unset하고 fake Claude를 한 번 실제 실행한다.

blast-radius 회귀는 R3.2의 네 수정 지점과 단일 축 실측 8메서드/10케이스를 서로 다른 단위로 확인하고, 여섯 settings write, 네 prescan call, 일곱 blocked-policy test, argv exact/부분 단언, 문서·ownership 계약을 source evidence와 일치시킨다. 실제 worktree 구현 전에는 스크래치 공유 클론에서 세 축을 함께 적용해 같은 두 전체 suite를 재측정하고 그 전수를 Plan의 충분성 근거로 고정한다. 최종 기존 전체 suite가 행동을 판정한다. portable 회귀는 실패군과 codex in-range에 기존 fixture를 사용하고 Claude in-range만 test-local fake를 쓴다. 별도 tree digest가 추가·삭제·rename·byte 변경을 모두 탐지한다.

### 판정 명령 표

| ID | 명령 | 통과 조건 |
|---|---|---|
| CMD-1 | `/opt/homebrew/bin/python3.14 -m unittest tests.test_ai_session.AiSessionCliTests.test_settings_compat_status_canonical_verifier_prescan_gate tests.test_ai_session.AiSessionCliTests.test_settings_compat_canonical_verifier_path_contract tests.test_ai_session.AiSessionCliTests.test_settings_compat_profile1_status` | canonical verifier 양성, 주입 verifier 음성, 단일 path source·normalization, 16-key status가 모두 통과한다. |
| CMD-2 | `/opt/homebrew/bin/python3.14 -m unittest tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_verifier_argv tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_enrollment_argv tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_role_launch_argv tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_profile1_launch_e2e tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_profile1_operational_status_command tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_profile1_noncanonical_verifier_policy tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_profile2_enrollment_to_ready tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_auth_status_sentinel tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_role_launch_sentinel tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_isolation_contract tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_blast_radius_contract tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_scope_and_secret_hygiene tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_cross_regression tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_claude_required_options tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_documentation_contract tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_fixture_bytes_unchanged tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_claude_untrusted_settings_prescan tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_claude_official_status_contract tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_portable_cli_contract tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_verifier_provider_environments tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_stale_pwd_rejected tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_account_root_permission_separation tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_no_opposite_root_grant tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_exact_git_common_dir_permission tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_chezmoi_fixture_render tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_claude_settings_prescan tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_effective_setting_sources tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_claude_plugin_policy tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_documentation_contract tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_profile_onboarding_documentation_contract` | argv·lifecycle·정본 운영 명령·비정본 차단·sentinel·감사표·scope·cross-regression·CLI·문서·fixture와 실측 영향 8메서드를 포함한 재정의/불변 기존 테스트 30개가 모두 통과한다. |
| CMD-3 | `/opt/homebrew/bin/python3.14 tests/test_ai_session.py` | 기존 29개 기대값과 추가 회귀가 failure/error 없이 exit 0이다. |
| CMD-4 | `AI_SESSION_LIVE_CLAUDE_AUTH_PROBE=1 /opt/homebrew/bin/python3.14 -m unittest tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_live_identity_projection` | baseline과 hardened canonical projection이 같고 값 비노출 상태로 exit 0이다. |
| CMD-5 | `/opt/homebrew/bin/python3.14 tests/test_orchestrator_profiles.py` | 기존 92개와 추가 회귀가 failure/error 없이 exit 0이고 opt-in live probe는 skip된다. |
| CMD-6 | `/opt/homebrew/bin/python3.14 -c 'from pathlib import Path; import re; p=Path(".claude/quality-state/20260917T051955Z-111-설정-호환성-결함을-방향-b-verifier-identity-기반-467cbcd9/evidence/spec-red-canonical-verifier.txt"); s=p.read_text(); required=("test_settings_compat_status_canonical_verifier_prescan_gate", "positive_actual=blocked_policy/4", "positive_expected=ready/0", "negative_actual=blocked_policy/4"); assert all(x in s for x in required); assert re.search(r"unittest_exit=[1-9][0-9]*", s); assert re.search(r"captured_at=\S+", s)'` | 구현 전 Red 전사가 고정 경로에 있고 exact test, nonzero test exit, 양성 실패 상태, 음성 유지 상태와 시각을 모두 포함한다. |
| CMD-7 | `/opt/homebrew/bin/python3.14 -c 'from pathlib import Path; import re; p=Path(".claude/quality-state/20260917T051955Z-111-설정-호환성-결함을-방향-b-verifier-identity-기반-467cbcd9/evidence/cli-contract-blast-radius-three-axis-measured.md"); s=p.read_text(); required=("scratch_clone=git clone -s", "scratch_head=56d65ca", "axes=R1.1,R1.2,R1.3(2)", "baseline_ai_session=Ran 29 OK", "baseline_orchestrator_profiles=Ran 92 OK", "tests_changed=0", "actual_worktree_changed=0", "source_repository_changed=0", "installed_artifacts_changed=0", "three_axis_ai_session_summary=", "three_axis_orchestrator_profiles_summary=", "sufficient_basis=test_methods_and_cases"); assert all(x in s for x in required); assert re.search(r"captured_at=\S+", s)'` | 구현 전 세 축 스크래치 재측정 evidence가 격리·baseline·전수 결과·메서드/케이스 충분성 표식을 모두 포함한다. |

CMD-1, CMD-2, CMD-3, CMD-5는 source tree, 임시 directory와 fake executable만 사용한다. CMD-4만 설치 Claude CLI의 auth status를 두 번 읽기 전용 호출하며 값을 파일에 저장하거나 출력하지 않는다. CMD-6과 CMD-7은 구현 전에 이미 저장된 비밀 없는 evidence만 읽는다. 어떤 판정 명령도 실제 `~/.claude`, `~/.local/share/ai-account-profiles/`, 실행 중 session을 변경하거나 model, login/logout, browser, chezmoi, tmux, git write를 실행하지 않는다. AC-26의 별도 Plan 재측정 태스크는 격리 스크래치 공유 클론 내부에서만 prospective source를 바꾸고 실제 worktree·원본 저장소·설치본에는 쓰지 않는다.

교차 회귀는 목표 1과 목표 2를 분리 판정하지 않는다. AC-18은 같은 위험 settings에서 status/launch 성공과 모든 주입 부재를 한 번에 요구한다. AC-23의 profile1 운영 명령은 R1.3의 정본 경로만 사용하고 AC-24의 비정본 차단을 약화하지 않으며, role 세션은 R1.2 결정에 따라 MCP server 없이 성공한다. 두 새 문서 block은 기존 `assertIn` 문서 계약을 유지하고 AC-21의 fixture를 읽거나 수정하지 않는다. AC-15의 네 수정 지점과 8메서드/10케이스 영향 열거는 서로 다른 단위이며, `test_exact_git_common_dir_permission`과 `test_chezmoi_fixture_render`을 포함한 helper 경유 여섯 메서드는 기대값을 약화하지 않고 원래 기대를 복원한다. 이 구분은 AC-21 fixture bytes 불변과 AC-20 문서 계약 불변을 동시에 통과해야 하므로 감사표와 보존 조건이 모순되지 않는다.

## Decisions

### D1. child argv에서 설정 source를 차단하고 증명된 경로만 prescan에서 제외한다

verifier와 enrollment auth status에 `--setting-sources "" --strict-mcp-config`를 적용하고 role argv에는 `--strict-mcp-config`와 exact-one 재검증을 더한다. 비대화형 auth 조회에는 MCP가 필요 없다. role argv에도 검토된 `--mcp-config`를 추가하지 않으므로 role 세션의 MCP server가 0개가 되는 호환성 결과는 D12에서 명시적으로 수용한다. project prescan은 유지하고 selected-home prescan만 각 실행 경계의 검증 뒤 조건부 skip한다. 정상 account-home 파일을 수정하지 않으면서 process가 그 설정을 읽지 않는 속성을 증명하는 방식이다.

### D2. canonical verifier 경로의 단일 source는 executable_ai-session이 소유한다

새 공유 module은 허용 변경 집합 밖의 파일을 만들고 배포 surface를 늘린다. 두 executable에 같은 문자열을 복제하면 새 동기화 함정이 된다. 따라서 `executable_ai-session` 한 곳에 provider별 canonical path 함수와 launch 기본값을 두고, role launcher는 caller verifier만 전달하며 기본값은 전달하지 않는다. status의 required `--verifier` CLI는 유지하되 같은 함수의 결과와 비교한다.

### D3. path는 lexical 정규화하고 resolve하지 않는다

현재 `ai-session` 프로세스의 `os.environ["HOME"]`가 nonempty absolute일 때만 expected path를 만들고, child environment나 pwd database로 fallback하지 않는다. expected와 supplied path에 `expanduser`, `abspath`, `normpath`를 적용해 후행 slash와 `..`를 제거한다. HOME 유효성이나 기존 absolute·regular·leaf non-symlink·executable 검사 실패는 모두 비치명적으로 skip 권한만 제거한다. `resolve()`는 symlink alias도 같은 target으로 승인할 수 있어 canonical namespace 동일성에 맞지 않는다. 이 결정은 leaf symlink 거부를 약화하지 않으며 alternate symlink spelling에는 skip 권한을 주지 않는다.

### D4. verifier digest 상수 방식은 기각한다

verifier SHA-256을 source 상수로 고정하면 verifier 수정 때마다 수동 갱신이 필요하고 누락 시 모든 session이 막힌다. 이는 별도 이슈 `#126`의 설치 CLI checker version exact-match 함정과 같은 구조다. path identity와 source hardening test를 사용한다.

### D5. provider-default home 신뢰와 allowlist 확장은 기각한다

home mode는 security 신뢰도를 뜻하지 않으며 사용자 home에도 위험 키가 있다. allowlist 확장은 process가 값을 로드할 가능성을 남긴다. compatibility는 파일을 benign으로 선언하지 않고 child 입력에서 제외해 해결한다.

### D6. broad mode flag와 bare mode는 기각한다

`--safe-mode`와 `--restricted`는 role의 plugin·instruction·tool·permission 행동까지 넓게 바꾼다. `--bare`는 OAuth와 Keychain을 읽지 않아 consumer identity 계약을 깨뜨린다. 필요한 source와 MCP 경계에 직접 대응하는 두 flag만 사용한다.

### D7. profile2 enrollment는 사용자 전경의 명시적 단계로 유지한다

`enrollment_required`와 `identity_enroll_foreground`는 backend 실행 지시가 아니라 사용자 descriptor다. 문서는 exact helper와 재검증 순서를 제공하지만 자동 실행·browser interaction·fallback을 추가하지 않는다.

### D8. hardening flag를 portable CLI required-option 계약에 편입한다

모든 Claude manifest, runtime expected list, 설치 checker required constant를 5-option으로 맞추고 runtime help가 미광고 installation을 provider session 전에 차단한다. 이때 provider session exec 0회와 read-only `--version`/`--help` probe는 구분한다. 설치본이 두 flag를 광고한다는 2026-09-17 직접 측정으로 baseline 세 테스트의 호환성을 확인했다.

### D9. 방향 B로 온디스크 fixture를 보존한다

대기 중인 #118이 `tests/fixtures/orchestrator-profiles/**`의 의미와 bytes 보존을 전제로 한다. Claude in-range만 test-local 5-option fake CLI로 전환하고 codex와 실패군 fixture는 그대로 둔다. fixture 변경으로 테스트를 맞추는 방향은 기각한다.

### D10. 수정 지점 감사와 실측 테스트 영향을 분리해 완전성 근거로 채택한다

선택 account-home·project settings write, Claude argv 단언, required-option/help 의존, 운영 문서 계약을 메서드 경계 기준으로 전수 스캔한 `blast-radius-audit-v2.md`를 근거로 정확히 네 기존 지점만 재정의한다. 그러나 이 수정 지점 수로 suite 충분성을 주장하지 않는다. `cli-contract-blast-radius-measured.md`가 R1.2 한 축에서 확인한 8메서드/10케이스를 하한선으로 삼고, 구현 전에 세 축을 함께 적용한 스크래치 전수 재측정으로 Plan의 충분성 근거를 확정한다. helper 경유 여섯 메서드는 테스트 기대를 바꾸지 않고 공유 help 수정으로 원래 기대를 복원한다. 전체 suite, targeted invariant, fixture digest를 함께 요구해 새 기대값이 감사 범위 밖으로 퍼지거나 기존 기대가 약화되면 실패하게 한다.

### D11. 설치 checker의 사전 version mismatch를 별도 이슈로 유지한다

`EXPECTED_VERSIONS["claude"]="2.1.272"`와 설치본 2.1.274의 exact 비교 때문에 checker는 변경 전부터 exit 1이다. 이번 작업은 required option만 갱신하고 version evidence는 `#126`에서 다룬다. 이 사전 실패를 이번 배포 gate나 회귀로 해석하지 않는다.

### D12. role 세션의 MCP 기능 손실을 보안 결과로 수용한다

`dot_claude/dot_mcp.json`은 실제 배포되고 `maestro` server 하나를 선언하지만 현재 변경 범위에는 해당 파일을 신뢰할 정책, digest pinning, 별도 `--mcp-config` 공급 계약이 없다. 검토되지 않은 MCP를 다시 열어 compatibility를 얻는 것보다 `--strict-mcp-config`만 적용해 role 세션의 MCP server를 0개로 만드는 쪽을 선택한다. verifier·enrollment의 비대화형 auth 조회에는 MCP가 필요 없다는 이유와 role 사용자 기능 손실을 수용한다는 이유를 구분하며, 두 운영 문서의 byte-identical 문구와 AC-3·AC-10·AC-12·AC-20으로 이 결과를 고지하고 판정한다.

### D13. profile1 운영 전환점은 문서화된 정본 verifier 명령이다

실패 재현은 소스 트리 verifier를 사용했으므로 canonical-path skip만 구현해서는 같은 명령의 결과가 바뀌지 않는다. 두 운영 문서에 `${HOME}/.local/libexec/ai-session-verify-claude`를 쓰는 exact status 명령을 byte-identical하게 싣고 이를 fixture `ready`/0에 묶는다. 소스 경로와 다른 executable은 계속 `blocked_policy`/4로 두어 경로 identity 통제를 보존한다. 따라서 결함 폐쇄는 소스 경로의 승격이 아니라 운영 명령의 정본 경로 전환으로 정의한다.

<!-- strict-only:start -->

This block is required only for strict work. Any inapplicable subsection must be removed for non-strict work; within strict work, mark it as not applicable with a reason before review.

### Threat and trust boundaries

신뢰 입력은 검토된 registry·role manifest·adapter source, digest 검증된 합성 settings/instruction/plugin, canonical path의 production verifier, exact argv builder/validator다. untrusted 입력은 user/project/local settings, caller provider arguments, 임의 주입 verifier, provider stdout/stderr, account home 내용과 enrollment 전 identity다.

주요 위협은 hook 명령 실행, MCP server 기동, env/permission 주입, 임의 verifier에 prescan skip 권한 부여, HOME fallback 불일치, symlink alias, duplicate option, forged admitted command, raw auth JSON 유출, profile 간 identity overwrite와 fixture 변경에 의한 false pass다. 통제는 current-process absolute HOME, 비치명 술어, canonical lexical equality, leaf non-symlink 검사, 두 차단 flag, exact-one 검증, caller override 거부, 미확인 경로 prescan, captured/redacted adapter, explicit-only enrollment, sentinel negative control과 immutable byte digest다.

trust boundary는 verifier/enrollment의 Claude exec, role launcher의 provider argv 생성, admitted role process의 최종 provider session exec다. 각 경계는 이전 단계 환경 flag만 신뢰하지 않고 자기 책임의 검사를 수행한다.

### Authorization and tenant isolation

기존 directory mapping과 binding generation을 유지한다. `~/code/profile1`은 `claude-profile1`, `~/code/profile2`는 `claude-profile2`에만 매핑되며 selection priority나 scope를 바꾸지 않는다. profile1 provider-default와 profile2 explicit home 사이 파일 복사·rename·symlink는 허용하지 않는다.

status prescan skip 권한은 provider=claude, current-process absolute HOME과 canonical verifier identity를 함께 만족한 경로에만 있다. 재현의 source executable을 포함한 임의 dependency-injection executable은 실행 seam일 수 있지만 보안 통제를 생략할 권한은 없다. enrollment write 권한은 사용자가 명시 호출한 helper와 선택 profile의 identity digest 경로에만 있고 status·launch에는 없다.

새 network service, OS role 또는 ACL은 없으므로 별도 OS multi-tenant migration은 해당하지 않는다. tenant 경계는 local account profile과 credential/identity home이다.

### Migration, compatibility, and rollback

registry schema, enrollment schema, public JSON, account alias와 home layout은 바뀌지 않아 data migration이나 backfill이 없다. launch의 verifier 기본값 owner만 role launcher에서 account launcher로 이동하며 외부 status의 required option은 유지된다. 기존에 소스 트리 verifier를 넘긴 profile1 운영 명령은 계속 `blocked_policy`/4이므로 두 문서의 정본 verifier 명령으로 전환해야 `ready`/0이 된다. 모든 Claude role manifest, validator, checker required list와 test helper를 함께 5-option으로 맞춘다.

`--strict-mcp-config`를 `--mcp-config` 없이 role argv에 넣으므로 배포된 `dot_claude/dot_mcp.json`의 `maestro`를 포함한 MCP server는 role 세션에서 더 이상 시작되지 않는다. 이 사용자 가시 기능 손실은 의도한 호환성 결과이며 별도 migration이나 자동 대체가 없다. verifier·enrollment의 비대화형 auth 조회는 MCP를 필요로 하지 않아 같은 flag의 기능 손실이 없다. MCP가 필요한 role workflow는 이 변경의 자동 fallback 대상이 아니며 후속의 검토된 config·digest 계약 없이는 다시 활성화하지 않는다.

rollback trigger는 canonical path negative case의 prescan 우회, live projection mismatch, sentinel/MCP/env/permission capture, duplicate option 우회, fixture·보존 tree digest mismatch, scope 위반, R3.2 밖 기존 기대값 회귀, profile2 lifecycle 실패다. rollback은 허용 10개 파일의 task 변경을 되돌리고 rollout을 중단하는 것이다. 사용자 settings·credential·identity, fixture와 보존 산출물은 건드리지 않는다. allowlist 확장이나 hardening 없는 prescan 제거 상태로 되돌리지 않는다.

### Failure recovery and observability

운영 신호는 public status와 exit code다. 문서화된 정본 명령의 profile1 성공은 `ready`/0, profile2 미등록은 `enrollment_required`/3과 `identity_enroll_foreground`다. canonical이 아닌 verifier 아래 위험 settings는 의도한 `blocked_policy`/4, benign settings의 invalid verifier는 `blocked_verifier`, CLI 미지원은 `blocked_cli_contract`/4, 오염 argv는 `blocked_policy` 또는 `blocked_contract`다. HOME과 verifier 사전 검사 실패 자체는 예외나 별도 status를 만들지 않는다.

테스트 신호는 exact argv capture, canonical/source/주입 verifier 대비, 구현 전 Red 전사, version/help probe와 provider session exec의 분리 계수, sentinel/MCP/env/permission capture 부재, 네 축 감사 목록, fixture/보존 byte digest와 unittest exit다. local CLI 저장소이므로 새 persistent metric·trace·alert backend는 해당하지 않는다. 로그에는 public status와 safe boolean만 허용한다.

### High-risk end-to-end verification

고위험 경로는 위험 selected-home settings가 있는 profile1의 status와 strict role launch다.

1. 구현 전 canonical verifier 양성 control이 현재 prescan 때문에 `blocked_policy`/4로 실패하고 주입 verifier 음성 control은 그대로 차단됨을 AC-25의 고정 경로에 기록하고 CMD-6으로 판정한다.
2. unhardened negative control이 sentinel을 생성해 fixture 탐지 능력을 증명한다.
3. 같은 settings를 바꾸지 않은 production path에서 AC-18이 status `ready`/0, provider session 1회, exact hardened argv, role MCP server·sentinel·env·permission 0회를 동시에 확인한다.
4. AC-4와 AC-5가 canonical verifier만 비치명 술어의 skip 권한을 얻음을 확인하고, AC-23이 문서화된 exact profile1 명령을 `ready`/0에 묶으며, AC-24가 source·임의 verifier의 `blocked_policy`/4를 유지한다. AC-22는 project 위험 settings 차단을 유지한다.
5. profile2 lifecycle, role MCP 기능 결과의 문서 고지, 네 축 감사 invariant, portable CLI, fixture·보존 byte digest와 exact scope를 확인한다.
6. CMD-4가 live canonical projection을 값 비노출로 확인하고 CMD-3·CMD-5가 기존 121개를 보존한다.

projection mismatch, raw 값 노출, 주입 부작용, 임의 verifier 우회, provider 중복 exec, 자동 enrollment, fixture·사용자 파일 변경, scope 위반 또는 suite 실패가 하나라도 있으면 중단하고 PASS로 기록하지 않는다.

### No production mutation confirmation

자동 workflow에는 production mutation이 없다. `chezmoi apply`, 실제 login/logout·enrollment·model 호출, browser, tmux/session 조작, git write, commit/push/merge를 실행하지 않는다. 합성 enrollment는 임시 identity root에만 쓰고 폐기한다. 유일한 live 동작 CMD-4는 auth status 두 조합을 읽기 전용으로 메모리 비교하며 값이나 파일을 남기지 않는다. 실제 Claude home, credential home, fixture와 앞선 산출물은 모든 자동 판정에서 불변이다.

<!-- strict-only:end -->
