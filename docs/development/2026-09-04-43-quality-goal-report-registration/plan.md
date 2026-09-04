# Quality Goal Implementation Plan

- Task ID: 20260904T051905Z-43-record-review의-자동-터미널-전이-때문에-보고서-등록-시-6eea40da
- Mode: standard
- Status: PLAN_REVIEW (round 1)
- Created: 2026-09-04T06:05:00Z
- Updated: 2026-09-04T06:05:00Z
- Source goal: #43 record-review의 자동 터미널 전이 때문에 보고서 등록 시점이 존재하지 않는 결함을 고친다.

## Spec link

- 승인 대상 Spec: `docs/development/2026-09-04-43-quality-goal-report-registration/spec.md`
- Spec SHA-256: `753d67fc35fccfbafd0ffc756613866b0109fc57d852b6cc143e74335a2d4030`
- Spec 리뷰 결과: 라운드 3에서 PASS (93점, blocker 0건). 잔여 advisory 1건(SPEC-009)은 아래 T4에서 흡수한다.
- 기준 커밋: `4fd0899fdc8efa32f78f9346eac5d730b0547ac6`

## Global constraints

1. **저장소 규약**: 이 저장소는 chezmoi dotfiles다. `dot_claude/skills/quality-goal/` 아래 소스만 수정한다. `chezmoi apply`를 **절대 실행하지 않는다** — 배포본을 다른 세션이 실행 중일 수 있다.
2. **허용 경로**: 아래 네 파일만 수정한다. 그 밖의 파일은 읽기만 한다.
   - `dot_claude/skills/quality-goal/scripts/quality_state.py`
   - `dot_claude/skills/quality-goal/SKILL.md`
   - `dot_claude/skills/quality-goal/tests/test_quality_state.py`
   - `dot_claude/skills/quality-goal/tests/test_content_contracts.py`
3. **금지 변경**: `record_review()`와 `record_review_validation_failure()`의 전이 로직(`scripts/quality_state.py:662-670`, `:770-771`), `ROUND_LIMITS`, `ALLOWED_TRANSITIONS`, `TERMINAL_STATES`, `state.json`의 `schema_version`과 필드 구성, `scripts/validate_review.py`, 루브릭·템플릿·스키마 파일. #59·#55·#60 관련 동작은 건드리지 않는다.
4. **기존 테스트 수정 금지**: 기존 229건의 테스트 본문을 수정하지 않는다. 유일한 예외는 T3이 요구하는 `tests/test_content_contracts.py:797`의 버전 문자열 한 줄(`"4.0.0"` → `"4.1.0"`)이다. 기존 테스트를 삭제하거나 이름을 바꾸지 않는다.
5. **test-first**: 모든 동작 변경은 실패하는 테스트를 먼저 기록한 뒤 구현한다. 각 작업의 1단계가 실패 증거, 3단계가 통과 증거다.
6. **커밋 경계**: 작업 브랜치 `43-fix/quality-goal-report-registration`에만 커밋·푸시한다. `main` 머지, 태그·릴리스 생성, 배포는 금지한다.
7. **검증 도구**: `pytest`는 설치돼 있지 않다. 표준 라이브러리 `unittest`를 쓴다.
8. **테스트 스타일**: 기존 관례를 따른다 — `unittest.TestCase`, `subTest`로 조합 순회, 상태 무변경 확인에는 `deepcopy` 비교, 임시 파일은 `tempfile.TemporaryDirectory()`.

## File map

| 파일 | 작업 | 책임 / 영향받는 동작 |
|---|---|---|
| `dot_claude/skills/quality-goal/scripts/quality_state.py` | 수정 | `set_artifact()`(현재 289-313행)의 검증 순서만 바꾼다. 다른 함수는 손대지 않는다 |
| `dot_claude/skills/quality-goal/SKILL.md` | 수정 | 프론트매터 `version`(3행), Stage table의 터미널 행(121행), `### Terminal` 절(240-248행) |
| `dot_claude/skills/quality-goal/tests/test_quality_state.py` | 수정(추가) | 신규 테스트 8종 추가. 기존 테스트는 손대지 않는다 |
| `dot_claude/skills/quality-goal/tests/test_content_contracts.py` | 수정(추가+1줄) | 신규 계약 테스트 1종 추가, 797행 버전 문자열 갱신 |
| `dot_claude/skills/quality-goal/tests/fixtures/` | 읽기만 | 기존 fixture는 변경하지 않는다 |
| `docs/development/2026-09-04-43-quality-goal-report-registration/` | 읽기만(Codex 기준) | Spec·증거 파일. 보고서는 오케스트레이터가 종결 시 작성한다 |

### 기존 테스트 헬퍼 (신규 테스트에서 재사용할 것)

`tests/test_quality_state.py`에 이미 있다. 새로 만들지 말고 재사용한다.

| 헬퍼 | 위치 | 용도 |
|---|---|---|
| `write_json(directory, name, value)` | 47-50행 | 리뷰 JSON 파일 작성 |
| `high_finding(finding_id, new_blocker_evidence=None)` | 53-62행 | High 심각도 finding 생성 |
| `valid_review(artifact, round_number, verdict, blockers)` | 65-83행 | 스키마 유효 리뷰 생성. `round_number >= 2`이면 각 finding에 `new_blocker_evidence`를 자동으로 채운다 |
| `state_at(stage, mode, project_root, goal)` | 95-106행 | 지정 stage의 상태 dict 생성 |
| `make_git_repo(testcase)` | 28-37행 | CLI 테스트용 임시 Git 저장소 |
| `assert_cli_success(args)` / `invoke_main(args)` | 2389-2392행 및 그 위 | CLI 호출 및 종료 코드 확인 |
| `VALID_DIGEST` 상수 | 42행 | 64자리 소문자 hex digest |

### 기존 테스트 클래스 소재 (실측 확인됨)

| 테스트 | 소속 클래스 | 클래스 선언 위치 |
|---|---|---|
| `test_terminal_states_are_immutable_for_active_only_mutators` (1561행) | `ReviewValidationRetryTests` | `tests/test_quality_state.py:1532` |
| `test_set_artifact_*` (604-637행) | `ArtifactTests` | `tests/test_quality_state.py:603` |
| `assert_cli_success` (2389행) 및 CLI 테스트 | `CLITests` | `tests/test_quality_state.py:2375` |
| `test_terminal_report_is_registered_before_transition_contract` 등 SKILL.md 계약 | `QualityGoalSkillContentTests` | `tests/test_content_contracts.py:724` |

`test_terminal_states_are_immutable_for_active_only_mutators`의 소속을 오인하기 쉽다. **1560행에는 클래스 선언이 없다.** 1532행의 `ReviewValidationRetryTests`가 이 메서드를 소유한다. 실행으로 확인했다:

```
$ python3 -m unittest tests.test_quality_state.ReviewValidationRetryTests.test_terminal_states_are_immutable_for_active_only_mutators
Ran 1 test ... OK
```

## Task dependencies

```
T1 (set_artifact 순서 변경)  ──┐
                               ├──> T5 (전체 스위트 + 범위 경계)
T2 (상태 머신 테스트 추가) ────┤
                               │
T3 (SKILL.md 문서·버전) ───────┤
                               │
T4 (문서 계약 테스트) ─────────┘
```

- **T2는 T1에 의존한다**: T2의 1단계(실패 확인)는 T1 이전에 실행해야 하고, T2의 3단계(통과 확인)는 T1 이후에 실행한다. 따라서 실제 실행 순서는 `T2-1단계 → T1 → T2-3단계`다.
- **T4는 T3에 의존한다**: 같은 방식으로 `T4-1단계 → T3 → T4-3단계`.
- **T1과 T3은 서로 독립**이며 순서를 바꿔도 된다.
- **T5는 T1~T4 완료 후**에만 실행한다.

## Tasks

### T1 — `set_artifact()` 검증 순서 변경 (R1, R2)

**대상**: `dot_claude/skills/quality-goal/scripts/quality_state.py`, `set_artifact()` 함수(현재 289-313행)

**현재 코드의 구조** (289-291행):

```python
def set_artifact(state, kind, path):
    """Bind an existing regular file to one of the workflow artifacts."""
    state = _require_active(state)
    if not isinstance(kind, str) or kind not in _ARTIFACT_KEYS:
        raise StateError(f"invalid artifact kind: {kind!r}")
    ...
```

**요구 변경**: `_require_active(state)` 무조건 호출을 조건부로 바꾼다. 나머지 본문은 그대로 둔다.

```python
def set_artifact(state, kind, path):
    """Bind an existing regular file to one of the workflow artifacts.

    A terminal state stays immutable for every artifact kind except
    ``report``: record_review and record_review_validation_failure
    transition into NEEDS_REDESIGN or BLOCKED by themselves, so the
    report pointer must remain registrable afterwards.
    """
    state = _require_state(state)
    if kind != "report":
        _require_active(state)
    if not isinstance(kind, str) or kind not in _ARTIFACT_KEYS:
        raise StateError(f"invalid artifact kind: {kind!r}")
    ...
```

**필수 순서(Spec R2)**: `_require_state` → (`kind != "report"`일 때만) `_require_active` → `kind` 멤버십 → `path` 타입 → `path` 정규 파일 → `artifacts` dict. `kind` 멤버십 검사를 `_require_active`보다 **앞으로 옮기면 안 된다**. 앞으로 옮기면 터미널 상태의 알 수 없는 `kind`가 `TransitionError` 대신 `StateError`가 되어 동작이 바뀐다.

**`kind != "report"` 비교를 `isinstance` 검사보다 앞에 두어도 안전한 이유**: `kind`가 문자열이 아니면(예: `None`, `3`) `!=` 비교는 그냥 `True`가 되어 `_require_active`가 호출되고, 이는 기존 동작과 같다. 예외를 던지지 않는다.

**금지**: `_require_active()` 함수 자체(108-113행)를 수정하지 않는다. 다른 호출자(`record_verification`, `invalidate_stale_verification`, `record_review_validation_failure`)의 동작이 함께 바뀌면 안 된다.

| 단계 | 명령 | 기대 결과 |
|---|---|---|
| 1 (실패) | T2-1단계에서 이미 확인됨 | 신규 테스트가 `TransitionError`로 실패 |
| 2 (구현) | 위 변경 적용 | — |
| 3 (통과) | `cd dot_claude/skills/quality-goal && python3 -m unittest tests.test_quality_state -v 2>&1 \| tail -5` | `OK` |

### T2 — 상태 머신 계약 테스트 추가 (R7, AC-1~AC-7, AC-9)

**대상**: `dot_claude/skills/quality-goal/tests/test_quality_state.py` (추가만)

아래 8개 테스트 메서드를 추가한다. 이름은 그대로 쓴다(추적표가 이 이름을 참조한다). 기존 `ArtifactTests` 클래스(`tests/test_quality_state.py:603`) 뒤에 새 클래스 `TerminalReportRegistrationTests(unittest.TestCase)`를 만들어 담는다.

| # | 테스트 메서드 이름 | 대응 AC | 내용 |
|---:|---|---|---|
| 1 | `test_report_registers_after_review_limit_exhausted_auto_transition` | AC-1 | `("spec", 3)`, `("plan", 2)`, `("code", 3)` 세 조합을 `subTest`로 순회한다. 각각 해당 리뷰 stage에서 `valid_review(artifact, r, "REVISE", [f"{ID}-{r}"])`를 라운드 1부터 한도까지 `record_review()`로 기록해 자동 전이를 유발한다. `state["stage"] == "NEEDS_REDESIGN"`과 `state["status_reason"] == f"REVIEW_LIMIT_EXHAUSTED:{artifact}"`를 확인한 뒤 `set_artifact(state, "report", <존재하는 파일>)`이 예외 없이 성공하고 `state["artifacts"]["report"] == str(path)`임을 확인한다 |
| 2 | `test_report_registers_after_recurring_blocking_finding_auto_transition` | AC-2 | `spec` 아티팩트로 라운드 1과 2에 **같은** blocker ID를 기록한다(한도 3에 도달하지 않음). `state["stage"] == "NEEDS_REDESIGN"`, `state["status_reason"] == "RECURRING_BLOCKING_FINDING:<id>"`, `state["rounds"]["spec"] == 2`를 확인한 뒤 report 등록 성공을 확인한다. 라운드 2 리뷰의 blocker는 라운드 1의 `open_finding_ids`에 있으므로 `new_blocker_evidence`가 없어도 검증을 통과한다(`scripts/validate_review.py:340-357`) |
| 3 | `test_report_registration_succeeds_in_every_terminal_state` | AC-3 | `quality_state.TERMINAL_STATES` 네 값을 `subTest`로 순회하며 `state_at(terminal)`에서 `set_artifact(state, "report", <존재하는 파일>)` 성공과 저장된 경로 값을 확인한다 |
| 4 | `test_non_report_kinds_stay_immutable_in_every_terminal_state` | AC-4 | 네 터미널 상태 × `("spec", "plan", "compact_plan")` 12개 조합을 순회하며 `TransitionError`가 나고 `deepcopy` 비교로 상태 무변경임을 확인한다. **경로는 반드시 `tempfile.TemporaryDirectory()`로 만든 존재하는 정규 파일이어야 한다**(테스트 #3과 같은 fixture). 없는 경로를 쓰면 경로 검증이 대신 예외를 내어 테스트가 엉뚱한 이유로 통과하고 회귀 가드가 무의미해진다. 또한 잡은 예외의 타입이 정확히 `TransitionError`인지(`StateError`가 아닌지) 확인한다 — `TransitionError`는 `StateError`의 하위 클래스이므로 `assertRaises(StateError)`로는 구별되지 않는다 |
| 5 | `test_terminal_report_registration_still_validates_the_path` | AC-5 | 네 터미널 상태를 순회하며 `kind="report"`에 대해 (없는 파일, 디렉터리, 빈 문자열) 세 경로로 `StateError`가 나고 상태가 무변경임을 확인한다 |
| 6 | `test_terminal_unknown_kind_is_rejected_as_transition_error` | AC-6 | 네 터미널 상태에서 `set_artifact(state, "unknown", <존재하는 파일>)`이 `StateError`가 아니라 `TransitionError`를 던지는지 확인한다. `assertRaises(quality_state.TransitionError)`를 쓰고, `TransitionError`가 `StateError`의 하위 클래스인지 확인해 필요하면 `assertNotIsInstance`가 아니라 정확한 타입 비교(`type(exc) is quality_state.TransitionError`)로 검사한다. **R2의 검증 순서가 뒤집히면 이 테스트가 깨진다** |
| 7 | `test_record_review_is_rejected_after_each_auto_transition` | AC-7 | 한도 소진 경로와 재발 경로 각각에서 자동 전이 후 `record_review()`를 한 번 더 호출하면 `StateError`가 나고 메시지에 `requires stage`가 포함되는지 확인한다 |
| 8 | `test_report_registers_after_review_output_invalid_auto_transition` | AC-9 | `state_at("PLAN_REVIEW")`에서 `record_review_validation_failure(state, "plan", 1, ["error"])`를 두 번 호출해 `stage == "BLOCKED"`, `status_reason == "REVIEW_OUTPUT_INVALID"`에 도달한 뒤 report 등록 성공을 확인한다 |

**CLI 레벨 검증(필수)**: 위 1번과 2번 각각에 대해 CLI 경로도 확인한다. 기존 클래스 `CLITests`(`tests/test_quality_state.py:2375`, `assert_cli_success`는 2389행)에 아래 두 메서드를 추가한다.

| # | 테스트 메서드 이름 | 대응 AC | 내용 |
|---:|---|---|---|
| 9 | `test_cli_registers_report_after_limit_exhausted_transition` | AC-1 | `make_git_repo` + `init` + `classify` + `set-artifact --kind spec` + `transition --to SPEC_REVIEW` 후 `record-review`를 한도까지 호출해 자동 전이시킨다. 그 다음 `set-artifact --kind report`가 **종료 코드 0**임을 확인하고, `state.json`을 다시 읽어 `artifacts.report`가 그 절대 경로와 같은지 확인한다. CLI 인자 형태는 아래 표를 따른다 |
| 10 | `test_cli_registers_report_after_recurring_finding_transition` | AC-2 | 같은 방식으로 재발 경로를 CLI로 확인한다 |

**CLI 인자 형태 (재발견 불필요)**. 기존 CLI 테스트 `tests/test_quality_state.py:2700-2724`에 같은 패턴이 있다.

| 인자 | 형태 |
|---|---|
| `classify --reasons` | **JSON 배열이 담긴 파일의 경로**. 인라인 문자열이 아니다 |
| `record-review --review` | 리뷰 JSON이 담긴 **파일 경로**. `write_json()`으로 먼저 파일에 쓴다 |
| `record-review --artifact-digest` | 64자리 소문자 hex 문자열 |
| `transition --to` | 대상 stage 이름. 플래그는 `--target`이 아니라 `--to`다 |
| `set-artifact --path` | **존재하는 정규 파일**의 경로 |

`capture-baseline`은 이 테스트에 필요하지 않다. `record_review()`가 요구하는 것은 stage와 rounds뿐이다.

**주의 — artifact별 digest 전제조건** (`scripts/quality_state.py:588-597`): `record_review()`는 artifact가 `spec` 또는 `plan`이고 `state["artifacts"][artifact]`가 설정돼 있을 때만 그 파일의 digest와 `artifact_digest` 인자의 일치를 요구한다. artifact별로 이렇게 처리한다.

| artifact | 처리 |
|---|---|
| `spec` | `tempfile`로 파일을 만들고 `set_artifact(state, "spec", path)`로 등록한 뒤, 매 라운드 `quality_state._file_digest(path)`를 `artifact_digest`로 넘긴다 |
| `plan` | 같은 방식으로 별도 파일을 만들어 `set_artifact(state, "plan", path)`로 등록하고 그 파일의 digest를 넘긴다. **spec용 digest를 재사용하면 `StateError`가 난다** |
| `code` | `code`는 `_ARTIFACT_KEYS`에 없어 파일 대조가 일어나지 않는다. 모듈 상수 `VALID_DIGEST` 같은 임의의 64자리 소문자 hex를 그대로 쓴다 |

또한 각 artifact의 리뷰는 대응 stage에서만 기록된다(`_REVIEW_STAGES`): `spec`→`SPEC_REVIEW`, `plan`→`PLAN_REVIEW`, `code`→`CODE_REVIEW`. `state_at()`으로 해당 stage를 만들어 쓴다.

| 단계 | 명령 | 기대 결과 |
|---|---|---|
| 1 (실패) | `cd dot_claude/skills/quality-goal && python3 -m unittest tests.test_quality_state.TerminalReportRegistrationTests -v 2>&1 \| tail -20` | 신규 테스트들이 `TransitionError: terminal state is immutable`로 실패한다. 이 출력을 증거로 기록한다 |
| 2 (구현) | T1 적용 | — |
| 3 (통과) | 같은 명령 | 신규 테스트 전부 `ok` |

### T3 — `SKILL.md` 순서 지시 및 버전 갱신 (R5, R6)

**대상**: `dot_claude/skills/quality-goal/SKILL.md`

**3-1. 프론트매터 버전 (3행)**: `version: 4.0.0` → `version: 4.1.0`

**3-2. Stage table의 터미널 행 (121행)**: 행 끝에 문장 D3을 축자로 덧붙인다. 기존 문장은 손대지 않는다.

- 변경 전 행 끝: `... BEFORE transitioning into the terminal state; then transition and explain the terminal outcome |`
- 변경 후 행 끝: `... BEFORE transitioning into the terminal state; then transition and explain the terminal outcome. When a helper has already transitioned automatically, register the report in the terminal state as the Terminal section describes. |`

**3-3. `### Terminal` 절 (240-248행)**: 기존 문단 **뒤에** 새 문단을 추가한다. 기존 문장 `For every terminal outcome, render report.md ... transitioning into COMPLETED, BLOCKED, NEEDS_REDESIGN, or CANCELLED.`의 내부에는 어떤 텍스트도 삽입하지 않는다(`tests/test_content_contracts.py:1296-1305`의 180자 윈도우 제약).

추가할 문단은 아래 두 문장을 축자로 포함한다. 줄바꿈 위치는 자유다.

> When the review you are about to record is expected to end the workflow, because it is the last allowed round without a PASS or it repeats a blocking finding ID from an earlier round, render report.md and register it with set-artifact --kind report before calling record-review, while the stage is still non-terminal.
>
> Because record-review and record-review-error transition into NEEDS_REDESIGN or BLOCKED on their own, set-artifact --kind report is also accepted after the state is already terminal; register the report there when the terminal transition has already happened. No other artifact kind may be registered once the state is terminal.

**크기 제약**: `tests/test_content_contracts.py:966-969`가 `SKILL.md`를 500줄 미만으로 제한한다. 현재 358줄이므로 여유가 크지만, 추가 후 줄 수를 확인한다.

| 단계 | 명령 | 기대 결과 |
|---|---|---|
| 1 (실패) | `cd dot_claude/skills/quality-goal && python3 -m unittest tests.test_content_contracts -v 2>&1 \| tail -20` | T4의 신규 계약 테스트와 버전 계약 테스트가 실패한다 |
| 2 (구현) | 위 세 변경 적용 | — |
| 3 (통과) | `cd dot_claude/skills/quality-goal && python3 -m unittest tests.test_content_contracts 2>&1 \| tail -5` 및 `wc -l SKILL.md` | `OK`, 줄 수 500 미만 |

### T4 — 문서 계약 테스트 추가 및 버전 pin 갱신 (AC-11, AC-13)

**대상**: `dot_claude/skills/quality-goal/tests/test_content_contracts.py`

**4-1. 버전 pin (797행)**: `"version": "4.0.0",` → `"version": "4.1.0",`. 이 한 줄이 기존 테스트에 가하는 유일한 수정이다.

**4-2. 신규 계약 테스트**: 기존 클래스 `QualityGoalSkillContentTests`(`tests/test_content_contracts.py:724`, `SKILL_PATH`는 725행이며 `read_skill()`과 `normalize()`를 제공한다)에 아래 메서드를 추가한다.

- 이름: `test_terminal_report_registration_ordering_contract`
- 대응 AC: AC-11

**검증 방식(Spec advisory SPEC-009 반영)**: 본문 전체를 정규화해 문장 존재만 확인하면 문장이 엉뚱한 절에 있어도 통과한다. 따라서 **위치를 좁혀서** 검사한다.

1. 본문에서 `### Terminal` 헤딩부터 다음 `## ` 헤딩(즉 `## Review invocation contract`) 직전까지를 잘라내 Terminal 절 본문을 만든다. 그 조각을 `normalize()`로 정규화한 뒤 문장 D1과 D2가 각각 `assertIn`으로 포함되는지 확인한다.
2. 본문 줄 중 `| COMPLETED, BLOCKED, NEEDS_REDESIGN, CANCELLED |`로 시작하는 Stage table 행 한 줄을 찾아 정규화한 뒤 문장 D3이 `assertIn`으로 포함되는지 확인한다. 해당 행이 정확히 한 줄 존재하는지도 확인한다.
3. 비교 대상 문장 D1·D2·D3은 테스트 안에 축자 문자열 상수로 두고 `normalize()`를 적용해 비교한다(공백·대소문자 차이를 흡수하기 위함).

| 단계 | 명령 | 기대 결과 |
|---|---|---|
| 1 (실패) | `cd dot_claude/skills/quality-goal && python3 -m unittest tests.test_content_contracts -v 2>&1 \| tail -20` | 신규 테스트가 문장 부재로 실패, 버전 계약 테스트가 `4.0.0 != 4.1.0`으로 실패 |
| 2 (구현) | T3 적용 + 4-1 적용 | — |
| 3 (통과) | 같은 명령 | 전부 `ok` |

### T5 — 전체 스위트 및 범위 경계 확인 (AC-8, AC-10, AC-12, AC-14, AC-15, AC-16)

수정 없이 통과해야 하는 기존 테스트를 개별로 먼저 확인한 뒤 전체 스위트를 돌린다.

| 단계 | 명령 | 기대 결과 |
|---|---|---|
| 1 | `python3 -m unittest tests.test_quality_state.ReviewValidationRetryTests.test_terminal_states_are_immutable_for_active_only_mutators -v 2>&1 \| tail` | `ok` — AC-6 첫 조건, AC-10 |
| 2 | `python3 -m unittest tests.test_content_contracts -v 2>&1 \| grep -E "terminal_report\|frontmatter"` | 해당 테스트들 `ok` — AC-12, AC-13 |
| 3 | `python3 -m unittest discover -s tests 2>&1 \| tail -5` | `OK`, `Ran <N> tests`에서 `N > 229` |
| 4 | `git -C <repo> status --porcelain` | Global constraints 2의 네 파일과 `docs/development/2026-09-04-...` 문서만 나타난다. 그 밖의 수정 파일이 있으면 되돌린다 |
| 5 | `git -C <repo> diff --stat` | 변경 규모가 계획과 일치한다 |

**Codex는 4·5단계까지만 수행한다.** 아래 커밋·PR·경계 확인은 오케스트레이터가 수행한다.

| 단계 | 명령 | 기대 결과 |
|---|---|---|
| 6 (오케스트레이터) | `git merge-base --is-ancestor $(git rev-parse HEAD) origin/main; echo $?` | **0이 아님** — 이 작업이 `main`에 머지되지 않았다 (AC-16 i) |
| 7 (오케스트레이터) | `gh pr view --json state,mergedAt` | `state=OPEN`, `mergedAt=null` (AC-16 ii) |
| 8 (오케스트레이터) | 이 실행의 명령 기록 검토 | `chezmoi apply` 호출 없음 (AC-16 iii) |

## Verification commands

작업 디렉터리는 모두 `dot_claude/skills/quality-goal/`이다. 순서대로 실행한다.

| 순서 | 범주 | 명령 | 기대 결과 |
|---:|---|---|---|
| 1 | 표적 테스트 | `python3 -m unittest tests.test_quality_state.TerminalReportRegistrationTests -v` | 신규 테스트 전부 `ok` |
| 2 | 표적 테스트 | `python3 -m unittest tests.test_content_contracts -v` | 신규·기존 계약 테스트 전부 `ok` |
| 3 | 전체 스위트 | `python3 -m unittest discover -s tests` | `OK`, `Ran N tests`에서 `N > 229` |
| 4 | 타입 검사 | 구성돼 있지 않음 | `find <repo> -maxdepth 3 \\( -name "mypy.ini" -o -name ".mypy.ini" -o -name "pyrightconfig.json" -o -name "pyproject.toml" \\) -not -path "*/.git/*"`의 출력을 근거로 "not configured"로 기록한다. `pyproject.toml`이 발견되면 그 자체를 근거로 삼지 말고 `[tool.mypy]`/`[tool.pyright]` 절이 있는지 열어 확인한다 |
| 5 | 린트 | 구성돼 있지 않음 | `find <repo> -maxdepth 3 \\( -name ".ruff.toml" -o -name "ruff.toml" -o -name ".flake8" -o -name "setup.cfg" -o -name "tox.ini" -o -name "pyproject.toml" \\) -not -path "*/.git/*"`의 출력을 근거로 "not configured"로 기록한다. `pyproject.toml`이 발견되면 `[tool.ruff]`/`[tool.flake8]` 절 유무를 확인한다 |
| 6 | 빌드 | 해당 없음 | 이 저장소는 빌드 산출물이 없는 dotfiles다 |
| 7 | E2E | 해당 없음 | Spec의 Test strategy가 `unittest` 스위트로 검증이 완결된다고 규정한다 |
| 8 | 문법 확인 | `python3 -c "import ast,pathlib; ast.parse(pathlib.Path('scripts/quality_state.py').read_text())"` | 출력 없음, 종료 코드 0 |

**"not configured"를 통과로 기록하지 않는다.** 각 범주는 근거 명령과 함께 미구성으로 기록한다.

## Rollout and rollback

**롤아웃**: 없다. 이 작업은 소스 파일만 수정하고 PR을 여는 데서 끝난다. 배포(`chezmoi apply`)는 사용자가 별도로 결정한다. 배포본 `~/.claude/skills/quality-goal/`은 이 작업 중 변경되지 않는다.

**호환성**: `state.json`의 스키마와 필드 구성이 바뀌지 않으므로, 이 변경 전에 만들어진 상태 파일과 이후 코드가 서로 호환된다. 반대로 변경 후 만들어진 상태 파일도 변경 전 코드로 읽을 수 있다. 다만 변경 전 코드는 터미널 상태에서 report 등록을 여전히 거부한다.

**롤백 트리거**: (i) 전체 스위트가 `OK`가 아니거나 실행 건수가 229 이하로 줄어든 경우, (ii) 기존 테스트가 R6의 버전 한 줄 외의 이유로 수정된 경우, (iii) Global constraints 2의 허용 경로 밖 파일이 수정된 경우, (iv) `record_review()` 또는 `record_review_validation_failure()`의 동작이 바뀐 경우.

**롤백 절차**: 커밋 전이면 `git checkout -- <파일>`로 되돌린다. 커밋 후면 `git revert <커밋>` 또는 브랜치 폐기로 되돌린다. 마이그레이션·백필·외부 부작용이 없으므로 파일 되돌리기로 완결된다.

**모니터링**: 해당 없음(실행 중 서비스가 아니다). 회귀는 다음 `unittest` 실행에서 즉시 드러난다.

## Acceptance-criteria traceability

| 기준 | 작업 | 검증 명령 | 기대 결과 |
|---|---|---|---|
| AC-1 | T1, T2(#1, #9) | `python3 -m unittest tests.test_quality_state.TerminalReportRegistrationTests.test_report_registers_after_review_limit_exhausted_auto_transition` 및 `...test_cli_registers_report_after_limit_exhausted_transition` | 두 테스트 `ok`. spec·plan·code 세 artifact 전부에서 `artifacts.report`가 등록된 경로와 일치, CLI 종료 코드 0 |
| AC-2 | T1, T2(#2, #10) | `python3 -m unittest tests.test_quality_state.TerminalReportRegistrationTests.test_report_registers_after_recurring_blocking_finding_auto_transition` 및 `...test_cli_registers_report_after_recurring_finding_transition` | 두 테스트 `ok`. `rounds.spec == 2`(한도 3 미도달)에서 전이했고 report가 등록됨 |
| AC-3 | T1, T2(#3) | `python3 -m unittest ...test_report_registration_succeeds_in_every_terminal_state` | `ok`. 네 터미널 상태 전부 성공 |
| AC-4 | T1, T2(#4) | `python3 -m unittest ...test_non_report_kinds_stay_immutable_in_every_terminal_state` | `ok`. 12개 조합 전부 `TransitionError` + 상태 무변경 |
| AC-5 | T1, T2(#5) | `python3 -m unittest ...test_terminal_report_registration_still_validates_the_path` | `ok`. 세 부적합 경로 전부 `StateError` + 상태 무변경 |
| AC-6 | T1, T2(#6) + 기존 테스트 | `python3 -m unittest ...test_terminal_unknown_kind_is_rejected_as_transition_error` 및 `python3 -m unittest tests.test_quality_state.ReviewValidationRetryTests.test_terminal_states_are_immutable_for_active_only_mutators` | 신규 테스트 `ok`(알 수 없는 kind → `TransitionError`), 기존 테스트가 **수정 없이** `ok`(`("spec", 없는 경로)` → `TransitionError`) |
| AC-7 | T1, T2(#7) | `python3 -m unittest ...test_record_review_is_rejected_after_each_auto_transition` | `ok`. 두 경로 모두 `StateError`, 메시지에 `requires stage` 포함 |
| AC-8 | T1(무변경 보장) + 기존 테스트 | `python3 -m unittest tests.test_quality_state 2>&1 \| tail -5` | `OK`. `record_review`/`record_review_validation_failure`를 다루는 기존 테스트(1429-1447행 포함)가 수정 없이 통과 |
| AC-9 | T1, T2(#8) | `python3 -m unittest ...test_report_registers_after_review_output_invalid_auto_transition` | `ok`. `BLOCKED`/`REVIEW_OUTPUT_INVALID` 상태에서 report 등록 성공 |
| AC-10 | T1(무변경 보장) + 기존 테스트 | `python3 -m unittest tests.test_quality_state.ReviewValidationRetryTests.test_terminal_states_are_immutable_for_active_only_mutators` | `ok`. `record_verification`·`invalidate_stale_verification`·`record_review_validation_failure`가 네 터미널 상태에서 여전히 `TransitionError` |
| AC-11 | T3(3-2, 3-3), T4(4-2) | `python3 -m unittest tests.test_content_contracts -k test_terminal_report_registration_ordering_contract` | `ok`. D1·D2가 `### Terminal` 절 조각 안에, D3이 Stage table 행 안에 있음 |
| AC-12 | T3(삽입 위치 제약 준수) + 기존 테스트 | `python3 -m unittest tests.test_content_contracts -k test_terminal_report_is_registered_before_transition_contract` | `ok`. 기존 180자 윈도우 계약 테스트가 **수정 없이** 통과 |
| AC-13 | T3(3-1), T4(4-1) | `python3 -m unittest tests.test_content_contracts -k test_frontmatter_contract` 및 `grep -n "^version:" SKILL.md` | `ok`, `version: 4.1.0` |
| AC-14 | T1(무변경 보장) + 기존 테스트 | `python3 -m unittest tests.test_quality_state.ArtifactTests` | 두 기존 테스트가 **수정 없이** `ok` |
| AC-15 | T5(3단계) | `python3 -m unittest discover -s tests 2>&1 \| tail -5` | `OK`이고 `Ran N tests`에서 `N > 229` |
| AC-16 | T5(6~8단계, 오케스트레이터) | `git merge-base --is-ancestor $(git rev-parse HEAD) origin/main; echo $?` / `gh pr view --json state,mergedAt` / 명령 기록 검토 | 첫 명령이 **비영 종료**, PR이 `state=OPEN`·`mergedAt=null`, `chezmoi apply` 호출 없음 |

### 신규 테스트 → AC 역매핑 (자체 감사용)

Codex가 테스트를 누락하지 않았는지 코드 리뷰 **전에** 이 표로 감사한다. 10개 테스트가 모두 존재하고 각각 통과해야 한다.

| # | 테스트 이름 | AC |
|---:|---|---|
| 1 | `test_report_registers_after_review_limit_exhausted_auto_transition` | AC-1 |
| 2 | `test_report_registers_after_recurring_blocking_finding_auto_transition` | AC-2 |
| 3 | `test_report_registration_succeeds_in_every_terminal_state` | AC-3 |
| 4 | `test_non_report_kinds_stay_immutable_in_every_terminal_state` | AC-4 |
| 5 | `test_terminal_report_registration_still_validates_the_path` | AC-5 |
| 6 | `test_terminal_unknown_kind_is_rejected_as_transition_error` | AC-6 |
| 7 | `test_record_review_is_rejected_after_each_auto_transition` | AC-7 |
| 8 | `test_report_registers_after_review_output_invalid_auto_transition` | AC-9 |
| 9 | `test_cli_registers_report_after_limit_exhausted_transition` | AC-1 (CLI) |
| 10 | `test_cli_registers_report_after_recurring_finding_transition` | AC-2 (CLI) |
| 11 | `test_terminal_report_registration_ordering_contract` | AC-11 |

AC-8·AC-10·AC-12·AC-14는 신규 테스트가 아니라 **기존 테스트가 수정 없이 통과**하는 것으로 검증한다. AC-13은 기존 프론트매터 계약 테스트가 갱신된 값으로 통과하는 것으로 검증한다. AC-15는 스위트 전체, AC-16은 오케스트레이터 확인이다.

## Strict-only 블록 제거 사유

standard 모드이므로 `templates/plan.md`의 strict-only 블록을 제거했다. 위협·신뢰 경계와 인가·테넌트 격리는 대상에 해당 개념이 없고, 마이그레이션·롤백은 스키마 변경이 없어 위 "Rollout and rollback" 절로 완결되며, 실패 복구·관측성은 실행 중 서비스가 아니어서 적용되지 않고, 고위험 E2E는 고위험 경로가 없어 `unittest` 스위트로 충분하며, 프로덕션 변경은 존재하지 않는다(Global constraints 1·6과 AC-16이 배포 부재를 강제한다).
