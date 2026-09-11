# Quality Goal Implementation Plan

- Task ID: 20260909T015728Z-79-pr-전-보완-code-002-code-search-형태-검증-i5-4c5e2758
- Mode: strict
- Status: PLAN_REVIEW
- Created: 2026-09-09T01:57:28Z
- Updated: 2026-09-10T01:30:00Z
- Source goal: #79 PR 전 보완 — CODE-002 code search 형태 검증, I5 권한 거부와 rate limit 구분 재시도, I8 clone 정리 실패로 산출물 유실 방지, I11 정적 검색 읽기 실패와 의도적 제외 구분, I9 sha256 의미 문서화

## Spec link

승인 대상 Spec 은 `/Users/lee-kyu-hwan/code/dotfiles__worktrees/79-feat-contribution-candidate-verifier/docs/development/2026-09-09-79-prereview-followup-retry-cleanup-static-search/spec.md` 이며 이 Plan 이 사용한 digest 는 `0f0309f3485973ec72b872b04a86233638d1f7c64606362e0552b44802c36df7` 다. Spec 리뷰 라운드 2 가 PASS 92 로 기록한 digest 와 같다. 요구사항 R1.1~R6.3 15개와 수용 기준 AC-1~AC-20 20개를 모두 소비한다.

## Global constraints

- 작업 경로는 `/Users/lee-kyu-hwan/code/dotfiles__worktrees/79-feat-contribution-candidate-verifier` 워크트리 하나다. `main`, 다른 워크트리, 전역 설치본(`~/.codex/skills`, `~/.claude/skills`), `$HOME` 설정을 바꾸지 않는다.
- 변경 허용 경로는 `dot_codex/skills/verifying-open-source-contribution-candidates/` 의 `scripts/verify_candidates.py`, `tests/test_verify_candidates.py`, `tests/test_skill_contract.py`, `tests/fixtures/**`, `SKILL.md`, `references/verification-contract.md`, `references/github-verification-contract.md`, 그리고 `docs/development/2026-09-09-79-prereview-followup-retry-cleanup-static-search/` 의 이번 실행 문서다.
- **불변 보존 대상**: `docs/development/2026-09-06-79-verifying-open-source-contribution-candidates/`, `docs/development/2026-09-07-79-verifying-open-source-contribution-candidates-plan-redesign/`, `docs/development/2026-09-08-79-pr-prereview-critical-fixes/`, 워크트리 루트 `AGENTS.md`, 형제 스킬 `analyzing-open-source-pr-patterns` 과 `collecting-recent-closed-prs`. 읽기만 하고 되돌리지도 않는다. `AGENTS.md` 는 이 실행이 만들지 않은 파일이므로 특히 손대지 않는다.
- commit, push, PR 생성, merge, `chezmoi apply`, 배포, GitHub Issue·댓글 작성을 하지 않는다. 추가 GitHub 요청, 라이브 `discover`·`recheck`, 대상 저장소 코드 실행, 의존성 설치를 하지 않는다. **모든 판정은 오프라인 fixture 와 주입 transport·sleeper·clock 으로 실행한다.**
- Python 은 `/opt/homebrew/bin/python3` 3.14.7, 표준 라이브러리만 사용한다. 모든 판정은 `PYTHONDONTWRITEBYTECODE=1` 로 실행한다.
- 테스트 우선 순서를 지킨다. 각 태스크는 실패하는 판정을 먼저 기록하고, 최소 구현 후 통과 판정을 기록한다. **판정 단정을 통과시키기 위해 약화·삭제·skip 처리하는 것을 금지한다.** 선행 구현이 없어 달성 불가한 단정을 만나면 순서를 다시 확인하고 단정은 그대로 둔다.
- 유지할 폐쇄 집합: `CANDIDATE_FIELDS`(29), `RECHECK_MUTABLE_FIELDS`(9, 여집합 default-deny), `STATUS_REASON_TABLE`, `READINESS_KEYS`(12), `POLICY_CHECK_KEYS`(8), `FAILED_SCOPE_REASONS`(5), `ACCESS_FAILURE_OUTCOMES`(4), `SNAPSHOT_EVIDENCE_FIELDS`(8), `INHERITED_EVIDENCE_FIELDS`(4), `COMMUNITY_PROFILE_KEYS`(6), `ALLOWED_RESPONSE_HEADERS`(7), `schema_version`, 종료 코드 0/1/2/3/4 와 그 우선순위. 계약 확장은 **R4.1 의 additive static-search 필드 세 개(`complete`, `exclusions`, `read_failures`)와 R2.3 의 additive retry event/warning 정보뿐** 이다.
- 예산·상한 상수를 키우지 않는다. `MAX_RETRIES = 3`(최초 요청 포함 최대 4회), `MAX_RETRY_DELAY_SECONDS = 300.0` 을 유지한다.
- **Spec 리뷰 라운드 2 의 미해소 advisory `SPEC-005`(Low) 를 구현에 반영한다.** R4.2 의 문언이 warning 계기를 "읽기 실패" 로 적었지만 `read_failures` 는 `walk` 항목도 담는다. 구현은 `read_failures` 가 비어 있지 않을 때 warning 을 내고 `static-search-incomplete:<count>` 의 `<count>` 는 `len(read_failures)` 로 한다. AC-11 이 stat·read·walk 세 주입을 모두 단정하므로 이 해석이 유일하게 단정을 만족한다. 이 사실을 테스트 주석에 남긴다.
- I9 는 문서만 바꾼다. 필드명·스키마·계산 코드를 바꾸지 않는다. I13 은 후속 문서화만 하고 구현하지 않으며 GitHub Issue 를 만들지 않는다.
- `compute_revision()` 해시 대상 6개 경로가 바뀌므로 리비전이 달라진다. 어떤 테스트도 리비전을 고정 hash 로 단정하지 않는다.
- 계약 테스트 함정: `tests/test_skill_contract.py:52` 의 `test_no_hardcoded_targets_dates_models` 는 스킬 디렉터리의 `.md`·`.yaml`·`.json`·`.py` 에서 (a) api-version 표기 없는 줄의 날짜 literal, (b) 모델명, (c) 이슈·PR URL 을 거부한다. `SKILL.md` 는 200줄 미만, 두 references 문서는 각각 400줄 미만을 유지한다. 현재 `SKILL.md` 30줄, `verification-contract.md` 145줄, `github-verification-contract.md` 82줄이다.
- 셸 변수 규약: `SK=/Users/lee-kyu-hwan/code/dotfiles__worktrees/79-feat-contribution-candidate-verifier/dot_codex/skills/verifying-open-source-contribution-candidates`, `PY=/opt/homebrew/bin/python3`, `RT=/Users/lee-kyu-hwan/code/dotfiles__worktrees/79-feat-contribution-candidate-verifier`, `QS=$RT/.claude/quality-state/20260909T015728Z-79-pr-전-보완-code-002-code-search-형태-검증-i5-4c5e2758`.

## File map

| 파일 | 책임 | 영향 인터페이스·동작 |
|---|---|---|
| `scripts/verify_candidates.py` `discover_code_search` (`:1463`~`:1500`) | code search 요청·소비 | 2xx payload 를 `_valid_search_payload` 동등 검사로 게이트, 실패 시 `available: false` + `total_count: null` + `invalid-search-payload` 경고 |
| `scripts/verify_candidates.py` `_retryable` (`:641`) | 재시도 판정 | 서명에 sanitized headers 추가, 403 을 header 근거로 `rate-limit`/`permission-denied` 분류, 판정과 이유를 함께 반환 |
| `scripts/verify_candidates.py` `GhApiClient.get_json` (`:670`, 판정 `:709`), `FixtureTransport.get_json` (`:743`, 판정 `:782`) | 두 transport 의 재시도 루프 | 같은 판정·지연 함수 사용, `request_events` 에 `retry_decision`(`retry` 또는 `return`)과 `retry_reason` 기록. 403 의 `retry_reason` 은 최소 `retry-after`, `remaining-zero-and-reset`, `ambiguous-403`, `retry-limit-reached` 네 값을 구분한다 |
| `scripts/verify_candidates.py` `_repository_failure` (`:1081` 부근) | 접근 실패 매핑 | 명시적 rate-limit 403 소진은 `failed`/`transport-or-5xx`/`repository-failed`, 모호한 403 은 기존 `forbidden`/`http-403`/`repository-forbidden` |
| `scripts/verify_candidates.py` `_append_response_warning` 계열 | 최종 실패 warning | 기존 `request-failed:<path>:http-403` 접두 유지 + `rate-limit:<reason>` 또는 `permission-denied:<reason>` 덧붙임 |
| `scripts/verify_candidates.py` `static_search` (`:492`~`:545`) | 정적 검색 | `complete`·`exclusions`·`read_failures` 추가, `os.walk(onerror=...)` 로 순회 실패 포착, 원인별 계수 분리 |
| `scripts/verify_candidates.py` `_static_record` (`:1747`) | 정적 검색 결과 조립 | clone 미요청·실패 기본 객체에 `available: false`, `complete: false` 와 빈 additive 필드 포함 |
| `scripts/verify_candidates.py` `discover_exit_code` (`:1550`, 술어 `:1565-1575`) | 종료 코드·상태 | record warning 검사에 두 접두를 기존 조건과 OR 로 추가한다. **T3 이 `static-search-incomplete:` 를, T4 가 `clone-cleanup-failed:` 를 각자 자기 실패 판정과 함께 추가한다.** 종료 4 선행 판정과 예산 소진 3 은 불변 |
| `scripts/verify_candidates.py` `_cleanup_clone_sessions` (`:1723`~`:1745`) | clone 정리 | 시도별 격리, `created` 이고 `keep_clone` 아닐 때만 삭제, 타입·소유권 검사 실패 시 삭제 시도 안 함, `removed` 는 `os.path.lexists` 실측 |
| `scripts/verify_candidates.py` `run_discover` (`:1811`, `finally` `:2010-2013`, 쓰기 `:2108-2109`) | discover 오케스트레이션 | 정리 예외가 밖으로 전파되지 않게 하고 record·manifest run 에 `clone-cleanup-failed:<repository>:<path>:<error-class>` warning 전파 |
| `tests/test_verify_candidates.py` | 표적 회귀 | 신설 6개: `test_code_search_malformed_2xx_is_partial_and_allows_clone_fallback`, `test_403_retry_classification_uses_headers_in_both_transports`, `test_retry_policy_preserves_429_and_5xx_bounds_and_observability`, `test_static_search_distinguishes_exclusions_and_read_failures`, `test_static_search_incomplete_evidence_never_claims_absence_or_ready`, `test_cleanup_failure_preserves_outputs_and_partial_status` (행위 테스트 6개) |
| `tests/test_skill_contract.py` | 고정 계약 | 신설 1개: `test_closed_sets_manifest_schema_and_exit_contract`. 이번 실행의 신설 테스트 총계는 행위 6개 + 계약 1개 = **7개** 이며 기대 총 테스트 수는 55 + 7 = **62** 다. 기존 `test_reference_documents_cover_contract` 에 additive static-search 필드·세 `sha256` 의미·I13 follow-up 문구 단정 추가 |
| `tests/fixtures/**` | 오프라인 입력 | **신설 fixture 파일을 예상하지 않는다.** malformed code-search payload 와 403 header matrix 는 fixture transport 의 응답 map 에 테스트 안에서 주입하고(기존 헬퍼 `write_fixture`·`fixture_response` 재사용), 정적 검색의 symlink·oversize·binary·읽기 실패 사례는 `tempfile.TemporaryDirectory()` 안의 로컬 repository 를 테스트 시점에 만들어(기존 헬퍼 `make_local_repo` 확장) 구성하고, cleanup 실패는 `mock.patch` 로 `shutil.rmtree` 예외를 주입한다. 구현 중 새 fixture 파일이 꼭 필요해지면 결과의 `changed_files` 에 선언하고 이 허용 경로 안에만 만든다 |
| `references/verification-contract.md` | 배포 계약 | additive static-search 필드와 구버전 missing-`complete` fail-closed 소비, `#80`~`#82` 영향, 세 `sha256` 의미, I13 follow-up 절 |
| `references/github-verification-contract.md` | GitHub 계약 | 403 분류 규칙과 재시도 경계 |
| `docs/development/2026-09-09-79-prereview-followup-retry-cleanup-static-search/report.md` | 실행 보고 | 결과·편차·잔여 한계. 오케스트레이터가 쓴다 |

## Task dependencies

**확정 실행 순서는 T1 → T2 → T3 → T4 → T5 → T6 이다.** 태스크 번호는 Spec 요구사항 대응 식별자이고 실행 순서는 이 문단이 정한다. 각 태스크의 통과 확인은 그 태스크가 끝나는 시점에 달성 가능해야 하며, 선행이 없어 달성 불가한 단정을 약화하지 않는다.

- **T1 과 T2 는 서로 독립** 이다. T1 은 code search 소비 경계만, T2 는 transport 재시도 경계만 만진다. T1 을 먼저 두어 `available: false` 가 기존 `combination_partial` 의 이미 존재하는 OR 항으로 종료 3 을 내는 것을 확인한 뒤 새 접두 조건을 다루게 한다.
- **T3 와 T4 는 같은 `combination_partial` 술어를 확장하지만 서로 독립이다.** T3 의 통과 확인(`CMD-4`)은 `static-search-incomplete:` 접두만 필요하고 T4 의 통과 확인(`CMD-3`)은 `clone-cleanup-failed:` 접두만 필요하다. 따라서 **각 태스크가 자기 접두만 추가하고 자기 실패 판정으로 그 분기를 즉시 검증한다.** T3 이 두 접두를 한꺼번에 넣으면 T3 안에 실패 판정이 없는 분기가 생겨 이 Plan 의 테스트 우선 규칙과 어긋나므로 그렇게 하지 않는다. 두 접두가 기존 조건과 OR 로 붙으므로 어느 순서로 추가해도 종료 4 선행 판정과 예산 소진 종료 3 을 바꾸지 않고, 두 조건이 동시에 참이어도 결과는 한 번의 종료 3 으로 수렴한다. 확정 순서에서 T3 을 T4 앞에 두는 것은 정적 검색 계약 확장이 더 넓은 표면을 만지므로 먼저 안정화하려는 선택이며 기술적 강제는 아니다.
- **T5 는 T1·T2·T3·T4 뒤** 다. 신설 계약 테스트가 두 새 warning 의 종료 3 우선순위와 additive static-search 필드를 단정해야 하므로 그 동작이 확정된 뒤여야 한다. 계약 문서도 확정된 동작을 서술한다.
- **T6 은 마지막** 이다. 전체 스위트·형제 스위트·보존 무결성 회귀를 함께 실행한다.
- 생산 인터페이스: T1 이 code-search 형태 게이트, T2 가 공용 재시도 분류 결과, T3 이 additive static-search 필드와 `static-search-incomplete:` 접두 조건, T4 가 격리된 정리와 cleanup warning 및 `clone-cleanup-failed:` 접두 조건을 제공한다. 소비 인터페이스: T5 가 T1~T4 의 동작 전부를 쓴다. T4 는 T3 의 산출물을 소비하지 않는다.
- 병렬 작업은 하지 않는다. 단일 Codex 구현 라운드가 확정 순서로 순차 진행한다.

## Tasks

### T1. code search 2xx 형태 게이트

대상 AC: AC-1 판정 `CMD-1` `test_code_search_malformed_2xx_is_partial_and_allows_clone_fallback`, AC-2 판정 `CMD-1` `test_code_search_malformed_2xx_is_partial_and_allows_clone_fallback`, AC-3 판정 `[문서]` `spec.md` Interfaces and data flow — Code search 경계.

1. 실패 확인: `tests/test_verify_candidates.py` 에 `test_code_search_malformed_2xx_is_partial_and_allows_clone_fallback` 을 추가한다. non-object, bool `total_count`, non-bool `incomplete_results`, non-array `items` 인 2xx code-search fixture 각각이 `code_search.available: false`, 해당 query 의 `total_count: null`, `invalid-search-payload` 경고가 되는지 단정한다. 유효한 빈 2xx 대조군이 `available: true` 를 유지하는지 단정한다. CLI 통합으로 malformed 입력이 종료 3·`status: partial` 이고 clone 허용 시 임시 로컬 git repository clone 과 static search 를 실제 시도하는지, 유효한 빈 2xx 대조군은 종료 0 이고 clone 을 시도하지 않는지 단정한다. `CMD-1` 실행 → 실패(현재는 HTTP 상태만 보고 `available: true` 를 유지하며 경고도 없다).
2. 최소 구현: `discover_code_search` 가 2xx 여도 `_valid_search_payload` 와 동등한 필수 형태(bool 아닌 정수 `total_count`, bool `incomplete_results`, 배열 `items`)를 검사한다. 실패면 빈 성공으로 합성하지 않고 `available` 을 `false` 로 만들며 해당 request path 의 `invalid-search-payload` 경고를 남긴다. 유효한 item 만 기존 `path`·`html_url`·`clue` hit 로 정규화한다. `run_discover` 한 경로에만 적용하고 recheck 요청 수·동작을 바꾸지 않는다.
3. 통과 확인: `CMD-1` 실행 → 종료 0, 해당 테스트 `ok`. 기존 `test_duplicate_search_four_combinations_and_completeness` 와 `test_static_search_reads_only` 가 회귀하지 않음을 함께 확인한다.

### T2. 403 재시도 분류

대상 AC: AC-4 판정 `CMD-2` `test_403_retry_classification_uses_headers_in_both_transports`, AC-5 판정 `CMD-2` `test_retry_policy_preserves_429_and_5xx_bounds_and_observability`, AC-6 판정 `CMD-2` `test_retry_policy_preserves_429_and_5xx_bounds_and_observability`.

1. 실패 확인: 두 테스트를 추가한다. 첫째는 두 transport 각각에서 403 + 숫자 `Retry-After`, 403 + `X-RateLimit-Remaining: 0` 과 숫자 `X-RateLimit-Reset` 이 retry 되고, 헤더 없음·malformed·`Remaining` 비0·NaN·무한대·음수 사례는 요청 한 번 뒤 permission-denied 로 반환되는지 단정한다. 둘째는 두 transport 에서 429 와 503 이 최초 요청 포함 최대 4회, 기본 대기 60·120·240초, 예산 4를 유지하고 각 지연이 300초를 넘지 않는지, rate-limit 403 한도 소진이 `failed`/`transport-or-5xx` 이고 모호한 403 이 `forbidden`/`http-403` 인지, `request_events` 에 `retry_decision`(`retry` 또는 `return`)과 `retry_reason` 이 남고 최종 warning 이 기존 접두에 분류 이유를 덧붙이며 허용되지 않은 header 나 secret 을 보존하지 않는지 단정한다. **`retry_reason` 은 네 값을 이름으로 각각 단정한다.** 숫자 `Retry-After` 재시도는 `retry-after`, `Remaining=0` + 숫자 `Reset` 재시도는 `remaining-zero-and-reset`, 모호한 403 의 즉시 반환은 `ambiguous-403`, 명시적 rate-limit 403 이 한도까지 소진된 마지막 event 는 `retry-limit-reached` 다. `CMD-2` 실행 → 실패(현재 `_retryable` 은 상태 코드만 보고 모든 403 을 재시도한다).
2. 최소 구현: `_retryable` 의 서명을 status 와 sanitized headers 를 받도록 바꾸고 판정과 이유를 함께 돌려준다. 429 와 500–599 는 기존대로 재시도한다. 403 은 (a) `Retry-After` 가 유한한 0 이상 숫자로 해석되거나 (b) `X-RateLimit-Remaining` 이 정확히 정수 0 이고 `X-RateLimit-Reset` 이 유한한 0 이상 숫자로 해석될 때만 `rate-limit` 으로 재시도한다. 그 밖은 `permission-denied` 이며 재시도하지 않는다. **`retry_reason` 은 R2.3 이 정한 최소 네 값을 구분해 발급한다.** (a) 경로는 `retry-after`, (b) 경로는 `remaining-zero-and-reset`, 재시도하지 않는 모호한 403 은 `ambiguous-403`, 명시적 rate-limit 403 이 `MAX_RETRIES` 까지 소진돼 반환되는 마지막 event 는 `retry-limit-reached` 다. 네 값은 429·5xx 의 기존 reason 과 충돌하지 않는 폐쇄 집합으로 둔다. 두 transport 가 같은 판정·지연 함수를 쓰게 하고 분류 결과를 `request_events`·warning·접근 실패 매핑에서 재사용한다. `MAX_RETRIES`·`MAX_RETRY_DELAY_SECONDS`·`RequestBudget` 을 바꾸지 않는다.
3. 통과 확인: `CMD-2` 실행 → 종료 0, 두 테스트 `ok`. 기존 `test_budget_and_retry_behaviour` 와 `test_only_gh_get_and_git_readonly_subprocesses` 가 회귀하지 않음을 확인한다.

### T3. 정적 검색 additive 계약과 partial 술어 확장

대상 AC: AC-10 판정 `CMD-4` `test_static_search_distinguishes_exclusions_and_read_failures`, AC-11 판정 `CMD-4` `test_static_search_distinguishes_exclusions_and_read_failures`, AC-12 판정 `CMD-4` `test_static_search_incomplete_evidence_never_claims_absence_or_ready`.

1. 실패 확인: 두 테스트를 추가한다. 첫째는 symlink·oversize·binary 만 있는 정적 검색이 `available: true`, `complete: true`, 정확한 `exclusions`, 빈 `read_failures`, 기존 합계의 `skipped_files`, 실패 warning 없음이 되는지, 그리고 stat·read·walk 실패를 각각 주입하면 `available: true`, `complete: false`, 상대 path 와 `operation` 을 가진 ordered `read_failures`, 규칙에 맞는 `skipped_files`, `static-search-incomplete:<count>` warning 이 나오고 exception 원문이 산출물에 없는지 단정한다. 읽기 실패를 포함한 CLI 대조군이 discovery `status: partial`, 새 manifest run `status: partial`, 종료 코드 3 인지, clone 미요청·실패 기본 객체가 `available: false`·`complete: false` 인지 단정한다. 둘째는 불완전 검색의 positive hit 가 기존 `evidence_status` 에 반영되지만 불완전 zero-hit 가 exhaustive absence 나 새 ready 근거가 되지 않고 candidate 29필드·readiness 12키·`evidence_status` 값 집합이 그대로인지 단정한다. `CMD-4` 실행 → 실패(현재 `static_search` 는 항상 `available: true`·`error: None` 이고 네 원인을 `skipped_files` 하나로 합친다).
2. 최소 구현: `static_search` 에 `complete`·`exclusions`·`read_failures` 를 추가하고 기존 여섯 필드의 이름·의미를 바꾸지 않는다. `exclusions` 는 정확히 `symlink`·`oversize`·`binary` 의 비음수 개수, `read_failures` 는 안전한 clone 상대 `path` 와 `operation`(`walk`·`stat`·`read`)만 가진 ordered array 이며 exception 원문을 저장하지 않는다. `os.walk(onerror=...)` 로 순회 실패를 포착해 `read_failures` 에만 기록하고 미지의 파일 수를 허위 계수하지 않는다. `skipped_files` 는 의도적 제외 세 계수와 파일 단위 `stat`/`read` 실패 수의 합으로 유지한다. **`read_failures` 가 비어 있지 않으면** record 와 manifest 에 `static-search-incomplete:<len(read_failures)>` warning 을 남긴다(전역 제약의 `SPEC-005` 반영). `_static_record` 의 clone 미요청·실패 기본 객체에 `available: false`·`complete: false` 와 빈 additive 필드를 넣는다. **`discover_exit_code` 의 `combination_partial` record warning 검사에 `static-search-incomplete:` 접두만 기존 조건과 OR 로 추가한다.** `clone-cleanup-failed:` 접두는 T4 가 자기 실패 판정과 함께 추가하므로 이 태스크에서 넣지 않는다. 종료 4 선행 판정과 예산 소진 종료 3 을 바꾸지 않는다.
3. 통과 확인: `CMD-4` 실행 → 종료 0, 두 테스트 `ok`. 기존 `test_shallow_clone_flags_and_head_mismatch_warning`·`test_static_search_reads_only`·`test_script_never_executes_cloned_code`·`test_exit_code_matrix` 가 회귀하지 않음을 확인한다.

### T4. clone 정리 격리

대상 AC: AC-7 판정 `CMD-3` `test_cleanup_failure_preserves_outputs_and_partial_status`, AC-8 판정 `CMD-3` `test_clone_cleanup_exact_path_only`, AC-9 판정 `CMD-3` `test_cleanup_failure_preserves_outputs_and_partial_status`.

1. 실패 확인: `test_cleanup_failure_preserves_outputs_and_partial_status` 를 추가한다. 현재 실행이 만든 clone 의 `rmtree` 를 주입 예외로 실패시켜도 discovery 와 manifest 가 기록되고, record 와 manifest run 에 `clone-cleanup-failed:<repository>:<path>:<error-class>` warning 이 있으며 clone entry 가 `removed: false` 이고 discovery `status: partial`·새 manifest run `status: partial`·CLI 종료 코드 3 인지 단정한다. 삭제가 실제 완료된 뒤 예외가 보고되는 주입 사례는 `removed: true` 와 cleanup warning 을 함께 남겨 어느 한쪽도 숨기지 않는지 단정한다. 모든 clone entry 가 기존 다섯 필드만 갖는지 단정한다. 기존 `test_clone_cleanup_exact_path_only` 를 확장해 pre-existing sibling path 와 clone root 가 정리 실패 전후 byte-identical 하고 삭제 호출 대상이 `created: true` session path 뿐이며 `--keep-clone` 대조군이 삭제 호출·실패 warning 없이 `removed: false` 를 유지하는지 단정한다. `CMD-3` 실행 → 실패(현재 `finally` 의 무보호 정리가 예외를 밖으로 전파해 산출물이 기록되지 않는다).
2. 최소 구현: `_cleanup_clone_sessions` 의 각 정리 시도를 서로 격리하고 예외가 `run_discover` 밖으로 전파되지 않게 한다. `created` 이고 `keep_clone` 이 아닐 때만 삭제하고, 타입·소유권 검사가 실패하면 삭제를 시도하지 않는다. clone root 자체와 기존 경로·다른 실행 경로는 삭제하지 않는다. `removed` 는 예외 유무가 아니라 `os.path.lexists(path)` 실측으로 계산한다. 예외가 나면 repository·path·안전한 오류 분류를 담은 warning 을 그 session 을 사용한 모든 record 와 manifest run 에 남긴다. manifest `clones` 의 다섯 필드를 추가·삭제 없이 유지한다. **`discover_exit_code` 의 `combination_partial` record warning 검사에 `clone-cleanup-failed:` 접두를 기존 조건과 OR 로 추가한다.** T3 이 넣은 `static-search-incomplete:` 조건은 건드리지 않고, 종료 4 선행 판정과 예산 소진 종료 3 도 바꾸지 않는다.
3. 통과 확인: `CMD-3` 실행 → 종료 0, 두 테스트 `ok`. 이 실행이 이 태스크가 추가한 `clone-cleanup-failed:` 분기를 처음으로 검증한다. 이어 `CMD-4` 를 재실행해 T3 이 넣은 `static-search-incomplete:` 조건이 회귀하지 않음을 확인한다.

### T5. 계약 문서와 계약 테스트

대상 AC: AC-13 판정 `CMD-5` `test_reference_documents_cover_contract`, AC-14 판정 `CMD-5` `test_reference_documents_cover_contract`, AC-15 판정 `[문서]` `spec.md` Non-goals 2 및 Decisions D5, AC-16 판정 `CMD-5` `test_closed_sets_manifest_schema_and_exit_contract`.

1. 실패 확인: `tests/test_skill_contract.py` 에 `test_closed_sets_manifest_schema_and_exit_contract` 를 추가한다. Non-goals 11 의 각 폐쇄 집합과 크기, 코드와 산출물의 동일한 `schema_version`, 종료 코드 0/1/2/3/4 와 종료 4 선행·예산 소진 3·두 새 warning 의 3 우선순위, clone entry 의 정확한 다섯 필드, 허용 header 일곱 개를 직접 단정한다.

   기존 `test_reference_documents_cover_contract` 에 additive static-search 필드 설명, 구버전 missing-`complete` 의 fail-closed 소비, `#80`~`#82` 영향, I13 follow-up 문구 단정을 더한다.

   **세 `sha256` 의미는 문구 단정만으로 끝내지 않고 실제 코드 계산과 대조한다.** R5.1·AC-14 가 요구하는 것은 문서와 코드의 일치이므로 계약 테스트가 각 의미마다 값을 스스로 계산해 산출물 필드와 같은지 단정한다. ① 일반 `_untrusted_text`: 저장된 `text` 를 UTF-8 로 인코딩해 `hashlib.sha256` 으로 해시한 값이 그 객체의 `sha256` 과 같다. ② 정책 file excerpt: fixture 의 base64 `content` 를 디코드한 **잘리기 전 원본 bytes** 의 해시가 excerpt 의 `sha256` 과 같고 그 policy result 의 `sha256` 과도 같다(발췌가 잘린 경우에도 `text` 해시와는 다름을 함께 단정해 두 의미가 구분됨을 보인다). ③ 정책 directory excerpt: 문자열 `name` 을 가진 항목만 정렬한 canonical JSON bytes(`json.dumps(names, sort_keys=True, separators=(",", ":")).encode("utf-8")`)의 해시가 excerpt 의 `sha256` 과 같고 그 policy result 의 `sha256` 과도 같다. 세 계산은 기존 fixture(`tests/fixtures/positive/responses.json` 의 정책 응답과 디렉터리 응답)로 수행하며 필드명·스키마·계산 코드를 바꾸지 않는다.

   `CMD-5` 실행 → 실패(신설 테스트 미존재로 `AttributeError`, 기존 테스트는 새 문구·새 해시 대조 부재로 실패).
2. 최소 구현: `references/verification-contract.md` 에 (a) additive static-search 필드와 `available`/`complete` 의미 구분, 구버전 산출물에 `complete` 가 없으면 새 소비자가 `true` 로 추정하지 않는다는 fail-closed 규칙, `#80`~`#82` 가 zero-hit 부재 판단 시 두 필드를 함께 확인해야 한다는 서술, (b) 일반 `_untrusted_text` 의 `sha256` 은 저장된 `text` 의 UTF-8 바이트 해시, 정책 file excerpt 의 같은 필드는 잘리기 전 decoded 원본 content bytes 해시, 정책 directory excerpt 는 유효 이름을 정렬한 canonical JSON bytes 해시이며 두 경우 모두 해당 policy result 의 `sha256` 과 같다는 세 의미 구분, (c) I13 follow-up 절(현재 `clone_repository` 가 git stderr 를 보존하지 않고 `_static_record` 가 `clone-failed` 로 축약해 진단이 제한된다는 사실, 향후 redaction·길이 제한·단계 분류를 함께 설계해야 한다는 방향, 이번 미구현과 Issue 미생성)을 넣는다. `references/github-verification-contract.md` 에 403 분류 규칙과 재시도 경계를 넣는다. **필드명·스키마·계산 코드는 바꾸지 않는다.** 두 references 문서의 400줄 미만과 `SKILL.md` 200줄 미만을 유지한다.
3. 통과 확인: `CMD-5` 실행 → 종료 0, 다섯 테스트 `ok`.

### T6. 전체 회귀와 범위 무결성

대상 AC: AC-17 판정 `CMD-6` `test_verify_candidates` `test_skill_contract`, AC-18 판정 `CMD-7` `test_validate_corpus`, AC-19 판정 `CMD-8` `test_collect_recent_closed_prs`, AC-20 판정 `[문서]` `spec.md` Security and risk — 범위 무결성 판정.

1. 실패 확인: 이 태스크는 종합 회귀다. T1~T5 완료 전에 실행하면 신설 테스트가 실패하는 것으로 선행 판정이 성립한다.
2. 최소 구현: 코드 변경 없음. T1~T5 의 결과만 모은다.
3. 통과 확인: `CMD-6` 실행 → 종료 0, `OK`, **`Ran 62 tests`** (기존 55 + 신설 7. 행위 6 + 계약 1). 하한이 아니라 정확값으로 단정한다. `CMD-7` → `Ran 30 tests` `OK`. `CMD-8` → `Ran 108 tests` `OK`. `CMD-9` 로 보존 대상 22개 파일의 byte 동일성을, `CMD-10` 으로 스킬 디렉터리의 실제 변경 경로가 승인 범위에만 있음을 확인한다. 네트워크 runner 호출이 없음을 `CMD-6` 출력으로 확인한다.

## Verification commands

실행 순서는 표적 판정(`CMD-1`~`CMD-5`) → 전체 스위트(`CMD-6`) → 형제 회귀(`CMD-7`, `CMD-8`) → 보존 무결성(`CMD-9`) → 변경 범위(`CMD-10`) 이다. 이 스킬에는 lint, type-check, build 도구가 구성되어 있지 않으므로 그 범주는 미구성으로 기록하고 통과로 적지 않는다. 라이브 명령, 대상 저장소 명령, 의존성 설치 명령은 판정 수단에 포함하지 않는다.

| ID | 명령 | 기대 결과 |
|---|---|---|
| CMD-1 | `cd "$SK" && PYTHONDONTWRITEBYTECODE=1 "$PY" -m unittest tests.test_verify_candidates.VerifyCandidatesTests.test_code_search_malformed_2xx_is_partial_and_allows_clone_fallback -v` | 종료 0, `ok` |
| CMD-2 | `cd "$SK" && PYTHONDONTWRITEBYTECODE=1 "$PY" -m unittest tests.test_verify_candidates.VerifyCandidatesTests.test_403_retry_classification_uses_headers_in_both_transports tests.test_verify_candidates.VerifyCandidatesTests.test_retry_policy_preserves_429_and_5xx_bounds_and_observability -v` | 종료 0, 두 테스트 `ok`. `retry_reason` 네 값 `retry-after`·`remaining-zero-and-reset`·`ambiguous-403`·`retry-limit-reached` 가 각각 이름으로 단정됨 |
| CMD-3 | `cd "$SK" && PYTHONDONTWRITEBYTECODE=1 "$PY" -m unittest tests.test_verify_candidates.VerifyCandidatesTests.test_cleanup_failure_preserves_outputs_and_partial_status tests.test_verify_candidates.VerifyCandidatesTests.test_clone_cleanup_exact_path_only -v` | 종료 0, 두 테스트 `ok` |
| CMD-4 | `cd "$SK" && PYTHONDONTWRITEBYTECODE=1 "$PY" -m unittest tests.test_verify_candidates.VerifyCandidatesTests.test_static_search_distinguishes_exclusions_and_read_failures tests.test_verify_candidates.VerifyCandidatesTests.test_static_search_incomplete_evidence_never_claims_absence_or_ready -v` | 종료 0, 두 테스트 `ok` |
| CMD-5 | `cd "$SK" && PYTHONDONTWRITEBYTECODE=1 "$PY" -m unittest tests.test_skill_contract.SkillContractTests.test_reference_documents_cover_contract tests.test_skill_contract.SkillContractTests.test_skill_layout_and_frontmatter tests.test_skill_contract.SkillContractTests.test_no_hardcoded_targets_dates_models tests.test_skill_contract.SkillContractTests.test_closed_sets_manifest_schema_and_exit_contract tests.test_verify_candidates.VerifyCandidatesTests.test_print_revision_matches_recomputation -v` | 종료 0, 다섯 테스트 `ok` |
| CMD-6 | `PYTHONDONTWRITEBYTECODE=1 "$PY" -m unittest discover -s "$SK/tests" -t "$SK/tests" -p 'test_*.py'` | 종료 0, `OK`, 정확히 `Ran 62 tests` (기존 55 + 신설 7); 네트워크 runner 호출 없음 |
| CMD-7 | `PYTHONDONTWRITEBYTECODE=1 "$PY" -m unittest discover -s "$RT/dot_codex/skills/analyzing-open-source-pr-patterns/tests" -t "$RT/dot_codex/skills/analyzing-open-source-pr-patterns/tests" -p 'test_*.py'` | 종료 0, `Ran 30 tests`, `OK` |
| CMD-8 | `PYTHONDONTWRITEBYTECODE=1 "$PY" -m unittest discover -s "$RT/dot_codex/skills/collecting-recent-closed-prs/tests" -t "$RT/dot_codex/skills/collecting-recent-closed-prs/tests" -p 'test_*.py'` | 종료 0, `Ran 108 tests`, `OK` |
| CMD-9 | `cd "$RT" && shasum -a 256 -c "$QS/preserved-baseline.sha256"` | 22개 항목 전부 `OK`. 루트 `AGENTS.md` 와 1·2·3차 실행 문서가 baseline 과 byte-identical |
| CMD-10 | `cd "$RT" && diff -ru "$QS/pre-impl-snapshot/skill" dot_codex/skills/verifying-open-source-contribution-candidates \| head -400` | 변경 파일이 승인된 허용 경로에만 있고 형제 스킬·전역 설치본에 변경이 없음. 이 diff 를 코드 리뷰 컨텍스트의 unified diff 근거로 쓴다 |

## Rollout and rollback

배포는 이번 범위가 아니다. 산출물은 워크트리의 미커밋 변경으로만 남고 `chezmoi apply`·배포·전역 설치본 갱신은 하지 않는다. rollout 단계는 "리뷰 통과 후 사용자에게 PR 준비와 제한된 라이브 검증 승인 판단을 넘긴다" 까지다.

관측 신호는 `discovery.json` 의 세 구획·`status`·`code_search.available`·`static_search` 의 `complete`·`exclusions`·`read_failures`, manifest 의 `retry_events`·`clones`·`warnings`·`status`·`outcome`, 그리고 종료 코드다.

rollback 트리거는 다음 중 하나다. `CMD-6` 가 `OK` 가 아님, `CMD-7`·`CMD-8` 의 형제 스위트 회귀, `CMD-9` 보존 무결성 실패, `CMD-10` 에서 승인 범위 밖 경로 변경 발견, 정상 단서·정상 응답의 요청 수·순서 변화, 예산 소진이 종료 4 로 바뀜, 모호한 403 이 재시도됨, 권한 거부 403 이 `failed` 로 기록됨, clone 정리가 `created` 아닌 경로를 삭제함, `removed: true` 가 실측과 어긋남.

rollback 절차는 이번 실행이 만든 코드·테스트·fixture·계약 문서 변경만 되돌리는 것이다. `CMD-10` 의 diff 로 변경 목록을 확인한 뒤 `$QS/pre-impl-snapshot/skill` 을 기준으로 복원한다. 1·2·3차 실행 문서, 루트 `AGENTS.md`, 형제 스킬, 전역 설치본, `main`, 다른 워크트리는 rollback 대상이 아니며 건드리지 않는다. 되돌린 뒤 `CMD-6`·`CMD-7`·`CMD-8`·`CMD-9` 를 재실행해 기준선 55/30/108 과 22개 `OK` 로 복귀했음을 확인한다.

## Acceptance-criteria traceability

| Criterion | Task | Verification command | Expected outcome |
|---|---|---|---|
| AC-1 | T1 | `CMD-1` `test_code_search_malformed_2xx_is_partial_and_allows_clone_fallback` | 종료 0, 네 malformed 형태가 `available: false`·`total_count: null`·경고, 유효 빈 2xx 는 `available: true` |
| AC-2 | T1 | `CMD-1` `test_code_search_malformed_2xx_is_partial_and_allows_clone_fallback` | 종료 0, malformed 는 종료 3/partial 과 clone·static 시도, 대조군은 종료 0·clone 미시도 |
| AC-3 | T1 | `[문서]` `spec.md` Interfaces and data flow — Code search 경계 | code search 요청·호출 위치가 각각 하나이고 recheck 신설 없음과 duplicate-search 게이트 보존이 명시됨 |
| AC-4 | T2 | `CMD-2` `test_403_retry_classification_uses_headers_in_both_transports` | 종료 0, 두 transport 의 403 header matrix 판정 통과 |
| AC-5 | T2 | `CMD-2` `test_retry_policy_preserves_429_and_5xx_bounds_and_observability` | 종료 0, 429·503 의 4회·60/120/240초·예산 4·300초 상한과 403 소진 매핑 통과 |
| AC-6 | T2 | `CMD-2` `test_retry_policy_preserves_429_and_5xx_bounds_and_observability` | 종료 0, `retry_decision` 과 네 `retry_reason` 값·warning 이유·header/secret 미보존 통과 |
| AC-7 | T4 | `CMD-3` `test_cleanup_failure_preserves_outputs_and_partial_status` | 종료 0, 산출물 보존·cleanup warning·`removed: false`·partial·종료 3 통과 |
| AC-8 | T4 | `CMD-3` `test_clone_cleanup_exact_path_only` | 종료 0, sibling·clone root 불변과 `created: true` 한정 삭제, keep-clone 대조 통과 |
| AC-9 | T4 | `CMD-3` `test_cleanup_failure_preserves_outputs_and_partial_status` | 종료 0, clone entry 다섯 필드 유지와 `removed: true` + warning 동시 기록 통과 |
| AC-10 | T3 | `CMD-4` `test_static_search_distinguishes_exclusions_and_read_failures` | 종료 0, 제외 전용 결과의 `complete: true`·정확한 `exclusions`·warning 없음 통과 |
| AC-11 | T3 | `CMD-4` `test_static_search_distinguishes_exclusions_and_read_failures` | 종료 0, stat·read·walk 주입의 `complete: false`·ordered `read_failures`·warning·partial·종료 3 과 clone 실패 기본 객체 통과 |
| AC-12 | T3 | `CMD-4` `test_static_search_incomplete_evidence_never_claims_absence_or_ready` | 종료 0, positive hit 보존과 불완전 zero-hit 의 부재·ready 근거 불가, 폐쇄 집합 불변 통과 |
| AC-13 | T5 | `CMD-5` `test_reference_documents_cover_contract` | 종료 0, additive 필드·fail-closed 소비·후속 소비자 영향 서술 단정 통과 |
| AC-14 | T5 | `CMD-5` `test_reference_documents_cover_contract` | 종료 0, 세 `sha256` 의미가 테스트가 직접 계산한 값과 각각 일치하고 두 의미의 구분까지 단정되며 필드·스키마 변경 없음 |
| AC-15 | T5 | `[문서]` `spec.md` Non-goals 2 및 Decisions D5 | I13 의 진단 손실·후속 방향·별도 승인·미구현·Issue 미생성이 함께 기록됨 |
| AC-16 | T5 | `CMD-5` `test_closed_sets_manifest_schema_and_exit_contract` | 종료 0, 폐쇄 집합·schema version·종료 집합과 우선순위·clone 다섯 필드·허용 header 일곱 개 단정 통과 |
| AC-17 | T6 | `CMD-6` `test_verify_candidates` `test_skill_contract` | 종료 0, `OK`, 정확히 `Ran 62 tests` |
| AC-18 | T6 | `CMD-7` `test_validate_corpus` | 종료 0, `Ran 30 tests`, `OK` |
| AC-19 | T6 | `CMD-8` `test_collect_recent_closed_prs` | 종료 0, `Ran 108 tests`, `OK` |
| AC-20 | T6 | `[문서]` `spec.md` Security and risk — 범위 무결성 판정 | `CMD-9`·`CMD-10` 의 실제 출력이 baseline 동일성과 승인 범위 내 변경을 증명 |

<!-- strict-only:start -->

### Threat and trust boundaries

구현과 검증이 보존해야 하는 경계 점검은 다섯이다. ① 2xx code-search payload 형태 검증이 형식 불일치를 확인된 빈 결과로 소비하지 않는다(`CMD-1`). ② 403 분류가 원격 자유 텍스트(body message)가 아니라 allowlist 에 이미 포함된 numeric header 만 근거로 삼는다(`CMD-2`). ③ 정적 검색이 exception 원문을 산출물에 저장하지 않고 안전한 clone 상대 path 와 operation 만 남긴다(`CMD-4`). ④ clone 정리가 이 실행이 만든 `created: true` path 만 삭제하고 기존 경로·다른 실행 경로·clone root 를 건드리지 않는다(`CMD-3`). ⑤ 재시도 관측 정보가 허용되지 않은 header 나 secret 을 보존하지 않는다(`CMD-2`). 미신뢰 주체는 GitHub 응답 본문·헤더, clone 된 대상 저장소 파일 내용, fixture payload 다.

### Authorization and tenant isolation

다중 tenant 기능이 없어 tenant isolation 테스트 케이스는 해당 없음이다. 이유는 이 스킬이 단일 사용자의 로컬 CLI 이고 tenant 개념·경계·권한 분기가 코드에 없기 때문이다. 대신 이번 변경의 핵심이 **권한 경계 해석** 이므로 `CMD-2` 가 권한 거부 403 과 rate limit 403 의 분류·재시도·접근 실패 매핑을 판정하고, `CMD-6` 이 네트워크 runner 호출이 없음을 확인한다. GitHub 인증은 기존 `gh` 자격을 read-only GET 에만 쓰며 권한을 확대하지 않는다.

### Migration, compatibility, and rollback

data migration 과 backfill 은 없다. 호환성 점검은 폐쇄 집합·`schema_version`·종료 코드 집합과 우선순위·manifest clone 다섯 필드·허용 header 일곱 개를 유지하는 것이며 `CMD-5` 의 신설 계약 테스트가 이를 직접 단정한다. 유일한 계약 확장은 `static_search` 결과의 additive 세 필드와 retry event/warning 의 additive 정보다. **하위 호환 규칙**: 기존 여섯 필드의 이름·의미를 바꾸지 않고, 구버전 산출물에 `complete` 가 없으면 새 소비자가 `true` 로 추정하지 않으며(fail-closed), `#80`~`#82` 는 zero-hit 부재 판단 시 `available` 과 `complete` 을 함께 확인한다. 이 규칙을 배포 계약 문서에 적고 `CMD-5` 가 단정한다. `compute_revision()` 값 변화는 계약된 동작이며 `CMD-5` 의 재계산 비교로 증명한다. rollback 트리거와 절차는 위 Rollout and rollback 절과 같고, 리뷰 전 필요한 근거는 `CMD-6`·`CMD-7`·`CMD-8`·`CMD-9`·`CMD-10` 의 실제 출력이다.

### Failure recovery and observability

실패 복구 점검은 넷이다. ① malformed 2xx code search 후 `available: false` 를 근거로 clone·static 대체 경로가 열리는가(`CMD-1`). ② 모호한 403 후 예산·대기를 낭비하지 않고 즉시 판정된 접근 실패로 끝나는가(`CMD-2`). ③ clone 정리 실패 후에도 유효한 조사 결과와 잔여 경로가 남아 다음 실행에서 수동 정리·재시도가 가능한가(`CMD-3`). ④ 정적 검색 불완전 후 zero-hit 를 부재로 확정하지 않고 새 승인 실행에서 다시 검증할 수 있는가(`CMD-4`). 필요한 관측 근거는 `code_search.available`, `static_search` 의 `complete`·`exclusions`·`read_failures`, manifest 의 `retry_events`·`clones`·`warnings`·`status`, 그리고 종료 코드이며 각 판정 명령의 단정으로 남긴다.

### High-risk end-to-end verification

고위험 경로 넷을 CLI 경계까지 검증한다. 권한 경계 해석은 `CMD-2`, 파괴적 정리의 범위 한정과 산출물 보존은 `CMD-3`, 계약 확장의 하위 호환은 `CMD-5`, 불완전 근거의 fail-closed 소비는 `CMD-4` 다. cross-regression 은 `CMD-6` 로 확인한다. 요구되는 근거는 각 명령의 종료 코드와 단정 통과 출력이며 모두 보존 fixture·주입 transport·임시 로컬 git repository 로만 실행한다. **새 라이브 검증은 이번 승인 범위 밖이므로 수행하지 않는다.** 따라서 `assessment`·`record`·`recheck` 실경로와 `CAN-*` 실물은 여전히 미검증이며 `discover` 실경로도 2차 실행의 1회 라이브 근거뿐이고 그것을 이번 변경의 검증으로 재사용하지 않는다. 오프라인 검증을 마친 뒤 제한된 라이브 검증의 대상·입력·명령·예산·clone·출력 경로를 제안해 별도 승인을 받는다.

### No production mutation confirmation

자동 워크플로에 production mutation 은 없다. 판정은 fixture 기반 unittest 와 문서 검사, 그리고 임시 디렉터리 안의 로컬 git repository 조작뿐이며 GitHub, 원격 저장소, `main`, 다른 워크트리, 전역 설치본, `$HOME` 설정을 바꾸지 않는다. commit, push, PR 생성, merge, `chezmoi apply`, 배포, Issue·댓글 작성, 라이브 `discover`·`recheck` 는 포함하지 않는다. 유일한 파일 삭제는 이 실행이 `created: true` 로 만든 임시 clone 경로에 대한 것이며 `CMD-3` 가 그 범위 한정을 판정한다.

<!-- strict-only:end -->
