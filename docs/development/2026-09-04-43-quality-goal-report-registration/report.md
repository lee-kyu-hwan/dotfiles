# Quality Goal Report

- Task ID: 20260904T051905Z-43-record-review의-자동-터미널-전이-때문에-보고서-등록-시-6eea40da
- Mode: standard
- Status: COMPLETED
- Created: 2026-09-04T05:19:05Z
- Updated: 2026-09-04T13:05:00Z
- Source goal: #43 record-review의 자동 터미널 전이 때문에 보고서 등록 시점이 존재하지 않는 결함을 고친다.

## Classification

**standard**. 사용자가 `--mode=standard`를 명시했고 리스크 스캔 결과도 standard였다. 다운그레이드가 아니므로 확인 절차가 필요하지 않았다.

- **strict 트리거 0건**: 인증·인가·테넌시, 결제·정산, PII·시크릿, DB 스키마 마이그레이션·백필·파괴적 작업, 공개/외부 API·웹훅·큐·멱등성·동시성, 프로덕션 인프라 중 해당 항목이 없다. 변경 대상은 로컬 개발 워크플로 스킬(`dot_claude/skills/quality-goal/`)이며 런타임 `state.json`은 `.gitignore:25`로 저장소 밖에 있다.
- **standard 조건 — 상태 전이 변경**: `scripts/quality_state.py:662-670`의 `record_review` 자동 터미널 전이가 걸린 상태 머신 규칙을 다룬다.
- **standard 조건 — 다중 파일·레이어**: 상태 머신, 계약 문서, 두 테스트 모듈이 함께 변경된다.
- **standard 조건 — 대안 택1 필요**: 이슈 #43이 (a)~(d) 네 안을 제시하고 택1을 요구했다.
- 이슈 라벨 `bug`.

## Review history

| 아티팩트 | 라운드 | 점수 | 판정 | blocker | 라운드 간 변화 |
|---|---:|---:|---|---|---|
| Spec | 1 | 77 | REVISE | SPEC-001, SPEC-002 | 초기 전면 리뷰. High 2건 + Medium 1건 + Low 2건 |
| Spec | 2 | 87 | REVISE | SPEC-006 | 라운드 1의 5건 전부 해소 확인. 개정이 새 High 1건을 낳았다(신규 AC-16의 고정 SHA) |
| Spec | 3 | 93 | **PASS** | 없음 | SPEC-006·007·008 해소. Low advisory 1건(SPEC-009)만 남음 |
| Plan | 1 | 90 | **PASS** | 없음 | Low advisory 5건(PLAN-001~005) |
| 코드 | 1 | 91 | **PASS** | 없음 | Low advisory 2건(CODE-001, CODE-002) |
| 코드 | 2 | 94 | **PASS** | 없음 | CODE-001·CODE-002 해소 확인. 잔여 finding **0건** |

### 리뷰 절차상 특이사항 (도구 관측)

이 실행에서 리뷰어 호출이 **네 번 비정상 종료**했다. #43과 별개의 워크플로 도구 관측이므로 기록한다.

| 라운드 | 사건 | 처리 |
|---|---|---|
| Spec 3 | PASS를 내면서 `verified: false` evidence를 남겨 스키마 검증 실패(`PASS reviews must not contain unverified evidence`) | `record-review-error` 1회 기록(라운드 미소모) 후 검증 오류만 덧붙여 같은 라운드 재실행 → PASS |
| Plan 1 (1차) | 24턴 한도 미완결. JSON은 나왔으나 High blocker PLAN-001이 **사실이 아니었다** | `record-review-error` 기록(라운드 미소모). 아래 별항 참조 |
| Plan 1 (2차) | 24턴 한도 미완결. **JSON 없음** | `record-review-error`를 기록하지 **않았다**. 아래 별항 참조 |
| 코드 2 (1차) | 세션 사용량 한도(HTTP 429)로 에이전트 종료 | 한도 회복 후 동일 계약 입력·동일 fingerprint로 재기동 → PASS. 워크스페이스가 중단 중 변하지 않았음을 fingerprint 일치로 확인했다 |

**Plan 1차 리뷰의 오진과 그 처리.** 1차 리뷰어는 `test_terminal_states_are_immutable_for_active_only_mutators`가 1560행에 선언된 `TerminalImmutabilityTests`에 속하므로 Plan의 `ReviewValidationRetryTests` 인용이 틀렸다는 High blocker를 냈다. 실행으로 반증했다 — `grep -n "^class "`는 1560행에 선언이 없음을 보이고(최근접 선행 선언은 1532행의 `ReviewValidationRetryTests`), Plan이 쓴 호출은 `Ran 1 test ... OK`로 실행되는 반면 리뷰어가 요구한 이름은 `FAILED (errors=1)`을 낸다. 시스템이 그 실행을 "24턴 한도 미완결, 부분 출력"으로 표시했고 그 미완결성이 검증 가능한 오류로 드러난 것이므로, 라운드를 소모하지 않고 리뷰 출력 무효로 기록하고 반증 근거를 상태 파일에 남겼다. 다만 그 리뷰의 나머지 4건(PLAN-002~005 계열)은 타당했으므로 재실행 전에 Plan에 반영했다.

**2차 미완결을 `record-review-error`로 기록하지 않은 판단.** 그 헬퍼는 "one malformed review response"를 세며, 같은 (artifact, round)에 대한 두 번째 기록은 즉시 `BLOCKED`/`REVIEW_OUTPUT_INVALID`로 종결시킨다. 그러나 2차는 잘못된 응답이 아니라 **응답이 아예 없었다** — 리뷰 품질 문제가 아니라 에이전트 턴 예산 문제다. 이를 `REVIEW_OUTPUT_INVALID`로 종결하면 상태 파일에 사실과 다른 기록이 남는다. 대신 실패 원인을 직접 제거했다: 세 리뷰어가 모두 3153행·1373행짜리 테스트 모듈을 통독하다 예산을 소진했으므로, 검증에 필요한 20개 구간(클래스 선언 전체, 헬퍼 목록, `set_artifact` 구현, digest 대조 로직, 세 개의 content contract, CLI 파서 인자, 인용된 unittest 호출의 실제 실행 출력)을 실행 행 번호와 함께 370행 발췌로 뽑아 제공했다. 3차 리뷰어는 도구 호출 10회로 완료했다(이전 35회, 40회).

## Blocking-finding resolutions

| ID | 심각도 | 내용 | 해소 | 확인 증거 |
|---|---|---|---|---|
| SPEC-001 | High | `set_artifact()` 검증 순서를 규정하지 않은 채 "기존 불변성 테스트는 안 깨진다"고 주장. 기존 테스트가 `set_artifact(state, "spec", "missing-artifact.md")`를 호출하는데 그 경로는 **존재하지 않으므로**, kind·경로 검증을 터미널 검사 앞으로 옮기면 `TransitionError` 대신 `StateError`가 나서 회귀가 발생 | Spec에 R2 "검증 순서의 규범적 고정" 6단계 표를 추가하고, `_require_active`를 `kind` 멤버십 검사보다 **앞**에 두어 `kind == "report"`일 때만 건너뛰도록 규정. Interfaces 표를 상호 배타적 4행으로 재작성. AC-6 신설 | 라운드 2 리뷰어가 코드와 대조해 해소 확인. 최종 구현에서 해당 기존 테스트가 **수정 없이** 통과 |
| SPEC-002 | High | Non-goal 4가 "커밋 금지"와 "PR 생성"을 동시에 규정해 모순이고, AC-14가 검증 불가 | Non-goal 4를 재작성해 브랜치 커밋·푸시를 허용하고 `main` 머지·태그·`chezmoi apply`를 금지. AC-16으로 검증 조건 3개와 명령을 명시 | 라운드 2 리뷰어가 해소 확인 |
| SPEC-006 | High (신규) | 새로 쓴 AC-16 (i)이 `origin/main`을 `4fd0899`로 고정했으나 실제 `origin/main`은 이미 `e61cee8`이어서, 올바르게 작업해도 결정적으로 실패하는 기준 | AC-16 (i)을 도달 가능성 검사로 교체: `git merge-base --is-ancestor <branch HEAD> origin/main`이 비영 종료. 무관한 머지에 영향받지 않고 "이 작업이 머지됐는가"만 측정 | 라운드 3 리뷰어가 `.git/packed-refs`와 reflog를 직접 읽어 확인. 그 시점 `origin/main`은 **또** `e039ec58`로 진행돼 있었다 — 고정 SHA를 버린 판단이 즉시 검증됐다 |

Plan과 코드 리뷰에서는 blocking finding이 발생하지 않았다.

## Plan approval

- Approval timestamp: 2026-09-04T08:07:10Z
- Plan digest: `0665fd5c433a77a41bddd3dab80d6e0c69fb5a74c2b7b0ded27c6b142fd51246`

승인 직전 확인: 승인 digest와 파일 digest가 일치했고, `approve-plan`이 통과 Plan 리뷰의 digest와도 대조했다. 승인 게이트는 이 실행에서 **한 번만** 열렸다.

## Changed files

| 파일 | 변경 |
|---|---|
| `dot_claude/skills/quality-goal/scripts/quality_state.py` | **프로덕션 변경은 이 6줄뿐.** `set_artifact()`의 진입 검사를 `state = _require_state(state)` + `if kind != "report": _require_active(state)`로 바꿔, `report` 한 kind에 대해서만 터미널 불변성을 면제한다. docstring에 면제 이유를 기록. `_require_active()` 자체, `record_review()`, `record_review_validation_failure()`, 상수는 손대지 않았다 |
| `dot_claude/skills/quality-goal/SKILL.md` | 버전 `4.0.0` → `4.1.0`. Stage table 터미널 행에 자동 전이 후 등록 지시(문장 D3) 추가. `### Terminal` 절에 (d) 선등록 지시(D1)와 자동 전이 후 등록 가능 서술(D2) 추가. 첫 문단에 전방 참조 추가(`CANCELLED` **뒤**에 삽입해 180자 윈도우 계약을 보존) |
| `dot_claude/skills/quality-goal/tests/test_quality_state.py` | 신규 테스트 10개 추가 — `TerminalReportRegistrationTests` 8개, `CLITests` 2개. 기존 테스트 본문은 한 줄도 변경하지 않았다 |
| `dot_claude/skills/quality-goal/tests/test_content_contracts.py` | 신규 계약 테스트 `test_terminal_report_registration_ordering_contract` 1개 추가. 버전 pin `"4.0.0"` → `"4.1.0"` 한 줄 갱신 — 기존 테스트에 가한 유일한 수정 |

## Verification evidence

모든 명령은 오케스트레이터가 Codex의 주장과 독립적으로 직접 실행했다. 작업 디렉터리는 `dot_claude/skills/quality-goal/`, 인터프리터는 `/opt/homebrew/bin/python3`(3.14.7)이다.

### 결함 해소 실측 — 이 작업의 핵심 증거

동일한 재현 스크립트를 변경 전후로 실행한 대조다.

| 경로 | 변경 전 | 변경 후 |
|---|---|---|
| `REVIEW_LIMIT_EXHAUSTED:spec` (spec 3라운드) | `set-artifact --kind report` → **exit 3** `error: terminal state is immutable: NEEDS_REDESIGN`, `artifacts.report=None` | **exit 0**, `artifacts.report`에 경로 등록 |
| `RECURRING_BLOCKING_FINDING:SPEC-A` (spec 2라운드, 한도 3 미도달) | **exit 3**, `artifacts.report=None` | **exit 0**, `artifacts.report`에 경로 등록 |
| 전이 후 라운드 재시도 | exit 2 `review for spec requires stage SPEC_REVIEW, got NEEDS_REDESIGN` | **exit 2 (가드 보존)** |

### 테스트

| 범주 | 명령 | 종료 코드 | 결과 |
|---|---|---:|---|
| 표적 | `python3 -m unittest tests.test_quality_state.TerminalReportRegistrationTests` | 0 | Ran 8 tests — OK |
| 표적 | `python3 -m unittest tests.test_quality_state.CLITests.test_cli_registers_report_after_limit_exhausted_transition tests...recurring_finding_transition` | 0 | Ran 2 tests — OK |
| 회귀 | `python3 -m unittest tests.test_quality_state.ReviewValidationRetryTests.test_terminal_states_are_immutable_for_active_only_mutators` | 0 | Ran 1 test — OK, **수정 없이** |
| 회귀 | `python3 -m unittest tests.test_quality_state.ArtifactTests` | 0 | Ran 2 tests — OK, **수정 없이** |
| 회귀 | `python3 -m unittest tests.test_content_contracts.QualityGoalSkillContentTests.test_terminal_report_is_registered_before_transition_contract` | 0 | OK — 180자 윈도우 계약(AC-12)이 CODE-002 편집 후에도 **수정 없이** 통과 |
| 전체 | `python3 -m unittest discover -s tests` | 0 | **Ran 240 tests — OK** (기준선 229 + 11) |
| 크기 계약 | `wc -l SKILL.md` | 0 | 372줄, 500줄 미만 |

### 뮤테이션 테스트 — CODE-001 수정의 실효 확인

`scripts/`와 `tests/`를 저장소 밖 임시 디렉터리로 복사해 `set_artifact`를 무조건 `_require_active`로 되돌린(결함 복원) 뒤 정밀화된 AC-5 테스트를 실행: **`FAILED (failures=12)`**. 수정 전 형태(`assertRaises(StateError)`)로는 통과했을 회귀를 이제 감지한다. 저장소 자체는 면제를 유지하며 스위트가 그린이다.

코드 리뷰 라운드 2가 이 수치를 **독립적으로 예측해 일치시켰다** — 소스만 읽고 영향 범위를 `4개 터미널 상태 × 3개 부적합 경로 = 12`로 계산했고, 비터미널 `CLASSIFIED` 루프는 그 뮤테이션에서 그린으로 남는다는 것까지 맞혔다. 또한 세 부적합 경로(없는 파일·디렉터리·빈 문자열) 모두 `StateError`만 발생하고 `TransitionError`·`FilesystemError` 같은 하위 클래스가 끼지 않으므로 정확 타입 단정이 15개 subTest 전부에서 성립함을 확인했다.

### 기존 테스트 무결성

| 확인 | 결과 |
|---|---|
| `git diff -U0 tests/ \| grep '^-' \| grep -v '^---'` | 삭제·변경된 줄이 **버전 pin 한 줄뿐** |
| 테스트 이름 대조(`comm -13` base vs 현재) | 정확히 **11개 추가, 0개 삭제**. Plan 역매핑표와 1:1 일치 |
| 함수 개수 | `test_quality_state` 131 → 141, `test_content_contracts` 52 → 53 |

### 미구성 범주 (통과로 기록하지 않음)

| 범주 | 근거 | 기록 |
|---|---|---|
| 타입 검사 | `find <repo> -maxdepth 3 \( -name mypy.ini -o -name .mypy.ini -o -name pyrightconfig.json -o -name pyproject.toml \) -not -path "*/.git/*"` → 출력 없음 | **not configured** |
| 린트 | `find <repo> -maxdepth 3 \( -name .ruff.toml -o -name ruff.toml -o -name .flake8 -o -name setup.cfg -o -name tox.ini \) -not -path "*/.git/*"` → 출력 없음 | **not configured** |
| 빌드 | 빌드 산출물이 없는 dotfiles 저장소 | **not applicable** |
| E2E | 승인 Spec의 Test strategy가 `unittest` 스위트로 검증 완결을 규정 | **not applicable** |

### AC별 자체 감사 (코드 리뷰 전 수행)

사용자 요구사항이다. Codex가 테스트를 적게 넣는 경향이 #66에서 확인됐으므로, 승인 Plan의 역매핑표대로 AC마다 테스트가 대응하는지 코드 리뷰를 요청하기 **전에** 감사했다.

- Plan이 이름을 못박은 11개 테스트가 **전부 존재**하며 초과도 누락도 없다(base 대비 추가된 이름이 정확히 그 11개).
- 각 본문을 읽어 해당 AC를 실제로 검증함을 확인했다. AC-1은 spec·plan·code 세 artifact를 순회하며 artifact별 digest 전제조건을 정확히 처리하고, AC-2는 `rounds.spec == 2`(한도 3 미도달)에서 재발 전이를 확인하며, AC-4는 **존재하는 정규 파일**을 써서 경로 검증이 대신 예외를 내는 함정을 피하고 `assertIs(type(...), TransitionError)`로 정확한 타입을 보며, CLI 테스트는 종료 코드와 `load_state()` 재조회를 모두 확인한다.

### 범위 경계

| 조건 | 확인 |
|---|---|
| `chezmoi apply` 실행 | **없음**. Codex 프롬프트에서 `chezmoi` 일체를 금지했고 실행 기록에도 없다 |
| Codex의 git 쓰기 작업 | **없음**. 워크트리에만 변경을 남겼다 |
| 허용 경로 밖 변경 | **없음**. `git status`가 네 파일 + 문서 디렉터리만 보고 |

## Remaining advisory findings

블로킹이 아닌 잔여 findings다. 전부 Low다.

| ID | 내용 | 처리 | 영향 |
|---|---|---|---|
| SPEC-009 | AC-11의 위치 검증 방법이 본문 전체 검색이라, 문장이 엉뚱한 절에 있어도 통과 | **해소됨** — Plan T4가 섹션 슬라이싱 방식으로 구체화하고 구현이 그대로 따랐다. 신규 계약 테스트는 Terminal 절과 Stage table 행을 각각 잘라 검사하며 해당 행이 정확히 1개인지도 확인한다 | 없음 |
| PLAN-001 | T2 서술이 `record_review()`에 dict를 넘기는 것처럼 읽힘 (실제 시그니처는 파일 경로) | **Codex 프롬프트에 보완 지시로 반영** — Plan 문서를 수정하면 승인 digest가 어긋나므로 문서는 그대로 두었다. 구현은 `write_json()`으로 파일을 만들어 경로를 넘긴다 | 없음 |
| PLAN-002 | 신규 테스트 개수가 문서 내에서 불일치(File map "8종" vs 실제 10종, 감사 문장 "10개" vs 표 11행) | 동일하게 프롬프트로 반영. 실제 추가는 11개로 확인 | 문서 정합성만. 후속 수정 권장 |
| PLAN-003 | `code` artifact의 digest 면제 근거를 `_ARTIFACT_KEYS`로 잘못 지목(실제는 `record_review()`의 `artifact in {"spec","plan"}` 가드) | 동일하게 프롬프트로 반영. 결론 자체는 옳았다 | 문서 정확성만. 후속 수정 권장 |
| PLAN-004 | CLI 테스트가 T2의 test-first 증거 명령에서 빠짐 | 동일하게 프롬프트로 반영. 두 CLI 테스트의 실패·통과 증거를 별도로 남겼다 | 없음 |
| PLAN-005 | 비터미널 + `kind="report"` + 부적합 경로 조합이 어떤 테스트도 덮지 않음 | **해소됨** — AC-5 테스트에 `state_at("CLASSIFIED")` 루프를 추가했다 | 없음 |
| CODE-001 | AC-5 테스트가 `StateError`를 assert하는데 `TransitionError`가 하위 클래스라, 면제 제거 회귀를 감지하지 못함 | **해소됨** — 두 루프 모두 `assertIs(type(context.exception), StateError)`로 정밀화. 뮤테이션 테스트로 실효 확인(12건 실패) | 없음 |
| CODE-002 | Terminal 절 첫 문단이 무조건적 명령이고 예외가 두 문단 뒤에 있어 전방 참조 부재 | **해소됨** — `CANCELLED` 뒤에 전방 참조를 추가하고 180자 윈도우 계약 통과를 확인 | 없음 |

**후속 권장**: PLAN-002와 PLAN-003은 Plan 문서의 정합성·정확성 문제로 남아 있다. 승인 digest 보존 때문에 이번 실행에서 문서를 고치지 않았다. 구현과 검증에는 영향이 없다.

## 이 실행이 (d) 순서를 실제로 사용했다는 기록

사용자 제약이 요구한 항목이다. **이 실행 자체가 #43을 밟을 수 있었고, (d) 순서를 적용해 보고서 포인터를 살렸다.**

이 보고서를 렌더한 뒤 `set-artifact --kind report`로 **먼저 등록하고**, 그 다음에 코드 리뷰 라운드 2의 `record-review`를 호출했다. 등록 시점의 stage는 `CODE_REVIEW`(비터미널)였으므로 등록이 통과했다.

우회를 사용했는지에 대한 정확한 기술: **이번 실행에서는 결함을 우회할 필요가 없었다.** 코드 리뷰 라운드 2 시점에 자동 전이 위험이 구조적으로 없었기 때문이다 — 라운드 2는 code 한도 3에 미달이고, 라운드 1의 blockers가 빈 목록이어서 `RECURRING_BLOCKING_FINDING` 분기가 성립할 수 없었다. 그래도 (d) 순서를 지킨 것은 사용자 지시이자 이 작업이 확립하려는 규율이기 때문이다.

한편 **이 실행의 Spec 단계는 결함의 사정권 안에 있었다.** Spec 라운드 3은 한도(3)의 마지막 라운드였고, 만약 PASS가 아니었다면 `record_review`가 그 자리에서 `REVIEW_LIMIT_EXHAUSTED:spec`으로 전이해 보고서 등록이 `exit 3`으로 거부됐을 것이다. 그 라운드에 진입하기 전 이 위험을 명시하고 (d) 순서를 준비했다. 라운드 3이 PASS해 실제로 발동하지는 않았다.

## 코드 리뷰 라운드 2의 확인 사항

라운드 2는 blocker와 finding을 하나도 내지 않았다. 확인된 내용을 기록한다.

- **CODE-001 해소 완결**: 두 루프 모두 정밀화됐고, 정확 타입 단정이 해당 테스트의 15개 subTest 전부에서 올바른 단정임을 소스 대조로 확인했다.
- **CODE-002 해소 완결**: 새 절이 `CANCELLED` 뒤, 즉 정규식이 이미 매칭을 끝낸 지점 뒤에 삽입돼 180자 윈도우(0-180)가 손상되지 않는다. 정규화 텍스트에서 두 앵커 사이는 여전히 ` and ` 다섯 글자뿐이다.
- **회귀 없음**: `scripts/quality_state.py`는 이번 라운드에 손대지 않았고 라운드 1이 통과시킨 상태와 바이트 동일하다. `tests/test_content_contracts.py`도 라운드 1과 바이트 동일하다. 축자 고정된 문장 D1·D2·D3은 변경되지 않았다. 나머지 신규 테스트 10개 중 어느 것도 바뀌지 않았다.
- **Terminal 절 가독성**: 세 문단이 모순 없이 두 순서를 모두 다루며, 첫 문단의 전방 참조가 이미 전이된 분기의 독자를 세 번째 문단으로 이끈다.
- **미재실행 명령 하나의 정산**: Plan 검증 항목 8(`ast.parse` 문법 확인)은 라운드 2에서 다시 실행하지 않았으나, 해당 파일이 라운드 1 통과 상태와 바이트 동일하고 라운드 2의 전체 스위트가 `quality_state`를 성공적으로 import하므로 파싱·컴파일 성공을 포함한다.
- 리뷰어가 finding으로 올리지 않은 사소한 관찰: 첫 문단의 "Then transition into the selected terminal state"가 무조건문으로 남아 있어, 이미 전이된 분기의 독자는 세 번째 문단에 의존해 전이가 끝났음을 안다. 전방 참조가 그 경로를 열어주므로 CODE-002의 요구 해소 조건은 충족됐다고 판정했다.

## Final status

- Status: `completed`
- Machine-readable reason: `COMPLETED`

채택안은 이슈 #43의 **(b) + (d)**다. (a)안(자동 전이 제거)은 실측으로 기각했다 — 현재 "한도 소진 후 다음 라운드 거부"를 stage 검사가 겸하고 있어(재현 시 거부 사유가 `requires stage SPEC_REVIEW, got NEEDS_REDESIGN`이었다), 자동 전이를 제거하면 한도 소진 경로는 기존 `expected_round > ROUND_LIMITS` 검사가 막지만 **재발 경로는 막지 못한다**(한도 3인 spec의 라운드 2에서 종결하면 라운드 3이 `3 ≤ 3`으로 통과). 즉 (a)는 제거가 아니라 제거 후 가드 재구현이며 상태 스키마 변경까지 요구하고, 결정적 종결을 포기한다.

(b)는 부수 효과로 `record_review_validation_failure()`의 `REVIEW_OUTPUT_INVALID` → `BLOCKED` 자동 전이 경로도 코드 추가 없이 함께 해소한다 — 이슈 본문이 예측만 하고 어떤 안도 명시적으로 다루지 않은 경로다. 신규 테스트 AC-9가 이를 검증한다.

배포는 수행하지 않았다. `chezmoi apply`는 사용자가 별도로 결정한다.
