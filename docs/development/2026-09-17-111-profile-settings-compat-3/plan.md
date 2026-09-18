# Quality Goal Implementation Plan

- Task ID: 20260917T051955Z-111-설정-호환성-결함을-방향-b-verifier-identity-기반-467cbcd9
- Mode: strict
- Status: PLAN_REVIEW
- Created: 2026-09-17
- Updated: 2026-09-17
- Source goal: #111 설정 호환성 결함을 방향 B(온디스크 fixture 불변, 테스트 내부 fake CLI 생성) + verifier 정본 경로 동일성 기반 prescan skip 강화(가)로 해결한다

## Spec link

승인 대상 Spec: `/Users/lee-kyu-hwan/code/profile1/dotfiles/111-profile-onboarding/docs/development/2026-09-17-111-profile-settings-compat-3/spec.md`

- Spec 리뷰 라운드 2 **PASS**, score 91, blocker 0
- 이 Plan이 사용하는 Spec digest(SHA-256): `a8ac9618082c917a470224f125e4e2de4ba6b4cec15130c0f2050331f59ef2e5`
- 요구사항 R1.1~R3.3(10개), 수용 기준 AC-1~AC-27(27개), 판정 명령 CMD-1~CMD-7

Spec 라운드 2가 남긴 비차단 권고 세 건을 이 Plan이 구현 수준에서 확정한다.

- `SPEC-006`(Medium): Spec `CMD-7`이 표식 문자열 존재만 검사해 내용이 빈 evidence도 통과한다. → `G8`이 원시 전사 기반 내용 판정을 exact 형식으로 추가한다.
- `SPEC-007`(Medium): 세 축 재측정이 다섯 번째 수정 지점을 드러냈을 때의 경로가 미명시다. → `G9`가 실행 기반 분류와 중단·재승인 규칙을 확정한다.
- `SPEC-008`(Low): Problem 절의 확신 수준이 본문의 하한선 프레이밍과 어긋난다. → `G10`이 Plan의 충분성 근거를 한 곳으로 고정한다.

## Global constraints

- **G1 저장소 형태.** chezmoi source 저장소다. 이 작업에서 `chezmoi apply`를 실행하지 않는다. 구현·검증은 실행 권한 없는 source를 `/opt/homebrew/bin/python3.14`로 직접 실행한다.
- **G2 Python.** 모든 테스트·판정·검사 스크립트는 `/opt/homebrew/bin/python3.14`를 사용한다.
- **G3 test-first.** 모든 동작 변경은 테스트 선작성이다. (1) 테스트를 먼저 쓰거나 기대값을 먼저 바꾸고 실행해 **실패를 관측**하고 실패 메시지를 기록한 뒤, (2) 최소 production 변경을 적용하고, (3) 같은 명령을 다시 실행해 통과를 기록한다. 실패를 관측하지 않은 테스트는 완료 증거로 쓸 수 없다. `AC-25`의 Red 전사는 대표 증거다.
- **G4 인증 자동 실행 금지.** `claude login`/`logout`, 브라우저 OAuth, 실제 identity enrollment, 실제 모델 호출을 하지 않는다. 실제 `claude` CLI 호출은 `CMD-4`의 읽기 전용 `auth status` 두 번뿐이며 opt-in 환경변수가 있을 때만 실행된다.
- **G5 사용자 자산 불변.** `~/.claude`, `~/.local/share/ai-account-profiles/**`, `~/.config/ai-session/**`, 실행 중 tmux 세션과 process를 수정하지 않는다. 모든 격리 테스트는 `TemporaryDirectory()`, PATH 선두 fake executable, 임시 `HOME`만 사용한다.
- **G6 secret 금지.** token, API key, 이메일, account ID 원문, `orgId` 원문, canonical identity 원문, 전체 digest를 소스·테스트·fixture·문서·로그·명령 출력에 기록하지 않는다. 실측 16개 키 fixture는 키 이름과 JSON 타입만 재현한다.
- **G7 변경 범위.** 허용 집합은 Spec `R3.3`이 고정한 정확히 10개 파일이다: `dot_local/bin/executable_ai-session`, `dot_local/bin/executable_ai-role-session`, `dot_local/libexec/executable_ai-session-verify-claude`, `dot_local/libexec/executable_ai-session-enroll-identity`, `dot_config/ai-session/roles.toml`, `tests/test_ai_session.py`, `tests/test_orchestrator_profiles.py`, `tests/check_installed_orchestrator_cli_contract.py`, `docs/session-account-profiles.md`, `docs/orchestrator-permission-profiles.md`. 이 중 앞의 여섯(`executable_ai-session`, `executable_ai-role-session`, 두 libexec, `roles.toml`, `check_installed_orchestrator_cli_contract.py`)을 이 Plan에서 **production 파일**이라 부른다. scope checker 비교 대상은 `git status --porcelain` 경로 중 prefix 제외 집합(`docs/development/2026-09-17-111-profile-settings-compat-3/`, `docs/development/2026-09-17-111-profile-settings-compat-2/`, `docs/development/2026-09-17-111-profile-settings-compat/`, `.claude/quality-state/`)에 속하지 않는 모든 경로다. `dot_config/ai-session/accounts.toml`, `tests/fixtures/**`, `#118` 소유 경로, 앞선 두 실행 산출물은 변경 금지다.
- **G8 세 축 evidence 내용 판정(SPEC-006 해소).** Spec `CMD-7`의 표식 검사에 **더해** 다음을 판정하는 스크립트 `three-axis-content-check.py`를 evidence 디렉터리에 두고 `T1`·`T11`에서 실행해 exit 0을 기록한다. 판정은 evidence 요약이 아니라 **원시 unittest 전사**를 근거로 한다.
  - **원시 전사 필수.** evidence 디렉터리에 네 파일이 있어야 한다: `three-axis-A-test_ai_session.log`, `three-axis-A-test_orchestrator_profiles.log`, `three-axis-B-test_ai_session.log`, `three-axis-B-test_orchestrator_profiles.log`. 각 파일은 `/opt/homebrew/bin/python3.14 -m unittest <module>`의 stdout+stderr 전문이다.
  - **요약 줄 파싱(exact 정규식).** 각 전사에서 `^Ran (\d+) tests? in \d+(?:\.\d+)?s$` 줄과 결과 줄 `^OK(?: \((.*)\))?$` 또는 `^FAILED \((.*)\)$`를 정확히 하나씩 찾는다. 괄호 안은 `, `로 나눈 `key=value` 목록이며 key는 `failures`, `errors`, `skipped`, `expected failures`, `unexpected successes` 중 하나다. 알 수 없는 key는 판정 실패다.
  - **케이스 줄 파싱(exact 정규식).** `^(FAIL|ERROR): (test_\w+) \(([\w.]+)\)(?: \((.*)\))?$`로 케이스를 추출한다. method는 둘째 그룹, case label은 넷째 그룹(없으면 `-`)이다. `^(FAIL|ERROR): `로 시작하지만 이 정규식에 맞지 않는 줄이 하나라도 있으면 판정 실패다. 케이스 줄 수는 결과 줄의 `failures`+`errors` 합과 같아야 한다.
  - **evidence 필드(exact 형식).** evidence md에는 Spec `CMD-7` 표식에 더해 다음 줄이 있어야 한다. `stageA_ai_session_summary=<Ran 줄> | <결과 줄>`, `stageA_orchestrator_profiles_summary=<Ran 줄> | <결과 줄>`, `stageB_ai_session_summary=...`, `stageB_orchestrator_profiles_summary=...`(각각 해당 전사의 두 줄과 바이트 동일), 케이스마다 `failed_case=<A|B>|<module>|<method>|<label>` 한 줄, 분류마다 `classification=<method>|<expectation_changed|restored_by_helper>` 한 줄, `g9_gate=<pass|stop>`, `g9_expectation_changed=<쉼표로 구분한 method 목록 또는 빈 값>`. Spec의 `three_axis_ai_session_summary=`와 `three_axis_orchestrator_profiles_summary=`는 각각 stage A 요약과 같은 값을 쓴다.
  - **assert 목록.** ① 각 stage·suite의 `failed_case` 집합이 해당 전사에서 파싱한 (method, label) 집합과 **정확히 같다**. ② stage A orchestrator 실패 method 집합이 한 축 실측 8개 method(`test_portable_cli_contract`, `test_claude_untrusted_settings_prescan`, `test_verifier_provider_environments`, `test_stale_pwd_rejected`, `test_account_root_permission_separation`, `test_no_opposite_root_grant`, `test_exact_git_common_dir_permission`, `test_chezmoi_fixture_render`)의 **상위집합**이고, 그 8개 method에 속한 stage A 케이스 수가 10 이상이다. ③ `classification`이 (stage A 실패 method ∪ stage B 실패 method) 각각에 정확히 하나씩 있고 `G9`의 실행 기반 분류와 일치한다. ④ `g9_expectation_changed`가 `expectation_changed` 분류 method 집합과 같다. ⑤ `g9_gate=pass`이면 `G9` 통과 조건이 모두 참이고, 조건이 하나라도 거짓이면 `g9_gate=stop`이어야 하며 이때 스크립트는 **nonzero로 종료**해 구현 착수를 막는다.
- **G9 실행 기반 분류와 다섯 번째 지점 중단(SPEC-007 해소).** 분류는 추정이 아니라 `T1`의 두 실행 결과로 기계적으로 정한다.
  - **stage A** = HEAD `56d65ca` + **production 파일 전체 변경**(아래 File map의 production 파일 여섯 행 전부), 테스트 파일 무편집.
  - **stage B** = stage A + **수정 지점 4만**(`make_fake_executable`의 Claude help 분기, 정확한 형식은 `G12`) 적용.
  - `restored_by_helper` = stage A에서 실패하고 stage B에서 통과한 method. `expectation_changed` = stage B에서 실패한 method(stage A 통과 여부 무관).
  - **통과 조건(모두 참이어야 `g9_gate=pass`)**: (a) `expectation_changed` ⊆ {`test_claude_untrusted_settings_prescan`, `test_claude_official_status_contract`, `test_portable_cli_contract`}(수정 지점 1·2·3), (b) `expectation_changed`에 세 method가 **모두** 있다(알려진 지점을 재현하지 못하면 측정이 불완전하다), (c) `test_claude_untrusted_settings_prescan`의 stage B 실패 케이스 label이 모두 `selected-account-home`을 포함한다(project 구간 불변), (d) stage B `test_ai_session` 결과가 `Ran 29 ... OK`다.
  - **통과하지 못하면**: 실제 worktree 구현을 시작하지 않는다. 새 지점의 테스트 기대를 약화하지 않으며 helper 수정으로 재분류하지 않는다. 발견 사실과 전사를 사용자에게 보고하고 Spec `R3.2`·`AC-15`를 개정해 재승인받은 뒤에만 진행한다.
- **G10 충분성 근거 단일화(SPEC-008 해소).** 이 Plan은 `blast-radius-audit-v2.md`를 **수정 지점 단위의 근거**로만 쓴다. 충분성 근거는 두 가지뿐이다: ① 구현 착수 게이트로서 `T1`의 stage A/B 전수 결과와 `G9` 판정, ② 완료 판정으로서 `T11`의 전체 suite 결과와 `T11`의 production diff 동일성 확인. 어떤 태스크도 "N개 지점을 고치면 충분하다"는 주장을 근거로 삼지 않는다. Spec `:34`가 감사표를 더 강하게 표현한 부분이 있어도 이 Plan의 판정은 `G10`을 따른다.
- **G11 fail-closed 보존.** `BENIGN_CLAUDE_SETTING_TYPES`에 키를 추가하지 않는다. prescan 본체를 제거하지 않고 `R1.3`이 정의한 네 지점의 최종 상태만 구현한다.
- **G12 기존 테스트·helper 편집 경계(PLAN-004 해소).** 기존 121개 테스트 중 편집 대상은 Spec `R3.2`의 **정확히 네 수정 지점**뿐이다.
  - 수정 지점 1: `test_claude_untrusted_settings_prescan`의 account-home 구간(`tests/test_orchestrator_profiles.py:2124-2178`)만.
  - 수정 지점 2: `test_claude_official_status_contract`의 `:3014` 한 줄만.
  - 수정 지점 3: `test_portable_cli_contract`의 Claude literal(`:5130-5132`)과 Claude in-range 케이스(`:5191-5210`)만.
  - 수정 지점 4: `OrchestratorProfileFixture.make_fake_executable`에서 **정확히 두 줄**만 허용한다. 기존 `version = ...` 줄(`:168`) 바로 다음에 `help_text = "--model --sandbox --ask-for-approval" if name == "codex" else "--append-system-prompt --settings --plugin-dir --setting-sources --strict-mcp-config"` 한 줄을 추가하고, `--help` 분기의 `print("--model --sandbox --ask-for-approval --append-system-prompt --settings --plugin-dir")`(`:183`)를 `print({help_text!r})` 한 줄로 바꾼다. `:168`의 `version` 값은 불변이다. **helper에 선택 인자를 추가하지 않으며 다른 공용 helper는 편집하지 않는다.** 테스트별 맞춤 fake CLI가 필요하면 그 테스트 본문 안에서 파일을 직접 만든다.
  - 이 경계는 `T11`의 일회성 검사 스크립트 `test-edit-boundary-check.py`가 판정한다(`T11` 3단계). 영구 unit test로 두지 않는 이유: 특정 commit(`56d65ca`)과 테스트 본문 동일성을 영구 단언하면 이후 누구든 다른 테스트를 고치는 순간 깨지는 유지보수 함정이 되며, 이는 이슈 `#126`과 같은 구조다.
- **G13 git 쓰기 금지와 스크래치 예외(PLAN-008 해소).** 실제 worktree와 원본 저장소에서 `git add`/`commit`/`push`/`checkout`/`stash`/`restore`/`apply`와 PR merge를 실행하지 않는다. `git status`, `git diff`, `git show`, `git rev-parse`는 읽기 전용으로 허용한다. **스크래치 예외**: `T1`은 `.claude/quality-state/20260917T051955Z-111-설정-호환성-결함을-방향-b-verifier-identity-기반-467cbcd9/scratch-three-axis/` 아래에 한해 `git clone -q -s -b 111-fix/claude-profile-onboarding /Users/lee-kyu-hwan/code/dotfiles <scratch>/repo`와 그 클론 안의 `git -C <scratch>/repo apply`·`git -C <scratch>/repo diff`를 허용한다. 이 경로는 `.gitignore:25`로 무시되고 workspace fingerprint에서 제외되며 Codex workspace-write sandbox 안이다. `git checkout`은 스크래치에서도 쓰지 않는다(`-b`로 대체).
- **G14 소유 경계.** `#118` Plan과 `#70` 2단계의 선언 경계를 존중한다. `G7` 허용 집합 밖 파일을 만들거나 고치지 않으며 `dot_claude/skills/**`와 profile2 mirror 파일을 변경하지 않는다.
- **G15 범위 밖.** `tests/check_installed_orchestrator_cli_contract.py`의 `EXPECTED_VERSIONS`와 frozen evidence 버전 갱신은 이슈 `#126`이다. 이 작업은 같은 파일의 `EXPECTED_REQUIRED["claude"]` 상수만 5-option으로 동기화한다. 그 script의 사전 실패(exit 1)는 이번 변경의 회귀가 아니고 배포 게이트도 아니다.

## File map

| 파일 | 조치 | 책임과 영향받는 인터페이스 |
|---|---|---|
| `dot_local/bin/executable_ai-session` | 수정(production) | ① **정본 verifier 경로 단일 출처 함수** 신설: `os.environ["HOME"]`만 읽고 `expanduser` 후 `abspath`/`normpath`로 lexical 정규화하며 `resolve()`를 쓰지 않는다. `HOME`이 unset·empty·비절대면 `None`(pwd fallback 금지). ② `status()`(`:1555-1583`)의 prescan 호출(`:1558-1559`)을 R1.3(2) 조건부로 만든다: provider=claude이고 `--verifier`가 기존 네 검사(절대경로·regular·leaf non-symlink·executable)와 정본 경로 동일성을 모두 통과할 때만 skip. 술어는 **raise하지 않으며** 검사 실패는 skip 권한만 제거하고 기존 `blocked_verifier`는 이후 `verify_admission`(`:1228-1231`)이 만든다. ③ `launch()`(`:1500-1552`)의 prescan 호출(`:1517`)을 R1.3(1) 조건부로 만든다: provider=claude, strict registry, 유효 `ROLE_CONTRACT_ID`, `AI_ROLE_ADMITTED=1`, 실행 명령이 trusted `executable_ai-role-session --admitted` shape, metadata provider 일치, 내포 최종 provider argv의 R1.2 exact-one 검증을 **모두** 통과할 때만 skip. ④ **`launch` parser의 `--verifier`를 선택 인자로 바꾼다**(`:2136`). 생략되면 ①의 함수로 정본 경로를 채우고, 함수가 `None`이면 provider·verifier exec 전에 `blocked_verifier`/exit 3으로 닫는다(fail closed). `status` parser의 `--verifier`(`:2141`)는 required를 유지한다. ⑤ `BENIGN_CLAUDE_SETTING_TYPES`(`:104-108`), `validate_untrusted_claude_settings`(`:995-1027`), `prescan_selected_claude_home`(`:1030-1041`) 본체와 status JSON 스키마·exit code는 불변. |
| `dot_local/bin/executable_ai-role-session` | 수정(production) | ① `claude_command()`(`:1011-1074`) argv에 `--setting-sources ""` 바로 뒤로 `--strict-mcp-config` 추가, `--mcp-config`는 넣지 않는다(Spec D12). ② `CLAUDE_POLICY_ARGUMENTS`(`:57-70`)에 `--strict-mcp-config`, `--mcp-config` 추가. ③ 최종 provider argv 검증 함수 도입: `--setting-sources` 정확히 1회(다음 원소가 빈 문자열), `--strict-mcp-config` 정확히 1회, `--settings` 정확히 1회(digest 검증 경로), `--mcp-config` 0회. `claude_command()` 반환 직전과 `admitted_main()`의 `os.execvpe`(`:1327`) 직전 **두 경계**에서 호출. ④ `admitted_main()`의 `prescan_selected_claude_home` 호출(`:1303-1304`) **제거**, 그 자리에 metadata provider 일치와 ③의 재검증을 의무화. 실패는 `blocked_contract`, provider session exec 0회. ⑤ `verify_provider_cli_contract()`의 `expected["claude"]["required"]`(`:748-752`)를 exact ordered 5-option으로. ⑥ **기본 verifier 경로 literal 제거**(`:1444-1445`): caller가 `--verifier`를 주지 않으면 옵션을 생략한다. |
| `dot_local/libexec/executable_ai-session-verify-claude` | 수정(production) | `_official_status()`(`:44-56`) argv를 `["claude", "--setting-sources", "", "--strict-mcp-config", "auth", "status", "--json"]`로. timeout 10초, `capture_output=True`, `close_fds=True`, `pass_fds=()`, fail-closed, redacted 6-field stdout 계약 유지. |
| `dot_local/libexec/executable_ai-session-enroll-identity` | 수정(production) | `_identity_status()`(`:122-142`) **비합성 분기** argv를 같은 exact argv로. 합성 분기, `CLAUDE_CONFIG_DIR` 주입, owner-only digest 쓰기, `enrolled`/0·`duplicate_mapping`/`blocked_verifier`/3 계약 유지. |
| `dot_config/ai-session/roles.toml` | 수정(production) | 네 Claude role `cli_required_options`(`:31`, `:74`, `:117`, `:164`)를 exact ordered `["--append-system-prompt", "--settings", "--plugin-dir", "--setting-sources", "--strict-mcp-config"]`로. Codex 항목(`:12`, `:55`, `:98`, `:145`)과 그 밖의 키 불변. |
| `tests/check_installed_orchestrator_cli_contract.py` | 수정(production) | `EXPECTED_REQUIRED["claude"]`(`:27-30`)만 5-option으로. `EXPECTED_VERSIONS`(`:22`)·`EXPECTED_RANGES`·`EXPECTED_FORBIDDEN` 불변(G15). |
| `tests/test_orchestrator_profiles.py` | 수정(추가 + 수정 지점 1·2·3·4) | 신규 `test_settings_compat_*` 회귀 추가. 수정 지점 1·2·3·4를 `G12`가 정한 exact 범위로만 편집. 지점 2는 `T4`, 지점 3·4는 `T5`, 지점 1은 `T6`이 소유한다. 신규 테스트 `test_settings_compat_launch_prescan_gate`(R1.3(1) 양성·음성)와 `test_settings_compat_launch_default_verifier`(launch 기본 verifier 채움)를 포함한다. |
| `tests/test_ai_session.py` | 수정(추가만) | `test_settings_compat_status_canonical_verifier_prescan_gate`, `test_settings_compat_canonical_verifier_path_contract`, `test_settings_compat_profile1_status` 추가. **기존 29개 테스트 본문·기대값 불변.** |
| `docs/session-account-profiles.md` | 수정(추가) | profile1 운영 block, profile2 lifecycle block, 설정 격리 block 추가. 세 block은 다른 운영 문서와 byte-identical. 기존 절 삭제 금지. |
| `docs/orchestrator-permission-profiles.md` | 수정(추가) | 같은 세 block을 byte-identical하게 추가. |
| `dot_config/ai-session/accounts.toml` | 검사만 | 변경하지 않는다. 보존을 `AC-17`이 확인. |
| `tests/fixtures/orchestrator-profiles/**` | 검사만 | 한 바이트도 바꾸지 않는다. `AC-21`이 tree digest로 확인. |
| `dot_local/libexec/ai_session_identity.py` | 검사만 | 변경하지 않는다. `AC-6`이 그대로 사용. |
| `.claude/quality-state/20260917T051955Z-111-설정-호환성-결함을-방향-b-verifier-identity-기반-467cbcd9/evidence/` | 생성(비추적) | `T1`의 `cli-contract-blast-radius-three-axis-measured.md`, 원시 전사 4개, `three-axis-production.patch`, `three-axis-helper-point4.patch`, `three-axis-content-check.py`; `T2`의 `spec-red-canonical-verifier.txt`; `T11`의 `test-edit-boundary-check.py`와 실행 전사. 모두 gitignore 경로이며 G7 비교에서 제외된다. |

## Task dependencies

```
T1 (스크래치 stage A/B 전수 측정 + G9 게이트) ── gate pass ──┐
                                                              │
T2 (Red 전사) ──> T3 (정본 경로 단일 출처 · status skip · launch 기본 verifier)
                    │
                    ├──> T4 (verifier/enroll argv · 수정 지점 2)
                    │
                    └──> T5 (A: CLI 5-option · helper 지점 4 · portable 지점 3
                             B: role argv · launch skip R1.3(1) · admitted prescan 제거 R1.3(4))
                                   │
                                   ├──> T6 (수정 지점 1 · blast radius 계약)
                                   ├──> T7 (profile1/2 E2E · 교차 회귀)
                                   ├──> T8 (문서 3 block · 운영 명령)
                                   └──> T9 (scope · secret · fixture 불변)
                                              │
                                   T10 (live projection, opt-in) ──> T11 (전체 판정 · production diff 동일성 · 편집 경계)
```

- **T1 → 그 외 전부**: `AC-26`의 선행 태스크다. `G9` 게이트가 `pass`가 아니면 이후 태스크를 시작하지 않는다. `T1`이 만든 `three-axis-production.patch`와 `three-axis-helper-point4.patch`가 `T3`~`T5`의 production·helper 변경 원본이다.
- **T2 → T3**: `AC-25`의 Red는 `T3` 구현 이전 상태에서만 관측된다.
- **T3 → T4, T5**: 정본 경로 함수와 launch 기본 verifier 채움이 있어야 role launch 경로 테스트가 caller `--verifier` 없이도 성립한다.
- **T5 내부 순서**: A(CLI 계약·helper·portable) → B(launch 경로). A에서 helper 지점 4를 계약 네 곳보다 먼저 바꾼다. 그러지 않으면 실측이 확인한 8개 method가 `blocked_cli_contract`로 한꺼번에 실패한다. B의 R1.3(1)은 `executable_ai-session`, R1.3(4)는 `executable_ai-role-session`에 있으며 둘이 **함께** 적용돼야 launch 경로 skip이 성립한다.
- **R1.3(1) 소유 기록(PLAN-002 해소)**: R1.3(1) launch skip의 구현과 선작성 테스트 `test_settings_compat_launch_prescan_gate`는 `T5` B가 소유한다. 그 결과가 수정 지점 1(`AC-22`)의 성립 조건이므로 `AC-22`의 검증은 `T6`이 `test_claude_untrusted_settings_prescan`과 `test_settings_compat_launch_prescan_gate`를 함께 실행해 닫는다. 추적표 `AC-22` 행이 두 테스트를 모두 명시한다.
- **T5 → T6, T7, T8, T9**: 네 수정 지점의 새 기대값, profile1 `ready`, 문서 block 문구, scope 판정은 세 축 구현이 끝난 뒤에만 성립한다.
- **T4 → T10**: `CMD-4`는 R1.1 argv 반영 후에 의미가 있다.
- **T1~T10 → T11**: 최종 판정·production diff 동일성·편집 경계 검사는 모든 변경이 끝난 worktree를 판정한다.

## Tasks

### T1. 스크래치 공유 클론에서 stage A/B 전수 측정을 하고 G9 게이트를 판정한다

대상 AC: AC-26 ([문서] `docs/development/2026-09-17-111-profile-settings-compat-3/plan.md` T1 선행 배치), AC-27 (판정 CMD-7 `three-axis-content-check.py`)

**이 태스크는 실제 worktree의 어떤 파일도 편집하기 전에 수행한다. `G9` 게이트가 `pass`가 아니면 여기서 멈춘다.**

1. **스크래치 준비.** `SCRATCH=.claude/quality-state/20260917T051955Z-111-설정-호환성-결함을-방향-b-verifier-identity-기반-467cbcd9/scratch-three-axis`를 새로 만들고(이미 있으면 삭제 후 재생성) `git clone -q -s -b 111-fix/claude-profile-onboarding /Users/lee-kyu-hwan/code/dotfiles "$SCRATCH/repo"`로 클론한다. `git -C "$SCRATCH/repo" rev-parse HEAD`가 `56d65cacbba661d5d3d5929ec27c8f1909fe0bac`인지 확인한다. 다르면 중단·보고한다.
2. **baseline.** `$SCRATCH/repo`에서 `/opt/homebrew/bin/python3.14 -m unittest tests.test_ai_session`과 `... tests.test_orchestrator_profiles`를 실행해 `Ran 29 tests`+`OK`, `Ran 92 tests`+`OK`를 확인한다. 그린이 아니면 환경 문제로 중단·보고한다.
3. **stage A 적용과 실행.** 스크래치에서 File map의 **production 파일 여섯 행에 적힌 변경 전부**를 적용한다(R1.1 argv, R1.2 CLI 5-option·role `--strict-mcp-config`·`CLAUDE_POLICY_ARGUMENTS`·argv 검증 함수 두 경계, R1.3(1) launch skip, R1.3(2) status skip, R1.3(4) admitted prescan 제거, 정본 경로 단일 출처 함수, `launch --verifier` 선택화·기본 채움, 기본 verifier literal 제거, `EXPECTED_REQUIRED["claude"]`). 테스트 파일은 **한 줄도 바꾸지 않는다**. `git -C "$SCRATCH/repo" diff -- <production 파일 여섯>`을 evidence의 `three-axis-production.patch`로 저장한다. 두 suite를 실행해 전문을 `three-axis-A-test_ai_session.log`, `three-axis-A-test_orchestrator_profiles.log`로 저장한다.
4. **stage B 적용과 실행.** stage A 위에 `G12` 수정 지점 4의 **두 줄만** 적용한다. `git -C "$SCRATCH/repo" diff -- tests/test_orchestrator_profiles.py`를 `three-axis-helper-point4.patch`로 저장하고, 그 patch의 변경 줄이 `G12`가 허용한 두 줄뿐인지 확인한다. 두 suite를 다시 실행해 `three-axis-B-test_ai_session.log`, `three-axis-B-test_orchestrator_profiles.log`로 저장한다.
5. **evidence 작성.** `cli-contract-blast-radius-three-axis-measured.md`에 Spec `CMD-7` 표식 전부(`scratch_clone=git clone -s`, `scratch_head=56d65ca`, `axes=R1.1,R1.2,R1.3(2)`, `baseline_ai_session=Ran 29 OK`, `baseline_orchestrator_profiles=Ran 92 OK`, `tests_changed=0`, `actual_worktree_changed=0`, `source_repository_changed=0`, `installed_artifacts_changed=0`, `three_axis_ai_session_summary=`, `three_axis_orchestrator_profiles_summary=`, `sufficient_basis=test_methods_and_cases`, `captured_at=`)와 `G8`의 exact 필드(`stageA_*_summary`, `stageB_*_summary`, `failed_case=`, `classification=`, `g9_gate=`, `g9_expectation_changed=`)를 쓴다. Spec의 `axes` 표식은 그대로 두고, stage A가 R1.3(1)·R1.3(4)·기본 verifier 처리까지 포함했음을 `stageA_production_scope=full_production_file_map` 한 줄로 추가 기록한다. `tests_changed=0`은 stage A 기준이며 stage B의 helper 두 줄은 `stageB_helper_lines_changed=2`로 따로 기록한다.
6. **판정.** Spec `CMD-7`과 `/opt/homebrew/bin/python3.14 .claude/quality-state/20260917T051955Z-111-설정-호환성-결함을-방향-b-verifier-identity-기반-467cbcd9/evidence/three-axis-content-check.py`를 실행한다. 둘 다 exit 0이고 `g9_gate=pass`면 통과. `g9_gate=stop`이면 `G9`에 따라 중단하고 사용자에게 보고한다.
7. **정리.** 판정 뒤 `$SCRATCH`를 삭제한다. evidence 파일은 남긴다.

실패 처리: Codex sandbox가 스크래치 클론·실행을 막으면 오케스트레이터가 같은 명령을 사용자에게 보이는 tmux 전경 pane에서 실행해 같은 파일명으로 전사를 남긴다. 실제 worktree로 대체 측정하지 않는다. 롤백: `$SCRATCH` 삭제(실제 저장소 영향 0).

### T2. 구현 전 Red 전사를 기록한다

대상 AC: AC-25 (판정 CMD-6 `spec-red-canonical-verifier.txt`)

1. **테스트 선작성.** `tests/test_ai_session.py`에 `test_settings_compat_status_canonical_verifier_prescan_gate`를 작성한다. 같은 위험 selected-home settings에서 (a) 임시 `${HOME}/.local/libexec/ai-session-verify-claude`에 둔 정본 verifier는 `blocked_policy`가 아니어야 하고(양성), (b) 임시 디렉터리의 `verifier-N` 주입 verifier는 exact `blocked_policy`/exit 4여야 한다(음성). 두 verifier 모두 기존 네 파일 검사를 통과하는 파일이다.
2. **Red 관측.** `/opt/homebrew/bin/python3.14 -m unittest tests.test_ai_session.AiSessionCliTests.test_settings_compat_status_canonical_verifier_prescan_gate`를 실행한다. 현재 코드는 prescan을 무조건 호출하므로(`executable_ai-session:1558-1559`) 양성 assert가 확정적으로 실패하고 음성은 통과한다.
3. **전사 보존.** 전사를 evidence의 `spec-red-canonical-verifier.txt`에 저장하고 `test_settings_compat_status_canonical_verifier_prescan_gate`, `positive_actual=blocked_policy/4`, `positive_expected=ready/0`, `negative_actual=blocked_policy/4`, `unittest_exit=<nonzero>`, `captured_at=<시각>` 표식을 넣는다. `CMD-6`을 실행해 exit 0을 기록한다.

실패 처리: 양성 assert가 구현 전에 통과하면 테스트가 skip 경로를 검사하지 않는 것이므로 고쳐 다시 Red를 만든다. 롤백: 전사 파일 삭제.

### T3. 정본 경로 단일 출처, status skip, launch 기본 verifier를 구현한다

대상 AC: AC-4 (판정 CMD-1 `test_settings_compat_status_canonical_verifier_prescan_gate`), AC-5 (판정 CMD-1 `test_settings_compat_canonical_verifier_path_contract` 및 CMD-5 `test_settings_compat_launch_default_verifier`)

1. **실패 관측.** 두 테스트를 선작성한다.
   - `test_settings_compat_canonical_verifier_path_contract`(`tests/test_ai_session.py`): (a) 정본 경로 계산 함수가 `executable_ai-session`에만 있고 `executable_ai-role-session`에는 `.local/libexec/ai-session-verify-` literal이 없음을 소스 텍스트로 assert. (b) absolute `HOME`의 `..`·후행 slash가 정규화되어 정본과 같게 비교됨. (c) 정본 위치를 가리키는 **다른 symlink 표기**는 `resolve()`를 쓰지 않으므로 정본으로 승격되지 않음. (d) `HOME` unset·empty·비절대면 술어가 false이고 pwd fallback이 없음. (e) 유효하지 않은 verifier + 위험 settings 조합에서 결과가 `blocked_policy`이지 `blocked_verifier`가 아님(술어 비치명성).
   - `test_settings_compat_launch_default_verifier`(`tests/test_orchestrator_profiles.py`): 소스 `ai-session`을 설치하고 role entrypoint `ai-claude`를 **caller `--verifier` 없이** 실행한다. 임시 `HOME/.local/libexec/ai-session-verify-claude`에 호출을 기록하는 verifier를 두고, 그 파일이 정확히 한 번 호출되고 launch가 성공함을 assert한다. 같은 조건에서 `HOME`을 비절대로 두면 provider·verifier exec 0회로 `blocked_verifier`/exit 3임을 assert한다.
   실행: `/opt/homebrew/bin/python3.14 -m unittest tests.test_ai_session.AiSessionCliTests.test_settings_compat_canonical_verifier_path_contract`와 `/opt/homebrew/bin/python3.14 -m unittest tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_launch_default_verifier`. 기대: 둘 다 `AssertionError` 또는 argparse 오류로 실패.
2. **최소 구현.** `three-axis-production.patch`에서 해당 hunk를 옮겨 적용한다: 정본 경로 함수, `status()` 조건부 prescan(비치명 술어), `launch` parser `--verifier` 선택화와 기본 채움·fail closed, `executable_ai-role-session:1444-1445` literal 제거.
3. **통과 확인.** `CMD-1`의 세 테스트와 `test_settings_compat_launch_default_verifier`를 실행해 exit 0을 기록한다.

실패 처리: 술어가 raise하면 (e)가 잡는다. launch가 기본 verifier를 채우지 못하면 argparse 오류로 실패하므로 즉시 드러난다. 롤백: 조건부 분기·parser 변경·literal 제거를 되돌려 전 경로 prescan 상태와 required `--verifier`로 복귀한다.

### T4. verifier·enrollment argv를 하드닝하고 수정 지점 2를 편집한다

대상 AC: AC-1 (판정 CMD-2 `test_settings_compat_verifier_argv` `test_claude_official_status_contract`), AC-2 (판정 CMD-2 `test_settings_compat_enrollment_argv`), AC-11 (판정 CMD-2 `test_settings_compat_auth_status_sentinel`)

1. **실패 관측.** 세 신규 테스트를 선작성하고 수정 지점 2의 기대값을 먼저 바꾼다.
   - `test_settings_compat_verifier_argv`, `test_settings_compat_enrollment_argv`: PATH 선두 fake `claude`가 기록한 argv가 정확히 `["claude", "--setting-sources", "", "--strict-mcp-config", "auth", "status", "--json"]`이고 호출 1회. enrollment 쪽은 `AI_SESSION_SYNTHETIC_TEST`와 `AI_SESSION_SYNTHETIC_STATUS_JSON`을 환경에서 **제거**해 실제 subprocess를 탄다.
   - `test_settings_compat_auth_status_sentinel`: sentinel hook·`mcpServers`·`env`·`permissions`가 든 임시 Claude home에서 하드닝 없는 negative control이 sentinel을 **생성함**을 먼저 증명하고, 하드닝된 verifier·enrollment 경로가 sentinel·MCP child·env/permission capture를 0개 만듦을 assert.
   - 수정 지점 2: `test_claude_official_status_contract`의 `:3014`를 하드닝 argv로 바꾼다(`:3015`의 `open_fds == []` 유지).
   실행: `/opt/homebrew/bin/python3.14 -m unittest tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_verifier_argv tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_enrollment_argv tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_auth_status_sentinel tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_claude_official_status_contract`. 기대: argv 불일치로 실패.
2. **최소 구현.** `three-axis-production.patch`에서 두 libexec 스크립트의 argv hunk를 적용한다.
3. **통과 확인.** 같은 명령 재실행으로 exit 0을 기록한다.

실패 처리: negative control이 sentinel을 만들지 못하면 fixture가 결함을 탐지하지 못하므로 fixture를 고친 뒤 다시 판정한다. 롤백: 두 argv와 `:3014`를 원래대로 되돌린다.

### T5. CLI 5-option 계약·helper·portable 테스트(A)와 launch 경로 skip(B)을 구현한다

대상 AC: AC-3 (판정 CMD-2 `test_settings_compat_role_launch_argv`), AC-12 (판정 CMD-2 `test_settings_compat_role_launch_sentinel`), AC-16 (판정 CMD-2 `test_claude_settings_prescan` `test_effective_setting_sources` `test_claude_plugin_policy`), AC-19 (판정 CMD-2 `test_settings_compat_claude_required_options` `test_portable_cli_contract`)

**A. CLI 계약·helper·portable (수정 지점 3·4)**

1. **실패 관측.** `test_settings_compat_claude_required_options`를 선작성한다: `roles.toml` 네 Claude role, runtime validator 리터럴(`executable_ai-role-session` 텍스트에서 `"claude": {` 블록 안 `"required": [...]`를 정규식 1회 추출 후 `ast.literal_eval`), 설치 checker `EXPECTED_REQUIRED["claude"]`, helper의 Claude help, `test_portable_cli_contract`의 Claude literal이 모두 exact ordered 5-option이고 helper Claude version이 `2.1.272 (Claude Code)`임을 assert한다. 미광고 두 경우는 **테스트 본문 안에서** `--setting-sources`만 뺀 fake `claude`와 `--strict-mcp-config`만 뺀 fake `claude`를 직접 만들어 provider **session exec 0회**(`--version`/`--help` probe는 세지 않음)로 `blocked_cli_contract`/exit 4임을 assert한다. 동시에 수정 지점 3을 먼저 편집한다: `:5130-5132` literal을 5-option으로, `:5191-5210`의 Claude in-range 케이스를 테스트 본문에서 만든 5-option fake CLI로 바꾸고 codex in-range와 lower·upper·missing-option 여섯 케이스는 온디스크 fixture를 그대로 쓴다. 실행: `/opt/homebrew/bin/python3.14 -m unittest tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_claude_required_options tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_portable_cli_contract`. 기대: 계약 네 곳이 3-option이라 실패.
2. **최소 구현(한 묶음).** 먼저 `three-axis-helper-point4.patch`의 두 줄(수정 지점 4)을 적용하고, 이어 `three-axis-production.patch`에서 `roles.toml` 네 곳, `executable_ai-role-session:748-752`, `check_installed_orchestrator_cli_contract.py:27-30` hunk를 적용한다. helper와 계약 사이에서 전체 suite를 판정하지 않는다.
3. **통과 확인.** 같은 명령과 `AC-16`의 기존 세 테스트(`test_claude_settings_prescan`, `test_effective_setting_sources`, `test_claude_plugin_policy`)를 실행해 exit 0을 기록한다. 이 셋은 fake `claude`를 만들지 않아 설치본을 probe하며 설치본 help가 두 플래그를 광고하므로(2026-09-17 실측) 통과해야 한다. `tests/fixtures/orchestrator-profiles/**`가 편집되지 않았는지 `git status --porcelain tests/fixtures`가 빈 출력인지 확인한다.

**B. role argv와 launch 경로 skip (R1.3(1), R1.3(4))**

4. **실패 관측.** 세 테스트를 선작성한다.
   - `test_settings_compat_role_launch_argv`: 네 role의 최종 argv가 `--setting-sources` 1회(값 빈 문자열)·`--strict-mcp-config` 1회·digest 검증 `--settings` 1회·`--mcp-config` 0회이고, caller가 `--strict-mcp-config`·`--mcp-config`·`--setting-sources`·`--settings`를 넘긴 네 경우와 하드닝이 빠진 위조 admitted argv가 exec 전에 거부됨.
   - `test_settings_compat_role_launch_sentinel`: 배포 `dot_claude/dot_mcp.json`에 server가 있어도 MCP child 0개, sentinel·env/permission 주입 0개, fake provider session 정확히 1회.
   - `test_settings_compat_launch_prescan_gate`(PLAN-002 해소): 위험 selected-home settings 아래 **양성** — strict admitted `ai-claude` launch가 prescan을 skip하고 fake provider session 1회로 성공. **음성**(각각 prescan 유지 → `blocked_policy`/exit 4, provider 0회) — (a) 비strict(v1) registry, (b) 유효하지 않은 `ROLE_CONTRACT_ID`, (c) `AI_ROLE_ADMITTED` 미설정, (d) 실행 명령이 `executable_ai-role-session --admitted` shape가 아님, (e) metadata provider 불일치, (f) 내포 provider argv에 `--strict-mcp-config` 누락 또는 `--setting-sources` 중복.
   실행: `/opt/homebrew/bin/python3.14 -m unittest tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_role_launch_argv tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_role_launch_sentinel tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_launch_prescan_gate`. 기대: `--strict-mcp-config` 부재와 prescan 무조건 실행으로 실패.
5. **최소 구현.** `three-axis-production.patch`에서 `claude_command()` 플래그, `CLAUDE_POLICY_ARGUMENTS`, argv 검증 함수 두 경계, `admitted_main()` prescan 제거(R1.3(4)), `executable_ai-session` `launch()` 조건부 prescan(R1.3(1)) hunk를 적용한다.
6. **통과 확인.** 4단계 명령 재실행으로 exit 0을 기록한다.

실패 처리: `help_advertises()`가 단어 경계 정규식이므로 미광고 fake는 토큰을 문자열에서 완전히 뺀다. B의 양성이 실패하면 R1.3(1)과 R1.3(4)가 함께 적용됐는지 먼저 확인한다. 롤백: A는 계약 네 곳과 helper 두 줄·portable 편집을 되돌리고, B는 해당 hunk를 되돌린다.

### T6. 수정 지점 1과 blast radius 계약을 닫는다

대상 AC: AC-14 (판정 CMD-3 `tests/test_ai_session.py`), AC-15 (판정 CMD-2 `test_settings_compat_blast_radius_contract` 및 CMD-5 `tests/test_orchestrator_profiles.py`), AC-22 (판정 CMD-2 `test_claude_untrusted_settings_prescan` 및 CMD-5 `test_settings_compat_launch_prescan_gate`)

1. **실패 관측.** `test_settings_compat_blast_radius_contract`를 선작성한다. 수정 지점이 정확히 네 개임을 열거로 assert하고, 한 축 실측 8 method/10 case 목록을 별도 단위로 assert하며, `T1` evidence의 `classification=` 결과를 읽어 `restored_by_helper` method(`test_exact_git_common_dir_permission`, `test_chezmoi_fixture_render`를 포함한 helper 경유 method)와 `expectation_changed` method를 구분해 assert한다. 동시에 수정 지점 1을 먼저 편집한다: `test_claude_untrusted_settings_prescan`의 account-home 구간(`:2124-2178`)에서 `{"hooks":{}}` 케이스를 exit 4에서 하드닝 argv 성공으로 바꾸고, 같은 구간에 최종 provider argv R1.2 충족과 sentinel·MCP·env·permission 주입 0개를 보상 단언으로 추가한다. project 구간(`:2059-2090`)과 `{"theme":"dark"}` 대조군(`:2144`)은 건드리지 않는다. 실행: `/opt/homebrew/bin/python3.14 -m unittest tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_blast_radius_contract tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_claude_untrusted_settings_prescan`. 기대: 계약 테스트 미작성 상태에서 실패, 지점 1은 `T5` 이전이면 실패(이미 `T5`를 마쳤다면 이 단계의 기대값 편집 전 실행으로 실패를 관측한다).
2. **최소 구현.** production 변경은 없다. 필요한 production 동작은 `T3`·`T5`가 이미 적용했다.
3. **통과 확인.** 1단계 명령, `test_settings_compat_launch_prescan_gate`, `CMD-3` 전체를 실행해 exit 0을 기록한다. `CMD-3` 통과가 `tests/test_ai_session.py` 기존 29개 불변의 증거다.

실패 처리: `G12`를 넘는 기존 테스트 편집이 필요해지면 `G9`의 다섯 번째 지점이므로 즉시 중단·보고한다. 롤백: 지점 1 편집과 신규 계약 테스트를 되돌린다.

### T7. profile1/profile2 격리 E2E와 교차 회귀를 검증한다

대상 AC: AC-7 (판정 CMD-1 `test_settings_compat_profile1_status`), AC-8 (판정 CMD-2 `test_settings_compat_profile1_launch_e2e`), AC-9 (판정 CMD-2 `test_settings_compat_profile2_enrollment_to_ready`), AC-18 (판정 CMD-2 `test_settings_compat_cross_regression`)

1. **실패 관측.** 네 테스트를 선작성한다. `test_settings_compat_profile1_status`: 실측 16개 키·타입과 정확히 같은(값은 복사하지 않은) 임시 provider-default home에서 정본 verifier profile1 status가 합성 matched identity에 `ready`/0이고 `blocked_policy`가 아님. `test_settings_compat_profile1_launch_e2e`: 같은 fixture에서 strict role launch가 fake provider session 정확히 1회, 최종 argv R1.2 충족. `test_settings_compat_profile2_enrollment_to_ready`: R2.3 exact status 명령 두 번과 그 사이 exact helper 한 번으로 `enrollment_required`/3 → `enrolled`/0 → `ready`/0, helper 자동 호출·profile 간 복사 0회. `test_settings_compat_cross_regression`: **한 테스트 안에서** 같은 위험 settings를 바꾸지 않고 profile1 status `ready`/0, role provider session 1회, verifier·enrollment·role 전 경로 주입 0개를 동시에 assert. 실행: `/opt/homebrew/bin/python3.14 -m unittest tests.test_ai_session.AiSessionCliTests.test_settings_compat_profile1_status`와 `/opt/homebrew/bin/python3.14 -m unittest tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_profile1_launch_e2e tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_profile2_enrollment_to_ready tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_cross_regression`. 기대: 미작성·fixture 미구축으로 실패.
2. **최소 구현.** production 변경은 없다. 필요한 production 변경이 드러나면 `T3`~`T5`로 돌아가고 `T11`의 production diff 동일성 규칙을 따른다.
3. **통과 확인.** 같은 명령 재실행으로 exit 0을 기록한다.

실패 처리: profile2가 helper 없이 `ready`가 되면 자동 enrollment 회귀이므로 즉시 중단한다. 롤백: 해당 태스크 롤백.

### T8. 두 운영 문서에 byte-identical 세 block을 추가한다

대상 AC: AC-10 ([문서] `docs/session-account-profiles.md` `docs/orchestrator-permission-profiles.md`), AC-20 (판정 CMD-2 `test_settings_compat_documentation_contract` `test_documentation_contract` `test_profile_onboarding_documentation_contract`), AC-23 (판정 CMD-2 `test_settings_compat_profile1_operational_status_command`), AC-24 (판정 CMD-2 `test_settings_compat_profile1_noncanonical_verifier_policy`)

1. **실패 관측.** 세 테스트를 선작성한다. `test_settings_compat_documentation_contract`: 두 문서에서 profile1 block, profile2 block, 설정 격리 block을 추출해 파일 간 byte-identical과 Spec이 요구한 exact 문구·명령·순서·결과·`${HOME}` 치환 규칙·MCP 0개 고지를 assert. `test_settings_compat_profile1_operational_status_command`: 문서 block에서 profile1 명령을 **추출**해 `${HOME}`를 임시 absolute home으로 확장하고 profile1 mapped cwd에서 실행해 16-key settings 아래 `ready`/0. `test_settings_compat_profile1_noncanonical_verifier_policy`: 같은 fixture에서 verifier만 저장소 소스 경로 또는 다른 absolute regular leaf non-symlink executable로 바꾸면 **두 경우 모두** exact `blocked_policy`/4, verifier child 0회. 실행: `/opt/homebrew/bin/python3.14 -m unittest tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_documentation_contract tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_profile1_operational_status_command tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_profile1_noncanonical_verifier_policy`. 기대: block 부재로 실패.
2. **최소 구현.** 두 문서에 같은 세 block을 byte-identical하게 추가한다. 한 곳에서 작성해 복사하고 기존 절은 지우지 않는다.
3. **통과 확인.** 1단계 명령과 기존 `test_documentation_contract`, `test_profile_onboarding_documentation_contract`를 실행해 exit 0을 기록한다. `AC-10` 문서 판정은 두 파일의 profile2 block을 사람이 읽어 exact 명령·순서·세 결과·치환 규칙·경계 문구가 있는지 확인하고 그 위치(`파일:줄`)를 코드 리뷰 evidence에 적는다.

실패 처리: 두 문서의 block이 한 글자라도 다르면 실패한다. 롤백: 추가한 세 block 제거.

### T9. scope·secret hygiene과 fixture 바이트 불변을 확인한다

대상 AC: AC-13 (판정 CMD-2 `test_settings_compat_isolation_contract`), AC-17 (판정 CMD-2 `test_settings_compat_scope_and_secret_hygiene`), AC-21 (판정 CMD-2 `test_settings_compat_fixture_bytes_unchanged`)

1. **실패 관측.** 세 테스트를 선작성한다. `test_settings_compat_isolation_contract`: 모든 신규 `test_settings_compat_*`가 임시 directory·PATH 선두 fake executable·합성 identity root만 쓰고 실제 user home·network·model·session을 쓰지 않음. `test_settings_compat_scope_and_secret_hygiene`: `git status --porcelain` 경로에서 `G7` 네 prefix 제외 집합을 뺀 나머지가 허용 10개 파일의 부분집합, `accounts.toml`·`#118` 소유 경로·앞선 두 실행 산출물의 파일명·bytes 보존, 변경 파일 내용에 이메일·UUID·64자 hex digest·`sk-` 접두 문자열 없음. `test_settings_compat_fixture_bytes_unchanged`: `tests/fixtures/orchestrator-profiles/**` 7개 파일의 relative path + bytes tree digest가 Spec `AC-21` 고정값과 같음(file mode는 범위 밖이며 그 이유 주석). 실행: `/opt/homebrew/bin/python3.14 -m unittest tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_isolation_contract tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_scope_and_secret_hygiene tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_settings_compat_fixture_bytes_unchanged`. 기대: 미작성으로 실패.
2. **최소 구현.** 앞 태스크 변경으로 충족돼야 한다. scope 위반이 발견되면 허용 집합 밖 변경을 되돌린다.
3. **통과 확인.** 같은 명령 재실행으로 exit 0을 기록한다.

실패 처리: `tests/fixtures/**` 변경 감지 시 방향 B 위반이므로 즉시 되돌린다. 롤백: 해당 변경 되돌리기.

### T10. 설치본 live identity projection 동일성을 읽기 전용으로 확인한다

대상 AC: AC-6 (판정 CMD-4 `test_settings_compat_live_identity_projection`)

1. **실패 관측.** `test_settings_compat_live_identity_projection`을 작성한다. `AI_SESSION_LIVE_CLAUDE_AUTH_PROBE=1`이 없으면 `unittest.SkipTest`. opt-in일 때 baseline `claude auth status --json`과 exact-order 하드닝 argv를 각각 읽기 전용 실행하고 `loggedIn`과 `canonical_identity()`의 `auth_method`·`org_id`·`subscription_type`을 메모리에서만 비교한다. 출력·assert 메시지에 값·이메일·`orgId`·digest를 넣지 않는다. 테스트 파일이 없던 상태에서 `CMD-4`를 실행하면 테스트 미존재 오류로 실패함을 관측한다.
2. **구현.** `T4`의 argv 변경이 전제다. 테스트 자체가 산출물이다.
3. **통과 확인.** `CMD-4` exit 0과 값 비노출을 기록하고, `CMD-5`에서 같은 테스트가 `skipped`임을 기록한다.

실패 처리: projection이 다르면 R1.4에 따라 판정 실패이며 배포하지 않는다. identity를 `matched`/`ready`로 승격하지 않고 보고한다. 롤백: `T4` argv 변경 되돌리기.

### T11. 최종 판정, production diff 동일성, 테스트 편집 경계를 확인한다

이 태스크는 특정 AC를 소유하지 않는다. 모든 태스크가 끝난 worktree에서 최종 판정 전사를 만들고, `G10`의 완료 판정 근거와 `G12`의 편집 경계를 기계적으로 확인한다.

1. **판정 명령 실행.** `CMD-7` → `CMD-6` → `CMD-1` → `CMD-2` → `CMD-3` → `CMD-5` → `CMD-4` 순으로 실행하고 각 exit code·건수를 전사로 남긴다. `CMD-7`과 함께 `three-axis-content-check.py`도 다시 실행한다.
2. **production diff 동일성(G10 ②).** `git diff 56d65ca -- <production 파일 여섯>`의 출력에서 `index ` 줄을 제외한 본문이 `three-axis-production.patch`의 같은 처리 결과와 **바이트 동일**한지 확인한다. 다르면 — 코드 리뷰 수정 등으로 production이 바뀐 경우 — 현재 worktree production diff로 `T1`의 stage A/B를 스크래치에서 다시 실행해 `G9`를 재판정하고 evidence를 갱신한 뒤에만 완료로 진행한다.
3. **편집 경계 검사(G12).** evidence에 `test-edit-boundary-check.py`를 두고 실행해 exit 0을 기록한다. 이 스크립트는 `git show 56d65ca:<path>`와 현재 파일을 `ast`로 파싱해 다음을 assert한다. (a) `tests/test_ai_session.py`의 HEAD 기존 `test_*` method 29개 source segment가 모두 현재와 동일하다. (b) `tests/test_orchestrator_profiles.py`의 HEAD 기존 `test_*` method 중 `test_claude_untrusted_settings_prescan`, `test_claude_official_status_contract`, `test_portable_cli_contract`를 뺀 나머지 source segment가 모두 현재와 동일하다. (c) `OrchestratorProfileFixture`의 `make_fake_executable`을 뺀 모든 method source segment가 동일하다. (d) `make_fake_executable`의 HEAD 대비 줄 단위 diff가 `G12`의 **추가 한 줄**(`help_text = ...`)과 **교체 한 줄**(`print({help_text!r})`)뿐이다. (e) `test_claude_official_status_contract`의 diff가 `:3014` 한 줄 교체뿐이다.
4. **보조 확인(게이트 아님).** `git status --porcelain`으로 `G7` 충족을, `git diff --stat`으로 규모를 기록한다.

실패 처리: 기존 테스트가 하나라도 깨지면 해당 태스크로 돌아간다. 편집 경계 검사가 실패하면 허용 밖 편집을 되돌리고, 되돌릴 수 없는 필요가 있으면 `G9`대로 중단·보고한다. 롤백: 해당 태스크 롤백 절차.

## Verification commands

실행 순서와 기대 결과. Python은 모두 `/opt/homebrew/bin/python3.14`다.

| 순서 | ID | 목적 | 기대 결과 |
|---|---|---|---|
| 1 | CMD-7 | 세 축 사전 재측정 evidence 표식 (T1) | Spec 표식이 모두 있고 exit 0. 함께 실행하는 `three-axis-content-check.py`가 `G8` assert 전부와 `g9_gate=pass`로 exit 0. |
| 2 | CMD-6 | 구현 전 Red 전사 (T2) | 필수 표식이 모두 있고 exit 0. |
| 3 | CMD-1 | account launcher 회귀 3개 | 정본 양성·주입 음성, 단일 path source·정규화·비치명 술어, 16-key status가 통과하고 exit 0. |
| 4 | CMD-2 | orchestrator 회귀 30개 | 재정의·불변 기존 테스트와 신규 회귀가 모두 통과하고 exit 0. |
| 5 | CMD-3 | `tests/test_ai_session.py` 전체 | 기존 29개와 추가 회귀가 failure/error 없이 exit 0. |
| 6 | CMD-5 | `tests/test_orchestrator_profiles.py` 전체 | 기존 92개와 추가 회귀(`test_settings_compat_launch_prescan_gate`, `test_settings_compat_launch_default_verifier` 포함)가 failure/error 없이 exit 0, live probe `skipped`. |
| 7 | CMD-4 | 설치본 live projection (opt-in) | canonical projection 동일, 값 비노출, exit 0. |

보조 검사 스크립트(판정 명령 아님, evidence로 첨부): `three-axis-content-check.py`(T1·T11), `test-edit-boundary-check.py`(T11).

`CMD-1`·`CMD-2`·`CMD-3`·`CMD-5`는 source tree와 임시 directory·fake executable만 쓴다. `CMD-4`만 설치 Claude CLI를 읽기 전용 두 번 호출한다. `CMD-6`·`CMD-7`은 저장된 비밀 없는 evidence만 읽는다. 어떤 판정 명령도 실제 `~/.claude`, `~/.local/share/ai-account-profiles/`, 실행 중 session을 변경하거나 model·login/logout·browser·chezmoi·tmux·git write를 실행하지 않는다. `tests/check_installed_orchestrator_cli_contract.py`는 판정 명령에 포함되지 않는다(`G15`).

## Rollout and rollback

롤아웃 순서는 `T1` → `T2` → `T3` → `T4` → `T5`(A→B) → `T6` → `T7` → `T8` → `T9` → `T10` → `T11`이다. `T1`의 `g9_gate`가 `pass`가 아니면 이후를 시작하지 않는다. 각 태스크는 자체 targeted 명령으로 닫히고 `T11`에서 전체 판정·production diff 동일성·편집 경계가 통과해야 구현이 끝난다. 이후 오케스트레이터가 독립 검증(실제 git 변경과 claimed changed_files 대조, `CMD-1`~`CMD-7` 재실행)을 하고 실행 전사를 첨부해 코드 리뷰를 받는다.

배포는 두 단계다. ① 코드 리뷰 통과와 잔여 blocker 0 확인 후 PR #124 갱신. ② 사용자 승인 시에만 draft 해제·머지·`chezmoi apply`. blocker가 남으면 머지·apply 금지.

호환성: registry schema, enrollment file schema, status JSON, launch record, account alias, home layout 불변으로 데이터 마이그레이션 없음. `launch --verifier`는 required에서 선택으로 바뀌지만 생략 시 정본 경로를 채우므로 기존 호출(명시 `--verifier`)은 그대로 동작한다. role 세션 MCP server 0개는 Spec D12가 수용한 보안 결과이며 운영 문서가 고지한다.

| 트리거 | 조치 |
|---|---|
| `T1` `g9_gate=stop` | **G9**: 구현 중단, 전사와 함께 사용자 보고, Spec `R3.2`·`AC-15` 개정 후 재승인. 테스트 기대 약화·helper 재분류 금지 |
| `T11` production diff가 `three-axis-production.patch`와 다름 | 현재 production으로 `T1` stage A/B 재실행·`G9` 재판정·evidence 갱신 후에만 완료 |
| `test-edit-boundary-check.py` 실패 | 허용 밖 테스트·helper 편집을 되돌린다. 필요가 남으면 G9대로 중단·보고 |
| production path에서 sentinel·MCP child·env/permission 주입 | 즉시 중단. `T3`·`T5` B의 조건부 skip을 제거해 전 경로 prescan 상태로 |
| skip 술어가 raise해 `blocked_policy`가 `blocked_verifier`로 바뀜 | `T3` 술어를 비치명으로 수정. 통과 전 배포 금지 |
| launch가 caller `--verifier` 없이 argparse 오류 | `T3`의 parser 선택화·기본 채움을 확인·수정 |
| `CMD-4` projection 불일치 | 배포 금지. `T4` argv 되돌리고 보고 |
| 기존 121개 중 하나라도 실패 | 해당 태스크 롤백 후 전체 suite 재실행 |
| profile2가 helper 없이 `ready` | 자동 enrollment 회귀. 즉시 중단, `T7` 대상 변경 되돌리기 |
| `tests/fixtures/**` 변경 | 방향 B 위반. 즉시 되돌리고 `CMD-2` 재실행 |
| `G7` 허용 집합 밖 변경 | 되돌린 뒤 `CMD-2` 재실행 |
| `tests/check_installed_orchestrator_cli_contract.py` 실행 실패 | 롤백 트리거 **아님**(`G15`) |

롤백은 코드·문서 변경만 되돌리며 사용자 settings·credential·identity를 건드리지 않는다. allowlist 확장이나 하드닝 없는 prescan 제거 상태로 롤백하지 않는다.

## Acceptance-criteria traceability

| Criterion | Task | Verification command | Expected outcome |
|---|---|---|---|
| AC-1 | T4 | CMD-2 `test_settings_compat_verifier_argv` `test_claude_official_status_contract` | verifier가 exact 하드닝 argv를 1회 쓰고 timeout·FD·redaction 계약 유지. 기존 `:3014`가 같은 argv로 재정의되고 `:3015` FD 기대 유지. |
| AC-2 | T4 | CMD-2 `test_settings_compat_enrollment_argv` | 합성 분기를 끈 enrollment helper가 fake claude를 실제로 1회 실행해 같은 argv를 캡처하고 임시 identity root 밖에 파일을 만들지 않는다. |
| AC-3 | T5 | CMD-2 `test_settings_compat_role_launch_argv` | 네 role 최종 argv가 exact-one 하드닝·`--mcp-config` 0개이고 caller override·위조 admitted argv가 거부된다. |
| AC-4 | T3 | CMD-1 `test_settings_compat_status_canonical_verifier_prescan_gate` | 정본 verifier는 skip되어 `blocked_policy`가 아니고 주입 verifier는 exact `blocked_policy`/4. |
| AC-5 | T3 | CMD-1 `test_settings_compat_canonical_verifier_path_contract` 및 CMD-5 `test_settings_compat_launch_default_verifier` | 단일 path source, lexical 정규화, symlink 비승격, HOME 결손 시 false, 비치명 술어가 성립하고, caller `--verifier` 없는 launch가 정본 기본값을 쓰며 HOME 무효 시 fail closed. |
| AC-6 | T10 | CMD-4 `test_settings_compat_live_identity_projection` | baseline과 하드닝 argv의 canonical 네 필드 동일, 값 비노출, exit 0. |
| AC-7 | T7 | CMD-1 `test_settings_compat_profile1_status` | 16키 fixture·정본 verifier에서 profile1 status `ready`/0, `blocked_policy` 아님. |
| AC-8 | T7 | CMD-2 `test_settings_compat_profile1_launch_e2e` | 같은 fixture에서 role launch fake provider session 1회, 최종 argv R1.2 충족. |
| AC-9 | T7 | CMD-2 `test_settings_compat_profile2_enrollment_to_ready` | exact status 두 번과 helper 한 번으로 3 → 0 → 0, 자동 호출·복사 0회. |
| AC-10 | T8 | [문서] `docs/session-account-profiles.md` `docs/orchestrator-permission-profiles.md` | 두 문서 profile2 block이 byte-identical하고 exact 명령·순서·세 결과·치환 규칙·경계 문구를 포함함을 문서 위치로 확인. |
| AC-11 | T4 | CMD-2 `test_settings_compat_auth_status_sentinel` | negative control은 sentinel 생성, 하드닝 verifier·enrollment는 sentinel·MCP·env/permission 0개. |
| AC-12 | T5 | CMD-2 `test_settings_compat_role_launch_sentinel` | 배포 `dot_mcp.json` 존재에도 role launch MCP child 0개, 주입 0개. |
| AC-13 | T9 | CMD-2 `test_settings_compat_isolation_contract` | 신규 회귀 전부 임시 directory·fake executable·합성 identity root만 사용. |
| AC-14 | T6 | CMD-3 `tests/test_ai_session.py` | 기존 29개 기대값과 `blocked_policy`/4 유지, 파일 전체 통과. |
| AC-15 | T6 | CMD-2 `test_settings_compat_blast_radius_contract` 및 CMD-5 `tests/test_orchestrator_profiles.py` | 수정 지점 네 개와 실측 8 method/10 case가 다른 단위로 열거되고 `T1` 실행 기반 분류와 일치하며 전체 suite 통과. |
| AC-16 | T5 | CMD-2 `test_claude_settings_prescan` `test_effective_setting_sources` `test_claude_plugin_policy` | 설치본을 probe하는 기존 세 테스트가 5-option 계약 뒤에도 기존 기대값으로 통과. |
| AC-17 | T9 | CMD-2 `test_settings_compat_scope_and_secret_hygiene` | 변경 집합이 허용 10개 파일 부분집합이고 보존·secret 위생 확인. |
| AC-18 | T7 | CMD-2 `test_settings_compat_cross_regression` | 한 테스트에서 호환성 성공과 주입 0개가 동시에 성립. |
| AC-19 | T5 | CMD-2 `test_settings_compat_claude_required_options` `test_portable_cli_contract` | 다섯 계약 지점 exact 5-option, helper version 불변, 미광고 두 경우 session exec 0회로 `blocked_cli_contract`/4, portable 테스트의 Claude in-range가 test-local fake로 통과. |
| AC-20 | T8 | CMD-2 `test_settings_compat_documentation_contract` `test_documentation_contract` `test_profile_onboarding_documentation_contract` | 설정 격리 block byte-identical·exact 문구 포함, 기존 두 문서 계약 테스트 통과. |
| AC-21 | T9 | CMD-2 `test_settings_compat_fixture_bytes_unchanged` | fixture 7개 파일 path·bytes tree digest가 Spec 고정값과 동일. |
| AC-22 | T6 | CMD-2 `test_claude_untrusted_settings_prescan` 및 CMD-5 `test_settings_compat_launch_prescan_gate` | project 구간은 exit 4·`blocked_policy`·dispatch 0회 유지, account-home 구간만 재정의되고 보상 단언 성립, launch skip 양성과 여섯 음성 조건이 각각 성립. |
| AC-23 | T8 | CMD-2 `test_settings_compat_profile1_operational_status_command` | 문서에서 추출한 profile1 exact 명령이 16-key fixture에서 `ready`/0. |
| AC-24 | T8 | CMD-2 `test_settings_compat_profile1_noncanonical_verifier_policy` | 소스 경로와 다른 비정본 경로 모두 exact `blocked_policy`/4, verifier child 0회. |
| AC-25 | T2 | CMD-6 `spec-red-canonical-verifier.txt` | 구현 전 Red 전사가 고정 경로에 있고 필수 표식을 모두 포함. |
| AC-26 | T1 | [문서] `docs/development/2026-09-17-111-profile-settings-compat-3/plan.md` T1 선행 배치 | 이 Plan의 T1이 첫 구현 태스크보다 앞에 있고 R1.1·R1.2·R1.3(2)를 포함한 production 전체를 스크래치에 적용해 재측정하며 evidence 보존과 구현 착수 금지를 규정함을 문서 위치로 확인. |
| AC-27 | T1 | CMD-7 `three-axis-content-check.py` | evidence가 원시 전사 기반 두 suite 요약, 실패 method·case 이름, 실행 기반 `expectation_changed`/`restored_by_helper` 분류, G9 판정을 모두 포함하고 두 검사 모두 exit 0. |

<!-- strict-only:start -->

This block is required only for strict work. Any inapplicable subsection must be removed for non-strict work; within strict work, mark it as not applicable with a reason before review.

### Threat and trust boundaries

| 경계 | 보존할 성질 | 검사 |
|---|---|---|
| verifier·enrollment helper가 Claude CLI를 exec하는 지점 | 미검토 user/project/local settings가 그 프로세스 입력이 되지 않는다 | CMD-2 `test_settings_compat_verifier_argv`, `test_settings_compat_enrollment_argv`, `test_settings_compat_auth_status_sentinel` |
| role launcher가 provider argv를 만드는 지점 | exact-one 하드닝·digest 검증 `--settings`·`--mcp-config` 0개, caller override 거부 | CMD-2 `test_settings_compat_role_launch_argv` |
| `ai-session launch`가 prescan을 건너뛰는 지점 | trusted admitted shape·strict registry·contract·provider·argv를 **모두** 만족할 때만 skip | CMD-5 `test_settings_compat_launch_prescan_gate` |
| admitted role process가 최종 Claude를 exec하는 지점 | 환경 flag 하나만 신뢰하지 않고 argv를 독립 재검증하며 prescan 성공을 fallback으로 쓰지 않는다 | CMD-2 `test_settings_compat_role_launch_argv`, `test_settings_compat_role_launch_sentinel` |
| `status`/`launch`가 verifier를 선택하는 지점 | 임의 실행 파일을 `--verifier`로 주입해 prescan을 우회할 수 없고, 생략 시 정본만 쓰며 HOME 무효 시 fail closed | CMD-1 `test_settings_compat_status_canonical_verifier_prescan_gate`, CMD-5 `test_settings_compat_launch_default_verifier`, CMD-2 `test_settings_compat_profile1_noncanonical_verifier_policy` |
| 구현자가 테스트를 편집하는 지점 | 네 수정 지점 밖 기존 테스트·helper를 바꿔 실패를 가리지 못한다 | `T1` `three-axis-content-check.py`, `T11` `test-edit-boundary-check.py` |

untrusted 입력: user/project/local settings, caller provider arguments, verifier·provider stdout/stderr, account home 내용, 인증 상태, enrollment 전 identity, caller 제공 `--verifier`, `HOME` 환경값. 위협: hook 명령 실행, MCP server 기동, env/permission 주입, duplicate option으로 하드닝 무효화, forged admitted command, raw auth JSON 유출, 다른 profile identity overwrite, 비정본 verifier 주입, **테스트·helper 약화로 회귀 은폐**. 통제: 차단 플래그 두 개, exact-one argv 검증, caller override 거부, 정본 경로 동일성, skip 조건 전부 충족 요구, 미확인 경로 prescan 유지, captured/redacted adapter, explicit-only enrollment, sentinel negative control, 실행 기반 분류와 편집 경계 검사.

### Authorization and tenant isolation

| 사례 | 기대 | 검증 명령 |
|---|---|---|
| `~/code/profile1` mapped cwd에서 Claude 선택 | `claude-profile1` 고정 | CMD-1 `test_settings_compat_profile1_status` |
| `~/code/profile2` mapped cwd에서 Claude 선택 | `claude-profile2` 고정 | CMD-2 `test_settings_compat_profile2_enrollment_to_ready` |
| profile2 enrollment가 profile1 digest 경로에 쓰기 시도 | 거부, profile1 digest 불변 | CMD-2 `test_settings_compat_profile2_enrollment_to_ready` |
| profile 간 설정·credential·identity 복사 | 0회 | CMD-2 `test_settings_compat_scope_and_secret_hygiene` |
| `accounts.toml` profile1 provider-default·profile2 explicit home | 보존 | CMD-2 `test_settings_compat_scope_and_secret_hygiene` |
| 비정본 verifier로 prescan 우회 시도 | exact `blocked_policy`/4 | CMD-2 `test_settings_compat_profile1_noncanonical_verifier_policy` |
| admitted shape를 위조한 launch로 prescan 우회 시도 | prescan 유지, `blocked_policy`/4 | CMD-5 `test_settings_compat_launch_prescan_gate` |
| duplicate mapping·identity drift | 기존 fail-closed 유지 | CMD-5 전체 suite |

OS 수준 multi-tenant authorization 변경은 해당 없음이다. tenant 경계는 로컬 account profile과 그 credential/identity home이며 새 네트워크 service·사용자 role·ACL을 만들지 않는다.

### Migration, compatibility, and rollback

데이터 마이그레이션과 backfill은 해당 없음이다. registry schema(v2), enrollment file schema(v2 digest line), status JSON, launch record, account alias, home layout이 불변이기 때문이다.

호환성 단계: ① `CMD-2` `test_settings_compat_claude_required_options`가 다섯 계약 지점 일치와 미광고 설치본 fail-closed를 확인. ② `CMD-4`가 canonical projection 동일성을 확인. 둘 중 하나라도 실패하면 배포하지 않는다.

호환성 결과 고지: (a) role 세션은 MCP server를 시작하지 않는다(Spec D12, 운영 문서 고지). verifier·enrollment 비대화형 조회에는 MCP가 필요 없어 그 경로에서는 기능 손실이 없다. (b) `ai-session launch --verifier`는 선택 인자가 되며 생략 시 정본 경로를 쓴다. 명시 `--verifier`를 넘기는 기존 호출은 그대로 동작한다. (c) 비정본 `--verifier`로 `status`를 호출하면 설계상 계속 `blocked_policy`/4다. 운영 문서의 정본 명령을 쓴다.

`EXPECTED_VERSIONS`·frozen evidence 갱신은 이슈 `#126`이며 배포 게이트가 아니다.

롤백 트리거와 조치는 `## Rollout and rollback` 표가 정본이다. 롤백 전 실패 명령 exit code·출력 요약·`git diff --stat`을 기록한다.

### Failure recovery and observability

| 실패 | 공개 상태와 exit | 복구 |
|---|---|---|
| 하드닝 argv 누락·중복·재정의, 위조 admitted argv | `blocked_policy` 또는 `blocked_contract`, exit 4 | argv 생성부·검증 함수 수정. Claude child 미시작 |
| 설치본 help 필수 옵션 미광고 | `blocked_cli_contract`, exit 4 | 설치본 정비 또는 배포 중단. session exec 0회 |
| 비정본 verifier로 status | `blocked_policy`, exit 4 | 설계 동작. 정본 경로 명령 사용 |
| launch에서 `--verifier` 생략 + HOME 무효 | `blocked_verifier`, exit 3 | 유효한 absolute HOME으로 실행 |
| `--verifier` 파일 검사 실패 | `blocked_verifier`, exit 3 | 술어는 raise 안 함, `verify_admission`이 기존 계약 생성 |
| `auth status` nonzero·timeout·malformed JSON | `unknown`/`identity_unverifiable` → 기존 `blocked_verifier` 계열 | raw output 없이 상태만 보고, 자동 재시도 없음 |
| profile2 미등록 | `enrollment_required`, exit 3 | 사용자가 전경에서 helper 실행. 자동 실행 안 함 |
| live projection 불일치 | 테스트 실패(값 비노출) | 배포 중단, `T4` 롤백, 보고 |
| sentinel·MCP child·env/permission 주입 | 테스트 실패 | 즉시 중단, `T3`·`T5` B skip 제거 |
| `g9_gate=stop` | 검사 스크립트 nonzero | 구현 중단, 보고, Spec 개정·재승인 |

새 persistent metric·trace·alert backend는 해당 없음이다. 로컬 CLI/chezmoi 저장소이고 외부 운영 service가 없다. 판정 신호는 exact argv capture, session exec 계수, sentinel/MCP/env capture 부재, compact public JSON, unittest exit code, 원시 unittest 전사, 검사 스크립트 exit code다. 로그에는 profile alias·public status·safe boolean만 남긴다.

### High-risk end-to-end verification

1. `T1`이 스크래치에서 production 전체(stage A)와 helper 지점 4(stage B)를 실행해 원시 전사를 남기고 `three-axis-content-check.py`로 `g9_gate=pass`를 확정한다. 이 없이 구현을 시작하지 않는다.
2. `T2` Red 전사가 구현 전 양성 control 실패를 기록한다.
3. `CMD-2` sentinel negative control이 먼저 sentinel을 생성해 fixture 탐지 능력을 증명한다.
4. `test_settings_compat_cross_regression`이 같은 위험 settings에서 status `ready`/0, provider session 1회, exact 하드닝 argv, sentinel·MCP·env/permission 0개를 **한 테스트 안에서 동시에** 확인한다.
5. `test_settings_compat_launch_prescan_gate`가 launch skip 양성과 여섯 음성 조건을 확인한다.
6. `test_settings_compat_profile1_operational_status_command`와 `test_settings_compat_profile1_noncanonical_verifier_policy`가 정본 명령 성공과 비정본 차단을 대비 확인한다.
7. `test_settings_compat_profile2_enrollment_to_ready`가 profile2 세 단계를 확인한다.
8. `T11`이 production diff 동일성과 `test-edit-boundary-check.py`로 측정된 production과 편집 경계가 최종 worktree와 일치함을 확인한다.
9. `CMD-4`가 설치본 projection 동일성을 읽기 전용으로 확인한다.

중단 조건: `g9_gate=stop`, production diff 불일치 후 재측정 미수행, 편집 경계 위반, projection mismatch, raw 값 출력, sentinel 생성, provider 중복 session exec, `blocked_policy` 재발, 자동 enrollment, 실제 사용자 파일 변경, `tests/fixtures/**` 변경, 기존 suite 실패 중 하나라도 발생하면 PASS로 기록하지 않고 중단한다.

### No production mutation confirmation

자동 workflow에는 production mutation이 없다. 구현·검증 어느 단계도 `chezmoi apply`, 실제 login/logout, 브라우저 OAuth, 실제 identity enrollment, 모델 호출, tmux/session 조작, 실제 worktree·원본 저장소 git write, commit/push/merge를 실행하지 않는다. `T1`은 gitignore된 `.claude/quality-state/.../scratch-three-axis/` 안의 `git clone -s -b` 클론에서만 production을 바꾸고 판정 후 삭제한다. 합성 enrollment는 임시 `AI_SESSION_IDENTITY_ROOT`에만 기록하고 테스트 종료 시 폐기한다. 유일한 live 동작인 `CMD-4`는 `claude auth status --json` 두 조합의 읽기 전용 호출이며 값이나 파일을 남기지 않는다. PR draft 해제·머지·`chezmoi apply`는 이 Plan 밖의 별도 사용자 승인 단계다.

<!-- strict-only:end -->
