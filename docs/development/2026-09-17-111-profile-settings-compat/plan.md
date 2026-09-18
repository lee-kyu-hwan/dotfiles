# Quality Goal Implementation Plan

- Task ID: 20260917T002844Z-111-프로필별-실경로-smoke의-기본-claude-설정-호환성-결함-f76eb54a
- Mode: strict
- Status: PLAN_REVIEW
- Created: 2026-09-17
- Updated: 2026-09-17
- Source goal: #111 프로필별 실경로 smoke의 기본 Claude 설정 호환성 결함(profile1 blocked_policy·profile2 enrollment_required)을 안전하게 해결한다

## Spec link

승인 대상 Spec: `/Users/lee-kyu-hwan/code/profile1/dotfiles/111-profile-onboarding/docs/development/2026-09-17-111-profile-settings-compat/spec.md`

- Spec 리뷰 라운드 2 PASS, score 93, blocker 0
- 이 Plan이 사용하는 Spec digest(SHA-256): `c9ae87cc62e9b1966cbc03123445548c102a2cbcc3f69a2070aad05d76204b24`
- 요구사항 R1.1~R3.3(10개), 수용 기준 AC-1~AC-18(18개), 판정 명령 CMD-1~CMD-5

Spec 라운드 2 리뷰가 남긴 비차단 권고 두 건을 이 Plan이 구현 수준에서 확정한다.

- `SPEC-007`(Medium): AC-15 scope checker가 비교하는 경로 집합이 Spec에 고정되지 않았다. 이 Plan의 `## Global constraints` G7이 비교 대상 집합과 제외 집합을 확정한다.
- `SPEC-008`(Low): AC-17의 "provider 호출 0회"는 `verify_provider_cli_contract()`가 반드시 수행하는 `claude --version`·`claude --help` 읽기 전용 probe와 문자 그대로 충돌한다. 이 Plan의 G8이 금지 대상을 provider **session exec**으로 확정하고 help/version probe는 허용으로 고정한다.

## Global constraints

- **G1 저장소 형태.** chezmoi source 저장소다. `dot_` 접두 파일은 `$HOME`에 배치될 원본이며 실행 권한이 없다. 이 작업에서 `chezmoi apply`를 실행하지 않는다. 모든 구현·검증은 저장소 안의 source 파일을 `/opt/homebrew/bin/python3.14`로 직접 실행한다.
- **G2 Python.** 모든 테스트와 판정 명령은 `/opt/homebrew/bin/python3.14`를 사용한다. 다른 인터프리터를 쓰지 않는다.
- **G3 test-first.** 모든 동작 변경은 테스트 선작성이다. 각 태스크는 (1) 테스트를 먼저 쓰고 실행해 **실패를 관측**하고 그 실패 메시지를 기록한 뒤, (2) 최소 구현을 하고, (3) 같은 명령을 다시 실행해 통과를 기록한다. 실패를 관측하지 않은 테스트는 완료 증거로 쓸 수 없다.
- **G4 인증 자동 실행 금지.** 구현·검증 어느 단계도 `claude login`, `claude logout`, 브라우저 OAuth, 실제 identity enrollment, 실제 모델 호출을 실행하지 않는다. 실제 `claude` CLI 호출은 CMD-4의 읽기 전용 `auth status` 두 번뿐이며 그것도 명시적 opt-in 환경변수가 있을 때만 실행된다.
- **G5 사용자 자산 불변.** `~/.claude`, `~/.local/share/ai-account-profiles/**`, `~/.config/ai-session/**`, 실행 중 tmux 세션과 process를 읽기 전용으로도 수정하지 않는다. 모든 격리 테스트는 `TemporaryDirectory()`와 PATH 선두 fake executable만 사용한다. profile 간 설정·credential·identity 복사·rename·symlink는 금지다.
- **G6 secret 금지.** OAuth token, API key, 이메일, account ID 원문, `orgId` 원문, canonical identity 원문, 전체 digest를 소스·테스트·fixture·문서·로그·명령 출력에 기록하지 않는다. 실측 16개 키 fixture는 **키 이름과 JSON 타입만** 재현하고 실제 값은 복사하지 않는다(예: `env`는 `{}`, `model`은 `"fixture-model"` 같은 무해한 자리값).
- **G7 변경 범위(AC-15 scope checker 비교 집합 확정).** scope checker가 비교하는 집합은 `git status --porcelain`이 보고하는 경로 중 아래 **제외 집합에 속하지 않는 모든 경로**다.
  - 허용 집합(정확히 이 10개 파일만 변경 가능):
    `dot_local/bin/executable_ai-session`,
    `dot_local/bin/executable_ai-role-session`,
    `dot_local/libexec/executable_ai-session-verify-claude`,
    `dot_local/libexec/executable_ai-session-enroll-identity`,
    `dot_config/ai-session/roles.toml`,
    `tests/test_ai_session.py`,
    `tests/test_orchestrator_profiles.py`,
    `tests/check_installed_orchestrator_cli_contract.py`,
    `docs/session-account-profiles.md`,
    `docs/orchestrator-permission-profiles.md`
  - 제외 집합(비교에서 빼는 경로 prefix): `docs/development/2026-09-17-111-profile-settings-compat/`(이번 quality-goal 실행의 Spec·Plan·report·revision note)와 `.claude/quality-state/`(워크플로 런타임 상태, `.gitignore:25`로 이미 무시됨). 이 둘은 산출물 자체이므로 scope 위반이 아니다.
  - 그 밖의 경로가 나타나면 checker는 실패한다. 특히 `dot_config/ai-session/accounts.toml`, `docs/development/2026-09-16-111-profile-onboarding/**`, `#118`이 소유한 경로는 허용 집합에 없으므로 변경 시 즉시 실패한다.
- **G8 AC-17 "provider 호출" 정의 확정.** 금지 대상은 **provider session exec**(최종 `claude` 세션 프로세스 실행, 즉 `os.execvpe`로 시작되는 Claude 실행)이다. `verify_provider_cli_contract()`가 계약 검사를 위해 반드시 수행하는 `claude --version`과 `claude --help` 읽기 전용 probe는 허용되며 그 호출 수는 금지 계수에 넣지 않는다. fake `claude`는 두 종류의 호출을 구분해 기록하고, AC-17 테스트는 session exec 계수가 정확히 0임을 판정한다.
- **G9 소유 경계 존중.** 대기 중인 `#118` Plan과 `#70` 2단계가 별도 경계를 선언해 두었다. 이 작업은 G7 허용 집합 밖 파일을 만들거나 고치지 않으며, `dot_claude/skills/quality-goal/**`와 `dot_local/share/ai-account-profiles/claude/profile2/**` mirror 파일을 변경하지 않는다.
- **G10 git 쓰기 금지.** 구현·검증 중 `git add`, `git commit`, `git push`, `git checkout`, `git stash`, `git restore`, PR merge를 실행하지 않는다. `git status`, `git diff`는 읽기 전용이므로 허용한다.
- **G12 기존 테스트 편집 경계(PLAN-001·PLAN-002 해소).** 기존 121개 테스트는 **본문과 기대 동작**을 유지한다. 다만 CLI 계약 상수를 코드가 아닌 테스트 쪽에 복제해 둔 두 지점은 계약 변경과 함께 동기화해야 한다. 허용되는 편집은 정확히 다음 둘뿐이다. ① `tests/test_orchestrator_profiles.py`의 공용 fixture helper `make_fake_executable()`의 Claude CLI probe 기본 `--help` 광고 목록과 `--version` 문자열(테스트 본문이 아니라 fixture 헬퍼다). ② 같은 파일 `test_portable_cli_contract`의 `expected_contracts["claude"]["cli_required_options"]` 리터럴 한 곳. 이 둘은 assert 대상 성질을 바꾸지 않고 계약 상수만 5-option으로 맞춘다. 그 밖의 기존 테스트 편집은 금지이며 AC-15 scope checker와 코드 리뷰가 이를 확인한다.
- **G13 설치 계약 checker는 배포 게이트가 아니다(PLAN-003 해소).** `tests/check_installed_orchestrator_cli_contract.py`는 **이번 변경 이전에 이미 실패한다.** 실측: `AI_SESSION_CLI_PROBE_MODE=help-only /opt/homebrew/bin/python3.14 tests/check_installed_orchestrator_cli_contract.py` → `claude installed version differs from frozen evidence`, exit 1(증거: `.claude/quality-state/20260917T002844Z-111-프로필별-실경로-smoke의-기본-claude-설정-호환성-결함-f76eb54a/evidence/checker-baseline.txt`). 원인은 이 작업과 무관하다. `EXPECTED_VERSIONS["claude"]`가 `2.1.272`(`:22`)로 고정돼 있고 `installed_version != version_tuple(expected_version)`를 요구하는데(`:111-113`) 설치본은 2.1.274다. 이를 통과시키려면 `EXPECTED_VERSIONS`와 `FROZEN_EVIDENCE`인 `docs/development/2026-09-15-103-orchestrator-permission-profiles-2/authoritative-inputs.md:81`의 동결 버전 문자열을 함께 올려야 하는데, 그 문서는 G7 허용 집합 밖이고 다른 완료 작업의 산출물이다. 따라서 이 작업은 (a) 그 script를 **배포 전 게이트로 사용하지 않고**, (b) AC-17이 요구하는 `EXPECTED_REQUIRED["claude"]` 상수만 5-option으로 동기화하며, (c) `EXPECTED_VERSIONS`·frozen evidence 갱신은 **별도 승인이 필요한 후속 작업**으로 분리해 report에 기록한다. 실제 배포 전 호환성 확인은 CMD-4(설치본 live projection 동일성)와 CMD-2의 `test_settings_compat_claude_required_options`가 담당한다. 이 script는 이번 작업의 어떤 판정 명령(CMD-1~CMD-5)에도 포함되지 않으므로 그 사전 실패는 이번 변경의 회귀가 아니다.
- **G11 fail-closed 보존.** 어떤 변경도 `BENIGN_CLAUDE_SETTING_TYPES`에 새 키를 추가하지 않는다. prescan 자체는 제거하지 않고, R1.3이 정의한 하드닝 증명 경로에서만 건너뛴다. 나머지 경로의 prescan과 status/exit 계약은 그대로 유지한다.

## File map

| 파일 | 조치 | 책임과 영향받는 인터페이스 |
|---|---|---|
| `dot_local/libexec/executable_ai-session-verify-claude` | 수정 | `_official_status()`의 subprocess argv를 `["claude", "--setting-sources", "", "--strict-mcp-config", "auth", "status", "--json"]`로 교체한다(현재 `:44-54`). 10초 timeout, `capture_output=True`, `close_fds=True`, `pass_fds=()`, nonzero/timeout/malformed JSON fail-closed, redacted 6-field stdout 계약은 바이트 수준으로 유지한다. 공개 출력 스키마는 바뀌지 않는다. |
| `dot_local/libexec/executable_ai-session-enroll-identity` | 수정 | `_identity_status()`의 비합성 분기 argv(현재 `:129`의 `command = ["claude", "auth", "status", "--json"]`)를 같은 exact argv로 교체한다. `AI_SESSION_SYNTHETIC_TEST=1` 합성 분기, `_status_environment()`의 `CLAUDE_CONFIG_DIR` 주입, owner-only digest 쓰기, `enrolled`/exit 0 및 `duplicate_mapping`·`blocked_verifier`/exit 3 계약은 유지한다. |
| `dot_local/bin/executable_ai-role-session` | 수정 | ① `claude_command()`(현재 `:1046-1060`)의 argv에 `--setting-sources ""` 바로 뒤로 `--strict-mcp-config`를 추가한다. ② `verify_provider_cli_contract()`(현재 `:741-793`)의 `expected["claude"]["required"]`를 exact ordered list `["--append-system-prompt", "--settings", "--plugin-dir", "--setting-sources", "--strict-mcp-config"]`로 바꾼다. ③ `CLAUDE_POLICY_ARGUMENTS`(현재 `:57-69`)에 `--strict-mcp-config`와 `--mcp-config`를 추가해 caller override를 `blocked_policy`로 거부한다. ④ 최종 provider argv를 검사하는 함수를 새로 도입해 `--setting-sources`가 정확히 1회이고 그 값이 빈 문자열, `--strict-mcp-config`가 정확히 1회, `--settings`가 정확히 1회이며 digest 검증 경로임을 확인한다. `claude_command()` 반환 직전과 `admitted_main()`(현재 `:1271-1336`)의 exec 직전 **두 경계 각각**에서 이 검사를 수행하고, 불충족이면 `blocked_policy`로 닫는다. ⑤ `admitted_main()`의 `prescan_selected_claude_home()` 호출(현재 `:1303-1304`)과 `claude_command()`의 `prescan_claude_settings(repository)` 호출(현재 `:1016`)은 ④의 하드닝 검사가 통과한 경우에만 건너뛰고, 검사가 불가능하거나 실패하면 기존 prescan을 그대로 수행한다. |
| `dot_config/ai-session/roles.toml` | 수정 | 네 Claude role 항목의 `cli_required_options`(현재 `:31,74,117,164`)를 ②와 같은 exact ordered 5-option list로 바꾼다. `cli_version_range`, `cli_forbidden_options`, 모델·effort·권한 값은 바꾸지 않는다. Codex role 항목(`:12,55,98,145`)은 손대지 않는다. |
| `tests/check_installed_orchestrator_cli_contract.py` | 수정 | `EXPECTED_REQUIRED["claude"]`(현재 `:27-30`)를 같은 exact ordered 5-option list로 바꾼다. `EXPECTED_VERSIONS`, `EXPECTED_RANGES`, `EXPECTED_FORBIDDEN`은 바꾸지 않는다. |
| `dot_local/bin/executable_ai-session` | 수정 | `status()`(현재 `:1555-1583`)에서 `binding.provider == "claude"`이고 `verify_admission()`이 이미 강제하는 trusted `--verifier` seam 조건(절대경로·regular·non-symlink·실행 가능, 현재 `:1228-1231`)을 만족할 때 `prescan_selected_claude_home(environment)` 호출을 건너뛴다. 조건을 하나라도 만족하지 못하면 기존 prescan을 수행한다. `launch()`(현재 `:1500-1552`)에서는 실행할 provider command가 `ai-role-session --admitted` 구조의 하드닝 검증 경계를 통과하는 경우에만 prescan을 건너뛰고, 그 밖의 임의 provider command에는 기존 prescan을 유지한다. `BENIGN_CLAUDE_SETTING_TYPES`, `validate_untrusted_claude_settings()`, `prescan_selected_claude_home()` 자체와 status JSON 스키마·exit code는 바꾸지 않는다. |
| `tests/test_ai_session.py` | 수정(추가) | `AiSessionCliTests`에 `test_settings_compat_unhardened_route_fail_closed`, `test_settings_compat_profile1_status` 두 테스트를 추가한다. 기존 29개 테스트의 본문과 기대값은 변경하지 않는다. |
| `tests/test_orchestrator_profiles.py` | 수정(추가 + 계약 동기화 2곳) | ① `OrchestratorProfileContractTests`에 `test_settings_compat_verifier_argv`, `test_settings_compat_enrollment_argv`, `test_settings_compat_role_launch_argv`, `test_settings_compat_profile1_launch_e2e`, `test_settings_compat_profile2_enrollment_to_ready`, `test_settings_compat_auth_status_sentinel`, `test_settings_compat_role_launch_sentinel`, `test_settings_compat_scope_and_secret_hygiene`, `test_settings_compat_cross_regression`, `test_settings_compat_claude_required_options`, `test_settings_compat_documentation_contract`, `test_settings_compat_live_identity_projection` 12개 테스트를 추가한다. ② **공용 fixture helper** `OrchestratorProfileFixture.make_fake_executable()`(현재 `:164-192`)의 하드코딩된 Claude CLI probe를 갱신한다. 현재 `:183`의 `--help` 출력은 `--model --sandbox --ask-for-approval --append-system-prompt --settings --plugin-dir`라서 두 하드닝 플래그를 광고하지 않는다. 이를 다섯 Claude 옵션을 모두 광고하는 기본값으로 바꾸고, 광고 목록과 `--version` 문자열을 테스트별로 덮어쓸 수 있는 선택 인자로 노출한다. ③ **기존 테스트 `test_portable_cli_contract`**(현재 `:5108-5142`)의 `expected_contracts["claude"]["cli_required_options"]`(현재 `:5130-5132`) 3-option 리터럴을 exact ordered 5-option list로 동기화한다. ②와 ③ 외에 기존 92개 테스트의 본문·기대값은 변경하지 않는다. |
| `docs/session-account-profiles.md` | 수정(추가) | AC-18의 설정 격리 block과 AC-9의 profile2 운영 block을 추가한다. 두 block은 `docs/orchestrator-permission-profiles.md`의 같은 block과 byte-identical이어야 한다. 기존 절은 지우지 않는다. |
| `docs/orchestrator-permission-profiles.md` | 수정(추가) | 위와 같은 두 block을 byte-identical하게 추가한다. |
| `dot_config/ai-session/accounts.toml` | 검사만 | profile1 `config_home_mode = "provider_default"`와 profile2 explicit home이 보존됨을 AC-15가 확인한다. 이 파일은 변경하지 않는다. |
| `dot_local/libexec/ai_session_identity.py` | 검사만 | `canonical_identity()`의 네 필드 투영을 변경하지 않는다. AC-5가 이 함수를 그대로 사용한다. |

## Task dependencies

```
T1 (CLI required-option 계약)  ──┐
T2 (verifier/enrollment argv)  ──┼──> T4 (prescan 우회 경계)  ──> T5 (sentinel 보안 회귀)
T3 (role launch argv 하드닝)   ──┘                                  │
                                                                     ├──> T6 (profile lifecycle E2E)
                                                                     ├──> T7 (문서 계약)
                                                                     └──> T8 (scope·secret hygiene + 교차 회귀 + 전체 suite)
T9 (live identity projection, opt-in)  — T2 에만 의존, T5 이후 아무 때나
```

- **T1 내부 순서(fixture → 계약 네 곳)**: `make_fake_executable()`의 Claude help 광고 목록이 다섯 옵션을 광고하도록 먼저 바뀌어야 한다. 그러지 않으면 `verify_provider_cli_contract()`가 5-option을 요구하는 순간 `ai-claude` 엔트리포인트를 쓰는 기존 테스트가 전부 `blocked_cli_contract`로 실패한다. fixture 갱신과 네 계약 상수 변경 사이에서는 전체 suite를 판정하지 않는다.
- **T1 → T3**: `verify_provider_cli_contract()`가 5-option 계약을 요구하게 된 뒤에야 role launch가 하드닝 argv를 만들어도 계약 검사를 통과한다. 순서가 바뀌면 T3의 테스트가 `blocked_cli_contract`로 잘못 실패한다.
- **T2, T3 → T4**: prescan 우회는 "하드닝이 증명된 경로"에서만 허용되므로, 우회 대상 경로들이 먼저 하드닝돼야 한다. 먼저 우회부터 구현하면 보안 구멍이 열린 중간 상태가 생긴다.
- **T4 → T5**: sentinel 회귀는 우회가 적용된 뒤의 production path에서 훅이 실행되지 않음을 판정하므로 T4 완료가 전제다. 단 T5의 negative control(하드닝 없는 호출이 sentinel을 만든다)은 T4와 무관하게 먼저 작성해 fixture의 결함 탐지 능력을 증명한다.
- **T4 → T6**: profile1 `ready` 판정은 prescan 우회가 있어야 성립한다. profile2 lifecycle은 우회와 무관하지만 같은 fixture 인프라를 쓰므로 T6에 함께 둔다.
- **T1, T4 → T7**: 문서 block의 문구가 최종 플래그 집합과 status/exit 계약을 그대로 인용하므로 계약 확정 후에 쓴다.
- **T1~T7 → T8**: scope·secret hygiene과 교차 회귀는 모든 변경이 끝난 상태의 worktree를 판정한다.
- **T9**는 실제 설치본을 읽기 전용으로 호출하므로 다른 태스크의 산출물에 의존하지 않지만, R1.1 argv가 소스에 반영된 뒤(T2) 실행해야 의미가 있다.

생산되는 인터페이스: T1은 5-option 계약 상수, T3은 최종 provider argv 검증 함수, T5는 sentinel fixture helper(fake `claude` + 위험 settings + sentinel 경로)를 만들고 T6·T8이 소비한다.

## Tasks

### T1. Claude CLI required-option 계약을 5-option으로 확장하고 공유 계약 상수를 동기화한다

대상 AC: AC-17 (판정 CMD-2 `test_settings_compat_claude_required_options`)

이 태스크는 계약 상수를 **네 곳**에서 동시에 바꾼다. 네 곳이 어긋난 중간 상태에서는 `ai-claude` 계열 엔트리포인트를 쓰는 기존 테스트가 `blocked_cli_contract`로 대거 실패하므로(현재 `dot_local/bin/executable_ai-role-session:787-793`의 missing-option 차단), 3단계의 네 편집은 **한 묶음으로** 적용하고 그 사이에 전체 suite를 판정하지 않는다.

1. **fixture 선행 갱신.** `tests/test_orchestrator_profiles.py`의 공용 helper `OrchestratorProfileFixture.make_fake_executable()`(현재 `:164-192`)는 `name`이 `claude`일 때 `--version`을 `2.1.272 (Claude Code)`로, `--help`를 `--model --sandbox --ask-for-approval --append-system-prompt --settings --plugin-dir`로 하드코딩해 `body`보다 **먼저** 가로챈다(현재 `:168`, `:183`). 따라서 테스트 본문으로는 help 광고 목록을 바꿀 수 없다. 이 helper에 선택 인자(예: `cli_help_options=None`, `cli_version=None`)를 추가해 ① 기본 Claude help 광고 목록을 다섯 옵션 `--append-system-prompt --settings --plugin-dir --setting-sources --strict-mcp-config`로 올리고(Codex 세 옵션 문자열은 그대로 유지), ② 테스트별로 광고 목록과 버전 문자열을 덮어쓸 수 있게 한다. `--version` 기본값 `2.1.272 (Claude Code)`는 지원 범위 `>=2.1.269,<2.2.0` 안이므로 바꾸지 않는다. 이것은 G12 ①이 허용하는 **fixture 헬퍼** 편집이며 기존 테스트 본문은 건드리지 않는다.
2. **실패 관측.** `test_settings_compat_claude_required_options`를 작성한다. 판정 방법을 다음 두 층으로 고정하고 다른 추출 방식을 병용하지 않는다.
   - **목록 일치(정적).** `dot_config/ai-session/roles.toml`을 `tomllib`로 읽어 네 Claude role의 `cli_required_options`가 exact ordered list `["--append-system-prompt", "--settings", "--plugin-dir", "--setting-sources", "--strict-mcp-config"]`와 같은지 assert한다. `tests/check_installed_orchestrator_cli_contract.py`의 `EXPECTED_REQUIRED["claude"]`는 같은 파일을 import해 assert한다. `verify_provider_cli_contract()`의 expected 목록은 확장자 없는 실행 스크립트(`dot_local/bin/executable_ai-role-session:741-759`)의 **함수 지역 리터럴**이라 import할 수 없으므로, 그 파일 텍스트를 읽어 `"claude": {` 블록 안의 `"required": [ ... ]` 리터럴을 정규식으로 한 번 추출한 뒤 `ast.literal_eval`로 파싱해 같은 exact ordered list와 비교한다.
   - **행위(동적).** 1단계에서 노출한 override로 help 광고에서 `--setting-sources`만 제거한 fake `claude`와 `--strict-mcp-config`만 제거한 fake `claude`를 각각 만들어 role launch를 실행한다. 두 경우 모두 public `blocked_cli_contract`와 exit 4가 나오고 provider **session exec** 계수가 0임을 assert한다(G8에 따라 `--version`/`--help` probe 계수는 세지 않는다). 대조군으로 다섯 옵션을 모두 광고하는 기본 fake `claude`에서는 `blocked_cli_contract`가 발생하지 않음을 assert한다.
   실행: `/opt/homebrew/bin/python3.14 -m unittest tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_claude_required_options`. 기대: 세 목록이 모두 3-option이므로 정적 assert에서 `AssertionError`로 실패한다. 이 실패 출력을 증거로 기록한다.
3. **최소 구현(네 편집을 한 묶음으로).** ① `dot_config/ai-session/roles.toml:31,74,117,164`의 Claude `cli_required_options`, ② `dot_local/bin/executable_ai-role-session:748-752`의 `expected["claude"]["required"]`, ③ `tests/check_installed_orchestrator_cli_contract.py:27-30`의 `EXPECTED_REQUIRED["claude"]`, ④ 기존 테스트 `test_portable_cli_contract`(현재 `:5108-5142`)의 `expected_contracts["claude"]["cli_required_options"]`(현재 `:5130-5132`)를 모두 같은 exact ordered 5-option list로 바꾼다. ④는 G12 ②가 허용하는 유일한 기존 테스트 편집이며 assert 대상 성질(manifest와 승인 계약의 일치)은 그대로 두고 계약 상수만 갱신한다. `cli_version_range`, `cli_forbidden_options`, `EXPECTED_VERSIONS`, `EXPECTED_RANGES`, `EXPECTED_FORBIDDEN`, Codex 항목은 바꾸지 않는다.
4. **통과 확인.** `/opt/homebrew/bin/python3.14 -m unittest tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_claude_required_options tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_portable_cli_contract`를 실행해 exit 0과 `OK`를 기록한다. 이어 `/opt/homebrew/bin/python3.14 tests/test_orchestrator_profiles.py`(CMD-5)를 실행해 기존 92개가 여전히 통과함을 확인하고 건수를 기록한다. 이 시점의 CMD-5 통과가 PLAN-001·PLAN-002가 지적한 회귀가 실제로는 발생하지 않음을 보이는 증거다.

실패 처리: CMD-5에서 `ai-claude` 계열 테스트가 `blocked_cli_contract`로 실패하면 1단계 fixture 갱신이 불완전한 것이다. `help_advertises()`의 단어 경계 정규식 때문에 fake help 문자열에 제거 대상 플래그가 부분 문자열로 남으면 안 되므로, 제거 케이스는 해당 토큰을 문자열에서 완전히 삭제해 만든다. 롤백: 네 목록을 3-option으로 되돌리고 fixture 기본 광고 목록도 원래 문자열로 되돌린다.

### T2. verifier와 enrollment helper의 인증 조회 argv를 하드닝한다

대상 AC: AC-1 (판정 CMD-2 `test_settings_compat_verifier_argv`), AC-2 (판정 CMD-2 `test_settings_compat_enrollment_argv`)

1. **실패 관측.** `test_settings_compat_verifier_argv`와 `test_settings_compat_enrollment_argv`를 먼저 작성한다. 두 테스트는 PATH 선두에 argv를 파일로 기록하는 fake `claude`를 두고, 전자는 `executable_ai-session-verify-claude`를 직접 실행하며 후자는 `executable_ai-session-enroll-identity`를 실행한다. 두 테스트 모두 기록된 argv가 정확히 `["claude", "--setting-sources", "", "--strict-mcp-config", "auth", "status", "--json"]`이고 호출 횟수가 1임을 assert한다. `test_settings_compat_enrollment_argv`는 `AI_SESSION_SYNTHETIC_TEST`와 `AI_SESSION_SYNTHETIC_STATUS_JSON`을 **환경에서 제거**해 합성 분기를 비활성화하고(R3.2·AC-2), `AI_SESSION_IDENTITY_ROOT`만 임시 경로로 지정해 그 밖에 파일이 생기지 않음을 assert한다. verifier 테스트는 stdout이 exact 6 필드 compact JSON 한 줄이고 raw Claude 출력이 포함되지 않음을 함께 assert한다. 실행: `/opt/homebrew/bin/python3.14 -m unittest tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_verifier_argv tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_enrollment_argv`. 기대: 기록된 argv가 `["claude","auth","status","--json"]`이라 `AssertionError`로 실패한다.
2. **최소 구현.** `executable_ai-session-verify-claude`의 `_official_status()` argv와 `executable_ai-session-enroll-identity`의 `_identity_status()` 비합성 분기 argv를 exact 하드닝 argv로 바꾼다. timeout·FD·에러 처리·출력 스키마는 건드리지 않는다.
3. **통과 확인.** 같은 명령 재실행으로 exit 0과 `OK`를 기록한다.

실패 처리: fake `claude`가 `auth status` 하위 명령과 전역 플래그 순서를 구분해 기록하지 못하면 argv 전체 리스트를 그대로 직렬화해 비교한다. 롤백: 두 argv를 `["claude","auth","status","--json"]`으로 되돌린다.

### T3. role launch 최종 provider argv를 하드닝하고 두 경계에서 검증한다

대상 AC: AC-3 (판정 CMD-2 `test_settings_compat_role_launch_argv`)

1. **실패 관측.** `test_settings_compat_role_launch_argv`를 먼저 작성한다. 네 Claude role(`general`, `orchestrator`, `feature-orchestrator`, `global-orchestrator`) 각각에 대해 생성된 최종 provider argv가 `--setting-sources`를 정확히 1회 포함하고 그 값이 빈 문자열, `--strict-mcp-config`를 정확히 1회 포함, `--settings`를 정확히 1회 포함하며 그 경로가 digest 검증된 경로임을 assert한다. 또한 (a) caller가 `--strict-mcp-config`, `--mcp-config`, `--setting-sources`, `--settings`를 각각 추가로 넘긴 네 경우가 `blocked_policy`로 거부되고, (b) `--admitted` 경계에 하드닝이 빠진 위조 provider argv를 넘긴 경우가 exec 없이 `blocked_policy`로 닫히는지 assert한다. 실행: `/opt/homebrew/bin/python3.14 -m unittest tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_role_launch_argv`. 기대: `--strict-mcp-config` 부재로 `AssertionError` 실패.
2. **최소 구현.** `claude_command()` argv에 `--strict-mcp-config`를 추가하고, `CLAUDE_POLICY_ARGUMENTS`에 `--strict-mcp-config`·`--mcp-config`를 추가하며, 최종 argv 검증 함수를 도입해 `claude_command()` 반환 직전과 `admitted_main()` exec 직전 두 곳에서 각각 호출한다.
3. **통과 확인.** 같은 명령 재실행으로 exit 0과 `OK`를 기록한다.

실패 처리: `--setting-sources` 값이 빈 문자열이라 단순 `in` 검사로는 값 위치를 놓칠 수 있으므로 인덱스 기반으로 (옵션, 바로 다음 원소) 쌍을 확인한다. 롤백: 추가한 플래그와 검증 함수 호출을 제거한다.

### T4. 하드닝이 증명된 경로에서만 prescan을 건너뛴다

대상 AC: AC-4 (판정 CMD-1 `test_settings_compat_unhardened_route_fail_closed`)

1. **실패 관측.** `tests/test_ai_session.py`에 `test_settings_compat_unhardened_route_fail_closed`를 먼저 작성한다. 이 테스트는 **positive control과 negative control을 한 테스트 안에서 대비**시킨다.
   - **positive control(구현 전 반드시 실패).** 위험 settings가 있는 임시 Claude home에서, 절대경로·regular·non-symlink·실행 가능 조건을 모두 만족하는 trusted `--verifier`로 `status --accept-usage-unknown`을 실행하면 결과가 `blocked_policy`가 **아니어야** 한다고 assert한다. 구현 전 현재 코드는 `prescan_selected_claude_home()`을 무조건 호출하므로(`dot_local/bin/executable_ai-session:1558-1559`) 이 assert는 `AssertionError: 'blocked_policy' == 'blocked_policy'` 형태로 확정적으로 실패한다. 이것이 G3이 요구하는 관측 가능한 Red다.
   - **negative control(구현 전후 모두 통과해야 함).** (a) `--verifier`가 symlink이거나 상대경로이거나 실행 불가인 세 경우, (b) launch의 provider command가 하드닝 검증 경계를 통과하지 않는 임의 명령인 경우에 대해 같은 위험 settings 아래에서 child 실행 0회로 fail-closed됨을 assert한다. 아울러 `BENIGN_CLAUDE_SETTING_TYPES`가 정확히 `{"$schema": str, "spinnerTipsEnabled": bool, "theme": str}`임을 assert한다.
   실행: `/opt/homebrew/bin/python3.14 -m unittest tests.test_ai_session.AiSessionCliTests.test_settings_compat_unhardened_route_fail_closed`. 기대: positive control assert에서 `AssertionError`로 실패하고 negative control assert는 통과한다. 이 실패 출력을 증거로 기록한다.
2. **최소 구현.** `executable_ai-session`의 `status()`에서 `binding.provider == "claude"`이고 trusted verifier seam 조건을 만족할 때 `prescan_selected_claude_home()`을 건너뛴다. `launch()`에서는 provider command가 T3의 하드닝 검증 경계를 통과할 때만 건너뛴다. `executable_ai-role-session`의 `claude_command()`·`admitted_main()` prescan도 T3 검증 통과 시에만 건너뛴다.
3. **통과 확인.** 같은 명령 재실행으로 exit 0과 `OK`를 기록한다.

실패 처리: 우회 조건이 넓어지면 보안 회귀이므로 T5의 sentinel 테스트가 즉시 잡는다. 롤백: 우회 분기를 제거해 모든 경로가 prescan을 수행하게 되돌린다(호환성은 다시 막히지만 안전한 상태다).

### T5. sentinel negative control로 훅 미실행을 증명한다

대상 AC: AC-10 (판정 CMD-2 `test_settings_compat_auth_status_sentinel`), AC-11 (판정 CMD-2 `test_settings_compat_role_launch_sentinel`)

1. **실패 관측.** 공용 fixture helper를 만든다. 임시 `CLAUDE_CONFIG_DIR`의 `settings.json`에 sentinel 파일을 쓰는 `hooks`, 자식 프로세스를 띄우는 `mcpServers`, 주입 표식이 있는 `env`, `permissions`를 넣는다. fake `claude`는 전달받은 argv를 보고 `--setting-sources ""`가 없을 때만 그 settings를 읽어 hook을 실행하고 sentinel을 만든다. `test_settings_compat_auth_status_sentinel`은 (a) 하드닝 없는 negative control 호출이 sentinel을 **생성함**을 먼저 assert해 fixture의 탐지 능력을 증명하고, (b) hardened verifier와 hardened enrollment 경로가 sentinel·MCP child·주입 env를 하나도 만들지 않음을 assert한다. `test_settings_compat_role_launch_sentinel`은 같은 판정을 strict role launch의 provider 경로에 적용한다. 실행: `/opt/homebrew/bin/python3.14 -m unittest tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_auth_status_sentinel tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_role_launch_sentinel`. 기대: negative control assert는 통과하고 production path assert가 실패하거나(우회 전) 두 번째 테스트가 role argv 미하드닝으로 실패한다.
2. **최소 구현.** T2·T3·T4의 변경만으로 production path가 sentinel을 만들지 않아야 한다. 여기서 프로덕션 코드를 추가로 고쳐야 한다면 그 사실이 T2~T4의 불완전성을 뜻하므로 해당 태스크로 돌아가 보완한다.
3. **통과 확인.** 같은 명령 재실행으로 exit 0과 `OK`를 기록하고, sentinel 파일이 negative control 경로에만 존재함을 함께 기록한다.

실패 처리: sentinel이 production path에서 하나라도 생기면 보안 판정 실패로 즉시 중단하고 이후 태스크를 진행하지 않는다. 롤백: T4의 우회 분기를 제거한다.

### T6. profile1 status·launch와 profile2 lifecycle을 격리 E2E로 검증한다

대상 AC: AC-6 (판정 CMD-1 `test_settings_compat_profile1_status`), AC-7 (판정 CMD-2 `test_settings_compat_profile1_launch_e2e`), AC-8 (판정 CMD-2 `test_settings_compat_profile2_enrollment_to_ready`)

1. **실패 관측.** 세 테스트를 먼저 작성한다.
   - `test_settings_compat_profile1_status`(`tests/test_ai_session.py`): 임시 provider-default home의 `settings.json`을 Spec `## Problem and context`의 실측 16개 키 fixture 계약과 **키 집합·각 JSON 타입이 정확히 같게** 구성하되 실제 값은 쓰지 않는다. 합성 matched identity와 `--accept-usage-unknown`으로 `status`를 실행해 `{"status":"ready", ...}`와 exit 0을 assert하고 `blocked_policy`가 아님을 assert한다.
   - `test_settings_compat_profile1_launch_e2e`(`tests/test_orchestrator_profiles.py`): 같은 16개 키 fixture에서 strict role launch가 fake Claude를 정확히 1회 session exec하고 최종 argv가 하드닝 계약을 만족하며 `blocked_policy`가 아님을 assert한다.
   - `test_settings_compat_profile2_enrollment_to_ready`(`tests/test_orchestrator_profiles.py`): 임시 identity root에서 ① 첫 `status`가 `enrollment_required`/`identity_status="not_enrolled"`/`identity_enroll_foreground`/exit 3, ② 명시적 helper 실행이 `enrolled`/exit 0, ③ 두 번째 `status`가 `ready`/exit 0임을 **이 순서대로** assert하고, backend가 helper를 자동 호출한 횟수가 0이며 profile 간 파일 복사가 0임을 assert한다.
   실행: `/opt/homebrew/bin/python3.14 -m unittest tests.test_ai_session.AiSessionCliTests.test_settings_compat_profile1_status` 및 `/opt/homebrew/bin/python3.14 -m unittest tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_profile1_launch_e2e tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_profile2_enrollment_to_ready`. 기대: 앞의 둘은 T4 이전 상태에서 `blocked_policy`로 실패하고, 세 번째는 fixture 미구축으로 실패한다.
2. **최소 구현.** T1~T4의 변경으로 충족돼야 한다. 추가 프로덕션 변경이 필요하면 해당 태스크로 돌아간다.
3. **통과 확인.** 같은 명령 재실행으로 exit 0과 `OK`를 기록한다.

실패 처리: profile2가 ①에서 `enrollment_required`가 아니거나 helper 없이 `ready`가 되면 자동 enrollment 회귀이므로 즉시 중단한다. 롤백: 해당 테스트가 가리키는 태스크의 롤백 절차를 따른다.

### T7. 두 운영 문서에 byte-identical 계약 block을 추가한다

대상 AC: AC-9 (판정 CMD-2 `test_settings_compat_documentation_contract`), AC-18 (판정 CMD-2 `test_settings_compat_documentation_contract`)

1. **실패 관측.** `test_settings_compat_documentation_contract`를 먼저 작성한다. `docs/session-account-profiles.md`와 `docs/orchestrator-permission-profiles.md`에서 설정 격리 block과 profile2 운영 block을 각각 추출해 **두 파일 사이에서 byte-identical**한지 assert하고, 설정 격리 block이 exact 문구 `profile1 provider-default 설정은 보존한다.`와 `verifier·enrollment·role provider는 --setting-sources "" --strict-mcp-config로 user/project/local settings와 비검토 MCP를 로드하지 않는다.`를 포함하는지, profile2 block이 AC-9가 열거한 exact status 명령·exact helper 명령·순서·세 status/exit 쌍·경계 문구를 모두 포함하는지 assert한다. 실행: `/opt/homebrew/bin/python3.14 -m unittest tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_documentation_contract`. 기대: 두 문서에 해당 block이 없어 실패한다.
2. **최소 구현.** 두 문서에 같은 두 block을 byte-identical하게 추가한다. 기존 절은 삭제하지 않는다.
3. **통과 확인.** 같은 명령 재실행으로 exit 0과 `OK`를 기록한다.

실패 처리: 두 문서의 block이 한 글자라도 다르면 테스트가 실패하므로 한 곳에서 작성해 복사한다. 롤백: 추가한 두 block을 제거한다.

### T8. scope·secret hygiene과 교차 회귀, 전체 suite를 확인한다

대상 AC: AC-12 (판정 CMD-1 및 CMD-2 `test_settings_compat_` 전체), AC-13 (판정 CMD-3 `tests/test_ai_session.py`), AC-14 (판정 CMD-5 `tests/test_orchestrator_profiles.py`), AC-15 (판정 CMD-2 `test_settings_compat_scope_and_secret_hygiene`), AC-16 (판정 CMD-2 `test_settings_compat_cross_regression`)

1. **실패 관측.** 두 테스트를 먼저 작성한다.
   - `test_settings_compat_scope_and_secret_hygiene`: `git status --porcelain`의 경로에서 G7 제외 집합(`docs/development/2026-09-17-111-profile-settings-compat/`, `.claude/quality-state/`)을 뺀 나머지가 G7 허용 10개 파일의 부분집합인지 assert한다. 아울러 `dot_config/ai-session/accounts.toml`의 profile1 `config_home_mode = "provider_default"`와 profile2 explicit home 문자열이 보존됐는지, `docs/development/2026-09-16-111-profile-onboarding/`에 변경이 없는지, 변경된 파일 내용에 이메일 형태·UUID 형태·64자 hex digest·`sk-` 접두 문자열이 없는지 assert한다.
   - `test_settings_compat_cross_regression`: 하나의 시나리오에서 위험 키가 있는 16키 settings를 그대로 둔 채 profile1 `status`가 `ready`/exit 0이고 role launch가 성공하며, **동시에** verifier·enrollment·role provider 어느 경로에서도 sentinel·MCP child·주입 env가 0개임을 같은 테스트 안에서 assert한다.
   실행: `/opt/homebrew/bin/python3.14 -m unittest tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_scope_and_secret_hygiene tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_cross_regression`. 기대: 미작성 상태에서 실패한다.
2. **최소 구현.** 앞 태스크들의 변경으로 충족돼야 한다. scope 위반이 발견되면 허용 집합 밖 파일의 변경을 되돌린다.
3. **통과 확인.** 두 targeted 명령(CMD-1, CMD-2)과 두 전체 suite 명령(CMD-3, CMD-5)을 순서대로 실행해 각각 exit 0, `OK`, 그리고 전체 건수(기존 29+92 이상)를 기록한다.

실패 처리: 전체 suite에서 기존 테스트가 하나라도 깨지면 그 테스트가 가리키는 태스크로 돌아간다. 롤백: 해당 태스크의 롤백 절차.

### T9. 설치본 live identity projection 동일성을 읽기 전용으로 확인한다

대상 AC: AC-5 (판정 CMD-4 `test_settings_compat_live_identity_projection`)

1. **실패 관측.** `test_settings_compat_live_identity_projection`을 작성한다. 이 테스트는 `AI_SESSION_LIVE_CLAUDE_AUTH_PROBE=1`이 없으면 `unittest.SkipTest`로 건너뛴다. opt-in일 때 baseline `claude auth status --json`과 하드닝 `claude --setting-sources "" --strict-mcp-config auth status --json`을 각각 한 번 실행하고, 두 결과에서 `loggedIn`과 `canonical_identity()`의 `auth_method`·`org_id`·`subscription_type`을 **메모리에서만** 비교해 동일할 때 통과한다. assert 실패 메시지와 테스트 출력에는 필드 값·이메일·orgId·digest를 넣지 않고 필드 이름과 boolean만 넣는다. 실행(opt-out): `/opt/homebrew/bin/python3.14 -m unittest tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_live_identity_projection` → `skipped` 관측. 실행(opt-in): CMD-4.
2. **최소 구현.** T2의 argv 변경이 이미 되어 있어야 한다. 테스트 자체가 산출물이다.
3. **통과 확인.** CMD-4가 exit 0이고 출력에 값이 없음을 기록한다. CMD-5에서 같은 테스트가 `skipped`로 나타남을 함께 기록한다.

실패 처리: 두 projection이 다르면 R1.4에 따라 판정 실패이며 배포하지 않는다. identity를 `matched`/`ready`로 승격하지 않고 사용자에게 보고한다. 롤백: T2의 argv 변경을 되돌린다.

## Verification commands

실행 순서는 아래와 같다. 각 명령의 exit code와 출력 요약을 증거로 기록한다.

| 순서 | ID | 명령 | 기대 결과 |
|---|---|---|---|
| 1 | CMD-1 | `/opt/homebrew/bin/python3.14 -m unittest tests.test_ai_session.AiSessionCliTests.test_settings_compat_unhardened_route_fail_closed tests.test_ai_session.AiSessionCliTests.test_settings_compat_profile1_status` | 두 테스트가 실행·통과하고 exit 0. 실제 home·network·provider session exec 0회. |
| 2 | CMD-2 | `/opt/homebrew/bin/python3.14 -m unittest tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_verifier_argv tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_enrollment_argv tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_role_launch_argv tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_profile1_launch_e2e tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_profile2_enrollment_to_ready tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_auth_status_sentinel tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_role_launch_sentinel tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_scope_and_secret_hygiene tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_cross_regression tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_claude_required_options tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_documentation_contract` | 11개 테스트가 모두 실행·통과하고 exit 0. |
| 3 | CMD-3 | `/opt/homebrew/bin/python3.14 tests/test_ai_session.py` | 기존 29개를 포함한 전체 suite가 failure/error 없이 exit 0. |
| 4 | CMD-5 | `/opt/homebrew/bin/python3.14 tests/test_orchestrator_profiles.py` | 기존 92개를 포함한 전체 suite가 failure/error 없이 exit 0이고 live probe는 `skipped`. |
| 5 | CMD-4 | `AI_SESSION_LIVE_CLAUDE_AUTH_PROBE=1 /opt/homebrew/bin/python3.14 -m unittest tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_live_identity_projection` | baseline과 exact-order 하드닝 argv의 canonical projection이 같고 출력에 값이 노출되지 않으며 exit 0. |

CMD-1·CMD-2·CMD-3·CMD-5는 source tree만 실행하고 실제 `~/.claude`, `~/.local/share/ai-account-profiles`, 실행 중 세션을 변경하지 않는다. CMD-4만 설치된 `claude` CLI를 읽기 전용으로 두 번 호출하며 stdout을 파일에 저장하거나 값으로 출력하지 않는다. 어떤 명령도 model prompt, login/logout, enrollment write, chezmoi, tmux, git write를 실행하지 않는다.

보조 읽기 전용 확인(증거용, 게이트 아님): `git status --porcelain`으로 변경 집합이 G7을 만족하는지 육안 확인하고, `git diff --stat`으로 변경 규모를 기록한다.

## Rollout and rollback

롤아웃 순서는 T1 → T2 → T3 → T4 → T5 → T6 → T7 → T8 → T9다. 각 태스크는 자체 targeted 명령으로 닫히고, T8에서 전체 suite가 통과해야 구현이 끝난다. 그 뒤 오케스트레이터가 독립 검증(실제 git 변경과 claimed changed_files 대조, CMD-1~CMD-5 재실행)을 수행하고 코드 리뷰를 거친다.

배포는 두 단계다. ① 코드 리뷰 통과와 잔여 blocker 0 확인 후 PR #124 갱신. ② 사용자가 승인한 경우에만 draft 해제·머지·`chezmoi apply`. blocker가 남아 있으면 머지와 apply를 하지 않는다. `chezmoi apply`는 이 Plan의 구현·검증 범위 밖이며 사용자 확인 뒤 별도로 수행한다.

호환성 처리: registry schema, enrollment file schema, status JSON, launch record, account alias, home layout은 바뀌지 않으므로 데이터 마이그레이션이나 backfill이 없다. 배포 전 호환성 확인은 **CMD-4**(설치본 baseline·하드닝 조회의 canonical projection 동일성)와 **CMD-2 `test_settings_compat_claude_required_options`**(네 계약 상수 일치 + 미광고 help 두 경우의 `blocked_cli_contract`/exit 4)가 담당한다. `tests/check_installed_orchestrator_cli_contract.py`는 G13에 따라 배포 게이트로 사용하지 않는다. 그 script는 이번 변경 이전에 이미 frozen evidence 버전 불일치로 실패하며(실측 exit 1) 이를 통과시키려면 G7 허용 집합 밖 문서를 고쳐야 하므로, `EXPECTED_VERSIONS`와 frozen evidence 갱신은 별도 승인이 필요한 후속 작업으로 분리해 report에 기록한다.

롤백 트리거와 조치:

| 트리거 | 조치 |
|---|---|
| production path에서 sentinel·MCP child·주입 env가 하나라도 생김 | 즉시 중단. T4의 우회 분기를 제거해 전 경로 prescan 상태로 되돌린다. |
| CMD-4의 live projection 값 불일치 | 배포하지 않는다. T2의 argv 변경을 되돌리고 사용자에게 보고한다. |
| 기존 121개 테스트 중 하나라도 실패 | 해당 태스크의 롤백 절차를 수행하고 원인을 수정한 뒤 전체 suite를 재실행한다. |
| profile2가 helper 없이 `ready`가 됨 | 자동 enrollment 회귀. 즉시 중단하고 T6이 가리키는 변경을 되돌린다. |
| `--setting-sources`/`--strict-mcp-config` 중복 또는 caller override가 통과 | T3의 최종 argv 검증 함수를 보완한다. 통과 전까지 배포하지 않는다. |
| G7 허용 집합 밖 파일 변경 감지 | 그 변경을 되돌린 뒤 CMD-2를 재실행한다. |
| `tests/check_installed_orchestrator_cli_contract.py` 실행 실패 | 롤백 트리거가 **아니다**. G13이 기록한 사전 실패(frozen evidence가 2.1.272로 고정, 설치본은 2.1.274)이며 이번 변경의 회귀가 아니다. 판정 명령 CMD-1~CMD-5에 포함되지 않는다. |

롤백은 코드와 문서 변경을 되돌리고 롤아웃을 중단하는 것이며, 사용자 settings·credential·identity를 변경하지 않는다. allowlist를 넓히는 방향이나 하드닝 없이 prescan만 제거한 상태로는 절대 롤백하지 않는다. enrollment file format이 변하지 않아 롤백 시 데이터 변환이 없다.

## Acceptance-criteria traceability

| Criterion | Task | Verification command | Expected outcome |
|---|---|---|---|
| AC-1 | T2 | CMD-2 `test_settings_compat_verifier_argv` | verifier가 exact 하드닝 argv를 1회 사용하고 redacted 6-field 출력을 유지한다. |
| AC-2 | T2 | CMD-2 `test_settings_compat_enrollment_argv` | 합성 분기를 끈 enrollment helper가 fake `claude`를 1회 실제 실행해 같은 exact argv를 캡처하고 임시 identity root 밖에 파일을 만들지 않는다. |
| AC-3 | T3 | CMD-2 `test_settings_compat_role_launch_argv` | 네 role의 최종 argv가 exact-one 하드닝 계약을 만족하고 caller override·위조 admitted argv가 거부된다. |
| AC-4 | T4 | CMD-1 `test_settings_compat_unhardened_route_fail_closed` | 미하드닝 경로가 child 실행 없이 fail-closed하고 allowlist에 위험 키가 없다. |
| AC-5 | T9 | CMD-4 `test_settings_compat_live_identity_projection` | baseline과 exact-order 하드닝 argv의 canonical 네 필드가 동일하고 출력에 값이 없으며 exit 0. |
| AC-6 | T6 | CMD-1 `test_settings_compat_profile1_status` | 16키 fixture 아래 profile1 status가 `ready`/exit 0이고 `blocked_policy`가 아니다. |
| AC-7 | T6 | CMD-2 `test_settings_compat_profile1_launch_e2e` | 같은 fixture에서 role launch가 fake Claude를 1회 session exec하고 하드닝 argv를 만족한다. |
| AC-8 | T6 | CMD-2 `test_settings_compat_profile2_enrollment_to_ready` | `enrollment_required`/3 → `enrolled`/0 → `ready`/0 순서가 성립하고 자동 호출·복사가 0회다. |
| AC-9 | T7 | CMD-2 `test_settings_compat_documentation_contract` | 두 문서의 profile2 block이 byte-identical하고 exact 명령·순서·status/exit·경계 문구를 모두 포함한다. |
| AC-10 | T5 | CMD-2 `test_settings_compat_auth_status_sentinel` | negative control은 sentinel을 만들고 하드닝된 verifier·enrollment 경로는 sentinel·MCP·env를 0개 만든다. |
| AC-11 | T5 | CMD-2 `test_settings_compat_role_launch_sentinel` | 하드닝된 role provider 경로도 sentinel·MCP·env를 0개 만들고 정상 capture만 남긴다. |
| AC-12 | T8 | CMD-1 및 CMD-2 (`test_settings_compat_` 전체) | 추가된 모든 `test_settings_compat_*`가 기본 격리 모드에서 통과한다. |
| AC-13 | T8 | CMD-3 `tests/test_ai_session.py` | 기존 29개 포함 전체 suite가 failure/error 0으로 exit 0. |
| AC-14 | T8 | CMD-5 `tests/test_orchestrator_profiles.py` | 기존 92개 포함 전체 suite가 failure/error 0으로 exit 0이고 live probe는 skip된다. G12가 허용한 fixture helper와 `test_portable_cli_contract` 상수 동기화 뒤에도 92개가 모두 통과한다. |
| AC-15 | T8 | CMD-2 `test_settings_compat_scope_and_secret_hygiene` | 변경 집합이 G7 허용 10개 파일의 부분집합이고 보존 대상과 secret 위생이 확인된다. |
| AC-16 | T8 | CMD-2 `test_settings_compat_cross_regression` | 한 시나리오에서 호환성 성공과 주입 0개가 동시에 성립한다. |
| AC-17 | T1 | CMD-2 `test_settings_compat_claude_required_options` | `roles.toml` 네 role, `verify_provider_cli_contract()` 리터럴, 설치 checker `EXPECTED_REQUIRED["claude"]` 세 목록이 exact ordered 5-option으로 일치하고, 두 미광고 fake help 경우가 provider session exec 0회로 `blocked_cli_contract`/exit 4가 되며 대조군은 차단되지 않는다. |
| AC-18 | T7 | CMD-2 `test_settings_compat_documentation_contract` | 두 문서의 설정 격리 block이 byte-identical하고 exact 두 문구를 포함한다. |

<!-- strict-only:start -->

This block is required only for strict work. Any inapplicable subsection must be removed for non-strict work; within strict work, mark it as not applicable with a reason before review.

### Threat and trust boundaries

구현과 검증이 보존해야 할 세 신뢰 경계와 그 검사는 다음과 같다.

| 경계 | 보존해야 할 성질 | 검사 |
|---|---|---|
| verifier·enrollment helper가 Claude CLI를 exec하는 지점 | 미검토 user/project/local settings가 그 프로세스의 입력이 되지 않는다 | CMD-2 `test_settings_compat_verifier_argv`, `test_settings_compat_enrollment_argv`, `test_settings_compat_auth_status_sentinel` |
| role launcher가 provider argv를 만드는 지점 | exact-one 하드닝 플래그와 digest 검증 `--settings`만 포함하고 caller override를 거부한다 | CMD-2 `test_settings_compat_role_launch_argv` |
| admitted role process가 최종 Claude를 exec하는 지점 | 앞 단계의 환경 flag 하나만 신뢰하지 않고 argv를 독립 재검증한다 | CMD-2 `test_settings_compat_role_launch_argv`(위조 admitted argv 거부), `test_settings_compat_role_launch_sentinel` |

untrusted 입력으로 취급할 대상: user/project/local settings, caller provider arguments, verifier·provider의 stdout/stderr, account home 내용, 현재 인증 상태, enrollment 전 identity. 위협: settings hook 명령 실행, MCP server 기동, env/permission 주입, duplicate option으로 하드닝 무효화, forged admitted command, raw auth JSON 유출, 다른 profile identity overwrite. 통제: 차단 플래그 두 개, exact-one argv 검증, caller override 거부, 미확인 경로의 prescan 유지, captured/redacted adapter, explicit-only enrollment, 임시 fixture와 sentinel negative control.

### Authorization and tenant isolation

| 사례 | 기대 | 검증 명령 |
|---|---|---|
| `~/code/profile1` 아래 실제 경로에서 Claude 선택 | `claude-profile1` 고정 | CMD-1 `test_settings_compat_profile1_status` |
| `~/code/profile2` 아래 실제 경로에서 Claude 선택 | `claude-profile2` 고정 | CMD-2 `test_settings_compat_profile2_enrollment_to_ready` |
| profile2 enrollment가 profile1 digest 경로에 쓰기 시도 | 거부되고 profile1 digest 불변 | CMD-2 `test_settings_compat_profile2_enrollment_to_ready`(복사 0회 assert) |
| profile 간 설정·credential·identity 복사 | 0회 | CMD-2 `test_settings_compat_scope_and_secret_hygiene` |
| `accounts.toml`의 profile1 provider-default·profile2 explicit home | 보존 | CMD-2 `test_settings_compat_scope_and_secret_hygiene` |
| duplicate mapping·identity drift | 기존 fail-closed 상태 유지 | CMD-5 전체 suite(기존 92개) |

OS 수준 multi-tenant authorization 변경은 해당 없음이다. 이 저장소의 tenant 경계는 로컬 account profile과 그 credential/identity home이며 새 네트워크 service·사용자 role·ACL을 만들지 않는다.

### Migration, compatibility, and rollback

데이터 마이그레이션과 backfill은 해당 없음이다. registry schema(v2), enrollment file schema(v2 digest line), status JSON, launch record, account alias, home layout이 모두 불변이기 때문이다.

호환성 단계: ① CMD-2 `test_settings_compat_claude_required_options`가 네 계약 상수의 exact ordered 일치와, 하드닝 플래그를 광고하지 않는 설치본에서 provider session exec 0회로 `blocked_cli_contract`/exit 4가 나오는 fail-closed 동작을 확인한다. ② CMD-4가 baseline과 하드닝 조회의 canonical projection 동일성을 확인한다. 둘 중 하나라도 실패하면 배포하지 않고 기존 fail-closed 상태를 유지한다. `tests/check_installed_orchestrator_cli_contract.py`는 G13이 기록한 사전 실패(frozen evidence 버전 불일치, 이번 변경과 무관) 때문에 이 단계의 게이트로 쓰지 않으며, 이 작업은 그 파일의 `EXPECTED_REQUIRED["claude"]` 상수만 동기화한다.

롤백 트리거와 조치는 위 `## Rollout and rollback` 표가 정본이다. 롤백 전 증거로 실패한 명령의 exit code와 출력 요약, `git diff --stat`을 기록한다. 롤백은 코드·문서 변경만 되돌리며 사용자 settings·credential·identity를 건드리지 않는다.

### Failure recovery and observability

| 실패 | 공개 상태와 exit | 복구 |
|---|---|---|
| 하드닝 argv 누락·중복·재정의, 위조 admitted argv | `blocked_policy` 또는 `blocked_contract`, exit 4 | argv 생성부와 검증 함수를 수정한다. Claude child를 시작하지 않는다. |
| 설치본 help가 required option 미광고 | `blocked_cli_contract`, exit 4 | 설치본을 지원 범위로 맞추거나 배포를 중단한다. provider session exec 0회. |
| `auth status` nonzero·timeout·malformed JSON·필드 타입 오류 | verifier가 `unknown`/`identity_unverifiable` 반환 → 기존 `blocked_verifier` 계열, exit 3 | raw output 없이 상태만 보고한다. 자동 재시도 없음. |
| profile2 미등록 | `enrollment_required`, exit 3, `identity_enroll_foreground` descriptor | 사용자가 전경에서 helper를 실행한다. 자동 실행하지 않는다. |
| live projection 불일치 | 테스트 실패(값 비노출) | 배포 중단, T2 롤백, 사용자 보고. |
| sentinel·MCP child·주입 env 발생 | 테스트 실패 | 즉시 중단, T4 우회 분기 제거. |

새 persistent metric·trace·alert backend는 해당 없음이다. 로컬 CLI/chezmoi 저장소이고 외부 운영 service가 없기 때문이다. 판정 신호는 exact argv capture, session exec 계수, sentinel/MCP/env capture 부재, compact public JSON, unittest exit code다. 로그에는 profile alias, public status, safe boolean만 남기고 raw stdout/stderr, email, orgId, account ID, digest, private home path를 넣지 않는다.

### High-risk end-to-end verification

고위험 경로는 위험 키가 있는 provider-default profile1에서 status와 strict role launch를 수행하는 격리 E2E다. 필수 순서와 증거는 다음과 같다.

1. CMD-2의 negative control이 **먼저** sentinel을 생성해 fixture의 결함 탐지 능력을 증명한다. 이 단계가 통과하지 못하면 이후 판정은 무효다.
2. 같은 settings를 바꾸지 않은 production path에서 `test_settings_compat_cross_regression`이 status `ready`/exit 0, provider session exec 정확히 1회, exact 하드닝 argv, sentinel·MCP child·env capture 0개를 **한 테스트 안에서 동시에** 확인한다.
3. `test_settings_compat_profile2_enrollment_to_ready`가 profile2의 세 단계 lifecycle을 확인한다.
4. CMD-4가 설치본에서 canonical projection 동일성을 읽기 전용으로 확인한다.

중단 조건: projection mismatch, raw 값 출력, sentinel 생성, provider 중복 session exec, `blocked_policy` 재발, 자동 enrollment, 실제 사용자 파일 변경, 기존 suite 실패 중 하나라도 발생하면 high-risk verification을 PASS로 기록하지 않고 중단한다.

### No production mutation confirmation

자동 workflow에는 production mutation이 없다. 구현·검증 어느 단계도 `chezmoi apply`, 실제 login/logout, 브라우저 OAuth, 실제 identity enrollment, 모델 호출, tmux/session 조작, git write, commit/push/merge를 실행하지 않는다. 합성 enrollment는 임시 `AI_SESSION_IDENTITY_ROOT`에만 기록하고 테스트 종료 시 폐기한다. 유일한 live 동작인 CMD-4는 `claude auth status --json` 두 조합의 읽기 전용 호출이며 출력 값이나 파일을 남기지 않는다. PR draft 해제·머지·`chezmoi apply`는 이 Plan 밖의 별도 사용자 승인 단계다.

<!-- strict-only:end -->
