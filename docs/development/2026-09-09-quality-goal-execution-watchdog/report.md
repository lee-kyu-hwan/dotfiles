# Quality Goal Report

- Task ID: 20260909T012111Z-85-quality-goal-의-codex-exec-호출-경로에-실행-감-5edbef6a
- Mode: standard
- Status: NEEDS_REDESIGN (코드 리뷰 3라운드 소진, 통과 게이트 미달)
- Created: 2026-09-09
- Updated: 2026-09-10
- Source goal: #85 quality-goal 의 codex exec 호출 경로에 실행 감시·회수 계약(timeout·무응답 감지·시작 확인·부분 결과 보존·소유 프로세스 정리·재시도 예산)을 추가한다

## Classification

선택 모드: **standard** (사용자 명시 `--mode=standard`, 하향 확정).

위험 스캔에서 strict 트리거 2건이 실재했다.

1. **파괴적 연산** — 범위 6번이 pid 트리 기준 프로세스 종료다. 이 저장소는 여러 세션이 동시에 `codex exec` 를 돌리므로 오종료는 타 세션 실행을 죽인다.
2. **동시성 정확성** — 범위 1·2·4번은 자식 정상 종료·결과 기록과 감시자 정지 판정 사이의 경합이다.

하향 근거는 난도가 아니라 **규모**였다. #42 4차(992행·요구 66·AC 86)와 #70 1차(715행·요구 69·AC 113)가 규모로 중단됐고 축소 재실행은 통과했다. strict 산출물 증가가 더 큰 위험으로 판단됐다.

하향 조건으로 strict 가 주려던 안전을 **요구사항·AC 로 이관**했다: pid 소유권 음성 대조(회수·수거 양쪽), 종료-완주 경합 해소 순서, 회수 전 부분 결과 선보존. 라벨 `enhancement`/`quality-goal`/`P3-low` 는 모드를 낮추지 않았다.

## Review history

### Spec — 3라운드, 최종 PASS

| 라운드 | 점수 | 결과 |
|---|---|---|
| 1 | 72 | REVISE. 블로커 3건 — 범위 (4)·(7) 결측, `EXECUTION_FAILED` 가 저장소에 부재 |
| 2 | 81 | REVISE. 블로커 1건 `SPEC-008` — 결과 파일이 자식 종료보다 먼저 보이면 성공 실행이 전부 실패로 판정 |
| 3 | 93 | **PASS**, 블로커 0 |

최종 Spec: 요구 20건(`R1.1`~`R9.5`) / AC 38건 / digest `163d1502…0ac40`.

### Plan — 1라운드, PASS

| 라운드 | 점수 | 결과 |
|---|---|---|
| 1 | 91 | **PASS**, 블로커 0, finding 5건(Medium 3·Low 2) |

최종 Plan: 태스크 T1~T5 / 검증 명령 `CMD-1`~`CMD-8` / digest `4a24736e…3abab1`. 2026-09-10 승인.

### Code — 3라운드 소진, 미통과

| 라운드 | 점수 | 결과 |
|---|---|---|
| 1 | 58 | REVISE. 블로커 4건 `CODE-001`~`004` |
| 2 | 79 | REVISE. 블로커 1건 `CODE-015` (라운드 2 수정이 들여온 회귀) |
| 3 | 76 | REVISE. 블로커 1건 `CODE-018` (라운드 3 수정이 들여온 회귀) |

**라운드 한도 소진으로 `NEEDS_REDESIGN`.**

## Blocking-finding resolutions

| finding | 해소 | 검증 |
|---|---|---|
| `SPEC-001` | `R9.1`·`R9.4` 신설(판정 행렬), `R6.2` 에 종료 코드·스키마 검증 필드 | 리뷰 r2 확인 |
| `SPEC-002` | `R9.2` 신설 — 예산 주체·범위·초기값·소진 시 정지 | 리뷰 r2 확인 |
| `SPEC-003` | 새 상태 값 신설 없이 기존 `BLOCKED_MODEL_UNAVAILABLE` 유지, 판별 다섯 사실만 기록 | `EXECUTION_FAILED` 0건 |
| `SPEC-008` | `R9.5` 신설(`EXIT_COLLECT_WAIT_SECONDS = 5`), `R9.1` 미확정 판정 정정 | 리뷰 r3 확인 |
| `CODE-001` | 래퍼 `--stdin-path` 옵션 + 래퍼 블록 넷에 `--stdin-path "$PROMPT_PATH"` | **변이 측정**: 전달 차단 시 실패, 복원 시 통과 |
| `CODE-002` | 다섯 사실 구체값 단언(두 변형) + 초기 예산 2 사례 | **변이 측정** 확인 |
| `CODE-003` | 미추적 아카이브·sha256·스트림 사본·보존↔SIGTERM 순서, 음성 픽스처 | **변이 측정** 확인 |
| `CODE-004` | `_capture_command` 가 git 비영 종료를 보존 실패로 처리 | **변이 측정** 확인 |
| `CODE-015` | 픽스처가 일회용 `git init` 체크아웃 사용, `shutil.rmtree` 로 부모까지, `tearDownModule` 잔재 검사 | **변이 측정** 확인 |
| `CODE-010` | `report_payload` 23키 정확 집합, `abort`·`reap` 별도 객체 | **변이 측정** 확인 |
| `CODE-016` | `git rev-parse --verify` 로 자식 기동 전 해석, 래퍼 블록 출처 산문 | 리뷰 r3 확인 |
| `CODE-017` | 죽은 `tempfile` import·`first_activity` 제거 | 리뷰 r3 확인 |
| `CODE-018` | **미해소 — 종료 사유** | — |

## Plan approval

- Approval timestamp: 2026-09-10T08:21:14Z
- Plan digest: `4a24736ea86bc70b91931ccda9eda927bf1a166f2923fe46534036549d3abab1`

## Changed files

| 경로 | 변경 |
|---|---|
| `dot_claude/skills/quality-goal/scripts/execution_watchdog.py` | 신규. 감시 래퍼(전송 계층) |
| `dot_claude/skills/quality-goal/tests/test_execution_watchdog.py` | 신규. 프로세스 픽스처 56건 |
| `dot_claude/skills/quality-goal/SKILL.md` | `version` 5.1.0→5.2.0, `### Execution watchdog` 절 신설 (+52/-1, 452행) |
| `dot_claude/skills/quality-goal/references/model-routing.md` | 래퍼 사용 블록 4개 추가 (기존 4개 `codex exec` 블록 불변) |
| `dot_claude/skills/quality-goal/templates/report.md` | 실행 기록·재시작 예산 필드 렌더링 |
| `dot_claude/skills/quality-goal/tests/test_content_contracts.py` | 계약 추가 + 버전 리터럴 `5.1.0`→`5.2.0` |
| `docs/development/2026-09-09-quality-goal-execution-watchdog/` | Spec·Plan·이 보고서 |

검토 전용 파일(`quality_state.py`, `assert_preserved_sections.py`, `assert_tests_preserved.py`, `evals/evals.json`, `docs/quality-goal-maintenance.md`) 전부 미변경. 범위 밖 변경 0건. 사전 dirty 경로 0건.

**커밋·머지·`chezmoi apply` 는 실행하지 않았다.** 모든 변경은 커밋되지 않은 워크트리 상태다.

## Verification evidence

기준 커밋 `9ff32a30c9498df007ec5dfa558a442cc7841be1`. 최종 지문 `f0d58bc37543de2005c45b3696614e3d4c023778693505fba169e90bbf6bb546`.
인터프리터 `/opt/homebrew/bin/python3` (3.14.7), `PYTHONDONTWRITEBYTECODE=1`.
**모든 명령을 오케스트레이터가 직접 실행했다.** Codex 자기 보고는 근거로 쓰지 않았다.

| 명령 | 종료 코드 | 근거 |
|---|---|---|
| CMD-1 (3회) | 0 / 0 / 0 | `Ran 56 tests` `OK` — 6.586s / 6.539s / 6.525s |
| CMD-2 | 0 | `Ran 104 tests` `OK` |
| CMD-3 | 0 | `보존 대상 절 불변` |
| CMD-4 | 0 | `기존 테스트 보존` |
| CMD-5 | 0 | `Ran 449 tests` `OK` (기준선 385 → 442 → 448 → 449) |
| CMD-6 | 0 / 1 | 양성 대조 exit 0, 음성 대조 exit 1 |
| CMD-7 | 0 | `SKILL.md` 452행 < 500, 코드 펜스 0개 |
| CMD-8 | 0 | 설정 파일 0개 |

### 미구성 항목 — 통과로 기록하지 않는다

`CMD-8` 이 `pyproject.toml`·`setup.cfg`·`tox.ini`·`.flake8`·`ruff.toml`·`mypy.ini`·`package.json`·`tsconfig.json`·`Makefile`·`justfile` 을 저장소 루트에서 탐색했고 **출력이 없다.**

- 타입 검사: **미구성** · 린트: **미구성** · 빌드: **미구성**
- E2E: 이 변경(스킬 스크립트·문서·테스트)에 해당 없음

### 변이 측정 (자기 보고를 증거로 쓰지 않기 위한 조치)

"테스트가 통과한다" 는 증거가 아니다. **오케스트레이터가 사본에서 직접** 결함을 되살려 측정했다.

라운드 2 (`mutation-transcript-r2.md`) — 5건 전부 대상 테스트를 죽였고 복원 시 통과:
stdin 전달 차단 / git 종료 코드 확인 제거 / 미추적 수집 제거 / 다섯 사실 중 하나 미기록 / 이름·명령줄 매칭 종료 도입.

라운드 3 (`mutation-transcript-r3.md`) — 4건 전부 확인:
픽스처 루트를 스킬 트리로 되돌림 / 정리에서 leaf 만 제거 / payload 키 제거 / `reap` 을 `abort` 와 동일 객체로.

부수 관측 둘:
- 변이 1의 실패는 60.5초, 복원 후 1.07초. 자식이 stdin 대기로 블록된 시간 차이가 프롬프트 전달의 증거다.
- 변이 준비 중 `timeout 90` 이 `command not found` 였다. **macOS 에 `timeout` 이 없다** — `R2.2`·`AC-33` 이 Python subprocess 로 상한을 강제하기로 한 이유가 실측으로 재확인됐다.

### 잔재 검사 — `git status` 에 의존하지 않는 방법

라운드 2에서 `git status --porcelain` 이 스킬 소스 트리에 쌓인 **빈 디렉터리 1158개를 구조적으로 못 봤다.** git 이 빈 디렉터리를 추적하지 않기 때문이다. 최종 상태는 파일 시스템을 직접 훑어 확인했다.

```
find dot_claude/skills/quality-goal -name '.claude' -type d   → 0
find dot_claude/skills/quality-goal -type d -empty            → 0
find dot_claude/skills/quality-goal -name '.watchdog-*'       → 0
result.json                                                   → 없음
grep -c 'watchdog preservation fixture' SKILL.md              → 0
```

## Codex 실행 감시 기록 (이 워크플로 자체)

이 작업이 `codex exec` 를 쓰므로 모든 호출에 wall-clock 상한 + events 8분 정지 감시 + 시작 확인을 걸었다.

| 사건 | 관측 |
|---|---|
| `plan-author-r1c` | **`events_stalled` 회수** (exit 125, 1354초). 모델이 최종 메시지까지 낸 뒤 정지, 결과 파일 미생성. 보존 먼저 → 소유 그룹만 종료 순서로 동작, 잔류 0건 |
| `readiness-spec-r2f` | **머신 재부팅으로 중단**. 감시 기록에 pid/pgid 가 남아 사후 조회 가능, 잔류 0건, 결과 없어 무효 처리 후 재실행 |
| `impl-r2` | **모델 용량 초과** (`Selected model is at capacity`, exit 1). 무단 대체 없이 사용자 승인을 받아 같은 모델로 재시도 |

**회수 사건이 이 작업의 요구사항을 실증했다.** `plan-author-r1c` 회수 시 오케스트레이터의 임시 하네스가 만든 보존 번들의 `git-diff-stat.txt` 가 **0바이트**였다 — `git diff --stat` 이 미추적 파일을 빼기 때문이다. readiness 가 `READY-03` 으로 예측한 결함이 실제로 관측됐고, 최종 구현은 `git diff --binary` + `--cached` + `git ls-files --others` 로 이를 피한다.

## Remaining advisory findings

| finding | 심각도 | 상태 |
|---|---|---|
| `CODE-018` | **High** | **미해소 — 종료 사유.** 픽스처 루트가 고정 `/private/tmp/.claude/quality-state` 로 옮겨져 `AC-2` 의 "`/tmp` 아래에 만들지 않음" 을 위반. `test_..._not_tmp` 가 정반대를 단언 |
| `CODE-019` | Medium | preflight 래퍼 블록이 `--stdin-path "$PROMPT_PATH"` 를 넘기는데 preflight 는 프롬프트를 argv 로 받는다. `$PROMPT_PATH` 미설정 시 `IsADirectoryError` 가 잡히지 않는다 |
| `CODE-005` | Medium | 경합 픽스처가 경합을 결정적으로 만들지 않는다 |
| `CODE-008` | Medium | 정지한 preflight 의 신호 기록을 단언하는 테스트가 없다 |
| `CODE-012` | Medium | 주입 시계가 `_signal_owned_group` 에만 적용, `run_execution` 픽스처는 실시간 여유 의존 |
| `PLAN-001`·`002`·`003`·`004`·`005` | Medium/Low | Plan 승인 시 열어 둔 자문 항목. 구현 프롬프트에 제약으로 실어 대응했다 |
| `SPEC-010` | Low | Spec 추적표 `R9.4` 행의 `CMD-2` 를 뒷받침하는 AC 부재. Plan 단계에서 대응 |

## 후속 과제 후보

1. **`CODE-018` 수정** — 리뷰어 판단으로 두 줄 수정이다. 픽스처 루트를 스킬 트리도 고정 `/tmp` 도 아닌 곳(예: 저장소 루트 `.claude/quality-state/`, `.gitignore:25` 가 이미 무시)으로 옮기고, `AC-2` 의 `/tmp` 부재 단언을 복원하며, `tearDownModule` 잔재 검사를 현재 실행의 루트로 한정한다.
2. **중단된 실행의 재개 인계** — Spec 비목표. `state.json` 재개 의미론 변경이 필요하다. 이번에 정한 실행 기록 필드가 기반이다.
3. **#49-C** — 결과 손상과 모델 미가용이 같은 복구 경로를 쓰는 문제의 분리. 바이트 보존 대상 `### Implementation` 절을 고쳐야 하므로 범위 밖이었다.
4. **readiness 체크리스트의 한계** — Spec 라운드 1·2 모두 `READY`/100 을 주고 범위 결측과 요구사항 모순을 놓쳤다. 범위 항목 매핑을 체크리스트에 넣을지 검토할 만하다.
5. **실제 `codex exec` 자식으로 래퍼 전 구간 검증** — 리뷰 3라운드 모두 `verified: false` 로 남긴 항목이다. 저장소의 어떤 호출자도 아직 래퍼를 라우팅 경로에 연결하지 않았고, 네 호출 형태는 Python 대역 자식으로만 증명됐다.

## Final status

- Status: `NEEDS_REDESIGN`
- Machine-readable reason: 코드 리뷰 라운드 한도(3) 소진, 통과 게이트 미달. 잔존 블로커 `CODE-018`
