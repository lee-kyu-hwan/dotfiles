# Model Routing

## Route table

| Stage | Model | Effort |
|---|---|---|
| Claude orchestrator | inherit | high |
| Fresh reviewer | opus | high |
| Codex light+standard | gpt-5.6-terra | high |
| Codex strict | gpt-5.6-sol | high |
| Bounded redesign only | gpt-5.6-sol | xhigh |
| Spec author (standard) | gpt-5.6-terra | high |
| Spec author (strict) | gpt-5.6-sol | high |
| readiness reviewer (fresh) | gpt-5.6-sol | high |

The Sol/xhigh route applies only after a failed high-risk implementation or a `NEEDS_REDESIGN` diagnosis, and only for the bounded redesign task.

`model-routing.md` owns the role-specific model and effort values and runnable templates. `references/readiness-policy.md` cites those templates and owns the procedure context: when to invoke them, what the prompt contains, and how the result is recorded.

## Codex invocation

For implementation and fix rounds, use the selected exact model and effort in these variables; this is the only runnable template for implementation and fix rounds:

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

Check the exit code, then validate the result file against the schema. A rejected or unavailable model is recorded as `BLOCKED_MODEL_UNAVAILABLE`; silent fallback to another model is never allowed.

### author 호출 템플릿

`Spec author (standard)` 또는 `Spec author (strict)` 라우트에서 선택한 `$CODEX_MODEL`과 `$CODEX_EFFORT`를 사용한다. 이 블록이 author 호출 템플릿의 실행 가능한 정본이며, `references/readiness-policy.md`는 이를 인용해 절차 문맥만 정한다.

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

### readiness 호출 템플릿

`readiness reviewer (fresh)` 라우트에서 선택한 `$CODEX_MODEL`과 `$CODEX_EFFORT`를 사용한다. 이 블록이 readiness 호출 템플릿의 실행 가능한 정본이며, `references/readiness-policy.md`는 이를 인용해 절차 문맥만 정한다.

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

## Preflight

Before the first implementation invocation, preflight the exact selected model and verify that it responds. Use this separate preflight block with a one-line prompt:

```bash
codex exec \
  -C "$PROJECT_ROOT" \
  --sandbox read-only \
  --ephemeral \
  --model "$CODEX_MODEL" \
  -c "model_reasoning_effort=\"low\"" \
  "Reply with one non-empty line."
```

The `-c` setting is `model_reasoning_effort="low"`. Success means exit code 0 with a non-empty model reply. Because preflight establishes only that the selected model responds, it deliberately omits `--output-schema` and `--output-last-message`. A failed preflight follows the same unavailable-model recovery path.

## Recovery and state

`BLOCKED_MODEL_UNAVAILABLE` is a `status_reason` string, not a stage. On this status reason, show the failed command and the exact rejection, propose candidate substitute models, and proceed only with explicit user approval. While awaiting the user's substitution decision, the workflow remains in its current stage. Only when the user declines a substitute (or cannot be reached) does the orchestrator transition to the terminal `BLOCKED` stage with reason `BLOCKED_MODEL_UNAVAILABLE`. An approved substitution is recorded in the report, and the workflow continues in the current stage with the approved model.

Prompt, result, event, and stderr paths live only under the task state directory that the repository should ignore, `.claude/quality-state/<task-id>/`. Do not place them in durable project documents or another directory.

The flag `--skip-git-repo-check` is forbidden.

The flag `--full-auto` is forbidden.

The flag `--yolo` is forbidden.

Sandbox-bypass options are prohibited.
