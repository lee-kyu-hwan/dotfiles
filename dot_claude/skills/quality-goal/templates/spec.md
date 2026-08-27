# Quality Goal Specification

- Task ID: {{TASK_ID}}
- Mode: {{MODE}}
- Status: {{STATUS}}
- Created: {{CREATED_AT}}
- Updated: {{UPDATED_AT}}
- Source goal: {{GOAL}}

## Problem and context

Describe the problem, relevant repository context, affected users, and evidence that motivates the work.

{{PROBLEM_AND_CONTEXT}}

## Goals

State the outcomes this work must achieve in terms that can be evaluated.

{{GOALS}}

## Non-goals

State explicitly what is out of scope so that scope does not expand during implementation.

{{NON_GOALS}}

## Requirements

List functional, operational, compatibility, and documentation requirements with enough precision to implement them.

{{REQUIREMENTS}}

## Acceptance criteria

Define every criterion so it is objectively verifiable and individually numbered.

{{ACCEPTANCE_CRITERIA}}

## Architecture

Describe the relevant components, responsibilities, boundaries, and decisions that make the design feasible.

{{ARCHITECTURE}}

## Interfaces and data flow

Describe inputs, outputs, contracts, state changes, and the flow between components or external systems.

{{INTERFACES_AND_DATA_FLOW}}

## Failure behavior

Describe expected failures, user-visible behavior, recovery, retries, and how failures are surfaced.

{{FAILURE_BEHAVIOR}}

## Security and risk

Describe security properties, trust assumptions, data sensitivity, risks, and mitigations relevant to the work.

{{SECURITY_AND_RISK}}

## Test strategy

Describe the tests and deterministic checks that will demonstrate the requirements and acceptance criteria.

{{TEST_STRATEGY}}

## Decisions

Record resolved decisions, alternatives considered, and the rationale needed by future implementers and reviewers.

{{DECISIONS}}

<!-- strict-only:start -->

This block is required only for strict work. Any inapplicable subsection must be removed for non-strict work; within strict work, mark it as not applicable with a reason before review.

### Threat and trust boundaries

Identify threats, trusted and untrusted actors, trust boundaries, and controls.

{{THREAT_AND_TRUST_BOUNDARIES}}

### Authorization and tenant isolation

Define authorization rules, tenant boundaries, and cases proving that data and actions remain isolated.

{{AUTHORIZATION_AND_TENANT_ISOLATION}}

### Migration, compatibility, and rollback

Describe migration or backfill steps, compatibility guarantees, rollback triggers, and rollback actions.

{{MIGRATION_COMPATIBILITY_AND_ROLLBACK}}

### Failure recovery and observability

Define recovery paths, alerts, logs, metrics, traces, and signals needed to detect and diagnose failures.

{{FAILURE_RECOVERY_AND_OBSERVABILITY}}

### High-risk end-to-end verification

Define the end-to-end verification required for the high-risk path, including evidence and stopping conditions.

{{HIGH_RISK_END_TO_END_VERIFICATION}}

### No production mutation confirmation

Explicitly confirm that no production mutation is part of the automated workflow.

{{NO_PRODUCTION_MUTATION_CONFIRMATION}}

<!-- strict-only:end -->
