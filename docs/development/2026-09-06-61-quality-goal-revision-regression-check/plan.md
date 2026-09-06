# Quality Goal Implementation Plan

- Task ID: 20260906T003045Z-61-quality-goal-개정-후-자기-회귀-점검-revision-r-d857b87b
- Mode: standard
- Status: PLAN_REVIEW
- Created: 2026-09-06
- Updated: 2026-09-06
- Source goal: #61 quality-goal 개정 후 자기 회귀 점검(revision regression check) 단계를 추가한다

## Spec link

- 승인 대상 Spec: `docs/development/2026-09-06-61-quality-goal-revision-regression-check/spec.md`
- SHA-256: `af2207bd51e4b36dc3f9cd702462b08bd2d080dcd3702385e61879fd9da5791c`
- 공식 리뷰: 라운드 3, score 91, PASS, blocker 0 (`.claude/quality-state/20260906T003045Z-61-quality-goal-개정-후-자기-회귀-점검-revision-r-d857b87b/spec-review-r3.json`). 잔여 Low SPEC-13(R7.3 스캐너 패턴)·SPEC-14(R5.2 판정 토큰 대상)는 T5·T4 의 구현 규칙으로 확정한다.
- 요구사항 30건(R1.1~R7.5), 수용 기준 54건(AC-1~AC-54), 추적표 30행

이 Plan 은 그 Spec 의 AC-1~AC-54 전부를 태스크와 검증 명령에 매핑한다.

## Global constraints

1. **chezmoi source 만 바꾼다.** 대상은 `dot_claude/skills/quality-goal/` 하위와 `docs/quality-goal-maintenance.md` 다. `chezmoi apply` 는 실행하지 않는다 — 다른 세션이 배포본 `~/.claude/skills/quality-goal/` 을 실행 중이다.
2. **Python 3.12 이상.** 셸에 따라 `python3` 가 `/usr/bin/python3` 3.9.6 으로 풀릴 수 있다(실측: 240 테스트 중 23 오류). 모든 명령은 § Verification commands 의 `QG_PY` 를 쓴다.
3. **테스트 우선.** 모든 행동 변경은 실패하는 테스트를 먼저 기록하고, 최소 구현 뒤 통과를 기록한다.
4. **기존 계약 불변(Spec R7.3).** `ROUND_LIMITS`, `REQUIRED_CHECKS` 키 집합, `SCORE_THRESHOLD`, 세 루브릭 `## Pass gate` 절, `templates/spec.md`, `templates/plan.md`, `SKILL.md` 일곱 보존 절은 base revision `b30a0dee8465b9b8a3cf5243a47740b3c2116a24` 과 바이트 동일해야 한다(`CMD-4`). 기존 테스트 메서드 이름(고유 239)은 삭제·개명하지 않는다(`CMD-5`).
5. **`SKILL.md` 500 행 미만**(`CMD-3`).
6. **초기 dirty 경로 없음.** 상태의 `initial_dirty_paths` 는 빈 목록이다. 작업 산출물 외 경로를 만들지 않는다.
7. **표준 라이브러리만.** `revision_check.py` 는 `subprocess`·`socket`·`urllib`·`http` 를 import 하지 않는다(Spec R1.6).

## File map

| 파일 | 작업 | 책임 | 영향 인터페이스 |
|---|---|---|---|
| `dot_claude/skills/quality-goal/schemas/revision-check.schema.json` | 신설 | 점검 산출물 계약(R1.2) | `record-review` 검증, `test_revision_check.py` |
| `dot_claude/skills/quality-goal/scripts/revision_check.py` | 신설 | 파싱·대칭 칸·diff·파급표·노트 점검·CLI(R1~R5) | 오케스트레이터가 `--state` 모드로 호출, CMD-6 |
| `dot_claude/skills/quality-goal/scripts/quality_state.py` | 수정 | `new_state` 필드, `record_review` 시그니처·검증·스냅숏·기록, CLI 인자(R6) | CLI 전체, 기존 테스트 11 개 본문 |
| `dot_claude/skills/quality-goal/scripts/validate_review.py` | 수정 | `validate_revision_check(payload)` 추가. 기존 `validate_review`·`REQUIRED_CHECKS`·`SCORE_THRESHOLD` 불변 | `quality_state.record_review` 가 호출 |
| `dot_claude/skills/quality-goal/references/revision-check-policy.md` | 신설 | 문법·칸 종류·노트 형식·라운드 규칙·포착 범위 표(R7.2) | `SKILL.md` 가 참조, 저자 필독 |
| `dot_claude/skills/quality-goal/SKILL.md` | 수정 | `### Spec`·`### Plan` 절차 문단, 참조 경로 셋, `version: 5.0.0`(R7.1·R7.4) | 오케스트레이터 지시 |
| `docs/quality-goal-maintenance.md` | 수정 | `## 개정 후 자기 회귀 점검` 절(R7.4) | 유지보수 runbook |
| `dot_claude/skills/quality-goal/tests/test_revision_check.py` | 신설 | R1~R5 테스트 | CMD-1·CMD-2 |
| `dot_claude/skills/quality-goal/tests/test_quality_state.py` | 수정 | R6 테스트 추가, 기존 11 개 본문 갱신 | CMD-1·CMD-2 |
| `dot_claude/skills/quality-goal/tests/test_content_contracts.py` | 수정 | R7·스키마 테스트 추가 | CMD-1·CMD-2 |
| `dot_claude/skills/quality-goal/tests/fixtures/revision-check/` | 신설 | 대칭 완전 Spec·Plan 쌍, PLAN-06 형태 Plan, 라운드 2 노트 있음·없음, legacy 상태 | 위 세 테스트 파일 |

`.gitignore` 는 손대지 않는다 — `.claude/quality-state/` 는 25행으로 이미 무시된다.

## Task dependencies

```text
T1 (스키마)
 └─ T2 (스크립트 골격 + Spec 대칭 + --state 모드 골격 + 픽스처) — AC-2 가 T1 스키마로 출력을 검증
     ├─ T5 (quality_state 스냅숏·--revision-check) — T1 의 스키마를 검증에, T2 의 --state 골격(스냅숏 경로·base_digest)을 AC-53 후반에 사용
     └─ T3 (Plan 대칭 + 하한)
     └─ T4 (diff·파급표·노트) — 착수 조건: T3 과 T5 완료 (AC-49 는 T5 의 record-review 검증을, AC-3 은 이 태스크의 파급표를 쓴다)
         └─ T6 (policy·유지보수 문서) — 칸 이름 확정 후
             └─ T7 (SKILL.md) — policy 경로 존재 후
                 └─ T8 (전수 회귀·자기 적용) — T1~T7 전부
```

수행 순서는 T1 → T2 → T3 → T5 → T4 → T6 → T7 → T8 이다. T5 는 T1·T2 뒤에 T3 과 병행 가능하다. T4 는 T3 과 T5 둘 다 끝난 뒤에만 시작한다. 이 간선들은 § Acceptance-criteria traceability 의 모든 AC 에 대해 "기대 결과가 의존하는 산출물의 생산 태스크가 소유 태스크와 같거나 선행" 임을 스크립트로 대조해 정했다(개정 노트 라운드 2).

## Tasks

**검증 수단의 두 종류.** 대부분의 AC 는 새 테스트 이름으로 판정한다 — 소유 태스크가 그 테스트를 **작성**하고(실패 확인) 통과시킨다(통과 확인). 다섯 개(AC-41·42·43·44·45)는 새 테스트 없이 § Verification commands 의 명령(CMD-3·4·5·1·6)을 그대로 돌려 판정한다.

**AC 소유권 원칙.** 각 AC 는 그 AC 의 통과 확인을 그 태스크가 끝난 시점에 실제로 실행할 수 있는 가장 이른 태스크가 소유한다. 태스크 본문의 `CMD-1`~`CMD-6` 은 § Verification commands 표를 가리키며 `QG_PY`·`QG_BASE` 를 먼저 설정한 뒤 쓴다.

### T1. 점검 산출물 스키마

대상 AC: AC-38

- **실패 확인**: 이 태스크가 소유한 AC 의 테스트 1개를 먼저 작성한다 — `test_revision_check_schema_contract`(AC-38). 작성 직후 각각을 `CMD-2 -k <이름>` 으로 돌리면 대상 코드가 없어 전부 실패한다.
- **구현**: `schemas/revision-check.schema.json` 을 만든다. 최상위 `type: object`, `additionalProperties: false`, `required` 는 Spec R1.2 의 열둘(`artifact`, `round`, `base_digest`, `current_digest`, `spec_digest`, `cells`, `empty_cells`, `touched_requirements`, `removed_ids`, `ripple`, `notes`, `passed`). `artifact` 는 `{"type": "string", "enum": ["spec", "plan"]}`, `round` 는 `{"type": ["integer", "null"], "minimum": 1}`, 세 digest 는 `{"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"}`, `cells[]` 는 `additionalProperties: false` 로 `kind`(string)·`key`(string)·`status`(enum `ok`/`empty`)·`detail`(string)·`line`(integer 또는 null) 다섯 필수, `empty_cells` 는 `integer`, `touched_requirements`·`removed_ids` 는 문자열 배열, `ripple[]` 는 `additionalProperties: false` 로 `requirement`(string)·`acceptance_criteria`(문자열 배열)·`plan_rows`(정수 배열 또는 null)·`tasks`(문자열 배열 또는 null)·`commands`(문자열 배열) 다섯 필수, `notes` 는 `additionalProperties: false` 로 `required`(boolean)·`path`(string 또는 null)·`section_found`(boolean)·`missing_rows`·`blank_cells`(문자열 배열) 다섯 필수, `passed` 는 boolean. `const` 는 쓰지 않는다.
- **통과 확인**: 소유 AC 의 테스트 1개를 `CMD-2 -k <이름>` 으로 하나씩 돌려 전부 통과시킨다 — `test_revision_check_schema_contract`(AC-38). 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.

### T2. 점검 스크립트 골격과 Spec 대칭

대상 AC: AC-1, AC-2, AC-4, AC-5, AC-6, AC-7, AC-8, AC-9, AC-10, AC-11, AC-12, AC-48

- **착수 조건**: T1 완료(AC-2 가 `schemas/revision-check.schema.json` 으로 출력을 검증한다).
- **실패 확인**: `python3 dot_claude/skills/quality-goal/scripts/revision_check.py --help` → `can't open file`. 이 태스크가 소유한 AC 의 테스트 12개를 먼저 작성한다 — `test_cli_exit_codes_and_usage`(AC-1), `test_output_matches_schema`(AC-2), `test_id_grammar_ignores_code_blocks`(AC-4), `test_missing_spec_traceability_marks_every_requirement_empty`(AC-5), `test_check_is_read_only`(AC-6), `test_requirement_without_trace_row_or_ac_is_empty`(AC-7), `test_ghost_trace_row_and_count_mismatch`(AC-8), `test_orphan_ac_and_missing_means`(AC-9), `test_execution_ac_requires_cmd_row`(AC-10), `test_ac_numbering_gap_and_duplicate_definition`(AC-11), `test_dangling_reference_is_empty_cell`(AC-12), `test_id_grammar_recognizes_all_definition_forms`(AC-48). 작성 직후 각각을 `CMD-2 -k <이름>` 으로 돌리면 대상 코드가 없어 전부 실패한다. 픽스처 디렉터리 `tests/fixtures/revision-check/` 도 이 태스크가 만든다 — `spec-complete.md`(요구사항 4·AC 8·결정 2·CMD 2, `## Requirements traceability` 4 행), `plan-complete.md`(태스크 3, 추적표 8 행, `## Verification commands` 에 첫째 셀 ID 표와 둘째 셀 ID 표 각 하나), `plan-plan06-shape.md`(AC 한 행의 판정 수단이 ``[문서] `spec.md` § Test strategy`` 이고 소유 태스크의 AC 등장 행은 `docs/quality-goal-maintenance.md` 만 언급, 다른 문단에 `spec.md` 존재), `spec-revision-notes-round2.md`(`## 라운드 2 개정` 과 R5.2 헤더 표), `spec-revision-notes-no-round2.md`(라운드 1 절만). 변형 픽스처는 테스트 안에서 기준 파일을 문자열 치환해 만든다.
- **구현**: `scripts/revision_check.py` 를 만든다. 표준 라이브러리만 import 한다(`argparse`, `difflib`, `hashlib`, `json`, `pathlib`, `re`, `sys`; `subprocess`·`socket`·`urllib`·`http` 금지). 구조는 넷이다 — (1) `parse_document(text)`: R1.4(a) 정의 문법으로 R·AC·D·T·CMD 정의를 모으되 펜스 코드 블록 안은 건너뛰고, R1.4(b)② 참조 범위(펜스·백틱 1개·백틱 2개 스팬 제거)로 참조 토큰을 모으고, 헤딩에 `traceability`/`추적` 이 있는 `##` 절의 `| R… | AC-… |` 행을 매핑으로 읽는다. (2) `judgement_means(ac_text)`: 코드 스팬 밖 마지막 `[실행]`/`[문서]` 를 고르고 `[실행]` 은 괄호 안, `[문서]` 는 줄 끝까지에서 R1.4(c) 토큰(`CMD-\d+` 정확 일치, `test_\w+`, `[\w./-]+\.[A-Za-z0-9]+`)을 뽑는다. (3) `spec_cells(doc)`: R2.1~R2.5 의 칸(`R→추적행`, `R→AC`, `추적행 AC 존재`, `추적행→R`, `R 수=추적 행 수`, `AC→R`, `AC→판정수단`, `AC→CMD 존재`, `AC 번호 연속`, `중복 정의`, `참조 무결성`)과 R1.4(d) 의 `문법 미충족`. (4) CLI 와 `--state` 모드 골격: R1.1 의 인자와 종료 코드 `0`/`1`/`2`, 상대 경로 해소, `--out` 만 쓰기, 표준 출력 두 표(R1.3); `--state` 가 주어지면 상태 JSON 을 읽어(파싱 실패 `2`) `round = rounds[artifact] + 1` 을 계산하고 `<state 디렉터리>/snapshots/<artifact>-r<rounds[artifact]>.md` 경로를 해소해 `rounds[artifact] >= 1` 인데 파일이 없으면 `2`, 있으면 그 파일의 SHA-256 을 `base_digest` 로 싣고(대조는 T4), `--state` 와 `--base` 동시 지정이면 `2` 를 낸다. **T2 가 구현하지 않는 것**: 스냅숏 digest 대조, `rounds == 0` 의 `notes.required = false` 의미, diff·`touched_requirements`·`removed_ids`·`ripple`·노트 점검 — 이들은 T4 가 채우며 T2 시점에는 빈 목록·`required: false` 로 둔다. AC-1·AC-2 의 통과 확인에 필요한 것은 위 골격까지다.
- **통과 확인**: 소유 AC 의 테스트 12개를 `CMD-2 -k <이름>` 으로 하나씩 돌려 전부 통과시킨다 — `test_cli_exit_codes_and_usage`(AC-1), `test_output_matches_schema`(AC-2), `test_id_grammar_ignores_code_blocks`(AC-4), `test_missing_spec_traceability_marks_every_requirement_empty`(AC-5), `test_check_is_read_only`(AC-6), `test_requirement_without_trace_row_or_ac_is_empty`(AC-7), `test_ghost_trace_row_and_count_mismatch`(AC-8), `test_orphan_ac_and_missing_means`(AC-9), `test_execution_ac_requires_cmd_row`(AC-10), `test_ac_numbering_gap_and_duplicate_definition`(AC-11), `test_dangling_reference_is_empty_cell`(AC-12), `test_id_grammar_recognizes_all_definition_forms`(AC-48). 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.
- **주의**: `revision_check.py` 는 `tests/` 밖 `scripts/` 에 두므로 `unittest discover -p 'test_*.py'` 에 수집되지 않는다. 픽스처 파일명은 `test_` 로 시작하지 않는다.

### T3. Plan 대칭과 정의 수 하한

대상 AC: AC-13, AC-14, AC-15, AC-16, AC-17, AC-50, AC-52

- **실패 확인**: 이 태스크가 소유한 AC 의 테스트 7개를 먼저 작성한다 — `test_plan_ac_set_equals_spec`(AC-13), `test_task_target_list_symmetry`(AC-14), `test_same_line_rule_catches_plan_06_shape`(AC-15), `test_same_line_rule_accepts_colocated_means`(AC-16), `test_plan_cmd_and_reference_integrity`(AC-17), `test_definition_floor_blocks_empty_artifacts`(AC-50), `test_verification_cell_reads_inside_code_spans`(AC-52). 작성 직후 각각을 `CMD-2 -k <이름>` 으로 돌리면 대상 코드가 없어 전부 실패한다.
- **구현**: `plan_cells(plan_doc, spec_doc)` 를 채운다 — R3.1(`Spec AC→Plan 추적행`, `Plan 추적행→Spec AC`), R3.2(`AC→태스크`, `태스크 존재`, `태스크 대상 AC→추적행`, `추적행→태스크 대상 AC`; `대상 AC:` 줄 파싱), R3.3(`AC 등장 행에 판정수단 동반`: 판정 수단 셀에서 백틱 제거 후 R1.4(c) 토큰을 뽑고, 소유 태스크 본문에서 그 AC ID 가 등장하는 줄(백틱 제거)에 각 토큰이 부분 문자열로 있는지), R3.4(`추적행 CMD 존재`: 판정 수단 셀의 CMD 가 Plan CMD 표에 있는지; 태스크 본문 CMD 는 코드 스팬 포함 범위로 읽어 미해소면 `참조 무결성`; `T` 는 Plan 정의, `AC`·`R`·`D` 는 `--spec` 정의로 해소). Plan 추적표는 `| Criterion | Task | Verification command | Expected outcome |` 헤더 뒤 첫 셀이 `AC-\d+` 인 행이고, Plan CMD 표는 첫째 또는 둘째 셀이 `CMD-\d+` 인 행이다. R1.4(d) 하한 — spec 은 요구사항 0 또는 AC 0, plan 은 태스크 0 또는 추적표 AC 행 0 이면 `문법 미충족` 칸 하나를 `empty` 로 넣고 다른 칸 산출을 건너뛴다.
- **통과 확인**: 소유 AC 의 테스트 7개를 `CMD-2 -k <이름>` 으로 하나씩 돌려 전부 통과시킨다 — `test_plan_ac_set_equals_spec`(AC-13), `test_task_target_list_symmetry`(AC-14), `test_same_line_rule_catches_plan_06_shape`(AC-15), `test_same_line_rule_accepts_colocated_means`(AC-16), `test_plan_cmd_and_reference_integrity`(AC-17), `test_definition_floor_blocks_empty_artifacts`(AC-50), `test_verification_cell_reads_inside_code_spans`(AC-52). 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.

### T4. 개정 diff·파급표·개정 노트 점검

대상 AC: AC-3, AC-18, AC-19, AC-20, AC-21, AC-22, AC-23, AC-24, AC-25, AC-26, AC-49

- **착수 조건**: T3 과 T5 가 각자의 통과 확인을 기록했을 것. AC-49 의 통과 확인은 T5 가 만든 `record_review(..., revision_check_path=)` 의 `round` 불일치 거부를, AC-3 은 이 태스크가 채우는 파급표 출력을 쓴다.
- **실패 확인**: 이 태스크가 소유한 AC 의 테스트 11개를 먼저 작성한다 — `test_stdout_prints_ripple_and_empty_cell_tables`(AC-3), `test_base_snapshot_located_and_digest_checked`(AC-18), `test_round_one_has_no_base_and_no_notes_requirement`(AC-19), `test_touched_requirements_from_diff_spec`(AC-20), `test_touched_requirements_from_diff_plan`(AC-21), `test_ripple_row_per_touched_requirement_with_empty_marking`(AC-22), `test_notes_section_required_from_round_two`(AC-23), `test_notes_table_header_and_row_coverage`(AC-24), `test_notes_blank_cell_is_empty`(AC-25), `test_notes_failure_sets_passed_false_and_exit_one`(AC-26), `test_standalone_base_mode`(AC-49). 작성 직후 각각을 `CMD-2 -k <이름>` 으로 돌리면 대상 코드가 없어 전부 실패한다. `--state` 모드 테스트는 `tempfile` 에 `state.json`(`rounds`·`reviews`·`artifacts`)과 `snapshots/<artifact>-r<N>.md` 를 만들어 쓴다.
- **구현**: (1) `--state` 모드 완성(T2 의 골격 위에): 스냅숏 SHA-256 이 `reviews[artifact][-1].artifact_digest` 와 다르면 종료 코드 `2`; `rounds[artifact] == 0` 이면 base 없음·`base_digest = null`·`notes.required = false`; `rounds >= 1` 이면 `notes.required = true`. 독립 모드 `--base` 는 digest 대조 없이 diff 원천, `round = null`. (2) `touched_requirements`: `difflib.SequenceMatcher(None, base_lines, cur_lines, autojunk=False).get_opcodes()` 의 `insert`·`replace` 가 만든 current 줄 번호 집합을 R4.2 규칙으로 요구사항에 되돌린다(spec: R 정의 줄·추적행·매핑 AC 정의 줄; plan: 추적행이 바뀐 AC 와 절이 바뀐 태스크의 AC 를 `--spec` 추적표로). `removed_ids` 는 base 에 정의됐고 current 에 없는 R·AC(plan 은 T·CMD). (3) `ripple`: 건드린 요구사항마다 `acceptance_criteria`(Spec 추적표), `plan_rows`·`tasks`(plan 만, spec 은 `null`), `commands`(AC 의 `[실행]` CMD + `[문서]` 파일명 토큰 + plan 추적행 셀 토큰). 판정 대상 칸이 빈 목록이면 `파급표` 칸 `empty`. (4) 노트: `--notes` 또는 `<current 디렉터리>/<artifact>-revision-notes.md`; `round >= 2` 이면 `## 라운드 <round> 개정` 절(`^## 라운드 (\d+) 개정\s*$`)과 헤더 `| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |` 표를 찾아 `missing_rows`(행 없음 `<R>`, 파급 AC 누락 `<R>/<AC>`, 판정 토큰 없음 `<R>/<AC>/판정` — 검사 대상은 `ripple[].acceptance_criteria` 의 AC 로 한정하며, 그 AC ID 의 등장 중 하나 이상이 바로 뒤 괄호를 `일치`/`모순` 으로 시작하면 충족)와 `blank_cells`(trim 후 빈 문자열·`-`·`—`)를 채운다. `passed` 는 R1.2 의 정의대로.
- **통과 확인**: 소유 AC 의 테스트 11개를 `CMD-2 -k <이름>` 으로 하나씩 돌려 전부 통과시킨다 — `test_stdout_prints_ripple_and_empty_cell_tables`(AC-3), `test_base_snapshot_located_and_digest_checked`(AC-18), `test_round_one_has_no_base_and_no_notes_requirement`(AC-19), `test_touched_requirements_from_diff_spec`(AC-20), `test_touched_requirements_from_diff_plan`(AC-21), `test_ripple_row_per_touched_requirement_with_empty_marking`(AC-22), `test_notes_section_required_from_round_two`(AC-23), `test_notes_table_header_and_row_coverage`(AC-24), `test_notes_blank_cell_is_empty`(AC-25), `test_notes_failure_sets_passed_false_and_exit_one`(AC-26), `test_standalone_base_mode`(AC-49). 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.

### T5. `quality_state.py` 스냅숏·`--revision-check`·면제

대상 AC: AC-27, AC-28, AC-29, AC-30, AC-31, AC-32, AC-33, AC-34, AC-53

- **착수 조건**: T1(스키마)과 T2(`--state` 골격: `snapshots/<artifact>-r<rounds>.md` 경로 해소와 `base_digest`) 완료. AC-53 후반은 T2 골격의 base 선택을 쓴다.
- **실패 확인**: 이 태스크가 소유한 AC 의 테스트 9개를 먼저 작성한다 — `test_record_review_writes_snapshot_with_reviewed_digest`(AC-27), `test_record_review_round_two_requires_revision_check`(AC-28), `test_record_review_rejects_mismatched_revision_check`(AC-29), `test_record_review_stores_revision_check_entry`(AC-30), `test_revision_check_option_rejected_for_code_review`(AC-31), `test_legacy_state_without_revision_checks_is_exempt`(AC-32), `test_new_state_has_empty_revision_checks_and_load_does_not_inject`(AC-33), `test_cli_record_review_accepts_revision_check_flag`(AC-34), `test_snapshot_write_failure_leaves_state_unchanged`(AC-53). 작성 직후 각각을 `CMD-2 -k <이름>` 으로 돌리면 대상 코드가 없어 전부 실패한다. `revision_checks` 키 없는 상태 픽스처 `tests/fixtures/revision-check/state-legacy-without-revision-checks.json` 을 이 태스크가 만든다.
- **구현**: `quality_state.py` 를 다섯 곳 고친다. (1) `new_state` 에 `"revision_checks": {"spec": [], "plan": []}`. `load_state` 는 주입하지 않는다. (2) `record_review(state, review_path, artifact_digest, *, revision_check_path=None, snapshot_dir=None)`. 기존 검사(digest 형식 → 리뷰 로드 → stage → `expected_round` → 재시도 digest → 등록 digest → `round` 일치 → 한도) 뒤에 신설 검사 — 면제 여부(`"revision_checks" not in state`) 확인, 비면제이고 spec/plan 이고 `expected_round >= 2` 인데 `revision_check_path is None` 이면 `StateError("record-review requires --revision-check for {artifact} round {n}")`; `code` 에 값이 오면 `StateError`; 값이 있으면 파일 존재 → `schemas/revision-check.schema.json` 검증(`validate_review.py` 의 수동 검증 방식과 같은 순수 파이썬 검사기 `validate_revision_check(payload)` 를 `validate_review.py` 에 추가) → `artifact`·`round == expected_round`·`current_digest == artifact_digest`·`passed is True`. 그 뒤 기존 리뷰 JSON 검증. (3) 검증이 모두 끝난 뒤 상태를 바꾸기 전에 `snapshot_dir` 가 주어지고 spec/plan 이고 `artifacts[artifact]` 가 있으면 `snapshot_dir.mkdir(parents=True, exist_ok=True)` 후 같은 디렉터리의 임시 파일(`tempfile.NamedTemporaryFile(dir=snapshot_dir, delete=False)`)에 쓰고 `os.replace` 로 `<artifact>-r<expected_round>.md` 를 만든다. 쓰기·교체 어느 단계든 `OSError` 가 나면 `finally` 에서 임시 파일을 `unlink(missing_ok=True)` 로 지운 뒤 `FilesystemError` 로 올리고 상태는 그대로 둔다(AC-53 의 '임시 파일도 남지 않는다'). (4) 기록 성공 시 `revision_checks[artifact]` 에 `{"round", "path"(절대 경로), "current_digest", "base_digest"}` 를 추가한다. 면제 상태에 값이 오면 검증 뒤 그때 키를 만든다. (5) CLI `record-review` 에 `--revision-check` 인자를 더하고 `snapshot_dir=Path(args.state).resolve().parent / "snapshots"`, `revision_check_path=args.revision_check` 를 넘긴다. 기존 테스트 11 개(Spec R7.3 열거)는 이름을 유지하고 본문만 고친다 — 통과 픽스처 JSON 을 만들어 `revision_check_path=` 로 넘기거나 legacy 픽스처 상태를 쓴다. 그 갱신을 판정하는 AC-54 의 테스트는 Spec AC-47 의 배치대로 `test_content_contracts.py` 에 두므로 T8 이 소유한다. T8 의 스캐너 규칙: `test_quality_state.py` 의 각 `def test_` 본문에서 `re.search(r"(?<!_unverified)record_review\(|\"record-review\"", body)` 이고 `re.search(r"round_number=[23]|valid_review\(\"(spec|plan)\", [23]|for round_number in \((1, 2|1, 2, 3)\)|range\(1, limit \+ 1\)", body)` 이며 `"code"` 만 다루는 테스트와 `rounds["plan"] == 0` 을 단언하는 거부 전용 테스트(`test_review_round_must_be_next_round`)를 제외한 집합이 Spec R7.3 의 11 개와 같음을 단언한다.
- **통과 확인**: 소유 AC 의 테스트 9개를 `CMD-2 -k <이름>` 으로 하나씩 돌려 전부 통과시킨다 — `test_record_review_writes_snapshot_with_reviewed_digest`(AC-27), `test_record_review_round_two_requires_revision_check`(AC-28), `test_record_review_rejects_mismatched_revision_check`(AC-29), `test_record_review_stores_revision_check_entry`(AC-30), `test_revision_check_option_rejected_for_code_review`(AC-31), `test_legacy_state_without_revision_checks_is_exempt`(AC-32), `test_new_state_has_empty_revision_checks_and_load_does_not_inject`(AC-33), `test_cli_record_review_accepts_revision_check_flag`(AC-34), `test_snapshot_write_failure_leaves_state_unchanged`(AC-53). 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.

### T6. policy 문서와 유지보수 문서

대상 AC: AC-37, AC-40

- **실패 확인**: 이 태스크가 소유한 AC 의 테스트 2개를 먼저 작성한다 — `test_revision_check_policy_contract`(AC-37), `test_maintenance_doc_covers_revision_check`(AC-40). 작성 직후 각각을 `CMD-2 -k <이름>` 으로 돌리면 대상 코드가 없어 전부 실패한다.
- **구현**: `references/revision-check-policy.md` 를 만든다 — Spec R1.4 의 (a)~(d) 전문(같은 문언), R2·R3·R4.3 의 칸 종류 이름 전부(`R→추적행`, `R→AC`, `추적행 AC 존재`, `추적행→R`, `R 수=추적 행 수`, `AC→R`, `AC→판정수단`, `AC→CMD 존재`, `AC 번호 연속`, `중복 정의`, `참조 무결성`, `문법 미충족`, `Spec AC→Plan 추적행`, `Plan 추적행→Spec AC`, `AC→태스크`, `태스크 존재`, `태스크 대상 AC→추적행`, `추적행→태스크 대상 AC`, `AC 등장 행에 판정수단 동반`, `추적행 CMD 존재`, `파급표`), 개정 노트 헤더 문자열과 다섯 열의 뜻과 대체값(`자체 개정`·`치환 없음`), 종료 코드 셋, 라운드 규칙(스냅숏 base·digest 대조·라운드 1 면제·`revision_checks` 키 부재 면제·`record-review` 검증 항목), R3.4 의 태스크 본문 CMD 예외 문언, § Security and risk 포착 범위 표 그대로. `docs/quality-goal-maintenance.md` 에 `## 개정 후 자기 회귀 점검` 절을 더해 `revision_check.py --artifact` 로 시작하는 명령, `snapshots/`, `revision_checks` 키 부재 면제를 싣는다.
- **통과 확인**: 소유 AC 의 테스트 2개를 `CMD-2 -k <이름>` 으로 하나씩 돌려 전부 통과시킨다 — `test_revision_check_policy_contract`(AC-37), `test_maintenance_doc_covers_revision_check`(AC-40). 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.

### T7. `SKILL.md` 절차·경로·버전

대상 AC: AC-35, AC-36, AC-39, AC-41, AC-42, AC-51

- **실패 확인**: 이 태스크가 소유한 AC 의 테스트 4개를 먼저 작성한다 — `test_skill_revision_check_procedure_contract`(AC-35), `test_skill_lists_revision_check_supporting_paths`(AC-36), `test_skill_version_is_major_bumped`(AC-39), `test_skill_names_identifier_grammar_for_authors`(AC-51). 작성 직후 각각을 `CMD-2 -k <이름>` 으로 돌리면 대상 코드가 없어 전부 실패한다. `CMD-3`·`CMD-4` 는 현재도 통과하므로 회귀 기준선으로 먼저 기록한다.
- **구현**: `SKILL.md` 를 세 곳만 고친다. (1) `### Spec` 과 `### Plan` 절 끝에 라운드 2 이상 절차 문단을 더한다 — 개정과 `<artifact>-revision-notes.md` 작성 → `set-artifact` 재등록 → `python3 ${CLAUDE_SKILL_DIR}/scripts/revision_check.py --artifact spec|plan --current <artifacts[artifact] 절대 경로> [--spec <artifacts.spec 절대 경로>] --state <project_root>/.claude/quality-state/<task-id>/state.json --out <같은 디렉터리>/revision-check-<artifact>-r<round>.json` 실행(plan 에만 `--spec`) → 종료 코드 `0` 까지 반복(라운드 소모 없음) → 리뷰어 근거에 점검 JSON 과 노트 경로 포함 → `record-review --revision-check`. 그리고 초안 작성 지시에 "산출물은 `references/revision-check-policy.md` 의 식별자 문법을 따른다 — `- **R<n>.<m>**`, `- **AC-<n>**`, `[실행]`, `[문서]`, 추적표, 판정 명령 표, `### T<n>.`, `대상 AC:`" 를 넣는다. (2) 참조 경로 목록에 `${CLAUDE_SKILL_DIR}/scripts/revision_check.py`, `${CLAUDE_SKILL_DIR}/references/revision-check-policy.md`, `${CLAUDE_SKILL_DIR}/schemas/revision-check.schema.json` 세 줄. (3) frontmatter `version: 5.0.0`. 일곱 보존 절(`### Approval`, `### Implementation`, `### Code review`, `## Review invocation contract`, `## Codex invocation contract`, `## Independent verification`, `## Safety rules`)은 한 글자도 바꾸지 않는다. 500 행 미만을 지킨다(현재 372, 여유 127).
- **통과 확인**: 소유 AC 의 테스트 4개를 `CMD-2 -k <이름>` 으로 하나씩 돌려 전부 통과시킨다 — `test_skill_revision_check_procedure_contract`(AC-35), `test_skill_lists_revision_check_supporting_paths`(AC-36), `test_skill_version_is_major_bumped`(AC-39), `test_skill_names_identifier_grammar_for_authors`(AC-51). 명령으로 판정하는 AC — `CMD-3`(AC-41), `CMD-4`(AC-42). 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.

### T8. 전수 회귀와 자기 적용

대상 AC: AC-43, AC-44, AC-45, AC-46, AC-47, AC-54

- **착수 조건**: T1~T7 이 각자의 통과 확인을 기록했을 것.
- **실패 확인**: 이 태스크의 테스트 셋은 T1~T7 산출물에 대한 회귀 가드라 작성 즉시 통과하는 것이 기대다. 그래서 실패 기록은 '테스트가 아직 없음' 으로 남긴다 — 테스트를 작성하기 전에 `CMD-2 -k test_round_limits_required_checks_threshold_unchanged`(AC-46), `CMD-2 -k test_fixtures_cover_each_cell_kind`(AC-47), `CMD-2 -k test_round_two_legacy_tests_were_updated_not_renamed`(AC-54)를 각각 돌려 매칭 0건의 종료 코드 `5`(`NO TESTS RAN`)를 기록한다. 명령 판정 AC 의 기준선도 함께 기록한다 — `CMD-1`(AC-44)은 T1 이전에 `Ran 240 tests` / `OK`, `CMD-5`(AC-43)는 T1 이전에 `기존 테스트 보존`, `CMD-6`(AC-45)은 `revision_check.py` 가 없으면 `can't open file` 로 실패한다.
- **구현**: 실패 확인에서 부재를 기록한 세 테스트를 이제 `tests/test_content_contracts.py` 에 추가한다 — `test_round_limits_required_checks_threshold_unchanged`(AC-46)와 `test_fixtures_cover_each_cell_kind`(AC-47) 는 다음과 같다. 앞의 것은 `quality_state.ROUND_LIMITS == {"spec": 3, "plan": 2, "code": 3}`, `validate_review.SCORE_THRESHOLD == 85`, `set(REQUIRED_CHECKS) == {"spec", "plan", "code"}`, 세 루브릭 `## Pass gate` 절에 `85` 존재를 단언한다. 뒤의 것은 `tests/fixtures/revision-check/` 의 다섯 파일 존재와 각 파일명이 `test_revision_check.py` 소스에 등장함, 그리고 Spec AC-47 의 파일 배치(AC-1~26·48~50·52 의 테스트 이름이 `test_revision_check.py` 에, AC-27~34·53 이 `test_quality_state.py` 에, AC-35~40·46·47·51·54 가 `test_content_contracts.py` 에 `def` 로 존재)를 Spec 의 AC 목록에서 읽은 이름으로 단언한다. 그리고 `test_round_two_legacy_tests_were_updated_not_renamed`(AC-54)를 같은 파일에 추가한다 — T5 가 정한 스캐너 규칙(`record_review(`/`"record-review"` 호출과 라운드 2 이상 표시의 동반, `code` 전용·거부 전용 제외)으로 `test_quality_state.py` 를 훑은 집합이 Spec R7.3 의 11 개 이름과 같고, 각 본문이 `revision_check_path=`·`--revision-check` 또는 legacy 픽스처를 쓰며, 11 개 이름이 존재함을 단언한다. 그 밖에 새 행동을 만들지 않는다.
- **통과 확인**: 소유 AC 의 테스트 3개를 `CMD-2 -k <이름>` 으로 하나씩 돌려 전부 통과시킨다 — `test_round_limits_required_checks_threshold_unchanged`(AC-46), `test_fixtures_cover_each_cell_kind`(AC-47), `test_round_two_legacy_tests_were_updated_not_renamed`(AC-54). 명령으로 판정하는 AC — `CMD-5`(AC-43), `CMD-1`(AC-44), `CMD-6`(AC-45). 마지막으로 `CMD-1` 을 돌려 회귀가 없는지 본다.
- **CMD-6 실패 처리(AC-45)**: 최종 스크립트가 승인된 `spec.md` 에서 빈 칸을 보고하면 `spec.md` 를 고치지 않는다. 먼저 그 칸이 Spec R1.4·R2 의 규칙대로 산출됐는지 프로토타입 결과(`evidence/proto-self-spec-r3.md`, 295 칸·빈 칸 0)와 대조한다 — 규칙과 다르면 스크립트 결함이므로 스크립트를 고치고, 규칙대로인데 Spec 이 자기 규칙을 어긴 것이면 구현을 멈추고 사용자에게 Spec 재승인 여부를 묻는다(승인 digest 가 바뀌므로 오케스트레이터가 임의로 진행하지 않는다).
- **추가 확인**: `git status --porcelain --untracked-files=all` 의 모든 경로가 `dot_claude/skills/quality-goal/` 하위, `docs/quality-goal-maintenance.md`, `docs/development/2026-09-06-61-quality-goal-revision-regression-check/` 하위 셋 중 하나다. `chezmoi apply` 는 실행하지 않는다.

## Verification commands

```bash
QG_PY="${QG_PY:-$(command -v python3.14 || command -v python3.13 || command -v python3.12)}"
QG_BASE=b30a0dee8465b9b8a3cf5243a47740b3c2116a24
A=docs/development/2026-09-06-61-quality-goal-revision-regression-check
```

`QG_PY` 가 비어 있으면 3.12 이상 인터프리터가 없다는 뜻이며 아래 명령을 실행하지 않는다.

| 순서 | ID | 명령 | 기대 결과 |
|---|---|---|---|
| 1 | CMD-1 | `"$QG_PY" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)' && PYTHONDONTWRITEBYTECODE=1 "$QG_PY" -m unittest discover -s dot_claude/skills/quality-goal/tests -p 'test_*.py'` | 종료 코드 0, `OK`, `Ran N tests` 의 N > 240 |
| 2 | CMD-2 | `"$QG_PY" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)' && PYTHONDONTWRITEBYTECODE=1 "$QG_PY" -m unittest discover -s dot_claude/skills/quality-goal/tests -p 'test_*.py' -k <테스트 이름>` | 종료 코드 0. 매칭 0건이면 5 |
| 3 | CMD-3 | `wc -l < dot_claude/skills/quality-goal/SKILL.md` | 500 미만 |
| 4 | CMD-4 | 아래 § CMD-4 전문 (`spec.md` § CMD-4 상세와 같은 검사. 인터프리터만 `python3` → `"$QG_PY"`) | 종료 코드 0, `보존 대상 절 불변` |
| 5 | CMD-5 | 아래 § CMD-5 전문 (`spec.md` § CMD-5 상세와 같은 검사. 인터프리터만 `python3` → `"$QG_PY"`) | 종료 코드 0, `기존 테스트 보존`(고유 239 부분집합) |
| 6 | CMD-6 | `"$QG_PY" dot_claude/skills/quality-goal/scripts/revision_check.py --artifact spec --current "$PWD/$A/spec.md" && "$QG_PY" dot_claude/skills/quality-goal/scripts/revision_check.py --artifact plan --current "$PWD/$A/plan.md" --spec "$PWD/$A/spec.md"` | 두 호출 모두 종료 코드 0 |

기준선은 `QG_BASE` 에서 CMD-1 이 `Ran 240 tests` / `OK` 인 것이다(3.14.7·3.12.14 실측). 이 저장소에 lint·type check·build·E2E 구성은 없다 — `not configured` 로 보고한다.

### CMD-4 전문

```bash
git show "$QG_BASE:dot_claude/skills/quality-goal/SKILL.md" > /tmp/qg-skill-base.md
QG_BASE=$QG_BASE "$QG_PY" - <<'EOF'
import re, pathlib, os, subprocess
KEEP = ["### Approval", "### Implementation", "### Code review",
        "## Review invocation contract", "## Codex invocation contract",
        "## Independent verification", "## Safety rules"]
def sections(text):
    out, cur = {}, None
    for line in text.splitlines():
        if re.match(r"^#{2,3} ", line):
            cur = line.strip(); out[cur] = []
        elif cur: out[cur].append(line)
    return out
base = sections(pathlib.Path("/tmp/qg-skill-base.md").read_text())
cur = sections(pathlib.Path("dot_claude/skills/quality-goal/SKILL.md").read_text())
bad = [k for k in KEEP if base.get(k) != cur.get(k)]
assert not bad, bad
root = "dot_claude/skills/quality-goal/"
for rel in ["templates/spec.md", "templates/plan.md"]:
    old = subprocess.check_output(["git", "show", f"{os.environ['QG_BASE']}:{root}{rel}"], text=True)
    assert old == pathlib.Path(root + rel).read_text(), rel
for rel in ["references/spec-rubric.md", "references/plan-rubric.md", "references/code-rubric.md"]:
    old = subprocess.check_output(["git", "show", f"{os.environ['QG_BASE']}:{root}{rel}"], text=True)
    assert sections(old)["## Pass gate"] == sections(pathlib.Path(root + rel).read_text())["## Pass gate"], rel
print("보존 대상 절 불변")
EOF
```

### CMD-5 전문

```bash
"$QG_PY" - <<'EOF'
import re, subprocess, pathlib
base = "b30a0dee8465b9b8a3cf5243a47740b3c2116a24"
files = ["test_content_contracts.py", "test_quality_state.py", "test_validate_review.py"]
old = set()
for f in files:
    text = subprocess.check_output(["git", "show", f"{base}:dot_claude/skills/quality-goal/tests/{f}"], text=True)
    old |= set(re.findall(r"^\s*def (test_\w+)", text, re.M))
new = set()
for p in pathlib.Path("dot_claude/skills/quality-goal/tests").glob("test_*.py"):
    new |= set(re.findall(r"^\s*def (test_\w+)", p.read_text(), re.M))
assert len(old) == 239, len(old)  # 240 건 실행, 고유 이름 239 (test_frontmatter_contract 가 두 클래스)
assert old <= new, sorted(old - new)
print("기존 테스트 보존")
EOF
```

## Rollout and rollback

**롤아웃.** chezmoi source 만 바꾼다. 배포는 사용자가 `chezmoi apply` 로 별도 수행한다. 배포 전 진행 중인 goal 의 상태 파일은 `revision_checks` 키가 없어 면제 상태로 계속 기록된다(Spec R6.4).

**호환성.** `schema_version` 1 유지. 새 필드는 `new_state` 가 만들고 `load_state` 는 주입하지 않는다. `record_review` 의 두 새 인자는 키워드 전용·기본값 `None` 이라 기존 세 인자 호출은 라운드 1 과 면제 상태에서 그대로 동작한다.

**롤백 트리거.** CMD-1 이 기존 테스트를 실패시킴, CMD-4 가 보존 절 변경을 보고, CMD-5 가 이름 삭제·개명을 보고, 배포 후 진행 중이던 goal 이 재개되지 않음.

**롤백 절차.** 커밋을 만들지 않으므로 `git checkout -- dot_claude/skills/quality-goal/ docs/quality-goal-maintenance.md` 로 수정 파일을 되돌리고 신설 파일 넷과 디렉터리 하나를 지운다 — `schemas/revision-check.schema.json`, `scripts/revision_check.py`, `references/revision-check-policy.md`, `tests/test_revision_check.py`, `tests/fixtures/revision-check/`. 이 목록은 § File map 의 신설 항목과 1:1 이다. 상태 파일은 손대지 않는다.

**모니터링.** 배포 후 첫 standard goal 의 라운드 2 에서 `snapshots/` 가 생기는지, `record-review` 가 `--revision-check` 없이 거부되는지, 점검 JSON 이 `revision_checks` 에 기록되는지를 `quality_state.py show` 로 확인한다.

## Acceptance-criteria traceability

Spec 의 수용 기준 54건 전부를 태스크와 검증 명령에 매핑한다. 각 AC 는 정확히 한 태스크가 소유한다. `CMD-2 -k <이름>` 은 § Verification commands 의 CMD-2 에 그 이름을 넣어 실행한다는 뜻이다. 기대 결과는 Spec 의 AC 문언 그대로다.

| Criterion | Task | Verification command | Expected outcome |
|---|---|---|---|
| AC-1 | T2 점검 스크립트 골격과 Spec 대칭 | `CMD-2 -k test_cli_exit_codes_and_usage` | `revision_check.py` 가 대칭이 완전한 픽스처에 `0`, 빈 칸이 있는 픽스처에 `1` 을 반환하고 `1` 일 때 `--out` JSON 의 `passed` 가 `false` 다. `--artifact plan` 에 `--spec` 누락, `--current` 파일 부재, `--spec` 파일 부재, `--state` 파일 부재, 명시한 `--base` 부재, 명시한 `--base` 가 디렉터리라 읽기 실패, 명시한 `--notes` 부재, 명시한 `--notes` 가 디렉터리라 읽기 실패, `--current` 의 UTF-8 디코딩 실패, `--spec` 의 UTF-8 디코딩 실패, `--state` 의 JSON 파싱 실패, `--state` 와 `--base` 동시 지정, 스냅숏 부재 열세 경우 각각 `2` 를 반환하고(스냅숏 digest 불일치는 AC-18) `--out` 파일이 생기지 않으며, 상대 경로로 준 `--current` 가 작업 디렉터리 기준으로 읽힌다. |
| AC-2 | T2 점검 스크립트 골격과 Spec 대칭 | `CMD-2 -k test_output_matches_schema` | 픽스처 실행의 `--out` JSON 이 `schemas/revision-check.schema.json` 을 통과하고, 최상위 미지 키, `cells[].status` 가 `ok`·`empty` 밖의 값, `notes` 의 다섯 필드 중 하나 누락, `ripple[]` 항목의 미지 키, `cells[]` 항목의 `key` 누락 다섯 변형이 각각 스키마 검증에 실패한다. 독립 모드 출력의 `round` 는 `null`, `--state` 모드(`rounds.spec == 1`)의 `round` 는 `2` 이고, `current_digest` 는 `--current` 의 SHA-256, plan 의 `spec_digest` 는 `--spec` 의 SHA-256, spec 의 `spec_digest` 는 `null` 이다. |
| AC-3 | T4 개정 diff·파급표·개정 노트 점검 | `CMD-2 -k test_stdout_prints_ripple_and_empty_cell_tables` | 빈 칸이 있는 픽스처의 표준 출력에서 공백이 아닌 모든 줄이 `#` 또는 `|` 로 시작하고, `| 종류 | 키 | 상태 | 상세 | 행 |` 표의 데이터 행 집합이 JSON `cells` 중 `empty` 항목의 (`kind`,`key`,`detail`,`line`) 집합과 같고, `| 요구사항 | 판정 AC | Plan 추적행 | 태스크 | 판정 명령/테스트 |` 표의 데이터 행 집합이 `ripple` 항목 집합과 값까지 같으며, 파급표의 빈 칸이 `**빈 칸**` 으로 표시된다. |
| AC-4 | T2 점검 스크립트 골격과 Spec 대칭 | `CMD-2 -k test_id_grammar_ignores_code_blocks` | 펜스 코드 블록 안의 `AC-999`·`R9.99`·`D99`·`T99`·`CMD-99`, 백틱 하나로 감싼 `AC-998`·`CMD-98`·`D98`·`T98`, 백틱 둘로 감싼 `R8.88`·`AC-997` 이 정의로도 참조로도 세어지지 않아 `참조 무결성` 칸을 만들지 않고, AC 본문에서 코드 스팬 안의 `[실행] (CMD-7 …)` 은 판정 수단으로 읽히지 않는다. |
| AC-5 | T2 점검 스크립트 골격과 Spec 대칭 | `CMD-2 -k test_missing_spec_traceability_marks_every_requirement_empty` | 추적표 절이 없는 Spec 과 절은 있어도 `| R… | AC-… |` 행이 없는 Spec 에서 정의된 요구사항 수만큼 `R→추적행` 칸이 `empty` 이고, 헤딩이 `## Requirements traceability` 인 Spec 과 `## 요구사항 추적표` 인 Spec 모두에서 행이 매핑 원천으로 읽힌다. |
| AC-6 | T2 점검 스크립트 골격과 Spec 대칭 | `CMD-2 -k test_check_is_read_only` | 실행 전후 픽스처 디렉터리와 상태 디렉터리의 모든 파일(`--current`·`--spec`·`--base`·노트·상태·스냅숏)의 SHA-256 이 같고 `--out` 외의 새 파일이 생기지 않으며, `revision_check.py` 소스가 `subprocess`·`socket`·`urllib`·`http` 를 import 하지 않는다. |
| AC-7 | T2 점검 스크립트 골격과 Spec 대칭 | `CMD-2 -k test_requirement_without_trace_row_or_ac_is_empty` | 추적표 행이 없는 요구사항은 `R→추적행`, 행은 있지만 AC 가 없는 요구사항은 `R→AC`, 미정의 AC 를 가리키는 행은 `추적행 AC 존재` 칸이 `empty` 다. |
| AC-8 | T2 점검 스크립트 골격과 Spec 대칭 | `CMD-2 -k test_ghost_trace_row_and_count_mismatch` | 정의 없는 요구사항을 가리키는 추적표 행은 `추적행→R` 칸이 `empty` 이고, 정의 수와 행 수가 다르면 `R 수=추적 행 수` 칸이 `empty` 다. |
| AC-9 | T2 점검 스크립트 골격과 Spec 대칭 | `CMD-2 -k test_orphan_ac_and_missing_means` | 어느 추적표 행에도 없는 AC 는 `AC→R`, `[실행]`·`[문서]` 표기가 없는 AC 는 `AC→판정수단` 칸이 `empty` 다. `[문서] \`docs/x.md\` § 절` 처럼 파일명 토큰이 따르는 AC 는 `ok` 이고 `[문서]` 뒤에 파일명 토큰이 없는 AC 는 `AC→판정수단` 이 `empty` 이며, 코드 스팬 밖에 `[실행] (CMD-1 …)` 과 `[문서]` 가 차례로 있는 AC 는 마지막 표기 `[문서]` 가 판정 수단이 되어 `AC→CMD 존재` 칸을 만들지 않는다. |
| AC-10 | T2 점검 스크립트 골격과 Spec 대칭 | `CMD-2 -k test_execution_ac_requires_cmd_row` | `[실행] (CMD-9 …)` 를 쓰는데 판정 명령 표에 `CMD-9` 행이 없으면 `AC→CMD 존재` 칸이 `empty` 다. |
| AC-11 | T2 점검 스크립트 골격과 Spec 대칭 | `CMD-2 -k test_ac_numbering_gap_and_duplicate_definition` | `AC-1`·`AC-2`·`AC-4` 만 정의된 Spec 은 `AC 번호 연속` 칸이, 같은 `R1.1` 이 두 줄에 정의된 Spec 과 같은 `AC-3` 이 두 줄에 정의된 Spec 은 각각 `중복 정의` 칸이 `empty` 다. |
| AC-12 | T2 점검 스크립트 골격과 Spec 대칭 | `CMD-2 -k test_dangling_reference_is_empty_cell` | 본문이 코드 스팬 밖에서 정의되지 않은 `AC-77`·`D9`·`R7.7`·`CMD-9` 를 참조하면 각각 `참조 무결성` 칸이 `empty` 이고, `AC-77` 을 두 줄에서 참조한 픽스처에서 그 칸의 `line` 이 첫 등장 행, `detail` 이 `2` 회를 담는다. |
| AC-13 | T3 Plan 대칭과 정의 수 하한 | `CMD-2 -k test_plan_ac_set_equals_spec` | Spec 에만 있는 AC 는 `Spec AC→Plan 추적행`, Plan 추적표에만 있는 AC 는 `Plan 추적행→Spec AC` 칸이 `empty` 다. |
| AC-14 | T3 Plan 대칭과 정의 수 하한 | `CMD-2 -k test_task_target_list_symmetry` | 추적표가 T2 에 배정한 AC 가 T2 의 `대상 AC:` 목록에 없으면 `추적행→태스크 대상 AC`, 목록에는 있는데 추적표가 다른 태스크에 배정했으면 `태스크 대상 AC→추적행` 칸이 `empty` 이고, 존재하지 않는 `T9` 를 지정한 행은 `태스크 존재` 칸이, Task 셀이 비어 있거나 `T` ID 가 없는 행은 `AC→태스크` 칸이 `empty` 다. |
| AC-15 | T3 Plan 대칭과 정의 수 하한 | `CMD-2 -k test_same_line_rule_catches_plan_06_shape` | `PLAN-06` 형태 픽스처 — 추적표 행이 ``[문서] `spec.md` § Test strategy`` 이고 소유 태스크 본문의 AC 등장 행이 `docs/quality-goal-maintenance.md` 만 언급하며 다른 문단에 `spec.md` 가 있음 — 에서 `AC 등장 행에 판정수단 동반` 칸이 `empty` 이고 `detail` 이 `spec.md` 를 누락으로 싣는다. |
| AC-16 | T3 Plan 대칭과 정의 수 하한 | `CMD-2 -k test_same_line_rule_accepts_colocated_means` | 판정 수단 셀이 백틱으로 감싼 `` `CMD-2 -k test_alpha` `` 인 추적표 행에서 토큰이 `CMD-2` 와 `test_alpha` 둘로 뽑히고(`-k` 는 아님), 소유 태스크 본문에 `` `CMD-2 -k`로 `test_alpha`(AC-3) `` 처럼 같은 행에 둘과 AC 가 있으면 그 칸은 `ok` 이고, `test_alpha` 가 그 AC 등장 행이 아닌 다른 행에만 있으면 `empty` 이며 `detail` 이 `test_alpha` 를 누락으로 싣고, `CMD-2` 만 그 행에 없으면 `detail` 이 `CMD-2` 를 싣는다. |
| AC-17 | T3 Plan 대칭과 정의 수 하한 | `CMD-2 -k test_plan_cmd_and_reference_integrity` | Plan 판정 명령 표에 없는 `CMD-8` 을 쓴 추적표 행은 `추적행 CMD 존재` 칸이, 태스크 본문의 코드 스팬 안에서만 참조되는 `CMD-7` 과 Plan 본문의 정의 없는 `T12`·`AC-66`·`R6.6`·`D6` 참조는 각각 `참조 무결성` 칸이 `empty` 다. |
| AC-18 | T4 개정 diff·파급표·개정 노트 점검 | `CMD-2 -k test_base_snapshot_located_and_digest_checked` | spec 과 plan 각각에 대해 `--state` 모드에서 `snapshots/<artifact>-r1.md` 의 SHA-256 이 `reviews[artifact][-1].artifact_digest` 와 같으면 `base_digest` 가 그 값이고 `round` 가 `2` 이며, `rounds.spec == 2` 이면 `round` 가 `3` 이고, 스냅숏 파일이 없거나 digest 가 다르면 종료 코드 `2` 다. |
| AC-19 | T4 개정 diff·파급표·개정 노트 점검 | `CMD-2 -k test_round_one_has_no_base_and_no_notes_requirement` | spec 과 plan 각각에 대해 `rounds[artifact] == 0` 인 상태에서 `round` 는 `1`, `base_digest` 는 `null`, `touched_requirements` 는 빈 목록, `notes.required` 는 `false` 이고 노트 파일이 없어도 `passed` 와 종료 코드는 대칭 결과만 따른다. |
| AC-20 | T4 개정 diff·파급표·개정 노트 점검 | `CMD-2 -k test_touched_requirements_from_diff_spec` | base 와 비교해 `R2.1` 정의 줄만 바꾼 Spec 은 `touched_requirements == ["R2.1"]`, `AC-5` 정의 줄만 바꾼 Spec 은 `AC-5` 를 가리키는 요구사항만, `R3.1` 추적표 행만 바꾼 Spec 은 `["R3.1"]`, `R3.1` 정의 바로 뒤에 새 줄을 삽입만 한 Spec 은 삽입 줄이 속한 요구사항만이며, base 에 있던 `R4.2` 정의와 `AC-8` 정의를 지우면 `removed_ids` 가 둘을 담는다. |
| AC-21 | T4 개정 diff·파급표·개정 노트 점검 | `CMD-2 -k test_touched_requirements_from_diff_plan` | base 와 비교해 `AC-7` 추적표 행만 바꾼 Plan 은 `AC-7` 의 요구사항만, `T3` 본문만 바꾼 Plan 은 `T3` 에 배정된 AC 들의 요구사항만 `touched_requirements` 에 있고, base 의 `T3` 절과 `CMD-2` 행을 지운 Plan 은 `removed_ids` 에 둘을 담는다. |
| AC-22 | T4 개정 diff·파급표·개정 노트 점검 | `CMD-2 -k test_ripple_row_per_touched_requirement_with_empty_marking` | 건드린 요구사항 둘이 있는 plan 점검에서 `ripple` 이 정확히 두 항목이고 완전한 행의 `acceptance_criteria`·`plan_rows`·`tasks`·`commands` 가 픽스처의 기대값과 같으며, 판정 AC 가 없는 요구사항, 추적행이 없는 AC 만 가진 요구사항, 태스크가 없는 행, 명령이 없는 행 네 경우 각각 `파급표` 종류의 `empty` 칸을 만들어 종료 코드가 `1` 이다. spec 점검의 `ripple` 항목은 `plan_rows`·`tasks` 가 `null` 이고 그 둘로는 `empty` 칸이 생기지 않으며, `[문서] \`docs/x.md\` § 절` 표기의 AC 만 가진 요구사항은 `commands` 가 `["docs/x.md"]` 이라 `파급표` 칸이 `ok` 다. |
| AC-23 | T4 개정 diff·파급표·개정 노트 점검 | `CMD-2 -k test_notes_section_required_from_round_two` | `rounds.spec == 1` 인 상태에서 노트 파일이 없거나 `## 라운드 2 개정` 헤딩이 없으면 `notes.required` 가 `true`, `section_found` 가 `false`, `passed` 가 `false`, 종료 코드 `1` 이다. `--notes` 를 생략하면 `notes.path` 가 `--current` 디렉터리의 `spec-revision-notes.md` 이고 주면 그 경로다. `rounds.plan == 1` 은 `plan-revision-notes.md` 의 `## 라운드 2 개정`, `rounds.spec == 2` 는 `## 라운드 3 개정` 을 찾는다. |
| AC-24 | T4 개정 diff·파급표·개정 노트 점검 | `CMD-2 -k test_notes_table_header_and_row_coverage` | 헤더가 `| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |` 와 다른 표는 인식되지 않아 모든 건드린 요구사항이 `missing_rows` 에 들어가고, 헤더가 같고 건드린 요구사항마다 행이 있으며 각 행의 `함께 바뀐 항목` 셀이 그 요구사항의 파급표 AC 전부를 담으면 `missing_rows` 가 비어 있고, 어느 행이 파급표 AC 하나를 빠뜨리면 `missing_rows` 에 `<요구사항>/<AC>` 가, AC ID 는 있지만 뒤 괄호가 `일치`/`모순` 으로 시작하지 않으면 `<요구사항>/<AC>/판정` 이 있다. |
| AC-25 | T4 개정 diff·파급표·개정 노트 점검 | `CMD-2 -k test_notes_blank_cell_is_empty` | 행의 `치환 근거` 셀이 빈 문자열, 공백만, `-`, `—` 네 경우 각각 `blank_cells` 에 `<요구사항>/치환 근거` 가 있고, 나머지 네 열(`요구사항`·`해소 finding`·`함께 바뀐 항목`·`상호작용 판정`) 각각에 같은 규칙이 적용되며, 형식이 맞는 임의의 비공백 문장은 `blank_cells` 에 들어가지 않는다. |
| AC-26 | T4 개정 diff·파급표·개정 노트 점검 | `CMD-2 -k test_notes_failure_sets_passed_false_and_exit_one` | 대칭 칸이 전부 `ok` 여도 `missing_rows` 또는 `blank_cells` 가 비어 있지 않으면, 또는 `notes.required` 가 `true` 인데 `section_found` 가 `false` 이면 `passed` 가 `false` 이고 종료 코드가 `1` 이다. 대칭 칸이 전부 `ok` 이고 `notes.required` 가 `false` 이면 노트가 없어도 `passed` 가 `true` 다. |
| AC-27 | T5 `quality_state.py` 스냅숏·`--revision-check`·면제 | `CMD-2 -k test_record_review_writes_snapshot_with_reviewed_digest` | spec 과 plan 각각에서 `record_review(..., snapshot_dir=<dir>)` 라운드 1 성공 뒤 `<dir>/<artifact>-r1.md` 가 존재하고 그 SHA-256 이 기록된 `artifact_digest` 와 같으며, 존재하지 않던 `snapshot_dir` 가 만들어지며, `snapshot_dir=None` 이거나 `artifacts[artifact]` 가 `null` 이거나 `code` 리뷰이면 스냅숏이 생기지 않고, 라운드 1 의 기존 세 인자 호출이 그대로 성공한다. |
| AC-28 | T5 `quality_state.py` 스냅숏·`--revision-check`·면제 | `CMD-2 -k test_record_review_round_two_requires_revision_check` | `revision_checks` 키가 있는 상태에서 spec 라운드 2, spec 라운드 3, plan 라운드 2 의 `record-review` 를 `--revision-check` 없이 호출하면 각각 `StateError` 이고 오류 메시지에 `--revision-check` 와 라운드 번호가 있으며 `rounds`·`reviews` 가 바뀌지 않는다. |
| AC-29 | T5 `quality_state.py` 스냅숏·`--revision-check`·면제 | `CMD-2 -k test_record_review_rejects_mismatched_revision_check` | 파일 부재, `artifact` 불일치, `round` 불일치, `current_digest` 가 `--artifact-digest` 와 다름, `passed: false`, 스키마 위반(미지 키) 여섯 경우 각각 `StateError` 이고 상태가 바뀌지 않는다. 리뷰 JSON 의 `round` 불일치와 `--revision-check` 누락이 동시면 라운드 불일치 오류가, `--revision-check` 누락과 리뷰 JSON 스키마 위반이 동시면 `--revision-check` 오류가 보고된다. |
| AC-30 | T5 `quality_state.py` 스냅숏·`--revision-check`·면제 | `CMD-2 -k test_record_review_stores_revision_check_entry` | spec 과 plan 각각에서 통과한 점검 JSON 으로 기록하면 `revision_checks[artifact]` 마지막 항목의 `round`·`current_digest`·`base_digest` 가 JSON 의 값과 같고 `path` 가 넘긴 경로의 절대 경로이며, 라운드 1 에서 인자를 주면 같은 검증 뒤 기록되며 `passed: false` 면 라운드 1 에서도 `StateError` 다. |
| AC-31 | T5 `quality_state.py` 스냅숏·`--revision-check`·면제 | `CMD-2 -k test_revision_check_option_rejected_for_code_review` | `code` 리뷰 `record-review` 에 `--revision-check` 를 주면 `StateError` 다. |
| AC-32 | T5 `quality_state.py` 스냅숏·`--revision-check`·면제 | `CMD-2 -k test_legacy_state_without_revision_checks_is_exempt` | `revision_checks` 키가 없는 상태 픽스처에서 spec 라운드 2 와 plan 라운드 2 의 `record-review` 가 `--revision-check` 없이 성공하고 키가 생기지 않으며, 인자를 주면 검증 뒤 `revision_checks` 키가 그때 만들어져 그 항목만 담는다. |
| AC-33 | T5 `quality_state.py` 스냅숏·`--revision-check`·면제 | `CMD-2 -k test_new_state_has_empty_revision_checks_and_load_does_not_inject` | `new_state` 결과에 `revision_checks == {"spec": [], "plan": []}` 이 있고, 키 없는 상태를 `load_state` 로 읽으면 키가 여전히 없으며 `schema_version` 이 1 이다. |
| AC-34 | T5 `quality_state.py` 스냅숏·`--revision-check`·면제 | `CMD-2 -k test_cli_record_review_accepts_revision_check_flag` | CLI `quality_state.py record-review --state … --review … --artifact-digest … --revision-check …` 가 `--revision-check` 값을 `revision_check_path` 로, `--state` 의 부모 디렉터리 아래 `snapshots` 를 `snapshot_dir` 로 넘겨 함수와 같은 상태 결과와 스냅숏 파일을 만들고, 인자 없는 라운드 2 호출은 0 이 아닌 종료 코드와 오류 메시지를 낸다. |
| AC-35 | T7 `SKILL.md` 절차·경로·버전 | `CMD-2 -k test_skill_revision_check_procedure_contract` | `SKILL.md` 의 `### Spec` 과 `### Plan` 절이 각각 `set-artifact` 재등록 뒤 `revision_check.py` 를 `--state` 로 실행하는 순서, `record-review` 의 `--revision-check`, 라운드 2 이상, 개정 노트(`revision-notes.md`), 리뷰어 근거 전달, 종료 코드 `0` 까지 반복을 언급한다. |
| AC-36 | T7 `SKILL.md` 절차·경로·버전 | `CMD-2 -k test_skill_lists_revision_check_supporting_paths` | `SKILL.md` 참조 경로 목록에 `${CLAUDE_SKILL_DIR}/scripts/revision_check.py`, `${CLAUDE_SKILL_DIR}/references/revision-check-policy.md`, `${CLAUDE_SKILL_DIR}/schemas/revision-check.schema.json` 세 줄이 있다. |
| AC-37 | T6 policy 문서와 유지보수 문서 | `CMD-2 -k test_revision_check_policy_contract` | `references/revision-check-policy.md` 가 식별자 문법 다섯 종과 코드 스팬 인용 규칙, R2·R3·R4.3 의 칸 종류 이름 전부, 개정 노트 헤더 문자열과 다섯 열의 뜻과 대체값(`자체 개정`·`치환 없음`), 종료 코드 셋, 라운드 규칙(스냅숏 base·digest 대조·라운드 1 면제·`revision_checks` 키 부재 면제·`record-review` 검증 항목), 그리고 § Security and risk 의 포착 범위 표를 그대로 담아 #70 교차 회귀 9건(1~5 는 성격이 같아 한 행에 다섯 번호를 함께 적는다)·#42 3건·#61 코멘트 3 사례가 모두 등장하고 각 행에 포착 칸 종류 또는 미포착 사유(Non-goal 2·3·4)가 있다. |
| AC-38 | T1 점검 산출물 스키마 | `CMD-2 -k test_revision_check_schema_contract` | `schemas/revision-check.schema.json` 이 최상위 `type: object`, `additionalProperties: false`, R1.2 의 열둘 `required` 를 가지며, `cells[]`·`ripple[]`·`notes` 하위 객체도 `additionalProperties: false` 와 R1.2 의 필수 키를 가지고, `cells[].line` 을 문자열로 준 JSON 과 `empty_cells` 를 문자열로 준 JSON 이 각각 검증에 실패한다. |
| AC-39 | T7 `SKILL.md` 절차·경로·버전 | `CMD-2 -k test_skill_version_is_major_bumped` | `SKILL.md` frontmatter 의 `version` 이 `5.0.0` 이다. |
| AC-40 | T6 policy 문서와 유지보수 문서 | `CMD-2 -k test_maintenance_doc_covers_revision_check` | `docs/quality-goal-maintenance.md` 에 `## 개정 후 자기 회귀 점검` 절이 있고 그 절이 `revision_check.py --artifact` 로 시작하는 명령, `snapshots/`, `revision_checks` 키 부재 면제를 담는다. |
| AC-41 | T7 `SKILL.md` 절차·경로·버전 | `CMD-3` | `SKILL.md` 가 500 행 미만이다. |
| AC-42 | T7 `SKILL.md` 절차·경로·버전 | `CMD-4` | `SKILL.md` 의 R7.3 일곱 절, 세 루브릭의 `## Pass gate` 절, `templates/spec.md`, `templates/plan.md` 가 base revision 과 바이트 단위로 같다. |
| AC-43 | T8 전수 회귀와 자기 적용 | `CMD-5` | base revision 세 테스트 파일의 테스트 메서드 이름 합집합(고유 239 개)이 현재 테스트 이름 집합의 부분집합이다. |
| AC-44 | T8 전수 회귀와 자기 적용 | `CMD-1` | 전체 테스트 스위트가 종료 코드 0, `OK` 로 끝나고 실행 테스트 수가 240 보다 크다. |
| AC-45 | T8 전수 회귀와 자기 적용 | `CMD-6` | 배포 소스의 `revision_check.py` 를 이 작업의 `spec.md` 와 `plan.md` 에 독립 모드로 실행하면 둘 다 종료 코드 `0` 이다. |
| AC-46 | T8 전수 회귀와 자기 적용 | `CMD-2 -k test_round_limits_required_checks_threshold_unchanged` | `quality_state.ROUND_LIMITS == {"spec": 3, "plan": 2, "code": 3}`, `validate_review.SCORE_THRESHOLD == 85`, `REQUIRED_CHECKS` 의 키 집합이 `{"spec", "plan", "code"}` 이고 세 루브릭의 Pass gate 문단이 `85` 를 싣는다. |
| AC-47 | T8 전수 회귀와 자기 적용 | `CMD-2 -k test_fixtures_cover_each_cell_kind` | `tests/fixtures/revision-check/` 에 대칭 완전 Spec·Plan 쌍, `PLAN-06` 형태 Plan, 라운드 2 노트 있음·없음 픽스처가 존재하고 각 파일이 `test_revision_check.py` 에서 한 번 이상 읽히며, AC-1~26·48~50·52 의 테스트 이름은 `test_revision_check.py` 에, AC-27~34·53 은 `test_quality_state.py` 에, AC-35~40·46·47·51·54 는 `test_content_contracts.py` 에 정의돼 있다. |
| AC-48 | T2 점검 스크립트 골격과 Spec 대칭 | `CMD-2 -k test_id_grammar_recognizes_all_definition_forms` | 요구사항 4·AC 8·결정 2·태스크 3·CMD 2(첫째 셀 ID 표 하나, 둘째 셀 ID 표 하나)를 가진 픽스처 쌍에서 파서가 정의 수를 각각 4·8·2·3·2 로 세고, `## Requirements traceability` 의 4 행을 매핑으로 읽는다. |
| AC-49 | T4 개정 diff·파급표·개정 노트 점검 | `CMD-2 -k test_standalone_base_mode` | 독립 모드에서 `--base` 를 주면 digest 대조 없이 `touched_requirements` 가 산출되고 `base_digest` 가 그 파일의 SHA-256, `round` 가 `null`, `notes.required` 가 `false` 이며, 그 JSON 을 `record-review --revision-check` 에 주면 `round` 불일치로 `StateError` 다. |
| AC-50 | T3 Plan 대칭과 정의 수 하한 | `CMD-2 -k test_definition_floor_blocks_empty_artifacts` | 요구사항 정의가 0 인 Spec, AC 정의가 0 인 Spec, 태스크 절이 0 인 Plan, 추적표 AC 행이 0 인 Plan 각각에서 `문법 미충족` 종류의 `empty` 칸이 정확히 하나 있고 `passed` 가 `false`, 종료 코드가 `1` 이며, 개정 노트가 완비돼도 `passed` 가 `true` 가 되지 않는다. |
| AC-51 | T7 `SKILL.md` 절차·경로·버전 | `CMD-2 -k test_skill_names_identifier_grammar_for_authors` | `SKILL.md` 의 `### Spec` 과 `### Plan` 절이 초안 작성 지시에서 `revision-check-policy.md` 의 식별자 문법을 따르라고 지시하고, `- **R<n>.<m>**`, `- **AC-<n>**`, `[실행]`, `[문서]`, 추적표, 판정 명령 표, `### T<n>.`, `대상 AC:` 여덟 표기를 그 지시 안에 열거한다. |
| AC-52 | T3 Plan 대칭과 정의 수 하한 | `CMD-2 -k test_verification_cell_reads_inside_code_spans` | 판정 수단 셀이 `` `CMD-7` `` 처럼 백틱 안에만 있는 추적표 행에서 `CMD-7` 이 Plan 판정 명령 표에 없으면 `추적행 CMD 존재` 칸이 `empty` 이고, 표에 있으면 `ok` 이며, 셀에서 `[\w./-]+\.[A-Za-z0-9]+` 에 맞는 `docs/quality-goal-maintenance.md` 는 토큰으로 뽑히고 `§`·`판정` 은 뽑히지 않는다. |
| AC-53 | T5 `quality_state.py` 스냅숏·`--revision-check`·면제 | `CMD-2 -k test_snapshot_write_failure_leaves_state_unchanged` | `snapshot_dir` 를 쓸 수 없는 경로로 주면 `record_review` 가 `FilesystemError` 를 내고 `rounds`·`reviews`·`revision_checks` 가 바뀌지 않으며, 실패 뒤 `<snapshot_dir>` 에 `spec-r1.md` 도 임시 파일도 남지 않으며, `rounds.spec == 1` 인 상태 디렉터리에 라운드 미기록 `spec-r2.md` 가 남아 있어도 점검이 `spec-r1.md` 를 base 로 써 `base_digest` 가 r1 의 digest 다. |
| AC-54 | T8 전수 회귀와 자기 적용 | `CMD-2 -k test_round_two_legacy_tests_were_updated_not_renamed` | R7.3 의 판정 방법(함수·CLI 두 호출 형태)으로 `test_quality_state.py` 를 기계적으로 훑어 얻은 집합이 R7.3 의 11 개 이름을 모두 포함하고, 그 집합의 각 테스트 본문이 `revision_check_path=`(함수) 또는 `--revision-check`(CLI) 를 넘기거나 `revision_checks` 키 없는 상태 픽스처를 쓰는 둘 중 하나이며, 11 개 이름이 현재 소스에 그대로 존재한다. |

## strict 전용 블록을 제거한 근거

standard 모드다. Spec D10 과 같다 — 인증·권한·결제·PII·마이그레이션·외부 API·프로덕션 인프라 요구사항이 없어 여섯 strict 절은 적용 대상이 아니다.
