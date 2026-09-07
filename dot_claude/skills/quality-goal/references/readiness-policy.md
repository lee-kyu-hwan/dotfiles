# Spec author 및 readiness 정책

`references/model-routing.md`가 역할별 모델·effort 값과 실행 가능한 호출 템플릿의 정본이다. 이 정책은 그 템플릿을 인용하고, 각 절차를 언제 실행하며 프롬프트에 무엇을 싣고 결과를 어떻게 기록하는지를 정한다.

## Spec author

standard 및 strict `SPEC_REVIEW`에서는 별도 Codex Spec author가 초안과 모든 개정을 작성한다. Claude 오케스트레이터는 Spec 본문을 직접 고치지 않는다. `references/model-routing.md`에서 `Spec author (standard)` 또는 `Spec author (strict)`를 선택한다. 라우트 표와 아래에서 인용한 호출 템플릿의 모델·effort 값은 그 파일이 정본이다.

### 호출 템플릿

실행 가능한 정본은 `references/model-routing.md`의 `### author 호출 템플릿`이다. 선택한 라우트의 모델과 effort를 사용하며, 프롬프트 파일은 표준 입력으로 전달한다.

```bash
codex exec \
  -C "$PROJECT_ROOT" \
  --sandbox workspace-write \
  --ephemeral \
  --model "$CODEX_MODEL" \
  -c "model_reasoning_effort=\"$CODEX_EFFORT\"" \
  --output-schema "$SKILL_DIR/schemas/codex-result.schema.json" \
  --output-last-message "$RESULT_PATH" \
  --json \
  - < "$PROMPT_PATH" > "$EVENTS_PATH" 2> "$STDERR_PATH"
```

### author 프롬프트

author 프롬프트에는 다음을 모두 넣는다.

- 작성하거나 개정할 Spec의 절대 경로, `/templates/spec.md`·`/references/spec-rubric.md`·`/references/brainstorming-policy.md`·`/references/revision-check-policy.md`의 절대 경로.
- 적용할 findings의 전체 경로. 기존 요구사항·AC 번호는 보존하고 새 번호는 뒤에 붙이며, `- **R<n>.<m>**`, `- **AC-<n>**`, `[실행]`/`[문서]`, 추적표, 판정 명령 표의 식별자 문법을 따른다.
- 발견 결과(문제, 목표, 비목표, 제약, 저장소 근거 경로). material ambiguity가 있으면 author 호출 전에 모두 사용자에게 묻는다.
- revision-note 경로, 이후 라운드의 필수 형식, git 쓰기 명령 금지, 완료 직전의 cross-regression 검토.

author는 revision-note에 `## 라운드 <n> 개정` 헤딩과 `references/revision-check-policy.md`의 정확한 헤더 `| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |`를 쓴다. 공식 라운드에는 이 절이 정확히 하나여야 한다. 새 행을 누적하고 판정이 바뀌면 그 행을 갱신한다. 범위는 readiness가 계기가 된 변경을 포함해 `snapshots/<artifact>-r<N-1>.md` 이후의 모든 변경이다.

cross-regression 검토는 모든 해소의 상호작용을 확인한다. `PLAN-009`, `PLAN-010`, `PLAN-012`, `SPEC-31`, `SPEC-34`는 국소적으로 맞는 편집도 충돌할 수 있음을 상기하는 사례다.

### 쓰기 범위와 실패 처리

author는 대상 Spec과 revision note만 쓸 수 있다. 호출 뒤 `initial_dirty_paths`와 `.claude/quality-state/<task-id>/`를 제외한 `git status --porcelain` 결과를 결과의 `changed_files` 목록과 비교한다. author가 허용 밖 파일을 수정했으면 그 변경을 되돌리지 않고 사용자에게 보고한 뒤 판단을 요청한다.

비정상 종료, 결과 파일 누락, 스키마 검증 실패, 또는 전후 artifact digest가 같게 남은 경우는 revision 실패로 처리한다. 현재 단계를 유지하고 실패를 보고하며 모델을 임의로 대체하지 않는다. author 실패를 보고할 때는 실패한 명령과 표준 오류 파일 경로를 함께 싣는다. 모델 거부 또는 부재는 기존 `BLOCKED_MODEL_UNAVAILABLE` 복구 경로를 따른다.

### 금지 Codex 옵션

codex-cli 0.153.4에서는 `--skip-git-repo-check`가 금지다.

codex-cli 0.153.4에서는 `--dangerously-bypass-approvals-and-sandbox`가 금지다.

codex-cli 0.153.4에서는 `--dangerously-bypass-hook-trust`가 금지다.

codex-cli 0.153.4에서는 `--approve-for-me`가 금지다.

codex-cli 0.153.4에서는 `--ignore-rules`가 금지다.

codex-cli 0.153.4에서는 `--ignore-user-config`가 금지다.

codex-cli 0.153.4에서는 `--add-dir`가 금지다.

codex-cli 0.153.4에서는 `--yolo`가 금지다. `codex exec --help`에 표시되지 않아도 허용되는 숨은 별칭이다.

템플릿보다 넓은 값을 `--sandbox`에 주는 것은 금지다. `codex exec`에는 `-a`/`--ask-for-approval` 옵션이 없으므로 어느 쪽도 쓰지 않는다.

## digest 대조

reviewer를 호출하기 전에 심사 대상 경로를 확정하고 등록 digest를 계산한다. 등록 digest는 `artifacts[artifact]`가 가리키는 파일의 현재 SHA-256이며, `artifact_digests`는 쓰지 않는다.

경로 불일치는 reviewer 호출 자체를 하지 않는 사전 중단이다.

경로가 일치하는 정상 경로에서 현재 SHA-256을 계산해 프롬프트에 싣고 심사 시점 digest로 기록한다.

digest 대조 실패는 SPEC_REVIEW 단계를 바꾸지 않고 사용자에게 보고한다.

심사 대상 경로 불일치는 SPEC_REVIEW 단계를 바꾸지 않고 사용자에게 보고한다.

## readiness reviewer

readiness reviewer는 author와 분리된 fresh Codex 프로세스다. author의 대화, 세션, 문맥, revision-note 주장을 상속하지 않는다. 그런 주장은 근거가 아니라 verification target이다. 정확한 모델·effort와 호출 템플릿은 `references/model-routing.md`의 `readiness reviewer (fresh)` 라우트와 `### readiness 호출 템플릿`에서 선택한다.

### 호출 템플릿

실행 가능한 정본은 `references/model-routing.md`의 `### readiness 호출 템플릿`이다. reviewer는 프롬프트 파일을 표준 입력으로 받는다.

```bash
codex exec \
  -C "$PROJECT_ROOT" \
  --sandbox read-only \
  --ephemeral \
  --model "$CODEX_MODEL" \
  -c "model_reasoning_effort=\"$CODEX_EFFORT\"" \
  --output-schema "$SKILL_DIR/schemas/readiness-result.schema.json" \
  --output-last-message "$RESULT_PATH" \
  --json \
  - < "$PROMPT_PATH" > "$EVENTS_PATH" 2> "$STDERR_PATH"
```

author와 readiness 호출은 모두 프롬프트 파일을 표준 입력으로 전달한다. 의도적인 명령행 프롬프트 변형에만 `< /dev/null`을 덧붙인다. 두 형태 모두 금지하지 않지만, 그 밖의 형태는 non-interactive infinite wait를 만들 수 있으므로 금지한다.

### reviewer 프롬프트와 근거

read-only 심사는 파일 수정과 git 쓰기 명령을 금지한다. 각 revision note를 `file:line` 근거와 대조한다. revision note는 근거가 아니라 verification target이며, design-preference deductions는 금지한다.

이 심사는 advisory이며 Claude의 official judgement를 대체하지 않고 공식 리뷰를 막지 않는다. 프롬프트에는 직전 readiness 결과 경로와 직전 공식 리뷰 open findings 경로를 넣고, 참조 finding마다 ID·severity·`required_resolution`을 읽을 수 있게 한다. 그 ID는 reference only이고 reviewer 자신의 finding은 `READY-` 접두로 발급한다. 이 경로 전달은 reviewer가 문맥을 상속하지 않는 규칙과 충돌하지 않는다.

score는 rubric weights로 계산한다. blocker가 있다고 0을 넣지 않는다.

`verified`가 true인 근거의 `location`은 `<path>:<line>`이어야 한다. `verified`가 false이면 `location`에 확인하지 못한 reason을 기록한다.

### finding 식별자

공식 finding과의 관계는 `description`에 기록한다. 하나의 revision cycle 안에서는 같은 물질적 문제에 같은 ID를 유지한다.

## 체크리스트

reviewer는 다음 여덟 항목을 각각 독립적으로 보고한다.

### C1

템플릿 절 구조 준수: `templates/spec.md`의 필수 절이 모두 존재하고 순서가 유지된다.

### C2

strict marker 쌍: 산출물에서 `templates/spec.md`의 두 HTML 주석 `<!-- strict-only:start -->`와 `<!-- strict-only:end -->`가 짝을 이루거나 non-strict 산출물에서 둘 다 없다. 한쪽만 남은 상태는 미충족이다.

### C3

요구사항 정의 수와 추적표 행 수가 같다.

### C4

추적표에 누락·중복·유령 참조가 0이다. 유령 참조는 추적표가 가리키는 요구사항 번호나 AC 번호가 본문에 정의되지 않은 경우다.

### C5

모든 AC에 판정 수단이 배정돼 있다. 판정 수단은 `[실행]` 명령 또는 `[문서]` 위치 중 하나다.

### C6

AC 번호가 연속이고 고유하다.

### C7

모든 `[실행]` 판정 명령이 판정 명령 표에 등재돼 있다.

### C8

프롬프트에 실린 직전 리뷰 findings 전문만 판정하고 상태 기록을 훑지 않는다. supplied target마다 `prior_findings` 항목을 정확히 하나 남긴다. `judgement`가 `partial`이면 미충족이다. 프롬프트에 findings가 없으면 `prior_findings`는 빈 배열이며 자동 충족이다. 참조 자리의 ID는 원 접두를 유지한다.

이 체크리스트에는 설계 정합성, 아키텍처 타당성, 시간축 development 판정을 넣지 않는다. 이 판단들은 Claude 공식 리뷰의 더 넓은 추론이 필요하다.

## readiness 지위

score는 record-only advisory 값이며 판정, 기록 거부, 상태 전이를 결정하는 데 쓰지 않는다. readiness는 어떤 상태 전이도 결정하지 않는다. readiness는 공식 리뷰의 시작 조건이 아니다. 결과가 `READY`이면 해당 라운드에서 readiness를 다시 시도하지 않는다. 다만 라운드당 시도 한도를 코드로 강제하지 않는다. 비용 상한은 오케스트레이터가 사용자 지시에 따라 정한다.

## 실패 보고

결과 스키마 검증 실패도 `SPEC_REVIEW`를 유지한 채 사용자에게 알린다. 결과 digest 불일치, 심사 대상 경로 불일치, 비정상 `codex exec` 종료, 결과 파일 누락, 타임아웃도 `SPEC_REVIEW`를 유지한 채 알린다. 뒤의 세 경우는 `--invocation-status failed`로 보낸다. 모델이 거부되거나 없으면 임의 대체하지 않고, 사용자가 대체 모델을 정하는 동안 현재 단계를 유지한다. 사용자가 거부하거나 응답할 수 없을 때만 `status_reason: BLOCKED_MODEL_UNAVAILABLE`로 `BLOCKED`로 전이한다.

## 근거 첨부

공식 리뷰 컨텍스트에는 저장소 근거 경로 둘을 첨부한다. 마지막 readiness 결과 JSON과 `.claude/quality-state/<task-id>/readiness-evidence-spec-r<N>.md`다. 보존 대상인 `SKILL.md`의 Review invocation contract가 리뷰 입력을 제한하므로 내용을 인라인하지 않는다. 첨부는 공식 reviewer의 judgement를 구속하지 않는다. 유효한 결과가 없으면 그 사실을 summary file에 기록한다.
