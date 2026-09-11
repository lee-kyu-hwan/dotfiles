# Quality Goal Implementation Plan

- Task ID: 20260910-85-watchdog-bounded-redesign
- Mode: standard (approved bounded redesign)
- Status: Draft — round 2
- Created: 2026-09-11
- Updated: 2026-09-11
- Source goal: #85 실행 감시 제한 재설계: 테스트 격리·결정적 시간 검증·preflight 입력 계약 보완.

## Spec link

Approved Spec: [spec.md](./spec.md), SHA-256 `c881680361ded31c9a05266680ac4820a734bebc388c5e7d9607f9fdc6931201`, initial baseline `e3df177db1b0c37fc9a00cf9301d029a99e8e515`.

## Global constraints

- 구현 변경은 `dot_claude/skills/quality-goal/{scripts/execution_watchdog.py,tests/test_execution_watchdog.py,tests/test_content_contracts.py,references/model-routing.md,SKILL.md}`에만 허용한다. `SKILL.md`는 기존 `### Execution watchdog` 절만 수정한다.
- 이전 승인 docs/state/report와 `9ff32a30c9498df007ec5dfa558a442cc7841be1` 기준 보호 절, 기존 `def test_*` 이름은 불변이다. commit/push 및 tracked runtime harness 추가를 금지한다.
- 모든 Python 판정은 먼저 `CMD-8`을 통과한 뒤 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.12`로 실행한다. watchdog 파일에는 `unittest.main()`이 없으므로 skill root에서 module invocation만 사용한다.
- 기존 shipped watchdog tests는 고정 `/tmp` root를 쓰므로 fixture 격리를 먼저 고치기 전 실행하지 않는다. RED는 focused negative assertion 또는 task-state 내부 disposable copy로만 얻는다.
- 정확성은 주입 fake monotonic clock/sleep과 marker handshake로 판정한다. bounded real timeout은 hang 방지 liveness guard일 뿐 logical-time correctness 근거가 아니다. 기존 actual-process signal-order tests는 유지한다.
- `residual_pids`는 기존 top-level `record`와 `record.report_payload` key다. `preflight_termination`에 새 nested key를 만들지 않고 기존 nested termination과 두 top-level residual copy를 정확히 검사한다.
- reviewer advisory: `CMD-11`은 문서의 literal prompt 일치가 아니라 documented option set 일치를 뜻한다. `--output-last-message`/reply file은 없다. AC-4 밖의 `test_dead_recorded_pid_without_result_records_five_facts_immediately` wall-clock bound는 이번 작업이 제거하거나 전체 timing certification하지 않는다.

## File map

| File | Responsibility and bounded change |
|---|---|
| `scripts/execution_watchdog.py` | 명시된 stdin path의 empty/missing/directory를 `Popen` 전에 stderr `stdin-path` 원인과 exit 2로 거부; 다른 signal/reap/watchdog 동작은 불변 |
| `tests/test_execution_watchdog.py` | process별 suite root와 exact cleanup, fake clock/barrier, race marker, CLI/preflight record tests; 네 새 test는 `WatchdogProcessTestCase`에 두며 subclass 상속으로 full module에서 두 번 실행됨을 수용 |
| `tests/test_content_contracts.py` | 기존 `test_execution_watchdog_wrapper_passes_named_prompt_path` 이름은 보존하고 body를 3:1 stdin 계약으로 치환; fixture-root source contract와 문서 계약 |
| `references/model-routing.md` | 세 prompt-file wrapper는 stdin-path 유지, preflight wrapper에서만 stdin-path 제거 |
| `SKILL.md` | 기존 Execution watchdog 절만 같은 3:1 입력 계약으로 갱신 |

## Task dependencies

`T1 → T2 → T3 → T4 → T5`. T1이 unsafe fixture를 먼저 격리한 뒤에만 shipped module을 실행한다. T2/T3의 corrected assertions가 legacy/live-before-implementation failure를 먼저 보여야 production/docs를 바꿀 수 있다. T4는 positive gate, T5는 immutable/scope/mutation/transport 최종 증거다. 병렬 실행은 `CMD-3` 자체의 검증 외에는 하지 않는다.

## Tasks

### T1. 안전한 test substrate와 격리 RED 구축

대상 AC: AC-1 — CMD-3.
대상 AC: AC-2 — CMD-1.
대상 AC: AC-3 — CMD-1.

1. `test_execution_watchdog.py` import당 UUID 하나와 repository `.claude/quality-state/watchdog-test-<uuid>` exact suite root를 만든다. 각 execution/preservation/disposable checkout은 그 하위이며 `/tmp`와 skill tree를 parent로 쓰지 않는다.
2. cleanup은 기억한 exact suite root만 제거하고 그 exact path 부재만 확인한다. glob 탐색/삭제를 금지하고, 삭제 전 target이 repository state root의 direct `watchdog-test-` child이며 현재 process 소유 path인지 검증한다. 검증 실패 시 삭제하지 않고 test failure로 남겨 arbitrary directory 삭제를 막는다.
3. 기존 `test_execution_artifacts_use_unique_state_directory_not_tmp` body를 확장한다. prompt, result, events, stderr, execution record, preservation bundle 여섯 경로 각각에 대해 `exists()`, execution directory 하위, repository state root 하위를 단언하고, `Path("/tmp")`와 `Path("/private/tmp")` 어느 쪽에도 `is_relative_to`가 아님을 `ARTIFACT_ROOT_ASSERTION:<kind>` 메시지로 명시한다. `CMD-1`은 여섯 kind 모두 이 네 조건을 통과해야 한다. 기존 shipped `SKILL.md` 시작 bytes와 disposable checkout tracked/untracked 보존 단언도 유지한다.
4. unsafe live fixture를 실행하지 않는 선행 RED는 task state copy만 사용한다. 아래 명령은 source copy 외에는 아무것도 만들지 않고 `/tmp`를 읽거나 쓰지 않는다. 현재 source에서 exit 1과 정확한 `SAFE_ROOT_RED: fixed /private/tmp suite root remains`를 기대하며, 다른 오류면 T1 구현을 시작하지 않는다.

```bash
cd <w> && RED_DIR="<w>/.claude/quality-state/20260910-85-watchdog-bounded-redesign/t1-safe-red" && mkdir -p "$RED_DIR" && cp dot_claude/skills/quality-goal/tests/test_execution_watchdog.py "$RED_DIR/test_execution_watchdog.py" && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.12 - "$RED_DIR/test_execution_watchdog.py" <<'PY'
from pathlib import Path
import sys
source = Path(sys.argv[1]).read_text(encoding="utf-8")
assert 'Path("/private/tmp")' not in source and 'Path("/tmp")' not in source, "SAFE_ROOT_RED: fixed /private/tmp suite root remains"
PY
```

5. 그 뒤 import당 `SUITE_UUID`, repository `REPOSITORY_STATE_ROOT`, exact `SUITE_ROOT = REPOSITORY_STATE_ROOT / f"watchdog-test-{SUITE_UUID}"`를 도입한다. cleanup은 이 root만 검증·제거한다. content source test `test_execution_watchdog_fixture_root_is_repository_state`에는 `FIXED_TMP_ROOT_ASSERTION`을 둔다. concurrency selector를 `WatchdogProcessTestCase`에 추가해 ready/release marker로 A cleanup 중 B 생존을 검사한다. 수정 후에만 `CMD-1`의 격리/preservation selectors와 `CMD-3` focused overlap을 실행한다.

### T2. 결정적 시간·경합·종료-record tests를 먼저 RED로 고정

대상 AC: AC-4 — CMD-1.
대상 AC: AC-5 — CMD-2.
대상 AC: AC-6 — CMD-1.

1. start/stall/hard timeout/first-poll test를 주입 `monotonic_clock`·`sleep`로 바꾸고 marker handshake에 bounded real liveness guard를 둔다. reason/result 전이는 logical clock/state로만 단언한다.
2. race test에 reason 선설정, 결과 발견 후 `watchdog_reason is None`, abort 미시도 및 `RACE_RESET_ASSERTION`을 넣는다. stalled preflight는 기존 실제 signal order를 유지하며 `preflight_termination.{attempted,signals,outcome}`, top-level `residual_pids`, `report_payload.preflight_termination`, `report_payload.residual_pids`를 `PREFLIGHT_TERMINATION_ASSERTION` 메시지로 정확히 검사한다.
3. corrected assertions를 먼저 실행하여 legacy copy가 expected assertion failure임을 기록한 뒤 최소 test support를 구현한다. `CMD-2`의 positive/mutation/restored 순서를 그대로 실행한다: e3df177 checkout 두 개에 허용 다섯 파일만 overlay하고 exact reset 한 줄 제거 시 지정 failure, 복원 시 pass여야 한다.
4. AC-4 범위 밖 dead-recorded-pid test의 기존 real-time bound는 그대로 남기고 모든 timing bound 제거를 주장하지 않는다.

### T3. preflight stdin 계약 tests RED 후 최소 구현·문서화

대상 AC: AC-7 — CMD-1 CMD-4.
대상 AC: AC-8 — CMD-1.

1. `WatchdogProcessTestCase`에 stalled termination, invalid explicit stdin, argv-only preflight tests를 추가한다. invalid test는 empty/missing/directory 모두 child marker 없음, exit 2, 원인 포함 `stdin-path` stderr를 `INVALID_STDIN_ASSERTION` 메시지로 요구한다. 또한 기존 `tests/test_content_contracts.py::ExecutionWatchdogContentTests.test_execution_watchdog_wrapper_passes_named_prompt_path`의 이름을 보존한 채 body를 고치는 것을 명시적으로 허용한다: implementation/author/readiness 세 wrapper에는 `--stdin-path "$PROMPT_PATH"`가 있고 preflight wrapper에는 없음을 `WRAPPER_STDIN_3_TO_1_ASSERTION`으로 단언한다.
2. corrected CLI/content tests가 현 구현/문서에서 실패함을 확인한다. 그 뒤 `execution_watchdog.py`에서 option omission(`None`)과 explicit invalid 값을 구분해 child `Popen` 전 검증하고, parser가 명시적 empty도 보존하도록 최소 변경한다.
3. `model-routing.md`의 preflight wrapper에서만 `--stdin-path "$PROMPT_PATH"`를 제거한다. implementation/author/readiness 세 wrapper에는 그대로 둔다. `SKILL.md`는 Execution watchdog 절에서만 이 3:1 계약을 설명한다.
4. `CMD-1`과 `CMD-4`로 GREEN을 확인한다. production 변경은 stdin validation뿐이며 termination/residual record shape는 test-only clarification이다.

### T4. 안전해진 targeted/full/concurrent 회귀 검증

대상 AC: AC-1 — CMD-3.
대상 AC: AC-7 — CMD-1 CMD-4 CMD-7.
대상 AC: AC-9 — CMD-5 CMD-6 CMD-7 CMD-9 CMD-10.
대상 AC: AC-10 — CMD-8 CMD-1 CMD-3 CMD-4 CMD-7 CMD-12.

1. `CMD-8` 후 `CMD-1`, `CMD-4`, `CMD-7` 순서로 실행한다. `CMD-7`의 다섯 selector는 반드시 `WatchdogAbortAndReapTestCase`를 사용하며 full discovery까지 통과해야 한다.
2. `CMD-3`을 실행해 focused overlap과 concurrent full watchdog module 두 process status 0을 모두 확인한다. parent/subprocess wait의 real timeout은 liveness guard로만 기록한다.
3. `CMD-7`의 full discovery 1회와 별도로 `CMD-12`를 실행한다. 각 회차의 실제 test count와 exit 0을 task state에 기록하며 inherited subclass 때문에 네 새 parent tests가 두 번 실행되는 것은 의도된 현 구조다.

### T5. mutation, immutability, scope, 실제 Sol transport 증거

대상 AC: AC-5 — CMD-2.
대상 AC: AC-7 — CMD-11.
대상 AC: AC-9 — CMD-5 CMD-6 CMD-9 CMD-10 CMD-13 CMD-14.
대상 AC: AC-10 — CMD-2 CMD-11.

1. Spec의 `CMD-2` exact inline harness를 task state의 unique disposable checkout에서 실행한다. cleanup은 owned `HARNESS_ROOT`만 대상으로 하고 path ownership 검증 실패 시 그대로 보존·실패 보고한다; arbitrary/glob directory는 삭제하지 않는다.
2. `CMD-5`, `CMD-6`, `CMD-9`, `CMD-10`, `CMD-13`, `CMD-14`를 실행한다. `CMD-13/14` evidence에 허용 목록 밖 변경이 있으면 중단한다.
3. 네 추가 mutation은 각각 task-state의 새 owned checkout에서 수행한다. checkout 생성은 approved Spec lines 118–144의 `CMD-2` clone/detach/five-file overlay를 그대로 재사용하고, case별 `$MUTATION_CHECKOUT`만 사용한다. 아래 exact edit 뒤 exact selector를 실행해 exit nonzero, `Ran 1 test`, 지정 식별자, `FAILED (failures=1)`을 모두 확인하고 import/collection/setup error는 거부한다. 매 case 뒤 해당 파일을 live overlay 원본으로 복원·`cmp`하고 같은 selector가 exit 0인 positive control을 반드시 재실행한다.
   - fixed tmp: owned `tests/test_execution_watchdog.py`의 유일한 `SUITE_ROOT = REPOSITORY_STATE_ROOT / f"watchdog-test-{SUITE_UUID}"`를 `SUITE_ROOT = Path("/private/tmp") / ".claude" / "quality-state" / f"watchdog-test-{SUITE_UUID}"`로 치환한다. `/tmp` 생성·접근 없이 `cd "$MUTATION_CHECKOUT/dot_claude/skills/quality-goal" && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.12 -m unittest tests.test_content_contracts.ExecutionWatchdogContentTests.test_execution_watchdog_fixture_root_is_repository_state`만 실행하며 `FIXED_TMP_ROOT_ASSERTION`을 기대한다.
   - preflight propagation: owned `scripts/execution_watchdog.py`의 report-payload key tuple에서 유일한 `"preflight_termination",` token만 제거한다. `cd "$MUTATION_CHECKOUT/dot_claude/skills/quality-goal" && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.12 -m unittest tests.test_execution_watchdog.WatchdogProcessTestCase.test_start_deadline_records_preflight_termination_payload`를 실행하며 `PREFLIGHT_TERMINATION_ASSERTION`을 기대한다.
   - invalid stdin bypass: owned `scripts/execution_watchdog.py`의 유일한 pre-launch stdin validation guard `if stdin_path is not None:`를 `if False and stdin_path is not None:`로 치환한다. `cd "$MUTATION_CHECKOUT/dot_claude/skills/quality-goal" && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.12 -m unittest tests.test_execution_watchdog.WatchdogProcessTestCase.test_cli_rejects_invalid_explicit_stdin_paths`를 실행하며 `INVALID_STDIN_ASSERTION`을 기대한다.
   - wrapper regression: owned `references/model-routing.md`의 preflight wrapper에서 `--stderr-path "$STDERR_PATH" \\` 바로 뒤에 `--stdin-path "$PROMPT_PATH" \\` 한 줄을 삽입한다. `cd "$MUTATION_CHECKOUT/dot_claude/skills/quality-goal" && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.12 -m unittest tests.test_content_contracts.ExecutionWatchdogContentTests.test_execution_watchdog_wrapper_passes_named_prompt_path`를 실행하며 `WRAPPER_STDIN_3_TO_1_ASSERTION`을 기대한다.
4. 마지막으로 approved Spec lines 289–344의 `CMD-11`을 byte-identical command source로 실행한다. named stdout events에서 nonempty child reply가 존재함을 확인하되 literal echo는 판정하지 않고 completed record semantics를 판정한다. type/lint/build는 `<w>/{pyproject.toml,setup.cfg,tox.ini,Makefile,package.json}`와 `<w>/dot_claude/skills/quality-goal/{pyproject.toml,setup.cfg,tox.ini,Makefile,package.json}`를 확인해 관련 command가 없으면 category별로 “not configured”와 이 checked paths를 기록하며 pass로 쓰지 않는다.

## Verification commands

`CMD-1`–`CMD-11`은 approved Spec `### 판정 명령 표` 및 inline harness가 유일한 명령 원문이다. 구현자는 이를 변경·대체하지 않고 `<w>`만 repository root로 해석한다. `CMD-12`–`CMD-14`는 Plan-only supplementary evidence이며 approved harness를 바꾸지 않는다.

| ID | Exact execution | Expected success |
|---|---|---|
| CMD-8 | `cd <w> && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.12 dot_claude/skills/quality-goal/tests/assert_python_version.py` | 모든 Python 판정보다 먼저 exit 0 |
| CMD-1 | Approved Spec line 100의 exact eight-selector module command | 8 tests, no loader error, exit 0 |
| CMD-2 | Approved Spec lines 118–194의 exact inline harness | baseline pass, mutation `RACE_RESET_ASSERTION` failure only, restored pass |
| CMD-3 | Approved Spec lines 196–227의 exact inline harness | focused barrier pass와 concurrent module A/B status 0 |
| CMD-4 | `cd <w>/dot_claude/skills/quality-goal && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.12 -m unittest tests.test_content_contracts` | 3:1 contract suite exit 0 |
| CMD-5 | `cd <w> && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.12 dot_claude/skills/quality-goal/tests/assert_preserved_sections.py 9ff32a30c9498df007ec5dfa558a442cc7841be1` | protected eight sections unchanged |
| CMD-6 | `cd <w> && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.12 dot_claude/skills/quality-goal/tests/assert_tests_preserved.py 9ff32a30c9498df007ec5dfa558a442cc7841be1` | existing guarded test names preserved |
| CMD-7 | Approved Spec line 106의 exact five `WatchdogAbortAndReapTestCase` selectors followed by exact full discovery | actual signal order/ownership and full suite pass |
| CMD-9 | Approved Spec lines 229–260의 exact inline harness | only five implementation files or task docs since e3df177 |
| CMD-10 | Approved Spec lines 262–287의 exact inline harness | e3df177 watchdog test-name set has no missing name |
| CMD-11 | Approved Spec lines 289–344의 exact Sol/low smoke; Plan에는 중복하지 않음 | wrapper/child exit 0, nonempty child reply/events, completed record |
| CMD-12 | `cd <w>/dot_claude/skills/quality-goal && for run in 1 2 3; do PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.12 -m unittest tests.test_execution_watchdog || exit; done` | 세 회차 모두 동일한 실제 test count, loader error 없음, exit 0 |
| CMD-13 | `cd <w> && git status --short` | 출력 전체를 evidence로 기록하고 구현 다섯 파일과 task docs 밖 새 변경 없음 |
| CMD-14 | `cd <w> && git diff --name-only e3df177db1b0c37fc9a00cf9301d029a99e8e515 --` | tracked path가 구현 다섯 파일 또는 task docs에만 속함 |

## Rollout and rollback

이 변경은 local skill/test contract이며 migration·production rollout은 없다. RED가 지정 assertion이 아닌 import/setup error면 구현을 시작하지 않고 fixture를 고친다. 어떤 gate, mutation positive control, scope/guard 또는 smoke가 실패하면 성공을 주장하지 않으며 dirty evidence를 task state에 보존한다. rollback은 허용된 다섯 파일에서 이번 task diff만 역적용하는 parent-authorized patch로 수행하며 이전 dirty 파일·승인 산출물·state는 건드리지 않는다. Runtime suite cleanup은 생성 시 저장한 exact owned root만 검증 후 제거하고, 검증 불가 path는 삭제하지 않는다.

## Acceptance-criteria traceability

| Criterion | Task | Verification command | Expected outcome |
|---|---|---|---|
| AC-1 | T1 | CMD-3 | two roots overlap safely; both concurrent suites exit 0 |
| AC-1 | T4 | CMD-3 | two roots overlap safely; both concurrent suites exit 0 |
| AC-2 | T1 | CMD-1 | all artifact paths are execution/state-root descendants, never `/tmp` |
| AC-3 | T1 | CMD-1 | disposable preservation holds; exact suite root removed; shipped bytes unchanged |
| AC-4 | T2 | CMD-1 | scoped deadline/first-poll tests use logical clock; no subsecond correctness bound |
| AC-5 | T2 | CMD-2 | positive/mutated/restored sequence isolates `RACE_RESET_ASSERTION` |
| AC-5 | T5 | CMD-2 | positive/mutated/restored sequence isolates `RACE_RESET_ASSERTION` |
| AC-6 | T2 | CMD-1 | exact nested termination and top-level residual copies pass |
| AC-7 | T3 | CMD-1 CMD-4 | 3:1 wrappers pass without reply file |
| AC-7 | T4 | CMD-1 CMD-4 CMD-7 | safe targeted and full regressions preserve the 3:1 wrapper contract |
| AC-7 | T5 | CMD-11 | argv-only real Sol preflight passes without reply file |
| AC-8 | T3 | CMD-1 | three explicit invalid paths fail pre-launch with exit 2; omission is valid |
| AC-9 | T4 | CMD-5 CMD-6 CMD-7 CMD-9 CMD-10 | protected content/names, signal behavior, full suite and exact scope pass |
| AC-9 | T5 | CMD-5 CMD-6 CMD-9 CMD-10 CMD-13 CMD-14 | protected content/names and exact scope/status evidence pass with mutation evidence |
| AC-10 | T4 | CMD-8 CMD-1 CMD-3 CMD-4 CMD-7 CMD-12 | pinned interpreter first; controlled targeted and three-repeat regression evidence passes |
| AC-10 | T5 | CMD-2 CMD-11 | controlled mutation evidence and completed Sol smoke pass |
