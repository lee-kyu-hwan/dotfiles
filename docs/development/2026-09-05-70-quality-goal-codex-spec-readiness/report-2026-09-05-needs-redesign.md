# Quality Goal Report

- Task ID: 20260905T073930Z-70-quality-goal-spec-단계에-codex-author-fr-7ec207bb
- Mode: standard
- Status: NEEDS_REDESIGN (Plan 공식 라운드 2 한도 소진, blocker 잔존)
- Created: 2026-09-05T07:39:30Z
- Updated: 2026-09-06
- Source goal: #70 quality-goal Spec 단계에 Codex author + fresh Codex 체크리스트 readiness 사전 심사 파이프라인 추가 (1단계)

## Classification

standard. 사용자가 명시했고 `routing-rules.md` 의 위험 스캔 결과와 같아 하향이 아니다.

- 요구사항이 대안·비목표·수용기준을 명시해야 하는 워크플로 계약 변경이다(#70 본문 '작업 항목' 12건, #72 섹션 3).
- `SKILL.md`·references·templates·schemas·scripts·tests 등 다중 파일과 계층이 함께 바뀐다(`dot_claude/skills/quality-goal/` 하위 16개 파일).
- `state.json` 상태 전이와 readiness 전용 필드라는 비자명한 인터페이스가 신설된다.
- strict 트리거 부재: 인증·권한·결제·PII·프로덕션 인프라·외부 API 호환성 없음. 지속 스키마 변경은 로컬 `.claude/quality-state/state.json` 에 한정되고 롤백은 `git revert` 로 즉시 가능하다.

## Review history

이 실행은 만들려는 파이프라인을 만드는 동안 스스로 사용했다. Codex 체크리스트 사전 심사 10회(Spec a1~a7, Plan b1~b3)와 Claude 공식 리뷰 5라운드(Spec 3, Plan 2)를 거쳤고, 사전 심사는 공식 라운드를 소모하지 않았다.

| 회차 | 대상 | 행수 | verdict | score | Critical/High | 체크리스트 | 게이트 판정 |
|---|---|---|---|---|---|---|---|
| readiness a1 | spec.md | 582 | REVISE | 82 | 2 | C1~C8 전부 통과 | RETRY |
| readiness a2 | spec.md | 641 | REVISE | 84 | 3 | C8 fail | RETRY |
| readiness a3 | spec.md | 647 | REVISE | 93 | 0 | C8 fail | ARBITRATION |
| **Claude 공식 r1** | spec.md | 659 | **REVISE** | **77** | **2** (SPEC-01·02) | — | 게이트 실패 |
| readiness a4 | spec.md | 695 | REVISE | 84 | 0 | C8 fail | RETRY |
| readiness a5 | spec.md | 697 | REVISE | 90 | 0 | C8 fail | ARBITRATION |
| **Claude 공식 r2** | spec.md | 699 | **REVISE** | **84** | **1** (SPEC-17) | — | 게이트 실패 |
| readiness a6 | spec.md | 715 | REVISE | 94 | 0 | C8 fail | RETRY |
| readiness a7 | spec.md | 715 | **READY** | **99** | **0** | **C1~C8 전부 통과** | **READY** |
| **Claude 공식 r3** | spec.md | 715 | **PASS** | **92** | **0** | — | **게이트 통과** |

Spec 은 공식 라운드 3 에서 통과했다(`SPEC_PASSED`). 이어 Plan 을 작성해 같은 구조로 심사했다.

| 회차 | 대상 | 행수 | verdict | score | Critical/High | 게이트 판정 |
|---|---|---|---|---|---|---|
| Plan 사전 심사 b1 | plan.md | 417 | REVISE | 63 | 4 | — |
| Plan 사전 심사 b2 | plan.md | 423 | REVISE | 70 | 3 (Critical 1) | — |
| Plan 사전 심사 b3 | plan.md | 427 | REVISE | 79 | 2 | — |
| **Claude 공식 Plan r1** | plan.md | 435 | **REVISE** | **86** | **1** (PLAN-02) | 게이트 실패 |
| **Claude 공식 Plan r2** | plan.md | 439 | **REVISE** | **89** | **1** (PLAN-06) | 게이트 실패 — 한도 소진 |

Spec 은 582행/요구사항 62/AC 68 에서 715행/요구사항 69/AC 113 으로 자랐다. 개정 근거는 `spec-revision-notes.md` 에 회차별로 남겼다.

### 두 심사가 서로 다른 것을 측정한다는 실증

이 실행이 이슈 #70 코멘트의 대응점 두 개(readiness 97↔Claude 74, 94↔78)에 세 번째와 네 번째 표본을 더했다.

| readiness (fresh Codex, 체크리스트) | 직후 Claude 공식 | 차이 |
|---|---|---|
| Spec a3 93점, Critical/High 0 | Spec r1 **77점**, blocker 2 | -16 |
| Spec a5 90점, Critical/High 0 | Spec r2 **84점**, blocker 1 | -6 |
| Plan b3 79점, Critical/High 0 | Plan r1 **86점**, blocker 1 | +7 |

Plan b3 은 부호가 반대다. 사전 심사가 공식 리뷰보다 낮게 준 첫 표본이며, 두 점수가 같은 축 위에 있지 않다는 것을 오히려 강화한다 — 낮게도 높게도 어긋난다. 예측력이 없다는 결론은 방향이 아니라 상관 부재에서 온다.

readiness 가 Critical/High 0 으로 통과시킨 산출물에서 공식 리뷰가 매번 High blocker 를 찾았다. 점수 게이트를 버리고 체크리스트 게이트로 간 이 Spec 의 D1 결정이 실측으로 다시 지지된다.

### 각 심사가 잡은 것과 놓친 것

readiness 가 반복적으로 정확히 잡은 것:

- 문서 내부 문언 불일치. 같은 사실을 두 곳에서 다르게 말하는 경우를 매 회차 두세 건씩 찾았다(READY-15·16·17·19·20·22).
- 저장소 근거 대조. `codex exec --help` 를 실제로 실행해 `--yolo` 가 숨은 별칭임을 확인했고(READY-11), `.gitignore` 사실 오류를 잡았으며(READY-04), 판정 명령을 실행해 Python 인터프리터 의존성을 드러냈다(READY-02).
- 직전 리뷰 findings 의 부분 해소 판정. "여섯 항목은 닫혔지만 전수 대조는 안 됐다"를 정확히 구별했다(READY-03·12·13·14·21).

readiness 가 구조적으로 놓친 것 — 전부 Claude 공식 리뷰가 잡았다:

- 권한 층위의 결함. "비권위 심사자가 종료 상태를 만든다"(SPEC-01)는 체크리스트 여덟 항목 어디에도 걸리지 않는다.
- 값의 산출 주체 부재. `formal_round` 를 누가 만드는지 정의되지 않아 한도가 무력화되는 경로(SPEC-02).
- 신설 개념의 거부 계약 부재. 새 stage 와 새 명령의 조건이 서술로만 있어 카운터를 임의 초기화할 수 있는 경로(SPEC-17).
- 기존 계약과의 조정 누락. dirty-worktree 보존 계약과 충돌하는 `git status` 대조(SPEC-03), 이름이 겹치는 기존 상태 필드(SPEC-07).

세 blocker 가 모두 "문서는 정합하지만 규칙이 실행될 때 깨지는" 유형이다. 이것이 이 Spec 의 § Architecture 가 규정한 역할 분리와 정확히 일치한다.

## Blocking-finding resolutions

| ID | 라운드 | severity | 해소 | 확인 |
|---|---|---|---|---|
| SPEC-01 | Spec r1 | High | 비종료 stage `AWAITING_READINESS_DECISION` 신설, R4.5 를 그리로 전이. 사용자 결정은 `resume-readiness` 서브커맨드로만. 자동 중재 경로 없음(#76 로 분리) | r2 evidence 에서 "라운드 1 required_resolution 의 선택지 (a) 를 충족한다" 로 확인 |
| SPEC-02 | Spec r1 | High | R6.7 을 "`formal_round` 는 `rounds[artifact]+1` 로 유도, `--formal-round` 불일치 시 거부" 로 재작성. AC-97·98 신설 | r2 evidence 에서 기존 `record_review` 와 같은 규칙임을 확인 |
| SPEC-17 | Spec r2 | High | R4.8 에 stage 가드, R4.9 신설로 `SPEC_REVIEW → AWAITING_READINESS_DECISION` 이 게이트 `HOLD` 를 요구. AC-106·107·108 신설 | Spec r3 PASS(92)로 확인 |
| PLAN-02 | Plan r1 | High | 113 AC 전수 대조 후 열일곱 태스크의 실패·통과 확인 전수 재생성, T17 에 AC-63·67 테스트 작성 단계 추가, AC-105 판정 대상을 유지보수 문서로 확정 | Plan r2 evidence 두 건이 `verified: true` 로 확인. 다만 확정 자체가 PLAN-06 을 낳음 |
| PLAN-06 | Plan r2 | High | **미해소** — 한도 소진으로 개정 기회 없음 | 종결 사유 |

SPEC-17 은 SPEC-01 해소가, PLAN-06 은 PLAN-02 해소가 만든 교차 회귀다. 이 실행에서 그 패턴이 아홉 번 나왔다 — 아래 § Plan 공식 리뷰 r2 와 종결 에 전수 표를 실었다.

## Plan approval

- Approval timestamp: 해당 없음
- Plan digest: 해당 없음

`AWAITING_PLAN_APPROVAL` 에 도달하지 않았다. Plan 이 공식 리뷰 한도 안에 통과하지 못해 승인 게이트 앞에서 종결했다. 구현 승인은 요청하지 않았고 구현도 시작하지 않았다.

## Changed files

스킬 소스는 한 줄도 바뀌지 않았다. Spec 단계 산출물만 추가됐다.

| 경로 | 성격 |
|---|---|
| `docs/development/2026-09-05-70-quality-goal-codex-spec-readiness/spec.md` | 신규. 715행, 요구사항 69, AC 113, 추적표 69행 |
| `docs/development/2026-09-05-70-quality-goal-codex-spec-readiness/spec-revision-notes.md` | 신규. 223행. 회차별 개정 근거와 조합 검토 |
| `docs/development/2026-09-05-70-quality-goal-codex-spec-readiness/plan.md` | 신규. 439행, 태스크 17, 추적표 113행. blocker 1건 잔존 |
| `docs/development/2026-09-05-70-quality-goal-codex-spec-readiness/report.md` | 신규. 이 문서 |
| `.prior-art/` | 실행 시작 시점의 초기 dirty 경로. 손대지 않았다 |

`dot_claude/skills/quality-goal/` 하위는 `git status --porcelain` 에 나타나지 않는다. `chezmoi apply` 도 실행하지 않았다 — 다른 세션이 배포본을 쓰고 있다는 제약대로다.

## Verification evidence

이 단계에서 실행한 명령과 결과다. Spec 단계이므로 구현 검증(lint·typecheck·build·E2E)은 아직 대상이 아니다.

| 명령 | 종료 코드 | 증거 |
|---|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/quality-goal/tests -p 'test_*.py'` (python3 3.14.7) | 0 | `Ran 240 tests` / `OK` — base revision `b30a0dee8465b9b8a3cf5243a47740b3c2116a24` 기준선 |
| 같은 명령 (`/usr/bin/python3` 3.9.6) | 1 | `Ran 240 tests` / `FAILED (errors=23)`, `AttributeError: 'ResumeSelectionTests' object has no attribute 'enterContext'` |
| 같은 명령 (`python3.12` 3.12.14) | 0 | `Ran 240 tests` / `OK` |
| `python3 -m unittest discover ... -k test_zzz_does_not_exist` (3.14.7) | 5 | `NO TESTS RAN` |
| 같은 명령 (`python3.12`) | 5 | `NO TESTS RAN` |
| 같은 명령 (`/usr/bin/python3` 3.9.6) | 0 | 매칭 0건인데 성공 반환 |
| `codex exec --yolo --version` | 0 | `codex-cli-exec 0.153.4` — `--help` 에 없는 숨은 별칭 |
| `codex exec --full-auto --version` | != 0 | 사용법 안내. 미지원 플래그와 같은 반응 |
| `codex exec --definitely-not-a-flag --version` | != 0 | 사용법 안내 |
| `git check-ignore -v .claude/quality-state/` | 0 | `.gitignore:25` — 런타임 상태는 이미 무시된다 |
| `codex exec -C . --sandbox read-only --ephemeral --model gpt-5.6-terra -c model_reasoning_effort="low"` | 0 | `Acknowledged.` — INTAKE 프리플라이트 |
| `validate_review.py validate --input spec-review-r1.json --artifact spec` | 0 | `{"valid":true,"errors":[]}` |
| `validate_review.py gate --input spec-review-r1.json --artifact spec --checks ...` | 3 | `score_below_85`, `verdict_not_pass`, `blockers_present`, `critical_or_high_finding`, `check_failed:acceptance_criteria_objective` |
| `validate_review.py validate --input spec-review-r2.json --artifact spec --prior ...` | 0 | `{"valid":true,"errors":[]}` |
| `validate_review.py gate --input spec-review-r2.json --artifact spec --checks ... --prior ...` | 3 | 위와 같은 다섯 사유 |
| Spec 자체 체크리스트 검사 (C1~C7 프로그램 검증) | 0 | 절 구조·순서 통과, strict marker 리터럴 0건, 요구사항 69 == 추적표 69행, 유령·미매핑 참조 0, AC 113 전부 판정 수단 배정, AC 번호 연속·고유·정의 순서 일치, 판정 명령 전부 표 등재 |
| 신설 식별자 거부 계약 전수 점검 (10개 식별자 × 3칸) | 0 | 빈 칸 없음. 점검 중 `--invocation-status`·`--stderr-path` 두 빈 칸을 발견해 R6.9·AC-112·113 으로 닫음 |
| `validate_review.py validate --input spec-review-r3.json --artifact spec --prior ...` | 0 | `{"valid":true,"errors":[]}` |
| `validate_review.py gate --input spec-review-r3.json --artifact spec --checks ... --prior ...` | 0 | `{"passed":true,...}` — Spec 통과 |
| Plan AC 전수 대조 (113 AC × 2칸) | 0 | 67 → 2 → 0 |
| `validate_review.py validate --input plan-review-r1.json --artifact plan` | 0 | `{"valid":true,"errors":[]}` |
| `validate_review.py gate --input plan-review-r1.json --artifact plan --checks ...` | 3 | `verdict_not_pass`, `blockers_present`, `critical_or_high_finding` |
| `validate_review.py validate --input plan-review-r2.json --artifact plan --prior ...` | 0 | `{"valid":true,"errors":[]}` |
| `validate_review.py gate --input plan-review-r2.json --artifact plan --checks ... --prior ...` | 3 | `verdict_not_pass`, `blockers_present`, `critical_or_high_finding` |
| Plan 결정적 체크 재실행 (절 순서·추적표·플레이스홀더) | 0 | 절 순서 일치, 추적표 113행 고유, Spec AC 113 과 차집합 0, 플레이스홀더 0(검출된 `...` 2건은 `raise StateError(...)` 와 경로 축약으로 실제 플레이스홀더 아님) |

`not configured` 항목: lint, type check, build, E2E. 이 저장소의 `dot_claude/skills/quality-goal/` 에는 그 구성이 없다(`tests/` 아래 `unittest` 스위트가 유일한 결정적 검증이며 `docs/quality-goal-maintenance.md` 의 '결정적 테스트' 절이 그 명령 하나만 싣는다). Spec 단계이므로 구현 대상 코드도 아직 없다.

## Remaining advisory findings

- **PLAN-06 (High, 미해소)** — AC-84 의 판정 대상이 추적표(`plan.md:399`, `spec.md` § Test strategy)와 T17 통과 확인(`plan.md:260`, `docs/quality-goal-maintenance.md`)에서 서로 다르다. 게다가 T16 구현 단계에 유지보수 문서로 "최소 Python 3.12" 와 두 근거(`enterContext`, `NO TESTS RAN` 종료 코드 5)를 옮기는 작업이 없어, 계획대로 실행하면 T17 의 grep 이 0건을 반환한다. 이것이 종결 사유다.
- PLAN-07 (Low) — T16 이 유지보수 문서 '결정적 테스트' 절을 판정 명령 표로 "바꾼다" 고만 적어 최종 헤딩 문자열이 확정되지 않았다. `test_version_guard_is_shared_not_inlined` 가 그 헤딩을 앵커로 쓰므로 문자열을 못 박아야 한다.
- PLAN-08 (Low) — `test_round_limits_and_required_checks_unchanged` 가 base revision 값을 리터럴로 고정할지 `git show` 로 읽을지 미정. `git show` 면 CMD-1 이 저장소 상태에 의존하게 된다.
- SPEC-24 (Low, Spec r3 통과 리뷰의 잔여) — § Decisions 의 D13·D14 가 D11·D12 보다 앞에 정의돼 번호와 정의 순서가 어긋난다.
- 이슈 #76: readiness 잔여 blocker 를 공식 리뷰가 upheld/overruled 로 판정하는 계약. 이 Spec 의 Non-goal 11 이자 D10 이 1단계에서 제외한 대안의 전제다. `review.schema.json` 의 닫힌 `$defs/finding` 구조와 세 값 `verdict` enum 을 함께 바꿔야 한다.
- 한도 2회의 적정값은 이 표본으로 정할 수 없다. D10 이 #76 에서 재검토한다고 기록했다.

## 파이프라인 자체에 대한 관찰 (#70 1단계 실증)

사용자가 요청한 "만들려는 파이프라인을 만들면서 스스로 써 본" 결과다.

**값을 한 것.** 사전 심사가 공식 라운드를 지켰다. a1·a2 에서 잡힌 High 5건, a4·a5 에서 잡힌 Medium 10건이 그대로 공식 리뷰로 갔다면 Spec 3라운드 한도를 훨씬 전에 소진했을 것이다. 특히 a2 는 a1 개정이 만든 회귀 2건을 즉시 잡았다. `#70` 코멘트의 "author 는 확실히 값을 했다" 가 심사 쪽에서도 성립한다.

**한계.** readiness 는 여섯 번 중 한 번도 READY 를 내지 못했다. C8(직전 리뷰 findings 의 부분 해소 판정)이 매번 fail 이었기 때문이다. 이 항목은 개정이 완벽할 때만 통과하므로 사실상 게이트를 항상 막는다. 설계대로라면 ARBITRATION 경로가 그 비용을 흡수하지만, 여섯 번 중 세 번이 ARBITRATION 이었다는 것은 C8 의 판정 기준(부분 해소는 미충족)이 실무에서 얼마나 엄격한지를 보여준다. #76 에서 재검토할 값이다.

**게이트 판정은 설계대로 작동했다.** a3·a5 는 심사 스스로 "Critical/High 0 이므로 추가 시도 없이 ARBITRATION 으로 진행하라"고 판정했고, RETRY·ARBITRATION 구분이 여섯 회 모두 규칙대로 나왔다.

**실무 함정 여섯 가지는 전부 계약으로 고정됐다.** `--output-schema` 의 `const` 금지(R2.4), stdin 무한 대기 차단(R2.3), `-a` 부재(R1.5), 라운드당 한도를 스키마 `maximum` 으로 옮기지 않기(R4.3), 심사 전 digest 대조(R5.1~5.4), 결과 스키마의 score·evidence 최소 요건(R8.2~8.3).

## Final status

- Status: **NEEDS_REDESIGN**
- Machine-readable reason: `REVIEW_LIMIT_EXHAUSTED:plan` (state.json 기록값)
- Spec 은 통과했다(공식 r3, score 92, `SPEC_PASSED`). 종결은 Plan 단계에서 났다.
- 승인 게이트에는 도달하지 않았다. 구현은 시작하지 않았고 스킬 소스는 한 줄도 바뀌지 않았다.

## Plan 단계 관찰 — 사전 심사가 잡은 것

Plan 은 공식 리뷰 2라운드 한도라 사전 심사의 값이 더 컸다. 세 회차가 잡은 것 중 공식 라운드를 아꼈다고 볼 수 있는 것들이다.

- **b1 (High 4)**: `python3` 가 셸에 따라 3.9.6 으로 풀린다는 것을 실행으로 확인했다(`zsh -lc` 에서 `/usr/bin/python3`). 선행 grep 경로 여덟 곳이 존재하지 않는 `scripts/…` 였다. T17 의 범위 검사가 T16 의 문서 변경과 직접 모순이었다.
- **b2 (Critical 1)**: **오케스트레이터가 프롬프트에 Spec digest 자리에 Plan digest 를 넣었다.** 정규식으로 기존 프롬프트를 고치다 "SHA-256 뒤에 `- 루브릭` 이 오는 자리" 가 Spec 행이라는 것을 놓쳤다. 이 Spec 의 R5.1~R5.4(심사 전 digest 대조)가 막으려는 바로 그 실수를 오케스트레이터가 저질렀고, 심사가 두 파일의 digest 를 직접 계산해 잡았다. 이후 프롬프트를 재활용하지 않고 새로 작성하며 두 digest 를 각각 확인해 넣었다.
- **b3 (High 2)**: AC 소유권을 표에서 고쳐도 각 태스크의 **통과 확인 목록**이 여전히 후속 태스크의 테스트를 담고 있었다. `.prior-art/` 보존을 경로 목록으로만 판정해 내용 변경을 못 잡았다.

## Plan 공식 리뷰 r1 과 전수 대조

공식 리뷰 r1 은 score 86, blocker 1(PLAN-02)이었다. PLAN-02 는 "추적표가 AC-105 를 T1 에 배정했지만 T1 본문에 그 테스트를 만드는 단계가 없고, 판정 대상인 '판정 명령 표' 가 goal 종료 후 사라질 수 있는 워크플로 문서 안에 있다" 는 지적이었다.

사용자 지시에 따라 그 하나만 고치지 않고 **113개 AC 전부를 스크립트로 전수 대조**했다. 각 AC 에 대해 두 칸을 확인했다 — (1) 배정 태스크 본문에 그 테스트를 만드는 단계가 있는가, (2) 실패 확인과 통과 확인 명령에 그 테스트가 등장하는가.

| 대조 시점 | 빈 칸 |
|---|---|
| PLAN-02 반영 직후 | **67** |
| 태스크별 실패·통과 확인을 소유 AC 로 전수 재생성한 뒤 | 2 |
| T17 에 AC-63·67 테스트 작성 단계를 넣은 뒤 | **0** |

67건은 전부 같은 원인이었다 — 태스크 본문이 "대상 AC 전부가 `[실행]` 이므로 각 테스트 이름을 CMD-2 로 돌린다" 는 축약을 써서 개별 테스트 이름이 어디에도 없었다. PLAN-02 는 그 축약이 가장 눈에 띄게 드러난 한 사례였다. 남은 2건은 T17 을 "구현 없는 검증 전용 태스크" 로 둔 탓에 AC-63·67 의 테스트를 만드는 태스크가 아예 없던 것이다.

AC-105 의 판정 대상은 `docs/quality-goal-maintenance.md` 의 판정 명령 표로 확정했다. 셋 중 스킬과 함께 유지되는 유일한 위치이며, 그 문서는 이미 실행 명령을 싣는 역할을 한다.

## Plan 공식 리뷰 r2 와 종결

r2 는 score 89, verdict REVISE, blocker 1(PLAN-06, High)이었다. Plan 은 2라운드 한도이므로 여기서 `NEEDS_REDESIGN` 으로 종결한다.

**r1 의 다섯 finding 은 전부 해소가 확인됐다.** r2 의 evidence 열한 건 중 여섯 건이 PLAN-01·03·04·05 와 PLAN-02 의 "테스트를 만드는 구현 단계" 요구를 각각 소스와 대조해 `verified: true` 로 확인했다. 전수 재생성의 산술도 확인됐다 — 추적표 113행과 열일곱 태스크의 소유 AC 합 113 이 1:1 이고, 각 태스크의 실패 확인 테스트 이름 집합과 통과 확인 집합이 일치한다.

**그런데 PLAN-02 를 닫은 개정이 새 blocker 를 만들었다.** AC-105 의 판정 대상을 `docs/quality-goal-maintenance.md` 로 못 박으면서, 같은 요구사항 R9.9 의 짝인 AC-84 가 갈라졌다. 추적표 `plan.md:399` 는 여전히 `spec.md` § Test strategy 를 가리키는데 T17 통과 확인 `plan.md:260` 은 유지보수 문서를 grep 한다. 그리고 T16 구현 단계 세 항목 어디에도 유지보수 문서에 "최소 Python 3.12" 와 두 근거를 싣는 작업이 없다. 현재 그 문서(29-35행)에 해당 문자열이 없으므로 계획대로 실행하면 T17 의 판정이 0건을 반환해 실패하고, 그것을 만드는 태스크는 존재하지 않는다.

리뷰가 남긴 흔적이 원인을 정확히 짚는다 — T17 의 `[문서]` 판정 문단에 T13 에서 옮겨온 보일러플레이트(`P=references/readiness-policy.md`)가 AC-84 하나뿐인 문단에 그대로 남아 있다. **기계적 전수 재생성이 만든 잔재다.** 전수 대조 스크립트는 "각 AC 의 테스트가 소유 태스크의 실패·통과 확인에 등장하는가" 만 봤고, "판정 대상 파일 경로가 추적표 행과 태스크 본문에서 같은가" 는 보지 않았다. 사용자가 지시한 두 칸 대조는 완결했지만, 그 두 칸이 이 결함을 덮지 못했다.

### 이 실행에서 교차 회귀가 아홉 번 나왔다

| # | 회차 | 어떤 해소가 | 무엇을 깼나 |
|---|---|---|---|
| 1~5 | readiness a2·a4·a6, Plan b2·b3 | 개별 문언 수정 | 같은 사실을 말하는 다른 곳 |
| 6 | Spec r2 (SPEC-17) | SPEC-01 의 신설 상태 | SPEC-02 가 닫은 카운터 초기화 구멍 |
| 7 | Plan b2 (Critical) | 프롬프트 정규식 재활용 | Spec digest 자리에 Plan digest |
| 8 | Plan r1 (PLAN-02) | — | 축약 표기가 67 AC 에 걸친 것 |
| 9 | **Plan r2 (PLAN-06)** | **PLAN-02 의 판정 대상 확정** | **같은 요구사항의 짝 AC 와의 정합** |

라운드마다 조합 검토를 붙이라는 제약을 지켰고 매 회차 실제로 붙였는데도 아홉 번 나왔다. **개별 해소가 인접 계약을 깨는지 보려면 "고친 대상" 이 아니라 "고친 대상과 같은 요구사항·같은 표·같은 절을 공유하는 것" 을 기준으로 훑어야 한다.** #9 는 R9.9 라는 요구사항 하나에 묶인 AC-84·AC-105 중 하나만 옮긴 것이고, 요구사항 단위로 훑었다면 걸렸다.

### 재설계 시 착수점

Plan 은 439행에서 blocker 하나만 남은 상태다. 재설계라기보다 R9.9 의 두 AC 를 한 문서로 모으는 국소 수정에 가깝다. 다음 실행에서 먼저 할 것:

1. AC-84·AC-105 의 판정 대상을 `docs/quality-goal-maintenance.md` 하나로 통일하고, 추적표 `plan.md:399` 행과 T17 본문을 같게 맞춘다.
2. T16 구현에 "판정 명령 표 옆에 최소 Python 3.12 와 두 근거(`enterContext`, `NO TESTS RAN` 종료 코드 5)를 싣는다" 를 넣고, AC-84 판정 명령이 그 두 근거까지 확인하게 바꾼다.
3. PLAN-07 을 함께 닫는다 — 유지보수 문서의 최종 헤딩 문자열을 못 박는다.
4. PLAN-08 을 함께 닫는다 — base revision 값을 리터럴로 고정할지 정한다.
5. **전수 대조 스크립트에 세 번째 칸을 더한다** — "AC 의 판정 대상 파일 경로가 추적표 행과 소유 태스크 본문에서 같은가". 이번 blocker 를 기계적으로 잡았을 칸이다.
6. 같은 요구사항 번호를 공유하는 AC 쌍을 열거해 판정 대상이 일치하는지 훑는다. R9.9 외에 몇 쌍이 더 있는지는 확인되지 않았다.

Spec(715행, PASS 92)은 그대로 재사용 가능하다. 재설계는 Plan 만 대상이다.

