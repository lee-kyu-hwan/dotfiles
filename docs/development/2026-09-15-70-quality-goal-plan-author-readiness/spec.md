# Quality Goal Specification

- Task ID: 20260915T084306Z-70-2단계-quality-goal-plan-단계-codex-author-69b2a42e
- Mode: standard
- Status: SPEC_REVIEW
- Created: 2026-09-15T08:43:06Z
- Updated: 2026-09-15T08:43:06Z
- Source goal: #70 2단계 — quality-goal Plan 단계에 Codex author와 참고용(advisory) readiness를 추가한다

## Problem and context

`quality-goal` v6.0.0은 Spec 단계에서만 Codex author와 fresh Codex readiness reviewer를 사용한다. `dot_claude/skills/quality-goal/SKILL.md:159-163`은 Spec 초안·개정과 공식 리뷰 전 readiness를 명시하지만, 같은 파일의 `### Plan` 절(`:230` 이후)은 Claude 오케스트레이터가 Plan을 직접 작성하는 기존 절차만 기술한다. 따라서 같은 고비용 모델이 Plan 작성·개정과 권위 있는 공식 심사를 함께 수행하는 병목이 남아 있고, 이슈 #70의 1단계 목표가 절반만 적용된 상태다.

Plan으로 확장되지 않은 계약은 저장소에서 기계적으로 확인된다.

- `dot_claude/skills/quality-goal/schemas/readiness-result.schema.json:6`의 `artifact` enum은 `spec` 하나뿐이고, `prior_findings`와 `resolved_finding_ids`는 `READY-` 또는 `SPEC-`만 허용한다. Plan 결과와 공식 `PLAN-` finding 참조를 표현할 수 없다.
- `dot_claude/skills/quality-goal/scripts/validate_review.py:137-147`은 readiness가 발급하는 finding과 blocker를 `READY-`로, 참조 finding을 `READY-` 또는 `SPEC-`로 고정한다. artifact별 의미 검증과 Spec/Plan 교차 오염 거부가 없다.
- `dot_claude/skills/quality-goal/references/model-routing.md:12-14`에는 Spec author 두 라우트와 공용 fresh readiness reviewer 한 라우트만 있고 Plan author 라우트가 없다.
- `dot_claude/skills/quality-goal/references/readiness-policy.md:1`은 제목부터 Spec 전용이며 author 입력, failure, digest, evidence attachment, C1~C8이 모두 Spec 문언이다.
- `docs/quality-goal-maintenance.md:29`도 Spec author 두 라우트와 readiness reviewer만 유지보수 대상으로 열거한다.

반면 Plan을 수용할 하부 구조는 이미 존재한다. `dot_claude/skills/quality-goal/scripts/quality_state.py:206-207`은 `readiness`와 `draft_attempts`에 `plan` 키를 만들고, 같은 파일의 CLI 정의(`:1396-1408`)는 두 기록 명령의 `--artifact plan`을 허용한다. `dot_claude/skills/quality-goal/scripts/revision_check.py:461-518`은 `--artifact plan`과 `--spec`을 처리한다. `dot_claude/skills/quality-goal/templates/plan.md:62-102`에는 strict-only marker 쌍이 이미 있고, `dot_claude/skills/quality-goal/templates/spec.md`와 함께 identifier grammar가 요구하는 추적·검증 구조를 제공한다. 이 구조를 재구현하거나 새 상태 키를 만들 필요가 없다.

테스트 기준선은 Git revision `92f387361775d6c6eebf9701d69e5653b5226806`에서 `/opt/homebrew/bin/python3` 3.14.7로 전체 `dot_claude/skills/quality-goal/tests`를 실행해 확인한 479건 `OK`다. `dot_claude/skills/quality-goal/tests/test_content_contracts.py:335-754`의 기존 author/readiness 내용 계약과 상태·validator 테스트는 1단계 Spec 동작의 하위 호환 계약이다.

## Goals

1. standard·strict Plan 초안과 모든 개정을 Codex Plan author가 작성하도록 입력·출력·쓰기 범위 계약을 추가한다.
2. Plan에 맞는 여덟 항목 advisory readiness 점검을 실행하고 결과와 요약 근거를 공식 Plan 리뷰에 첨부한다.
3. Plan author와 readiness reviewer의 fresh context 분리, 대상 artifact 경로·종류·digest, reviewer 실행 정보, findings와 근거의 연결을 검증한다.
4. Plan readiness 기록을 공식 review rounds와 분리하고, 기존·레거시 상태의 재개 및 하위 호환성을 보존한다.
5. 모델 unavailable, 비정상 종료, 누락·invalid result, digest 불일치, partial write와 허용 범위 밖 쓰기의 실패 경로를 검증한다.
6. Spec/Plan 85점, 공식 3/2/3 라운드, 승인 digest, dirty-worktree, 결정적 검증 및 Code 단계 계약을 회귀시키지 않는다.
7. `SKILL.md`, readiness/model-routing reference와 유지보수 문서를 Plan 계약에 맞춰 갱신한다.

## Non-goals

1. readiness 점수 게이트, 체크리스트 게이트, 자동 중재(`ARBITRATION`) 또는 신규 상태 전이 추가. 전부 이슈 #76 범위다.
2. 공식 리뷰 라운드 한도 변경. 특히 Plan 2회를 3회로 바꾸는 이슈 #60은 `NOT_PLANNED`로 종료됐으며 재개하지 않는다.
3. Code 단계 readiness 추가. 이슈 #70이 명시적으로 제외한다.
4. eval 추가, 호출 수 측정, 비용 또는 처리량 비교. 이슈 #70의 3단계에서 별도로 추적한다.
5. 모델 계정 배정 또는 계정 격리. 이슈 #111 범위다.
6. C1~C8을 아홉 항목 이상으로 늘리거나 식별자를 바꾸는 일. 정확히 여덟 항목을 유지한다.
7. `ALLOWED_TRANSITIONS`, `TERMINAL_STATES`, `ROUND_LIMITS`, `REQUIRED_CHECKS` 변경.
8. 이미 Plan을 지원하는 `readiness.plan`, `draft_attempts.plan`, 두 CLI의 `--artifact plan`, `revision_check.py --artifact plan --spec`, `templates/plan.md` strict marker를 재구현하거나 다른 상태 키·명령·템플릿 구조로 대체하는 일.

## Requirements

### R1. Codex Plan author

- **R1.1** standard·strict의 `PLAN_REVIEW`에서 첫 Plan 초안과 모든 개정은 별도 Codex Plan author가 작성한다. Claude 오케스트레이터는 `plan.md` 본문을 직접 작성하거나 개정하지 않는다. light의 compact Plan 절차는 현행 그대로다.
- **R1.2** Plan author 프롬프트는 대상 Plan, 통과한 Spec, `templates/plan.md`, `references/plan-rubric.md`, `references/planning-policy.md`, `references/revision-check-policy.md`의 절대 경로, 적용할 readiness·공식 findings 전문 경로, 발견 결과와 전역 제약, 허용 쓰기 경로, identifier grammar, 검증 명령 발견 의무, revision-note 형식, cross-regression 점검을 포함한다. material ambiguity는 호출 전에 사용자에게 해소한다.
- **R1.3** `references/model-routing.md`에 `Plan author (standard)`는 `gpt-5.6-terra`/high, `Plan author (strict)`는 `gpt-5.6-sol`/high로 추가한다. 두 라우트는 기존 author 실행 템플릿의 workspace-write, ephemeral, codex-result schema, stdin 및 execution watchdog 계약을 재사용하며 별도 실행 템플릿을 복제하지 않는다.
- **R1.4** Plan author는 대상 `plan.md`와 라운드 2 이상에서의 `plan-revision-notes.md`만 쓸 수 있다. 오케스트레이터는 `initial_dirty_paths`와 `.claude/quality-state/<task-id>/`를 제외한 실제 변경 경로를 codex-result의 `changed_files`와 대조하고, 결과 스키마·종료 코드와 호출 전후 Plan SHA-256 변화를 확인한 뒤에만 성공한 author write로 취급한다.
- **R1.5** 성공 여부와 무관하게 Plan author 호출은 기존 `record-draft-attempt --artifact plan`으로 `draft_attempts.plan`에 기록하며 `rounds`를 소비하지 않는다. 새 counter나 상태 키를 만들지 않는다.
- **R1.6** 공식 라운드 2 이상 개정은 기존 `plan-revision-notes.md` 형식과 `revision_check.py --artifact plan --current <plan> --spec <spec> --state <state> --out <result>`를 사용한다. `set-artifact` 후 revision check가 0으로 통과하기 전에는 공식 리뷰를 기록하지 않으며 `revision_check.py`의 Plan 구현이나 `templates/plan.md` marker를 중복 수정하지 않는다.

### R2. Plan advisory readiness 및 공식 리뷰 연결

- **R2.1** 성공한 각 Plan author write 뒤, 같은 공식 Plan 라운드의 공식 reviewer 호출 전에 author와 다른 fresh/ephemeral Codex readiness 프로세스를 실행한다. readiness는 `gpt-5.6-sol`/high, read-only sandbox, readiness-result schema와 execution watchdog을 사용하고 author의 대화·세션·숨은 문맥·revision-note 주장을 상속하지 않는다.
- **R2.2** readiness 호출 전에 `artifacts.plan`의 등록 경로가 심사 대상 절대 경로와 같은지 확인하고 현재 파일의 SHA-256을 계산한다. 프롬프트, 결과의 `artifact_digest`, `record-readiness --artifact plan --artifact-digest`, 상태의 readiness record가 모두 그 값과 `artifact: plan`에 연결되어야 하며 Spec 또는 이전 Plan 개정 결과를 현재 Plan 결과로 채택하지 않는다.
- **R2.3** Plan readiness 프롬프트는 현재 Plan과 통과한 Spec, Plan template/rubric/planning/revision policy, 같은 공식 라운드의 직전 readiness 결과, 직전 공식 Plan 리뷰의 open findings 전문을 경로로 제공한다. supplied finding마다 ID·severity·`required_resolution`을 제공하되 이는 reference only이고 reviewer가 발급하는 ID는 언제나 `READY-`다.
- **R2.4** readiness의 score·verdict·checklist는 record-only advisory다. 어떤 상태 전이, 공식 리뷰 라운드, 공식 리뷰 시작 조건, 공식 gate에도 영향을 주지 않으며 `READY` 또는 `REVISE`가 공식 reviewer의 독립 판단을 구속하지 않는다.
- **R2.5** 공식 Plan 리뷰 컨텍스트에는 마지막 Plan readiness 결과 JSON과 `.claude/quality-state/<task-id>/readiness-evidence-plan-r<N>.md` 두 경로를 repository evidence로 첨부한다. summary에는 미충족 checklist, 잔여 findings와 유효 결과 부재 사유를 기록하고 내용을 공식 reviewer prompt에 인라인하지 않는다.
- **R2.6** Plan readiness 기록과 공식 Plan review 기록은 독립적이다. readiness 실패·`REVISE`·낮은 점수만으로 `record-review`, `record-review-unverified`, `record-review-error`를 거부하지 않으며 readiness 기록은 `readiness.plan`만, 공식 review는 `reviews.plan`과 `rounds.plan`만 갱신한다.

### R3. readiness 결과 스키마와 식별자 검증

- **R3.1** 단일 `schemas/readiness-result.schema.json`을 유지하면서 `artifact` enum을 `spec`과 `plan`으로 확장한다. 모든 property의 기존 명시적 `type`, `additionalProperties: false`, required 필드, checklist 8개, evidence 최소 6개, SHA-256 및 verdict 제약은 유지한다. 현재 custom validator가 해석하지 않는 조건부·상수 schema 키 `if`, `then`, `oneOf`, `allOf`, `anyOf`, `const`는 schema 객체 트리 어디에도 추가하지 않는다.
- **R3.2** 발급 자리인 `findings[].id`와 `blockers[]`는 artifact와 무관하게 `^READY-`만 허용한다. `SPEC-`와 `PLAN-`은 이 두 자리에 절대 허용하지 않는다.
- **R3.3** 참조 자리인 `prior_findings[].id`와 `resolved_finding_ids[]`의 스키마 패턴은 `READY-`, `SPEC-`, `PLAN-`의 문법적 합집합을 허용하되, `validate_readiness_result`는 payload artifact가 `spec`이면 `READY-|SPEC-`, `plan`이면 `READY-|PLAN-`만 허용한다. Spec 결과의 `PLAN-` 및 Plan 결과의 `SPEC-` 교차 오염은 검증 실패다.
- **R3.4** `resolved_finding_ids` 집합은 `prior_findings`에서 `judgement == resolved`인 ID 집합과 정확히 같아야 하며, `source`, `judgement`, evidence 및 C1~C8 정확히 한 번 규칙은 두 artifact에 동일하게 적용한다.
- **R3.5** `record-readiness`는 결과 payload의 `artifact`가 CLI `--artifact`와 다르면 `schema_invalid`로 기록하고 유효 결과 필드를 채택하지 않는다. 검증 함수와 기록 호출부 사이에 expected artifact를 선택적 매개변수로 전달하되 기본값을 두어 기존 `validate_readiness_result(payload)` 단일 인자 호출이 그대로 동작해야 하며, 기존 record shape와 outcome 네 값은 바꾸지 않는다.
- **R3.6** Plan 결과가 schema와 semantic validation을 통과해도 결과 digest가 호출 시점 Plan digest와 다르면 `digest_mismatch`이며, 등록 artifact의 현재 digest와 CLI digest가 다르면 기록 자체를 거부한다. 검증 순서는 schema/artifact 의미 검증 후 결과 digest 대조다.

### R4. artifact별 C1~C8 사상

- **R4.1** readiness 정책은 C1~C8 식별자를 정확히 유지하고 Spec 사상을 의미·테스트 단위로 보존하면서, artifact별 표 또는 절로 Plan 사상을 명시한다. checklist 밖의 설계 정합성·아키텍처 타당성·시간축 판단은 계속 공식 reviewer의 책임이다.
- **R4.2** Plan C1~C7은 다음처럼 기계적으로 판정한다: C1 `templates/plan.md` 필수 절 존재·순서, C2 strict marker가 둘 다 존재하거나 standard에서 둘 다 부재, C3 Spec AC 정의 수와 Plan 추적표 행 수 동일, C4 각 추적행 Criterion이 Spec AC에 존재하고 Task가 `### T<n>.`에 존재, C5 각 추적행의 Verification command와 Expected outcome이 모두 비어 있지 않음, C6 `T<n>` 번호 연속·고유, C7 각 추적행이 참조하는 `CMD-<n>`이 `## Verification commands` 표에 정의됨.
- **R4.3** Plan C8 정책은 프롬프트에 제공된 직전 readiness `READY-`와 공식 `PLAN-` finding만 대상으로 하고 supplied target마다 `prior_findings`를 정확히 하나 남기며 `partial`을 미충족으로 판정한다. target이 없으면 빈 배열로 자동 충족이고 참조 ID의 원 접두를 보존한다. validator는 payload 안에서 artifact별 참조 접두 허용·거부, resolved 집합 일치, checklist와 verdict 규칙만 판정하며 프롬프트의 supplied target 집합을 추론하지 않는다. Spec C8은 기존 `READY-|SPEC-` 의미를 유지한다.

### R5. 상태·재개·하위 호환성

- **R5.1** schema version과 기존 state key/record shape를 바꾸지 않는다. `readiness.plan`과 `draft_attempts.plan`만 사용하며 readiness 또는 draft_attempts가 없는 schema v1 레거시 상태는 load만으로 변이하지 않고 첫 해당 기록 때 현재 기본 구조로 lazy 생성한다.
- **R5.2** Plan author/readiness를 여러 번 실행해도 `draft_attempts.plan`과 `readiness.plan[].attempt`만 단조 증가하고 Spec counter/list와 모든 공식 `rounds`는 변하지 않는다. readiness `formal_round`는 항상 다음 공식 Plan round인 `rounds.plan + 1`이다.
- **R5.3** 진행 중 `PLAN_REVIEW`를 재개하면 기존 Spec/Plan artifacts와 digests, reviews, rounds, open findings, revision checks, readiness, draft attempts 및 `plan_approval`을 손실·재번호화하지 않는다. 레거시 필드 부재는 0회 실행으로 해석한다.
- **R5.4** readiness 기록은 `recorded`, `schema_invalid`, `digest_mismatch`, `invocation_failed` 기존 outcome만 사용한다. 실패 record의 `verdict`·`score`는 null이고 checklist·findings·resolved IDs는 빈 배열이며 reviewer model, 대상 digest, result 또는 stderr 경로와 시각은 남긴다.
- **R5.5** `ALLOWED_TRANSITIONS`, `TERMINAL_STATES`, `ROUND_LIMITS == {spec: 3, plan: 2, code: 3}`, `REQUIRED_CHECKS`, Spec/Plan 85점 gate, approval digest와 completion fingerprint 계약은 변경하지 않는다.

### R6. 실패·쓰기 범위·복구

- **R6.1** Plan author가 0이 아닌 종료, result 누락·invalid, 동일 digest 또는 부분 쓰기로 끝나면 `PLAN_REVIEW`에 머물고 그 호출을 공식 라운드로 소비하지 않는다. 변경을 자동 revert하지 않고 stderr/result 경로와 실제 변경 경로를 보고하며, 다음 readiness·공식 리뷰에는 성공한 재작성 결과만 사용한다.
- **R6.2** author가 허용 범위 밖 파일을 쓰거나 codex-result `changed_files`와 실제 변경이 다르면 기존 dirty 파일을 포함해 자동 복구하지 않고 사용자 판단을 요청한다. pre-existing dirty path는 바이트 단위로 보존하고 task 변경으로 주장하지 않는다.
- **R6.3** readiness 비정상 종료, timeout, result 누락·invalid, artifact 종류·경로·digest 불일치는 현재 단계를 바꾸지 않고 실패 outcome 또는 호출 전 중단과 evidence summary로 드러난다. advisory 실패만으로 공식 리뷰를 소비하거나 막지 않으며, model unavailable은 현행 `BLOCKED_MODEL_UNAVAILABLE` 사용자 승인·무대체 복구를 따른다.
- **R6.4** author와 readiness 모델이 unavailable/rejected이면 다른 모델로 자동 대체하지 않는다. 현 단계에서 실패 명령·stderr를 제시하고 사용자 승인된 대체만 기록해 재시도하며, 사용자가 거부하거나 연락할 수 없을 때만 `BLOCKED`로 전이한다.

### R7. 테스트·문서·버전

- **R7.1** 기준선의 `test_content_contracts.py`, `test_quality_state.py`, `test_validate_review.py`, `test_revision_check.py`, `test_execution_watchdog.py` 다섯 파일에 있던 모든 테스트 이름을 삭제·이름 변경하지 않는다. 이를 기계적으로 강제하도록 `assert_tests_preserved.py`의 `TEST_PATHS`를 이 다섯 파일의 정확한 목록으로 갱신하고, `docs/quality-goal-maintenance.md`의 `QG_BASE`를 다섯째 파일도 존재하는 이 작업 기준선 `92f387361775d6c6eebf9701d69e5653b5226806`으로 갱신하여 그 값으로 `assert_tests_preserved.py "$QG_BASE"`가 성공하게 한다. 기존 Spec author/readiness 내용 계약 테스트 25개를 약화하지 않은 채 Plan author routes/prompt/write scope/failure, Plan evidence attachment, artifact별 C1~C8과 보호 절 밖의 `SKILL.md` Plan author 절을 검증하는 새 내용 계약 테스트를 추가한다. 이 helper와 maintenance 기준선 갱신은 비목표 8에 열거된 기존 Plan 지원 상태·CLI·revision/template 구조가 아니므로 그 비목표와 충돌하지 않는다.
- **R7.2** 모든 신규 Plan 전용 content contract, schema/validator, state 테스트 이름에는 공통 식별 규약으로 `plan_author` 또는 `plan_readiness` 중 하나를 포함한다. schema/validator 테스트는 `plan_readiness`를 포함하고 두 artifact 정상 결과, 발급 `READY-` 고정, Spec의 `PLAN-` 참조 거부, Plan의 `SPEC-` 참조 거부, Plan의 `READY-|PLAN-` 참조 허용, CLI/result artifact mismatch, 기존 단일 인자 validator 호출, resolved-set 및 digest 검증 순서를 포함한다.
- **R7.3** state 테스트는 Plan draft/readiness의 독립 counter, 공식 rounds 비소비, 낮은 점수·`REVISE`·실패 readiness와 공식 review 독립성, 네 failure outcome, 레거시 lazy 생성과 기존 `PLAN_REVIEW` 재개 보존을 포함한다.
- **R7.4** `/opt/homebrew/bin/python3`로 기존 479개 전부와 신규 테스트가 통과해야 한다. 기준선 테스트 이름 보존, Plan revision check, strict marker, Spec 동작, 85점·3/2/3·승인 digest·dirty-worktree·결정적 검증·Code completion 계약을 함께 회귀 검증한다.
- **R7.5** `SKILL.md`의 byte 보존 대상 `### Plan` 절은 수정하지 않고, 1단계 `### Execution watchdog` 전례와 같이 그 절 바로 앞의 보호 범위 밖에 새 `### Plan author` 절을 두어 author→readiness→공식 reviewer 순서와 evidence attachment를 추가한다. `readiness-policy.md`는 기존 Spec 문언/테스트를 보존하는 Spec/Plan 공용 정책으로 확장하고 `model-routing.md`와 `docs/quality-goal-maintenance.md`를 동기화한다. maintenance의 `QG_BASE`는 R7.1의 `92f387361775d6c6eebf9701d69e5653b5226806` 하나를 `assert_tests_preserved.py`와 `assert_preserved_sections.py`가 함께 사용하며, 보존 비교 기준도 옛 `6d60011cbdaead7946b191d3f12029eef5c141c8`에서 이 작업 기준선으로 의도적으로 이동한다. 두 helper가 그 값으로 성공해야 한다. 기능 추가이므로 frontmatter version은 문자열로 정확히 `6.1.0`이어야 하고 maintenance의 500행 미만 계약을 유지한다.

## Acceptance criteria

- **AC-1** standard·strict Plan 초안·개정의 작성 주체가 Codex이고 오케스트레이터가 Plan 본문을 직접 쓰지 않으며 light 절차는 불변이라는 계약을 `SKILL.md`의 보호 대상 `### Plan` 바로 앞에 둔 새 `### Plan author` 절과 정책 테스트가 확인하고, 기존 `### Plan` bytes는 보존된다. [실행] (CMD-1 CMD-10)
- **AC-2** Plan author 프롬프트 계약이 R1.2의 경로·findings·제약·문법·revision-note·cross-regression 요소를 모두 요구하고 모든 고정 문서 경로를 절대 경로로 전달하도록 테스트된다. [실행] (CMD-1)
- **AC-3** model route 표에 Plan author standard/strict 두 행이 정확한 모델·effort로 존재하고 기존 author 템플릿/watchdog를 하나만 재사용하며 별도 중복 템플릿이 없음을 테스트한다. [실행] (CMD-1)
- **AC-4** 허용 파일·dirty 제외·실제 변경과 `changed_files`·codex-result·종료 코드·Plan digest 변화의 성공 조건이 정책에 명시되고 내용 계약 테스트가 확인한다. [실행] (CMD-1)
- **AC-5** Plan draft attempt가 `draft_attempts.plan`만 증가시키고 어떤 공식 round도 바꾸지 않으며 새 state key가 생기지 않는다. [실행] (CMD-3)
- **AC-6** Plan 라운드 2 개정이 기존 revision-note와 `revision_check.py --artifact plan --spec`을 사용하고 검증 성공 전 공식 리뷰 기록이 거부되며, 기존 Plan revision-check 회귀 테스트가 통과한다. [실행] (CMD-4)
- **AC-7** Plan author와 readiness가 서로 다른 fresh/ephemeral context이고 readiness route가 `gpt-5.6-sol` high/read-only/schema/watchdog 계약을 사용함을 정책 테스트가 확인한다. [실행] (CMD-1)
- **AC-8** 등록 경로·payload artifact·CLI artifact·현재 Plan SHA-256이 모두 일치한 결과만 `readiness.plan`의 `recorded` outcome이 되고 Spec/이전 digest 결과는 채택되지 않는다. [실행] (CMD-2)
- **AC-9** Plan readiness prompt가 R2.3의 현재 문서·정책 경로와 prior finding 전문을 받고 reference/issued ID를 구분한다는 내용 계약이 통과한다. [실행] (CMD-1)
- **AC-10** score 0/100과 verdict `READY`/`REVISE`가 상태 전이·공식 round·공식 review 명령의 수용 여부를 바꾸지 않는다. [실행] (CMD-3)
- **AC-11** 공식 Plan reviewer evidence에 마지막 result JSON과 정확한 `readiness-evidence-plan-r<N>.md` 경로가 첨부되고, 무효·누락 결과 사유 및 미충족 항목이 summary에 남으며 인라인·판정 구속이 금지됨을 테스트한다. [실행] (CMD-1)
- **AC-12** Plan readiness 기록은 `readiness.plan`만, 공식 review 기록은 `reviews.plan`과 `rounds.plan`만 갱신하고, readiness 실패 또는 `REVISE` 상태에서도 세 공식 review 기록 명령이 독립적으로 동작한다. [실행] (CMD-3)
- **AC-13** readiness schema의 artifact enum이 정확히 `spec`, `plan`이고 나머지 R3.1 shape 제약이 유지되며, schema 객체 트리를 키 단위로 재귀 검사했을 때 `if`, `then`, `oneOf`, `allOf`, `anyOf`, `const`가 하나도 없다. 문자열 값에 이 철자가 부분 문자열로 들어가는지는 판정하지 않는다. [실행] (CMD-8)
- **AC-14** 두 artifact 모두 발급 finding/blocker에 `READY-` 외 접두를 주면 검증이 실패한다. [실행] (CMD-2)
- **AC-15** Spec 결과는 `READY-|SPEC-`, Plan 결과는 `READY-|PLAN-` 참조만 받아들이며 반대 artifact의 공식 접두를 넣은 교차 오염 결과는 각각 실패한다. [실행] (CMD-2)
- **AC-16** resolved ID 집합 일치, prior finding shape와 C1~C8 정확히 한 번 규칙이 Spec/Plan 정상·오류 fixture에서 동일하게 검증된다. [실행] (CMD-2)
- **AC-17** CLI `--artifact`와 payload artifact가 다른 결과는 `schema_invalid`이고 record shape의 유효 결과 필드는 비어 있으며, expected artifact 기본값 때문에 기존 `validate_readiness_result(payload)` 단일 인자 호출 회귀가 그대로 통과한다. [실행] (CMD-2)
- **AC-18** schema/artifact 오류와 digest 오류가 함께 있으면 `schema_invalid`, schema와 artifact가 정상이나 result digest만 다르면 `digest_mismatch`, 등록 파일과 CLI digest가 다르면 기록 거부가 된다. [실행] (CMD-2)
- **AC-19** readiness 정책에 Spec C1~C8 기존 의미와 정확히 여덟 ID가 보존되고, Plan 사상과 공식 reviewer 책임 경계가 별도 표 또는 절에 존재한다. [실행] (CMD-1)
- **AC-20** content contract가 Plan C1~C7 각각에서 R4.2의 대상·관계·실패 조건을 추출해 확인하고, readiness-result의 checklist pass/fail fixture가 여덟 항목 고정 및 verdict 규칙을 통과한다. 이는 문언의 기계적 명확성을 검증하며 artifact 판정 권한은 fresh readiness reviewer에 남긴다. [실행] (CMD-1)
- **AC-21** content contract는 Plan C8 정책의 supplied `READY-|PLAN-` target별 정확히 한 번 판정, `partial` 미충족, 빈 target과 원 접두 보존을 확인하고, validator 테스트는 payload 내부의 `SPEC-` 참조 거부, `READY-|PLAN-` 허용, resolved 집합 및 checklist/verdict 규칙을 확인한다. [실행] (CMD-1 CMD-2)
- **AC-22** 새 init state의 key와 schema version은 기준선과 같고, Plan 기록은 기존 두 필드만 사용하며 두 필드가 없는 v1 fixture는 load 시 byte·객체가 변하지 않고 첫 Plan 기록 때 lazy 생성된다. [실행] (CMD-3)
- **AC-23** Plan attempt가 공식 round를 넘어 단조 증가하고 `formal_round == rounds.plan + 1`이며 Spec counter/list와 모든 공식 round가 변하지 않는다. [실행] (CMD-3)
- **AC-24** 기존 `PLAN_REVIEW` 상태를 save/select-resume/load한 뒤 R5.3의 모든 값과 승인 path/digest가 재개 전과 같다. [실행] (CMD-3)
- **AC-25** Plan readiness의 정상 및 세 실패가 기존 네 outcome만 만들고 실패 record의 null/empty/실행 정보 shape가 R5.4와 정확히 일치한다. [실행] (CMD-3)
- **AC-26** 상태 전이·terminal·3/2/3·`REQUIRED_CHECKS`, 85점, approval digest와 completion fingerprint 회귀 테스트가 모두 통과한다. [실행] (CMD-6)
- **AC-27** Plan author의 nonzero/missing/invalid/unchanged/partial-write 각각에 대해 정책 content test가 단계·round 불변, 자동 revert 금지, 성공 재작성 전 후속 심사 금지를 확인한다. [실행] (CMD-1)
- **AC-28** 정책 content test가 out-of-scope write·changed_files mismatch·pre-existing dirty path에서 사용자 보고와 byte 보존을 요구하는지 확인한다. [실행] (CMD-1)
- **AC-29** readiness timeout/nonzero/missing/invalid/artifact/path/digest 실패가 단계·공식 round를 바꾸지 않고 실패 근거를 남기며, advisory 실패 뒤 공식 review가 가능함을 테스트한다. [실행] (CMD-3)
- **AC-30** Plan author/readiness model unavailable 계약이 무대체, 현 단계 대기, 사용자 승인 대체 기록, 거부·연락 불가 때만 `BLOCKED_MODEL_UNAVAILABLE`을 요구함을 내용 테스트가 확인한다. [실행] (CMD-1)
- **AC-31** R7.1의 기준선 다섯 테스트 파일에 있던 모든 테스트 이름이 남고, 그중 기존 Spec author/readiness 내용 계약 테스트 25개와 공통 이름 규약을 따르는 새 Plan 전용 내용 테스트를 포함한 content contract 전체가 통과한다. `assert_tests_preserved.py`의 대상 목록 자체도 그 다섯 파일과 정확히 일치하고 maintenance의 갱신된 `QG_BASE`로 실제 성공한다. [실행] (CMD-7 CMD-10)
- **AC-32** `plan_readiness` 이름 규약을 따르는 schema/validator 신규 테스트와 `plan_author|plan_readiness` 규약을 따르는 state 신규 테스트가 각각 R7.2와 R7.3의 Plan 정상·교차 오염·failure·resume 사례 및 기존 단일 인자 validator 호출 회귀를 포함해 통과한다. [실행] (CMD-2 CMD-3)
- **AC-33** CMD-7이 기준선 다섯 파일의 기존 테스트 이름 보존을 먼저 입증하고, `/opt/homebrew/bin/python3` 전체 suite가 479건보다 많은 테스트를 실제로 실행해 `OK`로 끝난다. [실행] (CMD-5 CMD-7)
- **AC-34** `revision_check.py`, `templates/plan.md`, `templates/spec.md`가 기준선과 byte 단위로 같고, 기존 Plan revision/strict marker/Spec 및 Code 계약 회귀가 통과한다. [실행] (CMD-4)
- **AC-35** `SKILL.md`의 새 `### Plan author` 절, readiness/model-routing 정책과 maintenance 문서가 Plan author/readiness를 일관되게 열거하고 기존 `### Plan` bytes를 보존하며, 두 preservation helper가 같은 갱신된 `QG_BASE`로 성공하고, 파싱한 `SKILL.md` frontmatter `version` 문자열이 정확히 `6.1.0`이며 파일이 500행 미만이다. [실행] (CMD-9 CMD-10)

## Requirements traceability

This table maps every requirement to acceptance criteria and the judgement method that proves the mapping.

| Requirement | Acceptance criteria | Judgement method |
|---|---|---|
| R1.1 | AC-1 | CMD-1 content contract and CMD-10 preserved section |
| R1.2 | AC-2 | CMD-1 Plan prompt contract |
| R1.3 | AC-3 | CMD-1 routing/template contract |
| R1.4 | AC-4 | CMD-1 write/output contract |
| R1.5 | AC-5 | CMD-3 state behavior |
| R1.6 | AC-6 | CMD-4 revision regression |
| R2.1 | AC-7 | CMD-1 fresh-context contract |
| R2.2 | AC-8 | CMD-2 artifact/digest validation |
| R2.3 | AC-9 | CMD-1 prompt contract |
| R2.4 | AC-10 | CMD-3 advisory independence |
| R2.5 | AC-11 | CMD-1 evidence contract |
| R2.6 | AC-12 | CMD-3 record separation |
| R3.1 | AC-13 | CMD-8 schema assertions |
| R3.2 | AC-14 | CMD-2 issued namespace tests |
| R3.3 | AC-15 | CMD-2 artifact namespace tests |
| R3.4 | AC-16 | CMD-2 shape/set tests |
| R3.5 | AC-17 | CMD-2 expected-artifact test |
| R3.6 | AC-18 | CMD-2 validation-order tests |
| R4.1 | AC-19 | CMD-1 policy contract |
| R4.2 | AC-20 | CMD-1 Plan C1~C7 fixtures |
| R4.3 | AC-21 | CMD-1 Plan C8 policy contract and CMD-2 validator tests |
| R5.1 | AC-22 | CMD-3 legacy compatibility |
| R5.2 | AC-23 | CMD-3 counters/formal round |
| R5.3 | AC-24 | CMD-3 resume preservation |
| R5.4 | AC-25 | CMD-3 outcome shape |
| R5.5 | AC-26 | CMD-6 protected contracts |
| R6.1 | AC-27 | CMD-1 author failure contract |
| R6.2 | AC-28 | CMD-1 dirty/write-scope contract |
| R6.3 | AC-29 | CMD-3 readiness failures |
| R6.4 | AC-30 | CMD-1 model recovery contract |
| R7.1 | AC-31 | CMD-7 preserved and new content tests, CMD-10 maintenance baseline execution |
| R7.2 | AC-32 | CMD-2 schema/validator coverage |
| R7.3 | AC-32 | CMD-3 state coverage with positive name guard |
| R7.4 | AC-33, AC-34 | CMD-5 full suite, CMD-7 baseline preservation, and CMD-4 protected files |
| R7.5 | AC-1, AC-35 | CMD-1 external Plan author contract, CMD-9 synchronized docs/exact version, CMD-10 shared baseline preservation |

## Architecture

변경은 기존 오케스트레이터 경계 안에서 세 층으로 나뉜다.

1. `SKILL.md`와 `references/readiness-policy.md`가 Plan stage 절차의 정본이다. 오케스트레이터는 Plan author를 호출하고, 성공한 파일을 등록한 뒤 fresh readiness를 호출하고, 마지막으로 기존 fresh 공식 reviewer를 호출한다.
2. `references/model-routing.md`가 역할별 모델·effort와 하나의 author 및 하나의 readiness 실행 템플릿 정본이다. Plan author는 역할 행만 추가하고 실행 블록은 Spec과 공유한다.
3. `schemas/readiness-result.schema.json`과 `scripts/validate_review.py`가 transport와 artifact별 의미 검증을 담당한다. `scripts/quality_state.py`는 이미 존재하는 Plan 기록 구조를 사용하되 payload/CLI artifact 일치 전달만 보강한다.

`templates/plan.md`, `templates/spec.md`, `scripts/revision_check.py`는 이번 기능의 소비 대상이지 변경 대상이 아니다. 상태 기계, 공식 review gate와 Code completion은 기존 경계 바깥에 두어 Plan author/readiness가 advisory evidence producer 이상이 되지 않게 한다.

## Interfaces and data flow

정상 standard·strict Plan round의 데이터 흐름은 다음과 같다.

1. 오케스트레이터가 통과한 Spec, 현재 formal round와 prior findings를 확정하고 `record-draft-attempt --artifact plan`을 호출한다.
2. Plan author는 workspace-write ephemeral 실행에서 `plan.md`와 필요 시 revision note를 쓰고 codex-result를 반환한다. 오케스트레이터가 result, 쓰기 범위, current digest를 검증해 `set-artifact --kind plan`으로 등록한다.
3. 라운드 2 이상이면 기존 revision check가 Plan/Spec/state를 대조한다.
4. 오케스트레이터가 등록 경로에서 current Plan SHA-256을 계산해 fresh read-only readiness prompt에 싣는다. 결과는 `artifact: plan`, 같은 digest, reviewer model/attempt/formal round, C1~C8, findings, prior judgements와 evidence를 가진다.
5. `record-readiness --artifact plan`이 schema → artifact namespace/match → digest 순으로 검증해 `readiness.plan`에 advisory record를 추가한다.
6. 오케스트레이터가 마지막 result와 `readiness-evidence-plan-r<N>.md` 경로를 공식 Plan review의 repository evidence에 추가한다. 공식 reviewer와 `record-review`는 readiness와 독립적으로 기존 Plan gate를 수행한다.

공식 finding의 원 접두는 artifact 의미를 보존한다. readiness가 새로 발급하는 `READY-`는 두 artifact에서 공통이고, Spec 공식 finding은 `SPEC-`, Plan 공식 finding은 `PLAN-`이다. `prior_findings.source`가 `readiness` 또는 `formal`을 표시하며 `resolved_finding_ids`는 resolved subset의 정확한 투영이다.

## Failure behavior

- author 호출 실패 또는 partial write는 성공으로 등록하지 않는다. stage와 공식 round를 유지하고 실제 bytes와 stderr/result evidence를 보존해 재시도 또는 사용자 판단에 사용한다. 사용자 소유 변경은 자동으로 되돌리지 않는다.
- readiness 경로·artifact·schema·digest 오류는 잘못된 결과가 현재 Plan에 귀속되지 않게 한다. 호출 전 path mismatch는 실행하지 않고, 실행 후 오류는 기존 failure outcome과 summary에 남긴다.
- readiness는 advisory이므로 낮은 점수, `REVISE`, schema/digest/invocation failure가 공식 gate 결과로 변환되지 않는다. 다만 model unavailable은 기존 사용자 승인 기반 복구 절차를 그대로 사용한다.
- 레거시 상태의 필드 부재는 오류가 아니라 아직 Plan/Spec author-readiness를 실행하지 않은 상태다. load는 비변이이고 첫 기록 시에만 기존 기본 구조를 생성한다.
- 공식 Plan reviewer 실패, 라운드 소진, 승인 digest mismatch와 Code verification 실패는 이번 기능이 가로채지 않고 기존 오류·전이 계약으로 처리한다.

## Security and risk

author는 workspace-write여서 허용 파일 밖 쓰기와 pre-existing dirty 변경이 주된 위험이다. 절대 경로 allowlist, ephemeral 실행, execution watchdog, codex-result와 실제 git 변화 대조, 자동 revert 금지로 사용자 데이터를 보호한다. readiness는 read-only fresh context로 격리해 author 주장을 독립 근거로 오인하지 않는다.

artifact enum 확대 뒤 가장 큰 무결성 위험은 교차 오염이다. schema의 문법적 합집합만으로는 Spec 결과에 `PLAN-`을 넣는 것을 막지 못하므로 validator가 artifact별 reference namespace와 expected artifact를 강제한다. digest는 등록 캐시가 아니라 실제 대상 파일에서 호출 직전에 계산해 stale revision 재사용을 막는다.

프롬프트·result·events·stderr·evidence는 기존 `.claude/quality-state/<task-id>/<execution-id>/` 경계에 두고 credential을 포함하지 않는다. git write, sandbox bypass, 자동 commit/push/merge/deploy는 현행 금지를 유지한다. 신규 상태 전이나 gate가 없으므로 advisory reviewer가 권위 있는 결정을 탈취하는 경로도 만들지 않는다.

## Test strategy

구현은 content contract, schema/semantic validator, state behavior, preserved regression 순으로 검증한다. 새 tests는 먼저 부재 또는 실패를 확인한 뒤 최소 구현으로 통과시킨다. 기존 479건과 특히 `test_content_contracts.py`의 Spec author/readiness 25건은 삭제·rename·완화할 수 없다. fixture는 Spec 정상/교차 오류와 Plan 정상/교차 오류를 분리해 artifact 의미를 한 눈에 드러내야 한다.

### 판정 명령 표

| ID | 명령 | 통과 조건 |
|---|---|---|
| CMD-1 | `/opt/homebrew/bin/python3 -c "import os,re,subprocess,sys; env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}; r=subprocess.run(['/opt/homebrew/bin/python3','-m','unittest','discover','-s','dot_claude/skills/quality-goal/tests','-p','test_content_contracts.py','-k','plan_author','-k','plan_readiness'],env=env,text=True,capture_output=True); out=r.stdout+r.stderr; print(out,end=''); m=re.search(r'^Ran ([0-9]+) tests?',out,re.MULTILINE); sys.exit(0 if r.returncode==0 and m and int(m.group(1))>0 else 1)"` | 종료 코드 0, 이름에 `plan_author` 또는 `plan_readiness`가 포함된 신규 내용 계약의 `Ran N tests`에서 N > 0, `OK` |
| CMD-2 | `/opt/homebrew/bin/python3 -c "import os,re,subprocess,sys; env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}; r=subprocess.run(['/opt/homebrew/bin/python3','-m','unittest','discover','-s','dot_claude/skills/quality-goal/tests','-p','test_validate_review.py','-k','plan_readiness'],env=env,text=True,capture_output=True); out=r.stdout+r.stderr; print(out,end=''); m=re.search(r'^Ran ([0-9]+) tests?',out,re.MULTILINE); sys.exit(0 if r.returncode==0 and m and int(m.group(1))>0 else 1)"` | 종료 코드 0, `plan_readiness`가 이름에 포함된 신규 Spec/Plan schema·namespace·artifact·digest 테스트의 `Ran N tests`에서 N > 0, `OK` |
| CMD-3 | `/opt/homebrew/bin/python3 -c "import os,re,subprocess,sys; env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}; r=subprocess.run(['/opt/homebrew/bin/python3','-m','unittest','discover','-s','dot_claude/skills/quality-goal/tests','-p','test_quality_state.py','-k','plan_author','-k','plan_readiness'],env=env,text=True,capture_output=True); out=r.stdout+r.stderr; print(out,end=''); m=re.search(r'^Ran ([0-9]+) tests?',out,re.MULTILINE); sys.exit(0 if r.returncode==0 and m and int(m.group(1))>0 else 1)"` | 종료 코드 0, 이름에 `plan_author` 또는 `plan_readiness`가 포함된 신규 Plan 기록·failure·resume·공식 round 독립성 테스트의 `Ran N tests`에서 N > 0, `OK` |
| CMD-4 | `git diff --quiet 92f387361775d6c6eebf9701d69e5653b5226806 -- dot_claude/skills/quality-goal/scripts/revision_check.py dot_claude/skills/quality-goal/templates/plan.md dot_claude/skills/quality-goal/templates/spec.md && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/quality-goal/tests -p 'test_revision_check.py'` | 종료 코드 0, 세 파일 byte 불변 및 Plan/Spec revision suite `OK` |
| CMD-5 | `/opt/homebrew/bin/python3 -c "import os,re,subprocess,sys; env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}; r=subprocess.run(['/opt/homebrew/bin/python3','-m','unittest','discover','-s','dot_claude/skills/quality-goal/tests','-p','test_*.py'],env=env,text=True,capture_output=True); out=r.stdout+r.stderr; print(out,end=''); m=re.search(r'^Ran ([0-9]+) tests?',out,re.MULTILINE); sys.exit(0 if r.returncode==0 and m and int(m.group(1))>479 else 1)"` | 종료 코드 0, `Ran N tests`의 N > 479, `OK` |
| CMD-6 | `for pattern in round_limits_and_required_checks_unchanged formal_pass_gate_threshold_unchanged transitions_and_terminal_states_unchanged approve_plan dirty completion; do /opt/homebrew/bin/python3 -c "import os,re,subprocess,sys; env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}; r=subprocess.run(['/opt/homebrew/bin/python3','-m','unittest','discover','-s','dot_claude/skills/quality-goal/tests','-p','test_*.py','-k',sys.argv[1]],env=env,text=True,capture_output=True); out=r.stdout+r.stderr; print(out,end=''); m=re.search(r'^Ran ([0-9]+) tests?',out,re.MULTILINE); sys.exit(0 if r.returncode==0 and m and int(m.group(1))>0 else 1)" "$pattern" || exit 1; done` | 각 패턴의 종료 코드 0과 `Ran N tests`의 N > 0, 보호 계약 회귀 테스트 `OK` |
| CMD-7 | `/opt/homebrew/bin/python3 -c "import runpy; actual=runpy.run_path('dot_claude/skills/quality-goal/tests/assert_tests_preserved.py')['TEST_PATHS']; expected=('dot_claude/skills/quality-goal/tests/test_content_contracts.py','dot_claude/skills/quality-goal/tests/test_quality_state.py','dot_claude/skills/quality-goal/tests/test_validate_review.py','dot_claude/skills/quality-goal/tests/test_revision_check.py','dot_claude/skills/quality-goal/tests/test_execution_watchdog.py'); assert actual==expected, (actual,expected)" && /opt/homebrew/bin/python3 dot_claude/skills/quality-goal/tests/assert_tests_preserved.py 92f387361775d6c6eebf9701d69e5653b5226806 && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/quality-goal/tests -p 'test_content_contracts.py'` | 종료 코드 0, 보존 helper의 대상이 기준선 다섯 파일과 정확히 일치, 다섯 파일의 `기존 테스트 보존`, content contract 전체 `OK` |
| CMD-8 | `/opt/homebrew/bin/python3 -c "import json; p='dot_claude/skills/quality-goal/schemas/readiness-result.schema.json'; d=json.load(open(p)); a=d['properties']['artifact']; assert a['type']=='string' and a['enum']==['spec','plan']; assert d['type']=='object' and d['additionalProperties'] is False; forbidden={'if','then','oneOf','allOf','anyOf','const'}; keys=lambda v: set(v).union(*(keys(x) for x in v.values())) if isinstance(v,dict) else set().union(*(keys(x) for x in v)) if isinstance(v,list) else set(); assert forbidden.isdisjoint(keys(d)), sorted(forbidden & keys(d)); print('OK')"` | 종료 코드 0, schema 객체 트리의 키에 `if`, `then`, `oneOf`, `allOf`, `anyOf`, `const`가 없고 artifact/shape 계약이 유지됨, `OK` |
| CMD-9 | `/opt/homebrew/bin/python3 -c "import pathlib,re; text=pathlib.Path('dot_claude/skills/quality-goal/SKILL.md').read_text(encoding='utf-8'); block=text.split('---',2)[1]; m=re.search(r'(?m)^version:\s*(.+?)\s*$',block); assert m and m.group(1)=='6.1.0', m.group(1) if m else None" && test "$(wc -l < dot_claude/skills/quality-goal/SKILL.md | tr -d ' ')" -lt 500 && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/quality-goal/tests -p 'test_content_contracts.py'` | 종료 코드 0, 파싱한 frontmatter `version` 문자열이 정확히 `6.1.0`, 500행 미만, 세 문서 동기화 content suite `OK` |
| CMD-10 | `QG_BASE=$(/opt/homebrew/bin/python3 -c "import pathlib,re; text=pathlib.Path('docs/quality-goal-maintenance.md').read_text(encoding='utf-8'); m=re.search(r'QG_BASE[^\n]*?([0-9a-f]{40})',text); assert m; print(m.group(1))") && test "$QG_BASE" = 92f387361775d6c6eebf9701d69e5653b5226806 && /opt/homebrew/bin/python3 dot_claude/skills/quality-goal/tests/assert_tests_preserved.py "$QG_BASE" && /opt/homebrew/bin/python3 dot_claude/skills/quality-goal/tests/assert_preserved_sections.py "$QG_BASE"` | 종료 코드 0, maintenance의 단일 `QG_BASE`가 정확히 작업 기준선이고 그 값으로 `기존 테스트 보존`과 `보존 대상 절 불변`이 모두 출력됨 |

CMD-1·CMD-2·CMD-3은 R7.2의 단일 이름 규약으로 선택한 테스트 수가 양수임을 강제한다. CMD-7은 기준선 다섯 파일의 테스트 이름 보존을, CMD-5는 전체 suite의 성공과 기준선보다 큰 실행 수를 서로 보완해 증명한다. CMD-10은 maintenance에서 읽은 동일한 작업 기준선을 테스트 보존과 `### Plan` 포함 절 보존에 함께 적용하며, 기준 이동이 두 helper에 동시에 미치는 영향을 의도적으로 검증한다. CMD-4의 byte 불변 대상과 회귀 suite는 AC-34의 별도 보호 경계이므로 이 주장들과 모순되지 않는다. 타깃 검증과 CMD-7·CMD-10 뒤 CMD-5를 최종 실행한다. 저장소에는 별도 type-check, lint, build, E2E 구성이 없으므로 구현 Plan은 이를 근거 경로와 함께 `not configured`로 기록하고 통과로 간주하지 않는다.

## Decisions

### D1. 하나의 readiness schema에서 두 artifact를 받되 artifact별 의미 검증은 validator가 담당한다

- 안 1: 현재 schema 하나의 artifact enum을 `spec`, `plan`으로 늘리고 참조 ID 패턴은 `READY-|SPEC-|PLAN-` 합집합으로 둔 뒤 validator가 artifact별 허용 집합을 강제한다. 기존 custom schema validator가 지원하는 키만 사용하고 output-schema도 하나로 유지할 수 있다.
- 안 2: 한 schema 안에 `if`/`then`/`oneOf`/`allOf`/`anyOf`/`const` 같은 조건부·상수 키로 artifact별 reference pattern을 표현한다. JSON Schema 자체는 더 엄격하지만 현재 `_validate_schema_value`가 이 키들을 지원하지 않아 범용 schema evaluator 확장과 별도 회귀가 필요하다.
- 안 3: Spec/Plan readiness schema 파일을 나눈다. 각 파일은 단순하지만 route·policy·watchdog·maintenance에서 schema 선택 분기가 늘고 공통 13필드가 쉽게 발산한다.

권고는 안 1이다. transport shape는 공통 schema 하나로 유지하고 D2의 semantic validator가 교차 오염을 거부한다. Plan은 참조 자리에서만 `READY-|PLAN-`을 허용하며 발급 자리는 계속 `READY-`다.

### D2. validator는 artifact별 reference prefix map과 expected-artifact 대조를 사용한다

- 안 1: `REFERENCE_PREFIXES = {spec: (READY-, SPEC-), plan: (READY-, PLAN-)}` 같은 명시적 map으로 `prior_findings`와 resolved IDs를 검사하고 기록 호출이 expected artifact를 전달한다. 교차 오염을 양방향 거부한다.
- 안 2: 세 접두를 모든 artifact에서 허용한다. 구현은 작지만 stale/misrouted 공식 finding이 현재 artifact의 해소 근거로 채택될 수 있어 digest 연결만으로 막을 수 없다.
- 안 3: ID prefix를 새 공통 namespace로 정규화한다. 1단계의 `SPEC-16`에서 확인한 발급/참조 구분과 공식 finding의 stable ID를 훼손한다.

권고는 안 1이다. error 문구도 expected artifact와 허용 접두를 드러내고, schema/artifact 의미 오류를 digest 오류보다 먼저 판정한다.

### D3. Plan C1~C8은 문서 구조·Spec 추적·실행 가능성을 검사하도록 사상한다

- 안 1: R4.2~R4.3처럼 C1/C2는 template, C3/C4는 Spec↔Plan traceability, C5/C7은 검증 셀·명령 정의, C6은 task 번호, C8은 supplied findings를 검사한다. 모두 parser/fixture 또는 명확한 content contract로 판정 가능하다.
- 안 2: Spec 체크리스트 문언에서 Spec만 Plan으로 치환한다. Plan에는 요구사항 정의와 AC 본문이 없어 C3~C7이 artifact 구조와 맞지 않는다.
- 안 3: Plan에 필요한 항목을 더해 C1~C9 이상으로 확장한다. schema의 정확히 8개 계약과 비목표를 위반한다.

권고는 안 1이다. C5는 Verification command뿐 아니라 Expected outcome의 비어 있지 않음도 함께 확인하고, C7은 추적행의 `CMD-<n>`이 `## Verification commands`에 실제 정의되는지 검사한다. 설계 품질 판단은 공식 Plan rubric에 남긴다.

### D4. readiness-policy는 공용 문서로 유지하되 기존 Spec 절을 보존하고 Plan 전용 절·표를 추가한다

- 안 1: 제목과 공통 설명을 Spec/Plan으로 일반화하고 기존 `## Spec author`, digest/readiness/advisory/failure 절의 핵심 문언을 보존한 채 `## Plan author`, artifact별 prompt/evidence/checklist 사상을 추가한다.
- 안 2: 문서 전체를 artifact-neutral 추상 절차로 재작성한다. 중복은 줄지만 `test_content_contracts.py`의 기존 author/readiness 계약 25개가 의존하는 정확한 용어·절 경계를 한꺼번에 깨뜨린다.
- 안 3: `plan-readiness-policy.md`를 새로 만든다. Spec 회귀는 작지만 호출·failure·금지 옵션·freshness 규칙이 두 정본으로 갈라져 유지보수 drift 위험이 커진다.

권고는 안 1이다. 기존 25개 테스트를 그대로 통과시키는 것을 하위 호환 gate로 두고 Plan 전용 테스트를 추가한다. 공통 규칙의 정본은 한 곳에 유지하면서 artifact별 차이만 명시한다.

### D5. SKILL.md version은 6.1.0으로 올린다

- 안 1: `6.1.0` MINOR. standard·strict Plan 단계의 새 author/readiness 기능과 정책·라우트 추가를 나타내며 유지보수 문서의 SemVer 규칙과 맞는다.
- 안 2: `6.0.1` PATCH. 단순 문구 정정이 아니므로 기능 추가의 의미를 축소한다.
- 안 3: `7.0.0` MAJOR. 상태 전이·gate·기존 키 형식을 바꾸지 않아 호환 파괴 근거가 없다.

권고는 안 1이다. 정확한 version `6.1.0`을 내용 계약으로 고정한다.

### D6. 보호 대상 Plan 절은 유지하고 Plan author 절차를 바로 앞의 새 절에 둔다

- 안 1: 1단계의 `### Execution watchdog` 전례처럼 byte 보존 대상 `### Plan` 바로 앞에 보호 범위 밖의 새 `### Plan author` 절을 두고 author→readiness→공식 reviewer 절차와 evidence attachment를 기술한다. 기존 Plan 절 bytes와 보존 helper를 유지하면서 새 절차의 선행 관계를 명확히 할 수 있다.
- 안 2: `assert_preserved_sections.py`의 `PRESERVED_SECTIONS`에서 `### Plan`을 제거하거나 내용을 바꾸고 새 기준으로 다시 보호한다. 한 절 안에서 절차를 읽을 수 있지만 검증된 보호 경계를 넓게 해제하고 기존 내용 계약의 의도까지 다시 판단해야 한다.
- 안 3: `### Plan`을 수정한 뒤 preservation helper 또는 maintenance CMD-4만 예외 처리한다. 문서와 검증 정본이 발산하고 이후 회귀에서 보호 여부가 불명확해진다.

권고는 안 1이다. `### Plan` bytes는 작업 기준선 `92f387361775d6c6eebf9701d69e5653b5226806`과 같게 유지하고 새 `### Plan author` 절만 추가한다. R7.1에 따라 maintenance의 `QG_BASE`도 같은 작업 기준선으로 올리므로 `assert_tests_preserved.py`와 `assert_preserved_sections.py`가 정확히 같은 revision을 사용한다. 이는 `assert_preserved_sections.py`의 비교 기준도 옛 `6d60011cbdaead7946b191d3f12029eef5c141c8`에서 의도적으로 이동시키지만, 선택한 작업 기준선의 `### Plan` bytes를 새 보호 기준으로 명시적으로 고정한다.
