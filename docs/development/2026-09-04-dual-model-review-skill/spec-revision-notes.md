# Spec 개정 기록

- 대상: `docs/development/2026-09-04-dual-model-review-skill/spec.md`
- 기준: `quality-goal`의 `templates/spec.md`, `references/spec-rubric.md`, `references/brainstorming-policy.md`
- 입력: `report.md`의 "4차 착수 전 확정된 설계 결정"과 Spec 라운드 2의 SPEC-09·SPEC-13·SPEC-14·SPEC-15·SPEC-16
- 번호 정책: 기존 요구사항·AC 번호는 유지했고, 신설 항목만 R7.19와 AC-64~AC-68로 뒤에 붙였다.

## Finding별 반영

| Finding | 반영 위치(개정 후 행) | 반영 내용 |
|---|---|---|
| SPEC-09 | R7.6a 143~157행, AC-10 262행, AC-62 313행, Architecture 387~416행, 조합 검토 648행, D21 688행 | R3.7(a) Codex 프리플라이트·모델 거부와 R3.7(c) 산출물 없는 종료를 추가해 결손 경로를 정확히 다섯으로 통일했다. AC-10은 다섯 결손이 모두 없는 보집합만 `resolved`가 되도록 좁혔고, AC-62는 다섯 경로와 이력 복원 실패를 모두 `not_re_reviewed`로 단정한다. |
| SPEC-13 | R2.5 71행, R6.1 122행, R7.4~R7.6a 140~157행, R7.9 169행, R7.17 181행, 신설 R7.19 182~206행, R8.2 211~228행, AC-64~AC-68 322~326행, 상태/이력 경계 387~391행, A7 438~439행, D24 691행 | GitHub를 head SHA를 넘는 게시 이력의 유일한 source of truth로 정했다. inline ID marker와 sticky 요약의 표준-base64 v1 인덱스로 `id`·`cat`·`src`·`path`·`line`·`fp`·`run`·`lifecycle`을 지속하고, 다음 실행이 issue comments·review comments·reviews·review threads를 전 페이지 조회해 복원한다. 로컬 상태와 git notes는 실행 간 이력에 쓰지 않는다. strict parse나 연결 검증이 실패하면 부분 복원 없이 `resolved`를 0건으로 하고 식별 가능한 과거 finding을 `history_unavailable`로 보존한다. |
| SPEC-14 | R2.5 71행, R8.1 210행, AC-61 312행, Failure behavior 555행 이후, 조합 검토 652행, D23 690행 | 같은 `run_id` 재실행에서 `requested_base_ref`·해석된 `base_sha`·`actual_base_sha`·유효 `rounds`를 고정 상태와 대조한다. 하나라도 다르면 상태 변경과 GitHub 쓰기 전에 비정상 종료하고 충돌 필드·기존값·새 값을 알리도록 했다. 같은 ref 문자열의 target SHA 이동도 충돌이다. |
| SPEC-15 | R8.2 211~228행, AC-55 306행, endpoint whitelist 511~530행, 조합 검토 653·655행, D15 678행 | `--pr` 생략 시 `git branch --show-current` 뒤 `list_open_prs(repo, head_ref, limit=2)`를 정확히 한 번 호출하는 것으로 고정했다. detached HEAD·0건·2건 이상은 상태 생성 전 중단하고, 정확히 1건일 때만 `get_pr_meta`를 호출한다. 게시 이력 review 연결용 `list_reviews`를 추가해 클라이언트는 정확히 열 메서드가 됐다. |
| SPEC-16 | publish plan 466~484행, 상태 파일 486~509행, 조합 검토 654행 | 닫힌 상태 필드 목록에 `skipped_threads`, `coverage_gap_evidence`, `history_restore`, `previous_reviews`를 명시했다. 게시 계획에도 `history_restore`·`coverage_gap_evidence`·`skipped_threads`의 shape와 불변식을 넣어 R7.6a·R7.17·R7.18과 맞췄다. |

## 신설 요구사항과 수용 기준

- R7.19: GitHub 기반 게시 이력의 생성·지속·복원 계약. marker/index 문법, 표준 base64, canonical JSON, 여덟 필드의 타입·허용값, 병합 출처 보존, legacy 처리, 엄격한 실패 기본값을 포함한다.
- AC-64: 로컬 이력과 git notes 없이 GitHub 응답만으로 metadata와 comment/review/thread 연결을 왕복 복원한다.
- AC-65: 인덱스·스키마·연결 오류를 모두 fail-closed로 처리하고 부분 복원과 자동 resolve를 금지한다.
- AC-66: 표준 base64 문자집합과 canonical JSON의 결정성을 판정한다.
- AC-67: inline comment가 없는 요약 전용 finding도 다음 실행에 복원·dedup한다.
- AC-68: 다섯 결손 경로를 직접 주입값이 아니라 실제 인덱스 디코드 결과에서 판정한다.
- D24: 실행 간 이력 저장소로 GitHub를 선택하고 로컬 파일·git notes를 배제한 근거를 기록한다.

## 함께 바로잡은 정합성

- R6.1의 출처 은닉 범위를 종합자 입력 view로 한정하고, `finding_provenance` sidecar를 통해 복수 reviewer 출처를 게시 인덱스에 되붙였다(122행, AC-23 278행).
- 위치를 실측할 수 없는 finding도 인덱스에 필요한 내용 지문을 갖도록 domain-separated fallback `anchor_fingerprint`를 정했다(140행).
- 게시 이력 네 목록의 pagination과 중간 실패 시 부분 결과 금지를 R8.2·AC-49·D20에 함께 명시했다(228·316·686행).
- SPEC-10의 잔여 표현을 바로잡아 D18의 API 응답 실측과 R7.16의 보수적 cross-hunk 정책을 분리했다(179·683행).
- 요구사항 61건을 추적표에 전부 연결했고, 메타 AC-27·AC-34를 제외한 66개 AC 참조와 전체 68개 AC의 판정 명령을 맞췄다(328~366행, 613~638행).

## 판단이 갈린 지점

- SPEC-14의 충돌 처리 선택지 중 "새 상태 생성" 대신 "기존 상태와 GitHub 쓰기를 건드리기 전 중단"을 택했다. 같은 head SHA에 다른 base/rounds를 섞은 결과를 하나의 `run_id` 아래 남기지 않기 위해서다.
- full metadata를 inline마다 반복하지 않고, 확정안의 두 층 구조대로 inline에는 기존 `finding_id` marker를 유지하고 sticky 요약 인덱스에 전체 metadata를 원자적으로 모았다. 요약 전용 finding도 같은 인덱스에 포함된다.
- `src`는 단일 문자열이 아니라 정렬·중복 제거 배열로 정했다. 같은 `finding_id`로 병합된 Claude/Codex 또는 복수 Claude 에이전트 출처를 잃으면 결손 판정이 거짓 음성이 되기 때문이다.
- 유효하지 않은 위치의 `fp`를 null로 두지 않고 title/body 기반 fallback 지문으로 만들었다. 인덱스 record의 shape를 모든 게시 finding에서 동일하게 유지하기 위해서다.
- legacy inline marker는 모르는 metadata를 지어내 v1 record로 승격하지 않는다. 가시적 `history_unavailable` 경고와 ID만 이어가고 자동 resolve를 금지했다.
- `resolved` record는 연결된 열린 스레드가 남은 동안만 활성 집합에 유지한다. 스레드가 이미 해결됐거나 애초에 없는 요약 전용 resolved record는 다음 실행의 비교 집합에서 제외해, 같은 ID의 후일 재발을 `new`로 취급한다.

## 조합 검토 결과

PLAN-009·PLAN-010·PLAN-012에서 있었던 개별 해소의 조합 회귀를 염두에 두고 다음 경계를 교차 점검했다.

- R3.7의 실패 세 유형, R10.2(b)의 범위 축소, R3.9의 에이전트 일부 실패가 R7.6a·AC-10·AC-62·AC-68에서 같은 다섯 사건 집합을 쓴다.
- 종합자 출처 은닉이 `src` 지속을 제거하지 않고, 반대로 provenance sidecar가 종합자 입력에 노출되지 않는다.
- 같은-run 재개 상태와 cross-head GitHub 이력의 역할이 겹치지 않는다. 로컬이 없어도 복원 가능하며, GitHub 복원 실패를 로컬 잔여물로 추측하지 않는다.
- review 조회 추가가 R8.2 인터페이스, R7.14 화이트리스트, AC-14·AC-49, D15·D20에 함께 반영됐고 쓰기 surface는 네 메서드로 유지된다.
- `history_restore`·`coverage_gap_evidence`·`skipped_threads`의 명칭과 shape가 요구사항, publish plan, 상태 파일, 테스트 계약에서 일치한다.
- 인덱스 오류·연결 오류·다섯 결손 중 어느 경로도 `resolved` 또는 `resolveReviewThread`로 합류하지 않는다.

## 문서 검증 기록

- 헤더의 Task ID·Mode·Status는 개정 전과 동일하다.
- 요구사항 정의 61건: 번호 중복 0, 추적 누락 0, 유령 참조 0.
- AC 정의 68건: AC-1~AC-68 연속, 번호 중복 0. 모든 AC에 `[실행]`과 판정 명령/검증 위치가 있다.
- 요구사항 추적표: 메타 기준 AC-27·AC-34를 제외한 AC 66건 전부 등장.
- 결손 경로 5건, GitHub 클라이언트 메서드 10건, 상태 필드의 `skipped_threads`·결손 근거 필드 존재를 기계 검사 대상으로 삼았다.
- Markdown fence 쌍, strict-only marker 쌍, `git diff --check`, 변경 파일 범위를 마지막 조합 검토 뒤 다시 확인했고 모두 이상 없었다.

## attempt 2 개정

이 절은 `.codex-readiness/result-attempt1.json`의 READY-01·READY-02를 반영한 두 번째 개정 기록이다. 위 attempt 1의 행 번호와 61개 요구사항·68개 AC 카운트는 당시 snapshot으로 유지하며, 아래 행 번호와 63개 요구사항·70개 AC가 현재 본을 가리킨다. readiness의 REVISE 판정을 옮겨 적을 뿐 이 문서에서 별도 리뷰 verdict를 내리지 않는다.

### Blocker별 반영

| Blocker | 반영 위치(개정 후 행) | 반영 내용 |
|---|---|---|
| READY-01 | R3.9 103행, 신설 R3.10 105~119행, R7.6a 172행 이하, AC-60 347행·AC-62 349행·AC-68 355행, 상태 파일 534~561행, 조합 검토 702~723행, D21·D25 752·756행 | 다섯 Claude 에이전트와 일곱 category의 `AGENT_CATEGORY_MAP_V1`을 완전하게 열거했다. `code-reviewer` 범위는 correctness/security/performance이고, correctness는 silent-failure/type과 중복 담당한다. 선택된 담당자 중 성공자가 하나라도 있으면 covered, 실패자만 남으면 uncovered라는 집합식을 고정했다. reviewer-contract canonical JSON·스크립트 상수·상태 map의 exact equality, category별 선택/성공/실패 상태, 다섯 에이전트 각각의 고유 category lifecycle 결과를 AC에 연결했다. |
| READY-02 | R5.2 131행, R6.1~R6.5 137~162행, R7.5 170행, AC-23 307행·AC-41 328행·AC-43 330행·AC-50 337행·AC-69~70 356~357행, Architecture 423~480행, synthesis Interfaces 502~510행, data flow 584행 이하, D19·D26 749·757행 | 같은 ID 병합 뒤에도 상위 reviewer group별 모든 source-free claim과 evidence-backed critique를 보존한다. 실제 group은 run-local `reviewer-1/2`로 바꾸고 실제 대응과 세부 provenance는 private sidecar에 둔다. 스크립트가 `bilateral`/`unilateral`/`contested` relation을 계산하고 비-미결 분류를 agreed/single_source/disputed와 1:1 검증한다. 양측 합의·한쪽 단독·상호 반박을 raw 입력부터 검증하는 AC를 추가했다. |

### 신설·보강 항목

- 신설 요구사항 R3.10: agent-category 책임표, canonical 순서, 중복 담당 집합식, 상태/상수 연결, 손상 상태 fail-closed 계약.
- 신설 요구사항 R6.5: 상위 reviewer group alias, per-finding observations/claims/critiques, source_count, relation 계산과 정렬 계약.
- 신설 AC-69: 병합→익명화 입력의 닫힌 key, 중첩 claims 보존, alias와 relation 결정성, private sidecar 분리를 판정한다.
- 신설 AC-70: 같은 finding의 양측 합의→agreed, 한쪽 단독→single_source, 상호 반박→disputed를 raw 입력부터 end-to-end로 판정한다.
- 보강 AC-23·41·43·50: 구조화 metadata의 익명성, critique target/stance/evidence, 조건부 unresolved reason, relation/classification 행렬을 단정한다.
- 보강 AC-60·62·68: 문서/상수/상태 매핑의 일치, 각 에이전트 고유 category 실패, correctness 중복 담당의 일부 성공·전원 실패, GitHub 복원 뒤 실제 lifecycle을 단정한다.
- AC 정의는 번호를 바꾸지 않고 기존 AC-48~54를 AC-47 뒤로 옮겨 AC-1~AC-70 단조 순서로 정리했다(313~357행).

### 판단이 갈린 지점

- `code-reviewer`를 일곱 category 전체의 catch-all로 두지 않았다. 그렇게 하면 항상 선택되는 code-reviewer가 성공하는 한 전문 에이전트 실패가 가려져 `agent_category_uncovered`가 사실상 무력화된다.
- correctness의 중복 담당자 중 한 명이 실패해도 다른 선택 담당자가 성공하면 covered로 정했다. 다만 code-reviewer/security, pr-test/tests, comment/comments, silent-failure/error-handling, type/types처럼 각 agent의 고유 책임 category fixture에서는 해당 agent 실패가 반드시 `not_re_reviewed`로 이어진다.
- map/coverage 상태 자체가 손상된 경우 `history_unavailable`이나 여섯 번째 결손 reason을 만들지 않고 lifecycle 계획 전에 중단한다. GitHub v1 인덱스의 의미와 다섯 결손 경로 수를 바꾸지 않기 위해서다.
- 익명 단위는 개별 Claude agent가 아니라 이중 리뷰의 상위 두 group(Claude/Codex)이다. 같은 Claude group의 여러 agent 주장은 한 observation의 `claims` 배열에 모두 남기고 실제 agent ID는 `finding_provenance`에만 둔다.
- `single_source`를 실행 전체가 단일 리뷰어인 경우에만 한정하지 않고, 두 리뷰어 실행에서도 한쪽만 finding을 지지하고 상대 입장이 없는 finding-level 상태로 확장했다. 이는 한쪽 단독 fixture를 `unresolved`와 구별하기 위한 선택이다.
- evidence를 통과한 challenge가 하나라도 있으면 보수적으로 `contested`다. `unresolved`는 relation을 우회하는 임의 분류가 아니라 다섯 축 중 부족한 축과 설명이 있을 때만 허용한다.

### attempt 1 계약과의 조합 검토

- 다섯 결손 경로는 그대로다. READY-01은 다섯째 경로의 판정 함수를 구체화했을 뿐 reason을 추가하지 않았다.
- R7.19 v1 인덱스는 기존 여덟 key와 실제 `src` 배열을 유지한다. 익명 alias는 synthesis 전용이며 GitHub에 게시되지 않는다.
- 과거 finding의 `cat`은 GitHub에서 복원하고 현재 실행의 `category_coverage`는 R3.10 상수와 실제 agent 상태에서 계산한다. 어느 한쪽만으로 자동 resolve를 결정하지 않는다.
- R7.5 병합은 상세 provenance와 함께 익명 observations/claims/critiques를 보존하므로 출처 은닉, 종합 분류, 다음 실행 `src` 복원이 서로의 입력을 지우지 않는다.
- map/coverage 손상, synthesis 입력 identity 누출, relation/classification 불일치는 모두 게시 전 중단하며 R7.19 복원 실패의 safe default나 기존 네 GitHub 쓰기 메서드를 우회하지 않는다.

### attempt 2 검증 기록

- 요구사항 정의 63건, 추적 63건이며 누락·유령·중복이 없다.
- AC 정의는 AC-1~AC-70의 단조 연속 순서이고, 모든 AC에 `[실행]`·`검증:`과 판정 명령 배정이 있다.
- 메타 AC-27·AC-34를 제외한 68개 AC가 요구사항 추적표에 등장한다.
- agent-category 표는 5개 agent, category 합집합 7개, correctness 담당 3개이며 code-reviewer 범위는 3개다.
- R6.5 입력 key 6개, observation key 2개, relation 3값과 AC-70의 세 fixture를 본문에서 상호 대조했다.
- 다섯 결손 행과 R7.19 인덱스 여덟 key, GitHub 클라이언트 열 메서드와 쓰기 네 메서드는 유지된다.
