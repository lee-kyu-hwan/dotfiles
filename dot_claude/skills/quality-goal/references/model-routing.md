# Model Routing

## Route table

| Stage | Model | Effort |
|---|---|---|
| Claude orchestrator | inherit | high |
| Fresh reviewer | opus | high |
| Codex light+standard | gpt-5.6-terra | high |
| Codex strict | gpt-5.6-sol | high |
| Bounded redesign only | gpt-5.6-sol | xhigh |

The Sol/xhigh route applies only after a failed high-risk implementation or a `NEEDS_REDESIGN` diagnosis, and only for the bounded redesign task.

## Codex invocation

Use the selected exact model and effort in these variables; the command is the only runnable template:

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

## Recovery and state

`BLOCKED_MODEL_UNAVAILABLE` is a `status_reason` string, not a stage. On this status reason, show the failed command and the exact rejection, propose candidate substitute models, and proceed only with explicit user approval. While awaiting the user's substitution decision, the workflow remains in its current stage. Only when the user declines a substitute (or cannot be reached) does the orchestrator transition to the terminal `BLOCKED` stage with reason `BLOCKED_MODEL_UNAVAILABLE`. An approved substitution is recorded in the report, and the workflow continues in the current stage with the approved model.

Prompt, result, event, and stderr paths live only under the ignored task state directory `.claude/quality-state/<task-id>/`. Do not place them in durable project documents or another directory.

Before the first implementation invocation, preflight the exact selected model and verify that it responds. A failed preflight follows the same unavailable-model recovery path.

The flag `--skip-git-repo-check` is forbidden.

The flag `--full-auto` is forbidden.

The flag `--yolo` is forbidden.

Sandbox-bypass options are prohibited.
