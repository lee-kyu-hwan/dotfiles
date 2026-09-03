# Quality Goal Report

- Task ID: 20260903T092537Z-44-37-38-quality-goal-리뷰-루프-결함-3건-수정-라운드-33f2fb89
- Mode: standard
- Status: COMPLETED
- Created: 2026-09-03T09:25:37Z
- Updated: 2026-09-04T00:10:00Z
- Source goal: #44 #37 #38 quality-goal 리뷰 루프 결함 3건 수정 — 라운드 2+ prior findings 전문 전달, 미검증 사유 REVISE의 라운드 소모 방지, no-PASS-when-unverified 결정적 게이트 승격
- Base revision: `5ed7b57387d6a271e8e014091ff8143f488e0d29`
- Implementation commit: `2336d23`

## Classification

선택 모드: **standard** (사용자 명시 모드도 standard이므로 다운그레이드 확인 불필요).

**strict 트리거 없음.** 인증·인가·테넌시, 결제·정산 회계, PII·보안통제·시크릿,
DB·영속 스키마 마이그레이션·파괴적 작업·어려운 롤백, 공개·외부 API·웹훅·큐·동시성,
프로덕션 인프라 중 어느 것도 해당하지 않는다. `review.schema.json`은 JSON 검증 계약이지
영속 데이터 스키마가 아니고, 롤백은 `git revert`와 경로 지정 배포 재실행으로 단순하다.

**standard 조건 성립.**

1. **다중 파일·모듈** — `SKILL.md`, `scripts/validate_review.py`,
   `scripts/quality_state.py`, `schemas/review.schema.json`,
   `dot_claude/agents/quality-reviewer.md`, `tests/` 3개 파일과 fixture 2개,
   `docs/quality-goal-maintenance.md`가 함께 바뀐다.
2. **비자명한 공유 인터페이스** — `--prior` 페이로드 형태와 `review.schema.json`의
   evidence 항목 형태는 오케스트레이터·리뷰어·검증기·픽스처가 공유하는 계약이며,
   `SchemaDriftTests`가 스키마와 Python 상수의 일치를 강제한다.
3. **상태 전이 변경** — #37이 미검증 사유 REVISE가 `ROUND_LIMITS`를 소모하지 않도록
   리뷰 라운드 회계를 바꾼다.
4. **대안·비목표·수용 기준의 명시 필요** — #38이 `verified` 불리언과 `status` enum 두
   대안을 제시했고 스키마 버전 처리를 미결로 남겼다.

**이슈 라벨 증거** — #44 `bug`, #37 `enhancement`, #38 `enhancement`. 라벨은 상향
근거로만 쓰였고 risk 스캔 결과를 대체하지 않았다.

**착수 전 확인(#57).** 배포본 `SKILL.md`의 라운드 수 서술(spec 3 / plan 2 / code 3)이
`quality_state.py:69`의 `ROUND_LIMITS`와 일치함을 확인했다. 불일치가 없어 조치 대상이
없었다.

**선행 실행과의 관계.** 이 실행은 `docs/development/2026-08-27-quality-goal-review-loop/`
의 Spec(952행, `NEEDS_REDESIGN`)을 초안으로 재사용했다. 그 Spec이 담았던 R6(spec 라운드
한도 2→3)과 R7(루브릭 라운드 수 단언)은 이후 v3.0.0으로 출시됐으므로 이번 범위에서
제외했다. 선행 실행의 미해소 findings 중 R6에 종속했던 SPEC-012·013·015는 함께
소멸했고, 남은 SPEC-006·SPEC-011은 이번 Spec의 D3·D9로 선반영해 해소했다.

## Review history

| 아티팩트 | 라운드 | 점수 | 판정 | 블로커 | Critical/High | 게이트 |
|---|---|---|---|---|---|---|
| Spec | 1 | 84 | REVISE | SPEC-001 | 1 | 실패 — `score_below_85`, `verdict_not_pass`, `blockers_present`, `critical_or_high_finding`, `check_failed:acceptance_criteria_objective` |
| Spec | 2 | 93 | **PASS** | 없음 | 0 | **통과** — `{"passed":true,"reasons":[]}` |
| Plan | 1 | 89 | **PASS** | 없음 | 0 | **통과** — `{"passed":true,"reasons":[]}` |
| Code | 1 | 62 | REVISE | CODE-001 | 1 | 실패 — `verdict_not_pass`, `blockers_present`, `critical_or_high_finding`, `check_failed:acceptance_criteria_met` |
| Code | 2 | 90 | **PASS** | 없음 | 0 | **통과** — `{"passed":true,"reasons":[]}` |

소모 라운드: spec 2/3, plan 1/2, code 2/3.

**라운드 간 변화 — Spec.** 라운드 1의 5건(High 1 · Medium 2 · Low 2)을 전부 개정했고,
라운드 2 리뷰어가 5건 전부의 해소를 개별 증거와 함께 확인했다. 점수 84 → 93.
라운드 2가 남긴 것은 Low 2건(SPEC-006·007)뿐이며 게이트를 막지 않았다.

**라운드 간 변화 — Code.** 라운드 1의 4건(High 1 · Medium 1 · Low 2)을 bounded Codex
수정 라운드로 전부 개정했다. 테스트 208 → 229개. 라운드 2 리뷰어가 4건 전부의 해소를
확인하고 Low 3건(CODE-005·006·007)을 새로 남겼다. 점수 62 → 90.

**리뷰어 산출물 미전달 1건.** Spec 라운드 1의 첫 리뷰어가 24턴 한도에서 JSON을 내지
못하고 종료했다. 계약에 따라 `record-review-error`로 기록하고(라운드 미소모 —
`rounds.spec`은 0 유지) 새 리뷰어를 1회 재시도해 산출물을 받았다. 이것은 이 작업이
고치려는 #37이 대상으로 하는 리뷰어 예산 소진 현상의 실측이다.

## Blocking-finding resolutions

| ID | 아티팩트 | 심각도 | 해소 내용 | 검증 증거 |
|---|---|---|---|---|
| SPEC-001 | Spec | High | `validate_review`는 `round >= 2`에 prior가 없으면 무조건 거부하는데(`validate_review.py:272`) I3의 CLI에 `--prior`가 없어 **라운드 2 이상의 미검증 REVISE 경로가 통째로 도달 불가**였다. R2.4b를 신설해 `record_review`(`quality_state.py:599-607`)와 동일하게 내부에서 prior를 조립하도록 규정하고, `--prior` 인자 추가를 금지했다. AC-61(라운드 2 종단)·AC-62(`--prior` 부재)와 D14(기각 대안 2건)를 추가했다 | 라운드 2 리뷰어 확인: R2.4b가 근거하는 두 코드 사실(`validate_review.py:270-273`, `quality_state.py:599-607`)을 직접 대조하고 AC-61·62·D14·I3 전문·추적표 행의 존재를 확인. 구현 후 `test_round_two_unverified_review_assembles_prior_from_state`가 실행 단언으로 고정 |
| CODE-001 | Code | High | Codex 구현 라운드가 실행 판정 대상 약 50개 AC에 테스트 메서드를 7개만 넣어, AC-19~AC-29·AC-32·AC-44·AC-61·AC-63이 전혀 검증되지 않았고 AC-3·10·11·37·39·40·42·52가 부분 커버였다. bounded 수정 라운드에서 테스트 메서드 21개를 추가해 각 기준에 대응 단언을 붙이고, 모든 부정 케이스가 **특정 오류 문자열**을 단언하도록 바꿨다 | 스위트 208 → 229개 통과(exit 0), 파일별 46/131/52로 합계 일치. 라운드 2 리뷰어가 기준별 테스트 메서드 대응을 전수 확인. 변이 검증 13/13 검출 |

## Plan approval

- Approval timestamp: `2026-09-03T14:20:12Z`
- Plan digest: `a4ee164fce17f2c63999d8752790fd8de53e2d8d25eb9bad5a784a9eec1380c4`

승인 게이트에서 Plan 전문과 라운드 1이 남긴 advisory 4건, 그리고 `approve_plan`이 Plan
digest를 통과 리뷰의 digest에 고정하므로 승인 후에는 Plan을 고칠 수 없다는 제약을 함께
제시했다. 사용자는 그 상태로 승인하고 Plan 라운드 2를 예비로 남기는 쪽을 택했다.
`approve_plan`이 기록한 digest는 Plan 리뷰 라운드 1이 통과시킨 digest와 동일하다.

## Changed files

`git diff --name-only 5ed7b57...HEAD` 기준 13개. 전부 allow-list(`dot_claude/skills/quality-goal/`,
`dot_claude/agents/quality-reviewer.md`, `docs/`) 안이다.

| 경로 | 의도한 변경 |
|---|---|
| `dot_claude/skills/quality-goal/scripts/validate_review.py` | prior에 `open_findings`·`resolved_finding_ids` 검증 추가, 최상위 unknown 키 거부, `EVIDENCE_FIELDS`에 `verified` 추가 + `EVIDENCE_STRING_FIELDS` 분리 + boolean 타입 검사, PASS+미검증 금지. `evaluate_gate`는 불변 |
| `dot_claude/skills/quality-goal/scripts/quality_state.py` | `record_review_unverified` 함수와 `record-review-unverified` 서브파서 신설, 초기 상태에 `review_unverified_retry: None`, `record_review`에 재수행 digest 바인딩 검사와 초기화 1줄 추가. 자동 전이 블록·`ROUND_LIMITS`·`ALLOWED_TRANSITIONS`·`TERMINAL_STATES`는 불변 |
| `dot_claude/skills/quality-goal/schemas/review.schema.json` | evidence 항목에 `verified`(boolean) 필수 추가. `additionalProperties: false`와 `uniqueItems` 2곳은 유지 |
| `dot_claude/skills/quality-goal/SKILL.md` | 리뷰 호출 계약을 구조화 prior로 확장, 미검증 REVISE 정책 신설, `version` 3.0.0 → 4.0.0. 342 → 358행(한도 500) |
| `dot_claude/agents/quality-reviewer.md` | 라운드 2+ open finding 해소 판정과 ID 재사용 규칙, 모든 evidence에 `verified` 기입 규칙. frontmatter·도구 목록·BLOCKED payload 규칙은 불변 |
| `dot_claude/skills/quality-goal/tests/test_validate_review.py` | prior 확장·`verified`·PASS 금지 회귀 테스트, `valid_review()` 헬퍼에 `verified` 추가. `:444`의 `for field in ("claim", "location")` 루프는 불변 |
| `dot_claude/skills/quality-goal/tests/test_quality_state.py` | `record-review-unverified` 수용·거부 전수, digest 바인딩, 상태 키, PASS+미검증 거부 테스트. 39 → 131개 |
| `dot_claude/skills/quality-goal/tests/test_content_contracts.py` | `version` 기대값 4.0.0, SKILL.md·리뷰어 계약 정규식 단언, 에이전트 파일 공용 헬퍼 |
| `dot_claude/skills/quality-goal/tests/fixtures/review-valid-plan.json` | evidence에 `"verified": true` |
| `dot_claude/skills/quality-goal/tests/fixtures/review-high-finding.json` | evidence에 `"verified": true` |
| `docs/quality-goal-maintenance.md` | 추적 목록에서 #37·#38 제거, #43을 의도적 비범위로 명시, 권위 목록이 GitHub 열린 이슈임을 밝히는 문장과 조회 명령 추가 |
| `docs/development/2026-09-03-quality-goal-review-loop/spec.md` | 산출물 |
| `docs/development/2026-09-03-quality-goal-review-loop/plan.md` | 산출물 |

**변경하지 않은 것** (결정적으로 확인): `dot_claude/skills/quality-goal/references/` 5개
파일, `tests/fixtures/verification-pass.json`, `ROUND_LIMITS`,
`record_review`의 자동 전이 블록 9줄, `.gitignore`, 그 밖의 모든 저장소 파일.

**초기 dirty 경로는 0건**이었고 보존할 사전 변경이 없었다.

## Verification evidence

### 실행한 명령

| 명령 | 종료 코드 | 증거 |
|---|---|---|
| `git rev-parse --is-inside-work-tree` / `rev-parse HEAD` | 0 | base `5ed7b57387d6a271e8e014091ff8143f488e0d29` |
| `codex --version` | 0 | `codex-cli 0.152.1` |
| `codex exec --sandbox read-only --ephemeral --model gpt-5.6-terra -c model_reasoning_effort="low"` (preflight) | 0 | 비어 있지 않은 응답 — 선택 모델 확인 |
| `git check-ignore -v .claude/quality-state/` | 0 | `.gitignore:25` — 런타임 상태가 이미 무시됨 |
| `gh issue view 44/37/38` | 0 | 요구사항 입력 확보 |
| `quality_state.py select-resume` | 0 | `{"match":null}` — 재개 대상 없음 |
| `quality_state.py init` / `classify` / `capture-baseline` | 0 | standard, 근거 7건, base 기록, dirty 0건 |
| **기준선** `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/quality-goal/tests -p 'test_*.py'` | 0 | **`Ran 201 tests` / `OK`** |
| 정적 교차 확인: 세 테스트 파일의 `def test_` 개수 | — | 50 + 112 + 39 = 201 |
| `validate_review.py validate` (spec r1) | 0 | `{"valid":true,"errors":[]}` |
| `validate_review.py gate` (spec r1) | 3 | 사유 5건 |
| `quality_state.py record-review-error --artifact spec --round 1` | 0 | 리뷰어 산출물 미전달 기록, `rounds.spec` 0 유지 |
| `quality_state.py record-review` (spec r1) | 0 | `rounds.spec: 1`, `open_finding_ids.spec: ["SPEC-001"]` |
| `validate_review.py validate --prior` (spec r2) | 0 | `{"valid":true,"errors":[]}` |
| `validate_review.py gate --prior` (spec r2) | 0 | `{"passed":true,"reasons":[]}` |
| `quality_state.py transition` SPEC_PASSED → PLAN_REVIEW | 0 | 가드 통과 |
| `validate_review.py validate` / `gate` (plan r1) | 0 / 0 | `{"passed":true,"reasons":[]}` |
| `quality_state.py approve-plan` | 0 | digest `a4ee164f…`, 리뷰 digest와 동일 |
| `codex exec --sandbox workspace-write --ephemeral --model gpt-5.6-terra -c model_reasoning_effort="high"` (구현) | 0 | `status: completed`, 11개 파일 |
| `codex exec …` (bounded fix) | 0 | `status: completed`, 4개 파일, `plan_deviations` 1건 |
| **최종** `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/quality-goal/tests -p 'test_*.py'` | 0 | **`Ran 229 tests` / `OK`** (기준선 201 → 구현 후 208 → 최종 229) |
| 파일별 discover (`test_validate_review.py` / `test_quality_state.py` / `test_content_contracts.py`) | 0 | 46 / 131 / 52 = 229 |
| `python3 -m json.tool …/schemas/review.schema.json` | 0 | 스키마 파싱 |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile …/validate_review.py …/quality_state.py` | 0 | 두 스크립트 컴파일 |
| `wc -l …/SKILL.md` | 0 | **358** (한도 500 미만, AC-54) |
| `grep '^version:' …/SKILL.md` | 0 | `version: 4.0.0` (AC-46) |
| `grep -n 'ROUND_LIMITS = ' …/quality_state.py` | 0 | `{"spec": 3, "plan": 2, "code": 3}` 불변 (AC-58) |
| `git diff --name-only $BASE...HEAD -- …/references/` | 0 | 빈 출력 — 5개 파일 불변 (AC-58) |
| `git diff --name-only $BASE...HEAD -- …/tests/fixtures/verification-pass.json` | 0 | 빈 출력 — 불변 (AC-51 둘째 절) |
| **AC-57** `git show $BASE:…/quality_state.py \| sed -n '/^    recurring = next/,/REVIEW_LIMIT_EXHAUSTED/p'` vs 작업 트리 동일 `sed`, 이후 `diff` | 0 | **양쪽 9줄 동일** — #43 블록 불변 |
| **AC-56** `git diff --name-only $BASE...HEAD \| grep -vE '^(dot_claude/skills/quality-goal/\|dot_claude/agents/quality-reviewer\.md$\|docs/)'` | 1 (grep) | 빈 출력 — allow-list 위반 없음 |
| **AC-53** `grep -rn 'output-schema' …/quality-goal \| grep -c 'review.schema.json'` | 1 (grep) | 0건 — `review.schema.json`은 Codex에 전달되지 않는다 |
| **AC-62** `quality_state.py record-review-unverified --state x --review y --artifact-digest z --prior w` | 2 | argparse가 `--prior`를 거부 |
| **AC-51** 파이썬 판정 — fixture 2개 `json.load` + 헬퍼 2개 호출 | 0 | 4곳의 evidence 객체가 모두 `{claim, location, verified}` |
| **AC-60** 파이썬 판정 — `spec.md`의 요구사항 ID 집합 vs 추적표 행 집합 | 0 | 42건 동등, 인용된 AC 전부 실재 |
| `quality_state.py record-verification` (r1, r2) | 0 / 0 | 지문 기록, `valid: true` |
| `validate_review.py validate` / `gate` (code r1) | 0 / 3 | 사유 4건 — `check_failed:acceptance_criteria_met` 포함 |
| `validate_review.py validate --prior` / `gate --prior` (code r2) | 0 / 0 | `{"passed":true,"reasons":[]}` |
| `git status --porcelain` (Codex 라운드마다) | 0 | Codex가 보고한 `changed_files`와 정확히 일치 |
| `git commit` | 0 | `2336d23` |

### AC-55 변이 검증 (신규 규칙 13건 전수)

각 항목마다 해당 규칙을 소스에서 무력화 → `__pycache__` 제거 → 전체 스위트 실행 →
소스 복원 → 백업과 바이트 비교의 순서로 수행했다. **13건 전부 대응 테스트가 검출했다.**

| # | 무력화 대상 | 변이 시 종료 코드 | 검출 |
|---:|---|---:|---|
| 1 | R1.5 `open_finding_ids` 커버리지 | 1 (failures=1) | ✅ |
| 2 | R1.8 prior 최상위 unknown 키 | 1 (failures=1) | ✅ |
| 3 | R1.2 `resolution_*` 문자열-또는-null | 1 (failures=2) | ✅ |
| 4 | R1.6 resolved ∩ open 교집합 | 1 (failures=1) | ✅ |
| 5 | R2.3 미검증 REVISE 트리거 조건 | 1 (failures=4) | ✅ |
| 6 | R2.4-4 현재-파일 digest 교차 검사 | 1 (failures=2) | ✅ |
| 7 | R2.5 폐기 2건 상한 | 1 (failures=2) | ✅ |
| 8 | R2.12 재수행 digest 바인딩 | 1 (failures=3) | ✅ |
| 9 | R3.3 PASS+미검증 금지 | 1 (failures=2) | ✅ |
| 10 | R3.2 `verified` boolean 타입 검사 | 1 (failures=1) | ✅ |
| 11 | R2.8 재수행 기록 초기화 | 1 (failures=2) | ✅ |
| 12 | R2.4b 내부 prior 조립 | 1 (errors=2) | ✅ |
| 13 | R2.13 (아티팩트, 라운드) 일치 술어 | 1 (errors=1) | ✅ |

복원 후 전체 스위트 재실행: `Ran 229 tests` / `OK`, exit 0.

### 검증 카테고리

| 카테고리 | 상태 | 근거 |
|---|---|---|
| 표적 테스트 | **실행됨** | 파일별 46 / 131 / 52, exit 0 |
| 전체 스위트 | **실행됨** | 229개, exit 0 |
| 타입 체크 | `not configured` | `tsconfig.json`·`package.json`·`Makefile`·`justfile` 부재 확인 |
| 린트 | `not configured` | `.pre-commit-config.yaml`에 gitleaks 훅만 존재(시크릿 스캔 전용) |
| 빌드 | `not configured` | `package.json`·`.github/workflows` 부재 확인 |
| E2E / 수동 검증 | **해당 없음** | 스킬 번들 성격상 E2E 대상이 없다. 그 역할은 위 변이 검증 13건과 범위·불변 명령(AC-56·57·58)이 수행했다. 통과로 기록하지 않는다 |

### 배포

**배포를 실행하지 않았다.** 사용자가 승인 게이트 이후 명시적으로 배포하지 않기로
결정했다. 배포본 `~/.claude/skills/quality-goal/SKILL.md`는 `version: 3.0.0`으로 남아
있으며, 이 실행 전체에서 경로 인자를 생략한 형태의 배포 명령을 실행한 적이 없다.
배포를 하게 되면 변경 파일 경로를 명시한 `chezmoi apply <경로>...` 형태만 사용한다.

**AC-59 판정과 그 기준 자체의 결함(기록).** 이 절의 초판은 배포 부재를 서술하면서
경로 인자가 없는 형태의 명령을 문장 안에 그대로 적었고, 그 **서술 문장 자체가**
AC-59의 판정 정규식에 걸려 기준이 실패했다. 문구만 고쳐 통과시켰고, 코드나 배포
사실은 바뀌지 않았다. 근본 원인은 AC-59의 판정 명령이 보고서 **전체**를 grep하도록
쓰였다는 점이다 — 기준의 의도는 "실행한 명령 표의 배포 행"만 보는 것이므로 명령이
의도보다 넓다. 후속 이슈 후보로 남긴다.

**터미널 전이 이후 보고서 편집(기록).** 위 문구 수정은 상태가 `COMPLETED`로 전이된
뒤에 이루어졌다. `set_artifact`는 report에 digest를 바인딩하지 않으므로
(`artifact_digests`의 report 슬롯은 `record_review`만 채운다) 기록된 어떤 digest도
무효화되지 않았고, `artifacts.report` 경로도 그대로다. 그럼에도 순서가 이상적이지
않았음을 밝힌다 — AC-59를 판정한 뒤에 전이했어야 했다.

## Remaining advisory findings

### Spec (라운드 2, Low 2건 — 통과한 Spec을 동결하고 Plan이 권위 서술을 제공했다)

| ID | 요약 | 처리 |
|---|---|---|
| SPEC-006 | Spec의 Test strategy 절이 변이 대상을 "신규 규칙 11개"로 적었으나 AC-55는 13개를 열거한다 | Plan이 13개를 권위로 확정했고, 실제로 13건을 수행했다. **해소** |
| SPEC-007 | Decision 인용 2건 오류 — R4.3의 `(D9)`는 D11이어야 하고, Non-goal 1의 `(D3)`는 D4여야 한다. 라운드 2 개정에서 D3을 끼워넣으며 밀린 번호를 본문에서 고치지 않은 결과다 | Plan이 두 곳 모두 정정해 권위 서술을 제공했다. Spec 본문의 인용은 그대로 남아 있다. **문서상 잔여** |

### Code (라운드 2, Low 3건)

| ID | 요약 | 영향 | 처리 |
|---|---|---|---|
| CODE-005 | 바인딩 검사를 `record_review`에서 앞으로 옮긴 결과, `record_review`와 `record_review_unverified`가 바인딩 대 한도 검사의 상대 순서가 달라졌다. `rounds[artifact] == ROUND_LIMITS[artifact]`이고 그 라운드에 다른 digest의 낡은 재수행 기록이 있는 입력에서 전자는 exit 2, 후자는 exit 3을 낸다 | Spec R2.4가 "같은 입력이 두 서브커맨드에서 다른 종료 코드를 내지 않게 한다"고 요구한 것과 어긋난다. **CLI로는 도달 불가** — `record_review_unverified`가 한도 초과 라운드에 재수행 기록을 저장하지 않고, `record_review`는 라운드를 기록할 때마다 그 키를 비운다. AC-23·26·31은 모두 충족된다 | 아래 "Plan 이탈" 항목에 잔여 발산을 명시해 기록으로 남긴다. 코드는 바꾸지 않는다 |
| CODE-006 | AC-25의 두 절 중 `--artifact-digest` 생략 거부에 실행 단언이 없다 | 동작 자체는 구성상 보장된다(`required=True` → `_ArgumentParser.error` → `StateError` → exit 2). 실행으로도 확인했다 | **AC-25의 argparse 절은 파서 선언과 1회 실측(exit 2)으로 판정했고 단위 테스트 단언은 없다**고 여기에 기록한다 |
| CODE-007 | `_prior_open_finding_ids`가 `prior.open_finding_ids`의 중복 항목을 거부한다. 어떤 요구사항도 이 규칙을 요구하지 않았고(R1.4는 `open_findings` 내부, R1.6은 `resolved_finding_ids`) 대응 테스트가 없다 | fail-closed 방향이고 `record_review`가 내부 조립하는 prior는 이미 중복이 걸러진 blocker 목록이라 실질 위험이 없다 | **R1 범위를 넘어선 의도적 fail-closed 추가**로 여기에 기록한다. 코드는 바꾸지 않는다 |

### Plan 이탈 1건 (승인 후, 기록된 이탈)

`record_review`의 재수행 digest 바인딩 검사를 **spec/plan 아티팩트 digest 교차 검사
앞으로 이동**했다. 승인된 Plan의 T2-2c는 라운드·한도 검사 뒤에 두라고 규정했으나, 그
위치에서는 등록된 spec/plan 아티팩트의 파일이 그대로인 경우 옛 오류
(`spec artifact digest mismatch`)가 먼저 발생해 **Spec AC-31의 메시지 보장이 도달
불가**였다. Spec이 수용 계약이고 Plan의 단계 순서는 수단이므로 Spec을 충족시켰다.
라운드 일치·한도 검사는 원래 위치에 두어 AC-23·AC-26의 순서와 종료 코드는 불변이고,
두 검사 모두 `StateError`라 종료 코드 변화도 없다. 이 이탈은 Plan 리뷰가 PLAN-001로
이미 지적했던 지점이며, Codex 결과의 `plan_deviations`와 검증 JSON의 `plan_deviation`에
기록되어 있다. **잔여 발산**은 위 CODE-005에 적은 대로이며 CLI로는 도달 불가다.

### Plan 라운드 1이 남긴 advisory (승인 게이트에서 사용자에게 제시함)

PLAN-001(바인딩 검사 위치)은 위 이탈로 해소됐다. PLAN-002(T6의 수행 주체·롤아웃 내
위치 미지정)는 오케스트레이터가 T6 전체를 커밋 이전에 수행하는 것으로 실행했고 그
결과가 위 검증 증거다. PLAN-003(행 범위 2건 미세 오차)·PLAN-004(대체 기록 필드 shape
미열거)는 구현에 영향을 주지 않았다. Plan 라운드 2는 사용하지 않고 예비로 남겼다.

## 이번 실행에서 발현한 quality-goal 스킬 자체의 결함 (실측)

이 실행은 수정 대상인 배포본 v3.0.0으로 돌았다. 우회하지 않고 기록한 관찰이다.

### #37의 재현 — 리뷰어 예산 소진

Spec 리뷰 라운드 1의 첫 리뷰어가 **24턴 한도에서 최종 JSON 없이 종료**했다.
`record-review-error`로 기록했고 `rounds.spec`은 0으로 유지되어 라운드는 소모되지
않았다. 다만 이 경로는 계약상 재시도가 1회뿐이며, 재시도도 실패했다면
`BLOCKED`/`REVIEW_OUTPUT_INVALID`로 종결됐을 것이다. 재시도 프롬프트에 턴 예산을
명시하고 증거 경로를 우선순위별로 정렬해 넘긴 뒤에는 8~26턴 안에서 모든 리뷰어가
산출물을 냈다. 이번 수정이 도입한 `record-review-unverified`는 well-formed 미검증
REVISE를 다루므로 이 사례(출력 자체가 없는 경우)와는 다른 경로이며, 두 경로가 별도
상태 키로 분리되어 종결 사유가 섞이지 않는다.

### #44의 재현 — 우회를 유지했다

라운드 2 이상에서 배포본 계약(`SKILL.md:256`)이 finding ID만 전달하므로, 계약대로면
Spec 라운드 2에는 blocker 1건(SPEC-001)의 ID만 갔을 것이고 Medium·Low 4건은 상태의
`open_finding_ids`가 blocker만 보존하는 탓에 전달 수단이 없었다. 우회로 **이전 라운드
findings 전문(설명·증거 위치·요구 해소책 + 오케스트레이터의 해소 주장·증거)을 리뷰어
프롬프트에 직접 포함**했다. 결과: Spec 라운드 2 리뷰어가 5건 전부의 해소를 개별 증거와
함께 확인했고, 코드 라운드 2 리뷰어도 4건 전부를 확인했다. 계약용 prior 파일은
`{"open_finding_ids": [...]}`로 최소 유지했다 — 배포본
`_prior_open_finding_ids`가 unknown 키를 검사하지 않는다는 성질(이번 수정의 R1.8이
닫는 구멍)에 의존하지 않기 위해서다.

### #38의 재현 — 미검증 표시가 산문뿐이다

모든 리뷰어가 미검증 항목을 `claim` 문자열 안의 산문(`NOT VERIFIED:` 등)으로만
표시했다. 배포본 스키마의 evidence 항목이 `{claim, location}`뿐이라 구조화된 필드가
없고 `evaluate_gate`는 evidence를 읽지 않는다. 리뷰어들이 정직해서 규칙이 작동했을
뿐이며, 이번 수정의 `verified` 필수 필드가 그 상태를 고친다.

### #43은 발현하지 않았다

`record_review`의 자동 터미널 전이는 라운드 한도 소진이나 recurring blocker에서만
발동한다. 이번 실행은 spec 2/3, plan 1/2, code 2/3으로 모두 한도 이전에 통과했고
recurring blocker도 없어 자동 전이 경로에 진입하지 않았다. 따라서 보고서 등록 시점이
사라지는 현상은 관측되지 않았다. **보고서 파일 경로**:
`docs/development/2026-09-03-quality-goal-review-loop/report.md`.

### 위생 항목

`.claude/quality-state/`는 `.gitignore:25`에 이미 등록되어 있어 런타임 상태가
`git status`에 노출되지 않는다. 별도 조치가 필요 없다.

변이 검증 중 `__pycache__` 오염이 오판을 만들 수 있어 모든 사이클에
`PYTHONDONTWRITEBYTECODE=1`과 `__pycache__` 제거를 넣었다. `.gitignore`가
`__pycache__/`를 덮어 `git status`에 보이지 않는다.

## Final status

- Status: `COMPLETED`
- Machine-readable reason: 없음 (`status_reason: null`) — 코드 리뷰 라운드 2가 PASS,
  블로커 0건, Critical/High 0건이고 오케스트레이터의 결정적 체크 4개가 모두 참이며,
  기록된 검증 워크스페이스 지문이 마지막 통과 코드 리뷰의 아티팩트 digest와 같다
  (`0d6f8b6f9fca4d5d2d5bce0441856e373fdfd46ce4d687af9ad66179776604f4`).

머지는 수행하지 않았다. 배포도 수행하지 않았다(배포본은 v3.0.0으로 유지).
