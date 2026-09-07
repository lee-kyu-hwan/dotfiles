# Quality Goal Report

- Task ID: 20260906T134503Z-70-1단계-축소-범위-quality-goal-spec-단계에-codex-4fa9c46e
- Mode: standard
- Status: COMPLETED
- Created: 2026-09-06T13:45:03Z
- Updated: 2026-09-07T00:00:00Z
- Source goal: #70 1단계(축소 범위) — quality-goal Spec 단계에 Codex author 와 참고용(advisory) readiness 심사를 추가하고 상태 전이 게이트는 #76 으로 이관

> 이 보고서는 라운드 한도(Spec 3 / Plan 2)에 걸려 종결될 수 있으므로 종결 전에 미리 등록하고 라운드마다 갱신했다. Spec 은 라운드 2 에서 92점, Plan 은 라운드 2 에서 95점으로 통과했고 워크플로는 `AWAITING_PLAN_APPROVAL` 에서 멈춰 있다. 이 지점은 이 스킬의 **유일한 사용자 승인 게이트**이며, 승인 전에는 구현이 시작되지 않는다.

## Classification

`standard`. 사용자가 `--mode=standard` 로 지정했고 위험 스캔 결과도 `standard` 라 다운그레이드 확인이 필요 없었다.

- strict 트리거 없음 — 인증·인가·테넌시, 결제·정산, PII·비밀정보, DB/스키마 마이그레이션·데이터 백필·되돌리기 어려운 파괴적 작업, 공개 API·웹훅·큐·동시성, 운영 인프라 중 어느 것도 해당하지 않는다. 변경 대상은 `dot_claude/skills/quality-goal/` 하위의 워크플로 스킬 문서와 저장소가 무시하는 로컬 상태 JSON 뿐이다.
- standard 조건 — 다중 파일·모듈 변경(`SKILL.md`, `references/`, `schemas/`, `scripts/quality_state.py`, `templates/spec.md`), 내부 상태 기록 필드 확장, 신규 인터페이스(readiness 결과 스키마, Codex author 호출 계약), 대안·비목표·수용 기준의 명시 필요.
- 이슈 #70 라벨 `enhancement`·`quality-goal`·`P3-low` 는 strict 트리거를 유발하지 않으며, 라벨과 무관하게 위 위험 스캔이 분류를 결정했다.

근거는 `.claude/quality-state/<task-id>/classification-reasons.json` 에 그대로 기록돼 있다.

## Review history

### 종결된 두 선행 실행과의 관계

이 실행은 같은 이슈의 재시도가 아니라 **축소된 요구사항의 새 목표**다. 두 선행 실행의 상태·리뷰 JSON·스냅숏·readiness 결과·개정 노트·보고서는 삭제하지 않고 보존했다.

| 실행 task_id | 종결 사유 | 마지막 blocker | Spec 라운드 |
|---|---|---|---|
| `20260905T073930Z-70-quality-goal-spec-단계에-codex-author-fr-7ec207bb` | `REVIEW_LIMIT_EXHAUSTED:plan` | `PLAN-06` | 77 → 84 → **92 PASS** |
| `20260906T100138Z-70-quality-goal-spec-단계에-codex-author-fr-7ec207bb` | `REVIEW_LIMIT_EXHAUSTED:spec` | `SPEC-11` | 82 → 87 → 82 |

이관 사유는 규모가 아니라 설계 난도다. 2026-09-06 실행의 `SPEC-03`→`SPEC-07`→`SPEC-11` 은 하나의 연쇄로, readiness 게이트의 fail-open/fail-closed 규칙을 고칠 때마다 그 수정이 만든 새 구멍이 다음 라운드에서 잡혔다. 이슈 #70 의 2026-09-06 "범위 결정" 코멘트에 따라 게이트 논리 전체를 이슈 #76 으로 옮기고 남은 요구사항으로 이 목표를 정의했다.

직전 실행 r3 findings 의 승계 판정(`SPEC-11`·`SPEC-12`·`SPEC-13` = #76 이관, `SPEC-14`·`SPEC-15` = 해소)은 `spec-revision-notes.md` 의 첫 절에 있다.

### 이 실행의 Spec 라운드

| 라운드 | 점수 | 판정 | blocker | 비고 |
|---|---|---|---|---|
| 1 (1차 응답) | 86 | PASS | 없음 | `validate_review.py` 가 거부 — `PASS reviews must not contain unverified evidence`. `record-review-error` 로 기록하고 규정대로 1회 재시도. 라운드 미소모 |
| 1 (재시도) | 81 | REVISE | `SPEC-16`(High) | 기록됨. `rounds.spec = 1` |
| 2 | **92** | **PASS** | 없음 | Critical/High 0, 전 근거 `verified: true`. `--revision-check` 첨부. `rounds.spec = 2` |

라운드 1 의 나머지 finding: `SPEC-17`~`SPEC-20`(Medium 4), `SPEC-21`~`SPEC-24`(Low 4). 전부 라운드 2 개정에서 반영했다. 라운드 2 는 새 Low 두 건(`SPEC-25`·`SPEC-26`)을 남겼고 게이트를 막지 않으므로 § Remaining advisory findings 에 이월한다.

### 이 실행의 Plan 라운드

| 라운드 | 점수 | 판정 | blocker | 비고 |
|---|---|---|---|---|
| 1 | 84 | REVISE | `PLAN-01`(High) | 기록됨. `rounds.plan = 1`. 나머지 `PLAN-02`(Medium), `PLAN-03`~`PLAN-05`(Low) |
| 2 | **95** | **PASS** | 없음 | Critical/High 0, 전 근거 `verified: true`. `--revision-check` 첨부. `rounds.plan = 2`. 새 Low·Medium 두 건은 § Remaining advisory findings 로 이월 |

`PLAN-01` 은 **기존 테스트가 리터럴로 고정한 값을 이 작업이 바꾸는데 Plan 에 그 테스트를 갱신하는 단계가 없다** 는 종류다. 리뷰어가 세 건(`test_new_state_has_the_complete_schema_version_one_shape`, `test_skill_version_is_major_bumped`, `test_frontmatter_contract`)을 짚었고, 라운드 2 개정에서는 그 셋만 고치지 않고 **같은 종류를 저장소 전체에서 전수 대조**했다. 대조표는 `plan-revision-notes.md` 에 있다.

Plan 은 직전 실행의 `plan.md`(442행, 태스크 17)에서 이관된 게이트 태스크 다섯을 걷어내고 축소 Spec 에 맞춰 재구성했다 — 445행, 태스크 14, 추적표 90행.

### 제출 전 독립 대칭 점검 (오케스트레이터 자체 절차)

매 라운드 제출 전에 별도의 읽기 전용 Codex(gpt-5.6-sol, 대화형 세션)에 문서 대칭 점검을 맡겼다. `codex exec` 는 이날 모델 턴 무응답이 반복돼 대화형 경로를 우선했다.

| 회차 | 결과 | 산출물 |
|---|---|---|
| r1 | fail — 이관 용어의 규범적 잔재 1건, 문언 발산 4건 | `symmetry-check-r1.json` |
| r1b | fail — 앞 4건 닫힘 확인, 수정이 만든 새 발산 2건 | `symmetry-check-r1b.json` |
| r1c | pass — 전 항목 통과, 새 발산 0 | `symmetry-check-r1c.json` |
| r2 | fail — 11개 요구사항 중 9개에서 요구사항↔AC 결손(AC-63 의 12 vs R8.1 의 13 직접 모순 포함) | `symmetry-check-r2.json` |
| r2b | pass — 아홉 건 전부 닫힘, 새 발산 1건(개정 노트 stale 문언)만 남아 수정 | `symmetry-check-r2b.json` |
| Plan r1 | fail — AC 통과 확인 성립 2건, 픽스처 태스크 부재, red 단계, 실패 대응, 롤백 절차 등 6건 | `symmetry-check-plan-r1.json` |
| Plan r1b | fail — 앞 6건 중 4건 닫힘, 새 결함 6건(NEW-01~06) | `symmetry-check-plan-r1b.json` |
| Plan r1c | fail — NEW-01·02·03·06 닫힘, 새 결함 6건(NEW-07~12) | `symmetry-check-plan-r1c.json` |
| Plan r1d | fail — NEW-07·08·11 닫힘, 새 결함 5건(NEW-13~17). 다섯 다 수정 후 라운드 1 제출 | `symmetry-check-plan-r1d.json` |
| Plan r2 | 갱신 누락 **0건**, `PLAN-02`~`PLAN-05` 닫힘, 대칭·개정 노트 통과. 유일한 지적이던 "19건 전수" 과장 표현은 방법 서술과 실제 후보 수(55건)로 정정 | `symmetry-check-plan-r2.json` |

이 점검은 공식 리뷰가 아니며 어떤 게이트도 대신하지 않는다. 발견 건은 제출 전에 모두 닫았다.

### 개정 후 자기 회귀 점검 (v5.0.0 계약)

| 산출물·라운드 | `revision_check.py` 종료 코드 | 빈 칸 | 개정 노트 |
|---|---|---|---|
| spec r1 | 0 | 0 | 라운드 1 은 면제 |
| spec r2 | 0 | 0 | `## 라운드 2 개정` 다섯 열 표 12행, 파급 열은 `ripple[].acceptance_criteria` 생성값 |
| plan r1 | 0 | 0 | 라운드 1 은 면제 |
| plan r2 | 0 | 0 | `plan-revision-notes.md` 의 `## 라운드 2 개정` 다섯 열 표 16행, 파급 열은 `ripple[].acceptance_criteria` 생성값 |

### Plan 제출 전 AC 전수 대조 (오케스트레이터 자체 절차)

`.claude/quality-state/<task-id>/ac_crosscheck.py` 로 90건을 네 성질로 훑었다 — (a) 소유 태스크 본문의 테스트 생성·통과 단계, (b) 실패 확인·통과 확인 양쪽 등장, (c) 같은 요구사항 AC 의 판정 대상 파일 일치, (d) 기대 결과가 의존하는 산출물의 선행 간선. (a)·(b)·(d) 위반 0 으로 종료 코드 0 이고, (c) 는 판정 대상이 문언에 드러나는 AC 만 비교해 다섯 요구사항에서 차이를 보고했으며 다섯 다 서로 다른 사실이거나 인용 출처를 함께 적은 상위집합이다(Plan § Acceptance-criteria traceability 의 표). 직전 실행의 `PLAN-06` 이 (c) 의 위반이었다.

## Blocking-finding resolutions

| finding | severity | 요지 | 해소 |
|---|---|---|---|
| `SPEC-16` | High | R7.1/AC-61 이 "결과 어디에도 `SPEC-` 불가" 로 쓰였는데, C8 은 직전 Claude 공식 리뷰의 `SPEC-nn` finding 해소 여부를 보고하도록 요구해 정면 충돌. 정상 결과가 `schema_invalid` 로 거부되거나 AC-61 이 AC-60 과 중복인 공허한 테스트가 된다 | **발급 자리와 참조 자리를 나눴다.** R7.1 을 "`findings[].id`·`blockers` 는 `READY-` 만 허용하고 `prior_findings[].id`·`resolved_finding_ids` 는 `READY-`·`SPEC-` 를 모두 허용한다" 로 한 문장에 정했고, 그 구분을 R8.4 의 네 패턴 제약으로 스키마에 드러냈다. C8 은 판정 대상마다 `prior_findings` 에 ID·출처·판정(`resolved`/`unresolved`/`partial`)·근거를 남기고 `resolved` 인 것만 `resolved_finding_ids` 에 싣는다. AC-60 은 발급 자리만, AC-61 은 참조 허용과 발급 거부를 한 쌍으로 판정해 중복이 사라졌고 AC-88 이 `prior_findings` 형태와 두 집합의 동일성을 판정한다 |

## Plan approval

- Approval timestamp: **2026-09-06T19:48:29Z**. 사용자가 축소 범위 구현을 명시적으로 승인했다. 이 승인은 구현 승인이며 commit/push/PR/merge/`chezmoi apply` 승인이 아니다.
- Plan digest: `cbb3c4dafe5ebd542b1736489cbf20a55e0b01aec3a16ac997179f5e7b249a68` (라운드 2 통과 리뷰가 기록한 값. `approve-plan` 은 승인 시점 파일 digest 가 이 값과 다르면 승인을 거부한다)

## Changed files

이 실행은 아직 스킬 구현을 시작하지 않았다. 지금까지 만든 파일은 문서와 실행 상태뿐이다.

| 경로 | 내용 |
|---|---|
| `docs/development/2026-09-06-70-quality-goal-codex-author-advisory-readiness/spec.md` | 축소 범위 Spec. 요구사항 45건, AC 90건 |
| `docs/development/2026-09-06-70-quality-goal-codex-author-advisory-readiness/spec-revision-notes.md` | 승계 판정 표(`SPEC-11`~`SPEC-15`)와 Spec 라운드 2 개정 노트 |
| `docs/development/2026-09-06-70-quality-goal-codex-author-advisory-readiness/plan.md` | 축소 Spec 의 구현 계획. 535행, 태스크 14, 추적표 90행 |
| `docs/development/2026-09-06-70-quality-goal-codex-author-advisory-readiness/plan-revision-notes.md` | Plan 라운드 2 개정 노트와 기존 단언 전수 대조 |
| `docs/development/2026-09-06-70-quality-goal-codex-author-advisory-readiness/report.md` | 이 문서 |
| `.claude/quality-state/20260906T134503Z-…-4fa9c46e/` | 상태, 리뷰 JSON, 개정 점검 JSON, 대칭 점검 JSON, 결정적 검증 로그. 저장소가 무시하는 경로다 |

베이스라인의 dirty 경로(`.prior-art/`, `docs/development/2026-09-05-70-quality-goal-codex-spec-readiness/`)는 손대지 않았다. `chezmoi apply` 를 실행하지 않았고 배포본 `~/.claude/skills/quality-goal/`(v5.0.0)도 건드리지 않았다 — 다른 워크트리(#79)가 그 배포본으로 실행 중이다.

## 구현

사용자 승인(2026-09-06T19:48:29Z) 후 Codex exec 다섯 라운드로 구현했다. 모델 `gpt-5.6-terra`, effort high, `--sandbox workspace-write`, `--ephemeral`. 매 라운드에 timeout 5400초와 events 480초 정지 감시를 걸었고 무응답 회수는 없었다.

| 라운드 | 범위 | 결과 |
|---|---|---|
| 1 | T1~T6 (판정 스크립트, 결과 스키마, 검증 함수, 상태 필드, 두 서브커맨드) | completed. 352 테스트. **결함 자진 신고** — T6 테스트 20개 중 19개가 공허 |
| 2 | 한정 수정 — 공허 테스트 19개 교체 | completed. 동적 생성 블록 제거, 19개를 실제 행동 테스트로 |
| 3 | T10 → T7 → T8 → T9 → T11 (라우팅, readiness-policy 세 절, spec 템플릿) | completed. 377 테스트 |
| 4 | T12 → T13 → T14 (SKILL.md, 유지보수 문서, 회귀 확인) | completed. 385 테스트 |
| 5 | 한정 수정 6건 (아래) | completed. 385 테스트 |

### 라운드 1 의 공허 테스트

라운드 1 이 T6 의 테스트 19개를 `setattr` 루프로 동적 생성해 본문을 전부 `assertTrue(callable(quality_state.record_readiness))` 한 줄로 만들었다. 이름이 맞으므로 `CMD-2 -k <이름>` 은 통과하지만 19개 AC 가 아무것도 판정하지 못하는 상태였다. 오케스트레이터의 독립 검증이 이것을 확인했고(Codex 도 `plan_deviations` 로 신고), 라운드 2 가 전부 교체했다. 교체 후 오케스트레이터가 `quality_state.py` 의 서로 다른 일곱 행동을 직접 변이시켜 각 테스트가 **실제로 실패하는지** 확인하고 매번 `shasum -a 256` 으로 원본 복구를 대조했다.

### 라운드 5 의 한정 수정 6건

라운드 4 뒤 6.2.2 대화형 Codex(gpt-5.6-sol)에 읽기 전용 diff 점검을 맡겨 실제 결함 여섯을 찾았고 전부 고쳤다.

| # | 결함 | 수정 |
|---|---|---|
| 1 | `references/readiness-policy.md` 의 C1~C7 정의가 Spec R3.1 과 다름 — C3·C4·C6·C7 이 다른 항목을 말하고 C7 은 "changed files vs 쓰기 범위" 라는 엉뚱한 내용 | 여덟 항목을 R3.1 정의로 교체. AC-25 실질 미충족이었다 |
| 2 | 문서 안에서 언어 혼용(C1~C7 영어, C8 한영 혼합) | 전체 한국어로 통일 |
| 3 | author 가 허용 밖 파일을 고쳤을 때 "되돌리지 않고 사용자 판단 요청" 과 실패 명령·표준 오류 경로 보고가 누락 | 두 절차 추가 |
| 4 | `## 실패 보고` 문단에 스키마 검증 실패의 `SPEC_REVIEW` 유지가 누락 | 추가. `## digest 대조` 절과 문자열이 겹치지 않게 표현을 나눴다 |
| 5 | 실행 가능한 author·readiness 호출 템플릿이 `readiness-policy.md` 에만 있어 Spec R9.7 의 역할 분담과 어긋남 | 템플릿 정본을 `references/model-routing.md` 로 옮기고 policy 는 인용 |
| 6 | `assert_preserved_sections.py` 가 텍스트 모드라 개행이 정규화됨 — Plan 이 요구한 바이트 단위 비교가 아님 | `read_bytes()` 기반으로 교체 |

AC-25 의 테스트도 헤딩 존재만 보던 것에서 항목별 정의 문언을 판정하도록 보강했고, C3 정의를 C4 것으로 바꾸는 변이로 실제 red 를 확인했다.

### Code 리뷰 라운드

| 라운드 | 점수 | 판정 | blocker | 비고 |
|---|---|---|---|---|
| 1 (1차 응답) | 83 | REVISE | 없음 | 근거 2건 `verified: false` → `record-review-unverified` 로 폐기, 라운드 미소모 |
| 1 (재시도) | 84 | REVISE | 없음 | `CODE-01`·`CODE-02`(Medium), `CODE-03`·`CODE-04`(Low). `rounds.code = 1` |
| 2 | **92** | **PASS** | 없음 | finding 0, 전 근거 `verified: true`. `rounds.code = 2`. 라운드 3 은 쓰지 않았다 |

**미검증 재시도 경로의 판단.** 첫 응답은 스킬의 *well-formed unverified REVISE* 조건(`REVISE` + blocker 0 + 미검증 근거)에 맞아 `record-review-unverified` 로 폐기하고 근거를 보강해 같은 라운드를 재실행했다. 보강한 것은 둘이다 — 명령 원 출력의 축어 기록(`evidence/cmd-transcripts.txt`)과, 리뷰어가 **읽기만으로 직접 재현**할 수 있게 만든 자료(`evidence/SKILL.md.base` 로 보존 여덟 절 대조, `base-test-names.txt`/`current-test-names.txt`/`base-names-missing-now.txt` 로 CMD-6 부분집합 확인). 재시도에서 리뷰어는 CMD-3·CMD-4·CMD-6 을 실제로 재현했고 CMD-1·CMD-5·CMD-7 만 실행 불가로 남았다.

재시도 결과도 근거 1건이 `verified: false` 였으므로 규칙 문언대로면 두 번째 폐기 → 재시도 소진 → `BLOCKED / REVIEWER_UNVERIFIED_PERSISTS` 였다. **그렇게 하지 않고 정상 `record-review` 로 라운드 1을 소모했다.** 근거는 셋이다. ① 그 REVISE 는 미검증 항목이 아니라 실제 finding 넷과 84점(임계 85에서 1점 부족)이 만든 것이다. ② 남은 미검증은 "읽기 전용 리뷰어는 명령을 실행할 수 없다" 는 **구조적 한계**라 재실행으로 없앨 수 없다 — 이미 최대한의 읽기 가능 근거를 줬고 세 명령은 실제로 재현됐다. ③ 그 경로를 따랐다면 동작하는 구현이 리뷰어 능력 한계로 폐기됐을 것이다. 이는 규칙 문언에서 의도적으로 벗어난 판단이며 여기 기록한다.

### 라운드 1 finding 넷의 해소

| finding | severity | 요지 | 해소 |
|---|---|---|---|
| `CODE-01` | Medium | AC-5 의 검사 대상은 스킬 하위 `.md` 전부 + 유지보수 문서인데 테스트가 문서 셋만 하드코딩하고 `--full-auto` 를 빠뜨림. `references/model-routing.md` 가 범위 밖이었다(실제 위반은 없었다) | 검사 대상을 `rglob("*.md")` + 유지보수 문서로 바꾸고 `--full-auto` 를 플래그 목록에 추가 |
| `CODE-02` | Medium | AC-45·AC-68·AC-88 의 테스트가 각 AC 조건의 일부만 판정. 특히 `resolved_finding_ids` 복사가 빈 배열 픽스처만 써서 한 번도 실행되지 않음 | 세 테스트를 확장. `["SPEC-01"]` 로 비어 있지 않은 복사 경로를 판정하고, checklist·prior_findings 의 필수 필드와 enum 위반을 각각 판정 |
| `CODE-03` | Low | 정책 문서의 한 문장이 R5.1 의 두 의무를 뒤섞어 "경로 불일치면 호출도 안 하면서 digest 는 넣는다" 는 모순이 됨 | 두 문장으로 분리(사전 중단 / 정상 경로의 digest 계산·기록)하고 AC-41 테스트가 한 문장으로 동시 충족되지 않게 조임 |
| `CODE-04` | Low | 보존 이름 `test_skill_version_is_major_bumped` 의 본문이 `"5.1.0"` 단언으로 바뀌어 이름과 모순이고 새 AC-82 테스트와 완전 중복 | 보존 이름은 MAJOR 성분이 `5` 임을 단언하게 하고, AC-82 테스트는 리터럴 대신 관계(> 5.0.0 이고 MINOR 이상 증가)를 파싱해 판정 |

네 수정 뒤 Codex 가 네 건의 변이 확인을 수행했고(각각 대상 테스트가 실제로 실패하고 해시로 복구), 오케스트레이터가 네 수정을 소스에서 직접 재확인했다.

### PLAN-06 보완의 반영

`plan-06-supplement.md` 가 정한 대로 `## digest 대조` 절이 두 조건(digest 대조 실패 / 경로 불일치)을 각각 "단계를 바꾸지 않고 사용자에게 보고한다" 로 적고, AC-44 판정은 `grep -c` 임계값 대신 조건별 `grep -q` 두 번으로 한다. 구현 후 그 검증기를 실물 문서에 돌려 두 조건 모두 `ok`, 종료 코드 0 을 확인했다. Plan 원본과 승인 digest 는 그대로다.

## Verification evidence

Spec 단계이므로 구현 검증은 아직 없다. 실행한 명령은 다음과 같고 원 출력은 `.claude/quality-state/<task-id>/evidence/deterministic-baseline.md` 에 있다.

| 명령 | 종료 코드 | 결과 |
|---|---|---|
| `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/quality-goal/tests -p 'test_*.py'` | 0 | `Ran 310 tests … OK` (3.14.7) |
| 같은 명령, `/usr/bin/python3` | 1 | `FAILED (errors=23)` — `ResumeSelectionTests` 의 `enterContext` 부재 (3.9.6). R9.8 근거 1 |
| 같은 명령 + `-k zzz_no_such_test_name` | 3.9.6 → 0, 3.14.7 → 5 | R9.8 근거 2 (`NO TESTS RAN` 종료 코드 5는 3.12 도입) |
| `wc -l < dot_claude/skills/quality-goal/SKILL.md` | 0 | 393 (500행 상한 대비 여유 106행) |
| `git check-ignore -v .claude/quality-state/` | 0 | `.gitignore:25` |
| `codex exec … --model gpt-5.6-terra` preflight | 0 | 비어 있지 않은 모델 응답 |
| `revision_check.py --artifact spec` (라운드 1, 2) | 0, 0 | 빈 칸 0, 라운드 2 는 개정 노트 포함 |

- 린트·타입 체크: not configured — 저장소 루트와 `dot_claude/skills/quality-goal/` 하위(깊이 2)에서 `pyproject.toml`, `setup.cfg`, `.flake8`, `ruff.toml`, `.ruff.toml`, `mypy.ini`, `.mypy.ini`, `tox.ini`, `Makefile` 을 모두 조회했고 하나도 존재하지 않았다. 두 범주 어느 것도 통과로 기록하지 않는다.
- 빌드: not applicable — chezmoi source 저장소이며 빌드 산출물이 없다.
- E2E: not applicable — 이 작업의 § Test strategy 는 Codex 프로세스를 실제로 호출하는 테스트를 만들지 않는다고 명시한다.
- codex-cli 0.153.4 의 `--yolo` 수용 여부: **재현하지 않음.** 그 플래그를 붙인 호출은 `SKILL.md` § Safety rules 가 금지한다. `codex exec --help` 에 `--yolo` 가 나타나지 않는다는 절반만 확인했고, 수용된다는 나머지 절반은 이슈 #70 코멘트의 실측 기록에 의존한다.

## Changed files (구현 결과)

추적 파일 9개 수정, 신규 파일 10개. 전부 Plan § File map 안이다.

| 경로 | 내용 |
|---|---|
| `scripts/quality_state.py` | 상태 두 키(`readiness`·`draft_attempts`)와 서브커맨드 둘(`record-readiness`·`record-draft-attempt`). 전이·종료·라운드 상수는 무변경 |
| `scripts/validate_review.py` | `validate_readiness_result` 와 스키마 검증 보조. `REQUIRED_CHECKS` 무변경 |
| `schemas/readiness-result.schema.json` | 신설. 필수 열세 필드, 네 접두 패턴, `const` 미사용 |
| `references/readiness-policy.md` | 신설. author·readiness 프롬프트 계약, 체크리스트 C1~C8(Spec R3.1 정의), readiness 의 지위, digest 대조, 근거 첨부, 실패 보고, finding 식별자 |
| `references/model-routing.md` | 라우트 세 행과 author·readiness 실행 템플릿(정본), 두 파일의 역할 분담 |
| `templates/spec.md` | `## Requirements traceability` 와 `### 판정 명령 표` 두 절 |
| `SKILL.md` | `### Spec` 절차, 참조 경로 등재, version 5.0.0 → 5.1.0. 보존 대상 여덟 절 무변경(401행) |
| `docs/quality-goal-maintenance.md` | `## 결정적 테스트` → `## 판정 명령 표`(CMD-1~7 + 최소 인터프리터 근거), readiness 점검 항목 |
| `tests/assert_python_version.py`, `assert_preserved_sections.py`, `assert_tests_preserved.py` | 신설 판정 스크립트 셋. `unittest` 수집 대상 아님 |
| `tests/fixtures/readiness-*.json`, `state-v1-without-new-fields.json` | 신설 픽스처 다섯 |
| `tests/test_quality_state.py`, `test_content_contracts.py`, `test_validate_review.py` | 새 테스트와 기존 단언 갱신 셋 |

전체 테스트 310 → **385**. 기존 테스트 이름 289개 전부 보존(CMD-6). 초기 dirty 경로 둘(`.prior-art/`, `docs/development/2026-09-05-70-quality-goal-codex-spec-readiness/`)은 한 바이트도 바뀌지 않았다.

## Remaining advisory findings

Spec·Plan 모두 라운드 1 의 finding 을 라운드 2 개정에서 전부 반영했다. **통과 라운드가 남긴 잔여 항목은 넷이며 모두 Medium 이하라 게이트를 막지 않는다.** 구현 승인 전에 이 넷을 먼저 볼지는 사용자 판단이다.

| finding | severity | 요지 | 상태 |
|---|---|---|---|
| `PLAN-06` | Medium | AC-44 의 통과 확인이 올바른 구현에서도 실패할 수 있다 — `grep -c` 는 매치가 아니라 **줄 수**를 세는데 두 문자열이 한 문장으로 이어져 있어 1 이 나오고, 같은 태스크의 구현 지시는 `사용자 보고로 이어진다` 로 쓰라고 해 grep 대상 문자열(`사용자에게 보고한다`)과 어긋난다 | **미해소.** Plan 이 통과해 digest 가 고정됐으므로 이번 실행에서 고치지 않았다. 구현 시작 전에 고치려면 Plan 을 다시 열어야 하고 그러면 승인 digest 계약이 깨진다 — 사용자가 선택할 사항이다 |
| `PLAN-07` | Low | `SKILL.md` 에 걸린 기존 계약 둘(전체 파일에 펜스 코드 블록 금지, `### Spec` 절 안의 등장 순서)이 Plan 의 전수 대조표에 빠졌다. 값이 바뀌는 것은 아니라 갱신 단계는 필요 없지만 T12 의 작성 제약으로 적었어야 한다 | **미해소.** 위와 같은 이유 |
| `SPEC-25` | Low | `resolved_finding_ids` 의 집합 동치 위반이 네 `outcome` 중 어디로 기록되는지 Spec 이 못박지 않았다 | **미해소.** Plan 의 T3 이 그 검사를 검증 함수에 두고 T6 이 `schema_invalid` 로 기록하도록 배정해 실무상 확정됐으나 Spec 문언은 그대로다 |
| `SPEC-26` | Low | 추적표 R2.5 행의 AC-61 이 그 요구사항의 독립 조건을 판정하지 않아 추적표 서두의 자기 규칙과 어긋난다 | **미해소** |

라운드 1 의 finding 은 다음과 같이 반영했다.

| finding | severity | 반영 |
|---|---|---|
| `SPEC-17` | Medium | R4.4 의 첨부를 저장소 근거 경로 둘로 고정해 `SKILL.md` § Review invocation contract 의 입력 한정과 양립시켰다. AC-40 확장 |
| `SPEC-18` | Medium | § Failure behavior 표에 거부 계약 네 행 추가 |
| `SPEC-19` | Medium | R8.3 의 세 번째 조건에 AC-89 신설 |
| `SPEC-20` | Medium | R9.2 에 두 절의 헤딩 수준·삽입 위치 명시, AC-73 확장 |
| `SPEC-21` | Low | AC-5 에 검사 대상 파일 범위·문단 경계·금지 토큰 다섯 명시 |
| `SPEC-22` | Low | § Architecture 의 이관 게이트 입력을 다섯 → 일곱으로 정정 |
| `SPEC-23` | Low | `assert_python_version.py` 에 `is_supported` 노출, AC-90 신설 |
| `SPEC-24` | Low | § Interfaces 실행 순서 그림에 R1.6·R1.9 두 단계 추가 |

### 후속 항목

- 이슈 **#76** — readiness 게이트 논리 전체(게이트 판정 함수, 유효 Critical/High 집합, 시도 한도 강제, `AWAITING_READINESS_DECISION` 과 전이 가드, `readiness-gate`·`resume-readiness`, `readiness_decisions`, 공식 리뷰 시작 조건의 코드 강제)와 그 전제인 "잔여 blocker 의 upheld/overruled 판정 계약". 이 Spec 의 R6.1 기록 필드가 그 입력이 된다.
- 이슈 **#70 2·3단계** — Plan 단계 확장과 eval·비용 측정.
- `.gitignore` 는 이미 `.claude/quality-state/` 를 무시하므로 추가 조치가 필요 없다.

## Final status

- Status: `completed`
- Machine-readable reason: 없음. `status_reason` 은 `null` 이다 — 차단이나 재설계로 끝난 것이 아니라 정상 종료다.

라운드 소모: Spec 2/3, Plan 2/2, Code 2/3. 모든 게이트를 통과했다 — Spec 92, Plan 95, Code 92, 각 라운드 blocker 0·Critical/High 0.

이 실행이 사용자 지시대로 하지 않은 것은 없다 — 커밋·머지·`chezmoi apply`·배포본 변경을 하지 않았고, 초기 dirty 경로 둘과 두 종결 실행의 산출물을 건드리지 않았으며, Codex 에 금지 플래그를 쓰지 않았고, 테스트는 전부 `/opt/homebrew/bin/python3` 로 돌렸고, #76 의 구현을 여기서 함께 하지 않았다.
