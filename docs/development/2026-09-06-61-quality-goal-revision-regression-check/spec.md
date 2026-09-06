# Quality Goal Specification

- Task ID: 20260906T003045Z-61-quality-goal-개정-후-자기-회귀-점검-revision-r-d857b87b
- Mode: standard
- Status: SPEC_REVIEW
- Created: 2026-09-06T00:30:45Z
- Updated: 2026-09-06
- Source goal: #61 quality-goal 개정 후 자기 회귀 점검(revision regression check) 단계를 추가한다

## Problem and context

`quality-goal` 스킬(`dot_claude/skills/quality-goal/`)의 Spec·Plan 리뷰 루프는 라운드마다 리뷰어 findings 를 반영한 개정본을 다시 제출한다. 개별 finding 의 해소는 각각 옳은데, 여러 해소가 **조합**되면 인접 계약에 결손이 생기고, 그 결손을 잡는 데 다음 라운드 예산이 소모된다. 이슈 #61 본문과 코멘트 넷(2026-09-05)이 이를 실측으로 기록한다.

- #42 실행(2026-08-28): Plan 라운드 2 신규 7건 중 3건이 라운드 1 해소가 만든 회귀(`PLAN-009` 번호 이동 파급 누락, `PLAN-010` 두 해소의 교차점 공백, `PLAN-012` 치환 근거 누락). 84점 1점 차로 종결.
- #70 1단계 실행(2026-09-05, `../70-feat-quality-goal-codex-spec-readiness/docs/development/2026-09-05-70-quality-goal-codex-spec-readiness/report.md` § "이 실행에서 교차 회귀가 아홉 번 나왔다"): Spec 3라운드 + Plan 2라운드 동안 교차 회귀 9건. 종결 사유 `PLAN-06` 은 `PLAN-02` 를 고치며 `AC-105` 의 판정 대상을 옮기고 **같은 요구사항 `R9.9` 의 짝 `AC-84`** 는 두지 않은 것이다(`plan.md:399` 추적표 행은 `spec.md` § Test strategy, `plan.md:260` T17 본문은 `docs/quality-goal-maintenance.md`).
- 같은 실행에서 **유일하게 교차 회귀가 없던 라운드는 Spec r3** 이다. 그 라운드에만 "신설 식별자 전부를 grep 으로 열거하고 거부 조건·판정 AC·추적표 연결 세 칸을 채워라, 빈 칸이 있으면 제출하지 마라"는 기계적 절차가 있었다(`spec-revision-notes.md` § "신설 식별자 거부 계약 전수 점검", 10 식별자 × 3칸, 점검 중 빈 칸 2개를 실제로 발견해 `AC-112·113` 으로 닫음). 나머지 라운드의 "조합 검토를 붙여라"는 서술 지시는 9회 모두 효과가 없었다.

이슈 #61 마지막 코멘트가 설계 요구 셋을 확정했다. (1) 점검 단위는 "이번에 고친 finding" 이 아니라 **"고친 항목과 같은 요구사항·같은 표를 공유하는 모든 항목"** 이다 — 요구사항 ID 를 기준으로 그 ID 를 참조하는 AC·추적표 행·태스크 본문·판정 명령을 전부 열거한다. (2) 출력은 서술이 아니라 **빈 칸이 드러나는 표** 이고, 빈 칸이 있으면 `record-review` 이전에 결정적으로 막힌다. (3) 서술형 지시는 대체 수단으로 인정하지 않는다.

이 Spec 을 쓰기 전에 오케스트레이터가 점검 규칙의 프로토타입(`.claude/quality-state/<task-id>/evidence/revision_check_proto.py`)을 #70 의 실제 산출물에 실행했다. 결과는 `.claude/quality-state/<task-id>/evidence/proto-on-70-plan.md` 에 보존됐다.

| 대상 | 칸 | 빈 칸 | 내용 |
|---|---|---|---|
| #70 `spec.md` (공식 r3 PASS, 715행) | 599 | 0 | 통과한 Spec 은 대칭이 깨진 곳이 없다 |
| #70 `plan.md` (공식 r2 REVISE, `PLAN-06` 잔존) | 560 | **1** | `AC-84/T17` — 추적표 행의 판정 대상 `spec.md` 가 `T17` 본문의 `AC-84` 등장 행에 없다. **종결 사유 `PLAN-06` 그 자체다** |
| 같은 `plan.md`, `AC-105` 행을 `PLAN-02` 반영 전으로 되돌린 base 와 비교 | — | — | 건드린 요구사항 3건(`R9.4`·`R9.8`·`R9.9`)의 파급표가 `R9.9` → `AC-105`·`AC-84`·`AC-85` → `T16`·`T17` 을 열거한다. 요구사항 단위로 훑었다면 `PLAN-06` 은 개정 시점에 드러났다 |

같은 프로토타입에서 "판정 수단 토큰이 태스크 본문 **어딘가에** 있으면 충족" 으로 규칙을 느슨하게 두면 빈 칸이 0 이 된다 — T17 의 다른 문단이 `spec.md` 를 언급하기 때문이다. 판정 수단은 **AC 가 등장하는 같은 행** 에 있어야 결손이 드러난다(R3.3, D6).

## Goals

1. Spec·Plan 개정본을 공식 리뷰에 제출하기 전에 요구사항 단위의 대칭(요구사항 ↔ AC ↔ 추적표 행 ↔ 태스크 본문 ↔ 판정 명령)과 참조 무결성을 **스크립트가** 검사하고, 빈 칸이 드러나는 표를 낸다.
2. 개정으로 건드린 요구사항을 직전 리뷰 시점 스냅숏과의 diff 로 **기계적으로** 산출하고, 그 요구사항을 공유하는 모든 항목을 파급표로 열거한다.
3. 판단이 필요한 부분(해소 간 상호작용, 치환 근거)은 개정 노트의 **정해진 표 형식**에 요구사항 단위로 기록하게 하고, 그 형식과 행 커버리지의 존재를 스크립트가 확인한다.
4. 라운드 2 이상의 `record-review` 가 통과한 점검 산출물을 요구해, 빈 칸이 있는 개정본은 리뷰 기록 자체가 거부되게 한다. 라운드 1 과 이 변경 전에 만들어진 상태는 면제한다.
5. 이 절차를 이 작업의 Spec·Plan 개정에 스스로 적용한다.

## Non-goals

1. **#58 요구사항 추적표 필수화는 포함하지 않는다.** `templates/spec.md` 에 추적표 절을 추가하거나 spec 루브릭의 `required_sections` 판정에 추적표를 넣는 것은 #58 이다. 이 작업은 추적표가 **있으면** 그것을 요구사항 → AC 매핑 원천으로 읽고, 없으면 모든 요구사항의 추적행 칸을 빈 칸으로 보고한다(R1.5). 그 결과 라운드 2 이상에서는 추적표 없는 Spec 이 `record-review` 를 통과할 수 없지만, 라운드 1 리뷰어의 판정 기준과 템플릿은 바꾸지 않는다.
2. Plan § File map 완전성 검사(태스크 본문이 참조하는 경로가 File map 에 있는지, `PLAN-010` 픽스처 미정의 류)는 후속이다. 경로 토큰 추출의 오탐률을 이 규모에서 확정할 수 없다.
3. 정의 본문이 다른 번호로 옮겨간 **번호 재배치의 의미 추적**은 하지 않는다. 옛 번호를 참조하는 곳은 참조 무결성(R2.5·R3.4)이 잡고, 새 번호로 옮긴 정의가 옛 정의와 같은 것인지는 리뷰어 판단이다.
4. 개정 노트 표의 **내용의 진위**는 판정하지 않는다. 스크립트는 형식·행 커버리지·빈 칸만 본다. 상호작용 판정의 옳고 그름은 리뷰어의 몫이며, 그래서 점검 산출물과 개정 노트를 리뷰어 근거로 넘긴다(R7.1).
5. 코드 리뷰 라운드(`code` artifact)에는 적용하지 않는다. 코드 산출물에는 요구사항 ID 표가 없다.
6. `record-review-unverified` 는 산출물을 개정하지 않는 재시도라 점검을 요구하지 않는다. `record-review-error` 도 마찬가지다.
7. `*_PASSED` 전이 가드에 `revision_checks` 저장소 대조를 추가하는 방어선은 후속이다. 라운드 1 통과와 `revision_checks` 키가 없는 기존 상태는 설계상(D7·R6.4) 점검 없이 기록되고 전이한다. 비면제 상태의 라운드 2 이상은 기록 자체가 거부되므로, 전이 가드가 추가로 막을 수 있는 것은 `state.json` 을 직접 편집해 `revision_checks` 항목을 지운 경우뿐이며 그것은 기존 계약(`state.json` 이 권위)의 보호 범위 밖이다.
8. Codex author·readiness(#70)와의 통합은 하지 않는다. 점검은 누가 개정했는지에 무관하게 파일만 읽으므로 #70 이 그대로 호출할 수 있다.
9. 공식 리뷰 라운드 한도(Spec 3 / Plan 2 / Code 3), `REQUIRED_CHECKS`, 점수 임계 85, 세 루브릭의 Pass gate, 리뷰어 에이전트 정의는 바꾸지 않는다(R7.3).
10. `light` 모드는 Spec·Plan 리뷰 라운드가 없으므로 대상이 아니다.
11. `chezmoi apply` 배포는 이 작업이 하지 않는다. 다른 세션이 배포본을 실행 중이다.

## Requirements

### R1. 점검 스크립트 계약

- **R1.1** `dot_claude/skills/quality-goal/scripts/revision_check.py` 를 신설한다. 인자는 `--artifact {spec,plan}`, `--current <경로>`, 선택 `--spec <경로>`(plan 이면 필수), 선택 `--state <state.json 경로>`, 선택 `--base <경로>`, 선택 `--notes <경로>`, 선택 `--out <JSON 경로>` 다. 경로는 상대 경로면 작업 디렉터리 기준으로 해소한다. 종료 코드는 셋이다 — `0` 빈 칸 없음, `1` 빈 칸 있음(JSON 은 `passed: false` 로 기록), `2` 전제 실패(`--current`·`--spec`·`--state` 파일 부재, 명시한 `--base`·`--notes` 경로의 부재나 읽기 실패, `--current`·`--spec` 의 UTF-8 디코딩 실패, plan 에 `--spec` 누락, `--state` 와 `--base` 동시 지정, 스냅숏 부재·digest 불일치, 상태 파일 파싱 실패). `--notes` 를 생략했을 때 기본 경로에 파일이 없는 것은 전제 실패가 아니라 R5.1 의 `section_found: false` 다. `2` 에서는 JSON 을 쓰지 않는다.
- **R1.2** `--out` 의 JSON 은 신설 `schemas/revision-check.schema.json` 을 따르며 `additionalProperties: false` 다. 최상위 필수 필드는 `artifact`, `round`(`--state` 모드는 `rounds[artifact] + 1`, 독립 모드는 `null`), `base_digest`(SHA-256 또는 `null`), `current_digest`(`--current` 파일의 SHA-256), `spec_digest`(plan 이면 `--spec` 의 SHA-256, spec 이면 `null`), `cells`(각 항목 `kind`·`key`·`status`(`ok`/`empty`)·`detail`·`line`), `empty_cells`(정수), `touched_requirements`, `removed_ids`, `ripple`(각 항목 `requirement`·`acceptance_criteria`·`plan_rows`·`tasks`·`commands`), `notes`(`required`·`path`·`section_found`·`missing_rows`·`blank_cells`), `passed` 열둘이다. `cells[]` 항목은 `kind`·`key`·`status`·`detail`·`line` 다섯, `ripple[]` 항목은 `requirement`·`acceptance_criteria`·`plan_rows`·`tasks`·`commands` 다섯을 필수로 하고 `additionalProperties: false` 다. `empty_cells` 는 정수, `base_digest` 는 base 파일(스냅숏 또는 독립 모드 `--base`)의 SHA-256 또는 `null` 이다. `cells[].status` 는 `ok`·`empty` 둘만, `cells[].line` 은 정수 또는 `null`, `notes` 의 다섯 필드는 모두 필수다. `passed` 는 `empty_cells == 0` 이고 `notes.missing_rows` 와 `notes.blank_cells` 가 비어 있고, `notes.required` 가 `true` 이면 `notes.section_found` 도 `true` 일 때만 `true` 다.
- **R1.3** 표준 출력은 `#` 로 시작하는 제목 줄과 `|` 로 시작하는 표 줄만으로 이루어진다. 첫 표는 `status == empty` 인 칸 전부를 `| 종류 | 키 | 상태 | 상세 | 행 |` 로, 둘째 표는 `ripple` 의 모든 행을 `| 요구사항 | 판정 AC | Plan 추적행 | 태스크 | 판정 명령/테스트 |` 로 싣고 빈 칸을 `**빈 칸**` 리터럴로 표시한다. 두 표의 행 집합은 JSON 의 `cells`(empty)·`ripple` 과 같다.
- **R1.4** 식별자 문법·추출 범위·정의 수 하한을 이 항에서 함께 정하고 `references/revision-check-policy.md` 에 같은 문언으로 싣는다. R1.5·R2.3·R2.5·R3.3·R3.4 는 이 항을 참조하며 따로 정의하지 않는다.
  - (a) **정의 문법** — 요구사항 `R<n>.<m>` 은 `- **R<n>.<m>**` 로 시작하는 줄, AC `AC-<n>` 은 `- **AC-<n>**` 로 시작하는 줄, 결정 `D<n>` 은 `### D<n>.` 헤딩, 태스크 `T<n>` 은 `### T<n>.` 헤딩, 판정 명령 `CMD-<n>` 은 첫째 또는 둘째 셀이 그 ID 인 표 행이다.
  - (b) **추출 범위 셋** — ① 정의 범위: 펜스 코드 블록 밖의 줄. ② 참조 범위: 펜스 코드 블록과 인라인 코드 스팬(백틱 1개 또는 2개로 감싼 구간) 밖의 텍스트. 다른 문서의 식별자나 예시를 인용할 때는 백틱으로 감싸 참조에서 제외한다. ③ 판정 수단 범위: Spec AC 본문은 코드 스팬 밖에 있는 마지막 `[실행]`/`[문서]` 표기를 고르고, `[실행]` 이면 그 뒤 괄호 안 전체를, `[문서]` 이면 그 뒤 줄 끝까지를(둘 다 코드 스팬 포함) 읽으며, Plan 추적표의 판정 수단 셀과 태스크 본문의 `CMD-<n>` 참조는 백틱을 제거한 전체 문자열을 읽는다. 관행상 판정 수단은 코드 스팬 안에 쓰이기 때문이다(#70 `plan.md:394` 의 `` `CMD-2 -k test_…` ``).
  - (c) **판정 수단 토큰** — ③ 범위의 문자열에서 백틱을 제거하고 공백으로 나눈 조각 중, `CMD-<n>` 에 정확히 일치하는 것, `test_` 로 시작하는 `\w+`, `[\w./-]+\.[A-Za-z0-9]+` 에 일치하는 파일명 형태(`spec.md`, `docs/quality-goal-maintenance.md`)의 셋이다. `-k`·`§`·서술어 같은 나머지 조각은 토큰이 아니다.
  - (d) **정의 수 하한** — spec 은 요구사항 정의 0 또는 AC 정의 0, plan 은 태스크 절 0 또는 추적표 AC 행 0 이면 `문법 미충족` 종류의 `empty` 칸 하나를 기록해 종료 코드 `1` 을 만든다. 하한 미달 산출물은 다른 칸이 하나도 없어도 `passed` 가 `true` 가 될 수 없다. 이것이 없으면 정의가 0 인 산출물이 `empty_cells == 0` 으로 공허하게 통과한다.
- **R1.5** Spec 의 요구사항 → AC 매핑 원천은 헤딩에 `traceability` 또는 `추적` 을 포함하는 `##` 절 안의 `| R<n>.<m> | AC-… |` 행이다. 요구사항·AC 의 정의는 R1.4(a)·(b)① 로 읽고, 정의 수 하한은 R1.4(d) 를 적용한다. 그 절이 없거나 절은 있어도 그런 행이 하나도 없으면 정의된 모든 요구사항의 `R→추적행` 칸을 `empty` 로 기록한다. `templates/spec.md`·`templates/plan.md` 는 바꾸지 않는다(Non-goal 1, R7.3).
- **R1.6** 스크립트는 `--out` 파일 외에 어떤 파일도 쓰지 않고 입력 파일(`--current`·`--spec`·`--base`·`--notes`·상태·스냅숏)을 수정하지 않는다. 표준 라이브러리만 쓰고 `subprocess`·`socket`·`urllib`·`http` 모듈을 import 하지 않는다 — 네트워크·git 실행 경로가 코드에 없다.

### R2. Spec 대칭 규칙

- **R2.1** 정의된 모든 요구사항에 대해 추적표 행이 있고(`R→추적행`), 그 행이 정의된 AC 를 하나 이상 가리킨다(`R→AC`, `추적행 AC 존재`). 어느 하나가 어긋나면 그 칸이 `empty` 다.
- **R2.2** 추적표의 모든 행은 정의된 요구사항을 가리키고(`추적행→R`), 요구사항 정의 수와 추적표 행 수가 같다(`R 수=추적 행 수`).
- **R2.3** 정의된 모든 AC 는 추적표 행 하나 이상에 등장하고(`AC→R`), R1.4(b)③ 의 규칙으로 읽은 마지막 `[실행] (CMD-<n> …)` 또는 `[문서]` 표기를 판정 수단으로 가지며(`AC→판정수단`), `[실행]` 의 CMD ID 는 Spec 의 판정 명령 표에 존재하고(`AC→CMD 존재`), `[문서]` 는 그 뒤에 R1.4(c) 의 파일명 토큰이 하나 이상 있어야 판정 수단으로 성립한다(없으면 `AC→판정수단` 이 `empty`). 그래서 R4.3 의 `commands` 칸은 `[문서]` 전용 요구사항에서도 비지 않는다.
- **R2.4** AC 번호는 1 부터 정의 수까지 빈 번호 없이 이어지고, 같은 요구사항 ID 나 AC ID 가 두 번 정의되지 않는다. 위반은 각각 `AC 번호 연속`·`중복 정의` 칸이다.
- **R2.5** R1.4(b)② 참조 범위의 모든 `R<n>.<m>`·`AC-<n>`·`CMD-<n>`·`D<n>` 토큰은 정의로 해소돼야 한다. 해소되지 않는 토큰은 `참조 무결성` 칸이며 `line` 은 첫 등장 행, `detail` 은 등장 횟수를 싣는다. 이것이 번호 이동 파급(`PLAN-009` 류)의 기계 검사다.

### R3. Plan 대칭 규칙

- **R3.1** Plan 추적표(`| Criterion | Task | Verification command | Expected outcome |` 형식의 AC 행)의 AC 집합은 Spec 의 AC 정의 집합과 같다. 차집합의 각 원소가 `Spec AC→Plan 추적행` 또는 `Plan 추적행→Spec AC` 칸이다.
- **R3.2** 모든 추적표 행은 존재하는 태스크 절을 하나 이상 지정하고(`AC→태스크`, `태스크 존재`), 각 태스크 본문의 `대상 AC:` 목록은 추적표가 그 태스크에 배정한 AC 집합과 양방향으로 같다(`태스크 대상 AC→추적행`, `추적행→태스크 대상 AC`).
- **R3.3** 추적표 행의 판정 수단 셀에서 R1.4(c) 로 뽑은 토큰은 각각 소유 태스크 본문에서 **그 AC ID 가 등장하는 행**(백틱 제거 후) 중 하나에 부분 문자열로 함께 나타나야 한다(`AC 등장 행에 판정수단 동반`). 태스크 본문 어딘가에 있는 것으로는 충족하지 않는다. 근거는 § Problem and context 의 프로토타입 실측이다.
- **R3.4** 추적표 행의 판정 수단 셀이 R1.4(b)③ 범위(코드 스팬 포함)에서 참조하는 모든 `CMD-<n>` 은 Plan 의 판정 명령 표에 존재해야 하며 없으면 `추적행 CMD 존재` 칸이 `empty` 다. 태스크 본문이 참조하는 `CMD-<n>` 은 R1.4(b)② 의 예외로 코드 스팬 포함 범위에서 읽어 Plan 의 판정 명령 표 정의로 해소하고, R1.4(b)② 참조 범위의 `T<n>` 은 Plan 정의로, `AC-<n>`·`R<n>.<m>`·`D<n>` 은 `--spec` 의 정의로 해소한다. 이 셋의 미해소는 `참조 무결성` 칸이다.

### R4. 개정 diff 와 파급표

- **R4.1** `--state` 모드에서 `round` 는 `rounds[artifact] + 1` 이고 base 는 직전 `record-review` 가 남긴 스냅숏 `<state.json 의 디렉터리>/snapshots/<artifact>-r<rounds[artifact]>.md` 다. spec·plan 모두 같은 규칙이다. 스크립트는 그 파일의 SHA-256 이 `reviews[artifact][-1].artifact_digest` 와 같은지 확인하고, 다르거나 파일이 없으면 종료 코드 `2` 로 사유를 출력한다. `rounds[artifact] == 0` 이면 base 가 없고 `base_digest` 는 `null`, `touched_requirements` 는 빈 목록, `notes.required` 는 `false` 다. `--base` 는 독립 모드에서만 받아 digest 대조 없이 diff 원천으로 쓰며(`round` 는 `null`), `--state` 와 함께 주면 종료 코드 `2` 다.
- **R4.2** 건드린 요구사항은 줄 단위 diff(`difflib.SequenceMatcher` 의 `insert`·`replace` opcode 가 만든 current 쪽 줄)로 산출한다. spec 은 요구사항 정의 줄, 그 요구사항의 추적표 행, 그 행이 가리키는 AC 정의 줄 중 하나라도 바뀐 요구사항이다. plan 은 추적표 행이 바뀐 AC, 또는 절 본문이 바뀐 태스크에 배정된 AC 를 `--spec` 추적표로 요구사항에 되돌린 것이다. base 에는 정의됐는데 current 에 정의가 없는 요구사항·AC ID(plan 이면 태스크·CMD ID)는 `removed_ids` 에 싣는다.
- **R4.3** 건드린 요구사항마다 파급표 행 하나를 만든다. 칸은 판정 AC(Spec 추적표), Plan 추적행 번호, 태스크, 판정 명령/테스트다. 마지막 칸은 AC 의 `[실행]` CMD ID, `[문서]` 표기 뒤의 파일명 토큰(R1.4(c)), 그리고 plan 이면 추적행 판정 수단 셀의 토큰을 합친 것이므로 `[문서]` 전용 AC 만 가진 요구사항도 파일명 토큰으로 채워진다. spec 점검에서는 `plan_rows`·`tasks` 가 `null` 이고 판정하지 않으며, plan 점검에서는 네 칸 모두 판정한다. 판정 대상 칸이 빈 목록이면 `파급표` 종류의 `empty` 칸으로도 기록해 종료 코드 `1` 을 만든다.

### R5. 개정 노트 형식

- **R5.1** 개정 노트는 산출물 디렉터리의 `<artifact>-revision-notes.md`(`spec-revision-notes.md`, `plan-revision-notes.md`)다. `--notes` 를 주지 않으면 `--current` 와 같은 디렉터리의 그 이름을 쓰고, 주면 그 경로를 쓴다. `--state` 모드에서 `round >= 2` 이면 `notes.required` 가 `true` 이고 노트에 `## 라운드 <round> 개정` 헤딩(`##` 뒤 한 칸, 그 라운드 숫자, 한 칸, `개정`)이 있어야 한다. 없으면 `notes.section_found` 는 `false` 다. artifact 와 라운드에 무관하게 같은 규칙이다.
- **R5.2** 그 절 안에 헤더 행이 정확히 `| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |` 인 표가 있어야 한다. `touched_requirements` 의 모든 요구사항에 대해 첫 셀이 그 ID 인 행이 있어야 하며 없는 것은 `notes.missing_rows` 에 싣는다. 그 행의 `함께 바뀐 항목` 셀에는 `ripple` 의 같은 요구사항 항목이 가진 `acceptance_criteria` 전부가 나타나야 하고, 각 AC ID 바로 뒤 괄호가 `일치` 또는 `모순` 으로 시작해야 한다(예: `AC-17(일치 — …)`). 빠진 AC 는 `<요구사항>/<AC>`, 판정 토큰이 없는 AC 는 `<요구사항>/<AC>/판정` 으로 `notes.missing_rows` 에 싣는다(D12). 어느 행이든 셀을 trim 한 결과가 빈 문자열·`-`·`—` 중 하나이면 `notes.blank_cells` 에 `<요구사항>/<열 이름>` 으로 싣는다. 열의 뜻은 `references/revision-check-policy.md` 가 정한다 — 해소 finding 은 그 요구사항을 건드리게 한 finding ID(없으면 `자체 개정`), 함께 바뀐 항목은 파급표에서 생성한 그 요구사항의 AC 전부와 각 AC 본문이 새 요구사항 문언과 일치하는지의 판정(`일치`/`모순`) 및 같이 고친 추적행·태스크, 상호작용 판정은 이 해소가 다른 해소의 전제를 깨거나 새 공백을 만들지 않는지 한 문장, 치환 근거는 자리표시자를 구체값으로 바꿨을 때 그 값의 출처(없으면 `치환 없음`).
- **R5.3** `notes.required == true` 인데 `section_found == false` 이거나, `missing_rows` 또는 `blank_cells` 가 비어 있지 않으면 `passed` 는 `false` 이고 종료 코드는 `1` 이다. `notes.required == false`(라운드 1, 독립 모드)이면 노트 부재는 `passed` 에 영향이 없다. 스크립트는 셀 내용의 진위를 판정하지 않는다 — 형식이 맞는 임의 문장은 통과한다(Non-goal 4).

### R6. 상태 머신

- **R6.1** `record_review` 의 시그니처를 `record_review(state, review_path, artifact_digest, *, revision_check_path=None, snapshot_dir=None)` 로 확장한다. 기존 세 인자 호출은 라운드 1 과 면제 상태(R6.4)에서 그대로 동작하고, 비면제 spec·plan 라운드 2 이상에서는 R6.2 대로 `revision_check_path` 가 필요하다. `snapshot_dir` 가 주어지고 artifact 가 spec 또는 plan 이고 `artifacts[artifact]` 가 `null` 이 아니면, 모든 검증이 끝난 뒤 상태를 바꾸기 **전에** 그 파일을 `<snapshot_dir>/<artifact>-r<expected_round>.md` 로 복사한다 — 디렉터리가 없으면 `mkdir(parents=True)` 로 만들고, 같은 디렉터리의 임시 파일에 쓴 뒤 `os.replace` 로 교체하므로 실패 시 불완전한 대상 파일이 남지 않는다. 이미 `_file_digest(artifact_path) == artifact_digest` 를 확인한 뒤이므로 스냅숏의 SHA-256 은 기록되는 `artifact_digest` 와 같다. 복사가 `OSError` 로 실패하면 `FilesystemError` 를 내고 상태를 바꾸지 않는다. `snapshot_dir` 가 `None`(함수 직접 호출)이거나 `artifacts[artifact]` 가 `null` 이거나 artifact 가 `code` 면 스냅숏을 만들지 않는다. `snapshot_dir=None` 으로 spec·plan 라운드를 기록한 호출자는 다음 라운드 점검이 R4.1 의 스냅숏 부재(`2`)로 끝난다는 것을 감수하는 것이며, 오케스트레이터 경로는 항상 CLI 이므로 이 경우는 테스트·직접 호출에만 해당한다. CLI 는 항상 `Path(args.state).parent / "snapshots"` 를 `snapshot_dir` 로 넘긴다. 스냅숏 뒤 `save_state` 가 실패하면 라운드 미기록 스냅숏 `r<expected_round>` 가 남지만, 다음 점검은 `rounds[artifact]` 가 가리키는 이전 라운드 파일만 읽으므로 무해하고 다음 성공 기록이 덮어쓴다.
- **R6.2** `record-review` 에 `--revision-check <JSON 경로>` 를 추가하고 CLI 는 그 값을 `revision_check_path` 인자로 넘긴다. 리뷰 artifact 가 spec 또는 plan 이고 `expected_round >= 2` 이고 상태가 면제 대상(R6.4)이 아니면 이 인자는 필수다(spec 라운드 2·3, plan 라운드 2). 주어진 파일은 존재해야 하고, `schemas/revision-check.schema.json` 을 통과해야 하며, `artifact` 가 리뷰 artifact 와, `round` 가 `expected_round` 와, `current_digest` 가 `--artifact-digest` 와 같아야 하고, `passed` 가 `true` 여야 한다. 하나라도 어긋나면 `StateError` 를 내고 상태를 바꾸지 않는다. 검사 순서는 기존 digest·라운드 검증 뒤, 리뷰 JSON 검증 앞이다.
- **R6.3** `revision_check_path` 가 통과하면 `state.revision_checks[artifact]` 에 `{round, path, current_digest, base_digest}` 를 추가한다. `path` 는 `revision_check_path` 를 절대 경로로 해소한 문자열이고 나머지 셋은 점검 JSON 의 같은 이름 필드 값이다. `expected_round == 1` 에서 인자가 주어지면 같은 규칙으로 검증하고 기록한다. `code` 리뷰에 이 인자를 주면 `StateError` 다.
- **R6.4** `new_state` 는 `"revision_checks": {"spec": [], "plan": []}` 을 만든다. `load_state` 는 이 키를 주입하지 않으며 `schema_version` 은 1 을 유지한다. 키가 없는 상태(이 변경 전에 만든 상태)는 R6.2 의 필수 규칙에서 면제되고, 그런 상태에 인자가 주어지면 검증 뒤 첫 기록 때 키를 만든다. #70 Spec `D14` 와 같은 방식이다.

### R7. 문서·회귀 방지

- **R7.1** `SKILL.md` 의 `### Spec` 과 `### Plan` 절에 라운드 2 이상의 절차를 넣는다 — 개정과 개정 노트 작성 → `set-artifact` 재등록 → `revision_check.py --state` 실행 → 종료 코드 `0` 이 될 때까지 개정 반복(라운드 소모 없음) → 리뷰어 근거에 점검 JSON 과 개정 노트 경로 포함 → `record-review --revision-check`. 같은 두 절의 초안 작성 지시에 "산출물은 `references/revision-check-policy.md` 의 식별자 문법(R1.4)을 따른다 — 요구사항 `- **R<n>.<m>**`, AC `- **AC-<n>**` 와 `[실행]`/`[문서]` 판정 수단, 요구사항 추적표, 판정 명령 표, 태스크 `### T<n>.` 과 `대상 AC:` 목록" 을 넣어 저자가 문법을 어디서 알게 되는지를 계약으로 고정한다. 참조 경로 목록에 `scripts/revision_check.py`, `references/revision-check-policy.md`, `schemas/revision-check.schema.json` 을 더한다. `SKILL.md` 는 500 행 미만을 유지한다.
- **R7.2** `references/revision-check-policy.md` 를 신설한다. 식별자 문법·추출 범위·하한(R1.4 의 (a)~(d) 를 같은 문언으로), 칸 종류와 뜻(R2·R3·R4.3), 개정 노트 표 헤더와 열의 뜻(R5.2), 종료 코드(R1.1), 라운드 규칙(R4.1·R6.2·R6.4), 그리고 § Security and risk 의 포착 범위 표(#70 교차 회귀 9건과 #42 3건)를 그대로 싣는다.
- **R7.3** `ROUND_LIMITS == {"spec": 3, "plan": 2, "code": 3}`, `REQUIRED_CHECKS` 의 키 집합, `SCORE_THRESHOLD == 85` 는 바꾸지 않는다. 세 루브릭의 `## Pass gate` 절, `templates/spec.md`, `templates/plan.md`, 그리고 `SKILL.md` 의 `### Approval`, `### Implementation`, `### Code review`, `## Review invocation contract`, `## Codex invocation contract`, `## Independent verification`, `## Safety rules` 일곱 절은 base revision `b30a0dee8465b9b8a3cf5243a47740b3c2116a24` 과 바이트 단위로 같다. 기존 테스트 메서드 이름(세 파일 합집합 고유 239 개 — 240 건이 실행되지만 `test_frontmatter_contract` 가 두 클래스에 있다)은 하나도 삭제·개명하지 않는다. 비면제 상태(`state_at()` 이 `new_state()` 로 만드는 상태)에서 spec 또는 plan 리뷰를 라운드 2 이상으로 **기록하는** 모든 기존 테스트 — 함수 `record_review(` 직접 호출과 CLI `record-review` 서브커맨드 호출 둘 다 포함한다. 판정 방법은 `test_quality_state.py` 의 각 `def test_` 본문에서 `record_review(`(`record_review_unverified(` 제외) 또는 `"record-review"` 호출과 `valid_review(artifact="spec"|"plan", round_number=2|3)` 또는 `for round_number in (1, 2[, 3])` 루프의 동반이며, 2026-09-06 소스에서 11 개(`test_report_registers_after_review_limit_exhausted_auto_transition`, `test_report_registers_after_recurring_blocking_finding_auto_transition`, `test_record_review_is_rejected_after_each_auto_transition`, `test_stale_unverified_retry_does_not_bind_normal_next_round_and_is_cleared`, `test_plan_round_three_is_rejected_after_two_recorded_rounds`, `test_spec_round_four_is_rejected_after_three_recorded_rounds`, `test_nonpassing_final_spec_round_enters_needs_redesign`, `test_repeated_stable_blocker_enters_needs_redesign_with_the_finding_id`, `test_cli_record_review_round_two_uses_state_held_prior_blockers`, `test_cli_registers_report_after_limit_exhausted_transition`, `test_cli_registers_report_after_recurring_finding_transition`)다. 라운드 2 JSON 을 라운드 0 상태에 넣어 거부만 확인하는 `test_review_round_must_be_next_round` 는 기록 테스트가 아니라 대상이 아니고, `record_review_unverified` 만 부르는 테스트와 `code` 라운드 테스트도 대상이 아니다. 이들은 `state_at()` 이 `new_state()` 로 만드는 비면제 상태를 쓰므로 R6.2 뒤에는 `revision_check_path` 에 통과 픽스처를 넘기거나 면제 상태 픽스처로 바꿔 본문만 갱신한다. 이름은 유지한다.
- **R7.4** `SKILL.md` frontmatter `version` 을 `5.0.0` 으로 올린다 — `docs/quality-goal-maintenance.md` 버전 정책의 "상태 머신 계약 변경: MAJOR" 에 해당한다. 같은 문서에 `## 개정 후 자기 회귀 점검` 절을 더해 `revision_check.py --artifact` 로 시작하는 실행 명령, 스냅숏 위치 `snapshots/`, 면제 규칙(`revision_checks` 키 부재)을 싣는다.
- **R7.5** 신규 계약은 `tests/test_revision_check.py`(신설, R1~R5 의 테스트), `tests/test_quality_state.py`(R6 의 테스트), `tests/test_content_contracts.py`(R7 과 스키마의 테스트)의 결정적 테스트로 판정한다. 픽스처 `tests/fixtures/revision-check/` 에 대칭이 완전한 최소 Spec·Plan 쌍, `PLAN-06` 형태(추적표 행의 판정 대상이 태스크 본문의 AC 등장 행에 없음)를 재현한 Plan, 라운드 2 노트가 있는 것과 없는 것을 둔다. 배포된 스크립트는 이 작업의 `spec.md`·`plan.md` 에 독립 모드로 실행해 종료 코드 `0` 이어야 한다.

## Acceptance criteria

판정 수단 표기는 두 가지다. `[실행]` 은 § Test strategy 판정 명령 표의 명령으로 판정하며 괄호 안은 명령 ID 와 테스트 이름이다. `[문서]` 는 지정한 파일에 해당 문언이 존재하는지로 판정한다.

- **AC-1** `revision_check.py` 가 대칭이 완전한 픽스처에 `0`, 빈 칸이 있는 픽스처에 `1` 을 반환하고 `1` 일 때 `--out` JSON 의 `passed` 가 `false` 다. `--artifact plan` 에 `--spec` 누락, `--current` 파일 부재, `--spec` 파일 부재, `--state` 파일 부재, 명시한 `--base` 부재, 명시한 `--base` 가 디렉터리라 읽기 실패, 명시한 `--notes` 부재, 명시한 `--notes` 가 디렉터리라 읽기 실패, `--current` 의 UTF-8 디코딩 실패, `--spec` 의 UTF-8 디코딩 실패, `--state` 의 JSON 파싱 실패, `--state` 와 `--base` 동시 지정, 스냅숏 부재 열세 경우 각각 `2` 를 반환하고(스냅숏 digest 불일치는 AC-18) `--out` 파일이 생기지 않으며, 상대 경로로 준 `--current` 가 작업 디렉터리 기준으로 읽힌다. [실행] (CMD-2 `test_cli_exit_codes_and_usage`)
- **AC-2** 픽스처 실행의 `--out` JSON 이 `schemas/revision-check.schema.json` 을 통과하고, 최상위 미지 키, `cells[].status` 가 `ok`·`empty` 밖의 값, `notes` 의 다섯 필드 중 하나 누락, `ripple[]` 항목의 미지 키, `cells[]` 항목의 `key` 누락 다섯 변형이 각각 스키마 검증에 실패한다. 독립 모드 출력의 `round` 는 `null`, `--state` 모드(`rounds.spec == 1`)의 `round` 는 `2` 이고, `current_digest` 는 `--current` 의 SHA-256, plan 의 `spec_digest` 는 `--spec` 의 SHA-256, spec 의 `spec_digest` 는 `null` 이다. [실행] (CMD-2 `test_output_matches_schema`)
- **AC-3** 빈 칸이 있는 픽스처의 표준 출력에서 공백이 아닌 모든 줄이 `#` 또는 `|` 로 시작하고, `| 종류 | 키 | 상태 | 상세 | 행 |` 표의 데이터 행 집합이 JSON `cells` 중 `empty` 항목의 (`kind`,`key`,`detail`,`line`) 집합과 같고, `| 요구사항 | 판정 AC | Plan 추적행 | 태스크 | 판정 명령/테스트 |` 표의 데이터 행 집합이 `ripple` 항목 집합과 값까지 같으며, 파급표의 빈 칸이 `**빈 칸**` 으로 표시된다. [실행] (CMD-2 `test_stdout_prints_ripple_and_empty_cell_tables`)
- **AC-4** 펜스 코드 블록 안의 `AC-999`·`R9.99`·`D99`·`T99`·`CMD-99`, 백틱 하나로 감싼 `AC-998`·`CMD-98`·`D98`·`T98`, 백틱 둘로 감싼 `R8.88`·`AC-997` 이 정의로도 참조로도 세어지지 않아 `참조 무결성` 칸을 만들지 않고, AC 본문에서 코드 스팬 안의 `[실행] (CMD-7 …)` 은 판정 수단으로 읽히지 않는다. [실행] (CMD-2 `test_id_grammar_ignores_code_blocks`)
- **AC-5** 추적표 절이 없는 Spec 과 절은 있어도 `| R… | AC-… |` 행이 없는 Spec 에서 정의된 요구사항 수만큼 `R→추적행` 칸이 `empty` 이고, 헤딩이 `## Requirements traceability` 인 Spec 과 `## 요구사항 추적표` 인 Spec 모두에서 행이 매핑 원천으로 읽힌다. [실행] (CMD-2 `test_missing_spec_traceability_marks_every_requirement_empty`)
- **AC-6** 실행 전후 픽스처 디렉터리와 상태 디렉터리의 모든 파일(`--current`·`--spec`·`--base`·노트·상태·스냅숏)의 SHA-256 이 같고 `--out` 외의 새 파일이 생기지 않으며, `revision_check.py` 소스가 `subprocess`·`socket`·`urllib`·`http` 를 import 하지 않는다. [실행] (CMD-2 `test_check_is_read_only`)
- **AC-7** 추적표 행이 없는 요구사항은 `R→추적행`, 행은 있지만 AC 가 없는 요구사항은 `R→AC`, 미정의 AC 를 가리키는 행은 `추적행 AC 존재` 칸이 `empty` 다. [실행] (CMD-2 `test_requirement_without_trace_row_or_ac_is_empty`)
- **AC-8** 정의 없는 요구사항을 가리키는 추적표 행은 `추적행→R` 칸이 `empty` 이고, 정의 수와 행 수가 다르면 `R 수=추적 행 수` 칸이 `empty` 다. [실행] (CMD-2 `test_ghost_trace_row_and_count_mismatch`)
- **AC-9** 어느 추적표 행에도 없는 AC 는 `AC→R`, `[실행]`·`[문서]` 표기가 없는 AC 는 `AC→판정수단` 칸이 `empty` 다. `[문서] \`docs/x.md\` § 절` 처럼 파일명 토큰이 따르는 AC 는 `ok` 이고 `[문서]` 뒤에 파일명 토큰이 없는 AC 는 `AC→판정수단` 이 `empty` 이며, 코드 스팬 밖에 `[실행] (CMD-1 …)` 과 `[문서]` 가 차례로 있는 AC 는 마지막 표기 `[문서]` 가 판정 수단이 되어 `AC→CMD 존재` 칸을 만들지 않는다. [실행] (CMD-2 `test_orphan_ac_and_missing_means`)
- **AC-10** `[실행] (CMD-9 …)` 를 쓰는데 판정 명령 표에 `CMD-9` 행이 없으면 `AC→CMD 존재` 칸이 `empty` 다. [실행] (CMD-2 `test_execution_ac_requires_cmd_row`)
- **AC-11** `AC-1`·`AC-2`·`AC-4` 만 정의된 Spec 은 `AC 번호 연속` 칸이, 같은 `R1.1` 이 두 줄에 정의된 Spec 과 같은 `AC-3` 이 두 줄에 정의된 Spec 은 각각 `중복 정의` 칸이 `empty` 다. [실행] (CMD-2 `test_ac_numbering_gap_and_duplicate_definition`)
- **AC-12** 본문이 코드 스팬 밖에서 정의되지 않은 `AC-77`·`D9`·`R7.7`·`CMD-9` 를 참조하면 각각 `참조 무결성` 칸이 `empty` 이고, `AC-77` 을 두 줄에서 참조한 픽스처에서 그 칸의 `line` 이 첫 등장 행, `detail` 이 `2` 회를 담는다. [실행] (CMD-2 `test_dangling_reference_is_empty_cell`)
- **AC-13** Spec 에만 있는 AC 는 `Spec AC→Plan 추적행`, Plan 추적표에만 있는 AC 는 `Plan 추적행→Spec AC` 칸이 `empty` 다. [실행] (CMD-2 `test_plan_ac_set_equals_spec`)
- **AC-14** 추적표가 T2 에 배정한 AC 가 T2 의 `대상 AC:` 목록에 없으면 `추적행→태스크 대상 AC`, 목록에는 있는데 추적표가 다른 태스크에 배정했으면 `태스크 대상 AC→추적행` 칸이 `empty` 이고, 존재하지 않는 `T9` 를 지정한 행은 `태스크 존재` 칸이, Task 셀이 비어 있거나 `T` ID 가 없는 행은 `AC→태스크` 칸이 `empty` 다. [실행] (CMD-2 `test_task_target_list_symmetry`)
- **AC-15** `PLAN-06` 형태 픽스처 — 추적표 행이 ``[문서] `spec.md` § Test strategy`` 이고 소유 태스크 본문의 AC 등장 행이 `docs/quality-goal-maintenance.md` 만 언급하며 다른 문단에 `spec.md` 가 있음 — 에서 `AC 등장 행에 판정수단 동반` 칸이 `empty` 이고 `detail` 이 `spec.md` 를 누락으로 싣는다. [실행] (CMD-2 `test_same_line_rule_catches_plan_06_shape`)
- **AC-16** 판정 수단 셀이 백틱으로 감싼 `` `CMD-2 -k test_alpha` `` 인 추적표 행에서 토큰이 `CMD-2` 와 `test_alpha` 둘로 뽑히고(`-k` 는 아님), 소유 태스크 본문에 `` `CMD-2 -k`로 `test_alpha`(AC-3) `` 처럼 같은 행에 둘과 AC 가 있으면 그 칸은 `ok` 이고, `test_alpha` 가 그 AC 등장 행이 아닌 다른 행에만 있으면 `empty` 이며 `detail` 이 `test_alpha` 를 누락으로 싣고, `CMD-2` 만 그 행에 없으면 `detail` 이 `CMD-2` 를 싣는다. [실행] (CMD-2 `test_same_line_rule_accepts_colocated_means`)
- **AC-17** Plan 판정 명령 표에 없는 `CMD-8` 을 쓴 추적표 행은 `추적행 CMD 존재` 칸이, 태스크 본문의 코드 스팬 안에서만 참조되는 `CMD-7` 과 Plan 본문의 정의 없는 `T12`·`AC-66`·`R6.6`·`D6` 참조는 각각 `참조 무결성` 칸이 `empty` 다. [실행] (CMD-2 `test_plan_cmd_and_reference_integrity`)
- **AC-18** spec 과 plan 각각에 대해 `--state` 모드에서 `snapshots/<artifact>-r1.md` 의 SHA-256 이 `reviews[artifact][-1].artifact_digest` 와 같으면 `base_digest` 가 그 값이고 `round` 가 `2` 이며, `rounds.spec == 2` 이면 `round` 가 `3` 이고, 스냅숏 파일이 없거나 digest 가 다르면 종료 코드 `2` 다. [실행] (CMD-2 `test_base_snapshot_located_and_digest_checked`)
- **AC-19** spec 과 plan 각각에 대해 `rounds[artifact] == 0` 인 상태에서 `round` 는 `1`, `base_digest` 는 `null`, `touched_requirements` 는 빈 목록, `notes.required` 는 `false` 이고 노트 파일이 없어도 `passed` 와 종료 코드는 대칭 결과만 따른다. [실행] (CMD-2 `test_round_one_has_no_base_and_no_notes_requirement`)
- **AC-20** base 와 비교해 `R2.1` 정의 줄만 바꾼 Spec 은 `touched_requirements == ["R2.1"]`, `AC-5` 정의 줄만 바꾼 Spec 은 `AC-5` 를 가리키는 요구사항만, `R3.1` 추적표 행만 바꾼 Spec 은 `["R3.1"]`, `R3.1` 정의 바로 뒤에 새 줄을 삽입만 한 Spec 은 삽입 줄이 속한 요구사항만이며, base 에 있던 `R4.2` 정의와 `AC-8` 정의를 지우면 `removed_ids` 가 둘을 담는다. [실행] (CMD-2 `test_touched_requirements_from_diff_spec`)
- **AC-21** base 와 비교해 `AC-7` 추적표 행만 바꾼 Plan 은 `AC-7` 의 요구사항만, `T3` 본문만 바꾼 Plan 은 `T3` 에 배정된 AC 들의 요구사항만 `touched_requirements` 에 있고, base 의 `T3` 절과 `CMD-2` 행을 지운 Plan 은 `removed_ids` 에 둘을 담는다. [실행] (CMD-2 `test_touched_requirements_from_diff_plan`)
- **AC-22** 건드린 요구사항 둘이 있는 plan 점검에서 `ripple` 이 정확히 두 항목이고 완전한 행의 `acceptance_criteria`·`plan_rows`·`tasks`·`commands` 가 픽스처의 기대값과 같으며, 판정 AC 가 없는 요구사항, 추적행이 없는 AC 만 가진 요구사항, 태스크가 없는 행, 명령이 없는 행 네 경우 각각 `파급표` 종류의 `empty` 칸을 만들어 종료 코드가 `1` 이다. spec 점검의 `ripple` 항목은 `plan_rows`·`tasks` 가 `null` 이고 그 둘로는 `empty` 칸이 생기지 않으며, `[문서] \`docs/x.md\` § 절` 표기의 AC 만 가진 요구사항은 `commands` 가 `["docs/x.md"]` 이라 `파급표` 칸이 `ok` 다. [실행] (CMD-2 `test_ripple_row_per_touched_requirement_with_empty_marking`)
- **AC-23** `rounds.spec == 1` 인 상태에서 노트 파일이 없거나 `## 라운드 2 개정` 헤딩이 없으면 `notes.required` 가 `true`, `section_found` 가 `false`, `passed` 가 `false`, 종료 코드 `1` 이다. `--notes` 를 생략하면 `notes.path` 가 `--current` 디렉터리의 `spec-revision-notes.md` 이고 주면 그 경로다. `rounds.plan == 1` 은 `plan-revision-notes.md` 의 `## 라운드 2 개정`, `rounds.spec == 2` 는 `## 라운드 3 개정` 을 찾는다. [실행] (CMD-2 `test_notes_section_required_from_round_two`)
- **AC-24** 헤더가 `| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |` 와 다른 표는 인식되지 않아 모든 건드린 요구사항이 `missing_rows` 에 들어가고, 헤더가 같고 건드린 요구사항마다 행이 있으며 각 행의 `함께 바뀐 항목` 셀이 그 요구사항의 파급표 AC 전부를 담으면 `missing_rows` 가 비어 있고, 어느 행이 파급표 AC 하나를 빠뜨리면 `missing_rows` 에 `<요구사항>/<AC>` 가, AC ID 는 있지만 뒤 괄호가 `일치`/`모순` 으로 시작하지 않으면 `<요구사항>/<AC>/판정` 이 있다. [실행] (CMD-2 `test_notes_table_header_and_row_coverage`)
- **AC-25** 행의 `치환 근거` 셀이 빈 문자열, 공백만, `-`, `—` 네 경우 각각 `blank_cells` 에 `<요구사항>/치환 근거` 가 있고, 나머지 네 열(`요구사항`·`해소 finding`·`함께 바뀐 항목`·`상호작용 판정`) 각각에 같은 규칙이 적용되며, 형식이 맞는 임의의 비공백 문장은 `blank_cells` 에 들어가지 않는다. [실행] (CMD-2 `test_notes_blank_cell_is_empty`)
- **AC-26** 대칭 칸이 전부 `ok` 여도 `missing_rows` 또는 `blank_cells` 가 비어 있지 않으면, 또는 `notes.required` 가 `true` 인데 `section_found` 가 `false` 이면 `passed` 가 `false` 이고 종료 코드가 `1` 이다. 대칭 칸이 전부 `ok` 이고 `notes.required` 가 `false` 이면 노트가 없어도 `passed` 가 `true` 다. [실행] (CMD-2 `test_notes_failure_sets_passed_false_and_exit_one`)
- **AC-27** spec 과 plan 각각에서 `record_review(..., snapshot_dir=<dir>)` 라운드 1 성공 뒤 `<dir>/<artifact>-r1.md` 가 존재하고 그 SHA-256 이 기록된 `artifact_digest` 와 같으며, 존재하지 않던 `snapshot_dir` 가 만들어지며, `snapshot_dir=None` 이거나 `artifacts[artifact]` 가 `null` 이거나 `code` 리뷰이면 스냅숏이 생기지 않고, 라운드 1 의 기존 세 인자 호출이 그대로 성공한다. [실행] (CMD-2 `test_record_review_writes_snapshot_with_reviewed_digest`)
- **AC-28** `revision_checks` 키가 있는 상태에서 spec 라운드 2, spec 라운드 3, plan 라운드 2 의 `record-review` 를 `--revision-check` 없이 호출하면 각각 `StateError` 이고 오류 메시지에 `--revision-check` 와 라운드 번호가 있으며 `rounds`·`reviews` 가 바뀌지 않는다. [실행] (CMD-2 `test_record_review_round_two_requires_revision_check`)
- **AC-29** 파일 부재, `artifact` 불일치, `round` 불일치, `current_digest` 가 `--artifact-digest` 와 다름, `passed: false`, 스키마 위반(미지 키) 여섯 경우 각각 `StateError` 이고 상태가 바뀌지 않는다. 리뷰 JSON 의 `round` 불일치와 `--revision-check` 누락이 동시면 라운드 불일치 오류가, `--revision-check` 누락과 리뷰 JSON 스키마 위반이 동시면 `--revision-check` 오류가 보고된다. [실행] (CMD-2 `test_record_review_rejects_mismatched_revision_check`)
- **AC-30** spec 과 plan 각각에서 통과한 점검 JSON 으로 기록하면 `revision_checks[artifact]` 마지막 항목의 `round`·`current_digest`·`base_digest` 가 JSON 의 값과 같고 `path` 가 넘긴 경로의 절대 경로이며, 라운드 1 에서 인자를 주면 같은 검증 뒤 기록되며 `passed: false` 면 라운드 1 에서도 `StateError` 다. [실행] (CMD-2 `test_record_review_stores_revision_check_entry`)
- **AC-31** `code` 리뷰 `record-review` 에 `--revision-check` 를 주면 `StateError` 다. [실행] (CMD-2 `test_revision_check_option_rejected_for_code_review`)
- **AC-32** `revision_checks` 키가 없는 상태 픽스처에서 spec 라운드 2 와 plan 라운드 2 의 `record-review` 가 `--revision-check` 없이 성공하고 키가 생기지 않으며, 인자를 주면 검증 뒤 `revision_checks` 키가 그때 만들어져 그 항목만 담는다. [실행] (CMD-2 `test_legacy_state_without_revision_checks_is_exempt`)
- **AC-33** `new_state` 결과에 `revision_checks == {"spec": [], "plan": []}` 이 있고, 키 없는 상태를 `load_state` 로 읽으면 키가 여전히 없으며 `schema_version` 이 1 이다. [실행] (CMD-2 `test_new_state_has_empty_revision_checks_and_load_does_not_inject`)
- **AC-34** CLI `quality_state.py record-review --state … --review … --artifact-digest … --revision-check …` 가 `--revision-check` 값을 `revision_check_path` 로, `--state` 의 부모 디렉터리 아래 `snapshots` 를 `snapshot_dir` 로 넘겨 함수와 같은 상태 결과와 스냅숏 파일을 만들고, 인자 없는 라운드 2 호출은 0 이 아닌 종료 코드와 오류 메시지를 낸다. [실행] (CMD-2 `test_cli_record_review_accepts_revision_check_flag`)
- **AC-35** `SKILL.md` 의 `### Spec` 과 `### Plan` 절이 각각 `set-artifact` 재등록 뒤 `revision_check.py` 를 `--state` 로 실행하는 순서, `record-review` 의 `--revision-check`, 라운드 2 이상, 개정 노트(`revision-notes.md`), 리뷰어 근거 전달, 종료 코드 `0` 까지 반복을 언급한다. [실행] (CMD-2 `test_skill_revision_check_procedure_contract`)
- **AC-36** `SKILL.md` 참조 경로 목록에 `${CLAUDE_SKILL_DIR}/scripts/revision_check.py`, `${CLAUDE_SKILL_DIR}/references/revision-check-policy.md`, `${CLAUDE_SKILL_DIR}/schemas/revision-check.schema.json` 세 줄이 있다. [실행] (CMD-2 `test_skill_lists_revision_check_supporting_paths`)
- **AC-37** `references/revision-check-policy.md` 가 식별자 문법 다섯 종과 코드 스팬 인용 규칙, R2·R3·R4.3 의 칸 종류 이름 전부, 개정 노트 헤더 문자열과 다섯 열의 뜻과 대체값(`자체 개정`·`치환 없음`), 종료 코드 셋, 라운드 규칙(스냅숏 base·digest 대조·라운드 1 면제·`revision_checks` 키 부재 면제·`record-review` 검증 항목), 그리고 § Security and risk 의 포착 범위 표를 그대로 담아 #70 교차 회귀 9건(1~5 는 성격이 같아 한 행에 다섯 번호를 함께 적는다)·#42 3건·#61 코멘트 3 사례가 모두 등장하고 각 행에 포착 칸 종류 또는 미포착 사유(Non-goal 2·3·4)가 있다. [실행] (CMD-2 `test_revision_check_policy_contract`)
- **AC-38** `schemas/revision-check.schema.json` 이 최상위 `type: object`, `additionalProperties: false`, R1.2 의 열둘 `required` 를 가지며, `cells[]`·`ripple[]`·`notes` 하위 객체도 `additionalProperties: false` 와 R1.2 의 필수 키를 가지고, `cells[].line` 을 문자열로 준 JSON 과 `empty_cells` 를 문자열로 준 JSON 이 각각 검증에 실패한다. [실행] (CMD-2 `test_revision_check_schema_contract`)
- **AC-39** `SKILL.md` frontmatter 의 `version` 이 `5.0.0` 이다. [실행] (CMD-2 `test_skill_version_is_major_bumped`)
- **AC-40** `docs/quality-goal-maintenance.md` 에 `## 개정 후 자기 회귀 점검` 절이 있고 그 절이 `revision_check.py --artifact` 로 시작하는 명령, `snapshots/`, `revision_checks` 키 부재 면제를 담는다. [실행] (CMD-2 `test_maintenance_doc_covers_revision_check`)
- **AC-41** `SKILL.md` 가 500 행 미만이다. [실행] (CMD-3)
- **AC-42** `SKILL.md` 의 R7.3 일곱 절, 세 루브릭의 `## Pass gate` 절, `templates/spec.md`, `templates/plan.md` 가 base revision 과 바이트 단위로 같다. [실행] (CMD-4)
- **AC-43** base revision 세 테스트 파일의 테스트 메서드 이름 합집합(고유 239 개)이 현재 테스트 이름 집합의 부분집합이다. [실행] (CMD-5)
- **AC-44** 전체 테스트 스위트가 종료 코드 0, `OK` 로 끝나고 실행 테스트 수가 240 보다 크다. [실행] (CMD-1)
- **AC-45** 배포 소스의 `revision_check.py` 를 이 작업의 `spec.md` 와 `plan.md` 에 독립 모드로 실행하면 둘 다 종료 코드 `0` 이다. [실행] (CMD-6)
- **AC-46** `quality_state.ROUND_LIMITS == {"spec": 3, "plan": 2, "code": 3}`, `validate_review.SCORE_THRESHOLD == 85`, `REQUIRED_CHECKS` 의 키 집합이 `{"spec", "plan", "code"}` 이고 세 루브릭의 Pass gate 문단이 `85` 를 싣는다. [실행] (CMD-2 `test_round_limits_required_checks_threshold_unchanged`)
- **AC-47** `tests/fixtures/revision-check/` 에 대칭 완전 Spec·Plan 쌍, `PLAN-06` 형태 Plan, 라운드 2 노트 있음·없음 픽스처가 존재하고 각 파일이 `test_revision_check.py` 에서 한 번 이상 읽히며, AC-1~26·48~50·52 의 테스트 이름은 `test_revision_check.py` 에, AC-27~34·53 은 `test_quality_state.py` 에, AC-35~40·46·47·51·54 는 `test_content_contracts.py` 에 정의돼 있다. [실행] (CMD-2 `test_fixtures_cover_each_cell_kind`)
- **AC-48** 요구사항 4·AC 8·결정 2·태스크 3·CMD 2(첫째 셀 ID 표 하나, 둘째 셀 ID 표 하나)를 가진 픽스처 쌍에서 파서가 정의 수를 각각 4·8·2·3·2 로 세고, `## Requirements traceability` 의 4 행을 매핑으로 읽는다. [실행] (CMD-2 `test_id_grammar_recognizes_all_definition_forms`)
- **AC-49** 독립 모드에서 `--base` 를 주면 digest 대조 없이 `touched_requirements` 가 산출되고 `base_digest` 가 그 파일의 SHA-256, `round` 가 `null`, `notes.required` 가 `false` 이며, 그 JSON 을 `record-review --revision-check` 에 주면 `round` 불일치로 `StateError` 다. [실행] (CMD-2 `test_standalone_base_mode`)
- **AC-50** 요구사항 정의가 0 인 Spec, AC 정의가 0 인 Spec, 태스크 절이 0 인 Plan, 추적표 AC 행이 0 인 Plan 각각에서 `문법 미충족` 종류의 `empty` 칸이 정확히 하나 있고 `passed` 가 `false`, 종료 코드가 `1` 이며, 개정 노트가 완비돼도 `passed` 가 `true` 가 되지 않는다. [실행] (CMD-2 `test_definition_floor_blocks_empty_artifacts`)
- **AC-51** `SKILL.md` 의 `### Spec` 과 `### Plan` 절이 초안 작성 지시에서 `revision-check-policy.md` 의 식별자 문법을 따르라고 지시하고, `- **R<n>.<m>**`, `- **AC-<n>**`, `[실행]`, `[문서]`, 추적표, 판정 명령 표, `### T<n>.`, `대상 AC:` 여덟 표기를 그 지시 안에 열거한다. [실행] (CMD-2 `test_skill_names_identifier_grammar_for_authors`)
- **AC-52** 판정 수단 셀이 `` `CMD-7` `` 처럼 백틱 안에만 있는 추적표 행에서 `CMD-7` 이 Plan 판정 명령 표에 없으면 `추적행 CMD 존재` 칸이 `empty` 이고, 표에 있으면 `ok` 이며, 셀에서 `[\w./-]+\.[A-Za-z0-9]+` 에 맞는 `docs/quality-goal-maintenance.md` 는 토큰으로 뽑히고 `§`·`판정` 은 뽑히지 않는다. [실행] (CMD-2 `test_verification_cell_reads_inside_code_spans`)
- **AC-53** `snapshot_dir` 를 쓸 수 없는 경로로 주면 `record_review` 가 `FilesystemError` 를 내고 `rounds`·`reviews`·`revision_checks` 가 바뀌지 않으며, 실패 뒤 `<snapshot_dir>` 에 `spec-r1.md` 도 임시 파일도 남지 않으며, `rounds.spec == 1` 인 상태 디렉터리에 라운드 미기록 `spec-r2.md` 가 남아 있어도 점검이 `spec-r1.md` 를 base 로 써 `base_digest` 가 r1 의 digest 다. [실행] (CMD-2 `test_snapshot_write_failure_leaves_state_unchanged`)
- **AC-54** R7.3 의 판정 방법(함수·CLI 두 호출 형태)으로 `test_quality_state.py` 를 기계적으로 훑어 얻은 집합이 R7.3 의 11 개 이름을 모두 포함하고, 그 집합의 각 테스트 본문이 `revision_check_path=`(함수) 또는 `--revision-check`(CLI) 를 넘기거나 `revision_checks` 키 없는 상태 픽스처를 쓰는 둘 중 하나이며, 11 개 이름이 현재 소스에 그대로 존재한다. [실행] (CMD-2 `test_round_two_legacy_tests_were_updated_not_renamed`)

## Requirements traceability

요구사항 정의 수는 30 이고 아래 표의 행 수도 30 이다. AC 는 54 개다. 행 순서는 정의 순서와 같다.

| 요구사항 | 판정하는 AC |
|---|---|
| R1.1 | AC-1, AC-18, AC-23 |
| R1.2 | AC-2, AC-18, AC-26, AC-38, AC-49 |
| R1.3 | AC-3 |
| R1.4 | AC-4, AC-9, AC-16, AC-37, AC-48, AC-50, AC-52 |
| R1.5 | AC-5, AC-42, AC-50 |
| R1.6 | AC-6 |
| R2.1 | AC-7 |
| R2.2 | AC-8 |
| R2.3 | AC-9, AC-10 |
| R2.4 | AC-11 |
| R2.5 | AC-12 |
| R3.1 | AC-13 |
| R3.2 | AC-14 |
| R3.3 | AC-15, AC-16 |
| R3.4 | AC-17, AC-52 |
| R4.1 | AC-1, AC-18, AC-19, AC-49, AC-53 |
| R4.2 | AC-20, AC-21 |
| R4.3 | AC-22 |
| R5.1 | AC-23 |
| R5.2 | AC-24, AC-25, AC-37 |
| R5.3 | AC-23, AC-25, AC-26 |
| R6.1 | AC-27, AC-34, AC-53 |
| R6.2 | AC-28, AC-29, AC-34 |
| R6.3 | AC-30, AC-31, AC-34 |
| R6.4 | AC-32, AC-33 |
| R7.1 | AC-35, AC-36, AC-41, AC-51 |
| R7.2 | AC-37 |
| R7.3 | AC-42, AC-43, AC-46, AC-54 |
| R7.4 | AC-39, AC-40 |
| R7.5 | AC-44, AC-45, AC-47 |

## Architecture

### 컴포넌트와 책임

| 컴포넌트 | 책임 | 변경 |
|---|---|---|
| `scripts/revision_check.py` | 산출물 파싱, 대칭 칸 산출, base diff 와 파급표, 개정 노트 형식 확인, JSON·표 출력 | 신설 |
| `schemas/revision-check.schema.json` | 점검 산출물 계약. `record-review` 와 테스트가 검증에 쓴다 | 신설 |
| `scripts/quality_state.py` | `record-review` 뒤 스냅숏 저장(R6.1), `--revision-check` 필수·검증·기록(R6.2·R6.3), `new_state` 필드(R6.4) | 수정 |
| `references/revision-check-policy.md` | 식별자 문법, 칸 종류, 노트 표 형식, 라운드 규칙, #70 9건 대응표 | 신설 |
| `SKILL.md` | `### Spec`·`### Plan` 절차, 참조 경로 셋, `version` | 수정(두 절과 목록·frontmatter 만) |
| `docs/quality-goal-maintenance.md` | 점검 명령·스냅숏·면제 규칙 | 수정 |
| `tests/` | `test_revision_check.py` 신설, 두 기존 파일에 추가, `fixtures/revision-check/` | 신설·수정 |

### 세 층의 역할 분리

- **기계 검사**(R2·R3·R4): 참조 무결성과 요구사항 단위 대칭은 규칙이 단순하고 결정적이다. 스크립트가 판정하고 리뷰어는 결과만 받는다. 이슈 #61 코멘트 2 의 권고("기계적으로 확인 가능한 검사는 controller 에 둔다")다.
- **판단 강제**(R5): 해소 간 상호작용과 치환 근거는 판단이므로 개정 노트 표에 요구사항 단위로 적게 하고, 스크립트는 **형식과 커버리지**만 본다. 내용은 리뷰어가 근거로 받아 판정한다.
- **상태 강제**(R6): 두 층을 거치지 않은 개정본은 라운드 2 이상에서 `record-review` 자체가 거부한다. 서술 지시가 9회 실패한 뒤이므로 지시가 아니라 거부 계약으로 둔다(D1).

### 라운드 2 이상의 실행 순서

```text
리뷰 r(N) 기록 ── record-review ──▶ snapshots/<artifact>-r<N>.md 저장 (R6.1)
      │
      ▼
개정 + <artifact>-revision-notes.md 의 "## 라운드 N+1 개정" 표 작성 (R5)
      │
      ▼
set-artifact --kind <artifact> (재등록, digest 갱신)
      │
      ▼
revision_check.py --artifact <a> --current … --state … --out …  (R1~R5)
      │  exit 1 → 빈 칸·노트 미비를 고치고 위로 (라운드 소모 없음)
      │  exit 2 → 전제 실패, § Failure behavior
      ▼  exit 0
리뷰어 r(N+1) 기동 — 근거에 점검 JSON·노트 경로 포함 (R7.1)
      │
      ▼
validate → gate → record-review --revision-check <JSON> --artifact-digest <sha> (R6.2·R6.3)
```

`current_digest` 는 `--current` 파일의 SHA-256 이므로 점검 뒤 산출물을 다시 고치면 `record-review` 의 `--artifact-digest` 대조에서 거부된다. 점검은 항상 제출 직전 내용에 대해 실행돼야 한다.

### 상태 머신에 대한 변경

전이 집합과 stage 는 바꾸지 않는다. 바뀌는 것은 `record-review` 의 입력 계약(인자 하나 추가, 라운드 2 이상 필수)과 부작용(스냅숏 저장, `revision_checks` 기록), 그리고 `new_state` 의 필드 하나다. 전이 가드는 손대지 않는다(Non-goal 7).

## Interfaces and data flow

### CLI

```bash
# --state 모드 (오케스트레이터 제출 전 점검)
python3 "$SKILL_DIR/scripts/revision_check.py" \
  --artifact spec \
  --current "$ARTIFACT_DIR/spec.md" \
  --state "$STATE_DIR/state.json" \
  --out "$STATE_DIR/revision-check-spec-r2.json"

python3 "$SKILL_DIR/scripts/revision_check.py" \
  --artifact plan \
  --current "$ARTIFACT_DIR/plan.md" --spec "$ARTIFACT_DIR/spec.md" \
  --state "$STATE_DIR/state.json" \
  --out "$STATE_DIR/revision-check-plan-r2.json"

# 독립 모드 (대칭만; round null; record-review 에 쓸 수 없음)
python3 "$SKILL_DIR/scripts/revision_check.py" --artifact plan \
  --current plan.md --spec spec.md [--base prev-plan.md]

# 기록
python3 "$SKILL_DIR/scripts/quality_state.py" record-review \
  --state "$STATE_DIR/state.json" --review "$STATE_DIR/spec-review-r2.json" \
  --artifact-digest "$SHA" --revision-check "$STATE_DIR/revision-check-spec-r2.json"
```

`--notes` 를 생략하면 `--current` 와 같은 디렉터리의 `<artifact>-revision-notes.md` 를 읽는다. `--state` 가 있을 때 `--base` 를 주면 종료 코드 `2` 다 — base 는 스냅숏만 허용한다.

### 점검 JSON

```json
{
  "artifact": "plan",
  "round": 2,
  "base_digest": "…64 hex…",
  "current_digest": "…64 hex…",
  "spec_digest": "…64 hex…",
  "cells": [{"kind": "AC 등장 행에 판정수단 동반", "key": "AC-84/T17", "status": "empty", "detail": "누락: spec.md", "line": 399}],
  "empty_cells": 1,
  "touched_requirements": ["R9.4", "R9.8", "R9.9"],
  "removed_ids": [],
  "ripple": [{"requirement": "R9.9", "acceptance_criteria": ["AC-84", "AC-85", "AC-105"], "plan_rows": [399, 400, 420], "tasks": ["T16", "T17"], "commands": ["CMD-2", "CMD-7", "test_version_guard_is_shared_not_inlined"]}],
  "notes": {"required": true, "path": "…/plan-revision-notes.md", "section_found": true, "missing_rows": [], "blank_cells": []},
  "passed": false
}
```

### 개정 노트 표

```markdown
## 라운드 2 개정

| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |
|---|---|---|---|---|
| R9.9 | PLAN-02 | AC-105 행, T16 본문, AC-84 행 | AC-105 판정 대상을 유지보수 문서로 옮기면서 짝 AC-84 도 같은 문서로 맞췄다. T17 grep 대상과 추적행이 같은 파일이다 | `docs/quality-goal-maintenance.md` 29-35행에 문자열 존재 확인 |
```

### 함수 시그니처

```python
def record_review(state, review_path, artifact_digest, *,
                  revision_check_path=None, snapshot_dir=None):
    ...
```

- `revision_check_path`: 점검 JSON 경로. CLI `--revision-check` 가 넘긴다. spec/plan 라운드 2 이상의 비면제 상태에서 `None` 이면 `StateError`(R6.2). `code` 리뷰에서 `None` 이 아니면 `StateError`(R6.3).
- `snapshot_dir`: 스냅숏 디렉터리. CLI 는 `Path(args.state).parent / "snapshots"` 를 넘긴다. `None` 이면 스냅숏을 만들지 않는다(R6.1). 상태 문서에는 상태 파일 경로가 없고 `init --root` 가 임의 루트를 허용하므로(`quality_state.py:820-835`) 디렉터리는 상태에서 유도하지 않고 호출자가 넘긴다.
- 기존 호출 `record_review(state, review_path, artifact_digest)` 는 두 키워드 인자의 기본값으로 그대로 동작한다. `record_review_unverified`·`record_review_validation_failure` 는 바꾸지 않는다.

### 상태 필드와 스냅숏

- `state.revision_checks`: `{"spec": [{"round", "path", "current_digest", "base_digest"}], "plan": […]}`. `new_state` 가 빈 목록으로 만든다. 읽기 시 주입하지 않는다.
- `<state 디렉터리>/snapshots/<artifact>-r<N>.md`: `record-review` CLI 가 라운드 N 기록 시 저장(`snapshot_dir` 인자). `.claude/quality-state/` 는 `.gitignore:25` 로 무시되므로 저장소에 들어가지 않는다.

### `record-review` 검사 순서

1. 기존: `artifact_digest` 형식 → 리뷰 로드 → stage → `expected_round` → 재시도 digest → 등록 digest 대조 → `round` 일치 → 한도.
2. **신설**: 면제 여부 확인(R6.4) → `expected_round >= 2` 이고 spec/plan 이면 `--revision-check` 필수 → 파일 존재·스키마·`artifact`·`round`·`current_digest`·`passed` 검증(R6.2).
3. 기존: 리뷰 JSON 검증.
4. **신설**: 상태를 바꾸기 전에 스냅숏 복사(R6.1, 실패 시 `FilesystemError` 로 중단).
5. 기존 + 신설: 기록, `revision_checks` 추가(R6.3), 재귀·한도 전이.

## Failure behavior

| 상황 | 동작 | 사용자에게 |
|---|---|---|
| 점검 종료 코드 `1` | JSON 은 `passed: false` 로 남는다. 오케스트레이터는 빈 칸을 고치고 재등록·재점검한다. 라운드를 소모하지 않는다 | 빈 칸 표를 그대로 보인다 |
| 점검 종료 코드 `2`: 스냅숏 없음 | 직전 라운드에 `artifacts[artifact]` 가 `null` 이었거나 파일이 지워졌다. digest 가 `reviews[artifact][-1].artifact_digest` 와 같은 사본이 있으면 그 경로에 두어 복구한다. 없으면 비면제 상태에서는 라운드 2 이상 기록이 불가능하다(면제 상태는 R6.4 대로 점검 없이 기록된다) | 사유와 복구 조건을 보고하고 결정을 묻는다 |
| 점검 종료 코드 `2`: 스냅숏 digest 불일치 | 스냅숏이 변조·덮어쓰기됐다. 위와 같은 복구 | 같음 |
| `record-review` 에 `--revision-check` 누락(라운드 2+, 비면제) | `StateError`, 상태 불변 | 메시지가 인자 이름과 라운드를 명시한다 |
| 스냅숏 복사 실패(`snapshot_dir` 쓰기 불가 등) | `FilesystemError`, 상태 불변, 라운드 미기록. 리뷰 JSON 은 그대로 남아 재시도 가능 | 경로와 OS 오류를 보인다 |
| 스냅숏 저장 뒤 `save_state` 실패 | 라운드 미기록 스냅숏 `r<N+1>` 이 남는다. 다음 점검은 `rounds[artifact]` 의 `r<N>` 만 읽으므로 영향 없음. 재시도 성공 시 덮어쓴다 | 상태 저장 오류를 보인다 |
| 점검 JSON 의 `current_digest` ≠ `--artifact-digest` | `StateError`, 상태 불변. 점검 뒤 산출물을 고친 경우다 | 재점검을 지시한다 |
| 점검 JSON `passed: false` 를 넘김 | `StateError`, 상태 불변 | 빈 칸 수를 보인다 |
| 노트 헤딩·표 헤더 불일치 | `section_found: false` 또는 전 요구사항 `missing_rows`, 종료 코드 `1` | 요구 헤딩·헤더 문자열을 보인다 |
| 면제 상태(키 부재) | 라운드 2 이상에서도 인자 없이 기록된다. 인자를 주면 검증 뒤 키 생성 | 면제로 기록됐음을 보고서에 적는다 |
| `--state` 와 `--base` 동시 지정 | 종료 코드 `2` | base 는 스냅숏만 허용한다고 알린다 |

## Security and risk

- 스크립트는 지정된 파일과 상태 디렉터리만 읽고 `--out` 만 쓴다. 네트워크·git 쓰기·환경 변수 참조가 없다(R1.6).
- 자격 증명은 다루지 않는다. 산출물·노트·점검 JSON 은 문서 식별자와 파일 경로·행 번호만 담는다.
- 스냅숏은 `.claude/quality-state/` 아래에만 있어 `.gitignore:25` 로 무시된다(`git check-ignore -v` 종료 코드 0 확인). 개정 노트는 `docs/development/` 의 프로젝트 문서로 남는다 — 기존 Spec·Plan 과 같은 노출 수준이다.
- 위험(위음성): 이 설계가 기계적으로 잡는 것은 식별자 대칭과 참조 무결성이며, 관측된 교차 회귀의 다수는 그 밖에 있다. 아래 표가 Spec 시점의 포착 범위다. 못 잡는 부류는 R5 개정 노트의 `상호작용 판정`·`치환 근거` 열이 요구사항 단위로 기록을 강제하고 리뷰어가 그 내용을 판정한다 — 스크립트는 형식만 보장하므로 잔여 위험은 "형식은 채웠지만 내용이 틀린 노트" 다. 이 위험은 노트를 리뷰어 근거로 전달(R7.1)해 라운드 안에서 드러나게 하는 것으로만 완화되며, MAJOR 비용의 직접 근거는 실증된 9번(PLAN-06)·8번(PLAN-02)·#42 PLAN-009 류다.

| 사례 | 성격 | 기계 포착 | 칸 종류 또는 미포착 사유 |
|---|---|---|---|
| #70 1~5 (readiness a2·a4·a6, Plan b2·b3) | 같은 사실을 말하는 다른 곳의 문언 발산 | 부분 | 식별자를 옮긴 경우만 `참조 무결성`(예: `READY-05` 의 `R4.3`→`R6.10` 참조 오류). 문언만 다른 경우는 미포착 — R5 `상호작용 판정` 열 |
| #70 6 (`SPEC-17`) | 신설 상태·명령에 거부 계약이 없어 닫힌 구멍이 새 경로로 되살아남 | 미포착 | 설계 판단. 파급표(R4.3)가 신설 요구사항의 AC 를 열거하지만 거부 계약의 유무는 리뷰어 몫 — R5 `상호작용 판정` 열 |
| #70 7 (Plan b2 Critical) | 오케스트레이터 프롬프트의 digest 자리 오기 | 범위 밖 | 산출물이 아니라 프롬프트 파일의 결함. Non-goal 이 아닌 대상 외 |
| #70 8 (`PLAN-02`) | 태스크 본문이 축약 표기를 써 67 AC 의 테스트 이름이 어디에도 없음 | 포착 | `AC 등장 행에 판정수단 동반` — 추적행의 테스트 이름이 태스크 본문의 AC 등장 행에 없음 |
| #70 9 (`PLAN-06`) | 같은 요구사항의 짝 AC 판정 대상 불일치 | 포착(실측) | `AC 등장 행에 판정수단 동반`, 파급표가 `R9.9` 의 세 AC 를 열거 |
| #42 `PLAN-009` | 번호 이동 뒤 옛 번호 참조 잔존 | 포착 | `참조 무결성`(정의 없는 ID 참조), `removed_ids` |
| #42 `PLAN-010` | 두 해소의 교차점에 픽스처 정의 공백 | 미포착 | Non-goal 2(File map 완전성) — R5 `함께 바뀐 항목`·`상호작용 판정` 열 |
| #42 `PLAN-012` | 자리표시자 치환의 근거 부재 | 형식만 | R5 `치환 근거` 열의 빈 칸 금지. 근거의 진위는 Non-goal 4 |
| #61 코멘트 3 (`AC-31` 누락) | 바꾼 요구사항을 참조하는 AC 를 파급 분석에서 빠뜨림 | 포착 | 파급표(R4.3)가 건드린 요구사항의 모든 AC 를 자동 열거 |

- 위험: 규칙이 지나치게 엄격해 오탐이 라운드를 늦출 수 있다. 완화 — 오탐은 라운드를 소모하지 않고(종료 코드 `1` 은 기록 전 단계), 규칙은 전부 문서화된 문법이므로 저자가 표기를 맞추면 해소된다. #70 Spec r3(715행)과 Plan r2(439행)에 프로토타입을 돌린 실측 오탐은 0 이다.
- 위험: 면제 규칙이 새 상태에도 적용되는 우회. 완화 — `new_state` 가 항상 키를 만들고, `load_state` 가 주입하지 않으므로 키를 지우는 것은 상태 파일 직접 편집뿐이다. 그것은 기존 계약(`state.json` 이 권위)에서도 보호 범위 밖이다.
- 위험: `python3` 가 셸에 따라 3.9.6 으로 풀린다. 완화 — CMD-1·CMD-2 가 3.12 이상을 먼저 단언한다(§ Test strategy).

## Test strategy

신규 계약은 전부 `dot_claude/skills/quality-goal/tests/` 의 결정적 테스트로 판정한다. 점검 규칙은 `test_revision_check.py` 에, 상태 계약은 `test_quality_state.py` 에, 문서·스키마 계약은 `test_content_contracts.py` 에 둔다. Codex·리뷰어를 호출하는 테스트는 만들지 않는다.

픽스처 `tests/fixtures/revision-check/` 는 최소 Spec·Plan 쌍(요구사항 4, AC 8, 결정 2, 태스크 3, CMD 2)을 기준으로 두고, 각 칸 종류를 만드는 변형은 테스트 안에서 기준 파일을 문자열 치환해 생성한다. 파일로 두는 것은 대칭 완전 쌍, `PLAN-06` 형태 Plan, 라운드 2 노트 있음·없음 넷이다(AC-47).

테스트 스위트는 **Python 3.12 이상**을 요구한다. 실측 — `/usr/bin/python3` 3.9.6 은 240건 중 23건 오류(`enterContext` 는 3.11+), `python3.12` 3.12.14 와 `python3` 3.14.7 은 `OK`. `-k` 매칭 0건일 때 `unittest` 가 종료 코드 5 를 내는 동작은 3.12 부터이며 3.14.7 에서 `5` 를 확인했다. 그래서 CMD-1·CMD-2 는 버전 단언을 앞에 둔다.

### 판정 명령 표

작업 디렉터리는 저장소 루트다. `QG_BASE=b30a0dee8465b9b8a3cf5243a47740b3c2116a24`.

| ID | 명령 | 통과 조건 |
|---|---|---|
| CMD-1 | `python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)' && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/quality-goal/tests -p 'test_*.py'` | 종료 코드 0, `OK`, `Ran N tests` 의 N > 240 |
| CMD-2 | `python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)' && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/quality-goal/tests -p 'test_*.py' -k <테스트 이름>` | 종료 코드 0. 매칭 0건이면 5 이므로 없는 이름은 통과할 수 없다 |
| CMD-3 | `wc -l < dot_claude/skills/quality-goal/SKILL.md` | 500 미만 |
| CMD-4 | 아래 § CMD-4 상세 | 종료 코드 0, `보존 대상 절 불변`. `SKILL.md` 일곱 절, 두 템플릿 전체, 세 루브릭 `## Pass gate` 절을 base 와 비교한다 |
| CMD-5 | 아래 § CMD-5 상세 | 종료 코드 0, `기존 테스트 보존` |
| CMD-6 | `A=docs/development/2026-09-06-61-quality-goal-revision-regression-check; S=dot_claude/skills/quality-goal/scripts/revision_check.py; python3 $S --artifact spec --current "$PWD/$A/spec.md" && python3 $S --artifact plan --current "$PWD/$A/plan.md" --spec "$PWD/$A/spec.md"` | 두 호출 모두 종료 코드 0 |

### CMD-4 상세

```bash
git show "$QG_BASE:dot_claude/skills/quality-goal/SKILL.md" > /tmp/qg-skill-base.md
QG_BASE=$QG_BASE python3 - <<'EOF'
import re, pathlib, os, subprocess
KEEP = ["### Approval", "### Implementation", "### Code review",
        "## Review invocation contract", "## Codex invocation contract",
        "## Independent verification", "## Safety rules"]
def sections(text):
    out, cur = {}, None
    for line in text.splitlines():
        if re.match(r"^#{2,3} ", line):
            cur = line.strip(); out[cur] = []
        elif cur: out[cur].append(line)
    return out
base = sections(pathlib.Path("/tmp/qg-skill-base.md").read_text())
cur = sections(pathlib.Path("dot_claude/skills/quality-goal/SKILL.md").read_text())
bad = [k for k in KEEP if base.get(k) != cur.get(k)]
assert not bad, bad
root = "dot_claude/skills/quality-goal/"
for rel in ["templates/spec.md", "templates/plan.md"]:
    old = subprocess.check_output(["git", "show", f"{os.environ['QG_BASE']}:{root}{rel}"], text=True)
    assert old == pathlib.Path(root + rel).read_text(), rel
for rel in ["references/spec-rubric.md", "references/plan-rubric.md", "references/code-rubric.md"]:
    old = subprocess.check_output(["git", "show", f"{os.environ['QG_BASE']}:{root}{rel}"], text=True)
    assert sections(old)["## Pass gate"] == sections(pathlib.Path(root + rel).read_text())["## Pass gate"], rel
print("보존 대상 절 불변")
EOF
```

### CMD-5 상세

```bash
python3 - <<'EOF'
import re, subprocess, pathlib
base = "b30a0dee8465b9b8a3cf5243a47740b3c2116a24"
files = ["test_content_contracts.py", "test_quality_state.py", "test_validate_review.py"]
old = set()
for f in files:
    text = subprocess.check_output(["git", "show", f"{base}:dot_claude/skills/quality-goal/tests/{f}"], text=True)
    old |= set(re.findall(r"^\s*def (test_\w+)", text, re.M))
new = set()
for p in pathlib.Path("dot_claude/skills/quality-goal/tests").glob("test_*.py"):
    new |= set(re.findall(r"^\s*def (test_\w+)", p.read_text(), re.M))
assert len(old) == 239, len(old)  # 240 건 실행, 고유 이름 239 (test_frontmatter_contract 가 두 클래스)
assert old <= new, sorted(old - new)
print("기존 테스트 보존")
EOF
```

### 검증 순서

1. CMD-1 로 전체 회귀를 먼저 본다.
2. 실패한 AC 는 CMD-2 로 좁혀 재현한다.
3. CMD-3·4·5·6 은 CMD-1 과 독립적으로 실행한다.
4. lint·type check·build·E2E 는 이 저장소에 구성이 없다(`docs/quality-goal-maintenance.md` '결정적 테스트' 절이 `unittest` 하나만 싣는다). `not configured` 로 보고한다.

## Decisions

### D1. 지시가 아니라 `record-review` 거부 계약으로 강제한다

대안 — (a) `SKILL.md` 에 "개정 후 대칭 점검을 하라" 는 절차만 추가, (b) 리뷰어 루브릭에 점검 항목 추가, (c) `record-review` 가 점검 산출물을 요구. (a) 는 #70 에서 9회 실패했고 이슈 #61 코멘트 4 가 대체 수단으로 인정하지 않는다. (b) 는 라운드를 소모한 뒤에 잡는 것이라 문제의 성격(라운드 예산 낭비)을 바꾸지 못한다. (c) 채택. 라운드 1 과 기존 상태는 면제해 하위 호환을 지킨다.

### D2. 점검 단위는 요구사항 ID 이고 매핑 원천은 Spec 추적표다

이슈 #61 코멘트 4 의 설계 요구 (1) 그대로다. 매핑 원천을 AC 본문의 인라인 `R` 참조로 하면 #70 Spec 처럼 AC 가 요구사항을 인라인 인용하지 않는 문서에서 매핑이 비어 점검이 무력화된다. 추적표를 원천으로 하되 템플릿 변경은 #58 에 남긴다(Non-goal 1).

### D3. base 는 `record-review` 가 남긴 스냅숏이며 저자가 지정하지 않는다

대안 — (a) 오케스트레이터가 개정 전에 사본을 만든다(지시), (b) `--base` 를 저자가 넘기고 스크립트는 digest 만 대조, (c) `record-review` 가 기록 직후 스냅숏을 저장하고 스크립트가 그것만 base 로 받는다. (a) 는 지시라 D1 과 같은 이유로 배격. (b) 는 저자가 유리한 base 를 고를 수 있어 "건드린 요구사항" 산출이 자기 신고가 된다. (c) 채택 — 리뷰된 내용과 같은 digest 임이 구조적으로 보장된다. `--base` 는 독립 모드(record-review 에 쓸 수 없는 `round: null`)에만 남긴다.

### D4. 면제는 `revision_checks` 키 부재로 판정하고 `schema_version` 은 1 을 유지한다

사용자 지시 "schema v1 상태와 라운드 1 에는 요구하지 않는다" 를 이렇게 해석했다 — 현재 모든 상태가 `schema_version: 1` 이고 `load_state` 가 그 값을 강제하므로(`quality_state.py:263-264`), "schema v1 상태" 는 이 변경 전에 만들어진 상태를 뜻한다. 버전을 2 로 올리면 `load_state` 와 모든 기존 테스트가 함께 바뀌어 규모가 커진다. #70 Spec `D14` 가 같은 문제를 "필드 부재 면제, 읽기 시 주입 금지" 로 풀었고 그 방식을 따른다.

### D5. 판단 항목은 개정 노트 표의 형식·커버리지만 강제한다

상호작용 판정의 진위를 스크립트가 판정할 수 없다. 강제할 수 있는 것은 "건드린 요구사항마다 한 행, 다섯 셀 비우지 않음, `함께 바뀐 항목` 에 파급표 AC 전부와 AC 별 `일치`/`모순` 토큰" 이다(D12). #70 Spec r3 의 세 칸 표가 바로 이 형태였고 빈 칸 2개를 실제로 드러냈다. 내용 판정은 리뷰어에게 넘기고, 그래서 점검 JSON 과 노트를 리뷰어 근거로 전달한다(R7.1).

### D6. 판정 수단은 AC 가 등장하는 같은 행에 있어야 한다

프로토타입 실측(§ Problem and context)이 규칙을 정했다. 태스크 본문 전체를 범위로 하면 `PLAN-06` 을 놓친다(빈 칸 0). 같은 행으로 좁히면 정확히 그 한 칸이 드러나고 #70 Plan 439행의 나머지 559칸에 오탐이 없다. 행 단위는 이 스킬의 Plan 이 목록 항목 한 줄에 태스크 단계를 적는 관행과 맞는다.

### D11. 문법·추출 범위·하한을 R1.4 한 항에 모아 정한다

라운드 1 리뷰의 SPEC-01(하한 부재)과 SPEC-02(추출 범위 모순)는 같은 정의를 두 곳에서 다르게 말한 결과다 — R1.4 는 코드 스팬을 전면 배제했고 R3.3·R3.4 는 범위를 말하지 않았다. 둘을 따로 고치면 다음 개정에서 또 어긋난다. 그래서 R1.4 를 (a) 정의 문법 (b) 추출 범위 셋 (c) 토큰 규칙 (d) 정의 수 하한의 한 항으로 만들고 R1.5·R2.3·R2.5·R3.3·R3.4 가 그 항만 참조하게 했다. 저자가 이 문법을 알게 되는 경로는 R7.1 의 `SKILL.md` 지시(AC-51)로 고정한다.

### D12. 개정 노트의 파급 열은 생성하며 저자의 기억을 신뢰하지 않는다

이 실행의 라운드 2 에서 실증됐다. 라운드 1 제출 전 노트 표(26행)는 AC-17 이 R3.2~R3.4 에 속한다고 이미 적었는데, 라운드 2 의 R3.4 파급 행(56행)은 "R1.4(b)③ 참조, AC-52" 만 적고 AC-17 을 빠뜨렸다 — 저자가 파급 열을 기억으로 썼기 때문이다. 그 빠진 AC-17 이 라운드 2 의 유일한 blocker SPEC-09(R3.4 와 AC-17 의 칸 종류 모순)가 됐다. 그래서 R4.3 의 파급표는 스크립트가 추적표에서 생성하고, R5.2 의 `함께 바뀐 항목` 열은 그 생성 목록을 그대로 옮기되 목록의 각 AC 본문을 새 요구사항 문언과 대조한 판정(일치/모순)을 함께 적는다. `references/revision-check-policy.md` 는 이 열을 생성 목록으로 채우라고 지시하고, 스크립트는 `ripple[].acceptance_criteria` 의 모든 AC ID 가 해당 노트 행의 `함께 바뀐 항목` 셀에 나타나는지를 `notes.missing_rows` 와 같은 방식으로 확인한다(R5.2 의 행 커버리지에 AC 커버리지가 더해진다).

### D7. 라운드 1 은 면제하되 점검 실행은 허용한다

라운드 1 은 개정이 아니라 초안이라 base 가 없고 "건드린 요구사항" 이 정의되지 않는다. 대칭 검사 자체는 유용하므로 실행과 기록(R6.3)은 허용하고 필수로는 하지 않는다. 이 Spec 도 라운드 1 제출 전 프로토타입으로 대칭을 확인했다.

### D8. 버전은 5.0.0 이다

`docs/quality-goal-maintenance.md` 버전 정책 — "게이트 규칙이나 상태 머신 계약 변경: MAJOR". `record-review` 입력 계약이 바뀌므로 MAJOR 다. 현재 4.1.0.

### D9. 리뷰어 계약과 한도는 바꾸지 않는다

점검은 리뷰 **전** 오케스트레이터 게이트다. 루브릭·`REQUIRED_CHECKS`·임계·한도를 바꾸면 #57·#60 이 다루는 별개의 정책 논의에 들어간다. `## Review invocation contract` 도 그대로 두고, 근거 전달 지시는 `### Spec`·`### Plan` 절에 둔다(R7.1·R7.3).

### D10. strict-only 블록을 제거한 근거

이 작업은 standard 다. 인증·권한·결제·PII·마이그레이션·외부 API·프로덕션 인프라에 해당하는 요구사항이 없어 여섯 strict 절(위협·권한 격리·마이그레이션·관측·고위험 E2E·프로덕션 무변경)은 적용 대상이 아니다. 유일한 지속 데이터 변경은 로컬 `state.json` 의 선택 필드 하나와 무시 디렉터리의 스냅숏이며 롤백은 `git checkout` 과 파일 삭제로 즉시 가능하다.
