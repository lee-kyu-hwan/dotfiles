# Quality Goal Implementation Plan

- Task ID: 20260906T134503Z-70-1단계-축소-범위-quality-goal-spec-단계에-codex-4fa9c46e
- Mode: standard
- Status: PLAN_REVIEW
- Created: 2026-09-06T13:45:03Z
- Updated: 2026-09-07T02:40:00Z
- Source goal: #70 1단계(축소 범위) — quality-goal Spec 단계에 Codex author 와 참고용(advisory) readiness 심사를 추가하고 상태 전이 게이트는 #76 으로 이관

## Spec link

- 승인 대상 Spec: `docs/development/2026-09-06-70-quality-goal-codex-author-advisory-readiness/spec.md`
- SHA-256: `328c17bb5a540e620699a175ad0808d4a956503fd0ce8c2fae3bbb818b8efbb1`
- 공식 리뷰: 라운드 2, score 92, PASS, blocker 0, Critical/High 0 (`.claude/quality-state/<task-id>/spec-review-r2.json`)
- 요구사항 45건(R1.1~R9.8), 수용 기준 90건(AC-1~AC-90), 추적표 45행

이 Plan 은 그 Spec 의 AC-1~AC-90 전부를 태스크와 검증 명령에 매핑한다. readiness 게이트 논리(게이트 판정 함수, 유효 Critical/High 집합, 시도 한도 강제, `AWAITING_READINESS_DECISION` 과 전이 가드, `readiness-gate`·`resume-readiness` 서브커맨드, `readiness_decisions` 필드, 공식 리뷰 시작 조건의 코드 강제)는 Spec § Non-goals 12 가 이슈 #76 으로 이관했으므로 이 Plan 에 그 태스크가 없다. 직전 실행의 Plan(`docs/development/2026-09-05-70-quality-goal-codex-spec-readiness/plan.md`, 442행, 태스크 17)에서 그 다섯 태스크(`readiness-gate`, 새 stage 와 전이 가드, `resume-readiness`, `record-review` 게이트 강제, 네 명령의 light 거부 중 게이트 명령 몫)를 걷어내고 남은 것을 축소 Spec 에 맞춰 재구성했다.

## Global constraints

1. **chezmoi source 만 바꾼다.** 대상은 `dot_claude/skills/quality-goal/` 하위와 `docs/quality-goal-maintenance.md` 다. `chezmoi apply` 를 실행하지 않는다 — 다른 워크트리(#79)의 세션이 배포본 `~/.claude/skills/quality-goal/`(v5.0.0)을 실행 중이다. 배포는 사용자가 별도로 한다.
2. **초기 dirty 경로를 보존한다.** 상태의 `initial_dirty_paths` 는 `.prior-art/` 와 `docs/development/2026-09-05-70-quality-goal-codex-spec-readiness/` 둘이다. 두 경로 모두 구현 태스크가 읽기만 하고 수정·되돌리기·커밋 대상 포함을 하지 않는다. 이번 실행의 산출물 디렉터리 `docs/development/2026-09-06-70-quality-goal-codex-author-advisory-readiness/` 에 쓰는 주체는 구현 태스크가 아니라 오케스트레이터다. **예외가 둘 있다** — 구현 태스크는 § Tasks 의 변이 확인 절차를 위해 `.claude/quality-state/<task-id>/mutation/` 아래에, § Rollout and rollback 의 중단·보고 절차를 위해 `.claude/quality-state/<task-id>/incident/` 아래에만 파일을 쓸 수 있다. 두 경로 모두 `.gitignore:25` 로 무시되고 저장소 산출물이 아니며, 남아 있어도 무해하다. 그 밖의 상태 디렉터리 경로에는 구현 태스크가 쓰지 않는다. 두 디렉터리는 쓰기 직전에 `mkdir -p` 로 만든다.
3. **Python 3.12 이상에서 작업한다.** `python3` 가 무엇으로 풀리는지는 셸에 따라 다르다 — 로그인 셸에서는 `/usr/bin/python3` 3.9.6 이고, PATH 에 homebrew 가 앞선 셸에서는 `/opt/homebrew/bin/python3` 3.14.7 이다. 따라서 모든 판정 명령은 `python3` 를 직접 부르지 않고 § Verification commands 가 정의한 `QG_PY` 를 쓴다. `QG_PY` 는 3.12 이상 인터프리터를 탐색해 고르고, 찾지 못하면 명령이 실패한다(Spec R9.8 의 "명령 자체가 전제를 확인한다").
4. **기존 계약을 건드리지 않는다.** `SKILL.md` 의 `### Plan`, `### Approval`, `### Implementation`, `### Code review`, `## Independent verification`, `## Safety rules`, `## Review invocation contract`, `## Codex invocation contract` 여덟 절과 `ROUND_LIMITS`, `REQUIRED_CHECKS`, 공식 게이트 임계 85 는 변경 금지다(Spec R9.5). 특히 `## Review invocation contract` 를 고치지 않으므로 Spec R4.4 의 근거 첨부는 반드시 **파일 경로**여야 한다.
5. **`SKILL.md` 는 파일 전체가 500행 미만이어야 한다.** 현재 393행이므로 추가 여유는 106행이다. readiness 절차의 상세는 `references/readiness-policy.md` 로 뺀다(Spec R9.1).
6. **테스트 우선.** 모든 행동 변경은 실패하는 검증을 먼저 기록하고, 최소 구현 뒤 통과를 기록한다.
7. **기존 테스트를 지우거나 이름을 바꾸지 않는다.** base revision `6d60011cbdaead7946b191d3f12029eef5c141c8` 의 310개 테스트 이름 집합이 부분집합으로 보존돼야 한다(CMD-6). **본문 갱신은 이 제약의 예외가 아니라 애초에 대상이 아니다** — CMD-6 은 `def test_` 이름만 비교하므로, 이 작업이 바꾸는 값을 리터럴로 고정한 기존 단언은 이름을 그대로 두고 본문만 고친다. 그런 단언이 셋이며 어느 태스크가 고치는지는 § File map 과 T4·T12 에 적혀 있다.
8. **신설 식별자에는 거부 계약의 대칭을 먼저 확인한다.** 이 Plan 의 T4·T5·T6 은 새 상태 필드와 서브커맨드를 도입한다. 각 태스크는 구현 전에 `quality_state.py` 에서 같은 부류의 기존 가드를 `grep` 으로 찾아 그 형태를 따른다. 기존 선례는 `approve_plan` 의 stage 가드, `CLASSIFIED → AWAITING_PLAN_APPROVAL` 의 모드 조건, `record_review` 의 등록 digest 대조다.
9. **상태 머신을 바꾸지 않는다.** `ALLOWED_TRANSITIONS`, `TERMINAL_STATES`, `ROUND_LIMITS`, `REQUIRED_CHECKS` 는 이 작업에서 한 글자도 바뀌지 않는다(Spec R4.1·AC-34·AC-79). 새 stage 도, 새 전이 가드도, 기존 전이의 새 거부 조건도 만들지 않는다.
10. **커밋·푸시·머지·배포를 하지 않는다.** 이 Plan 의 어떤 태스크도 git 쓰기 명령을 포함하지 않는다. `git show` 와 `git status --porcelain` 은 읽기이므로 허용한다.
11. **Codex 호출 금지 플래그.** 구현 중 Codex 를 부른다면 `--skip-git-repo-check`, `--dangerously-bypass-approvals-and-sandbox`, `--dangerously-bypass-hook-trust`, `--approve-for-me`, `--ignore-rules`, `--ignore-user-config`, `--add-dir`, `--yolo` 를 쓰지 않는다(Spec R1.4).

## File map

| 파일 | 작업 | 책임 | 영향 인터페이스 |
|---|---|---|---|
| `dot_claude/skills/quality-goal/tests/assert_python_version.py` | 신설 | `is_supported(version_info)` 로 3.12 이상 여부를 판정하고 `__main__` 이 그 함수로 분기 | CMD-1·CMD-2·CMD-7 이 호출 |
| `dot_claude/skills/quality-goal/tests/assert_preserved_sections.py` | 신설 | `SKILL.md` 의 보존 대상 여덟 절을 base revision 과 비교 | CMD-4 |
| `dot_claude/skills/quality-goal/tests/assert_tests_preserved.py` | 신설 | base revision 의 테스트 이름 집합이 부분집합인지 확인 | CMD-6 |
| `dot_claude/skills/quality-goal/schemas/readiness-result.schema.json` | 신설 | readiness 결과 구조 계약. 필수 열세 필드와 네 접두 패턴 | `codex exec --output-schema`, `validate_readiness_result` |
| `dot_claude/skills/quality-goal/scripts/validate_review.py` | 수정 | `validate_readiness_result` 추가 — 스키마 검증, 네임스페이스 발급/참조 구분, `resolved_finding_ids` 집합 동치, verdict 일관성. 기존 `validate_review`·`REQUIRED_CHECKS` 는 불변 | `quality_state.record_readiness` 가 호출 |
| `dot_claude/skills/quality-goal/scripts/quality_state.py` | 수정 | 상태 필드 둘(`readiness`, `draft_attempts`), 서브커맨드 둘(`record-readiness`, `record-draft-attempt`). `ALLOWED_TRANSITIONS`·`TERMINAL_STATES`·`ROUND_LIMITS`·v5.0.0 의 `revision_checks`·`record_review` 시그니처·스냅숏 저장 분기는 불변 | CLI |
| `dot_claude/skills/quality-goal/references/readiness-policy.md` | 신설 | author·readiness 프롬프트 계약, 호출 템플릿, 체크리스트 C1~C8 정의, readiness 의 지위, digest 대조, 근거 첨부, finding 식별자, 금지 플래그 열거 | `SKILL.md` 가 참조 |
| `dot_claude/skills/quality-goal/references/model-routing.md` | 수정 | author·readiness 라우트 행과 두 파일의 역할 분담. 기존 라우트 행·구현 라운드 템플릿·프리플라이트 블록은 불변 | `readiness-policy.md` 가 인용 |
| `dot_claude/skills/quality-goal/templates/spec.md` | 수정 | `## Requirements traceability` 절과 `### 판정 명령 표` 절 추가 | C1·C3·C4·C5·C7 의 파싱 앵커 |
| `dot_claude/skills/quality-goal/SKILL.md` | 수정 | `### Spec` 절차, Stage table, 참조 경로 목록, frontmatter `version`. 보존 대상 여덟 절은 불변 | 오케스트레이터 지시 |
| `docs/quality-goal-maintenance.md` | 수정 | readiness 점검 항목 추가, `## 결정적 테스트` → `## 판정 명령 표` 대체(CMD-1~CMD-7 일곱 행 + 최소 인터프리터 근거) | 유지보수 runbook, 판정 명령 표의 정본 |
| `dot_claude/skills/quality-goal/tests/test_quality_state.py` | 수정 | 상태·기록 테스트 **추가** + 기존 단언 **갱신** — `test_new_state_has_the_complete_schema_version_one_shape` 의 기대 키 집합에 `readiness`·`draft_attempts` 를 더한다(T4) | CMD-1·CMD-2 |
| `dot_claude/skills/quality-goal/tests/test_validate_review.py` | 수정 | readiness 결과 검증 테스트 추가 | CMD-1·CMD-2 |
| `dot_claude/skills/quality-goal/tests/test_content_contracts.py` | 수정 | 문서 계약 테스트 **추가** + 기존 단언 **갱신** — `test_skill_version_is_major_bumped` 와 `test_frontmatter_contract` 의 `5.0.0` 리터럴을 새 버전으로 바꾼다(T12) | CMD-1·CMD-2 |
| `dot_claude/skills/quality-goal/references/spec-rubric.md`, `references/plan-rubric.md` | 읽기 전용 판정 대상 | 공식 게이트 임계 85 의 불변을 판정하는 대상. T14 의 변이 확인에서 `spec-rubric.md` 의 `85` 를 일시 변경했다가 해시로 복구한다. 이 작업의 최종 산출물에서는 두 파일이 바뀌지 않는다 | AC-81(CMD-2) |
| `dot_claude/skills/quality-goal/tests/fixtures/readiness-ready.json`, `readiness-failed-check.json`, `readiness-high-finding.json`, `readiness-schema-invalid.json` | 신설 | readiness 결과 픽스처 넷 — 전부 `pass` / C4 만 `fail` / High 1건 포함 / `checklist` 일곱 항목 | T2 가 만들고 T2·T3·T6 의 테스트가 쓴다 |
| `dot_claude/skills/quality-goal/tests/fixtures/state-v1-without-new-fields.json` | 신설 | `schema_version: 1` 이고 `readiness`·`draft_attempts` 두 키가 없는 상태 픽스처 | T4 가 만들고 T4·T5·T6 의 테스트가 쓴다 |
| `.claude/quality-state/<task-id>/mutation/*.orig`, `*.sha256` | 신설(일회성) | 변이 확인 절차의 원본과 해시. 저장소 산출물이 아니며 `.gitignore:25` 로 무시된다 | § Tasks 의 변이 확인을 수행하는 T4·T12·T13·T14 |
| `.claude/quality-state/<task-id>/incident/*` | 신설(조건부) | 롤백 트리거 5 가 걸렸을 때 남기는 `git status`·`git diff` 출력. 같은 이유로 저장소 산출물이 아니다 | § Rollout and rollback 의 중단·보고 절차 |

`.gitignore` 는 손대지 않는다 — `.claude/quality-state/` 는 이미 `.gitignore:25` 로 무시된다.

## 이 작업이 바꾸는 값을 고정한 기존 테스트

`PLAN-01` 은 "기존 테스트가 리터럴로 고정한 값을 이 작업이 바꾸는데 갱신 단계가 없다" 는 종류다. 지적된 셋만 고치지 않고 `.claude/quality-state/<task-id>/brittle_assertions.py` 로 `dot_claude/skills/quality-goal/tests/` 전체를 훑었다. 스캐너는 정확 단언(`assertEqual`·`assertCountEqual`·`assertSetEqual`·`assertListEqual`·`assertDictEqual`·`len(...)`)을 담고 **이 작업이 건드리는 산출물**(상태 키 집합, `SKILL.md`, 버전 리터럴, `ROUND_LIMITS`, `REQUIRED_CHECKS`, 전이·종료 상태, rubric, `templates/`, `references/`, `schemas/`, 서브커맨드, 유지보수 문서, 파일 개수·행수)을 언급하는 테스트 함수를 후보로 뽑는다. 현재 후보는 **55건**이다.

**후보 수는 스캔의 폭에 따라 달라지므로 그 자체가 결론이 아니다.** 결론은 그 후보를 "이 작업이 그 값을 실제로 바꾸는가" 로 하나씩 판정한 결과이며, **바꾸는 것은 셋뿐**이다. 나머지는 이 작업이 값을 바꾸지 않거나(불변 대상), 단언이 `assertIn`·`assertRegex` 처럼 가산에 안전한 형태다. 아래 표는 판정이 자명하지 않았던 것들을 대표로 싣고, 셋을 제외한 전부가 "갱신 없음" 인 이유를 유형별로 적는다.

특히 새 파일이 생겨 깨질 수 있는 두 부류를 따로 확인했다 — `references/`·`templates/` 를 `glob` 으로 훑는 테스트는 `test_reference_documents_contain_no_unfinished_markers` 하나뿐이고 개수가 아니라 각 파일의 미완성 마커 부재를 보며, `SKILL.md` 의 참조 경로 목록을 보는 `test_skill_lists_revision_check_supporting_paths` 와 `test_supporting_links_and_skill_dir_contract` 는 둘 다 `assertIn` 이라 경로 추가에 안전하다. `schemas/`·`tests/` 디렉터리의 파일 개수를 세는 테스트는 없다.

| 테스트 | 고정하는 값 | 이 작업의 변경 여부 | 처리 |
|---|---|---|---|
| `test_quality_state.py:223` `test_new_state_has_the_complete_schema_version_one_shape` | `new_state()` 최상위 키 집합(base 25개)을 `assertEqual` 로 정확히 단언 | **바꾼다** — T4 가 `readiness`·`draft_attempts` 둘을 더한다 | **T4 가 기대 집합을 27개로 갱신.** 새로 만드는 `test_new_state_has_exactly_two_new_fields`(AC-49)와 **같은 리터럴**을 쓴다 |
| `test_content_contracts.py:607` `test_skill_version_is_major_bumped` | `assertEqual("5.0.0", frontmatter["version"])` | **바꾼다** — T12 가 5.1.0 으로 올린다 | **T12 가 `"5.1.0"` 으로 갱신** |
| `test_content_contracts.py:1067` `test_frontmatter_contract` | `expected["version"] = "5.0.0"` | **바꾼다** — 위와 같다 | **T12 가 `"5.1.0"` 으로 갱신** |
| `test_content_contracts.py:236` `test_rubric_pass_gate_keys_match_required_checks_exactly` | rubric 통과 게이트 키 ↔ `REQUIRED_CHECKS` | 바꾸지 않는다(AC-79) | 갱신 없음 |
| `test_content_contracts.py:621` `test_round_limits_required_checks_threshold_unchanged` | `ROUND_LIMITS`·`REQUIRED_CHECKS`·임계 85 | 바꾸지 않는다(AC-79·AC-81) | 갱신 없음 |
| `test_content_contracts.py:1240` `test_skill_size_and_state_names_contract` | `SKILL.md` 500행 미만 + stage 이름 13개 존재 | 행 수는 는다(393 → 500 미만 유지, AC-71). stage 이름은 늘지도 줄지도 않는다(AC-34) | 갱신 없음. **T12 는 이 상한을 넘지 않는 선에서만 쓴다** |
| `test_quality_state.py:142` `test_transition_terminal_and_round_constants_match_the_contract` | `ALLOWED_TRANSITIONS`·`TERMINAL_STATES`·`ROUND_LIMITS` | 바꾸지 않는다(AC-34·AC-79) | 갱신 없음 |
| `test_quality_state.py` 의 전이·종료 상태 테스트 일곱(`:446`, `:511`, `:764`, `:774`, `:788`, `:1479`, `:1871`)과 `:1423` 의 라운드 한도 테스트 | 전이 엣지·종료 상태·라운드 한도 | 바꾸지 않는다(AC-34·AC-79) | 갱신 없음 |
| `test_revision_check.py:147` `test_output_matches_schema` | `revision_check` **출력** 스키마의 키 집합 | 바꾸지 않는다 — 이 작업은 `revision_check.py` 를 건드리지 않는다(§ Global constraints 4) | 갱신 없음 |
| `test_content_contracts.py:644`, `test_revision_check.py:409`·`:524` | 픽스처 문자열 안의 `quality-goal-maintenance` 등 | 바꾸지 않는다 — 픽스처는 문서 실물이 아니다 | 갱신 없음 |

**기대값의 출처를 하나로 묶는다.** 갱신 대상 셋은 모두 그 값을 판정하는 AC 와 **같은 출처**를 쓴다 — 키 집합은 "base 25키 + `readiness` + `draft_attempts`"(AC-49 와 동일한 리터럴), 버전은 T12 가 frontmatter 에 실제로 쓰는 문자열(AC-82 가 관계로 판정하는 그 값)이다. 한쪽만 고쳐 두 자리가 다른 값을 단언하는 상태를 만들지 않는다.

**세 테스트 모두 이름을 바꾸지 않으므로 CMD-6 이 유지된다.** 본문 갱신은 § Global constraints 7 의 예외가 아니라 애초에 그 제약의 대상이 아니다 — CMD-6 은 `def test_` 이름 집합만 비교한다.

**두 가지 추가 제약을 여기서 함께 못박는다.**

- `test_content_contracts.py:405` `test_reference_documents_contain_no_unfinished_markers` 가 `references/*.md` 와 `templates/*.md` 전부에서 미완성 마커(TBD·TODO)를 금지한다. 신설 `references/readiness-policy.md`(T7·T8·T9)와 `templates/spec.md` 의 새 두 절(T11)에 그 토큰을 쓰지 않는다.
- `test_content_contracts.py:382-401` 은 `references/model-routing.md` 에서 금지 플래그 문자열이 나타나는 **줄마다** 금지 표현(`금지|않는다|never|forbid|prohibited`)이 같은 줄에 있을 것과 그 줄이 실행 가능한 `codex ` 명령이 아닐 것을 요구한다. AC-5 의 규칙(문단 단위)보다 엄격하므로, T10 이 그 파일에 라우트 행을 더할 때 플래그 문자열을 새로 싣지 않는다. 새 문서 `references/readiness-policy.md` 는 AC-5 의 문단 규칙을 따르되 이 줄 단위 규칙도 함께 만족하게 쓴다 — 두 규칙이 충돌하지 않도록 플래그 열거를 한 줄에 하나씩, 그 줄에 금지 표현을 함께 둔다.

## Task dependencies

```text
T1 (판정 스크립트 3종)
 └─ CMD-1·CMD-2·CMD-4·CMD-6·CMD-7 의 실행 기반. 가장 먼저.

T2 (readiness 결과 스키마)
 └─ T3 (validate_readiness_result)
      └─ T6 (record-readiness)

T4 (상태 필드 2종 + v1 호환 + 불변 확인)
 ├─ T5 (record-draft-attempt)
 └─ T6 (record-readiness)

T7·T8·T9 (readiness-policy.md 세 절)  ← T2~T6 의 계약이 확정된 뒤
T10 (model-routing.md) ─ 독립. T7·T8 이 그 템플릿을 인용
T11 (spec 템플릿) ─ 독립
T12 (SKILL.md) ─ T7·T8·T9 완료 후 (참조 경로가 존재해야 한다)
T13 (유지보수 문서) ─ T1·T7·T8·T9·T10 완료 후
T14 (회귀 확인) ─ 전부 완료 후
```

수행 순서는 **T1 → T2 → T3 → T4 → T5 → T6 → T10 → T7 → T8 → T9 → T11 → T12 → T13 → T14** 다. 태스크 번호와 수행 순서가 한 곳에서만 갈린다 — T10 을 T7 앞에 둔다. T7·T8 의 호출 템플릿 문언이 `references/model-routing.md` 의 라우트 값을 인용하므로 그 행이 먼저 있어야 인용이 실물을 가리킨다.

선행 간선의 근거는 다음과 같다.

- **T3 → T6.** T6 이 소유한 AC-58·AC-70 의 기대 결과가 "스키마 위반 결과가 `schema_invalid` 로 기록된다" 이므로, 검증 함수 없이는 T6 완료 시점에 통과 확인을 실행할 수 없다.
- **T2 → T3.** 검증 함수가 읽는 스키마 파일이 먼저 있어야 한다.
- **T4 → T5, T4 → T6.** 두 서브커맨드가 쓰는 필드의 생성 규칙(없으면 만들고 로드만으로는 만들지 않는다)이 T4 에서 확정된다.
- **T5 → T6.** AC-59(두 명령 모두 `light` 에서 거부)의 통과 확인은 두 명령이 다 있어야 실행된다. 그래서 뒤에 오는 T6 이 그 AC 를 소유한다.
- **T1 → T13.** AC-86 은 유지보수 문서의 CMD-1·CMD-2 정의가 `tests/assert_python_version.py` 를 호출하는지 보므로 그 파일이 먼저 있어야 한다.
- **T7·T8·T9 → T12.** AC-72 는 `SKILL.md` 의 참조 경로 목록에 `references/readiness-policy.md` 가 등재됐는지 보고, 그 파일이 존재해야 등재가 실물을 가리킨다.
- **T7·T8·T9·T10 → T13.** AC-5 의 검사 대상에 `dot_claude/skills/quality-goal/` 하위 모든 `.md` 와 `docs/quality-goal-maintenance.md` 가 들어가므로, 금지 플래그 문자열을 새로 싣는 문서가 전부 쓰인 뒤라야 통과 확인이 최종 상태에서 성립한다. 그래서 AC-5 를 마지막으로 플래그 문자열을 싣는 T13 이 소유한다.
- **전부 → T14.** AC-77(CMD-1 전체 스위트), AC-78(CMD-6), AC-80(CMD-4)은 최종 상태를 판정한다.

## Tasks

**검증 수단의 세 종류.** ① 77개는 새 테스트 이름으로 판정한다 — 소유 태스크가 그 테스트를 **작성**하고(실패 확인 단계) 통과시킨다(통과 확인 단계). ② 여섯 개(AC-64·71·77·78·80·85)는 새 테스트를 만들지 않고 § Verification commands 의 명령(CMD-5·3·1·6·4·7)을 그대로 돌려 판정한다. ③ 일곱 개(AC-28·31·35·39·44·62·76)는 Spec 이 `[문서]` 로 표기한 것이라 해당 문서의 해당 절을 `grep` 하는 명령으로 판정하며, 그 명령이 소유 태스크의 통과 확인에 그대로 적혀 있다. 세 종류를 합치면 77 + 6 + 7 = 90 으로 Spec 의 AC 총수와 같다.

**AC 소유권 원칙.** 각 AC 는 **그 AC 의 통과 확인을 그 태스크가 끝난 시점에 실제로 실행할 수 있는** 가장 이른 태스크가 소유한다. 두 명령의 상호작용을 보는 AC 는 뒤에 오는 명령의 태스크가 갖는다 — 두 서브커맨드의 `light` 거부를 함께 보는 AC-59 는 T6, `rounds` 불변과 `record-review` 독립성을 보는 AC-32·AC-33 은 readiness 기록을 만드는 T6 이다. 여러 문서에 걸친 문언을 보는 AC 는 마지막으로 그 문언을 쓰는 태스크가 갖는다 — AC-5 는 T13, AC-72 는 T12 다. 이 원칙 덕분에 태스크를 § Task dependencies 의 수행 순서대로 하나씩 완료하면 그 시점에 소유 AC 의 통과 확인이 실제로 실행 가능하다. **AC 소유권은 이 원칙으로만 정하고 편의로 옮기지 않는다.**

**불변 고정 테스트의 red 단계.** 이 Plan 의 테스트 중 일부는 *새 행동* 이 아니라 *바뀌지 않아야 하는 것* 을 고정한다 — T4 의 `test_transitions_and_terminal_states_unchanged`·`test_round_limits_and_required_checks_unchanged`·`test_resume_preserves_rounds_reviews_and_approval`·`test_v1_state_without_new_fields_is_not_mutated_on_load`, T12 의 `CMD-3`, T14 의 `test_formal_pass_gate_threshold_unchanged`·`CMD-1`·`CMD-4`·`CMD-6` 이다. 이들은 구현 전에도 통과하므로 통상의 red 단계가 성립하지 않는다. 대신 **변이 확인** 으로 red 를 만든다. 절차는 넷이며 순서를 지킨다.

0. **디렉터리 준비** — `mkdir -p .claude/quality-state/<task-id>/mutation` 를 먼저 실행한다. 깨끗한 실행에서는 이 디렉터리가 없으므로 이 단계 없이는 1번의 복사가 실패한다.
1. **원본 고정** — 변이할 파일의 현재 내용을 `.claude/quality-state/<task-id>/mutation/<파일명>.orig` 로 복사하고 `shasum -a 256 <파일>` 값을 같은 디렉터리의 `<파일명>.sha256` 에 적는다.
2. **변이** — 판정 대상을 한 곳 고친다(예: `ROUND_LIMITS['plan']` 을 3 으로, `ALLOWED_TRANSITIONS` 에 가짜 엣지 추가, 보존 대상 절의 한 줄 삭제, `SKILL.md` 끝에 빈 줄 200개 추가, `load_state` 가 두 필드를 주입하도록 한 줄 추가).
3. **실패 확인** — 그 테스트나 명령이 **실제로 실패하는지** 본다. 실패하지 않으면 그 테스트는 공허하므로 판정 자체를 고친다.
4. **복구 확인** — 1번에서 복사해 둔 `.orig` 로 파일을 되돌리고 `shasum -a 256 <파일>` 이 `<파일명>.sha256` 과 **같은지** 확인한 뒤 테스트를 다시 통과시킨다. `git diff` 로는 확인할 수 없다 — 커밋하지 않고 순차로 구현하므로 앞선 태스크의 정상 변경이 이미 워킹 트리에 쌓여 있어 `git diff` 가 비어 있을 수 없기 때문이다. **해시가 다르면 즉시 멈추고 `.orig` 파일 경로와 함께 사용자에게 보고한다.** 복구를 다시 시도하거나 다음 태스크로 넘어가지 않는다.

이 절차는 파일 복사와 해시 비교만 쓰고 git 쓰기 명령을 쓰지 않는다(§ Global constraints 10). `.claude/quality-state/<task-id>/mutation/` 은 저장소가 무시하는 경로다. 이 절차를 거치지 않은 불변 테스트는 공허하게 통과할 수 있다. 각 태스크의 실패 확인 줄이 어느 쪽인지 밝힌다.

각 태스크는 test-first 다 — 실패하는 검증을 먼저 기록하고, 최소 구현 뒤 통과를 기록한다. 태스크 본문의 `CMD-1`~`CMD-7` 은 § Verification commands 표의 명령을 그대로 가리키며, 그 표가 정의한 `QG_PY`·`QG_BASE` 를 먼저 셸에 설정한 뒤 쓴다. 이 Plan 의 어떤 명령도 `python3` 를 직접 부르지 않는다(§ Global constraints 3).

### T1. 판정 스크립트 세 개를 만든다

대상 AC: AC-85, AC-87, AC-90

- **실패 확인**: 순서를 지킨다. `CMD-2` 는 `assert_python_version.py` 를 먼저 실행하는 `&&` 사슬이므로(§ Verification commands), 그 파일이 없으면 `unittest` 가 아예 기동하지 않아 테스트 본문이 한 번도 실행되지 않는다. 그 상태의 실패는 대상 행동의 실패가 아니라 전제 실패이므로 red 로 치지 않는다(같은 기준을 T4 의 AC-51 에도 적용한다).
  1. **가드 스텁 먼저** — `assert_python_version.py` 를 `is_supported(version_info)` 가 인자와 무관하게 `True` 를 반환하는 최소 형태로 만든다. 이 스텁이 있으면 `CMD-2` 의 사슬이 통과해 `unittest` 가 기동한다. 나머지 두 스크립트는 아직 만들지 않는다.
  2. **테스트 작성과 red 확인** — `test_judgement_scripts_exist_and_are_not_collected`(AC-87)와 `test_python_version_guard_boundary_and_main_delegates`(AC-90)를 작성하고 각각을 `CMD-2 -k <이름>` 으로 돌린다. AC-87 은 세 스크립트 중 둘이 없어서, AC-90 은 스텁의 `is_supported((3, 11, 9))` 가 `True` 를 돌려주고 `__main__` 위임도 없어서 **각자의 사유로 본문이 실행된 뒤** 실패한다. 두 실패 메시지가 전제 실패가 아니라 단언 실패인지 확인한다.
  3. `CMD-7`(AC-85)은 스텁 상태에서 셋째 절(`! "$OLD_PY" … assert_python_version.py`)이 성공하지 못해 실패한다 — 스텁이 3.9.6 에서도 0 을 반환하기 때문이며, 이것도 단언 성격의 실패다.
- **구현**:
  - `assert_python_version.py` — 스텁을 실제 판정으로 바꾼다. `is_supported(version_info)` 가 `tuple(version_info[:2]) >= (3, 12)` 를 반환하고, `if __name__ == "__main__":` 분기가 `raise SystemExit(0 if is_supported(sys.version_info) else 1)` 로만 판정한다. 버전 비교식은 이 함수 안에만 둔다(Spec R9.8).
  - `assert_preserved_sections.py` — base revision 을 첫 인자로 받아 `git show <인자>:dot_claude/skills/quality-goal/SKILL.md` 를 읽고 현재 파일과 함께 `^#{2,3} ` 헤딩으로 쪼갠 뒤, 모듈 상수로 둔 여덟 절 이름(`### Plan`, `### Approval`, `### Implementation`, `### Code review`, `## Independent verification`, `## Safety rules`, `## Review invocation contract`, `## Codex invocation contract`)의 본문이 바이트 단위로 같은지 단언하고 `보존 대상 절 불변` 을 출력한다.
  - `assert_tests_preserved.py` — base revision 을 첫 인자로 받아 그 리비전의 `tests/test_content_contracts.py`, `test_quality_state.py`, `test_validate_review.py`, `test_revision_check.py` 에서 `^\s*def (test_\w+)` 이름을 모아 현재 집합의 부분집합인지 단언하고 `기존 테스트 보존` 을 출력한다.
  - 세 파일명이 `test_` 로 시작하지 않으므로 `unittest discover -p 'test_*.py'` 가 이 **스크립트들** 을 수집하지 않는다. 확인 방법은 테스트 총수가 아니다 — 이 태스크가 `test_quality_state.py` 등에 새 테스트 둘(AC-87·AC-90)을 더하므로 `CMD-1` 의 실행 수는 310 에서 312 로 **늘어난다**. 수집 제외는 `test_judgement_scripts_exist_and_are_not_collected`(AC-87)가 `unittest` 의 discover 결과에 세 스크립트의 모듈 이름이 없음을 직접 단언해 판정한다.
- **통과 확인**: 소유 테스트를 `CMD-2 -k <이름>` 으로 하나씩 돌려 전부 통과시킨다 — `test_judgement_scripts_exist_and_are_not_collected`(AC-87), `test_python_version_guard_boundary_and_main_delegates`(AC-90). 명령으로 판정하는 AC — `CMD-7`(AC-85). 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.

### T2. readiness 결과 스키마를 만든다

대상 AC: AC-21, AC-37, AC-63, AC-64, AC-65, AC-67, AC-69

- **실패 확인**: `CMD-5` 가 `FileNotFoundError` 로 실패한다. 이 태스크가 소유한 테스트를 먼저 작성한다 — `test_readiness_schema_uses_type_not_const`(AC-21), `test_readiness_schema_attempt_has_no_maximum`(AC-37), `test_readiness_schema_required_fields`(AC-63), `test_readiness_schema_digest_pattern_and_verdict_enum`(AC-65), `test_readiness_schema_evidence_min_items`(AC-67), `test_readiness_schema_resolved_ids_and_namespace_patterns`(AC-69). 작성 직후 각각을 `CMD-2 -k <이름>` 으로 돌리면 전부 실패한다. 명령으로 판정하는 AC 는 구현 전에 `CMD-5`(AC-64) 가 실패하거나 조건을 만족하지 못한다.
- **구현**:
  - `schemas/readiness-result.schema.json` 을 만든다. 최상위 `type: object`, `additionalProperties: false`.
  - `required` 는 열셋 — `artifact`, `attempt`, `formal_round`, `score`, `verdict`, `checklist`, `blockers`, `findings`, `prior_findings`, `evidence`, `required_next_action`, `artifact_digest`, `resolved_finding_ids`.
  - 모든 property 가 `type` 키를 갖고 `const` 를 한 번도 쓰지 않는다. 고정값은 `artifact: {"type": "string", "enum": ["spec"]}` 형태로 쓴다(Spec R2.4).
  - `attempt`: `{"type": "integer", "minimum": 1}`. `maximum` 을 두지 않는다(Spec R4.2).
  - `score`: `{"type": "integer", "minimum": 0, "maximum": 100}`. `verdict`: `{"type": "string", "enum": ["READY", "REVISE"]}`. `artifact_digest`: `{"type": "string", "pattern": "^[0-9a-f]{64}$"}`.
  - `findings[].id` 와 `blockers[]` 에 `"pattern": "^READY-"`, `prior_findings[].id` 와 `resolved_finding_ids[]` 에 `"pattern": "^(READY-|SPEC-)"` 를 둔다(Spec R7.1·R8.4의 네 패턴).
  - `prior_findings`: 배열이며 빈 배열 허용. 각 항목이 `id`·`source`·`judgement`·`evidence` 를 required 로 요구하고 `source` enum 은 `readiness`·`formal`, `judgement` enum 은 `resolved`·`unresolved`·`partial` 다.
  - `evidence`: `minItems: 6`, 각 항목이 `claim`·`location`·`verified` 를 required 로 요구하고 `additionalProperties: false` 다.
  - `checklist`: `minItems: 8`, `maxItems: 8`, 각 항목이 `id`·`status`·`evidence` 를 요구하고 `id` enum 은 `C1`~`C8`, `status` enum 은 `pass`·`fail`·`not_applicable` 다. **여덟 항목이 서로 다른 C1~C8 인지(중복·누락 없음)는 JSON Schema 로 표현할 수 없다** — `uniqueItems` 는 객체 전체를 비교해 같은 `id` 에 다른 `evidence` 를 둔 항목을 통과시키기 때문이다. 그 완전성 검사는 T3 의 검증 함수가 맡고 AC-68 도 T3 이 소유한다.
  - 집합 동치(`resolved_finding_ids` = `judgement == resolved` 인 항목의 ID 집합)는 JSON Schema 로 표현할 수 없으므로 스키마에 넣지 않고 T3 의 검증 함수가 집행한다.
  - 픽스처 다섯 중 결과 픽스처 넷을 `tests/fixtures/` 에 함께 만든다 — `readiness-ready.json`(여덟 항목 전부 `pass`, Critical/High 0, `verdict: READY`), `readiness-failed-check.json`(C4 만 `fail`), `readiness-high-finding.json`(체크리스트는 전부 `pass` 지만 `findings` 에 High 1건), `readiness-schema-invalid.json`(`checklist` 가 일곱 항목). 넷 다 이 태스크의 테스트와 T3·T6 의 테스트가 함께 쓴다.
- **통과 확인**: 소유 테스트를 `CMD-2 -k <이름>` 으로 하나씩 돌려 전부 통과시킨다 — `test_readiness_schema_uses_type_not_const`(AC-21), `test_readiness_schema_attempt_has_no_maximum`(AC-37), `test_readiness_schema_required_fields`(AC-63), `test_readiness_schema_digest_pattern_and_verdict_enum`(AC-65), `test_readiness_schema_evidence_min_items`(AC-67), `test_readiness_schema_resolved_ids_and_namespace_patterns`(AC-69). 명령으로 판정하는 AC — `CMD-5`(AC-64). 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.

### T3. `validate_review.py` 에 readiness 결과 검증을 더한다

대상 AC: AC-26, AC-27, AC-60, AC-61, AC-68, AC-88

- **실패 확인**: 이 태스크가 소유한 테스트를 먼저 작성한다 — `test_readiness_verdict_requires_all_checks_and_no_high`(AC-26), `test_readiness_verdict_blocks_on_failed_check_or_high_finding`(AC-27), `test_issued_finding_ids_require_ready_prefix`(AC-60), `test_spec_prefix_is_reference_only_not_issuable`(AC-61), `test_readiness_schema_checklist_shape`(AC-68), `test_prior_findings_shape_and_resolved_set_equality`(AC-88). 작성 직후 각각을 `CMD-2 -k <이름>` 으로 돌리면 전부 실패한다.
- **구현**:
  - `validate_review.py` 에 `validate_readiness_result(result)` 를 더한다. 기존 `validate_review`·`REQUIRED_CHECKS`·`gate` 는 한 줄도 바꾸지 않는다.
  - 순서는 ① `schemas/readiness-result.schema.json` 구조 검증 ② **체크리스트 완전성** ③ 네임스페이스 검증 — `findings[].id` 와 `blockers[]` 는 `^READY-` 만, `prior_findings[].id` 와 `resolved_finding_ids[]` 는 `^(READY-|SPEC-)` 를 허용 ④ 집합 동치 — `set(resolved_finding_ids)` 가 `{p["id"] for p in prior_findings if p["judgement"] == "resolved"}` 와 같아야 한다 ⑤ verdict 일관성 — `checklist` 여덟 항목이 전부 `pass`/`not_applicable` 이고 `findings` 에 `Critical`·`High` 가 하나도 없을 때에만 `verdict == "READY"` 가 허용된다.
  - **② 체크리스트 완전성**은 `{item["id"] for item in checklist}` 가 `{"C1", …, "C8"}` 와 정확히 같은지 본다. 여덟 항목이면서 `id` 가 중복된 입력을 여기서 거른다 — 스키마의 `minItems`/`maxItems`/`id` enum 만으로는 걸러지지 않는다(`uniqueItems` 는 객체 전체를 비교하므로 같은 `id` 에 다른 `evidence` 를 둔 항목을 통과시킨다).
- **①이 ②보다 먼저여야 한다.** ②는 `item["id"]` 를 직접 역참조하므로, `checklist` 항목이 객체가 아니거나 `id` 키가 없는 입력에서 ②를 먼저 돌리면 오류 목록을 만들기 전에 `TypeError`·`KeyError` 로 죽는다. ①이 통과한 입력만 ②에 들어가므로 그 역참조가 안전하다. 구현은 ①이 오류를 하나라도 내면 즉시 그 목록을 반환하고 ②~⑤를 실행하지 않는다.
- 다섯 검사 중 하나라도 실패하면 오류 목록을 반환한다. `record-readiness` 는 그 실패를 `outcome: schema_invalid` 로 기록한다(T6).
  - 함수는 `score` 값을 읽지 않는다 — `score` 는 스키마의 범위 제약 밖에서는 어떤 분기에도 쓰이지 않는다(Spec R3.2).
- **통과 확인**: 소유 테스트를 `CMD-2 -k <이름>` 으로 하나씩 돌려 전부 통과시킨다 — `test_readiness_verdict_requires_all_checks_and_no_high`(AC-26), `test_readiness_verdict_blocks_on_failed_check_or_high_finding`(AC-27), `test_issued_finding_ids_require_ready_prefix`(AC-60), `test_spec_prefix_is_reference_only_not_issuable`(AC-61), `test_readiness_schema_checklist_shape`(AC-68), `test_prior_findings_shape_and_resolved_set_equality`(AC-88). 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.

### T4. 상태에 두 필드를 더하고 v1 호환과 기존 불변을 지킨다

대상 AC: AC-34, AC-49, AC-51, AC-52, AC-79

- **실패 확인**: 이 태스크가 소유한 테스트를 먼저 작성한다. `test_new_state_has_exactly_two_new_fields`(AC-49)는 `new_state()` 에 두 키가 아직 없으므로 작성 직후 `CMD-2 -k <이름>` 에서 실제로 실패한다. 나머지 넷은 불변 고정 테스트라 § Tasks 서두의 **변이 확인** 으로 red 를 만든다 — `test_transitions_and_terminal_states_unchanged`(AC-34)는 `ALLOWED_TRANSITIONS` 에 가짜 엣지를 넣어, `test_v1_state_without_new_fields_is_not_mutated_on_load`(AC-51)은 `load_state` 가 두 필드를 주입하도록 한 줄을 넣어, `test_resume_preserves_rounds_reviews_and_approval`(AC-52)은 재개 경로가 `plan_approval` 을 지우도록 한 줄을 넣어, `test_round_limits_and_required_checks_unchanged`(AC-79)는 `ROUND_LIMITS['plan']` 을 3 으로 바꾸어 각각 실패를 확인하고 절차 4 로 복구한다. AC-51 이 이 부류인 이유는 base revision 이 이미 v1 로드 계약을 만족하기 때문이다 — 픽스처가 없어서 실패하는 것은 red 가 아니므로, 픽스처를 먼저 만든 뒤 변이로 red 를 만든다.
- **구현**:
  - `new_state()` 에 `"readiness": {"spec": [], "plan": []}` 과 `"draft_attempts": {"spec": 0, "plan": 0}` 두 키를 더한다. 그 밖의 최상위 키는 늘리지 않는다.
  - `load_state()` 는 두 필드가 없어도 읽되 **주입하지 않는다**. 부재는 readiness 미실행·author 미호출을 뜻한다(Spec R6.3).
  - `ALLOWED_TRANSITIONS`, `TERMINAL_STATES`, `ROUND_LIMITS`, `REQUIRED_CHECKS` 를 건드리지 않는다. 이 태스크의 테스트 두 개가 그 불변을 고정한다.
  - 재개(`select-resume`)와 전이 경로가 `rounds`·`reviews`·`open_finding_ids`·`plan_approval`·`revision_checks` 를 초기화하지 않는 현행 동작을 테스트로 고정한다.
- **기존 단언을 갱신한다** — `tests/test_quality_state.py` 의 `test_new_state_has_the_complete_schema_version_one_shape` 는 `new_state()` 의 최상위 키 집합을 `assertEqual` 로 **정확히** 단언한다(base 에서 25개). 이 태스크가 두 키를 더하므로 그 기대 집합에 `readiness` 와 `draft_attempts` 를 넣어 27개로 만든다. 테스트 이름은 바꾸지 않는다(§ Global constraints 7). 이 갱신 없이는 이 태스크의 통과 확인 마지막 줄인 `CMD-1` 이 반드시 실패한다. 새로 만드는 `test_new_state_has_exactly_two_new_fields`(AC-49)와 판정 대상이 같으므로 **두 테스트가 같은 기대 집합 리터럴을 쓰게 한다** — 한쪽만 고쳐 서로 다른 집합을 단언하는 상태를 만들지 않는다.
- **두 불변 테스트의 기준값은 테스트 안 리터럴로 고정한다.** `test_transitions_and_terminal_states_unchanged`(AC-34)의 기대 엣지·종료 상태 집합과 `test_new_state_has_exactly_two_new_fields`(AC-49)의 기대 키 집합을 소스에 그대로 적고, `git show` 로 base revision 을 읽지 않는다. 그래야 `CMD-1` 이 git 과 base revision 의 존재에 의존하지 않는다. base 를 `git show` 로 읽는 것은 CMD-4·CMD-6 의 두 스크립트뿐이고 그 둘은 `unittest` 수집 대상이 아니다.
- 다섯째 픽스처를 만든다 — `tests/fixtures/state-v1-without-new-fields.json`. `schema_version: 1` 이고 `readiness`·`draft_attempts` 두 키가 없는 상태 파일이며, AC-51 과 T5 의 AC-14·T6 의 AC-50 이 함께 쓴다.
- **통과 확인**: 소유 테스트를 `CMD-2 -k <이름>` 으로 하나씩 돌려 전부 통과시킨다 — `test_transitions_and_terminal_states_unchanged`(AC-34), `test_new_state_has_exactly_two_new_fields`(AC-49), `test_v1_state_without_new_fields_is_not_mutated_on_load`(AC-51), `test_resume_preserves_rounds_reviews_and_approval`(AC-52), `test_round_limits_and_required_checks_unchanged`(AC-79). 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.

### T5. `record-draft-attempt` 를 만든다

대상 AC: AC-12, AC-13, AC-14

- **실패 확인**: 이 태스크가 소유한 테스트를 먼저 작성한다 — `test_record_draft_attempt_increments_only_draft_attempts`(AC-12), `test_record_draft_attempt_is_per_artifact`(AC-13), `test_draft_attempts_created_on_first_record`(AC-14). 작성 직후 각각을 `CMD-2 -k <이름>` 으로 돌리면 전부 실패한다.
- **구현**:
  - `record-draft-attempt --state --artifact` 를 더한다. `draft_attempts` 가 없으면 그때 만들고 해당 artifact 값을 1 증가시킨다.
  - `rounds` 의 어떤 값도 바꾸지 않고, 다른 artifact 의 값도 바꾸지 않는다.
  - `light` 모드 거부는 T6 에서 두 명령에 함께 건다 — 이 태스크는 그 가드를 넣되 판정은 두 명령이 다 있는 T6 이 한다.
- **통과 확인**: 소유 테스트를 `CMD-2 -k <이름>` 으로 하나씩 돌려 전부 통과시킨다 — `test_record_draft_attempt_increments_only_draft_attempts`(AC-12), `test_record_draft_attempt_is_per_artifact`(AC-13), `test_draft_attempts_created_on_first_record`(AC-14). 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.

### T6. `record-readiness` 를 만든다

대상 AC: AC-30, AC-32, AC-33, AC-36, AC-38, AC-42, AC-43, AC-45, AC-46, AC-47, AC-48, AC-50, AC-53, AC-54, AC-55, AC-56, AC-57, AC-58, AC-59, AC-70

- **실패 확인**: 이 태스크가 소유한 테스트를 먼저 작성한다 — `test_readiness_recording_ignores_score`(AC-30), `test_record_readiness_does_not_touch_rounds`(AC-32), `test_review_recording_is_independent_of_readiness`(AC-33), `test_readiness_attempt_is_globally_monotonic`(AC-36), `test_record_readiness_has_no_attempt_limit`(AC-38), `test_record_readiness_rejects_registered_digest_mismatch`(AC-42), `test_record_readiness_records_digest_mismatch`(AC-43), `test_readiness_record_shape`(AC-45), `test_readiness_formal_round_advances_after_review`(AC-46), `test_record_readiness_rejects_mismatched_formal_round`(AC-47), `test_record_readiness_persists_review_time_digest`(AC-48), `test_readiness_field_created_on_first_record`(AC-50), `test_readiness_records_survive_stage_exit`(AC-53), `test_readiness_record_outcome_enum`(AC-54), `test_failed_readiness_attempt_record_shape`(AC-55), `test_invocation_status_enum_is_enforced`(AC-56), `test_invocation_failure_is_recorded_and_requires_stderr_path`(AC-57), `test_schema_invalid_precedes_digest_mismatch`(AC-58), `test_readiness_commands_rejected_in_light_mode`(AC-59), `test_invalid_readiness_result_is_recorded_as_schema_invalid`(AC-70). 작성 직후 각각을 `CMD-2 -k <이름>` 으로 돌리면 전부 실패한다.
- **구현**:
  - `record-readiness --state --artifact --result --artifact-digest --formal-round --reviewer-model --invocation-status --stderr-path` 를 더한다. `outcome` 은 인자로 받지 않는다.
  - **사전 거부**: `--artifact-digest` 가 `artifacts[artifact]` 의 현재 파일 digest 와 다르면 거부. `--formal-round` 가 `rounds[artifact] + 1` 과 다르면 거부. `--invocation-status` 가 `ok`·`failed` 가 아니면 거부. `failed` 인데 `--stderr-path` 가 없거나 그 경로가 존재하지 않으면 거부. `mode` 가 `light` 면 이 명령과 `record-draft-attempt` 둘 다 거부.
  - **`outcome` 결정 순서**: `--invocation-status failed` → `invocation_failed`(결과 파일 유무 무관, `result_path` 에 `--stderr-path` 값). `ok` 이면 T3 의 `validate_readiness_result` → 실패 시 `schema_invalid`, 통과하면 결과의 `artifact_digest` 와 심사 시점 digest 를 대조해 다르면 `digest_mismatch`, 같으면 `recorded`.
  - **기록 형태**: `recorded` 는 R6.1 의 열두 필드를 정확히 갖는다(`attempt`, `formal_round`, `outcome`, `verdict`, `score`, `checklist`, `findings`, `resolved_finding_ids`, `artifact_digest`, `reviewer_model`, `result_path`, `recorded_at`). 결과 JSON 의 `prior_findings` 는 상태에 복사하지 않는다. 실패 기록은 `verdict`·`score` 가 `null`, `checklist`·`findings`·`resolved_finding_ids` 가 빈 배열, 나머지 일곱 필드가 채워진다.
  - `attempt` 는 실행 전체 누적이며 `formal_round` 가 바뀌어도 초기화되지 않는다. 시도 수를 이유로 한 거부는 없다.
  - `rounds` 를 바꾸지 않고, `record-review`·`record-review-unverified`·`record-review-error` 의 동작에 어떤 조건도 추가하지 않는다.
- **통과 확인**: 소유 테스트를 `CMD-2 -k <이름>` 으로 하나씩 돌려 전부 통과시킨다 — `test_readiness_recording_ignores_score`(AC-30), `test_record_readiness_does_not_touch_rounds`(AC-32), `test_review_recording_is_independent_of_readiness`(AC-33), `test_readiness_attempt_is_globally_monotonic`(AC-36), `test_record_readiness_has_no_attempt_limit`(AC-38), `test_record_readiness_rejects_registered_digest_mismatch`(AC-42), `test_record_readiness_records_digest_mismatch`(AC-43), `test_readiness_record_shape`(AC-45), `test_readiness_formal_round_advances_after_review`(AC-46), `test_record_readiness_rejects_mismatched_formal_round`(AC-47), `test_record_readiness_persists_review_time_digest`(AC-48), `test_readiness_field_created_on_first_record`(AC-50), `test_readiness_records_survive_stage_exit`(AC-53), `test_readiness_record_outcome_enum`(AC-54), `test_failed_readiness_attempt_record_shape`(AC-55), `test_invocation_status_enum_is_enforced`(AC-56), `test_invocation_failure_is_recorded_and_requires_stderr_path`(AC-57), `test_schema_invalid_precedes_digest_mismatch`(AC-58), `test_readiness_commands_rejected_in_light_mode`(AC-59), `test_invalid_readiness_result_is_recorded_as_schema_invalid`(AC-70). 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.

### T7. `references/readiness-policy.md` 의 author 절을 쓴다

대상 AC: AC-2, AC-3, AC-4, AC-6, AC-7, AC-8, AC-9, AC-10, AC-11, AC-15, AC-16, AC-84

- **실패 확인**: 이 태스크가 소유한 테스트를 먼저 작성한다 — `test_author_prompt_required_elements_contract`(AC-2), `test_author_prompt_required_elements_contract`(AC-3), `test_author_invocation_template_contract`(AC-4), `test_forbidden_codex_flags_enumerate_current_cli`(AC-6), `test_codex_exec_has_no_approval_flag_contract`(AC-7), `test_author_prompt_required_elements_contract`(AC-8), `test_author_revision_note_format_contract`(AC-9), `test_author_cross_regression_review_contract`(AC-10), `test_author_write_scope_contract`(AC-11), `test_author_failure_recovery_contract`(AC-15), `test_author_no_change_is_failure_contract`(AC-16), `test_routing_and_policy_split_is_documented`(AC-84). 작성 직후 각각을 `CMD-2 -k <이름>` 으로 돌리면 전부 실패한다.
- **구현**:
  - `references/readiness-policy.md` 를 만들고 author 절을 쓴다.
  - **호출 템플릿** — `codex exec` 의 아홉 요소(`-C`, `--sandbox workspace-write`, `--ephemeral`, `--model`, `-c model_reasoning_effort`, `--output-schema`, `--output-last-message`, `--json`, 프롬프트 파일 stdin)를 담은 펜스 블록. 모델·effort 값은 `references/model-routing.md` 의 라우트 행을 인용한다(T10 이 먼저 끝나 있어야 한다).
  - **프롬프트 필수 요소 열둘**을 목록으로 싣고, 앞의 다섯을 절대 경로로 한정한다. 요구사항 발굴 결과의 반영과 발굴에서 남은 물질적 모호성의 사전 사용자 질의도 같은 목록에 담는다.
  - **개정 노트 형식**을 `references/revision-check-policy.md` 에서 그대로 인용하고, 한 공식 라운드에 절이 정확히 하나이며 행을 누적·갱신한다는 규칙과 그 절의 범위가 직전 스냅숏 이후의 모든 변경이라는 규정을 함께 싣는다.
  - **조합 검토 지시**와 그 근거로 교차 회귀 전례(`PLAN-009`·`PLAN-010`·`PLAN-012`·`SPEC-31`·`SPEC-34`)를 인용한다.
  - **쓰기 범위** — 대상 Spec 과 개정 노트 둘로 한정하고, 호출 후 `git status --porcelain` 확인에서 `initial_dirty_paths` 와 `.claude/quality-state/<task-id>/` 하위를 제외하며 결과의 `changed_files` 와 대조한다고 적는다.
  - **실패 경로** — 비정상 종료·결과 파일 없음·스키마 검증 실패·호출 전후 digest 동일 넷을 개정 실패로 규정하고, 단계를 유지한 채 보고하며 모델을 대체하지 않고 `BLOCKED_MODEL_UNAVAILABLE` 복구 경로를 따른다고 적는다.
  - **역할 분담**(AC-84) — 이 파일 서두에 `references/model-routing.md` 와 이 파일의 역할 분담을 적는다. T10 이 같은 문단을 `model-routing.md` 쪽에 이미 넣었으므로, 이 태스크가 끝나는 시점에 두 파일이 모두 존재하며 그 관계를 서술한다. AC-84 를 T10 이 아니라 여기서 소유하는 이유는 T10 종료 시점에는 `references/readiness-policy.md` 가 아직 없어 그 판정이 성립하지 않기 때문이다(소유권 원칙).
- **금지 플래그** — 여덟 이름을 CLI 버전 `codex-cli 0.153.4` 와 함께 열거하고, `--yolo` 가 `codex exec --help` 에 없는 숨은 별칭이라는 사실, `--sandbox` 의 확대 지정 금지, `codex exec` 에 `-a`/`--ask-for-approval` 이 존재하지 않는다는 사실을 함께 적는다. 이 문단들은 모두 금지 토큰을 포함하고, 플래그 문자열을 펜스 코드 블록 안에 넣지 않는다.
- **통과 확인**: 소유 테스트를 `CMD-2 -k <이름>` 으로 하나씩 돌려 전부 통과시킨다 — `test_author_prompt_required_elements_contract`(AC-2), `test_author_prompt_required_elements_contract`(AC-3), `test_author_invocation_template_contract`(AC-4), `test_forbidden_codex_flags_enumerate_current_cli`(AC-6), `test_codex_exec_has_no_approval_flag_contract`(AC-7), `test_author_prompt_required_elements_contract`(AC-8), `test_author_revision_note_format_contract`(AC-9), `test_author_cross_regression_review_contract`(AC-10), `test_author_write_scope_contract`(AC-11), `test_author_failure_recovery_contract`(AC-15), `test_author_no_change_is_failure_contract`(AC-16), `test_routing_and_policy_split_is_documented`(AC-84). 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.

### T8. `references/readiness-policy.md` 의 readiness reviewer 절을 쓴다

대상 AC: AC-17, AC-18, AC-19, AC-20, AC-22, AC-23, AC-24, AC-62, AC-66, AC-89

- **실패 확인**: 이 태스크가 소유한 테스트를 먼저 작성한다 — `test_readiness_reviewer_is_fresh_contract`(AC-17), `test_readiness_invocation_template_contract`(AC-18), `test_readiness_read_only_contract`(AC-19), `test_readiness_stdin_guard_contract`(AC-20), `test_readiness_prompt_treats_notes_as_claims`(AC-22), `test_readiness_is_advisory_not_authority_contract`(AC-23), `test_readiness_prompt_carries_prior_findings`(AC-24), `test_readiness_score_computation_instruction`(AC-66), `test_readiness_unverified_evidence_reason_contract`(AC-89). 작성 직후 각각을 `CMD-2 -k <이름>` 으로 돌리면 전부 실패한다. AC-62 — `grep -n -e 'description' -e '같은 물질적 문제' dot_claude/skills/quality-goal/references/readiness-policy.md` 가 아직 아무것도 잡지 못한다.
- **구현**:
  - 같은 파일에 readiness reviewer 절을 쓴다.
  - **호출 템플릿** — `--sandbox read-only` 를 쓰고 금지 플래그를 포함하지 않는 펜스 블록. 모델·effort 는 `references/model-routing.md` 를 인용한다.
  - **stdin 계약** — author·readiness 두 템플릿이 모두 프롬프트 파일을 표준 입력으로 주고, 명령행 인자 변형을 쓸 때만 `< /dev/null` 을 붙이며, 둘 중 어느 형태도 아닌 호출은 금지한다는 것과 그 이유(비대화형 무한 대기)를 적는다.
  - **fresh 계약** — author 와 별개 프로세스이며 author 의 대화 문맥·세션·개정 노트의 주장을 근거로 상속하지 않는다.
  - **읽기 전용** — 파일 수정과 git 쓰기 명령 금지.
  - **프롬프트 필수 명시 넷** — ① 개정 노트는 근거가 아니라 검증 대상이며 파일:행으로 대조한다 ② 이 판정은 참고용이며 Claude 공식 판정을 대체하지도 그 시작을 막지도 않는다 ③ 설계 취향 감점 금지 ④ 직전 readiness 시도 결과 경로와 직전 공식 리뷰 open findings 경로 둘, 각 finding 의 ID·severity·`required_resolution` 가시성, 그 ID 가 참조이고 reviewer 자신의 finding 은 `READY-` 로 발급한다는 구분, 그리고 그 전달이 fresh 계약의 문맥 상속 금지와 구분된다는 설명.
  - **score 계산 지시** — rubric 가중치로 실제 계산하고 "blocker 가 있다고 0 을 넣지 마라" 를 적는다.
  - **evidence 규칙** — `verified` 가 `true` 인 근거의 `location` 은 `<경로>:<행>` 형식, `false` 인 근거의 `location` 에는 확인하지 못한 사유를 적는다.
  - **finding 식별자** — 공식 finding 과의 대응 관계를 `description` 에 기록하고, 하나의 개정 주기 안에서 같은 물질적 문제에 같은 ID 를 유지한다.
- **통과 확인**: 소유 테스트를 `CMD-2 -k <이름>` 으로 하나씩 돌려 전부 통과시킨다 — `test_readiness_reviewer_is_fresh_contract`(AC-17), `test_readiness_invocation_template_contract`(AC-18), `test_readiness_read_only_contract`(AC-19), `test_readiness_stdin_guard_contract`(AC-20), `test_readiness_prompt_treats_notes_as_claims`(AC-22), `test_readiness_is_advisory_not_authority_contract`(AC-23), `test_readiness_prompt_carries_prior_findings`(AC-24), `test_readiness_score_computation_instruction`(AC-66), `test_readiness_unverified_evidence_reason_contract`(AC-89). AC-62 — `grep -n -e 'description' -e '같은 물질적 문제' dot_claude/skills/quality-goal/references/readiness-policy.md` 를 돌려 두 문언이 § finding 식별자 절 안에서 잡힌다. 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.

### T9. `references/readiness-policy.md` 의 체크리스트·지위·digest·근거 첨부 절을 쓴다

대상 AC: AC-25, AC-28, AC-29, AC-31, AC-35, AC-39, AC-40, AC-41, AC-44

- **실패 확인**: 이 태스크가 소유한 테스트를 먼저 작성한다 — `test_readiness_checklist_defines_eight_items`(AC-25), `test_readiness_score_is_advisory_contract`(AC-29), `test_readiness_evidence_attachment_contract`(AC-40), `test_readiness_path_and_digest_precede_invocation`(AC-41). 작성 직후 각각을 `CMD-2 -k <이름>` 으로 돌리면 전부 실패한다. AC-28 — `grep -n -e '프롬프트에 실린' -e '정확히 하나' -e 'partial' -e '빈 배열' -e '원 접두' dot_claude/skills/quality-goal/references/readiness-policy.md` 가 아직 아무것도 잡지 못한다. AC-31 — `grep -n -e '설계 정합성' -e '아키텍처 타당성' -e '시간축' dot_claude/skills/quality-goal/references/readiness-policy.md` 가 아직 아무것도 잡지 못한다. AC-35 — `grep -n -e '어떤 상태 전이도 결정하지 않는다' -e '공식 리뷰의 시작 조건이 아니다' dot_claude/skills/quality-goal/references/readiness-policy.md` 가 아직 아무것도 잡지 못한다. AC-39 — `grep -n -e 'READY' -e '한도를 코드로 강제하지 않는다' -e '비용 상한' dot_claude/skills/quality-goal/references/readiness-policy.md` 가 아직 아무것도 잡지 못한다. AC-44 — `sed -n '/^## digest 대조$/,/^## /p' dot_claude/skills/quality-goal/references/readiness-policy.md | grep -c -e '단계를 바꾸지 않고' -e '사용자에게 보고한다'` 가 아직 0 이다(파일이 없거나 절이 없다).
- **구현**:
  - 같은 파일에 체크리스트·지위·digest·근거 첨부 절을 쓴다.
  - **체크리스트** — C1~C8 여덟 항목을 각각 정의한다. C2 의 strict marker 주석 문자열 두 개는 `templates/spec.md` 에서 그대로 인용한다. C8 은 다섯을 담는다 — 판정 대상을 프롬프트에 실린 findings 전문으로 한정하고 상태 기록을 훑지 않는다, 대상 하나마다 `prior_findings` 항목을 정확히 하나 남긴다, `judgement` 가 `partial` 이면 미충족이다, 프롬프트에 findings 가 없으면 `prior_findings` 가 빈 배열이고 자동 충족이다, 참조 자리의 ID 는 원 접두를 유지한다. 항목 정의에 설계 정합성·아키텍처 타당성·시간축 전개 판정을 넣지 않는다는 것도 같은 절에 적는다.
  - **readiness 의 지위** — `score` 는 기록 전용 참고값이며 판정·기록 거부·전이에 쓰지 않는다. readiness 는 어떤 상태 전이도 결정하지 않고 공식 리뷰의 시작 조건이 아니다. 결과가 `READY` 이면 그 라운드의 추가 시도를 하지 않되 라운드당 시도 한도는 코드로 강제하지 않고 비용 상한은 오케스트레이터가 사용자 지시에 따라 정한다.
  - **digest 대조** — 등록 digest 의 정의(`artifacts[artifact]` 가 가리키는 파일의 현재 SHA-256)와 `artifact_digests` 를 쓰지 않는다는 것, 경로 불일치 시 호출 자체를 하지 않는다는 확인을 호출 전 절차로 배치하는 것, 심사 시점 digest 를 프롬프트에 싣는 것, 그리고 위반이 단계를 바꾸지 않고 사용자 보고로 이어진다는 것을 적는다.
  - **실패 보고** — readiness 쪽 실패 넷의 사용자 보고를 한 문단에 모은다: 결과 스키마 검증 실패(Spec R8.5 — 검증 오류를 사용자에게 보고), 결과 digest 불일치와 심사 대상 경로 불일치(Spec R5.3), `codex exec` 비정상 종료·결과 파일 미생성·타임아웃(그 셋을 모두 `--invocation-status failed` 로 넘긴다), 그리고 모델 거부·부재. 앞의 셋은 `SPEC_REVIEW` 단계를 유지한 채 보고하고 끝난다. 모델 거부·부재는 **두 국면으로 나뉜다** — 사용자에게 대체 모델을 묻는 동안에는 현재 단계를 유지하고, 사용자가 대체를 거부하거나 응답할 수 없을 때에만 `BLOCKED`(`status_reason: BLOCKED_MODEL_UNAVAILABLE`)로 전이한다. 이는 기존 `references/model-routing.md` 의 복구 경로 그대로이며 이 작업이 새로 만들지 않는다. 넷 다 모델을 임의로 대체하지 않는다. **이 문단은 AC-44 의 판정 대상이 아니다.** AC-44 는 Spec 이 `[문서] references/readiness-policy.md § digest 대조` 한 절만 지정했으므로 그 절에서만 판정한다. 두 절의 문언이 `grep` 에서 겹치지 않도록 **표현을 나눈다** — § digest 대조 절은 "단계를 바꾸지 않고 사용자에게 보고한다" 를 쓰고, 이 § 실패 보고 문단은 "`SPEC_REVIEW` 를 유지한 채 알린다" 를 쓴다. 같은 문자열을 두 절에 쓰지 않는다. 이 문단이 다루는 나머지 셋(스키마 검증 실패, 호출 실패, 모델 거부)은 Spec 이 AC 를 두지 않은 오케스트레이터 절차라 문서에 남기되 별도 판정 수단을 만들지 않는다.
- **근거 첨부** — 공식 리뷰 컨텍스트에 저장소 근거 경로 둘(마지막 readiness 결과 JSON, `.claude/quality-state/<task-id>/readiness-evidence-spec-r<N>.md`)을 첨부하고 내용을 프롬프트에 인라인하지 않는다는 것, 그 이유(`SKILL.md` § Review invocation contract 의 입력 한정이 보존 대상이라는 것), 첨부가 리뷰어 판정을 구속하지 않는다는 것, 유효한 결과가 없을 때 그 사실을 요약 파일에 적는다는 것을 적는다.
- **통과 확인**: 소유 테스트를 `CMD-2 -k <이름>` 으로 하나씩 돌려 전부 통과시킨다 — `test_readiness_checklist_defines_eight_items`(AC-25), `test_readiness_score_is_advisory_contract`(AC-29), `test_readiness_evidence_attachment_contract`(AC-40), `test_readiness_path_and_digest_precede_invocation`(AC-41). AC-28 — `grep -n -e '프롬프트에 실린' -e '정확히 하나' -e 'partial' -e '빈 배열' -e '원 접두' dot_claude/skills/quality-goal/references/readiness-policy.md` 를 돌려 다섯 문언이 § 체크리스트 절 안에서 모두 잡힌다. AC-31 — `grep -n -e '설계 정합성' -e '아키텍처 타당성' -e '시간축' dot_claude/skills/quality-goal/references/readiness-policy.md` 를 돌려 세 문언이 § 체크리스트 절 안에서 잡히고 모두 '넣지 않는다' 문맥이다. AC-35 — `grep -n -e '어떤 상태 전이도 결정하지 않는다' -e '공식 리뷰의 시작 조건이 아니다' dot_claude/skills/quality-goal/references/readiness-policy.md` 를 돌려 두 문언이 § readiness 의 지위 절 안에서 잡힌다. AC-39 — `grep -n -e 'READY' -e '한도를 코드로 강제하지 않는다' -e '비용 상한' dot_claude/skills/quality-goal/references/readiness-policy.md` 를 돌려 세 문언이 § readiness 의 지위 절 안에서 잡힌다. AC-44 — `sed -n '/^## digest 대조$/,/^## /p' dot_claude/skills/quality-goal/references/readiness-policy.md | grep -c -e '단계를 바꾸지 않고' -e '사용자에게 보고한다'` 가 2 이상이다. `sed` 로 § digest 대조 절만 잘라내므로 § 실패 보고 문단의 문언이 섞이지 않는다. 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.

### T10. `references/model-routing.md` 에 라우트 행과 역할 분담을 더한다

대상 AC: AC-83

- **실패 확인**: 이 태스크가 소유한 테스트를 먼저 작성한다 — `test_model_routing_includes_author_and_readiness_rows`(AC-83). 작성 직후 각각을 `CMD-2 -k <이름>` 으로 돌리면 전부 실패한다.
- **구현**:
  - `references/model-routing.md` 의 Route table 에 세 행을 더한다 — Spec author(standard) `gpt-5.6-terra` high, Spec author(strict) `gpt-5.6-sol` high, readiness reviewer(fresh) `gpt-5.6-sol` high.
  - 두 파일의 역할 분담을 한 문단으로 적는다 — `model-routing.md` 는 역할별 모델·effort 값과 실행 가능한 호출 템플릿을, `references/readiness-policy.md` 는 그 템플릿을 인용하며 절차 문맥(언제 부르고 무엇을 프롬프트에 싣고 결과를 어떻게 기록하는지)을 담는다.
  - 기존 라우트 행, 구현·수정 라운드 호출 템플릿, 프리플라이트 블록, 금지 플래그 문단은 건드리지 않는다.
- **통과 확인**: 소유 테스트를 `CMD-2 -k <이름>` 으로 하나씩 돌려 전부 통과시킨다 — `test_model_routing_includes_author_and_readiness_rows`(AC-83). 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.

### T11. `templates/spec.md` 에 두 절을 더한다

대상 AC: AC-73

- **실패 확인**: 이 태스크가 소유한 테스트를 먼저 작성한다 — `test_spec_template_has_traceability_and_command_table`(AC-73). 작성 직후 각각을 `CMD-2 -k <이름>` 으로 돌리면 전부 실패한다.
- **구현**:
  - `templates/spec.md` 에 두 절을 더한다.
  - `## Requirements traceability` 를 최상위 헤딩으로 `## Acceptance criteria` 바로 뒤·`## Architecture` 바로 앞에 넣는다. 본문은 요구사항↔AC 매핑 표의 자리표시자와 그 표의 규칙 한 문장이다.
  - `### 판정 명령 표` 를 `## Test strategy` 아래 **첫 하위 절**로 넣는다. 본문은 `| ID | 명령 | 통과 조건 |` 표의 자리표시자다.
  - 다른 절의 순서와 문언, strict-only 주석 쌍은 건드리지 않는다.
- **통과 확인**: 소유 테스트를 `CMD-2 -k <이름>` 으로 하나씩 돌려 전부 통과시킨다 — `test_spec_template_has_traceability_and_command_table`(AC-73). 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.

### T12. `SKILL.md` 를 갱신한다

대상 AC: AC-1, AC-71, AC-72, AC-82

- **실패 확인**: 이 태스크가 소유한 테스트를 먼저 작성한다 — `test_spec_authoring_is_delegated_to_codex_contract`(AC-1), `test_readiness_policy_is_referenced_from_skill`(AC-72), `test_skill_version_bumped_for_contract_extension`(AC-82) 셋은 해당 문언·등재·버전이 아직 없으므로 작성 직후 `CMD-2 -k <이름>` 에서 실제로 실패한다. `CMD-3`(AC-71)은 불변 고정 판정이라(현재 393행) § Tasks 서두의 **변이 확인** 으로 red 를 만든다 — `SKILL.md` 끝에 빈 줄 200개를 붙여 `CMD-3` 이 500 이상을 내는지 확인하고 즉시 되돌린다.
- **구현**:
  - `SKILL.md` 의 `### Spec` 절차에 Spec 초안과 개정의 실행 주체가 Codex author 이고 오케스트레이터가 Spec 본문을 직접 쓰지 않는다는 문장을 넣고, readiness 심사와 근거 첨부의 자리를 그 절차 안에 배치한다.
  - 참조 경로 목록에 `references/readiness-policy.md` 를 등재한다.
  - frontmatter `version` 을 `5.0.0` 에서 `5.1.0` 으로 올린다(상태 기록 계약 확장이므로 MINOR).
- **기존 단언 둘을 함께 갱신한다** — `tests/test_content_contracts.py` 의 `test_skill_version_is_major_bumped` 가 `assertEqual("5.0.0", frontmatter["version"])` 로, `test_frontmatter_contract` 가 `expected["version"] = "5.0.0"` 으로 버전을 리터럴 고정한다. 둘 다 `"5.1.0"` 으로 바꾼다. 테스트 이름은 바꾸지 않는다(§ Global constraints 7). 이 갱신 없이는 이 태스크의 `CMD-1` 이 반드시 실패한다. 새로 만드는 `test_skill_version_bumped_for_contract_extension`(AC-82)은 리터럴이 아니라 "5.0.0 보다 크고 MINOR 이상" 이라는 관계를 판정하므로 두 기존 단언과 중복이 아니다.
  - 보존 대상 여덟 절과 Safety rules 문언은 한 글자도 바꾸지 않는다.
  - 추가 분량이 106행을 넘지 않도록 상세는 전부 `references/readiness-policy.md` 에 두고 `SKILL.md` 에는 단계 절차와 참조 경로만 남긴다.
- **통과 확인**: 소유 테스트를 `CMD-2 -k <이름>` 으로 하나씩 돌려 전부 통과시킨다 — `test_spec_authoring_is_delegated_to_codex_contract`(AC-1), `test_readiness_policy_is_referenced_from_skill`(AC-72), `test_skill_version_bumped_for_contract_extension`(AC-82). 명령으로 판정하는 AC — `CMD-3`(AC-71). 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.

### T13. `docs/quality-goal-maintenance.md` 를 갱신한다

대상 AC: AC-5, AC-74, AC-75, AC-76, AC-86

- **실패 확인**: 이 태스크가 소유한 테스트를 먼저 작성한다. `test_maintenance_doc_covers_readiness`(AC-74), `test_maintenance_doc_replaces_test_section_with_command_table`(AC-75), `test_version_guard_is_shared_not_inlined`(AC-86) 셋은 해당 절과 문언이 아직 없으므로 작성 직후 `CMD-2 -k <이름>` 에서 실제로 실패한다. `test_forbidden_codex_flags_contract`(AC-5)는 **불변 고정 테스트**다 — T7·T10 이 금지 문맥을 지켜 썼다면 이 태스크가 문서를 고치기 전에도 통과한다. 따라서 § Tasks 서두의 **변이 확인** 으로 red 를 만든다: `references/readiness-policy.md` 의 금지 문단에서 **금지 토큰(`금지`·`사용하지 않는다`·`쓰지 않는다`·`forbidden`·`prohibited`)만** 지우고 플래그 문자열은 그대로 남긴다 — 문장을 통째로 지우면 검사 대상 플래그도 함께 사라져 red 가 만들어지지 않는다. 그 상태에서 테스트가 실제로 실패하는지 보고 절차 4 의 해시 비교로 복구한다. AC-76 — `grep -n -e '3.12' -e 'enterContext' -e 'NO TESTS RAN' docs/quality-goal-maintenance.md` 가 아직 아무것도 잡지 못한다.
- **구현**:
  - `docs/quality-goal-maintenance.md` 의 `## 결정적 테스트` 절을 `## 판정 명령 표` 절로 **대체**한다(병기하지 않는다).
  - 새 절에 CMD-1~CMD-7 일곱 행을 싣고, 그 표 **바로 아래**(표와 문언 사이에 다른 헤딩 없이) 최소 인터프리터 버전 3.12 와 두 근거(`enterContext` 는 3.11 도입, `NO TESTS RAN` 종료 코드 5 는 3.12 도입)를 적는다. 이 절이 판정 명령 표의 정본이라는 것도 명시한다.
  - CMD-1 과 CMD-2 의 정의는 `tests/assert_python_version.py` 호출을 포함하고 버전 비교식을 명령 안에 인라인으로 복제하지 않는다.
  - readiness 점검 항목을 더한다 — `codex exec` 플래그, readiness 결과 스키마, author·reviewer 라우팅 모델, 그리고 `references/model-routing.md` 와 `references/readiness-policy.md` 의 동기화.
  - 플래그 문자열을 싣는 문단마다 금지 토큰을 함께 두고 펜스 코드 블록 안에는 넣지 않는다 — 이 태스크가 그 문자열을 싣는 마지막 문서이므로 여기서 AC-5 가 최종 상태로 판정된다.
- **통과 확인**: 소유 테스트를 `CMD-2 -k <이름>` 으로 하나씩 돌려 전부 통과시킨다 — `test_forbidden_codex_flags_contract`(AC-5), `test_maintenance_doc_covers_readiness`(AC-74), `test_maintenance_doc_replaces_test_section_with_command_table`(AC-75), `test_version_guard_is_shared_not_inlined`(AC-86). AC-76 — `grep -n -e '3.12' -e 'enterContext' -e 'NO TESTS RAN' docs/quality-goal-maintenance.md` 를 돌려 세 문언이 § 판정 명령 표의 표 바로 아래에서 잡히고 그 사이에 다른 헤딩이 없다. 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.

### T14. 보존 계약과 전체 회귀를 확인한다

대상 AC: AC-77, AC-78, AC-80, AC-81

- **실패 확인**: 이 태스크의 네 판정은 전부 불변 고정이므로 § Tasks 서두의 **변이 확인** 으로 red 를 만든다. `test_formal_pass_gate_threshold_unchanged`(AC-81)을 먼저 작성한 뒤 `references/spec-rubric.md` 의 `85` 를 `80` 으로 바꿔 실패를 확인하고 되돌린다. `CMD-4`(AC-80)는 `SKILL.md` 의 `## Safety rules` 에서 한 줄을 지워 실패를 확인하고 되돌린다. `CMD-6`(AC-78)은 기존 테스트 하나의 이름을 임시로 바꿔 실패를 확인하고 되돌린다. `CMD-1`(AC-77)은 이 태스크가 만든 `test_formal_pass_gate_threshold_unchanged` 하나를 임시로 `self.fail()` 로 바꿔 전체 스위트가 실제로 `FAILED` 를 내는지 확인하고 절차 4 로 복구한다 — 전체 스위트가 어떤 실패도 드러내지 못하는 상태였는지 이 변이가 가른다. 그 뒤 T1~T13 이 끝난 상태에서 전체를 다시 돌리며, 그 전까지 각 태스크가 돌린 CMD-1 이 회귀 신호였다. 네 변이는 각각 § Tasks 서두의 절차 0~4 를 따로 수행하며, 복구는 `git diff` 가 아니라 절차 4 의 **해시 비교**로 확인한다 — 커밋 없이 순차로 구현한 워킹 트리에는 앞선 태스크의 정상 변경이 쌓여 있어 `git diff` 가 비어 있을 수 없다.
- **구현**:
  - 구현 산출물이 아니라 최종 상태의 판정 태스크다. 새 파일을 만들지 않는다.
  - `CMD-1` 로 전체 스위트를 돌린다. 실행 테스트 수가 310 + 이 Plan 의 태스크들이 만든 신규 테스트 수여야 하며, 그 수는 태스크마다 실제로 추가한 `def test_` 개수를 합해 얻는다(어림값을 쓰지 않는다).
  - `CMD-4` 로 `SKILL.md` 의 보존 대상 여덟 절이 base revision 과 바이트 단위로 같은지 확인한다.
  - `CMD-6` 으로 base revision 의 테스트 이름 집합이 부분집합인지 확인한다.
  - 공식 게이트 임계 85 가 `references/spec-rubric.md` 와 `references/plan-rubric.md` 에서 바뀌지 않았는지 테스트로 고정한다.
  - `git status --porcelain` 으로 초기 dirty 경로 둘이 그대로이고 그 밖의 변경이 § File map 의 목록 안인지 확인한다.
- **통과 확인**: 소유 테스트를 `CMD-2 -k <이름>` 으로 하나씩 돌려 전부 통과시킨다 — `test_formal_pass_gate_threshold_unchanged`(AC-81). 명령으로 판정하는 AC — `CMD-1`(AC-77), `CMD-6`(AC-78), `CMD-4`(AC-80). 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.
## Verification commands

**인터프리터와 base revision 을 먼저 고정한다.** 아래 두 줄을 셸에서 실행한 뒤 명령을 돌린다. `python3` 를 직접 부르지 않는 이유는 셸에 따라 3.9.6 으로 풀릴 수 있기 때문이다(§ Global constraints 3).

```bash
QG_PY="${QG_PY:-$(command -v python3.14 || command -v python3.13 || command -v python3.12 || echo /opt/homebrew/bin/python3)}"
QG_BASE=6d60011cbdaead7946b191d3f12029eef5c141c8
```

`assert_python_version.py` 가 `QG_PY` 의 버전을 다시 확인하므로, 탐색이 3.12 미만을 골랐다면 CMD-1·CMD-2 가 테스트를 실행하지 않고 실패한다. `QG_BASE` 는 CMD-4·CMD-6 이 `git show` 에 쓰는 값이며 두 스크립트가 첫 인자로 받는다.

| 순서 | ID | 명령 | 기대 결과 |
|---|---|---|---|
| 1 | CMD-1 | `"$QG_PY" dot_claude/skills/quality-goal/tests/assert_python_version.py && PYTHONDONTWRITEBYTECODE=1 "$QG_PY" -m unittest discover -s dot_claude/skills/quality-goal/tests -p 'test_*.py'` | 종료 코드 0, `OK`. 실행 테스트 수가 310 + 신규 테스트 수 |
| 2 | CMD-2 | `"$QG_PY" dot_claude/skills/quality-goal/tests/assert_python_version.py && PYTHONDONTWRITEBYTECODE=1 "$QG_PY" -m unittest discover -s dot_claude/skills/quality-goal/tests -p 'test_*.py' -k <테스트 이름>` | 종료 코드 0. 3.12 이상에서 매칭 0건이면 `unittest` 가 5 를 내므로 오타나 미구현 테스트 이름은 통과할 수 없다 |
| 3 | CMD-3 | `wc -l < dot_claude/skills/quality-goal/SKILL.md` | 500 미만 |
| 4 | CMD-4 | `"$QG_PY" dot_claude/skills/quality-goal/tests/assert_preserved_sections.py "$QG_BASE"` | 종료 코드 0, `보존 대상 절 불변` |
| 5 | CMD-5 | `"$QG_PY" -c "import json;d=json.load(open('dot_claude/skills/quality-goal/schemas/readiness-result.schema.json'));assert d['type']=='object';assert d['additionalProperties'] is False;print('OK')"` | 종료 코드 0, `OK` |
| 6 | CMD-6 | `"$QG_PY" dot_claude/skills/quality-goal/tests/assert_tests_preserved.py "$QG_BASE"` | 종료 코드 0, `기존 테스트 보존` |
| 7 | CMD-7 | `OLD_PY=/usr/bin/python3; "$OLD_PY" -c 'import sys;raise SystemExit(0 if sys.version_info<(3,12) else 1)' && "$QG_PY" dot_claude/skills/quality-goal/tests/assert_python_version.py && ! "$OLD_PY" dot_claude/skills/quality-goal/tests/assert_python_version.py` | 종료 코드 0 |

기준선은 `QG_BASE` 에서 CMD-1 이 `Ran 310 tests` / `OK` 인 것이다. 실측 로그는 `.claude/quality-state/<task-id>/evidence/deterministic-baseline.md` 에 있다 — 3.14.7 에서 `OK`(종료 코드 0), `/usr/bin/python3` 3.9.6 에서는 `enterContext` 부재로 23건이 오류(종료 코드 1)이며, 매칭 0건 `-k` 의 종료 코드는 3.9.6 이 0, 3.14.7 이 5 다. 태스크마다 CMD-1 을 다시 돌려 회귀가 없는지 본다.

**실행 순서.** ① CMD-1 로 전체 회귀 ② 실패한 AC 가 있으면 CMD-2 로 좁혀 재현 ③ CMD-3·CMD-4·CMD-5·CMD-6·CMD-7 은 CMD-1 과 독립적으로 실행. Codex CLI 자체의 성질(`--output-schema` 가 `const` 를 거부하는 것 등)은 이 저장소의 테스트로 판정하지 않고 유지보수 문서의 분기별 CLI 점검에 위임한다.

**CMD-7 을 실행할 수 없는 환경.** 3.12 미만 인터프리터가 없으면 CMD-7 을 돌릴 수 없고 AC-85 는 미판정으로 검증 기록에 남긴다. 그 경우에도 가드의 거부 분기는 AC-90(CMD-2)이 `is_supported` 의 경계값과 `__main__` 위임으로 판정하므로 미판정으로 남는 계약은 없다. 이 저장소의 macOS 환경에서는 `/usr/bin/python3` 3.9.6 이 있어 CMD-7 이 실행 가능하다(실측 로그 § 2·§ 3).

**구성되지 않은 검증 범주.** 이 저장소에 lint·type check·build·E2E 구성이 없다. 저장소 루트와 `dot_claude/skills/quality-goal/` 하위(깊이 2)에서 `pyproject.toml`, `setup.cfg`, `.flake8`, `ruff.toml`, `.ruff.toml`, `mypy.ini`, `.mypy.ini`, `tox.ini`, `Makefile` 을 모두 조회했고 하나도 없었다. 네 범주는 `not configured` 로 보고하며 통과로 기록하지 않는다.

## Rollout and rollback

**롤아웃.** 이 작업은 chezmoi source 만 바꾼다. 배포는 사용자가 `chezmoi apply` 로 별도 수행하며 이 Plan 의 어떤 태스크도 그것을 실행하지 않는다. 다른 워크트리(#79)의 세션이 배포본 v5.0.0 을 실행 중이므로 적용 시점은 사용자가 고른다.

**호환성.** 상태 파일 `schema_version` 은 1 을 유지한다. 새 필드 둘은 선택적이고, 없으면 미실행으로 간주하며 읽기만으로 생기지 않는다. 따라서 이 변경 전에 시작한 goal 의 상태 파일을 구버전 스크립트가 그대로 읽는다. 이 작업은 `record-review` 계열에 어떤 조건도 추가하지 않으므로, 진행 중 goal 이 재개 시점에 막히는 경로가 없다.

**Spec § Failure behavior 의 실패 경로 대응.** Spec 이 규정한 실패 경로는 전부 구현 대상이거나 운영 절차다. 어디가 그것을 지는지 다음과 같다.

| Spec 의 실패 경로 | 이 Plan 의 대응 |
|---|---|
| author 비정상 종료 / 결과 파일 없음·스키마 위반 / Spec 무변경 | 단계 유지 + 사용자 보고 + 모델 대체 금지. T7 이 `references/readiness-policy.md` 의 author 실패 절에 셋을 문서화하며, 그 절이 보고에 실을 것(실패한 명령과 표준 오류 파일 경로)까지 적는다. AC-15 가 앞의 셋을, AC-16 이 무변경 갈래를 판정한다. 코드가 아니라 오케스트레이터 절차이므로 판정 수단도 문서 계약이다 |
| author 가 허용 밖 파일 수정 | 변경을 **되돌리지 않고** 사용자에게 보고 후 판단 요청. T7 이 § 쓰기 범위 절에 `git status --porcelain` 확인과 제외 규칙, 그리고 되돌리지 않는다는 것을 함께 적는다(AC-11) |
| 모델 거부·부재 | author 쪽은 T7 의 author 실패 절이(AC-15), readiness 쪽은 T9 의 § 실패 보고 문단이 기존 `BLOCKED_MODEL_UNAVAILABLE` 복구 경로를 참조한다. 두 문서 모두 **묻는 동안 단계 유지 / 거부 시 `BLOCKED` 전이** 두 국면을 구분해 적는다. 이 Plan 은 그 경로를 새로 만들지 않는다 |
| readiness 호출 비정상 종료·결과 파일 미생성·타임아웃 | 기록은 T6 의 `--invocation-status failed` → `invocation_failed`(AC-57). 세 원인을 모두 `failed` 로 넘긴다는 지시는 T9 의 § 실패 보고 문단에 있다 |
| readiness 결과 스키마 위반 | 기록은 T3 의 검증 함수 + T6 의 `schema_invalid`(AC-70·AC-58). 검증 오류의 사용자 보고는 Spec R8.5 의 오케스트레이터 절차이고 T9 의 **§ 실패 보고** 문단이 그것을 싣는다. Spec 이 그 보고에 AC 를 두지 않았으므로 이 Plan 도 별도 판정 수단을 만들지 않는다 |
| 심사 대상 경로 불일치 | T9 의 § digest 대조 절이 호출 전 확인을 절차로 배치하고 § 실패 보고 문단이 단계 유지·보고를 적는다(AC-41·AC-44) |
| `--artifact-digest` != 등록 digest | T6 의 사전 거부(AC-42) |
| 결과 digest 불일치 | T6 의 `digest_mismatch` 기록(AC-43) |
| 네 거부 계약(`--formal-round` 불일치, `--invocation-status` 열거 위반, `failed` 인데 `--stderr-path` 부재, `light` 모드 호출) | 거부 자체는 T6 이 구현하고 AC-47·AC-56·AC-57·AC-59 가 판정한다. 거부 **뒤** 의 복구 동작(유도값 재계산 후 재호출, 허용값 제시 후 재호출, 표준 오류 파일 생성 후 재호출)은 Spec § Failure behavior 표가 규정하는 오케스트레이터 동작이고 Spec 이 그것에 AC 를 두지 않았다. 이 Plan 은 그 동작을 구현 대상으로 배정하지 않는다 — 거부가 남기는 상태 변화가 없어 판정할 산출물이 없기 때문이며, 재호출은 사람이 오류 메시지를 읽고 하는 일이다 |
| readiness 가 반복 실패해 유효 결과가 없음 | T9 의 § 근거 첨부 절이 그 사실을 요약 파일에 적게 한다(AC-40). 어떤 명령도 진행을 막지 않는다(AC-33) |
| 비대화형 stdin 무한 대기 | T8 의 stdin 계약 문언으로 사전 차단(AC-20) |

**롤백 트리거.** 다음 중 하나면 이 작업을 중단하고 아래 우선순위에 따라 처리한다. **"되돌린다" 가 모든 트리거에 해당하지는 않는다** — 트리거 5 의 초기 dirty 갈래는 되돌리지 않고 중단·보고로만 처리한다.

1. CMD-1 이 실패하고 30분 안에 원인을 좁히지 못한다.
2. CMD-4 가 보존 대상 여덟 절의 변경을 보고한다.
3. CMD-6 이 기존 테스트 이름의 삭제·개명을 보고한다.
4. CMD-3 이 500 이상을 보고한다.
5. `git status --porcelain` 에 § File map 밖의 경로나 초기 dirty 경로의 변경이 나타난다.

**롤백 절차.** 트리거 1~4 는 이 브랜치의 워킹 트리 변경만 되돌린다 — `git checkout -- <해당 경로>` 를 § File map 의 **수정 대상** 에만 적용하고 신설 파일은 삭제한다. 되돌릴 경로를 손으로 고르지 않고 § File map 의 목록에서 그대로 가져온다. 커밋하지 않았으므로 리비전 되돌리기는 필요 없고, 배포본을 갱신하지 않았으므로 다른 세션에 영향이 없다.

**트리거는 상호 배타적이지 않으므로 우선순위를 둔다.** 여러 트리거가 동시에 걸리면 **트리거 5 의 초기 dirty 갈래가 언제나 최우선** 이고, 그 절차가 끝날 때까지 다른 트리거의 롤백을 실행하지 않는다. 그다음은 트리거 5 의 나머지 갈래, 그다음이 트리거 1~4 다. 근거는 데이터 손실 위험의 크기다 — 사용자의 미커밋 변경을 잃는 것만 되돌릴 수 없다.

**트리거 5 의 초기 dirty 갈래는 롤백하지 않고 중단·보고한다.** 초기 dirty 경로 둘(`.prior-art/`, `docs/development/2026-09-05-70-quality-goal-codex-spec-readiness/`)은 이 작업 이전부터 사용자의 미커밋 변경이 들어 있는 경로다. 그 경로가 오염됐을 때 `git checkout --` 를 쓰면 **사용자의 변경을 지운다** — 되돌리기가 곧 데이터 손실이다. 절차는 다음이다.

1. 구현을 즉시 멈춘다. 이후 허용되는 명령은 **2번의 넷뿐** 이다 — `mkdir -p .claude/quality-state/<task-id>/incident`, `git status --porcelain`, `git diff -- <해당 경로>`, 그리고 두 출력을 그 디렉터리 아래 파일로 쓰는 리다이렉션. 저장소의 어떤 파일도 고치거나 되돌리거나 지우지 않는다.
2. 위 넷으로 `git status --porcelain` 과 `git diff -- <해당 경로>` 의 출력을 `.claude/quality-state/<task-id>/incident/` 아래 파일로 남긴다. 두 git 명령은 읽기이고, 쓰기는 저장소가 무시하는 상태 디렉터리에만 일어나므로 워킹 트리의 추적 대상이 바뀌지 않는다.
3. 그 파일 경로와 함께 사용자에게 보고하고 판단을 요청한다. 오케스트레이터가 되돌리기·유지·부분 채택 중 어느 것도 임의로 고르지 않는다.
4. 사용자의 결정이 나오기 전에는 § File map 의 다른 경로도 롤백하지 않는다 — 부분 롤백이 원인 진단을 어렵게 만들기 때문이다.

이는 기존 스킬의 dirty-path 보존 계약(`SKILL.md` 의 "Preserve initial dirty paths byte-identically, never revert them")과 같은 기준이다.

**§ File map 밖의 다른 경로가 오염된 경우**(트리거 5 의 나머지 절반)는 트리거 1~4 의 절차를 쓸 수 없다 — 그 절차는 되돌릴 대상을 § File map 안으로 한정하므로 목록 밖 경로를 복구하지 못한다. 이 갈래는 별도 절차를 쓴다.

1. 그 경로가 초기 dirty 경로 둘 중 하나인지 먼저 확인한다. 맞으면 위의 중단·보고 절차로 간다.
2. 아니면 `git ls-files --error-unmatch <경로>` 로 추적 여부를 본다. 추적 중이면 `git checkout -- <그 경로>` 로 그 경로만 되돌린다.
3. 추적되지 않는 새 파일이고 이 작업이 만든 것이 분명하면 그 파일만 삭제한다. 분명하지 않으면 삭제하지 않고 **바로 위 초기 dirty 갈래의 1~4 단계 중단·보고 절차** 를 그 경로에 대해 그대로 수행한다. 이 갈래의 1번으로 돌아가지 않는다 — 그러면 같은 검사를 반복하는 고리가 된다.
4. 어느 경우든 복구 대상은 오염된 그 경로 하나이며, § File map 의 다른 경로를 함께 되돌리지 않는다.

**모니터링.** 상시 실행 구성 요소가 없으므로 메트릭·알림 대상이 없다. 각 태스크 종료 시 CMD-1 의 실행 테스트 수와 `OK` 여부가 유일한 진행 신호다.

## Acceptance-criteria traceability

Spec 의 수용 기준 90건 전부를 태스크와 검증 명령에 매핑한다. 각 AC 는 정확히 한 태스크가 소유하며, 소유 태스크가 § Task dependencies 의 수행 순서에서 끝난 시점에 그 검증 명령이 실제로 실행 가능하다(§ Tasks 의 소유권 원칙). `CMD-2 -k <이름>` 은 § Verification commands 의 CMD-2 에 그 테스트 이름을 넣어 실행한다는 뜻이다. 기대 결과는 Spec 의 AC 문언을 그대로 옮긴 것이다.

**같은 요구사항의 AC 가 같은 판정 대상을 가리키는지 전수 대조했다.** 제출 전 `.claude/quality-state/<task-id>/ac_crosscheck.py` 로 90건을 네 성질로 훑었다 — (a) 소유 태스크 본문에 그 테스트를 만드는 단계가 있는가 (b) 실패 확인·통과 확인 명령에 등장하는가 (c) 같은 요구사항의 AC 들이 같은 판정 대상 파일을 가리키는가 (d) 기대 결과가 의존하는 산출물을 만드는 태스크에 선행 간선이 있는가. 직전 실행의 `PLAN-06` 이 (c) 의 위반이었다.

스크립트의 (a)·(b)·(d) 는 위반 0 이고 종료 코드 0 이다. (d) 는 이 작업이 **처음 만드는** 다섯 산출물(`tests/assert_python_version.py`, `tests/assert_preserved_sections.py`, `tests/assert_tests_preserved.py`, `schemas/readiness-result.schema.json`, `references/readiness-policy.md`)에 대해서만 존재를 선행 조건으로 강제하고, base revision 에 이미 있는 파일은 `d-warn` 으로 따로 보고해 사람이 판정한다. 그 경고는 한 건이며 의존이 아니다 — **AC-40**(T9 소유)이 `SKILL.md` 를 언급하지만, 판정 대상은 `references/readiness-policy.md` 의 문언이고 `SKILL.md` 쪽은 그 문언이 근거로 인용하는 `## Review invocation contract` 절이다. 그 절은 base 에 이미 있고 R9.5 의 바이트 단위 보존 대상이라 T12 가 건드리지 않으므로, T9 종료 시점에 AC-40 의 통과 확인이 성립한다. (c) 는 종료 코드를 바꾸지 않고 차이를 보고만 하며, 판정 대상 파일이 AC 문언에 드러나는 것만 비교했을 때 갈리는 요구사항은 다섯이고 다섯 다 의도된 것이다.

| 요구사항 | 갈리는 대상 | 의도된 이유 |
|---|---|---|
| R1.4 | AC-5 → `docs/quality-goal-maintenance.md` 를 포함한 검사 대상 전체, AC-6·AC-7 → `references/readiness-policy.md` | 한 금지가 여러 문서에 성립하는지를 나눠 본다. AC-5 는 표현 규범의 전역 성립을, AC-6 은 열거의 완전성을, AC-7 은 존재하지 않는 플래그의 부재를 본다 — 서로 다른 사실이다 |
| R1.5 | AC-8 → `references/readiness-policy.md`, AC-9 → 같은 파일 + `references/revision-check-policy.md` | AC-9 가 인용의 **출처** 를 함께 가리키는 것이며 판정 대상 자체는 같은 파일이다. 상위집합이지 분기가 아니다 |
| R9.1 | AC-71 → `SKILL.md`, AC-72 → `SKILL.md` + `references/readiness-policy.md` | AC-72 는 `SKILL.md` 의 참조 목록이 그 파일을 가리키는지 보므로 두 이름이 함께 나온다. 판정 대상은 `SKILL.md` 하나다 |
| R9.7 | AC-83 → `references/model-routing.md`, AC-84 → 같은 파일 + `references/readiness-policy.md` | 역할 분담은 두 파일의 관계를 규정하는 사실이므로 두 이름이 함께 나오는 것이 정의상 맞다 |
| R9.8 | AC-85·AC-90 → `tests/assert_python_version.py`, AC-86 → 그 스크립트 + `docs/quality-goal-maintenance.md` | 정본 문서가 스크립트를 부르는지(AC-86)와 스크립트 자체가 어떻게 동작하는지(AC-85·AC-90)는 서로 다른 사실이다 |

직전 실행의 `PLAN-06` 은 이와 달리 **같은 사실**(판정 명령 표)을 두 파일에서 판정하려던 것이었고, 이 Spec 은 그것을 `docs/quality-goal-maintenance.md` 하나로 통일해 정본을 못박았다(Spec § Test strategy). 위 다섯은 모두 서로 다른 사실이거나 인용 출처를 함께 적은 상위집합이며, 같은 사실을 두 곳에서 판정하는 자리는 없다.

| Criterion | Task | Verification command | Expected outcome |
|---|---|---|---|
| AC-1 | T12 SKILL.md | `CMD-2 -k test_spec_authoring_is_delegated_to_codex_contract` | `SKILL.md` 의 Spec 단계 절차가 Spec 초안과 개정의 실행 주체를 Codex author 로 지정하고, 오케스트레이터가 Spec 본문을 직접 쓰지 않는다고 명시한다. |
| AC-2 | T7 policy author 절 | `CMD-2 -k test_author_prompt_required_elements_contract` | `references/readiness-policy.md` 가 author 호출 전 요구사항 발굴 수행과 그 결과의 프롬프트 반영을 요구한다. |
| AC-3 | T7 policy author 절 | `CMD-2 -k test_author_prompt_required_elements_contract` | `references/readiness-policy.md` 가 요구사항 발굴에서 남은 물질적 모호성을 author 호출 **전에** 사용자 질의로 해소하도록 요구한다. |
| AC-4 | T7 policy author 절 | `CMD-2 -k test_author_invocation_template_contract` | `references/readiness-policy.md` 의 author 호출 템플릿이 R1.3 의 아홉 요소를 모두 포함한다. |
| AC-5 | T13 유지보수 문서 | `CMD-2 -k test_forbidden_codex_flags_contract` | R1.4 가 열거한 여덟 옵션과 `--full-auto` 가 검사 대상 파일에 나타나는 모든 위치가 금지 문언 안이다. 판정 규칙은 기계적이다 — 검사 대상은 `dot_claude/skills/quality-goal/` 하위의 `.md` 파일 전부와 `docs/quality-goal-maintenance.md` 이고, 문단은 빈 줄로 구분된 연속 줄 묶음이며, 금지 표현 토큰은 `금지`·`사용하지 않는다`·`쓰지 않는다`·`forbidden`·`prohibited` 다섯이다. 각 플래그 문자열을 포함한 줄이 속한 문단에 그 토큰이 하나 이상 있어야 하고, 플래그 문자열이 펜스 코드 블록 안에는 한 번도 나타나지 않아야 한다. |
| AC-6 | T7 policy author 절 | `CMD-2 -k test_forbidden_codex_flags_enumerate_current_cli` | `references/readiness-policy.md` 의 금지 목록이 R1.4 의 여덟 이름(`--yolo` 포함)을 모두 포함하고, 기준 CLI 버전 문자열과 `--yolo` 가 `--help` 에 없는 숨은 별칭이라는 사실을 함께 기록하며, `--sandbox` 의 확대 지정 금지를 포괄적으로 적는다. |
| AC-7 | T7 policy author 절 | `CMD-2 -k test_codex_exec_has_no_approval_flag_contract` | 스킬의 어떤 문서도 `codex exec` 호출에 `-a` 또는 `--ask-for-approval` 을 지시하지 않고, `references/readiness-policy.md` 가 그 플래그의 부재를 명시한다. |
| AC-8 | T7 policy author 절 | `CMD-2 -k test_author_prompt_required_elements_contract` | author 프롬프트 필수 요소 열두 가지가 `references/readiness-policy.md` 에 목록으로 존재하며, R1.5 가 절대 경로를 요구한 다섯 항목이 그 문서에서도 **절대 경로**로 한정돼 있다. |
| AC-9 | T7 policy author 절 | `CMD-2 -k test_author_revision_note_format_contract` | `references/readiness-policy.md` 가 라운드 2 이상의 개정 노트 형식을 `references/revision-check-policy.md` 에서 그대로 인용해 싣는다 — 절 헤딩 `## 라운드 <n> 개정` 과 다섯 열 표 머리. 같은 공식 라운드에 절이 정확히 하나이고 readiness 개정이 반복되면 새 절을 만들지 않고 그 절에 행을 누적·갱신한다는 규칙, 그리고 그 절의 범위가 직전 라운드 스냅숏 이후의 모든 변경이며 readiness 가 유발한 변경도 포함된다는 규정도 함께 싣는다. |
| AC-10 | T7 policy author 절 | `CMD-2 -k test_author_cross_regression_review_contract` | author 프롬프트 계약이 조합 검토 지시를 필수로 포함하고 교차 회귀 전례를 근거로 인용한다. |
| AC-11 | T7 policy author 절 | `CMD-2 -k test_author_write_scope_contract` | `references/readiness-policy.md` 가 author 의 수정 허용 파일을 대상 Spec 과 개정 노트 둘로 한정하고, 호출 후 `git status --porcelain` 확인을 요구하며, 그 비교에서 `initial_dirty_paths` 와 `.claude/quality-state/<task-id>/` 하위를 제외하고 결과의 `changed_files` 와 대조한다고 명시한다. |
| AC-12 | T5 record-draft-attempt | `CMD-2 -k test_record_draft_attempt_increments_only_draft_attempts` | `record-draft-attempt` 호출 1회가 `draft_attempts` 의 해당 artifact 값을 1 증가시키고 `rounds` 의 어떤 값도 바꾸지 않는다. |
| AC-13 | T5 record-draft-attempt | `CMD-2 -k test_record_draft_attempt_is_per_artifact` | `draft_attempts.spec` 증가가 `draft_attempts.plan` 을 바꾸지 않는다. |
| AC-14 | T5 record-draft-attempt | `CMD-2 -k test_draft_attempts_created_on_first_record` | `draft_attempts` 가 없는 schema v1 상태에 첫 `record-draft-attempt` 를 적용하면 그때 `draft_attempts` 가 생성되고 해당 artifact 값이 1 이 된다. |
| AC-15 | T7 policy author 절 | `CMD-2 -k test_author_failure_recovery_contract` | author 호출 실패(비정상 종료·결과 파일 없음·스키마 검증 실패) 시 단계를 유지하고 모델을 대체하지 않는다는 지시가 `references/readiness-policy.md` 에 존재하며 `BLOCKED_MODEL_UNAVAILABLE` 경로를 참조한다. |
| AC-16 | T7 policy author 절 | `CMD-2 -k test_author_no_change_is_failure_contract` | author 호출 전후 Spec digest 가 같으면 개정 실패로 처리한다는 지시가 존재한다. |
| AC-17 | T8 policy reviewer 절 | `CMD-2 -k test_readiness_reviewer_is_fresh_contract` | `references/readiness-policy.md` 가 readiness reviewer 를 author 와 별개 프로세스로 실행하고 author 문맥을 상속하지 않는다고 명시한다. |
| AC-18 | T8 policy reviewer 절 | `CMD-2 -k test_readiness_invocation_template_contract` | readiness 호출 템플릿이 `--sandbox read-only` 를 쓰고 금지 플래그를 포함하지 않는다. |
| AC-19 | T8 policy reviewer 절 | `CMD-2 -k test_readiness_read_only_contract` | readiness 프롬프트 계약이 읽기 전용과 git 쓰기 금지를 명시한다. |
| AC-20 | T8 policy reviewer 절 | `CMD-2 -k test_readiness_stdin_guard_contract` | `references/readiness-policy.md` 의 author·readiness 호출 템플릿이 모두 표준 입력을 프롬프트 파일 또는 `/dev/null` 에 연결하고, 둘 중 어느 형태도 아닌 호출을 금지한다고 명시하며, 그 이유(비대화형 무한 대기)를 기록한다. |
| AC-21 | T2 결과 스키마 | `CMD-2 -k test_readiness_schema_uses_type_not_const` | `schemas/readiness-result.schema.json` 의 모든 property 정의가 `type` 키를 가지며 `const` 키를 한 번도 쓰지 않는다. |
| AC-22 | T8 policy reviewer 절 | `CMD-2 -k test_readiness_prompt_treats_notes_as_claims` | readiness 프롬프트 계약이 "개정 노트는 근거가 아니라 검증 대상" 규칙과 그 주장을 Spec 본문에서 파일:행으로 대조하라는 지시를 포함한다. |
| AC-23 | T8 policy reviewer 절 | `CMD-2 -k test_readiness_is_advisory_not_authority_contract` | readiness 프롬프트 계약이 자신의 판정을 **참고용**으로 규정하고 Claude 공식 판정을 대체하지도 그 시작을 막지도 않는다고 명시하며, 설계 취향 감점을 금지한다. |
| AC-24 | T8 policy reviewer 절 | `CMD-2 -k test_readiness_prompt_carries_prior_findings` | `references/readiness-policy.md` 가 readiness 프롬프트 필수 요소로 같은 공식 라운드의 직전 readiness 시도 결과 경로와 직전 Claude 공식 리뷰 open findings 경로 둘 다를 지정하고, 각 finding 의 ID·severity·`required_resolution` 이 프롬프트에서 읽히도록 요구하며, 그 ID 가 **참조**이고 reviewer 자신의 finding 은 `READY-` 로 **발급**해야 한다는 R7.1 의 구분을 싣고, 그 전달이 R2.1 의 author 문맥 상속 금지와 구분된다는 것을 명시한다. |
| AC-25 | T9 policy 체크리스트 절 | `CMD-2 -k test_readiness_checklist_defines_eight_items` | `references/readiness-policy.md` 의 체크리스트 절이 C1~C8 여덟 항목을 각각 정의한다. |
| AC-26 | T3 결과 검증 | `CMD-2 -k test_readiness_verdict_requires_all_checks_and_no_high` | 체크리스트 여덟 항목이 모두 `pass` 또는 `not_applicable` 이고 Critical/High 가 0 인 결과만 `READY` 로 판정되며, `not_applicable` 은 충족으로 센다. |
| AC-27 | T3 결과 검증 | `CMD-2 -k test_readiness_verdict_blocks_on_failed_check_or_high_finding` | 체크리스트 항목 중 하나라도 `fail` 이면 판정이 `REVISE` 이고, 체크리스트가 전부 `pass` 여도 Critical 또는 High finding 이 하나라도 있으면 `READY` 가 아니다. |
| AC-28 | T9 policy 체크리스트 절 | [문서] `references/readiness-policy.md` § 체크리스트 | `references/readiness-policy.md` 의 C8 정의가 다섯을 모두 담는다 — 판정 대상을 프롬프트에 실린 findings 전문으로 한정하고 상태 기록을 훑어 대상을 유도하지 않는다는 것, 판정 대상 하나마다 `prior_findings` 항목을 정확히 하나 남긴다는 것, `judgement` 가 `partial` 이면 C8 이 미충족이라는 것, 프롬프트에 findings 가 없으면 `prior_findings` 가 빈 배열이고 항목이 자동 충족이라는 것, 참조 자리의 ID 는 원 접두(`SPEC-`·`READY-`)를 그대로 유지한다는 것. |
| AC-29 | T9 policy 체크리스트 절 | `CMD-2 -k test_readiness_score_is_advisory_contract` | `references/readiness-policy.md` 가 `score` 를 기록 전용 참고값으로 규정하고 판정·기록 거부·전이에 쓰지 않는다고 명시한다. |
| AC-30 | T6 record-readiness | `CMD-2 -k test_readiness_recording_ignores_score` | readiness 결과 검증과 기록 경로가 `score` 값을 읽지 않는다. 같은 입력의 `score` 를 0 과 100 으로 바꿔도 검증 결과와 기록된 `outcome` 이 같다. |
| AC-31 | T9 policy 체크리스트 절 | [문서] `references/readiness-policy.md` § 체크리스트 | 체크리스트 항목 정의에 설계 정합성·아키텍처 타당성·시간축 전개 판정이 포함되지 않는다는 것이 문서에 명시된다. |
| AC-32 | T6 record-readiness | `CMD-2 -k test_record_readiness_does_not_touch_rounds` | readiness 기록 추가가 `rounds` 의 어떤 값도 바꾸지 않는다. |
| AC-33 | T6 record-readiness | `CMD-2 -k test_review_recording_is_independent_of_readiness` | readiness 기록이 하나도 없는 상태와 마지막 readiness 결과가 `REVISE` 인 상태 양쪽에서 `record-review`·`record-review-unverified`·`record-review-error` 가 spec 리뷰를 거부하지 않는다. |
| AC-34 | T4 상태 필드 | `CMD-2 -k test_transitions_and_terminal_states_unchanged` | 이 작업이 `ALLOWED_TRANSITIONS` 의 엣지 집합과 `TERMINAL_STATES` 를 base revision 대비 바꾸지 않는다. |
| AC-35 | T9 policy 체크리스트 절 | [문서] `references/readiness-policy.md` § readiness 의 지위 | `references/readiness-policy.md` 가 readiness 는 어떤 상태 전이도 결정하지 않으며 공식 리뷰의 시작 조건이 아니라고 명시한다. |
| AC-36 | T6 record-readiness | `CMD-2 -k test_readiness_attempt_is_globally_monotonic` | readiness 기록 하나를 추가할 때마다 `attempt` 가 실행 전체에서 1씩 증가하며 `formal_round` 가 바뀌어도 초기화되지 않는다. |
| AC-37 | T2 결과 스키마 | `CMD-2 -k test_readiness_schema_attempt_has_no_maximum` | `schemas/readiness-result.schema.json` 의 `attempt` 에 `maximum` 제약이 없다. |
| AC-38 | T6 record-readiness | `CMD-2 -k test_record_readiness_has_no_attempt_limit` | 같은 `formal_round` 에 readiness 기록을 셋 이상 추가해도 `record-readiness` 가 시도 수를 이유로 거부하지 않는다. |
| AC-39 | T9 policy 체크리스트 절 | [문서] `references/readiness-policy.md` § readiness 의 지위 | `references/readiness-policy.md` 가 `READY` 이후 추가 시도 중단과, 라운드당 시도 한도를 코드로 강제하지 않고 비용 상한을 오케스트레이터 지시로 둔다는 것을 함께 명시한다. |
| AC-40 | T9 policy 체크리스트 절 | `CMD-2 -k test_readiness_evidence_attachment_contract` | `references/readiness-policy.md` 가 공식 리뷰 컨텍스트 첨부를 **저장소 근거 경로 둘**(마지막 readiness 결과 JSON, 그리고 미충족 체크리스트 항목과 잔여 finding 전문을 담은 `.claude/quality-state/<task-id>/readiness-evidence-spec-r<N>.md`)로 규정하고, 내용을 프롬프트에 인라인하지 않는다는 것과 그 근거(`SKILL.md` § Review invocation contract 의 입력 한정이 보존 대상이라는 것), 첨부가 리뷰어 판정을 구속하지 않는다는 것, 유효한 결과가 없을 때 그 사실을 요약 파일에 적는다는 것을 함께 적는다. |
| AC-41 | T9 policy 체크리스트 절 | `CMD-2 -k test_readiness_path_and_digest_precede_invocation` | `references/readiness-policy.md` 가 등록 digest 를 `artifacts[artifact]` 가 가리키는 파일의 현재 SHA-256 으로 정의하고, `artifact_digests` 를 이 대조에 쓰지 않는다고 명시하며, 경로 불일치 시 readiness 호출 자체를 하지 않는다는 확인을 호출 전 절차로 배치하고, 심사 시점 digest 를 프롬프트에 싣게 한다. |
| AC-42 | T6 record-readiness | `CMD-2 -k test_record_readiness_rejects_registered_digest_mismatch` | `--artifact-digest` 가 등록 digest 와 다르면 `record-readiness` 호출이 거부된다. |
| AC-43 | T6 record-readiness | `CMD-2 -k test_record_readiness_records_digest_mismatch` | `--invocation-status ok` 로 호출했을 때 결과의 `artifact_digest` 가 심사 시점 digest 와 다르면 유효 심사로 채택되지 않고 `digest_mismatch` 실패 기록이 남는다. |
| AC-44 | T9 policy 체크리스트 절 | [문서] `references/readiness-policy.md` § digest 대조 (절만 `sed` 로 잘라 `grep`) | digest 대조 실패와 경로 불일치가 단계를 바꾸지 않고 사용자 보고로 이어진다는 지시가 존재한다. |
| AC-45 | T6 record-readiness | `CMD-2 -k test_readiness_record_shape` | `outcome` 이 `recorded` 인 readiness 기록 하나의 키 집합이 R6.1 의 열두 필드와 **정확히 같고**(더도 덜도 아니다), `resolved_finding_ids` 의 값이 결과 JSON 의 같은 필드와 배열 단위로 같으며, 결과 JSON 에 `prior_findings` 가 있어도 상태 기록에는 그 키가 생기지 않는다. |
| AC-46 | T6 record-readiness | `CMD-2 -k test_readiness_formal_round_advances_after_review` | 공식 리뷰 기록 이후 추가되는 readiness 기록의 `formal_round` 가 `rounds[artifact] + 1` 과 같다. |
| AC-47 | T6 record-readiness | `CMD-2 -k test_record_readiness_rejects_mismatched_formal_round` | `record-readiness` 에 `rounds[artifact] + 1` 과 다른 `--formal-round` 를 주면 호출이 거부된다. |
| AC-48 | T6 record-readiness | `CMD-2 -k test_record_readiness_persists_review_time_digest` | 심사 시점 digest 가 readiness 기록의 `artifact_digest` 로 상태에 남고, 그 값이 호출 시점에 계산한 Spec 파일 digest 와 같다. |
| AC-49 | T4 상태 필드 | `CMD-2 -k test_new_state_has_exactly_two_new_fields` | 새 `init` 상태의 최상위 키 집합이 base revision 의 키 집합에 `readiness` 와 `draft_attempts` 둘만 더한 것과 정확히 같고, 두 필드의 값이 R6.2 가 정한 빈 값이다. |
| AC-50 | T6 record-readiness | `CMD-2 -k test_readiness_field_created_on_first_record` | `readiness` 필드가 없는 상태에 첫 `record-readiness` 를 적용하면 그때 필드가 생성된다. |
| AC-51 | T4 상태 필드 | `CMD-2 -k test_v1_state_without_new_fields_is_not_mutated_on_load` | R6.2 의 두 필드가 없는 schema v1 상태 파일을 읽을 수 있고, 읽기만으로는 어느 필드도 상태 파일에 생기지 않으며, readiness 미실행·author 미호출로 취급된다. |
| AC-52 | T4 상태 필드 | `CMD-2 -k test_resume_preserves_rounds_reviews_and_approval` | 진행 중 goal 을 재개해도 기존 `rounds`, `reviews`, `open_finding_ids`, `plan_approval`, `revision_checks` 가 보존되고 `plan_approval` 의 경로와 digest 가 재개 전과 바이트 단위로 같다. |
| AC-53 | T6 record-readiness | `CMD-2 -k test_readiness_records_survive_stage_exit` | `SPEC_PASSED`·`NEEDS_REDESIGN`·`BLOCKED`·`CANCELLED` 로 전이해도 readiness 기록과 `draft_attempts` 가 상태에 남는다. |
| AC-54 | T6 record-readiness | `CMD-2 -k test_readiness_record_outcome_enum` | readiness 기록의 `outcome` 이 `recorded`·`schema_invalid`·`digest_mismatch`·`invocation_failed` 네 값만 허용한다. |
| AC-55 | T6 record-readiness | `CMD-2 -k test_failed_readiness_attempt_record_shape` | 스키마 검증 실패·digest 불일치·호출 실패 각각의 기록에서 `verdict` 와 `score` 가 `null` 이고 `checklist`·`findings`·`resolved_finding_ids` 가 빈 배열이며 나머지 일곱 필드가 채워진다. |
| AC-56 | T6 record-readiness | `CMD-2 -k test_invocation_status_enum_is_enforced` | `--invocation-status` 에 `ok`·`failed` 밖의 값을 주면 호출이 거부되고, `record-readiness` 가 `outcome` 인자를 받지 않는다. |
| AC-57 | T6 record-readiness | `CMD-2 -k test_invocation_failure_is_recorded_and_requires_stderr_path` | `--invocation-status failed` 로 호출하면 결과 파일이 스키마를 통과하고 등록 digest 까지 가리키는 정상 결과여도 `invocation_failed` 로 기록되고 `result_path` 가 `--stderr-path` 값이 되며, `--stderr-path` 가 없거나 그 경로가 존재하지 않으면 호출이 거부된다. |
| AC-58 | T6 record-readiness | `CMD-2 -k test_schema_invalid_precedes_digest_mismatch` | `--invocation-status ok` 이고 결과가 스키마 위반과 digest 불일치를 동시에 만족하면 `schema_invalid` 로 기록된다. |
| AC-59 | T6 record-readiness | `CMD-2 -k test_readiness_commands_rejected_in_light_mode` | `light` 모드 상태에서 `record-readiness` 와 `record-draft-attempt` 두 명령이 모두 오류로 거부된다. |
| AC-60 | T3 결과 검증 | `CMD-2 -k test_issued_finding_ids_require_ready_prefix` | 발급 자리인 `findings[].id` 와 `blockers[]` 의 값이 하나라도 `^READY-` 를 만족하지 않으면 결과 검증이 실패한다. |
| AC-61 | T3 결과 검증 | `CMD-2 -k test_spec_prefix_is_reference_only_not_issuable` | 참조 자리(`prior_findings[].id`, `resolved_finding_ids`)는 `SPEC-` 와 `READY-` 두 접두를 모두 받아 검증을 통과하고, 같은 `SPEC-` 값이 발급 자리(`findings[].id`, `blockers`)에 있으면 검증이 실패한다. 세 조건을 한 결과 묶음으로 대조한다. |
| AC-62 | T8 policy reviewer 절 | [문서] `references/readiness-policy.md` § finding 식별자 | readiness 프롬프트 계약이 공식 finding 과의 대응 관계를 `description` 에 기록하도록 요구하고, 하나의 개정 주기 안에서 같은 물질적 문제에 같은 ID 를 유지하도록 요구한다. |
| AC-63 | T2 결과 스키마 | `CMD-2 -k test_readiness_schema_required_fields` | `schemas/readiness-result.schema.json` 의 `required` 가 R8.1 의 열세 필드를 정확히 포함하고 그 밖의 필드를 required 로 두지 않는다. |
| AC-64 | T2 결과 스키마 | `CMD-5` | `schemas/readiness-result.schema.json` 이 JSON 으로 파싱되고 최상위 `type` 이 `object` 이며 `additionalProperties` 가 `false` 다. |
| AC-65 | T2 결과 스키마 | `CMD-2 -k test_readiness_schema_digest_pattern_and_verdict_enum` | `artifact_digest` 가 소문자 SHA-256 64자 패턴으로 제약되고 `verdict` 가 `READY` 와 `REVISE` 두 값만 허용한다. |
| AC-66 | T8 policy reviewer 절 | `CMD-2 -k test_readiness_score_computation_instruction` | readiness 프롬프트 계약이 `score` 를 rubric 가중치로 실제 계산하도록 지시하고 "blocker 가 있다고 0 을 넣지 마라"를 포함한다. |
| AC-67 | T2 결과 스키마 | `CMD-2 -k test_readiness_schema_evidence_min_items` | `evidence` 최소 6건 요구가 스키마의 `minItems` 로 강제되고, 각 항목이 `claim`·`location`·`verified` 셋을 required 로 요구하며 그 밖의 키를 허용하지 않는다. |
| AC-68 | T3 결과 검증 | `CMD-2 -k test_readiness_schema_checklist_shape` | `checklist` 가 C1~C8 여덟 항목을 모두 포함하지 않으면 검증이 실패하고, 각 항목이 `id`·`status`·`evidence` 를 요구하며 `status` 가 `pass`·`fail`·`not_applicable` 셋만 허용한다. |
| AC-69 | T2 결과 스키마 | `CMD-2 -k test_readiness_schema_resolved_ids_and_namespace_patterns` | readiness 결과 스키마가 `resolved_finding_ids` 를 필수로 요구하고 그 값이 문자열 배열이며 빈 배열을 허용하고, R8.4 의 네 패턴 제약이 스키마에 존재한다 — `findings[].id` 와 `blockers[]` 에 `^READY-`, `prior_findings[].id` 와 `resolved_finding_ids[]` 에 `^(READY-|SPEC-)`. |
| AC-70 | T6 record-readiness | `CMD-2 -k test_invalid_readiness_result_is_recorded_as_schema_invalid` | `--invocation-status ok` 로 호출했을 때 스키마 검증에 실패한 결과가 유효 심사로 채택되지 않고 `schema_invalid` 실패 기록이 남는다. |
| AC-71 | T12 SKILL.md | `CMD-3` | `SKILL.md` 파일 전체가 500행 미만이다. |
| AC-72 | T12 SKILL.md | `CMD-2 -k test_readiness_policy_is_referenced_from_skill` | `references/readiness-policy.md` 가 존재하고 `SKILL.md` 의 참조 경로 목록에 등재된다. |
| AC-73 | T11 spec 템플릿 | `CMD-2 -k test_spec_template_has_traceability_and_command_table` | `templates/spec.md` 에 `## Requirements traceability` 절이 `## Acceptance criteria` 와 `## Architecture` 사이에 있고, `### 판정 명령 표` 절이 `## Test strategy` 아래 첫 하위 절로 있다. 헤딩 수준과 앞뒤 절을 모두 판정한다. |
| AC-74 | T13 유지보수 문서 | `CMD-2 -k test_maintenance_doc_covers_readiness` | `docs/quality-goal-maintenance.md` 에 readiness 점검 항목(`codex exec` 플래그, readiness 결과 스키마, author·reviewer 라우팅 모델, 두 참조 파일의 동기화)이 존재한다. |
| AC-75 | T13 유지보수 문서 | `CMD-2 -k test_maintenance_doc_replaces_test_section_with_command_table` | `docs/quality-goal-maintenance.md` 에 `## 판정 명령 표` 절이 존재하고 `## 결정적 테스트` 절이 존재하지 않으며, 새 절이 CMD-1~CMD-7 일곱 행을 모두 싣고 그 절이 판정 명령 표의 정본이라는 것이 문서에 명시된다. |
| AC-76 | T13 유지보수 문서 | [문서] `docs/quality-goal-maintenance.md` § 판정 명령 표 | `docs/quality-goal-maintenance.md` 의 판정 명령 표가 테스트 스위트의 최소 Python 버전을 3.12 로 명시하고 그 두 근거(`enterContext`, `NO TESTS RAN` 종료 코드 5)를 표 **바로 아래**(표와 그 문언 사이에 다른 헤딩이 없음)에 함께 싣는다. |
| AC-77 | T14 회귀 확인 | `CMD-1` | Python 3.12 이상에서 전체 테스트가 통과한다. |
| AC-78 | T14 회귀 확인 | `CMD-6` | base revision 의 테스트 이름 집합이 현재 테스트 이름 집합의 부분집합이다. 기존 테스트가 삭제되거나 이름이 바뀌면 실패한다. |
| AC-79 | T4 상태 필드 | `CMD-2 -k test_round_limits_and_required_checks_unchanged` | `ROUND_LIMITS` 가 `{"spec": 3, "plan": 2, "code": 3}` 그대로이고 `REQUIRED_CHECKS` 가 변경되지 않는다. |
| AC-80 | T14 회귀 확인 | `CMD-4` | CMD-4 의 보존 대상 여덟 절이 base revision 대비 바이트 단위로 같다. |
| AC-81 | T14 회귀 확인 | `CMD-2 -k test_formal_pass_gate_threshold_unchanged` | 공식 Claude 게이트의 점수 임계 85 가 `references/spec-rubric.md` 와 `references/plan-rubric.md` 에서 변경되지 않는다. |
| AC-82 | T12 SKILL.md | `CMD-2 -k test_skill_version_bumped_for_contract_extension` | `SKILL.md` frontmatter 의 `version` 이 5.0.0 보다 크고 MINOR 이상 증가한다. |
| AC-83 | T10 model-routing | `CMD-2 -k test_model_routing_includes_author_and_readiness_rows` | `references/model-routing.md` 의 라우트 표에 Spec author(standard `gpt-5.6-terra` high, strict `gpt-5.6-sol` high)와 readiness reviewer(fresh `gpt-5.6-sol` high) 행이 존재한다. |
| AC-84 | T7 policy author 절 | `CMD-2 -k test_routing_and_policy_split_is_documented` | `references/model-routing.md` 와 `references/readiness-policy.md` 의 역할 분담이 문서에 명시된다. |
| AC-85 | T1 판정 스크립트 | `CMD-7` | `tests/assert_python_version.py` 가 3.12 이상에서 성공하고 3.12 미만에서 비정상 종료한다. |
| AC-86 | T13 유지보수 문서 | `CMD-2 -k test_version_guard_is_shared_not_inlined` | `docs/quality-goal-maintenance.md` § 판정 명령 표의 CMD-1 과 CMD-2 정의가 `tests/assert_python_version.py` 호출을 포함하고, 버전 비교식을 명령 안에 인라인으로 복제하지 않는다. |
| AC-87 | T1 판정 스크립트 | `CMD-2 -k test_judgement_scripts_exist_and_are_not_collected` | R9.8 의 세 스크립트가 존재하고, 세 파일명이 모두 `test_` 로 시작하지 않아 `unittest discover -p 'test_*.py'` 의 수집 대상에서 빠진다. |
| AC-88 | T3 결과 검증 | `CMD-2 -k test_prior_findings_shape_and_resolved_set_equality` | `prior_findings` 가 항목마다 `id`·`source`·`judgement`·`evidence` 를 요구하고 `source` 는 `readiness`·`formal`, `judgement` 는 `resolved`·`unresolved`·`partial` 만 허용하며 빈 배열이 허용된다. 그리고 `resolved_finding_ids` 의 값 집합이 `judgement` 가 `resolved` 인 항목의 ID 집합과 다르면 검증이 실패한다. |
| AC-89 | T8 policy reviewer 절 | `CMD-2 -k test_readiness_unverified_evidence_reason_contract` | `references/readiness-policy.md` 의 readiness 프롬프트 계약이 `verified` 가 `true` 인 근거의 `location` 을 `<경로>:<행>` 형식으로 쓰게 하고 `false` 인 근거의 `location` 에는 확인하지 못한 사유를 적게 한다는 문언을 함께 담는다. |
| AC-90 | T1 판정 스크립트 | `CMD-2 -k test_python_version_guard_boundary_and_main_delegates` | `tests/assert_python_version.py` 가 `is_supported(version_info)` 를 노출해 `(3, 11, 9)` 에 `False` 를, `(3, 12, 0)` 과 `(3, 14, 7)` 에 `True` 를 반환하고, 그 모듈의 `__main__` 분기가 `is_supported` 호출로만 판정한다(모듈 어디에도 `version_info` 를 상수와 직접 비교하는 식이 그 함수 밖에 없다). |

## strict 전용 블록을 제거한 근거

이 Plan 은 standard 모드 산출물이므로 `templates/plan.md` 의 strict 전용 블록을 제거했다. 본문에 그 주석 쌍이 남아 있지 않다. 제거한 여섯 소절이 이 작업에 적용되지 않는 이유는 Spec § Decisions D11 과 같다 — 신뢰 경계를 넘는 입력이 없고, 권한 주체나 테넌트 개념이 없으며, 데이터 마이그레이션·백필이 없고(호환성은 § Rollout and rollback 이 다룬다), 상시 실행 구성 요소가 없어 관측 대상이 없고, 고위험 경로가 없어 별도 E2E 가 없으며, 프로덕션 대상이 존재하지 않는다. 배포본 `~/.claude/skills/quality-goal/` 을 이 작업이 갱신하지 않는다는 것은 § Global constraints 1 과 § Rollout and rollback 에 명시했다.
