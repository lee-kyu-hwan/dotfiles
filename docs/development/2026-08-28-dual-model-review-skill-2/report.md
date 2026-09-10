# Quality Goal Report

- Task ID: 20260828T021938Z-42-claude-codex-이중-리뷰-종합-pr-게시-스킬-추가-55cca675
- Mode: strict
- Status: NEEDS_REDESIGN
- Created: 2026-08-28
- Updated: 2026-08-28
- Source goal: #42 Claude+Codex 이중 리뷰 → 종합 → PR 게시 스킬 추가

이 실행은 선행 실행 `20260828T011459Z-...`(Spec 라운드 한도 소진으로 `NEEDS_REDESIGN`)의 재시작이다. 선행 실행의 Spec 개정본을 출발점으로 삼았고, Spec은 이번에 통과했으나 Plan이 라운드 한도에서 멈췄다.

## Classification

`auto` 요청에 대해 `strict`가 선택됐다. 근거는 선행 실행과 동일하다.

- **외부 API 쓰기 + 멱등성(strict 트리거).** 스킬이 `gh pr review`/`gh pr comment`로 GitHub PR에 게시하는 계약을 정의하고, 이슈 #42가 "중복 게시 방지, 커밋 SHA 명시, 재실행 갱신 정책"을 핵심 차별점으로 지목한다.
- **비가역 외부 노출.** 게시 계약 오류는 실제 PR에 되돌리기 어려운 중복·stale 댓글을 남긴다.
- **다층·다파일 변경(standard 조건).** `SKILL.md` + `references/`(4) + `schemas/`(4) + `scripts/`(2) + `tests/`(3)를 신설하고 외부 플러그인 둘을 오케스트레이션한다.
- **요구사항 명시 필요(standard 조건).** 교차비평 라운드 수, synthesizer 편향 완화, 종료 규칙, verdict 정책.
- 라벨 `enhancement`는 신규 기능임을 확인해 주지만 모드를 낮추지 않는다.
- 불확실 시 상위 모드를 택하는 `routing-rules.md` 6번 규칙을 적용했다.

## Review history

| 아티팩트 | 라운드 | 점수 | verdict | blockers | Critical/High | 게이트 |
|---|---|---|---|---|---|---|
| Spec | 1 | 78 | REVISE | SPEC-001~003 | 3건(High) | 실패 — `score_below_85`, `verdict_not_pass`, `blockers_present`, `critical_or_high_finding`, `check_failed:acceptance_criteria_objective` |
| Spec | 2 | 93 | **PASS** | 없음 | 0건 | **통과** |
| Plan | 1 | 70 | REVISE | PLAN-001~002 | 2건(High) | 실패 — `score_below_85`, `verdict_not_pass`, `blockers_present`, `critical_or_high_finding`, `check_failed:placeholders_absent` |
| Plan | 2 | 84 | REVISE | 없음 | 0건 | 실패 — `score_below_85`(1점 미달), `verdict_not_pass` |

Spec은 라운드 2에서 통과했다. 선행 실행이 같은 지점(라운드 2, 89점, blocker 0)에서 폐기된 것과의 차이는 **요구사항 추적표**다. 라운드 2 리뷰어가 표를 직접 검증하고 "every requirement maps to at least one acceptance criterion with a named verification method"를 evidence에 기록했으며, 두 실행 모두를 막았던 `acceptance_criteria_objective`가 이번엔 닫혔다.

Plan은 라운드 1에서 High 2건을 받고 8건 전부를 반영했으나, 라운드 2에서 84점(임계 85에 1점 미달)·`REVISE`로 게이트에 걸렸다. `plan` 라운드 한도는 2이므로 여기서 멈춘다.

## Blocking-finding resolutions

### Spec

| ID | 라운드 1 지적 | 적용한 해소 | 라운드 2 검증 |
|---|---|---|---|
| SPEC-001 | R3.2의 긍정 플래그(특히 `--sandbox read-only`)를 판정하는 AC 부재. Security 절이 AC-29에 잘못 귀속 | AC-48 신설(read-only 존재 + 다른 값 부재 + 여섯 플래그 존재), Security 절 귀속 정정, 추적표 갱신 | **해소.** 리뷰어가 세 위치를 대조 확인 |
| SPEC-002 | R4.2/AC-4가 `line_start`만 검증하나 실제 게시 라인은 `line_end`. 원자적 단일 호출이라 한 건이 전체를 실패시킴 | R4.2를 네 조건(파일 부재 / `line_start` 초과 / `line_end` 초과 / 역전)으로 확장, AC-4에 네 픽스처 요구, R4.4에 순서 제약이 JSON Schema로 표현 불가함을 명시 | **해소** |
| SPEC-003 | 세 목록 조회에 페이지네이션 계약 부재. 단일 페이지 fake로 검증되는 AC들이 구조적으로 검출 불가 | R8.2에 전체 페이지 순회 계약(REST `Link rel=next`, GraphQL `pageInfo.hasNextPage`), 순회 실패 시 부분 목록 대신 오류, R7.14에 반복 호출이 위반 아님 명시, AC-49 신설(다중 페이지 fake), 실패 표 행과 D20 추가 | **해소** |

Spec 라운드 1의 Medium/Low 9건(SPEC-004~012)도 전부 해소 확인됐다. 그중 둘은 오케스트레이터 자신의 오류였다: `model-routing.md` 인용이 틀렸고(실제 표는 quality-goal 자신의 모드 등급 기준이며 "고위험 구현 실패 이후" 한정은 xhigh 행에만 붙는다), `comment-analyzer.md`에 `Output Format` 표제가 없는데 "다섯 에이전트"라고 서술했다.

### Plan

| ID | 라운드 1 지적 | 적용한 해소 | 라운드 2 검증 |
|---|---|---|---|
| PLAN-001 | 검증 9에 자리표시자 `<상태>`·`<빈 finding 집합>`이 남고 `$PR`을 쓰지 않음. 스키마 유효성·쓰기 0건 판정 수단 부재 | `set -euo pipefail` 기반 실행 가능한 "검증 10 스크립트"로 재작성. `init`이 `state_path`를 반환하는 계약 추가, `validate_against_schema`로 계획 검사, `--calls-out` 덤프로 쓰기 0건 단정 | **해소.** 리뷰어가 heredoc 문법과 argv 전달까지 확인 |
| PLAN-002 | T7·T8이 T2~T5의 상태 산출에 의존하는데 그래프가 병렬이고 상태 계약 산출물 부재 | 의존 그래프를 T5 → T7로 수정, `tests/fixtures/state-*.json` 공유 픽스처 도입(T2 생성, T3·T5 갱신, T7·T8 소비) | **부분 해소.** 픽스처 집합에 `excluded`·단일 리뷰어 상태가 빠져 PLAN-010으로 남음 |

Plan 라운드 1의 Medium/Low 중 PLAN-005·PLAN-006·PLAN-008은 해소됐고, PLAN-003·PLAN-004·PLAN-007은 부분 해소로 남았다.

## Plan approval

- Approval timestamp: 없음 — `AWAITING_PLAN_APPROVAL` 단계에 도달하지 못했다
- Plan digest: 등록된 최종 Plan은 `1502a0db35efc7ddd161d374b39b1c28aa8951793fcecb2bbc13a8d9d3033ccd`이나 승인되지 않았다

## Changed files

구현은 시작되지 않았다. 저장소 변경은 durable 문서 세 개뿐이다.

| 파일 | 변경 |
|---|---|
| `docs/development/2026-08-28-dual-model-review-skill-2/spec.md` | 신규. 595행. 요구사항 56건(R1.1~R10.3), AC 54건, 결정 A1~A6·D1~D20, strict 전용 6절, 요구사항 추적표. **라운드 2 PASS** |
| `docs/development/2026-08-28-dual-model-review-skill-2/plan.md` | 신규. 441행. 태스크 11개, 검증 명령 10개 + 검증 10 스크립트, Spec Failure behavior 매핑 표, AC 54건 전수 추적표 |
| `docs/development/2026-08-28-dual-model-review-skill-2/report.md` | 신규. 이 리포트 |

선행 실행의 `docs/development/2026-08-28-dual-model-review-skill/`(초기 dirty 경로)은 바이트 단위로 보존했고 이 작업의 변경에 포함하지 않았다.

`dot_claude/skills/dual-review/`는 만들어지지 않았다. `.gitignore`는 변경되지 않았다. 커밋·푸시·PR 생성·`chezmoi apply`를 수행하지 않았다.

## Verification evidence

실제로 실행한 명령과 결과:

| 명령 | 종료 코드 | 증거 |
|---|---|---|
| `gh issue view 42 --json title,body,labels,comments` | 0 | 이슈 본문과 Codex deep research 코멘트를 요구사항 입력으로 확보 |
| `gh issue view 29 --json title,state,body` | 0 | #29가 `OPEN`·미구현임을 확인 → D8의 근거 |
| `git rev-parse HEAD`, `git status --porcelain` | 0 | `6d8ccad16b4f8345130fe56913a2eead4169030f`, dirty에 선행 실행 문서 디렉터리 |
| `codex exec --sandbox read-only --ephemeral --model gpt-5.6-sol -c model_reasoning_effort="low"` | 0 | 모델 응답 `Ready.` — strict 라우팅 프리플라이트 통과 |
| `gh auth status` | 0 | 계정 `lee-kyu-hwan`, 스코프 `gist, project, read:org, repo, user, workflow` |
| `gh api graphql`(Mutation 인트로스펙션) | 0 | `resolveReviewThread` 존재. `ResolveReviewThreadInput`의 필수 입력은 `threadId`(`ID!`) 하나 |
| `gh api graphql`(`PullRequestReviewThread` 필드) | 0 | `comments`·`isResolved`·`viewerCanResolve`·`isOutdated`·`path`·`line`·`originalLine` 존재 → R7.7 실현 가능 |
| `gh api repos/zambaguni/zambaguni-front/pulls/{1255,1211,1313}/comments`(키 집합만) | 0 | 리뷰 코멘트 79건. 세 PR 동일 구성: `path`·`line`·`side`·`start_line`·`start_side`·`body`·`node_id`·`pull_request_review_id`·`original_line`·`diff_hunk` 및 deprecated `position` → R7.16·R7.17·D18의 근거 |
| `git check-ignore -q .claude/quality-state/` | 0 | `.gitignore:25`에 등록됨 |
| `chezmoi source-path` | 0 | `/Users/lee-kyu-hwan/code/dotfiles` — **이 워크트리가 아님**. PLAN-007의 실측 근거 |
| `chezmoi --source "$PWD" target-path dot_claude/skills/quality-goal/SKILL.md` | 0 | `/Users/lee-kyu-hwan/.claude/skills/quality-goal/SKILL.md` — AC-35 판정 수단 확정 |
| `quality_state.py capture-baseline` | 0 | `base_revision=6d8ccad...`, `initial_dirty_paths=['docs/development/2026-08-28-dual-model-review-skill/']` |
| Spec 자체 검증(절 존재·플레이스홀더·AC 중복·추적표 정합) | 0 | 템플릿 17절 전부 존재, 플레이스홀더 0, AC 번호 중복 0, 요구사항 56건 전수 등재(누락 0·유령 0), `검증:` 없는 AC 0건 |
| `validate_review.py validate`(Spec r1·r2, Plan r1·r2) | 0 | 네 번 모두 `{"valid":true,"errors":[]}` |
| `validate_review.py gate`(Spec r1) | 3 | `passed:false` — 5개 사유 |
| `validate_review.py gate`(Spec r2) | 0 | **`passed:true`** |
| `validate_review.py gate`(Plan r1) | 3 | `passed:false` — 5개 사유 |
| Plan 자체 검증(절 존재·자리표시자·추적표 정합) | 0 | 템플릿 전 절 존재, 자리표시자 0, AC 54건 전수 매핑(누락 0·유령 0·빈칸 0) |

구현이 없으므로 코드 검증 범주는 전부 미실행이다.

- 단위 테스트: **미실행.** `dot_claude/skills/dual-review/tests/`가 아직 존재하지 않는다.
- 타입 체크: **not configured.** 저장소 루트에 `tsconfig.json`·`pyproject.toml`·`mypy.ini`가 없다.
- 린트: **not configured.** 저장소 루트에 린터 설정 파일이 없다.
- 빌드: **not configured.** 저장소 루트에 `Makefile`·`package.json`·빌드 스크립트가 없다.
- E2E: **미실행.** Spec의 고위험 E2E 셋(AC-27, AC-37, 수동 게시)은 모두 구현 이후 단계다.

## Remaining advisory findings

Plan 라운드 2가 남긴 7건. 셋(PLAN-009·PLAN-010·PLAN-012)은 **라운드 2 개정이 새로 만든 회귀**이며 `new_blocker_evidence`가 달려 있다.

| ID | 심각도 | 내용 | 영향 | 후속 조치 |
|---|---|---|---|---|
| PLAN-009 | Medium | 검증 번호 재배치 후 strict-only 절 세 곳의 "검증 9" 참조가 낡았다. 특히 "No production mutation confirmation"의 "검증 9는 GitHub를 읽기만 하고 쓰기 3튜플이 0건임을 함께 단정한다"는 **문언 그대로 거짓**이다 — 실제 검증 9는 로컬 스키마 검사이고 GitHub를 건드리지 않는다 | 프로덕션 무변경 확인 절이 존재하지 않는 단정을 근거로 든다 | L418·L434·L439의 "검증 9"를 "검증 10"으로 정정하고, 문서 전체의 검증 번호 참조를 일괄 대조 |
| PLAN-010 | Medium | 상태 픽스처 3종(`state-minimal`·`state-base-mismatch`·`state-scope-reduced`)이 T7의 요약 문구 단정을 감당하지 못한다. 리뷰어 `excluded` 사유·단일 리뷰어 승인·`single_source` 분류를 담은 픽스처를 만들라는 지시가 없다 | "픽스처만 읽는다" 규칙과 T7의 새 단정이 조합상 결손을 만든다 | `state-excluded-reviewer.json`·`state-single-reviewer.json` 생성을 T4·T5에 지정하고 File map 픽스처 목록에 추가 |
| PLAN-012 | Medium | 검증 10의 `--synthesis` 리터럴 `{"findings":[],"classification":{}}`가 `synthesis.schema.json`과 일치한다는 근거가 없다. T1은 루트 필드 구성을 정하지 않고, `plan`이 `--synthesis`를 스키마 검증하는지도 인터페이스 표에 없다 | 구현 결함이 아닌 이유로 AC-37 검증이 실패할 수 있다 | synthesis 루트 필드 구성을 T1에 고정하고 그 최소 유효 문서를 검증 10에 쓰거나, `plan`이 `--synthesis`를 검증하지 않음을 인터페이스 표에 명시 |
| PLAN-007 | Medium | AC-35의 판정 수단이 Spec 명시(`chezmoi diff`)와 달라졌는데 편차 선언이 없고, T11 3항은 여전히 `chezmoi diff`를 지시해 Plan 안에서 두 명령이 공존한다 | 같은 AC에 두 판정 수단 | 하나로 통일하고 Spec 명시 수단과의 편차를 기록 |
| PLAN-003 | Medium | 추적표 4개 행이 AC의 일부 조건만 판정한다: AC-5의 강등 분류, AC-18의 상태 조회 조건, AC-21의 라운드 상한, AC-49의 `resolved` 오분류 부재 | 해당 조건이 테스트로 강제되지 않는다 | 각 담당 태스크의 테스트 목록에 누락 조건 단정을 추가하고 추적표 기대 결과를 보강 |
| PLAN-004 | Medium | AC-41의 행동 단정(빈 `evidence` 반박 미채택)을 담을 테스트 파일이 지정되지 않았다. File map·Spec Test strategy 모두 AC-41을 "계약 문구"로만 배정 | 구현자가 중복 작성하거나 누락할 수 있다 | T4 지시와 File map 양쪽에 파일명을 명시하고 Spec Test strategy와의 편차를 기록 |
| PLAN-011 | Low | `--calls-out` 덤프 원소 형태가 미정인데 검증 10 스크립트는 `c["method"]`로 키 접근한다(배열이면 `TypeError`). `init --requested-base`에 `(선택)` 표기가 없다 | 인터페이스 세부 불일치로 검증이 실패할 수 있다 | 덤프 원소를 `{kind, method, target}` 객체로 명시하고 `--requested-base`를 선택 인자로 표기 |

Spec 라운드 2가 남긴 SPEC-007(Medium, R10.3의 "리포트" 하위 조항에 대응 AC 부재)은 Plan의 "잔여 advisory 처리" 절에서 다뤘다. 게시 요약 절반은 T7 테스트로 강제하고 리포트 산문만 문서 지시로 남기는 것으로 범위를 나눴다.

## 오케스트레이터 절차 이탈 (자기 기록)

Plan 라운드 1 리뷰를 받은 뒤 `record-review`를 실행하기 전에 개정을 먼저 수행했다. `quality_state.py:585`의 digest 교차 검증은 **등록된 파일의 현재 digest**를 비교하므로, 리뷰어가 실제로 읽은 판본(`9271923614227bff32420bd31615cfd17ff6dfc08ea9fe0669d26cdaa885fbaf`)은 이미 덮어써진 뒤였고 untracked 파일이라 git 복원도 불가능했다.

라운드 카운트를 정확히 유지하기 위해 개정본 digest로 라운드 1을 기록했다. 결과적으로 `reviews.plan[0].artifact_digest`가 리뷰어가 읽은 파일의 digest가 아니다. 리뷰 JSON 자체(`plan-review-r1.json`)는 반환된 그대로 보존했고 수정하지 않았다. 이 사실을 `.claude/quality-state/<task-id>/plan-review-r1-NOTE.md`에도 남겼다.

계약이 요구하는 순서는 리뷰 저장 → `validate` → `record-review` → `gate` → 개정이며, 이번에 그 순서를 지키지 못했다. Spec 라운드 1·2와 Plan 라운드 2는 순서를 지켰다.

## Final status

- Status: `NEEDS_REDESIGN`
- Machine-readable reason: `REVIEW_LIMIT_EXHAUSTED:plan`

`plan` 리뷰의 라운드 한도(최대 2)를 소진했고 라운드 2의 게이트가 `score_below_85`(84점, 1점 미달)와 `verdict_not_pass`로 실패했다. `plan-rubric.md`의 "After round 2 without a passing gate, stop and record `NEEDS_REDESIGN`" 규칙에 따라 중단했다.

설계가 틀렸다는 판정이 아니다. Spec은 93점으로 통과했고, Plan 라운드 2도 blocker 0·Critical/High 0이며 남은 7건은 전부 Medium/Low다. 그중 셋은 라운드 2 개정이 만든 회귀(낡은 검증 번호 참조, 픽스처 결손, synthesis 리터럴 근거 부재)로 수정이 기계적이다.

다음 결정은 사용자의 것이다. 새 워크플로를 시작하면 이 Spec(라운드 2 PASS, `bf75e7f1…`)과 Plan 개정본(`1502a0db…`)이 출발점이 되고, 위 표의 후속 조치 7건이 첫 Plan 라운드에서 반영해야 할 목록이다. Spec은 이미 통과했으므로 재검토 없이 그대로 쓸 수 있다.

## 워크플로 도구 관련 관찰

- **`plan` 라운드 한도 2.** 이슈 #53이 `spec`을 2→3으로 올렸고(v3.0.0에서 확인), `plan`은 2로 남았다. 이번 실행은 spec에서는 라운드 3을 쓰지 않았지만 plan에서 한도에 걸렸다. spec과 plan이 같은 성격의 문서 산출물임을 감안하면 `plan`에도 같은 논거가 적용될 수 있다.
- **개정이 회귀를 만드는 패턴.** 라운드 2에서 새로 제기된 셋(PLAN-009·010·012)이 모두 라운드 1 지적을 해소하는 과정에서 생겼다. 특히 PLAN-010은 두 지적(PLAN-002의 픽스처 규칙, PLAN-006의 요약 단정)을 각각 해소하면서 그 상호작용을 놓친 결과다. 여러 지적을 한 번에 반영할 때 개별 해소의 조합을 검토하는 단계가 없다.
