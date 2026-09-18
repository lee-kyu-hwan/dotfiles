# Quality Goal Implementation Plan

- Task ID: 20260910T111848Z-80-트래커-issue-코멘트-기반-pr-수집-스킬-collecting-8a205a42
- Mode: strict
- Status: draft
- Created: 2026-09-10
- Updated: 2026-09-10
- Source goal: #80 트래커 Issue 코멘트 기반 PR 수집 스킬 collecting-curated-contribution-prs 구현

## Spec link

- 승인된 Spec: `/Users/lee-kyu-hwan/code/dotfiles__worktrees/80-feat-curated-contribution-prs/docs/development/2026-09-10-80-collecting-curated-contribution-prs/spec.md`
- SHA-256: `586ad7b2e6490b5fbaf09574e1b492e7c4e71bc9794f9f22ef881386b7900d2c`
- 이 Plan은 위 digest의 요구사항 R1.1~R6.5, AC-1~AC-40, CMD-1~CMD-12, 결정 D1~D8을 변경 없이 구현 단계와 검증 단계로 옮긴다.

## Global constraints

- 기준 revision은 `067923b`다. 구현은 현재 worktree 안에서만 수행하고 초기 dirty path 및 #80과 무관한 변경을 보존한다.
- Spec의 `GitHubClient` 표기는 오기이며 실제 심볼은 `GhApiClient`다. 구현은 `collect_recent_closed_prs.py:91`의 `GhApiClient`와 `:117`의 `GhApiClient.get_json`을 참조한다.
- 신규 스킬은 `dot_codex/skills/collecting-curated-contribution-prs/`의 승인된 파일 집합만 소유한다. 형제 스킬에서는 merger 코드, merger 테스트, 병합·출처 계약 문단만 수정한다.
- `collect_repository_hits`, search, partition, 연결된 manifest search 필드, 형제 `references/github-rest-contract.md`, analyzer와 candidate verifier 기능은 변경하지 않는다.
- 구현 순서는 항상 실패하는 검증 추가 및 실행 → 해당 실패만 해소하는 최소 구현 → 같은 검증의 통과 기록이다. 테스트를 삭제·완화하거나 fixture의 기대값을 구현 결함에 맞추지 않는다.
- 모든 테스트와 repository fixture는 명시적으로 합성 데이터만 사용한다. 실제 저장소명, 인물, 멘토 관계, 날짜, 비공개 명부, token, 실명, 이메일, 인증된 원문을 source·test·eval·문서에 넣지 않는다.
- Python 표준 라이브러리와 `unittest`만 사용한다. pytest와 jsonschema는 설치돼 있지 않고 CI/type-check/lint/build 설정도 없으므로 새 의존성이나 CI 설정을 추가하지 않는다.
- GitHub 통신은 기존 `gh` 인증을 사용하는 직렬 read-only GET으로 한정한다. shell 실행, clone, install, GitHub 쓰기, 원격 텍스트가 지정한 경로 쓰기는 금지한다.
- corpus/manifest는 호출자가 지정한 서로 다른 경로에만 원자 저장한다. 기존 JSON과 unknown field/type 및 append-only prefix는 손상시키지 않는다.
- 형제 `_append_source`가 사용하는 `_observation_identity`는 `run_id`를 identity 첫 원소에 포함한다. 이 동작과 형제 dedup 경로는 변경하지 않으며, curated 계층이 `merge_corpus` 호출 전에 run-independent content identity로 중복을 제거한다.
- 신규 revision의 canonical 입력은 `SKILL.md`, `agents/openai.yaml`, `references/collection-contract.md`, `references/github-rest-contract.md`, `scripts/collect_curated_contribution_prs.py`, `tests/test_collect_curated_contribution_prs.py` 여섯 경로뿐이다. fixture와 eval은 digest 입력에서 제외한다.
- 구현자와 평가자는 commit, push, PR 생성, merge, 배포, 전역 설치본 변경을 하지 않는다. 상호 통합 확인과 Git 배포 단계는 root가 소유한다.
- RED baseline에서 이미 통과한 안전 행동은 `test_ac_32_end_to_end_safety_regression`과 행동 평가의 회귀 시나리오로만 고정하고 일반 지침을 중복 구현하지 않는다.

## File map

| 경로 | 작업 | 책임과 영향 인터페이스 |
|---|---|---|
| `docs/development/2026-09-10-80-collecting-curated-contribution-prs/spec.md` | inspect only | 승인 요구사항, AC, 판정 명령, D1~D8의 정본이다. |
| `docs/development/2026-09-10-80-collecting-curated-contribution-prs/plan.md` | inspect only after approval | 구현 순서·범위·검증 handoff의 정본이며 구현 중 수정하지 않는다. |
| `dot_codex/skills/collecting-curated-contribution-prs/SKILL.md` | create | tracker Issue 수집 routing, 인접 스킬/GitHub 쓰기 경계, script/reference/analyzer handoff를 정의한다. 결정 규칙은 복제하지 않는다. |
| `dot_codex/skills/collecting-curated-contribution-prs/agents/openai.yaml` | create | quoted `display_name`, `short_description`, `$collecting-curated-contribution-prs`를 포함한 `default_prompt`를 제공한다. |
| `dot_codex/skills/collecting-curated-contribution-prs/references/collection-contract.md` | create | corpus 1.0.0, manifest 2.0.0, tracker source/observation, cap/budget, resume, status/exit, atomic persistence 계약을 단일 정본으로 둔다. |
| `dot_codex/skills/collecting-curated-contribution-prs/references/github-rest-contract.md` | create | Issue/comment endpoint, `Link rel="next"` 검증, association 분리, read-only GET, retry/budget 계약을 단일 정본으로 둔다. |
| `dot_codex/skills/collecting-curated-contribution-prs/scripts/collect_curated_contribution_prs.py` | create | CLI preflight, `Path(__file__).resolve().parents[2]` 기준 sibling module load, `GhApiClient.get_json`, Issue/comment collection, reference selection, `hydrate_pull_request`, tracker observation의 curated content-identity 선행 dedup, curated `generated_by`를 가진 incoming corpus envelope의 `merge_corpus(..., source_policy="explicit-only")`, exit code, six-file revision을 구현한다. |
| `dot_codex/skills/collecting-curated-contribution-prs/tests/test_collect_curated_contribution_prs.py` | create | AC exact-method 계약, fake runner, 실제 CLI/JSON/exit code, corpus/manifest/merge/revision/meta 검증을 표준 라이브러리로 수행한다. |
| `dot_codex/skills/collecting-curated-contribution-prs/tests/fixtures/tracker-thread.json` | create | 합성 Issue 본문, 짧은 첫 page와 유효 next Link, 두 comment page, 중복 PR reference, 예시·공지·주입 text를 제공한다. |
| `dot_codex/skills/collecting-curated-contribution-prs/tests/fixtures/tracker-thread-edited.json` | create | 동일 comment node의 changed updated timestamp/body와 unchanged 재수집 대조를 제공한다. |
| `dot_codex/skills/collecting-curated-contribution-prs/tests/fixtures/tracker-thread-failures.json` | create | malformed/cursor/`before`/`after`/page-mismatch Link, comment ID 중복·역행, pagination/budget/preflight 실패를 제공한다. |
| `dot_codex/skills/collecting-curated-contribution-prs/tests/fixtures/pr-hydration.json` | create | 합성 resolved/open/role mapping 및 inaccessible/hydration failure 응답을 제공한다. |
| `dot_codex/skills/collecting-curated-contribution-prs/tests/fixtures/initial-corpus.json` | create | analyzer-valid recent/tracker prefix와 unknown JSON field/type을 가진 append-only 기준 corpus다. |
| `dot_codex/skills/collecting-curated-contribution-prs/tests/fixtures/expected-corpus.json` | create | T5만 실제 fresh CLI output에서 committed bytes를 작성·변경하는 corpus 1.0.0 oracle이며 CMD-6 입력이다. T4는 이 파일을 만들거나 바꾸지 않는다. |
| `dot_codex/skills/collecting-curated-contribution-prs/tests/fixtures/recollected-corpus.json` | create | unchanged dedup와 edited append 결과 oracle이며 CMD-7 입력이다. |
| `dot_codex/skills/collecting-curated-contribution-prs/tests/fixtures/manifest-cases.json` | create | valid same-tracker resume/append와 date-range, foreign method, foreign tracker repository/Issue discriminator 사례를 제공한다. |
| `dot_codex/skills/collecting-curated-contribution-prs/evals/behavioral-eval.md` | create | 합성 fixture를 새 컨텍스트에서 실제 스킬로 수행한 prompt, 명령, 경로, status, exit code, 산출물, 주입 무시 판정을 기록한다. |
| `dot_codex/skills/collecting-recent-closed-prs/scripts/collect_recent_closed_prs.py` | modify | base의 `merge_corpus`(933), 신규 record의 `_append_recent_observation` 호출(1019), `_validate_incoming_observation_identities`(1053), `_coalesce_incoming_records` 내부 호출(1197), `_coalesce_record_into`의 `_append_sources` 호출(1226), `_merge_existing_record`의 `_append_sources` 호출(1412), `_append_sources`의 `_append_source` 호출(1440), `_append_source`(1443), `_append_recent_observation`(1462)에 keyword-only `source_policy`를 전달한다. 세 coalescing/matched 함수는 파라미터 전달 외 동작을 바꾸지 않고 transport/search와 `_observation_identity`도 그대로 둔다. |
| `dot_codex/skills/collecting-recent-closed-prs/tests/test_collect_recent_closed_prs.py` | modify | 기본값과 명시적 `recent-closed` 동일성, unknown policy 거부, `explicit-only`의 coalesced/matched/new record 출처를 회귀 고정한다. |
| `dot_codex/skills/collecting-recent-closed-prs/references/collection-contract.md` | modify | 기본 `recent-closed`와 `explicit-only`의 validation/append 의미 및 caller 책임만 병합·출처 문단에 추가한다. |
| `dot_codex/skills/analyzing-open-source-pr-patterns/scripts/validate_corpus.py` | inspect only | `_validate_document` 및 `--existing`을 corpus 호환성 oracle로 사용한다. |

## Task dependencies

1. T1은 형제 merger의 `source_policy` 인터페이스만 먼저 제공하고 형제 `_observation_identity`와 기존 dedup 동작은 보존한다. T3~T5는 이 인터페이스를 소비하며 T1 완료 전 curated merge를 구현하지 않는다.
2. T2는 신규 스킬의 파일 구조, CLI spelling, `__file__` 기준 sibling module load, 계약 문서 경계를 제공한다. T3은 T2의 parser, request budget, `GhApiClient` adapter를 소비한다.
3. T3은 이름이 고정된 tracker observation 필드와 검증된 comment/reference/manifest state-machine을 산출한다. T4는 existing corpus와 incoming run을 상대로 curated content identity 선행 dedup을 수행하고 `initial-corpus.json` 및 `recollected-corpus.json`을 확정한다.
4. T4의 analyzer-valid append-only 결과가 T5의 실제 end-to-end oracle 선행조건이다. T5만 실제 fresh CLI output을 근거로 `expected-corpus.json` bytes를 작성·변경하고, fresh collection과 existing corpus handoff를 완성한 뒤 CMD-6을 판정한다.
5. T6의 revision/meta-test는 T2~T5에서 canonical source와 모든 filtered exact test method가 확정된 뒤 수행한다. T6은 전체 deterministic gate와 형제 regression을 함께 닫는다.
6. T7 행동 평가는 T1~T6이 모두 통과한 source revision을 새 컨텍스트에서 사용한다. 평가 중 발견된 code defect는 문서로 덮지 않고 소유 태스크로 돌아가 최소 수정 후 T6 전체 gate부터 다시 수행한다.
7. 동일 파일을 병렬 수정하지 않는다. 특히 T1의 형제 세 파일은 PR #102 통합 확인 대상이므로 단일 구현자가 merger 함수 범위만 수정하고 root가 후속 통합을 맡는다.

## Tasks

### T1. 형제 merger의 source-policy 기본 호환성과 explicit-only 경계를 고정한다

대상 AC: AC-15 — CMD-8

- 선행조건: base `067923b`; 형제 collector baseline에서 CMD-8이 `Ran 110 tests`, `OK`, 종료 코드 0임을 먼저 기록한다.
- 실패 검증: `test_collect_recent_closed_prs.py`에 아래 다섯 테스트를 먼저 추가하고 CMD-8을 실행한다. `test_merge_corpus_default_source_policy_preserves_recent_closed_behavior`는 수정 전에도 통과해야 하는 characterization 테스트다. 나머지 네 테스트는 수정 전에 실패해야 한다: `test_merge_corpus_explicit_recent_closed_matches_default`, `test_merge_corpus_explicit_only_does_not_synthesize_recent_closed`, `test_merge_corpus_explicit_only_propagates_through_coalesced_matched_and_new_records`는 `TypeError: merge_corpus() got an unexpected keyword argument 'source_policy'`, `test_merge_corpus_rejects_unknown_source_policy`는 요구한 `ValueError` 대신 같은 unexpected-keyword `TypeError`가 발생하는 것이 기대 RED 양상이다. characterization이 실패하거나 네 RED 중 하나라도 뜻밖에 통과하면 구현을 시작하지 않고 baseline/test setup을 바로잡는다.
- 최소 구현: `merge_corpus(..., *, source_policy="recent-closed", ...)`에서 허용값을 즉시 검증한다. 신규 record 경로의 `_append_recent_observation` 호출(1019), `_coalesce_incoming_records` 안의 호출(1197), `_coalesce_record_into` 안의 `_append_sources` 호출(1226), `_merge_existing_record` 안의 `_append_sources` 호출(1412), `_append_sources` 안의 `_append_source` 호출(1440)이 policy를 실제 소비하므로 incoming identity validation, coalescing, matched merge, new record append까지 keyword-only로 전달한다. `_append_sources`, `_append_source`, `_append_recent_observation`, `_validate_incoming_observation_identities`가 동일 policy를 받게 하되, `_coalesce_incoming_records`, `_coalesce_record_into`, `_merge_existing_record`에서는 파라미터 전달 외 어떤 동작도 바꾸지 않는다. `recent-closed`는 기존 합성을 그대로 수행하고 `explicit-only`는 incoming source/observation만 append한다. `_observation_identity`는 `run_id`를 포함하는 현재 구현 그대로이며 curated 계층이 이 전제에 맞춰 선행 dedup한다.
- 계약 문서: 형제 collection contract의 병합·출처 문단에 두 정책, 기본값 호환성, unknown 값의 `ValueError`, curated caller의 `explicit-only` 의무를 기록한다. search/partition/transport 문단은 건드리지 않는다.
- 통과 검증: CMD-8이 종료 코드 0이며 새 다섯 테스트와 기존 110 테스트가 모두 `OK`다. 기존 여섯 경로 revision framing 테스트도 통과하되 source 변경으로 digest 값이 달라지는 것은 실패로 보지 않는다. 이 결과로 omitted/default `recent-closed` dedup과 `run_id`를 포함하는 형제 `_observation_identity`가 바뀌지 않았음도 확인한다.
- 실패 처리: 기존 테스트 하나라도 깨지거나 explicit-only가 한 경로에서 recent source를 만들면 T2로 진행하지 않고 policy 전달 경로만 수정해 CMD-8을 다시 실행한다.

### T2. 신규 스킬 패키지와 caller-owned CLI 계약을 세운다

대상 AC: AC-1 — CMD-2 `test_ac_01_contract_routing`
대상 AC: AC-2 — CMD-2 `test_ac_02_contract_cli_validation`
대상 AC: AC-3 — CMD-2 `test_ac_03_contract_packaging`; CMD-5
대상 AC: AC-26 — CMD-2 `test_ac_26_contract_public_fixtures`

- 선행조건: T1 통과. 산출 인터페이스는 `collect` subcommand의 `--tracker-repo`, `--issue`, `--max-prs`, `--request-budget`, `--output`, `--manifest`, 선택적 `--existing-corpus`, `--existing-manifest`, `--resume-run-id`와 top-level `--print-revision`이다.
- 실패 검증: 합성 fixture 및 `test_ac_01_contract_routing`, `test_ac_02_contract_cli_validation`, `test_ac_03_contract_packaging`, `test_ac_26_contract_public_fixtures`를 먼저 작성한다. `sh -c 'for test_id in test_ac_01_contract_routing test_ac_02_contract_cli_validation test_ac_03_contract_packaging test_ac_26_contract_public_fixtures; do PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -v -s dot_codex/skills/collecting-curated-contribution-prs/tests -t dot_codex/skills/collecting-curated-contribution-prs/tests -p "test_*.py" -k "$test_id" || exit $?; done'`를 실행하고, 신규 source/metadata/parser가 없거나 fake client가 잘못 호출되어 비영 종료하는 것을 기록한다.
- 최소 구현: `SKILL.md`, `agents/openai.yaml`, 두 reference, script skeleton을 만든다. `SKILL.md`는 routing과 경계만 두고 deterministic 규칙을 reference/script로 보낸다. parser는 repository/positive integer cap·budget/positive Issue/output alias/existing+resume 조합을 network 전에 검사한다. sibling 경로는 정확히 `Path(__file__).resolve().parents[2] / "collecting-recent-closed-prs" / "scripts" / "collect_recent_closed_prs.py"`로 계산한다(`parents[0]`은 `scripts`, `parents[1]`은 curated 스킬 디렉터리, `parents[2]`는 `skills`). `importlib.util.spec_from_file_location`으로 한 번 load해 실제 `GhApiClient`, `RequestBudget`, `hydrate_pull_request`, `merge_corpus`, atomic JSON helper를 재사용한다. 파일이 없으면 network 전에 stderr에 `error: collecting-recent-closed-prs sibling script not found: <resolved-path>`를 정확히 한 줄 출력하고 종료 코드 2를 반환한다.
- 작업 디렉터리 회귀: T2가 소유하는 `test_ac_02_contract_cli_validation`은 repository root가 아닌 temporary directory를 `cwd`로 둔 subprocess CLI 실행이 성공하는 경우와 sibling path의 존재 검사를 false로 고정한 경우가 위 결정적 오류 한 줄·exit 2·GitHub 호출 0회가 되는 경우를 함께 검증한다.
- 안전 검사: contract test는 승인 파일 집합, YAML quoted interface, forbidden extra guide files, 합성 표기, credential/private marker 부재, fixture 밖 실제 사례 하드코딩, runtime private input의 caller destination 밖 복사를 검사한다.
- 통과 검증: `sh -c 'for test_id in test_ac_01_contract_routing test_ac_02_contract_cli_validation test_ac_03_contract_packaging test_ac_26_contract_public_fixtures; do PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -v -s dot_codex/skills/collecting-curated-contribution-prs/tests -t dot_codex/skills/collecting-curated-contribution-prs/tests -p "test_*.py" -k "$test_id" || exit $?; done'`가 네 exact ID 각각 `ok`, 최종 종료 코드 0을 내고 CMD-5가 종료 코드 0과 `Skill is valid!`를 출력한다. 전체 CMD-2는 T6에서 exact mapping meta-test까지 추가한 뒤 최종 판정한다.
- 실패 처리: skill validator 또는 package allowlist가 실패하면 새 파일을 늘리지 않고 canonical source/metadata/reference 경계만 수정한다.

### T3. Link 기반 comment collection, shared budget, manifest lifecycle과 원자 출력을 구현한다

대상 AC: AC-4 — CMD-3 `test_ac_04_collection_link_page_validation`
대상 AC: AC-6 — CMD-3 `test_ac_06_collection_cap_counts`
대상 AC: AC-7 — CMD-3 `test_ac_07_collection_shared_budget`
대상 AC: AC-9 — CMD-3 `test_ac_09_collection_role_separation`
대상 AC: AC-13 — CMD-3 `test_ac_13_collection_observation_provenance`
대상 AC: AC-21 — CMD-3 `test_ac_21_collection_resume_append`
대상 AC: AC-22 — CMD-3 `test_ac_22_collection_fingerprint_mismatch`
대상 AC: AC-23 — CMD-3 `test_ac_23_collection_partial_gaps`
대상 AC: AC-24 — CMD-3 `test_ac_24_collection_exit_matrix`
대상 AC: AC-25 — CMD-3 `test_ac_25_collection_atomic_output`
대상 AC: AC-39 — CMD-3 `test_ac_39_collection_rejects_foreign_manifest`

- 선행조건: T1의 policy와 T2의 CLI/client interface. 산출물은 ordered origin references, tracker observations, request/page provenance, capped selection, run/fingerprint/checkpoint 상태다.
- 실패 검증: `test_ac_04_collection_link_page_validation`, `test_ac_06_collection_cap_counts`, `test_ac_07_collection_shared_budget`, `test_ac_09_collection_role_separation`, `test_ac_13_collection_observation_provenance`, `test_ac_21_collection_resume_append`, `test_ac_22_collection_fingerprint_mismatch`, `test_ac_23_collection_partial_gaps`, `test_ac_24_collection_exit_matrix`, `test_ac_25_collection_atomic_output`, `test_ac_39_collection_rejects_foreign_manifest`와 필요한 합성 fixture를 먼저 추가하고 CMD-3을 실행한다. 구현 전에는 필수 ID 중 하나 이상이 실패해 종료 코드가 비영이어야 하며 0건 선택의 종료 코드 5도 실패로 기록한다.
- 최소 구현: Issue core와 comments page를 상대 endpoint/`page`만으로 `GhApiClient.get_json`에 전달한다. `Link rel="next"` 원문을 보존한 뒤 host, exact comments path, supported query, current+1 page, optional `per_page=100`을 검증하고 유효할 때만 다음 page를 요청한다. payload 길이 추측, cursor, `before`/`after`, page mismatch는 요청 없이 gap으로 남긴다.
- 최소 구현: comment database ID를 전체 page에서 엄격 오름차순 검증하고, first-reference 순서의 고유 제출 PR에 cap을 적용한다. body/comment origin, edited content hash, raw tracker association을 남기되 upstream role과 분리한다. 모든 request attempt는 preflight/pagination/hydration/retry/resume 공용 budget과 누적 request events를 소비한다.
- 최소 구현: manifest 2.0.0 run/fingerprint/discriminator, append와 exact resume, counts/outcomes/warnings/failed scopes/status와 exit 0/2/3/4를 구현한다. foreign generator/method/tracker identity는 network와 destination 변경 전에 거부한다. corpus/manifest는 sibling temporary file을 사용해 UTF-8 trailing newline으로 원자 교체한다.
- 통과 검증: CMD-3이 종료 코드 0이고 위 11개 exact ID가 모두 `ok`다. fake runner에는 invalid Link 이후 요청이 없고 output replace failure 뒤 destination bytes와 directory listing이 이전과 동일해야 한다.
- 실패 처리: gap을 complete로 만들거나 budget을 초과하거나 foreign manifest에서 network가 관측되면 checkpoint/status를 완화하지 않고 state transition과 preflight 순서만 수정한 뒤 CMD-3 전체를 재실행한다.

### T4. 글로벌 PR identity 병합, explicit source, 재수집과 projection prefix를 구현한다

대상 AC: AC-14 — CMD-4 `test_ac_14_merge_global_identity`
대상 AC: AC-16 — CMD-4 `test_ac_16_merge_explicit_only_sources`
대상 AC: AC-17 — CMD-4 `test_ac_17_merge_recollection_idempotency`
대상 AC: AC-18 — CMD-7
대상 AC: AC-19 — CMD-4 `test_ac_19_merge_projection_history`
대상 AC: AC-38 — CMD-4 `test_ac_38_merge_preserves_generated_by`

- 선행조건: T1의 `source_policy="explicit-only"`, T3의 tracker observations와 manifest provenance. T4가 작성·변경하는 fixture는 analyzer-valid `initial-corpus.json`과 `recollected-corpus.json`뿐이다. `expected-corpus.json`의 committed bytes는 T5만 소유하므로 T4는 만들거나 바꾸지 않는다.
- 실패 검증: `test_ac_14_merge_global_identity`, `test_ac_16_merge_explicit_only_sources`, `test_ac_17_merge_recollection_idempotency`, `test_ac_19_merge_projection_history`, `test_ac_38_merge_preserves_generated_by`를 먼저 추가하고 CMD-4를 실행한다. 특히 `test_ac_17_merge_recollection_idempotency`는 probe와 같은 tracker 관측을 `run_id="tracker-run-A"`로 한 번 병합한 뒤 같은 content를 `run_id="tracker-run-B"`로 재수집한다. curated 선행 dedup이 없는 수정 전 경로에서는 형제 `_observation_identity`가 두 run을 다른 identity로 보아 관측이 2건이 되므로 기대값 1건에 실패함을 먼저 기록한다. 같은 테스트에서 동일 comment node의 `updated_at` 또는 `body_sha256`을 바꾼 편집 재수집은 기존 prefix 뒤에 정확히 1건이 append되어야 한다. CMD-7도 recollected oracle이 없거나 prefix가 맞지 않아 비영 종료해야 한다.
- tracker 관측 필드 배치: 댓글 관측은 `run_id`, `comment_id`, `comment_node_id`, `comment_url`, `comment_html_url`, `commenter_login`, `tracker_author_association`, `created_at`, `updated_at`, `body_sha256`을 가진다. Issue 본문 관측은 `origin_kind`, `issue_node_id`, `issue_url`, `updated_at`, `body_sha256`, `run_id`를 가진다. 두 종류 모두 run ID를 담는 키는 정확히 `run_id`이며 provenance 전용이다.
- curated content identity와 강제 지점: 댓글 identity는 `(comment_node_id, updated_at, body_sha256)`, Issue 본문 identity는 `(issue_node_id, updated_at, body_sha256)`이고 `run_id`를 포함하지 않는다. curated 수집기는 `merge_corpus` 호출 전에 주어진 existing corpus에서 같은 global PR node identity의 record와 같은 tracker `source_key`의 source를 찾아 기존 관측의 content identity 집합을 만든다. incoming 관측을 원래 순서로 순회하면서 기존 집합에 있거나 같은 run의 앞선 incoming 관측과 같은 content identity는 제외하고, 처음 본 관측을 집합에 추가해 남은 진짜 새 관측만 형제 merger에 전달한다. 같은 comment node의 `updated_at` 또는 `body_sha256`이 바뀌면 content identity가 달라지므로 기존 관측 뒤에 append한다. 형제 `_observation_identity`가 `run_id`를 포함한다는 동작은 이 curated 선행 처리의 고정 전제이며 변경하지 않는다.
- 최소 구현: resolved record를 global PR node ID와 repository node ID로 형제 hydration/merge에 넘기고 curated 병합은 항상 `source_policy="explicit-only"`를 지정한다. tracker source key는 Issue node ID에서 결정적으로 namespace한다. 모든 호출은 bare record list가 아니라 `{"schema_version":"1.0.0","generated_by":{"name":"collecting-curated-contribution-prs","revision":<current-revision>},"records":[...]}` 형태의 incoming corpus envelope를 넘긴다. existing corpus가 있으면 형제 merger가 기존 envelope `generated_by`를 보존하고, fresh이면 incoming의 curated name/revision이 결과 envelope에 남는다.
- 최소 구현: same payload는 observation/state count를 늘리지 않고 edit는 정확한 prefix 뒤에 한 건을 append한다. latest authoritative PR timestamp만 projection을 바꾸고 inaccessible evidence는 failure basis의 unknown만 허용한다. 기존 `pr_id`, resolved identity, envelope `generated_by`, source metadata/order, observations, state history, unknown field/type은 deep-equal prefix로 보존한다.
- 양방향 대조: recent-existing+curated-incoming에서는 real recent 뒤 tracker만, curated-existing+real recent-incoming에서는 tracker 뒤 실제 recent만 남긴다. tracker-only record에 `recent-closed`가 없음을 byte-level JSON assertion으로 확인한다.
- 통과 검증: CMD-4의 다섯 exact ID가 모두 `ok`이고, `test_ac_17_merge_recollection_idempotency`에서 unchanged 재수집은 1건 유지·edited 재수집은 정확히 1건 append되며, CMD-7이 종료 코드 0과 append-only validation 성공을 출력한다. T4의 통과 조건에는 T5 소유 fixture를 입력으로 쓰는 CMD-6을 넣지 않는다.
- 실패 처리: analyzer prefix 실패는 fixture를 재생성해 숨기지 않는다. 첫 differing JSON path를 기록하고 merger/record builder의 해당 경로만 수정한 뒤 CMD-4와 CMD-7을 함께 재실행한다.

### T5. 실제 CLI end-to-end corpus/manifest handoff를 완성한다

대상 AC: AC-5 — CMD-12 `test_ac_05_end_to_end_reference_normalization`
대상 AC: AC-8 — CMD-12 `test_ac_08_end_to_end_authoritative_hydration`
대상 AC: AC-10 — CMD-12 `test_ac_10_end_to_end_injection_is_data`
대상 AC: AC-11 — CMD-6
대상 AC: AC-12 — CMD-12 `test_ac_12_end_to_end_corpus_invariants`
대상 AC: AC-20 — CMD-12 `test_ac_20_end_to_end_manifest_provenance`
대상 AC: AC-27 — CMD-12 `test_ac_27_end_to_end_read_only_runner`
대상 AC: AC-31 — CMD-12 `test_ac_31_end_to_end_red_to_green`
대상 AC: AC-32 — CMD-12 `test_ac_32_end_to_end_safety_regression`
대상 AC: AC-37 — CMD-12 `test_ac_37_end_to_end_fresh_generated_by`

- 선행조건: T2 CLI, T3 collection state, T4 merge/oracle. 산출 인터페이스는 fresh CLI exit 0 corpus/manifest와 partial/failed CLI exits다.
- 실패 검증: `test_ac_05_end_to_end_reference_normalization`, `test_ac_08_end_to_end_authoritative_hydration`, `test_ac_10_end_to_end_injection_is_data`, `test_ac_12_end_to_end_corpus_invariants`, `test_ac_20_end_to_end_manifest_provenance`, `test_ac_27_end_to_end_read_only_runner`, `test_ac_31_end_to_end_red_to_green`, `test_ac_32_end_to_end_safety_regression`, `test_ac_37_end_to_end_fresh_generated_by`를 먼저 추가하고 CMD-12를 실행한다. 실제 CLI orchestration 또는 expected artifact 불일치로 비영 종료해야 한다. `expected-corpus.json`을 쓰기 전 CMD-6이 파일 부재로 비영 종료하는 RED도 기록한다.
- 최소 구현: caller validation → preflight → Issue/comments → reference classification/cap → authoritative hydration → tracker source build → curated content-identity 선행 dedup → explicit-only merge → atomic corpus/manifest checkpoint/final 순서를 연결한다. 모든 curated merge는 bare record list가 아닌 incoming corpus envelope를 넘기며, envelope의 `generated_by`는 `name: "collecting-curated-contribution-prs"`와 현재 curated revision이다. fresh 결과와 manifest run에는 이 name/revision을 기록하고 existing corpus의 top-level envelope generator는 형제 merger가 바꾸지 않게 한다. T5만 성공한 deterministic fresh CLI output과 테스트 oracle이 deep-equal임을 확인한 뒤 그 정확한 bytes로 `expected-corpus.json`을 작성하며, 이후 이 fixture를 변경할 수 있는 태스크도 T5뿐이다.
- 신뢰 경계: PR/Issue/comment text는 hash/evidence/reference classification 입력일 뿐 argv, method, path, budget, role, PR state, retry, final status를 결정하지 않는다. fake runner는 모든 GitHub 호출이 `gh api --method GET`, `shell=False`인지와 clone/install/write/추가 network/지정 외 path write 0회를 검사한다.
- RED 회귀: edited provenance, tracker/upstream role 분리, analyzer-compatible corpus, deterministic run/manifest, unchanged/edited recollection을 GREEN으로 만들고, 이미 안전했던 주입 무시·예시/공지 제외·open 유지·404 비삭제·private roster 비사용·partial honesty는 하나의 회귀 scenario로 고정한다.
- 통과 검증: CMD-12가 종료 코드 0이고 위 아홉 exact ID가 모두 `ok`; CMD-6이 종료 코드 0과 validated record 수를 출력한다. temporary 실제 output bytes와 committed expected fixture가 deep-equal이어야 한다.
- 실패 처리: usable evidence gap이 생기면 expected complete fixture를 낮추지 않고 manifest `partial`, failed scope, 종료 코드 3을 고친다. global/no-usable 실패는 기존 corpus를 보존하고 failed/4를 유지한다.

### T6. revision, judgement mapping, packaging과 전체 회귀 gate를 닫는다

대상 AC: AC-28 — CMD-1; CMD-11; CMD-8
대상 AC: AC-29 — CMD-1
대상 AC: AC-33 — CMD-8
대상 AC: AC-34 — CMD-9
대상 AC: AC-35 — CMD-10
대상 AC: AC-36 — CMD-5
대상 AC: AC-40 — CMD-2 `test_ac_40_contract_judgement_mapping`

- 선행조건: T1~T5의 모든 canonical source와 filtered exact test method가 확정되어 있다.
- 실패 검증: canonical path별 byte mutation revision test와 `test_ac_40_contract_judgement_mapping`을 먼저 추가한다. CMD-1, CMD-2, CMD-11을 실행해 revision 미구현 또는 AC→CMD→filter→method mapping 누락으로 적어도 하나가 비영 종료하는 것을 기록한다. 0건 선택은 종료 코드 5이므로 통과로 취급하지 않는다.
- 최소 구현: six-file sorted relative path 각각에 unsigned 8-byte big-endian path length/path bytes/content length/raw bytes framing을 적용해 lowercase `sha256:` digest를 출력한다. meta-test는 Spec의 filtered 실행 AC 집합과 exact token, 2-digit AC 번호, CMD filter, discover된 method를 일대일 대조하고 자기 자신도 verbose 선택되게 한다.
- packaging 확인: CMD-5로 system validator를 실행하고 fixture/eval이 revision 입력에 없으며 canonical file 한 byte mutation마다 digest가 달라짐을 CMD-1 test로 확인한다.
- 기본값 회귀 별도 확인: CMD-8을 다시 실행해 T1에서 보존한 기존 110 tests가 전부 계속 통과하며 새 source-policy tests도 통과함을 기록한다. 이어 CMD-9와 CMD-10으로 무수정 analyzer와 verifier suite 회귀를 확인한다.
- 통과 검증: CMD-1~CMD-5, CMD-8~CMD-11이 모두 각 표의 성공 조건을 만족한다. 특히 CMD-2는 AC-1·AC-2·AC-3·AC-26·AC-40 exact ID 전부가 `ok`, CMD-11은 정확히 한 줄의 revision만 출력한다.
- 실패 처리: 전체 suite 실패는 관련 소유 태스크로 돌아가 최소 수정하고, 변경된 source digest를 기록한 뒤 CMD-1부터 이 태스크의 전체 순서를 다시 실행한다. analyzer/verifier 기능을 수정해 회귀를 피하지 않는다.

### T7. 새 컨텍스트의 합성 행동 평가를 증거 문서로 고정한다

대상 AC: AC-30 — `dot_codex/skills/collecting-curated-contribution-prs/evals/behavioral-eval.md`

- 선행조건: T6 전체 gate를 통과한 exact curated revision과 합성 tracker fixture. 구현 author의 추론이나 test transcript를 평가 결과로 재사용하지 않는다.
- 실패 검증: `test -s dot_codex/skills/collecting-curated-contribution-prs/evals/behavioral-eval.md`를 실행해 문서가 아직 없어 비영 종료함을 기록한다.
- 최소 구현: root가 마련한 새 독립 Codex 컨텍스트에 실제 `SKILL.md`, 합성 fixture, caller 지정 임시 corpus/manifest 경로만 제공한다. 평가자는 스킬의 실제 routing과 script 호출을 따르며 live GitHub나 private data를 사용하지 않는다.
- 증거 작성: `behavioral-eval.md`에 synthetic 표시, evaluator/context 식별, exact input prompt와 fixture revision, 실제 실행 명령·argv·경로·option, stdout/stderr, 각 exit code, corpus/manifest 위치와 digest, observed status, 주입 문구가 command/path/option/status에 들어가지 않았다는 판정, RED-1~RED-5 및 기존 안전 회귀 결과를 모두 실제 값으로 기록한다.
- 통과 검증: `test -s dot_codex/skills/collecting-curated-contribution-prs/evals/behavioral-eval.md`가 종료 코드 0이고, 문서 검토에서 위 증거 필드가 모두 채워져 있으며 CMD-12 → CMD-6 → CMD-7 → CMD-8을 다시 실행해 모두 통과한다.
- 실패 처리: injection이 control로 전달되거나 산출물/exit evidence가 누락되면 평가 문서만 성공으로 작성하지 않는다. 해당 소유 태스크를 수정하고 T6 gate와 독립 평가를 새 컨텍스트에서 처음부터 반복한다.

## Verification commands

판정 명령은 아래 순서로 실행한다. 필터 명령은 종료 코드 0만으로 충분하지 않으며 표에 지정한 모든 exact test ID의 verbose `ok`를 확인한다.

| ID | 명령 | 통과 조건 |
|---|---|---|
| CMD-1 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_codex/skills/collecting-curated-contribution-prs/tests -t dot_codex/skills/collecting-curated-contribution-prs/tests -p 'test_*.py'` | 종료 코드 0 |
| CMD-2 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -v -s dot_codex/skills/collecting-curated-contribution-prs/tests -t dot_codex/skills/collecting-curated-contribution-prs/tests -p 'test_*.py' -k contract` | 종료 코드 0이고 AC-1·AC-2·AC-3·AC-26·AC-40의 exact ID가 모두 `ok`; `NO TESTS RAN`, 종료 코드 5, 필수 ID 누락은 실패 |
| CMD-3 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -v -s dot_codex/skills/collecting-curated-contribution-prs/tests -t dot_codex/skills/collecting-curated-contribution-prs/tests -p 'test_*.py' -k collection` | 종료 코드 0이고 AC-4·AC-6·AC-7·AC-9·AC-13·AC-21·AC-22·AC-23·AC-24·AC-25·AC-39의 exact ID가 모두 `ok`; 0건 선택과 필수 ID 누락은 실패 |
| CMD-4 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -v -s dot_codex/skills/collecting-curated-contribution-prs/tests -t dot_codex/skills/collecting-curated-contribution-prs/tests -p 'test_*.py' -k merge` | 종료 코드 0이고 AC-14·AC-16·AC-17·AC-19·AC-38의 exact ID가 모두 `ok`; 0건 선택과 필수 ID 누락은 실패 |
| CMD-5 | `/opt/homebrew/bin/python3 /Users/lee-kyu-hwan/.codex/skills/.system/skill-creator/scripts/quick_validate.py dot_codex/skills/collecting-curated-contribution-prs` | 종료 코드 0과 `Skill is valid!` 출력 |
| CMD-6 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 dot_codex/skills/analyzing-open-source-pr-patterns/scripts/validate_corpus.py dot_codex/skills/collecting-curated-contribution-prs/tests/fixtures/expected-corpus.json` | 종료 코드 0과 validated record 수 출력 |
| CMD-7 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 dot_codex/skills/analyzing-open-source-pr-patterns/scripts/validate_corpus.py dot_codex/skills/collecting-curated-contribution-prs/tests/fixtures/recollected-corpus.json --existing dot_codex/skills/collecting-curated-contribution-prs/tests/fixtures/initial-corpus.json` | 종료 코드 0과 append-only validation 성공 출력 |
| CMD-8 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_codex/skills/collecting-recent-closed-prs/tests -t dot_codex/skills/collecting-recent-closed-prs/tests -p 'test_*.py'` | 종료 코드 0; 기존 110 tests와 새 merger tests, 기존 동작과 six-file revision 회귀가 모두 통과 |
| CMD-9 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_codex/skills/analyzing-open-source-pr-patterns/tests -t dot_codex/skills/analyzing-open-source-pr-patterns/tests -p 'test_*.py'` | 종료 코드 0 |
| CMD-10 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_codex/skills/verifying-open-source-contribution-candidates/tests -t dot_codex/skills/verifying-open-source-contribution-candidates/tests -p 'test_*.py'` | 종료 코드 0 |
| CMD-11 | `sh -c 'set -o pipefail; PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 dot_codex/skills/collecting-curated-contribution-prs/scripts/collect_curated_contribution_prs.py --print-revision | rg -x "sha256:[0-9a-f]{64}"'` | 종료 코드 0이고 출력이 revision 형식과 정확히 일치 |
| CMD-12 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -v -s dot_codex/skills/collecting-curated-contribution-prs/tests -t dot_codex/skills/collecting-curated-contribution-prs/tests -p 'test_*.py' -k end_to_end` | 종료 코드 0이고 AC-5·AC-8·AC-10·AC-12·AC-20·AC-27·AC-31·AC-32·AC-37의 exact ID가 모두 `ok`; 0건 선택과 필수 ID 누락은 실패 |

최종 strict 순서는 CMD-1 → CMD-2 → CMD-3 → CMD-4 → CMD-5 → CMD-11 → CMD-12 → CMD-6 → CMD-7 → CMD-8 → CMD-9 → CMD-10이다. type check, lint, build, browser E2E는 설정이 없어 not applicable이며 통과로 기록하지 않는다.

## Rollout and rollback

1. T1~T7과 최종 strict 명령이 모두 통과하기 전 배포하지 않는다. 구현자는 source/test/eval과 검증 transcript만 root에 handoff한다.
2. PR #102와 같은 `collect_recent_closed_prs.py`, `test_collect_recent_closed_prs.py`, `collection-contract.md`를 수정하므로 함수 단위 충돌이 없어도 merge conflict가 가능하다. root는 merger-only diff와 search/partition diff를 함께 검토하고 CMD-8을 통합 결과에서 다시 실행한다. collector 전체 배포는 이 상호 통합 확인 전까지 보류한다.
3. root만 commit, push, PR, merge, 배포를 수행한다. 구현자와 평가자는 Git 쓰기 명령이나 전역 설치본 변경을 수행하지 않는다.
4. rollback trigger는 기존 collector 회귀, explicit-only 출처 위조, analyzer prefix 실패, foreign manifest 수락, private fixture 유출, injection control 전달, 필수 exact test ID 미실행이다. trigger가 있으면 배포를 중단하고 root가 신규 스킬 변경과 형제 merger policy 변경을 함께 되돌린 뒤 CMD-8~CMD-10으로 기존 기능을 확인한다.
5. corpus/manifest schema migration과 backfill은 없다. 이미 생성된 runtime artifact는 삭제·rewrite하지 않고 생성 revision과 partial/failed evidence를 보존한 채 사용 중지한다.
6. 형제 collector를 curated manifest에 잘못 겨눠 오염된 manifest는 변형하지 말고 새 manifest 경로로 시작한다. 형제 collector에 역방향 상호 discriminator 검사를 추가하는 일은 이번 범위가 아니다.

## Acceptance-criteria traceability

| Criterion | Task | Verification command | Expected outcome |
|---|---|---|---|
| AC-1 | T2 | CMD-2 `test_ac_01_contract_routing` | skill name/description이 tracker Issue로 routing하고 인접 세 스킬과 GitHub 쓰기를 제외한다. |
| AC-2 | T2 | CMD-2 `test_ac_02_contract_cli_validation` | 유효 caller 입력만 parse되고 invalid/alias/incomplete resume은 fake client 0회로 거부된다. |
| AC-3 | T2 | CMD-2 `test_ac_03_contract_packaging`; CMD-5 | 승인 파일 집합과 YAML interface만 존재하고 system validator가 성공한다. |
| AC-4 | T3 | CMD-3 `test_ac_04_collection_link_page_validation` | valid next page만 상대 endpoint/page로 GET되고 invalid Link는 추가 요청 없이 partial이다. |
| AC-5 | T5 | CMD-12 `test_ac_05_end_to_end_reference_normalization` | 고유 제출 PR과 origin observations가 보존되고 예시·공지는 exclusion으로 분리된다. |
| AC-6 | T3 | CMD-3 `test_ac_06_collection_cap_counts` | first-reference 고유 PR cap과 matched/selected/excluded counts가 정확하다. |
| AC-7 | T3 | CMD-3 `test_ac_07_collection_shared_budget` | 모든 request attempt가 resume에도 재설정되지 않는 하나의 budget을 사용한다. |
| AC-8 | T5 | CMD-12 `test_ac_08_end_to_end_authoritative_hydration` | authoritative state/identity만 반영되고 access failure에는 fabricated state가 없다. |
| AC-9 | T3 | CMD-3 `test_ac_09_collection_role_separation` | tracker association과 upstream role basis가 분리되고 세 role mapping이 검증된다. |
| AC-10 | T5 | CMD-12 `test_ac_10_end_to_end_injection_is_data` | 주입 text가 command/network/path/budget/status/state를 바꾸지 않는다. |
| AC-11 | T5 | CMD-6 | fresh expected corpus가 실제 analyzer validator에서 종료 코드 0이다. |
| AC-12 | T5 | CMD-12 `test_ac_12_end_to_end_corpus_invariants` | 모든 corpus 1.0.0 record와 global identity invariant가 충족된다. |
| AC-13 | T3 | CMD-3 `test_ac_13_collection_observation_provenance` | comment edit와 Issue body provenance의 필수 ID/URL/time/hash/origin이 보존된다. |
| AC-14 | T4 | CMD-4 `test_ac_14_merge_global_identity` | 양방향 merge에서 같은 PR node ID는 기존 ID를 보존한 한 record가 된다. |
| AC-15 | T1 | CMD-8 | option 생략과 `recent-closed`가 기존 결과와 같고 unknown policy는 입력 오류다. |
| AC-16 | T4 | CMD-4 `test_ac_16_merge_explicit_only_sources` | explicit-only가 incoming에 없는 recent source/observation을 합성하지 않는다. |
| AC-17 | T4 | CMD-4 `test_ac_17_merge_recollection_idempotency` | unchanged observation은 dedup되고 edited observation은 prefix 뒤에 한 건 append된다. |
| AC-18 | T4 | CMD-7 | recollected corpus가 source/metadata/observation/history prefix 검증을 통과한다. |
| AC-19 | T4 | CMD-4 `test_ac_19_merge_projection_history` | older/access-failure evidence가 최신 projection을 덮거나 fabricated state를 만들지 않고 unknown 값이 보존된다. |
| AC-20 | T5 | CMD-12 `test_ac_20_end_to_end_manifest_provenance` | 실제 manifest가 2.0.0 run/page/count/outcome/gap provenance를 모두 가진다. |
| AC-21 | T3 | CMD-3 `test_ac_21_collection_resume_append` | exact resume은 같은 run을 갱신하고 no-resume recollection은 새 run을 append한다. |
| AC-22 | T3 | CMD-3 `test_ac_22_collection_fingerprint_mismatch` | fingerprint mismatch가 network/destination 변경 없이 exit 2다. |
| AC-23 | T3 | CMD-3 `test_ac_23_collection_partial_gaps` | pagination/order/access/hydration/budget gap이 usable corpus에서 partial/3이다. |
| AC-24 | T3 | CMD-3 `test_ac_24_collection_exit_matrix` | invalid=2, partial=3, global/no-usable failure=4, complete=0이며 secret/traceback이 없다. |
| AC-25 | T3 | CMD-3 `test_ac_25_collection_atomic_output` | replace 실패가 기존 bytes를 보존하고 temp를 정리하며 성공 JSON은 UTF-8 newline이다. |
| AC-26 | T2 | CMD-2 `test_ac_26_contract_public_fixtures` | repository artifact는 합성 표시를 가지며 private/credential 값이 caller output 밖에 없다. |
| AC-27 | T5 | CMD-12 `test_ac_27_end_to_end_read_only_runner` | 모든 GitHub 호출이 shell 없는 `gh api --method GET`이고 쓰기/clone/install은 0회다. |
| AC-28 | T6 | CMD-1; CMD-11; CMD-8 | 신규 canonical byte mutation은 digest를 바꾸고 두 revision framing 계약이 통과한다. |
| AC-29 | T6 | CMD-1 | stdlib 전체 suite가 실제 CLI/JSON/exit를 검사하며 종료 코드 0이다. |
| AC-30 | T7 | `dot_codex/skills/collecting-curated-contribution-prs/evals/behavioral-eval.md` | 새 컨텍스트의 synthetic 실행 명령·경로·status·artifact·exit 판정이 실제 값으로 기록된다. |
| AC-31 | T5 | CMD-12 `test_ac_31_end_to_end_red_to_green` | RED-1~RED-5가 실제 산출물 기준으로 모두 GREEN이다. |
| AC-32 | T5 | CMD-12 `test_ac_32_end_to_end_safety_regression` | 기존 주입/예시/state/access/private/partial 안전 행동이 회귀 고정된다. |
| AC-33 | T6 | CMD-8 | 기존 110 tests를 포함한 형제 collector 전체 suite가 종료 코드 0이다. |
| AC-34 | T6 | CMD-9 | analyzer 전체 suite가 종료 코드 0이다. |
| AC-35 | T6 | CMD-10 | candidate verifier 전체 suite가 종료 코드 0이다. |
| AC-36 | T6 | CMD-5 | 신규 skill directory가 `Skill is valid!`와 종료 코드 0을 낸다. |
| AC-37 | T5 | CMD-12 `test_ac_37_end_to_end_fresh_generated_by` | fresh corpus와 manifest run의 generator가 실제 curated name/revision이다. |
| AC-38 | T4 | CMD-4 `test_ac_38_merge_preserves_generated_by` | existing envelope generator는 deep-equal이고 curated revision은 새 run/source에만 남는다. |
| AC-39 | T3 | CMD-3 `test_ac_39_collection_rejects_foreign_manifest` | foreign/date-range/다른 tracker manifest는 network와 destination 변경 없이 exit 2다. |
| AC-40 | T6 | CMD-2 `test_ac_40_contract_judgement_mapping` | filtered AC의 exact token, 2-digit 번호, filter, discovered method가 일대일이며 모두 실행된다. |

<!-- strict-only:start -->

### Threat and trust boundaries

- caller CLI inputs만 repository/Issue/cap/budget/output/resume control을 정한다. 로컬 deterministic source, 인증된 `gh`, 비신뢰 GitHub payload, private일 수 있는 runtime JSON 사이의 경계를 T2/T3/T5가 유지한다.
- CMD-12는 remote text가 shell/argv/path/role/state/status/retry를 바꾸지 않고 모든 GitHub call이 GET임을 확인한다. CMD-3은 Link endpoint/query/page와 comment order mutation을 확인한다.
- CMD-4와 CMD-7은 거짓 source 합성과 append-only history 손상을 막는 데이터 무결성 gate다. CMD-2는 합성 repository fixture와 private/credential marker 경계를 확인한다.
- token은 `gh`가 관리하며 source, prompt, manifest diagnostic, test transcript에 읽거나 출력하지 않는다. runtime artifact는 caller output에만 남는다.

### Authorization and tenant isolation

다중 tenant 서비스가 아니므로 서비스 계정 간 tenant isolation은 not applicable이다. 이유는 이 기능이 호출자의 로컬 `gh` 권한으로 단일 실행되는 CLI이기 때문이다. 대신 데이터 경계의 allowed case는 같은 normalized tracker repository/Issue와 exact fingerprint의 curated manifest append/resume이고, denied case는 date-range/foreign method/다른 tracker repository/Issue다. CMD-3의 `test_ac_39_collection_rejects_foreign_manifest`가 denied case의 request 0회·destination 변경 0회·exit 2를, `test_ac_21_collection_resume_append`가 allowed case를 증명한다. tracker association은 upstream authorization으로 전이되지 않으며 `test_ac_09_collection_role_separation`이 이를 판정한다.

### Migration, compatibility, and rollback

schema migration과 backfill은 not applicable이다. 신규 collector는 corpus 1.0.0과 manifest 2.0.0을 처음부터 쓰고 foreign manifest를 migration하지 않고 거부한다. CMD-8이 omitted policy의 기존 behavior와 기존 110 tests를, CMD-4가 explicit-only를, CMD-7이 analyzer prefix를 증명해야 한다. rollback trigger와 root-owned rollback은 Rollout and rollback 절을 따른다. 이미 생성된 artifact는 변형하지 않는다. 오염된 manifest는 새 경로로 재시작하며 형제 collector의 역방향 discriminator 보강은 범위 밖이다.

### Failure recovery and observability

- exact fingerprint resume은 safe corpus/manifest checkpoint와 누적 request count를 이어받고, mismatch는 network 전에 exit 2다. atomic replace failure는 이전 bytes와 temp cleanup 증거를 남긴다.
- manifest는 run ID/fingerprint, generator/method/tracker identity, request count/events, page/Link validation/comment ID range, cap counts, hydration outcomes, warnings, failed scopes, timestamps, final status의 관측 정본이다.
- stderr와 exit 0/2/3/4는 credential/traceback 없는 사용자 신호다. 별도 metrics/alerts/traces backend는 로컬 CLI이므로 not applicable이다. CMD-3 verbose transcript와 manifest JSON이 그 대신 recovery/diagnosis evidence다.
- partial은 inventory보다 먼저 보이게 하며 complete로 승격하지 않는다. 검증 실패 시 artifact를 자동 수선하거나 상태를 낮춰 성공시키지 않는다.

### High-risk end-to-end verification

필수 순서는 CMD-12 → CMD-6 → CMD-7 → CMD-8이다. synthetic tracker를 fresh corpus/manifest로 수집하고 recent-existing과 병합한 뒤 unchanged/edited 재수집, reverse merge, malformed/cursor/page-mismatch Link, comment ID 역행, foreign manifest를 수행한다. 필수 증거는 temporary artifact bytes/digests, CLI exit codes, fresh/merged `generated_by`, next URL/page validation provenance, fake runner argv/side effects, 양방향 source arrays, analyzer outputs, 형제 suite transcript다.

tracker-only record의 recent source, existing generator/source/history prefix 변경, unchanged duplication, edited append 누락, tracker role 승격, Link/order gap의 complete 처리, foreign manifest 수락, injection control 전달, 필수 exact test 미실행, validator/full sibling suite 비영 종료 중 하나라도 있으면 완료를 중단한다. 라이브 tracker 실행은 이 gate에 포함되지 않는다.

### No production mutation confirmation

자동 workflow에는 production mutation이 없다. synthetic fixture와 repository source/test/eval, caller가 지정한 로컬 corpus/manifest만 변경한다. GitHub Issue/PR/comment/review/label/branch 쓰기, live tracker 수집, clone, dependency install, commit, push, PR, merge, 배포, main/다른 worktree/전역 설치본 변경은 수행하지 않는다.

<!-- strict-only:end -->
