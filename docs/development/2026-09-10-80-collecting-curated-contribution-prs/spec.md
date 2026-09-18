# Quality Goal Specification

- Task ID: 20260910T111848Z-80-트래커-issue-코멘트-기반-pr-수집-스킬-collecting-8a205a42
- Mode: strict
- Status: draft
- Created: 2026-09-10
- Updated: 2026-09-10
- Source goal: #80 트래커 Issue 코멘트 기반 PR 수집 스킬 collecting-curated-contribution-prs 구현

## Problem and context

Issue #80은 호출자가 지정한 GitHub 트래커 저장소와 Issue에서 제출 PR을 찾아, 출처 코멘트와 PR 사실을 오프라인 분석용 corpus로 정규화하는 Codex 스킬을 요구한다. 저장소에는 날짜 범위 기반 수집기 `dot_codex/skills/collecting-recent-closed-prs/`와 corpus 1.0.0 검증기 `dot_codex/skills/analyzing-open-source-pr-patterns/scripts/validate_corpus.py`가 이미 있다. 변경 전 형제 테스트는 collector 110개, analyzer 30개, candidate verifier 62개가 모두 종료 코드 0으로 통과했고, collector와 analyzer revision은 각각 `sha256:0f934b70d81a3be9d066dca7e4f9366342bf091e54f22485c8cf66c8b35493ad`, `sha256:87b9fc2bb39513851de14f6f029506f88101f3724653dfa820dc72280e8c7d24`였다. Fast-forward 후 base commit은 `067923b`이며, `merge_corpus` 및 하위 helper의 병합 영역은 이전 측정과 바이트 동일하고 출처 위조 결함도 재현되어 D1과 SPEC-001 해소의 근거는 유지된다.

RED 행동 평가는 신규 스킬 없이도 일부 안전 행동을 보였지만, `RED-1`부터 `RED-5`까지 댓글 편집 근거, 역할 출처, analyzer 호환성, manifest 결정성, 재수집 멱등성이 없거나 잘못됨을 실증했다. 또한 형제 collector의 현재 `merge_corpus`는 incoming record에 `recent-closed` 관측이 없을 때 record 필드에서 해당 관측과 출처를 합성한다. 트래커 전용 record를 그대로 넣은 probe에서는 검색 API가 관측하지 않은 PR에 `recent-closed` 출처가 생겼다. 따라서 형제 병합 로직을 재사용하되 출처 합성 정책을 호출자가 명시할 수 있어야 한다.

GitHub REST 계약상 Issue 댓글 목록은 `per_page` 최대 100, `page`, `since`를 지원하고 댓글을 `id` 오름차순으로 반환한다. 다음 페이지 존재 여부와 URL은 `Link` 응답 헤더의 `rel="next"`가 정본이다. `author_association`은 해당 댓글이 달린 저장소 문맥의 관계만 뜻하므로 트래커 댓글의 값은 upstream 권한 증거가 아니다. 원격 Issue 본문, 댓글, PR 텍스트는 모두 신뢰하지 않는 데이터이다.

영향받는 사용자는 트래커 제출 PR을 재현 가능하게 수집해 기존 analyzer로 넘기는 Codex 사용자와, 같은 PR을 날짜 기반 corpus와 결합하는 후속 분석 작업자다.

## Goals

- 호출자 지정 트래커 Issue의 본문과 모든 접근 가능한 댓글에서 제출 PR 출처를 수집하고, 편집·중복·부분 수집을 재현 가능한 관측과 manifest로 남긴다.
- corpus 1.0.0 및 append-only 비교 계약을 통과하는 산출물을 만들고, 글로벌 PR node identity로 날짜 기반 수집 결과와 안전하게 결합한다.
- 트래커 문맥의 association과 upstream에서 검증된 역할을 분리하고, 원격 텍스트가 명령·경로·권한·수집 상태를 바꾸지 못하게 한다.
- 기존 collector의 기본 동작과 6-file revision 계산 계약을 보존하면서, curated 호출에만 거짓 `recent-closed` 출처 합성을 끄는 최소 변경을 한다.
- Issue #80의 여섯 완료 기준을 표준 라이브러리 테스트, 실제 JSON 산출물 검증, 독립 행동 평가로 판정한다.

## Non-goals

- 일반 저장소의 Issue 전체를 탐색하거나 트래커 밖에서 후보를 발견하는 기능
- 다른 저장소에서 기여 후보를 검증하거나 `PAT-*`/`CAN-*` 분석 결과를 만드는 기능
- Issue, PR, 댓글, 리뷰, 라벨, 브랜치 등 GitHub 상태를 쓰거나 변경하는 기능
- 실제 트래커를 대상으로 한 이 변경의 라이브 수집 실행과 공용 배포(#82)
- `~/.codex`, `~/.claude`, main 또는 다른 worktree의 설치본·파일 변경
- 특정 실제 저장소, 프로그램, 멘토 관계, 날짜, cap 또는 API budget의 내장 기본 사례화
- corpus schema migration, 기존 manifest의 암묵적 변환, analyzer 또는 candidate verifier의 기능 변경
- README, changelog, 설치 가이드, 중복 quick reference 추가

## Requirements

- **R1.1** `dot_codex/skills/collecting-curated-contribution-prs/`에 자동 발견 가능한 신규 Codex 스킬을 두고, description과 본문은 사용자 지정 트래커 Issue 제출 PR 수집에만 라우팅하며 날짜 범위 수집·패턴 분석·후보 검증·GitHub 쓰기와 경계를 분명히 한다.
- **R1.2** 수집 CLI는 tracker repository, Issue number, PR collection cap, shared API request budget, corpus output, manifest output을 호출자에게서 받고, 선택적 existing corpus·existing manifest·resume run ID를 받는다. repository/Issue/cap/budget/output 유효성 및 output alias는 첫 GitHub 요청 전에 거부한다.
- **R1.3** 스킬의 허용 파일 집합은 `SKILL.md`, `agents/openai.yaml`, 필요한 `references/` 계약 문서, 단일 책임 `scripts/` 수집 script, 표준 라이브러리 test module, 합성 JSON을 둔 `tests/fixtures/`, `evals/` 행동 평가 문서다. README, changelog, 설치 가이드, 중복 quick reference와 그 밖의 파일은 추가하지 않는다. `SKILL.md`에는 결정적 Python 규칙을 복제하지 않고 script와 필요한 reference를 라우팅한다.

- **R2.1** GitHub 접근은 인증된 `gh api`의 직렬 GET만 사용한다. curated collector는 형제 `GitHubClient.get_json`을 변경 없이 사용하고 caller는 상대 endpoint와 `page`만 전달하며 adapter가 `per_page=100`을 한 번만 주입한다. 댓글 응답의 `Link rel="next"` 존재 여부만 다음 요청의 권위 신호로 삼고, 관측한 next URL이 기대한 comments endpoint의 page 기반 query이며 파싱한 `page`가 현재 요청 page + 1인지, `per_page`가 있으면 100인지 검증한 뒤 그 page 번호를 adapter에 전달한다. next가 없으면 멈추고 payload 길이로 다음 페이지를 추측하지 않는다. cursor 또는 `before`/`after`, 다른 endpoint·host, 기대와 다른 page, 지원하지 않는 결과 영향 query이면 요청하지 않고 해당 범위를 partial로 남긴다. 수집된 comment database ID가 전체 페이지에서 엄격한 오름차순이 아니거나 중복·역행하면 thread mutation gap으로 보아 complete로 보고하지 않는다.
- **R2.2** Issue 본문과 댓글에서 발견한 GitHub PR URL을 origin별 reference로 보존하고 실제 제출과 예시·공지 reference를 구분한다. 같은 PR의 여러 reference는 하나의 PR record에 각기 다른 출처 관측으로 남기며 cap의 한 건으로 계산한다.
- **R2.3** collection cap은 한 tracker Issue에서 선택하는 고유 제출 PR 수에 적용한다. request budget은 preflight, Issue, 검증된 Link page를 adapter로 요청하는 댓글 pagination, PR hydration, retry를 포함한 모든 GitHub 요청 시도에 공유 적용하며 resume이 이를 재설정하지 않는다. Link parsing·validation 자체는 요청을 소비하지 않고, 잘못된 next URL에서는 추측성 요청을 보내지 않는다. cap으로 제외된 수와 미방문 범위는 manifest에 구분해 기록한다.
- **R2.4** 선택된 PR은 형제 collector의 authoritative PR hydration과 identity/state 규칙을 재사용한다. 접근 실패는 확인되지 않은 identity/state와 구체적 failure scope로 보존하고, 접근 가능한 현재 PR state는 종료 여부와 관계없이 그대로 정규화한다.
- **R2.5** 각 tracker 관측에는 댓글 작성자의 원본 `author_association`을 tracker 문맥 값으로 보존하되 이를 PR author의 `resolved_role`로 사용하지 않는다. upstream 역할은 upstream PR 응답의 association만으로 형제 계약대로 `upstream-maintainer`, `contributor`, `unknown` 중 하나로 매핑하고 근거를 분리한다.
- **R2.6** Issue 본문·댓글·PR 본문·discussion·patch·commit message는 불활성 비신뢰 데이터다. 그 내용은 명령 실행, output path나 CLI option 선택, 권한 부여, authoritative PR state, run status, retry/budget 정책을 결정할 수 없다.

- **R3.1** corpus는 `schema_version: "1.0.0"`, `generated_by`, `records`를 출력하고 analyzer의 `_validate_document`를 통과한다. existing corpus가 없는 fresh 수집은 envelope `generated_by`에 curated skill의 실제 name/revision을 쓴다. existing corpus와 병합할 때는 기존 record의 생성자를 curated 생성자로 오기하지 않도록 기존 envelope `generated_by`를 deep-equal JSON 값으로 보존한다. curated skill의 실제 name/revision은 새 manifest run과 새로 생성하는 tracker source metadata에 기록하고, 이미 존재하는 tracker source metadata는 append-only prefix 계약대로 보존한다. 모든 record는 `resolved|unresolved` identity, 비어 있지 않은 고유 `source_key`의 source 배열, observation 배열, 비어 있지 않은 `state_history`, 비어 있지 않은 `pull_request.url`을 가진다.
- **R3.2** tracker source key는 Issue node ID에서 결정적으로 파생해 서로 다른 tracker Issue가 충돌하지 않게 한다. 댓글 관측은 최소한 run ID, comment database ID와 node ID, API URL과 HTML URL, commenter login, tracker `author_association`, created/updated timestamp, UTF-8 comment body의 SHA-256을 보존한다. Issue 본문 reference는 origin kind, Issue node ID/URL, updated timestamp, body SHA-256으로 댓글과 구분한다.
- **R3.3** resolved record는 `pull_request_node_id`, `repository.node_id`, `record_key == "github-pr:<pull_request_node_id>"`를 사용한다. 같은 글로벌 PR node ID는 수집 경로와 URL alias에 관계없이 한 record로 병합하고, unresolved URL은 node identity를 추측하지 않는다. 기존 non-null `pr_id`와 resolved identity mapping을 보존하며 신규 ID만 최대 numeric suffix 뒤에서 결정적으로 할당한다.
- **R3.4** 형제 collector의 `merge_corpus`에는 명시적 `source_policy`를 추가한다. 기본값 `recent-closed`는 기존 호출과 합성 동작을 보존하고, `explicit-only`는 incoming `sources`에 실제로 있는 source와 observation만 append한다. curated collector는 모든 병합에 `explicit-only`를 사용하며 별도 merger 복제나 산출 후 source 삭제를 하지 않는다. 알 수 없는 정책은 입력 오류다.
- **R3.5** tracker observation identity는 comment의 경우 comment node ID, updated timestamp, body SHA-256의 조합이고 Issue 본문은 Issue node ID, updated timestamp, body SHA-256의 조합이다. 같은 관측 재수집은 중복 append하지 않고, 같은 node의 수정된 관측은 이전 관측 뒤에 append한다. source order, source metadata, observations, state history는 기존 corpus의 정확한 prefix를 보존한다.
- **R3.6** materialized PR projection과 authoritative `state_history`는 PR API의 최신 authoritative timestamp만 반영한다. 접근 실패 record는 corpus 계약을 위해 failure 근거가 있는 `unknown` 관측만 남길 수 있고, tracker 텍스트나 접근 실패에서 open/closed/merged/deleted event를 합성하지 않는다. earlier authoritative observations와 unknown JSON fields/types를 보존한다.

- **R4.1** collection manifest는 형제와 같은 `schema_version: "2.0.0"`, `generated_by`, append-only `records` envelope를 사용한다. 각 run은 stable run ID와 request fingerprint, `collection_method: "tracker-issue-comments"`와 normalized tracker repository/Issue-number identity, cap/budget/API·client·curated skill name/revision, 시작·완료 시각, request count/events, comment page provenance, reference matched/selected/excluded counts, PR hydration outcomes, warnings, failed scopes, `complete|partial|failed` status를 기록한다. comment page provenance에는 요청한 page/endpoint, 원문 next URL 또는 부재, 파싱된 page, Link validation 결과와 실패 사유, comment ID 범위를 남겨 transport·pagination drift와 thread mutation을 검출할 수 있게 한다.
- **R4.2** resume은 existing corpus와 manifest, 정확히 일치하는 run ID와 fingerprint가 모두 있을 때만 같은 run을 갱신한다. fingerprint는 tracker repository/Issue identity, cap, budget, API version과 결과에 영향을 주는 입력을 포함한다. 변경된 입력은 network 전에 실패하고, resume ID 없는 재수집은 새 manifest run을 append한다.
- **R4.3** 선언한 capped scope와 필요한 evidence가 모두 처리되었을 때만 manifest status `complete`와 종료 코드 0이다. 잘못되거나 지원하지 않는 next URL, comment ID 중복·역행을 포함한 pagination gap, access·hydration·budget gap이 있으나 유효 corpus가 있으면 `partial`과 종료 코드 3, 유효 corpus가 없거나 global preflight가 실패하면 `failed`와 종료 코드 4, 입력·schema·resume·manifest discriminator 불일치는 종료 코드 2로 끝난다. partial/failed scope는 누락이 없는 것처럼 보고하지 않는다.
- **R4.4** corpus와 manifest는 UTF-8 및 trailing newline으로 서로 다른 호출자 지정 경로에 원자적으로 저장한다. checkpoint 또는 최종 저장 중 실패하면 기존 destination을 보존하고 임시 파일을 정리하며, JSON 저장 성공 전 파생 보고서를 성공 산출물로 제시하지 않는다.
- **R4.5** `--existing-manifest`는 append와 resume 모두에서 첫 GitHub 요청 전에 curated manifest인지 판별한다. envelope `generated_by.name`은 `collecting-curated-contribution-prs`, 각 기존 run의 `collection_method`는 `tracker-issue-comments`여야 하며, normalized tracker `OWNER/REPO`와 integer Issue number는 caller 입력과 같아야 한다. 날짜 범위 형제 manifest, collection method가 다른 manifest, 또는 다른 tracker repository/Issue manifest는 schema version이 같아도 입력 오류로 거부하고 network와 destination을 변경하지 않는다.

- **R5.1** 인증된 원본 Issue/댓글/PR payload와 그로부터 생성된 corpus·manifest는 호출자 지정 runtime 산출물로 취급한다. repository에 포함되는 계약·test·eval에는 합성 public fixture만 사용하고 token, private roster, 실명·이메일 또는 인증된 private 원문을 복사하지 않는다.
- **R5.2** 스킬과 script는 GitHub read-only 수집 및 요청된 로컬 산출물 쓰기만 수행한다. GitHub POST/PATCH/PUT/DELETE, Issue/PR/comment/review/label 변경, clone, dependency install, 원격 텍스트가 지정한 추가 파일 쓰기를 수행하지 않는다.

- **R6.1** 신규 skill revision은 `SKILL.md`, `agents/openai.yaml`, `references/collection-contract.md`, `references/github-rest-contract.md`, `scripts/collect_curated_contribution_prs.py`, `tests/test_collect_curated_contribution_prs.py` 여섯 canonical 경로만 sorted relative path 순서로 UTF-8 path length, path bytes, raw content length, raw bytes를 각각 unsigned 8-byte big-endian으로 framing해 SHA-256으로 계산하고 `sha256:<64 lowercase hex>`를 출력한다. 허용 파일인 `tests/fixtures/`와 `evals/`는 revision 입력이 아니다. 형제 collector의 기존 여섯 경로와 같은 framing/recalculation 계약은 보존하되 내용 변경으로 digest가 달라지는 것은 허용한다.
- **R6.2** 테스트는 외부 Python dependency 없이 표준 라이브러리 `unittest`로 실제 CLI/JSON/exit code와 analyzer validator를 판정한다. 신규 스킬은 system `quick_validate.py`를 통과하며 pytest, CI 설정, 네트워크 라이브 fixture를 요구하지 않는다.
- **R6.3** 독립 행동 평가는 합성 tracker fixture를 새 컨텍스트에서 신규 스킬로 처리하고, 실행 요청이 실제로 전달된 명령·경로·option·status에 들어가지 않았음을 산출물과 실행 기록으로 확인한다. 같은 평가에서 기존 RED가 이미 통과한 안전 행동은 회귀 시나리오로만 고정하고 일반 지침을 중복하지 않는다.
- **R6.4** 변경 후 신규 suite와 형제 collector·analyzer·candidate verifier 전체 suite를 실행한다. 최종 test count를 목표로 삼지 않고, source-policy의 기본/explicit 양방향 병합, 재수집, Issue #80 실패·경계 시나리오의 행위를 판정한다.
- **R6.5** 필터를 쓰는 CMD-2·CMD-3·CMD-4·CMD-12에 배정된 모든 실행 AC는 해당 AC 줄의 판정 수단에 정확한 `test_ac_<2-digit-number>_<filter>_<intent>` unittest method token을 하나 이상 선언한다. `<filter>`는 그 CMD의 `-k` 값과 같아야 한다. CMD는 verbose 출력에서 선언된 모든 exact test ID가 실행되어 `ok`인지 확인하며, 무관한 substring test 하나로 대체할 수 없다. `unittest`의 `NO TESTS RAN`과 종료 코드 5는 0건 선택을 뜻하므로 항상 실패다. contract meta-test는 Spec의 AC→CMD→test token 매핑, discover된 method 존재, filter 포함을 대조한다.

## Acceptance criteria

- **AC-1** 신규 폴더의 `SKILL.md` name은 `collecting-curated-contribution-prs`이고 description은 tracker Issue 수집으로 라우팅하며 인접 세 스킬과 GitHub 쓰기를 명시적으로 제외한다. [실행] (CMD-2 test_ac_01_contract_routing)
- **AC-2** 유효한 caller-supplied repository/Issue/cap/budget/output 조합은 파싱되고, 잘못된 값·중복 destination·불완전 resume 조합은 fake client 호출 0회로 입력 오류가 된다. fixture 밖 실제 저장소명·날짜·역할·cap·budget 하드코딩은 계약 검사에서 검출된다. [실행] (CMD-2 test_ac_02_contract_cli_validation)
- **AC-3** 신규 스킬의 허용 파일 집합은 계약·script·test module·합성 `tests/fixtures/`·`evals/`로 제한되고 `openai.yaml` quoted string/interface 값이 skill-creator 계약에 맞으며 README·changelog·설치 가이드·중복 quick reference·placeholder가 없다. [실행] (CMD-2 CMD-5 test_ac_03_contract_packaging)
- **AC-4** 두 페이지 댓글 fixture에서 첫 응답이 짧더라도 `Link rel="next"`가 있을 때 원문 next URL과 파싱된 page를 provenance에 남기고, 기대한 다음 page와 일치할 때만 형제 adapter에 상대 endpoint와 `page`를 전달한다. adapter argv의 `per_page=100`은 정확히 한 번이고, next가 사라진 뒤 요청하거나 payload 길이로 page를 추측하거나 비GET을 보내지 않으며 결과 comment ID는 엄격한 오름차순이다. cursor·`before`/`after`·page mismatch fixture는 추가 요청 없이 partial이 된다. [실행] (CMD-3 test_ac_04_collection_link_page_validation)
- **AC-5** Issue 본문과 댓글의 PR reference fixture는 고유 제출 PR 단위로 정규화되고, 같은 PR의 서로 다른 두 댓글은 한 record의 서로 다른 관측으로 보존되며 예시·공지 reference는 manifest exclusion으로 구분된다. [실행] (CMD-12 test_ac_05_end_to_end_reference_normalization)
- **AC-6** cap 초과 fixture는 first-reference 순서로 정확한 수의 고유 PR만 선택하고 matched/selected/excluded-by-cap을 각각 기록하며 capped scope를 uncapped census로 표현하지 않는다. [실행] (CMD-3 test_ac_06_collection_cap_counts)
- **AC-7** preflight·pagination·hydration·retry 요청이 하나의 budget을 소비하고, budget exhausted와 resume fixture에서 새 요청이 한도를 넘지 않으며 이전 request count가 재설정되지 않는다. 잘못된 next URL fixture는 추측성 request count를 늘리지 않는다. [실행] (CMD-3 test_ac_07_collection_shared_budget)
- **AC-8** authoritative PR fixture의 state와 identity가 corpus에 반영되고, 접근 실패 record는 failure 근거가 있는 `unknown` history만 가지며 현재 open PR은 authoritative open history를 가진다. 접근 실패에서 open/closed/merged/deleted를 합성하지 않는다. [실행] (CMD-12 test_ac_08_end_to_end_authoritative_hydration)
- **AC-9** tracker comment association과 upstream PR author association은 별도 필드·basis를 가지며 tracker `NONE` 또는 tracker `MEMBER`만으로 contributor/upstream-maintainer가 되지 않는다. upstream association 매핑의 세 결과가 모두 테스트된다. [실행] (CMD-3 test_ac_09_collection_role_separation)
- **AC-10** 주입 payload가 있는 fixture 실행에서 shell/추가 network/지정 외 파일 쓰기 0회이고 caller output, budget, status, PR state가 payload 전후 동일한 규칙으로 결정된다. [실행] (CMD-12 test_ac_10_end_to_end_injection_is_data)
- **AC-11** fresh end-to-end expected corpus가 실제 analyzer validator에서 종료 코드 0을 낸다. [실행] (CMD-6)
- **AC-12** expected corpus의 모든 record가 corpus 1.0.0 필수 identity/source/observation/state/URL 불변식을 만족하고 resolved record가 global node identity와 record key를 일치시킨다. [실행] (CMD-12 test_ac_12_end_to_end_corpus_invariants)
- **AC-13** edited-comment fixture의 두 관측 모두 comment ID/node ID/API URL/HTML URL/login/raw association/created/updated/body SHA-256을 가지며 원문 body를 바꾸면 hash가 달라진다. Issue-body 관측은 origin kind와 Issue identity로 구분된다. [실행] (CMD-3 test_ac_13_collection_observation_provenance)
- **AC-14** 같은 PR node ID가 recent-existing plus curated-incoming 및 curated-existing plus recent-incoming 양쪽 순서에서 각각 한 record가 되고 기존 `pr_id`와 identity를 보존한다. [실행] (CMD-4 test_ac_14_merge_global_identity)
- **AC-15** `merge_corpus`의 option 생략과 `source_policy="recent-closed"`가 기존 suite가 기대하는 corpus를 동일하게 만들고, 알 수 없는 policy는 입력 오류다. [실행] (CMD-8)
- **AC-16** `source_policy="explicit-only"`에서 recent-existing plus curated-incoming은 기존 real recent source 뒤에 tracker source만 append하고, tracker-only 신규 PR에는 `recent-closed` source/observation이 없다. reverse merge는 tracker prefix 뒤에 실제 incoming recent source만 append한다. [실행] (CMD-4 test_ac_16_merge_explicit_only_sources)
- **AC-17** 동일 tracker payload 재수집은 tracker observation/state event 수를 늘리지 않고, 같은 comment node의 changed updated timestamp/body hash 재수집은 기존 observation의 정확한 뒤에 한 건만 append한다. [실행] (CMD-4 test_ac_17_merge_recollection_idempotency)
- **AC-18** recollected corpus가 initial corpus를 `--existing`으로 준 analyzer append-only 검사에서 종료 코드 0을 내며 source key order, source metadata, observations, state history의 prefix를 보존한다. [실행] (CMD-7)
- **AC-19** older PR observation이 최신 materialized projection을 덮지 않고, 접근 실패 fixture는 `unknown` 이외의 fabricated state-history event를 만들지 않으며 unknown JSON fields/types가 보존된다. [실행] (CMD-4 test_ac_19_merge_projection_history)
- **AC-20** expected manifest는 2.0.0 envelope와 required run fields, `collection_method: "tracker-issue-comments"`, normalized tracker identity, comment page provenance, 원문 next URL·파싱 page·validation 결과·comment ID 범위, counts, outcomes, warnings/failed scopes를 실제 생성 결과로 가진다. [실행] (CMD-12 test_ac_20_end_to_end_manifest_provenance)
- **AC-21** exact fingerprint resume은 같은 run ID를 교체 갱신하고 이전 completed checkpoint를 재사용하며, resume ID 없는 같은 입력 재수집은 기존 run prefix 뒤에 새 run을 append한다. [실행] (CMD-3 test_ac_21_collection_resume_append)
- **AC-22** fingerprint 구성 입력 하나를 바꾼 resume fixture는 GitHub 요청과 destination 변경 없이 종료 코드 2가 된다. [실행] (CMD-3 test_ac_22_collection_fingerprint_mismatch)
- **AC-23** 댓글 next-page failure, invalid/cursor/page-mismatch next URL, comment ID 중복·역행, PR access failure, hydration failure, budget exhaustion 각각은 usable record가 있을 때 manifest partial·failed scope와 종료 코드 3을 만들고 complete를 만들지 않는다. [실행] (CMD-3 test_ac_23_collection_partial_gaps)
- **AC-24** invalid input/schema/resume/manifest discriminator는 종료 코드 2이고, global preflight 실패 또는 usable corpus 0건의 collection failure는 manifest failed와 종료 코드 4이며 traceback이나 credential을 출력하지 않는다. complete 성공은 종료 코드 0과 manifest status `complete`다. [실행] (CMD-3 test_ac_24_collection_exit_matrix)
- **AC-25** corpus/manifest serialization 또는 replace 실패 fixture가 기존 destination bytes를 보존하고 sibling temporary file을 남기지 않으며, 성공 JSON은 UTF-8 trailing newline을 가진다. [실행] (CMD-3 test_ac_25_collection_atomic_output)
- **AC-26** repository에 추가되는 fixture와 문서 전체에 synthetic 표기가 있고 baseline private-source marker의 roster/실명/이메일 값과 credential이 없으며, runtime private input은 caller output 밖 public artifact로 복사되지 않는다. [실행] (CMD-2 test_ac_26_contract_public_fixtures)
- **AC-27** fake runner가 관측한 모든 GitHub 호출은 `gh api --method GET`, `shell=False`이고, clone/install/GitHub write 및 injected output path 쓰기 호출은 0회다. [실행] (CMD-12 test_ac_27_end_to_end_read_only_runner)
- **AC-28** 신규 `--print-revision`은 정규식에 맞고 canonical file 한 개의 byte를 바꾼 임시 복제마다 달라진다. 형제 collector의 six-path framing 회귀 테스트와 전체 suite도 통과한다. [실행] (CMD-1, CMD-11, CMD-8)
- **AC-29** 신규 전체 suite는 pytest나 제3자 test dependency 없이 종료 코드 0이며 실제 temporary corpus/manifest와 CLI exit code를 검사한다. [실행] (CMD-1)
- **AC-30** 독립 행동 평가 문서는 신규 스킬로 수행한 injection 시나리오의 입력, 새 컨텍스트 조건, 실제 실행 기록, 명령·경로·status 관측, corpus/manifest 위치, 각 exit code와 판정을 기록한다. [문서] dot_codex/skills/collecting-curated-contribution-prs/evals/behavioral-eval.md
- **AC-31** RED fixture end-to-end 검사는 편집 근거, role separation, analyzer-compatible corpus, deterministic manifest/run contract, recollection idempotency를 모두 실제 산출물로 판정해 `RED-1`부터 `RED-5`의 재현 조건을 통과로 바꾼다. [실행] (CMD-12 test_ac_31_end_to_end_red_to_green)
- **AC-32** 같은 end-to-end 및 행동 평가 시나리오는 주입 무시, 예시·공지 제외, 현재 state 보존, inaccessible과 삭제의 비동치, private source 비사용, partial honesty의 기존 통과 행동을 회귀로 고정한다. [실행] (CMD-12 test_ac_32_end_to_end_safety_regression)
- **AC-33** 형제 recent collector 전체 suite가 source-policy 변경 후 종료 코드 0이다. [실행] (CMD-8)
- **AC-34** analyzer 전체 suite가 종료 코드 0이다. [실행] (CMD-9)
- **AC-35** candidate verifier 전체 suite가 종료 코드 0이다. [실행] (CMD-10)
- **AC-36** 신규 skill directory가 system skill validator에서 종료 코드 0과 `Skill is valid!`를 출력한다. [실행] (CMD-5)
- **AC-37** existing corpus가 없는 fresh 수집의 corpus envelope `generated_by`는 curated skill의 실제 name/revision과 일치하고 manifest run에도 같은 name/revision이 기록된다. [실행] (CMD-12 test_ac_37_end_to_end_fresh_generated_by)
- **AC-38** recent-generated existing corpus에 curated 결과를 병합하면 corpus envelope `generated_by`는 기존 JSON 값을 그대로 보존하고, curated skill의 실제 name/revision은 새 manifest run과 tracker source metadata에 남는다. [실행] (CMD-4 test_ac_38_merge_preserves_generated_by)
- **AC-39** 형제 date-range manifest와 caller와 다른 tracker repository 또는 Issue의 curated manifest를 각각 `--existing-manifest`로 주면 GitHub 요청 0회, destination 변경 0회, 종료 코드 2가 된다. 같은 tracker의 curated manifest만 append/resume validation으로 진행한다. [실행] (CMD-3 test_ac_39_collection_rejects_foreign_manifest)
- **AC-40** contract meta-test는 CMD-2·CMD-3·CMD-4·CMD-12에 배정된 모든 실행 AC에서 filter와 AC 번호가 포함된 exact test token을 추출하고 discover된 method와 일대일로 대조한다. 누락·오타·잘못된 filter·선택 0건에서는 실패하며 자신의 verbose test ID도 출력된다. [실행] (CMD-2 test_ac_40_contract_judgement_mapping)

## Requirements traceability

This table maps every requirement to acceptance criteria and the judgement method that proves the mapping.

| Requirement | Acceptance criteria | Judgement method |
|---|---|---|
| R1.1 | AC-1 | CMD-2의 routing/boundary 계약 검사 |
| R1.2 | AC-2 | CMD-2의 CLI preflight 및 hardcode 검사 |
| R1.3 | AC-3 | CMD-2의 packaging 계약 검사와 CMD-5의 실제 skill validator |
| R2.1 | AC-4 | CMD-3의 Link 기반 GET pagination 검사 |
| R2.2 | AC-5 | CMD-12의 실제 thread-to-corpus 산출물 검사 |
| R2.3 | AC-6, AC-7 | CMD-3의 cap·shared budget 검사 |
| R2.4 | AC-8 | CMD-12의 authoritative hydration 산출물 검사 |
| R2.5 | AC-9 | CMD-3의 association/role 분리 검사 |
| R2.6 | AC-10 | CMD-12의 injection end-to-end 검사 |
| R3.1 | AC-11, AC-12, AC-37, AC-38 | CMD-6의 analyzer 실행, CMD-12의 schema·fresh generator 검사, CMD-4의 merged generator 보존 검사 |
| R3.2 | AC-13 | CMD-3의 origin observation·hash 검사 |
| R3.3 | AC-14 | CMD-4의 global identity 양방향 병합 검사 |
| R3.4 | AC-15, AC-16 | CMD-8의 default 회귀와 CMD-4의 explicit-only 검사 |
| R3.5 | AC-17, AC-18 | CMD-4의 멱등 append와 CMD-7의 실제 prefix 검증 |
| R3.6 | AC-19 | CMD-4의 projection/history/unknown-value 검사 |
| R4.1 | AC-20 | CMD-12의 실제 manifest schema·provenance 검사 |
| R4.2 | AC-21, AC-22 | CMD-3의 resume/fingerprint 검사 |
| R4.3 | AC-23, AC-24 | CMD-3의 partial/failed/exit 검사 |
| R4.4 | AC-25 | CMD-3의 atomic output failure 검사 |
| R4.5 | AC-39 | CMD-3의 manifest discriminator·tracker identity 사전 거부 검사 |
| R5.1 | AC-26 | CMD-2의 public/private fixture·artifact 검사 |
| R5.2 | AC-27 | CMD-12의 실제 runner/side-effect 검사 |
| R6.1 | AC-28 | CMD-1의 canonical-byte mutation, CMD-11의 신규 revision, CMD-8의 형제 revision 회귀 검사 |
| R6.2 | AC-29, AC-36 | CMD-1의 stdlib suite와 CMD-5의 system validator |
| R6.3 | AC-30, AC-31, AC-32 | 행동 평가 문서와 CMD-12의 RED/safety end-to-end 검사 |
| R6.4 | AC-33, AC-34, AC-35 | CMD-8, CMD-9, CMD-10의 형제 전체 suite |
| R6.5 | AC-40 | CMD-2의 AC→exact unittest ID→filter 매핑 meta-test와 verbose 실행 증거 |

## Architecture

신규 스킬은 다음 경계를 가진다.

1. `SKILL.md`는 호출 조건, 입력 확인, 안전 경계, script/reference 실행 순서, analyzer handoff만 설명한다. `agents/openai.yaml`은 같은 의미의 UI metadata만 가진다.
2. 신규 collection contract는 corpus/manifest/recollection 규칙을, GitHub REST contract는 Issue/comment endpoint, Link pagination, association, retry/budget 규칙을 한 번씩만 정의한다.
3. 신규 Python script는 CLI validation, Issue와 comment 수집, PR reference 정규화, tracker observation/manifest 생성, checkpoint와 원자 저장을 맡는다. GitHub transport는 형제 `GitHubClient.get_json`의 상대 endpoint·page-number·adapter-owned `per_page=100` 계약을 변경 없이 재사용한다. curated pagination layer만 원문 `rel="next"` URL을 provenance로 저장하고 endpoint/query/expected page를 검증해 `params={"page": expected}`로 번역한다. PR hydration과 identity 병합도 형제 collector 모듈을 재사용한다.
4. 형제 collector의 변경은 병합 함수의 `source_policy`에만 한정한다. 이 option은 validation, incoming coalescing, matched record append, new record append까지 같은 값으로 전달되어 한 경로라도 암묵적 recent synthesis로 되돌아가지 않게 한다. 형제 transport와 `references/github-rest-contract.md`는 수정하지 않는다.
5. analyzer는 변경하지 않고 외부 호환성 oracle로 사용한다. 신규 tests는 fake GitHub 응답으로 실제 CLI와 파일 산출을 실행하며, committed synthetic expected corpus를 analyzer subprocess에 넘긴다.
6. 행동 평가는 deterministic unit/integration suite와 분리한다. 독립 Codex 컨텍스트가 `SKILL.md`의 실제 지시를 따라 synthetic fixture를 처리한 결과를 평가 문서에 기록한다.

새 스킬의 최소 예상 파일 맵은 `SKILL.md`, `agents/openai.yaml`, `references/collection-contract.md`, `references/github-rest-contract.md`, `scripts/collect_curated_contribution_prs.py`, `tests/test_collect_curated_contribution_prs.py`, 필요한 `tests/fixtures/` JSON, `evals/behavioral-eval.md`다. fixture와 eval은 허용 산출물이지만 six-file revision 입력은 아니다. 형제 쪽 변경은 `references/collection-contract.md`, `scripts/collect_recent_closed_prs.py`, `tests/test_collect_recent_closed_prs.py` 세 경로에 한정한다. 실제 계획 단계에서 불필요한 파일은 만들지 않는다.

## Interfaces and data flow

대표 CLI 형태는 다음 의미를 가진다. 정확한 option spelling은 계획에서 `--help` 계약 테스트와 함께 고정하되 의미를 바꾸지 않는다.

```text
python3 scripts/collect_curated_contribution_prs.py collect \
  --tracker-repo OWNER/REPO --issue NUMBER --max-prs N \
  --request-budget N --output CORPUS.json --manifest MANIFEST.json \
  [--existing-corpus CORPUS.json --existing-manifest MANIFEST.json \
   --resume-run-id RUN_ID]
```

데이터 흐름은 caller inputs → local validation/fingerprint와 existing-manifest discriminator 확인 → authenticated read-only preflight → Issue core → Link 존재 확인·next URL provenance 저장·page query 검증 → 형제 adapter의 page 요청 → 전역 comment ID 순서 확인 → ordered PR references → capped unique submissions → authoritative PR hydration → tracker source observations → `merge_corpus(..., source_policy="explicit-only")` → atomic corpus checkpoint → manifest checkpoint/finalization → analyzer validation 순서다.

Issue/comment payload의 body는 UTF-8 문자열 bytes로 SHA-256하고, raw body는 evidence로 보존될 수 있으나 어떤 control field도 만들지 않는다. tracker source metadata는 source key, Issue identity, collection method처럼 이후 변경되지 않을 값만 가진다. run-specific page/request/gap 정보는 manifest에, comment edit provenance는 source observations에 둔다.

동일 PR이 먼저 recent corpus에 있으면 기존 envelope `generated_by`, source 순서와 metadata를 그대로 두고 tracker source를 뒤에 append한다. tracker corpus가 먼저이고 후속 recent collector가 실제 검색 관측을 가져오면 기존 tracker prefix 뒤에 recent source를 append한다. curated-only PR에는 recent source가 생기지 않는다. fresh corpus만 curated name/revision을 envelope에 쓰고, 병합 시 현재 curated name/revision은 manifest run과 새 tracker source metadata에 둔다. 기존 tracker source metadata는 갱신하지 않는다. analyzer `--existing`이 이전 source keys, source metadata, observations, state history를 exact prefix로 확인한다.

## Failure behavior

- CLI/schema/resume 또는 existing-manifest discriminator 입력 오류는 network와 destination 변경 전에 stderr 요약과 종료 코드 2를 반환한다.
- retry 가능한 rate-limit/transport/5xx는 형제 transport의 bounded retry와 shared budget을 따른다. budget을 다 쓰면 새 요청을 시작하지 않는다.
- `rel="next"`가 없으면 정상 종료한다. next URL의 endpoint/query/page 검증 실패나 comment ID 중복·역행에서는 다음 요청을 추측하지 않고, 유효 record가 있으면 원문 URL·사유를 남긴 manifest와 corpus checkpoint를 보존해 partial/종료 코드 3으로 끝낸다.
- 선언한 capped scope와 evidence가 gap 없이 처리되면 manifest complete와 종료 코드 0으로 끝낸다.
- Issue/comment pagination이나 일부 PR hydration 실패 뒤 유효 record가 있으면 corpus와 manifest checkpoint를 보존하고 partial/종료 코드 3으로 끝낸다.
- global preflight 실패 또는 유효 record 없는 수집 실패는 이전 corpus를 손상하지 않고 failed manifest/종료 코드 4를 반환한다.
- 404를 포함한 access failure는 endpoint/status를 redacted diagnostic과 failed scope에 남기고 identity/state를 추측하지 않는다.
- atomic replacement가 실패하면 이전 destination bytes를 유지하고 오류를 성공이나 complete로 바꾸지 않는다.
- analyzer validation 실패 시 산출물을 자동 수선·downgrade하지 않고 호환되지 않는 artifact와 실패 이유를 보고한다.

## Security and risk

가장 큰 정확성 위험은 출처 위조, append-only history 손상, 불완전 수집의 complete 오보고다. 명시적 `source_policy`, analyzer `--existing`, manifest의 page/request/gap provenance와 종료 코드로 통제한다. 가장 큰 보안 위험은 원격 텍스트의 prompt injection과 인증된 private 원본의 public fixture 유출이다. 모든 control input은 caller/CLI에서만 받고, fake runner의 exact argv·side effect 검사와 독립 행동 평가, synthetic fixture 검사로 통제한다.

GitHub token은 `gh`가 관리하며 script가 읽거나 출력하지 않는다. retry/diagnostic에는 credential과 conditional header 값을 넣지 않는다. repository에 저장되는 예제는 모두 합성 데이터이며 실제 tracker, 참가자, 멘토, private roster를 사용하지 않는다. 수집 결과 자체는 private일 수 있으므로 사용자가 지정한 로컬 경로 밖으로 복사하거나 공용 문서에 인용하지 않는다.

## Test strategy

테스트는 test count가 아니라 observable contract를 기준으로 한다. 신규 suite는 fake `gh api` runner와 temporary directory를 사용해 CLI argv, Link pagination, budget, JSON bytes, manifest status와 exit code를 검사한다. integration fixture는 Issue core, 편집·중복·주입·access/pagination failure, malformed/cursor/page-mismatch Link, comment ID 역행, authoritative PR facts, existing recent corpus와 foreign manifest를 포함하고 fresh collection, same-input recollection, edited recollection, 양방향 merge를 실제로 실행한다. 생성된 corpus는 analyzer validator를 subprocess로 통과시킨다.

변경 전 baseline은 형제 세 suite가 각각 110/30/62 tests로 통과했다는 회귀 출발점일 뿐, 변경 후 총 개수 고정 조건이 아니다. 변경 후에는 신규 suite와 세 형제 전체 suite 모두 종료 코드 0이어야 한다. 필터 명령은 `-v`로 실행해 AC에 선언된 exact method ID가 모두 `ok`인지 확인한다. Python 3.14.7 실측에서 무매칭은 `NO TESTS RAN`과 종료 코드 5이므로 실패이며, 일부 무관 test만 매칭되어 종료 코드 0인 경우도 필수 exact ID가 빠지므로 실패다. pytest는 설치되어 있지 않고 CI 설정도 없으므로 `unittest`만 사용하며 type check/lint/build는 이 Python skill 저장소에 별도 설정이 없어 not applicable이다.

### 판정 명령 표

| ID | 명령 | 통과 조건 |
|---|---|---|
| CMD-1 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_codex/skills/collecting-curated-contribution-prs/tests -t dot_codex/skills/collecting-curated-contribution-prs/tests -p 'test_*.py'` | 종료 코드 0 |
| CMD-2 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -v -s dot_codex/skills/collecting-curated-contribution-prs/tests -t dot_codex/skills/collecting-curated-contribution-prs/tests -p 'test_*.py' -k contract` | 종료 코드 0이고 AC-1·AC-2·AC-3·AC-26·AC-40에 선언된 exact test ID가 모두 `ok`; `NO TESTS RAN`/종료 코드 5 또는 필수 ID 누락은 실패 |
| CMD-3 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -v -s dot_codex/skills/collecting-curated-contribution-prs/tests -t dot_codex/skills/collecting-curated-contribution-prs/tests -p 'test_*.py' -k collection` | 종료 코드 0이고 AC-4·AC-6·AC-7·AC-9·AC-13·AC-21·AC-22·AC-23·AC-24·AC-25·AC-39에 선언된 exact test ID가 모두 `ok`; `NO TESTS RAN`/종료 코드 5 또는 필수 ID 누락은 실패 |
| CMD-4 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -v -s dot_codex/skills/collecting-curated-contribution-prs/tests -t dot_codex/skills/collecting-curated-contribution-prs/tests -p 'test_*.py' -k merge` | 종료 코드 0이고 AC-14·AC-16·AC-17·AC-19·AC-38에 선언된 exact test ID가 모두 `ok`; `NO TESTS RAN`/종료 코드 5 또는 필수 ID 누락은 실패 |
| CMD-5 | `/opt/homebrew/bin/python3 /Users/lee-kyu-hwan/.codex/skills/.system/skill-creator/scripts/quick_validate.py dot_codex/skills/collecting-curated-contribution-prs` | 종료 코드 0과 `Skill is valid!` 출력 |
| CMD-6 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 dot_codex/skills/analyzing-open-source-pr-patterns/scripts/validate_corpus.py dot_codex/skills/collecting-curated-contribution-prs/tests/fixtures/expected-corpus.json` | 종료 코드 0과 validated record 수 출력 |
| CMD-7 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 dot_codex/skills/analyzing-open-source-pr-patterns/scripts/validate_corpus.py dot_codex/skills/collecting-curated-contribution-prs/tests/fixtures/recollected-corpus.json --existing dot_codex/skills/collecting-curated-contribution-prs/tests/fixtures/initial-corpus.json` | 종료 코드 0과 append-only validation 성공 출력 |
| CMD-8 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_codex/skills/collecting-recent-closed-prs/tests -t dot_codex/skills/collecting-recent-closed-prs/tests -p 'test_*.py'` | 종료 코드 0; 기존 동작과 six-file revision 회귀 포함 |
| CMD-9 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_codex/skills/analyzing-open-source-pr-patterns/tests -t dot_codex/skills/analyzing-open-source-pr-patterns/tests -p 'test_*.py'` | 종료 코드 0 |
| CMD-10 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_codex/skills/verifying-open-source-contribution-candidates/tests -t dot_codex/skills/verifying-open-source-contribution-candidates/tests -p 'test_*.py'` | 종료 코드 0 |
| CMD-11 | `sh -c 'set -o pipefail; PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 dot_codex/skills/collecting-curated-contribution-prs/scripts/collect_curated_contribution_prs.py --print-revision | rg -x "sha256:[0-9a-f]{64}"'` | 종료 코드 0이고 출력이 revision 형식과 정확히 일치 |
| CMD-12 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -v -s dot_codex/skills/collecting-curated-contribution-prs/tests -t dot_codex/skills/collecting-curated-contribution-prs/tests -p 'test_*.py' -k end_to_end` | 종료 코드 0이고 AC-5·AC-8·AC-10·AC-12·AC-20·AC-27·AC-31·AC-32·AC-37에 선언된 exact test ID가 모두 `ok`; `NO TESTS RAN`/종료 코드 5 또는 필수 ID 누락은 실패 |

양성 검사는 complete/종료 코드 0 fixture의 fresh collection과 analyzer handoff다. 음성 검사는 invalid input, unknown source policy, changed fingerprint resume, foreign manifest, missing·malformed·cursor·page-mismatch Link, comment ID 역행, malformed payload, access/preflight/replace failure다. mutation-style 대조는 explicit-only 호출에서 tracker-only PR에 recent source를 삽입하거나 기존 envelope generator 또는 source metadata/order를 바꾸면 CMD-4/CMD-7이 실패하고, injection text를 argv/path/status에 반영하면 CMD-12가 실패하는지 확인한다.

## Decisions

### D1. 기존 merger에 기본 호환 source policy를 추가한다

선택: 형제 `merge_corpus`에 `recent-closed` 기본값과 `explicit-only` 값을 갖는 keyword-only `source_policy`를 추가하고 curated 호출은 후자를 사용한다.

대안 1인 별도 curated merger 복제는 identity, ID allocation, alias, prefix 로직이 갈라져 장기 drift 위험이 크다. 대안 2인 merge 후 recent source 삭제는 기존 source prefix를 훼손하고 위조된 관측을 잠시라도 만들어 검증하기 어렵다. 선택안은 기존 호출을 보존하면서 결함 지점인 validation/append synthesis만 명시적으로 제어한다.

### D2. corpus 1.0.0과 manifest 2.0.0 envelope를 재사용한다

새 corpus schema를 만들지 않고 analyzer가 이미 강제하는 1.0.0을 그대로 쓴다. manifest는 형제의 append-only `records` 2.0.0 envelope와 run/fingerprint/resume 개념을 재사용하되, curated generator·collection method·tracker identity discriminator와 tracker/comment 전용 provenance를 강제한다. 같은 schema version은 호환성의 충분조건이 아니며 별도 manifest framework나 암묵적 migration은 만들지 않는다.

### D3. tracker source는 Issue identity로 namespace한다

고정 단일 `tracker-issue-comments` key는 서로 다른 tracker Issue가 같은 PR을 참조할 때 source metadata 충돌을 만든다. source key를 Issue node ID에서 결정적으로 파생하고 body/comment origin은 observation에서 구분한다. source metadata는 immutable하게 두고 run별 request/page 정보는 manifest에 둔다.

### D4. 재수집 관측 identity는 원격 객체 identity와 content version으로 정한다

댓글은 comment node ID + updated timestamp + body SHA-256, Issue 본문은 Issue node ID + updated timestamp + body SHA-256으로 deduplicate한다. run ID는 provenance로 보존하지만 dedup key에 넣지 않아 unchanged new run이 같은 관측을 복제하지 않는다. edit는 이전 observation 뒤에 새 content version을 append한다.

### D5. PR evidence hydration은 형제 구현을 재사용한다

트래커 collector가 PR core/state/identity/role 및 분석 evidence를 다시 구현하지 않는다. 검증된 형제 transport와 hydration을 재사용해 corpus 품질과 role/state 의미를 맞추고, tracker 고유 책임은 Issue/comment 수집, reference 분류, source observation, manifest에 둔다.

### D6. revision은 경로·framing 계약을 고정하고 digest 값은 고정하지 않는다

형제 collector의 canonical six paths와 framing/recalculation은 유지한다. 이번 source contract/script/test 변경은 계산된 digest를 정당하게 바꾸므로 baseline digest 자체를 기대값으로 두지 않는다. 신규 skill도 같은 방식의 source-derived revision을 사용한다.

### D7. Link는 권위 신호와 검증 provenance로 쓰고 형제 adapter에는 page만 전달한다

선택: `rel="next"`의 존재가 다음 요청 여부를 결정한다. curated layer는 원문 URL을 보존하고 host·comments endpoint·query가 page 기반인지와 page가 정확히 현재 + 1인지 검증한 뒤, 형제 adapter에 상대 endpoint와 `params={"page": expected}`만 전달한다. adapter가 `per_page=100`을 소유하므로 caller가 중복 전달하지 않으며, payload 길이는 pagination 판단에 쓰지 않는다. 검증 불가 Link와 comment ID 중복·역행은 추측 대신 partial gap이다.

대안인 형제 `get_json`의 절대 URL 추적 지원은 현재 endpoint allowlist와 caller-page/adapter-per-page 계약을 바꾸고 형제 `references/github-rest-contract.md`까지 변경 범위를 넓혀야 하므로 기각한다. curated 전용 transport 복제도 retry·budget·redaction drift를 만들므로 기각한다. 선택안은 형제 transport 문서와 코드를 그대로 두고 신규 script/reference/test 안에서 구현 가능하다.

### D8. corpus 생성자 provenance와 manifest 호환성을 분리한다

fresh corpus는 curated name/revision을 envelope에 기록한다. existing corpus 병합은 기존 envelope `generated_by`를 보존해 기존 record의 생성자를 오기하지 않고, 이번 curated 실행의 name/revision은 manifest run과 새 tracker source metadata에 기록한다. 기존 tracker source metadata는 현재 revision으로 덮어쓰지 않는다. manifest는 envelope generator뿐 아니라 exact collection method와 normalized caller tracker identity까지 모두 맞아야 append/resume할 수 있어, 형제 manifest와 다른 tracker manifest의 우연한 혼합을 막는다.

<!-- strict-only:start -->

This block is required only for strict work. Any inapplicable subsection must be removed for non-strict work; within strict work, mark it as not applicable with a reason before review.

### Threat and trust boundaries

신뢰 경계는 (1) caller가 직접 준 repository/Issue/cap/budget/output/resume inputs, (2) 로컬 skill source와 deterministic script, (3) 인증을 보유한 `gh` process, (4) 비신뢰 GitHub Issue/comment/PR 응답, (5) private일 수 있는 로컬 corpus/manifest 사이에 있다. GitHub 응답의 URL과 text는 evidence일 뿐 실행 제어가 아니다. 공격자는 댓글에 shell pipeline, output redirect, 권한 주장, complete 강제 문구를 넣거나 pagination 실패·cursor Link·thread mutation을 유도할 수 있다. 통제는 shell 없는 argv 실행, caller-only control fields, GET allowlist, Link endpoint/query/page 검증, 전역 comment ID 순서 검증, shared budget, redacted diagnostics, explicit source policy, analyzer prefix validation, synthetic eval fixture다.

출처 위조는 데이터 무결성 threat다. `explicit-only` 경로가 incoming source 외 출처를 만들지 않는다는 양방향 검사와 `--existing` 비교를 high-risk gate로 둔다. private data disclosure는 confidentiality threat다. runtime artifact와 repository fixture/document 경계를 나누고 credential/private marker scan 및 독립 평가 evidence를 요구한다.

### Authorization and tenant isolation

GitHub authorization은 호출자의 기존 `gh` authentication이 읽을 수 있는 범위로 제한하며 skill이 scope를 확대하거나 token을 직접 다루지 않는다. tracker `author_association`은 그 tracker repository 문맥에만 유효하고 upstream 권한으로 전이하지 않는다. GitHub 쓰기는 어떤 권한 상태에서도 금지한다.

다중 tenant 서비스는 아니므로 tenant isolation은 not applicable이다. 다만 서로 다른 tracker Issue의 데이터가 한 corpus에 결합될 수 있으므로 source key를 Issue node ID로 namespace하고, existing manifest는 curated generator·collection method·caller tracker identity가 모두 일치할 때만 받아 다른 tracker run을 혼합하지 않는다. 명시적으로 제공된 existing corpus 외 다른 run/artifact를 자동 탐색하지 않는다.

### Migration, compatibility, and rollback

기존 corpus/manifest schema migration은 not applicable이다. 신규 collector는 corpus 1.0.0과 manifest 2.0.0을 처음부터 쓰며 지원하지 않는 version뿐 아니라 같은 version의 foreign manifest도 discriminator로 명시적으로 거부한다.

호환성 핵심은 형제 `merge_corpus` option 생략 시 기존 `recent-closed` 동작, 기존 six-file revision framing, analyzer append-only 계약이다. rollback trigger는 기존 collector 회귀, explicit-only 출처 위조, analyzer prefix 실패, private fixture 유출이다. 구현 rollback은 신규 skill과 형제 source-policy 변경을 되돌리는 것이며 자동 배포·schema backfill은 없다. 이미 생성된 artifact는 삭제하거나 rewrite하지 않고 해당 skill revision과 failure/partial 상태를 근거로 사용 중지한다.

### Failure recovery and observability

manifest가 run ID/fingerprint, generator와 collection method, tracker identity, request events/count, 요청 page, 원문 next URL과 파싱·검증 결과, comment ID 범위, retries, cap counts, PR outcomes, failed scopes, timestamps, warnings와 final status의 정본이다. stderr는 secret이 제거된 간결한 오류와 exit code 의미를 제공한다. checkpoint는 안전하게 저장된 corpus와 동일 run manifest를 함께 남겨 exact fingerprint resume이 이어받게 한다.

별도 alert/metrics/traces backend는 로컬 CLI skill이므로 not applicable이다. 대신 exit code 0/2/3/4, manifest final status, Link validation과 failed scopes, analyzer stderr, verbose exact test ID transcript가 탐지·진단 신호다. partial은 사람이 놓치기 어렵게 최종 사용자 요약의 inventory보다 먼저 표시한다.

### High-risk end-to-end verification

고위험 경로는 synthetic tracker thread를 fresh corpus로 수집한 뒤 existing recent corpus와 병합하고, unchanged와 edited payload로 재수집하며, reverse-order merge·malformed/cursor/page-mismatch Link·comment ID 역행·foreign manifest를 수행하는 CMD-12 → CMD-6 → CMD-7 → CMD-8 순서다. 증거는 실제 temporary corpus/manifest bytes와 CLI exit codes, fresh/merged `generated_by`, next URL/page provenance, committed expected corpus/recollected fixtures의 analyzer 출력, fake runner argv/side effects, 양방향 source arrays, 형제 suite transcript다.

다음 중 하나라도 발생하면 완료를 중단한다: tracker-only record에 `recent-closed`가 생김, merged envelope generator나 기존 source metadata/order/history prefix가 바뀜, unchanged observation이 중복됨, edited observation이 append되지 않음, role이 tracker association으로 승격됨, Link/page/order gap이 complete가 됨, foreign manifest가 수락됨, injection text가 control field나 실행에 들어감, 필수 exact test ID가 실행되지 않음, validator 또는 전체 형제 suite가 비영 종료. 라이브 tracker 실행은 이 gate에 포함하지 않는다.

### No production mutation confirmation

자동 workflow에는 production mutation이 없다. GitHub에는 인증된 GET만 보내고, repository source와 synthetic tests 및 호출자가 지정한 로컬 corpus/manifest만 변경 대상이다. Issue/PR/comment/review/label/branch 쓰기, push, 배포, 전역 설치본 변경, live tracker 수집은 수행하지 않는다.

<!-- strict-only:end -->
