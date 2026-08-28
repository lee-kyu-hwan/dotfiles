# Quality Goal Report

- Task ID: 20260827T112608Z-44-37-38-quality-goal-리뷰-루프-결함-3건-수정-pri-f553db5a
- Mode: standard
- Status: NEEDS_REDESIGN
- Created: 2026-08-27T11:26:08Z
- Updated: 2026-08-27T12:25:00Z
- Source goal: #44 #37 #38 quality-goal 리뷰 루프 결함 3건 수정: --prior 입력 확장, 미검증 REVISE 라운드 정책, no-PASS 결정적 게이트 승격
- Base revision: 6d8ccad16b4f8345130fe56913a2eead4169030f

## Classification

선택 모드: **standard** (요청 모드 `auto`).

**strict 트리거 없음.** 인증·인가·테넌시, 결제·정산·쿠폰 회계, PII·보안통제·시크릿,
DB·스키마 마이그레이션·파괴적 작업·어려운 롤백, 공개·외부 API·웹훅·큐·멱등성·동시성,
프로덕션 인프라 중 어느 것도 해당하지 않는다. 변경 대상은 chezmoi 소스 트리의 로컬 개발
스킬(`dot_claude/skills/quality-goal`, `dot_claude/agents/quality-reviewer.md`)이고 롤백은
`git revert`로 단순하며, 이번 실행은 `chezmoi apply`를 하지 않으므로 배포본에 영향이 없다.

**standard 조건 4가지 모두 성립.**

1. **다중 파일·레이어** — `SKILL.md`의 Review invocation contract,
   `dot_claude/agents/quality-reviewer.md`의 리뷰어 계약, `schemas/review.schema.json`,
   `scripts/validate_review.py`의 게이트 엔진, `scripts/quality_state.py`의 상태 머신,
   `references/spec-rubric.md`, `tests/` 3개 파일과 fixture 2개가 함께 변경된다.
2. **인터페이스·상태 전이 변경** — #44는 `validate_review.py`의 `--prior` 입력 형태를 ID
   목록에서 구조화된 finding 정보로 확장하고, #37은 미검증 사유 REVISE가 라운드를
   소모하지 않는 재수행 정책과 신규 서브커맨드·상태 키를 신설하며, #38은 evidence에
   미검증 표시 필수 필드를 추가하고 검증 규칙을 추가한다. 스킬 번들 계약이
   SemVer MAJOR(1.0.0 → 2.0.0)로 바뀐다.
3. **비자명한 신규 인터페이스** — `review.schema.json` 확장은 `validate_review.py`의
   스키마-상수 드리프트 가드(`SchemaDriftTests`)와 기존 fixture·헬퍼의 형태 고정을
   동시에 만족해야 한다.
4. **대안·비범위·수용 기준의 명시 필요** — 이슈 3건의 수정 순서 의존(#44 → #37 → #38),
   #43(record-review 자동 터미널 전이)을 같은 파일에서 건드리지 않는 비범위 경계, 기존
   테스트 180개 기준선 유지 여부를 모두 명시해야 한다.

**이슈 라벨 증거** — #44 `bug`, #37 `enhancement`, #38 `enhancement`. 라벨은 상향
근거로만 쓰였고 위 risk 스캔 결과를 대체하지 않았다.

**실행 중 범위 추가 2건.** 피어 세션(`dotfiles-4e`)이 사용자 결정을 전달해 Spec 라운드 1
기록 후 R6(`ROUND_LIMITS` spec 2 → 3)과 R7(루브릭 라운드 수 단언 강화)이 추가됐다.
모드는 standard 그대로다 — 추가 항목도 게이트 규칙 변경이며 같은 파일군에 속한다.
라운드 예산은 되돌리지 않았다(아래 "라운드 예산 처리" 참조).

## Review history

| 아티팩트 | 라운드 | 점수 | 판정 | 블로커 | Critical/High | 게이트 실패 사유 |
|---|---|---|---|---|---|---|
| Spec | 1 | 87 | REVISE | SPEC-001 | 1건 | `verdict_not_pass`, `blockers_present`, `critical_or_high_finding`, `check_failed:acceptance_criteria_objective` |
| Spec | 2 | 86 | REVISE | SPEC-012 | 1건 | `verdict_not_pass`, `blockers_present`, `critical_or_high_finding`, `check_failed:acceptance_criteria_objective` |

Plan 및 코드 리뷰 라운드는 수행되지 않았다 (Spec 단계에서 종료).

**라운드 간 변화.** 라운드 1의 10건(High 1 · Medium 5 · Low 4)을 전부 개정했고, 라운드 2
리뷰어가 그중 **8건의 해소를 개별 증거와 함께 확인**했다. SPEC-006만 부분 해소로 남았고
(advisory 유실은 닫혔으나 두 번째 종료 시도의 상태 기록이 여전히 부재), 나머지 9건은
확인됐다. 점수는 87 → 86으로 미세 하락했는데, 이는 개정이 후퇴했기 때문이 아니라
**범위가 커졌기 때문**이다 — R6·R7과 AC-46~AC-64가 새로 들어오면서 새 검토 표면이
생겼고 그중 High 1건(SPEC-012)이 발견됐다.

**라운드 예산 처리.** 범위 추가(R6·R7)가 라운드 1 기록 후에 도착했으나 라운드 카운터를
되돌리지 않았다. `SKILL.md`의 scope-change 규칙은 영향받은 digest를 무효화하고 가장 이른
리뷰 스테이지로 돌아가라고 지시하지만 라운드 카운터 초기화를 규정하지 않으며, 그런 CLI도
없다. 범위가 늘었다는 이유로 예산을 되돌리는 것은 #37이 경고하는 "라운드 세탁"과 구조가
같으므로 하지 않았다.

## Blocking-finding resolutions

| ID | 라운드 | 심각도 | 해소 내용 | 검증 증거 |
|---|---|---|---|---|
| SPEC-001 | 1 | High | AC-43·AC-44가 작업 트리 대비 명령(`git status --porcelain`, 인자 없는 `git diff`)을 써서 **커밋 후 공허해지는** 결함. 두 기준을 base revision 기준으로 재작성했다 — AC-43은 `git diff --name-only $BASE...HEAD`를 Non-goal 12의 positive allow-list로 거른 결과가 비어야 하고, AC-44는 행 번호가 아니라 내용 앵커(`sed -n '/^    recurring = next/,/REVIEW_LIMIT_EXHAUSTED/p'`)로 base와 작업 트리의 블록을 `diff`한다. 평가 시점을 "최종 커밋 후 PR 생성 전"으로 명시했다 | 라운드 2 리뷰어 확인: AC-43·AC-44가 base-revision 기준으로 재작성되고 Non-goal 12의 allow-list와 평가 시점이 명시됐음을 확인. 오케스트레이터 독립 실측: 두 `sed` 앵커가 base(`6d8ccad`)와 작업 트리에서 동일한 9줄 블록을 추출하고, allow-list grep이 exit 1(위반 없음)을 낸다 |
| SPEC-012 | 2 | High | **미해소.** 라운드 한도 소진으로 개정하지 못했다 | — |

### 라운드 1의 Medium/Low 해소 (라운드 2 리뷰어 확인)

| ID | 심각도 | 해소 내용 | 라운드 2 판정 |
|---|---|---|---|
| SPEC-002 | Medium | R1.11 신설 — prior 최상위 unknown 키를 검증 오류로 만든다. 오타 키가 구조화 prior 검증을 조용히 전부 무력화하는 경로를 닫았다. AC-46과 변이 검증 추가 | 해소 확인 |
| SPEC-003 | Medium | AC-39·D1의 fixture 오카운트 정정 — evidence 형태 고정 지점은 리뷰 fixture 2개 + 헬퍼 2개 = 4곳이고 `verification-pass.json`은 evidence 배열이 없어 무관 | 해소 확인 |
| SPEC-004 | Medium | R2.4를 포괄 서술에서 전제 6개의 명시적 열거로 교체(digest 형식·digest 교차 검사·스테이지·스키마 검증·라운드 일치·한도 초과). I3에 `--artifact-digest`와 종료 코드 3행 추가. AC-51·52·53 신설 | 해소 확인 |
| SPEC-005 | Medium | 미대응 절 전수 보강 — R1.2 세분화(AC-47·48), R1.6 중복·타입(AC-49), R2.2의 좁힌 입력 구체화(AC-50), AC-42를 신규 규칙 11개 전수로 확대해 R5.5와 일치 | 해소 확인 |
| SPEC-006 | Medium | R2.7에 `discarded_reviews` 추가, R2.11 신설(폐기 리뷰의 비-blocking findings 승계), I4·I5·Failure behavior·Security 반영, AC-54·55 신설 | **부분 해소** — 아래 잔여 항목 참조 |
| SPEC-007 | Low | R3.2 수정 — `EVIDENCE_FIELDS`가 세 루프를 구동하므로 문자열 검사는 `EVIDENCE_STRING_FIELDS`로 분리하고 `verified`는 별도 boolean 검사. AC-56 신설 | 해소 확인 |
| SPEC-008 | Low | R4.3 전제 정정 — 현재 추적 목록은 #36·#37·#38·#39 4개이고 #43·#44는 애초에 없다. 조치를 "#37·#38 제거, #43 추가, #44 항목 미생성"으로 명시 | 해소 확인 |
| SPEC-009 | Low | R5.3·D8의 편차 ID 정정 — `uniqueItems`·lookaround HTTP 400 실측은 D-16이 아니라 **D-15**(`deviations.md:217-237`)에 있다. D-16 FIX 2 인용(maxTurns:12, no-PASS 유래)은 정확하므로 유지 | 해소 확인 |
| SPEC-010 | Low | AC-45에서 감사 불가능한 "세션 명령 기록" 절 제거. 배포본 `grep '^version:'`과 보고서 명령 표의 `chezmoi apply` 부재만 남김 | 해소 확인 |

## Plan approval

- Approval timestamp: 해당 없음 — Spec 단계에서 종료되어 Plan을 작성하지 않았다.
- Plan digest: 해당 없음.

사용자 승인 게이트(`AWAITING_PLAN_APPROVAL`)에 도달하지 않았다.

## Changed files

구현이 시작되지 않았으므로 **저장소 소스 파일 변경은 없다.** 이번 실행이 생성한 파일은
산출물 문서뿐이다.

| 경로 | 종류 | 내용 |
|---|---|---|
| `docs/development/2026-08-27-quality-goal-review-loop/spec.md` | 산출물 | 개정된 Spec (952행, SHA-256 `1ed1cff2c47cdb25e65632fb838d30008b313ca46f596110df72b34e41674505`) |
| `docs/development/2026-08-27-quality-goal-review-loop/report.md` | 산출물 | 이 보고서 |

의도한 변경 대상이었으나 **손대지 않은** 파일:

- `dot_claude/skills/quality-goal/SKILL.md`
- `dot_claude/skills/quality-goal/schemas/review.schema.json`
- `dot_claude/skills/quality-goal/scripts/validate_review.py`
- `dot_claude/skills/quality-goal/scripts/quality_state.py`
- `dot_claude/skills/quality-goal/references/spec-rubric.md`
- `dot_claude/agents/quality-reviewer.md`
- `dot_claude/skills/quality-goal/tests/` 3개 파일과 fixture 2개
- `docs/quality-goal-maintenance.md`

baseline 리비전 `6d8ccad` 기준 사전 dirty 경로는 없었고, 현재도 위 파일들은 수정되지
않았다. `git status --porcelain`은 산출물 디렉터리 1건(`?? docs/development/2026-08-27-quality-goal-review-loop/`)만 낸다.

**변이 검증 중 임시 수정과 복원.** SPEC-012 확인을 위해
`scripts/quality_state.py:69`의 `ROUND_LIMITS`를 일시적으로 `spec: 3`으로 바꿔 전체
스위트를 돌린 뒤 백업에서 복원했다. 복원 후 `git diff --stat`이 빈 출력이고 180개
테스트가 다시 통과함을 확인했다.

## Verification evidence

### 실행한 명령

| 명령 | 종료 코드 | 증거 |
|---|---|---|
| `git rev-parse --show-toplevel` / `rev-parse HEAD` | 0 | worktree 확인, base `6d8ccad16b4f8345130fe56913a2eead4169030f` |
| `git status --porcelain` (INTAKE) | 0 | 빈 출력 — 사전 dirty 경로 없음 |
| `codex --version` | 0 | `codex-cli 0.150.1` |
| `codex exec --sandbox read-only --ephemeral --model gpt-5.6-terra -c model_reasoning_effort="low" "Reply with one non-empty line."` | 0 | `Acknowledged.` — 선택 모델 preflight 통과 |
| `git check-ignore -v .claude/quality-state/` | 0 | `.gitignore:25:.claude/quality-state/` — 런타임 상태가 이미 무시됨 |
| `gh issue view 44/37/38/43 --json title,body,labels,comments` | 0 | 요구사항 입력 확보. 라벨 #44 `bug`, #37·#38 `enhancement`, #43 `bug` |
| `quality_state.py select-resume` | 0 | `{"match":null}` — 재개 대상 없음 |
| `quality_state.py init` / `classify` / `capture-baseline` | 0 | standard, 근거 6건, base·dirty 기록 |
| **`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/quality-goal/tests -p 'test_*.py'`** (기준선) | 0 | **`Ran 180 tests` / `OK`** |
| 정적 교차 확인: 세 테스트 파일의 `def test_` 개수 | — | 47 + 39 + 94 = 180 (리뷰어 독립 확인) |
| `validate_review.py validate --input spec-review-round1.json --artifact spec` | 0 | `{"valid":true,"errors":[]}` |
| `validate_review.py gate --input spec-review-round1.json --artifact spec --checks spec-checks-round1.json` | 3 | `verdict_not_pass`, `blockers_present`, `critical_or_high_finding`, `check_failed:acceptance_criteria_objective` |
| `quality_state.py record-review-error --artifact spec --round 1` | 0 | 리뷰어 산출물 미전달 기록. `rounds.spec`은 0 유지 — 라운드 미소모 |
| `quality_state.py record-review` (라운드 1) | 0 | `rounds.spec: 1`, `open_finding_ids.spec: ["SPEC-001"]` |
| `validate_review.py validate --input spec-review-round2.json --artifact spec --prior spec-prior-round2.json` | 0 | `{"valid":true,"errors":[]}` |
| `validate_review.py gate --input spec-review-round2.json --artifact spec --checks spec-checks-round2.json --prior …` | 3 | `verdict_not_pass`, `blockers_present`, `critical_or_high_finding`, `check_failed:acceptance_criteria_objective` |
| **SPEC-012 변이 검증**: `ROUND_LIMITS` spec 2 → 3 후 전체 스위트 | 1 | **`FAILED (failures=3)`** — `ConstantTests.test_transition_terminal_and_round_constants_match_the_contract`, `RoundLimitTests.test_nonpassing_final_spec_round_enters_needs_redesign`, `RoundLimitTests.test_spec_and_plan_round_three_are_rejected_after_two_recorded_rounds (artifact='spec')` |
| 복원 후 전체 스위트 | 0 | `Ran 180 tests` / `OK`, `git diff --stat` 빈 출력 |
| `sed -n '/^    recurring = next/,/REVIEW_LIMIT_EXHAUSTED/p'` (base vs 작업 트리) | 0 | 양쪽에서 동일한 9줄 블록 추출 — AC-44 앵커 실증 |
| `git diff --name-only 6d8ccad...HEAD \| grep -vE '^(dot_claude/skills/quality-goal/\|dot_claude/agents/quality-reviewer\.md$\|docs/)'` | 1 (grep) | 위반 없음 — AC-43 필터 실증 |
| `sed -n 33p` 비교: `spec-rubric.md` vs `plan-rubric.md` | 0 | **IDENTICAL** — 두 파일 33행이 바이트 동일. R6.2의 개별 편집 규칙 근거 |
| `grep -n 'After round' references/*.md` | 0 | 3줄: spec=2, plan=2, code=3 |
| 루브릭 정규식 실측 (`after round (\d+)` vs `after round (\d+) without a passing gate`) | 0 | 넓은 패턴 spec `['1','2']`·plan `['1','2']`·code `['1','3']` / 좁힌 패턴 spec `['2']`·plan `['2']`·code `['3']`. 기존 단언의 좌변 `stop.{0,100}round N`은 세 루브릭 전부 False |
| `grep '^version:' ~/.claude/skills/quality-goal/SKILL.md` | 0 | `version: 1.0.0` — 배포본 불변 확인 |
| `grep -n 'ROUND_LIMITS = ' ~/.claude/skills/quality-goal/scripts/quality_state.py` | 0 | `{"spec": 2, "plan": 2, "code": 3}` — 이번 실행에 적용된 한도 |

**`chezmoi apply`는 실행되지 않았다.** 위 명령 표에 없으며 배포본 `version`이 `1.0.0`으로
남아 있다.

### 검증 카테고리 상태

| 카테고리 | 상태 | 근거 |
|---|---|---|
| 표적 테스트 | **실행됨** | 위 스위트 180개, exit 0 |
| 전체 스위트 | **실행됨** | 같음 |
| 타입 체크 | `not configured` | `package.json`·`Makefile`·`justfile`·`tsconfig.json` 부재 확인 |
| 린트 | `not configured` | `.pre-commit-config.yaml`에 gitleaks 훅만 존재 (시크릿 스캔 전용) |
| 빌드 | `not configured` | `package.json`·`.github/workflows` 부재 확인 |
| E2E / 수동 검증 | **미실행** | 구현 단계에 도달하지 않았다. 통과로 기록하지 않는다 |

## Remaining advisory findings

### High (게이트 실패 사유, 미해소)

| ID | 요약 | 영향 | 후속 조치 |
|---|---|---|---|
| SPEC-012 | R6.4의 테스트 열거가 불완전하다. `ROUND_LIMITS["spec"]`를 3으로 올리면 R6.4가 지목하지 않은 동작 테스트 2개가 깨진다 — `test_quality_state.py:886-906`(spec·plan을 함께 도는 subTest에서 spec 라운드 3이 수용되어 `assertRaises` 실패)와 `:928-947`(`expected_round == ROUND_LIMITS`가 라운드 2에서 성립하지 않아 `NEEDS_REDESIGN` 단정 실패). AC-38(스위트 exit 0)이 Spec의 주 수용 명령이므로 R6은 명세대로는 자기 수용 기준을 만족할 수 없다 | R6 구현이 즉시 실패한다. `:928-947` 재작성은 라운드 3 재앵커와 라운드별 상이한 blocker ID를 요구하는데, 이는 Non-goal 1이 동결한 `record_review` 자동 전이 동작(`:588-596`)의 판정 경로에 걸린다 | **오케스트레이터가 변이 검증으로 확정했다** — spec을 3으로 바꾸면 정확히 그 두 테스트 + 상수 고정 테스트, 총 3건이 실패한다. R6.4를 3개 전수로 다시 쓰고 각 테스트의 변경 후 기대 상태를 명시할 것. 특히 `:928-947`은 라운드 3 REVISE + 라운드별 상이한 blocker ID로 재앵커해 `REVIEW_LIMIT_EXHAUSTED`(≠ `RECURRING_BLOCKING_FINDING`)가 기록되게 할 것 |

### Medium

| ID | 요약 | 영향 | 후속 조치 |
|---|---|---|---|
| SPEC-006 | (부분 해소) 두 번째 종료 시도가 상태에 기록되지 않는다. I3 표와 R2.5가 두 번째 `record-review-unverified`를 exit 3 + "상태 불변"으로 규정하므로, `REVIEWER_UNVERIFIED_PERSISTS`를 실제로 유발한 리뷰 JSON이 `discarded_reviews`에 append되지 않고 `attempts`는 2에 도달할 수 없다. 형제 함수 `record_review_validation_failure`는 차단 전에 `attempts: 2`를 기록한다(`quality_state.py:626-631`) | 상태 파일이 2회 시도 종결을 `attempts: 1` + 경로 1개로 기록한다 — `SKILL.md:232-238`의 권위 기록 선언과 어긋난다 | 두 가지 중 하나를 택해 명시할 것: (a) 거부 전에 지속(`attempts: 2` + 두 번째 경로, 형제 함수 패턴과 일치), (b) 두 번째 리뷰는 `report.md`에서만 참조 — 이 경우 R2.7에 그렇게 적고 `attempts` 필드를 제거하거나 범위를 고칠 것. 어느 쪽이든 `REVIEWER_UNVERIFIED_PERSISTS` 종결 시점의 상태 내용을 고정하는 AC를 추가할 것 |
| SPEC-011 | R2.4-2의 digest 교차 검사가 R2.2("재수행 중 아티팩트 개정 금지")를 "결정적으로 강제"한다는 주장이 과장이다. `--artifact-digest`는 호출자가 공급하고 **현재** 파일과 비교되므로(`record_review:514-520`), 아티팩트를 개정하고 digest를 재계산한 오케스트레이터는 검사를 통과한다. I5 5단계의 재기동 사이에는 아무 검사도 없다 | 실제 보장은 "기록된 시도가 특정 digest에 묶인다"까지이며 무개정은 지시문 수준이다. Spec이 R2.2·R2.4-2·Failure behavior·Security 완화 (c) 네 곳에서 결정적이라고 서술한다 | 두 가지 중 하나: (a) 네 곳의 서술을 실제 보장 수준으로 축소하고 무개정을 지시문 규칙으로 명시, (b) 실제로 결정적인 기제를 규정 — 예컨대 `record-review-unverified`가 수용한 digest를 `review_unverified_retry`에 저장하고 같은 라운드의 이후 `record-review`가 동일 digest를 제시해야 하게 할 것. 개정 후 digest 재계산 케이스의 AC를 추가할 것 |
| SPEC-013 | AC-58이 한 시퀀스에서 양립 불가한 두 결과를 단정한다 — "라운드 3 REVISE+blocker → `NEEDS_REDESIGN`"과 "라운드 4 → exit 3". `NEEDS_REDESIGN` 전이 후에는 `record_review`가 스테이지 가드에 먼저 걸려 `StateError` → **exit 2**를 낸다(`:505-512`, 매핑 `:1189-1194`). 저장소가 code 아티팩트에 대해 이 동작을 이미 고정한다(`test_quality_state.py:977-984`의 `requires stage CODE_REVIEW`) | AC-58을 그대로 구현하면 실패한다 | AC-58을 개별 판정 가능한 시퀀스 3개로 분리하고 각 종료 코드를 명시할 것: (a) 라운드 1·2를 상이·공백 blocker로 기록 후 라운드 3 → exit 0, (b) 라운드 3 REVISE+blocker → `NEEDS_REDESIGN`/`REVIEW_LIMIT_EXHAUSTED`, 이어지는 라운드 4 → exit 2 `requires stage SPEC_REVIEW`, (c) 라운드 3을 PASS로 기록해 스테이지 유지 후 라운드 4 → exit 3 |

### Low

| ID | 요약 | 영향 | 후속 조치 |
|---|---|---|---|
| SPEC-014 | AC-64가 "R1.1–R7.4의 모든 요구사항이 하나 이상의 AC에 대응"한다고 단정하지만, 대응표의 R6.6 행은 AC가 아니라 `Non-goal 7`을 가리킨다. 산문(`:598-600`)이 R6.6을 설명·면제하므로 의도는 분명하나 AC-64는 자기가 감사하는 대상에 의해 반증된다 | 기준 문구의 자기모순 | AC-64를 대응표에 맞게 고칠 것(R6.6 예외 명시) 또는 R6.6에 AC를 부여할 것(예: `quality_state.py` diff에 조건부 라운드 3 분기가 없음을 확인) |
| SPEC-015 | AC-59의 두 번째 절("SKILL.md의 spec 서술 3곳이 3이고 plan 3곳이 2, code 2곳이 3")이 명령을 지정하지 않아 Acceptance criteria 서두(`:352`)의 판정 규칙을 위반한다. 또한 숫자를 세는 독법에서만 참이다 — `SKILL.md:120`은 `fix at most three rounds`(영문 단어), `:225`는 `at most 3 rounds`(숫자)라 숫자 grep은 code 언급 2곳 중 1곳만 찾는다 | 기준이 명령으로 판정되지 않음 | AC-59의 SKILL.md 절에 구체적 명령을 부여할 것(앵커된 5개 행에 대한 `grep -n`, 또는 숫자와 영문 단어를 모두 수용하는 기존 `test_review_round_limits_and_reviewer_isolation_contract` 정규식). `SKILL.md:120`이 code 한도를 `three`로 적는다는 점을 명시할 것 |

### 리뷰어가 명시한 미검증 항목

라운드 1·2 리뷰어 모두 evidence에 `NOT VERIFIED`를 산문으로 기록했다.

- 180개 테스트 스위트의 exit 0 — 리뷰어는 `Read, Grep, Glob`만 보유해 명령을 실행할 수
  없다. 정적으로 `def test_` 개수 180만 교차 확인했다. 오케스트레이터가 독립 실행해
  exit 0을 확인했다(위 명령 표).
- 오케스트레이터 checks JSON 미공급으로 `material_decisions_resolved`와
  `acceptance_criteria_objective`를 교차 확인할 수 없었다. 이는 설계상 의도이며
  (`SKILL.md`의 리뷰 호출 계약 입력 목록에 checks가 없다) Spec의 Non-goal 13·D12가
  근거를 기록한다.

## 이번 실행에서 발현한 quality-goal 스킬 자체의 결함 (실측)

이 실행은 수정 대상인 배포본 v1.0.0으로 돌았다. 아래는 우회하지 않고 기록한 관찰이며
수정의 실증 근거다.

### 관찰 1·2 — 리뷰어 산출물 전달 실패, 원인 규명 (신규 발견, #37·#38 범위 밖)

**증상.** Spec 리뷰 리뷰어 3명(라운드 1, 라운드 1 재시도, 라운드 2) **전원**이 최종 JSON을
오케스트레이터에게 전달하지 못했다. 세 경우 모두 idle 통지만 도착했다. 오케스트레이터가
세션 트랜스크립트(`~/.claude/projects/…/subagents/agent-aspec-review-*.jsonl`)에서 최종
assistant 텍스트를 파싱해 회수했다.

**원인은 턴 소진도 출력 절단도 아니다.** 트랜스크립트 실측:

| 에이전트 | 최종 `stop_reason` | tool_use 턴 | 최종 텍스트 길이 | 산출물 |
|---|---|---|---|---|
| 라운드 1 | `end_turn` (2회) | 20 | 14,317 / 13,194자 | 완전한 JSON (score 80) |
| 라운드 1 재시도 | `end_turn` | 30 | 21,100자 | 완전한 JSON (score 87) |
| 라운드 2 | `end_turn` | 21 | 24,043자 | 완전한 JSON (score 86) |

세 경우 모두 `stop_reason`이 `end_turn`이고(`max_tokens` 아님) 최종 텍스트가 완결된 JSON
객체다. `maxTurns: 24`도 원인이 아니다 — 재시도 에이전트는 tool_use 턴이 30으로 24를
넘었는데도 정상 `end_turn`으로 끝냈다.

**규명된 원인 — 에이전트 기동 방식.** 세 에이전트의 meta가 모두
`"taskKind": "in_process_teammate"`다. 오케스트레이터가 Agent 호출에 `name`을 넘겼기
때문에 일회성 태스크가 아니라 **지속 teammate로 기동됐고**, teammate의 최종 메시지는
호출자에게 Agent 결과로 반환되지 않는다. 여기에
`dot_claude/agents/quality-reviewer.md:4`의 `tools: Read, Grep, Glob`이 겹친다 — 리뷰어는
`SendMessage`가 없어 결과를 push할 수단도 없다. **두 조건이 겹쳐 전달 경로가 0개가 된다.**

**따라서 수정 방향은 리뷰어 도구 확장이 아니다.** 읽기 전용 리뷰어는 의도된 설계다
(D-1, 리뷰어가 파일을 쓰지 못하게 하는 것이 계약의 핵심). 고칠 지점은 오케스트레이터
측이다 — 리뷰 라운드를 기동할 때 `name`을 넘기지 않아 일회성 태스크로 만들면 최종 보고가
Agent 결과로 반환된다.

**결정적 확인 실험(미실행).** 동일 리뷰어를 `name` 없이 기동해 Agent 결과가 반환되는지
관찰하면 원인이 확정된다. 이번 실행에서는 수행하지 않았다 — 리뷰 라운드를 하나 더 소비하지
않기 위해서다. 후속 이슈에서 이 실험을 먼저 할 것을 권한다.

**정정.** 이 보고서의 초판은 라운드 1 첫 시도를 "`deviations.md` D-16 FIX 2의 `maxTurns`
턴 소진과 같은 계열"로 서술했다. **그 서술은 틀렸다.** 첫 리뷰어는 턴이 소진되지 않았고
score 80의 완전한 리뷰를 실제로 생성했다. 즉 `record-review-error`로 소비한 1회 재시도는
리뷰 실패가 아니라 **전달 실패**에 지출됐다. 라운드는 소모되지 않았으므로 결과적 손해는
없으나, 기록의 정확성을 위해 정정한다. D-16 FIX 2가 기록한 턴 소진은 별개의 실제 현상이며
이번 관찰과 원인이 다르다.

### 관찰 3 — 미검증 표시가 산문뿐이다 (#38의 직접 실증)

라운드 1 리뷰어는 evidence 19건 중 2건을, 라운드 2 리뷰어도 evidence에 미검증 항목을
`claim` 문자열 안의 산문 `"NOT VERIFIED:"`로만 표시했다. `review.schema.json:52`의
evidence 항목이 `{claim, location}`뿐이라 구조화된 필드가 없고, `evaluate_gate`는
evidence를 읽지 않는다. 두 리뷰어 모두 정직하게 `REVISE`를 냈으므로 규칙이 작동했으나,
그것은 **지시문 준수 덕분이지 기계적 강제 때문이 아니다.** #38(R3.1의 `verified` 필수
필드)이 고치려는 상태가 그대로 관측됐다.

### 관찰 4 — #44 우회가 실제로 필요했고 효과가 있었다

라운드 2에서 `SKILL.md:246`의 "prior open finding IDs만 전달" 계약을 따르면 라운드 1의
10건 중 blocker 1건(SPEC-001)의 ID만 전달된다. Medium 5건·Low 4건은 상태의
`open_finding_ids`가 blocker만 보존하므로(`quality_state.py:583`) 전달 수단이 없다.

우회로 구조화된 prior(10건 전부의 설명·증거 위치·요구 해소책 + 오케스트레이터의 해소
주장·증거)를 파일로 만들어 프롬프트에 직접 전달했다. 결과: **라운드 2 리뷰어가 10건 중
9건의 해소를 개별 증거와 함께 확인**하고 1건을 부분 해소로 판정했다. 직전 실행에서
리뷰어가 5건을 검증하지 못했던 것과 대비된다.

부수 관찰: 배포본 `validate_review.py`의 `_prior_open_finding_ids`가 unknown 키를
검사하지 않아 확장 필드가 조용히 수용됐다. 우회는 그 덕에 가능했으나, 같은 성질이
오타로 인한 조용한 무력화를 허용한다 — Spec의 R1.11이 이 구멍을 닫는다.

### 관찰 5 — #43이 발현했고, SKILL.md의 순서를 지켜 회피했다

`record_review`가 라운드 한도 소진을 감지하면 스스로 `NEEDS_REDESIGN`으로 전이한다
(`quality_state.py:588-596`). 전이 후에는 `set-artifact`가 `_require_active`에 막혀
거부되므로(`:108-113`, `:288-312`) 보고서 등록 시점이 사라진다.

이번 실행은 `SKILL.md:232-238`이 요구하는 순서("터미널 전이 **전에** 보고서를 등록")를
문자 그대로 지켜 이를 회피했다 — **`record-review`를 호출하기 전에** 이 보고서를
렌더링하고 `set-artifact --kind report`로 등록했다. 결함을 우회한 것이 아니라, 결함이
있는 상태에서 규정된 순서를 만족시킬 수 있는 **유일한 시점**을 사용했다.

직전 실행(`.../2026-08-27-create-worktree-pr-session/report.md:196-213`)은 라운드 기록
후에 등록을 시도해 exit 3으로 실패하고 `artifacts.report`가 `null`로 남았다. 즉 #43은
"등록 시점이 존재하지 않는다"기보다 **"등록 시점이 리뷰 기록 이전으로 강제된다"**가 더
정확한 서술이며, 오케스트레이터가 최종 라운드의 결과를 미리 알아야 보고서를 쓸 수 있다는
비직관적 제약을 만든다. #43의 후속 작업에 이 관찰을 넘긴다.

### 관찰 6 — SPEC-012 후속을 위한 실측 (다음 실행용 설계 근거)

리뷰어의 High 블로커 SPEC-012를 확정한 뒤, 다음 실행이 R6을 바로 구현할 수 있도록 필요한
설계 결정을 실측으로 미리 확보했다.

**(a) `ConstantTests`의 단정 범위 — Non-goal 1 침범 위험 없음.**
`test_transition_terminal_and_round_constants_match_the_contract`는 클래스 내 유일한
테스트이며 `ALLOWED_TRANSITIONS`·`TERMINAL_STATES`·`ROUND_LIMITS`를 **각각 별개의
`assertEqual`**로 단정한다. 따라서 `ROUND_LIMITS` 기대 dict만 고치면 terminal 상태 집합과
전이 표 단정은 손대지 않는다. 다만 단일 테스트 메서드이므로 편집이 다른 두 단정에 번지지
않도록 주의해야 한다.

**(b) `test_nonpassing_final_spec_round_enters_needs_redesign` 재작성 방식 — 두 후보 모두
성립함을 실측 확인.** `ROUND_LIMITS` spec을 3으로 임시 변경한 격리 실행 결과:

| 시나리오 | 결과 |
|---|---|
| 라운드 1·2 = REVISE / blocker 없음, 라운드 3 = REVISE / blocker 1건 | `NEEDS_REDESIGN`, `REVIEW_LIMIT_EXHAUSTED:spec`, rounds=3 ✅ |
| 라운드 1·2·3 모두 blocker 있고 ID 상이 (A·B·C) | `NEEDS_REDESIGN`, `REVIEW_LIMIT_EXHAUSTED:spec`, rounds=3 ✅ |
| 라운드 1·2 blocker ID 동일 (X·X) | 라운드 2에서 recurring 분기 선발동 → 라운드 3이 `StateError: review for spec requires stage SPEC_REVIEW, got NEEDS_REDESIGN` ❌ |
| 현행 테스트 형태 (라운드 1 PASS, 라운드 2 REVISE+blocker) | `stage=SPEC_REVIEW`, `status_reason=None` — 전이하지 않음, 즉 현행 단정이 깨짐 |

성립 근거: 자동 전이 조건이 `expected_round == ROUND_LIMITS[artifact] and (verdict != "PASS"
or blockers)`이므로 blocker가 없어도 REVISE만으로 최종 라운드 전이가 성립하고,
`earlier_blockers`가 비어 있어 recurring 분기가 발동하지 않는다.

**권고: 첫 번째 방식.** 라운드 1·2를 blocker 없는 REVISE로 두는 것이 최소 변경이며 이
테스트의 원래 의도("최종 라운드가 통과하지 못하면 `REVIEW_LIMIT_EXHAUSTED`")를 그대로
표현한다. blocker ID를 3개로 늘리는 방식은 "서로 다른 블로커가 3라운드 연속"이라는 인위적
시나리오를 만들고, 그 경로가 검증하려던 것과 어긋난다.

**(c) 운영 주의 — `__pycache__` 오염.** 변이 검증 중 `PYTHONDONTWRITEBYTECODE`를 설정하지
않은 임시 스크립트가 스킬 모듈을 import해 패치된 바이트코드가
`scripts/__pycache__/quality_state.cpython-314.pyc`에 캐시됐다. 소스를 복원한 뒤에도 전체
스위트가 같은 3건으로 실패했고, `__pycache__`를 제거한 뒤 180개가 통과했다.
`docs/quality-goal-maintenance.md`의 기준 명령이 `PYTHONDONTWRITEBYTECODE=1`을 쓰는 이유가
이것이다. `.gitignore`가 `__pycache__/`를 덮으므로 `git status`에는 나타나지 않아 조용히
오판을 유발할 수 있다. 임시 진단 스크립트에도 같은 환경 변수를 붙일 것.

**교차 검증.** 위 (a)·(b) 실측과 SPEC-012의 3건 실패는 피어 세션(`dotfiles-4e`)이 격리
사본(`dot_claude/skills` + `dot_claude/agents` + `.gitignore`를 복사한 별도 트리)에서
독립 재현해 동일 결과를 확인했다.

### 관찰 7 — 다음 실행의 테스트 설계 제약 (범위 밖 Critical 결함, 미수정)

피어 세션(`dotfiles-4e`)이 Codex 전수 감사로 발견한 Critical 결함을 통보받아 독립
재현했다. **이 작업 범위 밖이며 고치지 않았다** — 별도 이슈로 처리된다. 다만 다음 실행이
R6 테스트를 작성할 때 제약이 되므로 기록한다.

**결함.** `SPEC_REVIEW → SPEC_PASSED`와 `PLAN_REVIEW → PLAN_PASSED` 전이에 리뷰·게이트
guard가 전혀 없다. `CODE_REVIEW → COMPLETED`는 `quality_state.py:380-403`에서 라운드 1회
이상·마지막 리뷰 PASS·blocker 없음·open finding 없음·`verification.valid`를 모두
요구하지만, 두 `*_PASSED` 전이에는 해당 블록이 존재하지 않는다.

**재현(오케스트레이터 독립 실측).**

```
before: stage=SPEC_REVIEW rounds.spec=0 reviews.spec=[]
transition(state, "SPEC_PASSED") -> ACCEPTED, stage=SPEC_PASSED
transition(state, "PLAN_PASSED") -> ACCEPTED, stage=PLAN_PASSED
```

리뷰를 한 번도 기록하지 않은 상태에서 두 전이가 모두 수용된다.

**다음 실행에 대한 제약.** 신규 테스트가 이 우회 경로를 **기대 동작으로 고정하지 않도록**
주의해야 한다. 기존 `test_quality_state.py:1965-1975`가 이미 그 형태다 — 리뷰 0건 상태에서
`SPEC_REVIEW → SPEC_PASSED → PLAN_REVIEW → PLAN_PASSED → AWAITING_PLAN_APPROVAL` 전체
사슬을 돌며 각 `transition`의 exit 0을 단정한다. R6이 라운드 관련 테스트를 손대므로 같은
형태를 늘리기 쉬운 위치에 있다. R6의 테스트는 `record_review`를 실제로 호출하는
경로만 쓰고, `transition`을 직접 불러 `*_PASSED`로 건너뛰는 형태는 새로 만들지 않을 것.


### 위생 항목

`.claude/quality-state/`는 `.gitignore:25`에 이미 등록되어 있어 런타임 상태가
`git status`에 노출되지 않는다. 별도 조치가 필요 없다.

## Final status

- Status: `NEEDS_REDESIGN`
- Machine-readable reason: `REVIEW_LIMIT_EXHAUSTED:spec`

Spec 리뷰가 배포본 v1.0.0이 규정한 최대 2라운드를 소진했고 두 라운드 모두 게이트를
통과하지 못했다(라운드 1: 87점 / 블로커 SPEC-001, 라운드 2: 86점 / 블로커 SPEC-012).
두 라운드 모두 **점수는 통과선 85를 넘겼고**, 실패 사유는 verdict·blocker·High
severity와 오케스트레이터의 `acceptance_criteria_objective` 자기 체크였다.

구현은 시작되지 않았고 저장소 소스 파일은 변경되지 않았다. 사용자 승인 게이트에도
도달하지 않았으며 PR은 생성되지 않았다.

**이 종결 자체가 R6의 세 번째 실측 근거다.** 실전 3회 연속으로 spec 리뷰가 2/2를
소진했다. 이번에는 점수 87 → 86으로 통과선을 두 라운드 모두 넘긴 상태였고, 남은 것은
해법이 이미 적힌 High 1건과 Medium 3건이었다. 사용자가 추가한 R6(spec 한도 2 → 3)이
소스에 반영되기 전이므로 이번 실행에는 적용되지 않았다 — 배포본 `ROUND_LIMITS`는
`{"spec": 2, "plan": 2, "code": 3}`이었다(실측).

**남은 작업의 성격.** 미해소 4건(SPEC-012 High, SPEC-006·011·013 Medium)은 Spec의 근본
설계 결함이 아니라 **명세 정밀도 문제**다. 네 건 모두 해법이 위 표에 구체적으로 적혀
있고, SPEC-012는 오케스트레이터가 변이 검증으로 원인과 범위를 확정했다(깨지는 테스트
정확히 3개, 이름과 행 번호 확인). 다음 실행에서는 이 네 건을 Spec 초안에 선반영한 상태로
시작하는 것이 합리적이다 — 직전 실행이 선행 실행의 High 2건을 선반영해 라운드 1
블로커를 1건으로 줄인 전례가 있다.

특히 SPEC-012의 해소는 R6의 실현 가능성 자체와 맞물린다. `test_quality_state.py:928-947`
재작성이 `record_review`의 자동 전이 판정 경로(`:588-596`, Non-goal 1이 동결)에 걸리므로,
다음 실행은 R6과 #43의 관계를 먼저 정리해야 한다 — 한도 값만 바꾸는 것으로는 그 테스트를
살릴 수 없고, 라운드별 상이한 blocker ID로 재앵커하는 설계 결정이 필요하다.
