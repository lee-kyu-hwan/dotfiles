# Quality Goal Report

- Task ID: 20260910-85-watchdog-bounded-redesign
- Mode: standard
- Status: completed
- Created: 2026-09-10T11:23:08Z
- Updated: 2026-09-11T05:05:47Z
- Source goal: #85 실행 감시 제한 재설계: 테스트 격리·결정적 시간 검증·preflight 입력 계약 보완

## Classification

기존 #85의 승인 범위에서 CODE-018, CODE-019, CODE-005, CODE-008, CODE-012만 보완했다. 프로세스 소유권, SIGTERM/SIGKILL, grace/cap, 보존·reap 알고리즘은 유지했고 production 변경은 명시적 stdin 경로의 pre-launch 검증으로 제한했다. 테스트 격리, 결정적 시간 검증, 문서 계약과 실제 모델 smoke가 함께 바뀌므로 standard mode를 유지했다.

## Review history

- Spec round 1: Opus 72, REVISE. High SPEC-001~003과 Medium/Low SPEC-004~009를 식별했다.
- Spec round 2: Opus 83, REVISE. 기존 finding을 해소했으나 실제 class selector 오류인 High SPEC-010과 Medium SPEC-011~012를 식별했다.
- Spec round 3: Opus 92, PASS. Low SPEC-013~015만 남겼다.
- Plan round 1: Opus 83, REVISE. High PLAN-001~002와 Medium/Low PLAN-003~006을 식별했다.
- Plan round 2: 최초 실행은 Claude quota로 review가 생성되지 않았다. 첫 재시도는 내용상 PASS 90이었으나 `PASS reviews must not contain unverified evidence` 검증 오류로 정식 등록하지 않았다. 허용된 동일 라운드 형식 재시도는 Opus 96, PASS였고 Low PLAN-007만 남겼다.
- Code round 1: fingerprint `d7e503b162c0d2bac3eb40c782f86410d363acb26023d7f57b3de05ec4675450`에 대해 Opus 88, PASS. Critical/High blocker는 없고 CODE-101~106 advisory를 남겼다.
- Code round 2: original CMD-11을 invalid/incomplete로 정정한 verification v2와 이 보고서를 포함한 최종 fingerprint를 fresh Opus가 다시 검토한다. 보고서가 round-2 입력이므로 결과는 immutable `review-code-r2.json`과 workflow state에 기록한다.

## Blocking-finding resolutions

- SPEC-001: `test_execution_watchdog.py`에 `unittest.main()`이 없음을 반영해 모든 selector를 `python3.12 -m unittest tests.test_execution_watchdog...`로 교정했다. CMD-1 8개, CMD-7 5개 및 full discovery 458개 실행으로 확인했다.
- SPEC-002: scope, 실제 signal test, full suite를 CMD-7/CMD-9/CMD-13/CMD-14로 분리했다. 최종 범위와 signal test가 모두 통과했다.
- SPEC-003: watchdog test 파일 전용 AST name-set CMD-10을 추가했다. base 37개, live 41개, missing 0으로 확인했다.
- SPEC-010: 실제 정의 class를 반영해 보존 test와 signal-order 5개 selector를 `WatchdogAbortAndReapTestCase`로 교정했다. loader error 없이 각각 실행됐다.
- PLAN-001: 이름을 보존한 기존 content test 본문을 3:1 stdin 계약으로 수정하도록 명시했고 최종 105개 content test와 wrapper mutation으로 확인했다.
- PLAN-002: prompt, result, events, stderr, execution record, preservation bundle 여섯 종류의 repository/execution root 소속과 외부 tmp 부재를 검사하도록 확장했다. CMD-1과 fixed-tmp mutation으로 확인했다.
- 구현 중 독립 mutation이 발견한 preflight report key의 KeyError와 invalid-stdin 3-subtest failure는 실제 Sol/high 수정 두 번으로 각각 단일 `PREFLIGHT_TERMINATION_ASSERTION`, `INVALID_STDIN_ASSERTION` failure가 되도록 고쳤다. 최종 네 추가 mutation 모두 `Ran 1 test`, 지정 식별자, `FAILED (failures=1)`, 복원 positive pass를 충족했다.

## Plan approval

- Approval timestamp: 2026-09-11T04:30:27Z
- Plan digest: ba783a1545c2710521d95fc1516019ae92268c7dec77cc6b21171cf2da450aac

## Changed files

- `dot_claude/skills/quality-goal/scripts/execution_watchdog.py`: empty, missing, directory, non-regular explicit stdin 경로를 Popen 전에 검증하고 exit 2 오류로 매핑한다.
- `dot_claude/skills/quality-goal/tests/test_execution_watchdog.py`: UUID 기반 repository-owned suite root와 exact cleanup, ready/release 동시성 증거, fake monotonic clock, race/preflight/CLI 검증을 추가한다. 기존 test 이름과 실제 signal test는 유지한다.
- `dot_claude/skills/quality-goal/tests/test_content_contracts.py`: wrapper 3:1 stdin 계약과 fixed-tmp source guard를 검증한다.
- `dot_claude/skills/quality-goal/references/model-routing.md`: preflight wrapper의 `--stdin-path`만 제거한다.
- `dot_claude/skills/quality-goal/SKILL.md`: `### Execution watchdog` 절에 prompt-file 세 호출과 argv-only preflight, invalid explicit stdin 계약을 문서화한다.
- `docs/development/2026-09-10-85-watchdog-bounded-redesign/{spec.md,spec-revision-notes.md,plan.md,plan-revision-notes.md,report.md}`: 이번 standard workflow의 immutable 요구사항, 계획, 개정 근거와 종료 증거다.

## Verification evidence

권위 있는 최종 판정은 모두 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.12`로 실행했다.

- CMD-8 Python version guard: exit 0. 다른 최종 Python 판정보다 먼저 실행했다.
- T1 safe source-copy RED: exit 1, `SAFE_ROOT_RED: fixed /private/tmp suite root remains`. unsafe suite를 import하기 전에 기대 실패를 확인했다.
- T1 isolation/preservation focused 2 tests: exit 0. ready/release overlap 1 test: exit 0.
- T2 최초 5-selector support run: exit 1. fake Popen fixture 2건과 과도한 residual 기대 1건을 확인한 뒤 test support만 교정했다. 같은 5 selectors 재실행: exit 0.
- T3 CLI RED: exit 1, 세 `INVALID_STDIN_ASSERTION` subcase 실패와 omitted-stdin pass를 확인했다. content RED: exit 1, preflight stdin 잔존으로 `WRAPPER_STDIN_3_TO_1_ASSERTION` 실패를 확인했다.
- 최종 CMD-1: exit 0, 8 tests, OK.
- 최종 CMD-2: exit 0. control 1 test pass, reset-line mutation은 `RACE_RESET_ASSERTION` 단일 failure, 복원 후 pass.
- CMD-3 구현자 시도 1: exit 1. concurrent 두 module 모두 legacy 80ms child-start liveness failure. 시도 2: exit 1. module A pass, module B의 dead-PID fixture 1건 실패. test-only default start guard를 0.08→0.5초, dead-PID test guard를 2초로 조정하되 해당 test의 `<1s` correctness assertion은 유지했다. 최종 구현자 CMD-3와 독립 최종 CMD-3: 모두 exit 0, focused overlap pass 및 module A/B 각각 64 tests/status 0.
- 최종 CMD-4: exit 0, 105 content tests, OK.
- 최종 CMD-5: exit 0, 보호된 여덟 SKILL 절 불변.
- 최종 CMD-6: exit 0, 기존 checker 대상 test 이름 보존.
- 최종 CMD-7 signal selectors: exit 0, 5 tests, OK. Full discovery: exit 0, 458 tests, OK.
- 최종 CMD-9: exit 0. 다섯 구현 파일과 이번 task docs directory 밖 변경 없음.
- 최종 CMD-10: exit 0. watchdog test name base 37, live 41, missing 0.
- exact fenced CMD-11: **invalid/incomplete evidence**. wrapper와 actual `gpt-5.6-sol`/low child는 exit 0이고 named events 13 bytes(`PREFLIGHT_OK`), stderr, execution record를 남겼지만, outer heredoc의 나머지 shell assertions가 inherited stdin으로 child에 소비되어 실행되지 않았다. 따라서 original CMD-11 assertion harness가 통과했다고 판정하지 않는다. persisted `execution-record.json`과 `preflight.stdout`을 별도로 검사해 completed semantics를 확인했고, tmux terminal stdin에서 byte-identical inner command를 실행한 supplemental smoke와 별도 artifact assertions는 exit 0, `PREFLIGHT_OK`, inherited-stdin notice 없음으로 통과했다.
- 최종 CMD-12: exit 0. 64 watchdog tests를 3회 실행했고 각 test count가 동일하며 모두 OK.
- 최종 CMD-13/CMD-14: exit 0. 상태와 base diff가 허용 범위임을 기록했다.
- 추가 fixed-tmp mutation: exit 1, `FIXED_TMP_ROOT_ASSERTION`, 단일 failure; 복원 positive exit 0.
- 추가 preflight propagation mutation: 최초 독립 실행은 KeyError `FAILED (errors=1)`로 결함을 발견했다. 수정 후 exit 1, `PREFLIGHT_TERMINATION_ASSERTION`, 단일 failure; 복원 positive exit 0.
- 추가 invalid stdin bypass mutation: 최초 독립 실행은 `FAILED (failures=3)`로 exact contract를 못 맞췄다. 수정 후 exit 1, `INVALID_STDIN_ASSERTION`, 단일 failure; empty/missing/directory의 exit·stderr·child marker 검증을 모두 집계하며 복원 positive exit 0.
- 추가 wrapper stdin mutation: exit 1, `WRAPPER_STDIN_3_TO_1_ASSERTION`, 단일 failure; 복원 positive exit 0.
- ResourceWarning 후속 검사: 경고가 지목한 PID 93367, 93981, 94901, 95102, 95313, 96210은 모두 `ps`에서 부재했고 repository `.claude/quality-state/watchdog-test-*` residue도 0이었다. 실제 process/root leak 증거는 없었다.
- 구현 fix2가 처음 실행한 unpinned system Python 3.9 명령은 import 단계에서 실패해 판정에서 제외했다. 이후 version guard와 모든 판정은 pinned Python 3.12로 재실행했다.
- 구현 fix2가 검증 후 owned checkout 하나를 `/private/tmp`로 옮긴 편차가 있었다. orchestrator가 exact path와 내용 소유권을 검증하고 그 경로만 제거했으며, 최종 mutation 네 건을 task state 아래 fresh checkout으로 다시 실행했다.
- type check: not configured. lint: not configured. build: not configured. Repository root와 skill root의 `pyproject.toml`, `setup.cfg`, `tox.ini`, `Makefile`, `package.json` 총 10개 path가 모두 없음을 확인했다.

## Remaining advisory findings

- SPEC-013 Low: CMD-11 smoke prompt literal은 shipped template의 예시 literal과 다르지만 동일한 one-line argv transport를 검증한다.
- SPEC-014 Low: dead-PID test의 `<1s` wall-clock assertion은 AC-4 범위 밖에 남는다. 이번 concurrent liveness 조정 뒤에도 correctness bound로 유지했다.
- SPEC-015 Low: 새 parent-class tests가 subclass discovery에서도 실행되어 full module에서 중복 비용이 있다.
- PLAN-007 Low: CMD-12의 세 test count 동일성은 command가 자동 비교하지 않고 기록된 `Ran 64 tests` 세 줄을 orchestrator가 비교했다.
- CODE-101 Medium: exact fenced CMD-11의 후속 shell assertions가 child stdin으로 소비된 증거 무결성 한계가 있다. 원문은 invalid/incomplete로 분류했고, parent가 승인한 transport-only 조정으로 outer heredoc만 제거한 byte-identical inner command의 모든 원래 assertions를 실제 실행했다. persisted artifact와 supplemental terminal run을 실행 증거로 사용한다. 보고서 조치는 완료됐으며 round-2 reviewer가 최종 판정한다.
- CODE-102 Low: `stdin=None`은 부모 stdin을 상속하므로 scripted heredoc/pipe에서 추가 prompt가 될 수 있다. production 변경 제한 때문에 이번 범위에서는 유지하며 DEVNULL 기본화는 별도 후속 goal 후보로 남긴다.
- CODE-103 Low: artifact test의 prompt/result path는 test가 직접 만들므로 production path regression에 대한 falsifiability가 나머지 네 artifact보다 약하다.
- CODE-104 Low: content test의 네 wrapper count는 hard-coded dict로 인해 tautological이고, block 부재 시 assertion 대신 StopIteration error가 난다.
- CODE-105 Low: Popen ResourceWarning이 남지만 post-run PID/root residue는 없다. 등록 handle의 wait/close는 별도 test hygiene 개선 후보다.
- CODE-106 Low: shared default start deadline 0.5초가 default hard timeout 0.25초보다 커져 default fixture에서 start_deadline branch가 우선하지 않는다. 해당 branch는 fake-clock focused test로 결정적으로 검증하며 이 조정을 보고서에 명시한다.

## Final status

- Status: completed
- Machine-readable reason: null

종료 상태를 round 1 뒤 한 차례 조기에 기록했으나, final verification v2와 fresh code round 2를 요구한 parent steering을 반영해 runtime state를 CODE_REVIEW로 복구했다. 이 복구는 tracked source를 바꾸지 않으며 이전 completed state snapshot을 보존한다.
