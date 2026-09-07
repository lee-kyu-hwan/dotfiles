# Quality Goal Specification

- Task ID: 20260906T134503Z-70-1단계-축소-범위-quality-goal-spec-단계에-codex-4fa9c46e
- Mode: standard
- Status: SPEC_REVIEW
- Created: 2026-09-06T13:45:03Z
- Updated: 2026-09-06T13:45:03Z
- Source goal: #70 1단계(축소 범위) — quality-goal Spec 단계에 Codex author 와 참고용(advisory) readiness 심사를 추가하고 상태 전이 게이트는 #76 으로 이관

## Problem and context

현행 `quality-goal` 스킬(`dot_claude/skills/quality-goal/SKILL.md:136-166`)에서 Spec 의 초안 작성과 모든 개정은 Claude 오케스트레이터가 수행하고, Codex 는 `IMPLEMENTING` 단계에 처음 호출된다. 그 결과 반복 작성 비용과 권위 있는 최종 심사가 같은 고비용 모델에 몰린다. 이슈 #70 본문은 2026-09-04 병렬 실행 7건에서 전부 구현 단계 전에 동일한 사용량 창의 영향을 받았다고 기록한다.

이슈 #70 코멘트 두 건은 이 흐름을 스킬 밖에서 손으로 재현한 실측이다.

- 2026-09-04 재현: Codex author 개정 2회(40분 38초 + 21분 33초, `spec.md` 651 → 745 → 811행)와 fresh Codex readiness 심사 2회(116,316 tok + 94,866 tok)를 Claude 호출 0회로 수행했다. 산출물은 `.prior-art/.codex-author/prompt.md`, `.prior-art/.codex-readiness/{prompt.md,schema.json,run.sh}`, `.prior-art/.codex-readiness/result-attempt1.json`~`result-attempt5.json` 로 이 저장소에 보존돼 있다.
- 2026-09-05 재현: #42 4차 실행에서 Codex author 가 Spec 을 3회 개정(651 → 959행, 85분, Claude 토큰 0)했고 Claude 공식 점수는 74 → 78 → 83 으로 올랐다.

같은 실측이 이슈 본문의 `readiness score >= 90` 게이트를 반증한다. 대응점 두 개가 모두 같은 방향으로 크게 벌어졌다.

| readiness (fresh Codex) | Claude 공식 | 차이 | 증거 |
|---|---|---|---|
| 97점 READY, blocker 0 | 74점 REVISE, blocker 3 (High 3) | -23 | `.prior-art/.codex-readiness/result-attempt2.json`, `.prior-art/.codex-author/claude-spec-review-r1.json` |
| 94점, blocker 1 (Medium) | 78점 REVISE, blocker 0 (High 3) | -16 | `.prior-art/.codex-readiness/result-attempt4.json`, 이슈 #70 코멘트 2 |

두 심사는 서로 다른 것을 측정한다. readiness 는 "문서가 정합한가"를 보고, Claude 공식 리뷰는 "이 규칙들이 여러 실행에 걸쳐 돌 때 무엇이 깨지는가"를 본다. 임계값을 90에서 95로 올려도 97점짜리가 74점을 받는 상황은 변하지 않는다.

readiness 가 실제로 신뢰할 만하게 잡은 것과 놓친 것도 실측으로 갈렸다.

- 잡은 것: 템플릿 절 구조와 strict marker 쌍, 요구사항↔AC 추적표 무결성, 번호 연속성·중복, 직전 리뷰 findings 의 `required_resolution` 부분 해소 판정(`.prior-art/.codex-readiness/result-attempt4.json` 의 `READY-01`), author 개정 노트 주장의 기각(`.prior-art/.codex-readiness/prompt.md` 의 "노트는 근거가 아니라 검증 대상" 규칙이 두 번 작동).
- 놓친 것: 시간축·상태 전개를 따라가야 보이는 결함, 개별 수정이 만든 교차 회귀, 요구사항 본문과 Decisions 절의 정면 충돌. 전부 Claude 가 잡았다.

따라서 이 작업은 readiness 를 **참고용 심사**로 도입한다. 판정 대상은 문서에서 기계적으로 확인 가능한 여덟 항목이고, 결과는 공식 리뷰 컨텍스트에 근거로 첨부될 뿐 어떤 상태 전이도 결정하지 않는다.

### 종결된 두 실행과 이 목표의 관계

이 워크트리에는 같은 이슈 #70 에 대한 종결 실행이 둘 있고 둘 다 `NEEDS_REDESIGN` 이다. 이 목표는 **그 목표의 재시도가 아니라 축소된 요구사항의 새 목표**다.

| 실행 task_id | 종결 사유 | 마지막 blocker | 산출물 |
|---|---|---|---|
| `20260905T073930Z-70-quality-goal-spec-단계에-codex-author-fr-7ec207bb` | `REVIEW_LIMIT_EXHAUSTED:plan` | `PLAN-06` | Spec 92점 PASS(라운드 3), Plan 86 → 89 REVISE |
| `20260906T100138Z-70-quality-goal-spec-단계에-codex-author-fr-7ec207bb` | `REVIEW_LIMIT_EXHAUSTED:spec` | `SPEC-11` | Spec 82 → 87 → 82 REVISE |

두 실행의 리뷰 JSON·스냅숏·readiness 결과·개정 노트·보고서는 `.claude/quality-state/` 의 각 task 디렉터리와 `docs/development/2026-09-05-70-quality-goal-codex-spec-readiness/` 에 그대로 보존한다. 이 작업은 그 파일들을 삭제하거나 옮기지 않는다.

**이관 사유는 규모가 아니라 설계 난도다.** 2026-09-06 실행의 세 blocker 는 하나의 연쇄였다 — `SPEC-03`(readiness 게이트의 fail-open) → 그 해소가 만든 `SPEC-07`(최신 기록이 앞선 High 를 재판정한다는 보장 없음) → 그 해소가 만든 `SPEC-11`(닫힘이 기록 간에 누적되지 않아 세 번째 시도부터 게이트가 영구히 열리지 않는 고리). 세 건 모두 **상태 기계 의미론의 구멍**이며, v5.0.0 의 `revision_check.py` 가 잡는 대칭·참조 결손과는 다른 범주다(그 실행의 라운드 2·3 은 빈 칸 0 으로 제출됐다). 직전 실행의 `R4.5` 논쟁까지 포함하면 이 게이트 논리 하나에서 연속 네 개의 High 가 나왔다. 따라서 게이트 논리 전체를 이슈 #76 으로 옮기고, 그 전제 조건인 "잔여 blocker 를 공식 리뷰가 upheld/overruled 로 판정하는 계약" 과 함께 한 번에 설계한다.

이관 대상은 이슈 #70 의 2026-09-06 "범위 결정" 코멘트가 확정했다. 직전 Spec 의 식별자로 적으면 다음과 같다(전부 인용이며 이 Spec 에 정의가 없다).

| 이관 대상 | 직전 Spec 의 식별자 | 이 Spec 에서의 처리 |
|---|---|---|
| ARBITRATION/HOLD 전이와 탈출 경로 | `R4.4`, `R4.5`, `R4.8`, `R4.9` | 정의하지 않는다. Non-goal 12 |
| 게이트 판정 함수와 유효 Critical/High 집합 | `R6.10` | 정의하지 않는다. Non-goal 12 |
| 공식 리뷰 시작 조건의 코드 강제 | `R2.8` | 정의하지 않는다. R4.1 이 그 반대를 명시한다 |
| C8 의 "직전 리뷰" 를 상태 기록에서 유도하고 닫힘을 기록 간에 누적시키는 범위 규칙 | `C8` 의 범위 규칙, `R2.10` 의 게이트 연계 | C8 은 남기되 대상을 "프롬프트에 실린 findings 전문" 으로 좁힌다(R2.5, R3.1) |
| 시도 구간 한도와 그 강제 | `R4.1`, `R4.2` | 시도 수는 기록하되 한도를 강제하지 않는다(R4.3) |
| `readiness-gate`·`resume-readiness` 서브커맨드, `AWAITING_READINESS_DECISION` 상태, `readiness_decisions` 필드 | 직전 Spec § Interfaces | 정의하지 않는다. Non-goal 12 |

작업 대상 파일은 `dot_claude/skills/quality-goal/` 하위다. 이 저장소는 chezmoi source 이며 `~/.claude/skills/quality-goal/` 이 배포본이다. 결정적 검증 기준선은 base revision `6d60011cbdaead7946b191d3f12029eef5c141c8` 에서 Python 3.12 이상으로 실행한 310 테스트 통과다(실측: `/opt/homebrew/bin/python3` 3.14.7 에서 `Ran 310 tests ... OK`). 인터프리터 전제가 붙는 이유는 § Test strategy 와 R9.8 에 있다.

## Goals

1. standard·strict 모드의 `SPEC_REVIEW` 단계에서 Spec 의 초안 작성과 모든 개정을 Codex author 가 수행하고, Claude 오케스트레이터는 Spec 본문을 직접 쓰지 않는다.
2. author 와 분리된 fresh Codex 프로세스가 Claude 공식 리뷰 전에 readiness 를 심사하고, 그 결과를 기계적으로 확인 가능한 여덟 항목 체크리스트로 표현한다.
3. readiness 결과·미충족 항목·잔여 finding 전문을 Claude 공식 리뷰 컨텍스트에 근거로 첨부한다.
4. readiness 는 어떤 상태 전이도 결정하지 않는다. 공식 리뷰 라운드를 소모하지도, 그 시작을 막지도 않는다.
5. 이슈 #70 코멘트에 기록된 실무 함정(비대화형 stdin 무한 대기, `--output-schema` 의 `const` 거부, 시도 번호 상한 충돌, 심사 대상 오지정)을 계약으로 고정해 재발을 막는다.
6. 상태 스키마를 확장하되 schema v1 상태 파일과 진행 중 goal 재개를 데이터 손실 없이 유지한다.
7. 기존 공식 게이트(`score >= 85`, Critical/High 0, blocker 0)와 라운드 한도(Spec 3 / Plan 2 / Code 3), 승인 digest, dirty-worktree 보호, 결정적 검증 계약이 회귀하지 않는다.

## Non-goals

1. Plan 단계로의 확장(#70 2단계). 이 작업은 Plan 의 author·readiness 를 도입하지 않는다.
2. eval fixture 추가와 비용·호출 수 측정(#70 3단계). `evals/evals.json` 은 손대지 않는다.
3. Code 단계 변경. Codex 구현 → 결정적 검증 → Claude 공식 코드 리뷰 → Codex 수정 계약은 현행 그대로다.
4. 상태 머신 전체의 Python controller 이관. `quality_state.py` 는 상태 헬퍼로 남고 호출 주체는 Claude 오케스트레이터다.
5. readiness 점수 임계값 결정. 점수는 기록만 하고 어떤 판정에도 쓰지 않으므로 임계값 자체가 존재하지 않는다.
6. Claude 공식 리뷰 계약 변경. 루브릭, 점수 임계 85, `REQUIRED_CHECKS`, finding severity 정의, 라운드 한도는 그대로다.
7. #60 의 Plan 라운드 2→3 변경. 현행 2회를 유지한다.
8. Code 단계 readiness 사전 심사(#70 코멘트 1 이 후속 검토 여지로 남긴 항목).
9. `chezmoi apply` 실행과 배포본 갱신. 이 작업은 chezmoi source 만 변경하며 배포는 사용자가 별도로 수행한다.
10. `.gitignore` 변경. 런타임 상태 경로는 이미 `.gitignore:25` 로 무시되므로 손댈 이유가 없다.
11. readiness 잔여 blocker 를 Claude 공식 리뷰가 upheld/overruled 로 판정하는 계약. `schemas/review.schema.json` 의 finding 구조와 `verdict` enum 을 함께 바꿔야 하므로 별도 작업이며 이슈 #76 이 추적한다.
12. **readiness 게이트 논리 전체.** § Problem and context 의 이관 표가 열거한 것 — 게이트 판정 함수, 유효 Critical/High 집합, 시도 구간 한도의 강제, `AWAITING_READINESS_DECISION` 상태와 그 전이 가드, `readiness-gate`·`resume-readiness` 서브커맨드, `readiness_decisions` 필드, 공식 리뷰 시작 조건의 코드 강제 — 는 이 작업의 범위 밖이며 이슈 #76 이 추적한다. 이 Spec 은 그것들을 정의하지도, 그것들이 있을 자리를 예약하지도 않는다. #76 이 나중에 추가할 때 이 Spec 이 만든 기록 필드(R6.1)를 입력으로 쓸 수 있다는 것이 이 분리의 전제다.
13. 두 종결 실행의 산출물 정리·이동·삭제. 그 파일들은 근거로 보존한다.

## Requirements

### R1. Codex Spec author

- **R1.1** standard·strict 모드의 `SPEC_REVIEW` 단계에서 Spec 초안 작성과 이후 모든 개정은 Codex author 프로세스가 수행한다. Claude 오케스트레이터는 `spec.md` 본문을 직접 작성하거나 편집하지 않는다.
- **R1.2** 오케스트레이터는 author 호출 전에 `references/brainstorming-policy.md` 에 따른 요구사항 발굴을 수행하고, 그 결과(문제·목표·비목표·제약·저장소 근거 경로)를 author 프롬프트에 담는다. 발굴에서 남은 물질적 모호성은 author 호출 **전에** 사용자에게 질의해 해소한다.
- **R1.3** author 는 `codex exec` 로 호출한다. 필수 인자는 `-C <project_root>`, `--sandbox workspace-write`, `--ephemeral`, `--model <route model>`, `-c model_reasoning_effort="<route effort>"`, `--output-schema <codex-result 스키마>`, `--output-last-message <result path>`, `--json`, 그리고 표준 입력으로 주는 프롬프트 파일 아홉이다.
- **R1.4** author·readiness 호출은 설치된 Codex CLI 가 노출하는 승인 우회·권한 확장 옵션을 사용하지 않는다. codex-cli 0.153.4 기준으로 그 목록은 `--skip-git-repo-check`, `--dangerously-bypass-approvals-and-sandbox`, `--dangerously-bypass-hook-trust`, `--approve-for-me`, `--ignore-rules`, `--ignore-user-config`, `--add-dir`, `--yolo` 여덟이며, `--sandbox` 에 그 호출의 지정값보다 넓은 값을 주는 것도 금지한다. `--yolo` 는 `codex exec --help` 에 나오지 않지만 실제로 수용된다 — `codex exec --yolo --version` 이 `codex-cli-exec 0.153.4` 를 출력하는 반면 존재하지 않는 플래그는 사용법 안내를 낸다. `--help` 출력만으로 금지 목록을 만들면 이 숨은 별칭을 놓친다. 같은 버전에서 `--full-auto` 는 존재하지 않는 플래그와 같은 반응을 보인다. 또한 `codex exec` 에는 `-a`/`--ask-for-approval` 이 존재하지 않으므로 이 스킬의 어떤 문서도 `codex exec` 호출에 그 플래그를 지시하지 않는다. 이 금지는 호출 계약에 그치지 않고 문서 표현에도 성립해야 한다 — 검사 대상 문서에서 이 플래그 문자열이 나타나는 모든 위치가 금지 문언과 같은 문단 안이어야 하고, 실행 가능한 호출 템플릿(펜스 코드 블록) 안에는 한 번도 나타나지 않아야 한다. 그래야 금지 목록이 복사·붙여넣기로 실행 가능한 명령이 되는 경로가 닫힌다. 이 금지의 열거는 CLI 버전과 함께 `references/readiness-policy.md` 에 싣는다. `SKILL.md` 의 기존 Safety rules 문언은 바꾸지 않는다 — 그 절은 이미 세 플래그 열거와 `Sandbox bypass is prohibited.` 라는 포괄 금지를 함께 담고 있어(`SKILL.md:391-392`) 새 플래그를 추가하지 않아도 포괄 금지가 성립하며, R9.5 가 그 절의 불변을 요구한다.
- **R1.5** author 프롬프트는 다음 **열둘**을 모두 포함한다: 개정 대상 Spec 파일의 절대 경로, `templates/spec.md` 절대 경로, `references/spec-rubric.md` 절대 경로, `references/brainstorming-policy.md` 절대 경로, `references/revision-check-policy.md` 절대 경로, 반영할 findings 전문의 경로, 기존 요구사항·AC 번호 보존과 신설 번호 이어붙이기 규칙, 그 정책이 정의한 식별자 문법(`- **R<n>.<m>**`, `- **AC-<n>**`, `[실행]`·`[문서]`, 추적표, 판정 명령 표)을 지키라는 지시, 개정 노트 파일 경로, 라운드 2 이상에서 개정 노트가 갖춰야 할 형식, git 쓰기 명령 금지, 그리고 개정 완료 직전의 조합 검토 지시. 앞의 다섯 경로는 절대 경로여야 한다. 개정 노트 형식은 `references/revision-check-policy.md` 에서 그대로 인용한다 — 라운드 `<n>` 의 절 헤딩 `## 라운드 <n> 개정` 과 다섯 열 표 머리 `| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |` 다. **한 공식 라운드에는 그 라운드의 절이 정확히 하나 있다.** 같은 라운드 안에서 readiness 개정이 반복되면 새 절을 만들지 않고 그 하나의 절에 행을 누적하고, 이미 있는 행의 판정이 바뀌면 그 행을 갱신한다. 그 절이 다루는 범위는 직전 라운드의 스냅숏(`snapshots/<artifact>-r<N-1>.md`) 이후의 모든 변경이며, readiness 가 유발한 변경도 거기 포함된다. 이 열둘 중 식별자 문법 지시, 개정 노트 경로, 개정 노트 형식, 조합 검토 지시 넷을 넣지 않으면 base revision 이 이미 강제하는 개정 점검(`scripts/revision_check.py`)이 라운드 2 이상에서 종료 코드 0 을 내지 못해 `record-review --revision-check` 가 거부되고, 그 복구를 오케스트레이터가 본문으로 하려 들면 R1.1 이 금지한 작성 주체 이전이 된다.
- **R1.6** author 는 대상 Spec 파일과 개정 노트 파일 두 개 외의 파일을 수정하지 않는다. 프롬프트가 그 제약을 명시하고, 오케스트레이터가 호출 후 `git status --porcelain` 으로 확인한다. 비교 대상은 상태의 `initial_dirty_paths` 와 `.claude/quality-state/<task-id>/` 하위를 **제외한** 경로이며, 그 결과를 author 결과의 `changed_files` 와 대조한다. 이 제외 규칙이 없으면 dirty 상태에서 시작한 모든 goal 이 author 호출마다 오탐으로 § Failure behavior 의 사용자 판단 요청 경로에 빠진다. 기존 스킬의 dirty-path 보존 계약(`SKILL.md:361-364`, `initial_dirty_paths`)과 같은 기준이다.
- **R1.7** author 의 조합 검토 지시는 "이번 개정이 직전 개정에서 세운 계약과 충돌하거나 새 결손을 만들지 않는지 마지막에 한 번 교차 점검한다"를 포함하고, 그 근거로 개별 해소가 교차 회귀를 만든 전례(#42 실행 계열의 `PLAN-009`·`PLAN-010`·`PLAN-012`·`SPEC-31`·`SPEC-34`)를 인용한다.
- **R1.8** author 호출 횟수는 상태의 `draft_attempts` 에 artifact 별로 기록하며 `rounds` 의 어떤 값도 바꾸지 않는다.
- **R1.9** author 호출이 0 이 아닌 종료 코드를 반환하거나, 결과 파일이 없거나, 결과가 `schemas/codex-result.schema.json` 검증에 실패하거나, 호출 전후 대상 Spec 파일의 SHA-256 이 같으면 개정 실패로 간주한다. 오케스트레이터는 `SPEC_REVIEW` 단계에 머문 채 실패 내용을 사용자에게 보고하고 모델을 임의로 대체하지 않는다. 모델 거부는 기존 `BLOCKED_MODEL_UNAVAILABLE` 복구 경로를 따른다.

### R2. fresh Codex readiness reviewer

- **R2.1** readiness reviewer 는 author 와 별개의 `codex exec` 프로세스로 실행한다. author 의 대화 문맥·세션·개정 노트의 주장을 근거로 상속하지 않는다.
- **R2.2** readiness reviewer 호출은 `--sandbox read-only` 를 사용하고 R1.4 가 금지한 옵션을 쓰지 않는다. 프롬프트는 reviewer 가 읽기 전용이며 파일 수정과 git 쓰기 명령이 금지된다는 것을 명시한다.
- **R2.3** author 와 readiness 호출은 표준 입력이 대화형 터미널에 연결되지 않게 한다. 기본 형태는 프롬프트 파일을 표준 입력으로 주는 것(`- < "$PROMPT_PATH"`)이고, 프롬프트를 명령행 인자로 넘기는 형태를 쓸 때는 `< /dev/null` 을 붙인다. 둘 중 어느 형태도 아닌 호출은 금지한다. 비대화형에서 stdin 을 열어두면 `Reading additional input from stdin...` 에서 무한 대기한다(이슈 #70 코멘트 1, 함정 2).
- **R2.4** readiness 결과 스키마의 모든 property 는 `type` 키를 갖는다. `const` 키는 사용하지 않는다. `codex exec --output-schema` 는 `const` 만 있는 property 를 `invalid_json_schema` 400 으로 거부한다(이슈 #70 코멘트 1, 함정 1). 고정값이 필요한 곳은 `{"type": "string", "enum": ["spec"]}` 형태로 쓴다.
- **R2.5** readiness reviewer 프롬프트는 넷을 명시한다 — ① 개정 노트는 근거가 아니라 검증 대상이며 노트가 반영했다고 적은 것을 Spec 본문에서 파일:행으로 확인한다, ② 이 판정은 **참고용**이며 Claude 공식 판정을 대체하지도 그 시작을 막지도 않는다, ③ 설계 취향 문제로 감점하지 않는다, ④ C8 의 검증 대상인 직전 리뷰 findings 전문의 경로. ④는 같은 공식 라운드의 직전 readiness 시도 결과 JSON 경로와 직전 Claude 공식 리뷰의 open findings 경로 둘이며, 각 finding 의 ID·severity·`required_resolution` 이 프롬프트에서 읽을 수 있어야 한다. 프롬프트는 그 ID 들이 **참조**이고 reviewer 자신의 finding 은 `READY-` 로 **발급**해야 한다는 R7.1 의 구분을 함께 명시한다. ④는 R2.1 의 문맥 상속 금지와 구분된다 — **금지 대상은 author 의 대화 문맥·세션·개정 노트의 주장이고, 리뷰어 산출물의 파일 전달은 허용이다.** 전자는 "고쳤다" 는 저자의 주장이고 후자는 독립 심사가 남긴 판정이기 때문이다.

### R3. 여덟 항목 체크리스트

- **R3.1** readiness 판정은 다음 여덟 항목 전부 충족이고 Critical/High severity 의 finding 이 하나도 없을 때만 `READY` 다. 항목 하나의 충족은 `pass` 또는 `not_applicable` 이고 `fail` 만 미충족이다. 하나라도 미충족이거나 Critical/High 가 하나라도 있으면 `REVISE` 다. 각 항목은 `status`(`pass`/`fail`/`not_applicable`)와 판정 근거(파일:행 또는 미확인 사유)를 함께 기록한다.
  - **C1** 템플릿 절 구조 준수: `templates/spec.md` 의 필수 절이 모두 존재하고 순서가 유지된다.
  - **C2** strict marker 쌍: `templates/spec.md` 가 strict 전용 구간의 시작과 끝을 표시하는 데 쓰는 두 HTML 주석이 산출물에서 짝을 이루거나, non-strict 산출물에서 둘 다 없다. 한쪽만 남은 상태는 미충족이다. 판정에 쓸 정확한 주석 문자열은 `references/readiness-policy.md` 가 템플릿에서 그대로 인용해 정의한다.
  - **C3** 요구사항 정의 수와 추적표 행 수가 같다.
  - **C4** 추적표에 누락·중복·유령 참조가 0 이다. 유령 참조는 추적표가 가리키는 요구사항 번호나 AC 번호가 본문에 정의되지 않은 경우다.
  - **C5** 모든 AC 에 판정 수단이 배정돼 있다. 판정 수단은 `[실행]` 명령 또는 `[문서]` 위치 중 하나다.
  - **C6** AC 번호가 연속이고 고유하다.
  - **C7** 모든 `[실행]` 판정 명령이 판정 명령 표에 등재돼 있다.
  - **C8** **프롬프트에 실린 직전 리뷰 findings 전문**(R2.5 ④) 각각에 대해 `required_resolution` 이 Spec 본문에서 확인되는지 판정한다. 판정 대상 하나마다 결과의 `prior_findings` 에 ID·출처·판정(`resolved`·`unresolved`·`partial`)·근거를 한 항목으로 남기고, 판정이 `resolved` 인 것의 ID 만 `resolved_finding_ids` 에 싣는다. 부분 해소는 `partial` 이며 미충족이다. 이 자리의 ID 는 발급이 아니라 참조이므로 `SPEC-` 접두를 그대로 쓴다(R7.1). 프롬프트에 findings 가 하나도 실리지 않았으면 `prior_findings` 는 빈 배열이고 이 항목은 자동 충족이다. **판정 대상은 프롬프트가 실은 것이 전부이며, 상태 기록을 훑어 대상을 유도하지 않는다.**
- **R3.2** readiness 결과의 `score` 는 기록 전용 참고값이다. 어떤 판정·기록 거부·상태 전이에도 사용하지 않으며, `quality_state.py` 와 `validate_review.py` 의 어떤 분기도 그 값을 읽지 않는다.
- **R3.3** 체크리스트 항목은 전부 문서에서 기계적으로 확인 가능한 것만으로 구성한다. 설계 정합성·아키텍처 타당성·시간축 전개 판정은 체크리스트에 넣지 않는다.

### R4. readiness 의 비권위성과 시도 기록

- **R4.1** readiness 는 어떤 상태 전이도 결정하지 않는다. 구체적으로 셋이다 — ① readiness 기록은 `rounds` 의 어떤 값도 바꾸지 않는다, ② readiness 를 한 번도 실행하지 않았거나 마지막 결과가 `REVISE` 여도 `record-review`·`record-review-unverified`·`record-review-error` 는 spec 리뷰 기록을 거부하지 않는다, ③ readiness 결과를 이유로 새 stage 로 전이하거나 종료 상태를 만들지 않는다. 이 작업은 `ALLOWED_TRANSITIONS` 와 `TERMINAL_STATES` 를 바꾸지 않는다.
- **R4.2** readiness 결과 스키마의 `attempt` 는 실행 전체 누적 번호이며 상한을 두지 않는다. 스키마에 `maximum` 을 넣지 않는다. 누적 번호를 라운드당 한도와 혼동해 스키마 제약으로 옮기면 심사자가 지시와 스키마의 충돌을 blocker 로 올리고 score 0 을 반환한다(이슈 #70 코멘트 2, 함정 4; `.prior-art/.codex-readiness/result-attempt5.json`).
- **R4.3** 라운드당 readiness 시도 한도를 코드로 강제하지 않는다. 시도 수는 상태 기록에서 셀 수 있지만 어떤 명령도 그 수를 이유로 호출을 거부하지 않는다. 절차 문서는 결과가 `READY` 이면 그 라운드의 추가 시도를 하지 않는다는 것과, 비용 상한은 오케스트레이터가 사용자 지시에 따라 정한다는 것을 명시한다.
- **R4.4** 오케스트레이터는 Claude 공식 Spec 리뷰 컨텍스트에 **저장소 근거 경로 둘**을 첨부한다 — ① 마지막 readiness 결과 JSON 의 절대 경로, ② 미충족 체크리스트 항목 목록과 잔여 finding 전문을 담은 요약 파일 `.claude/quality-state/<task-id>/readiness-evidence-spec-r<N>.md` 의 절대 경로. **둘 다 파일 경로로 전달하고 내용을 리뷰어 프롬프트에 인라인하지 않는다.** 형태를 경로로 고정하는 이유는 `SKILL.md` § Review invocation contract 가 리뷰어 입력을 `repository evidence paths` 를 포함한 목록으로 한정하는데 그 절이 R9.5 의 바이트 단위 보존 대상이기 때문이다 — 내용을 인라인하면 보존 대상 절을 고치지 않고는 그 한정을 지킬 수 없다. 첨부는 근거 제공이며 리뷰어의 판정을 구속하지 않는다. readiness 를 실행하지 못했거나 유효한 결과가 없으면 그 사실을 ②의 요약 파일에 적는다.

### R5. 심사 대상과 등록 아티팩트의 digest 대조

- **R5.1** 이 Spec 에서 **등록 digest** 는 `artifacts[artifact]` 가 가리키는 파일의 현재 SHA-256 을 뜻한다. 상태의 `artifact_digests` 필드는 `record-review` 가 기록하는 직전 공식 리뷰 시점의 값이며 이 대조에 쓰지 않는다. readiness 호출 전에 심사 대상 Spec 의 절대 경로가 `artifacts.spec` 과 같은지 확인하고, 다르면 호출하지 않는다. 심사 대상 파일의 현재 SHA-256 을 계산해 프롬프트에 싣고, 그 값을 심사 시점 digest 로 기록한다.
- **R5.2** `record-readiness` 는 `--artifact-digest` 가 등록 digest 와 다르면 호출 자체를 거부한다. 호출이 정상 종료한 경우, readiness 결과의 `artifact_digest` 가 심사 시점 digest 와 다르면 그 결과를 유효 심사로 채택하지 않고 `outcome` 이 `digest_mismatch` 인 실패 기록으로 남긴다. 호출 자체가 실패했으면 R6.6 의 순서에 따라 `invocation_failed` 가 우선한다.
- **R5.3** R5.1 또는 R5.2 위반은 `SPEC_REVIEW` 단계를 유지한 채 사용자에게 보고한다. 근거는 실행 중 다른 디렉터리의 옛 Spec 을 심사할 뻔한 사례다(이슈 #70 코멘트 2, 함정 5).

### R6. 상태 기록과 재개 호환성

- **R6.1** 상태에 readiness 전용 필드를 추가한다. 기록 단위는 시도 하나이며 다음 열둘을 포함한다: `attempt`(실행 누적 번호), `formal_round`, `outcome`, `verdict`, `score`, `checklist`, `findings`, `resolved_finding_ids`(결과의 배열을 그대로 복사한다), `artifact_digest`(심사 시점 digest), `reviewer_model`, `result_path`, `recorded_at`. `formal_round` 는 입력값이 아니라 상태에서 유도되는 값이며 `rounds[artifact] + 1` 이다. `record-readiness` 가 `--formal-round` 를 받는 경우 유도값과 다르면 호출을 거부한다. 결과 파일의 `prior_findings`(R8.4)는 상태에 복사하지 않는다 — 이관된 게이트의 입력이 아니며 `result_path` 가 가리키는 결과 파일에 그대로 남는다. 기록은 이력이며 어떤 판정에도 쓰이지 않는다 — 이슈 #76 이 게이트를 설계할 때의 입력이 될 뿐이다.
- **R6.2** 상태에 추가하는 필드는 `readiness` 와 `draft_attempts` **둘뿐**이다. `init` 은 두 필드를 빈 값(`{"spec": [], "plan": []}` 과 `{"spec": 0, "plan": 0}`)으로 만든다.
- **R6.3** schema v1 상태 파일을 읽을 수 있어야 한다. R6.2 의 두 필드가 없는 상태는 readiness 미실행·author 미호출로 간주한다. **읽는 시점에 두 필드를 상태 파일에 주입하지 않는다.** 각 필드는 그것을 처음 쓰는 명령(`record-readiness`, `record-draft-attempt`)이 생성한다.
- **R6.4** 진행 중 goal 을 재개할 때 기존 `rounds`, `reviews`, `open_finding_ids`, `plan_approval`, `revision_checks` 와 승인 digest 를 초기화하지 않는다. `revision_checks` 는 base revision 이 이미 갖는 필드이며(v5.0.0), 이 작업은 그 값을 읽지도 쓰지도 않는다.
- **R6.5** `SPEC_REVIEW` 를 벗어나는 전이(`SPEC_PASSED`, `NEEDS_REDESIGN`, `BLOCKED`, `CANCELLED`)는 readiness 기록과 `draft_attempts` 를 삭제하지 않는다.
- **R6.6** readiness 기록에 `outcome` 필드를 둔다. 값은 넷이다 — `recorded`(스키마 검증과 digest 대조를 모두 통과한 유효 심사), `schema_invalid`, `digest_mismatch`, `invocation_failed`(`codex exec` 비정상 종료, 결과 파일 미생성, 타임아웃). 실패 기록의 표현은 다음으로 고정한다: `verdict` 와 `score` 는 `null`, `checklist`·`findings`·`resolved_finding_ids` 는 빈 배열, 나머지 필드(`attempt`, `formal_round`, `outcome`, `artifact_digest`, `reviewer_model`, `result_path`, `recorded_at`)는 채운다. `outcome` 은 호출자가 고르는 값이 아니라 입력으로부터 결정된다. `record-readiness` 는 `--invocation-status <ok|failed>` 와 `--stderr-path` 를 받으며, `failed` 이면 결과 파일 유무와 무관하게 `invocation_failed` 로 기록하고 `result_path` 에 표준 오류 파일 경로를 넣는다. `ok` 이면 스키마 검증과 digest 대조 순으로 판정해 `schema_invalid`·`digest_mismatch`·`recorded` 중 하나가 된다. 이 순서가 없으면 결과 파일이 남은 비정상 종료를 `schema_invalid` 와 구별할 수 없다. 두 입력에는 거부 계약이 붙는다 — `--invocation-status` 는 `ok` 와 `failed` 두 값만 허용하고 그 밖의 값은 호출을 거부하며, `--invocation-status failed` 인데 `--stderr-path` 가 없거나 그 경로가 존재하지 않으면 호출을 거부한다. `record-readiness` 는 `outcome` 자체를 인자로 받지 않는다. 이 작업이 추가하는 두 서브커맨드(`record-readiness`, `record-draft-attempt`)는 `light` 모드 상태에서 모두 오류로 거부한다 — light 는 `SPEC_REVIEW` 를 거치지 않으므로 정상 경로에서 호출될 일이 없고, 조용히 무시하면 잘못된 호출이 드러나지 않는다.

### R7. finding 식별자 네임스페이스

- **R7.1** readiness 결과에서 **finding ID 를 발급하는 자리**(`findings[].id` 와 그것을 가리키는 `blockers`)는 `READY-` 접두만 허용하고, **직전 리뷰의 finding 을 참조하는 자리**(`prior_findings[].id` 와 그 판정 결과인 `resolved_finding_ids`)는 `READY-` 와 `SPEC-` 두 접두를 모두 허용한다. 곧 금지되는 것은 readiness 가 `SPEC-` 로 **새 finding 을 발급**하는 것이지 공식 finding 을 **참조**하는 것이 아니다. 이 구분은 서술이 아니라 결과 스키마의 패턴 제약으로 드러난다(R8.4). 두 자리를 한 규칙으로 묶으면 C8 이 요구하는 판정 — 직전 Claude 공식 리뷰의 `SPEC-nn` finding 이 해소됐는지 보고하는 것 — 을 담은 정상 결과가 검증에서 거부돼 `schema_invalid` 실패 기록이 된다.
- **R7.2** readiness finding 이 특정 공식 finding 에 대응하면 그 대응 관계를 `description` 에 기록한다. finding ID 는 하나의 개정 주기 안에서 안정적이다 — 같은 물질적 문제가 남으면 같은 ID 를 유지하고, 구별되는 새 문제에만 새 ID 를 매긴다.

### R8. readiness 결과 계약

- **R8.1** 결과 스키마는 다음 열세 필드를 필수로 요구하고 그 밖의 필드를 required 로 두지 않는다: `artifact`, `attempt`, `formal_round`, `score`, `verdict`, `checklist`, `blockers`, `findings`, `prior_findings`, `evidence`, `required_next_action`, `artifact_digest`, `resolved_finding_ids`. 최상위 `type` 은 `object` 이고 `additionalProperties` 는 `false` 다. `artifact_digest` 는 소문자 SHA-256 64자 패턴으로 제약하고, `verdict` 는 `READY` 와 `REVISE` 두 값만 허용한다.
- **R8.2** `score` 는 `references/spec-rubric.md` 의 가중치로 실제 계산한 0~100 정수다. 프롬프트는 "blocker 가 있다고 0 을 넣지 마라"를 명시한다.
- **R8.3** `evidence` 는 최소 6건이며 각 항목은 `claim`, `location`, `verified` 셋을 갖는다. `verified` 가 `true` 인 항목의 `location` 은 `<경로>:<행>` 형식이고, `false` 인 항목의 `location` 에는 확인하지 못한 사유를 적는다. 프롬프트 계약이 이 규칙을 명시해, 확인하지 못한 것을 확인한 것처럼 적는 경로를 닫는다.
- **R8.4** `checklist` 는 C1~C8 여덟 항목을 모두 포함하고 각 항목은 `id`, `status`, `evidence` 를 갖는다. `status` 는 `pass`·`fail`·`not_applicable` 셋만 허용한다. R7.1 의 발급·참조 구분은 스키마의 네 패턴 제약으로 드러난다 — `findings[].id` 와 `blockers[]` 는 `^READY-` 를, `prior_findings[].id` 와 `resolved_finding_ids[]` 는 `^(READY-|SPEC-)` 를 만족해야 한다. `prior_findings` 는 항목마다 `id`, `source`(`readiness`·`formal`), `judgement`(`resolved`·`unresolved`·`partial`), `evidence` 를 갖는 배열이며 빈 배열을 허용한다. `resolved_finding_ids` 는 문자열 배열이고 빈 배열을 허용하며, 그 값의 집합은 `judgement` 가 `resolved` 인 `prior_findings` 항목의 ID 집합과 정확히 같아야 한다.
- **R8.5** 호출이 정상 종료한 경우, 결과가 스키마 검증에 실패하면 그 결과를 유효 심사로 채택하지 않고 `outcome` 이 `schema_invalid` 인 실패 기록으로 남긴다. 오케스트레이터는 검증 오류를 사용자에게 보고한다.

### R9. 문서·계약 회귀 방지

- **R9.1** `SKILL.md` 파일 전체가 500행 미만을 유지한다. 현재 393행이며 `tests/test_content_contracts.py:1244` 가 frontmatter 를 포함한 파일 전체를 대상으로 검사한다(`assertLess(len(text.splitlines()), 500)`). readiness 절차의 상세는 새 `references/readiness-policy.md` 로 분리하고 `SKILL.md` 에는 단계 절차와 참조 경로만 싣는다.
- **R9.2** `templates/spec.md` 에 요구사항 추적표 절과 판정 명령 표 절을 추가한다. 두 절의 계층과 위치를 고정한다 — 추적표는 최상위 `## Requirements traceability` 로 `## Acceptance criteria` 바로 뒤·`## Architecture` 바로 앞에 놓고, 판정 명령 표는 `## Test strategy` 안의 `### 판정 명령 표` 로 그 절의 첫 하위 절에 놓는다. 위치를 고정하지 않으면 C1(필수 절의 존재와 순서)과 공식 게이트의 `required_sections` 판정이 구현자의 임의 선택에 좌우된다. C3·C4·C5·C7 은 이 두 표가 있어야 판정 가능하다.
- **R9.3** `docs/quality-goal-maintenance.md` 에 readiness 관련 점검 항목(`codex exec` 플래그, readiness 결과 스키마, author·reviewer 라우팅 모델, `references/model-routing.md` 와 `references/readiness-policy.md` 의 동기화)을 추가하고, 그 문서의 기존 `## 결정적 테스트` 절을 `## 판정 명령 표` 절로 **대체**한다. 새 절은 CMD-1~CMD-7 일곱 행을 싣고 그 바로 아래에 R9.8 의 최소 인터프리터 버전과 두 근거를 함께 싣는다. 병기가 아니라 대체인 이유는, 옛 절이 버전 가드 없는 `python3 -m unittest discover` 를 그대로 싣고 있어 남겨 두면 같은 명령이 두 곳에 서로 다른 형태로 존재하고 어느 쪽이 정본인지 알 수 없게 되기 때문이다. 이 절이 판정 명령 표의 정본이다.
- **R9.4** 기존 310개 테스트가 모두 통과하고 그 테스트 이름 집합이 보존되며, 신규 계약마다 판정 수단을 배정한다. 기본은 `tests/` 의 결정적 테스트이고, 문서 문언의 존재 여부만으로 확인되는 일곱 건(AC-28, AC-31, AC-35, AC-39, AC-44, AC-62, AC-76)은 `[문서]` 판정 수단을 쓴다.
- **R9.5** Plan 단계와 Code 단계의 기존 계약(라운드 한도 Spec 3 / Plan 2 / Code 3, `REQUIRED_CHECKS`, 공식 게이트 `score >= 85`, 승인 digest, dirty-worktree 보호, 결정적 검증, 개정 후 자기 회귀 점검)은 변경하지 않는다. `SKILL.md` 의 여덟 보존 대상 절(§ Test strategy 의 CMD-4 상세)이 base revision 대비 바이트 단위로 같아야 한다.
- **R9.6** `SKILL.md` frontmatter 의 `version` 을 유지보수 문서의 SemVer 정책에 따라 올린다. 상태 기록 계약이 확장되므로 MINOR 이상이다.
- **R9.7** author·readiness 라우팅 모델을 `references/model-routing.md` 의 라우트 표에 추가한다. standard 는 author `gpt-5.6-terra` high, strict 는 author `gpt-5.6-sol` high 이며, readiness reviewer 는 두 모드 모두 fresh `gpt-5.6-sol` high 다. 두 파일의 역할은 이렇게 나눈다 — `references/model-routing.md` 는 역할별 모델·effort 값과 실행 가능한 호출 템플릿을 담고, `references/readiness-policy.md` 는 그 템플릿을 인용하며 절차 문맥(언제 부르고 무엇을 프롬프트에 싣고 결과를 어떻게 기록하는지)을 담는다.
- **R9.8** 판정 명령은 실행 환경 전제를 명시하고 명령 자체가 그 전제를 확인한다. 테스트 스위트는 **Python 3.12 이상**을 요구한다. 두 가지 이유가 겹친다. 첫째, `tests/test_quality_state.py` 의 `ResumeSelectionTests` 가 `unittest.TestCase.enterContext` 를 쓰는데 그 API 는 3.11 에서 추가됐다 — 실측으로 `/usr/bin/python3` 3.9.6 은 310건 중 23건이 오류로 종료 코드 1 을 내고 `/opt/homebrew/bin/python3` 3.14.7 은 `OK` 다. 둘째, `unittest` 가 `-k` 필터에 아무것도 매칭되지 않을 때 종료 코드 5(`NO TESTS RAN`)를 내는 동작은 3.12 에서 도입됐다 — 실측으로 3.12.14 와 3.14.7 은 5 를, 3.9.6 은 0 을 반환한다. 3.12 미만에서는 CMD-2 가 존재하지 않는 테스트 이름에도 성공을 반환해 대부분의 AC 가 공허하게 통과한다. 그 전제 확인은 저장소 파일 셋으로 둔다 — CMD-1·CMD-2·CMD-7 이 공유하는 `tests/assert_python_version.py`, CMD-4 의 `tests/assert_preserved_sections.py`, CMD-6 의 `tests/assert_tests_preserved.py` 이며, 셋 다 파일명이 `test_` 로 시작하지 않아 `unittest` 수집 대상이 아니다. 버전 가드를 파일 하나로 모으는 이유는 가드가 명령마다 인라인으로 복제되면 CMD-1 에서 가드를 빼도 CMD-7 이 통과하기 때문이다. `tests/assert_python_version.py` 는 판정을 `is_supported(version_info) -> bool` 로 노출하고 `__main__` 이 그 함수로 분기한다. 3.12 미만 인터프리터가 없는 환경에서는 CMD-7 을 실행할 수 없으므로, 그 함수의 경계값 동작(`(3, 11, x)` 는 `False`, `(3, 12, 0)` 은 `True`)을 CMD-2 로 직접 판정해 거부 분기가 어떤 환경에서도 미판정으로 남지 않게 한다.

## Acceptance criteria

판정 수단 표기는 두 가지다. `[실행]` 은 판정 명령 표(§ Test strategy)에 등재된 명령으로 판정하며, 괄호 안은 그 명령의 식별자와 테스트 이름이다. `[문서]` 는 지정한 파일의 지정한 절에 해당 문언이 존재하는지로 판정한다.

- **AC-1** `SKILL.md` 의 Spec 단계 절차가 Spec 초안과 개정의 실행 주체를 Codex author 로 지정하고, 오케스트레이터가 Spec 본문을 직접 쓰지 않는다고 명시한다. [실행] (CMD-2 `test_spec_authoring_is_delegated_to_codex_contract`)
- **AC-2** `references/readiness-policy.md` 가 author 호출 전 요구사항 발굴 수행과 그 결과의 프롬프트 반영을 요구한다. [실행] (CMD-2 `test_author_prompt_required_elements_contract`)
- **AC-3** `references/readiness-policy.md` 가 요구사항 발굴에서 남은 물질적 모호성을 author 호출 **전에** 사용자 질의로 해소하도록 요구한다. [실행] (CMD-2 `test_author_prompt_required_elements_contract`)
- **AC-4** `references/readiness-policy.md` 의 author 호출 템플릿이 R1.3 의 아홉 요소를 모두 포함한다. [실행] (CMD-2 `test_author_invocation_template_contract`)
- **AC-5** R1.4 가 열거한 여덟 옵션과 `--full-auto` 가 검사 대상 파일에 나타나는 모든 위치가 금지 문언 안이다. 판정 규칙은 기계적이다 — 검사 대상은 `dot_claude/skills/quality-goal/` 하위의 `.md` 파일 전부와 `docs/quality-goal-maintenance.md` 이고, 문단은 빈 줄로 구분된 연속 줄 묶음이며, 금지 표현 토큰은 `금지`·`사용하지 않는다`·`쓰지 않는다`·`forbidden`·`prohibited` 다섯이다. 각 플래그 문자열을 포함한 줄이 속한 문단에 그 토큰이 하나 이상 있어야 하고, 플래그 문자열이 펜스 코드 블록 안에는 한 번도 나타나지 않아야 한다. [실행] (CMD-2 `test_forbidden_codex_flags_contract`)
- **AC-6** `references/readiness-policy.md` 의 금지 목록이 R1.4 의 여덟 이름(`--yolo` 포함)을 모두 포함하고, 기준 CLI 버전 문자열과 `--yolo` 가 `--help` 에 없는 숨은 별칭이라는 사실을 함께 기록하며, `--sandbox` 의 확대 지정 금지를 포괄적으로 적는다. [실행] (CMD-2 `test_forbidden_codex_flags_enumerate_current_cli`)
- **AC-7** 스킬의 어떤 문서도 `codex exec` 호출에 `-a` 또는 `--ask-for-approval` 을 지시하지 않고, `references/readiness-policy.md` 가 그 플래그의 부재를 명시한다. [실행] (CMD-2 `test_codex_exec_has_no_approval_flag_contract`)
- **AC-8** author 프롬프트 필수 요소 열두 가지가 `references/readiness-policy.md` 에 목록으로 존재하며, R1.5 가 절대 경로를 요구한 다섯 항목이 그 문서에서도 **절대 경로**로 한정돼 있다. [실행] (CMD-2 `test_author_prompt_required_elements_contract`)
- **AC-9** `references/readiness-policy.md` 가 라운드 2 이상의 개정 노트 형식을 `references/revision-check-policy.md` 에서 그대로 인용해 싣는다 — 절 헤딩 `## 라운드 <n> 개정` 과 다섯 열 표 머리. 같은 공식 라운드에 절이 정확히 하나이고 readiness 개정이 반복되면 새 절을 만들지 않고 그 절에 행을 누적·갱신한다는 규칙, 그리고 그 절의 범위가 직전 라운드 스냅숏 이후의 모든 변경이며 readiness 가 유발한 변경도 포함된다는 규정도 함께 싣는다. [실행] (CMD-2 `test_author_revision_note_format_contract`)
- **AC-10** author 프롬프트 계약이 조합 검토 지시를 필수로 포함하고 교차 회귀 전례를 근거로 인용한다. [실행] (CMD-2 `test_author_cross_regression_review_contract`)
- **AC-11** `references/readiness-policy.md` 가 author 의 수정 허용 파일을 대상 Spec 과 개정 노트 둘로 한정하고, 호출 후 `git status --porcelain` 확인을 요구하며, 그 비교에서 `initial_dirty_paths` 와 `.claude/quality-state/<task-id>/` 하위를 제외하고 결과의 `changed_files` 와 대조한다고 명시한다. [실행] (CMD-2 `test_author_write_scope_contract`)
- **AC-12** `record-draft-attempt` 호출 1회가 `draft_attempts` 의 해당 artifact 값을 1 증가시키고 `rounds` 의 어떤 값도 바꾸지 않는다. [실행] (CMD-2 `test_record_draft_attempt_increments_only_draft_attempts`)
- **AC-13** `draft_attempts.spec` 증가가 `draft_attempts.plan` 을 바꾸지 않는다. [실행] (CMD-2 `test_record_draft_attempt_is_per_artifact`)
- **AC-14** `draft_attempts` 가 없는 schema v1 상태에 첫 `record-draft-attempt` 를 적용하면 그때 `draft_attempts` 가 생성되고 해당 artifact 값이 1 이 된다. [실행] (CMD-2 `test_draft_attempts_created_on_first_record`)
- **AC-15** author 호출 실패(비정상 종료·결과 파일 없음·스키마 검증 실패) 시 단계를 유지하고 모델을 대체하지 않는다는 지시가 `references/readiness-policy.md` 에 존재하며 `BLOCKED_MODEL_UNAVAILABLE` 경로를 참조한다. [실행] (CMD-2 `test_author_failure_recovery_contract`)
- **AC-16** author 호출 전후 Spec digest 가 같으면 개정 실패로 처리한다는 지시가 존재한다. [실행] (CMD-2 `test_author_no_change_is_failure_contract`)
- **AC-17** `references/readiness-policy.md` 가 readiness reviewer 를 author 와 별개 프로세스로 실행하고 author 문맥을 상속하지 않는다고 명시한다. [실행] (CMD-2 `test_readiness_reviewer_is_fresh_contract`)
- **AC-18** readiness 호출 템플릿이 `--sandbox read-only` 를 쓰고 금지 플래그를 포함하지 않는다. [실행] (CMD-2 `test_readiness_invocation_template_contract`)
- **AC-19** readiness 프롬프트 계약이 읽기 전용과 git 쓰기 금지를 명시한다. [실행] (CMD-2 `test_readiness_read_only_contract`)
- **AC-20** `references/readiness-policy.md` 의 author·readiness 호출 템플릿이 모두 표준 입력을 프롬프트 파일 또는 `/dev/null` 에 연결하고, 둘 중 어느 형태도 아닌 호출을 금지한다고 명시하며, 그 이유(비대화형 무한 대기)를 기록한다. [실행] (CMD-2 `test_readiness_stdin_guard_contract`)
- **AC-21** `schemas/readiness-result.schema.json` 의 모든 property 정의가 `type` 키를 가지며 `const` 키를 한 번도 쓰지 않는다. [실행] (CMD-2 `test_readiness_schema_uses_type_not_const`)
- **AC-22** readiness 프롬프트 계약이 "개정 노트는 근거가 아니라 검증 대상" 규칙과 그 주장을 Spec 본문에서 파일:행으로 대조하라는 지시를 포함한다. [실행] (CMD-2 `test_readiness_prompt_treats_notes_as_claims`)
- **AC-23** readiness 프롬프트 계약이 자신의 판정을 **참고용**으로 규정하고 Claude 공식 판정을 대체하지도 그 시작을 막지도 않는다고 명시하며, 설계 취향 감점을 금지한다. [실행] (CMD-2 `test_readiness_is_advisory_not_authority_contract`)
- **AC-24** `references/readiness-policy.md` 가 readiness 프롬프트 필수 요소로 같은 공식 라운드의 직전 readiness 시도 결과 경로와 직전 Claude 공식 리뷰 open findings 경로 둘 다를 지정하고, 각 finding 의 ID·severity·`required_resolution` 이 프롬프트에서 읽히도록 요구하며, 그 ID 가 **참조**이고 reviewer 자신의 finding 은 `READY-` 로 **발급**해야 한다는 R7.1 의 구분을 싣고, 그 전달이 R2.1 의 author 문맥 상속 금지와 구분된다는 것을 명시한다. [실행] (CMD-2 `test_readiness_prompt_carries_prior_findings`)
- **AC-25** `references/readiness-policy.md` 의 체크리스트 절이 C1~C8 여덟 항목을 각각 정의한다. [실행] (CMD-2 `test_readiness_checklist_defines_eight_items`)
- **AC-26** 체크리스트 여덟 항목이 모두 `pass` 또는 `not_applicable` 이고 Critical/High 가 0 인 결과만 `READY` 로 판정되며, `not_applicable` 은 충족으로 센다. [실행] (CMD-2 `test_readiness_verdict_requires_all_checks_and_no_high`)
- **AC-27** 체크리스트 항목 중 하나라도 `fail` 이면 판정이 `REVISE` 이고, 체크리스트가 전부 `pass` 여도 Critical 또는 High finding 이 하나라도 있으면 `READY` 가 아니다. [실행] (CMD-2 `test_readiness_verdict_blocks_on_failed_check_or_high_finding`)
- **AC-28** `references/readiness-policy.md` 의 C8 정의가 다섯을 모두 담는다 — 판정 대상을 프롬프트에 실린 findings 전문으로 한정하고 상태 기록을 훑어 대상을 유도하지 않는다는 것, 판정 대상 하나마다 `prior_findings` 항목을 정확히 하나 남긴다는 것, `judgement` 가 `partial` 이면 C8 이 미충족이라는 것, 프롬프트에 findings 가 없으면 `prior_findings` 가 빈 배열이고 항목이 자동 충족이라는 것, 참조 자리의 ID 는 원 접두(`SPEC-`·`READY-`)를 그대로 유지한다는 것. [문서] `references/readiness-policy.md` § 체크리스트
- **AC-29** `references/readiness-policy.md` 가 `score` 를 기록 전용 참고값으로 규정하고 판정·기록 거부·전이에 쓰지 않는다고 명시한다. [실행] (CMD-2 `test_readiness_score_is_advisory_contract`)
- **AC-30** readiness 결과 검증과 기록 경로가 `score` 값을 읽지 않는다. 같은 입력의 `score` 를 0 과 100 으로 바꿔도 검증 결과와 기록된 `outcome` 이 같다. [실행] (CMD-2 `test_readiness_recording_ignores_score`)
- **AC-31** 체크리스트 항목 정의에 설계 정합성·아키텍처 타당성·시간축 전개 판정이 포함되지 않는다는 것이 문서에 명시된다. [문서] `references/readiness-policy.md` § 체크리스트
- **AC-32** readiness 기록 추가가 `rounds` 의 어떤 값도 바꾸지 않는다. [실행] (CMD-2 `test_record_readiness_does_not_touch_rounds`)
- **AC-33** readiness 기록이 하나도 없는 상태와 마지막 readiness 결과가 `REVISE` 인 상태 양쪽에서 `record-review`·`record-review-unverified`·`record-review-error` 가 spec 리뷰를 거부하지 않는다. [실행] (CMD-2 `test_review_recording_is_independent_of_readiness`)
- **AC-34** 이 작업이 `ALLOWED_TRANSITIONS` 의 엣지 집합과 `TERMINAL_STATES` 를 base revision 대비 바꾸지 않는다. [실행] (CMD-2 `test_transitions_and_terminal_states_unchanged`)
- **AC-35** `references/readiness-policy.md` 가 readiness 는 어떤 상태 전이도 결정하지 않으며 공식 리뷰의 시작 조건이 아니라고 명시한다. [문서] `references/readiness-policy.md` § readiness 의 지위
- **AC-36** readiness 기록 하나를 추가할 때마다 `attempt` 가 실행 전체에서 1씩 증가하며 `formal_round` 가 바뀌어도 초기화되지 않는다. [실행] (CMD-2 `test_readiness_attempt_is_globally_monotonic`)
- **AC-37** `schemas/readiness-result.schema.json` 의 `attempt` 에 `maximum` 제약이 없다. [실행] (CMD-2 `test_readiness_schema_attempt_has_no_maximum`)
- **AC-38** 같은 `formal_round` 에 readiness 기록을 셋 이상 추가해도 `record-readiness` 가 시도 수를 이유로 거부하지 않는다. [실행] (CMD-2 `test_record_readiness_has_no_attempt_limit`)
- **AC-39** `references/readiness-policy.md` 가 `READY` 이후 추가 시도 중단과, 라운드당 시도 한도를 코드로 강제하지 않고 비용 상한을 오케스트레이터 지시로 둔다는 것을 함께 명시한다. [문서] `references/readiness-policy.md` § readiness 의 지위
- **AC-40** `references/readiness-policy.md` 가 공식 리뷰 컨텍스트 첨부를 **저장소 근거 경로 둘**(마지막 readiness 결과 JSON, 그리고 미충족 체크리스트 항목과 잔여 finding 전문을 담은 `.claude/quality-state/<task-id>/readiness-evidence-spec-r<N>.md`)로 규정하고, 내용을 프롬프트에 인라인하지 않는다는 것과 그 근거(`SKILL.md` § Review invocation contract 의 입력 한정이 보존 대상이라는 것), 첨부가 리뷰어 판정을 구속하지 않는다는 것, 유효한 결과가 없을 때 그 사실을 요약 파일에 적는다는 것을 함께 적는다. [실행] (CMD-2 `test_readiness_evidence_attachment_contract`)
- **AC-41** `references/readiness-policy.md` 가 등록 digest 를 `artifacts[artifact]` 가 가리키는 파일의 현재 SHA-256 으로 정의하고, `artifact_digests` 를 이 대조에 쓰지 않는다고 명시하며, 경로 불일치 시 readiness 호출 자체를 하지 않는다는 확인을 호출 전 절차로 배치하고, 심사 시점 digest 를 프롬프트에 싣게 한다. [실행] (CMD-2 `test_readiness_path_and_digest_precede_invocation`)
- **AC-42** `--artifact-digest` 가 등록 digest 와 다르면 `record-readiness` 호출이 거부된다. [실행] (CMD-2 `test_record_readiness_rejects_registered_digest_mismatch`)
- **AC-43** `--invocation-status ok` 로 호출했을 때 결과의 `artifact_digest` 가 심사 시점 digest 와 다르면 유효 심사로 채택되지 않고 `digest_mismatch` 실패 기록이 남는다. [실행] (CMD-2 `test_record_readiness_records_digest_mismatch`)
- **AC-44** digest 대조 실패와 경로 불일치가 단계를 바꾸지 않고 사용자 보고로 이어진다는 지시가 존재한다. [문서] `references/readiness-policy.md` § digest 대조
- **AC-45** `outcome` 이 `recorded` 인 readiness 기록 하나의 키 집합이 R6.1 의 열두 필드와 **정확히 같고**(더도 덜도 아니다), `resolved_finding_ids` 의 값이 결과 JSON 의 같은 필드와 배열 단위로 같으며, 결과 JSON 에 `prior_findings` 가 있어도 상태 기록에는 그 키가 생기지 않는다. [실행] (CMD-2 `test_readiness_record_shape`)
- **AC-46** 공식 리뷰 기록 이후 추가되는 readiness 기록의 `formal_round` 가 `rounds[artifact] + 1` 과 같다. [실행] (CMD-2 `test_readiness_formal_round_advances_after_review`)
- **AC-47** `record-readiness` 에 `rounds[artifact] + 1` 과 다른 `--formal-round` 를 주면 호출이 거부된다. [실행] (CMD-2 `test_record_readiness_rejects_mismatched_formal_round`)
- **AC-48** 심사 시점 digest 가 readiness 기록의 `artifact_digest` 로 상태에 남고, 그 값이 호출 시점에 계산한 Spec 파일 digest 와 같다. [실행] (CMD-2 `test_record_readiness_persists_review_time_digest`)
- **AC-49** 새 `init` 상태의 최상위 키 집합이 base revision 의 키 집합에 `readiness` 와 `draft_attempts` 둘만 더한 것과 정확히 같고, 두 필드의 값이 R6.2 가 정한 빈 값이다. [실행] (CMD-2 `test_new_state_has_exactly_two_new_fields`)
- **AC-50** `readiness` 필드가 없는 상태에 첫 `record-readiness` 를 적용하면 그때 필드가 생성된다. [실행] (CMD-2 `test_readiness_field_created_on_first_record`)
- **AC-51** R6.2 의 두 필드가 없는 schema v1 상태 파일을 읽을 수 있고, 읽기만으로는 어느 필드도 상태 파일에 생기지 않으며, readiness 미실행·author 미호출로 취급된다. [실행] (CMD-2 `test_v1_state_without_new_fields_is_not_mutated_on_load`)
- **AC-52** 진행 중 goal 을 재개해도 기존 `rounds`, `reviews`, `open_finding_ids`, `plan_approval`, `revision_checks` 가 보존되고 `plan_approval` 의 경로와 digest 가 재개 전과 바이트 단위로 같다. [실행] (CMD-2 `test_resume_preserves_rounds_reviews_and_approval`)
- **AC-53** `SPEC_PASSED`·`NEEDS_REDESIGN`·`BLOCKED`·`CANCELLED` 로 전이해도 readiness 기록과 `draft_attempts` 가 상태에 남는다. [실행] (CMD-2 `test_readiness_records_survive_stage_exit`)
- **AC-54** readiness 기록의 `outcome` 이 `recorded`·`schema_invalid`·`digest_mismatch`·`invocation_failed` 네 값만 허용한다. [실행] (CMD-2 `test_readiness_record_outcome_enum`)
- **AC-55** 스키마 검증 실패·digest 불일치·호출 실패 각각의 기록에서 `verdict` 와 `score` 가 `null` 이고 `checklist`·`findings`·`resolved_finding_ids` 가 빈 배열이며 나머지 일곱 필드가 채워진다. [실행] (CMD-2 `test_failed_readiness_attempt_record_shape`)
- **AC-56** `--invocation-status` 에 `ok`·`failed` 밖의 값을 주면 호출이 거부되고, `record-readiness` 가 `outcome` 인자를 받지 않는다. [실행] (CMD-2 `test_invocation_status_enum_is_enforced`)
- **AC-57** `--invocation-status failed` 로 호출하면 결과 파일이 스키마를 통과하고 등록 digest 까지 가리키는 정상 결과여도 `invocation_failed` 로 기록되고 `result_path` 가 `--stderr-path` 값이 되며, `--stderr-path` 가 없거나 그 경로가 존재하지 않으면 호출이 거부된다. [실행] (CMD-2 `test_invocation_failure_is_recorded_and_requires_stderr_path`)
- **AC-58** `--invocation-status ok` 이고 결과가 스키마 위반과 digest 불일치를 동시에 만족하면 `schema_invalid` 로 기록된다. [실행] (CMD-2 `test_schema_invalid_precedes_digest_mismatch`)
- **AC-59** `light` 모드 상태에서 `record-readiness` 와 `record-draft-attempt` 두 명령이 모두 오류로 거부된다. [실행] (CMD-2 `test_readiness_commands_rejected_in_light_mode`)
- **AC-60** 발급 자리인 `findings[].id` 와 `blockers[]` 의 값이 하나라도 `^READY-` 를 만족하지 않으면 결과 검증이 실패한다. [실행] (CMD-2 `test_issued_finding_ids_require_ready_prefix`)
- **AC-61** 참조 자리(`prior_findings[].id`, `resolved_finding_ids`)는 `SPEC-` 와 `READY-` 두 접두를 모두 받아 검증을 통과하고, 같은 `SPEC-` 값이 발급 자리(`findings[].id`, `blockers`)에 있으면 검증이 실패한다. 세 조건을 한 결과 묶음으로 대조한다. [실행] (CMD-2 `test_spec_prefix_is_reference_only_not_issuable`)
- **AC-62** readiness 프롬프트 계약이 공식 finding 과의 대응 관계를 `description` 에 기록하도록 요구하고, 하나의 개정 주기 안에서 같은 물질적 문제에 같은 ID 를 유지하도록 요구한다. [문서] `references/readiness-policy.md` § finding 식별자
- **AC-63** `schemas/readiness-result.schema.json` 의 `required` 가 R8.1 의 열세 필드를 정확히 포함하고 그 밖의 필드를 required 로 두지 않는다. [실행] (CMD-2 `test_readiness_schema_required_fields`)
- **AC-64** `schemas/readiness-result.schema.json` 이 JSON 으로 파싱되고 최상위 `type` 이 `object` 이며 `additionalProperties` 가 `false` 다. [실행] (CMD-5)
- **AC-65** `artifact_digest` 가 소문자 SHA-256 64자 패턴으로 제약되고 `verdict` 가 `READY` 와 `REVISE` 두 값만 허용한다. [실행] (CMD-2 `test_readiness_schema_digest_pattern_and_verdict_enum`)
- **AC-66** readiness 프롬프트 계약이 `score` 를 rubric 가중치로 실제 계산하도록 지시하고 "blocker 가 있다고 0 을 넣지 마라"를 포함한다. [실행] (CMD-2 `test_readiness_score_computation_instruction`)
- **AC-67** `evidence` 최소 6건 요구가 스키마의 `minItems` 로 강제되고, 각 항목이 `claim`·`location`·`verified` 셋을 required 로 요구하며 그 밖의 키를 허용하지 않는다. [실행] (CMD-2 `test_readiness_schema_evidence_min_items`)
- **AC-68** `checklist` 가 C1~C8 여덟 항목을 모두 포함하지 않으면 검증이 실패하고, 각 항목이 `id`·`status`·`evidence` 를 요구하며 `status` 가 `pass`·`fail`·`not_applicable` 셋만 허용한다. [실행] (CMD-2 `test_readiness_schema_checklist_shape`)
- **AC-69** readiness 결과 스키마가 `resolved_finding_ids` 를 필수로 요구하고 그 값이 문자열 배열이며 빈 배열을 허용하고, R8.4 의 네 패턴 제약이 스키마에 존재한다 — `findings[].id` 와 `blockers[]` 에 `^READY-`, `prior_findings[].id` 와 `resolved_finding_ids[]` 에 `^(READY-|SPEC-)`. [실행] (CMD-2 `test_readiness_schema_resolved_ids_and_namespace_patterns`)
- **AC-70** `--invocation-status ok` 로 호출했을 때 스키마 검증에 실패한 결과가 유효 심사로 채택되지 않고 `schema_invalid` 실패 기록이 남는다. [실행] (CMD-2 `test_invalid_readiness_result_is_recorded_as_schema_invalid`)
- **AC-71** `SKILL.md` 파일 전체가 500행 미만이다. [실행] (CMD-3)
- **AC-72** `references/readiness-policy.md` 가 존재하고 `SKILL.md` 의 참조 경로 목록에 등재된다. [실행] (CMD-2 `test_readiness_policy_is_referenced_from_skill`)
- **AC-73** `templates/spec.md` 에 `## Requirements traceability` 절이 `## Acceptance criteria` 와 `## Architecture` 사이에 있고, `### 판정 명령 표` 절이 `## Test strategy` 아래 첫 하위 절로 있다. 헤딩 수준과 앞뒤 절을 모두 판정한다. [실행] (CMD-2 `test_spec_template_has_traceability_and_command_table`)
- **AC-74** `docs/quality-goal-maintenance.md` 에 readiness 점검 항목(`codex exec` 플래그, readiness 결과 스키마, author·reviewer 라우팅 모델, 두 참조 파일의 동기화)이 존재한다. [실행] (CMD-2 `test_maintenance_doc_covers_readiness`)
- **AC-75** `docs/quality-goal-maintenance.md` 에 `## 판정 명령 표` 절이 존재하고 `## 결정적 테스트` 절이 존재하지 않으며, 새 절이 CMD-1~CMD-7 일곱 행을 모두 싣고 그 절이 판정 명령 표의 정본이라는 것이 문서에 명시된다. [실행] (CMD-2 `test_maintenance_doc_replaces_test_section_with_command_table`)
- **AC-76** `docs/quality-goal-maintenance.md` 의 판정 명령 표가 테스트 스위트의 최소 Python 버전을 3.12 로 명시하고 그 두 근거(`enterContext`, `NO TESTS RAN` 종료 코드 5)를 표 **바로 아래**(표와 그 문언 사이에 다른 헤딩이 없음)에 함께 싣는다. [문서] `docs/quality-goal-maintenance.md` § 판정 명령 표
- **AC-77** Python 3.12 이상에서 전체 테스트가 통과한다. [실행] (CMD-1)
- **AC-78** base revision 의 테스트 이름 집합이 현재 테스트 이름 집합의 부분집합이다. 기존 테스트가 삭제되거나 이름이 바뀌면 실패한다. [실행] (CMD-6)
- **AC-79** `ROUND_LIMITS` 가 `{"spec": 3, "plan": 2, "code": 3}` 그대로이고 `REQUIRED_CHECKS` 가 변경되지 않는다. [실행] (CMD-2 `test_round_limits_and_required_checks_unchanged`)
- **AC-80** CMD-4 의 보존 대상 여덟 절이 base revision 대비 바이트 단위로 같다. [실행] (CMD-4)
- **AC-81** 공식 Claude 게이트의 점수 임계 85 가 `references/spec-rubric.md` 와 `references/plan-rubric.md` 에서 변경되지 않는다. [실행] (CMD-2 `test_formal_pass_gate_threshold_unchanged`)
- **AC-82** `SKILL.md` frontmatter 의 `version` 이 5.0.0 보다 크고 MINOR 이상 증가한다. [실행] (CMD-2 `test_skill_version_bumped_for_contract_extension`)
- **AC-83** `references/model-routing.md` 의 라우트 표에 Spec author(standard `gpt-5.6-terra` high, strict `gpt-5.6-sol` high)와 readiness reviewer(fresh `gpt-5.6-sol` high) 행이 존재한다. [실행] (CMD-2 `test_model_routing_includes_author_and_readiness_rows`)
- **AC-84** `references/model-routing.md` 와 `references/readiness-policy.md` 의 역할 분담이 문서에 명시된다. [실행] (CMD-2 `test_routing_and_policy_split_is_documented`)
- **AC-85** `tests/assert_python_version.py` 가 3.12 이상에서 성공하고 3.12 미만에서 비정상 종료한다. [실행] (CMD-7)
- **AC-86** `docs/quality-goal-maintenance.md` § 판정 명령 표의 CMD-1 과 CMD-2 정의가 `tests/assert_python_version.py` 호출을 포함하고, 버전 비교식을 명령 안에 인라인으로 복제하지 않는다. [실행] (CMD-2 `test_version_guard_is_shared_not_inlined`)
- **AC-87** R9.8 의 세 스크립트가 존재하고, 세 파일명이 모두 `test_` 로 시작하지 않아 `unittest discover -p 'test_*.py'` 의 수집 대상에서 빠진다. [실행] (CMD-2 `test_judgement_scripts_exist_and_are_not_collected`)
- **AC-88** `prior_findings` 가 항목마다 `id`·`source`·`judgement`·`evidence` 를 요구하고 `source` 는 `readiness`·`formal`, `judgement` 는 `resolved`·`unresolved`·`partial` 만 허용하며 빈 배열이 허용된다. 그리고 `resolved_finding_ids` 의 값 집합이 `judgement` 가 `resolved` 인 항목의 ID 집합과 다르면 검증이 실패한다. [실행] (CMD-2 `test_prior_findings_shape_and_resolved_set_equality`)
- **AC-89** `references/readiness-policy.md` 의 readiness 프롬프트 계약이 `verified` 가 `true` 인 근거의 `location` 을 `<경로>:<행>` 형식으로 쓰게 하고 `false` 인 근거의 `location` 에는 확인하지 못한 사유를 적게 한다는 문언을 함께 담는다. [실행] (CMD-2 `test_readiness_unverified_evidence_reason_contract`)
- **AC-90** `tests/assert_python_version.py` 가 `is_supported(version_info)` 를 노출해 `(3, 11, 9)` 에 `False` 를, `(3, 12, 0)` 과 `(3, 14, 7)` 에 `True` 를 반환하고, 그 모듈의 `__main__` 분기가 `is_supported` 호출로만 판정한다(모듈 어디에도 `version_info` 를 상수와 직접 비교하는 식이 그 함수 밖에 없다). [실행] (CMD-2 `test_python_version_guard_boundary_and_main_delegates`)

## Requirements traceability

요구사항 정의 수는 45이고 아래 표의 행 수도 45다. 표의 행 순서는 요구사항 정의 순서와 같다. 매핑된 AC 는 해당 요구사항 문언의 모든 독립 조건을 판정하는 것만 싣는다.

| 요구사항 | 판정하는 AC |
|---|---|
| R1.1 | AC-1 |
| R1.2 | AC-2, AC-3 |
| R1.3 | AC-4 |
| R1.4 | AC-5, AC-6, AC-7, AC-80 |
| R1.5 | AC-8, AC-9, AC-10 |
| R1.6 | AC-11 |
| R1.7 | AC-10 |
| R1.8 | AC-12, AC-13, AC-14 |
| R1.9 | AC-15, AC-16 |
| R2.1 | AC-17, AC-24 |
| R2.2 | AC-18, AC-19 |
| R2.3 | AC-20 |
| R2.4 | AC-21 |
| R2.5 | AC-22, AC-23, AC-24, AC-61 |
| R3.1 | AC-25, AC-26, AC-27, AC-28, AC-68, AC-88 |
| R3.2 | AC-29, AC-30 |
| R3.3 | AC-31 |
| R4.1 | AC-32, AC-33, AC-34, AC-35 |
| R4.2 | AC-36, AC-37 |
| R4.3 | AC-38, AC-39 |
| R4.4 | AC-40 |
| R5.1 | AC-41 |
| R5.2 | AC-42, AC-43 |
| R5.3 | AC-44 |
| R6.1 | AC-45, AC-46, AC-47, AC-48 |
| R6.2 | AC-49, AC-50 |
| R6.3 | AC-51 |
| R6.4 | AC-52 |
| R6.5 | AC-53 |
| R6.6 | AC-54, AC-55, AC-56, AC-57, AC-58, AC-59 |
| R7.1 | AC-60, AC-61, AC-69 |
| R7.2 | AC-62 |
| R8.1 | AC-63, AC-64, AC-65 |
| R8.2 | AC-66 |
| R8.3 | AC-67, AC-89 |
| R8.4 | AC-68, AC-69, AC-88 |
| R8.5 | AC-70 |
| R9.1 | AC-71, AC-72 |
| R9.2 | AC-73 |
| R9.3 | AC-74, AC-75, AC-76 |
| R9.4 | AC-77, AC-78 |
| R9.5 | AC-79, AC-80, AC-81 |
| R9.6 | AC-82 |
| R9.7 | AC-83, AC-84 |
| R9.8 | AC-85, AC-86, AC-87, AC-90 |

## Architecture

### 컴포넌트와 책임

| 컴포넌트 | 책임 | 신설 여부 |
|---|---|---|
| Claude 오케스트레이터 | 요구사항 발굴, 프롬프트 작성, 프로세스 호출, digest 대조, 상태 기록, 공식 리뷰 근거 첨부 | 기존 |
| Codex author 프로세스 | Spec 초안 작성과 개정, 개정 노트 작성, 조합 검토 | 신설 |
| fresh Codex readiness reviewer 프로세스 | 체크리스트 여덟 항목 판정, finding 생성, 참고 점수 계산 | 신설 |
| Claude quality-reviewer 에이전트 | 공식 Spec 리뷰. 설계 정합성·시간축 전개·교차 회귀 판정 | 기존, 변경 없음 |
| `scripts/quality_state.py` | readiness 기록, `draft_attempts` 기록, digest 대조 강제 | 확장 |
| `scripts/validate_review.py` | readiness 결과 검증 함수 추가. 기존 `validate_review` 와 `REQUIRED_CHECKS` 는 불변 | 확장 |
| `schemas/readiness-result.schema.json` | readiness 결과 구조 계약 | 신설 |
| `references/readiness-policy.md` | author·readiness 프롬프트 계약, 호출 템플릿, 체크리스트 정의, readiness 의 지위 | 신설 |
| `templates/spec.md` | 요구사항 추적표 절과 판정 명령 표 절 추가 | 확장 |

### 세 심사의 역할 분리

readiness 와 Claude 공식 리뷰는 서로를 대체하지 않는다. 실측(§ Problem and context)이 이 분리를 강제한다.

- readiness 는 문서의 **정합성**만 본다. 판정 대상은 절 구조, 번호 무결성, 추적표, 판정 수단 배정, 프롬프트에 실린 직전 findings 의 해소 여부다. 전부 문서를 훑어 기계적으로 확인 가능하다.
- Claude 공식 리뷰는 **설계**를 본다. 규칙이 여러 실행에 걸쳐 돌 때 무엇이 깨지는지, 개별 수정이 만든 교차 회귀가 있는지, 요구사항 본문과 Decisions 가 충돌하는지를 본다.
- 두 판정이 겹치지 않으므로 readiness 통과가 공식 통과를 예측하지 않는다. readiness 는 author 개정 주기 안에서 값싼 결함을 걷어내는 **참고 심사**이며, 그 결과는 공식 리뷰의 근거로만 넘어간다.

### 상태 머신에 대한 변경 — 없음

이 작업은 `ALLOWED_TRANSITIONS`, `TERMINAL_STATES`, `ROUND_LIMITS`, `REQUIRED_CHECKS` 를 바꾸지 않는다(AC-34, AC-79). 새 stage 도, 새 전이 가드도, 기존 전이의 새 거부 조건도 만들지 않는다. 상태에 추가되는 것은 데이터 두 필드뿐이다(R6.2).

직전 설계가 도입하려 했던 게이트 계층 — 게이트 판정 함수, `AWAITING_READINESS_DECISION` stage, 그 전이 가드 둘, `record-review` 의 새 거부 조건 — 은 전부 이관했다(Non-goal 12). 그 계층이 만든 `SPEC-03`→`SPEC-07`→`SPEC-11` 연쇄가 이관의 근거다. 이 Spec 이 그 자리에 남기는 것은 **기록뿐**이며, 기록은 판정하지 않으므로 fail-open/fail-closed 라는 개념 자체가 성립하지 않는다.

이 분리가 성립하려면 기록이 나중에 게이트의 입력이 될 만큼 충분해야 한다. R6.1 의 열두 필드가 그 조건이다 — 이관된 직전 설계의 게이트는 `outcome`, `formal_round`, `artifact_digest`, `findings`, `resolved_finding_ids`, `checklist`, `attempt` 일곱을 읽었고 그 일곱이 모두 열둘 안에 있다. 이슈 #76 은 이 필드들 위에 판정 함수를 얹으면 되고, 기록 형태를 바꿀 필요가 없다. `prior_findings`(R8.4)는 상태에 복사하지 않는다 — 이관된 게이트의 입력이 아니고, 필요하면 `result_path` 가 가리키는 결과 파일에 그대로 남아 있다.

## Interfaces and data flow

### SPEC_REVIEW 단계의 실행 순서

```text
SPEC_REVIEW 진입
 └─ 오케스트레이터: 요구사항 발굴 (references/brainstorming-policy.md)
     └─ 물질적 모호성이 남으면 사용자에게 질의해 해소
 └─ [반복] 개정 주기 (formal_round = N)
     ├─ author 호출 (codex exec, workspace-write, 프롬프트 파일을 stdin 으로)
     │   ├─ 호출 전후 대상 Spec SHA-256 비교 — 같으면 개정 실패 (R1.9)
     │   ├─ git status --porcelain 으로 쓰기 범위 확인 (R1.6)
     │   └─ record-draft-attempt → draft_attempts.spec += 1
     ├─ set-artifact --kind spec (절대 경로)
     ├─ N >= 2: spec-revision-notes.md 작성 → revision_check.py --artifact spec
     │            (종료 코드 0 까지 반복. 라운드를 소모하지 않는다)
     ├─ digest 대조: 대상 경로 == artifacts.spec, 현재 SHA-256 계산
     ├─ readiness 호출 (codex exec, read-only, 프롬프트 파일을 stdin 으로)
     ├─ record-readiness → 스키마 검증 + digest 대조 + 기록 (판정하지 않는다)
     └─ 오케스트레이터 판단
         ├─ REVISE 이고 더 고칠 여지가 있으면 → author 에 finding 전달하고 개정 주기 반복
         └─ 그 밖의 경우(READY, 또는 비용 상한 도달, 또는 결과 없음)
             └─ Claude 공식 리뷰 라운드 N (fresh quality-reviewer)
                 │   근거 첨부(경로 둘): readiness 결과 JSON, readiness-evidence-spec-r<N>.md (R4.4)
                 ├─ record-review [N>=2 는 --revision-check 필수] → PASS  → SPEC_PASSED
                 └─ record-review [N>=2 는 --revision-check 필수] → REVISE → formal_round = N+1, 개정 주기 재개
```

readiness 의 결과는 이 그림에서 **오케스트레이터의 판단 입력**일 뿐 어느 화살표도 강제하지 않는다. readiness 를 건너뛰거나 실패한 상태로 공식 리뷰에 들어가도 어떤 명령도 거부하지 않는다(AC-33). 비용 상한은 사용자 지시로 정해지며 코드가 세지 않는다(R4.3).

개정 점검(`scripts/revision_check.py`)과 `record-review --revision-check` 는 base revision 이 이미 갖는 계약이며(v5.0.0, `SKILL.md` 의 `### Spec` 절), 이 작업이 새로 만들지 않고 입력·출력·거부 조건도 바꾸지 않는다(R9.5). 개정 점검을 readiness 호출보다 앞에 두는 이유는, 식별자 정합이 깨진 산출물을 readiness 가 심사하면 체크리스트 C3~C5 가 같은 결손을 중복 보고하기 때문이다.

### author 호출 계약

```bash
codex exec \
  -C "$PROJECT_ROOT" \
  --sandbox workspace-write \
  --ephemeral \
  --model "$AUTHOR_MODEL" \
  -c "model_reasoning_effort=\"$AUTHOR_EFFORT\"" \
  --output-schema "$SKILL_DIR/schemas/codex-result.schema.json" \
  --output-last-message "$RESULT_PATH" \
  --json \
  - < "$PROMPT_PATH" > "$EVENTS_PATH" 2> "$STDERR_PATH"
```

프롬프트·결과·이벤트·표준 오류 파일은 `.claude/quality-state/<task-id>/` 아래에만 둔다.

### readiness 호출 계약

```bash
codex exec \
  -C "$PROJECT_ROOT" \
  --sandbox read-only \
  --ephemeral \
  --model gpt-5.6-sol \
  -c "model_reasoning_effort=\"high\"" \
  --output-schema "$SKILL_DIR/schemas/readiness-result.schema.json" \
  --output-last-message "$READINESS_RESULT_PATH" \
  --json \
  - < "$READINESS_PROMPT_PATH" > "$READINESS_EVENTS_PATH" 2> "$READINESS_STDERR_PATH"
```

두 호출 모두 프롬프트를 표준 입력으로 준다. 그러면 stdin 이 프롬프트 파일에 연결되므로 R2.3 의 무한 대기가 발생하지 않는다. 프롬프트를 명령행 인자로 넘기는 변형을 쓸 때만 `< /dev/null` 을 붙인다. 두 형태 중 어느 쪽도 아닌 호출은 금지된다.

author 결과는 기존 `schemas/codex-result.schema.json` 으로 검증한다. 새 스키마를 만들지 않는 이유는 § Decisions D8 에 있다.

### 상태 필드

```json
{
  "draft_attempts": {"spec": 0, "plan": 0},
  "readiness": {
    "spec": [
      {
        "attempt": 1,
        "formal_round": 1,
        "outcome": "recorded",
        "verdict": "REVISE",
        "score": 84,
        "checklist": [{"id": "C1", "status": "pass", "evidence": "spec.md:1-58"}],
        "findings": [{"id": "READY-01", "severity": "High", "description": "…",
                      "evidence_location": "spec.md:120-140", "rubric_item": "…",
                      "required_resolution": "…"}],
        "resolved_finding_ids": ["READY-00", "SPEC-03"],
        "artifact_digest": "…64 hex…",
        "reviewer_model": "gpt-5.6-sol",
        "result_path": "/abs/…/readiness-spec-a1.json",
        "recorded_at": "2026-09-06T14:00:00Z"
      }
    ],
    "plan": []
  }
}
```

`resolved_finding_ids` 의 예시가 `READY-` 와 `SPEC-` 를 함께 담는 것은 참조 자리가 두 네임스페이스를 모두 허용하기 때문이다(R7.1) — `SPEC-03` 은 직전 Claude 공식 리뷰의 finding 을 가리키는 참조이지 readiness 가 발급한 ID 가 아니다. 결과 파일의 `prior_findings` 는 상태에 복사하지 않으며 `result_path` 가 가리키는 파일에 남는다(R6.1).

`schema_version` 은 1 을 유지한다(§ Decisions D2). R6.2 의 두 필드가 없는 상태는 읽을 수 있지만 로드만으로 필드가 생기지 않는다(R6.3). 새 상태는 `init` 이 두 필드를 위 형태의 빈 값으로 만든다. `outcome` 이 `recorded` 가 아닌 실패 기록은 `verdict`·`score`·`checklist`·`findings`·`resolved_finding_ids` 를 비운 채 나머지 필드만 채운다(R6.6).

### 새 `quality_state.py` 서브커맨드

| 명령 | 입력 | 출력 | 효과 |
|---|---|---|---|
| `record-draft-attempt` | `--state`, `--artifact` | 갱신된 상태 JSON | `draft_attempts[artifact] += 1` |
| `record-readiness` | `--state`, `--artifact`, `--result`, `--artifact-digest`, `--formal-round`, `--reviewer-model`, `--invocation-status`, `--stderr-path` | 갱신된 상태 JSON | R6.6 의 순서(호출 상태 → 스키마 검증 → digest 대조)로 `outcome` 을 정해 기록 추가. `outcome` 은 인자로 받지 않는다. `outcome` 이 `recorded` 이면 결과의 `resolved_finding_ids` 를 상태 기록에 그대로 복사한다(R6.1). 실패도 기록한다 |

두 명령이 이 작업이 추가하는 전부다. 판정을 반환하는 명령은 없다.

`record-readiness` 는 `--artifact-digest` 가 `artifacts[artifact]` 의 현재 파일 digest 와 같지 않으면 호출 자체를 거부한다(R5.1·R5.2). 결과의 `artifact_digest` 가 그 값과 다르면 `digest_mismatch` 실패 기록을 남긴다. `--formal-round` 가 `rounds[artifact] + 1` 과 다르면 역시 호출을 거부한다(R6.1). `--invocation-status` 가 `ok`·`failed` 가 아니거나, `failed` 인데 `--stderr-path` 가 없거나 그 경로가 존재하지 않으면 거부한다(R6.6). 두 명령 모두 `light` 모드 상태에서는 거부된다(R6.6). 시도 수를 이유로 한 거부는 어느 명령에도 없다(R4.3).

## Failure behavior

| 실패 | 감지 | 동작 | 상태 |
|---|---|---|---|
| author 비정상 종료 | `codex exec` 종료 코드 != 0 | 명령과 표준 오류를 사용자에게 보고. 모델 대체 없음 | `SPEC_REVIEW` 유지 |
| author 결과 파일 없음·스키마 위반 | `schemas/codex-result.schema.json` 검증 실패 | 위와 같음 | `SPEC_REVIEW` 유지 |
| author 가 Spec 을 바꾸지 않음 | 호출 전후 SHA-256 동일 | 개정 실패로 보고 | `SPEC_REVIEW` 유지 |
| author 가 허용 밖 파일 수정 | `git status --porcelain` 에 예상 밖 경로 | 변경을 되돌리지 않고 사용자에게 보고 후 판단 요청 | `SPEC_REVIEW` 유지 |
| 모델 거부·부재 | Codex 의 모델 거부 응답 | `BLOCKED_MODEL_UNAVAILABLE` 복구 경로. 사용자 승인 없이 대체 금지 | 현재 단계 유지, 사용자가 거부하면 `BLOCKED` |
| readiness 호출 비정상 종료·결과 파일 미생성·타임아웃 | `codex exec` 종료 코드 != 0 또는 결과 파일 부재 | `--invocation-status failed` 로 `invocation_failed` 기록. 모델 거부면 `BLOCKED_MODEL_UNAVAILABLE` 경로 | `SPEC_REVIEW` 유지 |
| readiness 결과 스키마 위반 | `schemas/readiness-result.schema.json` 검증 실패 | `schema_invalid` 기록, 사용자 보고 | `SPEC_REVIEW` 유지 |
| 심사 대상 경로 불일치 | 대상 경로 != `artifacts.spec` | readiness 호출 자체를 하지 않음 | `SPEC_REVIEW` 유지 |
| `--artifact-digest` != 등록 digest | `record-readiness` 의 사전 검사 | 호출 거부, 사용자 보고 | `SPEC_REVIEW` 유지 |
| 결과 digest 불일치 | 결과 `artifact_digest` != 심사 시점 digest | `digest_mismatch` 기록 | `SPEC_REVIEW` 유지 |
| readiness 가 반복 실패해 유효 결과가 없음 | 그 라운드의 기록이 전부 실패 `outcome` | 오케스트레이터가 그 사실을 공식 리뷰 근거에 명시하고 공식 리뷰를 진행한다(R4.4). 어떤 명령도 이를 막지 않는다 | `SPEC_REVIEW` 유지 |
| `--formal-round` 가 `rounds[artifact] + 1` 과 다름 | `record-readiness` 의 사전 검사 | 호출 거부. 오케스트레이터가 유도값을 다시 계산해 재호출하고, 그래도 어긋나면 상태 불일치로 사용자에게 보고 | `SPEC_REVIEW` 유지 |
| `--invocation-status` 가 `ok`·`failed` 밖의 값 | `record-readiness` 의 사전 검사 | 호출 거부. 허용값을 오류 메시지로 보이고 재호출 | `SPEC_REVIEW` 유지 |
| `--invocation-status failed` 인데 `--stderr-path` 가 없거나 그 경로가 없음 | `record-readiness` 의 사전 검사 | 호출 거부. 표준 오류 파일을 먼저 만들고 재호출. 실패 원인을 기록 없이 흘리지 않기 위한 거부다 | `SPEC_REVIEW` 유지 |
| `light` 모드에서 `record-readiness`·`record-draft-attempt` 호출 | 상태의 `mode` 검사 | 호출 거부. light 는 `SPEC_REVIEW` 를 거치지 않으므로 정상 경로에 없는 호출이며, 조용히 무시하지 않고 드러낸다 | 현재 단계 유지 |
| 비대화형 stdin 무한 대기 | 프로세스가 응답 없이 멈춤 | 호출 계약이 stdin 을 프롬프트 파일에 고정해 사전 차단. `/dev/null` 변형은 프롬프트를 명령행 인자로 넘길 때만 쓴다 | 해당 없음 |

readiness 실패가 워크플로를 막지 않는 것이 이 축소 범위의 핵심 성질이다. 실패한 심사는 기록으로 남아 공식 리뷰 근거에 "유효한 readiness 결과 없음" 으로 실릴 뿐이고, 진행을 결정하는 것은 언제나 기존 공식 리뷰 게이트다. 직전 설계에서 무한 대기 고리를 만든 것은 실패가 한도를 소모하고 그 한도가 전이를 결정하는 구조였는데, 이 Spec 에는 그 구조가 없다.

## Security and risk

- 두 Codex 프로세스 모두 sandbox 를 우회하지 않는다. author 는 `workspace-write`, readiness 는 `read-only` 다. 승인 우회·권한 확장 옵션 여덟 개는 R1.4 가 CLI 버전과 함께 열거하고 `references/readiness-policy.md` 가 그것을 싣는다. 그 목록은 `--help` 출력이 아니라 플래그별 수용 여부 실측으로 만들었다.
- 프롬프트·결과·이벤트·표준 오류 파일에 자격 증명을 넣지 않는다. 이 파일들은 `.claude/quality-state/<task-id>/` 아래에만 둔다.
- 이 저장소에서 `.claude/quality-state/` 는 이미 무시된다. `git check-ignore -v .claude/quality-state/` 가 `.gitignore:25` 를 근거로 종료 코드 0 을 반환한다.
- 배포본 `~/.claude/skills/quality-goal/` 을 이 작업에서 갱신하지 않는다. 다른 세션이 그 배포본(v5.0.0)을 실행 중이며 `chezmoi apply` 는 그 세션의 계약을 실행 중에 바꿔 버린다.
- readiness reviewer 는 읽기 전용이므로 심사가 산출물을 조용히 고칠 수 없다. author 만 쓰기 권한을 갖고, 그 쓰기 범위는 두 파일로 한정된다.
- 위험: readiness 가 통과시킨 산출물을 Claude 가 낮게 평가하는 경우가 실측으로 두 번 있었다. 이 설계는 그 격차를 없애려 하지 않는다 — readiness 가 아무것도 결정하지 않으므로 격차가 손해를 만들지 않는다. 절감은 author 쪽에서 나온다(#42 4차: Spec 개정 3회 85분, Claude 토큰 0).
- 위험: readiness 가 아무것도 강제하지 않으므로 오케스트레이터가 그것을 무시하고 미성숙한 산출물을 공식 리뷰에 보낼 수 있다. 이 위험은 의도적으로 수용한다 — 강제하는 설계가 두 실행을 종결시킨 원인이었고(§ Problem and context), 공식 리뷰 라운드 한도 3 이 이미 비용 상한으로 작동한다. #76 이 게이트를 설계할 때 이 위험을 다시 다룬다.
- 위험: 체크리스트 항목이 늘어나면 readiness 가 형식 트집으로 개정을 반복시킬 수 있다. 항목을 여덟 개로 고정하고, 항목 추가는 별도 정책 결정으로 다룬다.

## Test strategy

신규 계약의 판정 수단은 `dot_claude/skills/quality-goal/tests/` 의 결정적 테스트가 기본이고, 문서 문언의 존재 여부만으로 확인되는 일곱 건(AC-28, AC-31, AC-35, AC-39, AC-44, AC-62, AC-76)만 `[문서]` 판정이다(R9.4). 결정적 테스트로 판정하는 것 중 문서 계약은 `test_content_contracts.py` 에, 상태·기록 계약은 `test_quality_state.py` 에, 결과 스키마 검증은 `test_validate_review.py` 에 추가한다. Codex 프로세스를 실제로 호출하는 테스트는 만들지 않는다. 호출 계약은 문서에 실린 템플릿 문자열로 판정하고, 기록·검증은 결과 JSON 픽스처로 판정한다.

픽스처는 `tests/fixtures/` 에 추가한다: READY 결과 1건, 체크리스트 1개 실패 결과 1건, Critical/High 포함 결과 1건, 스키마 위반 결과 1건, 새 두 필드가 없는 schema v1 상태 1건.

### 판정 명령 표

모든 `[실행]` AC 는 아래 명령 중 하나로 판정한다. 작업 디렉터리는 저장소 루트다.

| ID | 명령 | 통과 조건 |
|---|---|---|
| CMD-1 | `python3 dot_claude/skills/quality-goal/tests/assert_python_version.py && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/quality-goal/tests -p 'test_*.py'` | 종료 코드 0, `OK` |
| CMD-2 | `python3 dot_claude/skills/quality-goal/tests/assert_python_version.py &&` 를 앞에 두고 `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/quality-goal/tests -p 'test_*.py' -k <테스트 이름>` | 종료 코드 0. 3.12 이상에서 매칭이 0건이면 `unittest` 가 종료 코드 5 를 내므로 존재하지 않는 테스트 이름은 이 조건을 통과할 수 없다 |
| CMD-3 | `wc -l < dot_claude/skills/quality-goal/SKILL.md` | 500 미만 |
| CMD-4 | 아래 § CMD-4 상세의 스크립트 | 종료 코드 0, `보존 대상 절 불변` 출력 |
| CMD-5 | `python3 -c "import json;d=json.load(open('dot_claude/skills/quality-goal/schemas/readiness-result.schema.json'));assert d['type']=='object';assert d['additionalProperties'] is False;print('OK')"` | 종료 코드 0, `OK` 출력 |
| CMD-6 | 아래 § CMD-6 상세의 스크립트 | 종료 코드 0, `기존 테스트 보존` 출력 |
| CMD-7 | `OLD_PY` 를 3.12 미만 인터프리터 경로로 두고 `"$OLD_PY" -c 'import sys;raise SystemExit(0 if sys.version_info<(3,12) else 1)' && python3 dot_claude/skills/quality-goal/tests/assert_python_version.py && ! "$OLD_PY" dot_claude/skills/quality-goal/tests/assert_python_version.py` | 종료 코드 0. 첫 절이 `OLD_PY` 가 실제로 3.12 미만임을 단언하고, 둘째 절이 스크립트 부재·구문 오류를 잡고, 셋째 절이 거부 분기를 확인한다. macOS 에서는 `OLD_PY=/usr/bin/python3`(3.9.6)이 성립한다. 어떤 인터프리터도 3.12 미만이 아니면 이 명령은 실행할 수 없고, 그때 AC-85 는 미판정으로 검증 기록에 남긴다. 그 경우에도 가드의 거부 분기는 AC-90 이 CMD-2 로 판정하므로 미판정으로 남는 계약은 없다 |

테스트 스위트는 **Python 3.12 이상**을 요구한다. 근거 둘 다 실측이며 R9.8 이 같은 내용을 담는다. CMD-1 과 CMD-2 는 테스트를 실행하기 전에 `tests/assert_python_version.py` 로 그 조건을 확인하며, 조건이 어긋나면 테스트를 실행하지 않고 실패한다. CMD-7 은 **같은 스크립트**를 3.12 미만 인터프리터로 실행해 거부 분기를 직접 확인한다.

**판정 명령 표는 두 곳에 있고 정본은 하나다.** 정본은 `docs/quality-goal-maintenance.md` 의 `## 판정 명령 표` 절이며, 스킬과 함께 유지되고 저장소 테스트가 읽는다. 이 Spec 의 위 표는 그 정본을 이 작업 시점에 옮겨 적은 **사본**이다 — `docs/development/…/spec.md` 는 goal 이 끝나면 옮겨지거나 지워질 수 있는 일회성 산출물이라 영구 테스트가 읽으면 CMD-1 이 영구히 깨진다. 정본이나 그 판정 스크립트를 판정하는 AC 는 다섯이다 — AC-75 는 정본의 절 대체와 CMD-1~CMD-7 일곱 행과 정본 선언을, AC-76 은 정본의 최소 인터프리터 버전 문언과 두 근거를, AC-86 은 정본의 CMD-1·CMD-2 정의가 `tests/assert_python_version.py` 를 호출하고 버전 비교식을 인라인으로 복제하지 않는지를, AC-85 는 문서가 아니라 그 스크립트의 동작을 CMD-7 로, AC-87 은 세 스크립트의 존재와 `unittest` 수집 제외를 판정한다. § Requirements traceability 에서 앞의 둘은 R9.3 에, 뒤의 셋은 R9.8 에 매핑된다. 이 Spec 의 사본을 판정하는 AC 는 두지 않는다.

### CMD-4 상세

보존 대상 절을 base revision 과 바이트 단위로 비교한다. 비교 대상은 여덟이다 — `### Plan`, `### Approval`, `### Implementation`, `### Code review`, `## Independent verification`, `## Safety rules`, `## Review invocation contract`, `## Codex invocation contract`. 앞의 넷은 R9.5 의 Plan·Code 단계 절차이고, 다음 둘은 승인 digest·dirty-worktree 보호·결정적 검증 계약이며, 마지막 둘은 plan·code 리뷰어 호출과 구현·수정 라운드의 codex 호출·model-unavailable 복구를 실제로 지배하는 절이다. 이 변경은 여덟 절을 모두 건드리지 않는다. readiness 절차는 `### Spec` 절과 Stage table, 참조 경로 목록, 그리고 새 `references/readiness-policy.md` 에만 들어간다.

```
git show <base>:<SKILL.md> 로 base 본문을 얻고 현재 본문과 함께
^#{2,3} 헤딩으로 절을 쪼갠 뒤 위에 열거한 여덟 절의 본문이 같은지 단언한다.
절 이름 목록은 스크립트 안에 상수로 두고 여덟 개를 모두 싣는다.
모두 같으면 "보존 대상 절 불변" 을 출력하고 0 으로 끝낸다.
```

실행 스크립트는 `tests/assert_preserved_sections.py` 로 두고 CMD-4 는 그 스크립트를 호출한다.

### CMD-6 상세

base revision 의 `tests/test_*.py` 네 파일(`test_content_contracts.py`, `test_quality_state.py`, `test_validate_review.py`, `test_revision_check.py`)에서 `def test_` 이름을 모아 현재 이름 집합의 부분집합인지 단언한다. 하나라도 삭제되거나 이름이 바뀌면 실패하고, 통과하면 `기존 테스트 보존` 을 출력한다. 실행 스크립트는 `tests/assert_tests_preserved.py` 로 둔다.

### 검증 순서

1. CMD-1 로 전체 회귀를 먼저 확인한다.
2. 실패한 AC 가 있으면 CMD-2 로 해당 테스트만 좁혀 재현한다.
3. CMD-3·CMD-4·CMD-5·CMD-6·CMD-7 은 CMD-1 과 독립적으로 실행한다.
4. Codex CLI 자체의 계약(`--output-schema` 가 `const` 를 거부하는 성질 등)은 이 저장소의 테스트로 판정하지 않는다. `docs/quality-goal-maintenance.md` 의 분기별 CLI 점검 절차에 위임한다.

## Decisions

### D1. readiness 를 게이트가 아니라 참고 심사로 둔다

- 대안 A: 이슈 본문대로 `readiness score >= 90` 게이트.
- 대안 B: 직전 설계대로 체크리스트 여덟 항목을 통과 조건으로 하는 결정적 게이트와 `AWAITING_READINESS_DECISION` 탈출 경로.
- 대안 C(채택): 체크리스트 여덟 항목을 유지하되 결과를 기록하고 공식 리뷰 근거로 첨부만 하며, 어떤 상태 전이도 결정하지 않는다.

근거: 대안 A 는 실측이 반증했다 — readiness 97 대 Claude 74, readiness 94 대 Claude 78 로 대응점 두 개가 같은 방향으로 크게 벌어졌다(§ Problem and context). 대안 B 는 이 저장소에서 두 번 실제로 시도됐고 두 번 다 종결됐다. 2026-09-06 실행의 세 blocker(`SPEC-03`→`SPEC-07`→`SPEC-11`)는 전부 게이트의 fail-open/fail-closed 규칙을 고칠 때마다 그 수정이 만든 새 구멍이었고, 직전 실행의 `R4.5` 논쟁까지 합치면 이 한 계층에서 연속 네 개의 High 가 나왔다. 대안 C 는 그 계층을 통째로 들어낸다. readiness 의 가치는 기계적 결함을 값싸게 걷어내는 데 있고 그 가치는 판정 권한 없이도 그대로 남는다 — author 개정 주기 안에서 결함을 보여주는 것으로 충분하다. 비용은 미성숙 산출물이 공식 리뷰에 갈 수 있다는 것이며, 공식 리뷰 라운드 한도 3 이 이미 그 비용의 상한이다(§ Security and risk).

### D2. `schema_version` 은 1 을 유지한다

- 대안 A(채택): `schema_version` 1 유지. R6.2 의 두 필드를 선택적 필드로 추가하고, 없으면 미실행으로 간주한다. 로드 시 상태 파일에 주입하지 않는다(R6.3).
- 대안 B: `schema_version` 2 로 올리고 `load_state` 가 1 과 2 를 모두 수용한다.
- 대안 C: 2 로 올리고 v1 을 별도 마이그레이션 명령으로 변환한다.

근거: `load_state` 는 현재 `schema_version != 1` 을 거부한다(`scripts/quality_state.py:264-265`). 대안 B·C 로 v2 파일을 만들면 이 변경을 `git revert` 했을 때 진행 중인 goal 의 상태 파일을 구버전 스크립트가 읽지 못해 데이터가 손실된다. 스킬 롤백은 실제 운용 경로이며 유지보수 문서가 SemVer 정책으로 다루는 상황이다. 대안 A 는 신구 스크립트가 같은 파일을 양방향으로 읽게 한다. 비용은 버전 번호로 형태를 구별할 수 없다는 것이며, 필드 존재 검사로 대체한다.

### D3. 체크리스트 항목을 여덟 개로 고정한다

- 대안 A: 항목을 설정값으로 열어 둔다.
- 대안 B(채택): C1~C8 을 문서와 스키마에 고정하고 변경은 별도 정책 결정으로 다룬다.

근거: 항목이 유동적이면 readiness 가 형식 트집으로 개정을 반복시키는 실패 모드가 열린다. 고정하면 `checklist` 배열의 완전성 자체를 스키마로 강제할 수 있다(AC-68).

### D4. C8 의 판정 대상을 프롬프트에 실린 것으로 한정한다

- 대안 A: 직전 설계대로 "직전 리뷰" 를 상태 기록에서 유도하고, 닫힘이 기록 간에 누적되게 한다.
- 대안 B(채택): 판정 대상은 오케스트레이터가 그 호출의 프롬프트에 실은 findings 전문이 전부이며(R2.5 ④), 상태 기록을 훑지 않는다.

근거: 대안 A 의 누적 규칙은 게이트의 대체 판정(어떤 기록이 앞선 Critical/High 를 닫았는가)을 위해서만 필요했다. 게이트가 없으면 그 계산의 소비자가 없다. 실제로 `SPEC-11` 은 그 누적이 프롬프트 범위와 어긋나 세 번째 시도부터 영구히 열리지 않는 고리를 만든 것이었다. 대안 B 는 프롬프트와 판정 대상을 같은 것으로 묶어 그 어긋남 자체를 없앤다. `resolved_finding_ids` 는 계속 기록하지만(R6.1, R8.4) 아무것도 판정하지 않으며, 이슈 #76 이 게이트를 설계할 때 그 위에 누적 규칙을 얹는다.

### D5. author 가 초안 작성까지 담당한다

- 대안 A: 초안은 Claude 가 쓰고 개정만 Codex 가 한다.
- 대안 B(채택): 오케스트레이터가 요구사항 발굴을 수행해 프롬프트에 담고, 초안 작성과 개정을 모두 author 가 한다.

근거: 이슈 #70 의 목표는 "작성과 반복 개정"을 옮기는 것이다. 실측은 개정만 검증했으나(#42 는 이미 초안이 있었다), 초안 작성이 개정보다 분량이 크므로 절감 폭이 더 크다. 요구사항 발굴은 사용자 질의가 필요할 수 있어 오케스트레이터에 남긴다. 위험은 초안 품질이 낮으면 개정 주기가 늘어난다는 것이며, 그 상한은 오케스트레이터의 비용 지시와 공식 리뷰 라운드 한도가 함께 만든다(R4.3).

### D6. readiness 절차는 `references/readiness-policy.md` 로 분리한다

- 대안 A: `SKILL.md` 에 직접 싣는다.
- 대안 B(채택): 상세를 새 reference 로 빼고 `SKILL.md` 에는 단계 절차와 참조 경로만 싣는다.

근거: `tests/test_content_contracts.py:1244` 가 frontmatter 를 포함한 `SKILL.md` 파일 전체를 500행 미만으로 강제한다(R9.1). 현재 393행이고 상한이 499행이므로 더 넣을 수 있는 것은 106행이며, author·readiness 두 호출 계약과 체크리스트 정의를 모두 넣으면 초과한다. 기존 스킬이 이미 정책을 reference 로 분리하는 구조를 쓴다.

### D7. Spec 템플릿에 요구사항 추적표 절과 판정 명령 표 절을 추가한다

- 대안 A: 추적표가 있으면 검사하고 없으면 해당 항목을 `not_applicable` 로 둔다.
- 대안 B(채택): 템플릿에 두 절을 추가해 항상 존재하게 한다.

근거: C3·C4·C5·C7 네 항목은 추적표와 판정 명령 표가 있어야 판정 가능하다. 대안 A 는 체크리스트의 절반을 사실상 무력화한다. 이 결정은 열린 이슈 #58(Spec 요구사항 추적표 필수화)의 범위와 겹치지만, 겹치는 부분은 템플릿에 절을 추가하는 것 하나이고 #58 이 다루는 리뷰 루브릭·`REQUIRED_CHECKS` 변경은 하지 않는다.

### D8. author 결과는 기존 `codex-result.schema.json` 으로 검증한다

- 대안 A: author 전용 결과 스키마를 신설한다.
- 대안 B(채택): 구현 라운드가 쓰는 `schemas/codex-result.schema.json` 을 그대로 쓴다.

근거: 그 스키마가 요구하는 것은 `changed_files`, 명령별 종료 코드와 결과, 계획 이탈, 잔여 우려이며 전부 문서 개정 작업에도 그대로 대응한다. author 는 `spec.md` 와 개정 노트 두 파일을 바꾸고(R1.6), 자기 검증으로 돌린 명령이 있으면 그것을 싣고, 조합 검토에서 남은 우려를 잔여 우려로 보고한다. 스키마를 하나 더 만들면 `--output-schema` 계약이 둘로 갈라져 R2.4 의 `const` 금지 같은 제약을 두 곳에서 관리해야 한다.

### D9. 실패한 readiness 시도도 기록으로 남긴다

- 대안 A: 스키마 위반·digest 불일치·호출 실패는 기록하지 않고 재시도한다.
- 대안 B(채택): 실패도 `outcome` 이 붙은 기록으로 남긴다.

근거: 기록이 없으면 재개 시점에 그 라운드에서 무슨 일이 있었는지 알 수 없고, 이슈 #76 이 나중에 시도 한도를 설계할 때 셀 대상이 사라진다. 실제로 `.prior-art/.codex-readiness/result-attempt3.json`(score 0, evidence 0건)과 `result-attempt5.json`(스키마 충돌로 score 0)에서 결과가 손상된 사례가 두 번 있었다. 기록은 남기되 이 Spec 에서는 그 수가 아무것도 결정하지 않는다(R4.3).

### D10. readiness 는 Spec 단계에만 도입한다

Plan 확장은 #70 2단계, eval·비용 측정은 3단계, Code 단계 readiness 는 #70 코멘트 1 이 남긴 후속 검토 항목이다. Plan 은 Spec 이 확정된 뒤 파생되므로 Spec 단계에서 계약이 안정된 다음에 같은 구조를 복제하는 편이 재작업이 적다. 그럼에도 `draft_attempts` 와 `readiness` 두 필드는 처음부터 `spec`·`plan` 두 키를 갖는다 — 2단계가 상태 형태를 바꾸지 않고 값만 채우게 하기 위해서다(R6.2).

### D11. strict-only 블록을 제거한 근거

이 산출물은 standard 모드이므로 `templates/spec.md` 의 strict 전용 블록(템플릿에서 strict-only 주석 쌍으로 감싼 구간)을 제거했다. 이 Spec 본문에는 그 주석 쌍이 남아 있지 않다. 제거한 여섯 소절이 이 작업에 적용되지 않는 이유는 다음과 같다.

- Threat and trust boundaries — 신뢰 경계를 넘는 입력이 없다. 두 Codex 프로세스는 모두 로컬 sandbox 안에서 이 저장소 파일만 읽고 쓴다.
- Authorization and tenant isolation — 권한 주체나 테넌트 개념이 없다. 단일 사용자의 로컬 개발 환경이다.
- Migration, compatibility, and rollback — 해당 내용은 D2 와 R6.3·R6.4, § Failure behavior 에 이미 실렸다. 데이터 마이그레이션이나 백필은 없다.
- Failure recovery and observability — 알림·메트릭·트레이스 대상이 되는 상시 실행 구성 요소가 없다. 복구 경로는 § Failure behavior 표가 전부 다룬다.
- High-risk end-to-end verification — 고위험 경로가 없다. 결정적 검증은 § Test strategy 판정 명령 표의 일곱 명령이다.
- No production mutation confirmation — 프로덕션 대상이 존재하지 않는다. 다만 배포본 `~/.claude/skills/quality-goal/` 을 이 작업이 갱신하지 않는다는 것은 § Security and risk 에 명시했다.

### D12. 규모 목표와 그 달성 방법

이 Spec 의 요구사항은 45건, AC 는 90건이다(목표 상한 45·90). 직전 Spec 은 요구사항 71건, AC 120건이었으므로 요구사항은 26건, AC 는 30건 줄었다. 라운드 2 개정에서 AC 세 건(AC-88·AC-89·AC-90)이 늘어 상한과 같아졌으므로, 라운드 3 에서 AC 를 더 늘려야 하면 그 전에 중복 판정을 병합해 자리를 만든다. 요구사항 26건의 감소는 이관과 병합의 합이며, 이 Spec 이 새로 만든 요구사항은 R4.4(공식 리뷰 근거 첨부) 하나다.

- **통째로 사라진 요구사항은 여덟이다** — 직전 Spec 의 `R2.8`, `R4.1`, `R4.2`, `R4.4`, `R4.5`, `R4.8`, `R4.9`, `R6.10`. § Problem and context 의 이관 표는 `R2.10` 과 `C8` 도 함께 싣지만 그 둘은 사라지지 않았다 — `R2.10` 의 프롬프트 필수 요소는 R2.5 ④로, `C8` 은 체크리스트의 여덟 번째 항목으로 남았고 이관된 것은 그 둘의 게이트 연계(닫힘을 상태 기록에서 누적하는 범위 규칙)뿐이다(D4). 직전 `R6.2` 의 `readiness_decisions` 항목도 같은 방식으로 항목만 빠지고 요구사항 자체는 R6.2 로 남았다.
- **나머지 감소는 병합이다.** 조건이 같은 대상을 가리키는 문언을 하나로 합쳤다: `codex exec` 의 승인 플래그 부재를 금지 목록에 흡수(R1.4), 개정 노트 형식을 프롬프트 필수 요소에 흡수(R1.5), 호출 실패 네 경우를 하나로(R1.9), 프롬프트 명시 사항 넷을 하나로(R2.5), 체크리스트 충족 규칙과 항목별 기록을 하나로(R3.1), `outcome`·거부 계약·light 거부를 하나로(R6.6), 스키마 필드 제약을 하나로(R8.1), Python 버전 전제와 판정 스크립트를 하나로(R9.8).

병합한 요구사항은 조건이 여러 개이므로 각각 독립 AC 를 갖는다 — 추적표가 그 대응을 확정한다. 상한을 넘겨 비목표로 뺀 항목은 없다.
