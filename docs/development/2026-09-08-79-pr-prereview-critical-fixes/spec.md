# Quality Goal Specification

- Task ID: 20260908T011803Z-79-사전-리뷰-critical-4건-최소-수정-예산-소진-시-조합-누락-2b100e8c
- Mode: strict
- Status: SPEC_REVIEW
- Created: 2026-09-08T01:18:03Z
- Updated: 2026-09-08T02:28:45Z
- Source goal: #79 PR 사전 리뷰가 차단한 검증 결과 세탁 결함의 최소 수정 — 재현된 Critical 4건, 같은 원인의 포함 Important, 문서 드리프트, CODE-005를 오프라인 회귀로 닫는다.

## Problem and context

대상은 `dot_codex/skills/verifying-open-source-contribution-candidates/`의 검증 스킬이다. 2차 quality-goal 실행은 COMPLETED로 종결되었고 `discover` 실경로를 한 차례 라이브 검증했지만, 후속 PR 사전 리뷰는 준비 차단으로 판정했다. `pre-review-summary.md`, `followup-scope.md`, 보존 재현 스크립트와 `repro/output.txt`가 확인한 공통 결함은 조회 실패, 형식 불일치, 예산 소진, 재검증 실패 같은 **모름**이 확인된 부재·중복 없음·정책 없음·여전히 유효한 ready 같은 **검증된 부정**으로 바뀐다는 것이다.

구체적으로 저장소 단계에서 예산이 소진되면 먼저 완주한 저장소의 미처리 조합이 `records`, `failed_scopes`, `skipped_by_cap` 어디에도 남지 않는다. `record`의 금지 조합 분기는 기존 테스트가 잘못된 키와 빈 `records`를 함께 사용해 실제로 실행되지 않는다. 정책 파일의 `request-failed` 상태는 ready 게이트에서 읽히지 않고, `recheck`의 세 실패 경로는 후보를 바이트 동일하게 통과시켜 run 결과까지 `actionable-candidates`로 남긴다. 같은 원인은 `record` manifest의 낙관적 하드코딩, `render`의 낙관적 기본값, 파싱 실패 payload 합성, 미신뢰 검색 단서의 질의 주입, 형식 불일치 discovery의 거부 우회에서도 드러난다.

코드 근거는 `scripts/verify_candidates.py:1758,1786`의 budget 분기, `:2779-2794`의 금지 조합 gate, `:1101,1148,2040,2185-2203,3018`의 정책 status 생산/소비, `:3186-3216`의 recheck 실패 통과, `:2898-2910`의 record manifest 하드코딩, `:2582-2583`의 render default, `:590-594,1060-1074`의 payload 합성/정책 소비, `:670-681,403-413`의 guard 예외 포착, `:1330-1336,1383`의 query 조립, `:2765-2767`의 discovery 첨자 접근, `:1135`의 entry count다. 테스트 결함은 `tests/test_verify_candidates.py:362-379,519-525,1762`에서 확인되었고 보존 fixture와 `repro/output.txt`가 모두 오프라인으로 재현했다.

확정 범위는 `followup-scope.md`의 재현·분류를 따른다. 현재 요청이 열거한 12개 항목을 12개 요구사항 정의로 만든다. 그 문서에서 별도 포함 판정된 형식 불일치 2xx 검색 응답(I12)은 파싱/형식 실패를 검증된 결과로 소비하는 동일 경계이므로 R2.2에서 I3와 함께 처리한다. 이로써 별도 요구사항을 늘리지 않으면서 확정 범위의 포함 결함을 누락하지 않는다. CODE-006은 결함이 아니라는 재평가를 유지한다.

이번 산출물은 SPEC_REVIEW 라운드 2 개정이다. 라운드 1 기준은 보존된 `snapshots/spec-r1.md`이며, 그 이후의 변경과 finding 해소 관계는 `spec-revision-notes.md`의 `라운드 2 개정` 표에 기록한다.

현재 구현 계약은 후보 필드 29개, recheck 변경 가능 필드 9개와 그 여집합의 default-deny, 상태/이유 표, readiness 키 12개, policy-check 키 8개, failed-scope 이유 5개, 접근 실패 outcome 4개, 종료 코드 0/1/2/3/4를 후속 #80~#82에 제공한다. 이번 수정은 이 폐쇄 집합과 schema version을 넓히지 않는다. 경고 문자열과 기존 manifest 필드를 사용해 불완전성을 드러내고, ready 차단에는 기존 `unverified`/`insufficient-evidence` 조합을 사용한다.

## Goals

1. 선택된 모든 저장소×패턴 조합의 귀속을 완전하고 상호 배타적으로 만들어 예산 소진 뒤에도 유실된 범위가 없게 한다.
2. 정책·검색·discovery·recheck의 실패 또는 형식 불일치를 확인된 부재나 성공으로 해석하지 못하게 하고, 그런 근거로 actionable 상태가 산출되지 않게 한다.
3. 미신뢰 검색 단서가 대상 저장소의 검색 범위를 벗어나지 못하게 한다.
4. discovery의 부분 실패를 `record` manifest와 Markdown까지 정직하게 전파한다.
5. 기존 출력 계약과 종료 코드 우선순위를 유지하면서 표적 회귀와 전체 오프라인 테스트로 변경을 판정한다.

## Non-goals

1. I5의 403/429/5xx 재시도 대상 집합 변경. 이미 라이브 검증된 예산·재시도 계약을 바꾸므로 별도 사용자 승인과 새 라이브 검증이 필요하다.
2. I8의 `finally` 무보호 `rmtree` 수정. 결과 세탁과 독립적인 clone 정리 견고성 작업이다.
3. I9의 미신뢰 텍스트 `sha256` 이중 의미 수정. 현재 게이트 영향이 없고 필드 의미·문서화 결정을 별도로 해야 한다.
4. I11의 `static_search.available: true` 고정 수정. 읽기 한계를 표현할 새 채널이 필요한 기능 확장이다.
5. I13의 clone 실패 진단 정보 확장. ready 게이트가 아니라 진단 품질 작업이다.
6. CODE-006 변경. 재평가 결과 결함이 아니므로 코드와 문서를 바꾸지 않는다.
7. 새 서브커맨드, 새 상태·상태 이유·failed-scope 이유·접근 실패 outcome·candidate 필드·readiness 키·policy-check 키, schema version 변경, 새 의존성 도입.
8. `#80`~`#82` 구현, 기능 확장, 추가 GitHub 요청, `discover` 라이브 재실행, 새 라이브 검증, 대상 저장소 코드 실행, 의존성 설치.
9. `assessment`·`record`·`recheck` 실경로 라이브 검증. 이 경로는 승인되지 않았으며 오프라인 fixture만 사용한다.
10. commit, push, PR 생성, merge, `chezmoi apply`, 배포, GitHub Issue·댓글 작성, `main`·다른 worktree·전역 설치본 수정.
11. `docs/development/2026-09-06-79-verifying-open-source-contribution-candidates/`와 `docs/development/2026-09-07-79-verifying-open-source-contribution-candidates-plan-redesign/`의 파일 또는 이전 quality-goal 상태 수정. 이들은 불변 이력이다.
12. `#79` 전체 완료·배포 완료 주장. 유지되는 한계는 `discover` 실경로만 한 차례 검증되었고 `CAN-*` 실물은 없다는 것이다.

## Requirements

사전 리뷰 finding과 요구사항의 대응은 C1→R1.1, C2→R1.2, I7→R1.3, C3→R2.1, I3·I12→R2.2, I4→R2.3, I6→R2.4, C4→R3.1, I1→R3.2, I2→R3.3, I10→R4.1, CODE-005→R4.2다.

### R1. 범위 귀속과 입력 게이트

- **R1.1** `discover`가 cap 적용 전에 만든 전체 저장소×패턴 조합 universe는 `(repository, pattern_id)` 기준으로 서로 겹치지 않는 `records`, `skipped_by_cap`, `failed_scopes` 중 정확히 하나에 귀속되어야 한다. cap으로 선택된 조합은 `records` 또는 `failed_scopes`에만, cap에서 제외된 조합은 `skipped_by_cap`에만 들어간다. 저장소 단계의 어느 위치에서든 예산이 소진되면 이미 완주했으나 조합 단계가 시작되지 않은 저장소를 포함해 아직 레코드가 되지 않은 모든 선택 조합을 기존 이유 `budget-exhausted`의 `failed_scopes`로 남기고, 관련 repository run의 `reason`도 `budget-exhausted`로 남긴다. 출력 조립 직전 이 완전 분할을 검사한다. 중복이나 누락으로 불변식이 깨지면 기존 계약 위반 종료 코드 2를 사용하고, 기존 redaction 경로를 거친 정확히 한 줄의 stderr `error: discover partition invariant violated`만 남기며 traceback을 내지 않는다. 이때 `discovery.json`, manifest run, 선택 Markdown 출력은 새로 만들거나 기존 파일을 수정하지 않는다. 불변식을 만족한 예산 소진 결과는 이 내부 계약 위반과 구별하여 계속 종료 3과 partial 산출물을 쓴다.
- **R1.2** `record` 게이트는 실제 discovery `records`에 존재하더라도 같은 조합이 `skipped_by_cap` 또는 `failed_scopes`에 선언되어 있으면 종료 코드 2와 `combination is absent, skipped, or failed` 오류로 거부해야 한다. 회귀 테스트는 존재하지 않는 레코드 분기가 아니라 `combo in forbidden_combos` 분기를 `skipped_by_cap`과 `failed_scopes` 각각으로 실행하며, 잘못된 최상위 `skipped`/`failed` 키를 사용하지 않는다.
- **R1.3** `record`는 assessment 결합 전에 discovery 문서의 형태를 검증해야 한다. 최소한 top-level object와 schema version, object인 `inputs`와 그 안의 repository 배열, 배열인 `records`·`skipped_by_cap`·`failed_scopes`·`method_limitations`, `complete`/`partial`/`failed` 중 하나인 `status`, 각 구획 항목의 object 형태 및 조합 키, 각 record의 비어 있지 않은 `repository_node_id`와 이후 첨자 접근하는 필수 필드를 확인한다. `repository_node_id` 누락이나 배열이어야 할 구획이 문자열인 입력은 트레이스백·출력 파일 없이 안전한 한 줄 오류와 종료 코드 2로 끝나며 금지 조합 게이트를 우회하지 못한다.

### R2. 실패 상태와 미신뢰 입력

- **R2.1** 정책 결과 소비자는 `found`만 보지 않고 `policy_files[].status`의 `found`/`absent`/`request-failed`를 구분해야 한다. 대상 저장소와 `{owner}/.github` 각각에서 다음 경로를 해당 `POLICY_CHECK_KEYS`에 매핑한다: `contributing`은 `CONTRIBUTING.md`·`.github/CONTRIBUTING.md`·`docs/CONTRIBUTING.md`, `issue_template`은 `.github/ISSUE_TEMPLATE`, `pr_template`은 `.github/PULL_REQUEST_TEMPLATE.md`, `security_policy`는 `SECURITY.md`·`.github/SECURITY.md`·`docs/SECURITY.md`, `code_of_conduct`는 `CODE_OF_CONDUCT.md`·`.github/CODE_OF_CONDUCT.md`, `cla_or_dco`와 `ai_policy`는 앞의 정확히 10개 `POLICY_PATHS` 전부다. `program_rules`는 로컬 입력이므로 `policy_files[]` 경로에 매핑하지 않는다. 이 매핑에 속하는 경로 하나라도 `request-failed`이면 `record`는 `policy_files_reviewed: confirmed`와 `issue-ready` 또는 `pr-ready`의 결합을 거부하고, 확인된 `absent`만 실패 없는 부재로 취급한다. 매핑 밖 경로의 `request-failed`만으로는 이 게이트를 발동하지 않는다. 거부는 기존 redaction 경로의 한 줄 stderr와 종료 2로 끝나며 후보·manifest run·선택 Markdown 출력을 새로 만들거나 기존 파일을 수정하지 않는다. `recheck`에서도 매핑된 `request-failed`를 부재나 정책 불변으로 바꾸지 않고 불완전 관찰로 처리하여 R3.1의 상태 차단을 적용한다. 경고만 추가한 채 public ready를 유지하는 구현은 불충족이다.
- **R2.2** HTTP 성공 코드라도 JSON 파싱 실패나 소비자별 필수 형태 불일치는 성공 payload로 합성하거나 확인된 결과로 소비하지 않는다. 정책 파일 경로의 파싱/형식 실패는 `status: request-failed`, `found: false`, null hash/content와 경고가 되어야 하며 `found: true` 해시를 만들지 않는다. issue/PR 중복 검색의 non-object payload 또는 필수 검색 필드 형식 불일치는 `discover`와 `recheck` 모두 `duplicate_search.complete: false`와 경고로 남아 `open_and_closed_searched: confirmed`를 뒷받침하지 못한다. community profile 응답도 2xx이더라도 payload가 object가 아니거나 `files`가 object가 아니면 기존 비-2xx 실패와 똑같이 취급한다. 즉 `repository_checks.community_profile_files`의 요청 전 기본값을 덮어쓰지 않고 repository run의 `stages_completed`에 `community_profile`을 추가하지 않으며 경고를 남긴다. 새 필드나 상태를 만들지 않고 기존 `stages_completed` 유무를 관측 성공 신호로 유지한다. 이는 확정 범위의 I3과 I12 및 같은 원인의 community profile 소비자를 하나의 응답 경계에서 함께 닫는다.
- **R2.3** `run_child`의 실행 파일·서브커맨드·HTTP 메서드 allowlist 위반은 transport 오류와 구별되는 fail-closed 입력/불변식 오류여야 한다. 이 오류는 상태 599 payload로 변환하지 않고 같은 요청을 재시도하지 않으며 sleep을 호출하지 않는다. CLI 경계에서는 secret redaction을 거친 한 줄 오류와 종료 코드 2가 되고, 실패한 guard 호출 때문에 최대 네 번의 예산 소비나 420초 backoff가 발생하지 않는다. `discover` 또는 `recheck` 도중 이 오류가 발생하면 discovery/candidate 출력, manifest run, 선택 Markdown 출력을 새로 만들거나 기존 파일을 수정하지 않는다. OSError와 실제 subprocess/transport 실패의 기존 제한 재시도 계약은 유지한다.
- **R2.4** 분석의 `search_clues`는 미신뢰 입력이다. `discover`의 issue/PR 및 code 검색은 따옴표·역슬래시·제어 문자처럼 인용 경계를 바꿀 수 있는 단서를 요청 전에 fail-closed로 거부하고 해당 검색을 불완전/불가 및 경고로 기록해야 한다. 정상 query는 신뢰된 대상의 `repo:` 한정자 하나와 코드가 고정한 qualifier만 의미를 갖는다. `recheck`는 기존 snapshot의 저장된 query도 현재 후보 repository의 신뢰된 query 문법과 일치하는지 검증하고, 주입된 query를 재전송하지 않는다. 거부된 검색을 `complete: true`로 기록하지 않는다.

### R3. 상태·manifest·render 정직성

- **R3.1** 선택된 후보의 recheck가 선행 예산 소진 단축, `BudgetExhausted`, `observation is None` 중 어느 경로로 실패해도 그 후보는 그 실행의 actionable 결과로 남을 수 없다. 기존 상태가 `reproduced`, `issue-ready`, `pr-ready`, `private-report-ready` 중 하나이면 기존 조합 `unverified`/`insufficient-evidence`로 낮추고 `blocking_gaps`에 `recheck-failed`를 중복 없이 추가하며 `next_recheck_required`를 `false`로 갱신한다. 마지막 성공 관찰의 `verified_at`과 `verified_base_sha`는 새 성공처럼 갱신하지 않되, top-level과 마지막 snapshot의 상태·이유·시각·SHA 일치 및 append-only history를 지키는 실패 snapshot을 정확히 하나 추가한다. 실패 snapshot의 `evidence`는 정확히 기존 8키를 가진다. `readiness_checks`, `reproduction`, `execution_evidence`, `duplicate_verdict`는 직전 snapshot 값을 깊은 복사하여 동일하게 승계한다. 미관측 네 필드는 `repository_checks: null`, `observed_head_sha: null`, 모든 `POLICY_CHECK_KEYS` 8개의 값이 각각 `{found: null, source: null, sha256: null, assessment: "recheck observation failed", evidence_links: []}`인 `policy_checks`, 그리고 `{queries: [], complete: false, unused_clues: [], method_limitations: ["GitHub search index delay can omit recently created or updated matches."]}`인 `duplicate_search`로 고정한다. 실패 후 top-level `repository_checks`는 `null`, top-level `duplicate_search`는 그 실패 snapshot의 불완전 객체와 깊은 비교로 같게 갱신하고, 여집합 default-deny에 따라 top-level `policy_checks`를 포함한 나머지 20필드는 바꾸지 않는다. run warning에는 candidate ID, repository, 실패 원인을 식별 가능하게 남기고, 모든 actionable 후보가 이렇게 차단되면 outcome은 `no-actionable-candidates`다. 부분 recheck와 예산 소진 종료는 3이며 4로 바뀌지 않는다. 이 후보는 새 `discover`+`record` 성공 전에는 ready로 복귀하지 않는다.
- **R3.2** `record`가 만드는 manifest run은 discovery의 `status`, record별 `warnings`, `failed_scopes`, `method_limitations`, `inputs.repositories`와 기존 구획 정보에서 재구성 가능한 repository 실패/예산 상태를 기존 manifest 필드에 보존해야 한다. discovery가 partial 또는 failed인데 `status: complete`, 빈 warnings, 모든 repository `checked`/null reason으로 하드코딩해서는 안 된다. 이를 위해 discovery schema나 candidate 29필드를 늘리지 않는다.
- **R3.3** `render`는 manifest 최신 run의 `complete`/`partial`/`failed`만 그대로 표시한다. manifest가 없거나 최신 run/status가 없거나 알 수 없는 값이면 `complete`로 대체하지 않고 `unknown`과 근거 부재 경고를 표시한다. malformed status를 원문 그대로 신뢰된 상태로 승격하지 않으며, 렌더링은 오프라인으로 종료 코드 0을 유지한다.

### R4. 문서와 호환성

- **R4.1** `SKILL.md`와 `references/verification-contract.md`는 선택 조합이 `records`·`skipped_by_cap`·`failed_scopes`에 완전 분할되고, 정책/recheck 실패는 ready를 차단하며, record/render가 불완전 상태를 보존한다는 실제 동작을 설명해야 한다. 두 문서는 각각 정확히 다음 네 문장을 포함해야 하고 `test_reference_documents_cover_contract`가 두 파일 모두에서 각 문장의 존재를 단정한다: `Every pre-cap repository-pattern combination appears in exactly one of records, skipped_by_cap, or failed_scopes.`, `A request-failed policy observation cannot support issue-ready or pr-ready.`, `A failed recheck makes an actionable candidate unverified with status_reason insufficient-evidence.`, `record and render preserve partial, failed, and unknown run states instead of defaulting them to complete.` 1·2차 실행 문서는 수정하지 않는다. 후보 필드 29개, `RECHECK_MUTABLE_FIELDS` 9개와 여집합 default-deny, `STATUS_REASON_TABLE`, `READINESS_KEYS` 12개, `POLICY_CHECK_KEYS` 8개, `FAILED_SCOPE_REASONS` 5개, `ACCESS_FAILURE_OUTCOMES` 4개, schema version과 종료 코드 0/1/2/3/4는 그대로 유지한다. 특히 종료 코드 4는 모든 저장소가 실제로 시도된 접근 실패인 경우에만 허용하고 예산 소진은 항상 3이다. 소스·테스트 변경으로 `compute_revision()` 값이 바뀌는 것은 계약된 동작이며 어떤 테스트도 revision을 고정 hash로 단정하지 않는다.
- **R4.2** 정책 디렉터리 응답의 `entry_count`는 원본 payload 길이가 아니라 문자열 `name`을 가진 object만 정렬·정규화한 `names`의 길이여야 한다. 혼합 payload fixture에서 `entry_count == len(names)`이고 canonical content hash도 같은 `names`를 기준으로 유지한다.

## Acceptance criteria

- **AC-1** 예산 24의 보존 fixture에서 먼저 완주한 저장소와 미시작 저장소의 모든 선택 조합이 세 구획 중 정확히 하나에 있고, 완주 저장소의 미처리 조합도 `failed_scopes/budget-exhausted`에 남으며 종료 코드는 3이다. [실행] (`CMD-1`)
- **AC-2** 정상, cap skip, 접근 실패, 저장소 단계 소진, 조합 단계 소진 fixture 각각에서 세 구획의 조합 집합은 pairwise-disjoint이고 합집합이 입력에서 계산한 cap 전 전체 조합과 같다. 같은 표적 테스트 안에서 중복과 누락을 각각 주입한 분기는 종료 2, redaction을 거친 정확히 한 줄의 stderr `error: discover partition invariant violated`, traceback 없음, discovery·manifest run·Markdown 출력의 생성·수정 없음까지 단정한다. [실행] (`CMD-1`)
- **AC-3** 전 저장소의 실제 접근 실패만 종료 4이고, 일부 접근 실패는 3이며, 저장소 단계와 조합 단계의 예산 소진은 사용 가능한 record 유무와 무관하게 항상 3이다. [실행] (`CMD-2`)
- **AC-4** discovery `records`에 평가 대상 조합을 둔 상태에서 같은 조합을 올바른 `skipped_by_cap`에 넣으면 `record`가 종료 2와 지정 오류를 내며, `records=[]` 분기에 의존하지 않는다. [실행] (`CMD-3`)
- **AC-5** AC-4와 같은 구성에서 실제 discovery record와 동일한 조합을 `failed_scopes`에 넣은 fixture가 `combo in forbidden_combos` 분기를 실행하여 종료 2, `combination is absent, skipped, or failed` 한 줄 stderr, 후보·manifest 출력 없음으로 거부됨을 표적 테스트가 단정한다. [실행] (`CMD-3`)
- **AC-6** `repository_node_id`가 없는 discovery record는 `KeyError` 트레이스백 없이 종료 2, 한 줄 stderr, 후보·manifest 출력 없음으로 끝난다. [실행] (`CMD-4`)
- **AC-7** `skipped_by_cap` 또는 `failed_scopes`가 배열이 아닌 discovery는 종료 2로 거부되어 평가가 종료 0으로 통과하지 못한다. [실행] (`CMD-4`)
- **AC-8** 같은 assessment에 대해 `CONTRIBUTING.md`가 `absent`이면 기존 조건 아래 public ready가 가능하지만, `CONTRIBUTING.md` 또는 비-contributing 경로인 `.github/ISSUE_TEMPLATE`이 `request-failed`이면 `policy_files_reviewed: confirmed`와 `issue-ready`/`pr-ready` 결합이 종료 2로 거부되고 후보·manifest run·Markdown 출력은 생성·수정되지 않는다. 매핑 밖 경로 하나만 `request-failed`인 대조군은 이 정책 경로 게이트만으로 거부되지 않는다. [실행] (`CMD-5`)
- **AC-9** recheck의 정책 조회가 `request-failed`이면 이를 absent 또는 unchanged로 기록하지 않고, 이전 actionable 후보에 R3.1의 차단 상태·gap·snapshot·outcome 규칙을 적용한다. [실행] (`CMD-5`)
- **AC-10** 2xx non-JSON 정책 본문과 형식 불일치 정책 object는 `request-failed`와 null hash/content로 남고, 오류 본문을 `message` object의 정책 내용으로 해시한 `found: true` 결과가 생기지 않는다. [실행] (`CMD-6`)
- **AC-11** `discover`와 `recheck`의 2xx non-object 또는 필수 필드 형식 불일치 issue-search payload는 warning과 `duplicate_search.complete: false`를 만들고 ready 근거로 사용할 수 없다. [실행] (`CMD-6`)
- **AC-12** allowlist guard가 `ValueError`를 내는 주입 runner에서 호출은 한 번뿐이고 sleeper 호출은 0회이며, 599 응답이나 네 번의 예산 소비 없이 CLI 종료 2의 redacted 한 줄 오류가 나온다. `discover`와 `recheck` 각각에서 discovery/candidate·manifest run·Markdown 출력은 생성·수정되지 않는다. [실행] (`CMD-7`)
- **AC-13** 따옴표로 인용을 닫고 다른 `repo:`를 삽입하는 단서, 역슬래시 단서, CR/LF 단서는 issue/code 요청으로 전달되지 않고 각각 검색 불완전/불가와 warning으로 남는다. 정상 단서는 기존 요청 수·순서·query 의미를 유지한다. [실행] (`CMD-8`)
- **AC-14** 주입된 `repo:`를 포함하는 기존 duplicate query를 가진 후보를 recheck해도 그 query는 transport에 전달되지 않고 recheck는 partial 및 non-actionable 차단으로 끝난다. [실행] (`CMD-8`)
- **AC-15** 선행 소진 단축, `BudgetExhausted`, repository/head 실패로 `observation is None`이 되는 세 경로 각각에서 이전 actionable 후보가 `unverified/insufficient-evidence`, `recheck-failed` gap, `next_recheck_required: false`, append-only 실패 snapshot을 가지며 이전 ready record와 바이트 동일하지 않다. 새 snapshot의 evidence key set은 정확히 8개이고, `readiness_checks`·`reproduction`·`execution_evidence`·`duplicate_verdict`가 직전 snapshot과 깊은 비교로 같으며 `repository_checks`와 `observed_head_sha`는 각각 null이다. [실행] (`CMD-9`)
- **AC-16** AC-15의 실패 snapshot에서 `policy_checks`의 정확히 8키가 모두 R3.1의 null/실패 값 객체와 같고 `duplicate_search`가 R3.1의 빈 queries·`complete: false` 객체와 같다. top-level `repository_checks`는 null, top-level `duplicate_search`는 snapshot 값과 같고 top-level `policy_checks`를 포함한 불변 20필드는 이전 값과 깊은 비교로 같다. 마지막 성공 `verified_at`·`verified_base_sha`는 바뀌지 않으며 top-level 상태·이유·시각·SHA는 마지막 snapshot과 일치한다. run은 candidate ID·repository·원인을 경고에 남기고 exit 3 및 `no-actionable-candidates`를 보고한다. [실행] (`CMD-9`)
- **AC-17** partial discovery를 입력한 `record` run이 기존 필드만으로 partial status, 원래 warning/failed scope/method limitation, repository별 budget/access reason을 보존하고 complete·checked로 세탁하지 않는다. [실행] (`CMD-10`)
- **AC-18** manifest 없음, 최신 run 없음, 알 수 없는 status의 세 render 입력은 모두 Markdown에 `complete`가 아닌 `unknown`과 근거 부재 warning을 표시하고 종료 0이며, 유효한 세 status는 그대로 표시한다. [실행] (`CMD-11`)
- **AC-19** `test_reference_documents_cover_contract`가 현재 배포 계약 문서 `SKILL.md`와 `references/verification-contract.md` 각각에 R4.1의 정확한 네 문장이 모두 있음을 단정하고, 이 Spec의 Non-goals 11은 1·2차 실행 문서를 불변 이력으로 고정한다. [실행] (`CMD-13`)
- **AC-20** 혼합 디렉터리 payload에서 문자열 name을 가진 항목만 canonical `names`에 들어가고 `entry_count`는 그 수와 같으며 hash는 같은 canonical names의 hash다. [실행] (`CMD-12`)
- **AC-21** 계약 테스트가 고정 상수 집합·종료 코드 규칙·문서 동기화를 확인하고 revision은 재계산값과 비교할 뿐 고정값을 기대하지 않는다. [실행] (`CMD-13`)
- **AC-22** Python 3.14.7, 표준 라이브러리, 무네트워크 fixture 환경에서 전체 스위트가 종료 0과 `OK`로 통과한다. [실행] (`CMD-14`)
- **AC-23** community profile의 2xx non-object payload와 `files`가 object가 아닌 payload 각각에서 `repository_checks.community_profile_files`는 요청 전 기본값과 깊은 비교로 같고 repository run의 `stages_completed`에 `community_profile`이 없으며 경고가 있다. 정상 object/`files` 대조군만 6개 bool을 덮어쓰고 해당 stage를 추가한다. [실행] (`CMD-6`)

## Requirements traceability

This table maps every requirement to acceptance criteria and the judgement method that proves the mapping.

| Requirement | Acceptance criteria | Judgement method |
|---|---|---|
| R1.1 | AC-1, AC-2, AC-3 | CMD-1, CMD-2 |
| R1.2 | AC-4, AC-5 | CMD-3 |
| R1.3 | AC-6, AC-7 | CMD-4 |
| R2.1 | AC-8, AC-9 | CMD-5 |
| R2.2 | AC-10, AC-11, AC-23 | CMD-6 |
| R2.3 | AC-12 | CMD-7 |
| R2.4 | AC-13, AC-14 | CMD-8 |
| R3.1 | AC-15, AC-16 | CMD-9 |
| R3.2 | AC-17 | CMD-10 |
| R3.3 | AC-18 | CMD-11 |
| R4.1 | AC-19, AC-21, AC-22 | `SKILL.md`, `references/verification-contract.md`, CMD-13, CMD-14 |
| R4.2 | AC-20 | CMD-12 |

## Architecture

변경은 기존 단일 스크립트의 경계 함수와 두 현재 계약 문서에 국한한다. 새 서브커맨드, 모듈, schema version, 외부 의존성은 없다.

1. **입력/transport 경계**는 unparseable body를 dict처럼 합성하지 않고, allowlist 위반과 실제 transport 실패를 구분한다. policy와 search 소비자는 2xx 여부뿐 아니라 payload shape까지 성공 조건으로 삼는다.
2. **검색 query 경계**는 신뢰된 repository와 고정 qualifier만 코드가 만들고, 미신뢰 clue는 안전한 단일 quoted phrase로 표현 가능한 경우에만 사용한다. 저장된 recheck query도 같은 문법 검사를 다시 통과해야 한다.
3. **discover 귀속 경계**는 cap 계산 직후 전체 조합 universe를 보존한다. 각 조합은 record 생성, cap skip, failed scope 중 한 상태로만 이동하며 출력 직전 분할 불변식을 검사한다. 예산 소진은 처리 cursor 이후의 모든 미귀속 조합을 failed scope로 이동한다. 유효한 부분 결과는 종료 3으로 쓰지만, 이동 후에도 분할 불변식이 깨진 내부 계약 위반은 출력 쓰기 전 종료 2로 차단한다.
4. **record 경계**는 discovery shape를 먼저 검증한 뒤 assessment를 결합한다. manifest는 새 정보를 추측하지 않고 discovery의 기존 status, record warnings, failed scopes, limitations, repository 입력으로 정직한 최소 상태를 재구성한다.
5. **recheck 경계**는 성공 관찰과 실패 시도를 분리한다. 성공만 관찰 시각·SHA를 갱신한다. 실패한 actionable 후보는 기존 상태 집합 안에서 unverified로 차단하고 history에 append-only 실패 상태를 남긴다. 실패 snapshot의 8키 evidence 중 승계 4키는 직전 값, 미관측 4키는 R3.1의 null/불완전 값으로 고정하고 top-level 상태·이유·시각·SHA를 마지막 snapshot과 일치시킨다.
6. **render 경계**는 관찰된 run status와 근거 없음의 `unknown` 표현만 사용하며 낙관적 default를 두지 않는다.

R1.1의 분할 불변식과 R3.1의 상태 차단은 서로 다른 층이다. 전자는 `discover` 범위의 조합 귀속을 보장하여 유효한 예산 소진 결과를 종료 3으로 보존하고, 분할 자체가 깨진 내부 계약 위반만 무출력 종료 2로 막는다. 후자는 `recheck` 후보의 actionability를 제거한다. 둘 다 예산 소진을 접근 실패로 재분류하지 않으므로 종료 4 규칙과 충돌하지 않는다. R3.1이 바꾸는 모든 candidate top-level 필드는 기존 9개 `RECHECK_MUTABLE_FIELDS` 안에 있고, 나머지 20개는 그대로여서 여집합 default-deny와도 모순되지 않는다.

## Interfaces and data flow

입력·출력 파일 이름과 envelope는 유지한다.

- `discover`: validated analysis + repository/pattern/cap/budget → `discovery.json` + manifest run. 조합 universe를 만든 뒤 `records`/`skipped_by_cap`/`failed_scopes`로 완전 분할한다.
- `record`: shape-validated `discovery.json` + hash-bound `assessment.json` → gate → `candidates.json` + manifest run + optional Markdown. `request-failed` 정책과 금지 조합은 후보 쓰기 전에 종료 2로 거부된다.
- `recheck`: validated candidates + selected IDs + budget/fixture → successful observation 또는 failure state transition → candidates + manifest. 실패 transition은 기존 성공 시각·SHA를 보존하면서 actionable status를 제거한다.
- `render`: candidates + optional manifest → Markdown. run 근거가 없으면 `unknown`; 후보 자체의 status 집계는 기존 후보 계약을 따른다.

외부 경계는 기존처럼 read-only `gh api --method GET`과 승인된 shallow clone뿐이다. 이번 검증에서는 `--fixture-dir`와 주입 transport만 사용하므로 네트워크 요청과 clone은 발생하지 않는다. `compute_revision()`은 구성된 기존 경로를 해시하며 소스·테스트·계약 문서 변경에 따라 자연스럽게 달라진다.

## Failure behavior

- malformed discovery와 assessment gate 위반은 출력 쓰기 전에 safe stderr 한 줄과 종료 2로 끝난다.
- 정책·검색·community profile payload가 2xx여도 파싱/shape 검증에 실패하면 confirmed evidence가 아니다. 정책은 failed, 검색은 incomplete가 되고 community profile은 기본값과 미완료 stage를 유지하며 모두 warning을 남긴다.
- unsafe clue/query는 요청하지 않는다. issue duplicate search는 incomplete, code search는 unavailable로 남고 run은 partial이다.
- allowlist guard 위반은 재시도·sleep·599 합성·출력 쓰기 없이 종료 2다. 실제 OSError/subprocess/HTTP retry 동작은 바꾸지 않는다.
- discover 예산 소진은 모든 미귀속 조합을 failed scope로 남기고 분할 불변식을 만족하면 항상 종료 3이다. 분할 자체가 깨진 내부 계약 위반만 종료 2이며 출력이 없다. 모든 저장소가 실제 접근을 시도해 실패한 경우에만 종료 4다.
- recheck 실패는 이전 actionable 후보를 unverified로 차단하고 기존 성공 관찰 시각·SHA를 유지하며 실패 snapshot과 식별 가능한 warning을 추가한다. 자동 복구나 상태 승격은 하지 않는다.
- render의 run 근거 부재는 성공으로 추측하지 않고 `unknown`으로 표시한다.

## Security and risk

원격 정책 본문, Issue/PR 제목, 분석에서 온 검색 단서는 모두 미신뢰 데이터다. 가장 큰 위험은 텍스트가 query 문법 경계를 탈출해 다른 저장소를 검색한 뒤 그 결과가 complete로 기록되는 것이다. R2.4는 위험 문자를 가진 단서와 검증되지 않은 저장 query를 요청 전에 차단한다. 정책/검색 payload의 parser와 shape validator는 오류 페이지나 예상 밖 JSON을 실제 정책·검색 부재로 받아들이지 않는다.

상태 무결성 위험은 run-level warning만 남고 후보가 ready인 채 유지되는 것이다. R2.1과 R3.1은 각각 record와 recheck 쓰기 경계에서 actionable 상태를 제거한다. 오류 메시지는 기존 redaction 경로를 사용하고 응답 header allowlist는 바꾸지 않는다. 새 민감 데이터, 새 외부 쓰기, 새 권한은 없다.

잔여 위험은 안전한 clue 문자 집합을 보수적으로 제한해 일부 정상 단서가 검색되지 않을 수 있다는 점이다. 이는 다른 저장소 검색을 complete로 오인하는 것보다 안전하며, `complete: false`와 warning으로 사용자에게 드러난다. I5의 retry 집합은 의도적으로 유지되므로 403의 긴 대기는 별도 승인 작업으로 남는다.

## Test strategy

모든 판정은 `/opt/homebrew/bin/python3` 3.14.7과 Python 표준 라이브러리만 사용한다. 표적 테스트는 기존 unittest helper, fixture transport, 주입 runner/sleeper/clock을 사용하고 네트워크를 열지 않는다. 테스트 이름은 구현 계획이 그대로 만들 수 있도록 아래에 고정한다. `test_skill_contract.test_no_hardcoded_targets_dates_models`는 스킬 디렉터리의 `.md`·`.json`·`.py`에서 api-version 표기 줄을 제외한 `20\d{2}-\d{2}-\d{2}` literal을 거부하므로, 새 recheck fixture와 단정의 `verified_at`·`observed_at`은 연도 조각과 나머지 조각을 이어 붙여 만들고 이 형태의 날짜 literal을 소스에 쓰지 않는다.

### 판정 명령 표

| ID | 명령 | 통과 조건 |
|---|---|---|
| CMD-1 | `cd /Users/lee-kyu-hwan/code/dotfiles__worktrees/79-feat-contribution-candidate-verifier/dot_codex/skills/verifying-open-source-contribution-candidates && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest tests.test_verify_candidates.VerifyCandidatesTests.test_budget_exhaustion_partitions_all_selected_combinations -v` | 종료 0, 해당 테스트 `ok`; 모든 분할 fixture와 중복·누락 주입의 종료 2·고정 한 줄 stderr·무출력 단정 통과 |
| CMD-2 | `cd /Users/lee-kyu-hwan/code/dotfiles__worktrees/79-feat-contribution-candidate-verifier/dot_codex/skills/verifying-open-source-contribution-candidates && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest tests.test_verify_candidates.VerifyCandidatesTests.test_exit_code_matrix -v` | 종료 0, 해당 테스트 `ok`; 종료 4/3 우선순위 단정 통과 |
| CMD-3 | `cd /Users/lee-kyu-hwan/code/dotfiles__worktrees/79-feat-contribution-candidate-verifier/dot_codex/skills/verifying-open-source-contribution-candidates && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest tests.test_verify_candidates.VerifyCandidatesTests.test_record_rejects_present_forbidden_combinations -v` | 종료 0, 실제 record와 겹치는 skipped/failed fixture가 두 `combo in forbidden_combos` 분기의 종료 2·지정 stderr·무출력을 단정하여 `ok` |
| CMD-4 | `cd /Users/lee-kyu-hwan/code/dotfiles__worktrees/79-feat-contribution-candidate-verifier/dot_codex/skills/verifying-open-source-contribution-candidates && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest tests.test_verify_candidates.VerifyCandidatesTests.test_record_rejects_malformed_discovery_shapes -v` | 종료 0, 누락 node ID와 잘못된 구획 타입이 safe exit 2로 단정됨 |
| CMD-5 | `cd /Users/lee-kyu-hwan/code/dotfiles__worktrees/79-feat-contribution-candidate-verifier/dot_codex/skills/verifying-open-source-contribution-candidates && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest tests.test_verify_candidates.VerifyCandidatesTests.test_policy_request_failure_blocks_ready -v` | 종료 0, record/recheck의 absent 대 request-failed 구분 단정 통과 |
| CMD-6 | `cd /Users/lee-kyu-hwan/code/dotfiles__worktrees/79-feat-contribution-candidate-verifier/dot_codex/skills/verifying-open-source-contribution-candidates && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest tests.test_verify_candidates.VerifyCandidatesTests.test_malformed_success_payloads_remain_incomplete -v` | 종료 0, policy·discover/recheck duplicate·community profile malformed 2xx의 failed/incomplete/default+미완료 stage 단정 통과 |
| CMD-7 | `cd /Users/lee-kyu-hwan/code/dotfiles__worktrees/79-feat-contribution-candidate-verifier/dot_codex/skills/verifying-open-source-contribution-candidates && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest tests.test_verify_candidates.VerifyCandidatesTests.test_allowlist_violation_fails_without_retry -v` | 종료 0, 1회 guard·0 sleep·safe exit 2 단정 통과 |
| CMD-8 | `cd /Users/lee-kyu-hwan/code/dotfiles__worktrees/79-feat-contribution-candidate-verifier/dot_codex/skills/verifying-open-source-contribution-candidates && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest tests.test_verify_candidates.VerifyCandidatesTests.test_untrusted_search_clues_cannot_escape_repository_scope -v` | 종료 0, discover/recheck query 주입이 transport에 도달하지 않음 |
| CMD-9 | `cd /Users/lee-kyu-hwan/code/dotfiles__worktrees/79-feat-contribution-candidate-verifier/dot_codex/skills/verifying-open-source-contribution-candidates && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest tests.test_verify_candidates.VerifyCandidatesTests.test_recheck_failure_blocks_actionable_candidate -v` | 종료 0, 세 실패 경로의 후보 상태·history·manifest 단정 통과 |
| CMD-10 | `cd /Users/lee-kyu-hwan/code/dotfiles__worktrees/79-feat-contribution-candidate-verifier/dot_codex/skills/verifying-open-source-contribution-candidates && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest tests.test_verify_candidates.VerifyCandidatesTests.test_record_manifest_preserves_discovery_failure_state -v` | 종료 0, partial/warnings/repository reason 전파 단정 통과 |
| CMD-11 | `cd /Users/lee-kyu-hwan/code/dotfiles__worktrees/79-feat-contribution-candidate-verifier/dot_codex/skills/verifying-open-source-contribution-candidates && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest tests.test_verify_candidates.VerifyCandidatesTests.test_render_never_defaults_unknown_status_to_complete -v` | 종료 0, missing/unknown/valid status 렌더 단정 통과 |
| CMD-12 | `cd /Users/lee-kyu-hwan/code/dotfiles__worktrees/79-feat-contribution-candidate-verifier/dot_codex/skills/verifying-open-source-contribution-candidates && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest tests.test_verify_candidates.VerifyCandidatesTests.test_policy_directory_entry_count_uses_filtered_names -v` | 종료 0, entry_count와 canonical names/hash 단정 통과 |
| CMD-13 | `cd /Users/lee-kyu-hwan/code/dotfiles__worktrees/79-feat-contribution-candidate-verifier/dot_codex/skills/verifying-open-source-contribution-candidates && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest tests.test_skill_contract.SkillContractTests.test_reference_documents_cover_contract tests.test_verify_candidates.VerifyCandidatesTests.test_print_revision_matches_recomputation -v` | 종료 0, 두 테스트 `ok`; 두 계약 문서 각각의 정확한 네 문장과 동적 revision 재계산 통과 |
| CMD-14 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s "/Users/lee-kyu-hwan/code/dotfiles__worktrees/79-feat-contribution-candidate-verifier/dot_codex/skills/verifying-open-source-contribution-candidates/tests" -t "/Users/lee-kyu-hwan/code/dotfiles__worktrees/79-feat-contribution-candidate-verifier/dot_codex/skills/verifying-open-source-contribution-candidates/tests" -p 'test_*.py'` | 종료 0, 전체 출력에 양의 테스트 수의 `Ran … tests`와 `OK`; 네트워크 runner 호출 없음 |

표적 테스트는 먼저 현재 코드에서 실패하는 것을 확인한 뒤 최소 구현으로 통과시킨다. 이후 CMD-14로 기존 44개 테스트와 신설 회귀를 함께 실행한다. lint, type-check, build 도구는 이 스킬에 구성되어 있지 않으므로 별도 판정 명령을 만들지 않는다. 라이브 명령, 대상 저장소 명령, 의존성 설치 명령은 판정 수단에 포함하지 않는다.

## Decisions

### D1. 조합 cursor 보정과 출력 직전 분할 불변식을 함께 둔다

대안은 예산 예외 지점마다 누락만 보정하는 방식, 출력 직전 불변식만 검사해 실패시키는 방식, 둘을 결합하는 방식이다. 예외 지점 보정만으로는 새 `continue`/`break` 경로가 같은 결함을 되살릴 수 있고, 검사만으로는 사용 가능한 partial 결과를 버린다. 따라서 남은 조합을 `failed_scopes/budget-exhausted`로 이동한 뒤 완전 분할을 검사한다.

### D2. 정책 조회 실패는 warning-only가 아니라 public-ready gate 실패다

`request-failed`를 `absent`와 동일시하거나 warning만 남기는 대안은 재현된 ready 세탁을 유지한다. 새 상태를 추가하는 대안은 후속 소비자 계약을 넓힌다. 따라서 record에서는 public ready assessment를 종료 2로 거부하고, recheck에서는 기존 unverified 상태 조합으로 차단한다.

### D3. 검색 단서는 이스케이프 추정 대신 위험 문자를 fail-closed로 거부한다

GitHub 검색 문법의 escape 해석을 새 라이브 검증 없이 가정하는 방식은 repository confinement를 증명하기 어렵다. 모든 문자를 제거·정규화하면 원래 단서와 다른 검색을 complete로 오인할 수 있다. 따옴표·역슬래시·제어 문자가 있는 단서는 요청하지 않고 incomplete/unavailable로 남기는 방식이 가장 작고 검증 가능하다.

### D4. recheck 실패는 기존 `unverified/insufficient-evidence`로 차단한다

run warning만 추가하면 후보가 actionable인 결함이 남는다. 새 `recheck-failed` 상태/이유를 추가하면 상태 표와 후속 소비자를 넓힌다. 기존 unverified 조합, mutable `blocking_gaps`, append-only snapshot을 사용하면 상태를 실제로 차단하면서 29/9 필드 계약을 유지할 수 있다. 마지막 성공 시각과 SHA는 실패 시도 때문에 갱신하지 않는다.

### D5. discovery와 candidate schema를 넓히지 않는다

record가 원래 discover manifest를 추가 입력으로 받거나 discovery에 top-level warnings/repositories를 신설하는 대안은 CLI 또는 schema 확장이다. 이번에는 기존 `status`, `inputs.repositories`, record warnings, failed scopes, limitations에서 manifest의 정직한 최소 상태를 재구성한다. 원래 transport 세부가 재구성 불가능하면 추측하지 않고 canonical failure reason만 표시한다.

### D6. render의 근거 부재는 `unknown`으로 표현한다

manifest를 필수화하면 기존 optional interface가 깨지고, 알 수 없는 문자열을 그대로 신뢰하면 상태 vocabulary가 우회된다. optional interface와 종료 0은 유지하되 missing/malformed status를 `unknown`과 warning으로 렌더한다.

### D7. I12는 I3과 같은 malformed-success 경계에서 처리한다

정책과 검색마다 별도 임시 보정을 두면 같은 2xx payload 오류가 재발한다. transport는 파싱 실패를 성공 dict로 합성하지 않고, 각 소비자는 자신의 shape를 확인한다. 정책은 request-failed, 검색은 incomplete로 fail-closed한다.

### D8. cross-regression 판정

R1.1의 구획 완전성은 discover의 미처리 조합을 기존 failed scope로 귀속할 뿐 후보 상태를 만들지 않는다. 완전 분할을 이룬 예산 소진은 R1.3의 malformed-input 종료 2와 구별되어 기존 종료 3을 유지하고, 분할 불변식 자체가 깨진 경우만 출력 전 계약 위반 종료 2를 사용하므로 종료 3 규칙을 가리지 않는다. 두 종료 2 경로는 같은 redacted 한 줄·no-traceback·무출력 계약을 공유하지만 입력 검증과 출력 불변식이라는 서로 다른 경계다. R2.1·R3.1의 상태 차단은 record/recheck 후보 층에서만 일어나므로 같은 조합을 두 구획에 넣지 않는다. 예산 소진은 어느 층에서도 접근 실패로 바뀌지 않아 종료 3/4 규칙을 보존한다. R3.1의 실패 snapshot은 `SNAPSHOT_EVIDENCE_FIELDS` 8키를 정확히 유지하고 `INHERITED_EVIDENCE_FIELDS` 4키 동일성을 지키며, 상태·이유·`verified_at`·`verified_base_sha`의 top-level/latest-snapshot 일치도 보존한다. top-level에서 바꾸는 `status`, `status_reason`, `blocking_gaps`, `verification_history`, `next_recheck_required`, `repository_checks`, `duplicate_search`는 모두 기존 `RECHECK_MUTABLE_FIELDS` 9개 안이고 나머지 20필드는 동일하므로 여집합 default-deny를 약화하지 않는다. R2.2의 policy, duplicate search, community profile 처리는 같은 malformed-2xx 원칙을 공유하되 각각 `request-failed`, `complete: false`, 기본값+미완료 stage라는 기존 소비자 신호를 사용해 서로의 판정을 덮어쓰지 않는다. R2.4의 unsafe clue 거부는 요청 전 입력 실패를 담당하므로 응답 후 R2.2 판정과 겹치지 않는다. 확인 결과 요구사항 간 충돌과 새 ready 우회는 없다.

<!-- strict-only:start -->

### Threat and trust boundaries

미신뢰 주체는 분석에 보존된 외부 PR 텍스트, 저장소 정책 파일, GitHub Issue/PR 응답, fixture payload다. 신뢰하는 것은 호출자가 정한 repository scope, 로컬 검증 스크립트, 허용된 `gh`/`git` 실행 파일과 로컬 fixture 경로다. 경계는 (1) body→JSON parser, (2) JSON→policy/search shape validator, (3) clue→query builder, (4) discovery→assessment gate, (5) recheck observation→candidate state transition이다. 통제는 malformed 성공 거부, 위험 clue/query 요청 금지, policy status 기반 ready 거부, append-only 실패 snapshot, allowlist 예외의 fail-closed 전파다.

### Authorization and tenant isolation

다중 tenant 기능은 없어 tenant isolation은 해당 없음이다. GitHub 인증은 기존 `gh` 자격을 read-only GET에만 사용하며 권한을 요구하거나 확대하지 않는다. clone과 대상 저장소 코드 실행은 이번 판정에 사용하지 않는다. 사용자 승인 없는 external proposal, GitHub write, 외부 코드 실행은 계속 금지된다.

### Migration, compatibility, and rollback

data migration과 backfill은 없다. schema version, candidate/status/reason/readiness/policy/failure 집합, 종료 코드 숫자는 유지된다. 기존 candidates는 읽을 수 있고, 향후 실패한 recheck를 받는 actionable record만 append-only snapshot과 기존 unverified 상태로 전이한다. `compute_revision()`은 해시 대상 파일 변경에 따라 바뀌며 고정 revision 호환성은 약속하지 않는다. rollback trigger는 고정 계약 테스트 실패, 정상 clue 요청 수/순서 변화, 기존 candidate validator 거부, 종료 4/3 우선순위 회귀다. rollback은 이번 구현의 scoped code/test/current-contract 변경만 되돌리고 1·2차 이력과 전역 설치본은 건드리지 않은 채 새 설계가 나올 때까지 이전 배포를 유지하는 것이다.

### Failure recovery and observability

관찰 신호는 discovery의 세 구획과 status, manifest의 repository reason/failed scopes/warnings/status/outcome, candidate의 status/reason/blocking gaps/history/latest snapshot, Markdown의 run status/warnings, 종료 코드다. partial discover는 failed scope를 보고 남은 범위를 새 승인 run에서 다시 discover한다. malformed assessment/discovery는 입력을 고친 뒤 record를 재실행한다. recheck-failed 후보는 외부 제안에 쓰지 않고 새 discover+record가 성공할 때까지 unverified로 둔다. 자동 retry 집합은 I5 범위로 남아 이번에 바꾸지 않는다.

### High-risk end-to-end verification

이번 변경의 고위험 경로는 미신뢰 query confinement, 예산 소진 구획 완전성, malformed 2xx 소비, 정책 실패 ready gate, 실패 recheck 상태 전이다. CMD-1, CMD-5, CMD-6, CMD-8, CMD-9가 보존 fixture와 주입 transport로 각 경로를 CLI 경계까지 검증하고 CMD-14가 cross-regression을 확인한다. 정지 조건은 network runner 호출, 대상 저장소 명령 실행, 의존성 요구, 선택 조합 누락/중복, malformed community profile의 완료 stage 기록, request-failed에서 ready 유지, recheck 실패 뒤 actionable outcome, 예산 소진 exit 4 중 하나라도 관찰되는 경우다. 새 라이브 검증은 승인 범위 밖이므로 수행하지 않으며, 과거 `discover` 1회 라이브 근거는 읽기 전용 역사일 뿐 이번 변경의 검증으로 재사용하지 않는다. 따라서 `assessment`·`record`·`recheck` 실경로와 `CAN-*` 실물은 여전히 미검증이라고 보고한다.

### No production mutation confirmation

자동 판정은 fixture 기반 unittest와 문서 검사뿐이며 GitHub, 원격 저장소, `main`, 다른 worktree, 전역 설치본, `$HOME` 설정을 변경하지 않는다. commit, push, PR, merge, `chezmoi apply`, 배포, Issue/comment 작성, 라이브 discover/recheck는 포함하지 않는다.

<!-- strict-only:end -->
