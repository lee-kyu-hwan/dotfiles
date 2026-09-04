# Quality Goal Specification

- Task ID: 20260904T051905Z-43-record-review의-자동-터미널-전이-때문에-보고서-등록-시-6eea40da
- Mode: standard
- Status: SPEC_REVIEW (round 3)
- Created: 2026-09-04T05:19:05Z
- Updated: 2026-09-04T05:55:00Z
- Source goal: #43 record-review의 자동 터미널 전이 때문에 보고서 등록 시점이 존재하지 않는 결함을 고친다.

## Problem and context

`quality-goal` 스킬은 모든 종결 경로에서 보고서를 상태 파일에 등록하도록 계약한다. 이 계약은 두 곳에 적혀 있고 문구가 약간 다르다. `SKILL.md:121`(Stage table)은 전이 대상을 `the terminal state`로 뭉뚱그리고, `SKILL.md:240-248`(Terminal 절)은 네 상태를 열거한다. 순서 요구는 양쪽이 같다. Terminal 절의 문구는 다음과 같다:

> Render report.md from templates/report.md and register it with `set-artifact --kind report` (absolute path) **BEFORE** transitioning into COMPLETED, BLOCKED, NEEDS_REDESIGN, or CANCELLED

그러나 `scripts/quality_state.py`의 `record_review()`는 리뷰 라운드를 기록한 뒤 두 조건에서 **스스로** 터미널 상태로 전이한다.

| 위치 | 조건 | 결과 |
|---|---|---|
| `scripts/quality_state.py:662-665` | 이번 라운드의 blocker ID가 이전 라운드에도 있었음 | `stage = NEEDS_REDESIGN`, `status_reason = RECURRING_BLOCKING_FINDING:<id>` |
| `scripts/quality_state.py:666-670` | `expected_round == ROUND_LIMITS[artifact]`이고 `verdict != "PASS"` 또는 blocker 존재 | `stage = NEEDS_REDESIGN`, `status_reason = REVIEW_LIMIT_EXHAUSTED:<artifact>` |

전이 후에는 `set_artifact()`가 첫 줄에서 호출하는 `_require_active()`(`scripts/quality_state.py:108-113`)가 `TransitionError("terminal state is immutable: <stage>")`를 던진다. CLI는 이를 종료 코드 3으로 매핑한다(`scripts/quality_state.py:1349-1351`).

결과적으로 **오케스트레이터가 계약된 순서를 지킬 수 있는 시점이 존재하지 않는다.** 보고서 파일은 문서 디렉터리에 작성되지만 `state.json`의 `artifacts.report`는 `null`로 남고, 상태 파일만 보는 후속 세션은 보고서를 찾을 수 없다.

### 실측 재현 (2026-09-04, 커밋 4fd0899fdc8efa32f78f9346eac5d730b0547ac6 기준)

격리된 임시 Git 저장소에서 이 저장소의 `scripts/quality_state.py`를 CLI로 구동해 두 경로를 모두 재현했다. 재현 스크립트와 전체 출력은 이 문서와 함께 제출되는 증거 파일 `evidence/repro-43.txt`에 있다.

```
A) REVIEW_LIMIT_EXHAUSTED (spec 3라운드, 매 라운드 서로 다른 blocker)
  round 1: exit=0 / round 2: exit=0 / round 3: exit=0
  stage=NEEDS_REDESIGN status_reason=REVIEW_LIMIT_EXHAUSTED:spec artifacts.report=None
  set-artifact --kind report: exit=3 error: terminal state is immutable: NEEDS_REDESIGN
  FINAL artifacts.report=None
  extra round attempt: exit=2 error: review for spec requires stage SPEC_REVIEW, got NEEDS_REDESIGN

B) RECURRING_BLOCKING_FINDING (spec 2라운드, 같은 blocker 반복 — 한도 3 미도달)
  round 1: exit=0 / round 2: exit=0
  stage=NEEDS_REDESIGN status_reason=RECURRING_BLOCKING_FINDING:SPEC-A artifacts.report=None
  set-artifact --kind report: exit=3 error: terminal state is immutable: NEEDS_REDESIGN
  FINAL artifacts.report=None
  extra round attempt: exit=2 error: review for spec requires stage SPEC_REVIEW, got NEEDS_REDESIGN
```

두 경로 모두 `artifacts.report`가 `null`로 남는다. 경로 B는 라운드 한도(spec=3)에 도달하지 않은 라운드 2에서 종결하므로, 한도 소진과는 독립된 두 번째 진입점이다.

### 기준선 스위트

변경 전 스위트 실행 결과는 증거 파일 `evidence/baseline-suite.txt`에 있다: `Ran 229 tests ... OK`.

### 실전 재현 이력

이슈 #43의 원문은 증거 파일 `evidence/issue-43.json`에 있다. 본문·코멘트가 기록한 6회(2026-08-27~28: #28/#35 1차·2차, #45, #1320, #42)에 사용자가 이 실행에서 보고한 2026-09-03 #28/#35 3차를 더해 **총 7회 재현**됐다. 게이트 실패로 끝난 모든 실행에서 보고서 포인터가 유실됐다. 7회째는 이슈에 기록돼 있지 않고 사용자 진술이 유일한 근거다.

성공 경로(`COMPLETED`)는 오케스트레이터가 `transition`을 직접 호출하므로 영향이 없다. E2E와 초기 실전에서 이 결함이 보이지 않았던 이유다.

### 인접 경로의 현황

같은 결함 계열에 속하는 다른 종결 경로를 조사했다.

| 경로 | 함수 | 현재 동작 | #43 영향 |
|---|---|---|---|
| `REVIEW_OUTPUT_INVALID` | `record_review_validation_failure()` (`scripts/quality_state.py:770-771`) | 2회째 무효 응답에서 스스로 `stage = BLOCKED` | **동일하게 영향받음** — 이슈 #43 본문이 "같은 방식으로 전이하므로 동일할 것으로 보인다"고 예측한 경로 |
| `REVIEWER_UNVERIFIED_PERSISTS` | `record_review_unverified()` (`scripts/quality_state.py:716-717`) | `TransitionError`만 던지고 stage는 `SPEC_REVIEW` 유지 | **영향 없음** — 오케스트레이터가 전이를 호출한다. `tests/test_quality_state.py:1211-1233`이 "비터미널 확인 → report 등록 → BLOCKED 전이" 순서를 이미 검증한다 |

## Goals

1. 모든 자동 터미널 전이 경로에서 `set-artifact --kind report`가 성공해 `state.json`의 `artifacts.report`가 채워진다.
2. 자동 전이가 제공하는 **결정적 종결**(오케스트레이터가 전이를 빼먹어도 워크플로가 비터미널 상태에 머무르지 않음)을 보존한다.
3. 한도 소진·재발 감지 이후 추가 리뷰 라운드가 거부되는 가드를 보존한다.
4. `SKILL.md`가 규정하는 순서 계약과 CLI의 실제 동작 사이의 모순을 제거한다.
5. 기존 229건 테스트 스위트가 **수정 없이** 전부 통과한다. 유일한 예외는 R6이 요구하는 버전 상수 한 줄(`tests/test_content_contracts.py:797`)이다.

## Non-goals

1. **#59(digest 시점), #55, #60을 다루지 않는다.** 같은 파일(`scripts/quality_state.py`)을 만지더라도 해당 이슈의 동작은 변경하지 않는다.
2. 라운드 한도 값(`ROUND_LIMITS = {"spec": 3, "plan": 2, "code": 3}`) 조정은 범위 밖이다(#53 소관).
3. 리뷰 게이트 판정 로직, 루브릭, 리뷰어 계약은 변경하지 않는다.
4. **작업 범위는 PR 생성까지다.** 작업 브랜치 `43-fix/quality-goal-report-registration`에 커밋하고 원격에 푸시하는 것은 PR을 열기 위해 필요하므로 허용된다. 금지되는 것은 다음이다: `main`으로의 머지, 릴리스·태그 생성, 그리고 **`chezmoi apply`를 포함한 모든 배포 행위**. 배포본 `quality-goal`을 다른 세션이 실행 중일 수 있으므로 배포 시점은 사용자가 결정한다. AC-16이 이 경계를 검증한다.
5. `state.json`의 `schema_version`을 올리지 않는다. 이 변경은 상태 파일 스키마에 필드를 추가하거나 제거하지 않는다.
6. 보고서 **내용**의 품질 규칙(`templates/report.md`의 섹션 구성)은 변경하지 않는다.

## Requirements

### R1 — 터미널 상태에서 report 아티팩트 등록 허용

`set_artifact(state, kind, path)`는 `kind == "report"`인 호출에 한해 터미널 상태(`COMPLETED`, `BLOCKED`, `NEEDS_REDESIGN`, `CANCELLED`)에서도 성공해야 한다. 나머지 세 kind(`spec`, `plan`, `compact_plan`)는 터미널 상태에서 기존과 동일하게 `TransitionError`(종료 코드 3)로 거부되어야 한다.

### R2 — 검증 순서의 규범적 고정

`set_artifact()`의 검증은 **정확히 다음 순서**로 수행되어야 한다. 이 순서는 기존 동작 보존을 위한 필수 요건이며 구현 재량 사항이 아니다.

| 단계 | 검사 | 실패 시 |
|---:|---|---|
| 1 | `_require_state(state)` — state가 dict인지 | `StateError` |
| 2 | **`kind`가 문자열 `"report"`와 정확히 같지 않으면** `_require_active(state)` 호출 | `TransitionError` |
| 3 | `kind`가 `_ARTIFACT_KEYS` 원소인지 | `StateError` |
| 4 | `path`가 비어 있지 않은 `str`/`PathLike`인지 | `StateError` |
| 5 | `path`가 존재하는 정규 파일인지 | `StateError` |
| 6 | `state["artifacts"]`가 dict인지 | `StateError` |

2단계를 `kind` 멤버십 검사(3단계)보다 **앞에** 두는 것이 요건의 핵심이다. 그래야 터미널 상태에서 `_ARTIFACT_KEYS` 밖의 `kind`가 들어와도 기존과 동일하게 `TransitionError`로 거부된다. 즉 이 변경으로 오류 종류가 달라지는 입력 조합은 **`(터미널 상태, kind == "report")` 하나뿐이며**, 그 조합에서만 이전의 `TransitionError`가 성공 또는 경로 관련 `StateError`로 바뀐다.

### R3 — 자동 전이 동작의 보존

`record_review()`의 두 자동 전이 분기(`scripts/quality_state.py:662-670`)와 `record_review_validation_failure()`의 `BLOCKED` 전이(`scripts/quality_state.py:770-771`)는 **변경하지 않는다.** 전이 시점, `status_reason` 문자열, 라운드 기록 내용이 현행과 동일해야 한다.

### R4 — 라운드 재시도 가드의 보존

터미널 전이 이후 `record-review`를 다시 호출하면 기존과 동일하게 거부되어야 한다. 현재 이 거부는 `record_review()`의 stage 검사(`scripts/quality_state.py:575-579`)가 수행하며 `StateError("review for <artifact> requires stage <stage>, got <terminal>")`(종료 코드 2)를 낸다.

### R5 — SKILL.md 순서 지시 추가 (이슈 #43의 (d)안)

`SKILL.md`의 `### Terminal` 절에 아래 두 문단을 추가한다.

**삽입 위치 제약(필수).** 기존 문장

> For every terminal outcome, render report.md from templates/report.md and register it with set-artifact --kind report (absolute path) BEFORE transitioning into COMPLETED, BLOCKED, NEEDS_REDESIGN, or CANCELLED.

은 **한 덩어리로 유지되어야 하며, 그 안에 어떤 텍스트도 삽입해서는 안 된다.** `tests/test_content_contracts.py:1296-1305`는 정규화된 본문에서 `render report.md from templates/report.md`와 `register it with set-artifact --kind report (absolute path) before transitioning into <터미널 상태명>` 사이의 간격을 **최대 180자**로 제한한다. 새 문단은 이 문장 전체보다 앞이나 뒤에 배치한다.

**추가할 규범 문장(축자).** 아래 두 문장이 `### Terminal` 절 본문에 그대로 포함되어야 한다. 줄바꿈 위치는 자유이나 단어 순서는 바꿀 수 없다.

- 문장 D1:
  `When the review you are about to record is expected to end the workflow, because it is the last allowed round without a PASS or it repeats a blocking finding ID from an earlier round, render report.md and register it with set-artifact --kind report before calling record-review, while the stage is still non-terminal.`
- 문장 D2:
  `Because record-review and record-review-error transition into NEEDS_REDESIGN or BLOCKED on their own, set-artifact --kind report is also accepted after the state is already terminal; register the report there when the terminal transition has already happened. No other artifact kind may be registered once the state is terminal.`

**Stage table 행의 동반 보정(필수).** `SKILL.md:121`의 Stage table 행은 같은 순서 계약을 축약해 서술한다. Terminal 절만 고치면 두 위치가 서로 다른 강도로 같은 계약을 말하게 되므로, 그 행 끝에도 아래 문장을 축자로 추가한다.

- 문장 D3:
  `When a helper has already transitioned automatically, register the report in the terminal state as the Terminal section describes.`

이 추가는 `tests/test_content_contracts.py:1296-1305`의 180자 윈도우에 영향을 주지 않는다. 해당 정규식은 전이 대상이 네 상태명 중 하나로 끝나는 문장에만 일치하는데 Stage table 행은 `into the terminal state`로 끝나므로 애초에 일치 대상이 아니며, `assertRegex`는 정규화된 본문 전체에서 검색하므로 Terminal 절의 일치가 그대로 유효하다.

### R6 — 버전 갱신

`SKILL.md`의 `version` 프론트매터를 `4.0.0`에서 `4.1.0`으로 올린다. CLI 동작 계약이 하위 호환으로 확장되므로(터미널 상태에서 report 등록 허용) minor 증가가 적절하며, 기존 호출자를 깨뜨리지 않으므로 major는 아니다. `tests/test_content_contracts.py:797`이 버전을 고정하므로 그 한 줄을 함께 갱신한다. 저장소 전체에서 이 두 곳 외에 스킬 버전이 고정된 위치는 없다.

### R7 — 계약 테스트 추가

사용자 필수 산출물이다. 아래 두 경로 각각에 대해, 리뷰 라운드 기록 → 자동 터미널 전이 → 보고서 등록 → 상태 확인의 전체 순서가 성립함을 검증하는 테스트를 추가한다.

- 한도 소진 경로(`REVIEW_LIMIT_EXHAUSTED`)
- 재발 감지 경로(`RECURRING_BLOCKING_FINDING`)

### R8 — 기존 스위트 무회귀

`python3 -m unittest discover -s tests` 실행 시 기존 229건이 전부 통과해야 하며(R6의 버전 상수 한 줄 갱신 외에 기존 테스트 본문을 수정하지 않는다), 추가된 테스트를 포함한 총 건수가 229건보다 커야 한다.

## Acceptance criteria

| # | 기준 | 검증 방법 |
|---|---|---|
| AC-1 | `record-review`가 `REVIEW_LIMIT_EXHAUSTED:<artifact>`로 자동 전이시킨 `NEEDS_REDESIGN` 상태에서 `set-artifact --kind report <절대경로>`가 종료 코드 0으로 성공하고, 이후 `state.json`의 `artifacts.report`가 그 경로와 같다 | spec·plan·code 세 artifact 각각에 대한 자동화 테스트. 최소 한 건은 CLI(subprocess)로 종료 코드와 `state.json` 내용을 확인한다 |
| AC-2 | `record-review`가 `RECURRING_BLOCKING_FINDING:<id>`로 자동 전이시킨 `NEEDS_REDESIGN` 상태에서 `set-artifact --kind report`가 종료 코드 0으로 성공하고 `artifacts.report`가 채워진다 | 자동화 테스트. 라운드 한도에 도달하지 않은 라운드에서 재발이 감지되는 사례를 반드시 포함한다. 최소 한 건은 CLI(subprocess)로 확인한다 |
| AC-3 | 네 터미널 상태(`COMPLETED`, `BLOCKED`, `NEEDS_REDESIGN`, `CANCELLED`) 전부에서 `set_artifact(state, "report", <존재하는 정규 파일>)`이 성공하고 `artifacts["report"]`가 그 경로 문자열이 된다 | 네 상태를 순회하는 자동화 테스트 |
| AC-4 | 네 터미널 상태 전부에서 `kind`가 `spec`, `plan`, `compact_plan`인 `set_artifact` 호출은 `TransitionError`로 거부되고 상태가 전혀 변경되지 않는다 | 상태 딥카피 비교를 포함한 자동화 테스트 |
| AC-5 | 터미널 상태에서 `kind == "report"`이지만 경로가 존재하지 않거나 디렉터리이거나 빈 문자열이면 `StateError`로 거부되고 상태가 변경되지 않는다 | 자동화 테스트 |
| AC-6 | **R2의 순서가 실제로 지켜진다**: 터미널 상태에서 `kind`가 `spec`이고 경로가 존재하지 않으면 `StateError`가 아니라 `TransitionError`가 발생한다. 터미널 상태에서 `_ARTIFACT_KEYS` 밖의 `kind`(예: `"unknown"`)도 `TransitionError`로 거부된다 | 기존 테스트 `tests/test_quality_state.py:1561-1583`이 **수정 없이** 통과하는 것으로 첫 조건을 검증한다(그 테스트가 `set_artifact(state, "spec", "missing-artifact.md")`를 정확히 이 조합으로 호출한다). 두 번째 조건은 신규 테스트로 검증한다 |
| AC-7 | `record_review()`가 자동 전이한 뒤 같은 artifact로 `record-review`를 다시 호출하면 종료 코드 2로 거부된다 | 한도 소진 경로와 재발 경로 각각에 대한 자동화 테스트 |
| AC-8 | `record_review()`와 `record_review_validation_failure()`의 전이 시점·`status_reason`·라운드 기록이 변경 전과 동일하다 | 해당 함수를 다루는 기존 테스트(`tests/test_quality_state.py:1430-1498` 포함)가 수정 없이 통과 |
| AC-9 | `record_review_validation_failure()`가 자동 전이시킨 `BLOCKED` 상태에서도 `set-artifact --kind report`가 성공한다 | 자동화 테스트 |
| AC-10 | 다른 active-only 변경 함수(`record_verification`, `invalidate_stale_verification`, `record_review_validation_failure`)는 네 터미널 상태 전부에서 여전히 `TransitionError`로 거부되고 상태가 변경되지 않는다 | 기존 테스트 `tests/test_quality_state.py:1561-1583`이 수정 없이 통과 |
| AC-11 | `SKILL.md`가 R5의 문장 D1·D2를 `### Terminal` 절에, 문장 D3을 Stage table 행에 축자로 포함한다 | `tests/test_content_contracts.py`에 추가하는 계약 테스트가 세 문장을 정규화 비교로 검사한다 |
| AC-12 | `tests/test_content_contracts.py:1296-1305`의 기존 계약 테스트(`BEFORE transitioning` 180자 윈도우)가 **수정 없이** 통과한다 | 기존 테스트 실행 |
| AC-13 | `SKILL.md`의 `version`이 `4.1.0`이고 프론트매터 계약 테스트가 통과한다 | 기존 테스트(값 한 줄 갱신 후) 실행 |
| AC-14 | 비터미널 상태에서의 `set_artifact` 동작(네 kind 전부, 정상·이상 입력 모두)이 변경 전과 동일하다 | 기존 테스트 `tests/test_quality_state.py:604-637`이 수정 없이 통과 |
| AC-15 | `python3 -m unittest discover -s tests` 결과가 `OK`이고 실행 건수가 229보다 크다 | 스위트 전체 실행 출력 |
| AC-16 | 범위 경계가 지켜졌다: (i) 작업 브랜치 `43-fix/quality-goal-report-registration`의 HEAD 커밋이 `origin/main`에서 도달 불가능하다(즉 이 작업이 `main`에 머지되지 않았다), (ii) 생성된 PR이 열린 상태이고 머지되지 않았다, (iii) 이 실행의 명령 기록에 `chezmoi apply` 호출이 없다 | (i) `git merge-base --is-ancestor <branch HEAD> origin/main`이 **비영 종료 코드**를 반환한다, (ii) `gh pr view --json state,mergedAt`이 `state=OPEN`, `mergedAt=null`, (iii) 실행 명령 기록 검토. (i)에 `origin/main`의 절대 SHA를 고정하지 않는 이유: 작업 중에도 무관한 PR이 `main`에 머지될 수 있다. 실제로 이 Spec 작성 시점에 `origin/main`은 브랜치 base `4fd0899fdc8efa32f78f9346eac5d730b0547ac6`가 아니라 그 후손인 `e61cee8492ea0d6a2bee027474b3b7609322fb1a`였다(무관한 PR #32 머지). 도달 가능성 검사는 이런 무관한 진행에 영향받지 않고 "이 작업이 머지됐는가"만 측정한다 |

## Architecture

### 관련 구성요소

| 구성요소 | 파일 | 책임 |
|---|---|---|
| 상태 머신 헬퍼 | `dot_claude/skills/quality-goal/scripts/quality_state.py` | 상태 파일 읽기·쓰기, 전이 검증, 리뷰 라운드 기록, 아티팩트 바인딩 |
| 계약 문서 | `dot_claude/skills/quality-goal/SKILL.md` | 오케스트레이터가 따르는 절차와 순서 규정 |
| 상태 머신 테스트 | `dot_claude/skills/quality-goal/tests/test_quality_state.py` | 함수·CLI 레벨 동작 검증 |
| 문서 계약 테스트 | `dot_claude/skills/quality-goal/tests/test_content_contracts.py` | `SKILL.md`·레퍼런스 문구가 규정을 담고 있는지 검증 |

`dot_claude/` 접두사 파일은 chezmoi가 `~/.claude/`로 배치한다. 이 작업은 소스만 수정하고 배치는 수행하지 않는다.

### 결정: (b) 좁은 터미널 예외를 택하고 (d)를 병행한다

이슈 #43은 네 안을 제시한다(원문: `evidence/issue-43.json`). 사용자 지시에 따라 (a)와 (b)를 비교했다.

#### (a) `record_review`의 자동 전이 제거

`record_review()`가 stage를 바꾸지 않고 한도 소진·재발 사실만 반환하면, 오케스트레이터가 그 사실을 읽고 보고서를 등록한 뒤 명시적으로 `transition`한다. `ALLOWED_TRANSITIONS`(`scripts/quality_state.py:20-67`)는 `SPEC_REVIEW`, `PLAN_REVIEW`, `CODE_REVIEW`에서 `NEEDS_REDESIGN`으로의 전이를 이미 허용하므로 전이 자체는 가능하다.

그러나 실측 결과 두 가지 비용이 확인됐다.

1. **재시도 가드를 새로 만들어야 한다.** 현재 "한도 소진 후 다음 라운드 시도 거부"는 stage 검사가 수행한다. 재현 A·B 모두 거부 사유가 `review for spec requires stage SPEC_REVIEW, got NEEDS_REDESIGN`이었다. 자동 전이를 제거하면 stage가 `SPEC_REVIEW`로 남는다. 한도 소진 경로는 `expected_round > ROUND_LIMITS[artifact]` 검사(`scripts/quality_state.py:603-604`)가 여전히 막지만, **재발 경로는 막지 못한다**. 재현 B는 한도 3인 spec의 라운드 2에서 종결했고, 그 상태에서 라운드 3은 `expected_round = 3 ≤ 3`이므로 통과한다. 따라서 (a)는 `state.json`에 "종결 대기" 플래그를 추가하고 `record_review()` 초입에서 검사하는 새 가드를 요구한다. 즉 (a)는 제거가 아니라 **제거 후 재구현**이며, Non-goal 5(스키마 무변경)와도 충돌한다.
2. **새 결함 계열을 연다.** 오케스트레이터가 전이 호출을 빠뜨리면 워크플로가 리뷰 단계에 무기한 머무른다. 이슈 #43 본문 자신이 이 위험을 지적하며 가드 유지를 조건으로 단다. 결정적 종결(Goal 2)이 약해진다.

#### (b) 터미널 상태에서 `set-artifact --kind report`만 허용

`set_artifact()`의 `_require_active()` 호출을 `kind == "report"`에 한해 건너뛴다(R2의 2단계).

| 항목 | 평가 |
|---|---|
| 변경 범위 | `set_artifact()` 한 함수의 진입 검사 (최소) |
| 결정적 종결 | 자동 전이가 그대로 유지되므로 보존 |
| 재시도 가드 | stage 검사가 그대로 유지되므로 보존 (신규 가드 불필요) |
| 인접 경로 | `record_review_validation_failure()`의 `BLOCKED` 자동 전이도 **함께 해소**된다. (a)는 `record_review()`만 고치므로 이 경로가 남는다 |
| 불변식 | "터미널 상태 불변"이 report 한 kind에 대해서만 뚫린다. 나머지 세 kind와 `record_verification`·`invalidate_stale_verification`·`record_review_validation_failure`는 그대로 막힌다(AC-4, AC-10) |
| 기존 테스트 | `tests/test_quality_state.py:1561-1583`의 불변성 테스트는 `set_artifact`를 `kind="spec"`으로만 호출하므로, R2의 순서를 지키면 수정 없이 통과한다(AC-6) |

#### 채택

**(b)를 채택하고 (d)를 `SKILL.md` 지시로 병행한다.**

근거:

1. 계약이 실제로 요구하는 것은 "보고서 포인터가 상태에 남는다"이고, "전이보다 먼저"는 그 목적을 달성하기 위한 수단이었다. (b)는 목적을 직접 달성하면서 수단의 제약만 완화한다.
2. (a)는 결함 하나를 고치는 대가로 결정적 종결을 포기하고 새 가드와 상태 스키마 변경을 요구한다. 최근 작업(#44/#37/#38, 커밋 98f41b1)이 "no-PASS 결정적 강제"를 넣은 방향과 반대로 간다.
3. (b)는 `REVIEW_OUTPUT_INVALID` 경로를 추가 코드 없이 함께 해소한다. 이슈 #43 본문이 예측했으나 어떤 안도 명시적으로 다루지 않은 경로다.
4. (d)는 정상 경로에서 `BEFORE transitioning` 순서를 유지시켜 설계 의도를 문서상으로도 보존한다. 2026-09-04 #42 3차 실행이 (d)만으로 보고서 포인터를 살린 실적이 있다(사용자 진술). (b)가 (d)의 사각(종결을 예측하지 못하는 경로)을 메우므로, 둘을 합치면 근본 해소가 된다.

기각한 (c)는 `BEFORE transitioning` 계약 문구를 삭제해 설계 의도를 포기하므로 채택하지 않는다.

### 예외의 범위를 좁히는 방식

터미널 예외를 `kind == "report"` 조건 하나로 좁힌다. 아래 두 가지 추가 축소안을 검토했으나 채택하지 않는다.

- **`artifacts.report`가 `null`일 때만 허용**: 터미널 이후 보고서 교체를 막아 불변성을 더 보존한다. 그러나 종결 직전에 (d)로 선등록한 뒤 보고서를 보강하는 정상 흐름을 막고, 실패 시 진단이 어려운 조건부 거부를 낳는다. 예외 조건이 두 개가 되어 검증 표면도 넓어진다. 채택하지 않는다.
- **`NEEDS_REDESIGN`·`BLOCKED`에서만 허용**: `CANCELLED`도 오케스트레이터가 직접 전이하므로 이론상 불필요하지만, 네 터미널 상태를 다르게 취급하면 규칙이 상태별로 갈라진다. 단일 규칙("report는 언제나 등록 가능")이 서술과 검증 모두 단순하다. 채택하지 않는다.

## Interfaces and data flow

### 변경되는 인터페이스

`set_artifact(state: dict, kind: str, path: str | PathLike) -> dict`

아래 표는 R2의 순서를 전제로 한 입력 조합별 결과다. 각 행은 상호 배타적이며, 위에서 아래로 먼저 일치하는 행이 적용된다.

| # | 입력 조합 | 변경 전 | 변경 후 |
|---:|---|---|---|
| 1 | `stage` 비터미널 — `kind`·`path` 무관 | 기존 검증 결과 | **동일** (성공 또는 `StateError`) |
| 2 | `stage` 터미널, `kind != "report"` — `path` 유효성 무관 | `TransitionError` (코드 3) | **동일** |
| 3 | `stage` 터미널, `kind == "report"`, `path`가 존재하는 정규 파일 | `TransitionError` (코드 3) | **성공** — `artifacts["report"] = str(path)`, `updated_at` 갱신 |
| 4 | `stage` 터미널, `kind == "report"`, `path`가 빈 값·비존재·디렉터리 | `TransitionError` (코드 3) | `StateError` (코드 2), 상태 무변경 |

행 2가 행 4보다 위에 있다는 점이 R2 2단계의 귀결이다. 따라서 `(터미널, kind="spec", 존재하지 않는 경로)`는 행 2에 걸려 `TransitionError`가 되며, `tests/test_quality_state.py:1561-1583`이 수정 없이 통과한다(AC-6). 오류 종류가 달라지는 조합은 행 3과 행 4, 곧 `kind == "report"`인 경우뿐이다.

### 데이터 흐름 (종결 경로)

```
[예측 가능 경로 — (d) 적용, SKILL.md 문장 D1]
  리뷰 JSON 수신 → 종결 예상 판정 → report.md 렌더
    → set-artifact --kind report   (stage: SPEC_REVIEW, 비터미널)  ✅ 기존에도 성공
    → record-review                 (자동 전이 → NEEDS_REDESIGN)

[예측 불가 경로 — (b)가 메움, SKILL.md 문장 D2]
  리뷰 JSON 수신 → record-review    (자동 전이 → NEEDS_REDESIGN)
    → report.md 렌더
    → set-artifact --kind report   (stage: NEEDS_REDESIGN, 터미널)  ✅ 변경 후 성공
```

`state.json`의 필드 구성은 변하지 않는다. `artifacts.report`가 `null` 대신 경로 문자열을 갖게 되는 것이 유일한 관측 차이다.

## Failure behavior

| 실패 | 동작 | 근거 |
|---|---|---|
| 터미널 상태에서 존재하지 않는 report 경로 등록 | `StateError: artifact path is not a regular file: <path>` (종료 코드 2), 상태 무변경 | R2 5단계, AC-5 |
| 터미널 상태에서 `spec`/`plan`/`compact_plan` 등록 | `TransitionError: terminal state is immutable: <stage>` (종료 코드 3), 상태 무변경 | R2 2단계, AC-4 |
| 터미널 상태에서 알 수 없는 `kind` 등록 | `TransitionError: terminal state is immutable: <stage>` (종료 코드 3) — 기존과 동일 | R2 2단계, AC-6 |
| 터미널 전이 후 `record-review` 재호출 | `StateError: review for <artifact> requires stage <stage>, got <terminal>` (종료 코드 2) | R4, AC-7 |
| 오케스트레이터가 보고서 등록을 아예 빠뜨림 | 상태는 터미널로 남고 `artifacts.report`는 `null`. 이 결함의 원래 증상과 동일하나, 이제는 도구가 막는 것이 아니라 오케스트레이터의 누락이므로 같은 세션에서 재시도가 가능하다 | (b)의 특성 |
| `state.json`이 손상되어 `artifacts`가 dict가 아님 | 기존 `StateError: artifacts must be an object` 유지 | R2 6단계 |

되돌리기: 이 변경은 파일 수정만 수행하며 마이그레이션·백필·외부 부작용이 없다. `git revert` 또는 브랜치 폐기로 완전히 되돌릴 수 있다. 배포는 사용자가 `chezmoi apply`로 별도 결정한다.

## Security and risk

- **자격 증명 취급 없음.** 변경 대상 코드는 자격 증명을 읽거나 기록하지 않는다.
- **신뢰 경계 변화 없음.** `state.json`은 로컬 런타임 상태이며 `.gitignore:25`(`.claude/quality-state/`)로 저장소에서 제외된다. 프리플라이트에서 `git check-ignore -v`로 확인했다.
- **주 리스크 — 불변식 약화**: 터미널 상태가 완전히 불변이 아니게 된다. 완화: 예외를 `kind == "report"` 단일 조건으로 좁히고, AC-4가 나머지 세 kind의 거부를, **AC-10이 다른 active-only 변경 함수의 거부를**, AC-6이 검증 순서 자체를 각각 회귀 검증한다.
- **부차 리스크 — 배포본과 소스의 불일치**: 이 작업 자체가 배포본 `quality-goal` v4.0.0으로 구동되며, 다른 세션이 같은 배포본을 실행 중일 수 있다. 완화: `chezmoi apply`를 실행하지 않는다(Non-goal 4, AC-16). 소스만 수정하고 PR까지만 진행한다.
- **부차 리스크 — 이번 실행 자체가 #43을 밟음**: 이 실행이 종결될 때 자동 전이가 먼저 일어나면 보고서 등록에 실패한다. 완화: (d) 순서를 이 실행에 적용해 종결이 예상되면 보고서를 선등록한다. 우회를 사용한 경우 보고서에 그 사실을 기록한다.

## Test strategy

### 신규 테스트 (`tests/test_quality_state.py`)

| 대상 AC | 테스트 성격 |
|---|---|
| AC-1 | `record_review()`로 한도를 소진시켜 `NEEDS_REDESIGN`에 도달한 뒤 `set_artifact(..., "report", ...)` 성공과 `artifacts["report"]` 값을 확인. spec·plan·code 세 artifact 순회. 최소 한 건은 CLI(subprocess) |
| AC-2 | 같은 blocker ID를 두 라운드 연속 기록해 한도 미도달 상태에서 `RECURRING_BLOCKING_FINDING` 전이를 유발한 뒤 동일 검증. 최소 한 건은 CLI(subprocess) |
| AC-3 | 네 터미널 상태를 순회하며 report 등록 성공과 저장된 경로 값 확인 |
| AC-4 | 네 터미널 상태 × 세 kind(`spec`, `plan`, `compact_plan`)에서 `TransitionError`와 상태 무변경(딥카피 비교) 확인 |
| AC-5 | 터미널 상태에서 부적합 경로(없는 파일, 디렉터리, 빈 문자열)에 대한 `StateError`와 상태 무변경 확인 |
| AC-6 | 터미널 상태 × `kind="unknown"`에서 `TransitionError` 확인(순서 회귀 방지). 첫 조건은 기존 `tests/test_quality_state.py:1561-1583`이 담당 |
| AC-7 | 자동 전이 후 `record_review()` 재호출이 `StateError`로 거부됨을 두 경로 각각에서 확인 |
| AC-9 | `record_review_validation_failure()`를 2회 호출해 `BLOCKED`에 도달한 뒤 report 등록 성공 확인 |

AC-1·AC-2는 사용자가 지정한 필수 산출물이므로, 함수 레벨뿐 아니라 **CLI 레벨(subprocess)로도** 종료 코드와 `state.json` 내용을 검증한다. `tests/test_quality_state.py:2732` 이하에 기존 CLI 테스트 패턴이 있으므로 그 관례를 따른다.

### 신규 테스트 (`tests/test_content_contracts.py`)

| 대상 AC | 테스트 성격 |
|---|---|
| AC-11 | `SKILL.md` 본문 정규화 후 R5의 문장 D1·D2·D3이 축자로 포함되는지 확인 |

### 회귀 검증

| 대상 AC | 방법 |
|---|---|
| AC-6(첫 조건), AC-8, AC-10, AC-12, AC-14 | 해당 기존 테스트를 **수정 없이** 실행 |
| AC-13 | 프론트매터 계약 테스트를 버전 값 한 줄만 갱신해 실행 |
| AC-15 | `python3 -m unittest discover -s tests`가 `OK`, 실행 건수 > 229 |
| AC-16 | `git merge-base --is-ancestor <branch HEAD> origin/main`(비영 종료 기대), `gh pr view --json state,mergedAt`, 실행 명령 기록 검토 |

### 검증 명령

이 저장소는 `pytest`가 설치돼 있지 않다(`python3 -m pytest` 실행 시 `No module named pytest`). 표준 라이브러리 `unittest`를 사용한다.

```bash
cd dot_claude/skills/quality-goal
python3 -m unittest discover -s tests
```

린트·타입 검사·빌드 단계는 이 저장소에 구성돼 있지 않다. 구현 단계에서 저장소 증거와 함께 "not configured"로 기록하며, 통과로 기록하지 않는다.

## Decisions

| # | 결정 | 대안 | 근거 |
|---|---|---|---|
| D1 | 이슈 #43의 **(b)안** 채택 — 터미널 상태에서 `set-artifact --kind report`만 허용 | (a) 자동 전이 제거 | (a)는 재발 경로의 재시도 가드를 새로 만들어야 하고(실측 확인) 상태 스키마 변경을 요구하며 결정적 종결을 포기한다. (b)는 변경이 최소이고 `REVIEW_OUTPUT_INVALID` 경로까지 함께 해소한다 |
| D2 | 이슈 #43의 **(d)안** 병행 — `SKILL.md`에 선등록 순서 지시 추가 | (d) 생략 | 정상 경로에서 `BEFORE transitioning` 설계 의도를 유지한다. #42 3차 실행이 (d)만으로 보고서를 살린 실적이 있다. (b)가 (d)의 사각을 메운다 |
| D3 | (c)안 기각 — `BEFORE transitioning` 계약 문구를 유지 | 문구를 코드 동작에 맞춰 변경 | 설계 의도 포기이며, `tests/test_content_contracts.py:1296-1305`가 문구를 검증한다 |
| D4 | 예외 조건을 `kind == "report"` 단일 조건으로 유지 | `artifacts.report`가 `null`일 때만, 또는 특정 터미널 상태에서만 | 조건이 하나여야 서술·검증·진단이 단순하다. 추가 조건은 정상 흐름(선등록 후 보강)을 막는다 |
| D5 | `record_review()`와 `record_review_validation_failure()`를 변경하지 않음 | 두 함수도 함께 손봄 | R3. 변경 표면을 최소화하고 #59·#55·#60과의 충돌을 피한다 |
| D6 | `SKILL.md` 버전을 4.1.0으로 올림 | 유지, 또는 5.0.0 | CLI 동작 계약이 하위 호환으로 확장된다. 기존 호출자를 깨지 않으므로 major가 아니다 |
| D7 | 터미널 검사(`_require_active`)를 `kind` 멤버십 검사보다 **앞**에 두고 `kind == "report"`일 때만 건너뛴다 | `kind`·경로 검증을 모두 터미널 검사 앞으로 이동 | 후자는 `(터미널, kind="spec", 없는 경로)`에서 `StateError`를 내어 `tests/test_quality_state.py:1561-1583`을 깨뜨린다. 전자는 오류 종류가 바뀌는 조합을 `kind == "report"` 하나로 한정한다 |
| D8 | 검증에 `unittest`를 사용 | `pytest` | 저장소에 `pytest`가 없다(실측). 기존 테스트가 `unittest` 기반이다 |
| D9 | R5의 새 문단을 기존 계약 문장 **밖**(앞 또는 뒤)에 배치 | 문장 사이에 삽입 | `tests/test_content_contracts.py:1296-1305`의 180자 윈도우를 깨뜨리지 않기 위함(AC-12) |
| D10 | Terminal 절과 Stage table 행을 **함께** 보정 | Terminal 절만 보정 | 같은 계약이 두 곳에 서로 다른 강도로 남으면 오케스트레이터가 어느 쪽을 따를지 모호해진다. Stage table 행은 180자 윈도우 검사 대상이 아니므로 추가가 안전하다 |

## Strict-only 블록 제거 사유

이 작업은 standard로 분류됐으므로 `templates/spec.md`의 strict-only 블록을 제거했다. 제거한 여섯 항목이 적용되지 않는 이유는 다음과 같다.

| 항목 | 미적용 사유 |
|---|---|
| 위협·신뢰 경계 | 외부 입력 표면이 없다. 변경 대상은 로컬 CLI 헬퍼 한 함수의 진입 검사이며, 신뢰 경계를 넘는 데이터 흐름이 없다 |
| 인가·테넌트 격리 | 인가 개념도 테넌트 개념도 없는 단일 사용자 로컬 도구다 |
| 마이그레이션·호환성·롤백 | `state.json` 스키마가 변하지 않으므로 마이그레이션과 백필이 없다. 롤백은 파일 되돌리기로 완결되며 Failure behavior 절에 기록했다 |
| 실패 복구·관측성 | 알림·로그·메트릭·트레이스를 갖는 실행 중 서비스가 아니다. 실패는 CLI 종료 코드로 즉시 드러나며 Failure behavior 절에 표로 기록했다 |
| 고위험 E2E 검증 | 고위험 경로가 없다. 검증은 Test strategy 절의 `unittest` 스위트로 완결된다 |
| 프로덕션 변경 없음 확인 | 프로덕션 시스템이 존재하지 않는다. 다만 Non-goal 4가 `chezmoi apply`를 포함한 배포 부재를 명시하고 AC-16이 이를 검증한다 |
