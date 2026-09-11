# Quality Goal Implementation Plan

- Task ID: 20260908T011803Z-79-사전-리뷰-critical-4건-최소-수정-예산-소진-시-조합-누락-2b100e8c
- Mode: strict
- Status: PLAN_REVIEW
- Created: 2026-09-08T01:18:03Z
- Updated: 2026-09-08T03:55:00Z
- Source goal: #79 PR 사전 리뷰가 차단한 검증 결과 세탁 결함의 최소 수정 — 재현된 Critical 4건, 같은 원인의 포함 Important, 문서 드리프트, CODE-005를 오프라인 회귀로 닫는다.

## Spec link

승인 대상 Spec은 `/Users/lee-kyu-hwan/code/dotfiles__worktrees/79-feat-contribution-candidate-verifier/docs/development/2026-09-08-79-pr-prereview-critical-fixes/spec.md` 이며 이 Plan이 사용한 digest는 `b84050c0f52220033a576624c1c163fa2dc53da71d293fd8918f78512d5e1f14` 이며 Spec 리뷰 라운드 2 가 PASS 96 으로 기록한 digest 와 같다. 요구사항 R1.1~R4.2 12개와 AC-1~AC-23 23개를 모두 소비한다.

## Global constraints

- 작업 경로는 `/Users/lee-kyu-hwan/code/dotfiles__worktrees/79-feat-contribution-candidate-verifier` 워크트리 하나다. `main`, 다른 워크트리, 전역 설치본(`~/.codex/skills`, `~/.claude/skills`), `$HOME` 설정을 바꾸지 않는다.
- 변경 허용 경로는 `dot_codex/skills/verifying-open-source-contribution-candidates/` 의 `scripts/verify_candidates.py`, `tests/test_verify_candidates.py`, `tests/test_skill_contract.py`, `tests/fixtures/**`, `SKILL.md`, `references/verification-contract.md`, 그리고 `docs/development/2026-09-08-79-pr-prereview-critical-fixes/` 의 이번 실행 문서다.
- 초기 dirty 경로 중 `docs/development/2026-09-06-79-verifying-open-source-contribution-candidates/` 와 `docs/development/2026-09-07-79-verifying-open-source-contribution-candidates-plan-redesign/` 는 불변 이력이다. 읽기만 하고 되돌리지도 않는다. 나머지 두 초기 dirty 경로는 이번 승인 범위의 작업 대상이다.
- commit, push, PR 생성, merge, `chezmoi apply`, 배포, GitHub Issue·댓글 작성을 하지 않는다. 추가 GitHub 요청, `discover` 라이브 재실행, 대상 저장소 코드 실행, 의존성 설치를 하지 않는다.
- Python 은 `/opt/homebrew/bin/python3` 3.14.7, 표준 라이브러리만 사용한다. 모든 판정은 `PYTHONDONTWRITEBYTECODE=1` 로 실행하고 네트워크를 열지 않는다.
- 테스트 우선 순서를 지킨다. 각 태스크는 실패하는 판정을 먼저 기록하고, 최소 구현 후 통과 판정을 기록한다.
- 출력 계약을 넓히지 않는다. `CANDIDATE_FIELDS` 29, `RECHECK_MUTABLE_FIELDS` 9와 여집합 default-deny, `STATUS_REASON_TABLE`, `READINESS_KEYS` 12, `POLICY_CHECK_KEYS` 8, `FAILED_SCOPE_REASONS` 5, `ACCESS_FAILURE_OUTCOMES` 4, `schema_version`, 종료 코드 0/1/2/3/4를 유지한다. 예산 소진은 항상 3, 종료 4는 전 저장소 실제 접근 실패만이다.
- `compute_revision()` 해시 대상 6개 경로가 바뀌므로 어떤 테스트도 revision 을 고정 hash 로 단정하지 않는다.
- `tests/test_skill_contract.py` 의 `test_no_hardcoded_targets_dates_models` 는 스킬 디렉터리의 `.md`·`.json`·`.py` 에서 api-version 표기 줄을 제외한 `20\d{2}-\d{2}-\d{2}` literal 을 거부한다. 신설 recheck fixture 와 단정의 `verified_at`·`observed_at` 은 연도 조각과 나머지 조각을 이어 붙여 만들고 이 형태의 날짜 literal 을 소스에 쓰지 않는다.
- 판정 단정을 통과시키기 위해 약화하는 것을 금지한다. 특히 AC-9 의 recheck 단정(`request-failed` 정책 관찰에 R3.1 차단 규칙 적용)을 `CMD-5` 종료 0 을 얻으려고 완화·삭제·skip 처리하지 않는다. 필요한 선행 구현이 없으면 순서를 바꾸고, 단정은 그대로 둔다.
- Spec 리뷰 라운드 2 의 advisory Low finding `SPEC-009` 를 구현에 반영한다. AC-8 의 "매핑 밖 경로" 대조군은 **fixture 전용 합성 경로** 다. 생산 코드의 `discover_policy_files` 는 정확히 10개 `POLICY_PATHS` 만 순회하고 R2.1 은 `cla_or_dco`·`ai_policy` 를 그 10개 전부에 매핑하므로, 실제 수집 결과에는 매핑 밖 항목이 존재할 수 없다. 따라서 그 대조군은 손으로 작성한 discovery fixture 의 `policy_files[]` 항목으로만 만든다. 이 사실을 테스트 주석에 남긴다.
- 셸 변수 규약: `SK=/Users/lee-kyu-hwan/code/dotfiles__worktrees/79-feat-contribution-candidate-verifier/dot_codex/skills/verifying-open-source-contribution-candidates`, `PY=/opt/homebrew/bin/python3`, `RT=/Users/lee-kyu-hwan/code/dotfiles__worktrees/79-feat-contribution-candidate-verifier`, `QS=$RT/.claude/quality-state/20260908T011803Z-79-사전-리뷰-critical-4건-최소-수정-예산-소진-시-조합-누락-2b100e8c`.

## File map

| 파일 | 책임 | 영향 인터페이스·동작 |
|---|---|---|
| `scripts/verify_candidates.py` `run_discover` (`:1690`~`:1960`) | 조합 universe 생성과 세 구획 귀속 | 조합 단위 예산 처리, 잔여 조합의 `failed_scopes/budget-exhausted` 이동, 출력 직전 완전 분할 불변식 |
| `scripts/verify_candidates.py` `run_child` (`:395`~`:425`) | 실행 파일·서브커맨드·메서드 allowlist | 위반을 transport 오류와 구분되는 전용 예외로 승격 |
| `scripts/verify_candidates.py` `GhApiClient.get_json` (`:640`~`:690`) | 요청·재시도·예산 | allowlist 예외는 재시도·sleep·599 합성 없이 전파. OSError·subprocess 재시도 계약 유지 |
| `scripts/verify_candidates.py` `_payload_from_body` (`:590`), `_decode_policy_payload` (`:1060`) | 본문→payload 변환과 정책 내용 복호 | 파싱 실패를 성공 dict 로 합성하지 않는 sentinel |
| `scripts/verify_candidates.py` `discover_policy_files` (`:1075`~`:1180`) | 정책 파일 3상태 관측 | 파싱·형식 실패를 `request-failed`+null hash/content 로. `entry_count = len(names)` |
| `scripts/verify_candidates.py` `discover_duplicate_search` (`:1317`), `discover_code_search` (`:1370`), `_recheck_duplicate_search` (`:2975`) | 검색 요청 조립·소비 | 위험 단서 요청 전 차단, 저장 query 문법 재검증, 형식 불일치 2xx → `complete: false` |
| `scripts/verify_candidates.py` `_assessment_gate_violations` 정책 절 (`:2167`~`:2213`) | ready 게이트 | 관련 경로의 `request-failed` 존재 시 `policy_files_reviewed: confirmed` + public ready 거부 |
| `scripts/verify_candidates.py` `run_record` (`:2760`~`:2925`) | discovery 검증·assessment 결합·manifest | shape validator 선행, manifest 의 discovery status·warnings·repository reason 보존 |
| `scripts/verify_candidates.py` `run_recheck` (`:3155`~`:3300`) | 재검증과 상태 전이 | 세 실패 경로의 actionable 차단, 실패 snapshot, 식별 가능한 run 경고, outcome 재계산 |
| `scripts/verify_candidates.py` `render_markdown` (`:2565`~`:2600`) | Markdown 렌더 | 알 수 없는·없는 run status 를 `unknown` + 근거 부재 경고로 |
| `tests/test_verify_candidates.py` | 표적 회귀 | 신설 테스트 11개, `test_assessment_binding_and_missing_assessments` 의 금지 조합 절 정정 |
| `tests/test_skill_contract.py` | 고정 계약·문서 동기화 | 계약 문서 문구 확인 갱신 |
| `tests/fixtures/**` | 오프라인 입력 | 분할·정책 status·malformed payload·주입 단서 fixture 추가 |
| `SKILL.md`, `references/verification-contract.md` | 배포 계약 서술 | 구획 완전성·실패 차단·전파를 실제 동작대로 |
| `docs/development/2026-09-08-79-pr-prereview-critical-fixes/report.md` | 실행 보고 | 결과·편차·잔여 한계 |

## Task dependencies

**확정 실행 순서는 T1 → T3 → T2 → T4 → T7 → T5 → T6 → T8 → T9 → T10 이다.** 태스크 번호는 Spec 요구사항 대응을 위한 식별자이고 실행 순서는 이 문단이 정한다. 각 태스크의 통과 확인은 그 태스크가 끝나는 시점에 달성 가능해야 하며, 선행이 없어 달성 불가한 단정을 약화하지 않는다.

- **T3 → T2.** 둘은 같은 `record` 입력 경계를 만진다. T3 의 discovery shape validator 를 먼저 넣고, 그다음 T2 가 정정된 금지 조합 테스트를 추가한다. 따라서 T3 의 통과 확인은 `CMD-4` 와 기존 `CMD-3`(정정 전 상태)까지이고, shape validator 와 정정된 금지 조합 테스트의 양립 확인은 **T2 의 통과 확인** 에서 한다. T2 가 만드는 discovery fixture 는 T3 의 shape validator 를 이미 만족해야 한다. 즉 모든 record 에 비어 있지 않은 `repository_node_id` 가 있고 `records`·`skipped_by_cap`·`failed_scopes`·`method_limitations` 가 배열이며 `inputs` 가 object 이고 `status` 가 세 값 중 하나여야 한다.
- **T4 → T7 → T5.** T4 가 파싱·형식 실패 sentinel 과 allowlist 전용 예외를 제공한다. T7 이 recheck 실패의 상태 차단 전이를 제공한다. T5 의 AC-9 는 `request-failed` 정책 관찰에 **R3.1 의 차단 규칙을 적용** 하도록 요구하므로 T7 의 전이가 먼저 존재해야 T5 의 `CMD-5` 통과 확인이 단정을 약화하지 않고 달성된다. T7 의 `CMD-9` 는 T5 와 무관하게 세 실패 경로만 다루므로 T5 없이 통과한다.
- **T7 → T6.** AC-14 는 주입된 저장 query 를 가진 후보의 recheck 가 partial 및 non-actionable 차단으로 끝나야 한다고 요구하므로 T7 의 차단 전이가 선행이다.
- **T1 과 T8 은 독립** 이다. T1 은 `discover` 귀속 경계만, T8 은 `record` manifest 와 `render` 만 만진다. 위 확정 순서에서 각각 맨 앞과 T6 뒤에 둔다.
- **T9 는 T1·T5·T7·T8 뒤** 다. 계약 문서의 네 문장이 확정된 동작을 서술해야 한다.
- **T10 은 마지막** 이다. 전체 스위트·형제 스위트·이력 불변성 회귀를 함께 실행한다.
- 생산 인터페이스: T3 이 discovery shape validator, T4 가 파싱 실패 sentinel 과 allowlist 전용 예외, T7 이 recheck 차단 전이, T1 이 분할 불변식 검사를 제공한다. 소비 인터페이스: T2 가 shape validator, T5 가 sentinel 과 차단 전이, T6 이 차단 전이를 쓴다.
- 병렬 작업은 하지 않는다. 단일 Codex 구현 라운드가 확정 순서로 순차 진행한다.

## Tasks

### T1. discover 조합 구획 완전 분할

대상 AC: AC-1 판정 `CMD-1` `test_budget_exhaustion_partitions_all_selected_combinations`, AC-2 판정 `CMD-1` `test_budget_exhaustion_partitions_all_selected_combinations`, AC-3 판정 `CMD-2` `test_exit_code_matrix`.

1. 실패 확인: `tests/test_verify_candidates.py` 에 `test_budget_exhaustion_partitions_all_selected_combinations` 를 추가한다. 보존 fixture `tests/fixtures/budget/analysis.json` 과 저장소 `example-org/example-repository-completed`, `example-org/example-never-started`, 예산 24로 `discover` 를 실행해 세 구획의 조합 집합이 pairwise-disjoint 이고 각 구획 내부에 `(repository, pattern_id)` 중복이 없으며 **합집합이 cap 적용 전 전체 조합 universe(선택 저장소 × 선택 패턴)와 같은지**, 완주 저장소의 미처리 조합이 `failed_scopes` 의 `budget-exhausted` 로 남는지, 종료 코드가 3인지 단정한다. 합집합 비교는 다섯 시나리오 전부에서 cap 전 universe 를 기준으로 한다. 다섯 시나리오와 각각의 fixture 경로는 다음과 같다. ① 정상 — `tests/fixtures/budget/analysis.json` + 기존 헬퍼 `make_responses` (재사용). ② cap skip — `tests/fixtures/caps/analysis.json` (재사용). ③ 접근 실패 — `tests/fixtures/failures/cases.json` 과 `tests/fixtures/failures/all-404/case.json` (재사용). ④ 저장소 단계 소진 — `tests/fixtures/budget/repo-stage/case.json` (재사용). ⑤ 조합 단계 소진 — `tests/fixtures/budget/combo-stage/case.json` (재사용). AC-1 의 미시작 저장소 사례는 `tests/fixtures/budget/unstarted/case.json` (재사용). 중복·누락 주입 분기는 새 fixture `tests/fixtures/budget/partition-violation/case.json` (**신설**)로 만든다. 같은 테스트 안에서 중복과 누락을 각각 주입한 분기가 종료 2, redaction 을 거친 정확히 한 줄의 stderr `error: discover partition invariant violated`, traceback 없음, `discovery.json`·manifest run·Markdown 출력의 생성·수정 없음을 단정한다. `CMD-1` 실행 → 실패(현재는 완주 저장소 조합이 어느 구획에도 없고 불변식 검사가 존재하지 않는다).
2. 최소 구현: `run_discover` 에서 cap 계산 직후 `universe` 를 보존하고 귀속 집합을 추적한다. `if not exhausted:` 로 조합 단계를 통째로 막지 않고 조합을 순회하다 `BudgetExhausted` 가 나면 그 조합 이후의 모든 미귀속 조합을 `_failed_scope(..., "budget-exhausted")` 로 이동한다. 저장소 단계 소진도 같은 이동을 수행한다. 출력 조립 직전 `universe == records ∪ skipped_by_cap ∪ failed_scopes` 와 pairwise-disjoint, 구획 내부 중복 없음을 검사한다. 위반이면 기존 종료 코드 2 와 redaction 을 거친 한 줄 stderr `error: discover partition invariant violated` 로 끝내고 traceback 을 내지 않으며 출력·manifest·Markdown 파일을 생성·수정하지 않는다. 불변식을 만족한 예산 소진은 그대로 종료 3 과 partial 산출물을 쓴다.
3. 통과 확인: `CMD-1` 과 `CMD-2` 실행 → 종료 0, 두 테스트 `ok`. 기존 `test_budget_and_retry_behaviour` 와 `test_caps_record_skipped_combinations` 가 회귀하지 않음을 함께 확인한다.

### T2. record 금지 조합 회귀 테스트 정정

대상 AC: AC-4 판정 `CMD-3` `test_record_rejects_present_forbidden_combinations`, AC-5 판정 `CMD-3` `test_record_rejects_present_forbidden_combinations`.

1. 실패 확인: `test_record_rejects_present_forbidden_combinations` 를 추가한다. discovery `records` 에 평가 대상 조합을 둔 상태에서 같은 조합을 `skipped_by_cap` 에, 그리고 별도로 `failed_scopes` 에 넣고 각각 종료 2, 한 줄 stderr `combination is absent, skipped, or failed`, 후보·manifest 출력 없음을 단정한다. 최상위 `skipped`/`failed` 키를 쓰지 않는다. 또한 게이트의 `combo in forbidden_combos` 항을 제거하면 이 테스트가 실패함을 주석으로 명시하고, 기존 `test_assessment_binding_and_missing_assessments` 의 잘못된 키 사용 절을 올바른 키로 정정한다. `CMD-3` 실행 → 이 시점에는 T3 의 shape validator 가 이미 있으므로, 신설 테스트의 fixture 가 그 validator 를 통과하면서도 정정 전 기존 테스트가 `combo in forbidden_combos` 분기를 밟지 않음을 확인한다. 기존 테스트의 잘못된 최상위 `skipped`/`failed` 키 절이 아무 것도 거부하지 못함(레코드를 넣으면 종료 0)을 근거로 남긴다.
2. 최소 구현: 게이트 코드는 이미 옳으므로 코드 변경은 없다. 테스트와 헬퍼 사용만 정정한다. 헬퍼 `make_discovery_document` 의 키 이름을 바꾸지 않는다.
3. 통과 확인: `CMD-3` 실행 → 종료 0, 두 금지 분기 `ok`. 같은 실행이 T3 의 shape validator 와 정정된 금지 조합 테스트의 양립도 증명한다. 이어 `CMD-4` 를 재실행해 T3 판정이 회귀하지 않음을 확인한다.

### T3. record discovery shape 검증

대상 AC: AC-6 판정 `CMD-4` `test_record_rejects_malformed_discovery_shapes`, AC-7 판정 `CMD-4` `test_record_rejects_malformed_discovery_shapes`.

1. 실패 확인: `test_record_rejects_malformed_discovery_shapes` 를 추가한다. `repository_node_id` 가 없는 record 와 `skipped_by_cap`(그리고 `failed_scopes`)이 배열이 아닌 discovery 를 각각 넣고 `KeyError` 트레이스백 없이 종료 2, 한 줄 stderr, 후보·manifest 출력 없음을 단정한다. `CMD-4` 실행 → 실패(전자는 `KeyError` 트레이스백, 후자는 종료 0).
2. 최소 구현: `run_record` 에서 assessment 결합 전에 discovery shape validator 를 호출한다. top-level object, `schema_version == "1.0.0"`, object 인 `inputs` 와 그 안의 repository 배열, 배열인 `records`·`skipped_by_cap`·`failed_scopes`·`method_limitations`, `complete`/`partial`/`failed` 중 하나인 `status`, 각 구획 항목이 object 이며 `repository`·`pattern_id` 를 가짐, 각 record 가 object 이며 비어 있지 않은 `repository_node_id` 와 이후 첨자 접근하는 필수 필드를 가짐을 확인하고, 위반은 `CliInputError` 로 종료 2를 만든다.
3. 통과 확인: `CMD-4` 실행 → 종료 0. 이어 이 시점의 `CMD-3`(아직 정정 전인 기존 `test_assessment_binding_and_missing_assessments` 만 존재)을 재실행해 shape validator 가 기존 record 경계를 깨지 않음을 확인한다. 정정된 금지 조합 테스트와의 양립 확인은 T2 의 통과 확인에서 한다.

### T4. 응답 파싱·형식 실패의 fail-closed 경계

대상 AC: AC-10 판정 `CMD-6` `test_malformed_success_payloads_remain_incomplete`, AC-11 판정 `CMD-6` `test_malformed_success_payloads_remain_incomplete`, AC-23 판정 `CMD-6` `test_malformed_success_payloads_remain_incomplete`, AC-12 판정 `CMD-7` `test_allowlist_violation_fails_without_retry`.

1. 실패 확인: `test_malformed_success_payloads_remain_incomplete` 와 `test_allowlist_violation_fails_without_retry` 를 추가한다. 전자는 2xx non-JSON 정책 본문과 형식 불일치 정책 object 가 `status: request-failed`·`found: false`·null hash/content 로 남는지, 2xx non-object 검색 payload 가 `duplicate_search.complete: false` 와 경고를 만드는지(`discover` 와 `recheck` 모두), community profile 의 2xx non-object payload 와 `files` 가 object 아닌 payload 각각에서 `repository_checks.community_profile_files` 가 요청 전 기본값과 깊은 비교로 같고 `stages_completed` 에 `community_profile` 이 없으며 경고가 있는지, 정상 대조군만 6개 bool 을 덮어쓰고 stage 를 추가하는지 단정한다. 후자는 allowlist 위반 `runner` 에서 호출 1회·sleeper 0회·599 없음·CLI 종료 2와 redact 된 한 줄 오류, 그리고 `discover` 와 `recheck` 각각에서 출력·manifest·Markdown 파일의 생성·수정 없음을 단정한다. `CMD-6`, `CMD-7` 실행 → 실패(현재는 오류 본문이 `found: true` 내용으로 해시되고, 형식 불일치 검색이 `complete: true` 이며, guard 위반이 예산 4·대기 420초 뒤 599가 된다).
2. 최소 구현: `_payload_from_body` 가 파싱 실패에 구분 가능한 sentinel 을 반환하고 `_decode_policy_payload` 와 정책 경로가 이를 `request-failed` 로 처리한다. `discover_duplicate_search` 와 `_recheck_duplicate_search` 가 non-dict payload 와 필수 필드 형식 불일치를 `complete: false` + 경고로 처리한다. `discover_repository` 의 community profile 호출부(`:1256-1260`)가 2xx 여도 payload 와 `files` 가 object 인지 확인하고, 아니면 기본값을 덮어쓰지 않고 `stages_completed` 에 `community_profile` 을 추가하지 않으며 경고를 남긴다. `run_child` 의 allowlist 위반을 `ValueError` 하위가 아닌 전용 예외로 올리고 `get_json` 의 `except (OSError, subprocess.SubprocessError, ValueError)` 에 걸리지 않게 하며 CLI 경계에서 redact 된 종료 2로 만든다.
3. 통과 확인: `CMD-6`, `CMD-7` 실행 → 종료 0. 기존 `test_only_gh_get_and_git_readonly_subprocesses` 와 `test_budget_and_retry_behaviour` 회귀 없음을 확인한다.

### T5. 정책 status 3분기와 ready 차단

대상 AC: AC-8 판정 `CMD-5` `test_policy_request_failure_blocks_ready`, AC-9 판정 `CMD-5` `test_policy_request_failure_blocks_ready`.

1. 실패 확인: `test_policy_request_failure_blocks_ready` 를 추가한다. `CONTRIBUTING.md` 가 `absent` 이면 public ready 가 가능하고, `CONTRIBUTING.md` 또는 비-contributing 경로 `.github/ISSUE_TEMPLATE` 이 `request-failed` 이면 `policy_files_reviewed: confirmed` + `issue-ready`/`pr-ready` 가 종료 2로 거부되며 후보·manifest run·Markdown 출력이 생성·수정되지 않음을 단정한다. 매핑 밖 경로 하나만 `request-failed` 인 대조군은 이 게이트로 거부되지 않음을 함께 단정한다. recheck 쪽은 `request-failed` 를 부재·불변으로 바꾸지 않고 T7 이 이미 구현한 R3.1 차단 규칙을 적용함을 단정한다. 확정 순서에서 T7 이 T5 보다 앞이므로 이 단정은 T5 종료 시점에 달성 가능하다. **이 단정을 약화·삭제·skip 처리하는 것을 금지한다.** `CMD-5` 실행 → 실패(현재 두 status 가 동일하게 종료 0, `pr-ready` 생성).
2. 최소 구현: `_assessment_gate_violations` 정책 절에 R2.1 의 10개 `POLICY_PATHS` → `POLICY_CHECK_KEYS` 매핑(`program_rules` 제외)에 속하는 경로 중 하나라도 `request-failed` 이면 확정 조합을 거부하는 판정을 추가한다. `_policy_sha_values` 와 `_reobserved_policy_checks` 가 `found` 만 보지 않고 3상태를 구분한다. 새 상태·이유·키를 만들지 않는다.
3. 통과 확인: `CMD-5` 실행 → 종료 0. 기존 `test_policy_files_discovery_and_untrusted_excerpts`, `test_policy_checks_shape_and_sha_binding`, `test_readiness_gate_rejects_unsupported_ready` 회귀 없음을 확인한다.

### T6. 미신뢰 검색 단서·저장 query 차단

대상 AC: AC-13 판정 `CMD-8` `test_untrusted_search_clues_cannot_escape_repository_scope`, AC-14 판정 `CMD-8` `test_untrusted_search_clues_cannot_escape_repository_scope`.

1. 실패 확인: `test_untrusted_search_clues_cannot_escape_repository_scope` 를 추가한다. 따옴표로 인용을 닫고 다른 `repo:` 를 삽입하는 단서, 역슬래시 단서, CR/LF 단서가 issue·code 요청으로 전달되지 않고 각각 `duplicate_search.complete: false`·`code_search.available: false` 와 경고로 남는지, 정상 단서는 기존 요청 수·순서·query 의미를 유지하는지 단정한다. 주입된 `repo:` 가 든 저장 query 를 가진 후보의 recheck 가 그 query 를 전송하지 않고 partial·non-actionable 로 끝나는지 단정한다. `CMD-8` 실행 → 실패(현재 주입 단서가 그대로 질의에 들어가 다른 저장소를 검색하고 `complete: true` 다).
2. 최소 구현: 요청 조립 전에 단서를 검사해 따옴표·역슬래시·제어 문자를 가진 단서는 요청하지 않고 경고와 불완전·불가 상태로 남긴다. `_recheck_duplicate_search` 는 저장 query 가 현재 후보 repository 의 신뢰 문법과 정확히 일치하는지 검사하고 불일치면 전송하지 않는다. 이스케이프를 시도하지 않는다.
3. 통과 확인: `CMD-8` 실행 → 종료 0. 기존 `test_duplicate_search_four_combinations_and_completeness` 와 `test_injection_fixture_is_inert` 회귀 없음을 확인한다.

### T7. recheck 실패의 actionable 차단

대상 AC: AC-15 판정 `CMD-9` `test_recheck_failure_blocks_actionable_candidate`, AC-16 판정 `CMD-9` `test_recheck_failure_blocks_actionable_candidate`.

1. 실패 확인: `test_recheck_failure_blocks_actionable_candidate` 를 추가한다. 선행 예산 소진 단축, `BudgetExhausted`, repository·head 실패로 `observation is None` 이 되는 세 경로 각각에서 이전 actionable 후보가 `unverified`/`insufficient-evidence`, `blocking_gaps` 에 `recheck-failed`, `next_recheck_required: false`, append-only 실패 snapshot 을 가지며 이전 레코드와 바이트 동일하지 않음을 단정한다. 새 snapshot 의 evidence key set 이 정확히 8개이고 승계 4필드(`readiness_checks`·`reproduction`·`execution_evidence`·`duplicate_verdict`)가 직전 snapshot 과 깊은 비교로 같으며 `repository_checks`·`observed_head_sha` 가 각각 null, `policy_checks` 8키가 모두 R3.1 의 null/실패 값 객체, `duplicate_search` 가 R3.1 의 빈 queries·`complete: false` 객체와 같음을 단정한다. top-level `repository_checks` 는 null, top-level `duplicate_search` 는 snapshot 값과 같고 `policy_checks` 를 포함한 불변 20필드는 이전 값과 깊은 비교로 같으며, 마지막 성공 `verified_at`·`verified_base_sha` 가 유지되고 top-level 상태·이유·시각·SHA 가 마지막 snapshot 과 일치함을 단정한다. run 경고에 candidate ID·repository·원인이 있고 종료 3과 `no-actionable-candidates` 임을 단정한다. `CMD-9` 실행 → 실패(현재 세 경로 모두 레코드가 바이트 동일하고 outcome 이 `actionable-candidates` 다).
2. 최소 구현: `run_recheck` 의 세 실패 경로에서 후보 상태가 `ACTIONABLE_STATUSES` 면 `unverified`/`insufficient-evidence` 로 낮추고 `blocking_gaps` 에 `recheck-failed` 를 중복 없이 추가하며 `next_recheck_required` 를 `false` 로 두고, R3.1 이 못박은 값으로 실패 snapshot 을 정확히 하나 append 한다. 승계 4필드는 직전 snapshot 깊은 복사, 미관측 4필드는 `repository_checks: null`·`observed_head_sha: null`·8키 null 정책 객체·빈 queries `complete: false` duplicate 객체다. top-level `repository_checks` 는 null, top-level `duplicate_search` 는 그 실패 객체로 갱신하고 `verified_at`·`verified_base_sha` 는 성공 관찰 값을 보존한다. run 경고에 후보 식별 정보를 남기고 outcome 을 재계산한다. 모두 `RECHECK_MUTABLE_FIELDS` 안에서만 바꾼다.
3. 통과 확인: `CMD-9` 실행 → 종료 0. 기존 `test_recheck_staleness_and_change_detection`, `test_verification_history_append_only`, `test_ready_records_flag_recheck_required` 회귀 없음을 확인한다.

### T8. record manifest 전파와 render unknown

대상 AC: AC-17 판정 `CMD-10` `test_record_manifest_preserves_discovery_failure_state`, AC-18 판정 `CMD-11` `test_render_never_defaults_unknown_status_to_complete`.

1. 실패 확인: `test_record_manifest_preserves_discovery_failure_state` 와 `test_render_never_defaults_unknown_status_to_complete` 를 추가한다. 전자는 partial discovery 를 입력한 `record` run 이 partial status, 원래 warning·failed scope·method limitation, repository 별 budget·access reason 을 기존 필드로 보존하고 `complete`·`checked` 로 세탁하지 않음을 단정한다. 후자는 manifest 없음·최신 run 없음·알 수 없는 status 세 입력이 모두 `unknown` 과 근거 부재 경고를 표시하고 종료 0 이며, 유효한 세 status 는 그대로 표시됨을 단정한다. `CMD-10`, `CMD-11` 실행 → 실패.
2. 최소 구현: `run_record` manifest 조립에서 `status` 를 discovery `status` 로, `warnings` 를 record 별 `warnings` 합집합으로, repositories 의 `outcome`·`reason` 을 `failed_scopes` 이유와 `inputs.repositories` 로 재구성한다. 재구성 불가능한 transport 세부는 추측하지 않는다. `render_markdown` 의 `run_status` 기본값을 `unknown` + 경고로 바꾼다. discovery schema 와 후보 29필드를 넓히지 않는다.
3. 통과 확인: `CMD-10`, `CMD-11` 실행 → 종료 0. 기존 `test_manifest_append_only_runs`, `test_markdown_render_structure`, `test_negative_outcomes_are_honest_normal_results` 회귀 없음을 확인한다.

### T9. entry_count 정정과 계약 문서 동기화

대상 AC: AC-19 판정 `CMD-13` `test_reference_documents_cover_contract`, AC-20 판정 `CMD-12` `test_policy_directory_entry_count_uses_filtered_names`, AC-21 판정 `CMD-13` `test_reference_documents_cover_contract` `test_print_revision_matches_recomputation`.

1. 실패 확인: `test_policy_directory_entry_count_uses_filtered_names` 를 추가한다. 문자열 `name` 을 가진 항목과 그렇지 않은 항목이 섞인 디렉터리 payload 에서 canonical `names` 에 전자만 들어가고 `entry_count == len(names)` 이며 hash 가 같은 canonical names 의 hash 임을 단정한다. `CMD-12` 실행 → 실패(현재 `entry_count` 가 원본 payload 길이다).
2. 최소 구현: `:1135` 의 `entry_count` 를 `len(names)` 로 바꾼다. `SKILL.md` 와 `references/verification-contract.md` 각각에 R4.1 이 못박은 정확한 네 문장을 넣는다. `Every pre-cap repository-pattern combination appears in exactly one of records, skipped_by_cap, or failed_scopes.`, `A request-failed policy observation cannot support issue-ready or pr-ready.`, `A failed recheck makes an actionable candidate unverified with status_reason insufficient-evidence.`, `record and render preserve partial, failed, and unknown run states instead of defaulting them to complete.` 고정 계약 집합과 종료 코드 규칙은 그대로 유지하고 1·2차 실행 문서는 건드리지 않는다. `test_reference_documents_cover_contract` 가 두 파일 모두에서 네 문장의 존재를 단정하도록 갱신한다.
3. 통과 확인: `CMD-12`, `CMD-13` 실행 → 종료 0, 세 테스트 `ok`. `spec.md` Non-goals 11 이 1·2차 실행 문서를 불변 이력으로 고정함을 확인한다.

### T10. 전체 오프라인 스위트 회귀

대상 AC: AC-22 판정 `CMD-14` `test_verify_candidates` `test_skill_contract`.

1. 실패 확인: 이 태스크는 종합 회귀다. T1~T9 완료 전에 실행하면 신설 테스트가 실패하는 것으로 선행 판정이 성립한다.
2. 최소 구현: 코드 변경 없음. T1~T9 의 결과만 모은다.
3. 통과 확인: `CMD-14` 실행 → 종료 0, `OK`, `Ran` 수가 55 이상(기존 44 + 신설 11). 이어 `CMD-15` 로 형제 스킬 두 스위트의 무회귀를, `CMD-16` 으로 1차 실행 문서 5개의 불변성을, `CMD-17` 로 2차 실행 문서 7개의 불변성을 확인한다. 네트워크 runner 호출이 없음을 `CMD-14` 출력으로 확인한다.

## Verification commands

실행 순서는 표적 판정(`CMD-1`~`CMD-13`) → 전체 스위트(`CMD-14`) → 형제 회귀(`CMD-15`) → 1차 실행 문서 불변성(`CMD-16`) → 2차 실행 문서 불변성(`CMD-17`) 이다. `CMD-16` 이 참조하는 `preserved-run.sha256` 은 1차 실행 문서 5개만 담으므로 2차 실행 문서 7개는 `CMD-17` 이 별도로 검증한다. `CMD-17` 의 기준 목록 `$QS/preserved-run2.sha256` 은 구현 착수 전에 만든 baseline 이며 `QS=/Users/lee-kyu-hwan/code/dotfiles__worktrees/79-feat-contribution-candidate-verifier/.claude/quality-state/20260908T011803Z-79-사전-리뷰-critical-4건-최소-수정-예산-소진-시-조합-누락-2b100e8c` 다. 이 스킬에는 lint, type-check, build 도구가 구성되어 있지 않으므로 그 범주는 미구성으로 기록하고 통과로 적지 않는다.

| ID | 명령 | 기대 결과 |
|---|---|---|
| CMD-1 | `cd "$SK" && PYTHONDONTWRITEBYTECODE=1 "$PY" -m unittest tests.test_verify_candidates.VerifyCandidatesTests.test_budget_exhaustion_partitions_all_selected_combinations -v` | 종료 0, `ok` |
| CMD-2 | `cd "$SK" && PYTHONDONTWRITEBYTECODE=1 "$PY" -m unittest tests.test_verify_candidates.VerifyCandidatesTests.test_exit_code_matrix -v` | 종료 0, `ok` |
| CMD-3 | `cd "$SK" && PYTHONDONTWRITEBYTECODE=1 "$PY" -m unittest tests.test_verify_candidates.VerifyCandidatesTests.test_record_rejects_present_forbidden_combinations tests.test_verify_candidates.VerifyCandidatesTests.test_assessment_binding_and_missing_assessments -v` | 종료 0, 두 테스트 `ok` |
| CMD-4 | `cd "$SK" && PYTHONDONTWRITEBYTECODE=1 "$PY" -m unittest tests.test_verify_candidates.VerifyCandidatesTests.test_record_rejects_malformed_discovery_shapes -v` | 종료 0, `ok` |
| CMD-5 | `cd "$SK" && PYTHONDONTWRITEBYTECODE=1 "$PY" -m unittest tests.test_verify_candidates.VerifyCandidatesTests.test_policy_request_failure_blocks_ready -v` | 종료 0, `ok` |
| CMD-6 | `cd "$SK" && PYTHONDONTWRITEBYTECODE=1 "$PY" -m unittest tests.test_verify_candidates.VerifyCandidatesTests.test_malformed_success_payloads_remain_incomplete -v` | 종료 0, `ok` |
| CMD-7 | `cd "$SK" && PYTHONDONTWRITEBYTECODE=1 "$PY" -m unittest tests.test_verify_candidates.VerifyCandidatesTests.test_allowlist_violation_fails_without_retry -v` | 종료 0, `ok` |
| CMD-8 | `cd "$SK" && PYTHONDONTWRITEBYTECODE=1 "$PY" -m unittest tests.test_verify_candidates.VerifyCandidatesTests.test_untrusted_search_clues_cannot_escape_repository_scope -v` | 종료 0, `ok` |
| CMD-9 | `cd "$SK" && PYTHONDONTWRITEBYTECODE=1 "$PY" -m unittest tests.test_verify_candidates.VerifyCandidatesTests.test_recheck_failure_blocks_actionable_candidate -v` | 종료 0, `ok` |
| CMD-10 | `cd "$SK" && PYTHONDONTWRITEBYTECODE=1 "$PY" -m unittest tests.test_verify_candidates.VerifyCandidatesTests.test_record_manifest_preserves_discovery_failure_state -v` | 종료 0, `ok` |
| CMD-11 | `cd "$SK" && PYTHONDONTWRITEBYTECODE=1 "$PY" -m unittest tests.test_verify_candidates.VerifyCandidatesTests.test_render_never_defaults_unknown_status_to_complete -v` | 종료 0, `ok` |
| CMD-12 | `cd "$SK" && PYTHONDONTWRITEBYTECODE=1 "$PY" -m unittest tests.test_verify_candidates.VerifyCandidatesTests.test_policy_directory_entry_count_uses_filtered_names -v` | 종료 0, `ok` |
| CMD-13 | `cd "$SK" && PYTHONDONTWRITEBYTECODE=1 "$PY" -m unittest tests.test_skill_contract.SkillContractTests.test_reference_documents_cover_contract tests.test_verify_candidates.VerifyCandidatesTests.test_print_revision_matches_recomputation -v` | 종료 0, 두 테스트 `ok` |
| CMD-14 | `PYTHONDONTWRITEBYTECODE=1 "$PY" -m unittest discover -s "$SK/tests" -t "$SK/tests" -p 'test_*.py'` | 종료 0, `OK`, `Ran` 55 이상; 네트워크 runner 호출 없음 |
| CMD-15 | `cd "$RT" && for t in analyzing-open-source-pr-patterns collecting-recent-closed-prs; do PYTHONDONTWRITEBYTECODE=1 "$PY" -m unittest discover -s "dot_codex/skills/$t/tests" -t "dot_codex/skills/$t/tests" -p 'test_*.py' || exit 1; done` | 두 스위트 `OK` (`Ran 30 tests`, `Ran 108 tests`) |
| CMD-16 | `cd "$RT" && shasum -a 256 -c docs/development/2026-09-07-79-verifying-open-source-contribution-candidates-plan-redesign/preserved-run.sha256` | 5개 항목 전부 `OK`. 이 manifest 는 **1차 실행 문서 5개만** 담는다 |
| CMD-17 | `cd "$RT" && shasum -a 256 -c "$QS/preserved-run2.sha256" && git status --porcelain -- docs/development/2026-09-07-79-verifying-open-source-contribution-candidates-plan-redesign` | 7개 항목 전부 `OK`. `git status` 출력은 디렉터리 전체가 여전히 하나의 미추적 항목으로만 보고되어 새 파일 추가·삭제가 없음을 확인한다 |

## Rollout and rollback

배포는 이번 범위가 아니다. 산출물은 워크트리의 미커밋 변경으로만 남고 `chezmoi apply`·배포·전역 설치본 갱신은 하지 않는다. 따라서 rollout 단계는 "리뷰 통과 후 사용자에게 PR 준비 판단을 넘긴다" 까지다.

관측 신호는 `discovery.json` 의 세 구획과 `status`, manifest 의 repository reason·failed scopes·warnings·status·outcome, `candidates.json` 의 status·status_reason·blocking_gaps·verification_history, Markdown 의 run status, 그리고 종료 코드다.

rollback 트리거는 다음 중 하나다. `CMD-14` 가 `OK` 가 아님, `CMD-15` 의 형제 스위트 회귀, `CMD-16`(1차 실행 문서 5개) 또는 `CMD-17`(2차 실행 문서 7개) 불변성 실패, 선택 조합의 누락·중복, `request-failed` 상태에서 public ready 유지, recheck 실패 뒤 actionable outcome, 예산 소진이 종료 4로 바뀜, 정상 단서의 요청 수·순서 변화.

rollback 절차는 이번 실행이 만든 코드·테스트·현재 계약 문서 변경만 되돌리는 것이다. 구체적으로 `git diff` 로 변경 목록을 확인한 뒤 이번 실행이 만든 파일은 삭제하고 수정한 파일은 이번 실행 이전 내용으로 복원한다. 1·2차 실행 문서와 상태, 전역 설치본, `main`, 다른 워크트리는 rollback 대상이 아니며 건드리지 않는다. 되돌린 뒤 `CMD-14`·`CMD-15`·`CMD-16`·`CMD-17` 을 재실행해 기준선 44/30/108 과 5개 `OK`·7개 `OK` 로 복귀했음을 확인한다.

## Acceptance-criteria traceability

| Criterion | Task | Verification command | Expected outcome |
|---|---|---|---|
| AC-1 | T1 | `CMD-1` `test_budget_exhaustion_partitions_all_selected_combinations` | 종료 0, 완주 저장소 조합이 `failed_scopes/budget-exhausted` 에 있고 종료 코드 3 |
| AC-2 | T1 | `CMD-1` `test_budget_exhaustion_partitions_all_selected_combinations` | 종료 0, 다섯 fixture 에서 pairwise-disjoint 와 합집합 일치 |
| AC-3 | T1 | `CMD-2` `test_exit_code_matrix` | 종료 0, 전 저장소 접근 실패만 4, 예산 소진은 항상 3 |
| AC-4 | T2 | `CMD-3` `test_record_rejects_present_forbidden_combinations` | 종료 0, `skipped_by_cap` 분기가 종료 2로 거부 |
| AC-5 | T2 | `CMD-3` `test_record_rejects_present_forbidden_combinations` | 종료 0, `failed_scopes` 분기가 종료 2로 거부 |
| AC-6 | T3 | `CMD-4` `test_record_rejects_malformed_discovery_shapes` | 종료 0, 누락 node ID 가 트레이스백 없이 종료 2 |
| AC-7 | T3 | `CMD-4` `test_record_rejects_malformed_discovery_shapes` | 종료 0, 배열 아닌 구획이 종료 2 |
| AC-8 | T5 | `CMD-5` `test_policy_request_failure_blocks_ready` | 종료 0, `absent` 은 허용·`request-failed` 는 종료 2 |
| AC-9 | T5 | `CMD-5` `test_policy_request_failure_blocks_ready` | 종료 0, recheck 가 `request-failed` 를 부재로 접지 않음 |
| AC-10 | T4 | `CMD-6` `test_malformed_success_payloads_remain_incomplete` | 종료 0, 오류 본문이 `found: true` 해시가 되지 않음 |
| AC-11 | T4 | `CMD-6` `test_malformed_success_payloads_remain_incomplete` | 종료 0, 형식 불일치 검색이 `complete: false` |
| AC-12 | T4 | `CMD-7` `test_allowlist_violation_fails_without_retry` | 종료 0, 호출 1회·sleep 0회·종료 2 |
| AC-13 | T6 | `CMD-8` `test_untrusted_search_clues_cannot_escape_repository_scope` | 종료 0, 주입 단서가 요청되지 않음 |
| AC-14 | T6 | `CMD-8` `test_untrusted_search_clues_cannot_escape_repository_scope` | 종료 0, 주입된 저장 query 미전송 |
| AC-15 | T7 | `CMD-9` `test_recheck_failure_blocks_actionable_candidate` | 종료 0, 세 경로 모두 `unverified` 차단 |
| AC-16 | T7 | `CMD-9` `test_recheck_failure_blocks_actionable_candidate` | 종료 0, 시각·SHA 보존과 `no-actionable-candidates` |
| AC-17 | T8 | `CMD-10` `test_record_manifest_preserves_discovery_failure_state` | 종료 0, partial 상태·경고·이유 보존 |
| AC-18 | T8 | `CMD-11` `test_render_never_defaults_unknown_status_to_complete` | 종료 0, 세 입력 모두 `unknown` |
| AC-19 | T9 | `CMD-13` `test_reference_documents_cover_contract` | 종료 0, 두 계약 문서 각각에 R4.1 의 정확한 네 문장이 있음을 단정 |
| AC-20 | T9 | `CMD-12` `test_policy_directory_entry_count_uses_filtered_names` | 종료 0, `entry_count == len(names)` |
| AC-21 | T9 | `CMD-13` `test_reference_documents_cover_contract` `test_print_revision_matches_recomputation` | 종료 0, 두 테스트 `ok` |
| AC-22 | T10 | `CMD-14` `test_verify_candidates` `test_skill_contract` | 종료 0, `OK`, `Ran` 55 이상 |
| AC-23 | T4 | `CMD-6` `test_malformed_success_payloads_remain_incomplete` | 종료 0, malformed community profile 이 기본값·미완료 stage·경고로 남음 |

<!-- strict-only:start -->

### Threat and trust boundaries

구현과 검증이 보존해야 하는 경계 점검은 다섯이다. ① 본문→JSON parser 가 파싱 실패를 성공 dict 로 합성하지 않는다(`CMD-6`). ② JSON→정책·검색 shape validator 가 형식 불일치를 확인된 결과로 소비하지 않는다(`CMD-6`). ③ 단서→query builder 가 신뢰된 `repo:` 한정자 외의 의미를 만들지 않는다(`CMD-8`). ④ discovery→assessment 게이트가 형태 미검증 입력과 금지 조합을 통과시키지 않는다(`CMD-3`, `CMD-4`). ⑤ recheck 관측→후보 상태 전이가 실패를 성공처럼 기록하지 않는다(`CMD-9`). 미신뢰 주체는 외부 PR 텍스트에서 온 검색 단서, 저장소 정책 본문, GitHub 응답, fixture payload 다.

### Authorization and tenant isolation

다중 tenant 기능이 없어 tenant isolation 테스트 케이스는 해당 없음이다. 이유는 이 스킬이 단일 사용자의 로컬 CLI 이고 tenant 개념·경계·권한 분기가 코드에 없기 때문이다. 대신 권한 경계 판정으로 `CMD-7` 이 실행 파일·서브커맨드·HTTP 메서드 allowlist 위반이 fail-closed 로 거부되는지 확인하고, `CMD-14` 가 네트워크 runner 호출이 없음을 확인한다. GitHub 인증은 기존 `gh` 자격을 read-only GET 에만 쓰며 권한을 확대하지 않는다.

### Migration, compatibility, and rollback

data migration 과 backfill 은 없다. `schema_version`, candidate 29필드, `RECHECK_MUTABLE_FIELDS` 9와 여집합 default-deny, `STATUS_REASON_TABLE`, `READINESS_KEYS` 12, `POLICY_CHECK_KEYS` 8, `FAILED_SCOPE_REASONS` 5, `ACCESS_FAILURE_OUTCOMES` 4, 종료 코드 0/1/2/3/4를 유지하는 것이 호환성 점검이며 `CMD-13` 이 이를 확인한다. 기존 `candidates.json` 은 계속 읽히고, 실패한 recheck 를 받는 actionable 레코드만 append-only snapshot 과 기존 `unverified` 상태로 전이한다. `compute_revision()` 값 변화는 계약된 동작이며 `CMD-13` 의 재계산 비교로 증명한다. rollback 트리거와 절차는 위 Rollout and rollback 절과 같고, 리뷰 전 필요한 근거는 `CMD-14`·`CMD-15`·`CMD-16`·`CMD-17` 의 실제 출력이다.

### Failure recovery and observability

실패 복구 점검은 셋이다. ① partial `discover` 후 `failed_scopes` 를 근거로 남은 범위를 새 승인 실행에서 다시 discover 할 수 있는가(`CMD-1`). ② 형식 어긋난 discovery·assessment 를 고쳐 `record` 를 재실행할 수 있는가(`CMD-4`). ③ recheck-failed 후보가 새 `discover`+`record` 성공 전에는 ready 로 복귀하지 않는가(`CMD-9`). 필요한 관측 근거는 세 구획과 `status`, manifest 의 repository reason·failed scopes·warnings·status·outcome, 후보의 status·status_reason·blocking_gaps·최신 snapshot, Markdown 의 run status, 종료 코드이며 각 판정 명령의 단정으로 남긴다.

### High-risk end-to-end verification

고위험 경로 넷을 CLI 경계까지 검증한다. 미신뢰 query confinement 는 `CMD-8`, 예산 소진 구획 완전성은 `CMD-1`, 정책 실패 ready gate 는 `CMD-5`, 실패 recheck 상태 전이는 `CMD-9` 다. cross-regression 은 `CMD-14` 로 확인한다. 요구되는 근거는 각 명령의 종료 코드와 단정 통과 출력이며 모두 보존 fixture 와 주입 transport 로만 실행한다. 새 라이브 검증은 승인 범위 밖이므로 수행하지 않는다. 따라서 `assessment`·`record`·`recheck` 실경로와 `CAN-*` 실물은 여전히 미검증으로 보고한다. 과거 `discover` 1회 라이브 근거는 읽기 전용 이력이며 이번 변경의 검증으로 재사용하지 않는다.

### No production mutation confirmation

자동 워크플로에 production mutation 은 없다. 판정은 fixture 기반 unittest 와 문서 검사뿐이며 GitHub, 원격 저장소, `main`, 다른 워크트리, 전역 설치본, `$HOME` 설정을 바꾸지 않는다. commit, push, PR 생성, merge, `chezmoi apply`, 배포, Issue·댓글 작성, 라이브 `discover`·`recheck` 는 포함하지 않는다.

<!-- strict-only:end -->
