# Quality Goal Specification

- Task ID: 20260915T065141Z-80-post-review-hardening-curated-contrib-52ae436a
- Mode: strict
- Status: draft
- Created: 2026-09-15
- Updated: 2026-09-15
- Source goal: #80 post-review hardening: curated contribution PR collector의 보안·페이지네이션·manifest·분류·원자성 결함 수정

## Problem and context

`dot_codex/skills/collecting-curated-contribution-prs/`는 트래커 Issue의 비신뢰 텍스트에서 PR URL을 찾고, GitHub REST 응답을 hydration한 뒤 corpus 1.0.0과 append-only manifest 2.0.0을 쓰는 로컬 CLI 스킬이다. 기존 #80 Spec과 Plan은 원격 텍스트 비활성화, `Link rel="next"` 기반 페이지네이션, append-only manifest, 원자 저장, resume, 형제 collector의 hydration·병합 계약 재사용을 의도했다.

2026-09-15의 읽기 전용 최소 하네스 실행 결과는 `.claude/quality-state/20260915T065141Z-80-post-review-hardening-curated-contrib-52ae436a/repro/REPRODUCTION-RECORD.md`가 정본이다. 여기서 F1, F2, F3a~F3d, F4~F8, R1~R5가 재현되었고, 추가 대조에서 A1의 curated script 내 API version 폴백 리터럴 3곳과 형제 script의 `API_VERSION` 정본이 확인되었다. 결함은 비신뢰 텍스트가 API 경로를 조종하는 보안 문제, 마지막 댓글 페이지를 partial로 만드는 페이지네이션 문제, 제출/예시·공지 분류 오판, manifest 이력·필드·경고 손실, resume/corpus 불일치 은폐, run 범위 판정 오류, hydration 요청 낭비, 임시 파일 잔존, CLI 발견성 및 배포 artifact 이동성 저하를 만든다.

F4에 대해서는 후처리 `ValueError` 핸들러에 도달했을 때 기존 두 run이 한 실패 run으로 대체되는 데이터 손실이 재현되었다. 반면 클라이언트 수준 `ValueError`는 `collect()`가 잡아 기존 이력을 보존했다. 그러므로 이 Spec은 특정 예외가 핸들러에 도달한다고 가정하지 않고, 핸들러가 호출된 모든 경우의 append-only 보존만 계약한다.

현재 대상 경로들은 quality-goal의 `initial_dirty_paths`에 포함되어 있다. 일반 규칙과 달리 이 작업은 그 경로 자체를 고쳐야 한다. 작업 전 바이트는 `.claude/quality-state/20260915T065141Z-80-post-review-hardening-curated-contrib-52ae436a/baseline-snapshot/`에 있고, 대응 SHA-256 목록은 `.claude/quality-state/20260915T065141Z-80-post-review-hardening-curated-contrib-52ae436a/baseline-hashes.txt`에 있다. 따라서 구현 변경 판정은 Git 기준 상태만이 아니라 이 snapshot 대비 바이트 diff를 정본으로 삼는다.

## Goals

- 재현된 17개 결함 각각을 독립적인 최소 `unittest`로 먼저 RED 고정한 뒤 한 원인씩 GREEN으로 만든다.
- 원격 텍스트, 응답 헤더, resume 입력, manifest 이력 및 로컬 출력에 대한 기존 #80 안전·데이터 무결성 약속을 코드가 실제로 지키게 한다.
- corpus/manifest schema, exit-code 의미, 기존 CLI spelling, 형제 merger의 기본 동작과 analyzer/verifier 호환성을 보존한다.
- 배포되는 스킬 artifact가 사용자 홈 경로나 실제 저장소·인물·비공개 데이터를 포함하지 않게 한다.
- initial-dirty 예외를 baseline snapshot 대비 diff로 통제하고 #80 감사 문서 여섯 개를 바이트 동일하게 보존한다.

## Non-goals

- `canonicalize_curated_state_history`가 `state_history` 없는 record를 통과시킨다는 주장은 최소 하네스로 재현되지 않았으므로 제외한다.
- `except OSError`가 revision 입력 누락을 exit 4로 오분류한다는 주장은 재현되지 않았으므로 제외한다.
- `persist_outputs` 복원 실패 시 corpus/manifest 불일치 주장은 결함 주입이 작동하지 않아 예외 자체가 발생하지 않았고, 동작이 반증된 것이 아니라 근거가 없는 상태이므로 제외한다.
- `--existing-corpus`의 JSON 내용이 `null`일 때 기존 corpus가 덮인다는 주장은 재현되지 않았으므로 제외한다.
- 예산 소진이 세 가지 `kind`로 갈린다는 주장은 재현되지 않았으므로 제외한다.
- 테스트 revision fixture의 13개 변이가 생존한다는 주장은 재현되지 않았으므로 제외한다.
- `collect_repository_hits`, search, partition, 형제 GitHub REST 계약, analyzer, candidate verifier, main, 다른 worktree, `~/.codex` 또는 `~/.claude` 전역 설치본의 기능 변경
- corpus/manifest schema migration, 새 외부 의존성·CI 설정, live GitHub 호출, 실제 tracker 실행, GitHub 쓰기, 배포
- 확인된 결함과 관계없는 리팩터링, 새 수집 정책, 사용자 설정형 분류 문법 또는 더 넓은 문맥 추론의 도입
- F4 후처리 핸들러에 도달하는 특정 자연 발생 트리거를 새로 증명하는 일

## Requirements

- **R1.1** 모든 원격 PR URL에서 추출한 repository identity는 `--tracker-repo`와 동일한 canonical `OWNER/REPO` 검증을 hydration 또는 API endpoint 조립 전에 통과해야 한다. `.`·`..` path segment, 빈 segment, 추가 slash 또는 허용 문자 밖의 값은 submission identity가 될 수 없고 API 요청을 만들 수 없으며, sanitized exclusion과 warning으로 관측 가능해야 한다.

- **R2.1** comment response의 Link header가 존재하지만 `rel="next"`가 없고 `rel="prev"` 또는 `rel="first"`만 있으면 정상 마지막 페이지로 판정하고 추가 요청·failed scope·partial 상태를 만들지 않는다. Link header 자체가 없는 정상 종료와는 provenance 상태 및 사유를 구분한다.
- **R2.2** response headers가 지원하는 mapping 형태인지 검사한다. Link key 부재는 정상 종료로 처리하되, `None`이 아닌 list 등 해석 불가능한 header container는 조용히 Link 부재로 축소하지 않고 sanitized warning과 failed scope가 있는 partial gap으로 남긴다.

- **R3.1** URL span을 제거한 normalized label의 첫 token이 `예시` 또는 `공지`이고 그 token 바로 뒤가 label 끝 또는 `:`, `：`, `-`, `–`, `—` 중 하나일 때만 한국어 exclusion으로 일치시킨다. 일반 문장 중간의 키워드는 일치하지 않으므로 “리뷰 예시 스크린샷을 첨부합니다” 다음 줄의 PR은 실제 submission으로 유지하고, `공지:` 같은 기존 한국어 heading은 계속 제외한다.
- **R3.2** URL span을 제거한 normalized label에서 영어 `example|examples`는 ASCII 글자 경계에서만 일치시킨다. `Examples:`와 “Format example (do NOT count this one)” 같은 기존 설명형 example label은 동일한 exclusion으로 처리하되 다른 ASCII 단어에 포함된 부분 문자열은 일치시키지 않는다.
- **R3.3** URL span을 제거한 normalized label에서 영어 `notice|notices`와 `announcement`는 ASCII 글자 경계에서만 일치시킨다. `Notices:`를 포함한 기존 영어 notice/announcement label은 동일한 exclusion으로 처리하되 다른 ASCII 단어에 포함된 부분 문자열은 일치시키지 않는다.
- **R3.4** classification은 각 label에서 URL span을 먼저 제거한 뒤 남은 normalized label만 R3.1~R3.3의 키워드 판정 입력으로 삼는다. label에 issue 등 비-PR URL이 있더라도 그 URL 문자열의 `example` 같은 조각 때문에 뒤의 실제 PR submission을 제외해서는 안 된다.

- **R4.1** post-request processing failure handler가 호출되면 validated existing manifest의 모든 기존 record를 정확한 prefix로 보존하고 새 failed run 하나를 append한다. resume의 기존 동일-run 교체 계약은 바꾸지 않으며, 이 요구사항은 특정 예외 트리거 재현을 전제로 하지 않는다.
- **R4.2** normal, preflight-failed, post-processing-failed run record는 공통 manifest 계약 필드 `run_id`, `request_fingerprint`, `collection_method`, `tracker`, `collection_status`, `started_at`, `completed_at`, `checkpoint`, `api_version`, `client_version`, `skill`, `max_prs`, `request_budget`, `request_count`, `request_events`, `comment_pages`, `reference_counts`, `cap_exclusions`, `reference_exclusions`, `hydration_outcomes`, `warnings`, `failed_scopes`, `preflight`를 모두 가진다. 실패 경로는 필드를 생략해 schema 의미를 약화시키지 않고 사용할 수 없는 값만 명시적 `null` 또는 빈 collection으로 표현한다.
- **R4.3** `collection_status == "complete"`인 run의 resume 재사용 전에는 prior `hydration_outcomes`의 `collected|partial` 항목과 existing corpus의 normalized repository/PR number 및 가능한 node identity를 대조한다. 필요한 record가 없거나 서로 충돌하면 network와 destination 변경 및 `checkpoint_reused` 표시 없이 입력 오류 exit 2로 거부한다.
- **R4.4** manifest `warnings`는 장식용 빈 배열이 아니다. invalid remote identity, 지원하지 않는 header shape, pagination/hydration/budget/processing gap처럼 run을 partial 또는 failed로 만드는 각 recoverable 진단은 sanitized warning과 구조화된 `failed_scopes`가 상호 대응해야 하며 complete run에는 근거 없는 warning이 없어야 한다.

- **R5.1** 한 `collect()` run은 normalized repository별 성공한 metadata 결과 cache와 하나의 shared `license_cache`를 모든 기본 hydration 호출에 공유한다. 같은 repository의 여러 PR은 metadata GET을 반복하지 않고, cache는 다른 run 또는 호출자 사이에서 전역 공유되지 않는다.

- **R6.1** `persist_outputs`의 기존 계약인 serialization, 첫 번째 또는 두 번째 temporary write, replace 실패 시 temporary-file 정리와 기존 corpus/manifest destination-byte 보존은 유지한다. 이번 작업이 새로 계약하고 검증하는 범위는 재현된 두 번째 `_write_temporary` 실패 경로뿐이며, 이때 먼저 생성된 temporary file이 남아서는 안 된다. serialization·첫 번째 write·replace 단계는 기존 동작 보존 대상이지만 이 작업의 검증 범위 밖이고, 미재현 replace 후 restore 실패까지 계약을 확장하지 않는다.

- **R7.1** run status의 usable-evidence 판정은 병합 후 전체 corpus가 아니라 이번 run에서 성공 또는 partial로 생성한 usable selected record만 본다. 기존 corpus만 있고 이번 run의 usable record가 0인 수집 실패는 corpus를 보존하면서 failed/exit 4이며 partial/exit 3으로 승격되지 않는다. 여기서 #80 AC-24의 “usable corpus”는 #80 failure behavior의 “유효 record 없는 수집 실패” 및 Security and risk의 “불완전 수집의 complete 오보고” 방지 의도에 따라 이번 run의 수확을 뜻하며, complete/partial 오보고를 막는 원 계약의 보존이지 축소가 아니다.

- **R8.1** `--print-revision`은 argparse가 소유하는 top-level public option으로 `--help`에 노출되고 기존 단독 호출에서 정확한 `sha256:<64 lowercase hex>` 한 줄과 exit 0을 유지한다. `collect --help`와 기존 collect option spelling은 변하지 않는다.
- **R8.2** curated script는 API version fallback 리터럴을 복제하지 않고 로드된 형제 collector의 `API_VERSION` 한 곳을 정본으로 사용한다. 형제 script의 constant·transport·merge/search/partition 동작은 이 수정 때문에 변경하지 않는다.

- **R9.1** 배포되는 `evals/behavioral-eval.md`는 사용자 홈 절대 경로와 사용자 식별자를 포함하지 않고 두 worktree 기준 절대 경로를 일관된 `<worktree>` placeholder로 치환해 동일 evidence 관계를 보존한다. 이 파일의 변경은 baseline 대비 F8 경로 치환에 한정한다.

- **R10.1** 확인된 F1, F2, F3a~F3d, F4~F8, R1~R5, A1마다 기존 suite에서 가장 작은 단일 원인 테스트를 구현보다 먼저 추가하고, 수정 전 기대된 assertion/error와 함께 실제 RED 종료 코드를 기록한다. 그 뒤 한 원인씩 최소 구현하고 동일 테스트의 GREEN 및 관련 suite GREEN을 기록한다.
- **R10.2** 결함을 탐지하지 못하게 하는 단일 변이를 각 테스트 또는 인접 contract test가 거부하는지 확인한다. 살아 있는 revision/expected-corpus/recollected-corpus fixture를 단순 재생성하거나 assertion을 완화해 behavior 변화를 숨기지 않으며, oracle 변경이 불가피하면 독립적인 실제 behavior 증거와 root 승인을 남긴다.

- **R11.1** 구현 수정 가능 경로는 `dot_codex/skills/collecting-curated-contribution-prs/`의 `SKILL.md`, `agents/openai.yaml`, `references/`, `scripts/`, `tests/`, 그리고 F8에 한정한 `evals/behavioral-eval.md`다. 형제 collector는 필요성이 입증된 merger 영역만 후보지만 현재 설계는 수정하지 않는다. 기존 #80 감사 문서 여섯 개와 나머지 금지 경로는 baseline bytes를 유지하며, 최종 scope는 baseline snapshot 대비 diff로 판정한다.
- **R11.2** 테스트와 새 fixture는 Python 표준 라이브러리 `unittest`, temporary directory, 합성 repository/인물/시각/데이터만 사용한다. 모든 Python 실행은 `PYTHONDONTWRITEBYTECODE=1`을 붙이고 network, credential, private roster, 실제 원문, pytest, jsonschema, dependency install을 사용하지 않으며 curated·형제·analyzer·verifier 회귀 suite를 모두 통과한다.

## Acceptance criteria

- **AC-1** traversal-shaped PR URL을 포함한 합성 원격 본문에서 해당 reference는 invalid exclusion과 warning으로 남고, identity/API call log 어디에도 `..` segment가 없으며 exit/status가 gap을 숨기지 않는다. [실행] (CMD-1 test_ac_01_post_review_remote_repository_validation)
- **AC-2** `rel="prev"`와 `rel="first"`만 있는 합성 Link header는 정상 terminal provenance, 추가 comments 요청 0회, failed scope 0건을 만들며 Link header 부재 provenance와 구분된다. [실행] (CMD-1 test_ac_02_post_review_terminal_link_without_next)
- **AC-3** headers가 list인 합성 response는 header-container gap warning과 failed scope를 남겨 partial이 되고, mapping에서 Link key만 없는 response는 정상 종료가 된다. [실행] (CMD-1 test_ac_03_post_review_unsupported_header_shape)
- **AC-4** F3a의 한국어 일반 서술 “리뷰 예시 스크린샷을 첨부합니다” 다음 줄의 합성 PR은 submission으로 선택되고, normalized label 첫 token 뒤가 label 끝 또는 `:`, `：`, `-`, `–`, `—`인 `예시|공지` table case는 exclusion으로 분류되며 기존 `공지:` heading도 계속 제외된다. [실행] (CMD-1 test_ac_04_post_review_korean_label_boundary)
- **AC-5** F3b의 `Examples:`와 기존 설명형 “Format example (do NOT count this one)” 다음 줄의 합성 PR은 exclusion basis와 함께 `excluded-example-or-notice`로 분류되고, `example|examples`가 다른 ASCII 단어에 포함된 대조 label은 그 부분 문자열만으로 제외되지 않는다. [실행] (CMD-1 test_ac_05_post_review_examples_plural)
- **AC-6** F3c의 `Notices:` 및 ASCII 글자 경계의 `notice|notices|announcement` 다음 줄의 합성 PR은 exclusion basis와 함께 `excluded-example-or-notice`로 분류되고, 해당 문자열이 다른 ASCII 단어에 포함된 대조 label은 그 부분 문자열만으로 제외되지 않는다. [실행] (CMD-1 test_ac_06_post_review_notices_plural)
- **AC-7** F3d의 non-PR issue URL host에 `example`이 있고 같은 label에 합성 PR URL이 있어도 먼저 제거된 URL span은 keyword matching에 참여하지 않아 PR이 submission으로 선택된다. [실행] (CMD-1 test_ac_07_post_review_non_pr_url_label)
- **AC-8** 후처리 핸들러를 직접 도달시키는 합성 test에서 prior run 두 개는 byte-deep-equal prefix로 남고 세 번째 failed run만 append되며 exit 4다. 클라이언트 수준 예외가 이 핸들러에 도달한다는 주장은 test 전제에 포함하지 않는다. [실행] (CMD-1 test_ac_08_post_review_processing_handler_append_only)
- **AC-9** normal, preflight failure, post-processing failure의 합성 run record 모두 caller의 동일 `max_prs`와 공통 필수 key set을 가지며 manifest envelope가 append-only다. [실행] (CMD-1 test_ac_09_post_review_failed_record_field_parity)
- **AC-10** complete prior run의 collected outcome에 대응하는 corpus record를 제거하거나 identity를 충돌시킨 두 resume fixture는 client call 0회, destination byte 변경 0회, `checkpoint_reused` 없음, exit 2가 된다. 일치 fixture는 기존 network-free reuse를 유지한다. [실행] (CMD-1 test_ac_10_post_review_resume_corpus_reconciliation)
- **AC-11** invalid identity, unsupported headers, pagination, hydration, budget, processing 합성 gap 각각은 non-empty sanitized warning과 대응 failed scope를 가지며 complete fixture의 warnings는 비어 있다. [실행] (CMD-1 test_ac_11_post_review_manifest_warnings)
- **AC-12** 같은 normalized repository의 PR 두 개를 기본 hydrator로 처리하면 repository metadata GET은 1회이고 sibling hydration은 동일한 `license_cache` object를 받으며, 두 번째 독립 run은 새 cache를 사용한다. [실행] (CMD-1 test_ac_12_post_review_run_scoped_hydration_caches)
- **AC-13** 두 destination의 기존 bytes를 둔 상태에서 두 번째 temporary write를 실패시키면 예외 뒤 destination bytes와 directory entry set이 실행 전과 같고 orphan temporary file이 0개다. [실행] (CMD-1 test_ac_13_post_review_second_temporary_write_cleanup)
- **AC-14** non-empty existing corpus와 이번 run의 hydration 전부 실패 fixture는 기존 corpus bytes를 보존하고 새 manifest run을 failed, exit 4로 기록한다. 같은 run에서 usable record가 하나라도 생긴 대조 fixture만 partial, exit 3이 될 수 있다. [실행] (CMD-1 test_ac_14_post_review_current_run_usable_records)
- **AC-15** top-level `--help`가 `--print-revision`을 표시하고, 단독 option은 revision 정규식과 정확히 일치하는 한 줄 및 exit 0을 내며 기존 `collect --help` option 집합을 보존한다. 추가 인자가 붙은 `--print-revision` 호출과 자동 접두 축약 `--print-rev` 호출은 변경 전과 동일하게 argparse usage error, exit 2, revision stdout 0줄을 유지한다. [실행] (CMD-1 test_ac_15_post_review_print_revision_help)
- **AC-16** curated script의 AST/텍스트 contract test는 API date fallback 리터럴 0개와 sibling `API_VERSION` 참조를 확인하고, 실행 중 client가 version을 제공하지 않아도 fingerprint/run record가 sibling 정본과 같다. baseline의 형제 script bytes는 변하지 않는다. [실행] (CMD-1 CMD-7 test_ac_16_post_review_shared_api_version)
- **AC-17** 현재 eval 문서는 `/Users/` 및 baseline의 사용자 홈 절대 경로를 0회 포함하고, baseline 문서의 worktree 기준 절대 경로 두 곳을 정확히 `<worktree>`로 치환한 결과와 나머지 bytes가 같다. [실행] (CMD-1 test_ac_17_post_review_portable_eval_paths)
- **AC-18** 17개 결함 test 각각에 대해 test 추가 직후의 exact command, 수정 전 실패 assertion/error, 비영 exit, 최소 구현 뒤 같은 command의 GREEN, 관련 suite GREEN이 순서대로 기록되고 한 결함의 GREEN 전에 다음 원인 구현을 섞지 않는다. [문서] docs/development/2026-09-15-80-post-review-hardening/report.md § 결함별 RED→GREEN 증거 계약
- **AC-19** 각 결함의 핵심 방어를 되돌리는 단일 변이가 대응 test를 실패시키며, revision/expected corpus fixture를 재생성하거나 assertion을 약화한 경우에는 독립 evidence와 root 승인 없이는 GREEN으로 인정하지 않는다. [문서] docs/development/2026-09-15-80-post-review-hardening/report.md § 변이와 oracle 무결성
- **AC-20** baseline snapshot 대비 최종 diff에 허용된 curated 경로와 이 Spec 이외의 새 작업 변경이 없고, eval diff는 F8 portable path 치환에만 한정되며 형제 파일은 baseline과 같다. [실행] (CMD-8)
- **AC-21** 기존 #80 감사 디렉터리의 여섯 문서가 `baseline-hashes.txt`의 SHA-256과 모두 일치한다. [실행] (CMD-7)
- **AC-22** contract test는 stdlib-only, synthetic-only, no-network/no-credential, 허용 파일 집합, 모든 Python command의 bytecode 억제 및 eval F8-only 규칙을 검사하고 skill validator가 성공한다. [실행] (CMD-2 CMD-5 test_ac_22_contract_stdlib_synthetic_packaging)
- **AC-23** 17개 focused tests, curated 전체 suite, 수정하지 않은 형제 collector 전체 suite, analyzer 전체 suite, candidate verifier 전체 suite가 모두 exit 0이고 기존 #80 핵심 merge/pagination/manifest/atomic behavior test가 회귀하지 않는다. [실행] (CMD-1 CMD-2 CMD-3 CMD-4 CMD-6)

## Requirements traceability

This table maps every requirement to acceptance criteria and the judgement method that proves the mapping.

| Requirement | Acceptance criteria | Judgement method |
|---|---|---|
| R1.1 | AC-1 | CMD-1 focused security test |
| R2.1 | AC-2 | CMD-1 focused pagination test |
| R2.2 | AC-3 | CMD-1 focused header-shape test |
| R3.1 | AC-4 | CMD-1 focused Korean boundary test |
| R3.2 | AC-5 | CMD-1 focused plural test |
| R3.3 | AC-6 | CMD-1 focused plural test |
| R3.4 | AC-7 | CMD-1 focused URL-span test |
| R4.1 | AC-8 | CMD-1 direct handler test |
| R4.2 | AC-9 | CMD-1 run-record parity test |
| R4.3 | AC-10 | CMD-1 resume reconciliation test |
| R4.4 | AC-11 | CMD-1 warnings/failed-scope test |
| R5.1 | AC-12 | CMD-1 run-cache call-count/identity test |
| R6.1 | AC-13 | CMD-1 failure-injection persistence test |
| R7.1 | AC-14 | CMD-1 run-local status test |
| R8.1 | AC-15 | CMD-1 CLI help/revision subprocess test |
| R8.2 | AC-16 | CMD-1 source/runtime test; CMD-7 baseline guard |
| R9.1 | AC-17 | CMD-1 baseline-normalized byte comparison |
| R10.1 | AC-18 | Test strategy RED/GREEN evidence review |
| R10.2 | AC-19 | Test strategy mutation/oracle evidence review |
| R11.1 | AC-20, AC-21 | Baseline-snapshot scope diff review; CMD-7 hash guard |
| R11.2 | AC-22, AC-23 | CMD-1, CMD-2, CMD-3, CMD-4, CMD-5, CMD-6 |

## Architecture

수정은 기존 collector의 책임 경계를 유지한 채 결함 지점에 작은 guard와 run-scoped state를 추가한다.

1. **Reference trust gate:** URL 발견과 classification 뒤, identity를 selection key나 endpoint에 넣기 전에 하나의 repository canonicalizer가 CLI와 remote-derived repository를 모두 검증한다. invalid remote reference는 inert exclusion/warning으로만 이동한다.
2. **Pagination state:** header extraction은 `absent`, `present-terminal`, `present-next`, `unsupported-container`를 구분하는 구조화 결과를 만든다. next URL validator는 `present-next`에서만 실행되고, unsupported container만 gap이 된다.
3. **Label classifier:** URL span을 제거한 prose label에 대해 D1에서 root가 승인한 ASCII 글자 경계 및 한국어 첫-token/heading-delimiter 문법을 적용한다.
4. **Run manifest builder:** normal/preflight/processing failure가 동일한 공통-field factory를 사용한다. handler는 이미 읽고 검증한 manifest history에 `_manifest_records` 의미로 새 failed record를 결합한다. warning 생성은 structured failed scope 생성과 같은 지점에서 수행한다.
5. **Resume validator:** network-free complete reuse 전에 prior hydration outcomes와 existing corpus index를 대조한다. 이 단계는 client preflight와 persistence보다 앞선다.
6. **Hydration context:** `collect()` 지역 객체가 repository metadata cache와 shared license cache를 소유하며 default hydrator에 전달한다. module-global cache는 사용하지 않는다.
7. **Persistence staging:** 두 temporary path를 모두 `None`으로 초기화하고 각 생성 직후 동일한 outer cleanup 영역이 소유한다. destination replace/restore 의미는 재현되지 않은 복원 실패까지 확장하지 않는다.
8. **CLI/version and artifact portability:** argparse가 revision option의 발견성을 소유하고, curated runtime은 이미 로드한 sibling module의 `API_VERSION`을 사용한다. eval 변경은 source logic과 분리된 portable path 정규화다.

형제 `collect_recent_closed_prs.py`는 merge area의 통합 경계이지만 이 설계의 A1 해결에는 수정이 필요 없다. 현재 snapshot의 형제 merger 변경은 그대로 소비하고 baseline bytes를 유지한다.

## Interfaces and data flow

Public collect CLI 입력과 exit code 0/2/3/4, corpus 1.0.0, manifest 2.0.0 envelope는 유지한다. top-level `--print-revision`은 기존 동작을 argparse help surface에 정식 등록할 뿐 새 collection option을 추가하지 않는다.

데이터 흐름은 caller CLI validation → sibling load 및 API version 결정 → preflight/resume validation → Issue/comment pagination → reference label classification → remote repository trust gate → capped selection → run-scoped hydration → existing corpus merge → run-local status 계산 → common manifest record 생성 → paired persistence 순서다.

- Invalid remote repository identity는 `reference_exclusions`의 sanitized reason, `warnings`, `failed_scopes`로 흐르고 hydration/API로 흐르지 않는다.
- 한 comment page의 provenance는 header container 상태, Link 존재 상태, next URL/parsed page, validation/failure reason을 구분한다. terminal Link와 absent Link는 모두 정상 종료지만 서로 다른 관측값이다.
- Resume corpus index는 normalized `repository.full_name`과 `pull_request.number`, 가능하면 `pull_request_node_id`로 prior hydration outcome을 확인한다. 불일치는 input error이며 기존 artifact를 반환 성공으로 재사용하지 않는다.
- Warning 문자열은 credential, raw private body, header value 전체를 복사하지 않고 failed scope의 kind와 sanitized reason을 사람이 찾을 수 있게 연결한다.
- Metadata cache key는 normalized repository이고 value는 성공적으로 검증된 response object의 독립 copy다. license cache는 sibling hydration이 기대하는 mutable mapping 한 개를 run 안에서 공유한다.
- Failure run의 `max_prs`는 caller integer를 그대로 기록한다. 값이 없는 선택적 provenance는 `null`/빈 collection을 사용하되 key를 생략하지 않는다.

## Failure behavior

- Remote repository validation failure는 그 문자열로 endpoint를 만들지 않고 해당 reference를 제외하며 run을 warning/failed scope가 있는 partial 또는, usable current-run record가 없으면 failed로 만든다.
- Link header의 정상 부재와 next 없는 terminal header는 요청을 끝낸다. malformed next 또는 unsupported header container는 추가 요청 없이 gap으로 남긴다.
- Complete resume의 corpus 대조 실패는 GitHub request와 output write 전에 exit 2다. 일치하는 resume만 기존 network-free reuse를 수행한다.
- Preflight 및 post-processing failure manifest도 `max_prs`와 공통 필드를 유지한다. post-processing handler는 기존 history를 버리지 않는다.
- Gap이 있고 이번 run에 usable record가 있으면 partial/3, 없으면 failed/4다. 이전 corpus record는 이번 run의 usable 증거로 세지 않는다.
- 두 번째 temporary write를 포함한 staging 실패는 생성된 temporary file을 모두 정리하고 두 destination의 이전 bytes를 유지한 채 OSError를 상위 exit-4 처리에 전달한다.
- 테스트나 analyzer가 실패하면 계약 문서·assertion·fixture를 코드 결함에 맞게 약화하지 않고 구현을 중단한다.

## Security and risk

가장 높은 보안 위험은 원격 URL이 authenticated GitHub client의 endpoint를 조종하는 F1이다. 동일 canonical repository validation을 trust boundary에 두고 call-log negative assertion으로 방어한다. 원격 Issue/comment/PR text와 Link headers는 모두 비신뢰 데이터이며 명령, 파일 경로, authorization, API host/path 또는 success status를 직접 정하지 못한다.

가장 높은 데이터 무결성 위험은 F4의 manifest history 소실, R1의 corpus 불일치 resume 성공, F7의 부분 staging 잔존, R3의 기존 corpus를 이용한 partial 승격이다. baseline prefix 비교, network/write call count, destination bytes와 directory entry 비교, current-run evidence 판정으로 방어한다. Diagnostics는 token, conditional header, private body를 포함하지 않는다.

테스트 및 문서는 합성 데이터만 사용한다. `gh` credential은 기존 sibling transport 바깥으로 노출하지 않으며 이 작업은 GitHub 요청 자체를 실행하지 않는다. 기존 계약과 코드가 충돌하면 안전·append-only·불완전 수집 비성공이라는 #80 의도를 먼저 구현한다. 문서 약화는 대안이 없고 root가 근거를 승인한 경우에만 허용한다.

## Test strategy

17개 focused regression은 `post_review` filter와 AC 번호가 포함된 exact `unittest` method로 작성한다. fake client, `unittest.mock`, `tempfile.TemporaryDirectory`, 합성 payload만 사용하고 live network는 사용하지 않는다. CMD-1 verbose output에서 선언된 17개 exact test가 모두 `ok`인지 확인하며 `NO TESTS RAN`, 0건 선택 또는 필수 ID 누락은 실패다.

### 판정 명령 표

| ID | 명령 | 통과 조건 |
|---|---|---|
| CMD-1 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -v -s dot_codex/skills/collecting-curated-contribution-prs/tests -t dot_codex/skills/collecting-curated-contribution-prs/tests -p 'test_*.py' -k post_review` | 종료 코드 0이고 AC-1~AC-17의 exact test ID 17개가 모두 `ok`; 0건 선택·필수 ID 누락은 실패 |
| CMD-2 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_codex/skills/collecting-curated-contribution-prs/tests -t dot_codex/skills/collecting-curated-contribution-prs/tests -p 'test_*.py'` | 종료 코드 0; 신규 focused/contract tests와 기존 curated suite 모두 통과 |
| CMD-3 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_codex/skills/collecting-recent-closed-prs/tests -t dot_codex/skills/collecting-recent-closed-prs/tests -p 'test_*.py'` | 종료 코드 0; baseline의 sibling behavior 및 merger/source-policy 회귀 통과 |
| CMD-4 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_codex/skills/analyzing-open-source-pr-patterns/tests -t dot_codex/skills/analyzing-open-source-pr-patterns/tests -p 'test_*.py'` | 종료 코드 0; corpus/analyzer 회귀 통과 |
| CMD-5 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 /Users/lee-kyu-hwan/.codex/skills/.system/skill-creator/scripts/quick_validate.py dot_codex/skills/collecting-curated-contribution-prs` | 종료 코드 0과 `Skill is valid!` 출력 |
| CMD-6 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_codex/skills/verifying-open-source-contribution-candidates/tests -t dot_codex/skills/verifying-open-source-contribution-candidates/tests -p 'test_*.py'` | 종료 코드 0; candidate verifier 회귀 통과 |
| CMD-7 | `sh -c 'set -eu; hashes=.claude/quality-state/20260915T065141Z-80-post-review-hardening-curated-contrib-52ae436a/baseline-hashes.txt; sed -n "1,6p" "$hashes" | shasum -a 256 -c -; snapshot=.claude/quality-state/20260915T065141Z-80-post-review-hardening-curated-contrib-52ae436a/baseline-snapshot; for artifact_rel in dot_codex/skills/collecting-recent-closed-prs/references/collection-contract.md dot_codex/skills/collecting-recent-closed-prs/scripts/collect_recent_closed_prs.py dot_codex/skills/collecting-recent-closed-prs/tests/test_collect_recent_closed_prs.py; do cmp "$snapshot/$artifact_rel" "$artifact_rel"; done'` | 종료 코드 0; 감사 문서 6개 hash 일치 및 형제 3개 파일 baseline byte 일치 |
| CMD-8 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -c 'from pathlib import Path; import sys; root=Path.cwd().resolve(); snap=Path("/Users/lee-kyu-hwan/code/dotfiles__worktrees/80-feat-curated-contribution-prs/.claude/quality-state/20260915T065141Z-80-post-review-hardening-curated-contrib-52ae436a/baseline-snapshot"); curated=Path("dot_codex/skills/collecting-curated-contribution-prs"); audit=Path("docs/development/2026-09-10-80-collecting-curated-contribution-prs"); siblings=(Path("dot_codex/skills/collecting-recent-closed-prs/references/collection-contract.md"),Path("dot_codex/skills/collecting-recent-closed-prs/scripts/collect_recent_closed_prs.py"),Path("dot_codex/skills/collecting-recent-closed-prs/tests/test_collect_recent_closed_prs.py")); baseline={p.relative_to(snap) for p in snap.rglob("*") if p.is_file()}; current={p.relative_to(root) for base in (root/curated,root/audit) for p in base.rglob("*") if p.is_file()}|{p for p in siblings if (root/p).is_file()}; changed={p for p in baseline|current if not (snap/p).is_file() or not (root/p).is_file() or (snap/p).read_bytes() != (root/p).read_bytes()}; allowed=lambda p:p in (curated/"SKILL.md",curated/"agents/openai.yaml",curated/"evals/behavioral-eval.md") or any(curated/d in p.parents for d in ("references","scripts","tests")); bad=sorted(map(str,(p for p in changed if not allowed(p)))); eval_rel=curated/"evals/behavioral-eval.md"; source=(snap/eval_rel).read_bytes(); actual=(root/eval_rel).read_bytes(); marker=str(root).encode(); eval_ok=source.count(marker)==2 and actual==source.replace(marker,b"<worktree>") and b"/Users/" not in actual; print("outside_allowlist="+("none" if not bad else ",".join(bad))); print("eval_f8_only="+str(eval_ok)); sys.exit(0 if not bad and eval_ok else 1)'` | 종료 코드 0; snapshot 대비 변경은 curated allowlist 안에만 있고 감사 문서 6개와 형제 3개 파일은 byte-identical이며 eval은 baseline의 두 worktree 절대 경로를 `<worktree>`로 치환한 결과와 정확히 일치 |

#### 결함별 RED→GREEN 증거 계약

각 AC-1~AC-17에 대해 구현자는 task-state의 TDD transcript에 다음을 순서대로 기록한다.

1. test만 추가된 snapshot digest와 exact focused command
2. 실제 비영 exit code 및 해당 결함의 관측 동작과 일치하는 assertion/error
3. 한 원인만 바꾼 implementation diff
4. 동일 focused command의 exit 0과 exact test `ok`
5. CMD-2 및 영향을 받는 CMD-3~CMD-6의 GREEN

수정 전 test가 뜻밖에 통과하거나 다른 이유로 실패하면 RED로 인정하지 않고 fixture/관측점을 바로잡는다. F4는 handler 직접 도달을 사용하고, 특정 client 예외가 handler까지 전파된다는 가정은 하지 않는다.

#### 변이와 oracle 무결성

각 focused test는 최소한 핵심 방어를 제거한 단일 변이—repository 재검증 생략, no-next를 invalid 처리, unsupported header를 absent 처리, keyword 부분문자열 복원, plural 제거, URL span 검사 복원, history 재초기화, `max_prs` 생략, resume corpus 대조 생략, warnings 미추가, cache 재생성, first temporary cleanup 제거, merged-corpus usable 판정 복원, argv 완전일치 special-case 복원, API literal 복원, 절대 경로 복원—에서 실패함을 확인한다.

살아 있는 revision fixture 또는 expected/recollected corpus를 구현 출력으로 단순 재생성하지 않는다. Oracle 변경이 정말 필요하면 변경 전후 semantic diff, 기존 validator 결과, 새 behavior가 원래 #80 안전 계약을 유지한다는 근거와 root 승인을 먼저 기록한다.

#### Baseline-snapshot scope diff

구현 전후 바이트는 다음 absolute 정본을 기준으로 비교한다.

- Snapshot: `/Users/lee-kyu-hwan/code/dotfiles__worktrees/80-feat-curated-contribution-prs/.claude/quality-state/20260915T065141Z-80-post-review-hardening-curated-contrib-52ae436a/baseline-snapshot/`
- Hashes: `/Users/lee-kyu-hwan/code/dotfiles__worktrees/80-feat-curated-contribution-prs/.claude/quality-state/20260915T065141Z-80-post-review-hardening-curated-contrib-52ae436a/baseline-hashes.txt`

최종 verification evidence에는 editable curated subtree의 recursive snapshot diff, CMD-7 결과, `git status --short`, 그리고 이 Spec 파일 외 새 경로가 없다는 allowlist 판정을 포함한다. Eval diff는 두 absolute-path occurrences의 portable placeholder 치환만 허용한다. 감사 문서 여섯 개와 형제 세 파일은 CMD-7로 byte equality를 강제한다. 이 절차는 initial-dirty target을 작업 변경에서 제외하라는 일반 quality-goal 규칙의 명시적 예외이며, snapshot 이전 변경을 현재 작업의 성과로 주장하지 않는다.

Type check, lint, build, browser E2E, live API E2E는 repository에 설정이 없거나 금지된 network가 필요하므로 not applicable이며 통과로 기록하지 않는다.

## Decisions

### D1. 분류 keyword는 URL을 제외한 구조화 label token으로 판정한다 — root 승인 완료

root는 다음 문법을 승인했고 이 Spec의 확정 사항으로 채택한다. classification은 URL span을 먼저 제거한 label을 기준으로 한다. 영어 `example|examples`, `notice|notices`, `announcement`는 앞뒤가 ASCII 글자가 아닌 ASCII 글자 경계에서 판정한다. 한국어는 normalized label의 첫 token이 `예시|공지`이고 바로 뒤가 label 끝 또는 `:`, `：`, `-`, `–`, `—` 중 하나일 때만 일치시킨다.

이 확정 문법에서 F3a “리뷰 예시 스크린샷을 첨부합니다”는 submission, F3b `Examples:`와 F3c `Notices:`는 exclusion, F3d label의 비-PR URL에만 존재하는 keyword는 URL span 제거 뒤 submission이다. 기존 설명형 영어 example label “Format example (do NOT count this one)”과 한국어 heading `공지:`는 계속 exclusion이다. 이 결정은 분류 어휘의 최소 수정이며 사용자 설정형 문법이나 더 넓은 문맥 추론은 범위 밖이다.

대안 1인 punctuation 제거 후 전체 label과 keyword의 정확 일치는 오탐을 가장 적게 만들지만 기존 설명형 example label을 실제 submission으로 바꾸는 회귀 때문에 기각한다. 대안 2인 사용자 설정 keyword/locale grammar는 유연하지만 새 CLI/manifest 정책과 훨씬 넓은 테스트가 필요해 현재 재현 범위를 넘으므로 기각한다.

### D2. Header/Link 판정은 네 상태의 구조화 결과를 사용한다

선택안은 `absent`, `present-terminal`, `present-next`, `unsupported-container`를 명시하는 작은 parser 결과다. 단일 sentinel이나 `None`은 F2/R2의 원인이 된 의미 축소를 반복한다. exception-only 대안은 정상 terminal Link까지 예외 흐름에 섞는다. 네 상태는 provenance, request decision, warning/failed-scope 생성을 같은 사실에서 파생시켜 조용한 partial과 거짓 partial을 모두 막는다.

### D3. Manifest 공통 필드와 warning은 하나의 run-record builder에서 만든다

선택안은 normal/preflight/processing failure가 공통 base record를 만들고 각 경로가 결과 필드만 채우는 것이다. 세 dict literal을 각각 보강하는 대안은 F5/A1처럼 조용히 drift할 가능성이 높다. 별도 manifest schema migration은 재현 범위를 넘고 기존 2.0.0 소비자를 불필요하게 흔드므로 채택하지 않는다.

### D4. API version은 형제 constant를 소비하고 형제 파일은 수정하지 않는다

선택안은 이미 load된 sibling module의 `API_VERSION`을 fingerprint와 failure record fallback에 사용하는 것이다. 새 shared module을 만드는 대안은 packaging/revision 범위를 넓히고, curated constant를 하나만 남기는 대안은 여전히 정본 drift를 허용한다. 따라서 A1을 curated 경로 안에서 고치며 baseline의 형제 merge area는 byte-identical로 보존한다.

### D5. Hydration cache는 `collect()` 수명의 지역 context다

선택안은 normalized repository metadata cache와 sibling-compatible license mapping을 closure/context로 한 번 만들고 default hydration마다 전달하는 것이다. module-global cache는 호출자·run 간 데이터가 섞이고 test isolation을 깨뜨린다. hydrator signature를 public하게 확장하는 대안은 injected hydrator 호환성을 불필요하게 바꾸므로 채택하지 않는다.

### D6. Initial-dirty 대상은 baseline snapshot으로 소유권을 분리한다

일반 quality-goal 규칙대로 initial dirty 전체를 제외하면 이번 target을 수정할 수 없고, Git base diff만 사용하면 이전 #80 작업과 이번 hardening을 구분할 수 없다. 선택안은 curated 허용 경로만 snapshot 대비 변경으로 인정하고 감사 문서 및 형제 경로를 byte equality로 고정하는 것이다. 별도 worktree 복사는 사용자가 지정한 작업 위치와 state 정본을 갈라놓으므로 사용하지 않는다.

<!-- strict-only:start -->

This block is required only for strict work. Any inapplicable subsection must be removed for non-strict work; within strict work, mark it as not applicable with a reason before review.

### Threat and trust boundaries

Trust boundary는 caller CLI → local curated source → sibling transport/merger → authenticated `gh` → untrusted GitHub response → caller destinations 순서다. 원격 body와 URL, response headers는 모두 비신뢰이며 repository identity, endpoint, filesystem path, authorization, status를 직접 결정할 수 없다. F1은 URL-to-endpoint 경계, F2/R2는 header-to-next-request 경계, F4/R1/R3/F7은 runtime state-to-persisted evidence 경계의 결함이다.

통제는 canonical repository gate, structured header states, no speculative pagination, outcome/corpus reconciliation, append-only builder, run-local usable 판정, paired staging cleanup, fake-client exact call log와 destination-byte assertion이다. Credential과 private body는 warning에 복사하지 않는다.

### Authorization and tenant isolation

서비스형 multi-tenant system이 아니므로 tenant isolation은 not applicable이다. 이유는 호출자의 로컬 process와 기존 `gh` read scope로 한 tracker run을 처리하기 때문이다. 대신 서로 다른 tracker/run의 isolation은 caller-supplied exact manifest discriminator, fingerprint, resume run ID, corpus reconciliation로 유지한다. GitHub write authorization은 어떤 경우에도 없고 remote association/text가 권한을 높이지 않는다.

### Migration, compatibility, and rollback

Schema migration과 data backfill은 not applicable이다. corpus 1.0.0, manifest 2.0.0, exit 0/2/3/4, collect CLI spelling, six-file revision framing, sibling source-policy 기본 동작을 유지한다. 기존 incomplete failure records는 소급 변환하지 않고 새로 기록하거나 갱신하는 run부터 공통 필드를 적용한다.

Rollback trigger는 traversal endpoint 발생, history prefix 손상, mismatch resume 성공, orphan temp, 기존 corpus에 의한 partial 승격, 기존 suite regression, baseline 금지 경로 변화다. 자동 rollback은 하지 않는다. root는 baseline snapshot diff로 curated 변경만 되돌릴 수 있고 기존 runtime corpus/manifest는 삭제·rewrite하지 않은 채 해당 revision 사용을 중지한다.

### Failure recovery and observability

Manifest의 warnings/failed scopes, page provenance, hydration outcomes, request count/events, status와 process exit가 로컬 관측 정본이다. Resume mismatch는 명시적 input error, pagination/header gap은 partial 또는 no-usable failed, processing failure는 append-only failed run으로 복구된다. Persistence 실패는 stderr/exit 4로 드러나고 이전 destination bytes를 유지한다.

외부 alert, metrics, distributed trace backend는 로컬 one-shot CLI이고 새 운영 인프라가 범위 밖이므로 not applicable이다. 대신 exact unittest transcript, TDD RED/GREEN 기록, temporary directory listing, manifest projection, snapshot diff가 진단 evidence다.

### High-risk end-to-end verification

고위험 순서는 CMD-1 → CMD-2 → CMD-5 → CMD-3 → CMD-4 → CMD-6 → CMD-7이다. 모든 단계는 network 없이 synthetic fixture로 실행한다. 필수 evidence는 17 exact test ID, traversal call-log 부재, terminal/unsupported header provenance, prior manifest prefix, resume request/write 0회, warning/scope 대응, hydration call count/cache identity, pre/post destination bytes 및 directory entries, current-run status/exit, CLI help/revision, portable eval normalized diff, full regression output, immutable hash 결과다.

다음 중 하나라도 있으면 완료를 중단한다: 필수 RED가 실제 결함 양상으로 실패하지 않음, exact test 미실행, mutation 생존, remote-derived traversal endpoint, 정상 마지막 페이지 partial, gap warning 누락, manifest history/field 손실, corpus-mismatch reuse, orphan temp, existing-only partial 승격, API literal drift, 절대 홈 경로, oracle 무승인 재생성, 금지 경로 diff, suite 비영 종료.

### No production mutation confirmation

자동 workflow에는 production mutation이 없다. Spec 작성과 이후 구현·검증은 지정 worktree의 승인된 source/test/eval 및 task-state evidence만 다룬다. GitHub live 요청과 POST/PATCH/PUT/DELETE, Issue/PR/comment/review/label/branch 변경, credential 접근, dependency install, commit, push, PR 생성, merge, deploy, main·다른 worktree·전역 설치본 변경은 수행하지 않는다.

<!-- strict-only:end -->
