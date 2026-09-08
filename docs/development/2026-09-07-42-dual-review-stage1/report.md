# Quality Goal Report

- Task ID: 20260907T074534Z-42-1단계-claude-codex-독립-이중-리뷰-교차-비평-종합-로컬-bd3de195
- Mode: standard
- Status: CODE_REVIEW (구현·수정 진행 중, 라운드 1 소비)
- Created: 2026-09-07
- Updated: 2026-09-07
- Source goal: #42 1단계 — Claude+Codex 독립 이중 리뷰·교차 비평·종합 로컬 파이프라인 스킬(dual-review), PR 게시 제외

#42의 **다섯 번째** quality-goal 실행이다. 앞선 네 번은 모두 Spec 또는 Plan 한도로 죽었고, 이번은 이슈 #42 본문의 "범위 — 두 단계로 분할한다" 결정에 따라 **1단계(로컬 보고서까지)** 로 범위를 줄여 착수했다.

이 보고서는 사용자 지시에 따라 각 마지막 라운드 제출 **전에** 갱신·등록해 왔다. Spec 은 라운드 3에서 88점 PASS 했고, 지금은 Plan 라운드 1 결과를 기다린다.

## Classification

`--mode=standard`가 명시됐고 위험 스캔 결과와 일치해 다운그레이드 확인이 필요 없었다.

**strict 트리거 0건.** 4차 실행을 strict로 만든 유일한 근거는 "외부 API 쓰기 + 멱등성"이었는데, 이슈 #42 본문이 1단계를 "산출물은 로컬 보고서 파일까지. GitHub 에 쓰지 않는다"로 정의하면서 그 트리거가 범위에서 사라졌다. 인증·권한·테넌시·결제·PII·비밀·스키마 마이그레이션·파괴적 연산·프로덕션 인프라 모두 해당 없음.

**standard 조건 3건 충족.**

- 다파일·다모듈 변경 — `dot_claude/skills/dual-review/` 하위에 `SKILL.md`·`references/`·`schemas/`·`scripts/`·`tests/` 신설.
- 비자명 인터페이스 신설 — 리뷰어 구조화 출력 스키마, 교차 비평 계약, 종합자의 합의·불일치·신뢰도 출력 계약.
- 대안·비목표·수용 기준의 명시 필요 — 사용자가 비목표 4건(PR 게시 계약, 중복 게시 방지, 기준 커밋 SHA 명시, 재실행 갱신 정책)을 명시 지정.

이슈 라벨 `enhancement`·`quality-goal`·`P3-low` 중 `enhancement`를 기능 추가 근거로 인용했다. `P3-low`는 `routing-rules.md` 3항에 따라 모드를 낮추지 않는다.

## Review history

### Spec (한도 3, 3라운드 소진, PASS)

| 라운드 | 점수 | verdict | blockers | High | 처리 |
|---|---|---|---|---|---|
| 1 | **65** | REVISE | SPEC-001·002·003·004 | 4 | `record-review` — 라운드 1 소비 |
| 2 | **84** | REVISE | SPEC-012 | 1 | `record-review --revision-check` — 라운드 2 소비 |
| 3 | **88** | **PASS** | **없음** | **0** | `record-review --revision-check` — 라운드 3 소비. 게이트 `{"passed":true,"reasons":[]}` |

라운드 3은 첫 응답이 `PASS reviews must not contain unverified evidence`로 스키마 검증에 걸렸다. 리뷰어가 실행 도구 부재로 digest 를 직접 재계산하지 못해 `verified: false` 로 남긴 evidence 1건 때문이다. `record-review-error` 로 기록(재시도 1회 사용)하고 **검증 오류만** 추가해 같은 컨텍스트로 재호출했다. 재시도 응답은 같은 판정(88 PASS)을 유지하면서 그 항목을 실제로 검증한 것(두 독립 산출물의 digest·행 번호 교차 대조)으로 재서술해 `verified: true` 가 됐다. 라운드는 소비되지 않았다.

**다섯 번째 시도 만에 Spec 이 처음 통과했다.** 1차 89(한도 소진), 2차 93 PASS 후 Plan 에서 사망, 3차 83(재발 규칙), 4차 83(한도 소진), 5차 88 PASS.

### Plan (한도 2)

| 라운드 | 점수 | verdict | blockers | High | 처리 |
|---|---|---|---|---|---|
| 1 | **73** | REVISE | PLAN-001·PLAN-002 | 2 | `record-review` — 라운드 1 소비 |
| 2 | **90** | **PASS** | **없음** | **0** | `record-review --revision-check` — 라운드 2 소비. 게이트 `{"passed":true,"reasons":[]}` |

라운드 2도 Spec 라운드 3과 같은 스키마 제약(`PASS reviews must not contain unverified evidence`)에 첫 응답이 걸렸다. 리뷰어가 `-c` 오버라이드 우선순위·digest 재계산·구현 부재 셋을 `verified: false` 로 남긴 것이 원인이다. `record-review-error` 로 기록(재시도 1회 사용)하고 검증 오류만 추가해 재호출했고, 재시도 응답은 같은 판정(90 PASS)을 유지하면서 세 항목을 **실제로 확립한 것**으로 재서술했다 — digest 는 두 독립 산출물의 교차 대조로, 구현 부재는 "Plan 단계에서 가능한 검증"으로, `-c` 는 evidence 가 아니라 `PLAN-008` 의 `required_resolution` 안에 단서로 옮겼다.

**같은 스키마 제약이 두 산출물의 마지막 통과 라운드에서 연속으로 발생했다.** `#70` 후속에 기록할 만하다 — PASS 를 낼 만큼 충실히 검증한 리뷰어일수록 "내가 직접 확인하지 못한 것"을 정직하게 남기고, 그것이 곧 스키마 위반이 된다. 재시도 프롬프트에 "스키마 제약이지 평가가 틀렸다는 신호가 아니다"를 명시해야 판정이 흔들리지 않는다.

#### 라운드 2 findings — 전부 이번 개정이 만든 것

| ID | 심각도 | 내용 |
|---|---|---|
| PLAN-008 | Medium | 확장한 allowlist 에 `-c` 가 들어갔는데 **설정 키 값 공간에 제약이 없다.** `codex exec -c <key>=<value>` 는 일반 오버라이드라 sandbox·승인·디렉터리 관련 키를 실으면 `--sandbox read-only` 단정과 CMD-4 를 **둘 다 통과하면서** 우회할 수 있다 |
| PLAN-009 | Medium | T3 가 T1 템플릿으로 terminal `report.md` 를 렌더링하는데 **T1 이 그 템플릿에 무엇을 담는지 정하지 않는다.** 절 고정은 T8 이 한다 |
| PLAN-010 | Low | AC-65 의 "최소 한 Python 파일 검사" 절이 T2 의 CMD-6 통과 게이트와 충돌 |

셋 다 `new_blocker_evidence` 를 갖는다. `PLAN-008` 은 `PLAN-002` 해소가, `PLAN-009` 는 `PLAN-001` 해소가, `PLAN-010` 은 `PLAN-004` 해소가 만들었다.

**이것이 이 작업의 지속되는 패턴이다** — 개별 해소는 매번 정확한데 그 해소가 한 겹 아래에 새 결함을 만든다. 다만 이번 세 건은 전부 Medium·Low 로 나왔고 blocker 가 아니다. 규모를 66·86 에서 36·71 로 줄인 뒤 교차 회귀의 **심각도가 내려갔다.**

라운드 1 게이트 실패 사유: `score_below_85`·`verdict_not_pass`·`blockers_present`·`critical_or_high_finding`. 결정적 체크 셋(`required_sections`·`traceability_complete`·`placeholders_absent`)은 통과했다.

#### 라운드 1의 두 blocker

| ID | 심각도 | 내용 |
|---|---|---|
| PLAN-001 | High | T3 가 소유한 `AC-4`·`AC-5`·`AC-51`·`AC-55`·`AC-58` 다섯이 전부 **보고서 내용과 provenance sidecar** 를 단정하는데, sidecar 최초 작성은 T5·T7 이고 renderer 는 T8 이다. T3 종료 시점에 통과 불가능하고 Rollout gate 가 T3 에서 전체를 정지시킨다. **사전 점검이 잡아 고친 `AC-63`·`AC-64` 와 같은 결함 모양이 다섯 건 더 있었다** |
| PLAN-002 | High | **자기 참조 함정.** `CMD-4`·`CMD-5` 가 스킬 디렉터리 전체를 스캔해 금지 문자열 매치를 실패로 보는데, Plan 이 그 디렉터리 안 `references/verification.md` 에 "CMD-1~12 문서화" 를 시키고 T2 계약 테스트에 금지 옵션 열거를 시킨다. **검사가 자기 문서 때문에 영구히 실패**하고 Rollout 이 T2 에서 정지한다 |

`PLAN-002` 는 사전 점검 둘(6.1.2 대칭 점검, 자체 스크립트)이 모두 놓쳤다. 대칭 점검의 초점이 "통과 확인의 시점 성립"이었고 자체 스크립트는 구조 대조만 하므로, **명령의 스캔 범위와 그 범위 안 산출물의 내용이 충돌한다**는 종류를 볼 수 없었다. 공식 리뷰가 처음 잡았다.

#### 라운드 2 개정과 제출 전 점검

라운드 1의 7건을 한 라운드에 닫았다. 태스크 9개·AC 71개·추적표 71행 유지, 신설 0.

| ID | 해소 |
|---|---|
| PLAN-001 | **(A)** — T3 가 세 terminal 상태(`no_changes`·`reviewer_failure`·`single_reviewer`)의 최소 `report.md`·`provenance.json` writer 를 직접 만들고, T8 이 같은 renderer 를 full report 로 확장한다. 소유권 이동 없이 태스크 본문을 맞추는 쪽을 택했다 |
| PLAN-002 | Global constraints 에 **금지 리터럴 부재 불변식** + **우회 표기 규약**(`<forbidden-codex-option-N>`·`<github-write-command-N>` placeholder). `references/verification.md` 는 목적·종료 코드 계약만 서술하고, 계약 테스트는 allowlist 방식을 쓰며 필요한 금지 token 은 `tempfile.TemporaryDirectory()` 로 스캔 대상 밖에서 구성한다 |
| PLAN-003 | `derive_finding_id()` 등 T3~T8 의 생산·소비 callable 이름을 File map·각 태스크·T8 경계 테스트에 같은 이름으로 고정 |
| PLAN-004 | CMD-4·5 를 실패 확인에서 **부재 불변식**으로 분리하고 비공허 조건을 기록. AC-65 는 T2 가 불변식만 설치하고 T3 의 CMD-1 이 첫 비공허 관측임을 명시 |
| PLAN-005 | 전체 output schema 실패만 재요청하고 finding 단위 거부는 retry count·출처 제외를 일으키지 않음을 T3·T4 양쪽에 고정 |
| PLAN-006 | T1 이 `schemas/.gitkeep`·`scripts/.gitkeep` 을 만들어 여섯 구성 요소가 추적 가능한 산출물에 근거하게 함 |
| PLAN-007 | 실행 fixture 를 `TemporaryDirectory` 로 한정해 자동 제거. rollback 범위 정리 |

##### 우회 표기 규약을 오케스트레이터가 실측 검증했다

`PLAN-002` 의 해소는 "검사를 무력화하지 말고 성립하게 만들라"는 제약이 붙어 있었다. 규약이 실제로 성립하는지 합성 트리로 직접 측정했다.

| 대상 | CMD-4 | CMD-5 |
|---|---|---|
| placeholder 만 담은 `references/verification.md` | **exit 0**(통과) | **exit 0**(통과) |
| 실제 금지 리터럴(`--yolo`, `gh pr comment`)을 넣은 파일 | **exit 1**(실패) | **exit 1**(실패) |
| 확장 allowlist 여덟 플래그를 담은 문서 | **exit 0**(통과) | — |

스캔 범위를 줄이거나 패턴을 느슨하게 하지 않았고, 실제 위반은 여전히 잡힌다.

##### (f) 검사를 신설했다 — PLAN-001 계열의 기계 검출

사용자가 "9개 태스크 전수 대조"를 지시해, 기존 (a)~(d) 스크립트에 축을 하나 더 만들었다.

> **(f)** 각 소유 AC 의 기대 결과가 언급하는 산출물(`report.md`·`provenance.json`·run-root `.gitignore`·round0 프롬프트·시작 기록·run directory)을 **그 태스크 또는 그 선행 폐포가 실제로 만드는가.**

라운드 1 판본에 적용해 `PLAN-001` 의 핵심(T3/AC-5 의 `provenance.json`)을 독립 재현했고, 라운드 2 판본에서는 위반 0 이다.

한계도 기록한다. 선행 폐포를 넣기 전에는 T3 에서 6건을 잡았으나 넣은 뒤 1건으로 줄었다 — T1 이 만드는 `templates/report.md` 를 run-directory `report.md` 와 구별하지 못하기 때문이다. **어휘 기반 휴리스틱이고 권위는 공식 리뷰와 대칭 점검에 있다.**

##### 6.1.2 대칭 점검이 마지막 라운드 제출 전에 High 1건을 더 잡았다

초점은 사용자가 지정한 둘 — "각 태스크의 통과 확인이 그 태스크 종료 시점에 성립하는가", "CMD-4·5 가 자기 문서에서 오탐하지 않는가".

라운드 1 findings 7건 중 6건 해소 확인, `PLAN-002` 는 **부분 해소** 판정. 이유:

> T2 의 허용 플래그 **정확 집합**이 `{--sandbox, --output-schema}` 두 개뿐이라, 실제 안전한 Codex 호출에 필요한 `-C`·`--ephemeral`·`--model`·`-c`·`--output-last-message`·`--json` 을 템플릿에 넣으면 `test_reviewer_contract` 가 실패하고, 빼면 실행 계약을 표현하지 못한다. **자기 오탐 해소가 정상 호출 거부라는 새 회귀를 만들었다.**

allowlist 를 안전 여덟 플래그 전체로 확장해 닫았다. `--sandbox` 값 `read-only` 단정은 별도로 유지하고, 확장된 플래그가 CMD-4 패턴과 겹치지 않음을 실측했다.

이것은 오케스트레이터가 대칭 점검 요청서에 **의심 지점으로 명시해 넘긴 항목**이었다("T2 의 allowlist 가 Spec 의 실제 Codex 호출을 표현하기에 충분한지 판단하라"). 라운드가 하나뿐인 상태에서 잡혔다.

##### 제출 직전 상태

| 검사 | 결과 |
|---|---|
| `revision_check.py --artifact plan` (round 2) | exit 0, `empty_cells` 0, 개정 노트 파급표 통과 |
| 자체 대조 (a)(b)(c)(d) | exit 0 |
| (f) 산출물 대조 | exit 0 |
| 게이트 체크 3종 | 필수 절 8개·자리표시자 0·strict 마커 0·추적표 71행·태스크 9개 |

#### Plan 제출 전 대조 — 사용자가 스크립트 강제를 지시했다

최근 두 작업이 Plan 단계에서 죽었다(`#70` `PLAN-06`, `#79` 검증 지문 불일치). 사용자가 제출 전 다섯 축 (a)~(e)를 **스크립트로** 대조하라고 지시했다. 두 도구를 각각 돌렸고 **둘 다 실제 결함을 잡았다.**

| 도구 | 축 | 초안 1차 결과 |
|---|---|---|
| `revision_check.py --artifact plan` | AC 판정 수단의 co-location | **71건 전부 `empty`** |
| 오케스트레이터 자체 스크립트 | (a)(b)(c)(d) | 위반 0 (초기 (c) 정의 오류로 위양성 8건) |

**`revision_check` 가 잡은 것이 정확히 `#70` 의 `PLAN-06`이다.** 추적표의 판정 수단 토큰이 소유 태스크 본문에서 그 AC ID 가 등장하는 **바로 그 줄에** 있어야 하는데, 초안은 `- 대상 AC: AC-59, AC-60, …` 로 ID 만 나열했다. 정본 픽스처(`dot_claude/skills/quality-goal/tests/fixtures/revision-check/plan-complete.md`)의 통과 형태를 author 에게 제시해 AC별 한 줄 71개를 추가시켰고, 보정 후 exit 0 / `empty_cells: 0` / non-ok 0.

##### 자체 스크립트의 (c) 정의를 도중에 교정했다

처음에는 (c)를 "같은 요구사항의 형제 AC 가 같은 판정 대상을 가리키는가"로 구현해 8건을 보고했다. `plan-plan06-shape.md` 픽스처를 읽어 `PLAN-06` 의 실제 모양이 co-location 이며 그것을 `revision_check` 가 이미 정확히 구현하고 있음을 확인했다. 내 첫 구현은 전체 실행 명령 `CMD-1` 과 필터 명령을 불일치로 보는 **위양성**이었다.

(c)를 **"Plan 의 판정 대상이 Spec 의 AC별 배정과 다른가"** 로 다시 정의했다. 재실행 결과 위반 0, 관찰 4건(R2.3·R7.3·R9.3·R9.4 의 형제 AC 가 서로 다른 CMD 를 쓰지만 전부 Spec 배정 그대로).

스크립트 자체도 양방향 검증했다 — 통과해야 할 합성 Plan 에서 exit 0, 실패해야 할 합성 Plan 에서 (a)·(b)×2·(c)·(d) 다섯 위반을 정확히 검출.

**두 검사는 서로를 대체하지 않는다.** `revision_check` 는 co-location 을, 자체 스크립트는 Spec↔Plan 배정 일치와 (a)(b)(d)를 본다.

##### (e) 기존 테스트 갱신 대상 0건

추적 파일 중 `dual-review`·`dual_review`·`.claude/dual-review-state` 를 리터럴로 고정한 테스트가 없다. `skills/` 를 참조하는 두 스크립트는 경로가 `quality-goal` 로 하드코딩돼 있다 — `assert_preserved_sections.py:19` 의 `SKILL_PATH`, `assert_tests_preserved.py:10-13` 의 `TEST_PATHS`. 새 스킬이 이들을 깨뜨리지 않는다. Plan 은 이 사실을 기록하고 갱신 태스크를 만들지 않았다.

#### 6.1.2 대칭 점검이 Plan 에서 High 2건을 잡았다 — 라운드 소비 전

초점은 사용자가 지정한 "각 AC 의 통과 확인이 **소유 태스크 종료 시점에 실제로 성립하는가**" 였다. 71건 전수 대조 결과 67건 성립, 4건 미성립.

| # | 심각도 | 내용 | 해소 |
|---|---|---|---|
| 1 | **High** | `AC-64`(T3 소유)가 정규화·ID·셔플·종료·렌더링 Python 함수를 전부 요구하는데 그 구현은 T4·T6·T7·T8 에 있다. T3 의 `CMD-12`·`CMD-1` 이 T3 종료 시점에 통과 불가능하고, Rollout 의 "태스크별 통과 전 다음 태스크 진행 금지" gate 가 **T3 에서 전체를 정지**시킨다 | `AC-63`·`AC-64` 소유를 다섯 경계가 모두 존재하는 **T8** 로 이동(태스크 본문 `대상 AC:`·AC별 줄·추적표 `Task` 열 세 곳 동시). T3~T9 의 통과 확인을 "이 시점에 존재하는 테스트"로 좁힘 |
| 2 | **High** | **T4↔T7 데이터 순환.** `R3.2` 는 group 라벨을 `finding_id` 파생의 입력으로 요구하는데, T7 본문은 "T4 의 그룹-네임스페이스 `finding_id` 를 그대로 입력으로 삼아 A/B 를 배정"한다고 적어 group→ID→group 이 된다 | T7 을 **A/B 배정 → group 공급 → ID 파생 → ASCII 정렬·seeded shuffle** 순서로 고정. T4 는 **명시적 group 인자를 받는 순수 파생 함수와 fixture 만** 소유. T7 의 `[실패 확인]`·`[통과 확인]` 이 그 호출 순서 위반을 assertion failure 로 단정 |

**#2 는 오케스트레이터가 판단을 보류하고 넘긴 지점이었다.** Plan 초안을 읽으며 "T4 가 `finding_id` 를 계산하려면 group 라벨이 필요한데 A/B 배정은 T7 에 있다 — 순환인지 순수 함수 구조인지" 를 대칭 점검 요청서와 사용자 보고 양쪽에 명시했고, 대칭 점검이 **순환으로 판정**했다. 사용자가 앞서 경고한 "A/B 라벨과 원문 ID 처리가 다른 태스크로 흩어지면 구현 순서에 따라 한쪽만 반영된다"와 같은 계열이다.

Plan 은 라운드가 **2회뿐**이므로 두 건을 제출 전에 닫았다. 그대로 제출했다면 라운드 하나를 확실히 소비했을 것이다.

두 라운드 모두 게이트 실패 사유는 `score_below_85`·`verdict_not_pass`·`blockers_present`·`critical_or_high_finding`이고, 결정적 체크 셋(`required_sections`, `material_decisions_resolved`, `acceptance_criteria_objective`)은 두 번 모두 통과했다.

라운드 2는 **임계 85에 1점 미달**이다. 라운드 1의 11건 중 10건이 해소 확인됐고, 남은 blocker는 라운드 2 개정이 새로 만든 `SPEC-012` 하나다.

### 라운드 1 findings 11건의 라운드 2 판정

| ID | 심각도 | 라운드 2 판정 |
|---|---|---|
| SPEC-001 | High | 해소 — 추적표 11행 불일치가 0행. 거짓 봉합 문장 제거 |
| SPEC-002 | High | **부분 해소** — enum·범위·변환표는 들어갔으나 `원문 ID` 조달 경로가 없음 → `SPEC-012`로 분리 |
| SPEC-003 | High | 해소 — 프롬프트 사슬 다섯 고리 연결 |
| SPEC-004 | High | 해소 — A/B 익명 그룹 라벨로 관계 보존 |
| SPEC-005~011 | Medium 4 / Low 3 | 전부 해소 |

### 제출 전 사전 점검이 라운드를 아꼈다 — 누적

공식 리뷰 라운드는 한도가 3이고 그것만이 희소 자원이다. 이 실행은 매 제출 **전에** 두 종류의 사전 점검(Codex readiness, 별도 Codex 대칭 점검)을 돌려 결함을 미리 닫았다.

| 라운드 | 사전 점검이 잡은 것 | 제출 전 처리 | 공식 리뷰가 새로 낸 것 |
|---|---|---|---|
| 1 | readiness 0건. 오케스트레이터 기계 대조가 추적표 11행 불일치 | 미처리(초안 그대로 제출) | High 4 / Medium 4 / Low 3 |
| 2 | readiness `READY-001` 1건, 대칭 점검 High 1 · Medium 2 | **4건 전부 닫고 제출** | High 1 (`SPEC-012`) / Medium 1 / Low 1 |
| 3 | readiness 0건, 대칭 점검 High 1 · Medium 1 → 재점검 후 0건 | **2건 닫고 제출** | 기록 대기 |

**라운드 2와 3에서 사전 점검이 잡은 여섯 건은 전부 실제 결함이었다.** 특히 두 건은 라운드를 확실히 태웠을 것이다.

- 라운드 2 대칭 점검 High — `R2.1` 이 `severity` 라벨을 요구만 하고 허용값·변환을 정하지 않아, 실측상 `Important`·`CRITICAL` 을 쓰는 생산자의 finding 이 `R3.3` 에서 전량 거부되고 `R8.2` 로 Claude 출처가 통째로 제외되는 경로.
- 라운드 3 대칭 점검 High — `원문 ID` 를 익명화 대상에 넣어 직접 누설은 막았는데, 그것에서 파생되면서 **종합자 입력에 반드시 남아야 하는** `finding_id` 에 불투명성 제약이 없어 생산자명이 평문으로 다시 드러나는 경로.

두 번째는 이 작업을 여섯 번 죽인 교차 회귀와 정확히 같은 형태다 — 해소가 한 겹 아래에 새 구멍을 만들었다. 차이는 **공식 라운드를 쓰기 전에 잡혔다**는 것이다.

### v5.1.0 author / readiness 첫 실전 사용 기록 (이슈 #70 대응점)

이 실행이 배포본 `quality-goal` v5.1.0의 Codex author + 사전 readiness 심사를 처음 실전 사용한 사례다.

#### Spec author (`gpt-5.6-terra`, effort high, `--sandbox workspace-write`)

| 항목 | 값 |
|---|---|
| 라운드 1 초안 | exit 0, 605.5초, stderr 0바이트 |
| `changed_files` | `docs/development/2026-09-07-42-dual-review-stage1/spec.md` 1건 |
| 쓰기 범위 위반 | **없음** — `git status --porcelain`의 추가 항목은 기존 dirty 2건과 산출물 디렉터리뿐 |
| 산출 규모 | 282행 / 요구사항 35 / AC 70 / 결정 6 / 판정 명령 12 |
| 규모 상한(40·80) 준수 | 예 |

**author 가 값을 한 지점.** 4차 실행의 992행·요구사항 66·AC 86 대비 282행·35·70으로, 사용자가 지정한 상한을 지킨 초안을 Claude 토큰 소모 없이 605초에 냈다. 식별자 문법(`- **R<n>.<m>**`, `- **AC-<n>**`, `[실행]`, 추적표, 판정 명령 표)을 정확히 지켜 `revision_check.py`가 라운드 1에서 `empty_cells: 0`, `passed: true`로 통과했다.

**author 에서 어긋난 지점 — 오케스트레이터의 자기 오판 1건.** 오케스트레이터가 events 스트림의 **중간 `agent_message`** 를 최종 결과로 잘못 읽어 "author가 파일을 쓰지 않고 종료했다"고 판단하고 재시도 프롬프트를 준비했다. 실제로는 작업 중이었고 최종 결과 파일의 `changed_files`는 정상이었다.

이것은 이슈 `#29` 본문이 이미 실측으로 남긴 함정이다 — "로그 중간에 `[codex] Assistant message captured: {"verdict":"approve"…}`가 잡히는데 최종과 다르다. 최소 3개 라운드에서 중간 캡처는 `approve`, 최종은 `needs-attention`이었다." 오케스트레이터가 그 함정을 그대로 밟았고, 같은 세션에서 Spec에 "Codex 결과는 `--output-last-message`가 가리키는 파일에서만 읽는다"를 요구사항으로 넣으라고 지시하던 중이었다.

**후속으로 반영할 것:** `SKILL.md`의 Codex invocation contract에 "events 스트림의 `agent_message`를 결과로 읽지 않는다. 결과는 `--output-last-message` 파일에서만 읽는다"를 명시한다. 현재 그 문언이 없다.

#### readiness reviewer (`gpt-5.6-sol`, effort high, `--sandbox read-only`, fresh context)

| 항목 | 값 |
|---|---|
| attempt / formal_round | 1 / 1 |
| score / verdict | **100 / READY** |
| findings | **0건** |
| C1~C8 | 8항목 전부 `pass` |
| digest 대조 | 심사자 계산값이 등록 digest와 일치 |
| 미검증 evidence | 0건 |
| 실행 | exit 0, 215.2초 |

**같은 판본에 대한 Claude 공식 리뷰는 65점 REVISE, High 4건이었다. 35점 차다.**

| 심사 주체 | 대상 | 점수 | verdict | High | 실제로 잡은 것 |
|---|---|---|---|---|---|
| Codex readiness r1 | 282행 초안 | **100** | READY | 0 | **없음** |
| Codex readiness r2 | 289행 개정본 | 95 | REVISE | 0 | `SPEC-007` 부분 해소 (C8) |
| Claude 공식 r1 | 282행 초안 | **65** | REVISE | **4** | High 4건 |
| Claude 공식 r2 | 289행 개정본 | 84 | REVISE | 1 | 개정이 만든 교차 회귀 1건 |

**readiness 가 값을 한 지점.** 여덟 체크가 전부 정확했다. 요구사항·추적표 행 수 일치, AC 번호 연속성, 판정 수단 배정, CMD 등재, strict 마커 부재 — 오케스트레이터가 독립적으로 파싱한 결과와 전부 일치했고 거짓 양성·거짓 음성이 없었다. digest 대조도 수행했다.

**readiness 가 놓친 지점 — 이번 라운드에서 경계가 정확히 드러났다.** 오케스트레이터가 **기계적 대조만으로** 찾은 결함을 readiness가 잡지 못했다.

> 추적표 35행 중 **11행**의 `Judgement method` 열이, 그 행이 가리키는 AC 본문의 CMD와 다르다. 추적표는 `CMD-3`(`-k test_reviewer_contract`)을 선언하는데 AC 본문은 `CMD-7`~`CMD-12`를 쓴다. `unittest -k`는 이름 부분 일치 필터이므로 선언된 명령으로는 그 AC의 테스트가 실행되지 않는다.

`C4`는 "누락·중복·유령 참조 0"만 보고 `C7`은 "모든 `[실행]` CMD가 표에 등재됨"만 본다. **둘 다 참이다.** 그런데 "추적표가 선언한 CMD == 그 행이 가리키는 AC 본문의 CMD"를 보는 체크가 여덟 항목 어디에도 없다.

4차 실행의 관측은 "readiness는 형식·추적은 보장하고 설계 정합성은 미보장"이었다. **이번 관측은 그보다 좁다 — 형식·추적 안에서도 "두 표현의 상호 일치"는 보장하지 않는다.** 이것은 새 체크 하나(`C9: 추적표 판정 수단 == AC 본문 판정 수단`)로 기계적으로 닫을 수 있는 종류이며, 설계 정합성처럼 LLM 추론이 필요하지 않다.

readiness 임계값(현재 90)을 게이트로 쓰려면 이 표본이 가리키는 결론은 이렇다 — **100점 READY는 "체크리스트 여덟 항목이 참"이라는 뜻이지 "형식이 정합하다"는 뜻이 아니다.**

#### 두 라운드를 합쳐 본 readiness — 값은 C8 에서만 나왔다

| | 라운드 1 | 라운드 2 |
|---|---|---|
| score / verdict | 100 / READY | 95 / REVISE |
| C1~C7 | 전부 pass | 전부 pass |
| C8 (직전 findings 대조) | 자동 충족(직전 findings 없음) | **fail** — `SPEC-007` partial |
| findings | 0 | 1 (Medium, `READY-001`) |
| 같은 판본의 공식 리뷰 High | 4 | 1 |

**두 라운드 모두 C1~C7 의 기계적 형식 검사는 아무것도 잡지 못했다.** 라운드 1에서는 C1~C7 이 전부 pass 인 판본에 High 4건이 있었고, 그중 `SPEC-001`(추적표 11행 불일치)은 오케스트레이터가 파싱만으로 찾을 수 있는 **형식 결함**이었다.

**readiness 점수를 움직인 것은 오직 C8 이었다.** `READY-001`(AC-46 이 종료 사유 enum 을 판정하지 않음)은 유효한 지적이었고 오케스트레이터가 독립 확인 후 반영했다.

이 표본이 가리키는 개선 방향 둘.

1. 체크리스트에 **"추적표 판정 수단 == AC 본문 판정 수단"** 대조를 추가한다. 라운드 1에서 그 부재가 High 1건을 통과시켰고, 이것은 LLM 추론이 아니라 파싱으로 닫히는 종류다.
2. `readiness-policy.md` 에 **"readiness 결과는 다음 개정 전에 `record-readiness` 로 기록한다"** 를 명시한다. 아래 절에 실제 실패 사례가 있다.

#### v5.1.0 순서 위험 — `record-readiness` 가 거부됐다

라운드 2 readiness 결과를 `quality_state.py record-readiness` 로 기록하려 했으나 **`error: spec artifact digest mismatch`** 로 거부됐다.

원인은 오케스트레이터의 호출 순서다. readiness 결과(대상 digest `9d47e4cd…`)를 받은 뒤 **먼저 보정 개정을 돌리고** Spec 을 재등록해 등록 digest 가 바뀐 상태에서 `record-readiness` 를 불렀다. 헬퍼는 `--artifact-digest` 가 현재 등록 digest 와 같기를 요구한다.

결과: 라운드 2 readiness 는 `state.json` 의 `readiness.spec` 에 남지 않는다. 결과 JSON 은 디스크에 있고 공식 리뷰 컨텍스트에 경로로 첨부됐으므로 판정 근거로는 살아 있다. 라운드 1 readiness 는 개정 전에 기록해 정상 반영됐다.

**정책 문언에 이 순서 요구가 없다.** readiness 는 "advisory 이며 상태 전이를 결정하지 않는다"고 정의돼 있어 개정 전에 기록해야 한다는 압력이 없는데, 헬퍼의 digest 가드는 사실상 그것을 강제한다.

#### 개정 노트 — author 가 형식을 두 번 어겼다

`revision_check.py` 가 라운드 2 개정 노트를 **종료 코드 1** 로 거부했다. 원인 둘.

1. 셋째 열은 **각 AC 마다** `(일치` 또는 `(모순` 괄호를 요구하는데 author 는 행마다 마지막 AC 에만 붙였다 → `missing_rows` 30건.
2. 추적표 `Judgement method` 열만 바뀐 요구사항 8건(`R2.3`·`R4.1`·`R4.2`·`R6.1`·`R6.5`·`R7.3`·`R9.1`·`R9.2`)의 행이 통째로 빠졌다.

오케스트레이터가 `revision_check.py` 가 생성한 `ripple[].acceptance_criteria` 를 그대로 순회해 셋째 열을 재생성하고, 빠진 8행을 diff 실측에 근거해 추가했다. 사용자 지시 "파급 열은 생성값만 쓰고 저자 기억으로 쓰지 마라"에 따른 처리이며 Spec 본문은 건드리지 않았다.

세 번째 반복에서 한 번 더 종료 코드 1이 났다 — 셋째 열 문구에 쓴 `A|B` 의 파이프가 마크다운 표 열을 6개로 쪼개 `R6.2` 행이 파싱에서 탈락했다. `A·B` 로 고쳐 종료 코드 0.

**관측:** `revision_check.py` 는 값을 했다. 세 번의 종료 코드 1이 전부 실제 누락·실제 파싱 실패였고 거짓 양성이 없었다. 다만 author 가 다섯 열 표 형식을 한 번에 맞추지 못했으므로, author 프롬프트에 "각 AC 마다 괄호" 와 "셀 안 파이프 금지" 를 명시해야 한다.

#### 대칭 점검 (사용자 지시로 추가한 세 번째 심사)

사용자가 "이 작업이 만들려는 이중 리뷰를 만들면서 스스로 쓰라"고 지시해, 별도 tmux 세션의 Codex(`gpt-5.6-sol`)에 읽기 전용 대칭 점검을 시켰다. 초점은 다섯 축(출처 대칭, 라운드 대칭, 동일 값·규칙의 문서 내 발산, 추적표 대조, 비목표 침범)이었다.

| 라운드 | 발견 | 쓰기 범위 위반 | 공식 리뷰와의 관계 |
|---|---|---|---|
| 1 | High 1 / Medium 3 / Low 1 | 없음 (Spec digest 불변) | High 1건이 공식 리뷰 `SPEC-004`와 **독립적으로 일치** |
| 2 | High 1 / Medium 2 | 없음 (Spec digest 불변) | 세 건 모두 공식 리뷰 제출 **전에** 닫아 라운드를 아꼈다 |

대칭 점검의 High는 "`R3.2`가 `finding_id`를 출처에서 파생하는데 `R6.2`가 종합자 입력에서 출처를 전부 제거하므로, 종합자가 `합의`와 `한 리뷰어의 중복 보고`를 구별할 수 없다"였다. 공식 리뷰가 같은 모순을 `SPEC-004`로 독립 지적했다.

**이 작업이 설계하려는 것(두 모델의 독립 리뷰 → 교차 확인)이 이 작업 자신의 Spec 심사에서 값을 했다.** 두 심사가 서로의 결과를 모른 채 같은 결함에 도달했고, 그 finding은 공식 리뷰의 네 blocker 중 하나가 됐다.

한편 readiness(100점, findings 0)와 대칭 점검(High 1)의 차이는 **범위 설계의 차이**다. readiness는 체크리스트 여덟 항목으로 좁혀져 있고, 대칭 점검은 오케스트레이터가 다섯 축을 지정했다. 같은 모델(`gpt-5.6-sol`)이 같은 문서를 보고 낸 결과다.

라운드 2의 대칭 점검은 초점을 사용자가 지정했다 — "추적표 각 행의 `Judgement method` 가 그 AC 본문 CMD 와 같은가"와 "프롬프트 구성이 실제 디스패치 경로와 묶였는가". 그 결과 세 건을 찾았다.

| # | 심각도 | 내용 | 처리 |
|---|---|---|---|
| 1 | **High** | `R2.1` 이 Claude 자유 서술에 `severity` 라벨을 요구만 하고 허용값·변환 규칙을 정하지 않음. 실측상 `code-reviewer.md:52` 는 `Critical`·`Important` 를, `silent-failure-hunter.md:104` 는 대문자 `CRITICAL`·`HIGH`·`MEDIUM` 을 쓰는데 정규 enum 은 소문자 넷이라 Claude finding 이 `R3.3` 에서 거부되고 `R8.2` 로 Claude 출처가 통째로 제외될 수 있었다 | 제출 전 변환표로 닫음 |
| 2 | Medium | `R9.3` 의 Python 소유권을 매핑 AC 가 판정하지 않음 | 제출 전 `AC-64` 보강으로 닫음 |
| 3 | Medium | 종료 사유 여덟 값에 배타성·우선순위가 없어 복수 사유가 동시 성립 | 제출 전 `R7.1` 전순서 우선순위로 닫음 |

**#1 은 라운드를 하나 태웠을 결함이다.** readiness 는 이것을 잡지 못했다 — 체크리스트에 "요구사항 간 값 도메인 정합"이 없고, 정책이 설계 정합성을 범위 밖으로 명시하므로 정책대로 동작한 것이다.

#### 이 실행이 만들려는 구조가 이 실행 자신에게 값을 했다

두 라운드에서 **서로의 결과를 모르는 두 심사**를 돌렸고, 두 번 다 값이 나왔다.

- 라운드 1: 6.1.2 대칭 점검과 공식 리뷰가 같은 모순(`R3.2` 출처 파생 ID ↔ `R6.2` 출처 제거)에 **독립적으로 도달**했다. 그 finding 이 네 blocker 중 하나가 됐다.
- 라운드 2: 대칭 점검이 공식 리뷰 **제출 전에** High 1건과 Medium 2건을 잡아 라운드를 아꼈다. 같은 라운드에서 공식 리뷰는 두 심사가 모두 놓친 `SPEC-012`·`SPEC-013` 을 새로 제기했다.

즉 **세 심사(readiness · 대칭 점검 · 공식 리뷰)의 발견 집합이 서로 포함 관계가 아니다.** 이슈 #42 가 설계 근거로 든 "finding 의 신뢰도는 교차 검증 생존 여부에서 나오고, 두 리뷰어가 불일치하는 지점이 가장 정보량이 큰 신호다"가 이 실행의 표본에서 재현됐다.

## Blocking-finding resolutions

| ID | 심각도 | 라운드 1 지적 | 적용한 해소 | 라운드 2 판정 |
|---|---|---|---|---|
| SPEC-001 | High | 추적표 11행의 판정 수단이 AC 본문 CMD와 불일치. `spec.md:256`의 봉합 문장이 `CMD-3`의 실제 `-k` 필터와 모순 | 36행을 AC 본문 CMD 합집합으로 재생성. 봉합 문장을 사실 진술로 교체 | **해소** (불일치 0행) |
| SPEC-002 | High | severity enum·confidence 범위 미정의. Claude 다섯 에이전트가 자유 서술 Markdown을 내는데 정규화 입력 계약이 없음 | `R3.1`에 enum `critical`·`high`·`medium`·`low`와 `finding_confidence` 0–1. `R2.1`에 대소문자 무시 완전 변환표(`Critical`→`critical`, `Important`→`high` 등)와 기본값·거부 규칙. `R5.1`·`R5.2`의 "신규 high 이상(critical 포함)" | **부분 해소** — `원문 ID` 조달 경로 부재가 `SPEC-012`로 분리됨 |
| SPEC-003 | High | 독립성 계약이 보존 산출물에 묶여 있지 않아 AC-13·14가 요구사항 재진술 | `R9.3`에 프롬프트 구성·문자열 보존·순서 게이트를 Python 책임으로. `R2.4`에 무변경 디스패치 계약. `R1.4`에 실제 프롬프트·시작 순서 보존. `AC-13`·`AC-14`를 보존 산출물 판정으로. `AC-64`가 Python 소유를 직접 판정 | **해소** (다섯 고리 연결) |
| SPEC-004 | High | 익명화와 종합 분류의 상호 모순. provenance sidecar 미정의 | 사용자 확정 방향(A/B 익명 그룹 라벨) — `R6.2`가 출처 제거 대신 `group: A|B` 치환 + 출처 중립 후보 논점 제공, `R6.3`이 run ID 시드로 A/B 배정·기록·교대, `R3.2`가 그룹 라벨에서 ID 파생, `R6.4`가 세 분류 도출 규칙과 `decision_confidence`, Interfaces가 `provenance.json` 정의, `R3.4`·`AC-71` 신설로 형식 누설 차단, `D2` 재작성·`D7` 신설 | **해소** |

### 라운드 2의 blocker — 여섯 번째 교차 회귀

`SPEC-012`(High)는 `new_blocker_evidence`를 갖는다. **라운드 2 개정이 만든 결함이다.**

`SPEC-002`를 닫으려고 `R2.1`에 Claude 라벨 계약을 신설했는데, 그 라벨 집합이 일곱 개(`severity`·`confidence`·`file`·`line`·`title`·`body`·`recommendation`)라 `R3.1`의 열 개 필수 필드 중 **`원문 ID`를 조달하지 못한다.** `R3.3`이 필수 필드 누락을 거부하므로 문언대로면 Claude finding이 전량 거부되고 `R8.2`로 Claude 출처가 통째로 제외돼 `single_reviewer`로 끝난다 — `SPEC-002`가 막으려던 실패 모드가 다른 필드로 되살아났다.

`new_blocker_evidence`: 라운드 1 판본(`snapshots/spec-r1.md:44`)의 `R2.1`에는 출력 라벨 계약 자체가 없었다. `R3.1`의 `원문 ID`와 `AC-15`의 "열 개 필드"는 라운드 1에도 있었으므로, 이 교차 불일치는 라운드 2가 라벨 집합을 신설하면서 비로소 생겼다.

이 작업에서 개별 해소가 교차 회귀를 만든 것은 이번이 **여섯 번째**다(PLAN-009·PLAN-010·PLAN-012·SPEC-31·SPEC-34·35·SPEC-012).

**다만 이전 다섯과 다른 점이 있다.** 앞선 다섯은 전부 마지막 라운드에서 터져 종결 사유가 됐다. 이번은 **라운드 2에서 잡혀 한 라운드가 남았다.** 규모를 66·86에서 36·71로 줄인 효과로 읽는다.

## Implementation and code review

사용자가 Plan 을 승인했다. 승인 범위는 **구현·독립 검증·공식 Code 리뷰까지**이며 commit/push/PR/merge/`chezmoi apply` 는 포함하지 않는다.

### 구현·수정 라운드

| 단계 | 산출 | 판정 명령 | 독립 점검 |
|---|---|---|---|
| 구현 r1 | 17파일, `review_state.py` 287행, 테스트 24 | **12/12 exit 0** | 6.1.2 가 **13건(High 8)** — "Plan 을 수행하지 못한다" |
| 수정 r2 | 445행, 테스트 35 | 12/12 exit 0 | 6.1.2 재점검이 "13건 전부 닫음" 주장을 **뒤집고** 새 High 4건 추가 |
| 수정 r3 | 628행, 테스트 46 | 12/12 exit 0 | 공식 리뷰가 14건 닫힘 확인, `CODE-15` 실질 해소 |
| 수정 r4 | 629행, 테스트 57 | 12/12 exit 0 | 공식 리뷰 라운드 1의 blocker 4건 + Medium 3건 대응 |
| 수정 r5 | 테스트 58 → 63 | 12/12 exit 0 | 오케스트레이터 변이 점검이 찾은 **테스트 공백 3건** 보강 |
| 수정 r6 | 6파일 수정 | 12/12 exit 0 | 3차 6.1.2 diff 점검의 `CODE-R3-01`~`05` 대응, `plan_deviations` 없음 |
| 수정 r7 | 6파일, 테스트 63 → **72** | 12/12 exit 0 | 4차 diff 점검의 `CODE-R4-02`~`06` 대응. `CODE-R4-01` 은 반박·미수정 |
| 수정 r8 | 3파일 | 12/12 exit 0 | 5차 diff 점검의 `CODE-R5-01`~`03` 대응. High 0, D7 유지 확인 |
| 수정 r9 | 6파일, 테스트 72 → 79 | 12/12 exit 0 | 공식 리뷰 r2 의 `CODE-27`~`31` 대응 + 오케스트레이터가 0건 파싱 검사와 마스크 복원 테스트를 추가 |
| 수정 r10 | 오케스트레이터 직접, 테스트 79 → **83** | 12/12 exit 0 | 6차 diff 점검의 `CODE-R6-01` 대응 — A/B 복원의 두 누락 경로 |

### 공식 라운드 2 직전 상태

- 전체 스위트 **83 테스트 OK**, 판정 명령 **12/12 exit 0** (`command-transcript-r3.txt`)
- 변이 자기점검 누적 **39개 경계 전부 잡힘, 놓친 변이 0** (r6 15 + r7 6 + r8 5 + r9 7 + r10 6)
- 무관 변경 1건(`AGENTS.md`) 회수
- 독립 점검 4차의 High 1건(`CODE-R4-01`)을 **반박**하고 나머지 다섯을 닫음
- 독립 점검 5차: High **0**, D7 자율성 완전 유지 확인. Medium 1·Low 2 를 r8 에서 닫음

### 공식 라운드 2 — 88점 REVISE 의 원인은 결함이 아니라 검증 불가

| 라운드 | 점수 | verdict | blockers | 게이트 |
|---|---|---|---|---|
| 1 | 68 | REVISE | 4 (High) | 실패 — `verdict_not_pass`·`blockers_present`·`critical_or_high_finding`·`check_failed:acceptance_criteria_met`·`check_failed:documentation_current` |
| 2 | 88 | REVISE | 0 | 실패 — **`verdict_not_pass` 단 하나** |
| 3 | **93** | **PASS** | **0** | **통과 — `passed: true`, 사유 없음** |

라운드 2 는 라운드 1 의 High 4건과 advisory 7건을 **전부 해소** 로 판정했고, 수정이 만든 회귀는
없다고 확인했으며, `CODE-R4-01` 기각도 지지했다. 그런데도 PASS 가 아니었다. 리뷰어의
`required_next_action` 이 이유를 명시한다 — **리뷰어 에이전트에 명령 실행 도구가 없어**
CMD-1·2·3·6~12 열 개를 리뷰 대상 트리 상태에서 실행하지 못했고, 따라서
`required_commands_passed` 를 확인할 수 없어 PASS 를 낼 수 없었다.

**이것은 `no-PASS-when-unverified` 가 설계대로 작동한 것이다.** 리뷰어는 오케스트레이터가 준
검증 기록을 읽었지만 "읽는 것은 실행이 아니다" 라고 명시하며 `verified: false` 로 남겼다.
`quality-reviewer` 에이전트의 도구가 `Read, Grep, Glob` 뿐이라는 구조적 사실이 원인이다.

라운드 3 대응: 최종 트리 상태에서 열두 명령을 전부 실행하고 **명령 문자열과 종료 코드가 보이는
전사** 를 저장소 근거로 첨부했다(`command-transcript-r3.txt`). 명령 문자열은 `plan.md:218-229`
에서 정규식으로 기계 추출했고, 전사에 구현 트리 다이제스트를 실행 전후로 적어 리뷰 대상 상태와
같음과 명령이 대상을 바꾸지 않았음을 함께 보였다.

**이 대응이 통했다.** 라운드 3 리뷰어는 명령을 실행하지 못하는 같은 제약 아래에서도, 읽어서
실제로 할 수 있는 검사를 수행해 `required_commands_passed` 를 `verified: true` 로 확정했다 —
열두 명령 문자열을 Plan·Spec 표와 문자 단위 대조(전부 일치), 기록된 테스트 수를 자신이 센
테스트 메서드 수와 대조(83 = 30+15+11+9+8+7+3), 각 `-k` 필터가 고르는 메서드 수와 대조(CMD-6 이
2개인 것까지), CMD-4·CMD-5 는 **자신의 내용 검색으로 직접 재현**. 실행 전후 다이제스트 동일과
`__pycache__` 0 도 확인했다.

교훈: 도구가 없어 **실행** 하지 못하는 것과 **판정** 하지 못하는 것은 다르다. 실행 증거를 검사
가능한 형태로 주면 리뷰어가 판정할 수 있다. 명령 문자열을 손으로 옮겨 적지 않고 Plan 에서 기계
추출한 것, 다이제스트를 실행 전후로 남긴 것이 그 검사 가능성을 만들었다.

이 사실 자체가 `quality-goal` 후속 과제다 — **리뷰어에게 판정 명령 실행 능력이 없으면
`required_commands_passed` 는 구조적으로 영원히 `verified: false` 다.**

### 라운드 2 가 답한 오케스트레이터의 열린 질문

오케스트레이터가 `OBS-1` 로 "최종 보고서에서 출처 복원이 `Findings` 절에만 적용되고
`Synthesis`·`두 리뷰어가 갈린 지점` 은 익명 `A=`/`B=` 로 남는다. 의도된 표기인가 은닉 계약의
잔재인가" 를 리뷰어에게 판정 요청했다.

리뷰어 답변: **잔재다.** 원인은 그 절들이 의도적으로 익명으로 남겨진 것이 아니라, 보고서 state
전체가 마스킹된 종합자 view 에서 만들어지기 때문이다(`CODE-27`). 그래서 정당하게 금지 토큰을
포함한 본문까지 `<redacted:…>` 마커로 최종 산출물에 찍힌다. 다만 `AC-47`·`AC-48` 은 문언상
충족되므로 blocker 가 아니라 Medium 이다.

r9 에서 닫았다 — 보고서를 마스킹되지 않은 정규 finding 에서 렌더링하고, sidecar 의 `masks` 로
종합자가 되돌려준 문자열을 복원하며, `source_groups` 역매핑으로 `A`/`B` 를 실제 리뷰어명으로
바꾼다. 종합자 **입력** 은 그대로 마스킹이다.

오케스트레이터의 변이 점검이 이 수정에서 **경계 하나를 놓쳤다** — 마스크 복원(`restore()`)을
제거해도 79 테스트가 통과했다. 기존 fixture 의 종합자가 마스킹 토큰을 되돌려주지 않았기 때문이다.
종합자가 마스킹된 본문을 그대로 인용하는 fixture 를 추가해 닫았다. `r5` 의 정렬 키 사례와 같은
계열이다 — **테스트가 옳고 픽스처가 약해서 놓치는 경우.**

### 6차 점검 — CODE-27 수정이 익명화를 깨뜨렸는가

라운드 3 직전 점검을 **단일 초점**으로 좁혔다: `CODE-27` 수정(보고서를 익명 view 가 아니라
정규 finding 에서 렌더링)이 은닉 계약 자체를 훼손했는지.

| 초점 | 판정 |
|---|---|
| 종합자 입력의 다섯 생산자명·원문 ID·sidecar 키·root 세 개 | **PASS** — 네 항목 전부 |
| 실제 종합자 프롬프트 | **PASS** — `contract` 와 `anonymous_view` 뿐 |
| 복원 경로가 sidecar 만 쓰는가 | **PASS** — 원래 `source` 필드를 직접 읽지 않음 |
| D7 유지 | **PASS** |

발견 `CODE-R6-01`(Medium) 하나. 복원이 두 경로에서 불완전했다.

1. **두 리뷰어 모두 유효한데 한쪽 finding 이 0건인 정상 실행.** `build_anonymous_view()` 가
   findings 의 출처에서만 `source_groups` 를 만들어 빈 그룹의 역매핑이 없고, 렌더러가 그룹
   문자로 fallback 해 최종 보고서에 맨 `A=` 가 남는다. 오케스트레이터가 재현했다 —
   `source_groups = {'claude': 'B'}` 로 codex 항목이 아예 없었다.
2. **종합자가 rationale·claims 자유 문자열 안에 `A=`/`B=` 를 직접 쓴 경우.** 마스크 복원과
   구조 키 변환을 둘 다 통과해 그대로 남는다.

r10 에서 오케스트레이터가 직접 닫았다 — 라운드 0 이 만든 **완전한** group map 을 sidecar 에
보존하고, 렌더러는 그룹 문자 fallback 을 **허용하지 않고 예외를 던지며**(맨 라벨이 산출물에
남는 것은 익명화 누설이지 미관 문제가 아니다), 표시 문자열의 맨 `A=`/`B=` 토큰을 sidecar map 으로
치환한다. **classification 의미는 판정하지 않는다** — D7 경계를 넘지 않는 표시 계층 치환이다.

### 독립 점검 5회의 수렴

| 회차 | 시점 | High | Medium | Low | 처리 |
|---|---|---|---|---|---|
| 1차 | 구현 r1 | 8 | — | — | 13건 전부 r2 에서 |
| 2차 | 수정 r2 | 4 | — | — | r1 "전부 닫음" 주장을 뒤집음 |
| 3차 | 수정 r5 | 3 | 2 | — | r6 |
| 4차 | 수정 r6 | 2 | 4 | — | High 1 **반박**, 나머지 r7 |
| 5차 | 수정 r7 | **0** | 1 | 2 | r8 |

High 가 8 → 4 → 3 → 2 → 0 으로 단조 감소했다. 이 스킬이 만들려는 종료 규칙
(`두 라운드 연속 high 0`)의 근거가 되는 곡선이며, `#29` 실측이 말한 "1라운드 조용은 신호가
아니다" 도 이 실행에서 확인됐다 — 2차 점검이 1차의 "13건 전부 닫음" 주장을 뒤집었다.

### 변이 자기점검 — 테스트가 실제로 결함을 잡는가

사용자 지시로 각 수정 경계마다 코드를 한 곳 고쳐 스위트가 실제로 실패하는지 확인하고 복구했다.
15개 경계 전부에서 실패가 발생했다(상세는 `verification-r6.md`).

이 점검이 **r5 를 만들어냈다**. r4 시점의 58 테스트는 전부 통과했지만, 변이를 걸어보니 세 곳이
결함을 통과시켰다:

| 변이 | 왜 안 잡혔나 |
|---|---|
| `PUBLIC_FINDING_FIELDS` 에 실제 `source` 재추가 | 노출 금지 필드를 열거로만 검사하고 실제 산출물을 훑지 않았다 |
| 사이드카에서 `original_id` 삭제 | 복원 경로를 단언하는 테스트가 없었다 |
| 마스크 정렬 키 `(-len, token)` → `len` 되돌리기 | `test_mask_sidecar_is_byte_stable_across_hash_seeds` 는 **옳은 성질을 검사하고 있었으나** 픽스처(`comment-analyzer` 17자·`pr-test-analyzer` 16자)에 동길이 토큰이 없어 결함을 드러낼 수 없었다 |

세 번째가 특히 기록할 값이 있다. **테스트가 옳고 픽스처가 약해서 놓친 경우**로, 스위트 통과·
커버리지 어느 신호로도 보이지 않는다. 변이 점검만이 드러냈다.

### 4차 독립 점검 — 오케스트레이터가 반박한 finding 1건

4차 6.1.2 점검은 High 2건·Medium 4건을 냈다. 그중 `CODE-R4-01` 은 **반박했다.**

점검의 주장: 익명 view 의 금지 토큰 집합에 실제 `source`("claude"/"codex")와 모델명 alias 를
넣고 대소문자 무시로 치환해야 한다.

반박 근거 둘:

1. **Spec 이 범위를 명시 한정했다.** `AC-37`(`spec.md:136`)은 문자열 불변식을 "다섯 생산자
   에이전트명과 원문 ID의 평문 부분 문자열이 각각 0건" 으로 **열거**한다. 실제 `source` 는
   필드 제거 대상이고, 구현은 `source` 필드를 `group` 으로 치환해 이를 충족한다.
2. **제안된 해소가 산출물을 파괴한다.** 이 스킬의 대상 경로가 `dot_claude/skills/dual-review/…`
   다. "claude" 를 대소문자 무시로 치환하면 모든 finding 의 `file` 값이
   `dot_<redacted:…>/skills/…` 가 되어 종합자가 파일을 식별할 수 없다. 익명화를 얻으려다
   후보 논점 판단의 근거를 없앤다.

이 반박 자체가 이 스킬이 만들려는 규율의 실사용 사례다 — **반증은 코드·소스 실측으로 제시**
(`#29`). 상대 리뷰어의 High 를 문서 인용과 저장소 사실로 기각했고, 기각 사실을 버리지 않고
남겼다.

나머지 다섯(`CODE-R4-02`~`06`)은 실재를 직접 확인하고 fix 라운드 r7 에 넣었다.

| ID | 심각도 | 위반 | 오케스트레이터 재현 |
|---|---|---|---|
| `CODE-R4-02` | Medium | `R6.3` — `assign_anonymous_groups()` 가 `run_id` 를 읽지 않고 `execution_number % 2` 로만 배정 | 확인 (`review_state.py:181-185`) |
| `CODE-R4-03` | Medium | `R6.4` 의미 규칙이 fresh Claude 입력에 없음 | 확인 |
| `CODE-R4-04` | Medium | `R1.1` — `snapshot_from_repository()` 가 인자 해석 전에 무조건 `HEAD^` resolve | 확인 (`review_state.py:632`) |
| `CODE-R4-05` | **High** | 다섯 변이가 63 테스트를 통과 — self-critique 방향, `two_quiet_rounds` 후보, JSON `result` fallback, path guard, snapshot | 점검이 메모리 변이로 실측 |
| `CODE-R4-06` | Medium | `R4.4` — 반복 등장 finding 의 provenance 가 `update` 로 덮임 | 확인 |

`CODE-R4-05` 는 **오케스트레이터의 15개 변이 목록과 겹치지 않는 경계**에서 나왔다. 변이 점검을
했다는 사실이 변이 점검의 완전성을 뜻하지 않는다는 표본이다.

### 무관 변경 1건 — Codex 가 만든 `AGENTS.md`

Codex 라운드 중 워크트리 루트에 `AGENTS.md` 가 생겼다. `CLAUDE.md` 를 `Claude`→`Codex` 로
기계 치환한 것으로 `~/.Codex/skills/`·`Codex.ai/code`·`run_once_install-Codex-plugins.sh.tmpl`
같은 실재하지 않는 경로를 만들어냈다. Plan 어느 태스크의 산출물도 아니고 사실도 아니므로
워크트리 밖으로 회수했다.

`git status` 대조를 하지 않았다면 `unrelated_changes_absent` 게이트에서야 드러났을 것이다.
Codex 가 지시받지 않은 리포지터리 루트 파일을 만들 수 있다는 표본이다.

### 이 실행의 가장 큰 관측 — 판정 명령 통과가 구현을 보증하지 않았다

**구현 r1 에서 Plan 이 정한 판정 명령 12개가 전부 종료 코드 0 이었는데, 독립 점검은 "T3~T8 의 실제 이중 리뷰→교차 비평→익명 종합→완전 보고서 경로가 연결되지 않았다"고 판정했다.** 테스트가 공허해서 미구현을 가리고 있었다.

이슈 `#70` 구현에서 같은 점검이 공허 테스트 19개를 잡았던 것과 같은 계열이다. 사용자가 "각 라운드 제출 전에 6.1.2 에 diff 를 읽기 전용으로 넘겨라"를 지시하지 않았다면 그 상태로 공식 라운드를 태웠을 것이다.

### 공식 Code 리뷰

| 라운드 | 점수 | verdict | blockers | 처리 |
|---|---|---|---|---|
| 1 | **68** | REVISE | CODE-01·CODE-12·CODE-18·CODE-19 | `record-review` — 라운드 1 소비 |
| 2 | 대기 | — | — | — |

게이트 실패 사유: `verdict_not_pass`·`blockers_present`·`critical_or_high_finding`·`check_failed:acceptance_criteria_met`·`check_failed:documentation_current`.

### 오케스트레이터가 독립 재현한 결함

Codex 보고를 근거로 삼지 않고 직접 실행해 확인한 것들이다.

| ID | 재현 내용 | 상태 |
|---|---|---|
| `CODE-05` | 다섯 생산자가 서로 다른 `source` → A·B 로 찢어짐. "합의" 가 Claude 두 에이전트끼리의 합의가 될 수 있었다 | 해소 확인 (`['claude']` 통합, 두 그룹) |
| `CODE-13` | `test_no_mutation_contract` 가 스킬 트리 전체를 `read_text()` 로 읽어 `.pyc` 하나에 `UnicodeDecodeError`. `PYTHONDONTWRITEBYTECODE=1` 없이 Python 1회 실행이면 재현 | 해소 확인 |
| `CODE-16` | `CLAUDE_PRODUCERS` 가 다섯 모두 접두어. Spec `R2.1` 은 첫째만 접두어 | 해소 확인 — 문자 단위 일치 |
| `CODE-17` | 마스킹 정렬이 `key=len` 이라 동길이 토큰 순서가 set 순회 의존 | 해소 확인 — `(-len, token)` |
| `CODE-02` | `make_run_id(…,1)` 이 재실행에서 동일 ID | 해소 확인 — `max(existing)+1` |
| `CODE-01` | 리뷰어가 "미지원 플래그일 수 있다"고 우려 | **실측으로 반박** — `claude` 2.1.263 에서 여섯 플래그 전부 `--help` 에 실재. `codex exec` 도 stdin 프롬프트를 지원(`[PROMPT]` 생략 시 "instructions are read from stdin"). 다만 **문서화·검증 부재**라는 리뷰어의 요구는 유효 |

### 오케스트레이터의 검증이 놓친 것 — 기록해 둔다

라운드 1에서 익명화를 "성립한다"고 보고했으나 그 검증은 `source: "claude"/"codex"` 를 **손으로 넣어** 호출한 것이었다. 실제 파이프라인은 생산자명을 `source` 로 쓰고 있었고 다섯 생산자가 A·B 로 찢어졌다.

**단위를 오케스트레이터가 기대한 계약으로 검사했지 파이프라인이 실제로 만드는 데이터로 검사하지 않았다.** 이 실행에서 오케스트레이터 자신의 가장 큰 검증 결함이다.

### 오케스트레이터의 지시가 만든 결함

`CODE-18`(High)은 **오케스트레이터의 수정 지시가 과했던 결과**다. `CODE-07`(synthesis coverage 미검증)을 닫으라며 "각 결정이 하나의 candidate 에 대응함을 단정하라"고 썼는데, 그것이 Spec `D7` 이 종합자에게 남긴 "같은 결함인가" 판단을 코드가 빼앗는 구현을 낳았다. 정당한 불일치가 `reviewer_failure` 로 바뀐다.

사용자가 Spec 단계에서 `D7` 로 못박은 것("합의 판정을 기계 매칭으로 옮기지 않는다, 판단은 종합자에게 남기고 정보만 정확히 준다")을 구현 지시에서 오케스트레이터가 되돌린 셈이다.

## Plan approval

- Approval timestamp: **2026-09-08T01:11:07Z** — 사용자 승인, `approve-plan` 기록 완료
- Plan digest: `60428b5f4090aca82dd1148b6bf2f5789130915cbd65d104c22e58709f48ba88` (통과 리뷰가 기록한 digest와 동일)
- Spec digest: `9962ce1beea4f16bd62f62d918d5538d2eb4c7686d25faf9f346b092bcd95e5f`

승인 후 `approve-plan` 으로 digest 를 기록하고 `IMPLEMENTING` 으로 전이한다. 승인 전에는 소스를 변경하지 않는다.

## Changed files

| 파일 | 변경 |
|---|---|
| `docs/development/2026-09-07-42-dual-review-stage1/spec.md` | 신규. Codex author 작성·개정. 라운드 1 판본 282행 → 라운드 2 판본 289행 (요구사항 35→36, AC 70→71) |
| `docs/development/2026-09-07-42-dual-review-stage1/spec-revision-notes.md` | 신규. `## 라운드 2 개정` 다섯 열 표 27행. 셋째 열은 `revision_check.py` 생성 파급표를 전사 |
| `docs/development/2026-09-07-42-dual-review-stage1/report.md` | 신규. 이 보고서 |

| `docs/development/2026-09-07-42-dual-review-stage1/verification-r6.md` | 신규. r6 독립 검증 — AC 식별자 전수 대조, `AGENTS.md` 회수 |
| `docs/development/2026-09-07-42-dual-review-stage1/verification-r7.md` | 신규. r7 독립 검증 — 워치독 결함 실측 |
| `docs/development/2026-09-07-42-dual-review-stage1/verification-r8.md` | 신규. r8 독립 검증 — A/B 교대 수정 전후 실측 |
| `docs/development/2026-09-07-42-dual-review-stage1/command-transcript-r3.txt` | 신규. 판정 명령 12개 실행 전사 (공식 라운드 3 근거) |
| `dot_claude/skills/dual-review/` | 신규 17파일. `SKILL.md` 1, `references/` 2, `schemas/` 3, `scripts/review_state.py`, `templates/report.md` 1, `tests/` 6 (**83 테스트**), `.gitkeep` 2 |

커밋·머지·PR 생성·`chezmoi apply`를 수행하지 않았다. `.gitignore`는 변경되지 않았다. 다른 워크트리와 전역 배포본을 건드리지 않았다.

Codex 가 워크트리 루트에 만든 `AGENTS.md` 는 Plan 산출물이 아니므로 회수했다(위 참조).

초기 dirty 경로 둘(`.codex-author/`, `.codex-readiness/`)은 바이트 단위로 보존했고 이 작업의 변경에 포함하지 않았다.

## Verification evidence

| 명령 | 종료 코드 | 증거 |
|---|---|---|
| `grep '^version:' ~/.claude/skills/quality-goal/SKILL.md` | 0 | `5.1.0` |
| `codex --version` | 0 | `codex-cli 0.153.4` |
| `codex exec --sandbox read-only --model gpt-5.6-terra` (preflight) | 0 | 응답 `Acknowledged.` |
| `git check-ignore -v .claude/quality-state/` | 0 | `.gitignore:25` |
| `git check-ignore .codex-author/ .codex-readiness/` | 1 | **무시되지 않음** — follow-up |
| `quality_state.py capture-baseline` | 0 | `base_revision=7678ebf086bf845ef7b39e17c755239c601d498e`, dirty 2건 |
| Codex author 라운드 1 (초안) | 0 | 605.5초, `changed_files` 1건, 쓰기 범위 준수 |
| Codex author 라운드 2 (개정) | 0 | 635.4초, `changed_files` 2건, 쓰기 범위 준수 |
| Codex author 라운드 2 보정 개정 | 0 | 400.5초, `changed_files` 2건, 쓰기 범위 준수 |
| Codex readiness 라운드 1 | 0 | 215.2초, **100 READY**, findings 0, digest 일치 |
| Codex readiness 라운드 2 | 0 | 400.3초, **95 REVISE**, `READY-001` Medium 1건, C8 fail, digest 일치 |
| `quality_state.py record-readiness` (r1) | 0 | `readiness.spec[0]` 기록됨 |
| `quality_state.py record-readiness` (r2) | 2 | **`spec artifact digest mismatch`** — 개정 후 호출한 순서 오류. 결과 JSON은 디스크 보존 |
| Codex 대칭 점검 (tmux, read-only) ×2 | — | r1: High 1/Medium 3/Low 1. r2: High 1/Medium 2. 두 번 다 Spec digest 불변 |
| `revision_check.py` 라운드 1 | 0 | `empty_cells: 0`, `passed: true` (노트 면제) |
| `revision_check.py` 라운드 2 | 1 → 1 → **0** | 1차 `missing_rows` 30건, 2차 `A\|B` 파이프로 `R6.2` 행 탈락, 3차 `passed: true`, `touched_requirements` 27건 |
| Spec 구조 자체 파싱 (r1) | — | 필수 절 13개·순서 단조, 요구사항 35, AC 1~70 결번 0, 판정 수단 정확히 1개씩, strict 마커 0 |
| 추적표 판정 수단 전수 대조 (r1) | — | **35행 중 11행 불일치** — `SPEC-001`의 근거 |
| Spec 구조 자체 파싱 (r2) | — | 요구사항 36, AC 1~71 결번 0, 결정 7, CMD 미사용 0·미등재 0 |
| 추적표 판정 수단 전수 대조 (r2) | — | **36행 중 0행 불일치** — `SPEC-001` 해소 확인 |
| 종료 사유 enum 커버리지 대조 (r2) | — | 여덟 값 각각이 `R7.1`에 열거되고 발생 조건 요구사항에 대응 |
| `rg` 종료 코드 실측 | — | 매치 0 / 무매치 1 / **경로 부재 2**. 옛 관용구 `if rg …; then exit 1; fi`는 경로 부재에서 **0으로 공허 통과** — `SPEC-006(2)` 확인 |
| `unittest discover -k` 0건 일치 | 5 | 공허 통과 아님 |
| `chezmoi source-path` | 0 | `/Users/lee-kyu-hwan/code/dotfiles`. 워크트리 경로는 `--source "$PWD"` 없이 `not in …`으로 실패 — `SPEC-005`의 근거 |
| `validate_review.py validate` (r1·r2) | 0 | 두 번 모두 `{"valid":true,"errors":[]}` |
| `validate_review.py gate` (r1·r2) | 3 | 두 번 모두 `passed:false` |
| `quality_state.py record-review` (r1) | 0 | `rounds.spec=1`, 스냅샷 `spec-r1.md` digest 일치 |
| `quality_state.py record-review --revision-check` (r2) | 0 | `rounds.spec=2`, `revision_checks.spec` 1건, 스냅샷 `spec-r2.md` digest 일치 |

### 구현 이후 검증

| 항목 | 결과 | 증거 |
|---|---|---|
| 단위 테스트 | **83 tests OK** | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'` |
| 판정 명령 CMD-1~12 | **12/12 exit 0** | `command-transcript-r3.txt` — 명령 문자열과 종료 코드 전사, 실행 전후 구현 트리 다이제스트 동일 |
| 금지 옵션 스캔 (CMD-4) | exit 0 (무매치) | 자기 문서 오탐 없음 — 우회 표기가 `references/verification.md:23-24` 에만 존재 |
| GitHub 쓰기 명령 스캔 (CMD-5) | exit 0 (무매치) | `gh pr review`·`gh pr comment`·`gh api` 부재 |
| 변이 자기점검 | **39/39 잡힘** (누적) | `verification-r6.md`·`verification-r7.md`·`verification-r8.md` |
| 무관 변경 대조 | 1건 발견·회수 | Codex 생성 `AGENTS.md` |
| `quality_state.py record-verification` | 0 | 라운드마다 재기록. 최종 지문은 `state.json` 의 `verification` 참조 |
| 타입 체크·린트·빌드 | **not configured** | 저장소 루트에 `tsconfig.json`·`pyproject.toml`·`Makefile`·`package.json`·린터 설정이 없다 |
| E2E (실제 CLI 왕복) | **미실행** | 로컬에서 Claude·Codex 를 실제로 기동하는 경로는 Spec 이 요구하지 않았고, 계약 테스트는 주입 어댑터로 대체한다. 3차 대칭 점검이 지적한 live 경로 결함은 `CODE-R3-01`·`02` 로 처리했다 |

## Remaining advisory findings

### Spec 라운드 2 잔여 셋 — 라운드 3 에서 전부 해소됨

기록 목적으로 남긴다.

| ID | 심각도 | 내용 | 해소 방향 |
|---|---|---|---|
| SPEC-012 | **High** (blocker) | `R2.1`의 Claude 라벨 계약이 `R3.1`의 필수 필드 `원문 ID`를 조달하지 못해 `AC-15`와 `AC-16`이 상호 충족 불가 | 사용자 확정 — 어댑터가 생산자 에이전트명 + 출력 내 순번으로 결정적 부여. 파싱 순서를 "출력 문서 순서"로 명시하고, `원문 ID`가 사실상 출처 필드이므로 `R6.2`의 익명화 대상에 넣거나 불투명 값으로 치환 |
| SPEC-013 | Medium | 변환표 밖 명시 severity 의 처리가 레코드 단위 거부(`R2.1`·`R3.3`·Security)와 출처 단위 제외(Interfaces `spec.md:228`)로 갈림 | Interfaces를 레코드 단위 거부로 맞추고 `R8.2` 발동 경계를 한 구절로 확정 |
| SPEC-014 | Low | `run root`가 정의되지 않아 `.gitignore` 위치가 두 갈래 | `.claude/dual-review-state/` 루트로 확정하고 `AC-5`·Security 표기 정렬 |

라운드 1의 Medium 4건·Low 3건(`SPEC-005`~`SPEC-011`)은 라운드 2에서 전부 해소 확인됐다.
셋 모두 라운드 3 판본에서 닫혔고 리뷰어가 PASS 로 확인했다.

## 운영 관측 — 이 실행이 인프라 원인으로 세 번 죽었다

작업 내용과 무관하게 오케스트레이터 턴이 세 번 중단됐다. 셋 다 재개 가능했고 라운드 손실은 0 이었지만, 원인과 회복 방식이 서로 다르다.

| # | 원인 | 증상 | 손실 | 회복 |
|---|---|---|---|---|
| 1 | **사용량 한도 도달** | 턴이 끊기고 이후 요청 거부 | 없음 | 한도 재설정 후 상태 파일에서 이어감 |
| 2 | **DNS 오류 (`ENOTFOUND`)** | 턴이 죽고 약 2시간 유휴 | 없음 | 상태 확인 후 이어감. 다만 유휴 중 Codex author 재기동을 못 해 시간이 버려짐 |
| 3 | **컴퓨터 절전** (`Your computer went to sleep mid-response`) | 응답 도중 턴 종료 | 없음 | 상태 확인 후 이어감 |

세 경우 모두 **`state.json` 이 진실의 원천 역할을 했다.** 재개할 때마다 `stage`·`rounds`·`open_finding_ids`·산출물 digest 를 읽어 어디까지 갔는지 확정할 수 있었고, 대화 기억에 의존하지 않았다. 산출물 digest 대조로 "중단 사이에 파일이 바뀌지 않았다"를 매번 확인했다.

**3번(절전)은 이 작업에서 처음 본 실패 모드다.** 1·2번과 달리 로컬 머신 상태가 원인이라 재시도로 예방되지 않는다.

### 이 실행에서 관측한 다른 중단 둘 — 인프라가 아니다

위 셋과 구별해 기록한다. 둘 다 오케스트레이터 자신의 문제였다.

| 사건 | 실제 원인 |
|---|---|
| Plan author 라운드 2 가 결과 파일 없이 끝남 | **오케스트레이터의 의도적 회수.** 프롬프트 작성 21:16:11, events 마지막 21:16:23 — 12초 런타임. 사용자 추가 지시가 프롬프트에 빠져 `TaskStop`+`pkill` 로 회수했다. Codex 실패가 아니므로 `#49-C` RESULT_INVALID 표본으로 쓰면 안 된다 |
| 그 직후 재기동이 `elapsed_s: 0.0` 에 `events_stale` 로 즉사 | **오케스트레이터 워치독의 경쟁 조건 버그.** 이전 실행이 남긴 events 파일의 2시간 전 mtime 을 첫 루프에서 읽어 `now - last > 480` 이 즉시 참이 됐다. `sh` 가 리다이렉트로 파일을 새로 만들기 전에 검사한 것이다 |

워치독은 고쳤다 — 시작 전 events 파일 제거, 60초 grace 구간, 파일 부재 시 프로세스 시작 시각 기준. 2시간 전 mtime 잔재가 있는 상태로 자체 검증해 정상 완료를 확인했다.

### Plan 리뷰어 에이전트 스톨

공식 Plan 리뷰 라운드 2 의 첫 기동이 **600초 무진행으로 스톨**했다(`stream watchdog did not recover`). 출력은 `I'll start by reading the rubric, schema, and the artifact.` 한 줄뿐이었다.

`record-review` 를 부르기 전이었으므로 **라운드는 소비되지 않았다**(`rounds.plan` 1/2 유지, `review_validation_retry` 미사용, Plan digest 불변). 리뷰어 출력이 무효였던 것이 아니라 스트림이 죽은 것이므로 `record-review-error` 의 재시도 카운터를 쓰지 않고 같은 계약 입력으로 새 에이전트를 기동했다.

이것은 스킬의 세 복구 경로(`REVIEW_OUTPUT_INVALID`, `REVIEWER_UNVERIFIED_PERSISTS`, `BLOCKED_REVIEWER_MODEL_UNAVAILABLE`) 중 어디에도 정확히 해당하지 않는다. 모델은 응답했고 출력은 무효가 아니라 **없었다**. `SKILL.md` 에 "리뷰어 스트림이 결과 없이 죽으면 라운드를 소비하지 않고 재기동한다"를 명시하면 이 경로가 닫힌다.

## Follow-up

- `.codex-readiness/`와 `.codex-author/`가 이 저장소에서 무시되지 않는다. `git status`에 노출되고 실수로 커밋될 수 있다. `.gitignore`는 승인 범위 밖이라 이 워크플로에서 고치지 않았다.
- `quality-goal` `SKILL.md`의 Codex invocation contract에 "결과는 `--output-last-message` 파일에서만 읽고 events 스트림의 중간 `agent_message`를 결과로 읽지 않는다"를 명시할 것. 이 실행에서 오케스트레이터가 실제로 오판했다.
- readiness 체크리스트에 "추적표 판정 수단 == AC 본문 판정 수단" 대조를 추가하는 것을 이슈 `#70`에서 검토할 것. 이번 라운드에서 그 부재가 High 1건을 통과시켰다.

## Final status

- Status: **`COMPLETED`**
- Machine-readable reason: 없음
- 최종 리뷰: 라운드 3, 점수 **93**, verdict **PASS**, blockers 0, 게이트 `passed: true`
- 워크스페이스 지문: `72062a6d44a05a947244ab45dfa96bf47bf374774657ccab14c6c171d1347a99`

남은 advisory 2건은 blocker 가 아니며 어떤 AC 도 위반하지 않는다.

| ID | 심각도 | 내용 |
|---|---|---|
| `CODE-32` | Medium | 0건 파싱 차단이 **진짜로 깨끗한** Claude 리뷰와 수집 실패를 구별하지 못한다. 프롬프트에 빈 결과 선언 수단이 없어 다섯 생산자가 모두 아무것도 못 찾으면 `single_reviewer` 로 끝난다. fail-closed 방향이라 거짓 성공이 아니라 보수적 축소 보고이며 원문은 `raw-<producer>.json` 에 보존된다 |
| `CODE-33` | Low | `A=`/`B=` 치환이 등호 토큰 문법에만 걸린다. `"Group A reports…"` 같은 산문 참조는 남고, `A = 1` 같은 코드 인용은 잘못 치환된다 |

둘 다 2단계 또는 후속 이슈에서 다룰 항목이다.

**Spec 과 Plan 이 모두 통과했다. 다섯 번의 시도에서 처음이다.**

| 실행 | 종료 사유 | 도달 단계 |
|---|---|---|
| 1차 | `REVIEW_LIMIT_EXHAUSTED:spec` | SPEC_REVIEW |
| 2차 | `REVIEW_LIMIT_EXHAUSTED:plan` | PLAN_REVIEW |
| 3차 | `RECURRING_BLOCKING_FINDING:SPEC-09` | SPEC_REVIEW |
| 4차 | `REVIEW_LIMIT_EXHAUSTED:spec` | SPEC_REVIEW |
| **5차** | — | **COMPLETED** |

Plan 은 2026-09-08T01:11:07Z 에 승인됐고 구현·독립 검증·공식 Code 리뷰가 전부 끝났다.
승인 범위는 거기까지이며 commit/push/PR/merge/`chezmoi apply` 는 포함하지 않는다.
**아무것도 커밋하지 않았다.** 배포(`chezmoi apply`)도 하지 않았으므로
`~/.claude/skills/dual-review/` 는 아직 존재하지 않는다.
