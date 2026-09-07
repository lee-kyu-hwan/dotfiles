# Quality Goal Specification

- Task ID: 20260905T073930Z-70-quality-goal-spec-단계에-codex-author-fr-7ec207bb
- Mode: standard
- Status: SPEC_REVIEW
- Created: 2026-09-05T07:39:30Z
- Updated: 2026-09-05T07:39:30Z
- Source goal: #70 quality-goal Spec 단계에 Codex author + fresh Codex 체크리스트 readiness 사전 심사 파이프라인 추가 (1단계)

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

- 잡은 것: 템플릿 절 구조와 strict marker 쌍, 요구사항↔AC 추적표 무결성, 번호 연속성·중복, 직전 리뷰 findings 의 `required_resolution` 부분 해소 판정(`.prior-art/.codex-readiness/result-attempt4.json` 의 READY-01), author 개정 노트 주장의 기각(`.prior-art/.codex-readiness/prompt.md` 의 "노트는 근거가 아니라 검증 대상" 규칙이 두 번 작동).
- 놓친 것: 시간축·상태 전개를 따라가야 보이는 결함, 개별 수정이 만든 교차 회귀(#42 4차에서만 SPEC-31 과 SPEC-34·35 두 번), 요구사항 본문과 Decisions 절의 정면 충돌. 전부 Claude 가 잡았다.

따라서 이 작업은 점수 게이트가 아니라 **기계적으로 확인 가능한 항목만으로 구성된 체크리스트 게이트**를 설계한다. 설계 정합성 판정은 Claude 공식 리뷰에 온전히 남긴다.

작업 대상 파일은 `dot_claude/skills/quality-goal/` 하위다. 이 저장소는 chezmoi source 이며 `~/.claude/skills/quality-goal/` 이 배포본이다. 현재 두 트리는 이 작업이 고치는 실행 파일에서 동일하다(`SKILL.md`, `references/model-routing.md`, `references/spec-rubric.md`, `scripts/quality_state.py`, `scripts/validate_review.py` diff 무차이 확인). `tests/` 만 배포본이 뒤처져 있다(`test_revision_check.py` 와 `tests/fixtures/revision-check/` 미배포). 이 작업은 배포본을 갱신하지 않으므로(§ Security and risk) 그 격차를 좁히지 않는다. 결정적 검증 기준선은 base revision `6d60011cbdaead7946b191d3f12029eef5c141c8` 에서 Python 3.12 이상으로 실행한 310 테스트 통과다. 인터프리터 전제가 붙는 이유는 § Test strategy 의 CMD-1 과 R9.9 에 있다.

## Goals

1. standard·strict 모드의 `SPEC_REVIEW` 단계에서 Spec 의 초안 작성과 모든 개정을 Codex author 가 수행하고, Claude 오케스트레이터는 Spec 본문을 직접 쓰지 않는다.
2. author 와 분리된 fresh Codex 프로세스가 Claude 공식 리뷰 전에 readiness 를 사전 심사한다.
3. readiness 통과 판정을 전부 기계적으로 확인 가능한 체크리스트 항목으로 구성하고, 점수는 참고값으로만 기록한다.
4. readiness 시도가 Claude 공식 리뷰 라운드(`rounds.spec`)를 소모하지 않고, 시도 구간당 상한(R4.1)과 결정적인 탈출 경로를 갖는다.
5. 이슈 #70 코멘트에 기록된 여섯 가지 실무 함정을 계약으로 고정해 재발을 막는다.
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
11. readiness 잔여 blocker 를 Claude 공식 리뷰가 upheld/overruled 로 판정하는 계약. 그것이 있어야 Critical/High 가 남은 산출물도 공식 리뷰로 보낼 수 있지만, `review.schema.json` 의 닫힌 finding 구조와 `verdict` enum 을 함께 바꿔야 하므로 별도 작업이다. 이슈 #76 이 추적한다(§ Decisions D10).

## Requirements

### R1. Codex Spec author

- **R1.1** standard·strict 모드의 `SPEC_REVIEW` 단계에서 Spec 초안 작성과 이후 모든 개정은 Codex author 프로세스가 수행한다. Claude 오케스트레이터는 `spec.md` 본문을 직접 작성하거나 편집하지 않는다.
- **R1.2** 오케스트레이터는 author 호출 전에 `brainstorming-policy.md` 에 따른 요구사항 발굴을 수행하고, 그 결과(문제·목표·비목표·제약·저장소 근거 경로)를 author 프롬프트에 담는다. 발굴에서 남은 물질적 모호성은 author 호출 전에 사용자에게 질의해 해소한다.
- **R1.3** author 는 `codex exec` 로 호출한다. 필수 인자는 `-C <project_root>`, `--sandbox workspace-write`, `--ephemeral`, `--model <route model>`, `-c model_reasoning_effort="<route effort>"`, `--output-schema <author schema>`, `--output-last-message <result path>`, `--json`, 그리고 표준 입력으로 주는 프롬프트 파일이다.
- **R1.4** author 호출은 설치된 Codex CLI 가 노출하는 승인 우회·권한 확장 옵션을 사용하지 않는다. codex-cli 0.153.4 기준으로 그 목록은 `--skip-git-repo-check`, `--dangerously-bypass-approvals-and-sandbox`, `--dangerously-bypass-hook-trust`, `--approve-for-me`, `--ignore-rules`, `--ignore-user-config`, `--add-dir`, `--yolo` 여덟이며, `--sandbox` 에 `workspace-write` 보다 넓은 값을 주는 것도 금지한다. `--yolo` 는 `codex exec --help` 에 나오지 않지만 실제로 수용된다 — `codex exec --yolo --version` 이 `codex-cli-exec 0.153.4` 를 출력하는 반면 존재하지 않는 플래그는 사용법 안내를 낸다. `--help` 출력만으로 금지 목록을 만들면 이 숨은 별칭을 놓친다. 같은 버전에서 `--full-auto` 는 존재하지 않는 플래그와 같은 반응을 보인다. 이 금지의 열거는 CLI 버전과 함께 `references/readiness-policy.md` 에 싣는다. `SKILL.md` 의 기존 Safety rules 문언은 바꾸지 않는다 — 그 절은 이미 세 플래그 열거와 `Sandbox bypass is prohibited.` 라는 포괄 금지를 함께 담고 있어(SKILL.md:391-392) 새 플래그를 추가하지 않아도 포괄 금지가 성립하며, R9.6 이 그 절의 불변을 요구한다(AC-78).
- **R1.5** `codex exec` 에는 `-a/--ask-for-approval` 이 존재하지 않는다. 이 스킬의 어떤 문서도 `codex exec` 호출에 그 플래그를 지시하지 않는다.
- **R1.6** author 프롬프트는 다음 **열둘**을 모두 포함한다: 개정 대상 Spec 파일의 절대 경로, `templates/spec.md` 절대 경로, `references/spec-rubric.md` 절대 경로, `references/brainstorming-policy.md` 절대 경로, **`references/revision-check-policy.md` 절대 경로**, 반영할 findings 전문의 경로, 기존 요구사항·AC 번호 보존과 신설 번호 이어붙이기 규칙, **그 정책이 정의한 식별자 문법(`- **R<n>.<m>**`, `- **AC-<n>**`, `[실행]`·`[문서]`, 추적표, 판정 명령 표)을 지키라는 지시**, 개정 노트 파일 경로, **라운드 2 이상에서 개정 노트가 갖춰야 할 형식**(R1.12), git 쓰기 명령 금지, 그리고 개정 완료 직전의 조합 검토 지시. 뒤의 셋을 넣지 않으면 base revision 이 이미 강제하는 개정 점검(`revision_check.py`)이 라운드 2 이상에서 종료 코드 0 을 내지 못해 `record-review --revision-check` 가 거부되고, 그 복구를 오케스트레이터가 본문으로 하려 들면 R1.1 이 금지한 작성 주체 이전이 된다.
- **R1.7** author 는 대상 Spec 파일과 개정 노트 파일 두 개 외의 파일을 수정하지 않는다. 프롬프트가 그 제약을 명시하고, 오케스트레이터가 호출 후 `git status --porcelain` 으로 확인한다. 비교 대상은 상태의 `initial_dirty_paths` 와 `.claude/quality-state/<task-id>/` 하위를 **제외한** 경로이며, 그 결과를 author 결과의 `changed_files` 와 대조한다. 이 제외 규칙이 없으면 dirty 상태에서 시작한 모든 goal 이 author 호출마다 오탐으로 § Failure behavior 의 사용자 판단 요청 경로에 빠진다. 기존 스킬의 dirty-path 보존 계약(`SKILL.md:361-364`, `initial_dirty_paths`)과 같은 기준이다.
- **R1.8** author 의 조합 검토 지시는 "이번 개정이 직전 개정에서 세운 계약과 충돌하거나 새 결손을 만들지 않는지 마지막에 한 번 교차 점검한다"를 포함한다. 근거는 #42 실행 계열에서 개별 해소가 교차 회귀를 만든 전례 다섯 건(PLAN-009·010·012, SPEC-31, SPEC-34·35)이다.
- **R1.9** author 호출 횟수는 `draft_attempts.spec` 에 기록하며 `rounds.spec` 을 증가시키지 않는다.
- **R1.10** author 호출이 0 이 아닌 종료 코드를 반환하거나 결과 파일이 없거나 스키마 검증에 실패하면, 오케스트레이터는 `SPEC_REVIEW` 단계에 머문 채 실패 내용을 사용자에게 보고하고 모델을 임의로 대체하지 않는다. 모델 거부는 `BLOCKED_MODEL_UNAVAILABLE` 복구 경로를 따른다.
- **R1.11** author 호출 후 대상 Spec 파일의 SHA-256 이 호출 전과 같으면 개정 실패로 간주하고 R1.10 과 같은 경로를 따른다.
- **R1.12** author 프롬프트가 싣는 개정 노트 형식은 `references/revision-check-policy.md` 에서 그대로 인용한다 — 라운드 `<n>` 의 정확한 절 헤딩 `## 라운드 <n> 개정` 과 다섯 열 표 머리 `| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |` 다. **한 `formal_round` 에는 그 라운드의 절이 정확히 하나 있다.** 같은 라운드 안에서 readiness 개정이 반복되면 새 절을 만들지 않고 그 하나의 절에 행을 누적하고, 이미 있는 행의 판정이 바뀌면 그 행을 갱신한다. 그 절이 다루는 범위는 직전 라운드의 스냅숏(`snapshots/<artifact>-r<N-1>.md`) 이후의 모든 변경이며, readiness 가 유발한 변경도 거기 포함된다. 라운드마다 절이 하나여야 하는 이유는 개정 점검이 그 라운드의 절 하나만 읽어 파급표를 대조하기 때문이다. 이 규칙을 문서로만 두지 않고 `references/readiness-policy.md` 가 인용문으로 싣는다.

### R2. fresh Codex readiness reviewer

- **R2.1** readiness reviewer 는 author 와 별개의 `codex exec` 프로세스로 실행한다. author 의 대화 문맥·세션·개정 노트의 주장을 근거로 상속하지 않는다.
- **R2.2** readiness reviewer 호출은 `--sandbox read-only` 를 사용하고, R1.4 가 금지한 플래그를 사용하지 않는다.
- **R2.3** readiness reviewer 호출은 표준 입력이 대화형 터미널에 연결되지 않게 한다. 기본 형태는 프롬프트 파일을 표준 입력으로 주는 것(`- < "$PROMPT_PATH"`)이고, 프롬프트를 명령행 인자로 넘기는 형태를 쓸 때는 `< /dev/null` 을 붙인다. 둘 중 어느 형태도 아닌 호출은 금지한다. 비대화형에서 stdin 을 열어두면 `Reading additional input from stdin...` 에서 무한 대기한다(이슈 #70 코멘트 1, 함정 2). 이 요건은 author 호출(R1.3)에도 같이 적용된다.
- **R2.4** readiness 결과 스키마의 모든 property 는 `type` 키를 갖는다. `const` 키는 사용하지 않는다. `codex exec --output-schema` 는 `const` 만 있는 property 를 `invalid_json_schema` 400 으로 거부한다(이슈 #70 코멘트 1, 함정 1). 고정값이 필요한 곳은 `{"type": "string", "enum": ["spec"]}` 형태로 쓴다.
- **R2.5** readiness reviewer 프롬프트는 "개정 노트는 근거가 아니라 검증 대상이며, 노트가 반영했다고 적은 것을 Spec 본문에서 파일:행으로 확인한다"를 명시한다.
- **R2.6** readiness reviewer 프롬프트는 자신의 판정이 비용 제어 게이트이며 Claude 공식 판정을 대체하지 않는다는 것, 그리고 설계 취향 문제로 감점하지 않는다는 것을 명시한다.
- **R2.7** readiness reviewer 는 읽기 전용이다. 파일 수정과 git 쓰기 명령을 금지한다.
- **R2.8** Claude 공식 Spec 리뷰 라운드는 그 라운드의 게이트 판정(R6.10)이 `READY` 또는 `ARBITRATION` 일 때만 시작한다. readiness 를 한 번도 실행하지 않은 상태에서 공식 리뷰를 시작하지 않는다. 이 조건은 서술이 아니라 spec artifact 를 기록하는 두 경로 `record-review` 와 `record-review-unverified` 가 강제한다. `record-review-error` 는 면제한다 — 그 명령은 리뷰 결과를 무효로 처리하는 기록이라 통과시켜도 미성숙 산출물이 라운드를 소모하지 않는다. 다만 상태에 readiness 필드가 아예 없는 경우(R6.4 의 schema v1 재개)는 두 경로 모두 예외로 통과시킨다. 그 예외가 없으면 이 변경 이전에 시작한 goal 이 재개 시점에 영구히 막힌다.
- **R2.9** `light` 모드 상태에서 `record-readiness`, `readiness-gate`, `record-draft-attempt`, `resume-readiness` 네 명령은 모두 오류로 거부한다. light 는 `SPEC_REVIEW` 를 거치지 않으므로 정상 경로에서 호출될 일이 없고, 조용히 무시하면 잘못된 호출이 드러나지 않는다.
- **R2.10** readiness reviewer 프롬프트는 C8 이 정의한 **직전 리뷰** 의 findings 전문을 검증 대상으로 싣는다 — 같은 `formal_round` 의 직전 readiness 시도 결과 JSON 경로와 직전 Claude 공식 리뷰의 open findings 경로 둘 다이며, 각 finding 의 ID·severity·`required_resolution` 이 프롬프트에서 읽을 수 있어야 한다. 이는 R2.1 의 문맥 상속 금지와 구분된다 — **금지 대상은 author 의 대화 문맥·세션·개정 노트의 주장이고, 리뷰어 산출물의 파일 전달은 허용이다.** 둘의 차이는 전자가 "고쳤다" 는 저자의 주장인 반면 후자는 독립 심사가 남긴 판정이라는 데 있다. R2.5 가 개정 노트를 근거가 아니라 검증 대상으로 규정하는 것과 같은 구별이다.

### R3. 체크리스트 게이트

- **R3.1** readiness 판정은 다음 여덟 항목 전부 충족일 때만 READY 다. 항목 하나의 충족은 `pass` 또는 `not_applicable` 이고, `fail` 만 미충족이다. 하나라도 미충족이면 REVISE 다.
  - **C1** 템플릿 절 구조 준수: `templates/spec.md` 의 필수 절이 모두 존재하고 순서가 유지된다.
  - **C2** strict marker 쌍: `templates/spec.md` 가 strict 전용 구간의 시작과 끝을 표시하는 데 쓰는 두 HTML 주석이 산출물에서 짝을 이루거나, non-strict 산출물에서 둘 다 없다. 한쪽만 남은 상태는 미충족이다. 판정에 쓸 정확한 주석 문자열은 `references/readiness-policy.md` 가 템플릿에서 그대로 인용해 정의한다.
  - **C3** 요구사항 정의 수와 추적표 행 수가 같다.
  - **C4** 추적표에 누락·중복·유령 참조가 0 이다. 유령 참조는 추적표가 가리키는 요구사항 번호나 AC 번호가 본문에 정의되지 않은 경우다.
  - **C5** 모든 AC 에 판정 수단이 배정돼 있다. 판정 수단은 `[실행]` 명령 또는 `[문서]` 위치 중 하나다.
  - **C6** AC 번호가 연속이고 고유하다.
  - **C7** 모든 `[실행]` 판정 명령이 판정 명령 표에 등재돼 있다.
  - **C8** **직전 리뷰**의 findings 각각에 대해 `required_resolution` 이 Spec 본문에서 확인되고, 충족된 것은 그 finding ID 를 `resolved_finding_ids` 에 싣는다. 부분 해소는 미충족이며 그 ID 를 싣지 않는다. 여기서 **직전 리뷰**는 둘의 합집합이다 — ① 같은 `formal_round` 의 직전 readiness 시도 findings 전문, ② 직전 Claude 공식 리뷰의 open findings. 둘 다 없으면 이 항목은 자동 충족이다. ①을 포함하는 이유는 R6.10 의 대체 규칙이 '가장 최근 기록이 앞선 Critical/High 를 명시적으로 닫았는가' 를 게이트 입력으로 쓰기 때문이며, ①이 프롬프트에 실리지 않으면 fresh reviewer 가 앞선 finding 을 재판정할 방법이 없다(R2.10).
- **R3.2** readiness 결과의 `score` 는 기록 전용 참고값이다. 게이트 판정, 라운드 진행, 상태 전이 중 어디에도 사용하지 않는다.
- **R3.3** 각 체크리스트 항목의 판정은 `status`(`pass`/`fail`/`not_applicable`)와 판정 근거(파일:행 또는 미확인 사유)를 함께 기록한다.
- **R3.4** Critical/High severity 의 finding 이 하나라도 있으면 READY 가 될 수 없다. 이 조건은 체크리스트 여덟 항목과 별개로 독립 적용한다.
- **R3.5** 체크리스트 항목은 전부 문서에서 기계적으로 확인 가능한 것만으로 구성한다. 설계 정합성·아키텍처 타당성·시간축 전개 판정은 체크리스트에 넣지 않는다.

### R4. 반복 한도와 탈출 경로

- **R4.1** readiness 시도 한도의 단위는 **시도 구간**이다. 시도 구간은 하나의 `formal_round` 안에서 마지막 재개 결정(R4.8) 이후의 구간이며, 재개 결정이 없으면 그 `formal_round` 전체가 하나의 구간이다. 한 시도 구간의 readiness 시도는 최대 2회다. 이 한도는 공식 리뷰 라운드 한도(Spec 3 / Plan 2 / Code 3)와 다른 것이며 서로 소모하지 않는다(R4.6). 이 Spec 에서 '시도 구간' 이라는 말이 붙으면 readiness 한도를, '라운드 한도' 라는 말은 공식 리뷰 한도를 가리킨다.
- **R4.2** 이 2회 한도는 시도 구간 하나당 값이며 실행 전체 누적이 아니다. 새 시도 구간이 열리는 계기는 둘뿐이다 — Claude 공식 리뷰가 기록되어 `formal_round` 가 올라갈 때, 그리고 같은 `formal_round` 안에서 사용자의 재개 결정이 기록될 때(R4.8). 두 계기 모두 R6.10 의 한 계산 규칙으로 표현되므로 한 `formal_round` 가 재개를 거쳐 2회를 넘는 시도를 담을 수 있고, 그것이 자기모순이 아니라 정의다.
- **R4.3** readiness 결과 스키마의 `attempt` 는 실행 전체 누적 번호이며 상한을 두지 않는다. 스키마에 `maximum` 을 넣지 않는다. 누적 번호를 시도 구간당 한도와 혼동해 스키마 제약으로 옮기면 심사자가 지시와 스키마의 충돌을 blocker 로 올리고 score 0 을 반환한다(이슈 #70 코멘트 2, 함정 4; `.prior-art/.codex-readiness/result-attempt5.json`).
- **R4.4** 시도 구간의 2회를 소진하고도 READY 가 아닐 때, 그 `formal_round` 의 가장 최근 `recorded` 기록의 Critical/High finding 이 0 이면 Claude 공식 리뷰로 진행한다(arbitration). 이때 미충족 체크리스트 항목과 잔여 finding 전문을 공식 리뷰 컨텍스트의 저장소 근거로 함께 전달한다. 이 경로는 **Critical/High 가 남아 있다고 확인된 기록이 없을 때** 열린다. 두 경우가 해당한다 — (i) 그 `formal_round` 의 가장 최근 `recorded` 기록이 Critical/High 0 임을 확인한 경우, (ii) 그 `formal_round` 에 `recorded` 기록이 하나도 없어 판정 근거 자체가 없는 경우. (ii) 는 readiness 가 그 라운드에서 유효한 결과를 한 번도 내지 못한 상태이며, 오케스트레이터가 그 사실을 공식 리뷰 근거에 명시한다(§ Failure behavior). **금지되는 것은 이미 확인된 Critical/High 를 기록 무효화로 지우고 `ARBITRATION` 으로 내려가는 것이다** — 산출물을 한 번 더 고쳐 그 기록이 등록 digest 를 가리키지 않게 만드는 경로가 그것이며, R6.10 의 둘째 갈래가 그것을 막는다. 세 갈래의 반환값은 R6.10 이 하나의 표로 확정한다. Critical/High 가 남은 산출물을 공식 리뷰로 자동 진행시키는 경로는 두지 않는다 — 잔여 blocker 를 공식 리뷰가 upheld/overruled 로 판정하는 계약이 아직 없어 fail-open 이 되기 때문이다(이슈 #76).
- **R4.5** 시도 구간의 2회를 소진하고도 그 `formal_round` 의 가장 최근 `recorded` 기록에 Critical/High finding 이 남아 있으면(R6.10 표의 갈래 ②. 그보다 오래된 기록의 Critical/High 는 이 판정에 쓰지 않는다) 비종료 상태 `AWAITING_READINESS_DECISION` 으로 전이하고 `status_reason` 에 `READINESS_HELD:<finding id>` 를 기록한다. 이 상태에서 오케스트레이터는 잔여 Critical/High finding 전문과 미충족 체크리스트 항목을 사용자에게 제시하고 멈춘다. **사용자의 명시적 결정 없이는 공식 리뷰로도 종료 상태로도 진행하지 않는다.** readiness 는 비권위 심사자이므로 단독으로 종료 상태를 만들지 않는다(§ Architecture '세 심사의 역할 분리').
- **R4.6** readiness 시도는 `rounds.spec` 을 증가시키지 않는다.
- **R4.7** readiness 결과가 READY 인 즉시 그 라운드의 추가 시도를 중단하고 Claude 공식 리뷰로 진행한다.
- **R4.8** `AWAITING_READINESS_DECISION` 에서 사용자의 결정은 상태에 기록되는 서브커맨드로만 받는다. 재개 결정은 `resume-readiness` 가 `readiness_decisions` 에 기록하며 상태를 `SPEC_REVIEW` 로 되돌린다. 그 기록의 시점이 R6.10 시도 횟수 계산의 새 기준점이 되므로, 재개 직후 그 시도 구간의 시도 수는 0 이다. **`resume-readiness` 는 상태의 stage 가 `AWAITING_READINESS_DECISION` 이 아니면 호출을 거부한다.** 이 거부가 없으면 오케스트레이터가 `SPEC_REVIEW` 에서 곧바로 재개를 기록해 시도 구간을 임의로 새로 열 수 있고, R4.1 의 한도와 R4.4·R4.5 의 탈출 경로에 영원히 도달하지 않는다. 재설계·중단 결정은 기존 `transition` 으로 `NEEDS_REDESIGN`, `BLOCKED`, `CANCELLED` 중 하나로 간다. 대화 기록만으로는 어느 결정도 성립하지 않는다. 이는 stage 가 `AWAITING_PLAN_APPROVAL` 이 아니면 거부하는 `approve-plan` 과 같은 부류다(`quality_state.py:519-520`).
- **R4.9** `SPEC_REVIEW → AWAITING_READINESS_DECISION` 전이는 그 시점 게이트 반환값이 `HOLD` 가 아니면 거부한다. 서술이 아니라 `transition` 이 강제한다. 저장소에 같은 형태의 조건부 엣지 선례가 있다 — `CLASSIFIED → AWAITING_PLAN_APPROVAL` 은 모드가 `light` 가 아니면 거부되고(`quality_state.py:380-383`), `SPEC_REVIEW → SPEC_PASSED` 는 통과한 리뷰가 없으면 거부된다. 이 거부와 R4.8 의 stage 가드가 함께 있어야 두 엣지가 게이트 판정에 묶인다.

### R5. 심사 대상과 등록 아티팩트의 digest 대조

- **R5.1** readiness 호출 전에 심사 대상 Spec 의 절대 경로가 `state.artifacts.spec` 과 같은지 확인한다. 다르면 호출하지 않는다.
- **R5.2** readiness 호출 전에 심사 대상 파일의 현재 SHA-256 을 계산해 프롬프트에 싣는다. 오케스트레이터는 이 값을 심사 시점 digest 로 기록한다.
- **R5.3** 호출이 정상 종료한 경우, readiness 결과의 `artifact_digest` 가 R5.2 의 심사 시점 digest 와 다르면 그 결과를 유효 심사로 채택하지 않고 `outcome` 이 `digest_mismatch` 인 실패 기록으로 남긴다. 호출 자체가 실패했으면 R6.9 의 순서에 따라 `invocation_failed` 가 우선한다. 실패 기록도 R4.1 의 한도를 소모한다.
- **R5.4** R5.1 또는 R5.3 위반은 `SPEC_REVIEW` 단계를 유지한 채 사용자에게 보고한다. 근거는 실행 중 다른 디렉터리의 옛 Spec 을 심사할 뻔한 사례다(이슈 #70 코멘트 2, 함정 5).

### R6. 상태 스키마와 재개 호환성

- **R6.1** 상태에 readiness 전용 필드를 추가한다. 기록 단위는 시도 하나이며 다음을 포함한다: `attempt`(실행 누적 번호), `formal_round`(이 시도가 대비하는 Claude 공식 라운드 번호), `verdict`, `score`, `checklist`(항목별 status 와 근거), `findings`, `resolved_finding_ids`(결과의 배열을 그대로 복사한다), `artifact_digest`, `reviewer_model`, `result_path`, `recorded_at`. `resolved_finding_ids` 를 상태에 보존해야 하는 이유는 R6.10 의 유효 Critical/High 집합이 그 값을 읽기 때문이다 — 결과 파일에만 있고 상태에 없으면 게이트가 대체 여부를 판정할 수 없다.
- **R6.2** 상태에 `draft_attempts` 를 추가하고 author 호출 횟수를 artifact 별로 기록한다. 사용자의 readiness 재개 결정은 `readiness_decisions` 배열에 기록한다(R4.8). 이 작업이 상태에 추가하는 필드는 `readiness`, `draft_attempts`, `readiness_decisions` 셋이다.
- **R6.3** `rounds` 는 Claude 공식 리뷰 횟수만 계속 센다. readiness 시도와 author 호출은 `rounds` 의 어떤 값도 바꾸지 않는다.
- **R6.4** schema v1 상태 파일을 읽을 수 있어야 한다. R6.2 가 정의한 세 필드가 없는 상태는 readiness 미실행·author 미호출로 간주한다. **읽는 시점에 세 필드를 상태 파일에 주입하지 않는다.** 각 필드는 그것을 처음 쓰는 명령(`record-readiness`, `record-draft-attempt`, `resume-readiness`)이 생성한다. `readiness` 필드의 부재가 이 변경 이전에 시작한 goal 의 표지이며, R2.8 의 강제 면제가 그 표지를 쓴다(§ Decisions D14). 새 실행은 `init` 이 세 필드를 빈 값으로 만들므로 면제 대상이 아니다.
- **R6.5** 진행 중 goal 을 재개할 때 기존 `rounds`, `reviews`, `open_finding_ids`, `plan_approval`, `revision_checks` 와 승인 digest 를 초기화하지 않는다. `revision_checks` 는 이 작업이 만드는 필드가 아니라 base revision 이 이미 갖는 필드이며(v5.0.0), 이 작업은 그 값을 읽지도 쓰지도 않는다.
- **R6.6** 이 Spec 에서 **등록 digest** 는 `artifacts[artifact]` 가 가리키는 파일의 현재 SHA-256 을 뜻한다. 상태의 `artifact_digests` 필드는 `record_review` 가 기록하는 직전 공식 리뷰 시점의 digest 이며 게이트 판정에 쓰지 않는다. Spec 아티팩트가 교체돼 등록 digest 가 바뀌면, 그 digest 를 가리키지 않는 readiness 기록은 게이트의 **체크리스트·finding 판정** 입력에서 제외한다. **그 제외는 게이트가 산출물을 통과시키는 방향(`READY`·`ARBITRATION`)에만 적용된다** — 그 `formal_round` 의 **가장 최근** `recorded` 기록에 Critical/High 가 있으면, 그것이 등록 digest 를 가리키지 않더라도 R6.10 표의 갈래 ②가 그것을 근거로 `HOLD` 를 유지한다. 제외의 목적은 옛 판정으로 새 산출물을 통과시키지 않는 것이지 이미 확인된 결함을 지우는 것이 아니며, 두 목적을 한 규칙으로 묶으면 개정 한 번으로 `HOLD` 가 우회된다. **판정에 쓰이는 낡은 기록은 언제나 가장 최근 하나뿐이다.** 그보다 오래된 기록은 Critical/High 를 담고 있더라도 이력일 뿐이며 게이트 반환값에 영향을 주지 않는다 — 더 최근의 유효한 심사가 그 결함이 닫혔다고 판정했다면 그 판정이 앞선 것을 대체한다. 이 한정이 없으면 라운드 초기의 High 하나가 그 뒤 readiness 가 몇 번을 통과시키든 그 `formal_round` 를 영구히 `HOLD` 에 묶어 개정 자체가 무의미해진다. **다만 대체가 성립하려면 그 가장 최근 기록이 앞선 Critical/High 를 `resolved_finding_ids` 로 명시적으로 닫아야 한다**(R6.10). 재도출하지 못한 것과 재판정해 닫은 것은 결과 JSON 에서 구별되지 않으므로, 명시가 없으면 잔존으로 본다. 기록 자체는 이력으로 남고, **시도 횟수 계산에서는 제외하지 않는다**. 개정할 때마다 digest 가 바뀌므로 digest 기준으로 시도를 세면 R4.1 의 한도에 영원히 도달하지 못한다.
- **R6.7** `formal_round` 는 입력값이 아니라 상태에서 유도되는 값이며 `rounds[artifact] + 1` 이다. 공식 리뷰가 기록되면 `rounds[artifact]` 가 증가하므로 그 시점 이후의 readiness 시도는 자동으로 다음 값에 귀속된다. `record-readiness` 가 `--formal-round` 를 받는 경우 유도값과 다르면 호출을 거부한다. `readiness-gate` 도 같은 유도 규칙을 쓴다. 오케스트레이터가 임의의 값을 넣어 그 라운드의 시도 카운터를 되돌릴 수 없어야 R4.1 의 한도가 성립한다.
- **R6.8** `SPEC_REVIEW` 를 벗어나는 전이(`SPEC_PASSED`, `AWAITING_READINESS_DECISION`, `NEEDS_REDESIGN`, `BLOCKED`, `CANCELLED`)와 `AWAITING_READINESS_DECISION` 에서 나가는 전이는 readiness 기록과 `readiness_decisions` 를 삭제하지 않는다.
- **R6.9** readiness 기록에 `outcome` 필드를 둔다. 값은 넷이다 — `recorded`(스키마 검증과 digest 대조를 모두 통과한 유효 심사), `schema_invalid`, `digest_mismatch`, `invocation_failed`(`codex exec` 비정상 종료, 결과 파일 미생성, 타임아웃). 실패 기록의 표현은 다음으로 고정한다: `verdict` 와 `score` 는 `null`, `checklist` 와 `findings` 는 빈 배열, 나머지 필드(`attempt`, `formal_round`, `outcome`, `artifact_digest`, `reviewer_model`, `result_path`, `recorded_at`)는 채운다. `outcome` 은 호출자가 고르는 값이 아니라 입력으로부터 결정된다. `record-readiness` 는 `--invocation-status <ok|failed>` 와 `--stderr-path` 를 받으며, `failed` 이면 결과 파일 유무와 무관하게 `invocation_failed` 로 기록하고 `result_path` 에 표준 오류 파일 경로를 넣는다. `ok` 이면 스키마 검증과 digest 대조 순으로 판정해 `schema_invalid`·`digest_mismatch`·`recorded` 중 하나가 된다. 이 순서가 없으면 결과 파일이 남은 비정상 종료를 `schema_invalid` 와 구별할 수 없다. 두 입력에는 거부 계약이 붙는다 — `--invocation-status` 는 `ok` 와 `failed` 두 값만 허용하고 그 밖의 값은 호출을 거부하며, `--invocation-status failed` 인데 `--stderr-path` 가 없거나 그 경로가 존재하지 않으면 호출을 거부한다. `record-readiness` 는 `outcome` 자체를 인자로 받지 않으므로 호출자가 값을 지정할 수 없다. 네 값 모두 R6.10 의 시도 횟수에 포함된다.
- **R6.10** 게이트 판정의 입력은 두 가지로 나뉜다. 이 요구사항에서 어떤 `recorded` 기록이 **앞선 Critical/High 를 닫았다**는 것은 그 기록의 `resolved_finding_ids` 에 해당 finding ID 가 있다는 뜻이며, 그 밖의 어떤 정황도 대체 근거가 되지 않는다. 그에 따라 **유효 Critical/High 집합**을 다음으로 정의하고, 아래 두 경로(등록 digest 기록이 있을 때와 없을 때)가 **같은 집합을 쓴다** — ① 판정에 쓰는 가장 최근 `recorded` 기록의 Critical/High finding, ② 그 `formal_round` 의 그보다 앞선 `recorded` 기록의 Critical/High finding 중 ①의 기록이 `resolved_finding_ids` 로 닫지 않은 것. **이 집합이 비어 있지 않으면 게이트는 `READY` 도 `ARBITRATION` 도 반환하지 않는다.** 두 반환값을 함께 금지하는 이유는 둘 다 산출물을 공식 리뷰로 진행시키는 방향이기 때문이며, 한쪽만 막으면 다른 쪽이 같은 우회가 된다. 이 정의를 요구사항 하나에 두는 이유는, 경로마다 따로 쓰면 한 경로를 고칠 때 다른 경로가 남는 일이 반복되기 때문이다. **시도 횟수**는 현재 시도 구간(R4.1)에 속한 readiness 기록의 개수이며 `outcome` 과 digest 에 무관하다. 곧 현재 `formal_round` 에 귀속된 기록 중 그 라운드의 가장 최근 재개 결정 이후의 것을 세고, 재개 결정이 없으면 그 라운드의 모든 기록을 센다. 재개 시점을 빼면 `resume-readiness` 로 돌아온 직후에도 시도 수가 이미 2 이상이라 게이트가 즉시 다시 `HOLD` 를 반환해 재개가 아무 일도 하지 못한다. **체크리스트·finding 판정**은 그 `formal_round` 에 귀속되고 `outcome` 이 `recorded` 이며 현재 등록 Spec digest 를 가리키는 기록 중 가장 최근 것 하나만 쓴다. 그런 기록이 있으면 그 하나로 판정하되 **유효 Critical/High 집합**을 함께 본다 — 그 기록의 체크리스트가 전부 `pass`/`not_applicable` 이고 그 집합이 비어 있을 때에만 `READY` 다. 집합이 비어 있지 않으면 시도가 2회 미만이면 `RETRY`, 2회 이상이면 `HOLD` 다. 등록 digest 를 가리키는 기록이 없으면 체크리스트를 미충족으로 본 뒤 아래 표가 반환값을 확정하며, 표의 갈래 판정도 같은 집합을 쓴다. 표의 세 갈래는 서로 배타적이고 빠짐이 없다. **표의 적용 범위는 등록 digest 를 가리키는 `recorded` 기록이 없는 경우로 한정된다.** 그런 기록이 있으면 그 하나로 판정하며 반환값은 § Architecture 의 네 값 정의를 따른다 — 체크리스트가 전부 `pass`/`not_applicable` 이고 Critical/High 0 이면 `READY`(R4.7), 미충족이 있고 시도가 2회 미만이면 `RETRY`, 2회 이상이면 Critical/High 0 일 때 `ARBITRATION`·잔존일 때 `HOLD` 다. 곧 게이트의 반환값 집합은 네 값이고, 이 표는 그중 판정 기록이 없을 때의 세 경우를 확정한다.

| 갈래 | 그 `formal_round` 의 `recorded` 기록 | 시도 2회 미만 | 시도 2회 이상 | 판정 AC |
|---|---|---|---|---|
| ① 무기록 | 등록 digest 를 가리키는 기록이 없고, 그 라운드에 `recorded` 기록도 하나도 없다(판정 근거 자체가 없다) | `RETRY` | `ARBITRATION` | AC-83 |
| ② 잔존 Critical/High | 등록 digest 를 가리키는 기록이 없고, 그 라운드의 가장 최근 `recorded` 기록에 Critical/High 가 있다(또는 앞선 Critical/High 가 `resolved_finding_ids` 로 닫히지 않아 잔존으로 본다) | `RETRY` | `HOLD` | AC-116 |
| ③ 확인된 0 | 등록 digest 를 가리키는 기록이 없고, 그 라운드의 가장 최근 `recorded` 기록의 Critical/High 가 0 이며 앞선 Critical/High 가 모두 `resolved_finding_ids` 로 닫혔다 | `RETRY` | `ARBITRATION` | AC-117 |

갈래 ②가 이 규정의 핵심이다. 등록 digest 를 가리키지 않게 된 기록이라도 **그 `formal_round` 의 가장 최근 `recorded` 기록 하나**이면 그 Critical/High 는 사라지지 않는다. **판정에 쓰이는 기록은 언제나 그 하나뿐이며, 그보다 오래된 기록은 Critical/High 를 담고 있더라도 이력일 뿐 반환값에 영향을 주지 않는다**(R6.6, AC-44). **대체에는 명시적 재판정이 필요하다.** 가장 최근 `recorded` 기록이 앞선 `recorded` 기록의 Critical/High finding **각각을** `resolved_finding_ids` 에 실어 명시적으로 닫았다고 표기하지 않으면, 그 Critical/High 는 **잔존으로 본다**. 곧 최신 기록의 `findings` 에 그 ID 가 없다는 사실만으로는 대체가 성립하지 않는다 — fresh reviewer 는 문맥을 상속하지 않으므로(R2.1) 앞선 finding 을 **재도출하지 못한 것**과 **재판정해 닫은 것**이 결과 JSON 에서 구별되지 않기 때문이다. 이 구별이 없으면 author 가 Critical/High 를 고치지 않은 채 다른 곳만 개정해도 다음 시도가 clean 기록이 되어 게이트가 통과시킨다. R2.10 이 직전 시도 findings 를 프롬프트에 싣게 하고 C8 이 그 재판정을 요구하므로, 성실히 실행된 심사는 이 조건을 자연히 충족한다. 그것이 없으면 시도 구간이 소진된 상태에서 산출물을 한 번만 더 고쳐도 High 판정 기록이 등록 digest 를 가리키지 않게 되어 게이트가 `HOLD` 에서 `ARBITRATION` 으로 뒤집히고, 시도 한도가 이미 2 라 새 readiness 로 확인할 수도 없으며, R4.9 가 `HOLD` 아닌 전이를 거부하므로 `AWAITING_READINESS_DECISION` 엣지가 그 시도 구간에서 영영 도달 불가가 된다. 갈래 ①과 ③이 모두 `ARBITRATION` 인 것은 R4.4 의 "Critical/High 가 남아 있다고 확인된 기록이 없을 때 열린다" 와 같은 말이다 — ①은 확인한 적이 없는 상태이고 ③은 0 임을 확인한 상태이며, 둘 다 '남아 있다고 확인된' 상태가 아니다. ①과 ③을 구별해 기록하는 이유는 ①일 때 오케스트레이터가 "readiness 가 유효한 결과를 내지 못했다"를 공식 리뷰 근거에 명시해야 하기 때문이다.

### R7. finding 식별자 네임스페이스

- **R7.1** readiness finding 은 `READY-` 접두 네임스페이스를 쓴다.
- **R7.2** Claude 공식 리뷰의 `SPEC-` 식별자를 readiness finding 에 재사용하지 않는다.
- **R7.3** readiness finding 이 특정 공식 finding 에 대응하면 그 대응 관계를 `description` 에 기록한다.
- **R7.4** readiness finding ID 는 하나의 개정 주기 안에서 안정적이다. 같은 물질적 문제가 남으면 같은 ID 를 유지하고, 구별되는 새 문제에만 새 ID 를 매긴다.

### R8. readiness 결과 계약

- **R8.1** 결과 스키마는 다음 필드를 필수로 요구한다: `artifact`, `attempt`, `formal_round`, `score`, `verdict`, `checklist`, `blockers`, `findings`, `evidence`, `required_next_action`, `artifact_digest`, `resolved_finding_ids`. 마지막 것은 C8 이 재판정해 닫았다고 확인한 직전 리뷰 finding 의 ID 배열이며 빈 배열이 허용된다. 이 필드가 R6.10 의 대체 판정 입력이다.
- **R8.2** `score` 는 `spec-rubric.md` 의 가중치로 실제 계산한 0~100 정수다. 프롬프트는 "blocker 가 있다고 0 을 넣지 마라"를 명시한다.
- **R8.3** `evidence` 는 최소 6건이며 각 항목은 `claim` 과 `location`(파일:행)을 갖는다. 확인하지 못한 것은 사유와 함께 남긴다.
- **R8.4** `artifact_digest` 는 소문자 SHA-256 64자다.
- **R8.5** `verdict` 는 `READY` 또는 `REVISE` 다.
- **R8.6** `checklist` 는 C1~C8 여덟 항목을 모두 포함하고 각 항목은 `id`, `status`, `evidence` 를 갖는다.
- **R8.7** 호출이 정상 종료한 경우, 결과가 스키마 검증에 실패하면 그 결과를 유효 심사로 채택하지 않고 `outcome` 이 `schema_invalid` 인 실패 기록으로 남긴다. 호출 자체가 실패했으면 R6.9 의 순서에 따라 `invocation_failed` 가 우선한다. 실패 기록도 R4.1 의 한도를 소모한다. 오케스트레이터는 검증 오류를 사용자에게 보고한다.

### R9. 문서·계약 회귀 방지

- **R9.1** `SKILL.md` 파일 전체가 500행 미만을 유지한다. 현재 393행이며 `tests/test_content_contracts.py:1244` 가 frontmatter 를 포함한 파일 전체를 대상으로 검사한다(`assertLess(len(text.splitlines()), 500)`). 판정 대상을 본문으로 좁히면 테스트와 어긋난다.
- **R9.2** readiness 절차의 상세는 `references/readiness-policy.md` 로 분리하고, `SKILL.md` 에는 단계 절차와 참조 경로만 싣는다.
- **R9.3** `templates/spec.md` 에 요구사항 추적표 절과 판정 명령 표 절을 추가한다. C3·C4·C5·C7 은 이 두 표가 있어야 판정 가능하다.
- **R9.4** `docs/quality-goal-maintenance.md` 에 readiness 관련 점검 항목(`codex exec` 플래그, readiness 결과 스키마, author·reviewer 라우팅 모델)을 추가하고, 그 문서의 기존 `## 결정적 테스트` 절을 `## 판정 명령 표` 절로 **대체**한다. 새 절은 CMD-1~CMD-7 일곱 행을 싣고 그 바로 아래에 R9.9 의 최소 인터프리터 버전과 두 근거를 함께 싣는다. 병기가 아니라 대체인 이유는, 옛 절이 버전 가드 없는 `python3 -m unittest discover` 를 그대로 싣고 있어 남겨 두면 같은 명령이 두 곳에 서로 다른 형태로 존재하고 어느 쪽이 정본인지 알 수 없게 되기 때문이다. 이 절이 판정 명령 표의 정본이며 R9.9 의 AC-84·AC-105 가 그것을 판정한다(§ Test strategy).
- **R9.5** 기존 310개 테스트가 모두 통과하고, 신규 계약마다 결정적 테스트를 추가한다.
- **R9.6** Plan 단계와 Code 단계의 기존 계약(라운드 한도 Spec 3 / Plan 2 / Code 3, `REQUIRED_CHECKS`, 공식 게이트 `score >= 85`, 승인 digest, dirty-worktree 보호, 결정적 검증)은 변경하지 않는다. 이 불변에는 base revision 이 v5.0.0 에서 이미 갖는 개정 후 자기 회귀 점검 계약(`scripts/revision_check.py`, `record-review --revision-check`, 리뷰 기록 시의 `snapshots/<artifact>-r<N>.md` 저장)이 포함된다. 이 계약에 별도 AC 를 두지 않는 이유는 그것이 남김없이 기존 테스트로 판정되기 때문이다 — `test_revision_check.py` 를 포함한 전체 스위트의 통과를 AC-62 가, 그 테스트 이름의 보존을 AC-77 이 이미 판정한다. 새 AC 를 두면 같은 사실을 두 곳에서 판정하게 된다.
- **R9.7** `SKILL.md` frontmatter 의 `version` 을 유지보수 문서의 SemVer 정책에 따라 올린다. 상태 머신 계약이 확장되므로 MINOR 이상이다.
- **R9.8** author·readiness 라우팅 모델을 `references/model-routing.md` 의 라우트 표에 추가한다. 두 파일의 역할은 이렇게 나눈다 — `model-routing.md` 는 역할별 모델·effort 값과 실행 가능한 호출 템플릿을 담고, `references/readiness-policy.md` 는 그 템플릿을 인용하며 절차 문맥(언제 부르고 무엇을 프롬프트에 싣고 결과를 어떻게 기록하는지)을 담는다. R9.4 의 유지보수 점검 항목에 두 파일의 동기화를 넣는다. standard 는 author `gpt-5.6-terra` high, strict 는 author `gpt-5.6-sol` high 이며, readiness reviewer 는 두 모드 모두 fresh `gpt-5.6-sol` high 다.
- **R9.9** 판정 명령은 실행 환경 전제를 명시하고 명령 자체가 그 전제를 확인한다. 테스트 스위트는 **Python 3.12 이상**을 요구한다. 두 가지 이유가 겹친다. 첫째, `tests/test_quality_state.py` 의 `ResumeSelectionTests` 가 `unittest.TestCase.enterContext` 를 쓰는데 그 API 는 3.11 에서 추가됐다 — 실측으로 `/usr/bin/python3` 3.9.6 은 310건 중 23건이 오류로 종료 코드 1 을 내고 `/opt/homebrew/bin/python3` 3.14.7 은 `OK` 다. 둘째, `unittest` 가 필터에 아무것도 매칭되지 않을 때 종료 코드 5(`NO TESTS RAN`)를 내는 동작은 3.12 에서 도입됐다 — 실측으로 3.12.14 와 3.14.7 은 `-k` 가 0건을 매칭하면 종료 코드 5 를, 3.9.6 은 0 을 반환한다. 3.12 미만에서는 CMD-2 가 존재하지 않는 테스트 이름에도 성공을 반환해 약 70개 AC 가 공허하게 통과한다. 버전 전제 없이 `python3` 를 부르면 판정이 `PATH` 에 따라 갈린다.
- **R9.10** 판정 스크립트를 저장소 파일로 둔다. 셋이다 — CMD-4 의 `dot_claude/skills/quality-goal/tests/assert_preserved_sections.py`, CMD-6 의 `.../tests/assert_tests_preserved.py`, 그리고 CMD-1·CMD-2·CMD-7 이 공유하는 버전 가드 `.../tests/assert_python_version.py`. 셋 다 `unittest` 수집 대상이 아니어야 한다(파일명이 `test_` 로 시작하지 않는다). 버전 가드를 파일 하나로 모으는 이유는 R9.9 의 전제 확인이 세 명령에서 같은 코드로 이뤄져야 CMD-7 이 CMD-1·CMD-2 의 실제 가드를 판정하기 때문이다. 가드가 명령마다 인라인으로 복제되면 CMD-1 에서 가드를 빼도 CMD-7 이 통과한다.

## Acceptance criteria

판정 수단 표기는 두 가지다. `[실행]` 은 판정 명령 표(§ Test strategy)에 등재된 명령으로 판정하며, 괄호 안은 그 명령의 식별자와 테스트 이름이다. `[문서]` 는 지정한 파일의 지정한 절에 해당 문언이 존재하는지로 판정한다.

- **AC-1** `SKILL.md` 의 Spec 단계 절차가 Spec 초안과 개정의 실행 주체를 Codex author 로 지정하고, 오케스트레이터가 Spec 본문을 직접 쓰지 않는다고 명시한다. [실행] (CMD-2 `test_spec_authoring_is_delegated_to_codex_contract`)
- **AC-2** `references/readiness-policy.md` 가 author 호출 전 요구사항 발굴 수행과 그 결과의 프롬프트 반영을 요구한다. [실행] (CMD-2 `test_author_prompt_required_elements_contract`)
- **AC-3** `references/readiness-policy.md` 의 author 호출 템플릿이 `-C`, `--sandbox workspace-write`, `--ephemeral`, `--model`, `model_reasoning_effort`, `--output-schema`, `--output-last-message`, `--json`, 프롬프트 표준 입력 아홉 요소를 모두 포함한다. [실행] (CMD-2 `test_author_invocation_template_contract`)
- **AC-4** R1.4 가 열거한 여덟 옵션과 `--full-auto` 가 스킬 파일에 나타나는 모든 위치가 금지 문언 안이다. 판정 규칙은 기계적이다 — 각 플래그 문자열을 포함한 줄이 같은 문단 안에서 금지·사용하지 않음을 뜻하는 표현과 함께 나타나야 하며, 호출 템플릿 코드 블록 안에는 한 번도 나타나지 않아야 한다. `SKILL.md` 의 기존 금지 문언은 유지된다. [실행] (CMD-2 `test_forbidden_codex_flags_contract`)
- **AC-5** 스킬의 어떤 문서도 `codex exec` 호출에 `-a` 또는 `--ask-for-approval` 을 지시하지 않고, `readiness-policy.md` 가 그 플래그의 부재를 명시한다. [실행] (CMD-2 `test_codex_exec_has_no_approval_flag_contract`)
- **AC-6** author 프롬프트 필수 요소 열두 가지(대상 Spec 절대 경로, 템플릿 절대 경로, spec-rubric 절대 경로, brainstorming-policy 절대 경로, revision-check-policy 절대 경로, findings 전문 경로, 번호 보존 규칙, 식별자 문법 준수 지시, 개정 노트 경로, 라운드 2 이상 노트 형식, git 쓰기 금지, 조합 검토 지시)가 `references/readiness-policy.md` 에 목록으로 존재하며, R1.6 이 절대 경로를 요구한 다섯 항목이 그 문서에서도 **절대 경로**로 한정돼 있다. [실행] (CMD-2 `test_author_prompt_required_elements_contract`)
- **AC-7** `references/readiness-policy.md` 가 author 의 수정 허용 파일을 대상 Spec 과 개정 노트 둘로 한정하고, 호출 후 `git status --porcelain` 확인을 요구하며, 그 비교에서 `initial_dirty_paths` 와 `.claude/quality-state/<task-id>/` 하위를 제외하고 결과의 `changed_files` 와 대조한다고 명시한다. [실행] (CMD-2 `test_author_write_scope_contract`)
- **AC-8** author 프롬프트 계약이 조합 검토 지시를 필수로 포함하고 교차 회귀 전례를 근거로 인용한다. [실행] (CMD-2 `test_author_cross_regression_review_contract`)
- **AC-9** author 호출 1회가 `draft_attempts.spec` 을 1 증가시키고 `rounds.spec` 을 바꾸지 않는다. [실행] (CMD-2 `test_record_draft_attempt_increments_only_draft_attempts`)
- **AC-10** author 호출 실패(비정상 종료·결과 파일 없음·스키마 검증 실패) 시 단계를 유지하고 모델을 대체하지 않는다는 지시가 `references/readiness-policy.md` 에 존재하며 `BLOCKED_MODEL_UNAVAILABLE` 경로를 참조한다. [실행] (CMD-2 `test_author_failure_recovery_contract`)
- **AC-11** author 호출 전후 Spec digest 가 같으면 개정 실패로 처리한다는 지시가 존재한다. [실행] (CMD-2 `test_author_no_change_is_failure_contract`)
- **AC-12** `references/readiness-policy.md` 가 readiness reviewer 를 author 와 별개 프로세스로 실행하고 author 문맥을 상속하지 않는다고 명시한다. [실행] (CMD-2 `test_readiness_reviewer_is_fresh_contract`)
- **AC-13** readiness 호출 템플릿이 `--sandbox read-only` 를 쓰고 금지 플래그를 포함하지 않는다. [실행] (CMD-2 `test_readiness_invocation_template_contract`)
- **AC-14** `references/readiness-policy.md` 의 author·readiness 호출 템플릿이 모두 표준 입력을 프롬프트 파일 또는 `/dev/null` 에 연결하고, 둘 중 어느 형태도 아닌 호출을 금지한다고 명시하며, 그 이유(비대화형 무한 대기)를 기록한다. [실행] (CMD-2 `test_readiness_stdin_guard_contract`)
- **AC-15** `schemas/readiness-result.schema.json` 의 모든 property 정의가 `type` 키를 가지며 `const` 키를 한 번도 쓰지 않는다. [실행] (CMD-2 `test_readiness_schema_uses_type_not_const`)
- **AC-16** readiness 프롬프트 계약이 "개정 노트는 근거가 아니라 검증 대상" 규칙을 포함한다. [실행] (CMD-2 `test_readiness_prompt_treats_notes_as_claims`)
- **AC-17** readiness 프롬프트 계약이 자신의 판정을 비용 제어 게이트로 규정하고 Claude 공식 판정을 대체하지 않는다고 명시하며, 설계 취향 감점을 금지한다. [실행] (CMD-2 `test_readiness_is_cost_gate_not_authority_contract`)
- **AC-18** readiness 프롬프트 계약이 읽기 전용과 git 쓰기 금지를 명시한다. [실행] (CMD-2 `test_readiness_read_only_contract`)
- **AC-19** `SKILL.md` 와 `references/readiness-policy.md` 가 readiness 미실행 상태에서 Claude 공식 Spec 리뷰를 시작하지 않는다고 명시한다. [실행] (CMD-2 `test_formal_review_requires_readiness_contract`)
- **AC-20** `references/readiness-policy.md` 의 체크리스트 절이 C1~C8 여덟 항목을 각각 정의한다. [실행] (CMD-2 `test_readiness_checklist_defines_eight_items`)
- **AC-21** 체크리스트 여덟 항목이 모두 `pass` 또는 `not_applicable` 이고 Critical/High 가 0 인 결과만 READY 로 판정된다. `not_applicable` 은 충족으로 센다. [실행] (CMD-2 `test_readiness_gate_requires_all_checks_and_no_high`)
- **AC-22** 체크리스트 항목 중 하나라도 `fail` 이면 게이트 판정이 REVISE 다. [실행] (CMD-2 `test_readiness_gate_single_failed_check_blocks`)
- **AC-23** 게이트 판정 함수가 `score` 값을 읽지 않는다. `score` 를 0 과 100 으로 바꿔도 동일 입력의 판정 결과가 같다. [실행] (CMD-2 `test_readiness_gate_ignores_score`)
- **AC-24** `references/readiness-policy.md` 가 `score` 를 기록 전용 참고값으로 규정하고 게이트·전이에 쓰지 않는다고 명시한다. [실행] (CMD-2 `test_readiness_score_is_advisory_contract`)
- **AC-25** `checklist` 각 항목이 `status` 와 `evidence` 를 요구하며, `status` 는 `pass`·`fail`·`not_applicable` 셋만 허용한다. [실행] (CMD-2 `test_readiness_schema_checklist_shape`)
- **AC-26** Critical 또는 High finding 이 하나라도 있으면 체크리스트가 전부 `pass` 여도 READY 가 아니다. [실행] (CMD-2 `test_readiness_gate_high_finding_blocks_despite_all_checks_pass`)
- **AC-27** 체크리스트 항목 정의에 설계 정합성·아키텍처 타당성·시간축 전개 판정이 포함되지 않는다는 것이 문서에 명시된다. [문서] `references/readiness-policy.md` § 체크리스트 게이트
- **AC-28** 한 시도 구간(R4.1)의 readiness 시도가 2회를 초과하면 오케스트레이터가 추가 시도를 하지 않고 R4.4 또는 R4.5 경로로 간다. [실행] (CMD-2 `test_readiness_attempts_per_round_limit`)
- **AC-29** Claude 공식 리뷰가 기록되면 다음 라운드의 readiness 시도 카운터가 0 에서 시작한다. [실행] (CMD-2 `test_readiness_attempt_counter_resets_per_formal_round`)
- **AC-30** `schemas/readiness-result.schema.json` 의 `attempt` 에 `maximum` 제약이 없다. [실행] (CMD-2 `test_readiness_schema_attempt_has_no_maximum`)
- **AC-31** 시도 구간 2회 소진 상태에서 arbitration 경로가 열리는 두 경우(가장 최근 `recorded` 기록의 Critical/High 가 0, 그리고 그 `formal_round` 에 `recorded` 기록이 아예 없음)가 문서에 열거되고, 미충족 항목이 공식 리뷰 근거로 전달되며, **이미 확인된 Critical/High 를 기록 무효화로 지우고 arbitration 으로 내려가는 것은 금지된다**는 것이 함께 적혀 있다. [실행] (CMD-2 `test_readiness_arbitration_path_contract`)
- **AC-32** 시도 구간 2회 소진 + 그 `formal_round` 의 가장 최근 `recorded` 기록에 Critical/High 잔존이면 `AWAITING_READINESS_DECISION` 으로 전이하고 `status_reason` 이 `READINESS_HELD:` 로 시작하며, 그 상태가 `TERMINAL_STATES` 에 속하지 않는다. [실행] (CMD-2 `test_readiness_exhausted_with_high_holds_for_user`)
- **AC-33** readiness 시도 기록이 `rounds.spec` 을 증가시키지 않는다. [실행] (CMD-2 `test_record_readiness_does_not_touch_rounds`)
- **AC-34** READY 판정 직후 같은 라운드에서 추가 readiness 시도를 하지 않는다는 지시가 존재한다. [문서] `references/readiness-policy.md` § 반복 한도와 탈출
- **AC-35** 심사 대상 경로가 `state.artifacts.spec` 과 다르면 readiness 기록이 거부된다. [실행] (CMD-2 `test_record_readiness_rejects_path_mismatch`)
- **AC-36** 심사 대상 파일의 현재 SHA-256 을 프롬프트에 싣는다는 지시가 존재한다. [문서] `references/readiness-policy.md` § digest 대조
- **AC-37** `--invocation-status ok` 로 호출했을 때 결과의 `artifact_digest` 가 심사 시점 digest 와 다르면 유효 심사로 채택되지 않고 `digest_mismatch` 실패 기록이 남으며, 게이트의 시도 횟수가 1 증가한다. [실행] (CMD-2 `test_record_readiness_rejects_digest_mismatch_and_counts_attempt`)
- **AC-38** digest 대조 실패가 단계를 바꾸지 않고 사용자 보고로 이어진다는 지시가 존재한다. [문서] `references/readiness-policy.md` § digest 대조
- **AC-39** `outcome` 이 `recorded` 인 readiness 기록 하나가 `attempt`, `formal_round`, `verdict`, `score`, `checklist`, `findings`, `resolved_finding_ids`, `artifact_digest`, `reviewer_model`, `result_path`, `recorded_at` 열한 개 필드를 모두 갖고, `resolved_finding_ids` 의 값이 결과 JSON 의 같은 필드와 배열 단위로 같다. [실행] (CMD-2 `test_readiness_record_shape`)
- **AC-40** 새 상태에 `draft_attempts` 가 존재하고 artifact 별 초기값이 0 이다. [실행] (CMD-2 `test_new_state_has_draft_attempts`)
- **AC-41** readiness 기록과 author 호출 기록 어느 것도 `rounds` 의 값을 바꾸지 않는다. [실행] (CMD-2 `test_readiness_and_draft_attempts_leave_rounds_unchanged`)
- **AC-42** R6.2 의 세 필드가 없는 schema v1 상태 파일을 읽을 수 있고, 읽기만으로는 어느 필드도 상태 파일에 생기지 않으며, readiness 미실행·author 미호출로 취급된다. [실행] (CMD-2 `test_v1_state_without_readiness_fields_is_not_mutated_on_load`)
- **AC-43** 진행 중 goal 을 재개해도 기존 `rounds`, `reviews`, `open_finding_ids`, `plan_approval`, `revision_checks` 가 그대로 보존된다. [실행] (CMD-2 `test_resume_preserves_rounds_reviews_and_approval`)
- **AC-44** 등록 digest(`artifacts.spec` 이 가리키는 파일의 현재 SHA-256, R6.6)와 다른 digest 를 가리키는 readiness 기록은 게이트가 `READY`·`ARBITRATION` 을 내는 판정 입력에서 제외되고 이력으로 남되, 그 `formal_round` 의 **가장 최근** `recorded` 기록에 Critical/High 가 있으면 게이트는 `ARBITRATION` 으로 내려가지 않는다. 그보다 오래된 기록의 Critical/High 는 반환값에 영향을 주지 않는다. [실행] (CMD-2 `test_stale_readiness_record_excluded_from_gate`)
- **AC-45** 공식 리뷰 기록 이후 추가되는 readiness 기록의 `formal_round` 가 `rounds[artifact] + 1` 과 같다. [실행] (CMD-2 `test_readiness_formal_round_advances_after_review`)
- **AC-46** `SPEC_PASSED`·`AWAITING_READINESS_DECISION`·`NEEDS_REDESIGN`·`BLOCKED`·`CANCELLED` 로 전이해도 readiness 기록과 `readiness_decisions` 가 상태에 남는다. [실행] (CMD-2 `test_readiness_records_survive_stage_exit`)
- **AC-47** readiness finding ID 가 `READY-` 로 시작하지 않으면 결과 검증이 실패한다. [실행] (CMD-2 `test_readiness_finding_id_namespace`)
- **AC-48** `SPEC-` 로 시작하는 finding ID 가 readiness 결과에 있으면 검증이 실패한다. [실행] (CMD-2 `test_readiness_rejects_spec_namespace_ids`)
- **AC-49** readiness 프롬프트 계약이 공식 finding 과의 대응 관계를 `description` 에 기록하도록 요구한다. [문서] `references/readiness-policy.md` § finding 식별자
- **AC-50** readiness 프롬프트 계약이 하나의 개정 주기 안에서 같은 물질적 문제에 같은 ID 를 유지하도록 요구한다. [문서] `references/readiness-policy.md` § finding 식별자
- **AC-51** `schemas/readiness-result.schema.json` 의 `required` 가 R8.1 의 열두 필드(`artifact`, `attempt`, `formal_round`, `score`, `verdict`, `checklist`, `blockers`, `findings`, `evidence`, `required_next_action`, `artifact_digest`, `resolved_finding_ids`)를 정확히 포함하고 그 밖의 필드를 required 로 두지 않는다. [실행] (CMD-2 `test_readiness_schema_required_fields`)
- **AC-52** readiness 프롬프트 계약이 `score` 를 rubric 가중치로 실제 계산하도록 지시하고 "blocker 가 있다고 0 을 넣지 마라"를 포함한다. [실행] (CMD-2 `test_readiness_score_computation_instruction`)
- **AC-53** `evidence` 최소 6건 요구가 스키마의 `minItems` 로 강제되고, 각 항목이 `claim` 과 `location` 을 갖는다. [실행] (CMD-2 `test_readiness_schema_evidence_min_items`)
- **AC-54** `artifact_digest` 가 소문자 SHA-256 64자 패턴으로 제약된다. [실행] (CMD-2 `test_readiness_schema_digest_pattern`)
- **AC-55** `verdict` 가 `READY` 와 `REVISE` 두 값만 허용한다. [실행] (CMD-2 `test_readiness_schema_verdict_enum`)
- **AC-56** `checklist` 가 C1~C8 여덟 항목을 모두 포함하지 않으면 검증이 실패한다. [실행] (CMD-2 `test_readiness_schema_requires_all_eight_checks`)
- **AC-57** `--invocation-status ok` 로 호출했을 때 스키마 검증에 실패한 결과가 유효 심사로 채택되지 않고 `schema_invalid` 실패 기록이 남으며, 게이트의 시도 횟수가 1 증가한다. [실행] (CMD-2 `test_invalid_readiness_result_counts_attempt_and_is_not_recorded`)
- **AC-58** `SKILL.md` 파일 전체가 500행 미만이다. [실행] (CMD-3)
- **AC-59** `references/readiness-policy.md` 가 존재하고 `SKILL.md` 의 참조 경로 목록에 등재된다. [실행] (CMD-2 `test_readiness_policy_is_referenced_from_skill`)
- **AC-60** `templates/spec.md` 에 요구사항 추적표 절과 판정 명령 표 절이 존재한다. [실행] (CMD-2 `test_spec_template_has_traceability_and_command_table`)
- **AC-61** `docs/quality-goal-maintenance.md` 에 readiness 점검 항목(`codex exec` 플래그, readiness 결과 스키마, author·reviewer 라우팅 모델)이 존재한다. [실행] (CMD-2 `test_maintenance_doc_covers_readiness`)
- **AC-62** Python 3.12 이상에서 전체 테스트가 통과한다. [실행] (CMD-1)
- **AC-63** `ROUND_LIMITS` 가 `{"spec": 3, "plan": 2, "code": 3}` 그대로이고 `REQUIRED_CHECKS` 가 변경되지 않는다. [실행] (CMD-2 `test_round_limits_and_required_checks_unchanged`)
- **AC-64** `SKILL.md` frontmatter 의 `version` 이 5.0.0 보다 크고 MINOR 이상 증가한다. [실행] (CMD-2 `test_skill_version_bumped_for_contract_extension`)
- **AC-65** `references/model-routing.md` 의 라우트 표에 Spec author(standard `gpt-5.6-terra` high, strict `gpt-5.6-sol` high)와 readiness reviewer(fresh `gpt-5.6-sol` high) 행이 존재한다. [실행] (CMD-2 `test_model_routing_includes_author_and_readiness_rows`)
- **AC-66** Plan 단계와 Code 단계의 절차 문언이 base revision `6d60011cbdaead7946b191d3f12029eef5c141c8` 대비 의미상 변경되지 않는다. [실행] (CMD-4)
- **AC-67** 공식 Claude 게이트의 점수 임계 85 가 `references/spec-rubric.md`·`plan-rubric.md`·`code-rubric.md` 에서 변경되지 않는다. [실행] (CMD-2 `test_formal_pass_gate_threshold_unchanged`)
- **AC-68** `schemas/readiness-result.schema.json` 이 JSON 으로 파싱되고 최상위 `type` 이 `object` 이며 `additionalProperties` 가 `false` 다. [실행] (CMD-5)
- **AC-69** `references/readiness-policy.md` 가 요구사항 발굴에서 남은 물질적 모호성을 author 호출 **전에** 사용자 질의로 해소하도록 요구한다. [실행] (CMD-2 `test_author_prompt_required_elements_contract`)
- **AC-70** `references/readiness-policy.md` 의 금지 플래그 문언이 네 개를 열거하는 데 그치지 않고 `--sandbox` 의 승인·권한 우회 값을 포함한 모든 sandbox 우회 옵션을 포괄적으로 금지하며, 같은 변경이 `SKILL.md` 의 Safety rules 절을 건드리지 않는다. [실행] (CMD-2 `test_forbidden_codex_flags_contract`, CMD-4)
- **AC-71** readiness 프롬프트 계약이 개정 노트의 주장을 Spec 본문에서 파일:행으로 대조하도록 요구한다. [실행] (CMD-2 `test_readiness_prompt_treats_notes_as_claims`)
- **AC-72** 현재 `formal_round` 의 게이트 판정이 `READY` 도 `ARBITRATION` 도 아닌 상태에서 spec 리뷰를 `record-review` 로 기록하면 거부된다. [실행] (CMD-2 `test_record_review_requires_readiness_gate`)
- **AC-73** readiness 필드가 아예 없는 schema v1 상태에서는 AC-72 의 강제가 적용되지 않고 spec 리뷰 기록이 통과한다. [실행] (CMD-2 `test_record_review_gate_exempts_v1_state`)
- **AC-74** readiness 기록 하나를 추가할 때마다 `attempt` 가 실행 전체에서 1씩 증가하며 `formal_round` 가 바뀌어도 초기화되지 않는다. [실행] (CMD-2 `test_readiness_attempt_is_globally_monotonic`)
- **AC-75** `references/readiness-policy.md` 가 경로 불일치 시 readiness 호출 자체를 하지 않는다고 명시하고, 그 확인을 호출 전 절차로 배치한다. [실행] (CMD-2 `test_readiness_path_check_precedes_invocation`)
- **AC-76** `draft_attempts.spec` 증가가 `draft_attempts.plan` 을 바꾸지 않는다. [실행] (CMD-2 `test_record_draft_attempt_is_per_artifact`)
- **AC-77** base revision 의 테스트 이름 집합이 현재 테스트 이름 집합의 부분집합이다. 기존 테스트가 삭제되거나 이름이 바뀌면 실패한다. [실행] (CMD-6)
- **AC-78** `SKILL.md` 의 승인 게이트·dirty-path 보존·독립 검증 문언이 base revision 대비 변경되지 않는다. [실행] (CMD-4)
- **AC-79** `light` 모드 상태에서 `record-readiness`, `readiness-gate`, `record-draft-attempt`, `resume-readiness` 네 명령이 모두 오류로 거부된다. [실행] (CMD-2 `test_readiness_commands_rejected_in_light_mode`)
- **AC-80** readiness 기록의 `outcome` 이 `recorded`·`schema_invalid`·`digest_mismatch`·`invocation_failed` 네 값만 허용한다. [실행] (CMD-2 `test_readiness_record_outcome_enum`)
- **AC-81** 스키마 검증 실패와 digest 불일치가 각각 해당 `outcome` 의 실패 기록을 남기며, 그 기록의 `verdict` 와 `score` 가 `null` 이고 `checklist` 와 `findings` 가 빈 배열이다. [실행] (CMD-2 `test_failed_readiness_attempt_is_recorded_as_empty_outcome`)
- **AC-82** 게이트의 시도 횟수가 `outcome` 과 digest 에 무관하다 — 같은 `formal_round` 안에서 Spec digest 가 바뀐 뒤 두 번째 readiness 를 기록하면 2 로 계산되고, `outcome` 이 `recorded` 가 아닌 실패 기록도 함께 세며, 그 라운드에 재개 결정이 있으면 그 결정 이후의 기록만 센다. [실행] (CMD-2 `test_gate_attempt_count_ignores_digest`)
- **AC-83** R6.10 표의 갈래 ① — 등록 digest(`artifacts.spec` 이 가리키는 파일의 현재 SHA-256, R6.6)를 가리키는 `recorded` 기록이 없고 그 `formal_round` 에 귀속된 `recorded` 기록이 하나도 없을 때, 시도가 2 미만이면 게이트가 `RETRY` 를, 2 이상이면 `ARBITRATION` 을 반환한다. [실행] (CMD-2 `test_gate_without_current_digest_record`)
- **AC-84** `docs/quality-goal-maintenance.md` 의 판정 명령 표가 테스트 스위트의 최소 Python 버전을 3.12 로 명시하고 그 두 근거(`enterContext`, `NO TESTS RAN` 종료 코드 5)를 함께 싣는다. [문서] `docs/quality-goal-maintenance.md` § 판정 명령 표
- **AC-85** `tests/assert_python_version.py` 가 3.12 이상에서 성공하고 3.12 미만에서 비정상 종료한다. [실행] (CMD-7)
- **AC-86** R9.10 의 세 스크립트가 존재하고, 세 파일명이 모두 `test_` 로 시작하지 않아 `unittest discover -p 'test_*.py'` 의 수집 대상에서 빠진다. [실행] (CMD-2 `test_judgement_scripts_exist_and_are_not_collected`)
- **AC-87** `references/readiness-policy.md` 의 arbitration 절차가 공식 리뷰에 전달할 것으로 미충족 체크리스트 항목과 잔여 finding 전문의 파일 경로를 함께 지정한다. [실행] (CMD-2 `test_readiness_arbitration_path_contract`)
- **AC-88** 심사 시점 digest 가 readiness 기록의 `artifact_digest` 로 상태에 남고, 그 값이 호출 시점에 계산한 Spec 파일 digest 와 같다. [실행] (CMD-2 `test_record_readiness_persists_review_time_digest`)
- **AC-89** readiness 필드가 없는 상태에 첫 `record-readiness` 를 적용하면 그때 필드가 생성되고, 새 `init` 상태에는 `readiness`·`draft_attempts`·`readiness_decisions` 세 필드가 빈 값으로 존재한다. [실행] (CMD-2 `test_readiness_fields_created_on_first_record`)
- **AC-90** 재개 시 `plan_approval` 의 경로와 digest 가 재개 전과 바이트 단위로 같다. [실행] (CMD-2 `test_resume_preserves_rounds_reviews_and_approval`)
- **AC-91** 같은 `formal_round` 에 등록 digest(`artifacts.spec` 이 가리키는 파일의 현재 SHA-256, R6.6)를 가리키는 `recorded` 기록이 둘 이상이면 게이트가 `recorded_at` 이 가장 늦은 하나만 판정에 쓴다. [실행] (CMD-2 `test_gate_uses_latest_recorded_result`)
- **AC-92** `references/readiness-policy.md` 의 금지 목록이 R1.4 의 여덟 이름(`--yolo` 포함)을 모두 포함하고, 기준 CLI 버전 문자열과 `--yolo` 가 `--help` 에 없는 숨은 별칭이라는 사실을 함께 기록한다. [실행] (CMD-2 `test_forbidden_codex_flags_enumerate_current_cli`)
- **AC-93** `draft_attempts` 가 없는 schema v1 상태에 첫 `record-draft-attempt` 를 적용하면 그때 `draft_attempts` 가 생성되고 해당 artifact 값이 1 이 된다. [실행] (CMD-2 `test_draft_attempts_created_on_first_record`)
- **AC-94** 게이트가 `HOLD` 를 반환한 뒤 전이한 `AWAITING_READINESS_DECISION` 에서 `record-review` 와 `record-review-unverified` 가 모두 거부되고, 상태가 종료로 바뀌지 않는다. [실행] (CMD-2 `test_readiness_hold_blocks_review_and_is_not_terminal`)
- **AC-95** `resume-readiness` 가 사용자 결정을 `readiness_decisions` 에 기록하고 `AWAITING_READINESS_DECISION` 을 `SPEC_REVIEW` 로 되돌리며, 직후 게이트의 시도 횟수가 0 이 되어 반환값이 `RETRY` 다. [실행] (CMD-2 `test_resume_readiness_records_decision_and_returns_to_spec_review`)
- **AC-96** `AWAITING_READINESS_DECISION` 에서 `resume-readiness` 없이 `SPEC_REVIEW` 로 돌아가는 전이가 거부된다. [실행] (CMD-2 `test_readiness_hold_requires_recorded_decision`)
- **AC-97** `record-readiness` 에 `rounds[artifact] + 1` 과 다른 `--formal-round` 를 주면 호출이 거부된다. [실행] (CMD-2 `test_record_readiness_rejects_mismatched_formal_round`)
- **AC-98** `--formal-round` 를 임의로 올려 같은 공식 라운드의 시도 카운터를 0 으로 되돌릴 수 없다. [실행] (CMD-2 `test_formal_round_cannot_reset_attempt_counter`)
- **AC-99** 게이트가 `artifact_digests[artifact]` 를 판정 입력으로 쓰지 않는다. 그 값이 `None` 이거나 현재 파일 digest 와 달라도 게이트 결과가 바뀌지 않는다. [실행] (CMD-2 `test_gate_ignores_artifact_digests_field`)
- **AC-100** `--invocation-status failed` 로 호출하면 결과 파일이 스키마를 통과하고 현재 등록 digest 까지 가리키는 정상 결과여도 `invocation_failed` 로 기록되고, `verdict` 와 `score` 가 `null`, `checklist` 와 `findings` 가 빈 배열이며, `result_path` 가 `--stderr-path` 값이고, 게이트의 시도 횟수가 1 증가한다. [실행] (CMD-2 `test_invocation_failure_is_recorded_and_counts_attempt`)
- **AC-101** `references/readiness-policy.md` 가 C2 판정에 쓰려고 인용한 strict marker 주석 문자열 두 개가 `templates/spec.md` 에 그대로 존재한다. [실행] (CMD-2 `test_strict_marker_quotation_matches_template`)
- **AC-102** CMD-4 의 보존 대상 절 목록이 `## Review invocation contract` 와 `## Codex invocation contract` 를 포함하고, 두 절이 base revision 대비 변경되지 않는다. [실행] (CMD-4)
- **AC-103** readiness 게이트가 `READY` 도 `ARBITRATION` 도 아닌 상태에서 `record-review-unverified` 로 spec 리뷰를 기록하면 거부되고, `record-review-error` 는 거부되지 않는다. [실행] (CMD-2 `test_readiness_gate_applies_to_unverified_path_only`)
- **AC-104** `references/model-routing.md` 와 `references/readiness-policy.md` 의 역할 분담이 문서에 명시되고, `docs/quality-goal-maintenance.md` 의 점검 항목에 두 파일의 동기화가 등재된다. [실행] (CMD-2 `test_routing_and_policy_split_is_documented`)
- **AC-105** `docs/quality-goal-maintenance.md` § 판정 명령 표의 CMD-1 과 CMD-2 정의가 `tests/assert_python_version.py` 호출을 포함하고, 버전 비교식을 명령 안에 인라인으로 복제하지 않는다. [실행] (CMD-2 `test_version_guard_is_shared_not_inlined`)
- **AC-106** stage 가 `AWAITING_READINESS_DECISION` 이 아닌 상태에서 `resume-readiness` 를 호출하면 거부되고 `readiness_decisions` 에 아무것도 추가되지 않는다. [실행] (CMD-2 `test_resume_readiness_rejects_wrong_stage`)
- **AC-107** 게이트 반환값이 `HOLD` 가 아닌 상태에서 `SPEC_REVIEW → AWAITING_READINESS_DECISION` 전이를 시도하면 거부된다. [실행] (CMD-2 `test_hold_transition_requires_gate_hold`)
- **AC-108** 시도 구간의 시도가 2회인 `SPEC_REVIEW` 상태에서 `resume-readiness` 를 호출해도 거부되므로 게이트의 시도 횟수가 2 로 유지되고 반환값이 `RETRY` 로 돌아가지 않는다. [실행] (CMD-2 `test_resume_cannot_reset_attempt_window_outside_hold`)
- **AC-109** `--invocation-status ok` 이고 결과가 스키마 위반과 digest 불일치를 동시에 만족하면 `schema_invalid` 로 기록된다. [실행] (CMD-2 `test_schema_invalid_precedes_digest_mismatch`)
- **AC-110** `references/readiness-policy.md` 가 readiness 호출의 비정상 종료·결과 파일 미생성·타임아웃 세 경우를 모두 `--invocation-status failed` 로 넘기도록 지시한다. [실행] (CMD-2 `test_invocation_failure_causes_are_enumerated`)
- **AC-111** `AWAITING_READINESS_DECISION` 전이가 `status_reason` 에 `READINESS_HELD:` 로 시작하는 값을 남기고, `resume-readiness` 가 `SPEC_REVIEW` 로 되돌릴 때 그 값을 `null` 로 지운다. [실행] (CMD-2 `test_hold_status_reason_is_set_and_cleared`)
- **AC-112** `--invocation-status` 에 `ok`·`failed` 밖의 값을 주면 호출이 거부되고, `record-readiness` 가 `outcome` 인자를 받지 않는다. [실행] (CMD-2 `test_invocation_status_enum_is_enforced`)
- **AC-113** `--invocation-status failed` 인데 `--stderr-path` 가 없거나 그 경로가 존재하지 않으면 호출이 거부된다. [실행] (CMD-2 `test_failed_status_requires_existing_stderr_path`)
- **AC-114** `references/readiness-policy.md` 가 라운드 2 이상의 개정 노트 형식을 `references/revision-check-policy.md` 에서 그대로 인용해 싣는다 — 절 헤딩 `## 라운드 <n> 개정` 과 다섯 열 표 머리 `| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |`. 같은 `formal_round` 에 절이 정확히 하나이고 readiness 개정이 반복되면 새 절을 만들지 않고 그 절에 행을 누적·갱신한다는 규칙, 그리고 그 절이 다루는 범위가 직전 라운드 스냅숏(`snapshots/<artifact>-r<N-1>.md`) 이후의 모든 변경이며 readiness 가 유발한 변경도 거기 포함된다는 규정도 함께 싣는다. [실행] (CMD-2 `test_author_revision_note_format_contract`)
- **AC-115** `docs/quality-goal-maintenance.md` 에 `## 판정 명령 표` 절이 존재하고 `## 결정적 테스트` 절이 존재하지 않으며, 새 절이 CMD-1~CMD-7 일곱 행을 모두 싣고, 최소 인터프리터 버전 문언과 두 근거가 그 표 **바로 아래**(표와 그 문언 사이에 다른 헤딩이 없음)에 있으며, 그 절이 판정 명령 표의 정본이라는 것이 문서에 명시된다. [실행] (CMD-2 `test_maintenance_doc_replaces_test_section_with_command_table`)
- **AC-116** R6.10 표의 갈래 ② — 등록 digest 를 가리키는 `recorded` 기록이 없더라도 그 `formal_round` 의 가장 최근 `recorded` 기록에 Critical/High 가 있으면 게이트가 `ARBITRATION` 을 반환하지 않는다. 시도가 2 미만이면 `RETRY`, 2 이상이면 `HOLD` 다. [실행] (CMD-2 `test_gate_keeps_hold_when_stale_record_has_high`)
- **AC-118** `references/readiness-policy.md` 가 readiness 프롬프트 필수 요소로 같은 `formal_round` 의 직전 readiness 시도 결과 경로와 직전 Claude 공식 리뷰 open findings 경로 둘 다를 지정하고, 그 전달이 R2.1 의 author 문맥 상속 금지와 구분된다는 것을 명시한다. [실행] (CMD-2 `test_readiness_prompt_carries_prior_findings`)
- **AC-119** 가장 최근 `recorded` 기록이 앞선 `recorded` 기록의 Critical/High finding ID 를 `resolved_finding_ids` 에 싣지 않으면 게이트가 그 Critical/High 를 유효 집합에 넣어 **`READY` 도 `ARBITRATION` 도 반환하지 않는다**. 등록 digest 를 가리키는 기록이 있는 경로와 없는 경로 **양쪽 모두**에서 그렇다. 최신 기록의 `findings` 에 그 ID 가 없다는 것만으로는 대체가 성립하지 않는다. [실행] (CMD-2 `test_gate_requires_explicit_resolution_to_supersede`)
- **AC-120** readiness 결과 스키마가 `resolved_finding_ids` 를 필수 필드로 요구하고 그 값이 문자열 배열이며 빈 배열을 허용한다. [실행] (CMD-2 `test_readiness_schema_requires_resolved_finding_ids`)
- **AC-117** R6.10 표의 갈래 ③ — 등록 digest 를 가리키는 `recorded` 기록이 없고 그 `formal_round` 의 가장 최근 `recorded` 기록의 Critical/High 가 0 이면, 시도가 2 미만이면 `RETRY`, 2 이상이면 `ARBITRATION` 을 반환한다. 갈래 ①·②·③ 이 같은 상태에 동시에 적용되는 경우가 없다. [실행] (CMD-2 `test_gate_arbitration_when_stale_record_is_clean`)

## Requirements traceability

요구사항 정의 수는 71이고 아래 표의 행 수도 71다. 표의 행 순서는 요구사항 정의 순서와 같다. 매핑된 AC 는 해당 요구사항 문언의 모든 독립 조건을 판정하는 것만 싣는다.

| 요구사항 | 판정하는 AC |
|---|---|
| R1.1 | AC-1 |
| R1.2 | AC-2, AC-69 |
| R1.3 | AC-3, AC-14 |
| R1.4 | AC-4, AC-70, AC-92 |
| R1.5 | AC-5 |
| R1.6 | AC-6 |
| R1.7 | AC-7 |
| R1.8 | AC-8 |
| R1.9 | AC-9, AC-33 |
| R1.10 | AC-10 |
| R1.11 | AC-11 |
| R1.12 | AC-114 |
| R2.1 | AC-12 |
| R2.2 | AC-13, AC-70 |
| R2.3 | AC-14 |
| R2.4 | AC-15, AC-68 |
| R2.5 | AC-16, AC-71 |
| R2.6 | AC-17 |
| R2.7 | AC-18 |
| R2.8 | AC-19, AC-72, AC-73, AC-103 |
| R2.9 | AC-79 |
| R2.10 | AC-118 |
| R3.1 | AC-20, AC-21, AC-22, AC-101 |
| R3.2 | AC-23, AC-24 |
| R3.3 | AC-25 |
| R3.4 | AC-26 |
| R3.5 | AC-27 |
| R4.1 | AC-28, AC-29, AC-33, AC-98, AC-108 |
| R4.2 | AC-29, AC-95 |
| R4.3 | AC-30, AC-74 |
| R4.4 | AC-31, AC-87 |
| R4.5 | AC-32, AC-94, AC-111 |
| R4.6 | AC-33 |
| R4.7 | AC-34 |
| R4.8 | AC-95, AC-96, AC-106, AC-108 |
| R4.9 | AC-107 |
| R5.1 | AC-35, AC-75 |
| R5.2 | AC-36, AC-88 |
| R5.3 | AC-37, AC-81 |
| R5.4 | AC-38 |
| R6.1 | AC-39 |
| R6.2 | AC-40, AC-76, AC-89, AC-95 |
| R6.3 | AC-41 |
| R6.4 | AC-42, AC-89, AC-93 |
| R6.5 | AC-43, AC-90 |
| R6.6 | AC-44, AC-82, AC-99, AC-119 |
| R6.7 | AC-45, AC-97, AC-98 |
| R6.8 | AC-46 |
| R6.9 | AC-80, AC-81, AC-100, AC-109, AC-110, AC-112, AC-113 |
| R6.10 | AC-82, AC-83, AC-91, AC-116, AC-117, AC-119 |
| R7.1 | AC-47 |
| R7.2 | AC-48 |
| R7.3 | AC-49 |
| R7.4 | AC-50 |
| R8.1 | AC-51, AC-120 |
| R8.2 | AC-52 |
| R8.3 | AC-53 |
| R8.4 | AC-54 |
| R8.5 | AC-55 |
| R8.6 | AC-25, AC-56 |
| R8.7 | AC-57, AC-81 |
| R9.1 | AC-58 |
| R9.2 | AC-59 |
| R9.3 | AC-60 |
| R9.4 | AC-61, AC-104, AC-115 |
| R9.5 | AC-62, AC-77 |
| R9.6 | AC-63, AC-66, AC-67, AC-78, AC-102 |
| R9.7 | AC-64 |
| R9.8 | AC-65, AC-104 |
| R9.9 | AC-84, AC-85, AC-105 |
| R9.10 | AC-86, AC-105 |

## Architecture

### 컴포넌트와 책임

| 컴포넌트 | 책임 | 신설 여부 |
|---|---|---|
| Claude 오케스트레이터 | 요구사항 발굴, 프롬프트 작성, 프로세스 호출, digest 대조, 상태 기록, 게이트 결과에 따른 분기 | 기존 |
| Codex author 프로세스 | Spec 초안 작성과 개정, 개정 노트 작성, 조합 검토 | 신설 |
| fresh Codex readiness reviewer 프로세스 | 체크리스트 여덟 항목 판정, finding 생성, 참고 점수 계산 | 신설 |
| Claude quality-reviewer 에이전트 | 공식 Spec 리뷰. 설계 정합성·시간축 전개·교차 회귀 판정 | 기존, 변경 없음 |
| `scripts/quality_state.py` | readiness 기록, `draft_attempts` 기록, 게이트 판정, digest 대조 강제 | 확장 |
| `scripts/validate_review.py` | readiness 결과 검증 함수 추가. 기존 `validate_review` 와 `REQUIRED_CHECKS` 는 불변 | 확장 |
| `schemas/readiness-result.schema.json` | readiness 결과 구조 계약 | 신설 |
| `references/readiness-policy.md` | author·readiness 프롬프트 계약, 호출 템플릿, 체크리스트 정의, 반복·탈출 규칙 | 신설 |
| `templates/spec.md` | 요구사항 추적표 절과 판정 명령 표 절 추가 | 확장 |

### 세 심사의 역할 분리

readiness 와 Claude 공식 리뷰는 서로를 대체하지 않는다. 실측(§ Problem and context)이 이 분리를 강제한다.

- readiness 는 문서의 **정합성**만 본다. 판정 대상은 절 구조, 번호 무결성, 추적표, 판정 수단 배정, 직전 findings 의 해소 여부다. 전부 문서를 훑어 기계적으로 확인 가능하다.
- Claude 공식 리뷰는 **설계**를 본다. 규칙이 여러 실행에 걸쳐 돌 때 무엇이 깨지는지, 개별 수정이 만든 교차 회귀가 있는지, 요구사항 본문과 Decisions 가 충돌하는지를 본다.
- 두 판정이 겹치지 않으므로 readiness 통과가 공식 통과를 예측하지 않는다. readiness 는 "공식 리뷰를 쓸 만큼 문서가 형태를 갖췄는가"만 결정하는 비용 게이트다.

### 상태 머신에 대한 변경

`ALLOWED_TRANSITIONS` 에 비종료 stage `AWAITING_READINESS_DECISION` 하나를 추가한다. 그 밖의 기존 엣지와 상태는 그대로다. 추가되는 엣지는 셋이다.

| 엣지 | 조건 |
|---|---|
| `SPEC_REVIEW → AWAITING_READINESS_DECISION` | 게이트가 `HOLD` 를 반환했다. 아니면 `transition` 이 거부한다(R4.9) |
| `AWAITING_READINESS_DECISION → SPEC_REVIEW` | `resume-readiness` 만 수행한다. 다른 stage 에서의 호출과 이 엣지의 일반 `transition` 은 거부한다(R4.8) |
| `AWAITING_READINESS_DECISION → NEEDS_REDESIGN` / `BLOCKED` / `CANCELLED` | 사용자의 종료 결정을 `transition` 이 기록한다 |

**readiness 는 종료 상태를 만들지 않는다.** 새 stage 는 `TERMINAL_STATES` 에 속하지 않으며, 이 상태에서 종료로 가는 유일한 길은 사용자의 명시적 결정이다. 비권위 심사자가 단독으로 워크플로를 끝내지 않는다는 § '세 심사의 역할 분리'의 귀결이다.

상태 머신에서 함께 바뀌는 것이 둘 더 있다.

- **전이 가드 두 개.** `SPEC_REVIEW → AWAITING_READINESS_DECISION` 은 게이트 반환값이 `HOLD` 일 때만 허용하고(R4.9), `AWAITING_READINESS_DECISION → SPEC_REVIEW` 는 `resume-readiness` 만 수행한다(R4.8). 두 가드는 기존 `CLASSIFIED → AWAITING_PLAN_APPROVAL` 의 모드 조건, `SPEC_REVIEW → SPEC_PASSED` 의 리뷰 조건과 같은 층에 놓인다.
- **`status_reason` 기록 분기.** 현재 `transition` 은 target 이 `BLOCKED`·`NEEDS_REDESIGN`·`CANCELLED` 일 때에만 reason 을 `status_reason` 에 남긴다(`quality_state.py:510-511`). R4.5 가 비종료 stage 에 `READINESS_HELD:<finding id>` 를 남기라고 요구하므로 그 분기에 `AWAITING_READINESS_DECISION` 을 더한다. 값은 `transition --reason` 이 기록하고, `resume-readiness` 가 `SPEC_REVIEW` 로 되돌릴 때 `status_reason` 을 `null` 로 지운다.

그 밖에 상태에 추가되는 것은 데이터뿐이다.

### 게이트 판정의 위치

게이트 판정은 `quality_state.py` 안의 결정적 함수다. 오케스트레이터의 판단이 아니라 함수의 반환값이 분기를 결정한다. 입력은 R6.10 이 정의한 두 가지(시도 횟수와 체크리스트·finding 판정)이며, 판정 기록이 없을 때의 반환값은 R6.10 의 세 갈래 표가 확정한다. `formal_round` 는 인자가 아니라 `rounds[artifact] + 1` 로 상태에서 유도한다(R6.7). 시도 횟수는 그 라운드에서 가장 최근 재개 결정 이후의 기록 수이고(재개 결정이 없으면 그 라운드 전체, digest·`outcome` 무관), 체크리스트와 finding 판정은 그 라운드에 속하면서 `outcome` 이 `recorded` 이고 현재 등록 digest 를 가리키는 가장 최근 기록 하나만 쓴다. 여기서 **등록 digest** 는 `artifacts[artifact]` 가 가리키는 파일의 현재 SHA-256 이며, 기존 상태 필드 `artifact_digests` 는 직전 공식 리뷰 시점의 값이라 게이트 판정에 쓰지 않는다(R6.6). 출력은 네 값 중 하나다.

- `READY` — 판정 기록의 체크리스트 여덟 항목이 전부 `pass` 또는 `not_applicable` 이고 R6.10 의 **유효 Critical/High 집합**이 비어 있다. 곧 앞선 `recorded` 기록의 Critical/High 가 `resolved_finding_ids` 로 닫히지 않은 채 남아 있으면 `READY` 가 아니다. 공식 리뷰로 진행한다.
- `RETRY` — 미충족이 있고 이 시도 구간의 시도가 2회 미만이다. author 개정 후 재심사한다. 판정 기록이 아예 없는 경우(개정 직후, 또는 두 실패 시도만 있는 경우)도 미충족으로 본다.
- `ARBITRATION` — 시도 구간 2회 소진, 미충족이 있으나 R6.10 의 **유효 Critical/High 집합**이 비어 있다(표의 갈래 ① 또는 ③). 미충족 항목을 근거로 첨부해 공식 리뷰로 진행하며, 갈래 ①이면 readiness 가 유효한 결과를 내지 못했다는 사실도 함께 싣는다.
- `HOLD` — 시도 구간 2회 소진, R6.10 의 **유효 Critical/High 집합**이 비어 있지 않다(표의 갈래 ②). 등록 digest 를 가리키는 기록이 있는 경로에서도 같다. 그 기록이 등록 digest 를 가리키지 않게 됐더라도 같다. `AWAITING_READINESS_DECISION` 으로 전이하고 사용자 결정을 기다린다. 종료가 아니다.

`record-review` 와 `record-review-unverified` 는 spec artifact 에 대해 이 반환값이 `READY` 또는 `ARBITRATION` 임을 요구한다(R2.8). `record-review-error` 와 readiness 필드가 없는 schema v1 상태는 그 요구에서 면제된다.

## Interfaces and data flow

### SPEC_REVIEW 단계의 실행 순서

```text
SPEC_REVIEW 진입
 └─ 오케스트레이터: 요구사항 발굴 (brainstorming-policy.md)
     └─ 물질적 모호성이 남으면 사용자에게 질의해 해소
 └─ [반복] 개정 주기 (formal_round = N)
     ├─ author 호출 (codex exec, workspace-write, 프롬프트 파일을 stdin 으로)
     │   └─ record-draft-attempt → draft_attempts.spec += 1
     ├─ set-artifact --kind spec (절대 경로)
     ├─ N >= 2: spec-revision-notes.md 작성 → revision_check.py --artifact spec
     │            (종료 코드 0 까지 반복. 라운드를 소모하지 않는다)
     ├─ digest 대조: 대상 경로 == artifacts.spec, 현재 SHA-256 계산
     ├─ readiness 호출 (codex exec, read-only, 프롬프트 파일을 stdin 으로)
     ├─ record-readiness → 스키마 검증 + digest 대조 + 기록
     └─ readiness-gate → READY | RETRY | ARBITRATION | HOLD  (한도 단위는 시도 구간)
         ├─ RETRY  → author 에 finding 전달하고 개정 주기 반복
         ├─ HOLD   → AWAITING_READINESS_DECISION 전이, 사용자 결정 대기
         │            ├─ resume-readiness → SPEC_REVIEW 로 복귀, 개정 주기 재개
         │            └─ transition       → NEEDS_REDESIGN | BLOCKED | CANCELLED
         └─ READY | ARBITRATION
             └─ Claude 공식 리뷰 라운드 N (fresh quality-reviewer)
                 ├─ record-review [N>=2 는 --revision-check 필수] → PASS  → SPEC_PASSED
                 └─ record-review [N>=2 는 --revision-check 필수] → REVISE → formal_round = N+1, 개정 주기 재개
```

개정 점검(`revision_check.py`)과 `record-review --revision-check` 는 base revision 이 이미 갖는 계약이며(v5.0.0, `SKILL.md` 의 `### Spec` 절), 이 작업이 새로 만들지 않는다. 이 작업은 그 계약의 앞에 author 호출과 readiness 심사를 끼워 넣을 뿐이고, 개정 점검의 입력·출력·거부 조건을 바꾸지 않는다(R9.6). 개정 점검을 readiness 호출보다 앞에 두는 이유는, 식별자 정합이 깨진 산출물을 readiness 가 심사하면 체크리스트 C3~C5 가 같은 결손을 중복 보고하기 때문이다.

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

author 결과는 기존 `schemas/codex-result.schema.json` 으로 검증한다. 새 스키마를 만들지 않는 이유는 § Decisions D13 에 있다.

### 상태 필드

```json
{
  "draft_attempts": {"spec": 0, "plan": 0},
  "readiness_decisions": [],
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
        "resolved_finding_ids": ["READY-00"],
        "artifact_digest": "…64 hex…",
        "reviewer_model": "gpt-5.6-sol",
        "result_path": "/abs/…/readiness-spec-a1.json",
        "recorded_at": "2026-09-05T08:00:00Z"
      }
    ]
  }
}
```

사용자의 재개 결정은 `readiness_decisions` 배열에 `{artifact, formal_round, decision, reason, decided_at}` 로 남는다(R4.8). `decided_at` 은 R6.10 의 시도 횟수 계산에서 기준점으로 쓰인다.

`schema_version` 은 1 을 유지한다(§ Decisions D3). R6.2 의 세 필드가 없는 상태는 읽을 수 있지만 로드만으로 필드가 생기지 않는다(R6.4). 새 상태는 `init` 이 세 필드를 위 형태의 빈 값으로 만든다. `outcome` 이 `schema_invalid` 또는 `digest_mismatch` 인 실패 기록은 `verdict`·`score`·`checklist`·`findings` 를 비운 채 나머지 필드만 채운다(R6.9).

### 새 `quality_state.py` 서브커맨드

| 명령 | 입력 | 출력 | 효과 |
|---|---|---|---|
| `record-draft-attempt` | `--state`, `--artifact` | 갱신된 상태 JSON | `draft_attempts[artifact] += 1` |
| `record-readiness` | `--state`, `--artifact`, `--result`, `--artifact-digest`, `--formal-round`, `--reviewer-model`, `--invocation-status`, `--stderr-path` | 갱신된 상태 JSON | R6.9 의 순서(호출 상태 → 스키마 검증 → digest 대조)로 `outcome` 을 정해 기록 추가. `outcome` 은 인자로 받지 않는다. `outcome` 이 `recorded` 이면 결과의 `resolved_finding_ids` 를 상태 기록에 그대로 복사한다(R6.1). 실패도 기록한다 |
| `readiness-gate` | `--state`, `--artifact` | `{"decision": …, "formal_round": N, "attempts": N, "failed_checks": [...], "high_findings": [...], "judged_record": …}` | 없음(읽기 전용) |
| `resume-readiness` | `--state`, `--artifact`, `--reason` | 갱신된 상태 JSON | stage 가 `AWAITING_READINESS_DECISION` 일 때만 동작한다. 사용자 재개 결정을 `readiness_decisions` 에 기록하고 `SPEC_REVIEW` 로 전이하며 `status_reason` 을 지운다 |

`record-readiness` 는 `--artifact-digest` 가 `artifacts[artifact]` 의 현재 파일 digest 와 같지 않으면 호출 자체를 거부한다(R5.1·R5.2). 결과의 `artifact_digest` 가 그 값과 다르면 `digest_mismatch` 실패 기록을 남긴다. `--formal-round` 가 `rounds[artifact] + 1` 과 다르면 역시 호출을 거부한다(R6.7). `--invocation-status` 가 `ok`·`failed` 가 아니거나, `failed` 인데 `--stderr-path` 가 없거나 그 경로가 존재하지 않으면 거부한다(R6.9). `AWAITING_READINESS_DECISION` 진입 시의 `status_reason` 은 별도 명령이 아니라 기존 `transition --to AWAITING_READINESS_DECISION --reason "READINESS_HELD:<finding id>"` 가 기록한다. 그러려면 `transition` 의 reason 기록 분기에 이 비종료 stage 를 더해야 한다(§ Architecture). `resume-readiness` 가 `SPEC_REVIEW` 로 되돌릴 때 그 값을 `null` 로 지운다. `resume-readiness` 는 stage 가 `AWAITING_READINESS_DECISION` 이 아니면 거부하고(R4.8), `SPEC_REVIEW → AWAITING_READINESS_DECISION` 전이는 게이트 반환값이 `HOLD` 가 아니면 거부된다(R4.9). 네 명령 모두 `light` 모드 상태에서는 거부된다(R2.9).

## Failure behavior

| 실패 | 감지 | 동작 | 상태 |
|---|---|---|---|
| author 비정상 종료 | `codex exec` 종료 코드 != 0 | 명령과 표준 오류를 사용자에게 보고. 모델 대체 없음 | `SPEC_REVIEW` 유지 |
| author 결과 파일 없음·스키마 위반 | `codex-result.schema.json` 검증 실패 | 위와 같음 | `SPEC_REVIEW` 유지 |
| author 가 Spec 을 바꾸지 않음 | 호출 전후 SHA-256 동일 | 개정 실패로 보고 | `SPEC_REVIEW` 유지 |
| author 가 허용 밖 파일 수정 | `git status --porcelain` 에 예상 밖 경로 | 변경을 되돌리지 않고 사용자에게 보고 후 판단 요청 | `SPEC_REVIEW` 유지 |
| 모델 거부·부재 | Codex 의 모델 거부 응답 | `BLOCKED_MODEL_UNAVAILABLE` 복구 경로. 사용자 승인 없이 대체 금지 | 현재 단계 유지, 사용자가 거부하면 `BLOCKED` |
| readiness 호출 비정상 종료·결과 파일 미생성·타임아웃 | `codex exec` 종료 코드 != 0 또는 결과 파일 부재 | `invocation_failed` 실패 기록. 시도 1회 소모. 모델 거부면 `BLOCKED_MODEL_UNAVAILABLE` 경로 | `SPEC_REVIEW` 유지 |
| readiness 결과 스키마 위반 | `readiness-result.schema.json` 검증 실패 | `schema_invalid` 실패 기록. 시도 1회 소모 | `SPEC_REVIEW` 유지 |
| 심사 대상 경로 불일치 | 대상 경로 != `artifacts.spec` | readiness 호출 자체를 하지 않음 | `SPEC_REVIEW` 유지 |
| 결과 digest 불일치 | 결과 `artifact_digest` != 심사 시점 digest | `digest_mismatch` 실패 기록. 시도 1회 소모 | `SPEC_REVIEW` 유지 |
| 시도 구간 2회 소진, 가장 최근 `recorded` 기록에 Critical/High 잔존 | 게이트 판정 `HOLD` | 잔여 finding 을 사용자에게 제시하고 결정을 기다린다. 자동 진행·자동 종료 없음 | `AWAITING_READINESS_DECISION`, `status_reason = READINESS_HELD:<id>` |
| 시도 구간 2회 소진, 가장 최근 `recorded` 기록에 Critical/High 잔존, 그 뒤 산출물 개정으로 그 기록이 등록 digest 와 어긋남 | 게이트 판정 `HOLD`(R6.10 표의 갈래 ②) | 위와 같다. 개정만으로 `ARBITRATION` 으로 내려가지 않는다. 그보다 오래된 기록의 Critical/High 는 이 판정에 쓰이지 않는다 | `AWAITING_READINESS_DECISION` |
| 시도 구간 2회 소진, 가장 최근 `recorded` 기록의 Critical/High 가 0(앞선 것이 모두 `resolved_finding_ids` 로 닫힘)이거나 그 라운드에 `recorded` 기록이 없음 | 게이트 판정 `ARBITRATION`(R6.10 표의 갈래 ③ 또는 ①) | 미충족 항목을 근거로 첨부하고 공식 리뷰 진행 | `SPEC_REVIEW` 유지 |
| 비대화형 stdin 무한 대기 | 프로세스가 응답 없이 멈춤 | 호출 계약이 stdin 을 프롬프트 파일에 고정해 사전 차단. `/dev/null` 변형은 프롬프트를 명령행 인자로 넘길 때만 쓴다 | 해당 없음 |

readiness 시도 실패가 한도를 소모하는 이유는, 소모하지 않으면 반복적으로 실패하는 심사가 무한 루프를 만들기 때문이다. 한도를 실제로 셀 수 있으려면 실패도 상태에 남아야 하므로 R6.9 가 실패를 `outcome` 이 붙은 기록으로 남긴다. 기록하지 않고 한도만 소모한다고 규정하면 재개 시점에 시도 수가 0 으로 보여 계약이 무너진다. 그 `formal_round` 에 유효한 readiness 결과가 하나도 없는 상태에서 시도가 소진되면 Critical/High 판정 근거가 없으므로 `ARBITRATION` 으로 처리하고(R6.10 표의 갈래 ①), 그 사실을 공식 리뷰 근거에 명시한다. **유효한 결과가 있었으나 그 뒤의 개정으로 등록 digest 를 가리키지 않게 된 경우는 이와 다르다** — 그 `formal_round` 의 **가장 최근** `recorded` 기록에 Critical/High 가 있으면 그것이 그대로 살아 있어 게이트가 `HOLD` 를 내고(갈래 ②, AC-116), 그 기록의 Critical/High 가 0 이면 `ARBITRATION` 을 낸다(갈래 ③, AC-117). 두 갈래 모두 **가장 최근 하나**만 보며, 그보다 오래된 기록은 이력일 뿐이다. 세 갈래 모두 R6.10 의 표 하나가 확정하므로 같은 상태에 두 규정이 다른 값을 요구하는 일이 없다.

## Security and risk

- 두 Codex 프로세스 모두 sandbox 를 우회하지 않는다. author 는 `workspace-write`, readiness 는 `read-only` 다. 승인 우회·권한 확장 옵션 여덟 개는 R1.4 가 CLI 버전과 함께 열거하고 `references/readiness-policy.md` 가 그것을 싣는다. 그 목록은 `--help` 출력이 아니라 플래그별 수용 여부 실측으로 만들었다.
- 프롬프트·결과·이벤트·표준 오류 파일에 자격 증명을 넣지 않는다. 이 파일들은 `.claude/quality-state/<task-id>/` 아래에만 둔다.
- 이 저장소에서 `.claude/quality-state/` 는 이미 무시된다. `git check-ignore -v .claude/quality-state/` 가 `.gitignore:25` 를 근거로 종료 코드 0 을 반환한다. 프롬프트·결과·이벤트 파일이 실수로 커밋될 경로가 아니므로 이 작업에 추가 조치가 필요 없다.
- 배포본 `~/.claude/skills/quality-goal/` 을 이 작업에서 갱신하지 않는다. 다른 세션이 배포본을 실행 중이며 `chezmoi apply` 는 그 세션의 계약을 실행 중에 바꿔 버린다.
- readiness reviewer 는 읽기 전용이므로 심사가 산출물을 조용히 고칠 수 없다. author 만 쓰기 권한을 갖고, 그 쓰기 범위는 두 파일로 한정된다.
- 위험: readiness 가 통과시킨 산출물을 Claude 가 낮게 평가하는 경우가 실측으로 두 번 있었다. 체크리스트 게이트는 이 격차를 없애려 하지 않고 역할 분리로 수용한다. 절감은 author 쪽에서 나온다(#42 4차: Spec 개정 3회 85분, Claude 토큰 0).
- 위험: 체크리스트 항목이 늘어나면 readiness 가 형식 트집으로 개정을 반복시킬 수 있다. 항목을 여덟 개로 고정하고, 항목 추가는 별도 정책 결정으로 다룬다.

## Test strategy

신규 계약은 전부 `dot_claude/skills/quality-goal/tests/` 의 결정적 테스트로 판정한다. 문서 계약은 `test_content_contracts.py` 에, 상태·게이트 계약은 `test_quality_state.py` 에, 결과 스키마 검증은 `test_validate_review.py` 에 추가한다. Codex 프로세스를 실제로 호출하는 테스트는 만들지 않는다. 호출 계약은 문서에 실린 템플릿 문자열로 판정하고, 게이트·기록·검증은 결과 JSON 픽스처로 판정한다.

픽스처는 `tests/fixtures/` 에 추가한다: READY 결과 1건, 체크리스트 1개 실패 결과 1건, Critical/High 포함 결과 1건, 스키마 위반 결과 1건, readiness 필드가 없는 schema v1 상태 1건.

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
| CMD-7 | `OLD_PY` 를 3.12 미만 인터프리터 경로로 두고 `"$OLD_PY" -c 'import sys;raise SystemExit(0 if sys.version_info<(3,12) else 1)' && python3 dot_claude/skills/quality-goal/tests/assert_python_version.py && ! "$OLD_PY" dot_claude/skills/quality-goal/tests/assert_python_version.py` | 종료 코드 0. 첫 절이 `OLD_PY` 가 실제로 3.12 미만임을 단언하고, 둘째 절이 스크립트 부재·구문 오류를 잡고, 셋째 절이 거부 분기를 확인한다. macOS 에서는 `OLD_PY=/usr/bin/python3`(3.9.6)이 성립한다. 어떤 인터프리터도 3.12 미만이 아니면 이 명령은 실행할 수 없고, 그때 AC-85 는 미판정으로 기록한다 |

테스트 스위트는 **Python 3.12 이상**을 요구한다. 근거 둘 다 실측이다.

1. `tests/test_quality_state.py` 의 `ResumeSelectionTests` 가 `unittest.TestCase.enterContext` 를 쓰고 그 API 는 3.11 에서 추가됐다. `/usr/bin/python3` 3.9.6 은 310건 중 23건이 오류로 종료 코드 1 을 낸다.
2. `unittest` 가 `-k` 필터에 아무것도 매칭되지 않을 때 `NO TESTS RAN` 과 함께 종료 코드 5 를 내는 동작은 3.12 에서 도입됐다. 실측으로 3.12.14 와 3.14.7 은 5 를, 3.9.6 은 0 을 반환한다. 3.12 미만에서는 CMD-2 가 존재하지 않는 테스트 이름에도 성공을 반환해 그것을 판정 수단으로 쓰는 AC 들이 공허하게 통과한다.

CMD-1 과 CMD-2 는 테스트를 실행하기 전에 `tests/assert_python_version.py` 로 그 조건을 확인하며, 조건이 어긋나면 테스트를 실행하지 않고 실패한다(R9.9·R9.10). CMD-7 은 **같은 스크립트**를 3.12 미만 인터프리터로 실행해 거부 분기를 직접 확인한다. **판정 명령 표는 두 곳에 있고 정본은 하나다.** 정본은 `docs/quality-goal-maintenance.md` 의 `## 판정 명령 표` 절이며, 스킬과 함께 유지되고 저장소 테스트가 읽는다. 이 Spec 의 위 표는 그 정본을 이 작업 시점에 옮겨 적은 **사본**이다 — `docs/development/…/spec.md` 는 goal 이 끝나면 옮겨지거나 지워질 수 있는 일회성 산출물이라 영구 테스트가 읽으면 CMD-1 이 영구히 깨진다. R9.9 의 세 AC 는 모두 정본을 판정한다: AC-84 는 정본의 최소 인터프리터 버전 문언과 두 근거를, AC-105 는 정본의 CMD-1·CMD-2 정의가 `tests/assert_python_version.py` 를 호출하고 버전 비교식을 인라인으로 복제하지 않는지를, AC-85 는 문서가 아니라 그 스크립트의 동작을 CMD-7 로 판정한다. 사본을 판정하는 AC 는 두지 않는다. CMD-4 는 `SKILL.md` 의 여덟 절만 비교하므로 어느 표도 보지 않고, CMD-7 도 명령 문안이 아니라 스크립트 동작만 본다.

### CMD-4 상세

보존 대상 절을 base revision 과 바이트 단위로 비교한다. 비교 대상은 여덟이다 — `### Plan`, `### Approval`, `### Implementation`, `### Code review`, `## Independent verification`, `## Safety rules`, `## Review invocation contract`, `## Codex invocation contract`. 앞의 넷은 R9.6 의 Plan·Code 단계 절차이고, 다음 둘은 승인 digest·dirty-worktree 보호·결정적 검증 계약이며(AC-66, AC-78), 마지막 둘은 plan·code 리뷰어 호출과 구현·수정 라운드의 codex 호출·model-unavailable 복구를 실제로 지배하는 절이다(AC-102). 이 변경은 여덟 절을 모두 건드리지 않는다. readiness 절차는 `### Spec` 절과 Stage table, 참조 경로 목록, 그리고 새 `references/readiness-policy.md` 에만 들어간다.

```
git show <base>:<SKILL.md> 로 base 본문을 얻고 현재 본문과 함께
^#{2,3} 헤딩으로 절을 쪼갠 뒤 위에 열거한 여덟 절의 본문이 같은지 단언한다.
절 이름 목록은 스크립트 안에 상수로 두고 여덟 개를 모두 싣는다.
모두 같으면 "보존 대상 절 불변" 을 출력하고 0 으로 끝낸다.
```

실행 스크립트는 `tests/` 아래 `assert_preserved_sections.py` 로 두고 CMD-4 는 그 스크립트를 호출한다. Spec 본문에 스크립트를 그대로 싣지 않는 이유는 실행 가능한 판정 수단이 저장소 파일로 존재해야 재현 가능하기 때문이다.

### CMD-6 상세

base revision 의 `tests/test_*.py` 네 파일(`test_content_contracts.py`, `test_quality_state.py`, `test_validate_review.py`, `test_revision_check.py`)에서 `def test_` 이름을 모아 현재 이름 집합의 부분집합인지 단언한다. 하나라도 삭제되거나 이름이 바뀌면 실패하고, 통과하면 `기존 테스트 보존` 을 출력한다. 실행 스크립트는 `tests/assert_tests_preserved.py` 로 둔다.

### 검증 순서

1. CMD-1 로 전체 회귀를 먼저 확인한다.
2. 실패한 AC 가 있으면 CMD-2 로 해당 테스트만 좁혀 재현한다.
3. CMD-3·CMD-4·CMD-5·CMD-6·CMD-7 은 CMD-1 과 독립적으로 실행한다.
4. Codex CLI 자체의 계약(`--output-schema` 가 `const` 를 거부하는 성질 등)은 이 저장소의 테스트로 판정하지 않는다. `docs/quality-goal-maintenance.md` 의 분기별 CLI 점검 절차에 위임한다.

## Decisions

### D1. 점수 게이트가 아니라 체크리스트 게이트를 쓴다

- 대안 A: 이슈 본문대로 `readiness score >= 90`.
- 대안 B: 임계값을 상향(95 등)하거나 설정값으로 뺀다.
- 대안 C(채택): 점수를 판정에서 완전히 제거하고 기계적으로 확인 가능한 체크리스트 여덟 항목으로 게이트를 구성한다.

근거: 대응점 두 개에서 readiness 97 대 Claude 74, readiness 94 대 Claude 78 로 같은 방향으로 크게 벌어졌다(§ Problem and context). 대안 B 는 97점이 74점을 받는 상황을 바꾸지 못한다. 두 심사가 다른 것을 측정하므로 점수의 상관을 전제한 어떤 임계값도 근거가 없다. 체크리스트 항목은 실측에서 readiness 가 정확히 잡은 범주와 정확히 겹친다.

### D2. 체크리스트 항목을 여덟 개로 고정한다

- 대안 A: 항목을 설정값으로 열어 둔다.
- 대안 B(채택): C1~C8 을 문서와 스키마에 고정하고 변경은 별도 정책 결정으로 다룬다.

근거: 항목이 유동적이면 readiness 가 형식 트집으로 개정을 반복시키는 실패 모드가 열린다. 고정하면 `checklist` 배열의 완전성 자체를 스키마로 강제할 수 있다(AC-56).

### D3. `schema_version` 은 1 을 유지한다

- 대안 A(채택): `schema_version` 1 유지. R6.2 의 세 필드(`readiness`, `draft_attempts`, `readiness_decisions`)를 선택적 필드로 추가하고, 없으면 미실행으로 간주한다. 로드 시 상태 파일에 주입하지 않는다(R6.4).
- 대안 B: `schema_version` 2 로 올리고 `load_state` 가 1 과 2 를 모두 수용한다.
- 대안 C: 2 로 올리고 v1 을 별도 마이그레이션 명령으로 변환한다.

근거: `load_state` 는 현재 `schema_version != 1` 을 거부한다(`scripts/quality_state.py:264-265`). 대안 B·C 로 v2 파일을 만들면 이 변경을 `git revert` 했을 때 진행 중인 goal 의 상태 파일을 구버전 스크립트가 읽지 못해 데이터가 손실된다. 스킬 롤백은 실제 운용 경로이며 유지보수 문서가 SemVer 정책으로 다루는 상황이다. 대안 A 는 신구 스크립트가 같은 파일을 양방향으로 읽게 하고, R6.4 가 요구하는 "필드가 없으면 미실행으로 간주"를 그대로 구현한다. 비용은 버전 번호로 형태를 구별할 수 없다는 것이며, 필드 존재 검사로 대체한다. 그 검사가 성립하려면 로드가 필드를 만들지 않아야 하므로 R6.4 가 주입을 금지하고, D14 의 면제 표지가 그 성질에 의존한다. 세 곳(D3·R6.4·D14)이 같은 규칙을 말한다.

### D4. readiness 절차는 `references/readiness-policy.md` 로 분리한다

- 대안 A: `SKILL.md` 에 직접 싣는다.
- 대안 B(채택): 상세를 새 reference 로 빼고 `SKILL.md` 에는 단계 절차와 참조 경로만 싣는다.

근거: `tests/test_content_contracts.py:1244` 가 frontmatter 를 포함한 `SKILL.md` 파일 전체를 500행 미만으로 강제한다(R9.1). 현재 393행이고 상한이 499행이므로 더 넣을 수 있는 것은 106행이며, author·readiness 두 호출 계약과 체크리스트 정의와 반복 규칙을 모두 넣으면 초과한다. 기존 스킬이 이미 정책을 reference 로 분리하는 구조를 쓴다.

### D5. Spec 템플릿에 요구사항 추적표 절과 판정 명령 표 절을 추가한다

- 대안 A: 추적표가 있으면 검사하고 없으면 해당 항목을 `not_applicable` 로 둔다.
- 대안 B(채택): 템플릿에 두 절을 추가해 항상 존재하게 한다.

근거: C3·C4·C5·C7 네 항목은 추적표와 판정 명령 표가 있어야 판정 가능하다. 대안 A 는 게이트의 절반을 사실상 무력화한다. 이 결정은 열린 이슈 #58(Spec 요구사항 추적표 필수화)의 범위와 겹치지만, 겹치는 부분은 템플릿에 절을 추가하는 것 하나이고 #58 이 다루는 리뷰 루브릭·`REQUIRED_CHECKS` 변경은 하지 않는다. #58 이 구현될 때 이 절 정의를 그대로 재사용할 수 있다.

### D6. author 가 초안 작성까지 담당한다

- 대안 A: 초안은 Claude 가 쓰고 개정만 Codex 가 한다.
- 대안 B(채택): 오케스트레이터가 요구사항 발굴을 수행해 프롬프트에 담고, 초안 작성과 개정을 모두 author 가 한다.

근거: 이슈 #70 의 목표는 "작성과 반복 개정"을 옮기는 것이다. 실측은 개정만 검증했으나(#42 는 이미 초안이 있었다), 초안 작성이 개정보다 분량이 크므로 절감 폭이 더 크다. 요구사항 발굴은 사용자 질의가 필요할 수 있어 오케스트레이터에 남긴다. 위험은 초안 품질이 낮으면 개정 주기가 늘어난다는 것이며, 시도 구간당 2회 한도가 그 비용을 제한한다.

### D7. 실패한 readiness 시도도 시도 구간 한도를 소모한다

- 대안 A: 스키마 위반·digest 불일치 시도는 한도에서 제외한다.
- 대안 B(채택): 실패 시도도 시도 구간당 2회에 포함한다.

근거: 대안 A 는 반복적으로 실패하는 심사가 무한 루프를 만든다. 실패가 한도를 소모하는 단위도 시도 구간이다(R4.1). 실제로 `.prior-art/.codex-readiness/result-attempt3.json`(score 0, evidence 0건)과 `result-attempt5.json`(스키마 충돌로 score 0)에서 결과가 손상된 사례가 두 번 있었다. 대안 B 는 손상이 반복되면 `ARBITRATION` 으로 빠져나가 Claude 판정을 받는다.

### D8. 게이트 판정은 오케스트레이터의 판단이 아니라 결정적 함수의 반환값이다

- 대안 A: `SKILL.md` 가 판정 규칙을 서술하고 오케스트레이터가 적용한다.
- 대안 B(채택): `quality_state.py` 의 `readiness-gate` 가 네 값 중 하나를 반환하고 오케스트레이터는 그 값으로 분기한다.

근거: 기존 스킬이 같은 원칙을 쓴다. `record-review` 가 공식 리뷰 라운드 한도와 반복 blocker 를 직접 판정하고 전이까지 수행한다(`scripts/quality_state.py:735-742`). 게이트를 서술로만 두면 오케스트레이터가 점수를 참고하거나 항목을 임의로 완화할 여지가 남는다.

### D9. 상태 머신의 Python controller 전면 이관은 하지 않는다

이슈 #70 의 "구현 방향" 절은 Python controller 가 상태 전이·readiness·공식 리뷰 라운드·모델 라우팅·결과 검증을 모두 담당하는 구조를 제안한다. 이 작업은 그 방향의 첫 조각(readiness 기록과 게이트 판정)만 구현하고, Claude·Codex CLI 호출 자체를 Python 이 subprocess 로 실행하는 구조는 만들지 않는다. 근거는 범위 제어다. 호출 주체를 바꾸면 승인 게이트·리뷰어 호출 계약·모델 unavailable 복구 경로가 모두 영향을 받아 1단계의 검증 가능성이 무너진다. 후속 작업으로 남긴다.

### D10. 탈출 조건은 Critical/High 유무로 갈리고, 그 어느 갈래도 readiness 단독 종료로 끝나지 않는다

- 대안 A: 이슈 본문대로 85~89점 + blocker 0 이면 arbitration.
- 대안 B: 이슈 #70 코멘트 2 의 제안대로 "남은 finding 이 기계적 수정으로 닫히는가"로 판단한다.
- 대안 C: Critical/High 가 0 이면 arbitration, 남아 있으면 `NEEDS_REDESIGN` 으로 종결한다.
- 대안 D(채택): 그 `formal_round` 의 **가장 최근** `recorded` 기록의 Critical/High 가 0 이면(또는 그런 기록이 아예 없으면) arbitration, 그 기록에 Critical/High 가 남아 있으면 비종료 상태 `AWAITING_READINESS_DECISION` 으로 멈추고 사용자 결정을 기다린다. 판정에 쓰는 기록은 언제나 가장 최근 하나이며 더 오래된 기록은 반환값에 영향을 주지 않는다(R6.6, R6.10 표).

근거: 대안 A 는 점수를 판정에 다시 끌어들여 D1 과 모순된다. 대안 B 는 "기계적 수정으로 닫히는가"가 판단자의 해석에 달려 있어 R3.5 의 기계적 확인 가능성 요건을 만족하지 못한다. 대안 C 와 D 는 둘 다 severity 라는 이미 스키마로 강제된 값만 쓴다. C 와 D 의 차이는 Critical/High 가 남았을 때 무엇이 일어나는가다.

**대안 C 를 버린 이유는 역할 분리와 정면으로 충돌하기 때문이다.** `NEEDS_REDESIGN` 은 `quality_state.py:68` 의 `TERMINAL_STATES` 에 속한다. 대안 C 는 비권위 심사자인 readiness 가 어떤 Claude 판정도 사람의 결정도 없이 워크플로를 끝내게 만든다. R2.6 과 § Architecture '세 심사의 역할 분리'는 readiness 를 "비용 게이트이며 공식 판정을 대체하지 않는다"고 규정하는데, 종료 권한은 그 규정이 허용하는 것보다 큰 권한이다. R3.1 의 체크리스트 여덟 항목이 전부 문서 정합성 항목이라는 점도 이를 뒷받침한다 — 그 severity 는 설계 의미를 담지 않으므로 High 를 재설계 신호로 읽는 것은 범주 오류다(이슈 #76).

이 실행 자체가 대안 C 의 반례를 남겼다. readiness 를 세 번 돌렸고 High 는 2 → 3 → 0 으로 움직였다. attempt 2 의 High 3건 중 2건은 attempt 1 개정이 새로 만든 문서 내부 모순이었다. 2회 한도에서 대안 C 를 적용했다면 이 Spec 자체가 세 번째 시도에서 전부 닫힐 문제를 안은 채 재설계로 종료됐을 것이다.

판정 근거가 아예 없는 상태(R6.10 표의 갈래 ①)는 이 선택지 밖이다. readiness 가 유효한 결과를 한 번도 내지 못했다면 막을 근거도 없으므로 `ARBITRATION` 으로 공식 리뷰에 넘기고 그 사실을 근거에 싣는다. 대안 D 가 막는 것은 **확인된** Critical/High 의 자동 통과이지 미확인 상태의 통과가 아니다.

**그렇다고 Critical/High 가 남은 산출물을 공식 리뷰로 자동 진행시키지도 않는다.** 그 경로(R4.4 의 arbitration 을 severity 와 무관하게 항상 적용하는 것)는 잔여 blocker 를 공식 리뷰가 upheld/overruled 로 판정하는 계약이 있어야 안전하다. 그 계약은 아직 없고, 근거는 저장소에서 확인했다.

1. `schemas/review.schema.json` 의 finding 구조는 `$defs/finding` 으로 완전히 정의돼 있고 `id`·`severity`·`description`·`evidence_location`·`rubric_item`·`required_resolution`·`new_blocker_evidence` 일곱을 required 로 요구하며 `additionalProperties: false` 다. 구조가 부실한 것이 아니라, **닫혀 있는 그 구조에 readiness finding 을 upheld/overruled 로 판정할 필드가 없다.** 필드를 넣으려면 스키마와 `validate_review.py` 를 함께 바꿔야 한다.
2. 같은 스키마의 `verdict` enum 은 `PASS`·`REVISE`·`BLOCKED` 뿐이라 공식 리뷰가 "재설계가 필요하다"를 표현할 값이 없다.
3. AC-31 은 arbitration 경로에서 미충족 항목과 잔여 finding 전문의 전달만 판정한다. 전달됐다는 사실이 판정됐다는 사실을 뜻하지 않는다.

따라서 대안 D 를 택한다. fail-closed 는 그대로다 — 사용자가 명시적으로 결정하기 전에는 공식 리뷰로도 종료로도 진행하지 않는다. 바뀐 것은 "누가 그 막다른 길에서 결정하는가"뿐이며, 그 결정은 대화가 아니라 상태에 기록되는 서브커맨드로 받는다(R4.8). 이 구조는 새로 발명한 것이 아니라 기존 `BLOCKED_MODEL_UNAVAILABLE` 복구 경로와 같다 — 그 경로도 현재 stage 를 유지한 채 사용자에게 묻고, 사용자가 거부할 때에만 종료로 간다. 사용자 승인 게이트가 하나 더 생기는 것이 아니다. 구현 승인 게이트는 여전히 `AWAITING_PLAN_APPROVAL` 하나뿐이고, 이것은 막다른 길의 복구 요청이다.

한도 2회의 적정값은 이 표본 하나로 정할 수 없으므로 유지하고, 잔여 blocker 판정 계약과 함께 이슈 #76 에서 재검토한다.

### D11. readiness 는 Spec 단계에만 도입한다

Plan 확장은 #70 2단계, eval·비용 측정은 3단계, Code 단계 readiness 는 #70 코멘트 1 이 남긴 후속 검토 항목이다. Plan 은 Spec 이 확정된 뒤 파생되므로 Spec 단계에서 계약이 안정된 다음에 같은 구조를 복제하는 편이 재작업이 적다.

### D12. strict-only 블록을 제거한 근거

이 산출물은 standard 모드이므로 `templates/spec.md` 의 strict 전용 블록(템플릿에서 strict-only 주석 쌍으로 감싼 구간)을 제거했다. 이 Spec 본문에는 그 주석 쌍이 남아 있지 않다. 제거한 여섯 소절이 이 작업에 적용되지 않는 이유는 다음과 같다.

- Threat and trust boundaries — 신뢰 경계를 넘는 입력이 없다. 두 Codex 프로세스는 모두 로컬 sandbox 안에서 이 저장소 파일만 읽고 쓴다.
- Authorization and tenant isolation — 권한 주체나 테넌트 개념이 없다. 단일 사용자의 로컬 개발 환경이다.
- Migration, compatibility, and rollback — 해당 내용은 D3 과 R6.4·R6.5, § Failure behavior 에 이미 실렸다. 데이터 마이그레이션이나 백필은 없다.
- Failure recovery and observability — 알림·메트릭·트레이스 대상이 되는 상시 실행 구성 요소가 없다. 복구 경로는 § Failure behavior 표가 전부 다룬다.
- High-risk end-to-end verification — 고위험 경로가 없다. 결정적 검증은 § Test strategy 판정 명령 표의 일곱 명령이다.
- No production mutation confirmation — 프로덕션 대상이 존재하지 않는다. 다만 배포본 `~/.claude/skills/quality-goal/` 을 이 작업이 갱신하지 않는다는 것은 § Security and risk 에 명시했다.

### D13. author 결과는 기존 `codex-result.schema.json` 으로 검증한다

- 대안 A: author 전용 결과 스키마를 신설한다.
- 대안 B(채택): 구현 라운드가 쓰는 `schemas/codex-result.schema.json` 을 그대로 쓴다.

근거: 그 스키마가 요구하는 것은 `changed_files`, 명령별 종료 코드와 결과, 계획 이탈, 잔여 우려이며 전부 문서 개정 작업에도 그대로 대응한다. author 는 `spec.md` 와 개정 노트 두 파일을 바꾸고(R1.7), 자기 검증으로 돌린 명령이 있으면 그것을 싣고, 조합 검토에서 남은 우려를 잔여 우려로 보고한다. 스키마를 하나 더 만들면 `--output-schema` 계약이 둘로 갈라져 R2.4 의 `const` 금지 같은 제약을 두 곳에서 관리해야 한다. 대신 R1.10 이 검증 실패 시의 경로를 명시한다.

### D14. R2.8 은 코드로 강제하되 schema v1 상태만 면제한다

- 대안 A: 서술로만 두고 오케스트레이터가 지킨다.
- 대안 B: 예외 없이 `record-review` 가 게이트 결과를 요구한다.
- 대안 C(채택): `record-review` 가 spec artifact 에 대해 게이트 결과를 요구하되, 상태에 readiness 필드가 아예 없으면 면제한다.

근거: 대안 A 는 D8 이 배격한 구조다. 게이트를 서술로 두면 오케스트레이터가 완화할 여지가 남는다. 대안 B 는 R6.4 의 하위 호환과 정면 충돌한다. 이 변경 이전에 시작해 `SPEC_REVIEW` 에 머물러 있는 goal 은 readiness 기록이 있을 수 없으므로, 예외가 없으면 재개하는 순간 공식 리뷰를 영영 기록하지 못한다. 대안 C 는 새 실행에는 강제를 걸고 진행 중 실행에는 걸지 않는다. 면제 조건을 "필드 부재"로 좁힌 이유는, 필드가 있는데 비어 있는 상태(새 실행의 첫 진입)까지 면제하면 강제가 무력해지기 때문이다.

