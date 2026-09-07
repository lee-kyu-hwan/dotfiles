# Quality Goal Report

- Task ID: 20260906T100138Z-70-quality-goal-spec-단계에-codex-author-fr-7ec207bb
- Mode: standard
- Status: NEEDS_REDESIGN (`REVIEW_LIMIT_EXHAUSTED:spec`)
- Created: 2026-09-06T10:01:38Z
- Updated: 2026-09-06
- Source goal: #70 quality-goal Spec 단계에 Codex author + fresh Codex 체크리스트 readiness 사전 심사 파이프라인 추가 (1단계)

**이 실행은 Spec 라운드 한도 3 을 소진해 종결했다.** 라운드 3 이 `82 / REVISE / blocker SPEC-11` 로 끝났고 `record-review` 가 `NEEDS_REDESIGN`(`REVIEW_LIMIT_EXHAUSTED:spec`)으로 전이시켰다. 보고서는 종결 전에 등록됐다(#43 수정이 세 번째로 실전 작동).

**Spec 은 통과하지 못했지만 재사용 가능하다.** 743행, 요구사항 71, AC 120 이며 라운드 1·2 의 finding 열 건이 전부 해소 확인됐다. 남은 것은 라운드 3 이 새로 낸 다섯(`SPEC-11` High, `SPEC-12`~`SPEC-14` Medium, `SPEC-15` Low)이고 `SPEC-11` 의 해소 방향은 리뷰어가 두 갈래로 명시했다. Plan 도 개정본이 준비돼 있다.

## 선행 실행과의 관계

직전 실행(`20260905T073930Z-…`)은 Spec 라운드 3 에서 `92 / PASS / blocker 0` 을 받은 뒤 Plan 라운드 2 에서 `PLAN-06` 하나로 한도를 소진해 `NEEDS_REDESIGN`(`REVIEW_LIMIT_EXHAUSTED:plan`)으로 종결했다. 그 보고서는 `report-2026-09-05-needs-redesign.md` 로 보존했다. 이번 실행은 같은 goal 문자열·같은 산출물 디렉터리로 새 task 를 열어 그 Spec·Plan 을 재사용한다. `select-resume` 은 직전 task 가 터미널이라 매치를 반환하지 않았다.

**재개 전 rebase.** 워크트리를 `main` 으로 fast-forward rebase 했다(충돌 0). base revision 이 `b30a0dee8465b9b8a3cf5243a47740b3c2116a24` → `6d60011cbdaead7946b191d3f12029eef5c141c8` 로 바뀌었고, 그 사이 #61(PR #83)이 quality-goal 을 v4.1.0 → **v5.0.0** 으로 올렸다. untracked `docs/development/…/` 와 `.prior-art/` 는 그대로 보존됐다.

## Classification

`standard`. 사용자가 명시한 모드이며 위험 스캔 결과와 같아 강등 확인이 필요 없었다.

- 요구사항이 대안·비목표·수용기준을 명시해야 하는 워크플로 계약 변경이다 (#70 본문 '작업 항목' 12건, '완료 조건' 10건)
- `SKILL.md`·references·templates·schemas·scripts·tests 등 다중 파일과 계층이 함께 바뀐다 (`dot_claude/skills/quality-goal/` 하위 16개 파일)
- `state.json` 상태 전이와 readiness 전용 필드라는 비자명한 인터페이스가 신설된다 (#70 본문 '상태 스키마와 재개 호환성')
- 이슈 라벨은 `enhancement`·`quality-goal`·`P3-low` 로 strict 를 요구하지 않는다. 라벨은 보조 근거일 뿐이며 아래 strict 스캔 결과가 판정을 확정한다
- strict 트리거 부재: 인증·권한·결제·PII·프로덕션 인프라·외부 API 호환성 없음. 지속 스키마 변경은 로컬 `.claude/quality-state/state.json` 에 한정되고 롤백은 `git revert` 로 즉시 가능하다

## Review history

### Spec — 공식 리뷰(Claude Opus quality-reviewer)

| 라운드 | score | verdict | blockers | 산출물 |
|---|---|---|---|---|
| 1 | 82 | REVISE | `SPEC-01`, `SPEC-02`, `SPEC-03` | 719행 / 요구사항 69 / AC 113 |
| 2 | 87 | REVISE | `SPEC-07`(신규) | 737행 / 요구사항 70 / AC 117 |
| 3 | 82 | REVISE | `SPEC-11`(신규) | 743행 / 요구사항 71 / AC 120 |

라운드 2 는 `SPEC-01`~`SPEC-06` 여섯을 **전부 해소 확인**했고 점수가 82 → 87 로 올랐다. 재발한 blocker 는 없다(`recurring` 판정 없음). 새 blocker `SPEC-07` 은 `new_blocker_evidence` 를 갖췄다 — 그것이 지적하는 규칙 자체가 라운드 2 개정으로 들어온 것이라 라운드 1 에서는 판정 대상이 아니었다.

라운드 1 의 결정적 게이트: `required_sections` true, `material_decisions_resolved` true, `acceptance_criteria_objective` true. 게이트 실패 사유는 `score_below_85`·`verdict_not_pass`·`blockers_present`·`critical_or_high_finding` 넷이며 전부 리뷰 판정에서 온 것이고 결정적 점검에서 온 것은 없다.

### Spec — Codex readiness 사전 심사(fresh `codex exec`, read-only, `gpt-5.6-sol` high)

| attempt | formal_round | verdict | score | 체크리스트 | findings |
|---|---|---|---|---|---|
| 1 | 1 | REVISE | 92 | C1~C7 pass, **C8 fail** | `READY-01`(Low) |
| 2 | 1 | READY | 92 | C1~C8 전부 pass | 없음 |
| 3 | 2 | REVISE | 79 | C1~C7 pass, C8 fail | `READY-02`(High) 외 다섯 |
| 4 | 2 | REVISE | 85 | **C1~C8 전부 pass** | `READY-08`(High), `READY-09` |
| 5 | 2 | REVISE | 88 | C1~C7 pass, C8 fail | `READY-08` **재발**, `READY-09` |
| 6 | 2 | 회수 | — | — | 시스템 메모리 부족으로 호스트가 종료. Codex 실패 아님 |
| 7 | 3 | **`invocation_failed`** | — | — | `codex exec` 응답 정지, 39 이벤트 뒤 감시자 회수(600s) |
| 8 | 3 | **`invocation_failed`** | — | — | 같은 모드, 7 이벤트 뒤 회수(480s). 프롬프트 8.2KB → 2.6KB 축소도 무효 |
| 9 | 3 | **`invocation_failed`** | — | — | 같은 모드, 2 이벤트. 사용자 지시로 exec 경로 중단 |
| 10 | 3 | REVISE | 78 | C1~C7 pass, C8 fail | **6.2.2 대화형 세션으로 우회.** `READY-10`·`READY-11`(High 둘), `READY-12`, `READY-13` |

합계: 유효 심사 7회(attempt 1~5, 10), `invocation_failed` 3회(attempt 7~9), 호스트 종료 1회(attempt 6). **readiness 가 잡은 High 는 넷(`READY-02`·`READY-08`·`READY-10`·`READY-11`)이고 그중 셋은 공식 리뷰 라운드를 소모하기 전에 닫혔다.** 나머지 하나(`READY-08`)는 두 번 재발한 뒤 닫혔다.

**attempt 1 이 점수가 아니라 체크리스트로 막은 첫 사례다.** score 92, blocker 0 이었지만 C8(직전 리뷰 findings 의 `required_resolution` 확인)이 `fail` 이라 READY 가 아니었다. 직전 실행 공식 리뷰 r3 의 비차단 finding `SPEC-24`(결정 절 D11·D12 가 D13·D14 뒤에 정의됨)가 미해소로 남아 있던 것을 잡았다. 이슈 #70 코멘트 2 가 제안한 "점수 게이트를 체크리스트 게이트로" 가 실제로 값을 한 관측이다.

**attempt 2 가 READY 를 냈는데 공식 리뷰가 blocker 셋을 냈다.** 두 심사가 다른 층을 본다는 이슈 #70 코멘트 2 의 결론이 이 실행에서도 재현됐다. readiness 가 놓친 셋은 각각 요구사항↔프롬프트 계약의 결손(`SPEC-01`), 짝 AC 의 판정 대상 미정(`SPEC-02`), 상태 전개를 따라가야 보이는 fail-open(`SPEC-03`)이다. attempt 3 은 그 층에 가까운 심사(요구사항↔AC 전수 대조)로 초점을 바꿔 돌렸다.

### `codex exec` 의 새 실패 모드 — 3연속 `invocation_failed`

라운드 3 사전 심사에서 `codex exec` 가 세 번 연속 응답을 멈췄다. 세 번 모두 **분석에 들어가기 전 단계**(digest 확인·파일 읽기 직후)에서 정지했고, stderr 는 비어 있었으며, 잔존 프로세스가 없고 `spec.md` digest 는 불변이었다. 프롬프트를 8.2KB → 2.6KB 로 줄여도 같았고 attempt 5 는 5.8KB 로 성공했으므로 프롬프트 크기가 원인이라 보기 어렵다.

**이슈 #70 코멘트 1 이 기록한 함정 2(비대화형 stdin 무한 대기)와는 다른 모드다.** 그 함정은 stdin 이 열린 채 대화형 입력을 기다리는 것이고, 여기서는 stdin 이 프롬프트 파일에 고정돼 있었으며 초기 이벤트가 정상적으로 흘렀다. 감시자(벽시계 상한 + events 정지 감지)가 세 번 다 정상 작동해 회수했다 — 그 장치가 없었다면 #61 에서 관측된 80분 무응답이 재현됐을 것이다.

**우회.** 사용자 결정으로 exec 경로를 중단하고 6.2.2 의 대화형 Codex 세션(`gpt-5.6-sol max`, 같은 워크트리)에 같은 체크리스트 프롬프트를 읽기 전용으로 넘겼다. 대화형 경로는 정상 동작했고 **High 둘을 잡았다** — `READY-10` 은 `SPEC-07` 해소가 등록 digest 기록이 **있을 때**의 `READY` 경로를 덮지 않았다는 것이고, `READY-11` 은 AC-51 과 AC-120 이 동시에 통과할 수 없으며 `resolved_finding_ids` 가 상태로 복사되지 않아 게이트가 읽을 수 없다는 것이다. **exec 경로가 세 번 실패한 뒤의 대체 심사가 마지막 공식 라운드를 지켰다.** 그 둘을 반영하지 않고 라운드 3 에 들어갔다면 한도 소진으로 종결했을 가능성이 높다.

**#76 에 남길 근거.** 이 실행의 readiness 는 배포본 v5.0.0 이 강제하는 게이트가 아니라 자기 적용 실험이며 상태 머신은 `record-review` 에 readiness 결과를 요구하지 않는다. 따라서 R4 의 `HOLD`/`ARBITRATION` 경로가 이 실행을 묶지 않았다. 다만 **설계대로였다면 어느 경로로 갔는지**는 기록해 둔다 — `formal_round` 3 의 시도 구간에 `outcome` 이 `recorded` 인 기록이 하나도 없으므로 R6.10 표의 **갈래 ①(무기록)** 이고 시도가 2 이상이므로 반환값은 **`ARBITRATION`** 이다. 곧 "readiness 가 유효한 결과를 내지 못했다"는 사실을 공식 리뷰 근거에 명시한 채 라운드 3 으로 진행했을 것이며 실제 진행과 같다.

그래서 갈래 ①은 이 표본에서 **fail-open 이 아니라 합리적 탈출구**로 작동했다. 다만 그 경로는 "심사가 통과시켰다" 와 "심사가 돌지 못했다" 를 반환값만으로 구별하지 못하므로, R4.4 가 요구하는 "그 사실을 공식 리뷰 근거에 명시" 가 이 경로의 유일한 안전장치다. 그 명시를 코드로 강제할지는 #76 에서 다룰 항목이다.

### 결정적 개정 점검(`revision_check.py`, v5.0.0)

| 라운드 | 빈 칸 | 개정 노트 | passed |
|---|---|---|---|
| 1 | 0 | 라운드 1 면제 | true |
| 2 | 0 | `## 라운드 2 개정` 절 + 다섯 열 표 10행 | **true** |
| 3 | 0 | `## 라운드 3 개정` 절 + 다섯 열 표 7행 | **true** |

**이 실행이 v5.0.0 개정 점검 절차의 첫 실전 사용자다.** 라운드 2 에서 그 절차가 실제로 두 결손을 잡았다.

1. `중복 정의 R1.9 2회` — 신설 요구사항 번호를 `R1.9` 로 골랐는데 그 번호가 이미 `draft_attempts` 규정으로 존재했다. 지적대로 `R1.12`(R1 계열 마지막 `R1.11` 다음)로 옮겼다.
2. `R 수=추적 행 수 69 / 70` — 위 중복 때문에 요구사항 정의 수와 추적표 행 수가 어긋났다. 번호를 옮기면서 함께 닫혔다.

파급표는 스크립트가 diff 에서 생성한 것만 썼고 저자 기억으로 채우지 않았다. 라운드 2 의 파급표는 개정이 진행되면서 요구사항 8개 → 9개 → **10개**로 늘었다(`R1.6`·`R1.12`·`R4.4`·`R4.5`·`R6.5`·`R6.6`·`R6.10`·`R9.4`·`R9.9`·`R9.10`). **늘어난 둘이 이 절차의 값을 보여 준다** — `R6.6` 은 `READY-02` 해소 뒤에, `R4.5` 는 `READY-08` 해소 뒤에 스크립트가 새로 올렸고, 둘 다 저자 기억으로 표를 채웠다면 빠졌을 행이다. `R6.6` 은 갈래 ②와 정면 충돌했고 `R4.5` 는 `HOLD` 조건 한정이 빠져 있었다. 개정 노트 셋째 열이 매핑된 AC 를 전부 단어 경계로 싣고 각각에 `(일치)` 판정을 붙였다.

### Plan

이번 실행에서는 아직 공식 리뷰를 돌리지 않았다. 직전 실행의 결과는 라운드 1 `86 / REVISE / PLAN-01~05`, 라운드 2 `89 / REVISE / PLAN-06`(한도 소진). 이번 실행에서 `PLAN-06`·`PLAN-07`·`PLAN-08` 을 모두 닫고 v5.0.0 정렬을 적용한 개정본이 준비돼 있다.

## Blocking-finding resolutions

### `SPEC-01` (High, Requirement clarity) — 해소

**지적.** R1.1 이 Spec 의 모든 개정 주체를 Codex author 로 옮겼는데, author 프롬프트 필수 요소(R1.6, 판정 AC-6)에 base revision 이 이미 강제하는 개정 점검 계약의 입력이 하나도 없다. 그러면 라운드 2 이상에서 `revision_check.py` 가 종료 코드 0 을 내지 못해 `record-review --revision-check` 가 거부되고, 그 복구를 오케스트레이터가 본문으로 하려 들면 R1.1 이 금지한 작성 주체 이전이 된다.

**해소.** R1.6 의 필수 요소를 아홉 → **열둘**로 늘렸다(`references/revision-check-policy.md` 절대 경로, 식별자 문법 준수 지시, 라운드 2 이상 노트 형식). 노트 형식의 상세는 **R1.12 를 신설**해 그쪽에 뒀다 — 절 헤딩 `## 라운드 <n> 개정`, 다섯 열 표 머리, 한 `formal_round` 에 절 하나, readiness 개정 반복 시 새 절을 만들지 않고 행을 누적·갱신, 절이 다루는 범위는 직전 라운드 스냅숏 이후 전부. AC-6 을 열두 항목으로 늘리고 **AC-114 를 신설**해 추적표 `R1.12` 행에 실었다.

**검증.** 파급표가 `R1.6 → AC-6`, `R1.12 → AC-114` 를 생성했고 둘 다 새 문언과 대조해 일치를 확인했다. 이 실행 자신이 그 절차의 사용자이므로 `## 라운드 2 개정` 절이 R1.12 가 규정한 형식을 그대로 따르는지가 곧 자기 검증이다 — `revision_check.py` 가 `section_found true`, `missing_rows []`, `blank_cells []` 로 통과했다.

### `SPEC-02` (High, Acceptance criteria and testability) — 해소

**지적.** AC-84 의 판정 대상을 `docs/quality-goal-maintenance.md` 로 옮긴 결과, 같은 요구사항 R9.9 의 짝인 AC-105 의 판정 대상이 미정이 됐다. AC-105 는 파일 한정 없이 "판정 명령 표" 를 말하는데 § Test strategy 의 설명 문단은 "이 Spec 의 판정 명령 표" 를 AC-105 가 판정한다고 못박아, 두 읽기가 서로 다른 파일을 가리킨다.

**이것이 직전 실행의 종결 사유 `PLAN-06` 이 Spec 층에서 그대로 재현된 것이다.** 라운드 1 에서 `PLAN-06` 의 근원을 고치면서 짝 AC 를 또 한쪽만 옮겼다. 같은 실수를 같은 요구사항에서 두 번 했다.

**해소.** 셋을 한 개정에서 함께 고쳤다.

1. AC-105 문언에 판정 대상 파일 `docs/quality-goal-maintenance.md` 를 명시했다.
2. § Test strategy 의 설명 문단을 **정본·사본 규정**으로 다시 썼다 — 정본은 유지보수 문서의 `## 판정 명령 표` 절이고, 이 Spec 의 표는 그것을 옮겨 적은 사본이며 사본을 판정하는 AC 는 두지 않는다. `docs/development/…/spec.md` 는 goal 이 끝나면 옮겨지거나 지워질 수 있어 영구 테스트가 읽으면 CMD-1 이 영구히 깨지기 때문이다.
3. R9.9 의 세 AC 가 각각 무엇을 판정하는지를 그 문단에 열거했다 — AC-84 는 정본의 최소 버전 문언과 두 근거, AC-105 는 정본의 CMD-1·CMD-2 정의, AC-85 는 문서가 아니라 `tests/assert_python_version.py` 의 동작(CMD-7).

**검증.** 파급표가 `R9.9 → AC-84, AC-85, AC-105` 셋을 모두 생성했고 셋 다 새 문언과 대조했다. 라운드 1 에서 이 대조를 파급표 없이 했기 때문에 한쪽을 놓쳤다.

**AC-84 소유 태스크에 대한 판단과 그 충돌.** 사용자 지시는 판정 대상 "파일" 통일이었고 태스크 소유권 반전은 아니었다. 그런데 Plan 의 소유권 원칙("통과 확인을 실제로 실행할 수 있는 **가장 이른** 태스크가 소유한다")을 적용하면 그 문언을 만드는 T16 이 AC-84 를 소유하게 되어, 지시 문언의 "T17 의 판정 명령" 과 어긋난다. **둘은 양립 불가하며 Plan 원칙을 택했다.** 소유자를 T17 에 두면 T16 종료 시점에 이미 판정 가능한 AC 를 뒤 태스크가 들고 있게 되어 원칙이 깨지고, 전수 대조 스크립트가 그것을 `[A 생성]` 결손으로 잡는다. 지시의 실질(판정 명령이 두 근거까지 확인한다)은 T16 통과 확인의 세 절 `&&` grep 으로 지켰고, T17 에는 같은 명령을 회귀 재확인으로 남겼다. 이 충돌과 근거는 `spec-revision-notes.md` 의 `## 라운드 2 개정` R9.9 행 `상호작용 판정` 셀에도 적었다.

### `SPEC-03` (High, Feasibility, failure handling, and risk) — 해소

**지적.** 시도 구간이 소진된 뒤 산출물을 한 번 개정하는 것만으로 fail-closed 인 `HOLD` 경로가 영구히 죽고 fail-open 이 열린다. R6.10 은 "등록 digest 를 가리키는 `recorded` 기록이 없으면 Critical/High 를 0 으로 본다" 고 했는데, 시도 2회째가 High 를 남긴 채 끝난 상태에서 author 가 Spec 을 한 번 더 고치면 그 High 기록이 등록 digest 를 가리키지 않게 되어 게이트가 `HOLD` → `ARBITRATION` 으로 뒤집힌다. 시도 한도가 이미 2 라 새 readiness 로 확인할 수도 없고, R4.9 가 `HOLD` 아닌 전이를 거부하므로 `AWAITING_READINESS_DECISION` 엣지가 그 시도 구간에서 영영 도달 불가가 된다.

**이 부류가 Codex readiness 가 구조적으로 못 보는 것이다** — 여러 상태 전개를 따라가야 보이고, 문서 정합성 검사로는 잡히지 않는다. 이슈 #70 코멘트 2 가 "readiness 는 문서가 정합한가를, Claude 는 이 규칙들이 여러 실행에 걸쳐 돌 때 무엇이 깨지는가를 본다" 고 적은 그대로다.

**해소.** R6.10 에 둘째 갈래를 명문화했다. 등록 digest 를 가리키는 `recorded` 기록이 없을 때, 그 `formal_round` 에 귀속된 `recorded` 기록이 **하나도 없으면** Critical/High 를 0 으로 보고, **하나라도 있으면 그중 가장 최근 것의 Critical/High 유무를 그대로 쓴다**. 곧 등록 digest 를 가리키지 않게 된 옛 기록의 Critical/High 는 사라지지 않으며, `ARBITRATION` 은 Critical/High 가 0 임을 확인한 기록이 있을 때에만 나온다. 함께 고친 것:

- **AC-83** 에 배타 조건("그 `formal_round` 에 귀속된 `recorded` 기록이 하나도 없을 때")을 넣어 새 갈래와 겹치지 않게 했다. 두 AC 의 조건이 배타적이어야 게이트가 결정적이다.
- **AC-116 신설** — 둘째 갈래를 그대로 판정한다(시도 2 미만 `RETRY`, 2 이상 `HOLD`). 추적표 `R6.10` 행에 실었다.
- **R4.4** 의 전제를 "Critical/High 가 0 임을 실제로 확인한 `recorded` 기록이 있을 때에만" 으로 고치고 "'판정 근거 없음' 은 'Critical/High 0' 이 아니다" 를 명시했다. **AC-31** 을 같은 문언으로 맞췄다.
- **§ Failure behavior** 에 문단 하나와 표 행 하나를 더해 "유효한 결과가 없었던 경우" 와 "있었으나 개정으로 무효화된 경우" 를 구별했다.

**검증.** 파급표가 `R6.10 → AC-82, AC-83, AC-91, AC-116` 과 `R4.4 → AC-31, AC-87` 을 생성했고 여섯 개를 각각 새 문언과 대조했다. AC-83·AC-116 의 배타성은 Codex attempt 3 점검의 명시 항목으로 넣었다.

### `SPEC-07` (High, Feasibility, failure handling, and risk) — 라운드 3 에서 해소 중

**지적.** 라운드 2 가 `SPEC-03`·`READY-08` 을 닫으려고 신설한 "판정에 쓰이는 기록은 언제나 가장 최근 `recorded` 하나" 대체 규칙에, **그 최신 기록이 앞서 확인된 Critical/High 를 실제로 재판정했다는 보장이 없다.** 두 경로로 fail-open 이 열린다.

- **(a) 재판정 없는 대체** — readiness reviewer 는 fresh context 라 문맥을 상속하지 않는다(R2.1). C8 의 "직전 리뷰" 범위가 정의돼 있지 않고, readiness 프롬프트에 직전 readiness 시도의 findings 를 싣도록 요구하는 문장이 Spec 어디에도 없다. 따라서 시도 1 이 High 를 내고 author 가 그것을 고치지 않은 채 다른 곳만 개정해도, 시도 2 의 reviewer 가 그 High 를 재도출하지 못하면 clean 기록이 되어 게이트가 통과시킨다.
- **(b) 한도 뒤 추가 기록** — `record-readiness` 의 거부 계약에 시도 구간 한도 초과 거부가 없다. 게이트가 갈래 ②로 `HOLD` 를 낸 뒤에도 `SPEC_REVIEW` 에 머문 채 3번째 기록을 남길 수 있고, 그 하나가 clean 이면 `HOLD` 가 소멸해 R4.5 의 사용자 결정 게이트를 우회한다.

**이것이 이 실행에서 관측된 세 번째 교차 회귀이며, 가장 깊다.** `SPEC-03` 해소가 만든 규칙이 `READY-08` 을 부르고, `READY-08` 해소가 다시 `SPEC-07` 을 불렀다. 같은 구멍이 세 번 모양을 바꿔 나타났다 — 매번 "직전 지적이 가리킨 곳" 만 고친 것이 원인이다.

**라운드 3 해소 방향(사용자 결정).** 두 갈래를 모두 닫는다.

1. C8 의 "직전 리뷰" 를 **"같은 `formal_round` 의 직전 readiness 시도 findings 전문 + 직전 Claude 공식 리뷰의 open findings"** 로 명시하고, R2 계열에 "readiness 프롬프트는 그 findings 전문을 검증 대상으로 싣는다" 를 신설한다. R2.1 의 author 문맥 상속 금지와는 구분된다 — 금지 대상은 author 의 대화 문맥이고, 리뷰어 산출물(파일)의 전달은 허용이다.
2. R6.10 의 대체 규칙을 **"가장 최근 `recorded` 기록이 앞선 Critical/High 각각을 명시적으로 `resolved` 로 표기하지 않으면 그 Critical/High 는 잔존으로 본다"** 로 좁힌다.

`(2)` 가 `(b)` 경로도 함께 닫는다 — 한도 뒤에 3번째 기록을 남기더라도 앞선 High 를 명시적으로 닫지 않으면 잔존으로 보므로 `HOLD` 가 소멸하지 않는다.

### `SPEC-08` (Medium) — 라운드 3 에서 해소 중

R6.10 세 갈래 표에 "등록 digest 를 가리키는 `recorded` 기록이 없을 때" 라는 적용 범위 한정이 표 **안**에 없어, 유효 기록이 있고 체크리스트 전부 pass 인 `READY` 상태까지 갈래 ③에 문면상 포섭된다. "이 표 밖의 값을 반환하지 않는다" 도 `READY` 가 표에 없어 문면상 거짓이다.

### `SPEC-09` (Low) — 라운드 3 에서 해소 중

§ Failure behavior 세 행이 `High` 로만 적혀 Critical 만 있는 기록이 어느 행에도 맞지 않는다. 다른 곳은 모두 `Critical/High` 다.

### `SPEC-10` (Low) — 라운드 3 에서 해소 중

AC-86 의 판정 수단 표기(CMD-4·CMD-6·CMD-7)가 그 AC 의 조건(파일명 규칙, 공유 가드)을 판정하지 못한다. 공유 가드는 실제로 AC-105 가 판정한다.

### `SPEC-07` (High) — 해소 확인됨

라운드 3 리뷰가 두 갈래를 모두 확인했다. (a) R2.10 신설로 readiness 프롬프트가 직전 시도 findings 와 직전 공식 리뷰 open findings 를 싣게 됐고 R2.1 과의 구분이 본문에 있다(AC-118). (b) R6.6·R6.10 이 대체 규칙을 `resolved_finding_ids` 명시로 좁혔고 AC-119 가 `READY`·`ARBITRATION` 양쪽 금지를 두 경로에서 판정한다. 리뷰어가 `formal_round` 를 올려 우회하는 경로도 저장소에서 확인해 닫혀 있음을 근거로 남겼다 — `record-review-error` 는 `rounds` 를 건드리지 않고, `rounds` 를 올리는 유일한 경로 `record_review` 는 R2.8 의 게이트 요구를 받는다.

### `SPEC-11` (High, blocker) — 미해소. 이 실행의 종결 사유

**지적.** `SPEC-07` 해소가 만든 규칙이 **같은 `formal_round` 의 세 번째 시도부터 게이트를 영구히 닫는다.** 닫힘 표기는 판정 기록 하나에만 귀속되는데(R6.10 유효 집합 ②), 프롬프트는 직전 시도 하나의 findings 만 싣는다(R2.10·C8). 그래서 닫힘이 기록 간에 누적되지 않는다.

구체적으로 — attempt1 이 `READY-01`(High)을 내고 attempt2 가 그것을 받아 `resolved_finding_ids:[READY-01]` 로 닫아도, attempt3 의 프롬프트에는 attempt2 의 findings(빈 배열)만 실린다. attempt3 은 `READY-01` 을 알 수도 닫을 수도 없고, 판정 기록이 된 attempt3 기준으로 `READY-01` 이 다시 유효 집합에 들어간다. `READY` 도 `ARBITRATION` 도 나오지 않아 `RETRY` → `HOLD` 만 반복되며, R2.8 이 `record-review` 를 막아 `formal_round` 도 올라가지 못한다. `resume-readiness` 로 되돌아와도 같은 벽에 닿는다. 사용자가 `NEEDS_REDESIGN`/`BLOCKED`/`CANCELLED` 로 끝내는 것 말고는 탈출 경로가 없다.

**리뷰어가 이 Spec 자신의 문장을 반례로 들었다.** D10 은 "readiness 를 세 번 돌렸고 High 는 2 → 3 → 0 으로 움직였다" 를 대안 C 를 버린 근거로 싣는다. 새 규칙 아래에서는 그 실행의 attempt3 이 attempt1 의 High 를 볼 수 없어 닫지 못하고, **D10 이 대안 C 의 반례로 든 바로 그 실행이 대안 D 아래에서도 진행 불가가 된다.**

**해소 방향(리뷰어 제시, 둘 중 하나).**

1. **닫힘의 누적** — R6.10 유효 집합 ②를 "①의 기록 **또는 그보다 뒤의 어떤 `recorded` 기록**이 `resolved_finding_ids` 로 닫은 것을 제외한다" 로 고치고, 그 누적이 상태에서 계산 가능함을 R6.1 로 뒷받침한다.
2. **프롬프트 입력의 누적** — R2.10·C8 의 "직전 리뷰" 범위를 "그 `formal_round` 에서 **아직 닫히지 않은 모든** Critical/High"(예: `readiness-gate` 의 `high_findings` 출력)로 넓혀 판정 기록이 그 전부를 닫을 수 있게 한다.

어느 쪽이든 "라운드 N 의 attempt1 High → attempt2 닫음 → attempt3 clean 이 `READY` 에 도달하는가" 를 판정하는 AC 를 신설하고 추적표에 등재해야 한다.

### `SPEC-12` (Medium) — 미해소

경로 A(등록 digest 기록 있음)에서 판정 기록보다 **뒤에** 있으면서 등록 digest 를 가리키지 않는 `recorded` 기록의 Critical/High 가 유효 집합의 어느 항에도 들어가지 않는다. 산출물이 이전 digest 로 되돌아간 경우 실제로 발생하며, 그때 더 최근에 확인된 High 가 무시된다.

### `SPEC-13` (Medium) — 미해소

`유효 Critical/High 집합`을 쓰지 않고 "가장 최근 기록의 Critical/High 0" 만으로 arbitration 을 서술하는 자리가 셋 남았다 — R4.4 (i), AC-31, § Architecture 의 `ARBITRATION` 정의(범위를 표 갈래로만 한정). **`HOLD` 정의에는 "등록 digest 를 가리키는 기록이 있는 경로에서도 같다" 가 있는데 `ARBITRATION` 에는 없다** — 같은 개정에서 한쪽만 넣은 것이다.

### `SPEC-14` (Medium) — 미해소

실패 기록(`schema_invalid`·`digest_mismatch`·`invocation_failed`)에서 `resolved_finding_ids` 의 값이 미정이다. R6.1 은 "결과의 배열을 그대로 복사한다" 고 하는데 R6.9 의 실패 기록 필드 열거에는 그 필드가 없고, `invocation_failed` 는 복사할 결과 파일 자체가 없을 수 있다.

### `SPEC-15` (Low) — 미해소

AC 정의 순서가 AC-116 → AC-118·119·120 → AC-117 로 어긋났다. 번호는 연속·고유하지만 이 Spec 이 산출물에 요구하는 규율(C6)과 맞지 않는다.

### 이 실행이 남긴 패턴 — 같은 구멍이 다섯 번

`SPEC-03` → `READY-08` → `SPEC-07` → `READY-10` → `SPEC-11`. 전부 **"확인된 Critical/High 가 게이트 판정에서 사라지는 경로"** 라는 하나의 구멍이 모양을 바꾼 것이다. 매번 직전 지적이 가리킨 경로만 고쳤고, 그때마다 고치지 않은 다른 경로가 다음 라운드의 blocker 가 됐다.

라운드 3 에서 `유효 Critical/High 집합`을 한 번 정의해 두 경로가 같은 집합을 쓰게 한 것은 그 반복을 끊으려는 시도였고, 실제로 경로 문제는 닫혔다. 그러나 **집합의 시간축 누적**(기록 간 닫힘 전파)이라는 축이 남아 있었고 그것이 `SPEC-11` 이다. 곧 이 설계는 "어느 경로에서 보는가" 와 "어느 시점까지 누적하는가" 두 축을 함께 다뤄야 하는데, 세 라운드 동안 첫째 축만 반복해 좁혔다.

**후속 실행에 넘길 교훈.** 이 부류의 규칙은 지적된 문장을 고치는 방식으로 수렴하지 않는다. 상태 전개의 **불변식**을 먼저 한 문장으로 못박고("확인된 Critical/High 는 명시적으로 닫히기 전까지 그 `formal_round` 의 모든 후속 판정에서 유효하다"), 그 불변식을 참조하는 형태로 각 경로를 쓰는 편이 낫다. 라운드 3 의 `유효 Critical/High 집합`이 그 방향의 절반이었다.

## Plan approval

- Approval timestamp: 아직 없음 — `AWAITING_PLAN_APPROVAL` 에 도달하지 않았다
- Plan digest: 아직 없음

승인 게이트는 이 워크플로의 유일한 사용자 승인 지점이다. 구현 도달 시 그 자리에서 멈춘다.

## Changed files

구현은 시작하지 않았다. 지금까지 바뀐 것은 워크플로 산출물뿐이며 전부 untracked 다.

| 파일 | 상태 | 내용 |
|---|---|---|
| `docs/development/2026-09-05-…/spec.md` | 수정 | 719 → 720행. 요구사항 69 → 70, AC 113 → 116 |
| `docs/development/2026-09-05-…/spec-revision-notes.md` | 수정 | `## v5.0.0 정렬 개정`, `### readiness attempt 1 반영`, `## 라운드 2 개정` 세 절 추가 |
| `docs/development/2026-09-05-…/plan.md` | 수정 | 439 → 440행. `PLAN-06`·`07`·`08` 해소와 v5.0.0 정렬 |
| `docs/development/2026-09-05-…/plan-revision-notes.md` | 신설 | 재개 실행 개정 노트 |
| `docs/development/2026-09-05-…/report.md` | 수정 | 이 문서 |
| `docs/development/2026-09-05-…/report-2026-09-05-needs-redesign.md` | 신설 | 직전 실행 보고서 보존본 |

`.prior-art/` 와 `dot_claude/skills/quality-goal/` 은 손대지 않았다. 커밋·푸시·머지·`chezmoi apply` 를 하지 않았다.

## Verification evidence

구현 전이므로 구현 검증은 아직 없다. 지금까지 실제로 실행한 명령과 결과는 다음과 같다.

| 명령 | 종료 코드 | 근거 |
|---|---|---|
| `git rebase main` | 0 | fast-forward, 충돌 0. HEAD `6d60011cbdaead7946b191d3f12029eef5c141c8` |
| `git check-ignore -v .claude/quality-state/` | 0 | `.gitignore:25` 가 근거. 런타임 상태가 `git status` 에 노출되지 않는다 |
| `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/quality-goal/tests -p 'test_*.py'` | 0 | `Ran 310 tests` / `OK` (3.14.7) |
| 같은 명령, `/opt/homebrew/bin/python3.12` | 0 | `OK` (3.12.14) |
| 같은 명령, `/usr/bin/python3` | 1 | `Ran 310 tests` / `FAILED (errors=23)` — `enterContext` 부재 (3.9.6) |
| 같은 명령 `-k zzz`, 3.14.7 / 3.12.14 | 5 / 5 | `NO TESTS RAN` |
| 같은 명령 `-k zzz`, 3.9.6 | 0 | `OK` — 3.12 미만에서 존재하지 않는 테스트 이름이 통과한다 |
| `revision_check.py --artifact spec` 라운드 1 | 0 | `passed true`, 빈 칸 0 |
| `revision_check.py --artifact spec` 라운드 2 (1차) | 1 | `중복 정의 R1.9 2회`, `R 수=추적 행 수 69 / 70` |
| `revision_check.py --artifact spec` 라운드 2 (최종) | 0 | `passed true`, 빈 칸 0, 노트 절·행·셀 완비 |
| `validate_review.py validate --artifact spec` r1 | 0 | `{"valid":true,"errors":[]}` |
| `validate_review.py gate --artifact spec` r1 | 3 | `score_below_85`·`verdict_not_pass`·`blockers_present`·`critical_or_high_finding` |
| `ac_crosscheck.py` (AC 전수 대조) | 1 | 1차 10건 → 스크립트 결함 6건 수정 → 진짜 결손 1건(`[A 생성] AC-84`) 해소 → 의도된 예외 1건(`R9.6`) |
| `revision_check.py --artifact spec` 라운드 2 (최종, 노트 누적 뒤) | 0 | `passed true`, 빈 칸 0, `missing_rows []`, `blank_cells []` |
| `validate_review.py validate --artifact spec --prior` r2 | 0 | `{"valid":true,"errors":[]}` |
| `validate_review.py gate --artifact spec --prior` r2 | 3 | `verdict_not_pass`·`blockers_present`·`critical_or_high_finding` (score 87 이라 `score_below_85` 없음) |
| `record-review --revision-check` 라운드 2 | 0 | `rounds.spec=2`, `revision_checks.spec` 에 라운드 2 기록, `snapshots/spec-r2.md` 생성. **v5.0.0 개정 점검 계약의 첫 실전 통과** |
| `latest_record_check.py` | 0 | 게이트 문맥 19개 줄 중 '가장 최근 recorded 기록' 한정 누락 0 |
| `codex exec` readiness attempt 1~5 | 0 | read-only, `--ephemeral`, `gpt-5.6-sol` high. 금지 플래그 미사용 |
| `codex exec` readiness attempt 6 | 회수 | 시스템 메모리 부족으로 호스트가 종료(events 7행). Codex 실패·타임아웃이 아니며 `spec.md` digest 불변 확인 |
| `codex exec` readiness attempt 7·8·9 | 125 / 125 / 144 | 세 번 다 모델 응답 정지. 감시자가 events 정지(600s·480s·360s)로 회수. stderr 비어 있음, 잔존 프로세스 0, `spec.md` digest 불변 |
| `revision_check.py --artifact spec` 라운드 3 | 0 | `passed true`, 빈 칸 0, `## 라운드 3 개정` 절·행·셀 완비 |
| 계수 스크립트 (라운드 3) | 0 | 요구사항 71 / 추적표 71행 / AC 120, 중복·결번·유령 참조 0, 요구사항 정의 집합 == 추적표 행 집합 |
| `latest_record_check.py` (라운드 3 최종) | 0 | 게이트 문맥 23개 줄 전부 한정 있음 |
| `validate_review.py validate --artifact spec --prior` r3 | 0 | `{"valid":true,"errors":[]}` |
| `validate_review.py gate --artifact spec --prior` r3 | 3 | `score_below_85`·`verdict_not_pass`·`blockers_present`·`critical_or_high_finding` |
| `record-review --revision-check` 라운드 3 | 0 | `NEEDS_REDESIGN` / `REVIEW_LIMIT_EXHAUSTED:spec` 전이. `revision_checks.spec` 에 라운드 3 기록 |

**lint·type check·build·E2E 는 `not configured` 다.** 근거로 확인한 것은 `docs/quality-goal-maintenance.md` 의 `## 결정적 테스트` 절이 `unittest` 명령 하나만 싣는다는 것과, `dot_claude/skills/quality-goal/` 아래에 그런 설정 파일이 없다는 것이다. 통과로 기록하지 않는다.

## Remaining advisory findings

| ID | severity | 상태 | 내용 |
|---|---|---|---|
| `SPEC-04` | Medium | 해소 | AC-84 가 가리키는 `## 판정 명령 표` 절을 만들라는 요구사항이 없었다. R9.4 에 "`## 결정적 테스트` 를 `## 판정 명령 표` 로 대체" 규정을 넣고 AC-115 를 신설했다 |
| `SPEC-05` | Medium | 해소 | R6.5 의 새 보존 조건 `revision_checks` 를 판정하는 AC 가 없었다. AC-43 의 보존 대상 목록에 넣었다 |
| `SPEC-06` | Low | 해소 | `### D13.` 헤딩 앞 빈 줄 복원 |
| `READY-01` | Low | 해소 | 직전 실행 r3 의 `SPEC-24`(결정 절 번호와 정의 순서 불일치) 미해소. D11·D12 를 D10 뒤로 이동 |
| `SPEC-07` | High | 라운드 3 진행 중 | 대체 규칙에 재판정 보장이 없어 두 경로로 fail-open. 사용자 결정으로 두 갈래 모두 닫는다 |
| `SPEC-08` | Medium | 라운드 3 진행 중 | R6.10 표에 적용 범위 한정이 표 안에 없음 |
| `SPEC-09` | Low | 라운드 3 진행 중 | § Failure behavior 의 `High` 표기를 `Critical/High` 로 통일 |
| `SPEC-10` | Low | 라운드 3 진행 중 | AC-86 의 판정 수단 표기가 실제 판정 위치와 어긋남 |
| `READY-02`~`READY-09` | High 둘 외 | 해소 | Codex 사전 심사가 잡은 여덟. 상세는 `spec-revision-notes.md` 의 `## 라운드 2 개정` |
| 전수 대조 `R9.6` | — | **의도된 예외** | AC-67 은 세 rubric 의 임계 85 를, AC-78 은 `SKILL.md` 문언을 판정해 대상 파일이 갈린다. R9.6 은 성질상 서로 다른 파일에 사는 서로 다른 사실을 묶는 요구사항이라 정상이다. Plan 추적표 머리말에 명시했다 |

### 후속으로 넘기는 것

- **배포본 `tests/` 격차** — `~/.claude/skills/quality-goal/tests/` 가 source 보다 뒤처져 있다(`test_revision_check.py` 와 `tests/fixtures/revision-check/` 미배포). 이 작업은 `chezmoi apply` 를 하지 않으므로 사용자가 배포 시점을 고를 때 해소된다. 실행 파일 다섯(`SKILL.md`, `references/model-routing.md`, `references/spec-rubric.md`, `references/plan-rubric.md`, `scripts/quality_state.py`, `scripts/validate_review.py`)은 두 트리가 동일하다.
- **`.gitignore` 상태** — `.claude/quality-state/` 는 이미 무시된다(`.gitignore:25`). 추가 조치가 필요 없다.
- **리뷰어 턴 한도** — Spec 라운드 1 에서 quality-reviewer 가 24턴 한도에 걸려 중간에 멈췄고, 남은 확인 항목을 좁혀 이어서 진행시킨 뒤에야 JSON 을 반환했다. 라운드 2 이후에도 같은 일이 생길 수 있다.

## Final status

- Status: `NEEDS_REDESIGN`
- Machine-readable reason: `REVIEW_LIMIT_EXHAUSTED:spec`

**종결.** Spec 라운드 3 이 `82 / REVISE / blocker SPEC-11` 로 끝나 `record-review` 가 `NEEDS_REDESIGN`(`REVIEW_LIMIT_EXHAUSTED:spec`)으로 전이시켰다. Plan 단계·구현·승인 게이트에는 도달하지 않았다. 커밋·푸시·머지·`chezmoi apply` 를 하지 않았고 `dot_claude/skills/quality-goal/` 은 한 글자도 바뀌지 않았다.

### 재개 방법

Spec 은 버리지 않는다. 743행, 요구사항 71, AC 120 이며 라운드 1·2 의 finding 열 건이 전부 해소 확인됐다. 남은 다섯(`SPEC-11`~`SPEC-15`)을 반영한 뒤 **새 goal 로 `/quality-goal` 재시작**하면 라운드 셋을 다시 쓸 수 있다.

- `SPEC-11` 은 위 두 갈래 중 하나를 택해 닫는다. 리뷰어가 제시한 판정 AC("attempt1 High → attempt2 닫음 → attempt3 clean 이 `READY` 에 도달하는가")를 함께 신설한다.
- `SPEC-12`~`SPEC-15` 는 문언 정합과 순서 정리라 기계적이다.
- **Plan 은 이번 실행에서 개정을 마쳤다** — `PLAN-06`·`PLAN-07`·`PLAN-08` 해소와 v5.0.0 정렬이 끝났고, 남은 것은 AC 일곱 행(AC-114~AC-120)을 추적표에 추가하고 소유 태스크를 확정하는 것이다. 잠정 배치는 개정 노트에 있다.
- 재개 시 `.claude/quality-state/20260906T100138Z-…/` 의 리뷰 JSON·readiness 결과·개정 점검 JSON·스냅숏을 근거로 쓸 수 있다.

### 산출물

`docs/development/2026-09-05-70-quality-goal-codex-spec-readiness/` 의 `spec.md`(743행), `plan.md`(440행), `spec-revision-notes.md`, `plan-revision-notes.md`, `report.md`(이 문서), `report-2026-09-05-needs-redesign.md`(직전 실행 보존본). 워크트리 브랜치 `70-feat/quality-goal-codex-spec-readiness`, base `6d60011cbdaead7946b191d3f12029eef5c141c8`, 전부 미커밋.

**라운드 3 이 Spec 한도의 마지막이다.** PASS 면 `SPEC_PASSED` → `PLAN_REVIEW` 로 진행하고, Plan 개정본(AC 117 반영 포함 — `AC-114`~`AC-117` 네 행이 아직 Plan 추적표에 없다)을 등록해 readiness 와 공식 리뷰를 돌린 뒤 `AWAITING_PLAN_APPROVAL` 에서 사용자 승인을 기다린다. PASS 가 아니면 `record-review` 가 그 자리에서 `NEEDS_REDESIGN`(`REVIEW_LIMIT_EXHAUSTED:spec`)으로, `SPEC-07` 이 재발하면 `RECURRING_BLOCKING_FINDING:SPEC-07` 로 종결한다. 어느 쪽이든 이 보고서가 이미 등록돼 있어 종결 시점의 등록 실패는 발생하지 않는다.

**이 실행이 남긴 실측 하나.** Spec 자신의 R4.1 은 시도 구간당 readiness 2회를 규정하는데 `formal_round` 2 에서 attempt 3·4·5·6 을 썼다. 설계된 규칙대로였다면 attempt 4 뒤 게이트가 갈래 ②로 `HOLD` 를 내고 사용자 결정을 기다렸을 자리이며, attempt 5 는 그 상태에서 `READY-08` 재발을 잡았고 attempt 6 은 회수됐다. 배포본 v5.0.0 에 그 게이트가 없어 실행이 가능했다. 이슈 #70 이 "2회 한도의 적정성은 미검증" 이라고 남긴 항목의 표본이 된다 — **이 표본에서는 2회로 부족했다.**
