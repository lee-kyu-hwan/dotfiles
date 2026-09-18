# Quality Goal Report

- Task ID: 20260917T051955Z-111-설정-호환성-결함을-방향-b-verifier-identity-기반-467cbcd9
- Mode: strict
- Status: NEEDS_REDESIGN
- Created: 2026-09-17
- Updated: 2026-09-17
- Source goal: #111 설정 호환성 결함을 방향 B(온디스크 fixture 불변) + verifier 정본 경로 동일성 기반 prescan skip 강화(가)로 해결한다

## Classification

선택 모드 `strict`(사용자 명시, risk scan과 동일).

- 인증·authorization·계정 격리: `prescan_selected_claude_home`(`dot_local/bin/executable_ai-session:1030-1041`)과 admission(`launch:1517`, `status:1558-1559`) 변경.
- 보안 통제: `BENIGN_CLAUDE_SETTING_TYPES`(`:104-108`)는 `hooks`·`env`·`mcpServers` 등 임의 명령 실행 가능 키를 fail-closed로 차단한다.
- 신뢰 경계 축소: 방향 (가)는 status prescan skip 조건을 네 경로 검사에서 정본 verifier 경로 동일성까지 좁힌다.
- 선행 두 실행이 각각 `REVIEW_LIMIT_EXHAUSTED:plan`, `RECURRING_BLOCKING_FINDING:SPEC-001`로 종료했고 공통 원인은 "변경이 깨뜨리는 기존 테스트의 불완전 열거"였다.

## Review history

| 산출물 | 라운드 | 점수 | verdict | blocker | 비고 |
|---|---|---|---|---|---|
| Spec | 1 | 81 | REVISE | 1 | SPEC-001(High: 정본 경로가 실제 운영 명령과 미연결), SPEC-002·003(Medium), SPEC-004·005(Low). 리뷰어가 네 축 열거 완전성을 독립 확인 |
| Spec | 2 | **91** | **PASS** | 0 | SPEC-001~005 resolved. 비차단 SPEC-006·007(Medium), SPEC-008(Low). 최초 PASS는 미검증 evidence 포함으로 validator가 반려했고 규정된 1회 재시도로 확정 |
| Plan | 1 | 71 | REVISE | 4 | PLAN-001~004(High), PLAN-005·006(Medium), PLAN-007·008(Low) |
| Plan | 2 | 80 | REVISE | 2 | PLAN-001·002·003·005·006·007·008 resolved. **PLAN-004 동일 ID 재발(High)**, **PLAN-010 신규(High)**, PLAN-011(Low). Plan 라운드 한도 소진 |

advisory readiness(Codex Sol): Spec 라운드 1·2 모두 `READY` 100, C1~C8 pass. readiness는 상태 전이를 결정하지 않는다.

결정적 검사: `revision_check.py --artifact spec` 라운드 2 exit 0, `--artifact plan` 라운드 2 exit 0(빈 칸 0, 누락 note 행 0). 오케스트레이터가 Spec AC 27개의 판정 토큰을 Plan 추적표와 전수 대조해 누락 0.

리뷰어 운영 사고: Spec 라운드 1은 24턴 한도에서 보고 없이 멈춰 결과 전달을 요청했다. Spec 라운드 2의 첫 PASS는 오케스트레이터의 예산 지시("못 끝낸 검사는 `verified: false`")가 "PASS에 미검증 evidence 금지" 규칙과 충돌해 `REVIEW_OUTPUT_INVALID` 재시도 1회를 소비했다. 원인은 지시문이었다.

## Blocking-finding resolutions

| Finding | 심각도 | 해소 | 검증 |
|---|---|---|---|
| SPEC-001 | High | 재현이 쓴 `--verifier`가 저장소 소스 경로였음을 `repro.sh:5`로 기록하고 정본·소스 두 경로를 대비 측정(`evidence/repro-canonical-verifier.txt`, 오늘은 둘 다 `blocked_policy`/4), 정본 경로 운영 명령과 비정본 차단을 AC-23·AC-24로 고정 | Spec 라운드 2 resolved |
| PLAN-001 | High | T1 stage A가 production 파일 여섯 전체 변경을 스크래치에 적용 | Plan 라운드 2 resolved |
| PLAN-002 | High | R1.3(1) launch skip을 T5 B가 소유, `test_settings_compat_launch_prescan_gate` 양성 1·음성 6 선작성 | Plan 라운드 2 resolved |
| PLAN-003 | High | `launch --verifier` 선택화·정본 기본 채움·HOME 무효 시 fail closed, `test_settings_compat_launch_default_verifier` 선작성 | Plan 라운드 2 resolved |
| **PLAN-004** | **High** | **미해소(재발)** | 아래 |
| **PLAN-010** | **High** | **미해소(신규)** | 아래 |

### 미해소 blocker

**PLAN-004 — 테스트·helper 편집 경계 검사의 범위 부족(재발).** 라운드 2에서 분류를 stage A/B 실행 기반으로 바꾸고 helper 편집을 두 줄로 한정했지만, `T11`의 `test-edit-boundary-check.py`가 HEAD와 비교하는 대상이 `test_*` method, `OrchestratorProfileFixture` method, `make_fake_executable`뿐이다. 오케스트레이터 확인 결과 검사 밖에 다음이 실재한다: `tests/test_ai_session.py`의 `make_verifier`(`:114`), `strict_claude_status`(`:296`), `strict_claude_launch`(`:312`); `tests/test_orchestrator_profiles.py`의 `prepare_workmux_harness`(`:1630`), `run_official_verifier`(`:2958`), `run_permission_boundary_launch`(`:4150`), `run_cross_profile_move`(`:4369`)와 module-level 정의. 또 재정의 대상 세 method는 통째로 제외되어 수정 지점 1의 project 구간(`:2059-2090`)이나 수정 지점 3의 여섯 실패 케이스가 바뀌어도 검출되지 않는다.

**PLAN-010 — 영구 테스트가 비추적 evidence에 의존(이번 개정이 만든 회귀).** 라운드 2의 `T6` 1단계가 영구 회귀 `test_settings_compat_blast_radius_contract`에 "`T1` evidence의 `classification=` 결과를 읽어" assert하라고 적었다(`plan.md:186`). 그 evidence는 gitignore된 `.claude/quality-state/<task-id>/` 아래에만 있어(`.gitignore:25`) 다른 checkout·머지 후 main에서 `CMD-5`가 실패한다. `G12`가 #126과 같은 유지보수 함정이라며 스스로 피한 구조를 다른 곳에서 만들었다. 라운드 1 스냅샷(`snapshots/plan-r1.md:163`)에는 없던 결함이다.

**종료 규칙**: `references/plan-rubric.md`의 "After round 2 without a passing gate, stop and record `NEEDS_REDESIGN`"과 "same blocking finding ID recurs twice"가 모두 해당한다.

## Plan approval

- Approval timestamp: 해당 없음 — Plan 게이트를 통과하지 못해 `AWAITING_PLAN_APPROVAL`에 도달하지 않았고 사용자 구현 승인을 요청하지 않았다.
- Plan digest: `21708823add8aa47c1339a2fd44a6a6aec4793f1e643673c66365c5d71d8588a` (라운드 2 심사 대상, 미승인)

## Changed files

구현을 시작하지 않았다. 소스·테스트·운영 문서 변경 0건.

| 파일 | 내용 |
|---|---|
| `docs/development/2026-09-17-111-profile-settings-compat-3/spec.md` | strict Spec. 요구사항 10, AC 27, 판정 명령 7. **라운드 2 PASS(91)** |
| `docs/development/2026-09-17-111-profile-settings-compat-3/spec-revision-notes.md` | Spec 라운드 2 개정 note |
| `docs/development/2026-09-17-111-profile-settings-compat-3/plan.md` | Plan. 태스크 11. 라운드 2 REVISE, 미승인 |
| `docs/development/2026-09-17-111-profile-settings-compat-3/plan-revision-notes.md` | Plan 라운드 2 개정 note |
| `docs/development/2026-09-17-111-profile-settings-compat-3/report.md` | 이 보고서 |

`dot_local/**`, `dot_config/**`, `tests/**`, 두 운영 문서는 변경하지 않았다. `tests/fixtures/**` 바이트 불변. `~/.claude`, `~/.local/share/ai-account-profiles/**`, `~/.config/ai-session/**`, `#118` 소유 경로, 앞선 두 실행 산출물 보존.

## Verification evidence

구현이 없어 `CMD-1`~`CMD-7`은 실행하지 않았다. 아래는 이번 실행에서 실제로 실행한 명령이다. Python은 `/opt/homebrew/bin/python3.14`.

| 명령 | exit | 증거 |
|---|---|---|
| `ai-session status` 소스 경로 verifier vs 정본 경로 verifier 대비(읽기 전용, `~/code/profile1/111-account-profile-smoke`) | 4 / 4 | 둘 다 `blocked_policy`. 정본 경로는 regular non-symlink로 실재 — `evidence/repro-canonical-verifier.txt` |
| 테스트 파일 네 축 소스 재감사(`blocked_policy` 단언·settings write·argv 동일성·CLI 계약·문서 계약 → 테스트 함수 매핑) | 0 | `evidence/blast-radius-audit-v2.md` |
| 사용자 인계 실측 복사(한 축 스크래치 측정: 계약 정의만 변경 시 `test_ai_session` Ran 29 OK, `test_orchestrator_profiles` Ran 92 FAILED failures=10, 8 method/10 case) | 0 | `evidence/cli-contract-blast-radius-measured.md` |
| Codex preflight `gpt-5.6-sol` | 0 | 6.0초 |
| `revision_check.py --artifact spec` / `--artifact plan` (라운드 2) | 0 / 0 | `passed: true` |
| Plan 추적표 대 Spec AC 27개 판정 토큰 전수 대조 | 0 | 누락 0 |

선행 실행에서 측정해 유효한 증거(`.claude/quality-state/20260917T002844Z-…-f76eb54a/evidence/`): `baseline-tests.txt`(29 + 92 OK), `repro-baseline.txt`, `probe-argv.txt`, `probe-flags.txt`, `checker-baseline.txt`(설치 계약 checker는 이번 작업 이전부터 exit 1).

type check·lint·build는 `not configured`다(근거: `tests/`에 unittest 스위트와 설치 계약 checker만 있고 저장소 루트에 해당 설정 파일이 없다). E2E·high-risk 검증은 구현 미시작으로 실행하지 않았다.

## Execution watchdog

모든 Codex 실행을 `execution_watchdog.py`로 감쌌고 abort·reap·잔여 프로세스가 없었다.

- Execution ID: `preflight-001`, `spec-author-001`, `readiness-spec-r1`, `spec-author-002`, `spec-author-003`, `readiness-spec-r2`
- PID / PGID: 각 실행이 자기 pid를 pgid로 소유
- Start / end / elapsed: `preflight-001` 6.0s, `spec-author-001` 509.9s, `readiness-spec-r1` 127.6s, `spec-author-002` 621.3s, `spec-author-003` 578.1s, `readiness-spec-r2` 200.7s
- Child exit code: 모두 0
- Result exists / schema validation: `preflight-001` false / `not_run`(result 경로 없음), 나머지 true / `passed`
- Start confirmed / watchdog reason: true / `null`
- Signals / preservation bundle: `[]` / `null`
- Abort: `not_needed`
- Reap: `not_needed`
- Residual PIDs: `[]`

## Watchdog restart budget

- Initial / remaining: `null` / `null` — 재시작 후보 없음. preflight는 예산을 소비하지 않는다.
- Exactly-once consumption: 0
- Restart attempted / stopped: false / false

## Remaining advisory findings

| ID | 심각도 | 내용 | 후속 |
|---|---|---|---|
| SPEC-006 | Medium | Spec `CMD-7`이 표식만 검사 | Plan `G8`이 원시 전사 기반 내용 판정으로 해소(Plan 라운드 2에서 resolved 판정) |
| SPEC-007 | Medium | 다섯 번째 지점 출현 경로 미명시 | Plan `G9`가 실행 기반 분류와 중단·재승인 규칙으로 해소 |
| SPEC-008 | Low | Problem 절 확신 수준 불일치 | Plan `G10`이 충분성 근거를 단일화 |
| PLAN-011 | Low | `make_fake_executable` codex help를 여섯 토큰에서 세 토큰으로 좁혀 AC-19의 "codex help 불변"과 문언 충돌 | codex 분기는 기존 리터럴을 바이트 그대로 유지하도록 고칠 것 |
| 설치 계약 checker | Medium | `EXPECTED_VERSIONS["claude"]="2.1.272"` 고정으로 설치본 2.1.274에서 사전 실패 | 이슈 `#126` |

## Final status

- Status: `NEEDS_REDESIGN`
- Machine-readable reason: Plan 리뷰 2라운드 한도 소진 및 blocker `PLAN-004` 재발. `record_review`가 `RECURRING_BLOCKING_FINDING:PLAN-004` 또는 `REVIEW_LIMIT_EXHAUSTED:plan`으로 전이한다.

### 이번 실행이 남긴 재사용 가능한 자산

- **통과한 Spec**: `spec.md` digest `a8ac9618082c917a470224f125e4e2de4ba6b4cec15130c0f2050331f59ef2e5`, 라운드 2 PASS 91. 세 실행 중 처음으로 Spec 게이트를 넘었고 blocker가 모두 Plan 수준이다.
- **Plan 라운드 2**: 라운드 1의 8건 중 7건과 Spec 권고 3건을 해소한 상태이며 남은 결함 두 건은 좁고 해소 방법이 구체적이다.
- **측정 증거**: 정본/소스 verifier 대비, 네 축 감사, 한 축 스크래치 실측.

### 남은 결함의 구체적 해소 방법(리뷰어 required_resolution 요약)

1. **PLAN-004**: `test-edit-boundary-check.py`가 두 테스트 파일의 HEAD `56d65ca` **모든 module-level 문과 모든 함수·method 노드**를 현재와 source 동일성으로 비교한다. 예외는 재정의 세 method와 `make_fake_executable`뿐이며 새 노드는 `test_settings_compat_*` 접두만 허용한다. 재정의 세 method는 `G12` 범위(지점 1 `:2124-2178`, 지점 2 `:3014`, 지점 3 `:5130-5132`·`:5191-5210`) **안의 줄 diff만** 허용하고 project 구간 `:2059-2090`과 theme-dark 대조군 `:2144`를 포함한 범위 밖 변경은 실패시킨다.
2. **PLAN-010**: `test_settings_compat_blast_radius_contract`는 `.claude/quality-state`를 읽지 않는다. `restored_by_helper`·`expectation_changed` method 집합을 테스트 안 **리터럴**로 두고, 그 리터럴이 T1 측정 `classification=`과 같은지는 일회성 `three-axis-content-check.py`가 판정한다.
3. **PLAN-011**(선택): codex help 리터럴을 바이트 그대로 유지한다.

### 사용자 수동 게이트 (자동 실행하지 않음)

- **profile2 identity enrollment**: `enrollment_required`/3은 설계된 정상 상태이며 사용자 전경 절차다. 자동 실행하지 않았다.
- **PR #124**: draft 유지. 머지·`chezmoi apply` 미수행. 잔여 blocker가 있어 금지 조건 유효.
