# Quality Goal Specification

- Task ID: 2026-09-09-79-prereview-followup-retry-cleanup-static-search
- Mode: strict
- Status: SPEC_REVIEW
- Created: 2026-09-09
- Updated: 2026-09-09
- Source goal: #79 PR 사전 리뷰 후속 승인 범위인 code search 2xx 형태 검증, 403 재시도 분류, clone 정리 실패 격리, 정적 검색 완전성 표현을 구현하고 sha256 의미와 clone 실패 진단 후속을 문서화한다.

## Problem and context

대상은 `dot_codex/skills/verifying-open-source-contribution-candidates/`의 검증 스킬이다. 직전 세 번째 quality-goal 실행은 사전 리뷰의 Critical 4건과 포함 Important 8건을 수정하고 대상 스킬 55 tests OK로 COMPLETED가 되었다. 그 실행의 `report.md`, `pre-review-summary.md`, `followup-scope.md`는 이번 항목을 의도적으로 보류했다. 오케스트레이터가 현재 코드로 다시 확인한 결과, 이번 승인 범위의 구현 결함 네 건과 계약 문서 공백 두 건은 여전히 존재한다.

`discover_code_search`는 2xx 상태만 성공으로 보고 payload가 object가 아니면 빈 object로 바꾼다. 따라서 잘못된 2xx가 `available: true`, 빈 hits, 경고 없음으로 기록된다. 이 값은 `discover_exit_code`에서 partial 여부를 결정하고 clone 허용식에서 정적 검색 대체 경로를 여는 데 쓰이므로, 현재 동작은 종료 3을 0으로 바꾸고 허용된 clone을 건너뛸 수 있다. 반면 issue/PR 중복 검색은 이미 `_valid_search_payload`로 형태를 검사한다. `/search/code`의 생산자와 호출자는 각각 `discover_code_search`와 `run_discover` 한 곳뿐이며 recheck에는 code search가 없다. recheck의 중복 검색 형태 게이트는 직전 실행에서 이미 수정되었다.

재시도 경계에서는 `_retryable(status)`가 모든 403, 429, 5xx를 같은 방식으로 최대 3회 재시도한다. 권한 거부 403도 총 4회 요청과 420초의 기본 대기를 소비하지만, GitHub는 rate limit에도 403을 사용할 수 있어 403의 일괄 재시도와 일괄 금지 모두 부정확하다. 응답에는 허용된 `Retry-After`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`이 보존되고 지연 계산도 이미 이 값을 이용한다. `GhApiClient.get_json`과 `FixtureTransport.get_json`이 같은 분류를 사용해야 한다.

clone 정리는 `run_discover`의 산출물 쓰기 전에 무보호 `finally`에서 실행된다. `_cleanup_clone_sessions`의 타입 오류나 `shutil.rmtree` 오류가 전파되면 유효한 discovery와 manifest가 모두 유실된다. 정리 대상은 현재 실행이 `created`로 표시한 clone으로 제한되어야 하고 `--keep-clone`의 의미도 유지되어야 한다.

정적 검색은 symlink, 4 MiB 초과, NUL 포함 파일이라는 의도적 제외와 실제 `OSError`를 모두 `skipped_files`에 합치고 항상 `available: true`를 반환한다. clone은 성공했지만 일부 또는 전체를 읽지 못한 경우와 완전한 무-hit 결과를 소비자가 구분할 수 없다. `static_search.hits`는 `evidence_status` 계산에 들어가므로, 최소 additive 계약으로 수행 가능성과 관찰 완전성을 분리해야 한다.

마지막으로 미신뢰 텍스트의 `sha256`은 일반 `_untrusted_text` 결과에서는 저장된 발췌 `text`의 UTF-8 바이트 해시지만, 정책 파일과 정책 디렉터리 발췌에서는 전체 원본 또는 canonical 정책 내용의 해시로 덮어써진다. 코드는 이번 범위에서 바꾸지 않고 실제 의미를 배포 계약에 명시한다. clone 실패가 git stderr를 버리고 `clone-failed`로 합쳐지는 I13도 구현하지 않고 후속 항목으로만 남긴다.

현재 근거 위치는 `scripts/verify_candidates.py:641-642,709-713,782-786`의 재시도, `:1463-1505,1550-1576,1942-1982`의 code search 소비, `:1723-1763,2010-2013,2108-2109`의 cleanup/static/output 순서, `:497-550`의 정적 검색, `:1001-1008,1193-1194,1234-1235`의 hash 계산이다. 배포 계약 근거는 `references/verification-contract.md`와 `references/github-verification-contract.md`, 직전 실행 근거는 `docs/development/2026-09-08-79-pr-prereview-critical-fixes/`의 세 참조 문서다.

## Goals

1. code search의 잘못된 2xx를 사용 불가로 판정하여 partial 종료와 허용된 정적 검색 대체 경로를 복원한다.
2. 명시적 rate-limit 근거가 있는 403만 기존 한도 안에서 재시도하고, 권한 거부 및 모호한 403은 즉시 판정하며 그 이유를 관측 가능하게 한다.
3. clone 정리 실패가 조사 산출물을 없애지 못하게 하면서 잔여 경로, 실패 상태, 삭제 소유권을 정직하게 보존한다.
4. 정적 검색의 `available`과 `complete`을 분리하고 의도적 제외와 읽기 실패를 additive 계약으로 구분한다.
5. 현재 코드의 `sha256` 두 의미와 미구현 clone 진단 후속을 문서화하고 기존 폐쇄 집합 및 직전 실행의 안전 동작을 회귀시키지 않는다.

## Non-goals

1. I9의 필드 이름, 스키마, 해시 계산 또는 덮어쓰기 코드 변경. 이번 범위는 각 위치의 실제 `sha256` 의미를 문서화하는 것뿐이며 단일 의미로의 개편은 별도 후속이다.
2. I13의 `CloneError`, git stderr 캡처, clone 실패 세분화 또는 새 진단 필드 구현. GitHub Issue를 만들지 않고 배포 계약의 후속 항목으로만 기록한다.
3. recheck에 새 code search 요청 또는 새 정적 검색 경로 추가. recheck는 code search를 하지 않으며 기존 `_recheck_duplicate_search`의 형태 게이트를 유지한다.
4. 사전 리뷰 보류 항목 중 이번 승인에 없는 항목과 직전 실행의 Low advisory `CODE-001`인 분할 불변식 구획 내부 중복 분기 미커버 수정.
5. 새 서브커맨드, 새 후보 상태·상태 이유·failed-scope 이유·접근 실패 outcome·candidate 필드·readiness 키·policy-check 키, `schema_version` 변경 또는 새 의존성. R4.1의 정적 검색 결과에 대한 최소 additive 필드만 예외다.
6. 종료 코드 숫자 집합 0/1/2/3/4 또는 우선순위 변경. R3.2와 R4.2의 두 warning prefix를 `combination_partial`에 추가하는 것은 기존 partial 술어의 additive 확장일 뿐이다. 모든 저장소가 실제로 시도된 접근 실패이면 다른 partial 조건보다 먼저 4이고, 그 외 예산 소진은 항상 3인 기존 우선순위를 유지한다.
7. `#80`~`#82` 구현과 공용 배포 검증. 이번 정적 검색 계약이 후속 소비자에 주는 영향만 문서화하며 공용 배포 검증은 `#82`에 남긴다.
8. 추가 GitHub 요청, 라이브 `discover`·`recheck`, 대상 저장소 코드 실행, 의존성 설치. 판정은 오프라인 fixture, 주입 transport, 임시 로컬 git 저장소만 사용한다.
9. commit, push, PR 생성, merge, `chezmoi apply`, 배포, GitHub Issue·댓글 작성, `main`·다른 워크트리·전역 설치본 수정.
10. Python 표준 라이브러리 밖의 패키지 도입 또는 `MAX_RETRIES = 3`, `MAX_RETRY_DELAY_SECONDS = 300.0`, `RequestBudget` 한도 상향.
11. `CANDIDATE_FIELDS` 29개, `RECHECK_MUTABLE_FIELDS` 9개와 여집합 default-deny, `STATUS_REASON_TABLE`, `READINESS_KEYS` 12개, `POLICY_CHECK_KEYS` 8개, `FAILED_SCOPE_REASONS` 5개, `ACCESS_FAILURE_OUTCOMES` 4개, `SNAPSHOT_EVIDENCE_FIELDS` 8개, `INHERITED_EVIDENCE_FIELDS` 4개, `COMMUNITY_PROFILE_KEYS` 6개, `ALLOWED_RESPONSE_HEADERS` 7개의 확장·축소.
12. 1·2·3차 실행 문서, 워크트리 루트 `AGENTS.md`, 형제 스킬, 배포된 전역 설치본의 수정. 이들은 불변 보존 대상이다.

## Requirements

### R1. Code search 응답 경계

- **R1.1** `discover_code_search`는 각 2xx `/search/code` 응답을 `_valid_search_payload`와 동등한 필수 형태, 즉 bool이 아닌 정수 `total_count`, bool `incomplete_results`, 배열 `items`를 가진 object인지 검사해야 한다. 형식이 틀리면 빈 성공으로 합성하지 않고 전체 `code_search.available`을 `false`로 만들며 해당 request path의 `invalid-search-payload` 경고를 남긴다. 유효한 item만 기존 `path`, `html_url`, `clue` hit로 정규화하고, 유효한 빈 2xx는 계속 `available: true`인 무-hit 결과다.
- **R1.2** 잘못된 2xx로 `available: false`가 되면 기존 `discover_exit_code` 규칙에 따라 usable partial인 종료 코드 3이 되고, `--allow-clone`과 기존 archived/disabled 조건을 만족하면 `not code_search.available` 분기로 clone 및 정적 검색을 시도해야 한다. 유효한 빈 2xx는 종료 0과 clone 미시도를 유지한다. 이 변경은 `run_discover` 한 경로에만 적용하고 recheck 요청 수와 동작을 바꾸지 않으며, 이미 형태 게이트가 있는 discovery/recheck 중복 검색을 회귀시키지 않는다.

### R2. 403 재시도 분류

- **R2.1** `_retryable`의 서명은 최소한 status와 sanitized response headers를 받도록 바뀌고 다음 폐쇄 정책을 사용해야 한다. 429와 500–599는 기존처럼 재시도 가능하다. 403은 (a) `Retry-After`가 유한한 0 이상의 숫자로 해석되거나, (b) `X-RateLimit-Remaining`이 정확히 정수 0이고 `X-RateLimit-Reset`이 유한한 0 이상의 숫자로 해석될 때만 `rate-limit`으로 재시도한다. `X-RateLimit-Limit` 단독, reset 단독, remaining이 0이 아닌 경우, 헤더 부재·음수·NaN·무한대·해석 불가 값은 rate-limit 근거가 아니다. 모호한 403은 `permission-denied/ambiguous-403`으로 분류하고 재시도하지 않으며 기존 `forbidden`/`http-403`/`repository-forbidden` 접근 실패에 매핑한다. 이 fail-closed 선택은 헤더 없는 secondary rate limit의 일시 회복을 놓칠 수 있지만, 확인되지 않은 403마다 예산 4회와 장시간 대기를 쓰지 않고 기존 권한 거부 계약을 보존하는 쪽을 우선한다.
- **R2.2** `GhApiClient.get_json`과 `FixtureTransport.get_json`은 R2.1의 같은 판정 함수와 같은 지연 함수를 사용해야 한다. 허용된 retry는 최초 요청을 포함한 기존 최대 4회, 기존 `RequestBudget`, 최대 단일 지연 300초 안에 포함한다. 숫자로 해석 가능한 `Retry-After` 다음 `X-RateLimit-Reset` 다음 60·120·240초 지수 backoff의 지연 우선순위, 429와 5xx의 기존 동작은 유지한다. 명시적 rate-limit 403이 재시도 한도까지 소진되면 권한 거부로 가장하지 않고 기존 `failed`/`transport-or-5xx`/`repository-failed` 접근 실패로 귀결한다.
- **R2.3** 모든 response `request_events`에는 비밀이나 비허용 헤더를 추가하지 않고 `retry_decision`(`retry` 또는 `return`)과 안정된 `retry_reason`을 기록해야 한다. 403의 reason은 최소 `retry-after`, `remaining-zero-and-reset`, `ambiguous-403`, `retry-limit-reached`를 구분한다. 최종 403 warning은 기존 `request-failed:<path>:http-403` prefix를 유지하면서 `rate-limit:<reason>` 또는 `permission-denied:<reason>`을 덧붙여 판정 근거를 식별 가능하게 한다. 성공으로 회복된 retry는 manifest의 `retry_events`로 관측되고 실패 warning을 만들지 않는다.

### R3. Clone 정리 격리

- **R3.1** 정리 함수는 현재 실행에서 `session.created is true`인 clone path만 삭제할 수 있다. 기존 경로, 다른 실행의 경로, clone root 자체는 삭제하지 않으며 타입 또는 소유권 검사가 실패하면 삭제를 시도하지 않는다. `--keep-clone`이면 현재 실행이 만든 path도 삭제하지 않고 기존처럼 `removed: false`를 기록하며 정리 실패 warning을 만들지 않는다.
- **R3.2** 각 정리 시도는 서로 격리되고 예외가 `run_discover` 밖으로 전파되어 discovery 또는 manifest 쓰기를 막아서는 안 된다. 시도 후 `removed`는 예외 유무가 아니라 `os.path.lexists(path)`의 실제 결과로 계산한다. 예외가 발생하면 repository, path, 안전한 오류 분류를 포함한 `clone-cleanup-failed:<repository>:<path>:<error-class>` warning을 그 session을 사용한 모든 record와 manifest run에 남기고, 잔여 path가 있으면 `removed: false`로 남긴다. 정확한 상태 메커니즘은 `combination_partial`의 record warning 검사에 `isinstance(warning, str) and warning.startswith("clone-cleanup-failed:")`를 기존 조건과 OR로 추가하는 것이다. 따라서 유효한 조사 결과를 보존한 discovery의 `status`와 새 manifest run의 `status`는 모두 `partial`, `run_discover` 종료 코드는 3이다. 이 조건은 종료 4 선행 판정과 예산 소진 종료 3을 바꾸지 않는다. manifest `clones`의 기존 다섯 필드 `repository`, `path`, `sha`, `removed`, `size_bytes`는 추가·삭제 없이 유지한다.

### R4. 정적 검색 완전성 계약

- **R4.1** 기존 `static_search` 필드 `available`, `hits`, `execution_surfaces`, `skipped_files`, `clone_sha`, `error`를 제거하거나 의미를 바꾸지 않고 `complete`, `exclusions`, `read_failures`만 추가한다. `available`은 clone 성공 후 정적 검색 루틴을 수행할 수 있었는지이고 clone 미요청·실패에는 false다. `complete`는 발견 가능한 디렉터리를 순회하고, 의도적 제외로 분류되지 않은 모든 발견 파일의 eligibility 확인과 읽기를 마쳤는지다. clone 미요청·실패 또는 어떤 eligibility 확인·읽기·순회 실패에도 false이고 의도적 제외만 있으면 true일 수 있다. `exclusions`는 정확히 `symlink`, `oversize`, `binary`의 비음수 개수를 가지며 `read_failures`는 안전한 clone 상대 `path`와 `operation`(`walk`, `stat`, `read`)만 가진 ordered array다. exception 원문은 저장하지 않는다.
- **R4.2** 기존 `skipped_files`는 하위 호환을 위해 발견한 파일 중 검색하지 않은 파일 수로 유지하며, 의도적 제외 세 계수와 파일 단위 `stat`/`read` 실패 수를 포함한다. `os.walk`의 `onerror`로 포착한 디렉터리 순회 실패는 미지의 파일 수를 허위 계수하지 않고 `read_failures`에만 기록한다. 읽기 실패가 하나라도 있으면 record와 manifest에 `static-search-incomplete:<count>` warning을 남긴다. 정확한 상태 메커니즘은 R3.2와 같은 record warning 검사에 `isinstance(warning, str) and warning.startswith("static-search-incomplete:")`를 기존 조건과 OR로 추가하는 것이다. 따라서 읽기 실패로 `complete: false`인 discovery와 새 manifest run의 `status`는 모두 `partial`, 종료 코드는 3이다. 이는 불완전한 zero-hit를 종료 0/complete로 표시하지 않으면서 positive hit를 보존하는 usable-partial 의미와 일치한다. intentional exclusion만 있는 경우에는 실패 warning이 없고 종료 상태도 이 조건으로 바뀌지 않는다.
- **R4.3** 읽힌 파일에서 얻은 positive hit는 검색이 불완전해도 기존 `evidence_status`의 `remote+static` 또는 `static-only` 근거로 보존한다. 그러나 `complete: false`인 zero-hit 결과는 전체 부재 증거로 해석할 수 없다. 기존 `evidence_status` 값 집합과 candidate/readiness 계약은 바꾸지 않고, 정적 검색 불완전성만으로 ready를 새로 만들거나 기존 gate를 완화하지 않는다. 배포 계약은 구버전 산출물에 `complete`이 없으면 새 소비자가 `true`로 추정하지 않도록 하고, `#80`~`#82`가 zero-hit 부재 판단 시 `available`과 `complete`을 함께 확인해야 한다고 명시한다.

### R5. 문서 전용 후속

- **R5.1** `references/verification-contract.md`는 일반 `_untrusted_text` 객체의 `sha256`이 저장된 `text`의 UTF-8 바이트 해시임을 명시해야 한다. 정책 file excerpt의 같은 필드는 잘리기 전 decoded 원본 content bytes의 해시이고, 정책 directory excerpt에서는 유효한 이름을 정렬한 canonical JSON bytes의 해시이며 두 경우 모두 해당 policy result의 `sha256`과 같다는 현재 동작도 구분해 적는다. 필드명·스키마·코드는 바꾸지 않으며 계약 테스트가 세 의미를 코드와 대조한다.
- **R5.2** 배포 계약의 명시적 follow-up 절에 I13을 남긴다. 현재 `clone_repository`가 git clone/rev-parse stderr를 보존하지 않고 `_static_record`가 `clone-failed`로 축약하므로 운영 진단이 제한된다는 사실, 향후 안전하게 redaction된 단계·stderr 요약 계약을 별도 승인으로 설계해야 한다는 방향, 이번 구현과 GitHub Issue 생성은 범위 밖임을 적는다.

### R6. 호환성, 회귀, 범위

- **R6.1** Python 표준 라이브러리만 사용하고 R4.1의 additive static-search 필드와 R2.3의 additive retry event/warning 정보 외의 배포 계약을 넓히지 않는다. Non-goals의 폐쇄 집합, manifest clone 다섯 필드, schema version, 종료 코드 집합과 우선순위를 유지한다. `SkillContractTests.test_closed_sets_manifest_schema_and_exit_contract`를 추가하여 코드 상수와 계약 문서를 대조한 Non-goals 11의 각 폐쇄 집합 및 크기, manifest `clones` entry의 정확한 다섯 key, 코드와 산출물의 `schema_version`, 종료 코드 0/1/2/3/4의 집합과 종료 4 선행·예산 소진 3·두 새 warning의 3 우선순위를 직접 단정해야 한다. `test_skill_layout_and_frontmatter`도 독립적으로 실행해 `SKILL.md` 줄 수를 단정한다. 소스·테스트·계약 문서 변경으로 `compute_revision()`은 재계산되어 달라질 수 있으며 테스트는 고정 hash가 아니라 재계산값을 단정한다.
- **R6.2** 직전 실행의 분할 완전성, 정책 `request-failed` ready 차단, recheck 실패 상태 차단, malformed 2xx 정책·중복 검색·community profile 처리, 미신뢰 검색 단서·저장 query 거부, record manifest 전파, render `unknown` 동작을 회귀시키지 않는다. 대상 스킬 전체 55-test 기준선과 형제 스킬 30·108-test 기준선을 오프라인 전체 스위트로 통과한다. 세 전체 스위트의 unittest discovery는 각각 같은 `tests` 디렉터리를 start directory와 top-level directory로 지정하여 `tests/__init__.py` 없이도 실행 가능한 형태여야 한다.
- **R6.3** 변경 파일은 대상 스킬의 구현·테스트·필요 최소 fixture·두 배포 계약 문서와 현재 quality-goal 산출물로 한정한다. 스킬 디렉터리의 날짜 literal·모델명·issue/PR URL 계약 함정, `SKILL.md` 200줄 미만, 두 references 문서 각각 400줄 미만을 지키며 Non-goals 12의 불변 경로는 baseline과 byte-identical하게 보존한다.

## Acceptance criteria

- **AC-1** non-object, bool `total_count`, non-bool `incomplete_results`, non-array `items`인 2xx code-search fixture 각각이 `available: false`, `total_count: null`, `invalid-search-payload` 경고가 되고 유효한 빈 2xx 대조군은 `available: true`를 유지한다. [실행] (`CMD-1`)
- **AC-2** malformed 2xx code search의 CLI discover는 종료 3/partial이고, clone 허용 시 임시 로컬 repository clone과 static search를 실제 시도한다. 같은 입력의 유효한 빈 2xx 대조군은 종료 0이며 clone을 시도하지 않는다. [실행] (`CMD-1`)
- **AC-3** code search 요청 위치가 `discover_code_search` 하나, 호출자가 `run_discover` 하나이고 recheck에는 code search를 신설하지 않는 범위와 기존 duplicate-search 형태 게이트 보존이 명시되어 있다. [문서] spec.md Interfaces and data flow — Code search 경계
- **AC-4** 두 transport 각각에서 403+숫자 `Retry-After`, 403+`Remaining=0`/숫자 `Reset`은 retry되고, 헤더 없음·malformed·Remaining 비0·NaN·무한대·음수 사례는 한 번만 요청한 뒤 permission-denied로 반환된다. [실행] (`CMD-2`)
- **AC-5** 두 transport에서 429와 503은 기존 최대 4회, 기본 대기 60·120·240초와 예산 4를 유지하고 각 지연은 300초를 넘지 않는다. rate-limit 403 한도 소진은 `failed`/`transport-or-5xx`이고 모호한 403은 `forbidden`/`http-403`이다. [실행] (`CMD-2`)
- **AC-6** retry 성공·한도 소진·모호한 403의 request event가 `retry_decision`과 `retry_reason`을 남기고, 최종 실패 warning은 기존 prefix와 rate-limit/permission-denied 이유를 포함하며 허용되지 않은 header나 secret을 보존하지 않는다. [실행] (`CMD-2`)
- **AC-7** 현재 실행이 만든 clone의 `rmtree`를 주입 예외로 실패시켜도 discovery와 manifest가 기록되고, record와 manifest run에 `clone-cleanup-failed:<repository>:<path>:<error-class>` warning이 있으며 clone entry는 `removed: false`다. 같은 실행에서 discovery `status == "partial"`, 새 manifest run `status == "partial"`, CLI 종료 코드 3을 함께 단정한다. [실행] (`CMD-3`)
- **AC-8** pre-existing sibling path와 clone root는 정리 실패 전후 byte-identical하고 삭제 호출 대상은 `created: true` session path뿐이다. `--keep-clone` 대조군은 삭제 호출·실패 warning 없이 `removed: false`를 유지한다. [실행] (`CMD-3`)
- **AC-9** 성공·실패·keep-clone의 모든 clone entry가 기존 다섯 필드만 가지며, 삭제가 실제 완료된 뒤 예외가 보고되는 주입 사례는 `removed: true`와 cleanup warning을 함께 남겨 어느 한쪽도 숨기지 않는다. [실행] (`CMD-3`)
- **AC-10** symlink, oversize, binary만 있는 정적 검색은 `available: true`, `complete: true`, 정확한 `exclusions`, 빈 `read_failures`, 기존 합계의 `skipped_files`, 실패 warning 없음으로 기록된다. [실행] (`CMD-4`)
- **AC-11** stat, read, walk 실패를 각각 주입하면 `available: true`, `complete: false`, 상대 path/operation의 ordered `read_failures`, 규칙에 맞는 `skipped_files`, `static-search-incomplete:<count>` warning이 기록되고 exception 원문은 산출물에 없다. 읽기 실패를 포함한 CLI 대조군은 discovery `status == "partial"`, 새 manifest run `status == "partial"`, 종료 코드 3을 함께 단정한다. clone 미요청·실패 기본 객체는 `available: false`, `complete: false`다. [실행] (`CMD-4`)
- **AC-12** 불완전 검색의 positive hit는 기존 evidence status에 반영되지만 불완전 zero-hit는 exhaustive absence나 새 ready 근거가 되지 않고, candidate 29필드·readiness 12키·evidence status 값 집합이 그대로다. [실행] (`CMD-4`)
- **AC-13** 두 배포 계약 문서가 additive static-search 필드, 구버전 missing-`complete`의 fail-closed 소비, `#80`~`#82` 영향을 코드 상수 및 결과 형태와 일치하게 설명한다. [실행] (`CMD-5`)
- **AC-14** 계약 문서와 계약 테스트가 일반 text, 정책 file, 정책 directory의 세 `sha256` 의미를 현재 코드 계산과 대조하며 필드·스키마 변경은 없다. [실행] (`CMD-5`)
- **AC-15** I13의 현재 진단 손실, redaction된 후속 설계 방향, 별도 승인 필요와 이번 미구현·Issue 미생성 범위가 함께 기록되어 있다. [문서] spec.md Non-goals 2 및 Decisions D5
- **AC-16** CMD-5의 명시된 독립 테스트들이 Non-goals 11의 각 폐쇄 집합과 크기, 코드·산출물의 동일한 schema version, 종료 코드 0/1/2/3/4와 종료 4 선행·예산 소진 3·두 새 warning의 3 우선순위, clone entry의 정확한 다섯 필드, 허용 header 일곱 개, revision 재계산 계약, `SKILL.md` 200줄 미만·두 reference 각각 400줄 미만 및 literal 함정을 모두 단정해 통과한다. [실행] (`CMD-5`)
- **AC-17** 대상 스킬 전체 오프라인 스위트가 기존 55건과 신설 회귀를 모두 포함해 OK이고, 직전 실행이 보장한 실패·불완전성 gate 회귀가 없다. [실행] (`CMD-6`)
- **AC-18** 형제 `analyzing-open-source-pr-patterns`의 오프라인 전체 스위트가 기존 30건으로 OK다. [실행] (`CMD-7`)
- **AC-19** 형제 `collecting-recent-closed-prs`의 오프라인 전체 스위트가 기존 108건으로 OK다. [실행] (`CMD-8`)
- **AC-20** 실제 변경 경로가 승인 범위에만 있고 1·2·3차 문서, 루트 `AGENTS.md`, 형제 스킬, 전역 설치본은 baseline과 byte-identical하다는 diff·digest 증거가 review context에 기록된다. [문서] spec.md Security and risk — 범위 무결성 판정

## Requirements traceability

This table maps every requirement to acceptance criteria and the judgement method that proves the mapping.

| Requirement | Acceptance criteria | Judgement method |
|---|---|---|
| R1.1 | AC-1 | `CMD-1` malformed/valid code-search payload 단정 |
| R1.2 | AC-2, AC-3 | `CMD-1` CLI fallback 대조 및 Interfaces 범위 검토 |
| R2.1 | AC-4 | `CMD-2` 403 header matrix |
| R2.2 | AC-5 | `CMD-2` transport·budget·delay·outcome matrix |
| R2.3 | AC-6 | `CMD-2` event·warning·header 단정 |
| R3.1 | AC-8 | `CMD-3` ownership/keep-clone 대조 |
| R3.2 | AC-7, AC-9 | `CMD-3` 산출물·partial·removed 사실성 단정 |
| R4.1 | AC-10, AC-11 | `CMD-4` complete/available 및 additive shape 단정 |
| R4.2 | AC-10, AC-11 | `CMD-4` exclusion/failure 계수와 warning 단정 |
| R4.3 | AC-12, AC-13 | `CMD-4` evidence 소비 및 `CMD-5` 계약 문서 단정 |
| R5.1 | AC-14 | `CMD-5` 세 hash 계산 계약 단정 |
| R5.2 | AC-15 | Non-goals 2와 D5 문서 검토 |
| R6.1 | AC-16 | `CMD-5` 폐쇄 집합·호환성 계약 단정 |
| R6.2 | AC-17, AC-18, AC-19 | `CMD-6`, `CMD-7`, `CMD-8` 전체 오프라인 회귀 |
| R6.3 | AC-20 | review context의 changed-path 및 baseline digest 검토 |

## Architecture

변경 경계는 네 구현 축과 두 문서 축으로 나뉜다.

1. **HTTP response policy** — `_valid_search_payload`를 code search에도 재사용한다. `_retryable(status, headers)`는 순수한 공용 분류 경계가 되고 두 transport가 동일하게 호출한다. 403의 rate-limit/permission 결과는 request event, warning, repository failure mapping까지 같은 분류를 재사용해 서로 다른 해석을 막는다.
2. **Discovery orchestration** — `run_discover`는 code-search availability를 기존 exit/clone 판정에 그대로 공급한다. clone cleanup은 조사 루프와 산출물 조립 사이에 있지만, per-session 오류를 값과 warning으로 바꿔 control flow를 끊지 않는다. 현재 partial 술어는 cleanup warning을 인식하지 않으므로 `combination_partial`에 `clone-cleanup-failed:` record-warning prefix 조건을 additive하게 추가하고, 기존 종료 코드로부터 discovery와 manifest run의 `partial` status를 도출한다.
3. **Static evidence result** — `static_search`는 기존 결과에 완전성 및 원인별 진단을 추가한다. `_static_record`는 clone 미요청/실패의 additive 기본값을 만들고, 수행 결과가 불완전하면 warning을 전파한다. `static-search-incomplete:`도 같은 `combination_partial` warning 검사에 additive하게 포함해 읽기 실패 run을 종료 3/partial로 만들며, `_evidence_status`의 네 값은 유지하고 positive evidence만 기존 방식으로 계산한다.
4. **Contract documentation** — `references/github-verification-contract.md`는 retry, code search, clone cleanup, static-search additive 계약과 하위 호환 소비를 소유한다. `references/verification-contract.md`는 persisted untrusted-text hash 의미와 I13 follow-up을 소유한다. 계약 테스트가 코드 상수·결과 형태·문구를 연결한다.

구현 파일은 `scripts/verify_candidates.py`, 행동 회귀는 `tests/test_verify_candidates.py`, 계약 회귀는 `tests/test_skill_contract.py`, 필요 시 기존 fixture 또는 승인 범위의 최소 새 fixture다. 새 모듈이나 의존성은 만들지 않는다.

## Interfaces and data flow

### Code search 경계

`run_discover` → `discover_code_search` → transport의 `/search/code` GET → status+payload 형태 검사 → `{available, queries, hits}` → `discover_exit_code` 및 clone 허용 판정 순서다. invalid 2xx는 `available: false`와 warning으로 흐르고, clone이 승인된 경우에만 정적 검색으로 이어진다. `/search/code` 요청은 이 경로 하나뿐이다. recheck는 `_recheck_duplicate_search`만 사용하고 새 code search를 만들지 않는다.

### Retry 경계

각 transport는 sanitized headers와 status를 공용 분류기에 넘기고, event에 decision/reason을 기록한 뒤 return 또는 기존 delay/retry를 수행한다. 최종 response의 같은 분류가 `_append_response_warning`과 repository access mapping에 전달된다. rate-limit 403이 회복되면 정상 payload만 소비하고, 소진되면 generic failed 접근 실패가 된다. 모호한 403은 최초 응답에서 forbidden 접근 실패가 된다.

### Clone cleanup 경계

clone session은 내부 소유권 메타데이터 `created`를 유지한다. cleanup은 각 session의 size와 삭제 전후 존재를 관찰하고 manifest의 기존 다섯 필드를 만든다. 실패는 exception이 아니라 warning과 실제 `removed` 값으로 orchestration에 돌아간다. warning은 그 session을 사용한 같은 repository의 모든 record와 run에 합쳐지고, 신설 `clone-cleanup-failed:` prefix 조건이 `combination_partial`을 참으로 만든 뒤 atomic discovery/manifest 쓰기가 종료 3/partial로 계속된다.

### Static-search additive shape

생산자는 기존 여섯 필드에 다음을 추가한다.

```text
complete: boolean
exclusions: {symlink: integer, oversize: integer, binary: integer}
read_failures: [{path: clone-relative string, operation: walk|stat|read}, ...]
```

구버전 소비자는 기존 필드만 읽어 계속 동작할 수 있다. 새 소비자는 `complete` 누락을 unknown/incomplete로 처리하고 true로 기본값 처리하지 않는다. 현재 candidate schema에는 static-search 객체가 직접 들어가지 않으므로 candidate 29필드는 변하지 않는다. discovery record와 manifest warning이 후속 `#80`~`#82`의 소비 경계다.

`read_failures`가 비어 있지 않아 `static-search-incomplete:` warning이 생기면 신설 warning-prefix 조건이 `combination_partial`을 참으로 만들고 discovery와 새 manifest run은 종료 3/partial이 된다. intentional exclusion만으로 `complete: true`인 결과에는 이 warning이 없으므로 상태를 바꾸지 않는다.

## Failure behavior

- invalid 2xx code search는 repository 전체 실패가 아니라 해당 조합의 code-search unavailable이다. discovery와 manifest를 쓰고 종료 3으로 끝나며, clone이 명시적으로 승인된 경우에만 정적 fallback을 시도한다.
- 모호한 403은 대기 없이 forbidden/http-403으로 끝난다. 명시적 rate-limit 403은 기존 budget/retry/delay 안에서만 재시도하고 소진되면 failed/transport-or-5xx로 끝난다. 429와 5xx는 기존 정책을 유지한다.
- cleanup 실패는 다른 session 정리를 계속하고 조사 산출물을 쓴다. 잔여 path가 있으면 제거되지 않았다고 기록하고 종료 3으로 표시한다. 운영자는 warning의 임시 path를 확인해 별도 수동 정리할 수 있지만 자동 재시도나 더 넓은 삭제는 하지 않는다.
- 정적 검색의 파일/디렉터리 읽기 실패는 검색을 중단시키지 않고 읽을 수 있는 나머지 파일을 계속 검색한다. 결과는 available이지만 incomplete이며 positive hit는 보존하고 discovery와 새 manifest run은 종료 3/partial이다. 실패가 없는 의도적 제외는 계약상 정상이며 이 partial 조건을 만들지 않는다.
- 계약 문서나 additive 기본 객체가 실제 코드와 어긋나면 계약 테스트가 실패한다. 어떤 실패도 새 candidate ready 상태나 확인된 부재로 합성하지 않는다.

## Security and risk

HTTP status, response headers, payload, 원격 텍스트는 모두 미신뢰 입력이다. rate-limit 분류는 allowlist로 sanitize된 header의 엄격한 숫자 파싱만 사용하며 body 문구로 권한을 추측하지 않는다. NaN과 무한대도 거부해 sleep 계산과 budget 흐름을 오염시키지 않는다. request event와 warning에는 허용 header 및 안정된 reason만 기록하고 credential이나 원문 오류 본문을 추가하지 않는다.

clone은 임시 디렉터리 아래, 현재 실행이 생성했다고 확인된 정확한 path만 삭제한다. cleanup 견고성 수정이 삭제 범위를 넓혀서는 안 되며 pre-existing path와 root는 신뢰 경계 밖이다. 정적 검색은 clone 파일을 실행하지 않고 읽기만 하며 symlink·oversize·binary 제외를 유지한다. OSError 원문 대신 상대 path와 operation만 저장해 로컬 절대 경로 또는 민감한 시스템 오류의 노출을 줄인다.

### 범위 무결성 판정

implementation review context는 quality-goal baseline과 현재 changed-file 목록 및 digest를 대조한다. 승인된 대상 스킬 파일·최소 fixture·두 계약 문서·현재 실행 산출물 밖의 변화가 있거나 1·2·3차 문서, 루트 `AGENTS.md`, 형제 스킬, 전역 설치본의 digest가 바뀌면 통과할 수 없다. 테스트는 네트워크와 대상 저장소 코드 실행을 막는 기존 주입 runner를 유지한다.

주요 잔여 위험은 header 없이 반환되는 secondary rate limit 403을 권한 거부로 분류해 자동 회복 기회를 놓칠 수 있다는 점이다. 이는 지연·예산 폭증보다 작은 위험으로 선택했으며, 사용자는 warning을 보고 새 run으로 회복할 수 있다. 향후 GitHub 계약이 안정된 추가 신호를 제공하면 별도 변경으로 분류 근거를 넓힐 수 있다.

## Test strategy

표적 테스트는 실패를 먼저 재현한 뒤 최소 구현을 검증한다. 모든 CLI 통합 테스트는 fixture transport, 주입 sleeper/clock, 임시 로컬 git repository를 사용한다. 실제 sleep, GitHub 요청, 대상 저장소 코드 실행은 없다. 표적 회귀 뒤 대상 전체, 계약 전체, 형제 전체 순서로 실행한다.

### 판정 명령 표

| ID | 명령 | 통과 조건 |
|---|---|---|
| CMD-1 | `cd /Users/lee-kyu-hwan/code/dotfiles__worktrees/79-feat-contribution-candidate-verifier/dot_codex/skills/verifying-open-source-contribution-candidates && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest tests.test_verify_candidates.VerifyCandidatesTests.test_code_search_malformed_2xx_is_partial_and_allows_clone_fallback -v` | AC-1·AC-2의 malformed matrix, partial/clone fallback, valid-empty 대조가 모두 OK |
| CMD-2 | `cd /Users/lee-kyu-hwan/code/dotfiles__worktrees/79-feat-contribution-candidate-verifier/dot_codex/skills/verifying-open-source-contribution-candidates && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest tests.test_verify_candidates.VerifyCandidatesTests.test_403_retry_classification_uses_headers_in_both_transports tests.test_verify_candidates.VerifyCandidatesTests.test_retry_policy_preserves_429_and_5xx_bounds_and_observability -v` | AC-4·AC-5·AC-6의 두 transport 분류, budget/delay, event/warning matrix가 모두 OK |
| CMD-3 | `cd /Users/lee-kyu-hwan/code/dotfiles__worktrees/79-feat-contribution-candidate-verifier/dot_codex/skills/verifying-open-source-contribution-candidates && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest tests.test_verify_candidates.VerifyCandidatesTests.test_cleanup_failure_preserves_outputs_and_partial_status tests.test_verify_candidates.VerifyCandidatesTests.test_clone_cleanup_exact_path_only -v` | AC-7·AC-8·AC-9의 산출물 보존, ownership, keep-clone, removed 사실성 및 기존 정리 회귀가 모두 OK |
| CMD-4 | `cd /Users/lee-kyu-hwan/code/dotfiles__worktrees/79-feat-contribution-candidate-verifier/dot_codex/skills/verifying-open-source-contribution-candidates && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest tests.test_verify_candidates.VerifyCandidatesTests.test_static_search_distinguishes_exclusions_and_read_failures tests.test_verify_candidates.VerifyCandidatesTests.test_static_search_incomplete_evidence_never_claims_absence_or_ready -v` | AC-10·AC-11·AC-12의 additive shape, 원인 구분, warning, evidence/ready 불변성이 모두 OK |
| CMD-5 | `cd /Users/lee-kyu-hwan/code/dotfiles__worktrees/79-feat-contribution-candidate-verifier/dot_codex/skills/verifying-open-source-contribution-candidates && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest tests.test_skill_contract.SkillContractTests.test_reference_documents_cover_contract tests.test_skill_contract.SkillContractTests.test_skill_layout_and_frontmatter tests.test_skill_contract.SkillContractTests.test_no_hardcoded_targets_dates_models tests.test_skill_contract.SkillContractTests.test_closed_sets_manifest_schema_and_exit_contract tests.test_verify_candidates.VerifyCandidatesTests.test_print_revision_matches_recomputation -v` | AC-13·AC-14·AC-16의 계약 문구/코드 대조, 모든 열거 불변식, literal·줄 수 제한, revision 재계산이 모두 OK |
| CMD-6 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s "/Users/lee-kyu-hwan/code/dotfiles__worktrees/79-feat-contribution-candidate-verifier/dot_codex/skills/verifying-open-source-contribution-candidates/tests" -t "/Users/lee-kyu-hwan/code/dotfiles__worktrees/79-feat-contribution-candidate-verifier/dot_codex/skills/verifying-open-source-contribution-candidates/tests" -p 'test_*.py' -v` | 현재 기준선 실측 `Ran 55 tests`/`OK`, 구현 후 기존 55건과 신설 테스트가 모두 OK; 네트워크 호출 없음 |
| CMD-7 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s "/Users/lee-kyu-hwan/code/dotfiles__worktrees/79-feat-contribution-candidate-verifier/dot_codex/skills/analyzing-open-source-pr-patterns/tests" -t "/Users/lee-kyu-hwan/code/dotfiles__worktrees/79-feat-contribution-candidate-verifier/dot_codex/skills/analyzing-open-source-pr-patterns/tests" -p 'test_*.py' -v` | 기준선 실측 `Ran 30 tests`/`OK` |
| CMD-8 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s "/Users/lee-kyu-hwan/code/dotfiles__worktrees/79-feat-contribution-candidate-verifier/dot_codex/skills/collecting-recent-closed-prs/tests" -t "/Users/lee-kyu-hwan/code/dotfiles__worktrees/79-feat-contribution-candidate-verifier/dot_codex/skills/collecting-recent-closed-prs/tests" -p 'test_*.py' -v` | 기준선 실측 `Ran 108 tests`/`OK` |

### Cross-regression 검토 결과

1. **I5와 접근 실패 outcome** — 모호한 403만 기존 forbidden/http-403으로 남고, 명시적 rate-limit 403의 retry 소진은 failed/transport-or-5xx로 분리된다. 따라서 권한 거부와 rate limit이 같은 outcome으로 세탁되지 않으며, 모든 저장소가 이처럼 실제 요청 후 실패한 경우에만 기존 종료 4 조건에 들어간다. 예산 소진 자체는 계속 3이다.
2. **CODE-002와 exit/clone** — invalid 2xx의 `available: false`가 정확히 기존 `combination_partial`과 `(remote_hits or not available)`에 들어가 종료 3 및 승인된 static fallback을 동시에 연다. valid empty 2xx는 `available: true`라 종료 0/clone 미시도를 유지한다. 두 소비자의 의미가 일치한다.
3. **I11과 evidence/readiness** — positive static hit 계산은 유지하되 incomplete zero-hit를 부재로 확정하지 않는다. candidate 29필드와 ready gate를 바꾸지 않으므로 기존 gate는 약화되지 않으며 후속 소비자는 additive `complete`을 확인해야 한다.
4. **I8·I11 partial과 종료 우선순위** — 예외를 삼키는 범위는 cleanup control flow뿐이고 삭제 허용식은 `created and not keep_clone`보다 넓어지지 않는다. `clone-cleanup-failed:`와 `static-search-incomplete:`는 `combination_partial`에 OR로만 추가되어 두 경우 모두 종료 3/partial이 된다. 모든 저장소가 실제로 시도된 접근 실패인지 보는 종료 4 판정은 이 OR보다 먼저 실행되고, repository budget 소진은 기존 `repository_partial`로 계속 종료 3이다. CODE-002의 `code_search.available: false`도 기존의 별도 OR 조건이므로 새 warning과 겹쳐도 결과는 한 번의 종료 3일 뿐 종료 4로 승격하거나 우선순위를 바꾸지 않는다. 타입·소유권 불명 path는 삭제하지 않는다.
5. **R6.1 증명 범위** — AC-16을 좁히지 않고 CMD-5에 layout 검사와 전용 closed-set/schema/clone/exit 계약 검사를 명시했으므로 manifest clone 다섯 필드, schema version, 모든 폐쇄 집합과 종료 우선순위의 증명 범위가 유지된다. 이 표적 판정은 discovery import 형태에 의존하지 않고, 실행 가능하게 고친 CMD-6 전체 회귀가 별도로 보강한다.

## Decisions

### D1. 403은 명시적 header 근거가 있을 때만 rate limit으로 분류한다

대안은 모든 403 재시도, 모든 403 즉시 거부, header 기반 분류 세 가지다. 첫째는 현재의 예산·대기 폭증을 유지하고, 둘째는 GitHub가 403으로 보내는 rate limit 회복을 포기한다. 세 번째가 두 실패를 구분한다. 그 안에서도 body message를 읽는 대안은 원격 자유 텍스트와 문구 변화에 의존하므로 제외하고, 이미 allowlist와 delay 계약에 포함된 numeric header만 사용한다. 모호한 403을 즉시 권한 거부로 보는 위험과 회복 방법은 R2.1 및 Security and risk에 기록했다.

### D2. 재시도 분류 결과를 response 소비 단계까지 일관되게 사용한다

재시도 여부만 고치고 repository mapping을 status-only로 두면 rate-limit 403 소진이 forbidden으로 오기록된다. 공용 분류 결과를 request event, warning, access mapping에서 재사용해 명시적 rate-limit 소진은 기존 generic failed 채널로, 모호한 403은 기존 forbidden 채널로 보낸다. 새 접근 실패 outcome이나 reason은 만들지 않는다.

### D3. Clone cleanup failure는 기존 clone shape와 usable partial로 표현한다

대안은 예외 전파, 새 `cleanup_error` clone 필드 추가, 기존 필드+warning 사용이다. 예외 전파는 산출물을 유실하고 새 필드는 하위 계약을 넓힌다. 기존 `path`, 실제 `removed`와 run/record warning이면 잔여 위치와 실패를 모두 표현할 수 있으므로 세 번째를 선택한다. 전체 성공으로 보이지 않게 종료 3/partial을 요구한다.

### D4. Static search 계약은 additive complete/exclusions/read_failures로 최소 확장한다

`available`의 의미를 incomplete까지 포함하도록 바꾸는 방법은 기존 소비자를 깨뜨리고, 새 evidence status를 만드는 방법은 승인된 폐쇄 집합과 후속 소비자 범위를 넓힌다. 기존 `available`과 `skipped_files`를 유지하고 orthogonal `complete`, 원인별 `exclusions`, 안전한 `read_failures`를 추가한다. positive evidence는 보존하고 negative evidence만 fail-closed로 소비한다.

### D5. I9와 I13은 구현하지 않고 정확한 계약 및 후속으로 남긴다

I9를 단일 hash 의미로 바꾸면 기존 정책 hash gate와 persisted schema 해석이 달라져 별도 migration 설계가 필요하다. 이번에는 세 현재 의미를 정확히 문서화한다. I13은 stderr의 redaction·길이 제한·단계 분류를 함께 설계해야 하므로 현재 `clone-failed` 한계를 배포 계약 follow-up에 기록하고 별도 승인으로 미룬다. GitHub Issue나 외부 기록은 만들지 않는다.

<!-- strict-only:start -->

### Threat and trust boundaries

미신뢰 경계는 GitHub status/header/payload/free text, offline fixture payload, clone 안의 파일명·내용, filesystem 오류다. 신뢰 경계는 코드의 header allowlist, 임시 clone-root 검증, 현재 run의 `created` 메타데이터, 고정된 closed-set 상수, atomic output writer다. 통제는 strict numeric parsing, body 기반 분류 금지, relative-path/operation만의 오류 기록, clone 실행 금지, exact-path cleanup, additive fail-closed `complete` 의미다. 공격 또는 오작동으로 malformed 2xx, NaN delay, symlink, OSError, rmtree failure가 들어와도 ready나 complete로 승격되지 않아야 한다.

### Authorization and tenant isolation

다중 tenant 서비스가 아니므로 tenant isolation은 해당 없음이다. 대신 repository와 실행 간 권한 경계를 적용한다. API는 read-only GET만 허용하고 403은 R2.1 근거로 분류한다. clone 삭제 권한은 현재 run이 생성한 정확한 temporary path에만 있으며 pre-existing path, sibling repository path, clone root, 다른 실행 path에는 없다. `--keep-clone`은 삭제 권한을 철회한다. 오프라인 테스트가 repository별 warning 귀속과 exact deletion target을 증명한다.

### Migration, compatibility, and rollback

persisted candidate나 manifest schema migration과 backfill은 없다. static-search producer는 기존 필드를 유지한 additive change이고 clone entry는 그대로다. 새 소비자는 과거 산출물의 missing `complete`을 unknown/incomplete로 취급한다. warning과 retry event의 additive key를 모르는 구버전 소비자는 기존 prefix·기존 필드로 계속 동작할 수 있다.

rollback trigger는 malformed 2xx가 종료 0이 되는 회귀, 모호한 403의 4회 소비, rate-limit 403의 forbidden 오분류, cleanup failure의 output 유실, incomplete zero-hit의 부재 승격, 폐쇄 집합 변화다. rollback은 구현·테스트·두 계약 문서의 현재 실행 diff만 되돌리고 persisted artifact를 변환하지 않는다. rollback 뒤 새 소비자는 missing `complete`을 계속 fail-closed로 다뤄야 한다. commit·push·배포는 이 workflow 범위 밖이다.

### Failure recovery and observability

관측 신호는 discovery/manifest status와 exit code, record/run warnings, manifest `retry_events`, clone entry의 path/removed/size, static `complete`/`exclusions`/`read_failures`다. rate-limit recovery는 같은 호출의 bounded retry이며 모호한 403은 새 discover run으로 회복한다. cleanup failure는 산출물의 잔여 path를 운영자가 확인하되 자동으로 상위 디렉터리를 지우지 않는다. static incomplete는 읽힌 파일의 hit를 보존하고 다음 clone/discover run으로 재관찰한다. 별도 alert·metric·trace backend가 없는 로컬 CLI이므로 manifest가 durable audit signal이다.

### High-risk end-to-end verification

승인된 high-risk E2E는 실제 CLI `discover`를 offline fixture transport와 임시 로컬 git repository로 끝까지 실행하여 HTTP 분류 → search result → clone/static fallback → cleanup → discovery/manifest atomic write → exit code를 함께 검증하는 CMD-1~CMD-4 및 전체 CMD-6이다. 증거는 명령, 종료 코드, unittest output, 생성 JSON의 단정이다. 네트워크 호출, 실제 sleep, 대상 저장소 코드 실행, 비임시 clone 삭제가 관찰되거나 어느 표적/전체 테스트가 실패하면 즉시 중단하고 통과로 기록하지 않는다. 라이브 검증은 승인되지 않았으므로 판정 수단이 아니다.

### No production mutation confirmation

자동 workflow에는 production mutation이 없다. GitHub는 호출하지 않고 fixture만 사용하며, commit·push·PR·merge·Issue·댓글·배포·`chezmoi apply`·전역 설치 수정도 하지 않는다. filesystem write는 승인된 worktree 파일과 테스트가 만든 임시 디렉터리로 제한한다.

<!-- strict-only:end -->
