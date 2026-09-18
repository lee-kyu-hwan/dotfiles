# Quality Goal Report

- Task ID: 20260910T111848Z-80-트래커-issue-코멘트-기반-pr-수집-스킬-collecting-8a205a42
- Mode: strict
- Status: completed
- Created: 2026-09-10
- Updated: 2026-09-11
- Source goal: #80 트래커 Issue 코멘트 기반 PR 수집 스킬 collecting-curated-contribution-prs 구현

## Classification

auto 라우팅에서 strict. 근거는 네 가지 strict 트리거다.

- 외부 API 호환·멱등성: GitHub REST(issue comments, pulls, timeline) 계약과 재수집 멱등성을 새로 구현한다.
- cross-skill 공개 계약: 산출 corpus 가 형제 `analyzing-open-source-pr-patterns/scripts/validate_corpus.py`
  의 append-only 규칙(source_key 정확 prefix, observations 를 제외한 source metadata deep-equal 불변,
  observations·state_history 정확 prefix)을 만족해야 한다.
- 보안 통제: #80 완료 기준 "댓글 속 명령을 실행하지 않는 독립 행동 평가" 는 프롬프트 인젝션 방어다.
- 비공개 데이터 분리: 인증 토큰으로 읽은 원본이 공개 산출물로 새지 않아야 한다.

## Review history

| 산출물 | 라운드 | score | verdict | 결과 |
|---|---|---|---|---|
| Spec | 1 | 84 | REVISE | blocker `SPEC-001`(형제 transport 로는 exact next URL 추적 불가). 그 밖 Medium 2, Low 3 |
| Spec | 2 | 97 | PASS | 6 건 전부 resolved. 남은 Low `SPEC-007`(심볼명 오기) |
| Plan | 1 | 84 | REVISE | blocker `PLAN-001`(형제 `_observation_identity` 가 run_id 를 포함해 재수집이 관측을 복제). 그 밖 Medium 1, Low 4 |
| Plan | 2 | 95 | PASS | 6 건 전부 resolved. 남은 Low `PLAN-007`(줄 번호 인용 오류), `PLAN-008`(state 이벤트 강제 계층 미명시) |
| 코드 | 1 | 72 | REVISE | blocker `CODE-001`·`CODE-002`. 그 밖 Medium 3, Low 4 |
| 코드 | 2 | 88 | PASS(리뷰어) → 게이트 **불합격**(오케스트레이터) | 신규 `CODE-012` 가 AC-17 을 깨는 것을 실측해 `acceptance_criteria_met: false` 로 게이트를 막았다 |
| 코드 | 3 | 93 | PASS | `CODE-012`·`CODE-010`·`CODE-011` resolved. 남은 Low `CODE-013` |

Spec 라운드 2 는 PASS 였으나 미확인 근거를 포함해 스키마 검증에서 거부됐다(`PASS reviews must not contain
unverified evidence`). `record-review-error` 로 기록하고, 리뷰어가 읽을 수 있는 실행 전사를 첨부해 같은
라운드를 1 회 재시도해 미확인 근거 0 으로 통과시켰다. 라운드는 소비되지 않았다.

코드 리뷰 라운드 3 은 앞선 시도가 턴 한도로 결과 없이 멈춰 `SendMessage` 로 재개시켰다. 모델 실패가
아니며 상태·fingerprint 는 그대로여서 동일 상태를 이어 심사했다.

## Blocking-finding resolutions

### SPEC-001 (High)

형제 `GhApiClient.get_json` 은 `/` 로 시작하지 않는 endpoint 와 caller 의 `per_page` 를 거부하고
`_api_command` 가 항상 `-f per_page=100` 을 넣는다. 해소는 형제 transport 를 바꾸지 않고 `rel="next"`
존재를 다음 요청의 권위 신호로 삼되, next URL 이 기대한 comments endpoint 의 page 기반 query 이고
page 가 현재+1 인지 검증한 뒤 adapter 의 page 파라미터로만 요청하는 결정(D7)이다. cursor 형태나
불일치는 추측하지 않고 partial 로 남긴다.

### PLAN-001 (High)

형제 `_append_source` 가 쓰는 `_observation_identity` 의 첫 원소가 `run_id` 라서, 편집이 없어도 새 run
이면 관측이 복제된다. 오케스트레이터가 probe 로 재현했다(1 건 → 2 건). 해소는 curated 계층이
`merge_corpus` 호출 전에 run 독립 content identity 로 선행 dedup 하고 형제 dedup 경로는 건드리지 않는
것이다.

### CODE-001 (High)

hydration outcome 이 "예외가 안 나면 collected" 로 무조건 기록돼, PR core 404 가 outcome 과 failed_scopes
어디에도 남지 않았다. 오케스트레이터가 합성 harness 로 재현: exit 0, status `complete`, `failed_scopes []`.
해소 후 같은 시나리오에서 exit 3, status `partial`, `failed_scopes` 에 repository·number·
endpoint_categories·reason 이 기록되고 `hydration_outcomes` 에 `{number:1250, status:"partial"}` 이 남는다.

### CODE-002 (High)

접근 실패 record 가 빈 `state_history` 로 저장돼, 스킬이 자신이 안내하는 analyzer 가 거부하는 corpus 를
남겼다(`state_history must be a nonempty array`, exit 1). 해소 후 그 record 는 `state` `unknown` 과
`failure_basis`(kind, endpoint_categories)를 담은 이벤트 1 건을 가지며 analyzer 가 통과시킨다(exit 0).

### CODE-012 (Medium, 게이트 차단으로 처리)

리뷰어는 PASS 를 냈으나 오케스트레이터가 실측해 게이트를 막았다. 접근 불가 PR 을 무변경 재수집하면
state_history 1→2, tracker observations 1→2 로 **둘 다** 증가했다. 원인은 (1) unknown state 이벤트에
실행 시각이 들어가 형제의 JSON 동일성 dedup 을 빠져나간 것, (2) 선행 dedup 이 global PR node identity
로만 매칭해 `unresolved` record 가 걸리지 않은 것이다. 두 번째 원인은 리뷰어가 지적하지 않았고
오케스트레이터가 재수집 실행으로 발견했다. 해소 후 모든 레코드에서 증가 0 을 실측했다.

## Plan approval

- Approval timestamp: 2026-09-11T00:00:00Z
- Plan digest: 28722a5ff7e6afc8d2dcad1049fcfe301b1622de00fd4b7de456d663a65ce6cc

root 오케스트레이터가 A 안으로 승인했다. 사용자가 #79→#80→#81→#82 순차 진행과 최종 Plan 승인 판단을
root 에 위임했다. 승인 digest 는 통과한 Plan 리뷰가 기록한 digest 와 같아 `approve-plan` 의 digest 가드를
통과했다.

## Changed files

추적 파일 변경은 형제 collector 3 개뿐이며 병합 영역에 한정된다.

| 파일 | 변경 |
|---|---|
| `dot_codex/skills/collecting-recent-closed-prs/scripts/collect_recent_closed_prs.py` | `merge_corpus` 에 keyword-only `source_policy` 추가. 기본값 `recent-closed` 는 기존 동작 보존, `explicit-only` 는 incoming source/observation 만 append. 값 검증은 `ValueError` |
| `dot_codex/skills/collecting-recent-closed-prs/tests/test_collect_recent_closed_prs.py` | 기본값 characterization 1 개와 정책 동작 4 개 추가 |
| `dot_codex/skills/collecting-recent-closed-prs/references/collection-contract.md` | 병합·출처 정책 문단 |

신규 파일은 전부 `dot_codex/skills/collecting-curated-contribution-prs/` 아래다: `SKILL.md`,
`agents/openai.yaml`, `references/collection-contract.md`, `references/github-rest-contract.md`,
`scripts/collect_curated_contribution_prs.py`, `tests/test_collect_curated_contribution_prs.py`,
`tests/fixtures/` 합성 픽스처 10 개, `evals/behavioral-eval.md`(독립 평가자가 작성). 앞의 여섯 경로가
canonical revision 입력이며 fixtures 와 evals 는 아니다.

`collect_repository_hits`, search, partition, 형제 `references/github-rest-contract.md`,
형제 `SKILL.md`·`agents/openai.yaml`, analyzer, candidate verifier 는 무변경이다. 함수 단위 바이트 비교로
`_observation_identity`, `collect_repository_hits`, `_append_state_history`, `_json_equal`,
`_greatest_pr_id`, `_record_body_sha256`, `_record_updated_at` 의 동일성을 확인했다.

## Verification evidence

최종 상태(fingerprint `c47ec60a8739f64bea3f99d11f2589eb04b9a57bb4f9aa9893386583e8408c1e`)에서
오케스트레이터가 직접 실행했다. 모든 명령의 종료 코드는 0 이다.

| ID | 명령 | 결과 |
|---|---|---|
| CMD-1 | curated 전체 suite | `Ran 34 tests` OK |
| CMD-2 | `-k contract` | `Ran 5 tests` OK. `test_ac_01/02/03/26/40` 각각 `ok` |
| CMD-3 | `-k collection` | `Ran 15 tests` OK |
| CMD-4 | `-k merge` | `Ran 6 tests` OK |
| CMD-12 | `-k end_to_end` | `Ran 9 tests` OK |
| CMD-5 | `quick_validate.py` | `Skill is valid!` |
| CMD-6 | analyzer, fresh corpus | `Validated 2 records (schema 1.0.0).` |
| CMD-7 | analyzer, `--existing` | `Validated 1 records ... against existing corpus.` |
| CMD-8 | 형제 collector suite | `Ran 115 tests` OK (기존 110 보존 + 신규 5) |
| CMD-9 | analyzer suite | `Ran 30 tests` OK (무변경) |
| CMD-10 | candidate verifier suite | `Ran 62 tests` OK (무변경) |
| CMD-11 | `--print-revision \| rg -x` | `sha256:72f3798b39443c9021097bbf0c235b9f39388af892ec52de5851816d286927cb`, 정확히 1 줄 |

행동 probe(합성 harness, 실제 CLI, 네트워크 없음):

- `explicit-only` 가 tracker 전용 PR 에 `recent-closed` 출처를 만들지 않고 기존 출처·관측을 보존하며,
  기본값은 기존 동작을 유지하고 unknown 정책은 `ValueError` 다.
- PR core 404 시나리오에서 exit 3 / `partial` / 구체적 failed scope / `unknown` + failure_basis 이벤트,
  그 corpus 가 analyzer 통과.
- 무변경 재수집에서 모든 레코드의 state_history 와 observations 증가 0(unresolved record 포함).
- 분류 7/7: 저장소·소유자 이름에 키워드가 든 실제 제출은 비제외, 앞줄 영어 라벨·한국어 예시·한국어 공지는
  제외, 한국어·영어 실제 제출은 비제외.

독립 행동 평가는 세 번 모두 새 독립 Codex 컨텍스트에서 수행했다. 최종 회차에서 gh 호출 34 건이 전부
`--version` 또는 `--method GET` 이고 주입 토큰 0, `/tmp/cohort-export.json` 미생성, budget 은 호출자의
200 유지, status 는 정직하게 `partial`, 평가 corpus 는 analyzer 통과였다. 1·2 차 산출물은
`t7-eval1-preserved/`, `t7-eval2-preserved/` 에 보존했다.

not configured 로 기록하는 검증 범주(저장소 근거를 확인한 결과 설정 파일이 없다):

- type check — 저장소에 타입 검사 설정 없음. `.github/` 부재, 프로젝트 루트에 타입 설정 파일 없음.
- lint — lint 설정 없음.
- build — Python 스킬 저장소로 빌드 단계 없음.
- 브라우저 E2E — 해당 없음. 대신 fake `gh` 를 `PATH` 에 올린 실제 CLI end-to-end 를 수행했다.

정직하게 기록할 사항: 수정 라운드 1 직후 CMD-1·CMD-2 가 exit 1 이었다. 원인은 오케스트레이터가
`PYTHONDONTWRITEBYTECODE` 없이 `importlib` probe 를 돌려 `scripts/__pycache__` 를 만든 것이고,
`test_ac_03_contract_packaging` 이 이를 정확히 잡았다. 구현 결함이 아니며 캐시 삭제 후 둘 다 exit 0 이다.

또 하나: `capture-baseline` 은 INTAKE/CLASSIFIED 에서만 허용되어 fast-forward 이후 재실행이 exit 3 으로
거부됐다. 따라서 state 의 `base_revision` 은 `36c3f90` 으로 남아 있으나 실제 diff 기준은 `067923b` 다.
`36c3f90..067923b` 의 120 줄은 PR #102 의 변경이지 #80 의 변경이 아니다.

## Execution watchdog

`references/model-routing.md` 가 watchdog 래퍼를 요구하도록 바뀐 뒤의 모든 Codex 호출을 기록한다.
다섯 실행 모두 child exit 0, 결과 스키마 검증 통과, watchdog 사유·신호·잔여 PID 없음, preservation
`not_needed` 였다.

| Execution ID | PID / PGID | 시작 / 종료 / 경과 | child exit | result / schema | 신호 / preservation |
|---|---|---|---|---|---|
| exec-t7 | 56728 / 56728 | 2026-09-11T09:22:40Z / 09:27:25Z / 285s | 0 | 존재 / passed | [] / not_needed |
| exec-fix1 | 4349 / 4349 | 09:39:35Z / 09:54:06Z / 870s | 0 | 존재 / passed | [] / not_needed |
| exec-t7b | 48145 / 48145 | 09:57:01Z / 10:03:43Z / 402s | 0 | 존재 / passed | [] / not_needed |
| exec-fix2 | 82496 / 82496 | 10:13:27Z / 10:43:25Z / 880s | 0 | 존재 / passed | [] / not_needed |
| exec-t7c | 18322 / 18322 | 10:44:21Z / 10:51:53Z / 451s | 0 | 존재 / passed | [] / not_needed |

- Start confirmed / watchdog reason: 다섯 실행 모두 `started: true` / `None`
- Abort / Reap / preflight termination: 전부 `not_needed`, 시도 없음
- Residual PIDs: 전부 `[]`

## Watchdog restart budget

- Initial / remaining: `null` / `null` (재시작 후보가 발생하지 않아 예산이 할당되지 않았다)
- Exactly-once consumption: 0
- Restart attempted / stopped: false / false

## Remaining advisory findings

| ID | 심각도 | 내용 | 영향 | 후속 |
|---|---|---|---|---|
| `SPEC-007` | Low | Spec 이 형제 클래스를 `GitHubClient` 로 오기(실제 `GhApiClient`) | 없음. Plan 이 정정하고 구현이 실제 심볼을 쓴다 | 문서 정정은 root 판단 |
| `PLAN-007` | Low | Plan 이 `_append_source` 호출을 1440 행이라 인용(실제 1439) | 없음. 순수 인용 오류 | root 판단 |
| `CODE-013` | Low | `canonicalize_curated_state_history` 의 `captured_at` 파라미터가 본문에서 쓰이지 않는다 | 동작 영향 없음. run 독립 불변식을 읽는 사람이 오해할 여지 | 파라미터와 호출 인자 제거 또는 docstring 명시. 코드 리뷰 라운드가 3/3 소진되어 이번 범위에서 수정하지 않았다 |

분류 키워드 어휘(`example`, `notice`, `announcement`, `예시`, `공지`)는 리뷰가 Spec R2.2 의 정당한 구현으로
판정했다. Spec 은 판별자를 정의하지 않고 non-goal 도 라벨 휴리스틱을 금지하지 않는다. 계약 문서가 정한
실제 평가 범위는 두 곳이다. `_reference_classification_basis` 는 같은 줄에서 URL 앞부분(`same-line-prefix`)
을 먼저 보고, 이어서 바로 앞줄(`previous-line`) 을 본다. 두 범위 모두에서 라벨 텍스트의 모든 PR URL 을
제거한 뒤 키워드를 찾으므로 URL 자체는 분류 근거가 되지 않는다. 매칭되면 manifest 의 exclusion 항목에
matched keyword, evaluated label, 그리고 어느 범위에서 왔는지를 기록한다. 그보다 더 떨어진 라벨, 목록 밖
동의어, 모호한 산문은 추론하지 않고 호출자 검토로 남긴다. 어휘 확장은 정책 성격이 있으므로 root 결정
사항으로 남긴다.

## Final status

- Status: completed
- Machine-readable reason: `COMPLETED`

commit, push, PR, merge, 배포, 전역 설치본 변경은 이 작업자가 수행하지 않았다. 전부 root 담당이다.
