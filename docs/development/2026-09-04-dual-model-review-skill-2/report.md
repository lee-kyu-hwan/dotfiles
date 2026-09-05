# Quality Goal Report

- Task ID: 20260904T141047Z-42-claude-codex-이중-리뷰-종합-pr-게시-스킬-dual-r-0ed6e1bc
- Mode: strict
- Status: NEEDS_REDESIGN
- Created: 2026-09-04
- Updated: 2026-09-05
- Source goal: #42 Claude+Codex 이중 리뷰 → 종합 → PR 게시 스킬 dual-review 구현

#42의 네 번째 quality-goal 실행이다. Spec 리뷰 라운드 한도(3)를 소진해 종결했다.

## Classification

`--mode=strict`가 명시됐고 위험 스캔 결과와 일치해 다운그레이드 확인이 필요 없었다.

- **외부 API 쓰기 + 멱등성(strict 트리거).** 스킬이 PR에 게시하고 이슈 #42가 "중복 게시 방지, 커밋 SHA 명시, 재실행 갱신 정책"을 핵심 차별점으로 지목한다.
- **비가역 외부 노출.** 게시 계약 오류는 되돌리기 어려운 댓글을 남긴다.
- **게시 이력을 GitHub 자체에 보존하는 설계.** 외부 시스템을 상태 저장소로 쓰므로 그 계약의 정확성이 곧 멱등성이다.
- 다층·다파일 변경, 요구사항 명시 필요(standard 조건).

## Review history

| 라운드 | 시도 | 점수 | verdict | blockers | 처리 |
|---|---|---|---|---|---|
| 1 | 1 | **74** | REVISE | SPEC-20·21·22 | `record-review` — 라운드 1 소비 |
| 2 | 1 | 83 | REVISE | 없음 | 미검증 evidence 1건 → `record-review-unverified`, 라운드 미소모 |
| 2 | 2 | **78** | REVISE | 없음 | `record-review` — 라운드 2 소비 |
| 3 | 1 | **83** | REVISE | SPEC-34·35 | `record-review` — 라운드 3 소비, 한도 소진 |

### Codex 사전 심사와 Claude 공식 리뷰의 점수 차 (이슈 #70 대응점)

이 Spec은 **Codex author가 작성하고 별도 Codex(fresh context, read-only)가 사전 심사**한 것이다. 그 심사는 **97점 READY**를 냈고 Medium 1건(READY-03)만 남겼다. 같은 아티팩트에 대한 Claude 공식 Spec 리뷰의 첫 판정은 **74점 REVISE, High 3건**이었다.

| 심사 주체 | 대상 판본 | 점수 | 판정 | High |
|---|---|---|---|---|
| Codex readiness (attempt 2) | 811행본 | **97** | READY | 0 |
| Claude 공식 r1 | 같은 판본 + READY-03 반영 | **74** | REVISE | 3 |
| Claude 공식 r2 | 959행본 | 78 | REVISE | 3 |
| Claude 공식 r3 | 992행본 | 83 | REVISE | 2 |

**첫 판정에서 23점 차이가 났다.** 이 실행에서 관측한 차이의 성격은 이렇다.

- Codex readiness는 **형식·추적·findings 해소 판정에서는 정확했다.** 요구사항 전수 등재, AC 결번, 판정 명령 배정, 이전 라운드 지적의 반영 여부 같은 대조 작업은 Claude 리뷰와 결론이 일치했다. READY-03(AC-24가 실현 불가능한 조건을 요구)도 유효한 지적이었고 그대로 반영했다.
- **갈린 곳은 전부 설계 정합성이다.** Claude r1의 High 3건은 (a) 게시 이력 복원 계약이 첫 해소 주기 뒤 영구히 죽는 경로, (b) 결손 경로 열거가 스킬 자신의 커버리지 정의보다 좁은 것, (c) 커버리지 판정의 핵심 술어가 정의되지 않은 것이었다. 셋 다 **여러 요구사항의 교차점**에 있고 단일 문서를 정독하는 것으로는 드러나지 않는다.
- 이후 라운드에서도 같은 패턴이 반복됐다. r2의 High 3건, r3의 High 2건이 모두 요구사항 간 상호작용에서 나왔다.

임계값 보정에 쓸 관측: **readiness 90점 임계는 형식·추적 결함을 거르는 데는 유효하지만 설계 정합성 결함은 통과시킨다.** 97점 READY 판정을 받은 판본이 공식 리뷰에서 High 3건을 받았고, 그중 하나(SPEC-20)는 정상 운용에서 `resolved` 경로가 영구히 죽는 결함이었다. readiness를 게이트로 쓰려면 그 점수가 무엇을 보장하는지 좁혀 정의해야 한다 — 이 실행의 표본은 "형식·추적은 보장, 설계 정합성은 미보장"을 가리킨다.

## Blocking-finding resolutions

| ID | 라운드 1 지적 | 적용한 해소 | 라운드 2 판정 |
|---|---|---|---|
| SPEC-20 | 종결 이력 record가 인덱스에서 탈락한 뒤 남는 고아 마커가 R7.17의 전체 복원 실패를 상시 유발해, 첫 해소 주기 뒤 `resolved`가 영구히 0건이 된다 | R7.17을 3층으로 분리 — 인덱스 무결성만 전체 실패, record 대조 실패는 개별 격리, 고아 마커는 스레드 상태로 판정. AC-65(a)(b)(c)와 AC-76(3세대 왕복) 신설 | **해소** |
| SPEC-21 | 결손 경로가 "에이전트 실패"만 담고 "미선택"을 빠뜨려, 담당자가 아무도 선택되지 않은 category의 finding이 `resolved`가 된다 | R7.6a에 6행 `agent_category_unselected` 추가, R3.10에 배타적 술어 정의, AC-77 신설 | **해소** |
| SPEC-22 | 커버리지 판정의 입력인 에이전트 단위 성공/실패 술어가 정의되지 않았고 `excluded`의 적용 단위가 불확정 | R3.5를 주체 단위 5값 열거로 고정, R3.5a로 리뷰어 `excluded`를 주체 실패의 집계로 확정, AC-19·63·78이 술어를 직접 판정 | **해소** |

라운드 2의 High 3건(SPEC-28·31·32)도 라운드 3에서 기전이 막혔음이 확인됐다. 그러나 그 해소가 새 High 2건을 만들었다.

## 종결 원인 — 다섯 번째 교차 회귀

라운드 3의 두 blocker는 모두 `new_blocker_evidence`를 갖는다. 즉 **라운드 3 개정 자체가 만든 결함**이다.

### SPEC-34 — ID 재대응이 다음 실행에 남기는 구멍

SPEC-32(제목 비결정성으로 `finding_id`가 흔들려 미해소 finding이 `resolved`가 되는 것)를 해소하려고 R7.6a에 단계 0 ID 재대응을 신설했다. `(path, cat, fp)`가 모두 같은 현재 finding을 찾아 `persisting`으로 확정하는 규칙이다.

그런데 **재대응된 record가 다음 실행의 인덱스에 어떤 `id`로 실려야 하는지를 규정하지 않았다.**

- `new_id`로 실으면 → GitHub에 남은 `old_id` marker가 고아가 되고, `new_id` marker는 0개라 `inline_pending` → `retry_inline`으로 **같은 결함에 두 번째 inline 코멘트**가 생긴다. SPEC-32가 막으려던 중복 게시가 한 실행 뒤로 미뤄져 재현된다.
- `old_id`로 유지하면 → 매 실행 재대응이 반복돼야 안정적인데, `id_remapped`는 `state.json`/`plan.json`에만 있고 head SHA를 넘어 지속되지 않는다. 인덱스가 유일한 연결 고리인데 규정이 없다.

AC-84는 재대응이 일어난 **그 실행 안의** `persisting`·resolve 0건·새 inline 0건만 단정하고 다음 실행의 인덱스 `id`를 단정하지 않아 이 경로를 검출하지 못한다.

### SPEC-35 — `fp` 소비처 선언의 문서 내 충돌

같은 개정에서 `fp`를 lifecycle 판정에 들였다. 조합 검토로 다섯 곳(R7.21 첫 문장, R7.6 `persisting` 정의, `id_remapped` 상태 필드 두 곳, R7.20 경고 목록, "여덟 key" 오기)을 찾아 고쳤다.

**그런데 다섯 곳이 더 남았다.** R7.4(요구사항 본문), D24, D28, Security and risk 절, 그리고 개정 조합 검토 표의 다른 행이 여전히 "`fp`는 lifecycle·게시·resolve 판정을 바꾸지 않는다"고 규정한다. 특히 D28은 "판정에 영향을 주지 않는 중간안을 선택한다"는 **결정 근거 자체가 뒤집혔는데** 문언이 그대로다. 구현자가 R7.4·D28을 따르면 단계 0을 구현하지 않거나 `fp`를 lifecycle에서 배제해 SPEC-32의 오분류가 그대로 재발한다.

Decisions 절은 이 Spec이 확정한 설계 결정을 담는 곳이므로 이 불일치는 요구사항 본문의 충돌과 같은 무게를 갖는다.

### 패턴

이 작업에서 개별 해소가 교차 회귀를 만든 것이 이번이 다섯 번째다.

| # | 회귀 | 원인 |
|---|---|---|
| 1 | PLAN-009 | 검증 번호 재배치 후 strict-only 절 참조 미갱신 |
| 2 | PLAN-010 | "픽스처만 읽는다" 규칙과 요약 문구 단정을 각각 고치며 교차점 누락 |
| 3 | PLAN-012 | 자리표시자를 리터럴로 바꾸며 스키마 정합 미확인 |
| 4 | SPEC-31 | SPEC-21을 category 단위로만 해소해 출처 에이전트 단위를 놓침 |
| 5 | SPEC-34·35 | SPEC-32 해소가 `fp`를 lifecycle에 들이면서 파급을 절반만 갱신 |

다섯 건 모두 조합 검토를 **수행했음에도** 발생했다. 4번과 5번은 검토 절을 문서에 명시적으로 두고 교차점을 열거한 뒤에도 남았다. 이 실행의 조합 검토는 신설 요구사항과 기존 요구사항의 교차만 봤고, **Decisions 절과 Security 절처럼 요구사항을 되짚어 설명하는 부분**은 검토 범위에 넣지 않았다. 다음 개정에서는 "이 값·규칙을 언급하는 모든 위치"를 기계적으로 전수 검색하는 단계가 필요하다.

## Plan approval

- Approval timestamp: 없음 — `AWAITING_PLAN_APPROVAL`에 도달하지 못했다
- Plan digest: 없음 — 이 실행에서 Plan은 리뷰되지 않았다

## Changed files

구현은 시작되지 않았다.

| 파일 | 변경 |
|---|---|
| `docs/development/2026-09-04-dual-model-review-skill-2/spec.md` | 신규. 992행. 요구사항 66(R1.1~R10.3), AC 86, 결정 D1~D30, strict 전용 6절, 추적표 66행, 개정 조합 검토 절 |
| `docs/development/2026-09-04-dual-model-review-skill-2/plan.md` | 신규. 3차 Plan 515행본을 초안으로 시딩. 이 실행에서 리뷰되지 않았다 |
| `docs/development/2026-09-04-dual-model-review-skill-2/report.md` | 신규. 이 리포트 |

`dot_claude/skills/dual-review/`는 만들어지지 않았다. `.gitignore`는 변경되지 않았다. 커밋·푸시·PR 생성·`chezmoi apply`를 수행하지 않았다.

초기 dirty 경로 넷(`.codex-author/`, `.codex-readiness/`, 3차 디렉터리의 `spec-revision-notes.md`·`spec.md`)은 바이트 단위로 보존했고 이 작업의 변경에 포함하지 않았다.

## Verification evidence

| 명령 | 종료 코드 | 증거 |
|---|---|---|
| `grep '^version:' ~/.claude/skills/quality-goal/SKILL.md` | 0 | `4.1.0` |
| `grep ROUND_LIMITS quality_state.py` | 0 | `{"spec": 3, "plan": 2, "code": 3}` — 배포본·소스·main 일치 |
| `codex exec --sandbox read-only --model gpt-5.6-sol -c model_reasoning_effort="low"` | 0 | 응답 `Acknowledged.` |
| `gh auth status` | 0 | 계정 `lee-kyu-hwan`, 스코프에 `repo` |
| `gh issue view 42` | 0 | OPEN, 라벨 `enhancement` |
| `gh issue view 60` | 0 | **CLOSED / `NOT_PLANNED`** — plan 한도 상향은 채택되지 않았다 |
| `gh issue view 70` | 0 | OPEN — readiness 이관 |
| WebFetch(REST issues/comments 문서) | 0 | **코멘트 본문 길이 상한 미명시** — R7.20의 자체 상한 근거 |
| `git check-ignore -q .claude/quality-state/` | 0 | 무시됨 |
| `git check-ignore .codex-readiness/` | 1 | **무시되지 않음** — follow-up |
| `quality_state.py capture-baseline` | 0 | `base_revision=861836c…`, dirty 4건 |
| Spec 정합 자체 검증(요구사항·AC·추적표·판정 명령) | 0 | 요구사항 66 전수 등재(누락 0·유령 0), AC 1~86 결번 0, 표 참조 누락 0·미참조 0 |
| `validate_review.py validate`(4회) | 0 | 네 리뷰 모두 `{"valid":true,"errors":[]}` |
| `validate_review.py gate`(r1·r2·r3) | 3 | 세 번 모두 `passed:false` |

구현이 없으므로 코드 검증 범주는 전부 미실행이다.

- 단위 테스트: **미실행.** `dot_claude/skills/dual-review/tests/`가 존재하지 않는다.
- 타입 체크·린트·빌드: **not configured.** 저장소 루트에 `tsconfig.json`·`pyproject.toml`·`Makefile`·`package.json`·린터 설정이 없다.
- E2E: **미실행.** 고위험 E2E는 구현 이후 단계다.

## Remaining advisory findings

| ID | 심각도 | 내용 | 후속 조치 |
|---|---|---|---|
| SPEC-34 | High | 재대응된 record가 다음 인덱스에 실을 `id`가 미정의 | `old_id` 유지 또는 `new_id` 갱신 중 하나로 확정하고, 전자면 R7.19의 `persisting` metadata 승계 예외를, 후자면 R7.17의 일치 marker 정의 확장을 명시. 다중 실행 왕복 AC 추가 |
| SPEC-35 | High | `fp` 소비처 선언이 R7.4·D24·D28·Security 절·조합 검토 표에서 여전히 lifecycle 배제 | 다섯 곳을 단계 0 예외 포함으로 갱신. D28은 결정 근거가 뒤집혔으므로 문언과 대안 비교를 다시 쓰고 AC-75·AC-86의 역할 분담을 명시 |
| SPEC-36 | Medium | 6행 술어가 `--base` 여부를 검사하지 않아 `base_narrowed`가 catch-all이 됨 | 판정식에 `requested_base_ref != null` 조건을 넣고 그 밖의 경우에 별도 reason 신설, 또는 6행을 원인 중립적으로 개명하고 AC-10 서술을 술어에 맞춤 |
| SPEC-37 | Medium | AC-84·85·86이 판정 명령 표 어느 행에도 배정되지 않음 | PUB 행에 배정하고 `test_publish_findings.py` 설명에 세 판정을 추가. 조합 검토의 AC 총계를 86으로 정정 |
| SPEC-38 | Medium | 리뷰어가 같은 결함을 이번에 보고하지 않은 비결정성이 결손 열거에 없는데 열거의 완전성을 단언 | 결정적으로 구별 불가능한 잔존 경로로 명시하고, `resolved`로 스레드를 닫은 finding을 요약에 ID와 함께 남기는 요구를 추가 |
| SPEC-39 | Low | "여섯 사건"·"AC 83건" 잔존 표기 | 세 곳 정정 |

## Final status

- Status: `NEEDS_REDESIGN`
- Machine-readable reason: `REVIEW_LIMIT_EXHAUSTED:spec`

`spec-rubric.md`의 "After round 3 without a passing gate, stop and record `NEEDS_REDESIGN`" 규칙에 따라 중단했다. 라운드 3의 게이트 실패 사유는 `score_below_85`(83점, 2점 미달), `verdict_not_pass`, `blockers_present`, `critical_or_high_finding`, `check_failed:acceptance_criteria_objective`다.

재발 규칙에는 걸리지 않았다. 라운드 1의 blocker 셋(SPEC-20·21·22)은 라운드 2에서 해소 확인됐고, 라운드 3의 blocker 둘(SPEC-34·35)은 이번에 처음 등장했다.

## 네 실행 누적

| 실행 | 종료 사유 | 도달 단계 | Spec 최고점 |
|---|---|---|---|
| 1차 `20260828T011459Z` | `REVIEW_LIMIT_EXHAUSTED:spec` | SPEC_REVIEW | 89 |
| 2차 `20260828T021938Z` | `REVIEW_LIMIT_EXHAUSTED:plan` | PLAN_REVIEW | 93 (PASS) |
| 3차 `20260903T160637Z` | `RECURRING_BLOCKING_FINDING:SPEC-09` | SPEC_REVIEW | 83 |
| 4차 `20260904T141047Z` | `REVIEW_LIMIT_EXHAUSTED:spec` | SPEC_REVIEW | 83 |

네 번 모두 구현에 도달하지 못했다. 2차가 Spec을 93점 PASS까지 올렸으나 Plan에서 1점 차로 막혔고, 3·4차는 그 Spec을 확장하면서 매번 새 설계 결함을 찾았다.

관측된 것: **이 Spec은 라운드를 거듭할수록 커지고 있고(651 → 811 → 959 → 992행), 개정이 새 결함을 만드는 비율이 줄지 않는다.** 라운드 3에서 여섯 건을 반영해 두 건의 새 High를 만들었다. 요구사항 66개와 AC 86개가 서로를 참조하는 밀도에서 사람이든 모델이든 한 번의 개정으로 모든 파급을 잡기 어렵다는 신호로 읽힌다.

다음 시도에서 고려할 것 둘.

1. **범위 분할.** `resolved`/`not_re_reviewed` 판정과 게시 이력 복원은 이 Spec에서 가장 결함이 집중된 영역이다(SPEC-09·13·20·21·28·31·32·34·35가 전부 여기다). 1차 구현에서 이 기능을 비목표로 두고 `new`/`persisting`만 다루면 나머지는 훨씬 단순해진다. 이력 복원은 별도 이슈로 분리해 실제 사용 경험이 쌓인 뒤 설계하는 편이 낫다.
2. **개정 후 전수 검색을 절차로.** 이 실행의 조합 검토는 신설 요구사항과 기존 요구사항의 교차만 봤다. SPEC-35는 Decisions 절과 Security 절이 검토 범위 밖이라 남았다. "바뀐 값·규칙을 언급하는 모든 위치"를 문자열로 전수 검색하는 단계를 개정 절차에 넣어야 한다.

## Follow-up

- `.codex-readiness/`와 `.codex-author/`가 이 저장소에서 무시되지 않는다. `git status`에 노출되고 실수로 커밋될 수 있다. `.gitignore`는 승인 범위 밖이라 이 워크플로에서 고치지 않았다.
- 이슈 #60이 `NOT_PLANNED`로 종결돼 `plan` 라운드 한도는 2로 남는다. 2차 실행이 84점(1점 미달)으로 막힌 표본이 그 이슈에 기록돼 있다.
