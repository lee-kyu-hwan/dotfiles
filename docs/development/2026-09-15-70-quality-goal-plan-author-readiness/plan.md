# Quality Goal Implementation Plan

- Task ID: 20260915T084306Z-70-2단계-quality-goal-plan-단계-codex-author-69b2a42e
- Mode: standard
- Status: PLAN_REVIEW
- Created: 2026-09-15T08:43:06Z
- Updated: 2026-09-17T00:00:00Z
- Source goal: #70 2단계 — quality-goal Plan 단계에 Codex author와 참고용(advisory) readiness를 추가한다

## Spec link

승인 대상 Spec은 `/Users/lee-kyu-hwan/code/dotfiles__worktrees/70-feat-quality-goal-plan-author-readiness/docs/development/2026-09-15-70-quality-goal-plan-author-readiness/spec.md` 이며 이 Plan이 사용한 SHA-256은 `0d76c16024b98ef68101d888823481c5aea0b112279c3a8615cecf9dfa95c402` 다. 공식 Spec 리뷰는 라운드 2에서 PASS(93점, blocker 0)로 통과했다. 미해결 advisory finding 둘을 이 Plan이 흡수한다. SPEC-06(Medium)은 `SKILL.md` 가 489행이고 CMD-9 가 500행 미만을 요구해 새 절 예산이 10행뿐이라는 것으로 T6 의 줄 수 예산 제약이 된다. SPEC-07(Low)은 AC-35 의 "maintenance 문서가 Plan author/readiness 를 일관되게 열거" 절에 기계적 판정 수단이 없다는 것으로, T6 이 maintenance 문서에 `Plan author (standard)`·`Plan author (strict)` 문자열을 추가하고 CMD-10 이 그 문자열 포함을 확인하게 해서 닫는다.

## Global constraints

- 저장소 관례: chezmoi 소스를 직접 편집하고 `chezmoi apply` 는 별도 승인 후에만 실행한다. 대화·커밋 메시지는 한국어.
- 테스트 실행기는 `/opt/homebrew/bin/python3` (CPython 3.14.7) 고정이다. `/usr/bin/python3` 는 `enterContext` 부재로 오탐을 만든다.
- 구현은 Codex `gpt-5.6-sol` 이 수행하고 오케스트레이션·리뷰 판단은 Claude Opus 가 한다. 모든 모델 호출은 사용자가 보는 tmux 전경 pane 에서 실행한다.
- **테스트 우선**: 각 태스크는 그 태스크가 검증할 테스트를 **그 태스크 안에서 먼저 작성**해 실패를 기록하고, 최소 구현을 붙인 뒤 통과를 기록한다. 테스트 작성을 뒤쪽 태스크로 미루지 않는다.
- 기준선은 `92f387361775d6c6eebf9701d69e5653b5226806` 이다. Spec 의 CMD-4·CMD-7·CMD-10 이 이 값을 참조하므로 구현 중에 바꾸지 않는다.
- **착수 선행 조건**: #111(PR #124)이 main 에 머지된 뒤에만 착수한다. 그 PR 이 profile2 미러와 `test_profile2_quality_bundle_mirror` 를 함께 들여오므로 머지 전에 스킬을 고치면 미러 기준이 흔들린다. 또 #111 이 Codex 를 점유하는 동안 동시 실행하면 capacity 오류로 라운드를 낭비한다. 미러 디렉터리가 없는 상태에서 착수하지 않으므로 CMD-11 에 조건부 건너뛰기는 없다.
- **profile2 미러 동기화**: `dot_claude/skills/quality-goal/` 하위 파일을 수정·추가·삭제할 때마다 `dot_local/share/ai-account-profiles/claude/profile2/skills/quality-goal/` 의 대응 경로에 **동일한 바이트**를 적용한다. #111 PR #124 의 `tests/test_orchestrator_profiles.py::test_profile2_quality_bundle_mirror` 가 `is_public_quality_file`(실파일, 심볼릭 링크 아님, `__pycache__` 밖, 확장자 `.pyc` 아님) 기준으로 **파일 집합의 정확한 일치**(`assertEqual(set(canonical), set(mirrored))`)와 **바이트 일치**(`assertEqual(source.read_bytes(), target.read_bytes())`)를 강제한다. 심볼릭 링크는 금지이고 미러 파일은 git 에 추적돼야 한다(`test_profile2_chezmoi_diff_redaction` 이 `git ls-files` 결과와 집합 일치를 요구한다). **신규 fixture 나 신규 파일을 추가하면 미러에도 같은 상대 경로로 추가한다** — 수정만 동기화하고 추가를 빠뜨리면 집합 불일치로 실패한다. 미러 동기화는 각 태스크의 완료 조건이며 T8 이 최종 확인한다.
- 사용자 미추적 작업을 삭제하거나 덮어쓰지 않는다. 착수 시 `initial_dirty_paths` 를 재확인하고 그 경로는 바이트 단위로 보존한다. `git clean` 을 쓰지 않는다.
- 자동 commit·push·merge·deploy 금지. 검증 blocker 가 남은 상태에서는 머지와 `chezmoi apply` 를 하지 않는다.
- 금지 Codex 플래그: `--skip-git-repo-check`, `--dangerously-bypass-approvals-and-sandbox`, `--dangerously-bypass-hook-trust`, `--approve-for-me`, `--ignore-rules`, `--ignore-user-config`, `--add-dir`, `--yolo`, `--full-auto`. 샌드박스는 템플릿보다 넓게 주지 않는다.
- macOS 에는 `timeout`·`gtimeout` 이 없다. 대기는 `execution_watchdog.py` 로 처리한다.

## File map

| 경로 | 조치 | 책임과 영향받는 계약 |
|---|---|---|
| `dot_claude/skills/quality-goal/schemas/readiness-result.schema.json` | 수정 | `artifact` enum 을 `["spec","plan"]` 으로 확장. 발급 자리 `^READY-` 유지, 참조 자리 패턴을 `READY-|SPEC-|PLAN-` 합집합으로. 조건부 키 미사용 유지 |
| `dot_claude/skills/quality-goal/scripts/validate_review.py` | 수정 | `validate_readiness_result` 에 expected artifact 를 기본값 있는 선택적 매개변수로 추가. artifact 별 참조 접두 map 으로 교차 오염 양방향 거부. 기존 단일 인자 호출 보존 |
| `dot_claude/skills/quality-goal/scripts/quality_state.py` | 수정 | `record-readiness` 가 CLI `--artifact` 를 검증 함수에 전달. payload/CLI artifact 불일치는 `schema_invalid`. 기존 네 outcome·record shape 불변 |
| `dot_claude/skills/quality-goal/references/readiness-policy.md` | 수정 | Spec/Plan 공용으로 확장. `## Plan author` 절과 artifact 별 C1~C8 사상 추가. **삽입 민감 단언 주의**: `test_content_contracts.py:377` 이 `policy.count("실행 가능한 정본은 \`references/model-routing.md\`") == 2` 를 단언한다 |
| `dot_claude/skills/quality-goal/references/model-routing.md` | 수정 | 라우트 표에 `Plan author (standard)`=`gpt-5.6-terra`/high, `Plan author (strict)`=`gpt-5.6-sol`/high 두 행 추가. 실행 템플릿은 기존 author 블록 재사용, 복제 금지 |
| `dot_claude/skills/quality-goal/SKILL.md` | 수정 | 보호 대상 `### Plan` **bytes 불변**, 그 바로 앞에 새 `### Plan author` 절 추가. frontmatter `version` 을 `6.1.0` 으로. 전체 500행 미만 유지. **접두 충돌 주의**: `### Plan` 은 `### Plan author` 의 문자열 접두다 |
| `dot_claude/skills/quality-goal/tests/assert_tests_preserved.py` | 수정 | `TEST_PATHS` 를 `test_execution_watchdog.py` 포함 다섯 파일 tuple 로 확장 |
| `dot_claude/skills/quality-goal/tests/assert_preserved_sections.py` | **불변·실행 대상** | CMD-10 이 실행한다. `PRESERVED_SECTIONS` 첫 항목 `### Plan` 이 T6 이 의존하는 계약이다. `_sections` 가 헤딩 줄 전체를 키로 쓰므로 새 절 삽입에도 `### Plan` 청크는 불변이다. 파일 자체는 수정하지 않는다 |
| `docs/quality-goal-maintenance.md` | 수정 | `QG_BASE` 를 `92f3873…` 로 갱신. 점검 라우트 열거에 `Plan author (standard)`·`Plan author (strict)` 추가(SPEC-07). 500행 미만 유지 |
| `dot_claude/skills/quality-goal/tests/test_content_contracts.py` | 수정 | Plan author/readiness 정책 내용 계약 테스트 추가. 이름에 `plan_author` 또는 `plan_readiness` 포함. 기존 25개 author/readiness 테스트 이름 보존 |
| `dot_claude/skills/quality-goal/tests/test_validate_review.py` | 수정 | `plan_readiness` 규약 테스트 추가: 두 artifact 정상, 발급 `READY-` 고정, 교차 오염 양방향 거부, CLI/result mismatch, 검증 순서, 단일 인자 회귀 |
| `dot_claude/skills/quality-goal/tests/test_quality_state.py` | 수정 | `plan_author`/`plan_readiness` 규약 state 테스트 추가: 독립 counter, 공식 round 비소비, 네 failure outcome, 레거시 lazy 생성, `PLAN_REVIEW` 재개 보존 |
| `dot_claude/skills/quality-goal/tests/fixtures/readiness-plan-ready.json` | 신규 | Plan artifact 의 정상 readiness 결과. 미러에도 같은 경로로 추가 |
| `dot_claude/skills/quality-goal/tests/fixtures/readiness-plan-cross-prefix.json` | 신규 | Plan 결과에 `SPEC-` 참조를 넣은 교차 오염 fixture. 미러에도 추가 |
| `dot_claude/skills/quality-goal/tests/fixtures/readiness-spec-cross-prefix.json` | 신규 | Spec 결과에 `PLAN-` 참조를 넣은 교차 오염 fixture. 미러에도 추가 |
| `dot_claude/skills/quality-goal/tests/fixtures/readiness-plan-checklist-fail.json` | 신규 | C1~C8 여덟 항목 고정과 verdict 규칙을 확인하는 checklist 실패 fixture(AC-20 둘째 절). 미러에도 추가 |
| `dot_local/share/ai-account-profiles/claude/profile2/skills/quality-goal/**` | 수정·추가 | 위 스킬 파일 변경 전체의 바이트 동일 미러. 신규 fixture 네 개도 같은 상대 경로로 추가 |
| `tests/test_orchestrator_profiles.py` | **불변·실행 대상** | CMD-11 이 실행한다. #111 이 들여오는 파일이며 이 작업에서 수정하지 않는다 |
| `dot_claude/skills/quality-goal/scripts/revision_check.py` | **불변** | CMD-4 가 byte 불변을 강제 |
| `dot_claude/skills/quality-goal/templates/plan.md` | **불변** | CMD-4 가 byte 불변을 강제 |
| `dot_claude/skills/quality-goal/templates/spec.md` | **불변** | CMD-4 가 byte 불변을 강제 |

## Task dependencies

T1(스키마) → T2(validator) → T3(quality_state) 는 실행 계층의 선형 의존이다. validator 는 확장된 enum 을 전제하고, `record-readiness` 는 validator 의 새 선택적 매개변수를 호출한다. T4(readiness-policy)와 T5(model-routing)는 문서 계층이며 서로 독립이지만 T6(SKILL.md)이 둘이 정의한 용어를 참조하므로 T6 보다 앞선다. T7(보존 helper)은 T6 이 옮긴 `QG_BASE` 값을 전제하므로 T6 직후다. T8 은 전체 재판정이다.

**모든 태스크는 자기 테스트를 자기 안에서 작성한다.** T1 은 스키마 테스트, T2 는 validator 테스트, T3 은 state 테스트, T4·T5·T6 은 내용 계약 테스트를 각각 그 태스크에서 먼저 실패시키고 구현으로 통과시킨다. 따라서 각 태스크의 통과 조건은 그 시점에 도달 가능하다. 전체 suite 의 `N > 479`(CMD-5)는 신규 테스트가 모두 존재하는 T8 에서만 판정하며 앞선 태스크의 통과 조건에 넣지 않는다.

## Tasks

각 태스크는 자기 테스트를 자기 안에서 작성한다. 실패하는 검증을 먼저 기록하고, 최소 구현을 붙인 뒤, 통과를 기록한다. 스킬 파일을 만들거나 고칠 때마다 profile2 미러에 같은 바이트를 적용하는 것이 완료 조건에 포함된다.

### T1. readiness 결과 스키마를 두 artifact로 확장한다

대상 AC: AC-13 (CMD-8)

실패 기록: `CMD-8` 을 지금 실행하면 `artifact` enum 이 `["spec"]` 이라 AssertionError 로 종료 코드 1 이 난다. 이 종료 코드를 기록한다.

구현: `schemas/readiness-result.schema.json` 의 `properties.artifact.enum` 을 `["spec","plan"]` 으로 바꾼다. `prior_findings[].id` 와 `resolved_finding_ids[]` 의 패턴을 `^(READY-|SPEC-|PLAN-)` 합집합으로 넓힌다. `findings[].id` 와 `blockers[]` 의 `^READY-` 는 그대로 둔다. `type: object`, `additionalProperties: false`, required 13필드, checklist `minItems`/`maxItems` 8, evidence `minItems` 6, `artifact_digest` 의 64자리 hex 패턴, verdict enum 을 보존한다. `if`/`then`/`oneOf`/`allOf`/`anyOf`/`const` 를 새로 넣지 않는다.

통과 기록: `CMD-8` 종료 코드 0 과 `OK` 출력.

미러: 이 파일을 profile2 미러에 동일 바이트로 반영한다.

### T2. validator에 artifact별 참조 접두 검증을 넣고 그 테스트를 쓴다

대상 AC: AC-14 (CMD-2), AC-15 (CMD-2), AC-16 (CMD-2), AC-18 (CMD-2), AC-32 (CMD-2 CMD-3)

실패 기록: 먼저 `tests/test_validate_review.py` 에 이름이 `plan_readiness` 를 포함하는 테스트를 작성한다. 범위는 두 artifact 정상 결과 통과, 발급 finding·blocker 에 `READY-` 외 접두를 주면 실패, Spec 결과의 `PLAN-` 참조 거부, Plan 결과의 `SPEC-` 참조 거부, Plan 결과의 `READY-|PLAN-` 참조 허용, resolved 집합 일치, checklist·verdict 규칙, schema/artifact 오류와 digest 오류가 함께 있을 때 `schema_invalid` 우선이고 schema·artifact 정상에 digest 만 다르면 `digest_mismatch` 인 검증 순서, 그리고 기존 `validate_readiness_result(payload)` **단일 인자 호출 회귀**다. fixture 는 `tests/fixtures/readiness-plan-ready.json`, `readiness-plan-cross-prefix.json`, `readiness-spec-cross-prefix.json` 를 새로 만든다. 이 시점에 `CMD-2` 를 실행하면 구현이 없어 테스트가 실패하므로 종료 코드가 0 이 아니다. 그 종료 코드를 기록한다.

구현: `scripts/validate_review.py` 의 `validate_readiness_result` 에 expected artifact 를 **기본값 있는 선택적 두 번째 매개변수**로 추가한다. 기존 단일 인자 호출이 그대로 동작해야 한다. 참조 접두 map 을 `{"spec": ("READY-","SPEC-"), "plan": ("READY-","PLAN-")}` 로 두고 `prior_findings[].id` 와 `resolved_finding_ids[]` 를 payload 의 `artifact` 값에 따라 검사해 교차 오염을 양방향으로 거부한다. 발급 자리는 artifact 와 무관하게 `^READY-` 만 허용한다. 오류 문구에 expected artifact 와 허용 접두를 드러낸다.

통과 기록: `CMD-2` 종료 코드 0, `Ran N tests` 의 N > 0, `OK`. AC-32 의 state 쪽 절반은 T3 에서 `CMD-3` 로 마저 증명한다.

미러: 수정한 `validate_review.py`, `test_validate_review.py` 와 신규 fixture 세 개를 profile2 미러에 같은 상대 경로로 반영한다.

### T3. record-readiness가 expected artifact를 전달하고 state 테스트를 쓴다

대상 AC: AC-5 (CMD-3), AC-8 (CMD-2), AC-10 (CMD-3), AC-12 (CMD-3), AC-17 (CMD-2), AC-22 (CMD-3), AC-23 (CMD-3), AC-24 (CMD-3), AC-25 (CMD-3), AC-29 (CMD-3)

실패 기록: 먼저 `tests/test_quality_state.py` 에 이름이 `plan_author` 또는 `plan_readiness` 를 포함하는 테스트를 작성한다. 범위는 Plan draft attempt 가 `draft_attempts.plan` 만 증가시키고 공식 round 를 바꾸지 않으며 새 state 키를 만들지 않음, readiness score 0/100 과 verdict 가 상태 전이·공식 round·공식 review 명령 수용을 바꾸지 않음, readiness 기록이 `readiness.plan` 만 갱신하고 공식 review 가 `reviews.plan`·`rounds.plan` 만 갱신함, 새 init state 의 키와 schema version 이 기준선과 같음, 두 필드가 없는 v1 레거시 fixture 가 load 시 변하지 않고 첫 Plan 기록 때 lazy 생성됨, Plan attempt 가 공식 round 를 넘어 단조 증가하고 `formal_round == rounds.plan + 1` 이며 Spec counter 와 공식 round 가 불변임, 기존 `PLAN_REVIEW` 상태를 save/select-resume/load 한 뒤 artifacts·digests·reviews·rounds·open findings·revision checks·readiness·draft attempts·`plan_approval` 이 보존됨, readiness 의 정상과 세 실패가 기존 네 outcome 만 만들고 실패 record 의 null/empty/실행 정보 shape 가 명세와 일치함, readiness 실패가 단계와 공식 round 를 바꾸지 않고 advisory 실패 뒤에도 공식 review 가 가능함이다. 이 시점에 `CMD-3` 을 실행하면 실패하므로 그 종료 코드를 기록한다.

구현: `scripts/quality_state.py` 의 `record-readiness` 경로에서 CLI `--artifact` 값을 `validate_readiness_result` 에 전달한다. payload 의 `artifact` 가 CLI 값과 다르면 `schema_invalid` outcome 으로 기록하고 유효 결과 필드를 채택하지 않는다. 등록 artifact 의 현재 digest 와 CLI `--artifact-digest` 가 다르면 기록 자체를 거부한다. 기존 outcome 네 값과 record shape 를 바꾸지 않고 새 state 키를 만들지 않는다.

통과 기록: `CMD-3` 종료 코드 0 과 N > 0 과 `OK`, `CMD-2` 종료 코드 0 과 N > 0 과 `OK`.

미러: 수정한 `quality_state.py`, `test_quality_state.py` 를 profile2 미러에 반영한다.

### T4. readiness-policy를 Spec/Plan 공용으로 확장하고 그 내용 계약을 쓴다

대상 AC: AC-2 (CMD-1), AC-4 (CMD-1), AC-7 (CMD-1), AC-9 (CMD-1), AC-11 (CMD-1), AC-19 (CMD-1), AC-20 (CMD-1 CMD-2), AC-21 (CMD-1 CMD-2), AC-27 (CMD-1), AC-28 (CMD-1), AC-30 (CMD-1)

실패 기록: 먼저 `tests/test_content_contracts.py` 에 이름이 `plan_author` 또는 `plan_readiness` 를 포함하는 정책 내용 계약 테스트를 작성한다. 범위는 Plan author 프롬프트 필수 요소, 쓰기 범위와 성공 조건, fresh/ephemeral 분리, Plan readiness 프롬프트 요소와 reference/issued ID 구분, evidence 첨부 두 경로와 인라인 금지, C1~C8 여덟 ID 보존과 Plan 사상 존재, Plan C1~C7 각각의 대상·관계·실패 조건, Plan C8 의 supplied target 정책, author 의 다섯 실패 형태, 범위 밖 쓰기와 dirty 보존, model unavailable 계약이다. AC-20 의 둘째 절을 위해 `tests/fixtures/readiness-plan-checklist-fail.json` 을 만들어 checklist 여덟 항목 고정과 verdict 규칙을 validator 쪽에서 확인한다. 이 시점에 `CMD-1` 을 실행하면 문언이 없어 실패하므로 그 종료 코드를 기록한다.

구현: `references/readiness-policy.md` 의 제목과 공통 설명을 Spec/Plan 공용으로 일반화하되 기존 `## Spec author`, digest 대조, readiness 지위, 실패 보고, 금지 Codex 옵션 절의 **문언을 보존**한다. `## Plan author` 절에 Plan 프롬프트 필수 요소(대상 Plan·통과한 Spec·`templates/plan.md`·`references/plan-rubric.md`·`references/planning-policy.md`·`references/revision-check-policy.md` 의 절대 경로, 적용할 findings 전문 경로, 발견 결과와 전역 제약, 허용 쓰기 경로, identifier grammar, 검증 명령 발견 의무, revision-note 형식, cross-regression 점검, material ambiguity 사전 해소)를 적는다. 쓰기 범위는 대상 `plan.md` 와 라운드 2 이상의 `plan-revision-notes.md` 뿐이며 오케스트레이터가 `initial_dirty_paths` 와 `.claude/quality-state/<task-id>/` 를 제외한 실제 변경 경로를 codex-result 의 `changed_files` 와 대조하고 결과 스키마·종료 코드·호출 전후 Plan SHA-256 변화를 확인한 뒤에만 성공으로 취급한다고 적는다. 실패 처리, 모델 unavailable 처리, Plan readiness 의 fresh 분리와 read-only 샌드박스, 프롬프트 구성, 근거 첨부 두 경로를 적는다. C1~C8 은 여덟 ID 를 유지하고 artifact 별 사상을 표로 나눈다. Plan 사상은 C1 `templates/plan.md` 필수 절 존재·순서, C2 strict marker 쌍 또는 standard 에서 양쪽 부재, C3 Spec AC 정의 수 == Plan 추적표 행 수, C4 각 추적행 Criterion 이 Spec AC 에 존재하고 Task 가 `### T<n>.` 에 존재, C5 각 추적행의 Verification command 와 Expected outcome 이 비어 있지 않음, C6 `T<n>` 번호 연속·고유, C7 각 추적행이 참조하는 `CMD-<n>` 이 `## Verification commands` 표에 정의됨, C8 supplied `READY-|PLAN-` target 별 정확히 한 번 판정이다.

**삽입 민감 단언 제약**: `test_content_contracts.py:377` 이 `policy.count("실행 가능한 정본은 \`references/model-routing.md\`") == 2` 를 단언한다. 그 문장은 현재 `readiness-policy.md:11` 과 `:83` 에 정확히 두 번 있다. 새 `## Plan author` 절은 **그 문장을 반복하지 않는다**. 템플릿 정본을 가리킬 때는 다른 표현(예: "author 호출 템플릿의 정본은 위 `## Spec author` 절이 가리키는 것과 같다")을 쓴다. 구현 직후 `grep -c` 가 아니라 Python `str.count` 로 2 임을 확인한다.

통과 기록: `CMD-1` 종료 코드 0 과 N > 0 과 `OK`, `CMD-2` 종료 코드 0(checklist fixture 포함).

미러: 수정한 `readiness-policy.md`, `test_content_contracts.py` 와 신규 fixture 를 profile2 미러에 반영한다.

### T5. model-routing에 Plan author 라우트를 추가하고 그 계약을 쓴다

대상 AC: AC-3 (CMD-1)

실패 기록: 먼저 라우트 표 내용 계약 테스트를 `test_content_contracts.py` 에 추가한다. 두 행의 존재와 정확한 모델·effort, 실행 템플릿이 복제되지 않았음을 확인한다. 이 시점에 `CMD-1` 은 실패하므로 그 종료 코드를 기록한다.

구현: `references/model-routing.md` 의 라우트 표에 `| Plan author (standard) | gpt-5.6-terra | high |` 와 `| Plan author (strict) | gpt-5.6-sol | high |` 두 행을 추가한다. 기존 여덟 행을 바꾸지 않는다. 실행 템플릿은 기존 `### author 호출 템플릿` 을 재사용하고 Plan 전용 템플릿을 복제하지 않는다. 템플릿이 Spec/Plan 공용임을 한 문장으로 밝힌다.

통과 기록: `CMD-1` 종료 코드 0 과 N > 0 과 `OK`.

미러: 수정한 두 파일을 profile2 미러에 반영한다.

### T6. SKILL.md에 Plan author 절을 넣고 문서를 동기화한다

대상 AC: AC-1 (CMD-1 CMD-10), AC-35 (CMD-9 CMD-10)

실패 기록: `CMD-9` 는 지금 frontmatter version 이 `6.0.0` 이라 종료 코드 1 이고, `CMD-10` 은 maintenance 의 `QG_BASE` 가 기준선과 달라 종료 코드 1 이다. 두 종료 코드를 기록한다. 새 절과 maintenance 라우트 열거를 확인하는 내용 계약 테스트도 이 태스크에서 먼저 작성해 실패를 기록한다.

구현: 보호 대상 `### Plan` 절의 bytes 를 한 글자도 바꾸지 않고 그 바로 앞에 새 `### Plan author` 절을 삽입한다. 새 절에는 standard·strict 에서 Codex Plan author 가 초안과 모든 개정을 쓰고 오케스트레이터가 Plan 본문을 직접 쓰지 않는다는 것, 각 author write 뒤 공식 reviewer 호출 전에 advisory readiness 를 돌린다는 것, readiness 근거를 공식 리뷰 컨텍스트에 첨부하되 advisory 는 전이를 결정하거나 공식 리뷰를 막지 않는다는 것, light 의 compact Plan 절차는 불변이라는 것을 적는다. frontmatter `version` 을 정확히 `6.1.0` 으로 올린다. 같은 태스크에서 `docs/quality-goal-maintenance.md` 의 `QG_BASE` 를 `92f387361775d6c6eebf9701d69e5653b5226806` 으로 갱신하고 점검 라우트 열거에 `Plan author (standard)` 와 `Plan author (strict)` 문자열을 추가한다(SPEC-07 해소).

**접두 충돌 제약**: `### Plan` 은 `### Plan author` 의 **문자열 접두**다. `test_content_contracts.py:946` 과 `:1037` 이 Plan 절을 `text.split("### Plan", 1)[1].split("### Approval", 1)[0]` 로 자르므로, 삽입 후 그 slice 는 **새 절에서 시작**한다. 따라서 새 `### Plan author` 절 본문에 다음 토큰을 **쓰지 않는다**: `set-artifact`, `revision_check.py`, `record-review --revision-check`, `exit code 0`, `references/revision-check-policy.md`, `revision-notes.md`, `--state`, `round-2-or-later`. 이 토큰들이 새 절에 없으면 `:946` 의 순서 단언(`section.index("set-artifact") < section.index("revision_check.py") < section.index("record-review --revision-check")`)은 원래 `### Plan` 절 기준으로 계산되어 그대로 성립하고, `:1037` 이 찾는 **첫 번째** `references/revision-check-policy.md` 등장 줄도 원래 절에 남는다. Plan author 절차의 상세 문언은 `references/readiness-policy.md` 가 정본이므로 새 절은 요약과 참조로 충분하다. `:974` 의 `text.split("### Spec",1)[1].split("### Plan",1)[0]` 은 새 절보다 앞 구간이라 영향이 없고, `:2153`·`:2186` 은 새 절이 `### Execution watchdog` 뒤에 오므로 순서 단언이 유지된다. `assert_preserved_sections.py` 는 헤딩 줄 전체를 키로 쓰므로 `### Plan` 청크는 불변이다. 1단계의 `### Execution watchdog` 전례는 그 헤딩이 다른 헤딩의 접두가 아니라서 이 위험을 겪지 않았다 — 전례는 배치 방식에만 적용되고 접두 문제에는 적용되지 않는다.

**줄 수 예산 제약(SPEC-06 해소)**: 현재 `SKILL.md` 는 489행이고 `CMD-9` 가 500행 미만을 요구하므로 새 절의 예산은 **최대 10행**이다. 보호 절 여덟 개는 byte 보존 대상이라 축약할 수 없고 비보호 `### Spec`·`### Execution watchdog` 문언은 기존 25개 내용 계약이 의존하므로 줄일 수 없다. 10행 안에 들어가지 않으면 절차 정본을 `references/readiness-policy.md` 에 두고 `SKILL.md` 에는 요약과 참조만 남긴다. 비교 기준으로 `### Spec` 의 Codex author 문단은 6행이다(SKILL.md:159-164). 구현 직후 `wc -l < dot_claude/skills/quality-goal/SKILL.md` 로 실제 행 수를 기록한다.

통과 기록: `CMD-9` 종료 코드 0, `CMD-10` 종료 코드 0, `CMD-1` 종료 코드 0.

미러: `SKILL.md` 를 profile2 미러에 동일 바이트로 반영한다. `docs/quality-goal-maintenance.md` 는 스킬 디렉터리 밖이라 미러 대상이 아니다.

### T7. 보존 helper 대상을 다섯 파일로 넓힌다

대상 AC: AC-31 (CMD-7 CMD-10)

실패 기록: `CMD-7` 은 지금 `TEST_PATHS` 가 네 파일이라 다섯 파일 tuple 단언에서 종료 코드 1 이다. 그 종료 코드를 기록한다.

구현: `tests/assert_tests_preserved.py` 의 `TEST_PATHS` 에 `dot_claude/skills/quality-goal/tests/test_execution_watchdog.py` 를 추가해 정확히 다섯 파일 tuple 로 만든다. 순서는 CMD-7 이 비교하는 tuple 과 동일해야 한다. `QG_BASE` 는 T6 에서 `92f3873…` 으로 옮겨져 있고 그 revision 에 다섯째 파일이 존재하므로 `git show` 의 `check=True` 가 실패하지 않는다. 이 helper 파일 자체는 `TEST_PATHS` 외에 바꾸지 않는다.

통과 기록: `CMD-7` 종료 코드 0 과 `기존 테스트 보존`, `CMD-10` 종료 코드 0.

미러: 수정한 `assert_tests_preserved.py` 를 profile2 미러에 반영한다.

### T8. 최종 트리에서 전 명령을 재실행해 판정한다

대상 AC: AC-6 (CMD-4 CMD-6), AC-26 (CMD-6), AC-33 (CMD-5 CMD-7), AC-34 (CMD-4)

실패 기록: T1~T7 이 끝나기 전에는 `CMD-5` 가 N > 479 를 만족하지 못해 종료 코드 1 이다. 그 종료 코드를 기록한다.

구현 아닌 최종 검증 태스크다. **CMD-1 부터 CMD-11 까지 전부를 최종 트리에서 다시 실행하고 각 종료 코드를 기록한다.** 앞선 태스크에서 한 번 통과한 명령도 이후 태스크가 그 전제를 바꿨을 수 있으므로 재실행한다. 특히 `CMD-10` 은 T6 에서 실행됐지만 T7 이 `assert_tests_preserved.py` 를 고쳤으므로 반드시 다시 돌린다. `CMD-9` 도 T8 이후 추가된 내용 계약 테스트를 포함해 다시 돌린다. 실행 순서는 CMD-1·CMD-2·CMD-3·CMD-8(타깃), CMD-4·CMD-6·CMD-7·CMD-9·CMD-10(보존·회귀), CMD-11(미러), CMD-5(전체)다.

AC-6 의 "revision check 성공 전 공식 리뷰 기록 거부" 절은 신규 동작이 아니라 기존 계약이며 `CMD-6` 의 `REQUIRED_CHECKS` 회귀 패턴이 그것을 증명한다. AC-34 의 byte 불변은 `CMD-4` 가 증명한다.

저장소 루트에 lint·type-check·build 구성이 없다(루트에 `package.json`, `pyproject.toml`, `setup.cfg`, `tox.ini`, `.eslintrc*`, `Makefile`, `.pre-commit-config.yaml` 이 모두 부재하며 `ls -1` 결과로 확인한다). 따라서 그 세 범주는 이 부재 목록을 근거 경로로 기록해 `not configured` 로 남기고 통과로 간주하지 않는다. E2E 는 `tests/deep-research.test.mjs` 와 `tests/tmux-open-pr.test.sh` 가 이 작업과 무관한 다른 기능의 것이므로 역시 `not configured` 로 기록한다.

통과 기록: CMD-1~CMD-11 전부 종료 코드 0, `CMD-5` 의 `Ran N tests` 에서 N > 479 와 `OK`.

## Verification commands

아래 표의 CMD-1~CMD-10 은 Spec `### 판정 명령 표` 를 문자 단위로 그대로 옮긴 것이며 CMD-11 만 추가한다. T8 에서 **전 명령을 최종 트리에서 다시 실행**하고 각 종료 코드를 기록한다. 실행 순서는 타깃(CMD-1·CMD-2·CMD-3·CMD-8), 보존·회귀(CMD-4·CMD-6·CMD-7·CMD-9·CMD-10), 미러(CMD-11), 전체(CMD-5)다. 모든 명령은 저장소 루트에서 실행한다.

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
| CMD-11 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s tests -p 'test_orchestrator_profiles.py' -k profile2_quality_bundle_mirror` | 종료 코드 0, `dot_claude/skills/quality-goal` 과 profile2 미러의 파일 집합·바이트 일치 및 심볼릭 링크 부재로 `OK` |

## Rollout and rollback

착수 선행 조건은 #111(PR #124)의 main 머지다. 그 PR 이 profile2 미러와 `test_profile2_quality_bundle_mirror` 를 함께 들여오므로 머지 전에 스킬을 고치면 미러 기준이 흔들린다. 또 #111 이 Codex 를 점유하는 동안 동시 실행하면 capacity 오류가 난다. 이 선행 조건은 조건부가 아니며, 미러가 없는 상태에서 착수하지 않으므로 CMD-11 을 건너뛰는 경로도 없다.

착수 시점 절차는 다음 순서다. 첫째, `git fetch` 후 현재 main 을 확인하고 이 worktree 를 rebase 한다. **rebase 판정 근거**: `92f3873..72ad4f2` 구간의 변경은 #103(PR #119)뿐이고 그 구간에서 `dot_claude/skills/quality-goal/` 과 `docs/quality-goal-maintenance.md` 는 무변경이므로 파일 충돌이 없다. `92f3873` 은 `72ad4f2` 의 조상이라 CMD-4 의 `git diff 92f3873` 과 CMD-7·CMD-10 의 `QG_BASE=92f3873` 은 rebase 후에도 유효하며 `test_execution_watchdog.py` 는 두 revision 모두에 존재한다. 따라서 rebase 는 파일 충돌 없이 가능하고 Spec 개정이 필요 없다. #111 머지로 main 이 더 앞서면 같은 기준으로 다시 판정하되, #111 이 건드리는 `dot_local/share/ai-account-profiles/claude/profile2/` 는 이 작업이 미러로서 함께 수정할 경로이므로 rebase 후 미러 상태를 먼저 확인한다. 둘째, `initial_dirty_paths` 를 재확인하고 사용자 미추적 작업을 보존한다. 셋째, T1 부터 순서대로 진행한다.

롤백 트리거와 조치는 다음과 같다. `CMD-5` 가 N ≤ 479 이거나 `OK` 가 아니면 해당 태스크 변경을 되돌리고 원인을 기록한다. `CMD-4` 가 실패하면 세 불변 파일 중 하나가 바뀐 것이므로 `git checkout 92f3873 -- <경로>` 로 되돌린다. `CMD-9` 가 500행 초과로 실패하면 T6 의 예산 제약에 따라 새 절을 요약으로 줄이고 정본을 `references/readiness-policy.md` 로 옮긴다. **`CMD-1` 이 `test_skill_revision_check_procedure_contract` 또는 `test_skill_names_identifier_grammar_for_authors` 에서 실패하면 T6 의 접두 충돌이 발생한 것이다** — 새 `### Plan author` 절에서 금지 토큰(`set-artifact`, `revision_check.py`, `record-review --revision-check`, `exit code 0`, `references/revision-check-policy.md`, `revision-notes.md`, `--state`, `round-2-or-later`)을 제거하고 그 내용을 `references/readiness-policy.md` 로 옮긴다. `CMD-1` 이 `readiness-policy.md` 의 count 단언에서 실패하면 T4 가 정본 문장을 반복한 것이므로 다른 표현으로 바꾼다. `CMD-11` 이 집합 불일치로 실패하면 누락된 미러 파일을 추가하거나 잉여 파일을 제거한다. 전체 롤백이 필요하면 이 worktree 는 전용 브랜치이므로 `git reset --hard` 로 되돌릴 수 있으나 사용자 미추적 파일은 `git clean` 을 쓰지 않고 그대로 둔다.

배포는 검증이 전부 통과한 뒤에만 한다. 검증 blocker 가 하나라도 남으면 머지와 `chezmoi apply` 를 하지 않는다. `chezmoi apply` 는 경로를 한정해 실행하고 다른 창이 사용 중인 스킬 버전과 충돌하지 않는 시점을 확인한 뒤 수행한다.

## Acceptance-criteria traceability

Spec 의 수용 기준 35개를 각각 하나의 구현 태스크와 판정 명령에 대응시킨다.

| Criterion | Task | Verification command | Expected outcome |
|---|---|---|---|
| AC-1 | T6 | CMD-1 CMD-10 | 새 `### Plan author` 절이 Codex 작성 주체·light 불변을 기술하고 `### Plan` bytes 가 보존되어 두 명령이 종료 코드 0 |
| AC-2 | T4 | CMD-1 | Plan author 프롬프트 필수 요소 계약이 `Ran N tests` 의 N > 0 으로 `OK` |
| AC-3 | T5 | CMD-1 | 라우트 표에 Plan author 두 행이 정확한 모델·effort 로 존재하고 템플릿 복제가 없어 `OK` |
| AC-4 | T4 | CMD-1 | 쓰기 범위·`changed_files` 대조·종료 코드·digest 변화 성공 조건 계약이 `OK` |
| AC-5 | T3 | CMD-3 | `draft_attempts.plan` 만 증가하고 공식 round 불변, 새 state 키 없음으로 `OK` |
| AC-6 | T8 | CMD-4 CMD-6 | CMD-4 가 세 파일 byte 불변과 revision suite 를 증명하고, revision check 성공 전 공식 리뷰 기록 거부는 기존 계약이라 CMD-6 의 `REQUIRED_CHECKS` 회귀가 증명하여 둘 다 종료 코드 0 |
| AC-7 | T4 | CMD-1 | author·readiness 의 fresh/ephemeral 분리와 readiness 라우트 계약이 `OK` |
| AC-8 | T3 | CMD-2 | 등록 경로·payload·CLI artifact·현재 digest 가 모두 일치한 결과만 `recorded` 로 기록되어 `OK` |
| AC-9 | T4 | CMD-1 | Plan readiness 프롬프트 요소와 reference/issued ID 구분 계약이 `OK` |
| AC-10 | T3 | CMD-3 | score 와 verdict 가 전이·round·review 수용을 바꾸지 않음이 확인되어 `OK` |
| AC-11 | T4 | CMD-1 | 공식 evidence 두 경로 첨부와 인라인·구속 금지 계약이 `OK` |
| AC-12 | T3 | CMD-3 | readiness 는 `readiness.plan` 만, 공식 review 는 `reviews.plan`·`rounds.plan` 만 갱신하여 `OK` |
| AC-13 | T1 | CMD-8 | `artifact` enum 이 정확히 `['spec','plan']` 이고 조건부 키 부재로 종료 코드 0 과 `OK` |
| AC-14 | T2 | CMD-2 | 발급 자리에 `READY-` 외 접두를 주면 검증 실패가 확인되어 `OK` |
| AC-15 | T2 | CMD-2 | Spec 의 `PLAN-` 참조와 Plan 의 `SPEC-` 참조가 양방향으로 거부되어 `OK` |
| AC-16 | T2 | CMD-2 | resolved 집합 일치·prior shape·C1~C8 한 번 규칙이 두 artifact 에서 동일하게 검증되어 `OK` |
| AC-17 | T3 | CMD-2 | CLI 와 payload artifact mismatch 가 `schema_invalid` 이고 유효 필드가 비어 `OK` |
| AC-18 | T2 | CMD-2 | schema/artifact 오류 우선, digest 단독 오류는 `digest_mismatch`, 등록 digest 불일치는 기록 거부로 `OK` |
| AC-19 | T4 | CMD-1 | C1~C8 여덟 ID 보존과 Plan 사상·공식 reviewer 경계 절 존재가 확인되어 `OK` |
| AC-20 | T4 | CMD-1 CMD-2 | CMD-1 이 Plan C1~C7 의 대상·관계·실패 조건 추출을 확인하고 CMD-2 가 `readiness-plan-checklist-fail.json` fixture 로 여덟 항목 고정과 verdict 규칙을 확인하여 둘 다 `OK` |
| AC-21 | T4 | CMD-1 CMD-2 | supplied target 정책은 CMD-1 content contract 로, payload 내부 규칙은 CMD-2 validator 로 분리 판정되어 둘 다 `OK` |
| AC-22 | T3 | CMD-3 | init state 키·schema version 이 기준선과 같고 v1 레거시가 load 시 불변, 첫 기록 때 lazy 생성되어 `OK` |
| AC-23 | T3 | CMD-3 | Plan attempt 단조 증가와 `formal_round == rounds.plan + 1`, Spec counter 불변으로 `OK` |
| AC-24 | T3 | CMD-3 | `PLAN_REVIEW` 재개 후 모든 값과 승인 path/digest 가 재개 전과 같아 `OK` |
| AC-25 | T3 | CMD-3 | 정상과 세 실패가 네 outcome 만 만들고 실패 record shape 가 명세와 일치하여 `OK` |
| AC-26 | T8 | CMD-6 | 여섯 보호 계약 패턴이 각각 N > 0 과 종료 코드 0 으로 `OK` |
| AC-27 | T4 | CMD-1 | author 의 다섯 실패 형태에서 단계·round 불변과 자동 revert 금지가 확인되어 `OK` |
| AC-28 | T4 | CMD-1 | 범위 밖 쓰기·`changed_files` 불일치·dirty 보존에서 사용자 보고 요구가 확인되어 `OK` |
| AC-29 | T3 | CMD-3 | readiness 실패 일곱 형태가 단계·공식 round 를 바꾸지 않고 근거를 남겨 `OK` |
| AC-30 | T4 | CMD-1 | model unavailable 의 무대체·대기·승인 기록·거부 시 전이 계약이 확인되어 `OK` |
| AC-31 | T7 | CMD-7 CMD-10 | 보존 helper 대상이 다섯 파일과 정확히 일치하고 `기존 테스트 보존` 출력과 갱신된 `QG_BASE` 로 두 helper 가 성공하여 `OK` |
| AC-32 | T2 | CMD-2 CMD-3 | 신규 validator 테스트가 R7.2 사례와 단일 인자 회귀를, 신규 state 테스트가 R7.3 사례를 포함해 둘 다 `OK` |
| AC-33 | T8 | CMD-5 CMD-7 | CMD-7 이 다섯 파일 이름 보존을 먼저 입증한 뒤 CMD-5 가 최종 트리에서 N > 479 와 `OK` |
| AC-34 | T8 | CMD-4 | 세 파일이 기준선과 byte 동일하고 revision suite 가 종료 코드 0 으로 `OK` |
| AC-35 | T6 | CMD-9 CMD-10 | 새 절·세 문서 일관 열거·`### Plan` bytes 보존·같은 `QG_BASE` 두 helper 성공·version `6.1.0`·500행 미만으로 두 명령이 종료 코드 0 |
