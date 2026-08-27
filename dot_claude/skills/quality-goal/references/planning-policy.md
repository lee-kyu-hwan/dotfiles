# Planning Policy

This is the adapted planning policy for the quality-goal orchestrator. The bundled writing-plans skill must not be invoked or modified.

- Trace every Spec acceptance criterion to at least one implementation task and one verification step.
- Name exact files and interface contracts when knowable from repository evidence; otherwise state the boundary and the evidence still required.
- Break the work into independently testable tasks with clear ordering, dependencies, and completion evidence.
- Use test-first implementation for behavior changes unless the approved Plan records a user-authorized exception and its reason.
- Give every task concrete commands and expected outcomes, including deterministic checks, failure handling, and rollback or recovery actions.
- Plans must not contain unfinished-marker tokens (the two common all-caps markers) or vague placeholder phrasing such as "add appropriate tests"; every task names its actual commands and expected outcomes.
- Include a complete traceability table mapping each acceptance criterion to its implementation task, verification command or evidence, and expected outcome.
- Keep scope, non-goals, interfaces, error cases, and testability consistent with the approved Spec.
- Hand the approved Plan to Codex with the allowed files, interface contracts, verification commands, and rollback constraints.

An approved Plan is the implementation handoff. Missing file precision, unverifiable outcomes, absent failure handling, or an incomplete traceability table blocks that handoff.
