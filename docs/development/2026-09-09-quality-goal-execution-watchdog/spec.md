# Quality Goal Specification

- Task ID: 20260909T012111Z-85-quality-goal-execution-watchdog-5edbef6a
- Mode: standard (사용자가 규모를 근거로 strict 트리거 2건에도 하향을 확정함)
- Status: Draft — round 3
- Created: 2026-09-09
- Updated: 2026-09-09
- Source goal: quality-goal의 Codex 실행 경로에 실행 감시, 안전한 회수 및 완료 뒤 잔류 프로세스 수거를 추가한다.

## Problem and context

`codex exec` 호출은 현재 `model-routing.md`의 세 runnable 템플릿에서 셸 리다이렉션으로 실행된다. 2026-09-06~09에 프로세스는 살아 있으나 events가 멈춘 사례가 네 건, 오케스트레이터가 끝난 실행을 기다린 사례를 포함해 오케스트레이터 턴이 끝난 사례가 네 건 관측되었다. 원인은 미확인이다. 따라서 이 작업은 원인을 진단하지 않고, 유한한 감시·안전한 종료·사후 증거 보존 계약을 만든다.

저장소의 `assert_preserved_sections.py`는 SKILL.md의 여덟 절을 기준 커밋과 바이트 동일하게 강제한다. 또한 `test_content_contracts.py`는 `model-routing.md`의 `codex exec` 코드 블록 플래그를 허용목록으로 제한하며, `assert_tests_preserved.py`는 기존 테스트 함수를 삭제할 수 없게 한다. 감시 계약은 보존 절 밖의 새 SKILL.md 절과 새 reference/스크립트/추가 테스트로 구현해야 한다.

상태 지문은 `.claude/quality-state/`를 제외하고, 기존 routing은 prompt·result·events·stderr를 실행별 상태 디렉터리에 둔다. 감시 산출물도 같은 실행별 디렉터리에 두어야 한다. 2026-09-09 실측 프리플라이트는 `--json` 없이 stdout에 한 줄, stderr에 진행 출력을 냈으므로 stdout(events)만으로 시작을 확인하면 안 된다.

## Goals

- 멈춘 Codex 실행을 시작 지연, 출력 정지, hard wall-clock 상한으로 감시하고 제한된 재시도로 회수한다.
- 결과 파일이 생긴 실행은 정지 판정보다 우선하여 회수하지 않되, 결과 스키마 검증이 통과하고 종료 코드가 0이거나 `EXIT_COLLECT_WAIT_SECONDS` 만료로 미확정인 경우에만 정상 완료로 채택한다. 비0 종료 코드 또는 스키마 불일치는 채택하지 않으며, 채택된 실행에 남은 소유 프로세스가 있으면 별도로 수거한다.
- 회수·수거 전에 재현 가능한 증거를 남기며, 어떤 경우에도 다른 실행의 프로세스를 종료하지 않는다.
- 오케스트레이터가 결과를 기다릴 때 유한 상한의 폴링 계약을 제공한다.

## Non-goals

- 중단 뒤 재개 시 실행 중 프로세스를 발견하여 부분 결과와 함께 이어받는 절차와 `state.json` 재개 의미론 변경은 후속 과제다. 이번에는 그 기반인 실행 기록 파일의 필드만 정한다.
- 결과 손상과 모델 미가용이 같은 복구 경로를 쓰는 문제는 #49-C의 범위이며 이 작업이 그 분리를 하지 않는다. 지금 분리하려면 바이트 보존 대상인 `### Implementation` 절을 고쳐야 하므로 범위 밖이다. #49-C는 열린 제안 이슈이며, 이 Spec은 저장소에 없는 상태 값을 신설하거나 실재하는 것처럼 인계 대상으로 쓰지 않는다.
- #39 모델 퇴역·리네이밍, #29 adversarial-review 스킬 변경, #50-E의 다른 문제 해결은 범위 밖이다.
- 광역 `pkill`, 이름/명령줄 패턴으로 프로세스를 찾아 종료하는 방식, 계정·API 키 순환, 무제한 재시도, 무단 모델 대체, 무응답 원인 진단은 하지 않는다.
- 요구사항 20건과 AC 38건은 상한인 요구사항 35건·AC 70건 이내로 제한하며, 과거 실패 실행(#42 4차 요구 66·AC 86, #70 1차 요구 69·AC 113)이 그 상한을 넘겼으므로 재개 하위 시스템과 결과 세부 분류를 제외했다.

## Requirements

- **R1.1** 구현·Spec author·readiness 및 preflight의 Codex 호출을 실행 감시 래퍼가 전송 계층으로 감싼다. 래퍼는 기존 `codex exec` argv, 모델, sandbox, 스키마 및 리다이렉션 대상의 의미를 보존하되 stdin·stdout(events)·stderr의 소유권을 받아 자식에 연결한다.
- **R1.2** 감시 실행의 prompt, result, events, stderr, watchdog 기록 및 보존 번들은 `.claude/quality-state/<task-id>/<execution-id>/` 안에만 둔다. `/tmp` 고정 경로를 쓰지 않는다.
- **R2.1** `RESULT_PATH`가 설정된 실행의 대기 루프는 매 폴링에서 (a) 결과 파일 존재, (b) 실행 기록에 적힌 pid의 생존, (c) events 또는 stderr 중 하나의 기준 시각 뒤 증가 순서로 확인한다. 결과 파일이 있으면 시작·활동 정지·hard timeout 감시 상한은 더 기다리지 않고 R9.5의 별도 유한 종료 코드 회수 뒤 R9.1에 따라 판정한다. 결과 파일이 없으면 이름·명령줄 검색 없이 기록된 pid만 생존 확인에 쓰고, pid가 살아 있는 경우에만 events 또는 stderr 증가를 확인한다. 실제 시작 확인은 기록된 pid의 생존과 첫 events 또는 stderr 증가가 모두 충족될 때 성공이다. 기록된 pid가 죽고 결과 파일도 없으면 대기 상한을 기다리지 않고 즉시 R9.1 행렬로 판정하며, 종료 코드, 결과 파일 존재, 결과 스키마 검증 결과, 보존 위치, 감시자 판정 사유의 다섯 사실을 기록한다. pid가 살아 있으나 둘 다 증가하지 않은 시작 상한 만료는 결과 파일을 먼저 확인한 뒤 회수 후보가 된다. `RESULT_PATH` 없는 preflight의 종료는 R9.3이 정하며 이 결과 파일 판정에 넣지 않는다.
- **R2.2** 시작 뒤에는 Python `subprocess`와 단조 시계로 hard wall-clock 상한과 events·stderr의 결합 활동 정지 상한을 감시한다. 외부 `timeout` 또는 `gtimeout` 바이너리에 의존하지 않는다. 파일이 아직 생성되지 않은 경우도 무활동으로 계산하며, 각 상한·폴링 간격·재시도 상한은 이름 있는 설정값으로 둔다. 운영 활동 정지 상한 `ACTIVITY_STALL_SECONDS`의 기본값은 관측된 회수 지점 8~10분을 포괄하는 600초이고, 운영 설정 허용 범위는 480~600초이며, 빠른 fixture의 짧은 값 주입은 이 운영 범위를 바꾸지 않는다.
- **R3.1** 결과 파일 존재는 시작 실패, 활동 정지, hard timeout의 정지 판정보다 우선하여 감시자가 회수 신호를 보내지 않게 한다. 감시자는 종료 신호 직전에 결과 파일을 다시 확인한다. 그러나 결과 파일의 존재만으로 완료를 채택하지 않으며, R9.5로 회수한 종료 코드가 0이거나 그 유한 대기 만료 뒤 미확정으로 기록되고 결과 스키마 검증이 통과한 경우에만 정상 완료로 결과를 채택한다.
- **R3.2** 결과를 채택한 뒤 자식 또는 기록된 소유 그룹이 남아 있으면, R9.1이 정상 완료로 판정한 미확정 종료 코드의 경우를 포함하여 실행의 정상 완료 분류를 바꾸지 않고 수거(reap) 후보로 처리한다.
- **R4.1** 결과 없는 회수(abort)는 종료 전에 현재 workspace diff, events, stderr, 실행 지문을 실행별 보존 번들에 성공적으로 저장해야 한다. 보존 성공 뒤 기록된 소유 그룹에 SIGTERM을 보내고 `ABORT_GRACE_SECONDS = 60` 동안 기다린 뒤에만 SIGKILL을 보낸다. 이 값과 근거는 결과를 이미 채택한 프로세스에도 같은 정상 종료 기회를 주면서 무기한 잔류를 막는 R7.1의 `REAP_GRACE_SECONDS = 60`과 같으며, 두 경로의 소유권 검증은 동일하다. 보존 실패면 SIGTERM·SIGKILL을 보내지 않고 회수를 실패로 기록해 상위 흐름에 표면화한다.
- **R4.2** 회수는 소유권이 확인된 기록 pid와 그 시작 시 생성한 프로세스 그룹에만 신호를 보낼 수 있다. 이름, 명령줄, 전역 프로세스 검색 결과는 종료 대상 판정에 사용하지 않는다.
- **R5.1** pid 소유권 검증은 회수와 수거에 공통으로 적용한다. 같은 이름과 명령줄을 가진 기록 트리 밖 미끼 프로세스는 두 경로 모두에서 살아남아야 한다.
- **R6.1** 회수와 수거는 별도 상태 필드와 보고서 필드로 기록한다. 채택된 정상 완료와 그 수거는 재시도 예산을 소모하지 않고, 결과 없는 회수와 R9.4의 결과 존재·미채택 실패는 재기동 후보마다 재시도 예산을 정확히 한 번 소모한다. 이 예산 대칭은 기록 분리를 바꾸지 않으며, 이 사실은 기존 `BLOCKED_MODEL_UNAVAILABLE` 복구로 인계할 때도 기록하되 새 상태 값·단계·복구 경로를 만들지 않는다.
- **R6.2** 실행 기록에는 최소한 execution ID, pid, pgid, 시작 시각, 종료 시각 또는 경과 시간, 자식 종료 코드(0·비0·미확정), 결과 파일 존재 여부, 결과 스키마 검증 결과(통과·불일치·미실행), 시작 확인, 감시 중단 사유, 종료 신호 결과, 보존 번들 경로, 회수 값, 수거 값 및 잔류 pid를 기록한다.
- **R7.1** 수거는 기록된 소유 그룹에 SIGTERM을 먼저 보내고 `REAP_GRACE_SECONDS = 60` 동안 종료를 기다린 뒤에만 SIGKILL을 보낸다. 60초는 결과가 이미 채택된 뒤 정상 종료 기회를 주면서 무기한 잔류를 막는 사용자 확정 권고값이다.
- **R7.2** 수거 대기는 `REAP_WAIT_CAP_SECONDS`로 상한을 둔다. 상한을 넘으면 잔류 pid와 수거 실패를 기록하고 결과 사용 및 다음 파이프라인 단계는 진행한다. 이는 보존 실패 시 회수의 종료를 금지하는 R4.1과 달리, 이미 결과가 있는 수거 실패가 실행을 막지 않는 규칙이다.
- **R8.1** SKILL.md의 보존 대상 여덟 절 밖에 유한 상한 폴링 계약을 추가한다. 오케스트레이터는 result 파일·watchdog 기록·프로세스 종료를 유한 대기 간격으로 확인하고, 이미 존재하는 결과를 발견하면 시작·활동 정지·hard timeout 감시 상한은 더 기다리지 않는다. R9.5의 짧고 별도인 종료 코드 회수 대기는 이 감시 상한 대기가 아니며, 그 결과를 완료로 채택할지는 R9.1 판정 행렬이 정한다.
- **R8.2** 기존 보존 절의 바이트와 기존 `def test_*` 이름을 유지하고, `model-routing.md`의 `codex exec` 코드 블록에 허용목록 밖 플래그를 추가하지 않는다. 새 감시 래퍼의 사용법은 `codex exec` 리터럴이 없는 별도 코드 블록 또는 문서로 둔다.
- **R9.1** 결과 파일 존재 여부 × R9.5로 회수한 자식 종료 코드(0·비0·미확정) × 결과 스키마 검증 결과를 함께 판정한다. 결과가 있고 스키마가 통과하며 종료 코드가 0 또는 R9.5 유한 대기 만료 뒤의 미확정이면 완료이고, 그 미확정 완료에서 자식이 남아 있으면 R3.2·R7.1의 수거 경로로 간다. 결과 부재 또는 스키마 불일치에서는 종료 코드 0이라도 성공이 아니고 미확정도 실패이며, 비0 종료 코드는 결과·스키마 여부와 무관하게 실패다. 결과 부재이면 스키마 검증 결과는 미실행으로 기록한다. 감시자가 자식의 자연 종료를 관측하면 대기 루프는 즉시 감시 타이머를 끝내고 마지막 결과 확인, 종료 코드 회수, 필요한 스키마 검증을 수행한 뒤 이 판정으로 완료 또는 기존 복구 경로를 선택한다.
- **R9.2** 재기동 예산의 주체는 상위 quality-goal 오케스트레이터이며 감시 래퍼는 스스로 재기동하지 않는다. 예산은 implementation·Spec author·readiness 각각의 단계별 실행 묶음에 적용하고 preflight에는 적용하지 않는다. 단계 시작 시 오케스트레이터가 입력의 이름 있는 `WATCHDOG_RESTART_BUDGET`을 초기값으로 기록하며 입력이 없으면 새 기본값 1을 사용한다. 예산은 재기동 후보가 되는 실패마다 정확히 한 번 소모하며, 결과 없는 abort와 R9.4의 결과 존재·미채택 실패가 각각 그 대상이고 채택된 정상 완료와 그 수거는 소모하지 않는다. 실행 기록과 최종 보고서에는 초기값·남은 값·각 대상 실패의 한 번 차감·재기동 여부를 남긴다. 남은 값이 0이면 재기동하지 않고 현재 단계를 정지해 사용자와 보고서에 예산 소진 사실을 표면화하며 기존 복구 경로를 유지한다.
- **R9.3** preflight는 `RESULT_PATH`가 없는 선택적 결과 경로 호출이다. 래퍼는 argv 프롬프트와 stdout·stderr 관찰을 전달하며 결과 스키마 검증을 요구하지 않는다. preflight는 종료 코드 0과 비어 있지 않은 모델 응답일 때만 성공이고, 시작·정지·hard-timeout 또는 그 밖의 실패는 기존 모델 미가용 복구 경로로 분류하며 자동 재기동하거나 R9.2의 예산을 소모하지 않는다.
- **R9.4** 결과 파일이 존재해 abort 신호를 보내지 않는 규칙과 R9.1의 채택 판정은 분리한다. 결과가 있어도 종료 코드 비0 또는 스키마 불일치이면 결과를 채택하지 않고 다섯 회수 사실(종료 코드, 결과 파일 존재, 결과 스키마 검증 결과, 보존 위치, 감시자 판정 사유)을 기록하여 기존 복구 경로에 넘긴다. 이 결과 존재·미채택 실패는 R9.2에 따라 재시도 예산을 정확히 한 번 소모하고, 남은 예산이 있으면 상위 오케스트레이터만 재기동하며 0이면 현재 단계를 정지·표면화한다. 이때 결과 파일이 있다는 이유로 abort로 종료하지 않으며 새 분류 값도 만들지 않는다.
- **R9.5** `RESULT_PATH`가 있는 결과 파일을 발견하면 감시 상한 대기를 끝내고 `EXIT_COLLECT_WAIT_SECONDS = 5` 동안에만 자식의 자연 종료와 종료 코드를 회수한다. 이 유한 대기가 만료된 뒤에만 종료 코드를 미확정으로 기록한다. R2.1·R8.1의 “더 기다리지 않는다”는 시작·활동 정지·hard timeout 감시 상한을 더 기다리지 않는다는 뜻이며, 이 짧은 종료 코드 회수 대기는 별개다. 결과 기록 직후 정상 종료는 초 단위이므로 5초는 이를 회수하면서 `ACTIVITY_STALL_SECONDS = 600`, `ABORT_GRACE_SECONDS = 60`, `REAP_GRACE_SECONDS = 60`보다 훨씬 짧고, 더 긴 대기로 인한 파이프라인 지연을 피하는 값이다.

## Acceptance criteria

- **AC-1** 구현·author·readiness·preflight 각각의 호출 계약 테스트가 원래 Codex argv와 stdin, events(stdout), stderr 대상이 래퍼를 거쳐 자식에 전달됨을 확인한다. preflight fixture는 `RESULT_PATH` 없이 argv 프롬프트를 전달하는 원래 호출 형태도 확인한다. [실행] (`CMD-1`)
- **AC-2** 실행 fixture가 모든 감시·보존 파일을 실행별 상태 디렉터리에 만들고 `/tmp` 아래에는 만들지 않음을 확인한다. [실행] (`CMD-1`)
- **AC-3** events가 비어 있어도 stderr가 증가하고 종료 코드 0·비어 있지 않은 응답을 낸 `RESULT_PATH` 없는 preflight fixture가 시작 및 최종 성공이 됨을 확인한다. [실행] (`CMD-1`)
- **AC-4** events와 stderr가 모두 생성·증가하지 않은 fixture가 시작 상한 뒤에 감시 사유로 기록됨을 확인한다. [실행] (`CMD-1`)
- **AC-5** 존재하지 않는 events/stderr 파일이 활동 정지 상한을 피하지 못하고, hard timeout도 별도 사유로 기록됨을 확인한다. [실행] (`CMD-1`)
- **AC-6** 각 시간·폴링·재시도 값이 이름 있는 설정으로 노출되고 테스트 fixture가 짧은 값으로 주입됨을 확인한다. `ACTIVITY_STALL_SECONDS`의 운영 기본값 600초와 운영 범위 480~600초, `EXIT_COLLECT_WAIT_SECONDS = 5`의 감시 상한·abort·reap 유예보다 짧은 관계는 유지되고 fixture 주입은 테스트에만 적용됨을 확인한다. [실행] (`CMD-1`)
- **AC-7** 종료 코드 0과 스키마 통과 결과 파일이 정지 판정 전에 있으면 R9.5 종료 코드 회수 뒤 회수가 일어나지 않고 정상 완료가 됨을 확인한다. [실행] (`CMD-1`)
- **AC-8** 정지 판정과 종료 직전 재확인 사이에 결과 파일을 생성하는 경합 fixture가 신호를 보내지 않고 시작·활동 정지·hard timeout 감시 상한을 더 기다리지 않으며, R9.5의 별도 유한 종료 코드 회수와 스키마 검증 뒤 R9.1 행렬이 결과 채택 또는 기존 복구 경로를 정함을 확인한다. [실행] (`CMD-1`)
- **AC-9** 결과를 채택했으나 소유 자식이 남은 fixture가 정상 완료를 유지하고 수거 후보로만 기록됨을 확인한다. [실행] (`CMD-1`)
- **AC-10** 결과 없는 회수 fixture가 diff, events, stderr, 지문 보존의 성공 기록 뒤에만 SIGTERM을 보내는 순서를 확인한다. [실행] (`CMD-1`)
- **AC-11** 보존 writer를 실패시키는 fixture가 SIGTERM과 SIGKILL을 보내지 않고 보존 실패를 표면화함을 확인한다. [실행] (`CMD-1`)
- **AC-12** 회수 경로가 기록한 pid/pgid 밖의 프로세스에 신호를 보내지 않고 이름·명령줄 검색을 종료 판정에 호출하지 않음을 확인한다. [실행] (`CMD-1`)
- **AC-13** 같은 이름·명령줄의 미끼와 소유 자식이 공존하는 회수 fixture에서 소유 자식만 종료되고 미끼가 살아남음을 확인한다. [실행] (`CMD-1`)
- **AC-14** 같은 이름·명령줄의 미끼와 결과 뒤 잔류 자식이 공존하는 수거 fixture에서 소유 자식만 종료되고 미끼가 살아남음을 확인한다. [실행] (`CMD-1`)
- **AC-15** 결과 없는 회수 fixture가 종료 코드, 결과 파일 존재, 결과 스키마 검증 결과, 보존 번들 위치, 감시자 판정 사유의 다섯 사실을 `abort` 기록에 남기고 재시도 예산을 정확히 한 번 차감하며, 보존 대상 `### Implementation`의 기존 `BLOCKED_MODEL_UNAVAILABLE` 복구 경로가 바뀌지 않음을 확인한다. [실행] (`CMD-1` `CMD-2`)
- **AC-16** 결과를 채택한 수거는 `reap` 필드에만 기록되고 정상 완료와 재시도 예산 불변을 확인한다. [실행] (`CMD-1`)
- **AC-17** 상태 및 최종 보고서 fixture가 R6.2의 모든 최소 기록 필드(자식 종료 코드와 결과 스키마 검증 결과 포함)를, `abort`와 `reap`을 별도 값으로, 포함함을 확인한다. [실행] (`CMD-1`)
- **AC-18** 수거 fixture가 SIGTERM을 SIGKILL보다 먼저 보냄을 확인한다. [실행] (`CMD-1`)
- **AC-19** `REAP_GRACE_SECONDS`가 값 60을 가진 이름 있는 상수이고, 그 근거가 문서화됨을 확인한다. [실행] (`CMD-2`)
- **AC-20** 수거 유예 뒤에도 소유 자식이 남으면 SIGKILL을 보내고 종료 결과를 기록함을 확인한다. [실행] (`CMD-1`)
- **AC-21** `REAP_WAIT_CAP_SECONDS`를 넘기는 fixture가 잔류 pid와 수거 실패를 기록하지만 결과 사용과 다음 단계 진행을 막지 않음을 확인한다. [실행] (`CMD-1`)
- **AC-22** 수거 실패가 회수로 재분류되지 않고 재시도 예산을 소모하지 않으며, 보존 실패 시 종료 금지 규칙은 결과 없는 회수에만 적용됨을 확인한다. [실행] (`CMD-1`)
- **AC-23** SKILL.md의 새 보존 대상 밖 계약이 result·watchdog·프로세스 종료를 유한 폴링하며 result 우선을 명시함을 content-contract 테스트로 확인한다. [실행] (`CMD-2`)
- **AC-24** 유한 폴링 fixture가 이미 존재한 결과 파일을 첫 검사에서 발견하면 시작·활동 정지·hard timeout 감시 상한을 더 기다리지 않고 R9.5의 별도 유한 종료 코드 회수와 스키마 검증 뒤 R9.1 행렬을 적용함을 확인한다. 결과 없는 종료·watchdog 상태는 상한 안에 반환함을 확인한다. [실행] (`CMD-1`)
- **AC-25** 보존 절 검사가 기준 커밋에 대해 통과함을 확인한다. [실행] (`CMD-3`)
- **AC-26** 기존 테스트 이름 보존 검사가 기준 커밋에 대해 통과함을 확인한다. [실행] (`CMD-4`)
- **AC-27** `model-routing.md`의 `codex exec` 코드 블록이 현 허용 플래그 계약을 계속 통과하고, 래퍼 사용법 블록에는 `codex exec` 문자열이 없음을 확인한다. [실행] (`CMD-2`)
- **AC-28** quality-goal 전체 단위 테스트가 통과하며, 타입 검사·린트·빌드는 저장소에 미구성임을 검증 기록에 명시한다. [실행] (`CMD-5`)
- **AC-29** 결과 파일 유무, R9.5로 회수한 자식 종료 코드 0·비0·미확정, 스키마 통과·불일치·미실행의 모든 유효 조합 fixture가 R9.1의 완료/실패 행렬을 판정한다. 자연 종료 fixture는 대기 루프가 감시 상한을 더 기다리지 않고 마지막 확인·종료 코드 회수·스키마 검증 뒤 반환하고, 결과·스키마 통과 미확정은 정상 완료임을 확인한다. [실행] (`CMD-1`)
- **AC-30** 단계별 fixture가 `WATCHDOG_RESTART_BUDGET`의 초기값·남은 값을 기록하고, 결과 없는 abort와 결과 존재·미채택 실패 각각에서 예산이 정확히 한 번 소진됨을 확인한다. 상위 오케스트레이터는 잔여 예산이 있는 재기동 후보 실패만 재기동하고, 남은 값 0에서는 재기동하지 않고 현재 단계 정지·사용자/보고서 표면화를 기록함을 확인한다. [실행] (`CMD-1`)
- **AC-31** SIGTERM을 무시하는 결과 없는 abort fixture가 보존 성공 뒤 `ABORT_GRACE_SECONDS = 60`의 이름 있는 유예를 거쳐 SIGKILL로 종료되고 신호 결과를 기록함을 확인한다. 이 값과 근거가 `REAP_GRACE_SECONDS`와 같음을 확인한다. [실행] (`CMD-1` `CMD-2`)
- **AC-32** `RESULT_PATH` 없는 preflight fixture가 종료 코드 0·비어 있지 않은 응답일 때만 성공하고, 시작·정지·hard-timeout 및 비0/빈 응답은 기존 모델 미가용 복구로 분류되며 자동 재기동과 재시도 예산 차감이 없음을 확인한다. [실행] (`CMD-1`)
- **AC-33** 감시 상한 fixture와 content-contract 검사가 Python `subprocess`·단조 시계만 사용하고 외부 `timeout` 또는 `gtimeout` 실행·의존이 없음을 확인한다. [실행] (`CMD-1` `CMD-2`)
- **AC-34** `RESULT_PATH`가 설정되고 기록된 pid가 죽은 결과 파일 없는 fixture가 대기 상한을 기다리지 않고 즉시 R9.1 행렬로 판정하며 다섯 사실을 기록함을 확인한다. [실행] (`CMD-1`)
- **AC-35** `RESULT_PATH`가 설정된 대기 루프 fixture가 매 폴링에서 결과 파일, 기록된 pid 생존, 첫 events 또는 stderr 증가 순서로 확인하고, 이름·명령줄 검색을 사용하지 않음을 확인한다. [실행] (`CMD-1`)
- **AC-36** 결과 파일 기록 직후 자식이 아직 종료 전인 fixture가 `EXIT_COLLECT_WAIT_SECONDS` 안에 종료 코드 0을 회수하고 스키마 통과 결과를 정상 완료로 판정하며, 남은 소유 자식은 reap 후보로만 기록되고 abort·재시도 예산 차감이 없음을 확인한다. [실행] (`CMD-1`)
- **AC-37** `EXIT_COLLECT_WAIT_SECONDS` 만료로 종료 코드가 미확정으로 기록되지만 결과·스키마가 유효한 fixture가 정상 완료와 reap 후보가 되고 재시도 예산을 소모하지 않음을 확인한다. [실행] (`CMD-1`)
- **AC-38** 결과 파일이 있으나 종료 코드 비0 또는 스키마 불일치로 채택하지 않는 fixture가 abort와 별도로 R9.4 실패를 기록하고 재시도 예산을 정확히 한 번 차감하며, 잔여 예산이 있으면 상위 오케스트레이터만 재기동하고 0이면 현재 단계를 정지·표면화함을 확인한다. [실행] (`CMD-1`)

## Requirements traceability

This table maps every requirement to acceptance criteria and the judgement method that proves the mapping.

| Requirement | Acceptance criteria | Judgement method |
|---|---|---|
| R1.1 | AC-1, AC-32 | `CMD-1` |
| R1.2 | AC-2 | `CMD-1` |
| R2.1 | AC-3, AC-4, AC-34, AC-35, AC-36, AC-37 | `CMD-1` |
| R2.2 | AC-5, AC-6, AC-33 | `CMD-1`, `CMD-2` |
| R3.1 | AC-7, AC-8, AC-29, AC-36, AC-37 | `CMD-1` |
| R3.2 | AC-9, AC-36, AC-37 | `CMD-1` |
| R4.1 | AC-10, AC-11, AC-15, AC-31 | `CMD-1`, `CMD-2` |
| R4.2 | AC-12 | `CMD-1` |
| R5.1 | AC-13, AC-14 | `CMD-1` |
| R6.1 | AC-15, AC-16, AC-30, AC-36, AC-37, AC-38 | `CMD-1`, `CMD-2` |
| R6.2 | AC-15, AC-17, AC-29 | `CMD-1`, `CMD-2` |
| R7.1 | AC-18, AC-19, AC-20, AC-36, AC-37 | `CMD-1`, `CMD-2` |
| R7.2 | AC-21, AC-22 | `CMD-1` |
| R8.1 | AC-23, AC-24, AC-36, AC-37 | `CMD-1`, `CMD-2` |
| R8.2 | AC-25, AC-26, AC-27, AC-28 | `CMD-2`, `CMD-3`, `CMD-4`, `CMD-5` |
| R9.1 | AC-7, AC-8, AC-24, AC-29, AC-36, AC-37 | `CMD-1` |
| R9.2 | AC-15, AC-30, AC-38 | `CMD-1`, `CMD-2` |
| R9.3 | AC-1, AC-3, AC-32 | `CMD-1` |
| R9.4 | AC-29, AC-38 | `CMD-1`, `CMD-2` |
| R9.5 | AC-6, AC-7, AC-8, AC-24, AC-29, AC-36, AC-37 | `CMD-1` |

## Architecture

새 `execution-watchdog` 구성요소는 routing 템플릿의 Codex argv를 받는 전송 계층이다. 이 구성요소가 자식을 새 세션/기록된 프로세스 그룹으로 시작하고, 출력 파일의 변화·결과 파일·pid 소유권·시간 상한을 Python `subprocess`와 단조 시계로 관찰한다. `quality_state.py` 또는 새 실행 기록 도우미는 실행별 JSON을 원자적으로 기록하고, 보고서 렌더링은 그 JSON에서 `abort`와 `reap`을 독립적으로 읽는다. 상위 오케스트레이터가 단계별 재기동 예산과 다음 실행만 소유한다.

종료 권한은 기록된 root pid와 이 root가 시작 때 받은 pgid에 한정한다. pid가 이미 사라졌거나 pgid가 일치하지 않으면 종료하지 않고 소유권 거부를 기록한다. 결과가 없는 회수는 보존 성공 뒤에만 신호를 보낼 수 있다. R9.1이 정상 완료로 채택한 결과 뒤의 수거는 결과 전달을 막지 않는 비차단 또는 상한 있는 후속 작업으로 처리한다.

### D1. 감시 위치와 호출 보존

대안은 (1) 각 routing 템플릿에 timeout 플래그를 추가, (2) 셸 함수에 로직을 중복, (3) 별도 래퍼를 전송 계층으로 두는 것이다. (3)을 채택한다. (1)은 `codex exec` 플래그 허용목록을 깨고, (2)는 구현·author·readiness·preflight 간 동작 발산을 만든다. 래퍼는 argv를 재해석하지 않아 기존 호출 계약과 보존 절을 유지한다.

### D2. 결과 우선과 종료 경계

결과 파일 존재는 감시자의 abort 신호를 막는 결정적 증거다. 감시 사유가 먼저 계산되어도 실제 종료 직전 다시 결과를 확인한다. 결과가 있으면 abort를 취소하고 R9.5의 짧은 종료 코드 회수를 거친다. 정상 완료는 스키마 통과와 종료 코드 0 또는 R9.5 만료 뒤의 미확정을 함께 만족해야 한다. 결과 뒤 잔류 프로세스는 유효한 결과를 채택한 경우에만 별도 reap으로 다루므로 결과를 버리지 않으면서 프로세스 증식을 제한한다.

### D3. 회수와 수거의 오류 규칙

abort는 결과 없는 실패 경로이므로 보존 실패 시 되돌릴 수 없는 종료를 금지하고 실패를 표면화한다. reap은 이미 결과를 채택한 정상 완료의 부수 정리이므로, 대기 상한 또는 수거 실패가 결과 사용을 막지 않는다. 두 규칙은 적용 전제와 결과가 달라 충돌하지 않는다.

## Interfaces and data flow

1. 호출자는 기존 Codex argv 및 실행별 상태 디렉터리를 래퍼에 준다. 구현·author·readiness는 `PROMPT_PATH`, `EVENTS_PATH`, `STDERR_PATH`, `RESULT_PATH`를 주고, preflight는 argv 프롬프트와 stdout·stderr 대상만 주며 `RESULT_PATH`는 선택적으로 생략한다. 래퍼가 각 원래 호출 형태의 stdin/stdout/stderr를 자식에 연결한다.
2. 래퍼는 execution ID, root pid, pgid, 시작 시각을 즉시 기록하고 events 또는 stderr 증가로 시작을 확인한다.
3. `RESULT_PATH`가 설정된 실행은 매 폴링마다 (a) 결과 파일을 먼저 확인해 있으면 시작·활동 정지·hard-timeout 감시 상한을 끝내고 R9.5의 별도 유한 대기로 종료 코드를 회수한 뒤 R9.1 판정으로 넘긴다. 결과가 없을 때 (b) 기록된 pid의 생존을 이름·명령줄 검색 없이 확인하고, pid가 죽었으면 대기 상한을 기다리지 않고 즉시 R9.1 행렬과 다섯 사실 기록으로 판정한다. pid가 살아 있을 때만 (c) 첫 events 또는 stderr 증가를 확인한 뒤 시작/정지/hard-timeout 상태를 평가한다. 종료 직전에도 결과 파일을 재확인한다. 자식의 자연 종료를 관측하면 이 대기 루프를 끝내고 종료 코드와 마지막 결과 상태를 회수한 뒤, 결과가 있으면 스키마를 검증하여 R9.1 행렬을 적용한다. `RESULT_PATH` 없는 preflight는 R9.3의 종료 코드·응답 판정으로 이 결과 파일 대기와 분리한다.
4. 결과가 없으면 보존 번들을 원자적으로 쓰고 성공한 경우에만 abort한다. 결과가 있으면 abort 신호 없이 R9.5의 종료 코드·스키마로 채택 여부를 가르고, 종료 코드 0 또는 미확정의 유효 결과를 채택한 경우에만 남은 소유 그룹을 reap 기록으로 따로 처리한다.
5. 상위 quality-goal 흐름은 R9.1·R9.4 실패의 다섯 사실을 기록해 바이트 보존 대상 `### Implementation`의 기존 `BLOCKED_MODEL_UNAVAILABLE` 복구로 인계한다. 재기동 후보 실패는 abort 여부와 무관하게 단계별 예산을 한 번 감소시키고, 남은 값이 0이면 재기동하지 않아 사용자·보고서에 표면화한다. reap은 정상 완료와 별도 필드로 보고되어 예산을 바꾸지 않는다.

실행 기록의 제안 JSON 인터페이스는 `execution_id`, `pid`, `pgid`, `started_at`, `ended_at`, `elapsed_s`, `child_exit_code`, `result_exists`, `result_schema_validation`, `started`, `watchdog_reason`, `signals`, `preservation_bundle`, `abort`, `reap`, `residual_pids`, `retry_budget_initial`, `retry_budget_remaining`, `retry_consumed`, `restart_attempted`, `restart_stopped`를 가진다. `child_exit_code`는 `0`·비0 정수·`unknown`이고 `result_schema_validation`은 `passed`·`mismatch`·`not_run`이다. `abort`와 `reap`은 상호 배타가 아니라, 결과 없는 실행은 abort만, 유효한 결과가 있는 잔류 정리는 reap만 기록하는 별도 의미의 객체다.

## Failure behavior

- 시작 확인·활동 정지·hard timeout이 생겨도 결과 파일이 있으면 abort 신호를 보내지 않는다. 정상 완료 반환은 스키마 통과와 종료 코드 0 또는 R9.5 만료 뒤의 미확정 조합에 가능하며, 미확정 완료의 잔류 자식은 수거한다. 경합 fixture는 이 재확인과 분리를 강제한다.
- 결과가 없고 보존에 성공하면 abort를 기록하고 소유 그룹에만 SIGTERM, `ABORT_GRACE_SECONDS`, SIGKILL 순서로 신호를 보낸 뒤, 다섯 사실을 기록한 채 기존 `BLOCKED_MODEL_UNAVAILABLE` 복구 경로로 넘긴다. 결과 존재·미채택 R9.4 실패도 abort 없이 같은 복구로 넘긴다. 상위 오케스트레이터만 설정된 유한 예산 안에서 재기동 후보 실패마다 정확히 한 번 재기동 예산을 소모하며, 예산이 0이면 재기동하지 않고 현재 단계를 정지·보고한다.
- 보존이 실패하거나 pid/pgid 소유권이 확인되지 않으면 종료하지 않는다. 원인과 보존 실패 또는 소유권 거부를 기록하고 상위 흐름에 실패로 보인다.
- 결과 뒤 reap은 SIGTERM, `REAP_GRACE_SECONDS`, SIGKILL 순서다. `REAP_WAIT_CAP_SECONDS`를 넘기거나 실패하면 residual pid를 기록하고 정상 결과의 사용을 계속한다.
- 자연 종료의 비0, 결과 부재, 스키마 불일치, 또는 결과 부재·스키마 불일치와 함께 기록된 미확정은 기존 `BLOCKED_MODEL_UNAVAILABLE` 처리와 무단 모델 대체 금지를 바꾸지 않는다. 결과·스키마 통과 미확정은 R9.1의 정상 완료 및 reap 경로다. `RESULT_PATH` 없는 preflight는 종료 코드 0과 비어 있지 않은 응답 외의 경우 같은 복구로 분류하며 자동 재기동·예산 차감은 하지 않는다.

## Security and risk

프로세스 종료는 동일 머신의 다른 세션에 영향을 줄 수 있는 고위험 동작이다. 신뢰 경계는 래퍼가 시작해 기록한 root pid/pgid이며, 이름·명령줄은 표시용 증거일 뿐 종료 권한이 아니다. 회수와 수거 각각의 미끼 프로세스 음성 대조가 이 경계를 검증한다.

diff·events·stderr에는 작업 내용이나 오류 출력이 들어갈 수 있으므로 기존 무시된 실행별 상태 디렉터리에만 보관하고, 자격 증명을 새 로그·보고서·문서에 싣지 않는다. 보존 전에 종료하면 사후 조사가 불가능해지는 위험은 보존 성공 선행과 보존 실패 시 종료 금지로 완화한다. 결과-종료 경합은 종료 직전 재확인으로 완화한다.

`EXIT_COLLECT_WAIT_SECONDS = 5`는 `ACTIVITY_STALL_SECONDS = 600`, `ABORT_GRACE_SECONDS = 60`, `REAP_GRACE_SECONDS = 60`보다 짧아 결과 직후 자연 종료를 회수하되 파이프라인 지연을 제한한다. `REAP_GRACE_SECONDS = 60` 및 유한 수거 상한은 잔류를 무기한으로 두지 않는 대신 강제 종료 위험을 갖는다. 결과는 이미 채택되었고 소유권 검증을 통과한 프로세스 그룹에만 신호를 보내므로, 수거 실패는 기록만 하고 파이프라인을 막지 않는다.

## Test strategy

새 `tests/test_execution_watchdog.py`는 실제 짧은 자식 프로세스와 제어 가능한 시계/신호 fixture를 사용한다. 동일 이름·명령줄의 미끼를 별도 프로세스 그룹으로 만들고, abort 및 reap에서 각각 미끼 생존을 검사한다. 결과-종료 경합은 감시 판정 뒤 최종 결과 검사 직전에 결과 파일을 만드는 동기화 fixture로 재현한다. 보존 순서는 이벤트 로그와 보존 writer 실패 주입으로 검사한다. 결과 파일 직후 살아 있는 자식의 5초 안 종료 코드 회수와, 5초 만료 뒤 유효 결과·미확정의 정상 완료 및 reap 후보를 각각 재현한다. 결과 파일 유무·종료 코드 0/비0/미확정·스키마 통과/불일치/미실행의 행렬, 기록된 pid 사망·결과 부재의 즉시 판정, 결과·pid·첫 이벤트 폴링 순서, 자연 종료의 즉시 대기 종료, 결과 없는 abort와 결과 존재·미채택 실패의 예산 소진 뒤 재기동 금지, `RESULT_PATH` 없는 preflight, SIGTERM 무시 abort를 각각 fixture로 재현한다.

기존 content-contract·보존 절·테스트 이름 검사는 새 계약이 기존 제약을 손상시키지 않음을 확인한다. 전체 unittest discovery를 최종 회귀 검사로 실행한다. 타입 검사, 린트, 빌드는 저장소에 설정이 미구성이므로 성공 판정으로 가장하지 않고 검증 보고서에 미구성으로 기록한다.

### 판정 명령 표

| ID | 명령 | 통과 조건 |
|---|---|---|
| CMD-1 | `cd dot_claude/skills/quality-goal && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest tests.test_execution_watchdog` | watchdog lifecycle, race, 보존 순서, pid 음성 대조, 기록 및 상한 fixture가 모두 통과한다. |
| CMD-2 | `cd dot_claude/skills/quality-goal && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest tests.test_content_contracts` | 새 폴링·수거 상수 문서 계약과 routing 플래그 안전 계약이 통과한다. |
| CMD-3 | `cd /Users/lee-kyu-hwan/code/dotfiles__worktrees/85-feat-quality-goal-execution-watchdog && /opt/homebrew/bin/python3 dot_claude/skills/quality-goal/tests/assert_preserved_sections.py 9ff32a30c9498df007ec5dfa558a442cc7841be1` | 저장소 루트를 작업 디렉터리로 하여 여덟 SKILL.md 보존 절이 기준 커밋과 바이트 동일하다. |
| CMD-4 | `cd /Users/lee-kyu-hwan/code/dotfiles__worktrees/85-feat-quality-goal-execution-watchdog && /opt/homebrew/bin/python3 dot_claude/skills/quality-goal/tests/assert_tests_preserved.py 9ff32a30c9498df007ec5dfa558a442cc7841be1` | 저장소 루트를 작업 디렉터리로 하여 기준의 모든 기존 `def test_*` 이름이 남아 있다. |
| CMD-5 | `cd dot_claude/skills/quality-goal && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s tests -p "test_*.py"` | 전체 quality-goal 테스트가 실패 없이 끝난다. |

## Decisions

### D4. 수거 대기와 결과 전달

R9.1이 결과를 채택한 실행의 reap은 결과 전달의 선행 조건이 아니다. 구현이 단순한 동기 대기를 선택하더라도 `REAP_WAIT_CAP_SECONDS`를 넘기면 채택된 결과를 반환하고 residual pid를 기록해야 한다. 따라서 R4.1의 “보존 실패 시 abort 금지”는 결과 없는 abort에만, R7.2의 “reap 실패도 진행”은 결과 있는 정상 완료에만 적용된다.

### D5. 재시도 예산의 경계

예산은 재기동 후보가 되는 실패마다 한 번 감소한다. 결과 없는 abort와 결과 존재·미채택 R9.4 실패는 각각 한 번 감소하고, 결과 우선 경합에서 종료 코드 0 또는 R9.5 만료 뒤 미확정의 스키마 통과 결과가 채택되면 abort가 발생하지 않으며 예산도 감소하지 않는다. reap은 정상 완료 부수 작업이므로 실패해도 예산을 감소시키지 않는다. 예산은 상위 오케스트레이터가 단계 시작 때 `WATCHDOG_RESTART_BUDGET` 또는 기본값 1로 고정·기록하고, 0이 되는 다음 시도부터는 재기동하지 않고 사용자·보고서에 정지를 표면화한다. 이 정지는 결과가 있는 수거 실패에도 다음 단계를 진행시키는 R7.2와 다른, 재기동 후보 실패 뒤의 재기동 결정이다.

### D6. 범위와 미확인 사항

관측된 무응답의 근본 원인과 타입 검사·린트·빌드 설정은 미확인 또는 미구성이다. 새 감시 설정의 값은 기존 동작이라고 단정하지 않으며, 이 Spec이 새로 정한 활동 정지 상한 480~600초(기본 600초)와 단계별 재기동 기본 예산 1을 구현 계획에서 설정 표면과 함께 문서화한다.
