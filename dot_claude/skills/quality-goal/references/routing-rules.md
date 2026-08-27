# Routing Rules

Use this ordered algorithm at intake. Risk takes precedence over implementation size; file count is evidence, not the classifier.

1. Parse the optional first token as `--mode=auto`, `--mode=light`, `--mode=standard`, or `--mode=strict`. If the value is unknown or invalid, show the valid syntax `--mode=auto|light|standard|strict`, reject the input, and stop without creating any state (no `.claude/quality-state/` directory); never fall back to `auto`.
2. Run the strict risk scan before any size estimation. Record each matching trigger and its concrete evidence.
3. Apply an explicit mode: an explicitly selected higher or equal mode is accepted. An explicitly selected lower mode must show the strict or higher-mode triggers and require user confirmation; never silently downgrade.
4. For `auto`, select `strict` when any strict trigger is present.
5. If no strict trigger exists, select `standard` when any standard condition is present; in `auto`, a cross-layer or interface change is standard. Select `light` only when all light conditions hold.
6. When classification is uncertain between two modes, select the higher mode.
7. Print the selected mode and concrete evidence before continuing to the next workflow stage.

## Strict triggers

Any one of these triggers selects `strict` in automatic routing:

- Authentication, authorization, tenancy, roles, or tenant isolation, including cross-account data isolation.
- Payment, settlement, refund, coupon, points, or other money-adjacent accounting.
- Personally identifiable information, security controls, or secrets.
- Database or schema migration, data backfill, destructive operation, or difficult rollback.
- Public or external API compatibility, webhooks, queues, idempotency, or concurrency correctness.
- Production infrastructure or a failure mode with broad customer impact.

## Light conditions

Select `light` only when all conditions hold:

- The behavior change is localized and its expected result is unambiguous.
- There is no public API, persistent schema, cross-service contract, permission boundary, or production operation change.
- There is no authentication, authorization, payment, settlement, coupon/points accounting, privacy, migration, destructive operation, or concurrency/idempotency impact.
- Existing targeted verification can demonstrate the change.
- No strict trigger applies, so light is permitted.

Typical light work includes copy changes, a local presentation fix, or a small isolated defect with an existing targeted verification location.

## Standard conditions

When no strict trigger exists, select `standard` if any of these applies:

- Multiple files, modules, or layers must change.
- A user flow, internal API, state transition, async or asynchronous process, or shared component changes.
- A new dependency or non-trivial interface is introduced.
- The requirements need alternatives, non-goals, or acceptance criteria to be made explicit.

Examples:

- Adding partner multi-account switching across the selector, session state, and API client is standard because it crosses a user flow, multiple layers, and an internal interface.
- Changing authorization so sales admins can inspect partner coupon usage without exposing other partners' data is strict because it changes authorization, tenant isolation, and coupon usage accounting.

The routing result is evidence-based: after classification, state the mode, every relevant trigger or condition, and the reason that evidence satisfies the selected mode before proceeding.
