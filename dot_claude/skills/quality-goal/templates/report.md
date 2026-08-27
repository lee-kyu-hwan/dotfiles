# Quality Goal Report

- Task ID: {{TASK_ID}}
- Mode: {{MODE}}
- Status: {{STATUS}}
- Created: {{CREATED_AT}}
- Updated: {{UPDATED_AT}}
- Source goal: {{GOAL}}

## Classification

Record the selected mode and the concrete evidence-based reasons for that classification.

{{CLASSIFICATION}}

## Review history

Record each artifact’s review rounds, scores, verdicts, and the findings that changed between rounds.

{{REVIEW_HISTORY}}

## Blocking-finding resolutions

Record every blocking finding, the resolution applied, and the verification evidence that closed it.

{{BLOCKING_FINDING_RESOLUTIONS}}

## Plan approval

Record the plan approval timestamp and digest used for implementation.

- Approval timestamp: {{PLAN_APPROVAL_TIMESTAMP}}
- Plan digest: {{PLAN_DIGEST}}

## Changed files

List the changed files and summarize the intentional change in each.

{{CHANGED_FILES}}

## Verification evidence

Record EVERY actually executed command with its exit code and concise output evidence. If a verification category is missing or does not apply to the repository, record the missing verification category as `not configured` together with the repository evidence consulted (files checked); that category is never reported or marked as passed.

{{VERIFICATION_EVIDENCE}}

## Remaining advisory findings

Record remaining Medium or Low advisory findings, their impact, and any follow-up owner or action.

{{REMAINING_ADVISORY_FINDINGS}}

## Final status

Record `completed` or the stopped state, together with its machine-readable reason.

- Status: {{FINAL_STATUS}}
- Machine-readable reason: {{MACHINE_READABLE_REASON}}
