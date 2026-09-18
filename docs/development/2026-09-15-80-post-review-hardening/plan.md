# Quality Goal Implementation Plan

- Task ID: 20260915T065141Z-80-post-review-hardening-curated-contrib-52ae436a
- Mode: strict
- Status: draft
- Created: 2026-09-15
- Updated: 2026-09-15
- Source goal: #80 post-review hardening: curated contribution PR collector의 보안·페이지네이션·manifest·분류·원자성 결함 수정

## Spec link

- 승인 Spec: `/Users/lee-kyu-hwan/code/dotfiles__worktrees/80-feat-curated-contribution-prs/docs/development/2026-09-15-80-post-review-hardening/spec.md`
- 승인 Spec SHA-256: `58717dcbbcf55774934a9e2176398df7494c0236c10397da5761a2dcd4746c49`
- 이 Plan은 위 digest의 요구사항, AC-1~AC-23, D1~D6만 구현 대상으로 삼는다.

## Global constraints

- 구현자는 `dot_codex/skills/collecting-curated-contribution-prs/` 아래 `SKILL.md`, `agents/openai.yaml`, `references/`, `scripts/`, `tests/`와 F8만을 위한 `evals/behavioral-eval.md`만 수정할 수 있다. 이 Plan에서 예정한 실제 변경은 collector script, 단일 test module, `references/collection-contract.md`, F8 eval 문서 네 파일이다. 다른 허용 경로가 필요해지면 구현을 멈추고 Plan 변경으로 되돌린다.
- 형제 collector는 통합 경계로 읽되 수정하지 않는다. `collect_repository_hits`, search, partition, 형제 `references/github-rest-contract.md`, analyzer, candidate verifier, main, 다른 worktree 및 전역 설치본은 변경하지 않는다. 형제 merger 영역 수정 필요성이 새로 입증되어도 먼저 Plan 변경과 root 승인을 받는다.
- `/Users/lee-kyu-hwan/code/dotfiles__worktrees/80-feat-curated-contribution-prs/docs/development/2026-09-10-80-collecting-curated-contribution-prs/`의 `final-handoff.md`, `plan-revision-notes.md`, `plan.md`, `report.md`, `spec-revision-notes.md`, `spec.md` 여섯 문서는 모든 단계와 rollback에서 바이트 불변이다.
- 대상 경로가 `initial_dirty_paths`와 겹치는 절차 예외를 적용한다. 구현 전 바이트 정본은 `/Users/lee-kyu-hwan/code/dotfiles__worktrees/80-feat-curated-contribution-prs/.claude/quality-state/20260915T065141Z-80-post-review-hardening-curated-contrib-52ae436a/baseline-snapshot/`, 해시 정본은 `/Users/lee-kyu-hwan/code/dotfiles__worktrees/80-feat-curated-contribution-prs/.claude/quality-state/20260915T065141Z-80-post-review-hardening-curated-contrib-52ae436a/baseline-hashes.txt`다. 최종 변경 판정은 Git base가 아니라 이 snapshot 대비 diff인 CMD-7과 CMD-8로 한다.
- F1, F2, F3a~F3d, F4~F8, R1~R5, A1의 17건만 고친다. Spec Non-goals의 재현되지 않은 여섯 항목에는 test나 구현 태스크를 만들지 않는다.
- 태스크는 T1부터 T17까지 직렬 실행한다. 각 태스크에서 test-only 상태의 snapshot digest와 실제 RED를 먼저 기록하고, 해당 원인만 최소 수정하며, 같은 focused command의 GREEN 전에는 다음 태스크 구현을 시작하지 않는다. RED가 예상 결함과 다른 이유로 나거나 뜻밖에 통과하면 구현하지 않고 합성 fixture 또는 관측점을 바로잡는다.
- 테스트는 표준 라이브러리 `unittest`, `unittest.mock`, `tempfile.TemporaryDirectory`와 합성 repository·인물·시각·payload만 사용한다. live network, credential, private roster, 실제 원문, pytest, jsonschema, dependency install을 사용하지 않는다. 모든 Python 명령은 `PYTHONDONTWRITEBYTECODE=1`로 실행한다.
- 살아 있는 revision fixture와 `expected-corpus.json`, `recollected-corpus.json`을 구현 출력으로 재생성하거나 assertion을 완화해 GREEN을 만들지 않는다. oracle 변경이 불가피하면 변경 전후 semantic diff, 기존 validator 결과, 원래 #80 안전 계약을 보존하는 독립 행위 증거를 먼저 제시하고 root의 명시적 승인을 받은 뒤 진행한다. 승인 전에는 해당 태스크를 중단한다.
- 각 focused test 또는 인접 contract test는 Spec의 단일 변이 신호를 거부해야 한다. 변이 판정은 repository 방어를 훼손하지 않도록 격리된 임시 복제본에서 같은 focused command를 실행하고 예상 비영 종료를 task-state transcript에 기록한다.
- corpus 1.0.0, manifest 2.0.0, exit 0/2/3/4, 기존 full CLI spelling, injected hydrator signature, sibling merger/source-policy 기본 동작을 보존한다. schema migration, data backfill 및 새 외부 의존성은 없다.
- D1 문법은 확정 사항이다. URL span을 먼저 제거하고 영어 `example|examples`, `notice|notices`, `announcement`를 앞뒤 ASCII 글자가 아닌 ASCII 글자 경계로 판정한다. 한국어는 normalized label의 첫 token이 `예시|공지`이고 바로 뒤가 label 끝 또는 `:`, `：`, `-`, `–`, `—`일 때만 일치시킨다. 기존 설명형 영어 example label과 한국어 `공지:` heading은 계속 제외한다.
- 구현자는 commit, push, PR 생성, merge, deploy 또는 production mutation을 수행하지 않는다. 이 외부 동작과 최종 통합은 root만 수행한다.

## File map

| 경로 | 작업 | 책임과 영향 |
|---|---|---|
| `dot_codex/skills/collecting-curated-contribution-prs/scripts/collect_curated_contribution_prs.py` | 수정 | repository trust gate, 4-state Link/header 판정, D1 classifier, 공통 run-record builder, resume/corpus 대조, warning, run-local hydration cache, paired staging cleanup, current-run usable 판정, argparse revision option, sibling API version 정본을 구현한다. |
| `dot_codex/skills/collecting-curated-contribution-prs/tests/test_collect_curated_contribution_prs.py` | 수정 | 17개 exact `post_review` regression과 `test_ac_22_contract_stdlib_synthetic_packaging`을 inline synthetic data로 추가한다. 기존 34 tests와 기존 fixture oracle은 유지한다. |
| `dot_codex/skills/collecting-curated-contribution-prs/evals/behavioral-eval.md` | 수정 | F8에 한해 baseline의 worktree 절대 경로 두 곳을 정확히 `<worktree>`로 치환하고 나머지 bytes를 유지한다. |
| `dot_codex/skills/collecting-curated-contribution-prs/tests/fixtures/expected-corpus.json`, `recollected-corpus.json` 및 revision fixture | 검사 전용 | 살아 있는 oracle이다. 단순 재생성 금지이며 변경에는 독립 행위 증거와 root 승인이 선행한다. |
| `dot_codex/skills/collecting-curated-contribution-prs/references/collection-contract.md` | 수정 | 배포 계약의 label 분류 설명을 D1의 URL-span 제거, 영어 ASCII 글자 경계와 복수형, 한국어 첫-token/delimiter 문법으로 맞춘다. |
| `dot_codex/skills/collecting-curated-contribution-prs/SKILL.md`, `agents/openai.yaml`, `references/`의 나머지 파일 | 검사 전용 | 공개 CLI·schema·packaging 계약 호환성을 확인하며 `collection-contract.md` 외에는 쓰지 않는다. |
| `dot_codex/skills/collecting-recent-closed-prs/references/collection-contract.md`, `scripts/collect_recent_closed_prs.py`, `tests/test_collect_recent_closed_prs.py` | 검사 전용·바이트 불변 | sibling `API_VERSION`, hydration, merger/source-policy 경계의 정본이며 CMD-7이 baseline equality를 판정한다. |
| `docs/development/2026-09-10-80-collecting-curated-contribution-prs/`의 여섯 문서 | 검사 전용·바이트 불변 | #80 감사 산출물이며 CMD-7의 첫 여섯 hash로 보존한다. |
| `.claude/quality-state/20260915T065141Z-80-post-review-hardening-curated-contrib-52ae436a/baseline-snapshot/` 및 `baseline-hashes.txt` | 검사 전용 | initial-dirty 예외의 작업 전 bytes와 최종 scope 판정 정본이다. |
| `docs/development/2026-09-15-80-post-review-hardening/report.md` | root가 종료 단계에서 작성 | AC-18과 AC-19의 태스크별 RED/GREEN·변이·oracle 증거를 집계한다. 구현자는 이 파일을 작성하지 않는다. |

## Task dependencies

T1 → T2 → T3 → T4 → T5 → T6 → T7 → T8 → T9 → T10 → T11 → T12 → T13 → T14 → T15 → T16 → T17 순서로 실행한다. 각 태스크는 이전 태스크의 focused GREEN과 mutation signal을 입력으로 받고 자신의 test-only RED, 최소 implementation diff, focused GREEN, 관련 suite GREEN을 산출한다. 각 태스크 네 번째 단계에 열거한 명령이 해당 결함의 영향 경계 정본이며, 그 결과를 다음 태스크 전에 기록한다. T9의 공통 record builder는 T8의 append-only 처리를 소비하고, T11의 warning 연결은 T1·T3 및 기존 pagination/hydration/budget/processing scopes를 소비한다. T17은 앞선 16개 GREEN과 transcript를 소비해 F8, packaging contract, 전체 회귀, scope hash를 한 번에 닫는다. 병렬 구현은 금지한다.

## Tasks

### T1. F1 원격 repository identity trust gate

대상 AC: AC-1 — `CMD-1 CMD-9 test_ac_01_post_review_remote_repository_validation`

1. **RED:** test module에 traversal-shaped PR URL과 fake-client call log를 쓰는 exact test만 추가하고 test-only snapshot digest를 기록한 뒤 CMD-9를 실행한다. 현재 `('../..', 1)`이 selection/hydration으로 흘러 `/repos/../..` 요청이 생기거나 warning이 없어 비영 종료해야 한다.
2. **최소 구현:** CLI와 remote identity가 함께 쓰는 canonical `OWNER/REPO` validator를 두고 `.`·`..`, 빈 segment, 추가 slash, 허용 문자 밖 값을 endpoint 조립 전 거부한다. invalid reference를 sanitized `reference_exclusions`, warning, 대응 failed scope로 보내며 raw body나 credential은 복사하지 않는다. `collect_repository_hits`, search, partition은 건드리지 않는다.
3. **GREEN:** 같은 CMD-9가 exit 0이고 exact test가 `ok`이며 identity/API call log에 `..`가 없고 gap에 맞는 partial 또는 failed 상태가 관측되어야 한다. validator 생략 변이는 이 test를 실패시켜야 한다.
4. **관련 suite GREEN:** CMD-2를 실행해 exit 0을 확인하고 focused GREEN 직후 결과를 기록한다.

### T2. F2 terminal Link 상태

대상 AC: AC-2 — `CMD-1 CMD-10 test_ac_02_post_review_terminal_link_without_next`

1. **RED:** `rel="prev"`와 `rel="first"`만 있는 mapping header와 Link key 부재 대조를 추가하고 CMD-10을 실행한다. 현재 terminal Link가 malformed next로 기록되어 비영 종료해야 한다.
2. **최소 구현:** header/Link 결과에 `absent`, `present-terminal`, `present-next` 상태를 만들고 next validator는 `present-next`에서만 호출한다. terminal은 추가 request·failed scope 없이 끝내되 absent와 다른 provenance를 남긴다.
3. **GREEN:** 같은 CMD-10이 exit 0이고 exact test가 `ok`이며 추가 comments request 0회와 서로 다른 provenance를 확인해야 한다. no-next를 invalid로 되돌리는 변이는 실패해야 한다.
4. **관련 suite GREEN:** CMD-2를 실행해 exit 0을 확인하고 focused GREEN 직후 결과를 기록한다.

### T3. R2 unsupported header container

대상 AC: AC-3 — `CMD-1 CMD-11 test_ac_03_post_review_unsupported_header_shape`

1. **RED:** list headers와 mapping-without-Link 대조를 추가하고 CMD-11을 실행한다. 현재 둘 다 `None`으로 축소되어 list case에 warning/failed scope가 없어 비영 종료해야 한다.
2. **최소 구현:** T2 parser에 `unsupported-container` 상태를 추가한다. `None` 또는 mapping의 Link 부재는 정상 absent, `None`이 아닌 비-mapping은 sanitized header-container warning과 failed scope가 있는 gap으로 만들고 추가 요청은 하지 않는다.
3. **GREEN:** 같은 CMD-11이 exit 0이고 exact test가 `ok`이며 list case만 partial gap이고 mapping key 부재는 정상 종료여야 한다. unsupported를 absent로 되돌리는 변이는 실패해야 한다.
4. **관련 suite GREEN:** CMD-2를 실행해 exit 0을 확인하고 focused GREEN 직후 결과를 기록한다.

### T4. F3a 한국어 첫-token 경계

대상 AC: AC-4 — `CMD-1 CMD-12 test_ac_04_post_review_korean_label_boundary`

1. **RED:** 일반 문장과 `예시|공지` 뒤 label 끝 및 다섯 delimiter table case, 기존 `공지:` heading을 추가하고 CMD-12를 실행한다. 현재 한국어 부분문자열 판정이 일반 문장을 제외해 비영 종료해야 한다.
2. **최소 구현:** normalized URL-free label의 시작에서만 `예시|공지`를 찾고 바로 뒤가 label 끝 또는 `:`, `：`, `-`, `–`, `—`인지 검사한다. 일반 문장 중간 keyword는 submission으로 둔다.
3. **GREEN:** 같은 CMD-12가 exit 0이고 exact test가 `ok`이며 일반 문장은 submission, table case와 기존 heading은 exclusion이어야 한다. 한국어 부분문자열 판정 복원 변이는 실패해야 한다.
4. **관련 suite GREEN:** CMD-2, CMD-4, CMD-6을 실행해 모두 exit 0임을 확인하고 focused GREEN 직후 결과를 기록한다.

### T5. F3b 영어 example 복수형과 ASCII 경계

대상 AC: AC-5 — `CMD-1 CMD-13 test_ac_05_post_review_examples_plural`

1. **RED:** `Examples:`, 기존 설명형 `Format example (do NOT count this one)`, ASCII 단어 내부 대조를 추가하고 CMD-13을 실행한다. 현재 plural case가 submission이라 비영 종료해야 한다.
2. **최소 구현:** URL-free normalized label에서 `example|examples`를 앞뒤 ASCII 글자가 아닌 경계로 검색한다. 설명형 label exclusion은 보존하고 다른 ASCII 단어 내부 부분문자열은 제외 근거로 쓰지 않는다.
3. **GREEN:** 같은 CMD-13이 exit 0이고 exact test가 `ok`여야 한다. plural 제거 또는 부분문자열 복원 변이는 실패해야 한다.
4. **관련 suite GREEN:** CMD-2, CMD-4, CMD-6을 실행해 모두 exit 0임을 확인하고 focused GREEN 직후 결과를 기록한다.

### T6. F3c 영어 notice 복수형과 announcement 경계

대상 AC: AC-6 — `CMD-1 CMD-14 test_ac_06_post_review_notices_plural`

1. **RED:** `Notices:`와 ASCII 경계의 `notice|notices|announcement`, 단어 내부 대조를 추가하고 CMD-14를 실행한다. 현재 plural case가 submission이라 비영 종료해야 한다.
2. **최소 구현:** URL-free normalized label에서 세 token을 ASCII 글자 경계로 검색하고 classification basis에 실제 matched token을 남긴다.
3. **GREEN:** 같은 CMD-14가 exit 0이고 exact test가 `ok`여야 한다. plural 제거 또는 부분문자열 복원 변이는 실패해야 한다.
4. **관련 suite GREEN:** CMD-2, CMD-4, CMD-6을 실행해 모두 exit 0임을 확인하고 focused GREEN 직후 결과를 기록한다.

### T7. F3d 모든 URL span 선제 제거

대상 AC: AC-7 — `CMD-1 CMD-15 test_ac_07_post_review_non_pr_url_label`

1. **RED:** host/path에 `example`이 있는 non-PR issue URL과 같은 label의 합성 PR URL을 추가하고, 배포 계약 문서가 D1 문법을 그대로 서술하는지 확인하는 assertion을 같은 exact test에 넣어 CMD-15를 실행한다. 현재 PR URL만 제거되어 실제 submission이 제외되고 문서도 구문이 어긋나므로 비영 종료해야 한다.
2. **최소 구현:** keyword 검사 전에 label의 일반 URL span을 모두 제거하고 남은 normalized label만 T4~T6 matcher에 전달한다. URL 자체의 keyword는 classification basis가 될 수 없다. `references/collection-contract.md`의 기존 “URL 앞 label” 및 same-line/앞줄 설명을 D1의 모든 URL span 제거, 영어 `example|examples`, `notice|notices`, `announcement` ASCII 글자 경계, 한국어 normalized label 첫 token `예시|공지`와 label 끝 또는 `:`, `：`, `-`, `–`, `—` delimiter 문법으로 갱신한다.
3. **GREEN:** 같은 CMD-15가 exit 0이고 exact test가 `ok`이며 PR이 submission이고 문서의 문법 항목과 코드 table case가 일치해야 한다. URL span 제거를 PR URL 전용으로 되돌리거나 계약 문서를 이전 문법으로 되돌리는 변이는 실패해야 한다.
4. **관련 suite GREEN:** CMD-2, CMD-4, CMD-5, CMD-6을 실행해 모두 exit 0임을 확인하고 focused GREEN 직후 결과를 기록한다.

### T8. F4 post-processing failure의 append-only history

대상 AC: AC-8 — `CMD-1 CMD-16 test_ac_08_post_review_processing_handler_append_only`

1. **RED:** validated prior run 두 개가 있는 manifest와 handler 직접 도달 injection을 추가하고 CMD-16을 실행한다. 특정 client 예외 전파를 가정하지 않으며 현재 records가 failed run 하나로 대체되어 비영 종료해야 한다.
2. **최소 구현:** `main`의 post-request `ValueError` handler가 이미 검증·복사한 prior records를 사용하게 하고 non-resume은 새 failed run을 append하며 resume은 기존 `_manifest_records`의 동일-run 교체 의미를 유지한다.
3. **GREEN:** 같은 CMD-16이 exit 0이고 exact test가 `ok`, prior two-record prefix가 byte-deep-equal이고 세 번째 failed run과 exit 4만 추가되어야 한다. history 재초기화 변이는 실패해야 한다.
4. **관련 suite GREEN:** CMD-2를 실행해 exit 0을 확인하고 focused GREEN 직후 결과를 기록한다.

### T9. F5 공통 run-record 필드 builder

대상 AC: AC-9 — `CMD-1 CMD-17 test_ac_09_post_review_failed_record_field_parity`

1. **RED:** normal, preflight failure, post-processing failure를 동일 caller `max_prs`로 생성하는 test를 추가하고 CMD-17을 실행한다. 현재 실패 records의 key set과 `max_prs`가 달라 비영 종료해야 한다.
2. **최소 구현:** normal/preflight/processing이 하나의 base run-record builder를 사용하게 하고 Spec R4.2의 23개 공통 key를 모두 만든다. 사용할 수 없는 값은 `null` 또는 빈 collection으로 두고 key를 생략하지 않으며 manifest envelope와 T8 prefix를 유지한다.
3. **GREEN:** 같은 CMD-17이 exit 0이고 exact test가 `ok`, 세 경로의 common key set과 caller `max_prs`가 같아야 한다. `max_prs` 생략 또는 독립 dict literal 복원 변이는 실패해야 한다.
4. **관련 suite GREEN:** CMD-2를 실행해 exit 0을 확인하고 focused GREEN 직후 결과를 기록한다.

### T10. R1 complete resume와 corpus reconciliation

대상 AC: AC-10 — `CMD-1 CMD-18 test_ac_10_post_review_resume_corpus_reconciliation`

1. **RED:** collected outcome record 제거, repository/PR 또는 가능한 node identity 충돌, 일치 대조 fixture를 추가하고 CMD-18을 실행한다. 현재 mismatch도 complete checkpoint로 재사용되어 비영 종료해야 한다.
2. **최소 구현:** complete resume fast path보다 먼저 prior `hydration_outcomes`의 `collected|partial`을 normalized repository/PR number와 가능한 `pull_request_node_id` corpus index에 대조한다. 누락·충돌은 client call과 persistence 전 `ValueError` input error로 만들고 `checkpoint_reused`를 쓰지 않는다.
3. **GREEN:** 같은 CMD-18이 exit 0이고 exact test가 `ok`; mismatch 두 case는 request/write 0회·destination bytes 불변·exit 2, 일치 case는 기존 network-free reuse여야 한다. 대조 생략 변이는 실패해야 한다.
4. **관련 suite GREEN:** CMD-2를 실행해 exit 0을 확인하고 focused GREEN 직후 결과를 기록한다.

### T11. R4 warning과 failed-scope 대응

대상 AC: AC-11 — `CMD-1 CMD-19 test_ac_11_post_review_manifest_warnings`

1. **RED:** invalid identity, unsupported headers, pagination, hydration, budget, processing gap과 complete 대조를 table case로 추가하고 CMD-19를 실행한다. 현재 warnings append가 없어 gap cases가 비영 종료해야 한다.
2. **최소 구현:** structured failed scope 생성 지점과 동일한 지점에서 sanitized warning을 만드는 helper를 사용한다. kind와 안전한 reason은 대응시키되 raw body, 전체 header value, token, conditional header를 포함하지 않고 complete run에는 warning을 만들지 않는다.
3. **GREEN:** 같은 CMD-19가 exit 0이고 exact test가 `ok`; 각 recoverable gap은 non-empty warning/failed-scope pair를 갖고 complete fixture는 빈 warnings여야 한다. warning append 제거 변이는 실패해야 한다.
4. **관련 suite GREEN:** CMD-2를 실행해 exit 0을 확인하고 focused GREEN 직후 결과를 기록한다.

### T12. F6 collect 수명의 hydration caches

대상 AC: AC-12 — `CMD-1 CMD-20 test_ac_12_post_review_run_scoped_hydration_caches`

1. **RED:** 같은 normalized repository의 PR 두 개와 독립 두 번째 run, sibling hydrator의 cache object identity를 관측하는 test를 추가하고 CMD-20을 실행한다. 현재 metadata GET 2회와 서로 다른 빈 license cache 때문에 비영 종료해야 한다.
2. **최소 구현:** `collect()` 지역 context에 성공한 normalized repository metadata의 deep-copied cache와 sibling-compatible mutable `license_cache` 하나를 만든다. default hydrator closure만 이를 공유하고 public/injected hydrator signature와 run 간 isolation은 유지한다.
3. **GREEN:** 같은 CMD-20이 exit 0이고 exact test가 `ok`; 첫 run metadata GET 1회·동일 license cache object, 둘째 run 새 cache여야 한다. 호출별 cache 재생성 변이는 실패해야 한다.
4. **관련 suite GREEN:** CMD-2와 CMD-3을 실행해 모두 exit 0임을 확인하고 focused GREEN 직후 결과를 기록한다.

### T13. F7 두 번째 temporary write 실패 cleanup

대상 AC: AC-13 — `CMD-1 CMD-21 test_ac_13_post_review_second_temporary_write_cleanup`

1. **RED:** 두 destination 기존 bytes와 두 번째 `_write_temporary` failure injection, pre/post directory entry set을 추가하고 CMD-21을 실행한다. 현재 첫 temporary가 남아 비영 종료해야 한다.
2. **최소 구현:** 두 temporary 변수를 먼저 `None`으로 초기화하고 첫 staging부터 하나의 outer `try/finally`가 생성된 모든 temporary를 소유하게 한다. serialization, 첫 write, replace/restore 의미는 바꾸지 않고 두 번째 write 예외를 기존 exit-4 경로로 전달한다.
3. **GREEN:** 같은 CMD-21이 exit 0이고 exact test가 `ok`; destination bytes와 directory entries가 실행 전과 같고 orphan temp가 0이어야 한다. 첫 temporary cleanup 제거 변이는 실패해야 한다.
4. **관련 suite GREEN:** CMD-2를 실행해 exit 0을 확인하고 focused GREEN 직후 결과를 기록한다.

### T14. R3 current-run usable 판정

대상 AC: AC-14 — `CMD-1 CMD-22 test_ac_14_post_review_current_run_usable_records`

1. **RED:** non-empty existing corpus와 이번 run hydration 전부 실패, 같은 run에서 usable record 하나가 생기는 대조를 추가하고 CMD-22를 실행한다. 현재 merged corpus가 usable로 계산되어 전부 실패 case가 partial/3이라 비영 종료해야 한다.
2. **최소 구현:** status 계산을 `selected_records` 중 성공 또는 partial로 생성된 이번 run record에만 근거하게 한다. 기존 corpus bytes는 보존하되 current-run usable 0과 gap이면 failed/4, 하나 이상이면 partial/3으로 둔다.
3. **GREEN:** 같은 CMD-22가 exit 0이고 exact test가 `ok`; existing-only case는 failed/4, 대조만 partial/3이어야 한다. merged-corpus usable 판정 복원 변이는 실패해야 한다.
4. **관련 suite GREEN:** CMD-2를 실행해 exit 0을 확인하고 focused GREEN 직후 결과를 기록한다.

### T15. R5 argparse 소유 revision option과 축약 거부

대상 AC: AC-15 — `CMD-1 CMD-23 test_ac_15_post_review_print_revision_help`

1. **RED:** subprocess로 top-level `--help`, 단독 `--print-revision`, 추가 인자 조합, `--print-rev`, `--hel`, `collect --help`의 full option set과, (a) subcommand와 `--print-revision`이 모두 없는 bare invocation, (b) 알 수 없는 subcommand를 검사하는 test를 추가하고 CMD-23을 실행한다. 현재 help 미노출과 기본 `allow_abbrev=True`의 `--print-rev` 수용 때문에 비영 종료해야 한다.
2. **최소 구현:** top-level `ArgumentParser`를 `allow_abbrev=False`로 만들고 `--print-revision`을 top-level public option으로 등록한다. top-level subcommand requiredness는 `add_subparsers(..., required=True)`에서 argparse parse 후 `parser.error(...)` 규칙으로 이동해 revision 단독 호출만 예외로 허용하고, 기존 argv 완전일치 special-case는 제거한다. full `--help`, `--print-revision`, `collect --help`와 collect option spelling은 보존한다.
3. **GREEN:** 같은 CMD-23이 exit 0이고 exact test가 `ok`; 단독 full spelling은 `sha256:<64 lowercase hex>` 한 줄과 exit 0, 추가 인자·`--print-rev`·`--hel`, bare invocation, 알 수 없는 subcommand는 모두 argparse usage error와 exit 2 및 revision stdout 0줄이어야 한다. 확정된 부수 효과는 top-level 자동 prefix abbreviation 전체가 비활성화되는 것이며 full spelling과 subcommand requiredness에는 영향이 없다. argv special-case 복원, `allow_abbrev=True`, bare invocation의 traceback/성공 변이는 실패해야 한다.
4. **관련 suite GREEN:** CMD-2와 CMD-5를 실행해 모두 exit 0임을 확인하고 focused GREEN 직후 결과를 기록한다.

### T16. A1 sibling API_VERSION 단일 정본

대상 AC: AC-16 — `CMD-1 CMD-7 CMD-24 test_ac_16_post_review_shared_api_version`

1. **RED:** AST/text로 curated API date fallback literal을 세고 client version 부재의 fingerprint/run record를 검사하는 test를 추가한 뒤 CMD-24를 실행한다. 현재 fallback literal 3곳 때문에 비영 종료해야 한다.
2. **최소 구현:** 이미 load된 sibling module의 `API_VERSION`을 fingerprint, normal/preflight/processing record fallback에 사용하고 curated fallback literal을 제거한다. 형제 script와 transport/merge/search/partition은 수정하지 않는다.
3. **GREEN:** 같은 CMD-24가 exit 0이고 exact test가 `ok`, curated fallback literal 0개와 sibling constant reference 및 runtime equality를 확인해야 한다. API literal 복원 변이는 실패해야 한다. 이어 CMD-7로 형제 세 파일과 감사 문서 bytes가 그대로임을 확인한다.
4. **관련 suite GREEN:** CMD-2, CMD-3, CMD-5를 실행해 모두 exit 0임을 확인하고 focused GREEN 및 CMD-7 직후 결과를 기록한다.

### T17. F8 portable eval, packaging contract와 최종 evidence

대상 AC: AC-17 — `CMD-1 CMD-25 test_ac_17_post_review_portable_eval_paths`
대상 AC: AC-18 — `docs/development/2026-09-15-80-post-review-hardening/report.md § 결함별 RED→GREEN 증거 계약`
대상 AC: AC-19 — `docs/development/2026-09-15-80-post-review-hardening/report.md § 변이와 oracle 무결성`
대상 AC: AC-20 — `CMD-8`
대상 AC: AC-21 — `CMD-7`
대상 AC: AC-22 — `CMD-2 CMD-5 CMD-26 test_ac_22_contract_stdlib_synthetic_packaging`
대상 AC: AC-23 — `CMD-1 CMD-2 CMD-3 CMD-4 CMD-6`

1. **RED:** F8 baseline-normalized byte test와 stdlib/synthetic/no-network/allowed-path/bytecode/F8-only contract test만 추가해 test-only snapshot digest를 기록한다. CMD-25와 CMD-26을 실행하며 현재 eval의 사용자 홈 절대 경로 두 곳 때문에 둘 다 비영 종료해야 한다.
2. **최소 구현:** eval baseline bytes에서 현재 worktree 절대 경로 두 occurrence만 `<worktree>`로 치환한다. 다른 eval bytes, source logic, live fixtures는 바꾸지 않는다. contract test는 17 exact IDs의 존재, third-party test import 부재, synthetic data 규칙, 허용 파일 집합, 문서에 기록된 Python command의 bytecode 억제, baseline 대비 F8-only 변환을 구체적으로 assert한다.
3. **GREEN:** 같은 CMD-25와 CMD-26이 각각 exit 0이고 두 exact tests가 `ok`; `/Users/` 0회이고 baseline의 두 경로만 치환되어야 한다. 절대 경로 복원 변이는 실패해야 한다.
4. **증거 집계:** root는 T1~T17 각각의 test-only digest, 실제 RED exit/assertion, 한 원인 implementation diff, 동일 focused GREEN `ok`, 격리 mutation 실패, 관련 suite GREEN을 시간순으로 report의 `결함별 RED→GREEN 증거 계약`과 `변이와 oracle 무결성` 절에 기록한다. oracle을 건드리지 않았음을 명시하며, 변경했다면 사전 root 승인과 독립 evidence가 없을 경우 완료를 거부한다.
5. **최종 판정:** CMD-1 → CMD-2 → CMD-5 → CMD-3 → CMD-4 → CMD-6 → CMD-7 → CMD-8 순으로 한 번 실행한다. curated baseline 34 tests를 보존하고 17 focused tests 및 AC-22 contract test가 추가로 실행되며, sibling 115, analyzer 30, verifier 62 tests가 모두 통과해야 한다. 하나라도 비영 종료, 누락 ID, 금지 diff 또는 hash mismatch면 rollout을 중단한다.

## Verification commands

| ID | 명령 | 기대 성공 결과 |
|---|---|---|
| CMD-1 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -v -s dot_codex/skills/collecting-curated-contribution-prs/tests -t dot_codex/skills/collecting-curated-contribution-prs/tests -p 'test_*.py' -k post_review` | exit 0; AC-1~AC-17 exact test 17개가 모두 `ok`, 누락·0건 선택 없음 |
| CMD-2 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_codex/skills/collecting-curated-contribution-prs/tests -t dot_codex/skills/collecting-curated-contribution-prs/tests -p 'test_*.py'` | exit 0; baseline 34 tests를 포함한 curated 전체 suite, 17 focused tests와 AC-22 contract test 통과 |
| CMD-3 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_codex/skills/collecting-recent-closed-prs/tests -t dot_codex/skills/collecting-recent-closed-prs/tests -p 'test_*.py'` | exit 0; sibling baseline 115 tests와 merger/source-policy 회귀 통과 |
| CMD-4 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_codex/skills/analyzing-open-source-pr-patterns/tests -t dot_codex/skills/analyzing-open-source-pr-patterns/tests -p 'test_*.py'` | exit 0; analyzer baseline 30 tests와 corpus 호환성 통과 |
| CMD-5 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 /Users/lee-kyu-hwan/.codex/skills/.system/skill-creator/scripts/quick_validate.py dot_codex/skills/collecting-curated-contribution-prs` | exit 0과 `Skill is valid!` |
| CMD-6 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_codex/skills/verifying-open-source-contribution-candidates/tests -t dot_codex/skills/verifying-open-source-contribution-candidates/tests -p 'test_*.py'` | exit 0; verifier baseline 62 tests 통과 |
| CMD-7 | `sh -c 'set -eu; hashes=.claude/quality-state/20260915T065141Z-80-post-review-hardening-curated-contrib-52ae436a/baseline-hashes.txt; sed -n "1,6p" "$hashes" | shasum -a 256 -c -; snapshot=.claude/quality-state/20260915T065141Z-80-post-review-hardening-curated-contrib-52ae436a/baseline-snapshot; for artifact_rel in dot_codex/skills/collecting-recent-closed-prs/references/collection-contract.md dot_codex/skills/collecting-recent-closed-prs/scripts/collect_recent_closed_prs.py dot_codex/skills/collecting-recent-closed-prs/tests/test_collect_recent_closed_prs.py; do cmp "$snapshot/$artifact_rel" "$artifact_rel"; done'` | exit 0; 감사 문서 6개 hash와 형제 3개 파일 baseline bytes 일치 |
| CMD-8 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -c 'from pathlib import Path; import sys; root=Path.cwd().resolve(); snap=Path("/Users/lee-kyu-hwan/code/dotfiles__worktrees/80-feat-curated-contribution-prs/.claude/quality-state/20260915T065141Z-80-post-review-hardening-curated-contrib-52ae436a/baseline-snapshot"); curated=Path("dot_codex/skills/collecting-curated-contribution-prs"); audit=Path("docs/development/2026-09-10-80-collecting-curated-contribution-prs"); siblings=(Path("dot_codex/skills/collecting-recent-closed-prs/references/collection-contract.md"),Path("dot_codex/skills/collecting-recent-closed-prs/scripts/collect_recent_closed_prs.py"),Path("dot_codex/skills/collecting-recent-closed-prs/tests/test_collect_recent_closed_prs.py")); baseline={p.relative_to(snap) for p in snap.rglob("*") if p.is_file()}; current={p.relative_to(root) for base in (root/curated,root/audit) for p in base.rglob("*") if p.is_file()}|{p for p in siblings if (root/p).is_file()}; changed={p for p in baseline|current if not (snap/p).is_file() or not (root/p).is_file() or (snap/p).read_bytes() != (root/p).read_bytes()}; allowed=lambda p:p in (curated/"SKILL.md",curated/"agents/openai.yaml",curated/"evals/behavioral-eval.md") or any(curated/d in p.parents for d in ("references","scripts","tests")); bad=sorted(map(str,(p for p in changed if not allowed(p)))); eval_rel=curated/"evals/behavioral-eval.md"; source=(snap/eval_rel).read_bytes(); actual=(root/eval_rel).read_bytes(); marker=str(root).encode(); eval_ok=source.count(marker)==2 and actual==source.replace(marker,b"<worktree>") and b"/Users/" not in actual; print("outside_allowlist="+("none" if not bad else ",".join(bad))); print("eval_f8_only="+str(eval_ok)); sys.exit(0 if not bad and eval_ok else 1)'` | exit 0; `outside_allowlist=none`, `eval_f8_only=True`, snapshot 대비 curated allowlist 외 변경 없음 |
| CMD-9 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -v -s dot_codex/skills/collecting-curated-contribution-prs/tests -t dot_codex/skills/collecting-curated-contribution-prs/tests -p 'test_*.py' -k test_ac_01_post_review_remote_repository_validation` | exit 0; `test_ac_01_post_review_remote_repository_validation ... ok` |
| CMD-10 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -v -s dot_codex/skills/collecting-curated-contribution-prs/tests -t dot_codex/skills/collecting-curated-contribution-prs/tests -p 'test_*.py' -k test_ac_02_post_review_terminal_link_without_next` | exit 0; `test_ac_02_post_review_terminal_link_without_next ... ok` |
| CMD-11 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -v -s dot_codex/skills/collecting-curated-contribution-prs/tests -t dot_codex/skills/collecting-curated-contribution-prs/tests -p 'test_*.py' -k test_ac_03_post_review_unsupported_header_shape` | exit 0; `test_ac_03_post_review_unsupported_header_shape ... ok` |
| CMD-12 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -v -s dot_codex/skills/collecting-curated-contribution-prs/tests -t dot_codex/skills/collecting-curated-contribution-prs/tests -p 'test_*.py' -k test_ac_04_post_review_korean_label_boundary` | exit 0; `test_ac_04_post_review_korean_label_boundary ... ok` |
| CMD-13 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -v -s dot_codex/skills/collecting-curated-contribution-prs/tests -t dot_codex/skills/collecting-curated-contribution-prs/tests -p 'test_*.py' -k test_ac_05_post_review_examples_plural` | exit 0; `test_ac_05_post_review_examples_plural ... ok` |
| CMD-14 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -v -s dot_codex/skills/collecting-curated-contribution-prs/tests -t dot_codex/skills/collecting-curated-contribution-prs/tests -p 'test_*.py' -k test_ac_06_post_review_notices_plural` | exit 0; `test_ac_06_post_review_notices_plural ... ok` |
| CMD-15 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -v -s dot_codex/skills/collecting-curated-contribution-prs/tests -t dot_codex/skills/collecting-curated-contribution-prs/tests -p 'test_*.py' -k test_ac_07_post_review_non_pr_url_label` | exit 0; `test_ac_07_post_review_non_pr_url_label ... ok`, D1 코드 동작과 `references/collection-contract.md` 문법 일치 |
| CMD-16 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -v -s dot_codex/skills/collecting-curated-contribution-prs/tests -t dot_codex/skills/collecting-curated-contribution-prs/tests -p 'test_*.py' -k test_ac_08_post_review_processing_handler_append_only` | exit 0; `test_ac_08_post_review_processing_handler_append_only ... ok` |
| CMD-17 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -v -s dot_codex/skills/collecting-curated-contribution-prs/tests -t dot_codex/skills/collecting-curated-contribution-prs/tests -p 'test_*.py' -k test_ac_09_post_review_failed_record_field_parity` | exit 0; `test_ac_09_post_review_failed_record_field_parity ... ok` |
| CMD-18 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -v -s dot_codex/skills/collecting-curated-contribution-prs/tests -t dot_codex/skills/collecting-curated-contribution-prs/tests -p 'test_*.py' -k test_ac_10_post_review_resume_corpus_reconciliation` | exit 0; `test_ac_10_post_review_resume_corpus_reconciliation ... ok` |
| CMD-19 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -v -s dot_codex/skills/collecting-curated-contribution-prs/tests -t dot_codex/skills/collecting-curated-contribution-prs/tests -p 'test_*.py' -k test_ac_11_post_review_manifest_warnings` | exit 0; `test_ac_11_post_review_manifest_warnings ... ok` |
| CMD-20 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -v -s dot_codex/skills/collecting-curated-contribution-prs/tests -t dot_codex/skills/collecting-curated-contribution-prs/tests -p 'test_*.py' -k test_ac_12_post_review_run_scoped_hydration_caches` | exit 0; `test_ac_12_post_review_run_scoped_hydration_caches ... ok` |
| CMD-21 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -v -s dot_codex/skills/collecting-curated-contribution-prs/tests -t dot_codex/skills/collecting-curated-contribution-prs/tests -p 'test_*.py' -k test_ac_13_post_review_second_temporary_write_cleanup` | exit 0; `test_ac_13_post_review_second_temporary_write_cleanup ... ok` |
| CMD-22 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -v -s dot_codex/skills/collecting-curated-contribution-prs/tests -t dot_codex/skills/collecting-curated-contribution-prs/tests -p 'test_*.py' -k test_ac_14_post_review_current_run_usable_records` | exit 0; `test_ac_14_post_review_current_run_usable_records ... ok` |
| CMD-23 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -v -s dot_codex/skills/collecting-curated-contribution-prs/tests -t dot_codex/skills/collecting-curated-contribution-prs/tests -p 'test_*.py' -k test_ac_15_post_review_print_revision_help` | exit 0; `test_ac_15_post_review_print_revision_help ... ok`, bare/unknown-subcommand가 usage error·exit 2·revision stdout 0줄 |
| CMD-24 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -v -s dot_codex/skills/collecting-curated-contribution-prs/tests -t dot_codex/skills/collecting-curated-contribution-prs/tests -p 'test_*.py' -k test_ac_16_post_review_shared_api_version` | exit 0; `test_ac_16_post_review_shared_api_version ... ok` |
| CMD-25 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -v -s dot_codex/skills/collecting-curated-contribution-prs/tests -t dot_codex/skills/collecting-curated-contribution-prs/tests -p 'test_*.py' -k test_ac_17_post_review_portable_eval_paths` | exit 0; `test_ac_17_post_review_portable_eval_paths ... ok` |
| CMD-26 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -v -s dot_codex/skills/collecting-curated-contribution-prs/tests -t dot_codex/skills/collecting-curated-contribution-prs/tests -p 'test_*.py' -k test_ac_22_contract_stdlib_synthetic_packaging` | exit 0; `test_ac_22_contract_stdlib_synthetic_packaging ... ok` |

## Rollout and rollback

구현 rollout은 T1~T17의 직렬 RED→GREEN, 최종 CMD-1·CMD-2·CMD-5·CMD-3·CMD-4·CMD-6·CMD-7·CMD-8 GREEN, quality-goal code review 통과 순서다. local source와 tests 외 runtime corpus/manifest를 rewrite하지 않으며 live GitHub나 production에 배포하지 않는다. commit, push, PR, merge, deploy는 구현자가 수행하지 않고 root가 모든 evidence와 승인 digest를 확인한 뒤 별도로 수행한다.

Rollback trigger는 traversal endpoint, terminal page의 거짓 partial, unsupported header의 조용한 축소, D1 분류 회귀, manifest prefix/필드 손실, mismatch resume 성공, warning/scope 불일치, cache 격리 실패, orphan temp, existing-only partial 승격, CLI full spelling 회귀, API literal drift, 사용자 홈 경로, oracle 무승인 변경, suite 비영 종료, CMD-7 또는 CMD-8 실패다. 구현자는 자동 rollback이나 Git reset을 하지 않고 즉시 중단해 root에 evidence를 넘긴다.

Rollback은 root가 baseline snapshot에서 이번 변경 파일의 bytes를 복원하고 CMD-7·CMD-8로 금지 경로와 감사 산출물 불변을 다시 확인하는 방식이다. #80 감사 문서 여섯 개는 rollback source나 destination으로도 변경하지 않는다. 기존 runtime corpus/manifest는 삭제하거나 rewrite하지 않고 해당 revision 사용만 중지한다. schema migration과 data backfill이 없으므로 역 migration은 not applicable이다.

## Acceptance-criteria traceability

| Criterion | Task | Verification command | Expected outcome |
|---|---|---|---|
| AC-1 | T1 | `CMD-1 CMD-9 test_ac_01_post_review_remote_repository_validation` | traversal reference가 inert exclusion/warning이 되고 `..` identity/API call이 없다. |
| AC-2 | T2 | `CMD-1 CMD-10 test_ac_02_post_review_terminal_link_without_next` | prev/first-only Link는 정상 terminal이며 absent provenance와 구분된다. |
| AC-3 | T3 | `CMD-1 CMD-11 test_ac_03_post_review_unsupported_header_shape` | unsupported container만 sanitized partial gap이고 missing Link key는 정상이다. |
| AC-4 | T4 | `CMD-1 CMD-12 test_ac_04_post_review_korean_label_boundary` | 한국어 첫-token/delimiter 문법과 기존 heading 회귀가 모두 통과한다. |
| AC-5 | T5 | `CMD-1 CMD-13 test_ac_05_post_review_examples_plural` | example 복수형·설명형은 제외되고 ASCII 단어 내부는 제외되지 않는다. |
| AC-6 | T6 | `CMD-1 CMD-14 test_ac_06_post_review_notices_plural` | notice 복수형·announcement 경계는 제외되고 단어 내부는 제외되지 않는다. |
| AC-7 | T7 | `CMD-1 CMD-15 test_ac_07_post_review_non_pr_url_label` | 제거된 non-PR URL span의 keyword가 실제 PR을 제외하지 않고 배포 계약 문서와 코드의 D1 문법이 일치한다. |
| AC-8 | T8 | `CMD-1 CMD-16 test_ac_08_post_review_processing_handler_append_only` | prior two-run prefix 뒤 failed run 하나만 append되고 exit 4다. |
| AC-9 | T9 | `CMD-1 CMD-17 test_ac_09_post_review_failed_record_field_parity` | 세 run 경로의 23개 공통 key와 caller `max_prs`가 같다. |
| AC-10 | T10 | `CMD-1 CMD-18 test_ac_10_post_review_resume_corpus_reconciliation` | mismatch resume는 request/write 없이 exit 2, 일치 resume만 재사용한다. |
| AC-11 | T11 | `CMD-1 CMD-19 test_ac_11_post_review_manifest_warnings` | 모든 recoverable gap은 warning/scope pair, complete는 빈 warnings다. |
| AC-12 | T12 | `CMD-1 CMD-20 test_ac_12_post_review_run_scoped_hydration_caches` | 한 run은 metadata/license cache를 공유하고 독립 run은 격리된다. |
| AC-13 | T13 | `CMD-1 CMD-21 test_ac_13_post_review_second_temporary_write_cleanup` | 두 번째 staging 실패 뒤 destination bytes와 entries가 같고 temp가 없다. |
| AC-14 | T14 | `CMD-1 CMD-22 test_ac_14_post_review_current_run_usable_records` | existing-only 실패는 failed/4이고 current-run usable이 있을 때만 partial/3이다. |
| AC-15 | T15 | `CMD-1 CMD-23 test_ac_15_post_review_print_revision_help` | revision option은 help에 보이고 full spelling만 성공하며 축약·bare·unknown-subcommand는 usage/2와 revision stdout 0줄이다. |
| AC-16 | T16 | `CMD-1 CMD-7 CMD-24 test_ac_16_post_review_shared_api_version` | curated literal 0개, sibling constant 사용, 형제 bytes 불변이다. |
| AC-17 | T17 | `CMD-1 CMD-25 test_ac_17_post_review_portable_eval_paths` | baseline의 두 절대 경로만 `<worktree>`로 바뀌고 `/Users/`가 없다. |
| AC-18 | T17 | `docs/development/2026-09-15-80-post-review-hardening/report.md § 결함별 RED→GREEN 증거 계약` | 17건 각각의 test-only digest, 실제 RED, 단일 원인 diff, 동일-command GREEN, suite GREEN이 순서대로 기록된다. |
| AC-19 | T17 | `docs/development/2026-09-15-80-post-review-hardening/report.md § 변이와 oracle 무결성` | 17 mutation signals가 실패하고 oracle 재생성/완화가 없거나 사전 승인 증거가 있다. |
| AC-20 | T17 | `CMD-8` | snapshot diff가 curated allowlist 안이고 eval은 F8-only다. |
| AC-21 | T17 | `CMD-7` | #80 감사 문서 여섯 개가 hash 일치한다. |
| AC-22 | T17 | `CMD-2 CMD-5 CMD-26 test_ac_22_contract_stdlib_synthetic_packaging` | stdlib/synthetic/no-network/bytecode/allowlist 계약과 skill validation이 통과한다. |
| AC-23 | T17 | `CMD-1 CMD-2 CMD-3 CMD-4 CMD-6` | 17 focused, curated, sibling 115, analyzer 30, verifier 62 tests가 모두 exit 0이다. |

<!-- strict-only:start -->

### Threat and trust boundaries

caller CLI → curated source → sibling transport/merger → authenticated `gh` → untrusted GitHub response → caller destinations 경계를 유지한다. 원격 body/URL과 response headers는 비신뢰이고 repository endpoint, filesystem path, authorization 또는 성공 status를 직접 결정할 수 없다. T1은 canonical trust gate와 negative call log, T2~T3은 구조화 header state와 no-speculative-request, T8~T14는 append-only history·resume reconciliation·run-local evidence·paired staging으로 검증한다. warning에는 credential, private body, 전체 header value를 넣지 않는다.

### Authorization and tenant isolation

Tenant isolation은 not applicable이다. 이 도구는 서비스형 multi-tenant system이 아니라 caller의 로컬 process에서 한 tracker run을 처리한다. 대신 tracker/run isolation은 exact manifest discriminator, fingerprint, resume run ID, corpus reconciliation과 run-scoped cache로 판정한다. GitHub write 권한은 없으며 remote text가 기존 read scope를 높일 수 없다.

### Migration, compatibility, and rollback

Schema migration과 data backfill은 not applicable이다. corpus 1.0.0, manifest 2.0.0, exit 0/2/3/4, 기존 full CLI spelling과 sibling source-policy를 유지하고 새 run records에만 공통 필드를 적용한다. 호환성 evidence는 CMD-1~CMD-6이며 rollback은 root가 baseline snapshot에서 이번 변경 파일 bytes를 복원한 뒤 CMD-7·CMD-8을 재실행하는 것이다. 감사 문서 여섯 개와 runtime corpus/manifest는 rollback 중에도 rewrite하지 않는다.

### Failure recovery and observability

Manifest warnings/failed scopes, page provenance, hydration outcomes, request count/events, status/exit, destination pre/post bytes와 task-state RED/GREEN transcript가 로컬 관측 정본이다. Resume mismatch는 input error/2, header·pagination gap은 current-run usable 여부에 따른 partial/3 또는 failed/4, processing failure는 append-only failed run, staging failure는 old destination bytes 보존과 exit 4로 복구한다. 외부 alert/metrics/distributed tracing은 local one-shot CLI이고 새 운영 인프라가 범위 밖이므로 not applicable이다.

### High-risk end-to-end verification

CMD-1 → CMD-2 → CMD-5 → CMD-3 → CMD-4 → CMD-6 → CMD-7 → CMD-8을 network 없이 실행한다. 필수 evidence는 17 exact `ok`, traversal request 부재, terminal/unsupported provenance, manifest prefix와 field parity, mismatch resume request/write 0회, warning/scope 대응, cache call-count/object identity, destination bytes/directory entries, current-run status/exit, CLI abbreviation usage/2, sibling API equality, portable eval diff, baseline 34·115·30·62 regression counts 및 immutable hashes다. RED 양상 불일치, mutation 생존, oracle 무승인 변경, 누락 test, nonzero suite 또는 금지 diff 중 하나라도 있으면 완료하지 않는다. Type check, lint, build, browser E2E와 live API E2E는 repository에 설정이 없거나 금지된 network가 필요하므로 not applicable이며 passed로 기록하지 않는다.

### No production mutation confirmation

자동 workflow에는 production mutation이 없다. 합성 fixture를 쓰는 지정 worktree source/test/eval과 task-state evidence만 다룬다. GitHub live 요청 및 POST/PATCH/PUT/DELETE, Issue/PR/comment/review/label/branch 변경, credential 접근, dependency install, commit, push, PR 생성, merge, deploy, main·다른 worktree·전역 설치본 변경은 수행하지 않는다. commit 이후 동작은 root의 별도 책임이다.

<!-- strict-only:end -->
