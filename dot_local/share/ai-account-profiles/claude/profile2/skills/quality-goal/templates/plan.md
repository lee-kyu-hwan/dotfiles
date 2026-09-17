# Quality Goal Implementation Plan

- Task ID: {{TASK_ID}}
- Mode: {{MODE}}
- Status: {{STATUS}}
- Created: {{CREATED_AT}}
- Updated: {{UPDATED_AT}}
- Source goal: {{GOAL}}

## Spec link

Link the approved specification and identify the version or digest used by this plan.

{{SPEC_LINK}}

## Global constraints

List repository conventions, approved scope, safety constraints, and implementation rules that apply to every task.

{{GLOBAL_CONSTRAINTS}}

## File map

List each file to create, modify, or inspect, its responsibility, and the interface or behavior affected.

{{FILE_MAP}}

## Task dependencies

Describe task ordering, prerequisites, produced interfaces, consumed interfaces, and any dependency that affects parallel work.

{{TASK_DEPENDENCIES}}

## Tasks

For every task, use test-first ordering: record the failing verification, implement the smallest change, then record the passing verification. Include exact commands and expected outcomes for each step; do not use placeholder phrasing such as “add appropriate tests.”

{{TASKS}}

## Verification commands

List the exact repository commands to run, their order, and the expected successful outcome for each command.

{{VERIFICATION_COMMANDS}}

## Rollout and rollback

Describe rollout sequencing, monitoring, compatibility handling, rollback triggers, and concrete rollback steps.

{{ROLLOUT_AND_ROLLBACK}}

## Acceptance-criteria traceability

Map every acceptance criterion to the task that satisfies it and the verification command that proves its expected outcome.

| Criterion | Task | Verification command | Expected outcome |
|---|---|---|---|
| {{CRITERION}} | {{TASK}} | {{VERIFICATION_COMMAND}} | {{EXPECTED_OUTCOME}} |

Repeat the row once per acceptance criterion.

<!-- strict-only:start -->

This block is required only for strict work. Any inapplicable subsection must be removed for non-strict work; within strict work, mark it as not applicable with a reason before review.

### Threat and trust boundaries

List the strict-work threat and trust-boundary checks that implementation and verification must preserve.

{{PLAN_THREAT_AND_TRUST_BOUNDARIES}}

### Authorization and tenant isolation

Specify tenant-isolation test cases for allowed and denied access, including the exact verification commands and expected outcomes.

{{TENANT_ISOLATION_TEST_CASES}}

### Migration, compatibility, and rollback

Specify migration and rollback steps, compatibility checks, triggers, and evidence required before review.

{{MIGRATION_COMPATIBILITY_AND_ROLLBACK_STEPS}}

### Failure recovery and observability

Specify failure-recovery checks and the observability evidence required for the strict path.

{{PLAN_FAILURE_RECOVERY_AND_OBSERVABILITY}}

### High-risk end-to-end verification

Specify the required high-risk end-to-end verification, exact command, and expected evidence before review.

{{REQUIRED_HIGH_RISK_END_TO_END_VERIFICATION}}

### No production mutation confirmation

Explicitly confirm that no production mutation is part of the automated workflow.

{{PLAN_NO_PRODUCTION_MUTATION_CONFIRMATION}}

<!-- strict-only:end -->
