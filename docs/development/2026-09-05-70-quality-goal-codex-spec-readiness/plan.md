# Quality Goal Implementation Plan

- Task ID: 20260906T100138Z-70-quality-goal-spec-단계에-codex-author-fr-7ec207bb
- Mode: standard
- Status: PLAN_REVIEW
- Created: 2026-09-06
- Updated: 2026-09-06
- Source goal: #70 quality-goal Spec 단계에 Codex author + fresh Codex 체크리스트 readiness 사전 심사 파이프라인 추가 (1단계)

## Spec link

- 승인 대상 Spec: `docs/development/2026-09-05-70-quality-goal-codex-spec-readiness/spec.md`
- SHA-256: `025a85bf092834172c120d449376a91c763f2c438479d18b0012322f3c9a12ae`
- 공식 리뷰: 라운드 3, score 92, PASS, blocker 0 (`.claude/quality-state/<task-id>/spec-review-r3.json`)
- 요구사항 69건(R1.1~R9.10), 수용 기준 113건(AC-1~AC-113), 추적표 69행

이 Plan 은 그 Spec 의 AC-1~AC-113 전부를 태스크와 검증 명령에 매핑한다.

## Global constraints

1. **chezmoi source 만 바꾼다.** 대상은 `dot_claude/skills/quality-goal/` 하위와 `docs/quality-goal-maintenance.md` 다. `chezmoi apply` 를 실행하지 않는다 — 다른 세션이 배포본 `~/.claude/skills/quality-goal/` 을 실행 중이다. 배포는 사용자가 별도로 한다.
2. **초기 dirty 경로를 보존한다.** 상태의 `initial_dirty_paths` 는 `.prior-art/` 와 `docs/development/2026-09-05-70-quality-goal-codex-spec-readiness/` 둘이다. 두 경로 모두 구현 태스크가 읽기만 하고 수정·되돌리기·커밋 대상 포함을 하지 않는다. 뒤엣것이 초기 dirty 경로가 된 이유는 이번 실행이 직전 실행의 Spec·Plan 을 재사용해 baseline 시점에 이미 존재했기 때문이며, 그 디렉터리에 쓰는 주체는 구현 태스크가 아니라 오케스트레이터다(T17 의 허용 목록 3번과 같은 뜻).
3. **Python 3.12 이상에서 작업한다.** `python3` 가 무엇으로 풀리는지는 셸에 따라 다르다 — 로그인 셸(`zsh -lc`)에서는 `/usr/bin/python3` 3.9.6 이고, PATH 에 homebrew 가 앞선 셸에서는 `/opt/homebrew/bin/python3` 3.14.7 이다. 따라서 모든 판정 명령은 `python3` 를 직접 부르지 않고 § Verification commands 가 정의한 `QG_PY` 를 쓴다. `QG_PY` 는 3.12 이상 인터프리터를 탐색해 고르고, 찾지 못하면 명령이 실패한다(Spec R9.9 의 '명령 자체가 전제를 확인한다').
4. **기존 계약을 건드리지 않는다.** `SKILL.md` 의 `### Plan`, `### Approval`, `### Implementation`, `### Code review`, `## Independent verification`, `## Safety rules`, `## Review invocation contract`, `## Codex invocation contract` 여덟 절과 `ROUND_LIMITS`, `REQUIRED_CHECKS`, 공식 게이트 임계 85 는 변경 금지다(Spec R9.6).
5. **`SKILL.md` 는 파일 전체가 500행 미만이어야 한다.** 현재 393행이므로 추가 여유는 106행이다. readiness 절차의 상세는 `references/readiness-policy.md` 로 뺀다(Spec R9.1·R9.2).
6. **테스트 우선.** 모든 행동 변경은 실패하는 테스트를 먼저 기록하고, 최소 구현 뒤 통과를 기록한다.
7. **기존 테스트를 지우거나 이름을 바꾸지 않는다.** 310개 테스트 이름 집합이 부분집합으로 보존돼야 한다(CMD-6).
8. **신설 식별자에는 거부 계약의 대칭을 먼저 확인한다.** 이 Plan 의 T4·T6·T8·T9·T11 은 새 stage·서브커맨드·엣지·입력을 도입한다. 각 태스크는 구현 전에 `quality_state.py` 에서 같은 부류의 기존 가드를 `grep` 으로 찾아 그 형태를 따른다. 근거: Spec 라운드 1 의 해소가 라운드 2 의 blocker(SPEC-17)를 만들었고, 그 원인이 "신설 식별자의 조건을 서술로만 두는 것" 이었다. 기존 선례는 `approve_plan` 의 stage 가드(`quality_state.py:519-520`), `CLASSIFIED → AWAITING_PLAN_APPROVAL` 의 모드 조건(`380-383`), `SPEC_REVIEW → SPEC_PASSED` 의 리뷰 조건(`390-424`)이다.
9. **커밋·푸시·머지·배포를 하지 않는다.** 이 Plan 의 어떤 태스크도 git 쓰기 명령을 포함하지 않는다.
10. **Codex 호출 금지 플래그.** 구현 중 Codex 를 부른다면 `--skip-git-repo-check`, `--dangerously-bypass-approvals-and-sandbox`, `--dangerously-bypass-hook-trust`, `--approve-for-me`, `--ignore-rules`, `--ignore-user-config`, `--add-dir`, `--yolo` 를 쓰지 않는다(Spec R1.4).

## File map

| 파일 | 작업 | 책임 | 영향 인터페이스 |
|---|---|---|---|
| `dot_claude/skills/quality-goal/tests/assert_python_version.py` | 신설 | 인터프리터가 3.12 이상인지 단언 | CMD-1·CMD-2·CMD-7 이 호출 |
| `dot_claude/skills/quality-goal/tests/assert_preserved_sections.py` | 신설 | `SKILL.md` 의 보존 대상 여덟 절을 base revision 과 비교 | CMD-4 |
| `dot_claude/skills/quality-goal/tests/assert_tests_preserved.py` | 신설 | base revision 의 테스트 이름 집합이 부분집합인지 확인 | CMD-6 |
| `dot_claude/skills/quality-goal/schemas/readiness-result.schema.json` | 신설 | readiness 결과 구조 계약 | `codex exec --output-schema`, `validate_readiness_result` |
| `dot_claude/skills/quality-goal/scripts/validate_review.py` | 수정 | `validate_readiness_result` 추가. 기존 `validate_review`·`REQUIRED_CHECKS` 는 불변 | `quality_state.record_readiness` 가 호출 |
| `dot_claude/skills/quality-goal/scripts/quality_state.py` | 수정 | 상태 필드 셋, 서브커맨드 넷, stage 하나, 전이 가드 둘, `status_reason` 분기 확장, `record-review` 게이트 강제. v5.0.0 의 `revision_checks` 키·`record_review` 시그니처·스냅숏 저장 분기는 불변 | CLI 전체 |
| `dot_claude/skills/quality-goal/references/readiness-policy.md` | 신설 | author·readiness 프롬프트 계약, 호출 템플릿, 체크리스트 C1~C8 정의, 반복·탈출 규칙, 금지 플래그 열거 | `SKILL.md` 가 참조 |
| `dot_claude/skills/quality-goal/references/model-routing.md` | 수정 | author·readiness 라우트 행 셋과 두 호출 템플릿 추가. 기존 라우트 행과 구현 라운드 템플릿·프리플라이트 블록은 불변 | `readiness-policy.md` 가 인용 |
| `dot_claude/skills/quality-goal/templates/spec.md` | 수정 | 요구사항 추적표 절과 판정 명령 표 절 추가 | C3·C4·C5·C7 의 파싱 앵커 |
| `dot_claude/skills/quality-goal/SKILL.md` | 수정 | Spec 단계 절차, Stage table 행, 참조 경로 목록, frontmatter `version` | 오케스트레이터 지시 |
| `docs/quality-goal-maintenance.md` | 수정 | readiness 점검 항목과 두 reference 파일 동기화 항목 추가 | 유지보수 runbook |
| `dot_claude/skills/quality-goal/tests/test_quality_state.py` | 수정 | 상태·게이트·전이 테스트 추가 | CMD-1·CMD-2 |
| `dot_claude/skills/quality-goal/tests/test_validate_review.py` | 수정 | readiness 결과 검증 테스트 추가 | CMD-1·CMD-2 |
| `dot_claude/skills/quality-goal/tests/test_content_contracts.py` | 수정 | 문서 계약 테스트 추가 | CMD-1·CMD-2 |
| `dot_claude/skills/quality-goal/tests/fixtures/readiness-*.json` | 신설 | READY / 체크리스트 1개 실패 / High 포함 / 스키마 위반 결과와 v1 상태 픽스처 | 위 세 테스트 파일(수정 대상) |

`.gitignore` 는 손대지 않는다 — `.claude/quality-state/` 는 이미 25행으로 무시된다.

## Task dependencies

```text
T1 (판정 스크립트 3종)
 └─ 이후 모든 태스크의 검증 기반. 가장 먼저.

T2 (readiness 결과 스키마)
 └─ T3 (validate_readiness_result) ─┐
                                     │
T4 (상태 필드 3종 + v1 호환)         │
 ├─ T5 (record-draft-attempt)        │
 └─ T7 (readiness-gate) ─────────────┤
      └─ T6 (record-readiness) ──────┘
           └─ T8 (새 stage + 전이 가드)
                └─ T9 (resume-readiness)
                     └─ T10 (record-review 게이트 강제)
                          └─ T11 (light 모드 거부, 네 명령 확정 후)

T12 (spec 템플릿) ─ 독립
T13 (readiness-policy.md) ─ T2~T11 의 계약이 확정된 뒤 문서화
T14 (model-routing.md) ─ 독립, T13 이 인용
T15 (SKILL.md) ─ T13 완료 후 (참조 경로가 존재해야 함)
T16 (유지보수 문서) ─ T13·T14 완료 후
T17 (회귀 확인) ─ 전부 완료 후
```

T4 는 T5~T11 전부의 선행이다. **T7 은 T6 보다 먼저다** — T6 이 소유한 AC-37·AC-57·AC-100 의 기대 결과가 모두 "게이트의 시도 횟수가 1 증가한다" 이므로 `readiness-gate` 없이는 T6 완료 시점에 통과 확인을 실행할 수 없다. 게이트는 상태를 읽는 순수 함수라 기록 명령 없이도 구현 가능하며, 그 테스트는 상태 픽스처를 직접 만들어 검증한다. T8 은 T7 이 반환하는 `HOLD` 를 전이 조건으로 쓰므로 T7 뒤여야 한다. T10 은 T7 의 게이트 결과를 요구하므로 T7·T8·T9 뒤다. T13 은 T2~T11 이 확정한 계약을 문서로 옮기므로 그 뒤다. 태스크 번호는 문서 작성 순서이고 **수행 순서는 이 그래프**다 — T1, T2, T3, T4, T5, T7, T6, T8, T9, T10, T11, T12, T13, T14, T15, T16, T17.

## Tasks

**검증 수단의 세 종류.** ① 97개는 새 테스트 이름으로 판정한다 — 소유 태스크가 그 테스트를 **작성**하고(실패 확인 단계) 통과시킨다(통과 확인 단계). ② 아홉 개(AC-58·62·66·68·77·78·85·86·102)는 새 테스트를 만들지 않고 § Verification commands 의 명령(CMD-1·3·4·5·6·7)을 그대로 돌려 판정한다. ③ 일곱 개(AC-27·34·36·38·49·50·84)는 Spec 이 `[문서]` 로 표기한 것이라 해당 문서를 `grep` 하는 명령으로 판정하며, 그 명령은 소유 태스크의 통과 확인에 그대로 적혀 있다 — 앞의 여섯은 T13 이, AC-84 는 T16 이 소유한다. 세 종류를 합치면 97 + 9 + 7 = 113 으로 Spec 의 AC 총수와 같다. 태스크 본문의 통과 확인은 세 종류를 나눠 적는다.

**AC 소유권 원칙.** 각 AC 는 **그 AC 의 통과 확인을 그 태스크가 끝난 시점에 실제로 실행할 수 있는** 가장 이른 태스크가 소유한다. 두 명령의 상호작용을 보는 AC 는 뒤에 오는 명령의 태스크가 갖는다 — 필드 생성 시점을 보는 AC-89·93 은 T6·T5, `rounds` 불변을 보는 AC-33·41 은 `record-readiness` 를 구현하는 T6, artifact 별 분리를 보는 AC-76 은 `record-draft-attempt` 를 구현하는 T5 다. `status_reason` 의 설정과 해제를 함께 보는 AC-111 은 해제를 구현하는 T9 가, 두 문서를 함께 보는 AC-19 는 나중에 오는 `SKILL.md` 태스크(T15)가, 그 밖의 문서 문언을 보는 AC-20·24·36·101·104 는 그 문서를 쓰는 태스크(T13·T16)가 소유한다. 이 원칙 덕분에 태스크를 § Task dependencies 순서대로 하나씩 완료하면 그 시점에 소유 AC 의 통과 확인이 실제로 실행 가능하다.

각 태스크는 test-first 다 — 실패하는 검증을 먼저 기록하고, 최소 구현 뒤 통과를 기록한다. 태스크 본문의 `CMD-1`~`CMD-7` 은 § Verification commands 표의 명령을 그대로 가리키며, 그 표가 정의한 `QG_PY`·`QG_BASE` 를 먼저 셸에 설정한 뒤 쓴다. 이 Plan 의 어떤 명령도 `python3` 를 직접 부르지 않는다(§ Global constraints 3).

### T1. 판정 스크립트 세 개를 만든다

대상 AC: AC-86

- **실패 확인**: 세 명령이 모두 `can't open file` 로 비정상 종료한다 — `"$QG_PY" dot_claude/skills/quality-goal/tests/assert_python_version.py`, `"$QG_PY" dot_claude/skills/quality-goal/tests/assert_preserved_sections.py`, `"$QG_PY" dot_claude/skills/quality-goal/tests/assert_tests_preserved.py`.
- **구현**: 세 파일을 만든다.
  - `assert_python_version.py`: `sys.version_info >= (3, 12)` 가 아니면 종료 코드 1, 맞으면 0.
  - `assert_preserved_sections.py`: base revision 을 첫 인자로 받아 `git show <인자>:dot_claude/skills/quality-goal/SKILL.md` 를 읽고 현재 파일과 함께 `^#{2,3} ` 헤딩으로 쪼갠 뒤, 상수로 둔 여덟 절 이름의 본문이 같은지 단언하고 `보존 대상 절 불변` 을 출력한다. 여덟 이름은 Spec § Test strategy CMD-4 상세가 열거한 것 그대로다.
  - `assert_tests_preserved.py`: base revision 을 첫 인자로 받아 그 리비전의 `tests/test_*.py` 네 파일(`test_content_contracts.py`, `test_quality_state.py`, `test_validate_review.py`, `test_revision_check.py`)에서 `^\s*def (test_\w+)` 이름을 모아 현재 집합의 부분집합인지 단언하고 `기존 테스트 보존` 을 출력한다.
- **통과 확인**: 명령으로 판정하는 AC — `CMD-4 + CMD-6 + CMD-7`(AC-86). 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.
- **주의**: 세 파일명이 `test_` 로 시작하지 않아야 `unittest discover -p 'test_*.py'` 가 수집하지 않는다. `CMD-1` 의 실행 테스트 수가 310 에서 늘지 않는 것으로 확인한다.

### T2. readiness 결과 스키마를 만든다

대상 AC: AC-15, AC-25, AC-30, AC-51, AC-53, AC-54, AC-55, AC-56, AC-68

- **실패 확인**: `CMD-5` → `FileNotFoundError`. 이 태스크가 소유한 AC 의 테스트 8개를 먼저 작성한다 — `test_readiness_schema_uses_type_not_const`(AC-15), `test_readiness_schema_checklist_shape`(AC-25), `test_readiness_schema_attempt_has_no_maximum`(AC-30), `test_readiness_schema_required_fields`(AC-51), `test_readiness_schema_evidence_min_items`(AC-53), `test_readiness_schema_digest_pattern`(AC-54), `test_readiness_schema_verdict_enum`(AC-55), `test_readiness_schema_requires_all_eight_checks`(AC-56). 작성 직후 각각을 `CMD-2 -k <이름>` 으로 돌리면 전부 실패한다.
- **구현**: `schemas/readiness-result.schema.json` 을 만든다. 최상위 `type: object`, `additionalProperties: false`. `required` 는 `artifact`, `attempt`, `formal_round`, `score`, `verdict`, `checklist`, `blockers`, `findings`, `evidence`, `required_next_action`, `artifact_digest` 열한 개. `verdict` 는 `{"type": "string", "enum": ["READY", "REVISE"]}`. `artifact` 는 `{"type": "string", "enum": ["spec"]}` — `const` 를 쓰지 않는다(Spec R2.4). `attempt` 는 `{"type": "integer", "minimum": 1}` 이고 `maximum` 을 두지 않는다. `artifact_digest` 는 `{"type": "string", "pattern": "^[0-9a-f]{64}$"}`. `evidence` 는 `minItems: 6` 이고 각 항목이 `claim`·`location` 을 required 로 요구한다. `checklist` 는 `minItems: 8`, `maxItems: 8` 이고 각 항목이 `id`·`status`·`evidence` 를 요구하며 `status` enum 은 `pass`·`fail`·`not_applicable` 다.
- **통과 확인**: 소유 AC 의 테스트 8개를 `CMD-2 -k <이름>` 으로 하나씩 돌려 전부 통과시킨다 — `test_readiness_schema_uses_type_not_const`(AC-15), `test_readiness_schema_checklist_shape`(AC-25), `test_readiness_schema_attempt_has_no_maximum`(AC-30), `test_readiness_schema_required_fields`(AC-51), `test_readiness_schema_evidence_min_items`(AC-53), `test_readiness_schema_digest_pattern`(AC-54), `test_readiness_schema_verdict_enum`(AC-55), `test_readiness_schema_requires_all_eight_checks`(AC-56). 명령으로 판정하는 AC — `CMD-5`(AC-68). 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.

### T3. `validate_review.py` 에 readiness 결과 검증을 더한다

대상 AC: AC-47, AC-48, AC-52

- **선행 grep**: `grep -n "def validate_review\|REQUIRED_CHECKS" dot_claude/skills/quality-goal/scripts/validate_review.py` — 기존 함수와 상수를 건드리지 않을 경계를 확인한다.
- **실패 확인**: `CMD-2 test_readiness_finding_id_namespace` → `ImportError`. 이 태스크가 소유한 AC 의 테스트 3개를 먼저 작성한다 — `test_readiness_finding_id_namespace`(AC-47), `test_readiness_rejects_spec_namespace_ids`(AC-48), `test_readiness_score_computation_instruction`(AC-52). 작성 직후 각각을 `CMD-2 -k <이름>` 으로 돌리면 전부 실패한다.
- **구현**: `validate_readiness_result(result, expected_digest)` 를 추가한다. 스키마 필수 필드 존재, finding id 가 `READY-` 로 시작하는지, `SPEC-` 로 시작하는 id 가 없는지, `evidence` 6건 이상, `checklist` 여덟 항목, `blockers` 가 Critical/High finding id 집합과 일치하는지를 오류 목록으로 반환한다. 기존 `validate_review` 와 `REQUIRED_CHECKS` 는 한 줄도 바꾸지 않는다.
- **통과 확인**: 소유 AC 의 테스트 3개를 `CMD-2 -k <이름>` 으로 하나씩 돌려 전부 통과시킨다 — `test_readiness_finding_id_namespace`(AC-47), `test_readiness_rejects_spec_namespace_ids`(AC-48), `test_readiness_score_computation_instruction`(AC-52). 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.

### T4. 상태에 세 필드를 더하고 v1 호환을 지킨다

대상 AC: AC-40, AC-42, AC-43, AC-90

- **선행 grep**: `grep -n "def new_state\|def load_state\|schema_version" dot_claude/skills/quality-goal/scripts/quality_state.py` — `load_state` 가 `schema_version != 1` 을 거부하는 것(264-265행)을 확인하고 그 값을 바꾸지 않는다. 같은 grep 으로 `new_state` 가 v5.0.0 에서 이미 만드는 `revision_checks` 키를 확인한다.
- **실패 확인**: `CMD-2 test_new_state_has_draft_attempts` → `KeyError`. 이 태스크가 소유한 AC 의 테스트 3개를 먼저 작성한다 — `test_new_state_has_draft_attempts`(AC-40), `test_v1_state_without_readiness_fields_is_not_mutated_on_load`(AC-42), `test_resume_preserves_rounds_reviews_and_approval`(AC-43·AC-90). 작성 직후 각각을 `CMD-2 -k <이름>` 으로 돌리면 전부 실패한다.
- **구현**: `new_state` 가 `readiness: {"spec": [], "plan": []}`, `draft_attempts: {"spec": 0, "plan": 0}`, `readiness_decisions: []` 셋을 **추가로** 만든다. 기존 키를 하나도 지우지 않으며, v5.0.0 이 만드는 `revision_checks: {"spec": [], "plan": []}` 도 그대로 둔다. `load_state` 는 그 필드가 없어도 읽고, **읽기만으로 필드를 만들지 않는다**. 각 필드는 그것을 처음 쓰는 명령이 만든다. `schema_version` 은 1 을 유지한다.
- **통과 확인**: 소유 AC 의 테스트 3개를 `CMD-2 -k <이름>` 으로 하나씩 돌려 전부 통과시킨다 — `test_new_state_has_draft_attempts`(AC-40), `test_v1_state_without_readiness_fields_is_not_mutated_on_load`(AC-42), `test_resume_preserves_rounds_reviews_and_approval`(AC-43·AC-90). 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.
- **픽스처**: readiness 필드가 없는 schema v1 상태 파일을 `tests/fixtures/state-v1-without-readiness.json` 으로 둔다.

### T5. `record-draft-attempt` 를 만든다

대상 AC: AC-9, AC-76, AC-93

- **실패 확인**: `CMD-2 test_record_draft_attempt_increments_only_draft_attempts` → `StateError: invalid choice`. 이 태스크가 소유한 AC 의 테스트 3개를 먼저 작성한다 — `test_record_draft_attempt_increments_only_draft_attempts`(AC-9), `test_record_draft_attempt_is_per_artifact`(AC-76), `test_draft_attempts_created_on_first_record`(AC-93). 작성 직후 각각을 `CMD-2 -k <이름>` 으로 돌리면 전부 실패한다.
- **구현**: 서브커맨드를 더한다. `draft_attempts[artifact] += 1` 만 하고 `rounds` 를 건드리지 않는다. `draft_attempts` 가 없으면 이때 만든다.
- **통과 확인**: 소유 AC 의 테스트 3개를 `CMD-2 -k <이름>` 으로 하나씩 돌려 전부 통과시킨다 — `test_record_draft_attempt_increments_only_draft_attempts`(AC-9), `test_record_draft_attempt_is_per_artifact`(AC-76), `test_draft_attempts_created_on_first_record`(AC-93). 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.

### T6. `record-readiness` 를 만든다

대상 AC: AC-33, AC-35, AC-37, AC-39, AC-41, AC-45, AC-57, AC-74, AC-80, AC-81, AC-88, AC-89, AC-97, AC-100, AC-109, AC-112, AC-113

- **선행 grep**: `grep -n "artifact digest mismatch\|expected_round = rounds" dot_claude/skills/quality-goal/scripts/quality_state.py` — `record_review` 가 digest 를 대조하는 방식(599-612행)과 `rounds[artifact] + 1` 유도식(589-592행)을 확인해 같은 형태를 쓴다.
- **실패 확인**: `CMD-2 test_record_readiness_rejects_path_mismatch` → `StateError: invalid choice`. 이 태스크가 소유한 AC 의 테스트 17개를 먼저 작성한다 — `test_record_readiness_does_not_touch_rounds`(AC-33), `test_record_readiness_rejects_path_mismatch`(AC-35), `test_record_readiness_rejects_digest_mismatch_and_counts_attempt`(AC-37), `test_readiness_record_shape`(AC-39), `test_readiness_and_draft_attempts_leave_rounds_unchanged`(AC-41), `test_readiness_formal_round_advances_after_review`(AC-45), `test_invalid_readiness_result_counts_attempt_and_is_not_recorded`(AC-57), `test_readiness_attempt_is_globally_monotonic`(AC-74), `test_readiness_record_outcome_enum`(AC-80), `test_failed_readiness_attempt_is_recorded_as_empty_outcome`(AC-81), `test_record_readiness_persists_review_time_digest`(AC-88), `test_readiness_fields_created_on_first_record`(AC-89), `test_record_readiness_rejects_mismatched_formal_round`(AC-97), `test_invocation_failure_is_recorded_and_counts_attempt`(AC-100), `test_schema_invalid_precedes_digest_mismatch`(AC-109), `test_invocation_status_enum_is_enforced`(AC-112), `test_failed_status_requires_existing_stderr_path`(AC-113). 작성 직후 각각을 `CMD-2 -k <이름>` 으로 돌리면 전부 실패한다.
- **구현**: 입력은 `--state`, `--artifact`, `--result`, `--artifact-digest`, `--formal-round`, `--reviewer-model`, `--invocation-status`, `--stderr-path` 다. 거부 계약 넷을 먼저 건다 — 대상 경로가 `artifacts[artifact]` 와 다르면 거부, `--artifact-digest` 가 그 파일의 현재 SHA-256 과 다르면 거부, `--formal-round` 가 `rounds[artifact] + 1` 과 다르면 거부, `--invocation-status` 가 `ok`·`failed` 밖이거나 `failed` 인데 `--stderr-path` 가 없거나 존재하지 않으면 거부. 그다음 `outcome` 을 순서대로 정한다: `failed` → `invocation_failed`, 그 외에는 스키마 검증 실패 → `schema_invalid`, digest 불일치 → `digest_mismatch`, 모두 통과 → `recorded`. 실패 기록은 `verdict`·`score` 를 `null`, `checklist`·`findings` 를 빈 배열로 둔다. `attempt` 는 `readiness[artifact]` 길이 + 1 로 전역 단조 증가시킨다. `rounds` 를 건드리지 않는다.
- **통과 확인**: 소유 AC 의 테스트 17개를 `CMD-2 -k <이름>` 으로 하나씩 돌려 전부 통과시킨다 — `test_record_readiness_does_not_touch_rounds`(AC-33), `test_record_readiness_rejects_path_mismatch`(AC-35), `test_record_readiness_rejects_digest_mismatch_and_counts_attempt`(AC-37), `test_readiness_record_shape`(AC-39), `test_readiness_and_draft_attempts_leave_rounds_unchanged`(AC-41), `test_readiness_formal_round_advances_after_review`(AC-45), `test_invalid_readiness_result_counts_attempt_and_is_not_recorded`(AC-57), `test_readiness_attempt_is_globally_monotonic`(AC-74), `test_readiness_record_outcome_enum`(AC-80), `test_failed_readiness_attempt_is_recorded_as_empty_outcome`(AC-81), `test_record_readiness_persists_review_time_digest`(AC-88), `test_readiness_fields_created_on_first_record`(AC-89), `test_record_readiness_rejects_mismatched_formal_round`(AC-97), `test_invocation_failure_is_recorded_and_counts_attempt`(AC-100), `test_schema_invalid_precedes_digest_mismatch`(AC-109), `test_invocation_status_enum_is_enforced`(AC-112), `test_failed_status_requires_existing_stderr_path`(AC-113). 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.
- **픽스처**: `readiness-ready.json`, `readiness-one-check-failed.json`, `readiness-high-finding.json`, `readiness-schema-invalid.json`.

### T7. `readiness-gate` 를 만든다

대상 AC: AC-21, AC-22, AC-23, AC-26, AC-28, AC-29, AC-44, AC-82, AC-83, AC-91, AC-98, AC-99

- **선행 grep**: `grep -n "def _validate_transition_request" -A 40 dot_claude/skills/quality-goal/scripts/quality_state.py` — 기존 게이트가 상태에서 값을 유도하는 방식을 확인한다.
- **실패 확인**: `CMD-2 test_readiness_gate_requires_all_checks_and_no_high` → `StateError: invalid choice`. 이 태스크가 소유한 AC 의 테스트 12개를 먼저 작성한다 — `test_readiness_gate_requires_all_checks_and_no_high`(AC-21), `test_readiness_gate_single_failed_check_blocks`(AC-22), `test_readiness_gate_ignores_score`(AC-23), `test_readiness_gate_high_finding_blocks_despite_all_checks_pass`(AC-26), `test_readiness_attempts_per_round_limit`(AC-28), `test_readiness_attempt_counter_resets_per_formal_round`(AC-29), `test_stale_readiness_record_excluded_from_gate`(AC-44), `test_gate_attempt_count_ignores_digest`(AC-82), `test_gate_without_current_digest_record`(AC-83), `test_gate_uses_latest_recorded_result`(AC-91), `test_formal_round_cannot_reset_attempt_counter`(AC-98), `test_gate_ignores_artifact_digests_field`(AC-99). 작성 직후 각각을 `CMD-2 -k <이름>` 으로 돌리면 전부 실패한다.
- **구현**: 읽기 전용 서브커맨드. `formal_round` 는 `rounds[artifact] + 1` 로 유도한다. 시도 횟수는 그 `formal_round` 에 귀속된 기록 중 마지막 재개 결정 이후의 것을 센다(`outcome`·digest 무관). 체크리스트·finding 판정은 같은 라운드에서 `outcome == "recorded"` 이고 `artifact_digest` 가 등록 digest(=`artifacts[artifact]` 파일의 현재 SHA-256)와 같은 기록 중 `recorded_at` 이 가장 늦은 하나만 쓴다. 반환은 `{"decision", "formal_round", "attempts", "failed_checks", "high_findings", "judged_record"}` 다. `decision` 은 체크리스트 여덟 항목이 전부 `pass`·`not_applicable` 이고 Critical/High 0 이면 `READY`, 미충족이 있고 시도 2 미만이면 `RETRY`, 시도 2 이상이고 Critical/High 0 이면 `ARBITRATION`, 시도 2 이상이고 Critical/High 잔존이면 `HOLD` 다. `score` 를 읽지 않는다. `artifact_digests` 를 읽지 않는다.
- **통과 확인**: 소유 AC 의 테스트 12개를 `CMD-2 -k <이름>` 으로 하나씩 돌려 전부 통과시킨다 — `test_readiness_gate_requires_all_checks_and_no_high`(AC-21), `test_readiness_gate_single_failed_check_blocks`(AC-22), `test_readiness_gate_ignores_score`(AC-23), `test_readiness_gate_high_finding_blocks_despite_all_checks_pass`(AC-26), `test_readiness_attempts_per_round_limit`(AC-28), `test_readiness_attempt_counter_resets_per_formal_round`(AC-29), `test_stale_readiness_record_excluded_from_gate`(AC-44), `test_gate_attempt_count_ignores_digest`(AC-82), `test_gate_without_current_digest_record`(AC-83), `test_gate_uses_latest_recorded_result`(AC-91), `test_formal_round_cannot_reset_attempt_counter`(AC-98), `test_gate_ignores_artifact_digests_field`(AC-99). 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.

### T8. `AWAITING_READINESS_DECISION` stage 와 전이 가드를 만든다

대상 AC: AC-32, AC-46, AC-94, AC-107

- **선행 grep**: `grep -n "ALLOWED_TRANSITIONS" -A 45 dot_claude/skills/quality-goal/scripts/quality_state.py`, `grep -n "TERMINAL_STATES" dot_claude/skills/quality-goal/scripts/quality_state.py`, `grep -n "target in {\"BLOCKED\"" -B 2 -A 4 dot_claude/skills/quality-goal/scripts/quality_state.py` — 새 stage 를 `TERMINAL_STATES` 밖에 두고, `status_reason` 기록 분기를 어디에 넓힐지 확인한다.
- **실패 확인**: `CMD-2 test_readiness_exhausted_with_high_holds_for_user` → `TransitionError: invalid transition`. 이 태스크가 소유한 AC 의 테스트 4개를 먼저 작성한다 — `test_readiness_exhausted_with_high_holds_for_user`(AC-32), `test_readiness_records_survive_stage_exit`(AC-46), `test_readiness_hold_blocks_review_and_is_not_terminal`(AC-94), `test_hold_transition_requires_gate_hold`(AC-107). 작성 직후 각각을 `CMD-2 -k <이름>` 으로 돌리면 전부 실패한다.
- **구현**: `ALLOWED_TRANSITIONS` 에 `SPEC_REVIEW → AWAITING_READINESS_DECISION` 과 `AWAITING_READINESS_DECISION → {SPEC_REVIEW, NEEDS_REDESIGN, BLOCKED, CANCELLED}` 를 더한다. 새 stage 를 `TERMINAL_STATES` 에 넣지 않는다. 가드 둘을 건다 — 앞 엣지는 게이트 반환값이 `HOLD` 가 아니면 거부하고 `READINESS_HELD:` 로 시작하는 비어 있지 않은 `--reason` 을 요구한다. 뒤 엣지 중 `SPEC_REVIEW` 로 가는 것은 일반 `transition` 으로는 거부한다(T9 의 `resume-readiness` 만 수행). `status_reason` 기록 분기에 `AWAITING_READINESS_DECISION` 을 더한다. `record-review`·`record-review-unverified` 는 이 stage 에서 stage 불일치로 이미 거부된다 — 그것을 테스트로 고정한다.
- **통과 확인**: 소유 AC 의 테스트 4개를 `CMD-2 -k <이름>` 으로 하나씩 돌려 전부 통과시킨다 — `test_readiness_exhausted_with_high_holds_for_user`(AC-32), `test_readiness_records_survive_stage_exit`(AC-46), `test_readiness_hold_blocks_review_and_is_not_terminal`(AC-94), `test_hold_transition_requires_gate_hold`(AC-107). 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.
- **회귀 근거**: 새 stage 를 더해도 기존 `test_skill_size_and_state_names_contract` 는 초록으로 남는다. 그 테스트는 열세 개 상태 이름이 `SKILL.md` 본문에 **존재하는지**만 단언하고(`tests/test_content_contracts.py:970-985` 의 `assertIn(state, body)` 루프) 상태 집합의 완전 일치를 요구하지 않는다. 따라서 `SKILL.md` Stage table 행 추가를 T15 로 미뤄도 T8~T14 구간에서 CMD-1 이 빨개지지 않는다.

### T9. `resume-readiness` 를 만든다

대상 AC: AC-95, AC-96, AC-106, AC-108, AC-111

- **선행 grep**: `grep -n "def approve_plan" -A 8 dot_claude/skills/quality-goal/scripts/quality_state.py` — stage 가드의 기존 형태(`if state.get("stage") != "AWAITING_PLAN_APPROVAL": raise StateError(...)`)를 그대로 따른다.
- **실패 확인**: `CMD-2 test_resume_readiness_rejects_wrong_stage` → `StateError: invalid choice`. 이 태스크가 소유한 AC 의 테스트 5개를 먼저 작성한다 — `test_resume_readiness_records_decision_and_returns_to_spec_review`(AC-95), `test_readiness_hold_requires_recorded_decision`(AC-96), `test_resume_readiness_rejects_wrong_stage`(AC-106), `test_resume_cannot_reset_attempt_window_outside_hold`(AC-108), `test_hold_status_reason_is_set_and_cleared`(AC-111). 작성 직후 각각을 `CMD-2 -k <이름>` 으로 돌리면 전부 실패한다.
- **구현**: 입력은 `--state`, `--artifact`, `--reason` 이다. stage 가 `AWAITING_READINESS_DECISION` 이 아니면 거부한다. `readiness_decisions` 에 `{artifact, formal_round, decision: "resume", reason, decided_at}` 를 추가하고 stage 를 `SPEC_REVIEW` 로 되돌리며 `status_reason` 을 `None` 으로 지운다. `--formal-round` 같은 임의 값 입력을 받지 않는다.
- **통과 확인**: 소유 AC 의 테스트 5개를 `CMD-2 -k <이름>` 으로 하나씩 돌려 전부 통과시킨다 — `test_resume_readiness_records_decision_and_returns_to_spec_review`(AC-95), `test_readiness_hold_requires_recorded_decision`(AC-96), `test_resume_readiness_rejects_wrong_stage`(AC-106), `test_resume_cannot_reset_attempt_window_outside_hold`(AC-108), `test_hold_status_reason_is_set_and_cleared`(AC-111). 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.

### T10. `record-review` 에 readiness 게이트 강제를 건다

대상 AC: AC-72, AC-73, AC-103

- **선행 grep**: `grep -n "def record_review\b" -A 20 dot_claude/skills/quality-goal/scripts/quality_state.py`, `grep -n "def record_review_unverified" -A 12 dot_claude/skills/quality-goal/scripts/quality_state.py` — 두 경로의 초입에 같은 형태로 가드를 건다.
- **실패 확인**: `CMD-2 test_record_review_requires_readiness_gate` → 현재는 통과해 버리므로 테스트가 실패한다. 이 태스크가 소유한 AC 의 테스트 3개를 먼저 작성한다 — `test_record_review_requires_readiness_gate`(AC-72), `test_record_review_gate_exempts_v1_state`(AC-73), `test_readiness_gate_applies_to_unverified_path_only`(AC-103). 작성 직후 각각을 `CMD-2 -k <이름>` 으로 돌리면 전부 실패한다.
- **구현**: `record_review` 와 `record_review_unverified` 가 `artifact == "spec"` 일 때 게이트 결과를 요구한다. `READY` 도 `ARBITRATION` 도 아니면 거부한다. **가드의 위치는 라운드 한도 검사(`expected_round > ROUND_LIMITS[artifact]`) 직후, v5.0.0 의 개정 점검 요구 검사(`record-review requires --revision-check`) 직전이다.** 그 자리에 두면 게이트 판정이 라운드 번호와 무관해져 소유 AC 세 개의 테스트가 라운드 1 상태만으로 결정적으로 판정되고, 개정 점검 인자를 만들지 않아도 된다. `record_review` 의 시그니처(`revision_check_path`·`snapshot_dir` 키워드), `revision_checks` 기록 분기, `snapshots/<artifact>-r<N>.md` 저장 분기는 한 줄도 바꾸지 않는다(Spec R9.6). 상태에 `readiness` 필드가 아예 없으면(schema v1 재개) 면제한다 — 필드가 있고 비어 있는 경우는 면제하지 않는다. `record_review_validation_failure` 는 면제한다.
- **통과 확인**: 소유 AC 의 테스트 3개를 `CMD-2 -k <이름>` 으로 하나씩 돌려 전부 통과시킨다 — `test_record_review_requires_readiness_gate`(AC-72), `test_record_review_gate_exempts_v1_state`(AC-73), `test_readiness_gate_applies_to_unverified_path_only`(AC-103). 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.

### T11. `light` 모드에서 네 명령을 거부한다

대상 AC: AC-79

- **선행 grep**: `grep -n "requires light mode\|mode\") != \"light\"" dot_claude/skills/quality-goal/scripts/quality_state.py` — 기존 모드 조건의 오류 문구 형태를 따른다.
- **실패 확인**: `CMD-2 test_readiness_commands_rejected_in_light_mode` → 네 명령이 성공해 테스트가 실패한다. 이 태스크가 소유한 AC 의 테스트 1개를 먼저 작성한다 — `test_readiness_commands_rejected_in_light_mode`(AC-79). 작성 직후 각각을 `CMD-2 -k <이름>` 으로 돌리면 전부 실패한다.
- **구현**: `record-readiness`, `readiness-gate`, `record-draft-attempt`, `resume-readiness` 가 `state["mode"] == "light"` 이면 `StateError` 로 거부한다.
- **통과 확인**: 소유 AC 의 테스트 1개를 `CMD-2 -k <이름>` 으로 하나씩 돌려 전부 통과시킨다 — `test_readiness_commands_rejected_in_light_mode`(AC-79). 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.

### T12. Spec 템플릿에 두 절을 더한다

대상 AC: AC-60

- **실패 확인**: `CMD-2 test_spec_template_has_traceability_and_command_table` → `AssertionError`. 이 태스크가 소유한 AC 의 테스트 1개를 먼저 작성한다 — `test_spec_template_has_traceability_and_command_table`(AC-60). 작성 직후 각각을 `CMD-2 -k <이름>` 으로 돌리면 전부 실패한다.
- **구현**: `templates/spec.md` 의 `## Acceptance criteria` 뒤에 `## Requirements traceability` 를, `## Test strategy` 안에 `### 판정 명령 표` 를 더한다. 두 헤딩 문자열은 `readiness-policy.md` 가 C3·C4·C5·C7 의 앵커로 그대로 인용한다. 기존 열한 절의 이름·순서·strict 블록은 바꾸지 않는다.
- **통과 확인**: 소유 AC 의 테스트 1개를 `CMD-2 -k <이름>` 으로 하나씩 돌려 전부 통과시킨다 — `test_spec_template_has_traceability_and_command_table`(AC-60). 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.

### T13. `references/readiness-policy.md` 를 만든다

대상 AC: AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, AC-10, AC-11, AC-12, AC-13, AC-14, AC-16, AC-17, AC-18, AC-20, AC-24, AC-27, AC-31, AC-34, AC-36, AC-38, AC-49, AC-50, AC-69, AC-70, AC-71, AC-75, AC-87, AC-92, AC-101, AC-110

- **실패 확인**: `CMD-2 test_readiness_policy_is_referenced_from_skill` → 파일 부재. 이 태스크가 소유한 AC 의 테스트 21개를 먼저 작성한다 — `test_author_prompt_required_elements_contract`(AC-2·AC-6·AC-69), `test_author_invocation_template_contract`(AC-3), `test_forbidden_codex_flags_contract`(AC-4·AC-70), `test_codex_exec_has_no_approval_flag_contract`(AC-5), `test_author_write_scope_contract`(AC-7), `test_author_cross_regression_review_contract`(AC-8), `test_author_failure_recovery_contract`(AC-10), `test_author_no_change_is_failure_contract`(AC-11), `test_readiness_reviewer_is_fresh_contract`(AC-12), `test_readiness_invocation_template_contract`(AC-13), `test_readiness_stdin_guard_contract`(AC-14), `test_readiness_prompt_treats_notes_as_claims`(AC-16·AC-71), `test_readiness_is_cost_gate_not_authority_contract`(AC-17), `test_readiness_read_only_contract`(AC-18), `test_readiness_checklist_defines_eight_items`(AC-20), `test_readiness_score_is_advisory_contract`(AC-24), `test_readiness_arbitration_path_contract`(AC-31·AC-87), `test_readiness_path_check_precedes_invocation`(AC-75), `test_forbidden_codex_flags_enumerate_current_cli`(AC-92), `test_strict_marker_quotation_matches_template`(AC-101), `test_invocation_failure_causes_are_enumerated`(AC-110). 작성 직후 각각을 `CMD-2 -k <이름>` 으로 돌리면 전부 실패한다.
- **구현**: 다음을 담는다.
  - author 호출 템플릿(아홉 요소)과 readiness 호출 템플릿. 둘 다 프롬프트 파일을 표준 입력으로 준다. 인자로 넘기는 변형에만 `< /dev/null` 을 붙이며, 둘 중 어느 형태도 아닌 호출을 금지한다.
  - author 프롬프트 필수 요소 아홉 가지와 수정 허용 파일 두 개, `git status --porcelain` 대조 규칙(`initial_dirty_paths` 와 `.claude/quality-state/<task-id>/` 제외, 결과의 `changed_files` 와 대조).
  - readiness 프롬프트 계약: 개정 노트는 근거가 아니라 검증 대상, 비용 게이트 성격, 설계 취향 감점 금지, 읽기 전용, finding ID 네임스페이스와 안정성, score 실계산과 evidence 6건.
  - 체크리스트 C1~C8 정의. C2 의 strict marker 문자열과 C3·C4·C5·C7 의 두 절 헤딩을 `templates/spec.md` 에서 그대로 인용한다. C8 의 입력 집합을 명시한다.
  - 반복 한도·탈출 경로, arbitration 시 전달할 것(미충족 항목과 잔여 finding 전문의 파일 경로), digest 대조 절차(호출 전 확인, 실패 시 단계 유지·사용자 보고), author 실패 복구.
  - 금지 플래그 여덟 개와 기준 CLI 버전(`codex-cli 0.153.4`), `--yolo` 가 `--help` 에 없는 숨은 별칭이라는 사실.
  - readiness 호출 실패의 세 원인(비정상 종료·결과 파일 미생성·타임아웃)을 모두 `--invocation-status failed` 로 넘기라는 지시.
  - 두 reference 파일의 역할 분담. author·readiness 호출 템플릿은 `references/model-routing.md` 의 `## Codex invocation` 절에 실행 가능한 형태로 두고 이 문서가 그것을 인용한다(T14 와 같은 문언). AC-3·AC-13 은 이 문서의 인용을 판정하고, R9.8 의 분담은 원본이 `model-routing.md` 에 있다는 것으로 충족된다.
- **통과 확인**: 소유 AC 의 테스트 21개를 `CMD-2 -k <이름>` 으로 하나씩 돌려 전부 통과시킨다 — `test_author_prompt_required_elements_contract`(AC-2·AC-6·AC-69), `test_author_invocation_template_contract`(AC-3), `test_forbidden_codex_flags_contract`(AC-4·AC-70), `test_codex_exec_has_no_approval_flag_contract`(AC-5), `test_author_write_scope_contract`(AC-7), `test_author_cross_regression_review_contract`(AC-8), `test_author_failure_recovery_contract`(AC-10), `test_author_no_change_is_failure_contract`(AC-11), `test_readiness_reviewer_is_fresh_contract`(AC-12), `test_readiness_invocation_template_contract`(AC-13), `test_readiness_stdin_guard_contract`(AC-14), `test_readiness_prompt_treats_notes_as_claims`(AC-16·AC-71), `test_readiness_is_cost_gate_not_authority_contract`(AC-17), `test_readiness_read_only_contract`(AC-18), `test_readiness_checklist_defines_eight_items`(AC-20), `test_readiness_score_is_advisory_contract`(AC-24), `test_readiness_arbitration_path_contract`(AC-31·AC-87), `test_readiness_path_check_precedes_invocation`(AC-75), `test_forbidden_codex_flags_enumerate_current_cli`(AC-92), `test_strict_marker_quotation_matches_template`(AC-101), `test_invocation_failure_causes_are_enumerated`(AC-110). `[문서]` 판정 AC 는 `P=dot_claude/skills/quality-goal/references/readiness-policy.md` 로 두고 각 명령이 1건 이상을 반환하는지 본다 — AC-27 → `grep -nE '설계 정합성|아키텍처 타당성|시간축' "$P"`; AC-34 → `grep -nE 'READY.*(즉시|추가 시도).*(중단|하지 않)' "$P"`; AC-36 → `grep -nE 'SHA-256.*프롬프트|프롬프트.*SHA-256' "$P"`; AC-38 → `grep -nE 'digest.*(불일치|대조).*(단계 유지|사용자에게 보고)' "$P"`; AC-49 → `grep -nE 'description.*대응 관계|대응 관계.*description' "$P"`; AC-50 → `grep -nE '같은 물질적 문제.*같은 ID|ID 를 유지' "$P"`. 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.

### T14. `references/model-routing.md` 에 라우트 행을 더한다

대상 AC: AC-65

- **실패 확인**: `CMD-2 test_model_routing_includes_author_and_readiness_rows` → `AssertionError`. 이 태스크가 소유한 AC 의 테스트 1개를 먼저 작성한다 — `test_model_routing_includes_author_and_readiness_rows`(AC-65). 작성 직후 각각을 `CMD-2 -k <이름>` 으로 돌리면 전부 실패한다.
- **구현**: 라우트 표에 세 행을 더한다 — Spec author (standard) `gpt-5.6-terra` high, Spec author (strict) `gpt-5.6-sol` high, readiness reviewer `gpt-5.6-sol` high. `## Codex invocation` 절에는 author·readiness 호출 템플릿 두 개를 실행 가능한 형태로 더한다. 기존 라우트 행, 구현·수정 라운드 호출 템플릿, 프리플라이트 블록, 금지 플래그 문언은 바꾸지 않는다. 두 reference 의 역할 분담을 한 문장으로 적는다.
- **호출 템플릿의 위치**: Spec R9.8 은 `model-routing.md` 가 "역할별 모델·effort 값과 실행 가능한 호출 템플릿" 을 담는다고 한다. 그러나 AC-3 과 AC-13 은 author·readiness 호출 템플릿의 판정 대상을 `references/readiness-policy.md` 로 지정한다. 두 문언을 함께 만족시키려면 템플릿이 양쪽에 있어야 하므로, `model-routing.md` 의 `## Codex invocation` 절에 author·readiness 호출 템플릿 두 개를 실제 실행 가능한 형태로 더하고(기존 구현 라운드 템플릿은 그대로 둔다), `readiness-policy.md` 는 그것을 인용하면서 절차 문맥을 붙인다. 이 배치를 T14 본문과 T13 본문 양쪽에 같은 문언으로 적는다.
- **통과 확인**: 소유 AC 의 테스트 1개를 `CMD-2 -k <이름>` 으로 하나씩 돌려 전부 통과시킨다 — `test_model_routing_includes_author_and_readiness_rows`(AC-65). 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.

### T15. `SKILL.md` 를 갱신한다

대상 AC: AC-1, AC-19, AC-58, AC-59, AC-64, AC-66, AC-78, AC-102

- **선행 확인**: `wc -l dot_claude/skills/quality-goal/SKILL.md` 로 현재 393행을 확인하고, 추가 여유가 106행임을 계산한다.
- **실패 확인**: `CMD-2 test_spec_authoring_is_delegated_to_codex_contract` → `AssertionError`. 이 태스크가 소유한 AC 의 테스트 4개를 먼저 작성한다 — `test_spec_authoring_is_delegated_to_codex_contract`(AC-1), `test_formal_review_requires_readiness_contract`(AC-19), `test_readiness_policy_is_referenced_from_skill`(AC-59), `test_skill_version_bumped_for_contract_extension`(AC-64). 작성 직후 각각을 `CMD-2 -k <이름>` 으로 돌리면 전부 실패한다.
- **구현**: 네 곳만 바꾼다.
  - 참조 경로 목록에 `references/readiness-policy.md` 와 `schemas/readiness-result.schema.json` 을 더한다.
  - Stage table 의 `SPEC_REVIEW` 행에 readiness 사전 심사를 한 줄로 넣고, `AWAITING_READINESS_DECISION` 행을 더한다.
  - `### Spec` 절에 author 위임과 readiness 게이트를 요약하고 상세는 `readiness-policy.md` 로 넘긴다.
  - frontmatter `version` 을 `5.0.0` 에서 `5.1.0` 으로 올린다(상태 머신 계약 확장이므로 MINOR 이상).
  `### Plan`·`### Approval`·`### Implementation`·`### Code review`·`## Independent verification`·`## Safety rules`·`## Review invocation contract`·`## Codex invocation contract` 여덟 절은 한 글자도 바꾸지 않는다.
- **통과 확인**: 소유 AC 의 테스트 4개를 `CMD-2 -k <이름>` 으로 하나씩 돌려 전부 통과시킨다 — `test_spec_authoring_is_delegated_to_codex_contract`(AC-1), `test_formal_review_requires_readiness_contract`(AC-19), `test_readiness_policy_is_referenced_from_skill`(AC-59), `test_skill_version_bumped_for_contract_extension`(AC-64). 명령으로 판정하는 AC — `CMD-3`(AC-58), `CMD-4`(AC-66), `CMD-4`(AC-78), `CMD-4`(AC-102). 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.

### T16. 유지보수 문서를 갱신한다

대상 AC: AC-61, AC-84, AC-104, AC-105

- **실패 확인**: `CMD-2 test_maintenance_doc_covers_readiness` → `AssertionError`. 이 태스크가 소유한 AC 의 테스트 3개를 먼저 작성한다 — `test_maintenance_doc_covers_readiness`(AC-61), `test_routing_and_policy_split_is_documented`(AC-104), `test_version_guard_is_shared_not_inlined`(AC-105). 작성 직후 각각을 `CMD-2 -k <이름>` 으로 돌리면 전부 실패한다.
- **구현**: `docs/quality-goal-maintenance.md` 를 세 곳 고친다.
  1. "의존 CLI 점검" 에 readiness·author 라우팅 모델과 금지 플래그 목록의 CLI 버전 재확인을 더한다.
  2. 기존 `## 결정적 테스트` 헤딩을 **`## 판정 명령 표`** 로 **대체**한다 — 옛 헤딩 문자열을 지우고 새 헤딩으로 바꾸며 두 헤딩을 병기하지 않는다. 그 절에 CMD-1~CMD-7 일곱 행의 표를 싣는다. 표의 CMD-1·CMD-2 정의는 `tests/assert_python_version.py` 를 호출하는 형태여야 하고 버전 비교식(`sys.version_info`)을 명령 안에 인라인으로 쓰지 않는다. `test_version_guard_is_shared_not_inlined` 는 **`## 판정 명령 표` 헤딩을 앵커로** 그 절만 잘라내 CMD-1·CMD-2 행을 파싱한다. 헤딩 문자열을 여기서 확정하는 이유는, 확정하지 않으면 문서를 쓰는 사람과 테스트를 쓰는 사람이 서로 다른 앵커를 고를 수 있기 때문이다.
  3. 그 표 **바로 아래에** 테스트 스위트의 최소 Python 버전이 **3.12** 임을 명시하고 두 근거를 함께 싣는다 — (i) `tests/test_quality_state.py` 의 `ResumeSelectionTests` 가 `unittest.TestCase.enterContext` 를 쓰고 그 API 는 3.11 에서 추가됐다, (ii) `unittest` 가 `-k` 매칭 0건에 `NO TESTS RAN` 과 종료 코드 5 를 내는 동작은 3.12 에서 도입됐다. 이 문언이 Spec AC-84 의 판정 대상이며 **이 태스크가 AC-84 를 소유한다** — § Tasks 의 소유권 원칙이 "통과 확인을 그 태스크가 끝난 시점에 실제로 실행할 수 있는 가장 이른 태스크"를 소유자로 정하는데, 그 문언을 만드는 것이 이 태스크이므로 여기가 가장 이르다. T17 은 회귀 확인에서 같은 명령을 다시 돌린다. 이 단계가 없으면 판정 명령이 0건을 반환해 실패하고 어느 태스크도 그 문언을 만들지 않는다(직전 실행 blocker `PLAN-06`).
  4. `model-routing.md` 와 `readiness-policy.md` 의 동기화를 점검 항목으로 넣는다.
  그리고 `tests/test_content_contracts.py` 에 `test_version_guard_is_shared_not_inlined` 를 추가한다. 그 테스트는 **`docs/quality-goal-maintenance.md` 를 읽어** 판정 명령 표의 CMD-1·CMD-2 행이 `assert_python_version.py` 문자열을 포함하고 `sys.version_info` 를 포함하지 않는지 단언한다.
- **AC-84·AC-105 의 판정 대상을 이 문서로 통일하는 근거**: 둘 다 요구사항 R9.9 에 묶인 짝이므로 같은 파일의 같은 표를 판정해야 한다. AC-105 는 "판정 명령 표의 CMD-1 과 CMD-2 정의" 를, AC-84 는 같은 표의 최소 버전 문언과 두 근거를 본다. 그 표가 실릴 수 있는 곳은 셋인데, 이 워크플로의 `docs/development/.../spec.md` 는 goal 이 끝나면 옮겨지거나 지워질 수 있는 일회성 산출물이라 스킬 테스트가 읽으면 CMD-1 이 영구히 깨진다. `templates/spec.md` 의 `### 판정 명령 표` 는 채워지지 않은 템플릿 절이라 CMD 정의가 없다. 남는 것은 스킬과 함께 유지되는 `docs/quality-goal-maintenance.md` 이며, 그 문서는 이미 `## 결정적 테스트` 절에 실행 명령을 싣는 역할을 한다(현재 29-35행). 따라서 그 절을 `## 판정 명령 표` 로 대체하고, AC-105 는 그 표의 CMD-1·CMD-2 행을, AC-84 는 그 표 아래의 최소 버전 문언과 두 근거를 판정한다. R9.9 의 나머지 AC 인 AC-85 는 문서가 아니라 `tests/assert_python_version.py` 의 동작을 CMD-7 로 판정하므로 판정 대상이 갈리지 않는다.
- **통과 확인**: 소유 AC 의 테스트 3개를 `CMD-2 -k <이름>` 으로 하나씩 돌려 전부 통과시킨다 — `test_maintenance_doc_covers_readiness`(AC-61), `test_routing_and_policy_split_is_documented`(AC-104), `test_version_guard_is_shared_not_inlined`(AC-105). `[문서]` 판정 AC — AC-84 는 `M=docs/quality-goal-maintenance.md` 로 두고 `grep -n 'Python 3.12' "$M" && grep -n 'enterContext' "$M" && grep -nE 'NO TESTS RAN|종료 코드 5' "$M"` 를 돌려 **세 절이 모두 1건 이상**을 반환하는지 본다. 첫째가 최소 버전 명시를, 나머지 둘이 AC-84 가 요구하는 두 근거를 확인하며, `&&` 로 묶으므로 하나라도 0건이면 명령 전체가 비정상 종료한다. 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.

### T17. 불변 계약 테스트를 만들고 회귀를 확인한다

대상 AC: AC-62, AC-63, AC-67, AC-77, AC-85

- **착수 조건**: T1~T16 이 각자의 green 을 기록했을 것. 하나라도 미완이면 T17 을 시작하지 않는다.
- **실패 확인**: 이 태스크가 소유한 두 테스트를 먼저 작성한다 — `test_round_limits_and_required_checks_unchanged`(AC-63), `test_formal_pass_gate_threshold_unchanged`(AC-67). 작성 직후 각각을 `CMD-2 -k <이름>` 으로 돌리면 파일에 없던 이름이므로 실패한다.
- **구현**: 두 테스트를 `tests/test_content_contracts.py` 에 추가한다. 앞의 것은 `quality_state.ROUND_LIMITS == {"spec": 3, "plan": 2, "code": 3}` 과 `validate_review.REQUIRED_CHECKS` 의 세 키 집합이 기대값과 같은지 단언한다. **기대값은 테스트 안에 리터럴로 고정한다** — `git show` 로 base revision 을 읽으면 CMD-1 이 저장소 상태(리비전 존재 여부, `git` 실행 가능 여부)에 의존해 결정성을 잃는다. 리터럴 고정의 비용은 base 값이 바뀌면 테스트를 함께 고쳐야 한다는 것인데, 이 세 값은 바뀌면 안 되는 것이므로 그 마찰이 곧 목적이다. base revision 을 읽는 것은 파일 단위 비교가 필요한 CMD-4·CMD-6 뿐이고 그 둘은 `unittest` 수집 대상이 아닌 별도 스크립트다. 뒤의 것은 뒤의 것은 `references/spec-rubric.md`·`plan-rubric.md`·`code-rubric.md` 의 Pass gate 절이 각각 임계 85 를 그대로 싣는지 단언한다. 그 밖에 이 태스크는 새 행동을 만들지 않고 T1~T16 이 만든 것을 확인만 한다.
- **통과 확인**: 소유 AC 의 테스트 2개를 `CMD-2 -k <이름>` 으로 하나씩 돌려 전부 통과시킨다 — `test_round_limits_and_required_checks_unchanged`(AC-63), `test_formal_pass_gate_threshold_unchanged`(AC-67). 명령으로 판정하는 AC — `CMD-1`(AC-62), `CMD-6`(AC-77), `CMD-7`(AC-85). 회귀 재확인 — T16 이 소유한 AC-84 의 판정 명령(`M=docs/quality-goal-maintenance.md` 로 두고 `grep -n 'Python 3.12' "$M" && grep -n 'enterContext' "$M" && grep -nE 'NO TESTS RAN|종료 코드 5' "$M"`)을 여기서 한 번 더 돌린다. T15·T16 이 유지보수 문서를 각각 건드리므로 마지막 태스크에서 그 문언이 살아 있는지 다시 본다. 소유는 T16 이고 이것은 회귀 확인이다. 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.
- **추가 확인**: `git status --porcelain --untracked-files=all` 로 개별 파일까지 펼친 뒤 각 경로가 허용 목록 안에 있는지 본다. 기본 `--porcelain` 은 untracked 디렉터리를 한 줄로 접으므로 반드시 `--untracked-files=all` 을 붙인다. 허용 목록은 셋이다.
  1. `dot_claude/skills/quality-goal/` 하위 — 구현 대상.
  2. `docs/quality-goal-maintenance.md` — T16 이 고친다.
  3. `docs/development/2026-09-05-70-quality-goal-codex-spec-readiness/` 하위 — 이 워크플로가 만든 Spec·Plan·개정 노트·보고서. 구현 산출물이 아니라 워크플로 산출물이다.
  `.prior-art/` 하위 17개 파일은 초기 dirty 경로라 `--untracked-files=all` 로 펼치면 `??` 로 나타난다. 그것은 정상이며 허용 목록과 별개로 다룬다. 보존 판정은 목록이 아니라 **내용 fingerprint** 로 한다 — T1 착수 전에 `find .prior-art -type f -print0 | sort -z | xargs -0 shasum -a 256 > /tmp/qg-prior-art.sha` 를 만들어 두고, T17 에서 `shasum -a 256 -c /tmp/qg-prior-art.sha` 가 모두 `OK` 인지 확인한다. 파일 수가 늘거나 줄었으면 `find` 결과 행 수가 17 이 아니게 되므로 함께 본다.
  `docs/development/2026-09-05-70-quality-goal-codex-spec-readiness/` 를 허용하는 이유는 이 워크플로가 그 디렉터리에 Spec·Plan·개정 노트·보고서를 쓰기 때문이다. 구현 태스크(T1~T16)는 그 디렉터리에 파일을 만들지 않으며, T17 은 그 디렉터리에서 `spec.md`·`plan.md`·`spec-revision-notes.md`·`report.md` 네 파일만 나타나는지 확인한다.

## Verification commands

**인터프리터와 base revision 을 먼저 고정한다.** 아래 두 줄을 셸에서 실행한 뒤 명령을 돌린다. `python3` 를 직접 부르지 않는 이유는 셸에 따라 3.9.6 으로 풀릴 수 있기 때문이다(§ Global constraints 3).

```bash
QG_PY="${QG_PY:-$(command -v python3.14 || command -v python3.13 || command -v python3.12 || echo /opt/homebrew/bin/python3)}"
QG_BASE=6d60011cbdaead7946b191d3f12029eef5c141c8
```

`assert_python_version.py` 가 `QG_PY` 의 버전을 다시 확인하므로, 탐색이 3.12 미만을 골랐다면 CMD-1·CMD-2 가 테스트를 실행하지 않고 실패한다. `QG_BASE` 는 CMD-4·CMD-6 이 `git show` 에 쓰는 값이며 두 스크립트가 인자로 받는다.

| 순서 | ID | 명령 | 기대 결과 |
|---|---|---|---|
| 1 | CMD-1 | `"$QG_PY" dot_claude/skills/quality-goal/tests/assert_python_version.py && PYTHONDONTWRITEBYTECODE=1 "$QG_PY" -m unittest discover -s dot_claude/skills/quality-goal/tests -p 'test_*.py'` | 종료 코드 0, `OK`. 실행 테스트 수가 310 + 신규 테스트 수 |
| 2 | CMD-2 | `"$QG_PY" dot_claude/skills/quality-goal/tests/assert_python_version.py && PYTHONDONTWRITEBYTECODE=1 "$QG_PY" -m unittest discover -s dot_claude/skills/quality-goal/tests -p 'test_*.py' -k <테스트 이름>` | 종료 코드 0. 3.12 이상에서 매칭 0건이면 `unittest` 가 5 를 내므로 오타나 미구현 테스트 이름은 통과할 수 없다 |
| 3 | CMD-3 | `wc -l < dot_claude/skills/quality-goal/SKILL.md` | 500 미만 |
| 4 | CMD-4 | `"$QG_PY" dot_claude/skills/quality-goal/tests/assert_preserved_sections.py "$QG_BASE"` | 종료 코드 0, `보존 대상 절 불변` |
| 5 | CMD-5 | `"$QG_PY" -c "import json;d=json.load(open('dot_claude/skills/quality-goal/schemas/readiness-result.schema.json'));assert d['type']=='object';assert d['additionalProperties'] is False;print('OK')"` | 종료 코드 0, `OK` |
| 6 | CMD-6 | `"$QG_PY" dot_claude/skills/quality-goal/tests/assert_tests_preserved.py "$QG_BASE"` | 종료 코드 0, `기존 테스트 보존` |
| 7 | CMD-7 | `OLD_PY=/usr/bin/python3; "$OLD_PY" -c 'import sys;raise SystemExit(0 if sys.version_info<(3,12) else 1)' && "$QG_PY" dot_claude/skills/quality-goal/tests/assert_python_version.py && ! "$OLD_PY" dot_claude/skills/quality-goal/tests/assert_python_version.py` | 종료 코드 0 |

기준선은 `QG_BASE` 에서 CMD-1 이 `Ran 310 tests` / `OK` 인 것이다. 3.14.7 과 3.12.14 로 각각 실행해 확인했고, `/usr/bin/python3` 3.9.6 에서는 23건이 오류로 종료 코드 1 이다. `-k` 매칭 0건의 종료 코드도 세 인터프리터에서 실측했다 — 3.14.7 과 3.12.14 는 5, 3.9.6 은 0 이다. 태스크마다 CMD-1 을 다시 돌려 회귀가 없는지 본다.

이 저장소에 lint·type check·build·E2E 구성은 없다. `docs/quality-goal-maintenance.md` 의 `## 결정적 테스트` 절이 `unittest` 명령 하나만 싣고, `dot_claude/skills/quality-goal/` 아래에 그런 설정 파일이 없다. 그 네 범주는 `not configured` 로 보고하며 통과로 기록하지 않는다.

## Rollout and rollback

**롤아웃.** 이 작업은 chezmoi source 만 바꾼다. 배포는 사용자가 `chezmoi apply` 로 별도 수행하며 이 Plan 의 어떤 태스크도 그것을 실행하지 않는다. 다른 세션이 배포본을 실행 중이므로 적용 시점은 사용자가 고른다.

**호환성.** 상태 파일 `schema_version` 은 1 을 유지한다. 새 필드 셋은 선택적이고, 없으면 미실행으로 간주하며 읽기만으로 생기지 않는다. 따라서 이 변경 전에 시작한 goal 의 상태 파일을 구버전 스크립트가 그대로 읽는다(`load_state` 는 미지 필드를 거부하지 않는다 — `quality_state.py:264-265`).

**롤백 트리거.** 다음 중 하나면 되돌린다.

- CMD-1 이 기존 310 테스트 중 하나라도 실패시킨다.
- CMD-4 가 보존 대상 여덟 절의 변경을 보고한다.
- CMD-6 이 기존 테스트 이름의 삭제·개명을 보고한다.
- 배포 후 진행 중이던 goal 이 재개되지 않는다.

**롤백 절차.** 이 작업은 커밋을 만들지 않으므로 워크트리 되돌리기로 충분하다. `git checkout -- dot_claude/skills/quality-goal/ docs/quality-goal-maintenance.md` 로 수정 파일을 되돌리고, 신설 파일은 삭제한다 — `references/readiness-policy.md`, `schemas/readiness-result.schema.json`, `tests/assert_python_version.py`, `tests/assert_preserved_sections.py`, `tests/assert_tests_preserved.py`, `tests/fixtures/readiness-ready.json`, `tests/fixtures/readiness-one-check-failed.json`, `tests/fixtures/readiness-high-finding.json`, `tests/fixtures/readiness-schema-invalid.json`, `tests/fixtures/state-v1-without-readiness.json` 열 개다. 이 목록은 § File map 의 신설 항목과 1:1 로 대응한다. 신설 파일은 untracked 라 `git checkout --` 로 사라지지 않으므로 명시적으로 지운다. 사용자가 이미 `chezmoi apply` 를 했다면 되돌린 source 로 다시 `apply` 한다. 상태 파일은 손대지 않는다 — 새 필드가 남아 있어도 구버전 스크립트가 무시한다.

**모니터링.** 배포 후 첫 standard goal 실행에서 `readiness` 기록이 쌓이는지, `rounds.spec` 이 readiness 로 증가하지 않는지, 진행 중이던 goal 이 재개되는지 세 가지를 `quality_state.py show` 로 확인한다.

## Acceptance-criteria traceability

Spec 의 수용 기준 113건 전부를 태스크와 검증 명령에 매핑한다. 각 AC 는 정확히 한 태스크가 소유하며, 소유 태스크가 § Task dependencies 의 수행 순서에서 끝난 시점에 그 검증 명령이 실제로 실행 가능하다(§ Tasks 의 소유권 원칙). `CMD-2 -k <이름>` 은 § Verification commands 의 CMD-2 에 그 테스트 이름을 넣어 실행한다는 뜻이다. 기대 결과는 Spec 의 AC 문언을 그대로 옮긴 것이다.

**같은 요구사항의 AC 는 같은 판정 대상을 가리킨다 — 한 곳만 예외이며 그 예외는 의도된 것이다.** 제출 전 `.claude/quality-state/<task-id>/ac_crosscheck.py` 로 113건을 전수 대조했다(네 성질: 소유 태스크의 생성 단계, 실패·통과 확인 등장, 같은 요구사항의 판정 대상 일치, 선행 간선). 유일하게 갈리는 것은 **R9.6** 으로, AC-67 은 세 rubric 파일의 임계 85 를, AC-78 은 `SKILL.md` 의 승인 게이트·dirty-path·독립 검증 문언을 본다. R9.6 은 "기존 계약 불변" 이라는 성질상 서로 다른 파일에 사는 **서로 다른 사실** 을 묶는 요구사항이므로 대상이 갈리는 것이 정상이다. 직전 실행의 `PLAN-06` 은 이와 달리 **같은 사실**(R9.9 의 판정 명령 표)을 두 파일에서 판정하려 한 것이었고, 그것은 이 개정으로 `docs/quality-goal-maintenance.md` 하나로 통일됐다.

| Criterion | Task | Verification command | Expected outcome |
|---|---|---|---|
| AC-1 | T15 SKILL.md | `CMD-2 -k test_spec_authoring_is_delegated_to_codex_contract` | `SKILL.md` 의 Spec 단계 절차가 Spec 초안과 개정의 실행 주체를 Codex author 로 지정하고, 오케스트레이터가 Spec 본문을 직접 쓰지 않는다고 명시한다. |
| AC-2 | T13 readiness-policy.md | `CMD-2 -k test_author_prompt_required_elements_contract` | `references/readiness-policy.md` 가 author 호출 전 요구사항 발굴 수행과 그 결과의 프롬프트 반영을 요구한다. |
| AC-3 | T13 readiness-policy.md | `CMD-2 -k test_author_invocation_template_contract` | `references/readiness-policy.md` 의 author 호출 템플릿이 `-C`, `--sandbox workspace-write`, `--ephemeral`, `--model`, `model_reasoning_effort`, `--output-schema`, `--output-last-message`, `--json`, 프롬프트 표준 입력 아홉 요소를 모두 포함한다. |
| AC-4 | T13 readiness-policy.md | `CMD-2 -k test_forbidden_codex_flags_contract` | R1.4 가 열거한 여덟 옵션과 `--full-auto` 가 스킬 파일에 나타나는 모든 위치가 금지 문언 안이다. 판정 규칙은 기계적이다 — 각 플래그 문자열을 포함한 줄이 같은 문단 안에서 금지·사용하지 않음을 뜻하는 표현과 함께 나타나야 하며, 호출 템플릿 코드 블록 안에는 한 번도 나타나지 않아야 한다. `SKILL.md` 의 기존 금지 문언은 유지된다. |
| AC-5 | T13 readiness-policy.md | `CMD-2 -k test_codex_exec_has_no_approval_flag_contract` | 스킬의 어떤 문서도 `codex exec` 호출에 `-a` 또는 `--ask-for-approval` 을 지시하지 않고, `readiness-policy.md` 가 그 플래그의 부재를 명시한다. |
| AC-6 | T13 readiness-policy.md | `CMD-2 -k test_author_prompt_required_elements_contract` | author 프롬프트 필수 요소 아홉 가지(대상 Spec 절대 경로, 템플릿 경로, spec-rubric 경로, brainstorming-policy 경로, findings 전문 경로, 번호 보존 규칙, 개정 노트 경로, git 쓰기 금지, 조합 검토 지시)가 `references/readiness-policy.md` 에 목록으로 존재한다. |
| AC-7 | T13 readiness-policy.md | `CMD-2 -k test_author_write_scope_contract` | `references/readiness-policy.md` 가 author 의 수정 허용 파일을 대상 Spec 과 개정 노트 둘로 한정하고, 호출 후 `git status --porcelain` 확인을 요구하며, 그 비교에서 `initial_dirty_paths` 와 `.claude/quality-state/<task-id>/` 하위를 제외하고 결과의 `changed_files` 와 대조한다고 명시한다. |
| AC-8 | T13 readiness-policy.md | `CMD-2 -k test_author_cross_regression_review_contract` | author 프롬프트 계약이 조합 검토 지시를 필수로 포함하고 교차 회귀 전례를 근거로 인용한다. |
| AC-9 | T5 record-draft-attempt | `CMD-2 -k test_record_draft_attempt_increments_only_draft_attempts` | author 호출 1회가 `draft_attempts.spec` 을 1 증가시키고 `rounds.spec` 을 바꾸지 않는다. |
| AC-10 | T13 readiness-policy.md | `CMD-2 -k test_author_failure_recovery_contract` | author 호출 실패(비정상 종료·결과 파일 없음·스키마 검증 실패) 시 단계를 유지하고 모델을 대체하지 않는다는 지시가 `references/readiness-policy.md` 에 존재하며 `BLOCKED_MODEL_UNAVAILABLE` 경로를 참조한다. |
| AC-11 | T13 readiness-policy.md | `CMD-2 -k test_author_no_change_is_failure_contract` | author 호출 전후 Spec digest 가 같으면 개정 실패로 처리한다는 지시가 존재한다. |
| AC-12 | T13 readiness-policy.md | `CMD-2 -k test_readiness_reviewer_is_fresh_contract` | `references/readiness-policy.md` 가 readiness reviewer 를 author 와 별개 프로세스로 실행하고 author 문맥을 상속하지 않는다고 명시한다. |
| AC-13 | T13 readiness-policy.md | `CMD-2 -k test_readiness_invocation_template_contract` | readiness 호출 템플릿이 `--sandbox read-only` 를 쓰고 금지 플래그를 포함하지 않는다. |
| AC-14 | T13 readiness-policy.md | `CMD-2 -k test_readiness_stdin_guard_contract` | `references/readiness-policy.md` 의 author·readiness 호출 템플릿이 모두 표준 입력을 프롬프트 파일 또는 `/dev/null` 에 연결하고, 둘 중 어느 형태도 아닌 호출을 금지한다고 명시하며, 그 이유(비대화형 무한 대기)를 기록한다. |
| AC-15 | T2 결과 스키마 | `CMD-2 -k test_readiness_schema_uses_type_not_const` | `schemas/readiness-result.schema.json` 의 모든 property 정의가 `type` 키를 가지며 `const` 키를 한 번도 쓰지 않는다. |
| AC-16 | T13 readiness-policy.md | `CMD-2 -k test_readiness_prompt_treats_notes_as_claims` | readiness 프롬프트 계약이 "개정 노트는 근거가 아니라 검증 대상" 규칙을 포함한다. |
| AC-17 | T13 readiness-policy.md | `CMD-2 -k test_readiness_is_cost_gate_not_authority_contract` | readiness 프롬프트 계약이 자신의 판정을 비용 제어 게이트로 규정하고 Claude 공식 판정을 대체하지 않는다고 명시하며, 설계 취향 감점을 금지한다. |
| AC-18 | T13 readiness-policy.md | `CMD-2 -k test_readiness_read_only_contract` | readiness 프롬프트 계약이 읽기 전용과 git 쓰기 금지를 명시한다. |
| AC-19 | T15 SKILL.md | `CMD-2 -k test_formal_review_requires_readiness_contract` | `SKILL.md` 와 `references/readiness-policy.md` 가 readiness 미실행 상태에서 Claude 공식 Spec 리뷰를 시작하지 않는다고 명시한다. |
| AC-20 | T13 readiness-policy.md | `CMD-2 -k test_readiness_checklist_defines_eight_items` | `references/readiness-policy.md` 의 체크리스트 절이 C1~C8 여덟 항목을 각각 정의한다. |
| AC-21 | T7 readiness-gate | `CMD-2 -k test_readiness_gate_requires_all_checks_and_no_high` | 체크리스트 여덟 항목이 모두 `pass` 또는 `not_applicable` 이고 Critical/High 가 0 인 결과만 READY 로 판정된다. `not_applicable` 은 충족으로 센다. |
| AC-22 | T7 readiness-gate | `CMD-2 -k test_readiness_gate_single_failed_check_blocks` | 체크리스트 항목 중 하나라도 `fail` 이면 게이트 판정이 REVISE 다. |
| AC-23 | T7 readiness-gate | `CMD-2 -k test_readiness_gate_ignores_score` | 게이트 판정 함수가 `score` 값을 읽지 않는다. `score` 를 0 과 100 으로 바꿔도 동일 입력의 판정 결과가 같다. |
| AC-24 | T13 readiness-policy.md | `CMD-2 -k test_readiness_score_is_advisory_contract` | `references/readiness-policy.md` 가 `score` 를 기록 전용 참고값으로 규정하고 게이트·전이에 쓰지 않는다고 명시한다. |
| AC-25 | T2 결과 스키마 | `CMD-2 -k test_readiness_schema_checklist_shape` | `checklist` 각 항목이 `status` 와 `evidence` 를 요구하며, `status` 는 `pass`·`fail`·`not_applicable` 셋만 허용한다. |
| AC-26 | T7 readiness-gate | `CMD-2 -k test_readiness_gate_high_finding_blocks_despite_all_checks_pass` | Critical 또는 High finding 이 하나라도 있으면 체크리스트가 전부 `pass` 여도 READY 가 아니다. |
| AC-27 | T13 readiness-policy.md | [문서] `references/readiness-policy.md` § 체크리스트 게이트 | 체크리스트 항목 정의에 설계 정합성·아키텍처 타당성·시간축 전개 판정이 포함되지 않는다는 것이 문서에 명시된다. |
| AC-28 | T7 readiness-gate | `CMD-2 -k test_readiness_attempts_per_round_limit` | 한 시도 구간(R4.1)의 readiness 시도가 2회를 초과하면 오케스트레이터가 추가 시도를 하지 않고 R4.4 또는 R4.5 경로로 간다. |
| AC-29 | T7 readiness-gate | `CMD-2 -k test_readiness_attempt_counter_resets_per_formal_round` | Claude 공식 리뷰가 기록되면 다음 라운드의 readiness 시도 카운터가 0 에서 시작한다. |
| AC-30 | T2 결과 스키마 | `CMD-2 -k test_readiness_schema_attempt_has_no_maximum` | `schemas/readiness-result.schema.json` 의 `attempt` 에 `maximum` 제약이 없다. |
| AC-31 | T13 readiness-policy.md | `CMD-2 -k test_readiness_arbitration_path_contract` | 시도 구간 2회 소진 + Critical/High 0 상태에서 arbitration 경로가 선택되고 미충족 항목이 공식 리뷰 근거로 전달된다는 지시가 존재한다. |
| AC-32 | T8 새 stage·전이 가드 | `CMD-2 -k test_readiness_exhausted_with_high_holds_for_user` | 시도 구간 2회 소진 + Critical/High 잔존이면 `AWAITING_READINESS_DECISION` 으로 전이하고 `status_reason` 이 `READINESS_HELD:` 로 시작하며, 그 상태가 `TERMINAL_STATES` 에 속하지 않는다. |
| AC-33 | T6 record-readiness | `CMD-2 -k test_record_readiness_does_not_touch_rounds` | readiness 시도 기록이 `rounds.spec` 을 증가시키지 않는다. |
| AC-34 | T13 readiness-policy.md | [문서] `references/readiness-policy.md` § 반복 한도와 탈출 | READY 판정 직후 같은 라운드에서 추가 readiness 시도를 하지 않는다는 지시가 존재한다. |
| AC-35 | T6 record-readiness | `CMD-2 -k test_record_readiness_rejects_path_mismatch` | 심사 대상 경로가 `state.artifacts.spec` 과 다르면 readiness 기록이 거부된다. |
| AC-36 | T13 readiness-policy.md | [문서] `references/readiness-policy.md` § digest 대조 | 심사 대상 파일의 현재 SHA-256 을 프롬프트에 싣는다는 지시가 존재한다. |
| AC-37 | T6 record-readiness | `CMD-2 -k test_record_readiness_rejects_digest_mismatch_and_counts_attempt` | `--invocation-status ok` 로 호출했을 때 결과의 `artifact_digest` 가 심사 시점 digest 와 다르면 유효 심사로 채택되지 않고 `digest_mismatch` 실패 기록이 남으며, 게이트의 시도 횟수가 1 증가한다. |
| AC-38 | T13 readiness-policy.md | [문서] `references/readiness-policy.md` § digest 대조 | digest 대조 실패가 단계를 바꾸지 않고 사용자 보고로 이어진다는 지시가 존재한다. |
| AC-39 | T6 record-readiness | `CMD-2 -k test_readiness_record_shape` | `outcome` 이 `recorded` 인 readiness 기록 하나가 `attempt`, `formal_round`, `verdict`, `score`, `checklist`, `findings`, `artifact_digest`, `reviewer_model`, `result_path`, `recorded_at` 열 개 필드를 모두 갖는다. |
| AC-40 | T4 상태 필드 | `CMD-2 -k test_new_state_has_draft_attempts` | 새 상태에 `draft_attempts` 가 존재하고 artifact 별 초기값이 0 이다. |
| AC-41 | T6 record-readiness | `CMD-2 -k test_readiness_and_draft_attempts_leave_rounds_unchanged` | readiness 기록과 author 호출 기록 어느 것도 `rounds` 의 값을 바꾸지 않는다. |
| AC-42 | T4 상태 필드 | `CMD-2 -k test_v1_state_without_readiness_fields_is_not_mutated_on_load` | R6.2 의 세 필드가 없는 schema v1 상태 파일을 읽을 수 있고, 읽기만으로는 어느 필드도 상태 파일에 생기지 않으며, readiness 미실행·author 미호출로 취급된다. |
| AC-43 | T4 상태 필드 | `CMD-2 -k test_resume_preserves_rounds_reviews_and_approval` | 진행 중 goal 을 재개해도 기존 `rounds`, `reviews`, `open_finding_ids`, `plan_approval` 이 그대로 보존된다. |
| AC-44 | T7 readiness-gate | `CMD-2 -k test_stale_readiness_record_excluded_from_gate` | 등록 digest(`artifacts.spec` 이 가리키는 파일의 현재 SHA-256, R6.6)와 다른 digest 를 가리키는 readiness 기록은 게이트의 체크리스트·finding 판정 입력에서 제외되고 이력으로 남는다. |
| AC-45 | T6 record-readiness | `CMD-2 -k test_readiness_formal_round_advances_after_review` | 공식 리뷰 기록 이후 추가되는 readiness 기록의 `formal_round` 가 `rounds[artifact] + 1` 과 같다. |
| AC-46 | T8 새 stage·전이 가드 | `CMD-2 -k test_readiness_records_survive_stage_exit` | `SPEC_PASSED`·`AWAITING_READINESS_DECISION`·`NEEDS_REDESIGN`·`BLOCKED`·`CANCELLED` 로 전이해도 readiness 기록과 `readiness_decisions` 가 상태에 남는다. |
| AC-47 | T3 결과 검증 | `CMD-2 -k test_readiness_finding_id_namespace` | readiness finding ID 가 `READY-` 로 시작하지 않으면 결과 검증이 실패한다. |
| AC-48 | T3 결과 검증 | `CMD-2 -k test_readiness_rejects_spec_namespace_ids` | `SPEC-` 로 시작하는 finding ID 가 readiness 결과에 있으면 검증이 실패한다. |
| AC-49 | T13 readiness-policy.md | [문서] `references/readiness-policy.md` § finding 식별자 | readiness 프롬프트 계약이 공식 finding 과의 대응 관계를 `description` 에 기록하도록 요구한다. |
| AC-50 | T13 readiness-policy.md | [문서] `references/readiness-policy.md` § finding 식별자 | readiness 프롬프트 계약이 하나의 개정 주기 안에서 같은 물질적 문제에 같은 ID 를 유지하도록 요구한다. |
| AC-51 | T2 결과 스키마 | `CMD-2 -k test_readiness_schema_required_fields` | `schemas/readiness-result.schema.json` 의 `required` 가 R8.1 의 열한 필드(`artifact`, `attempt`, `formal_round`, `score`, `verdict`, `checklist`, `blockers`, `findings`, `evidence`, `required_next_action`, `artifact_digest`)를 정확히 포함하고 그 밖의 필드를 required 로 두지 않는다. |
| AC-52 | T3 결과 검증 | `CMD-2 -k test_readiness_score_computation_instruction` | readiness 프롬프트 계약이 `score` 를 rubric 가중치로 실제 계산하도록 지시하고 "blocker 가 있다고 0 을 넣지 마라"를 포함한다. |
| AC-53 | T2 결과 스키마 | `CMD-2 -k test_readiness_schema_evidence_min_items` | `evidence` 최소 6건 요구가 스키마의 `minItems` 로 강제되고, 각 항목이 `claim` 과 `location` 을 갖는다. |
| AC-54 | T2 결과 스키마 | `CMD-2 -k test_readiness_schema_digest_pattern` | `artifact_digest` 가 소문자 SHA-256 64자 패턴으로 제약된다. |
| AC-55 | T2 결과 스키마 | `CMD-2 -k test_readiness_schema_verdict_enum` | `verdict` 가 `READY` 와 `REVISE` 두 값만 허용한다. |
| AC-56 | T2 결과 스키마 | `CMD-2 -k test_readiness_schema_requires_all_eight_checks` | `checklist` 가 C1~C8 여덟 항목을 모두 포함하지 않으면 검증이 실패한다. |
| AC-57 | T6 record-readiness | `CMD-2 -k test_invalid_readiness_result_counts_attempt_and_is_not_recorded` | `--invocation-status ok` 로 호출했을 때 스키마 검증에 실패한 결과가 유효 심사로 채택되지 않고 `schema_invalid` 실패 기록이 남으며, 게이트의 시도 횟수가 1 증가한다. |
| AC-58 | T15 SKILL.md | `CMD-3` | `SKILL.md` 파일 전체가 500행 미만이다. |
| AC-59 | T15 SKILL.md | `CMD-2 -k test_readiness_policy_is_referenced_from_skill` | `references/readiness-policy.md` 가 존재하고 `SKILL.md` 의 참조 경로 목록에 등재된다. |
| AC-60 | T12 Spec 템플릿 | `CMD-2 -k test_spec_template_has_traceability_and_command_table` | `templates/spec.md` 에 요구사항 추적표 절과 판정 명령 표 절이 존재한다. |
| AC-61 | T16 유지보수 문서 | `CMD-2 -k test_maintenance_doc_covers_readiness` | `docs/quality-goal-maintenance.md` 에 readiness 점검 항목(`codex exec` 플래그, readiness 결과 스키마, author·reviewer 라우팅 모델)이 존재한다. |
| AC-62 | T17 회귀 확인 | `CMD-1` | Python 3.12 이상에서 전체 테스트가 통과한다. |
| AC-63 | T17 회귀 확인 | `CMD-2 -k test_round_limits_and_required_checks_unchanged` | `ROUND_LIMITS` 가 `{"spec": 3, "plan": 2, "code": 3}` 그대로이고 `REQUIRED_CHECKS` 가 변경되지 않는다. |
| AC-64 | T15 SKILL.md | `CMD-2 -k test_skill_version_bumped_for_contract_extension` | `SKILL.md` frontmatter 의 `version` 이 5.0.0 보다 크고 MINOR 이상 증가한다. |
| AC-65 | T14 model-routing.md | `CMD-2 -k test_model_routing_includes_author_and_readiness_rows` | `references/model-routing.md` 의 라우트 표에 Spec author(standard `gpt-5.6-terra` high, strict `gpt-5.6-sol` high)와 readiness reviewer(fresh `gpt-5.6-sol` high) 행이 존재한다. |
| AC-66 | T15 SKILL.md | `CMD-4` | Plan 단계와 Code 단계의 절차 문언이 base revision `6d60011cbdaead7946b191d3f12029eef5c141c8` 대비 의미상 변경되지 않는다. |
| AC-67 | T17 회귀 확인 | `CMD-2 -k test_formal_pass_gate_threshold_unchanged` | 공식 Claude 게이트의 점수 임계 85 가 `references/spec-rubric.md`·`plan-rubric.md`·`code-rubric.md` 에서 변경되지 않는다. |
| AC-68 | T2 결과 스키마 | `CMD-5` | `schemas/readiness-result.schema.json` 이 JSON 으로 파싱되고 최상위 `type` 이 `object` 이며 `additionalProperties` 가 `false` 다. |
| AC-69 | T13 readiness-policy.md | `CMD-2 -k test_author_prompt_required_elements_contract` | `references/readiness-policy.md` 가 요구사항 발굴에서 남은 물질적 모호성을 author 호출 **전에** 사용자 질의로 해소하도록 요구한다. |
| AC-70 | T13 readiness-policy.md | `CMD-2 -k test_forbidden_codex_flags_contract` | `references/readiness-policy.md` 의 금지 플래그 문언이 네 개를 열거하는 데 그치지 않고 `--sandbox` 의 승인·권한 우회 값을 포함한 모든 sandbox 우회 옵션을 포괄적으로 금지하며, 같은 변경이 `SKILL.md` 의 Safety rules 절을 건드리지 않는다. |
| AC-71 | T13 readiness-policy.md | `CMD-2 -k test_readiness_prompt_treats_notes_as_claims` | readiness 프롬프트 계약이 개정 노트의 주장을 Spec 본문에서 파일:행으로 대조하도록 요구한다. |
| AC-72 | T10 게이트 강제 | `CMD-2 -k test_record_review_requires_readiness_gate` | 현재 `formal_round` 의 게이트 판정이 `READY` 도 `ARBITRATION` 도 아닌 상태에서 spec 리뷰를 `record-review` 로 기록하면 거부된다. |
| AC-73 | T10 게이트 강제 | `CMD-2 -k test_record_review_gate_exempts_v1_state` | readiness 필드가 아예 없는 schema v1 상태에서는 AC-72 의 강제가 적용되지 않고 spec 리뷰 기록이 통과한다. |
| AC-74 | T6 record-readiness | `CMD-2 -k test_readiness_attempt_is_globally_monotonic` | readiness 기록 하나를 추가할 때마다 `attempt` 가 실행 전체에서 1씩 증가하며 `formal_round` 가 바뀌어도 초기화되지 않는다. |
| AC-75 | T13 readiness-policy.md | `CMD-2 -k test_readiness_path_check_precedes_invocation` | `references/readiness-policy.md` 가 경로 불일치 시 readiness 호출 자체를 하지 않는다고 명시하고, 그 확인을 호출 전 절차로 배치한다. |
| AC-76 | T5 record-draft-attempt | `CMD-2 -k test_record_draft_attempt_is_per_artifact` | `draft_attempts.spec` 증가가 `draft_attempts.plan` 을 바꾸지 않는다. |
| AC-77 | T17 회귀 확인 | `CMD-6` | base revision 의 테스트 이름 집합이 현재 테스트 이름 집합의 부분집합이다. 기존 테스트가 삭제되거나 이름이 바뀌면 실패한다. |
| AC-78 | T15 SKILL.md | `CMD-4` | `SKILL.md` 의 승인 게이트·dirty-path 보존·독립 검증 문언이 base revision 대비 변경되지 않는다. |
| AC-79 | T11 light 거부 | `CMD-2 -k test_readiness_commands_rejected_in_light_mode` | `light` 모드 상태에서 `record-readiness`, `readiness-gate`, `record-draft-attempt`, `resume-readiness` 네 명령이 모두 오류로 거부된다. |
| AC-80 | T6 record-readiness | `CMD-2 -k test_readiness_record_outcome_enum` | readiness 기록의 `outcome` 이 `recorded`·`schema_invalid`·`digest_mismatch`·`invocation_failed` 네 값만 허용한다. |
| AC-81 | T6 record-readiness | `CMD-2 -k test_failed_readiness_attempt_is_recorded_as_empty_outcome` | 스키마 검증 실패와 digest 불일치가 각각 해당 `outcome` 의 실패 기록을 남기며, 그 기록의 `verdict` 와 `score` 가 `null` 이고 `checklist` 와 `findings` 가 빈 배열이다. |
| AC-82 | T7 readiness-gate | `CMD-2 -k test_gate_attempt_count_ignores_digest` | 같은 `formal_round` 안에서 Spec digest 가 바뀐 뒤 두 번째 readiness 를 기록하면 게이트의 시도 횟수가 2 로 계산된다. |
| AC-83 | T7 readiness-gate | `CMD-2 -k test_gate_without_current_digest_record` | 등록 digest(`artifacts.spec` 이 가리키는 파일의 현재 SHA-256, R6.6)를 가리키는 `recorded` 기록이 없고 시도가 2 미만이면 게이트가 `RETRY` 를, 2 이상이면 `ARBITRATION` 을 반환한다. |
| AC-84 | T16 유지보수 문서 | [문서] `docs/quality-goal-maintenance.md` § 판정 명령 표 | `docs/quality-goal-maintenance.md` 의 판정 명령 표가 테스트 스위트의 최소 Python 버전을 3.12 로 명시하고 그 두 근거(`enterContext`, `NO TESTS RAN` 종료 코드 5)를 함께 싣는다. |
| AC-85 | T17 회귀 확인 | `CMD-7` | `tests/assert_python_version.py` 가 3.12 이상에서 성공하고 3.12 미만에서 비정상 종료한다. |
| AC-86 | T1 판정 스크립트 | `CMD-4` + `CMD-6` + `CMD-7` | R9.10 의 세 스크립트가 존재하고, 세 파일명이 모두 `test_` 로 시작하지 않아 `unittest discover -p 'test_*.py'` 의 수집 대상에서 빠진다. |
| AC-87 | T13 readiness-policy.md | `CMD-2 -k test_readiness_arbitration_path_contract` | `references/readiness-policy.md` 의 arbitration 절차가 공식 리뷰에 전달할 것으로 미충족 체크리스트 항목과 잔여 finding 전문의 파일 경로를 함께 지정한다. |
| AC-88 | T6 record-readiness | `CMD-2 -k test_record_readiness_persists_review_time_digest` | 심사 시점 digest 가 readiness 기록의 `artifact_digest` 로 상태에 남고, 그 값이 호출 시점에 계산한 Spec 파일 digest 와 같다. |
| AC-89 | T6 record-readiness | `CMD-2 -k test_readiness_fields_created_on_first_record` | readiness 필드가 없는 상태에 첫 `record-readiness` 를 적용하면 그때 필드가 생성되고, 새 `init` 상태에는 `readiness`·`draft_attempts`·`readiness_decisions` 세 필드가 빈 값으로 존재한다. |
| AC-90 | T4 상태 필드 | `CMD-2 -k test_resume_preserves_rounds_reviews_and_approval` | 재개 시 `plan_approval` 의 경로와 digest 가 재개 전과 바이트 단위로 같다. |
| AC-91 | T7 readiness-gate | `CMD-2 -k test_gate_uses_latest_recorded_result` | 같은 `formal_round` 에 등록 digest(`artifacts.spec` 이 가리키는 파일의 현재 SHA-256, R6.6)를 가리키는 `recorded` 기록이 둘 이상이면 게이트가 `recorded_at` 이 가장 늦은 하나만 판정에 쓴다. |
| AC-92 | T13 readiness-policy.md | `CMD-2 -k test_forbidden_codex_flags_enumerate_current_cli` | `references/readiness-policy.md` 의 금지 목록이 R1.4 의 여덟 이름(`--yolo` 포함)을 모두 포함하고, 기준 CLI 버전 문자열과 `--yolo` 가 `--help` 에 없는 숨은 별칭이라는 사실을 함께 기록한다. |
| AC-93 | T5 record-draft-attempt | `CMD-2 -k test_draft_attempts_created_on_first_record` | `draft_attempts` 가 없는 schema v1 상태에 첫 `record-draft-attempt` 를 적용하면 그때 `draft_attempts` 가 생성되고 해당 artifact 값이 1 이 된다. |
| AC-94 | T8 새 stage·전이 가드 | `CMD-2 -k test_readiness_hold_blocks_review_and_is_not_terminal` | 게이트가 `HOLD` 를 반환한 뒤 전이한 `AWAITING_READINESS_DECISION` 에서 `record-review` 와 `record-review-unverified` 가 모두 거부되고, 상태가 종료로 바뀌지 않는다. |
| AC-95 | T9 resume-readiness | `CMD-2 -k test_resume_readiness_records_decision_and_returns_to_spec_review` | `resume-readiness` 가 사용자 결정을 `readiness_decisions` 에 기록하고 `AWAITING_READINESS_DECISION` 을 `SPEC_REVIEW` 로 되돌리며, 직후 게이트의 시도 횟수가 0 이 되어 반환값이 `RETRY` 다. |
| AC-96 | T9 resume-readiness | `CMD-2 -k test_readiness_hold_requires_recorded_decision` | `AWAITING_READINESS_DECISION` 에서 `resume-readiness` 없이 `SPEC_REVIEW` 로 돌아가는 전이가 거부된다. |
| AC-97 | T6 record-readiness | `CMD-2 -k test_record_readiness_rejects_mismatched_formal_round` | `record-readiness` 에 `rounds[artifact] + 1` 과 다른 `--formal-round` 를 주면 호출이 거부된다. |
| AC-98 | T7 readiness-gate | `CMD-2 -k test_formal_round_cannot_reset_attempt_counter` | `--formal-round` 를 임의로 올려 같은 공식 라운드의 시도 카운터를 0 으로 되돌릴 수 없다. |
| AC-99 | T7 readiness-gate | `CMD-2 -k test_gate_ignores_artifact_digests_field` | 게이트가 `artifact_digests[artifact]` 를 판정 입력으로 쓰지 않는다. 그 값이 `None` 이거나 현재 파일 digest 와 달라도 게이트 결과가 바뀌지 않는다. |
| AC-100 | T6 record-readiness | `CMD-2 -k test_invocation_failure_is_recorded_and_counts_attempt` | `--invocation-status failed` 로 호출하면 결과 파일이 스키마를 통과하고 현재 등록 digest 까지 가리키는 정상 결과여도 `invocation_failed` 로 기록되고, `verdict` 와 `score` 가 `null`, `checklist` 와 `findings` 가 빈 배열이며, `result_path` 가 `--stderr-path` 값이고, 게이트의 시도 횟수가 1 증가한다. |
| AC-101 | T13 readiness-policy.md | `CMD-2 -k test_strict_marker_quotation_matches_template` | `references/readiness-policy.md` 가 C2 판정에 쓰려고 인용한 strict marker 주석 문자열 두 개가 `templates/spec.md` 에 그대로 존재한다. |
| AC-102 | T15 SKILL.md | `CMD-4` | CMD-4 의 보존 대상 절 목록이 `## Review invocation contract` 와 `## Codex invocation contract` 를 포함하고, 두 절이 base revision 대비 변경되지 않는다. |
| AC-103 | T10 게이트 강제 | `CMD-2 -k test_readiness_gate_applies_to_unverified_path_only` | readiness 게이트가 `READY` 도 `ARBITRATION` 도 아닌 상태에서 `record-review-unverified` 로 spec 리뷰를 기록하면 거부되고, `record-review-error` 는 거부되지 않는다. |
| AC-104 | T16 유지보수 문서 | `CMD-2 -k test_routing_and_policy_split_is_documented` | `references/model-routing.md` 와 `references/readiness-policy.md` 의 역할 분담이 문서에 명시되고, `docs/quality-goal-maintenance.md` 의 점검 항목에 두 파일의 동기화가 등재된다. |
| AC-105 | T16 유지보수 문서 | `CMD-2 -k test_version_guard_is_shared_not_inlined` | `docs/quality-goal-maintenance.md` 판정 명령 표의 CMD-1 과 CMD-2 정의가 `tests/assert_python_version.py` 호출을 포함하고, 버전 비교식을 명령 안에 인라인으로 복제하지 않는다. |
| AC-106 | T9 resume-readiness | `CMD-2 -k test_resume_readiness_rejects_wrong_stage` | stage 가 `AWAITING_READINESS_DECISION` 이 아닌 상태에서 `resume-readiness` 를 호출하면 거부되고 `readiness_decisions` 에 아무것도 추가되지 않는다. |
| AC-107 | T8 새 stage·전이 가드 | `CMD-2 -k test_hold_transition_requires_gate_hold` | 게이트 반환값이 `HOLD` 가 아닌 상태에서 `SPEC_REVIEW → AWAITING_READINESS_DECISION` 전이를 시도하면 거부된다. |
| AC-108 | T9 resume-readiness | `CMD-2 -k test_resume_cannot_reset_attempt_window_outside_hold` | 시도 구간의 시도가 2회인 `SPEC_REVIEW` 상태에서 `resume-readiness` 를 호출해도 거부되므로 게이트의 시도 횟수가 2 로 유지되고 반환값이 `RETRY` 로 돌아가지 않는다. |
| AC-109 | T6 record-readiness | `CMD-2 -k test_schema_invalid_precedes_digest_mismatch` | `--invocation-status ok` 이고 결과가 스키마 위반과 digest 불일치를 동시에 만족하면 `schema_invalid` 로 기록된다. |
| AC-110 | T13 readiness-policy.md | `CMD-2 -k test_invocation_failure_causes_are_enumerated` | `references/readiness-policy.md` 가 readiness 호출의 비정상 종료·결과 파일 미생성·타임아웃 세 경우를 모두 `--invocation-status failed` 로 넘기도록 지시한다. |
| AC-111 | T9 resume-readiness | `CMD-2 -k test_hold_status_reason_is_set_and_cleared` | `AWAITING_READINESS_DECISION` 전이가 `status_reason` 에 `READINESS_HELD:` 로 시작하는 값을 남기고, `resume-readiness` 가 `SPEC_REVIEW` 로 되돌릴 때 그 값을 `null` 로 지운다. |
| AC-112 | T6 record-readiness | `CMD-2 -k test_invocation_status_enum_is_enforced` | `--invocation-status` 에 `ok`·`failed` 밖의 값을 주면 호출이 거부되고, `record-readiness` 가 `outcome` 인자를 받지 않는다. |
| AC-113 | T6 record-readiness | `CMD-2 -k test_failed_status_requires_existing_stderr_path` | `--invocation-status failed` 인데 `--stderr-path` 가 없거나 그 경로가 존재하지 않으면 호출이 거부된다. |

## strict 전용 블록을 제거한 근거

이 Plan 은 standard 모드이므로 `templates/plan.md` 의 strict 전용 구간을 제거했다. 제거한 여섯 소절이 이 작업에 적용되지 않는 이유는 Spec § Decisions D12 와 같다.

- Threat and trust boundaries — 신뢰 경계를 넘는 입력이 없다. 변경 대상은 로컬 스킬 파일뿐이다.
- Authorization and tenant isolation — 권한 주체나 테넌트 개념이 없다.
- Migration, compatibility, and rollback — § Rollout and rollback 이 같은 내용을 이미 담는다. 데이터 마이그레이션이나 백필은 없다.
- Failure recovery and observability — 알림·메트릭 대상이 되는 상시 실행 구성 요소가 없다. 롤백 트리거 네 개와 모니터링 세 항목이 § Rollout and rollback 에 있다.
- High-risk end-to-end verification — 고위험 경로가 없다. 결정적 검증은 CMD-1~CMD-7 일곱이다.
- No production mutation confirmation — 프로덕션 대상이 없다. 이 Plan 은 `chezmoi apply` 를 실행하지 않고 배포 시점을 사용자에게 남긴다(§ Global constraints 1).
