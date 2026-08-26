# Quality Goal Claude Code Orchestration Design

- Date: 2026-08-25
- Status: Approved by user on 2026-08-25
- Scope: A reusable, project-local Claude Code workflow that plans with Claude, implements with Codex, and repeats independent reviews until explicit quality gates pass

## 1. Purpose

`quality-goal` provides one manual entry point for software-development work:

```text
/quality-goal <goal>
/quality-goal --mode=light <goal>
/quality-goal --mode=standard <goal>
/quality-goal --mode=strict <goal>
```

The workflow classifies the task by risk and change surface, creates only the documentation appropriate to that class, obtains one implementation approval, delegates implementation to Codex, and repeats deterministic verification and independent Claude review within bounded limits.

The primary outcomes are:

1. Resolve ambiguous requirements before implementation.
2. Preserve the specification, plan, review decisions, and final verification as project documentation.
3. Keep the author, implementer, and reviewer roles separate.
4. Prevent a numeric score from overriding objective failures or unresolved high-severity findings.
5. Resume safely after a terminal or context interruption without repeating completed stages.

## 2. Goals and non-goals

### Goals

- Provide one user-facing skill instead of separate commands for each task size.
- Default to automatic routing while allowing an explicit mode override.
- Use brainstorming-style requirement discovery for work that needs a specification.
- Automatically review and revise Spec and Plan documents before requesting implementation approval.
- Require explicit user approval immediately before implementation.
- Use Codex as the implementation and revision worker.
- Use a fresh-context Claude reviewer for Spec, Plan, and code review.
- Run repository-defined tests, type checks, lint, and builds as deterministic gates.
- Keep durable human-readable documents separate from local machine state and raw review payloads.
- Bound all loops and produce an actionable stopped state instead of looping indefinitely.

### Non-goals

- Automatically decide unresolved product policy on the user's behalf.
- Modify the bundled `brainstorming` or `writing-plans` skills.
- Invoke bundled skills whose mandatory approval or handoff behavior conflicts with this workflow.
- Treat review score as the only measure of quality.
- Automatically push, merge, deploy, run production migrations, or expose credentials.
- Create parallel implementation workers in the same worktree.
- Replace repository CI or a human's final merge responsibility.

## 3. Key design decisions

1. **One public orchestrator:** expose only `/quality-goal` to the user.
2. **Modes are data, not duplicated skills:** use `auto`, `light`, `standard`, and `strict` routing inside the orchestrator.
3. **Responsibilities remain isolated:** use separate policy files, templates, deterministic scripts, and one read-only reviewer agent.
4. **Adapt, do not directly invoke, bundled workflows:** preserve the useful principles of brainstorming and detailed planning while implementing the agreed single approval gate.
5. **Risk precedes size:** a small authentication, authorization, payment, privacy, or migration change is `strict`.
6. **Hybrid gates:** require a score threshold, zero Critical/High findings, required sections, and successful deterministic checks.
7. **Project-local installation:** keep the workflow in `.claude/` so project conventions, documents, and verification remain versioned with the codebase.

## 4. Proposed project structure

```text
.claude/
├── agents/
│   └── quality-reviewer.md
├── skills/
│   └── quality-goal/
│       ├── SKILL.md
│       ├── references/
│       │   ├── brainstorming-policy.md
│       │   ├── planning-policy.md
│       │   ├── routing-rules.md
│       │   ├── spec-rubric.md
│       │   ├── plan-rubric.md
│       │   ├── code-rubric.md
│       │   └── model-routing.md
│       ├── templates/
│       │   ├── spec.md
│       │   ├── plan.md
│       │   └── report.md
│       ├── schemas/
│       │   └── review.schema.json
│       ├── scripts/
│       │   ├── quality_state.py
│       │   └── validate_review.py
│       └── evals/
│           └── evals.json
└── quality-state/                # Local runtime state; gitignored

docs/
└── development/
    └── YYYY-MM-DD-<task-slug>/
        ├── spec.md               # standard and strict
        ├── plan.md               # standard and strict
        └── report.md             # all modes
```

`SKILL.md` stays concise and contains the state-machine rules and navigation to supporting files. Detailed policies and rubrics are loaded only for the active stage. Python scripts use only the Python 3 standard library so the workflow does not introduce a package dependency.

## 5. Invocation contract

The skill is manually invoked and must declare `disable-model-invocation: true`. It must not start automatically when a normal coding request is made.

The optional first token is `--mode=auto|light|standard|strict`. If omitted, the mode is `auto`. All remaining input is the goal. An unknown mode is an input error and must not silently fall back to `auto`.

Examples:

```text
/quality-goal 파트너 전환 메뉴의 문구를 수정해줘
/quality-goal --mode=standard 파트너 다계정 전환 기능을 구현해줘
/quality-goal --mode=strict 결제 정산과 쿠폰 차감 로직을 변경해줘
```

An explicit mode may always raise the safety level. If the user explicitly selects a lower mode than the risk scan requires, the orchestrator explains the strict trigger and requires confirmation before accepting the downgrade. It never silently downgrades.

## 6. Automatic routing

Routing evaluates irreversible or high-impact risk first, then interface breadth and implementation size. File count is evidence, not the sole classifier.

### Light

Select `light` only when all conditions hold:

- The behavior change is localized and its expected result is unambiguous.
- No public API, persistent schema, cross-service contract, permission boundary, or production operation changes.
- No authentication, authorization, payment, settlement, coupon/points accounting, privacy, migration, destructive operation, or concurrency/idempotency impact.
- Existing targeted verification can demonstrate the change.

Examples include copy changes, a local presentation fix, or a small isolated defect with an existing regression-test location.

### Standard

Select `standard` when any of these apply and no strict trigger exists:

- Multiple files, modules, or application layers must change.
- A user flow, internal API, state transition, asynchronous process, or shared component changes.
- A new dependency or non-trivial interface is introduced.
- Requirements need alternatives, non-goals, or acceptance criteria to be made explicit.

### Strict

Select `strict` when any of these apply:

- Authentication, authorization, tenancy, roles, or cross-account data isolation.
- Payment, settlement, refund, coupon, points, or other money-adjacent accounting.
- Personally identifiable information, security controls, or secrets.
- Database/schema migration, data backfill, destructive operation, or difficult rollback.
- Public or external API compatibility, webhooks, queues, idempotency, or concurrency correctness.
- Production infrastructure or a failure mode with broad customer impact.

When classification is uncertain between two modes, select the higher mode. Before continuing, display the selected mode and concrete reasons.

## 7. Workflow by mode

### Light workflow

```text
INTAKE
→ CLASSIFIED
→ inspect repository context
→ present compact Plan in chat
→ AWAITING_PLAN_APPROVAL
→ Codex implementation
→ deterministic checks
→ fresh Claude code review
→ Codex fix loop when required
→ report.md
→ COMPLETED
```

Light work does not create separate Spec or Plan files. The compact Plan states intent, affected area, expected verification, and non-goals. Implementation cannot start until the user explicitly approves it.

### Standard workflow

```text
INTAKE
→ CLASSIFIED
→ brainstorming-style clarification
→ Spec draft
→ independent Spec review and revision
→ SPEC_PASSED
→ Plan draft
→ independent Plan review and revision
→ PLAN_PASSED
→ AWAITING_PLAN_APPROVAL
→ Codex implementation
→ deterministic checks
→ fresh Claude code review
→ Codex fix loop when required
→ report.md
→ COMPLETED
```

Clarifying questions remain allowed because they resolve missing requirements; they are not approval gates. There is no separate user approval after the automated Spec gate. The user approves the reviewed final Plan immediately before implementation.

### Strict workflow

Strict follows the standard workflow and adds mandatory sections and checks for:

- Threat and trust-boundary analysis.
- Authorization and tenant-isolation cases.
- Data migration, compatibility, and rollback strategy when applicable.
- Failure recovery and observability.
- End-to-end verification of the high-risk path.
- Explicit confirmation that no production mutation is part of the automated workflow.

Strict uses the same score threshold as standard. It raises quality by adding hard requirements rather than encouraging longer prose to reach a higher score.

## 8. Adapted brainstorming and planning policies

The installed bundled workflows are not called directly because their required human gates and implementation handoff differ from the agreed workflow.

`brainstorming-policy.md` retains these principles:

- Inspect existing repository conventions before proposing changes.
- Ask only materially necessary questions, one at a time.
- Compare two or three approaches for architectural decisions and recommend one.
- Define scope, non-goals, acceptance criteria, interfaces, error cases, and testability.
- Decompose a request that contains independent subsystems.
- Never begin implementation while requirements remain materially ambiguous.

`planning-policy.md` retains these principles:

- Trace every Spec acceptance criterion to an implementation task and verification step.
- Identify exact files and interface contracts when the repository makes them knowable.
- Break work into independently testable tasks without needless micro-steps.
- Use test-first implementation for behavior changes unless the approved Plan records a user-authorized exception.
- Include concrete commands and expected outcomes; do not use placeholders such as `TBD`, `TODO`, or “add appropriate tests.”
- Hand the approved Plan to Codex instead of asking the user to choose a Claude execution mode.

## 9. Durable documents

Each task uses `docs/development/YYYY-MM-DD-<task-slug>/`. If a directory already exists, append a deterministic numeric suffix.

### `spec.md`

Contains the problem, context, goals, non-goals, requirements, acceptance criteria, architecture, interfaces/data flow, failure behavior, security/risk considerations, and test strategy.

### `plan.md`

Contains the Spec link, global constraints, file map, task order, task dependencies, interfaces produced/consumed, test-first steps, exact verification commands, rollout/rollback handling, and an acceptance-criteria traceability table.

### `report.md`

Contains:

- Selected mode and classification reasons.
- Spec and Plan review scores by round.
- Blocking findings and how each was resolved.
- Plan approval timestamp.
- Changed files and implementation summary.
- Actual verification commands, exit results, and relevant evidence.
- Code-review rounds and resolutions.
- Remaining Medium/Low advisory findings.
- Final status and stopped-state reason when not completed.

Raw model prose and internal reasoning are not stored. The report keeps conclusions, evidence, and decisions needed by future developers.

## 10. Runtime state and resumability

Runtime files live under `.claude/quality-state/<task-id>/` and are ignored by Git:

```text
state.json
spec-review-01.json
spec-review-02.json
plan-review-01.json
plan-review-02.json
code-review-01.json
verification.json
```

`state.json` records the task ID, goal, mode, current stage, artifact paths, base Git revision when available, dirty-worktree summary, round counters, open finding IDs, verification status, and timestamps.

Allowed terminal states are:

- `COMPLETED`: all required gates passed.
- `BLOCKED`: missing information, unavailable command/model, permission failure, or invalid tool output prevents safe continuation.
- `NEEDS_REDESIGN`: a review limit was exceeded or the same material issue recurred twice.
- `CANCELLED`: the user stopped the task.

On reinvocation, the orchestrator searches for an incomplete matching task in the current worktree, summarizes its recorded state, and resumes from the last successfully completed transition. It does not regenerate a passed artifact or re-run an implementation step whose verification evidence is already valid for the unchanged revision.

## 11. Independent reviewer contract

`.claude/agents/quality-reviewer.md` defines a read-only reviewer. Each invocation starts in a fresh context and receives only:

- Artifact type: `spec`, `plan`, or `code`.
- Target artifact or code diff.
- The relevant rubric.
- Repository evidence needed to verify claims.
- Prior open finding IDs on follow-up rounds.

It does not receive the author's hidden reasoning and does not edit files. It returns JSON for the orchestrator to validate and persist.

Required result shape:

```json
{
  "artifact": "plan",
  "round": 2,
  "score": 87,
  "verdict": "PASS",
  "blockers": [],
  "findings": [],
  "evidence": [],
  "required_next_action": null
}
```

Every finding has a stable ID, severity, concise description, evidence location, violated rubric item, and required resolution. Unsupported opinions cannot block a gate.

Round 1 is a full review. Later rounds verify open findings and look for regressions introduced by revisions. A new blocking finding after Round 1 must be Critical/High and include evidence that it was newly introduced or could not reasonably have been identified earlier.

Malformed output is rejected by `validate_review.py` and retried once with the validation error. A second malformed output results in `BLOCKED`.

## 12. Scoring and gates

### Spec rubric: 100 points

- Problem, scope, and non-goals: 15
- Requirement clarity: 20
- Acceptance criteria and testability: 25
- Architecture, interfaces, and data flow: 20
- Feasibility, failure handling, and risk: 20

The Spec passes only when:

- Score is at least 85.
- Critical and High findings are zero.
- Required sections are present.
- Unresolved material decisions are zero.
- Every acceptance criterion is objectively verifiable.

### Plan rubric: 100 points

- Spec-to-task traceability: 25
- Task ordering, boundaries, and dependencies: 20
- File and interface precision: 15
- Tests and deterministic verification: 25
- Failure, rollout, rollback, and risk handling: 15

The Plan passes only when:

- Score is at least 85.
- Critical and High findings are zero.
- Every Spec acceptance criterion maps to an implementation task and verification step.
- Required file, interface, test, and rollback details are present when applicable.
- Placeholder text is absent.

### Code gate

The code-review score is recorded for observability but is not the sole pass condition. Code passes only when:

- All approved targeted and final verification commands exit successfully.
- Critical and High findings are zero.
- Spec acceptance criteria are met with evidence.
- No unrelated changes are included.
- Required documentation is updated.

Medium and Low findings are advisory unless the rubric identifies a specific acceptance-criteria violation. They remain visible in `report.md`.

## 13. Loop bounds

- Spec author/reviewer loop: maximum 2 review rounds.
- Plan author/reviewer loop: maximum 2 review rounds.
- Codex implementation/reviewer loop: maximum 3 review rounds.
- The same material finding recurring twice: stop as `NEEDS_REDESIGN`.
- A loop reaching its maximum without passing: stop as `NEEDS_REDESIGN`.

The workflow never lowers severity or changes a rubric merely to obtain a passing result.

## 14. Model routing

### Claude

- Orchestrator: `model: inherit`, `effort: high`.
- Reviewer: Claude Opus, `effort: high`, fresh subagent context on every round.

The orchestrator retains the interactive conversation and user decisions. The reviewer is isolated to reduce self-review bias.

### Codex

- `light` and `standard`: `gpt-5.6-terra`, reasoning effort `high`.
- `strict`: `gpt-5.6-sol`, reasoning effort `high`.
- Escalation after a failed high-risk implementation or a `NEEDS_REDESIGN` diagnosis: `gpt-5.6-sol`, reasoning effort `xhigh`, only for the bounded redesign task.

This routing follows the official OpenAI model positioning: Sol for complex reasoning and coding, and Terra for an intelligence/cost balance. If the selected model is unavailable to the authenticated subscription, the workflow reports `BLOCKED_MODEL_UNAVAILABLE`; it does not silently substitute a weaker model.

## 15. Codex implementation contract

Codex receives the approved Spec and Plan paths, the current task or bounded fix request, allowed change scope, repository instructions, verification commands, and required completion format.

Codex must:

- Work only in the current approved worktree.
- Preserve unrelated user changes.
- Follow the approved Plan and report any necessary deviation before broadening scope.
- Apply test-first development for behavior changes unless the approved Plan records an exception.
- Run targeted verification after each implementation task.
- Return changed files, commands executed, exit results, and remaining concerns.

The orchestrator runs final deterministic verification independently of Codex's summary. It never treats “tests should pass” as evidence.

The workflow reuses the user's existing authenticated Claude Code and Codex CLI subscriptions. It does not read, copy, print, or repurpose authentication tokens. It does not automatically commit, push, merge, deploy, or mutate production systems.

## 16. Deterministic verification

Verification commands are discovered from repository evidence such as `package.json`, workspace configuration, CI workflows, Makefiles, and project documentation. The Plan records the exact chosen commands before user approval.

The default verification order is:

1. Targeted tests for changed behavior.
2. Full relevant test suite.
3. Type checking.
4. Linting.
5. Build.
6. End-to-end or manual verification explicitly required by the Plan.

Only commands that apply to the repository are run. A missing category is recorded as “not configured” with evidence; it is not reported as passed. Strict work cannot pass when its required high-risk verification is absent unless the user explicitly approves a documented alternative before implementation.

## 17. Failure handling and safety

- **Dirty worktree:** record the initial state and never overwrite or revert unrelated changes.
- **Unclear requirement:** ask one focused question; do not invent product policy.
- **Invalid mode:** show valid syntax and stop without creating state.
- **Unavailable model or CLI:** enter `BLOCKED` with the failed command and recovery action.
- **Failed deterministic check:** return to Codex with the exact failure output; never ask the reviewer to waive it.
- **Review output schema failure:** retry once, then enter `BLOCKED`.
- **Loop exhaustion or recurring finding:** enter `NEEDS_REDESIGN` with the unresolved findings and recommended next decision.
- **User changes the approved scope:** return to Spec or Plan as appropriate, invalidate downstream evidence, and re-run affected gates.
- **Destructive or external action:** stop and request explicit authorization in the normal tool flow.

## 18. Skill evaluation strategy

Skill development follows a baseline-first evaluation cycle. Before writing the operational instructions, run representative fresh-context scenarios without the skill and record failures. Then run the same scenarios with the skill and compare behavior.

Minimum routing evaluations:

1. **Light:** “Change the partner-switch button copy and update its existing snapshot.”
2. **Standard:** “Add partner multi-account switching across the selector, session state, and API client.”
3. **Strict:** “Change authorization so sales admins can inspect partner coupon usage without exposing other partners' data.”

Additional pressure evaluations verify that the workflow:

- Does not implement before Plan approval.
- Does not let a score override a Critical/High finding.
- Stops after bounded review rounds.
- Resumes rather than recreating completed work.
- Rejects malformed reviewer JSON.
- Preserves unrelated dirty-worktree changes.

Deterministic script tests cover valid and invalid state transitions, review-schema validation, gate calculation, loop exhaustion, and resume selection.

Runtime claims must distinguish among:

- Structurally validated.
- Tested in a fixture repository.
- Tested end-to-end in Claude Code with authenticated Codex CLI.

The skill is not reported as fully verified unless the last category succeeds.

## 19. Rollout

1. Install as a project-local, manually invoked skill.
2. Validate on the three routing scenarios and one interrupted/resumed scenario.
3. Use it on five real tasks while retaining reports.
4. Recalibrate routing language or rubric weights only from observed false classifications or recurring low-value findings.
5. Consider team-wide packaging or CI integration only after the project-local workflow is stable.

## 20. Acceptance criteria

The implementation is complete when all of the following are demonstrated:

1. `/quality-goal <goal>` defaults to automatic routing and prints its mode with reasons.
2. Valid manual overrides work, invalid modes fail clearly, and risky downgrades require confirmation.
3. The public skill cannot be invoked automatically by Claude.
4. Light work creates a compact Plan approval gate and a durable report without separate Spec/Plan files.
5. Standard and strict work create `spec.md`, `plan.md`, and `report.md` in the documented task directory.
6. Spec and Plan reviews use a fresh, read-only Claude reviewer and schema-valid JSON.
7. Spec and Plan cannot pass below 85, with Critical/High findings, missing required sections, or incomplete traceability.
8. Only the reviewed final Plan requires user approval before standard/strict implementation.
9. Codex uses Terra/high for light/standard and Sol/high for strict, with no silent model downgrade.
10. Code cannot pass while a required deterministic command fails or a Critical/High finding remains.
11. Review loops stop at their configured limits and produce `NEEDS_REDESIGN` rather than continuing indefinitely.
12. Interrupted work resumes from recorded state without repeating an already valid completed stage.
13. The final report contains classification, approvals, review history, actual verification evidence, remaining advisory findings, and final status.
14. The workflow preserves unrelated changes and performs no automatic push, merge, deployment, production mutation, or credential extraction.
15. Baseline and with-skill evaluations cover light, standard, strict, approval pressure, malformed review output, and resume behavior.

## 21. References

- Claude Code Skills: https://code.claude.com/docs/ko/skills
- OpenAI model selection: https://developers.openai.com/api/docs/models
