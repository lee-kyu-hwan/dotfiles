# Quality Goal Specification

- Task ID: 20260910-85-watchdog-bounded-redesign
- Mode: standard
- Status: Draft — round 3
- Created: 2026-09-10
- Updated: 2026-09-11
- Source goal: #85 실행 감시 제한 재설계: 테스트 격리·결정적 시간 검증·preflight 입력 계약 보완.

## Problem and context

스냅샷 `e3df177`의 실행 감시 구현은 #85의 결과 우선 폴링·소유 프로세스 신호·보존 계약을 도입했지만, 최종 코드 검토에서 다섯 제한된 후속 결함이 남았다. `CODE-018`은 fixture 상태를 고정 `/private/tmp/.claude/quality-state`에 두어 테스트 자체가 금지한 경로와 동시 실행 간 간섭을 만들었다. `CODE-019`는 argv 프롬프트인 preflight에도 stdin 파일을 요구해 빈 경로가 디렉터리 열기 예외로 이어진다. `CODE-005`, `CODE-008`, `CODE-012`는 각각 결과-중단 경합, stalled preflight 종료 기록, 시간 상한 검증이 결정적으로 증명되지 않은 문제다.

이 작업은 위 다섯 finding만 해소한다. 이전 PASS Spec·Plan 및 이전 state/report는 변경하지 않으며, 신호 알고리즘이나 #85의 운영 값·모델 라우팅 정책을 다시 설계하지 않는다. 초기 dirty 경로는 없었고, 이 명세 작성자는 기존의 안전하지 않은 실행 감시 테스트를 실행하지 않는다.

## Goals

- 각 테스트 suite가 실제 저장소의 무시된 상태 루트 아래에서만 자기 fixture를 만들고, 동시 suite와 서로 정리·잔류 검사를 간섭하지 않게 한다.
- start·stall·hard timeout·결과 경합·first-poll 경로를 주입 단조 시계와 동기화로 결정적으로 검증한다.
- preflight의 argv 입력 계약과 명시적 stdin 파일 입력의 거부 계약을 분리하고, 종료 기록을 빠짐없이 검증한다.

## Non-goals

- `CODE-018`, `CODE-019`, `CODE-005`, `CODE-008`, `CODE-012` 밖의 finding 및 #85의 기능 확장은 범위 밖이다.
- `execution_watchdog.py`의 프로세스 소유권 판단, SIGTERM/SIGKILL 순서, grace/cap, 보존 또는 reap 알고리즘은 바꾸지 않는다. production 변경은 stdin 입력 검증으로 한정한다.
- 기존 PASS 산출물(`docs/development/2026-09-09-quality-goal-execution-watchdog/`), 기존 state/report, 보호된 SKILL 절, 기존 `def test_*` 이름, 버전은 변경 대상이 아니다.
- 고정 `/tmp` 경로, skill source tree, 새 임시 전역 루트, 무단 모델 대체, Git commit/push는 사용하지 않는다.

## Requirements

- **R1.1** `test_execution_watchdog.py`를 import하는 각 unittest module process는 import 시 한 번 새 UUID를 생성하고, 실제 repository root의 `.claude/quality-state/watchdog-test-<uuid>/`를 그 process만의 suite root로 소유한다. 각 fixture는 그 아래 `.claude/quality-state/watchdog-test-<uuid>/<execution-uuid>/`에만 생성한다. `watchdog-test-` prefix는 live task state와 test state를 구조적으로 구분하며, skill tree와 `/tmp`는 fixture·prompt·result·events·stderr·record·preservation의 어떤 상위 경로도 될 수 없다.
- **R1.2** cleanup과 residue 검사는 현재 process가 생성해 기억한 exact suite root 하나만 제거하고 그 exact path의 부재만 확인한다. `watchdog-test-*` glob으로 다른 suite를 탐색·삭제하지 않는다. 각 보존 fixture의 disposable Git checkout은 자기 execution directory 안에 만들고, shipped `SKILL.md` 시작 바이트 비교와 disposable fixture의 tracked/untracked 보존 검증은 유지한다. `/tmp` 밖이라는 음성 단언을 복구한다.
- **R2.1** 시간 판정 테스트는 `run_execution`의 주입 `monotonic_clock`과 `sleep`, 그리고 테스트가 제어하는 동기화 지점으로 start deadline, activity stall, hard timeout, first-poll 및 결과-중단 경합의 순서를 결정한다. 정확성 판정에 subsecond 실벽시계 또는 CPython 시작 시간 상한을 쓰지 않는다. 경합 fixture는 watchdog reason이 먼저 설정된 뒤 다음 제어 poll에서 결과가 발견되어 reason이 `None`으로 재설정됨을 검증하고, reset 대입문을 제거한 통제 mutation이 실패함을 증거로 요구한다.
- **R3.1** model-routing의 implementation·author·readiness wrapper 세 개만 prompt file의 `--stdin-path "$PROMPT_PATH"`를 전달한다. preflight wrapper는 argv의 one-line prompt와 stdout/stderr만 전달하고 `--stdin-path`를 갖지 않는다. `SKILL.md`의 기존 Execution watchdog 절과 content contract는 이 3:1 계약을 문서화·검증한다.
- **R3.2** 명시적으로 제공된 `--stdin-path`가 빈 문자열·없는 경로·디렉터리이면 wrapper는 child `Popen` 전에 원인을 포함한 명확한 `stdin-path` 오류를 stderr에 내고 종료 코드 2로 끝낸다. stdin path를 생략한 argv-prompt preflight는 유효하다. production code 변경은 이 pre-launch stdin validation에만 한정한다.
- **R3.3** stalled preflight는 기존 실제 프로세스 신호 순서를 유지하면서 `record.preflight_termination`에 `attempted`, `signals`, `outcome`을 남긴다. residual PID는 새 nested field를 만들지 않고 기존 top-level `record.residual_pids`와 `record.report_payload.residual_pids`에 동일하게 남기며, `preflight_termination` 자체도 top-level `record.report_payload.preflight_termination`에 복사한다.
- **R4.1** 구현 변경 가능 파일은 `scripts/execution_watchdog.py`, `tests/test_execution_watchdog.py`, `tests/test_content_contracts.py`, `references/model-routing.md`, `SKILL.md`의 기존 Execution watchdog 절뿐이다. 보호 절과 기존 테스트 이름은 보존하고, 실제 signal-order 테스트는 실제 프로세스 행동을 계속 검증한다.
- **R5.1** 검증 프로세스 요구사항: 구현 뒤 orchestrator는 pinned `/opt/homebrew/bin/python3.12`로 version guard, targeted·full unittest, 보존·scope·watchdog-name 검사, 동시 suite 및 task state root 내부 controlled mutation을 실행한다. 마지막 transport 증거는 사용자 override에 따른 Codex `gpt-5.6-sol`/low 실제 preflight wrapper smoke이며, documented argv prompt와 named stdout events·stderr·execution record만 사용하고 reply file이나 result schema를 사용하지 않는다. Claude reviewer route는 Opus로 유지한다. 이 검증 거버넌스는 production 동작이나 파일 범위를 넓히지 않는다.

## Acceptance criteria

- **AC-1** focused barrier test가 서로 다른 두 module-import process를 ready/release 지점에서 겹쳐 둔 동안 각각 `.claude/quality-state/watchdog-test-<서로 다른 uuid>/<execution-uuid>`만 사용한다. A teardown 뒤 A의 exact root는 없고 B의 root와 marker는 남으며, B teardown 뒤 B의 exact root도 없어야 한다. 이어 두 full watchdog module을 동시에 background 실행해 두 status가 모두 0임을 확인한다. [실행] (`CMD-3`)
- **AC-2** `test_execution_artifacts_use_unique_state_directory_not_tmp`는 prompt, result, events, stderr, execution record 및 preservation bundle의 생성 경로가 자신의 execution directory 하위이고 repository state root 하위이며 `/tmp` 하위가 아님을 확인한다. [실행] (`CMD-1`)
- **AC-3** 보존 fixture는 execution directory 내부의 disposable Git checkout에서 tracked/untracked 증거를 검증하고, suite 종료 뒤 자기 suite 트리만 잔류 없이 제거하며 shipped `SKILL.md` 바이트가 suite 시작 시점과 동일함을 확인한다. [실행] (`CMD-1`)
- **AC-4** start deadline, activity stall, hard timeout과 first-poll 결과/terminal 경로의 테스트는 주입 단조 시계와 sleep으로 기대 reason·결과를 판정하며, correctness assertion에 `time.monotonic()` 실측 경과 또는 1초 미만 같은 wall-clock 상한이 없다. [실행] (`CMD-1`)
- **AC-5** 결과-중단 경합 테스트는 reason이 먼저 설정된 사실과 결과 발견 뒤 `watchdog_reason is None`, abort 미시도를 `RACE_RESET_ASSERTION` 식별자로 확인한다. e3df177 disposable checkout 두 개에 live worktree의 허용된 다섯 구현 파일만 overlay한 positive baseline은 통과하고, result-first branch의 정확한 `record["watchdog_reason"] = None` 한 줄만 제거한 copy는 import·collection·setup 오류 없이 그 식별자의 assertion failure로 실패하며, 그 줄을 복원한 control은 다시 통과한다. [실행] (`CMD-2`)
- **AC-6** stalled preflight fixture는 실제 프로세스에 대한 신호 순서를 보존하면서 `record.preflight_termination.attempted`, `signals`, `outcome`, top-level `record.residual_pids`, 그리고 `record.report_payload.preflight_termination`·`record.report_payload.residual_pids`의 복사를 모두 단언한다. 새 nested residual field는 요구하지 않는다. [실행] (`CMD-1`)
- **AC-7** content contract는 wrapper 네 개 중 implementation·author·readiness 세 블록에만 `--stdin-path "$PROMPT_PATH"`가 있고 preflight 블록에는 없음을 확인한다. focused CLI test와 실제 Sol/low smoke 모두 one-line argv prompt와 named stdout events·stderr·execution record만으로, reply file과 result schema 없이 성공한다. [실행] (`CMD-1`, `CMD-4`, `CMD-11`)
- **AC-8** CLI 테스트는 명시적 empty, missing, directory stdin path마다 child marker가 생성되지 않고 exit 2 및 `stdin-path`을 포함한 명확한 stderr를 확인하며, stdin path 생략 preflight는 거부되지 않음을 확인한다. [실행] (`CMD-1`)
- **AC-9** e3df177 이후 변경·untracked 경로가 다섯 구현 파일 또는 이 task의 새 docs directory에만 속하고 이전 승인 docs는 불변이다. 두 기존 guard가 9ff32a30c9498df007ec5dfa558a442cc7841be1에 대해 통과하며, 별도 AST name-set guard가 e3df177의 watchdog `def test_*` 이름을 모두 보존하고, 명시한 실제 signal-order tests와 full suite가 모두 통과한다. 첨부된 `spec-r3-base-evidence.json`은 e3df177이 현재 branch에 포함되고 해당 watchdog test file의 `git show`가 성공함을 증명한다. [실행] (`CMD-5`, `CMD-6`, `CMD-7`, `CMD-9`, `CMD-10`)
- **AC-10** orchestrator가 모든 Python 판정을 `/opt/homebrew/bin/python3.12`와 `PYTHONDONTWRITEBYTECODE=1`로 실행하고 version guard를 먼저 통과시킨다. controlled mutation·동시성 증거는 이 task state directory 아래 named paths에만 두며, 마지막 실제 transport 증거인 Sol/low preflight는 reply file이나 result schema 없이 wrapper exit 0, child exit 0, nonempty stdout events 및 completed semantics의 execution record를 남긴다. [실행] (`CMD-1`, `CMD-2`, `CMD-3`, `CMD-4`, `CMD-7`, `CMD-8`, `CMD-11`)

## Requirements traceability

| Requirement | Acceptance criteria | Judgement method |
|---|---|---|
| R1.1 | AC-1, AC-2 | `CMD-1`, `CMD-3` |
| R1.2 | AC-2, AC-3 | `CMD-1` |
| R2.1 | AC-4, AC-5 | `CMD-1`, `CMD-2` |
| R3.1 | AC-7 | `CMD-1`, `CMD-4`, `CMD-11` |
| R3.2 | AC-8 | `CMD-1` |
| R3.3 | AC-6 | `CMD-1` |
| R4.1 | AC-9 | `CMD-5`, `CMD-6`, `CMD-7`, `CMD-9`, `CMD-10` |
| R5.1 | AC-1, AC-5, AC-10 | `CMD-1`, `CMD-2`, `CMD-3`, `CMD-4`, `CMD-7`, `CMD-8`, `CMD-11` |

## Architecture

테스트 격리 경계는 `repository root → .claude/quality-state → watchdog-test-<uuid> → execution UUID`다. 각 OS process가 watchdog test module을 import할 때 UUID를 정확히 한 번 생성하고 exact suite-root path를 보유한다. fixture cleanup은 그 exact path만 재귀 제거하고 residue 검사도 그 path의 부재만 본다. prefix glob은 cleanup이나 성공 판정에 쓰지 않으므로 live task directory, 다른 병렬 suite와 과거 suite 상태는 구조적으로 현재 suite의 삭제·판정 대상이 아니다.

시간 제어는 실제 child 프로세스의 신호·소유권 동작과 분리한다. 테스트 동기화가 child가 준비되었음을 알리고, fake clock의 `sleep`이 다음 poll과 deadline 경과를 전진시킨다. 동시성 focused test는 두 subprocess module import의 ready/release barrier와 marker 존재를 사용한다. barrier/process wait의 real timeout은 hang 방지용 liveness guard일 뿐 성공의 시간 기준이 아니며, 정확성은 두 ready 관찰, A 제거 중 B 생존, 최종 exact-root 제거라는 상태 전이로 판정한다. signal-order 검증은 기존 실제 process fixture를 그대로 두어 결정적 시간 제어가 process-signaling 동작을 mock으로 대체하지 않게 한다.

## Interfaces and data flow

세 prompt-file 호출은 `PROMPT_PATH → --stdin-path → child stdin`을 사용한다. preflight는 `PREFLIGHT_CHILD_ARGV` 안의 argv prompt를 사용하고 stdin-path 옵션을 전달하지 않는다. `stdin_path=None`은 정상 입력이고, CLI에 명시된 비어 있음·부재·directory path는 pre-launch validation 오류다.

`run_execution`은 주입된 `monotonic_clock`과 `sleep`을 모든 test-controlled polling에 사용한다. 경합은 timeout reason 설정 → final result check → reason reset → result-first completion 순서를 관찰한다. stalled preflight의 termination object는 `record.preflight_termination`과 `record.report_payload.preflight_termination`에, residual PID 목록은 각각의 top-level `residual_pids`에 같은 의미로 복사된다.

## Failure behavior

invalid base revision의 기존 fail-fast 계약과 같은 단계에서 invalid explicit stdin path는 child를 시작하지 않고 exit 2로 실패한다. 오류에는 사용자가 고칠 수 있도록 `stdin-path`와 원인(비어 있음, 없음, directory)이 드러난다. preflight에서 stdin 옵션을 생략한 것은 오류가 아니다.

테스트 cleanup 또는 residue 확인 실패는 현재 process가 소유한 exact `watchdog-test-<uuid>` path의 미정리 상태만 보고한다. 다른 suite나 live task directory를 glob으로 찾거나 지우지 않고, 그 존재만으로 실패하지 않는다. mutation copy가 기대와 달리 통과하거나, 지정한 race failure가 아닌 import·collection·setup 오류로 실패하거나, Sol/gpt-5.6-sol preflight smoke가 실패하면 orchestrator는 성공을 주장하지 않고 해당 증거를 실패로 기록한다.

## Security and risk

상태·보존 번들은 untracked 파일 내용을 포함할 수 있으므로 world-writable `/tmp`나 skill tree가 아닌 repository가 무시하는 state root 아래의 execution directory에만 둔다. test suite는 `watchdog-test-` namespace와 무작위 UUID를 함께 쓰고, cleanup target은 생성 시 저장한 exact path로 제한해 live task와 병렬 suite의 데이터를 삭제하지 않는다. mutation checkout도 이 task의 state directory 아래 unique harness root에만 생성하고 fixed tmp나 cleanup glob을 사용하지 않는다.

production 변경은 stdin path validation뿐이다. 신호 대상·순서·ownership을 바꾸지 않고, 기존 실제 signal-order tests를 유지해 이 제한을 회귀 검증한다. 실제 Codex smoke에는 Sol/gpt-5.6-sol만 쓰고 prompt/result은 해당 task state root에만 둔다.

## Test strategy

아래 명령은 구현 후 orchestrator가 실행할 CODE gate다. 이 Spec 단계의 의무는 proposed focused tests와 명령이 future implementation bug를 실제로 falsify할 수 있도록 입력·동기화·observable·negative control을 완전하게 설계하는 것이다. 실제 동시 full-suite 성공과 실제 Sol 응답은 구현 뒤에만 성립할 CODE 증거이며, pre-implementation SPEC 실행 누락으로 보지 않는다. 이 명세 작성 단계에서는 기존 watchdog suite나 unsafe test를 실행하지 않는다.

모든 Python 명령은 system `python3` 3.9.6이 아니라 version guard를 통과한 `/opt/homebrew/bin/python3.12` 3.12.14를 절대 경로로 사용한다. watchdog test module에는 `unittest.main()`이 없으므로 직접 파일 invocation은 금지하고, 반드시 skill directory로 이동한 뒤 `-m unittest tests.test_execution_watchdog...` 형태로 실행한다. test 내부 real timeout은 barrier/process hang을 끊는 liveness guard일 뿐 elapsed-time correctness criterion이 아니다.

### 판정 명령 표

| ID | 명령 | 통과 조건 |
|---|---|---|
| CMD-1 | `cd <w>/dot_claude/skills/quality-goal && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.12 -m unittest tests.test_execution_watchdog.WatchdogProcessTestCase.test_execution_artifacts_use_unique_state_directory_not_tmp tests.test_execution_watchdog.WatchdogAbortAndReapTestCase.test_abort_preserves_diff_events_stderr_and_fingerprint_before_sigterm tests.test_execution_watchdog.WatchdogProcessTestCase.test_start_deadline_records_no_output_reason tests.test_execution_watchdog.WatchdogProcessTestCase.test_missing_streams_trigger_stall_and_hard_timeout_reasons tests.test_execution_watchdog.WatchdogProcessTestCase.test_first_poll_result_and_terminal_paths_return_within_bounds tests.test_execution_watchdog.WatchdogProcessTestCase.test_start_deadline_records_preflight_termination_payload tests.test_execution_watchdog.WatchdogProcessTestCase.test_cli_rejects_invalid_explicit_stdin_paths tests.test_execution_watchdog.WatchdogProcessTestCase.test_preflight_cli_argv_prompt_without_stdin_path` | 실제로 여덟 test가 실행되고 주입 clock·격리·preservation·preflight record·stdin 계약을 통과한다. zero-test exit 0과 loader error는 통과가 아니다. |
| CMD-2 | 아래 `CMD-2` inline harness | task state 아래 두 e3df177 disposable checkout에 live 다섯 파일만 overlay한다. positive baseline 통과, exact result-first reset 한 줄 제거 뒤 `RACE_RESET_ASSERTION` failure, import/collection/setup error 부재, exact line 복원 뒤 재통과가 모두 성립한다. |
| CMD-3 | 아래 `CMD-3` inline harness | focused test가 ready/release barrier로 두 module-import fixture lifetime의 실제 overlap과 A 제거 중 B exact root·marker 생존을 관찰한다. 이어 두 full watchdog module process를 background로 띄우고 둘을 await해 두 status 0을 확인한다. |
| CMD-4 | `cd <w>/dot_claude/skills/quality-goal && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.12 -m unittest tests.test_content_contracts` | 3:1 stdin wrapper와 Execution watchdog 문서 계약을 포함한 content tests가 실제로 실행·통과한다. |
| CMD-5 | `cd <w> && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.12 dot_claude/skills/quality-goal/tests/assert_preserved_sections.py 9ff32a30c9498df007ec5dfa558a442cc7841be1` | 보호된 여덟 `SKILL.md` 절이 바이트 동일하다. repository evidence에서 base resolution과 기존 guard 통과가 이미 확인되었으며 CODE gate에서도 재실행한다. |
| CMD-6 | `cd <w> && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.12 dot_claude/skills/quality-goal/tests/assert_tests_preserved.py 9ff32a30c9498df007ec5dfa558a442cc7841be1` | 기존 checker가 담당하는 다른 네 test module의 기준 `def test_*` 이름이 모두 남는다. repository evidence에서 기존 guard 통과가 이미 확인되었으며 CODE gate에서도 재실행한다. |
| CMD-7 | `cd <w>/dot_claude/skills/quality-goal && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.12 -m unittest tests.test_execution_watchdog.WatchdogAbortAndReapTestCase.test_abort_kills_owned_child_but_not_same_command_decoy tests.test_execution_watchdog.WatchdogAbortAndReapTestCase.test_sigterm_ignoring_abort_uses_abort_grace_then_sigkill tests.test_execution_watchdog.WatchdogAbortAndReapTestCase.test_reap_kills_owned_residual_child_but_not_same_command_decoy tests.test_execution_watchdog.WatchdogAbortAndReapTestCase.test_reap_sends_sigterm_before_sigkill tests.test_execution_watchdog.WatchdogAbortAndReapTestCase.test_reap_escalates_to_sigkill_and_records_outcome && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.12 -m unittest discover -s tests -p 'test_*.py'` | 명시한 다섯 actual-process signal ownership/order/escalation tests와 전체 suite가 loader error 없이 모두 실제 실행·통과한다. |
| CMD-8 | `cd <w> && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.12 dot_claude/skills/quality-goal/tests/assert_python_version.py` | pinned interpreter가 repository의 Python >=3.12 guard를 통과한다. 이 명령이 다른 Python 판정보다 먼저 실행된다. |
| CMD-9 | 아래 `CMD-9` inline harness | e3df177 이후 tracked 변경과 현재 untracked 경로의 합집합이 정확한 다섯 구현 path 또는 이 task의 새 docs directory에만 속한다. 이전 승인 docs를 포함한 다른 path가 하나라도 있으면 실패한다. |
| CMD-10 | 아래 `CMD-10` inline harness | AST로 e3df177과 live watchdog module의 모든 `def test_*` name set을 비교해 base name 누락이 0임을 증명한다. 기존 generic checker가 담당하지 않는 watchdog module 전용 guard다. |
| CMD-11 | 아래 `CMD-11` inline harness | 실제 `gpt-5.6-sol`/low child를 stdin redirection, `--stdin-path`, `--output-last-message`, `--output-schema` 없이 documented one-line argv prompt로 실행한다. wrapper exit 0, child exit 0, named stdout events nonempty, named stderr와 execution record 생성, record의 completed semantics를 모두 확인한다. |

`CMD-2`의 기존 경합 test는 mutation failure를 안정적으로 식별하도록 assertion message에 `RACE_RESET_ASSERTION`을 포함한다. `test_execution_watchdog.py`에는 기존 테스트를 개명하지 않고 `test_start_deadline_records_preflight_termination_payload`, `test_cli_rejects_invalid_explicit_stdin_paths`, `test_preflight_cli_argv_prompt_without_stdin_path`, `test_concurrent_module_runs_isolate_suite_roots_during_overlapping_lifetimes`를 추가한다. 마지막 test가 띄운 두 controlled import subprocess는 각 exact suite-root path와 marker를 ready channel로 알리고 release barrier에서 대기한다. parent는 두 ready를 받은 뒤 A만 release해 A path 부재와 B path/marker 존재를 동시에 단언하고, B를 release한 뒤 B path 부재를 단언한다. subprocess wait timeout은 hang protection일 뿐 이 상태 assertion을 대체하지 않는다.

`test_content_contracts.py`는 wrapper별 stdin 옵션 수와 preflight 부재를 구조적으로 단언한다. concurrent test와 module teardown은 외부 `/tmp`를 만들거나 관찰하지 않고 자신이 생성해 저장한 exact root만 조사·정리한다. `CMD-3`의 동시 full-module 실행은 focused overlap proof를 대체하지 않는 supplementary regression check다.

클래스 정의를 읽기 전용으로 확인한 결과 보존 test 하나와 CMD-7의 signal-order test 다섯 개는 모두 `WatchdogAbortAndReapTestCase`에 정의되어 있으므로 CMD-1/CMD-7은 그 실제 정의 class를 사용한다. 이 Spec 개정에서는 해당 unsafe watchdog tests를 실행하지 않는다. 또한 첨부 evidence `.claude/quality-state/20260910-85-watchdog-bounded-redesign/spec-r3-base-evidence.json`은 `git cat-file -e e3df177…` 성공, 현재 `85-feat/quality-goal-execution-watchdog` branch의 포함, `git show e3df177…:dot_claude/skills/quality-goal/tests/test_execution_watchdog.py` 성공을 기록하므로 CMD-2/CMD-9/CMD-10/CMD-11의 base revision 전제는 충족된다.

`CMD-2` inline harness:

```bash
bash <<'BASH'
set -euo pipefail
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
BASE_REVISION=e3df177db1b0c37fc9a00cf9301d029a99e8e515
TASK_STATE_DIR="$PROJECT_ROOT/.claude/quality-state/20260910-85-watchdog-bounded-redesign"
HARNESS_ID="$(/opt/homebrew/bin/python3.12 -c 'import uuid; print(uuid.uuid4().hex)')"
HARNESS_ROOT="$TASK_STATE_DIR/cmd-2-mutation-$HARNESS_ID"
CONTROL_CHECKOUT="$HARNESS_ROOT/control"
MUTATION_CHECKOUT="$HARNESS_ROOT/mutation"
OVERLAY_FILES=(
  dot_claude/skills/quality-goal/scripts/execution_watchdog.py
  dot_claude/skills/quality-goal/tests/test_execution_watchdog.py
  dot_claude/skills/quality-goal/tests/test_content_contracts.py
  dot_claude/skills/quality-goal/references/model-routing.md
  dot_claude/skills/quality-goal/SKILL.md
)
mkdir -p "$HARNESS_ROOT"
for checkout in "$CONTROL_CHECKOUT" "$MUTATION_CHECKOUT"; do
  git clone --quiet --no-hardlinks "$PROJECT_ROOT" "$checkout"
  git -C "$checkout" checkout --quiet --detach "$BASE_REVISION"
  for relative in "${OVERLAY_FILES[@]}"; do
    cp "$PROJECT_ROOT/$relative" "$checkout/$relative"
  done
done
MUTATION_SCRIPT="$MUTATION_CHECKOUT/dot_claude/skills/quality-goal/scripts/execution_watchdog.py"
/opt/homebrew/bin/python3.12 - "$MUTATION_SCRIPT" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text(encoding="utf-8")
needle = (
    "            # A result found at the final abort recheck wins over a stale timer.\n"
    "            record[\"watchdog_reason\"] = None\n"
    "            record[\"result_exists\"] = True\n"
)
replacement = (
    "            # A result found at the final abort recheck wins over a stale timer.\n"
    "            record[\"result_exists\"] = True\n"
)
if source.count(needle) != 1:
    raise SystemExit("expected exactly one contextual result-first watchdog reset")
path.write_text(source.replace(needle, replacement, 1), encoding="utf-8")
PY
run_race_test() {
  local checkout="$1"
  local label="$2"
  (
    cd "$checkout/dot_claude/skills/quality-goal"
    PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.12 -m unittest \
      tests.test_execution_watchdog.WatchdogProcessTestCase.test_result_created_before_final_abort_recheck_wins
  ) >"$HARNESS_ROOT/$label.stdout" 2>"$HARNESS_ROOT/$label.stderr"
}
set +e
run_race_test "$CONTROL_CHECKOUT" baseline
BASELINE_STATUS=$?
run_race_test "$MUTATION_CHECKOUT" mutation
MUTATION_STATUS=$?
set -e
test "$BASELINE_STATUS" -eq 0
test "$MUTATION_STATUS" -ne 0
grep -F 'Ran 1 test' "$HARNESS_ROOT/baseline.stderr"
grep -F 'Ran 1 test' "$HARNESS_ROOT/mutation.stderr"
grep -F 'RACE_RESET_ASSERTION' "$HARNESS_ROOT/mutation.stderr"
grep -F 'FAILED (failures=1)' "$HARNESS_ROOT/mutation.stderr"
if grep -Eq '^(ERROR:|ImportError|ModuleNotFoundError|SyntaxError)|FAILED \(errors=' "$HARNESS_ROOT/mutation.stderr"; then
  exit 1
fi
cp "$PROJECT_ROOT/dot_claude/skills/quality-goal/scripts/execution_watchdog.py" "$MUTATION_SCRIPT"
cmp "$PROJECT_ROOT/dot_claude/skills/quality-goal/scripts/execution_watchdog.py" "$MUTATION_SCRIPT"
run_race_test "$MUTATION_CHECKOUT" restored
grep -F 'Ran 1 test' "$HARNESS_ROOT/restored.stderr"
BASH
```

`CMD-3` inline harness:

```bash
bash <<'BASH'
set -euo pipefail
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
TASK_STATE_DIR="$PROJECT_ROOT/.claude/quality-state/20260910-85-watchdog-bounded-redesign"
RUN_ID="$(/opt/homebrew/bin/python3.12 -c 'import uuid; print(uuid.uuid4().hex)')"
EVIDENCE_DIR="$TASK_STATE_DIR/cmd-3-concurrency-$RUN_ID"
SKILL_DIR="$PROJECT_ROOT/dot_claude/skills/quality-goal"
mkdir -p "$EVIDENCE_DIR"
cd "$SKILL_DIR"
PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.12 -m unittest \
  tests.test_execution_watchdog.WatchdogProcessTestCase.test_concurrent_module_runs_isolate_suite_roots_during_overlapping_lifetimes \
  >"$EVIDENCE_DIR/focused.stdout" 2>"$EVIDENCE_DIR/focused.stderr"
set +e
PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.12 -m unittest tests.test_execution_watchdog \
  >"$EVIDENCE_DIR/module-a.stdout" 2>"$EVIDENCE_DIR/module-a.stderr" &
MODULE_A_PID=$!
PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.12 -m unittest tests.test_execution_watchdog \
  >"$EVIDENCE_DIR/module-b.stdout" 2>"$EVIDENCE_DIR/module-b.stderr" &
MODULE_B_PID=$!
wait "$MODULE_A_PID"
MODULE_A_STATUS=$?
wait "$MODULE_B_PID"
MODULE_B_STATUS=$?
set -e
printf 'module-a=%s\nmodule-b=%s\n' "$MODULE_A_STATUS" "$MODULE_B_STATUS" >"$EVIDENCE_DIR/statuses.txt"
test "$MODULE_A_STATUS" -eq 0
test "$MODULE_B_STATUS" -eq 0
BASH
```

`CMD-9` inline harness:

```bash
bash <<'BASH'
set -euo pipefail
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
BASE_REVISION=e3df177db1b0c37fc9a00cf9301d029a99e8e515
EVIDENCE_PATH="$PROJECT_ROOT/.claude/quality-state/20260910-85-watchdog-bounded-redesign/cmd-9-changed-files.txt"
mkdir -p "$(dirname "$EVIDENCE_PATH")"
cd "$PROJECT_ROOT"
{
  git diff --name-only -z "$BASE_REVISION" --
  git ls-files --others --exclude-standard -z
} | /opt/homebrew/bin/python3.12 -c '
import pathlib, sys
evidence = pathlib.Path(sys.argv[1])
paths = sorted(set(filter(None, sys.stdin.buffer.read().decode("utf-8").split("\0"))))
allowed_files = {
    "dot_claude/skills/quality-goal/scripts/execution_watchdog.py",
    "dot_claude/skills/quality-goal/tests/test_execution_watchdog.py",
    "dot_claude/skills/quality-goal/tests/test_content_contracts.py",
    "dot_claude/skills/quality-goal/references/model-routing.md",
    "dot_claude/skills/quality-goal/SKILL.md",
}
docs_prefix = "docs/development/2026-09-10-85-watchdog-bounded-redesign/"
unexpected = [p for p in paths if p not in allowed_files and not p.startswith(docs_prefix)]
evidence.write_text("\n".join(paths) + ("\n" if paths else ""), encoding="utf-8")
if unexpected:
    raise SystemExit("unexpected paths since e3df177: " + ", ".join(unexpected))
' "$EVIDENCE_PATH"
BASH
```

`CMD-10` inline harness:

```bash
bash <<'BASH'
set -euo pipefail
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
BASE_REVISION=e3df177db1b0c37fc9a00cf9301d029a99e8e515
WATCHDOG_TEST=dot_claude/skills/quality-goal/tests/test_execution_watchdog.py
EVIDENCE_DIR="$PROJECT_ROOT/.claude/quality-state/20260910-85-watchdog-bounded-redesign"
BASE_SOURCE="$EVIDENCE_DIR/cmd-10-base-test_execution_watchdog.py"
REPORT_PATH="$EVIDENCE_DIR/cmd-10-watchdog-test-names.txt"
mkdir -p "$EVIDENCE_DIR"
git -C "$PROJECT_ROOT" show "$BASE_REVISION:$WATCHDOG_TEST" >"$BASE_SOURCE"
/opt/homebrew/bin/python3.12 -c '
import ast, pathlib, sys
def names(path):
    tree = ast.parse(pathlib.Path(path).read_text(encoding="utf-8"))
    return {node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")}
base, live = names(sys.argv[1]), names(sys.argv[2])
missing = sorted(base - live)
pathlib.Path(sys.argv[3]).write_text("base=%d\nlive=%d\nmissing=%s\n" % (len(base), len(live), ",".join(missing)), encoding="utf-8")
if missing:
    raise SystemExit("missing watchdog test names: " + ", ".join(missing))
' "$BASE_SOURCE" "$PROJECT_ROOT/$WATCHDOG_TEST" "$REPORT_PATH"
BASH
```

`CMD-11` inline harness:

```bash
bash <<'BASH'
set -euo pipefail
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
BASE_REVISION=e3df177db1b0c37fc9a00cf9301d029a99e8e515
TASK_STATE_DIR="$PROJECT_ROOT/.claude/quality-state/20260910-85-watchdog-bounded-redesign"
SMOKE_ID="$(/opt/homebrew/bin/python3.12 -c 'import uuid; print(uuid.uuid4().hex)')"
EXECUTION_DIR="$TASK_STATE_DIR/cmd-11-sol-low-$SMOKE_ID"
EVENTS_PATH="$EXECUTION_DIR/preflight.stdout"
STDERR_PATH="$EXECUTION_DIR/preflight.stderr"
WRAPPER_STDOUT_PATH="$EXECUTION_DIR/wrapper.stdout.json"
RECORD_PATH="$EXECUTION_DIR/execution-record.json"
SKILL_DIR="$PROJECT_ROOT/dot_claude/skills/quality-goal"
CODEX_MODEL=gpt-5.6-sol
CODEX_EFFORT=low
PREFLIGHT_PROMPT='Reply with exactly PREFLIGHT_OK. Do not inspect or modify files.'
PREFLIGHT_CHILD_ARGV=(
  codex exec
  -C "$PROJECT_ROOT"
  --sandbox read-only
  --ephemeral
  --model "$CODEX_MODEL"
  -c "model_reasoning_effort=\"$CODEX_EFFORT\""
  "$PREFLIGHT_PROMPT"
)
mkdir -p "$EXECUTION_DIR"
set +e
PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.12 "$SKILL_DIR/scripts/execution_watchdog.py" \
  --project-root "$PROJECT_ROOT" \
  --base-revision "$BASE_REVISION" \
  --execution-dir "$EXECUTION_DIR" \
  --events-path "$EVENTS_PATH" \
  --stderr-path "$STDERR_PATH" \
  -- "${PREFLIGHT_CHILD_ARGV[@]}" \
  >"$WRAPPER_STDOUT_PATH"
WRAPPER_STATUS=$?
set -e
test "$WRAPPER_STATUS" -eq 0
test -s "$EVENTS_PATH"
test -e "$STDERR_PATH"
test -s "$WRAPPER_STDOUT_PATH"
/opt/homebrew/bin/python3.12 -c '
import json, pathlib, sys
record = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert record["child_exit_code"] == 0
assert record["started"] is True
assert record["watchdog_reason"] is None
assert record["result_exists"] is False
assert record["preflight_termination"]["attempted"] is False
assert record["report_payload"]["child_exit_code"] == 0
assert record["report_payload"]["watchdog_reason"] is None
' "$RECORD_PATH"
BASH
```

## Decisions

### D1. 실제 repository state root를 fixture 최상위로 선택

`/tmp`는 빠르게 만들 수 있으나 고정 shared parent와 cross-user/cross-worktree 간섭을 재도입한다. skill tree는 shipped 파일 오염 위험이 있다. repository root의 이미 ignore된 `.claude/quality-state` 아래에 process별 `watchdog-test-<uuid>`를 두면 production 경로 형태를 검증하면서 live task와 구조적으로 구별되고 cleanup 소유권도 명확하다.

### D2. deterministic fake clock과 실제 signal fixture를 병행

실벽시계 짧은 sleep은 interpreter·Git fixture 비용에 따라 불안정하다. fake clock만으로 process signaling까지 대체하지 않고, deadline/race 순서만 제어하며 기존 actual signal-order fixture는 남긴다.

### D3. preflight stdin을 제거하고 explicit stdin만 검증

preflight는 이미 argv에 one-line prompt를 넣으므로 prompt file을 발명하지 않는다. 반면 세 result-path 호출은 prompt file stdin transport가 필요하다. 따라서 optional stdin omission은 정상, 명시된 잘못된 path는 pre-launch exit 2라는 구분이 가장 작고 문서와 실행이 일치한다.
