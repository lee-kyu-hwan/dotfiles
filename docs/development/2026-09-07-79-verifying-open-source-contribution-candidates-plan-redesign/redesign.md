# #79 제한된 Plan 재설계 기록

## 실행 관계

- 이전 실행: `20260906T125225Z-79-다른-저장소의-기여-후보-탐색-검증-스킬-verifying-open-ec840cba` — 최종 상태 NEEDS_REDESIGN, `status_reason: REVIEW_LIMIT_EXHAUSTED:plan`. 상태·리뷰 JSON·스냅숏·Spec·Plan·report 는 `.claude/quality-state/<이전 ID>/` 와 `docs/development/2026-09-06-79-verifying-open-source-contribution-candidates/` 에 그대로 보존하며 이 실행은 그 파일을 편집하지 않는다(state.json `updated_at` 2026-09-06T14:01:12Z 불변 확인).
- 이 실행: `20260906T194200Z-79-verifying-open-source-contribution-ca-f0ac72ad`(UTC 기준 ID; 로컬 날짜 2026-09-07). 설치된 quality-goal 의 정상 절차(INTAKE → 분류 → Spec 리뷰 → Plan 리뷰 → 승인)를 처음부터 다시 밟는다. quality-goal 은 Plan-only 재개나 과거 PASS 승계를 지원하지 않으므로, 이전 실행의 Spec PASS 는 **이 실행의 게이트 근거가 아니다**. Spec 은 이전 PASS 본문을 바이트 동일하게(`sha256 e672be97c1d547eb59f1b3cb4ff3d1f826f2af5a61735951c97389c0afd85947`) 재제출하고 이 실행에서 리뷰를 새로 받는다.
- 범위(당초): Plan 의 PLAN-012(High, blocker)·PLAN-013(Medium)·PLAN-007 잔여(Low) 만 고친다. 실제: 이 실행 Spec 라운드 1 리뷰가 요구해 Spec 본문도 개정했다(§ 영향 범위). 그 밖의 Plan 문장은 이전 라운드 2 본문(`sha256 92430b9d…`)을 유지한다. 같은 목표에 새 ID 를 붙여 한도를 우회하는 것이 아니라, 재설계 결정을 기록하고 전체 리뷰를 다시 받는 것이 이 실행의 목적이다.
- 설치본 확인(2026-09-07): `~/.claude/skills/quality-goal` version 5.0.0. 이전 실행 시작 시점과 비교해 `tests/` 디렉터리(`test_revision_check.py`, `tests/fixtures/revision-check/`, 갱신된 `test_content_contracts.py`·`test_quality_state.py`)가 저장소 소스와 동일하게 갱신됐고, SKILL.md·references·schemas·scripts·templates 는 바이트 동일하다. 실행 계약에 영향 없음.

## 원인

이전 실행 Plan 라운드 2 에서 PLAN-003(예산 소진 시 출력 형태 미정) 을 해소하려고 넣은 두 문장이 충돌했다. (a) "저장소 단계에서 예산이 소진되면 그 저장소를 `repositories[]` 에 `outcome: failed`, `reason: budget-exhausted` 로 기록", (b) "종료 코드: 하나라도 실패·소진·불완전이면 3, 저장소 전부 실패면 4". 저장소 1개 픽스처(AC-13)에서 소진되면 유일한 저장소가 `failed` 가 되어 (b) 의 두 절이 동시에 성립하고, Plan 이 기대한 `3` 과 `4` 가 모두 가능해졌다. 라운드 1 스냅숏에는 두 문장이 없었으므로 라운드 2 에서 처음 발생한 회귀였고, Plan 라운드 한도(2)로 이전 실행은 종료됐다.

## PLAN-012 결정 규칙 (변경 전 → 변경 후)

변경 전: outcome 매핑과 종료 코드 규칙이 병렬로 놓여 우선순위가 없었다.

변경 후(단일 규칙):

1. **접근 실패**는 ① `GET /repos/{owner}/{name}` 요청이 실제로 실행되어 404/401/403/재시도 소진·5xx·전송 오류로 끝난 경우만이다. outcome 은 R3.1 의 네 값(`not-found-or-inaccessible`, `unauthorized`, `forbidden`, `failed`), `reason` 은 각각 `http-404`, `http-401`, `http-403`, `transport-or-5xx`.
2. **예산 소진**은 접근 실패가 아니다. ① 이 성공한 뒤 ②~⑧ 어디서 소진되면 outcome `checked`, `reason: budget-exhausted`, `stages_completed`(완료 단계 목록), `head_sha`(② 완료 시 값, 아니면 `null`). ① 조차 시작하지 못한 저장소는 outcome `budget-exhausted`, `reason: budget-exhausted`, `stages_completed: []`, `head_sha: null`. 이 여섯째 outcome 값은 이 실행 Spec 라운드 2 개정(R8.1, D12)으로 추가됐다(라운드 1 본문에서는 `failed` 를 넓혀 읽는 해석이었고 리뷰어가 SPEC-022 로 지적).
3. **종료 코드**: `4` 는 모든 저장소가 1 의 접근 실패인 경우에만(`reason` 이 `budget-exhausted` 인 저장소가 하나라도 있으면 `4` 가 아님). 그 외에 접근 실패·소진·`duplicate_search.complete: false`·`code_search.available: false` 가 하나라도 있으면 `3`. 전부 없으면 `0`. 예산 소진은 **항상** `3` 이다.
4. **status**: 종료 코드 0/3/4 와 각각 `complete`/`partial`/`failed` 로 일치.
5. **records**: 접근 실패 저장소와 저장소 단계 소진 저장소의 조합은 `records[]` 에 없고 `failed_scopes[]` 에만 있다(R3.1·R3.5·R3.6). 조합 단계(⑦~⑧) 소진은 소진된 조합과 이후 조합만 `failed_scopes`, 이미 완료된 조합은 `records[]` 유지. `4` 이면 `records[]` 는 항상 비어 있다.
6. **출력 파일**: `4` 에서도 discovery envelope(`status: failed`, 빈 `records`)과 manifest run 은 기록한다. R8.2 의 "사용 가능한 출력 없는" 은 후보 평가에 쓸 수 있는 레코드가 없다는 뜻이며 감사 기록 자체는 남긴다.
7. **run outcome**: `records[]` 비면 `no-candidates`, 아니면 `discovered`(R8.1). `4` 이면 항상 `no-candidates`.

### 사례 표

| 사례 | 저장소 outcome / reason | stages_completed·head_sha | records | failed_scopes | status | 종료 코드 | 사용 가능한 결과 |
|---|---|---|---|---|---|---|---|
| A. 예산 소진만(AC-13: 저장소 1, 예산 6, ①~④ 성공 뒤 ⑥ 에서 소진) | `checked` / `budget-exhausted` | `[repository, head, community_profile, private_vulnerability_reporting]`, `head_sha` 값 | 없음 | 그 저장소×패턴 조합 전부(`budget-exhausted`) | `partial` | **3** | `repositories[]` 의 `head_sha`·`stages_completed`, `requests_consumed == 6` |
| B. 일부 성공 후 소진(저장소 2: A 완료, B 의 ⑦ 에서 소진) | A `checked`/`null`; B `checked`/`budget-exhausted` | A 전 단계; B ①~⑥ | A 의 조합 전부 | B 의 소진 조합과 이후 조합 | `partial` | **3** | A 의 records + B 의 저장소 사실 |
| B′. 일부 성공 후 소진(저장소 2: A 완료, B 의 ① 미시도) | A `checked`; B `budget-exhausted`/`budget-exhausted` | B `[]`, `null` | A 의 조합 | B 의 조합 전부 | `partial` | **3** | A 의 records |
| C. 모든 저장소 실제 접근 실패(저장소 2 모두 404, 또는 하나 404·하나 403) | 각각 네 값 중 하나 / `http-…` 또는 `transport-or-5xx` | `[]`, `null` | 없음 | 전부(`repository-<outcome>`, Plan 이 고정한 어휘) | `failed` | **4** | 후보용 레코드 없음. discovery(`status: failed`)·manifest 는 기록 |
| D. 실패와 소진 혼합(A 404, B 소진) | A `not-found-or-inaccessible`/`http-404`; B `checked` 또는 `budget-exhausted`/`budget-exhausted` | B 는 소진 지점까지 | 없음(B 가 저장소 단계 소진) 또는 B 완료 조합 | A 전부 + B 소진 이후 | `partial` | **3**(소진 저장소가 있으므로 `4` 아님) | B 의 완료 사실·레코드 |
| E. 단일 저장소 404(AC-8 의 저장소 하나가 아닌 전 저장소인 경우) | 위 C 와 같음 | | | | `failed` | **4** | 없음 |
| F. 저장소 여러 개 중 하나만 404, 나머지 완료(AC-8) | 404 저장소 네 값 중 하나; 나머지 `checked` | | 나머지의 조합 | 404 저장소 조합 | `partial` | **3** | 나머지 records |

각 사례는 규칙 1~7 로 정확히 하나의 결과만 갖는다. 반례 점검: "모든 저장소가 실패 outcome" 인데 그중 하나가 `budget-exhausted` 인 B′·D 는 규칙 3 의 예외 절로 `3` 에 고정되고, `4` 는 C·E 만이다. AC-13(A)은 `3`, AC-35 의 "전 저장소 실패 `4`" 는 C, AC-8(F) 은 `3` 으로 서로 배타적이다.

### Spec 대조 (이 실행 Spec 라운드 2 개정본 기준으로 갱신 — SPEC-023 해소)

- R3.1: 접근 실패 네 outcome 과 `reason`(`http-404`/`http-401`/`http-403`/`transport-or-5xx`), "실행되어 실패" 한정, 조합은 `records` 없이 `failed_scopes` — 규칙 1·5 와 같다.
- R3.5: 요청 발행 순서 ①~⑧, 저장소·조합 처리 순서, 소진 시 outcome(`checked`+`reason` / `budget-exhausted`)·`stages_completed`·`head_sha`, 미완료 조합 `failed_scopes` `budget-exhausted`, `partial`(3) — 규칙 2·3·5 와 같다.
- R3.6: `records[]` 항목 필드와 `status` 세 값 — 규칙 4·5 와 같다.
- R8.1: `repositories[]` 완전성(요청 저장소 전부, `--repo` 순서, 한 번씩), 항목 다섯 키, outcome 여섯 값, reason 여섯 값 — 규칙 1·2 와 같다.
- R8.2: 단일 우선순위(전부 접근 실패이고 소진 없음 → 4; 접근 실패·소진·미완결·코드 검색 불가 하나라도 → 3; 없음 → 0; 4 에서도 파일 기록) — 규칙 3·4·6 과 같다.
- AC-13: 29 요청 산식, ①~④ + ⑥ 두 요청에서 소진, outcome `checked`/`budget-exhausted`, `stages_completed` 네 단계, `records` 빈 것, `no-candidates`, 3 — 사례 A.
- AC-33: 세 저장소(정상·404·① 미시도) 의 `repositories[]` 완전성과 값 — 사례 B′·F 의 조합.
- AC-35: 여섯 사례 3/3/3/4/3/3 — 사례 A·B·B′·C·D·F.
- AC-8: 하나만 접근 실패 → 3, 접근 실패 저장소는 `records` 없음 — 사례 F.
- `failed_scopes[].reason` 의 허용 값 집합은 Spec 이 열거하지 않으므로 Plan 이 구현 결정으로 고정한다: `budget-exhausted`, `repository-not-found-or-inaccessible`, `repository-unauthorized`, `repository-forbidden`, `repository-failed`(T1 계약 문서·T3 구현·T5 AC-8 테스트 단정).

### 영향 범위 (이 실행 Spec 라운드 1 리뷰 뒤 갱신)

당초 계획은 Spec 본문 불변이었으나, 이 실행 Spec 라운드 1 리뷰가 새 디렉터리 배치로 생긴 High(SPEC-020: R11.1·AC-46·AC-47·AC-51·CMD-5·CMD-7 이 이전 디렉터리를 가리킴)와 Medium 다섯(SPEC-016·017·018·019·022), Low 하나(SPEC-021)를 냈다. 따라서 Spec 본문을 개정했다: R3.1 reason 값, R3.5 요청 순서·소진 outcome, R5.1 recheck 가변/불변 필드, R5.3 스냅숏 evidence(duplicate_verdict·observed_head_sha), R6.3 여덟째 모순, R7.1 recheck 값 규칙, R8.1 repositories[] 완전성·여섯째 outcome·reason, R8.2 종료 코드 단일 규칙, R11.1 문서 경로·이전 디렉터리 보존, AC-13·24·30·32·33·35·46·47·51 개정, AC-52·CMD-8·D12·D13 신설, 머리말 Lineage. 요구사항 수 49 는 그대로이고 AC 는 51→52 다. 이전 실행의 PASS Spec 은 `docs/development/2026-09-06-79-…/spec.md` 에 그대로 남는다.

## PLAN-013 (T8 의 CMD-6 재실행)

변경 전: AC-48(3.9 문법 파싱, CMD-6) 을 T2 가 소유해 골격 시점에만 판정. 변경 후: AC-48 소유를 T8 로 옮겨 최종 스크립트에 대해 판정하고, T2 는 CMD-6 을 착수 확인으로만 돌린다. T3~T7 의 회귀 문장을 "`CMD-1` 과 `CMD-6` 로 회귀를 본다" 로 바꿔 각 태스크 끝에서도 3.9 파싱을 확인한다. 반례 점검: T5 가 3.10 문법(`match`)을 쓰면 T5 의 회귀 확인(CMD-6)에서 즉시 실패하고, 놓치더라도 T8 의 AC-48 판정에서 잡힌다.

## PLAN-007 잔여 (strict-only Migration 절·성공 판정)

변경 전: strict-only § Migration 절이 "`git checkout`/`git clean` 두 디렉터리" 를 가리켰고, 성공 판정이 `grep -c .` 의 표준출력 0 과 종료 상태를 혼동. 변경 후(이 실행 Plan 라운드 2 확정 문언, PLAN-019 반영): Migration 절은 § Rollout and rollback 의 절차를 그대로 참조하고, 롤백 대상은 스킬 디렉터리와 이 실행 문서 디렉터리 두 경로만이며, 성공 판정은 `test ! -e <두 경로> && test -z "$(git status --porcelain | cut -c4- | sed 's/^.* -> //' | grep -v -E '^"?docs/development/2026-09-06-79-verifying-open-source-contribution-candidates/')" && git diff --quiet "$QG_BASE" && shasum -a 256 -c .claude/quality-state/<task-id>/preserved-run.sha256` 다(사전에 `<task-id>` 치환·`QG_BASE` 설정·digest 사본 복사가 필요하다는 점은 PLAN-020 Low 로 남아 있다). 반례 점검(이 실행 Plan 라운드 1 리뷰 PLAN-014·016 반영): 미추적 디렉터리는 셋(스킬, 이 실행 문서, 이전 실행 문서)이다. 롤백 pathspec 은 앞의 둘만이고 이전 실행 문서는 절대 넣지 않는다. `git clean -fd -- <두 경로>` 뒤 `git status --porcelain` 은 이전 실행 문서 한 줄을 남기므로 성공 판정은 그 접두어를 필터한 뒤 `test -z` 를 적용하고, 이전 실행 다섯 파일 불변은 미리 무시 경로에 복사한 `preserved-run.sha256` 으로 `shasum -c` 한다(이전 실행에서 `git checkout -- <미추적>` 종료 1, `git clean` 종료 0 실측).

## 계승한 findings

- 이전 Spec advisory(Spec 본문 미수정, Plan 이 흡수): SPEC-016(recheck 가변 필드), SPEC-017(AC-13 산식·요청 순서), SPEC-018(duplicate_verdict 보존). 이 실행의 Spec 리뷰에서 다시 제기되면 그 판정을 따른다.
- 이전 Plan open: PLAN-012·PLAN-013·PLAN-007 잔여 — 이 실행 Plan 라운드 1 리뷰가 해소 확인. 이 실행에서 새로 나온 PLAN-014~018 은 라운드 2 에서 해소 확인, PLAN-019(Low, 이 문서 문장 — 위에서 정정)·PLAN-020(Low, '그대로 실행 가능' 문구) 은 advisory 로 남는다. 이전 Plan 라운드 2 에서 해소 확인된 PLAN-001~006·008~011 은 그대로 유지한다.
- 오케스트레이터 편차 DEV-1(이전 실행) 은 보고서에 기록돼 있고 이 실행에서는 validate → gate → record-review 순서를 지킨다.

## 변경한 항목과 영향 없는 범위

- 변경: Spec 본문(§ 영향 범위 참조), Plan § Spec link(실행 관계·SPEC-017/022 문단), File map(report.md 경로·이전 문서 보존 행), § Rollout and rollback(대상 경로·성공 판정), § Global constraints(예산 산식 문장 유지), T2 대상 AC(AC-48 제외)·구현 문장, T3 구현(예산 소진·종료 코드 단일 규칙), T3~T7 회귀 문장(CMD-6 추가), T6 통과 확인(AC-35 의 사례 A~F 판정), T8 대상 AC(AC-48 추가)·구현·통과 확인, § Rollout and rollback 성공 판정, strict-only § Migration, 추적표 AC-13·AC-35·AC-48 행.
- 영향 없음: T1·T4·T5·T7 의 테스트 이름 44 개, CMD-1~CMD-6 명령 문자열, 나머지 추적표 행. (당초 'Spec 전체 바이트 동일' 을 예상했으나 이 실행 Spec 라운드 1 리뷰로 Spec 본문·CMD-5·CMD-7 이 개정됐고 CMD-8·AC-52 가 추가됐다 — § 영향 범위.)
