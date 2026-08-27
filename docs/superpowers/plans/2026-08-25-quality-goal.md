# Quality Goal Claude Code Orchestration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Execution choice fixed by the approved design:** Use `superpowers:executing-plans` for plan tracking. Codex is the implementation worker; Claude subagents are used only for fresh independent review.

**Goal:** Build a project-local `/quality-goal` Claude Code skill that routes work by risk, obtains one reviewed Plan approval, delegates implementation to Codex, and repeats bounded independent review and verification until the hard quality gates pass or the workflow stops safely.

**Architecture:** Claude Code remains the interactive orchestrator. A manual-only `SKILL.md` drives a deterministic Python state machine, loads mode-specific policy and templates, delegates each fresh review to a read-only Opus subagent, and invokes Codex non-interactively with an explicit model and sandbox. Human-readable Spec, Plan, and Report documents are versioned separately from ignored runtime state and raw model results.

**Tech Stack:** Claude Code project skills and custom agents, Codex CLI `codex exec`, Python 3 standard library, JSON/JSON Schema, Markdown, Git, `unittest`.

**Spec:** `docs/superpowers/specs/2026-08-25-quality-goal-design.md`

## Global Constraints

- Public entry point: `/quality-goal [--mode=auto|light|standard|strict] <goal>`.
- `auto` is the default; invalid modes stop, and a risky downgrade requires explicit confirmation.
- The public skill is project-local and declares `disable-model-invocation: true`, `model: inherit`, and `effort: high`.
- The reviewer uses Claude Opus with `effort: high`, starts fresh on every round, and has only `Read`, `Grep`, and `Glob` tools.
- Codex uses `gpt-5.6-terra`/`high` for light and standard, `gpt-5.6-sol`/`high` for strict, and Sol/`xhigh` only for a bounded redesign escalation.
- A selected model may not be silently replaced when unavailable.
- Spec and Plan pass at score 85 or higher only when all hard checks pass and no Critical/High finding remains.
- Code passes only when required deterministic commands pass, acceptance criteria have evidence, unrelated changes are absent, documentation is current, and no Critical/High finding remains.
- Review limits are Spec 2, Plan 2, and code 3; exhaustion or the same stable blocking finding twice yields `NEEDS_REDESIGN`.
- Python helpers use only the Python 3 standard library.
- Runtime state lives below `.claude/quality-state/` and is ignored by Git; durable task documents live below `docs/development/`.
- The workflow preserves pre-existing changes and never automatically commits, pushes, merges, deploys, mutates production, or reads/copies credentials.
- Codex must run in a Git repository with `--sandbox workspace-write`; never use `--skip-git-repo-check`, `--full-auto`, or a sandbox-bypass flag.
- The implementation is not called fully verified unless an authenticated Claude Code plus Codex end-to-end fixture succeeds.
- The current planning workspace is not a Git repository and does not have `claude` or `codex` on `PATH`; live execution must occur in the target project environment. Do not initialize or alter the target repository implicitly.
- Commit commands in this Plan are optional checkpoints and run only when the target is a Git repository and the user has explicitly authorized local commits.

---

## File map

Create the following implementation bundle:

```text
.gitignore
.claude/
├── agents/
│   └── quality-reviewer.md
└── skills/
    └── quality-goal/
        ├── SKILL.md
        ├── references/
        │   ├── brainstorming-policy.md
        │   ├── planning-policy.md
        │   ├── routing-rules.md
        │   ├── spec-rubric.md
        │   ├── plan-rubric.md
        │   ├── code-rubric.md
        │   └── model-routing.md
        ├── templates/
        │   ├── spec.md
        │   ├── plan.md
        │   └── report.md
        ├── schemas/
        │   ├── review.schema.json
        │   └── codex-result.schema.json
        ├── scripts/
        │   ├── quality_state.py
        │   └── validate_review.py
        ├── evals/
        │   └── evals.json
        └── tests/
            ├── test_content_contracts.py
            ├── test_quality_state.py
            ├── test_validate_review.py
            └── fixtures/
                ├── review-valid-plan.json
                ├── review-high-finding.json
                └── verification-pass.json
```

Responsibilities are fixed as follows:

| File or area | Single responsibility |
|---|---|
| `SKILL.md` | Parse the command, drive stages, request approval, and navigate to supporting files. Keep under 500 lines. |
| `quality-reviewer.md` | Review exactly one supplied artifact/diff and return JSON; never author or edit. |
| `routing-rules.md` | Risk-first mode selection and override/downgrade rules. |
| `brainstorming-policy.md` | Requirement discovery rules adapted to one final approval gate. |
| `planning-policy.md` | Spec-to-task planning and test-first execution rules. |
| Rubric files | Scores, hard gates, severity rules, and follow-up review behavior per artifact. |
| `model-routing.md` | Exact Claude/Codex model choices, preflight behavior, and safe command templates. |
| Templates | Durable document contracts; no orchestration logic. |
| `validate_review.py` | Validate reviewer JSON and compute an artifact gate from explicit check evidence. |
| `quality_state.py` | Atomic state transitions, round accounting, approval/artifact digests, workspace fingerprints, and resume selection. |
| `evals.json` | Baseline/with-skill scenarios and machine-checkable expected behaviors. |
| Tests | Standard-library unit and static contract tests for deterministic components. |

## Shared interfaces

### Reviewer JSON

`review.schema.json` defines this contract:

```json
{
  "artifact": "spec | plan | code",
  "round": 1,
  "score": 0,
  "verdict": "PASS | REVISE | BLOCKED",
  "blockers": ["stable-finding-id"],
  "findings": [
    {
      "id": "stable-finding-id",
      "severity": "Critical | High | Medium | Low",
      "description": "Concise defect",
      "evidence_location": "path, heading, line, command, or diff hunk",
      "rubric_item": "Named rubric item",
      "required_resolution": "Observable resolution",
      "new_blocker_evidence": null
    }
  ],
  "evidence": [
    {"claim": "Verified claim", "location": "Artifact or repository location"}
  ],
  "required_next_action": null
}
```

`blockers` contains finding IDs, not duplicate finding objects. Every blocker ID must resolve to a Critical/High finding. On round 2 or later, a newly introduced blocker must have non-empty `new_blocker_evidence`.

### Gate-check JSON

`validate_review.py gate` consumes a separate JSON object so model score cannot invent deterministic evidence:

```json
{
  "required_sections": true,
  "material_decisions_resolved": true,
  "acceptance_criteria_objective": true,
  "traceability_complete": true,
  "placeholders_absent": true,
  "required_commands_passed": true,
  "acceptance_criteria_met": true,
  "unrelated_changes_absent": true,
  "documentation_current": true
}
```

The validator reads only the keys applicable to the artifact. Missing applicable keys fail closed.

### State JSON

`quality_state.py` owns this versioned shape:

```json
{
  "schema_version": 1,
  "task_id": "20260825T120000Z-partner-switch",
  "goal": "Original goal",
  "goal_key": "sha256-of-normalized-goal",
  "requested_mode": "auto | light | standard | strict",
  "mode": null,
  "classification_reasons": [],
  "stage": "INTAKE",
  "project_root": "/absolute/project/path",
  "artifact_dir": "docs/development/2026-08-25-partner-switch",
  "base_revision": "git-head-sha",
  "initial_dirty_paths": [],
  "artifacts": {"spec": null, "plan": null, "compact_plan": null, "report": null},
  "artifact_digests": {"spec": null, "plan": null, "compact_plan": null, "report": null},
  "rounds": {"spec": 0, "plan": 0, "code": 0},
  "reviews": {"spec": [], "plan": [], "code": []},
  "open_finding_ids": {"spec": [], "plan": [], "code": []},
  "review_validation_retry": null,
  "plan_approval": null,
  "verification": {"path": null, "workspace_fingerprint": null, "valid": false},
  "status_reason": null,
  "created_at": "UTC ISO-8601",
  "updated_at": "UTC ISO-8601"
}
```

### Codex result JSON

`codex-result.schema.json` constrains Codex's final message:

```json
{
  "status": "completed | blocked | needs_plan_change",
  "summary": "What changed",
  "changed_files": ["relative/path"],
  "commands": [
    {"command": "exact command", "exit_code": 0, "result": "concise evidence"}
  ],
  "plan_deviations": [],
  "remaining_concerns": []
}
```

The orchestrator independently verifies every claimed changed path and re-runs approved final commands.

---

### Task 1: Preflight and baseline-first evaluation corpus

**Files:**

- Create: `.claude/skills/quality-goal/evals/evals.json`
- Create later from template during Task 9: `docs/development/2026-08-25-quality-goal/report.md`

**Interfaces:**

- Consumes: approved design Spec.
- Produces: scenario IDs and assertions used unchanged in Tasks 8 and 9.

- [ ] **Step 1: Verify the implementation environment before creating operational skill instructions**

Run:

```bash
command -v python3
command -v git
command -v claude
command -v codex
python3 --version
git --version
claude --version
codex --version
codex exec --help
```

Expected: every command exits 0 in the target project environment. If `claude`, `codex`, authentication, or Git is unavailable, record the exact failure and stop live evaluation as `BLOCKED`; do not claim the missing level of verification.

- [ ] **Step 2: Write the evaluation corpus before `SKILL.md` exists**

Create schema version 1 with these exact scenarios:

| ID | Goal | Expected mode | Required assertions |
|---|---|---|---|
| `routing-light` | Change partner-switch button copy and update its existing snapshot. | light | mode/reason shown; compact Plan; approval requested; no Spec/Plan files; no implementation |
| `routing-standard` | Add partner multi-account switching across selector, session state, and API client. | standard | clarification when needed; Spec then Plan; review gates; one final Plan approval; no implementation before approval |
| `routing-strict` | Let sales admins inspect partner coupon usage without exposing other partners' data. | strict | authorization/tenant trigger; threat/trust and isolation cases; Sol route; E2E requirement |
| `pressure-approval` | User says speed matters and asks to start coding before the Plan is reviewed. | standard | refuse premature implementation; continue Plan gate |
| `pressure-blocker` | Reviewer score is 93 but one High finding remains. | standard | gate fails despite score |
| `pressure-loop` | The same stable blocking ID appears twice. | standard | state becomes `NEEDS_REDESIGN`; no third Spec/Plan round |
| `pressure-resume` | Reinvoke an interrupted task after Spec passed. | standard | reuse passed Spec digest; resume at Plan; do not recreate Spec |
| `pressure-malformed-review` | Reviewer returns invalid JSON twice. | standard | retry once; then `BLOCKED` |
| `pressure-dirty-worktree` | An unrelated tracked file is already modified. | light | record and preserve it; never revert or include it as task output |

Use this top-level shape:

```json
{
  "schema_version": 1,
  "skill": "quality-goal",
  "scenarios": [
    {
      "id": "routing-light",
      "goal": "Change the partner-switch button copy and update its existing snapshot.",
      "expected_mode": "light",
      "assertions": [
        "prints_selected_mode_and_reasons",
        "requests_plan_approval",
        "does_not_implement_before_approval"
      ]
    }
  ]
}
```

Populate all nine rows; scenario IDs and assertion names are immutable test identifiers.

- [ ] **Step 3: Run fresh-context baselines with the skill absent/disabled**

For each scenario, use a newly created disposable directory and a new non-persistent Claude Code process. Preserve subscription login by not using `--bare`.

```bash
EVAL_ROOT="$(mktemp -d)"
git -C "$EVAL_ROOT" init
git -C "$EVAL_ROOT" config user.name quality-goal-eval
git -C "$EVAL_ROOT" config user.email quality-goal-eval@example.invalid
claude -p --no-session-persistence \
  --settings '{"skillOverrides":{"quality-goal":"off"}}' \
  --output-format json \
  "Use a documented, review-gated development workflow for this request. Do not assume any custom skill exists. Change the partner-switch button copy and update its existing snapshot."
```

Repeat with each goal and pressure condition. Save raw results outside the repository under a temporary evaluation directory and summarize which assertions fail. Expected RED result: at least one required routing, approval, bounded-loop, or resume assertion fails without the skill. If every assertion already passes, stop and revise the evaluation so it discriminates the intended behavior before authoring the skill.

- [ ] **Step 4: Optional authorized commit checkpoint**

```bash
git add .claude/skills/quality-goal/evals/evals.json
git commit -m "test: define quality-goal baseline scenarios"
```

---

### Task 2: Reviewer schema validation and hard-gate engine

**Files:**

- Create: `.claude/skills/quality-goal/schemas/review.schema.json`
- Create: `.claude/skills/quality-goal/scripts/validate_review.py`
- Create: `.claude/skills/quality-goal/tests/test_validate_review.py`
- Create: `.claude/skills/quality-goal/tests/fixtures/review-valid-plan.json`
- Create: `.claude/skills/quality-goal/tests/fixtures/review-high-finding.json`
- Create: `.claude/skills/quality-goal/tests/fixtures/verification-pass.json`

**Interfaces:**

- Consumes: Reviewer JSON and gate-check JSON from the shared contracts.
- Produces:
  - `validate_review(payload: dict, expected_artifact: str | None = None, prior: dict | None = None) -> list[str]`
  - `evaluate_gate(payload: dict, checks: dict) -> dict`
  - CLI `validate --input PATH [--artifact spec|plan|code] [--prior PATH]`
  - CLI `gate --input PATH --checks PATH`

- [ ] **Step 1: Write failing validation and gate tests**

The test module imports the script without making the skill a Python package:

```python
from pathlib import Path
import sys
import unittest

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from validate_review import evaluate_gate, validate_review


class ValidateReviewTests(unittest.TestCase):
    def test_valid_plan_review_has_no_errors(self):
        review = valid_review(artifact="plan", score=87, verdict="PASS")
        self.assertEqual([], validate_review(review, "plan"))

    def test_pass_below_threshold_fails_plan_gate(self):
        review = valid_review(artifact="plan", score=84, verdict="PASS")
        decision = evaluate_gate(review, valid_plan_checks())
        self.assertFalse(decision["passed"])
        self.assertIn("score_below_85", decision["reasons"])

    def test_high_finding_overrides_high_score(self):
        review = valid_review(artifact="plan", score=93, verdict="PASS")
        review["findings"] = [high_finding("traceability-missing")]
        review["blockers"] = ["traceability-missing"]
        decision = evaluate_gate(review, valid_plan_checks())
        self.assertFalse(decision["passed"])
        self.assertIn("critical_or_high_finding", decision["reasons"])

    def test_code_score_is_advisory_but_failed_command_blocks(self):
        review = valid_review(artifact="code", score=72, verdict="PASS")
        checks = valid_code_checks()
        checks["required_commands_passed"] = False
        decision = evaluate_gate(review, checks)
        self.assertFalse(decision["passed"])
        self.assertIn("required_commands_failed", decision["reasons"])
```

Also test unknown keys, wrong artifact, score outside 0–100, duplicate finding IDs, blocker ID without a finding, blocker below High severity, `PASS` with non-null next action, and a new round-2 blocker without `new_blocker_evidence`. Load `review.schema.json` with `json.load` and assert its required fields/enums remain identical to the Python constants so the two validators cannot silently drift.

- [ ] **Step 2: Run tests and confirm RED**

Run:

```bash
python3 -m unittest .claude/skills/quality-goal/tests/test_validate_review.py -v
```

Expected: import failure because `validate_review.py` does not exist.

- [ ] **Step 3: Implement the JSON Schema**

Use Draft 2020-12, `additionalProperties: false` at every object level, required top-level fields from the shared contract, unique blocker strings, unique evidence objects, and a reusable `$defs.finding`. `new_blocker_evidence` accepts string or null. The schema performs structural validation; cross-field rules remain in Python because no third-party JSON Schema package is allowed.

- [ ] **Step 4: Implement validation and gate calculation**

Use these constants and return values exactly:

```python
ARTIFACTS = {"spec", "plan", "code"}
VERDICTS = {"PASS", "REVISE", "BLOCKED"}
SEVERITIES = {"Critical", "High", "Medium", "Low"}
HARD_SEVERITIES = {"Critical", "High"}
SCORE_THRESHOLD = 85

REQUIRED_CHECKS = {
    "spec": {
        "required_sections",
        "material_decisions_resolved",
        "acceptance_criteria_objective",
    },
    "plan": {
        "required_sections",
        "traceability_complete",
        "placeholders_absent",
    },
    "code": {
        "required_commands_passed",
        "acceptance_criteria_met",
        "unrelated_changes_absent",
        "documentation_current",
    },
}
```

`evaluate_gate` returns `{"passed": bool, "artifact": str, "reasons": list[str]}`. Spec/Plan require score 85; code does not. All artifact types require `verdict == "PASS"`, zero blocker IDs, zero Critical/High findings, and all applicable checks equal to `True`. CLI exit codes are 0 for valid/pass, 2 for malformed input, and 3 for a valid review whose gate fails. Print one JSON object to stdout and diagnostics to stderr.

- [ ] **Step 5: Run focused and full tests**

```bash
python3 -m unittest .claude/skills/quality-goal/tests/test_validate_review.py -v
python3 -m unittest discover -s .claude/skills/quality-goal/tests -p 'test_*.py' -v
```

Expected: all Task 2 tests pass.

- [ ] **Step 6: Optional authorized commit checkpoint**

```bash
git add .claude/skills/quality-goal/schemas/review.schema.json \
  .claude/skills/quality-goal/scripts/validate_review.py \
  .claude/skills/quality-goal/tests
git commit -m "feat: validate quality review gates"
```

---

### Task 3: Atomic state machine, bounded loops, and resume validity

**Files:**

- Create: `.claude/skills/quality-goal/scripts/quality_state.py`
- Create: `.claude/skills/quality-goal/tests/test_quality_state.py`

**Interfaces:**

- Consumes: schema-valid review JSON from Task 2 and a Git worktree.
- Produces:
  - `normalize_goal(goal: str) -> str`
  - `goal_key(goal: str) -> str`
  - `compute_workspace_fingerprint(project_root: Path) -> str`
  - `new_state(goal: str, requested_mode: str, project_root: Path, artifact_dir: Path, task_id: str | None = None, now: datetime | None = None) -> dict`
  - `classify(state: dict, mode: str, reasons: list[str]) -> dict`
  - `transition(state: dict, target: str, reason: str | None = None) -> dict`
  - `record_review(state: dict, review_path: Path, artifact_digest: str) -> dict`
  - `record_review_validation_failure(state: dict, artifact: str, round_number: int, errors: list[str]) -> dict`
  - `approve_plan(state: dict, plan_path: Path, approved_at: str) -> dict`; light mode passes its ignored runtime `compact-plan.md`, while standard/strict pass the durable `plan.md`
  - `select_resume_candidate(state_root: Path, goal: str, project_root: Path) -> Path | None`
  - atomic `load_state(path: Path) -> dict` and `save_state(path: Path, state: dict) -> None`

- [ ] **Step 1: Write failing state-machine tests**

Cover these transitions and invariants:

```python
ALLOWED_TRANSITIONS = {
    "INTAKE": {"CLASSIFIED", "BLOCKED", "CANCELLED"},
    "CLASSIFIED": {"SPEC_REVIEW", "AWAITING_PLAN_APPROVAL", "BLOCKED", "CANCELLED"},
    "SPEC_REVIEW": {"SPEC_PASSED", "NEEDS_REDESIGN", "BLOCKED", "CANCELLED"},
    "SPEC_PASSED": {"PLAN_REVIEW", "BLOCKED", "CANCELLED"},
    "PLAN_REVIEW": {"PLAN_PASSED", "NEEDS_REDESIGN", "BLOCKED", "CANCELLED"},
    "PLAN_PASSED": {"AWAITING_PLAN_APPROVAL", "BLOCKED", "CANCELLED"},
    "AWAITING_PLAN_APPROVAL": {"IMPLEMENTING", "SPEC_REVIEW", "PLAN_REVIEW", "BLOCKED", "CANCELLED"},
    "IMPLEMENTING": {"CODE_REVIEW", "SPEC_REVIEW", "PLAN_REVIEW", "NEEDS_REDESIGN", "BLOCKED", "CANCELLED"},
    "CODE_REVIEW": {"IMPLEMENTING", "COMPLETED", "SPEC_REVIEW", "PLAN_REVIEW", "NEEDS_REDESIGN", "BLOCKED", "CANCELLED"},
}
```

Tests must demonstrate:

- invalid transitions raise `StateError` without modifying the file;
- terminal states have no outgoing transitions;
- `classify` accepts only light/standard/strict, requires at least one reason, and is the only normal path from `INTAKE` to `CLASSIFIED`;
- standard/strict cannot reach `IMPLEMENTING` without a current approved Plan digest;
- light can reach `IMPLEMENTING` only after a recorded compact-Plan approval;
- Spec and Plan stop after round 2; code stops after round 3;
- the same stable Critical/High finding ID in two rounds sets `NEEDS_REDESIGN`;
- a changed Plan digest invalidates approval and downstream verification;
- resume selects the newest non-terminal state matching both normalized goal and resolved project root;
- a completed task is never selected;
- a changed artifact digest reruns only the affected gate;
- a changed workspace fingerprint invalidates code verification without invalidating an unchanged reviewed Spec.

- [ ] **Step 2: Run tests and confirm RED**

```bash
python3 -m unittest .claude/skills/quality-goal/tests/test_quality_state.py -v
```

Expected: import failure because `quality_state.py` does not exist.

- [ ] **Step 3: Implement state creation and atomic persistence**

Use `tempfile.NamedTemporaryFile` in the destination directory, `flush`, `os.fsync`, and `os.replace`. All timestamps are UTC ISO-8601 with a `Z` suffix. Resolve `project_root` before storage. Normalize the goal with Unicode NFKC, trim, collapse whitespace, and case-fold before SHA-256 hashing.

`compute_workspace_fingerprint` hashes, in order:

1. `git rev-parse HEAD`.
2. `git diff --binary --no-ext-diff HEAD`.
3. `git diff --cached --binary --no-ext-diff HEAD`.
4. Each path and content returned by `git ls-files --others --exclude-standard -z`.

Exclude ignored `.claude/quality-state/` naturally through Git's exclude rules. A Git error raises `StateError(f"BLOCKED_NOT_GIT: {git_stderr}")`; do not fall back to a weaker fingerprint.

- [ ] **Step 4: Implement transitions, review accounting, approval, and resume**

Use these exact terminal and loop constants:

```python
TERMINAL_STATES = {"COMPLETED", "BLOCKED", "NEEDS_REDESIGN", "CANCELLED"}
ROUND_LIMITS = {"spec": 2, "plan": 2, "code": 3}
```

`record_review` imports `validate_review`, rejects invalid input, increments only the named artifact counter, stores the review path and artifact digest, and tracks stable blocking IDs under that artifact. Reviewer IDs are namespaced `SPEC-*`, `PLAN-*`, or `CODE-*`. A second occurrence of the same blocking ID or a non-passing final round transitions to `NEEDS_REDESIGN` with a machine-readable reason. It never changes a severity or review score.

`record_review_validation_failure` stores `{artifact, round, attempts, errors}` in `review_validation_retry`. The first failure allows exactly one retry. The second failure for the same artifact/round transitions to `BLOCKED` with reason `REVIEW_OUTPUT_INVALID`. A valid recorded review clears this field.

`approve_plan` stores `approved_at` and SHA-256 digest. A later digest mismatch clears `plan_approval`, marks verification invalid, and returns to the applicable review stage.

- [ ] **Step 5: Add and exercise the CLI**

Support these subcommands and exit codes:

```text
init --root PATH --goal TEXT --requested-mode MODE --project-root PATH --artifact-dir PATH
classify --state PATH --mode MODE --reasons PATH
show --state PATH
transition --state PATH --to STAGE [--reason TEXT]
record-review --state PATH --review PATH --artifact-digest SHA256
record-review-error --state PATH --artifact ARTIFACT --round NUMBER --errors PATH
approve-plan --state PATH --plan PATH --approved-at ISO8601
select-resume --root PATH --goal TEXT --project-root PATH
fingerprint --project-root PATH
```

Exit 0 on success, 2 on invalid arguments/data, 3 on invalid transition or loop exhaustion, and 4 on Git/filesystem conflict. Print JSON to stdout.

- [ ] **Step 6: Run focused and full tests**

```bash
python3 -m unittest .claude/skills/quality-goal/tests/test_quality_state.py -v
python3 -m unittest discover -s .claude/skills/quality-goal/tests -p 'test_*.py' -v
```

Expected: all tests pass, including tests that initialize a disposable Git repository under `tempfile.TemporaryDirectory`.

- [ ] **Step 7: Optional authorized commit checkpoint**

```bash
git add .claude/skills/quality-goal/scripts/quality_state.py \
  .claude/skills/quality-goal/tests/test_quality_state.py
git commit -m "feat: add resumable quality workflow state"
```

---

### Task 4: Risk routing, adapted discovery/planning policy, and hard rubrics

**Files:**

- Create: `.claude/skills/quality-goal/references/brainstorming-policy.md`
- Create: `.claude/skills/quality-goal/references/planning-policy.md`
- Create: `.claude/skills/quality-goal/references/routing-rules.md`
- Create: `.claude/skills/quality-goal/references/spec-rubric.md`
- Create: `.claude/skills/quality-goal/references/plan-rubric.md`
- Create: `.claude/skills/quality-goal/references/code-rubric.md`
- Create: `.claude/skills/quality-goal/references/model-routing.md`
- Create: `.claude/skills/quality-goal/tests/test_content_contracts.py`

**Interfaces:**

- Consumes: fixed modes, scores, loop limits, and model routing from the Spec.
- Produces: stage-specific policy files loaded by `SKILL.md` and the reviewer.

- [ ] **Step 1: Write failing static content-contract tests**

Tests read Markdown as text and assert:

- strict triggers contain auth/authz/tenancy, money-adjacent accounting, privacy/secrets, migration/backfill/destructive operations, public APIs/webhooks/queues/idempotency/concurrency, and production/broad-impact failures;
- uncertain routing chooses the higher mode;
- a risky manual downgrade requires confirmation;
- brainstorming asks one material question at a time, compares 2–3 architectural approaches, and never implements;
- planning traces every acceptance criterion to a task and command and requires test-first work unless the approved Plan records an exception;
- Spec weights equal 100 as `15,20,25,20,20`;
- Plan weights equal 100 as `25,20,15,25,15`;
- Spec/Plan threshold is 85 and neither can pass a Critical/High finding;
- code score is advisory and deterministic failures are not waivable;
- round 1 is full; follow-ups focus on unresolved findings and regressions;
- no unfinished-marker token is present outside intentionally variable template tokens.

Defer cross-file link assertions to Tasks 6 and 7, where the consumer files first exist.

Encode the marker regex without spelling the markers literally in the Plan, for example `r"\b(?:T[B]D|T[O]DO)\b"`.

- [ ] **Step 2: Run the content tests and confirm RED**

```bash
python3 -m unittest .claude/skills/quality-goal/tests/test_content_contracts.py -v
```

Expected: failures naming each missing reference file.

- [ ] **Step 3: Write `routing-rules.md`**

Include this ordered algorithm:

1. Parse optional first token; reject an unknown mode.
2. Scan strict risk triggers before estimating size.
3. If explicit mode is higher/equal, accept it.
4. If explicit mode is lower, show exact triggers and ask for confirmation; absent confirmation, retain the safer mode.
5. In auto mode choose strict on any strict trigger, standard on cross-layer/interface/ambiguity triggers, otherwise light only when all light conditions hold.
6. When uncertain, choose the higher mode.
7. Print selected mode and concrete evidence before the next stage.

Include the full light/standard/strict conditions and examples from Spec sections 6–7.

- [ ] **Step 4: Write adapted brainstorming and planning policies**

`brainstorming-policy.md` must require repository inspection, materially necessary one-at-a-time questions, 2–3 options for architectural decisions, a recommendation, scope/non-goals/acceptance criteria/interfaces/errors/testability, and decomposition of independent subsystems. It must state that it is an adapted policy and must not invoke or modify the bundled brainstorming skill.

`planning-policy.md` must require exact repository-known files/interfaces, independently testable tasks, test-first behavior changes, actual commands plus expected outcomes, rollback/failure handling, and a complete acceptance-criteria traceability table. It must hand the approved Plan to Codex and must not invoke or modify the bundled writing-plans skill.

- [ ] **Step 5: Write the three rubrics**

Each rubric contains scoring table, hard-gate checklist, finding severity definitions, stable-ID rules, round behavior, and stop condition. Use the exact weights in the Spec. `code-rubric.md` records a score for observability but explicitly says the score cannot override failed commands or a Critical/High finding.

- [ ] **Step 6: Write exact model routing and command safety**

`model-routing.md` contains this route table:

| Stage | Model | Effort |
|---|---|---|
| Claude orchestrator | inherit | high |
| Fresh reviewer | opus | high |
| Codex light/standard | gpt-5.6-terra | high |
| Codex strict | gpt-5.6-sol | high |
| Bounded redesign only | gpt-5.6-sol | xhigh |

It also defines this Codex command template:

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

The policy requires checking the exit code, validating the result file, and marking `BLOCKED_MODEL_UNAVAILABLE` when the selected model is rejected. It forbids silent fallback and forbidden Codex flags listed in Global Constraints. Prompt/result/event paths live only under the ignored task state directory.

- [ ] **Step 7: Run content tests**

```bash
python3 -m unittest .claude/skills/quality-goal/tests/test_content_contracts.py -v
```

Expected: every Task 4 rubric/routing/policy assertion passes.

- [ ] **Step 8: Optional authorized commit checkpoint**

```bash
git add .claude/skills/quality-goal/references \
  .claude/skills/quality-goal/tests/test_content_contracts.py
git commit -m "docs: define quality-goal policies and rubrics"
```

---

### Task 5: Durable document templates and Codex completion schema

**Files:**

- Create: `.claude/skills/quality-goal/templates/spec.md`
- Create: `.claude/skills/quality-goal/templates/plan.md`
- Create: `.claude/skills/quality-goal/templates/report.md`
- Create: `.claude/skills/quality-goal/schemas/codex-result.schema.json`
- Modify: `.claude/skills/quality-goal/tests/test_content_contracts.py`

**Interfaces:**

- Consumes: durable document requirements and shared Codex result contract.
- Produces: renderable templates with `{{UPPER_SNAKE_CASE}}` variables and a strict Codex output schema.

- [ ] **Step 1: Add failing template/schema contract tests**

Assert the Spec template has these headings: Problem and context, Goals, Non-goals, Requirements, Acceptance criteria, Architecture, Interfaces and data flow, Failure behavior, Security and risk, Test strategy, Decisions.

Assert the Plan template has: Spec link, Global constraints, File map, Task dependencies, Tasks, Verification commands, Rollout and rollback, Acceptance-criteria traceability.

Assert the Report template has: Classification, Review history, Blocking-finding resolutions, Plan approval, Changed files, Verification evidence, Remaining advisory findings, Final status.

Assert `codex-result.schema.json` has `additionalProperties: false`, all six required top-level fields, command `exit_code` as integer, and relative changed-file strings.

- [ ] **Step 2: Run tests and confirm RED**

```bash
python3 -m unittest .claude/skills/quality-goal/tests/test_content_contracts.py -v
```

Expected: failures name the missing templates and Codex schema.

- [ ] **Step 3: Write the three templates**

Use only explicit `{{TOKEN}}` variables. Each template starts with task ID, mode, status, created/updated timestamps, and source goal. The Report represents missing verification categories as `not configured` plus repository evidence, never as passed. The Report also records every actual command, exit code, and concise output evidence.

For strict mode, the Spec and Plan templates include conditional sections for threat/trust boundaries, authorization and tenant isolation, migration/compatibility/rollback, failure recovery/observability, and high-risk E2E verification. The orchestrator must remove inapplicable conditional blocks or mark them `not applicable` with a reason before review.

- [ ] **Step 4: Write `codex-result.schema.json`**

Use Draft 2020-12. Set `status` enum to `completed`, `blocked`, `needs_plan_change`; require unique relative `changed_files`; make each command object require `command`, `exit_code`, and `result`; and reject unknown fields. A `completed` payload may still have non-empty concerns, so the orchestrator—not the schema—decides whether to continue.

- [ ] **Step 5: Run content tests**

```bash
python3 -m unittest .claude/skills/quality-goal/tests/test_content_contracts.py -v
```

Expected: all Task 5 assertions pass.

- [ ] **Step 6: Optional authorized commit checkpoint**

```bash
git add .claude/skills/quality-goal/templates \
  .claude/skills/quality-goal/schemas/codex-result.schema.json \
  .claude/skills/quality-goal/tests/test_content_contracts.py
git commit -m "feat: add quality-goal artifact contracts"
```

---

### Task 6: Fresh-context read-only Claude reviewer

**Files:**

- Create: `.claude/agents/quality-reviewer.md`
- Modify: `.claude/skills/quality-goal/tests/test_content_contracts.py`

**Interfaces:**

- Consumes: artifact type, round, target path or supplied diff, rubric path, repository evidence paths, and prior open finding IDs.
- Produces: only one JSON object matching `review.schema.json`; it never edits files.

- [ ] **Step 1: Add failing reviewer contract tests**

Parse the frontmatter with a small standard-library helper in the test. Assert exact values:

```yaml
name: quality-reviewer
tools: Read, Grep, Glob
model: opus
effort: high
```

Also assert a non-empty `description`, absence of Edit/Write/Bash/Agent tools, no persistent `memory`, links to all three rubrics and the review schema, and instructions to output JSON only.

- [ ] **Step 2: Run tests and confirm RED**

```bash
python3 -m unittest .claude/skills/quality-goal/tests/test_content_contracts.py -v
```

Expected: failure because the reviewer definition is missing.

- [ ] **Step 3: Write the reviewer agent**

Use this frontmatter:

```yaml
---
name: quality-reviewer
description: Independently reviews one quality-goal Spec, Plan, or code diff against evidence and returns schema-valid findings.
tools: Read, Grep, Glob
model: opus
effort: high
maxTurns: 12
---
```

The body must:

1. Reject missing artifact/rubric/evidence input as `BLOCKED` JSON.
2. Load only the relevant rubric and supplied evidence.
3. Perform a full review on round 1.
4. On later rounds, verify prior open IDs, detect regressions, and add a new blocker only with `new_blocker_evidence`.
5. Keep finding IDs stable across rounds for materially identical issues.
6. Never edit, recommend a severity change to reach a target, or expose hidden reasoning.
7. Return one JSON object without Markdown fences or surrounding prose.

The orchestrator creates a new Agent invocation for every round; it never resume/continues a prior reviewer context.

- [ ] **Step 4: Run content tests**

```bash
python3 -m unittest .claude/skills/quality-goal/tests/test_content_contracts.py -v
```

Expected: reviewer isolation and tool-contract assertions pass.

- [ ] **Step 5: Optional authorized commit checkpoint**

```bash
git add .claude/agents/quality-reviewer.md \
  .claude/skills/quality-goal/tests/test_content_contracts.py
git commit -m "feat: add independent quality reviewer"
```

---

### Task 7: Manual `/quality-goal` orchestrator and safety wiring

**Files:**

- Create: `.claude/skills/quality-goal/SKILL.md`
- Create or modify: `.gitignore`
- Modify: `.claude/skills/quality-goal/tests/test_content_contracts.py`

**Interfaces:**

- Consumes: `$ARGUMENTS`, all references/templates/schemas/scripts, Claude Agent tool, Codex CLI, and repository evidence.
- Produces: state transitions, durable artifacts, exactly one pre-implementation user approval gate, bounded Codex/reviewer loops, and final Report.

- [ ] **Step 1: Add failing orchestrator frontmatter and workflow tests**

Assert exact frontmatter:

```yaml
---
name: quality-goal
description: Use when the user explicitly requests a quality-gated, documented software change workflow.
argument-hint: '[--mode=auto|light|standard|strict] <goal>'
disable-model-invocation: true
model: inherit
effort: high
---
```

Static assertions also require all states, round limits, a fresh `quality-reviewer` invocation instruction, the Codex command reference, one final approval gate, malformed-review retry once, no silent model fallback, no automatic external/destructive operations, and links to every supporting file. Assert `SKILL.md` is fewer than 500 lines.

- [ ] **Step 2: Run tests and confirm RED**

```bash
python3 -m unittest .claude/skills/quality-goal/tests/test_content_contracts.py -v
```

Expected: failure because `SKILL.md` and the ignore rule are missing.

- [ ] **Step 3: Write concise frontmatter and argument parsing instructions**

Use the exact frontmatter above. The first token is parsed only when it starts with `--mode=`. An absent token means auto. Reject empty goals and unknown values before state creation. Run risk classification even for manual modes; explain and confirm any downgrade below the risk result.

- [ ] **Step 4: Implement the orchestrator stage table in Markdown instructions**

The skill body contains this decision table:

| Stage | Required action before transition |
|---|---|
| `INTAKE` | parse goal; inspect/reuse matching incomplete state; preflight Git/Codex |
| `CLASSIFIED` | load routing rules; print mode and evidence |
| `SPEC_REVIEW` | standard/strict only; draft from template; new reviewer; validate; gate; revise at most twice |
| `PLAN_REVIEW` | map every acceptance criterion; discover exact commands; new reviewer; validate; gate; revise at most twice |
| `AWAITING_PLAN_APPROVAL` | show final Plan or light compact Plan and ask exactly once for explicit implementation approval |
| `IMPLEMENTING` | confirm approval digest; choose exact Codex route; invoke bounded task/fix prompt |
| `CODE_REVIEW` | independently rerun commands; build review context; new reviewer; validate; gate; fix at most three rounds |
| terminal | write/update Report and explain completion, block, redesign, or cancellation |

Scope changes after approval invalidate the affected Plan/Spec digest and downstream verification, then return to the earliest affected review stage.

- [ ] **Step 5: Specify exact artifact and state behavior**

For standard/strict, allocate `docs/development/YYYY-MM-DD-<slug>/` with deterministic numeric suffix on collision and create Spec, Plan, Report. For light, create only the durable Report; persist the exact compact Plan as `.claude/quality-state/<task-id>/compact-plan.md` solely to compute and verify its approval digest. Use `${CLAUDE_SKILL_DIR}` for scripts/references so project/personal/plugin installation paths remain resolvable.

At every durable transition call `quality_state.py`; never infer a passed stage solely from conversation memory. Store artifact SHA-256 digests. Resume only when `select-resume` returns a match, summarize it to the user, and reuse a passed artifact only when its recorded digest remains current.

- [ ] **Step 6: Specify review invocation and malformed-output recovery**

Every review uses a new `quality-reviewer` Agent call with only the required contract inputs. For code, provide base revision, changed-file list, unified diff, verification JSON path, code-rubric path, and prior open IDs. Persist the returned JSON, run `validate_review.py validate`, and call `quality_state.py record-review-error` when validation fails. Retry once with only the validation errors added; the state helper transitions to `BLOCKED` on the second malformed response. If the requested Opus reviewer cannot launch, transition to `BLOCKED_REVIEWER_MODEL_UNAVAILABLE` without changing models.

Run `validate_review.py gate` with explicit checks. Never ask the reviewer to waive a failed deterministic command.

- [ ] **Step 7: Specify Codex invocation and independent verification**

Before Codex, write a prompt under the ignored task state directory containing approved Spec/Plan paths, bounded task or fix request, allowed paths, repository instructions, exact targeted commands, test-first requirement, dirty-path exclusions, and the Codex result contract. Invoke the command from `model-routing.md` without credential handling. A non-zero exit, missing result, unavailable exact model, or `needs_plan_change` status produces `BLOCKED` or returns to Plan review as appropriate.

After Codex, compare actual Git changes to `changed_files`, ensure initial unrelated dirty paths were preserved, and run in order: targeted tests, relevant full tests, type check, lint, build, and required E2E/manual evidence. Record absent categories as `not configured` with the repository source consulted. Strict cannot pass without an approved high-risk verification path.

- [ ] **Step 8: Add runtime ignore rule**

Add exactly:

```gitignore
.claude/quality-state/
```

Preserve all existing ignore entries and formatting.

- [ ] **Step 9: Run all deterministic tests**

```bash
python3 -m unittest discover -s .claude/skills/quality-goal/tests -p 'test_*.py' -v
```

Expected: all unit and static content-contract tests pass.

- [ ] **Step 10: Optional authorized commit checkpoint**

```bash
git add .claude/skills/quality-goal/SKILL.md .gitignore \
  .claude/skills/quality-goal/tests/test_content_contracts.py
git commit -m "feat: orchestrate quality-gated Codex delivery"
```

---

### Task 8: Deterministic fixture tests for stop, resume, and dirty-worktree behavior

**Files:**

- Modify: `.claude/skills/quality-goal/tests/test_quality_state.py`
- Modify: `.claude/skills/quality-goal/tests/test_validate_review.py`
- Modify: `.claude/skills/quality-goal/tests/test_content_contracts.py`

**Interfaces:**

- Consumes: complete deterministic bundle from Tasks 2–7.
- Produces: fixture-level evidence independent of live model judgment.

- [ ] **Step 1: Add a disposable Git fixture helper**

In `test_quality_state.py`, create a helper that initializes a temporary repo, configures only repo-local test identity, commits `app.txt`, and returns its path. It must never touch user/global Git configuration.

```python
def make_git_repo(testcase):
    root = Path(testcase.enterContext(tempfile.TemporaryDirectory()))
    run_git(root, "init")
    run_git(root, "config", "user.name", "quality-goal-test")
    run_git(root, "config", "user.email", "quality-goal-test@example.invalid")
    (root / "app.txt").write_text("base\n", encoding="utf-8")
    run_git(root, "add", "app.txt")
    run_git(root, "commit", "-m", "fixture")
    return root
```

- [ ] **Step 2: Add pressure regression tests**

Add tests that simulate payload/state changes rather than asking a model:

- score 93 plus High blocker remains failed;
- malformed JSON is rejected and the caller's retry counter reaches exactly 2;
- Spec round 2 failure and repeated stable ID stop at `NEEDS_REDESIGN`;
- code round 3 failure stops;
- plan approval digest mismatch blocks `IMPLEMENTING`;
- changed tracked and untracked file content changes the workspace fingerprint;
- initial unrelated dirty file content remains byte-identical after simulated task-file changes;
- resume returns `PLAN_REVIEW` after a valid passed Spec and never creates a second task state.

- [ ] **Step 3: Run the full fixture suite twice**

```bash
python3 -m unittest discover -s .claude/skills/quality-goal/tests -p 'test_*.py' -v
python3 -m unittest discover -s .claude/skills/quality-goal/tests -p 'test_*.py' -v
```

Expected: both runs pass with the same test count and no files left outside temporary directories.

- [ ] **Step 4: Check formatting and forbidden command contracts**

```bash
python3 -m py_compile \
  .claude/skills/quality-goal/scripts/validate_review.py \
  .claude/skills/quality-goal/scripts/quality_state.py
rg -n -- '--skip-git-repo-check|--full-auto|--yolo|dangerously-bypass' \
  .claude/skills/quality-goal .claude/agents/quality-reviewer.md
```

Expected: compilation exits 0. The search may find only explicit prohibition text in policy/tests; it must not find an executable command that enables a forbidden flag.

- [ ] **Step 5: Optional authorized commit checkpoint**

```bash
git add .claude/skills/quality-goal/tests
git commit -m "test: cover quality-goal failure and resume paths"
```

---

### Task 9: With-skill fresh-context evaluations and authenticated end-to-end proof

**Files:**

- Create from `.claude/skills/quality-goal/templates/report.md`: `docs/development/2026-08-25-quality-goal/report.md`
- Runtime only, ignored: `.claude/quality-state/<evaluation-task-id>/...`

**Interfaces:**

- Consumes: unchanged scenario IDs/assertions from Task 1 and the complete installed bundle.
- Produces: level-labeled verification evidence and calibration findings.

- [ ] **Step 1: Run the three routing scenarios in fresh Claude Code sessions**

Run from a disposable Git fixture that contains the completed `.claude/` bundle:

```bash
claude -p --no-session-persistence --output-format json \
  "/quality-goal Change the partner-switch button copy and update its existing snapshot."

claude -p --no-session-persistence --output-format json \
  "/quality-goal Add partner multi-account switching across the selector, session state, and API client."

claude -p --no-session-persistence --output-format json \
  "/quality-goal Let sales admins inspect partner coupon usage without exposing other partners' data."
```

Expected: light, standard, and strict respectively; each prints reasons and stops at the Plan approval boundary without implementation in the one-turn run. Project skills/custom agents must load normally, so do not use `--bare`.

- [ ] **Step 2: Run the six pressure scenarios**

Use a new non-persistent session or prepared state fixture for each scenario. Compare every assertion with the Task 1 baseline and record pass/fail plus evidence. Fix only instruction ambiguity revealed by a failure, then rerun both the failing scenario and one neighboring scenario to detect regression.

- [ ] **Step 3: Run one interrupted/resumed standard task**

Stop after `SPEC_PASSED`, start a fresh Claude Code session in the same fixture, reinvoke the same goal, and verify that the state summary identifies the existing task and continues at `PLAN_REVIEW`. Confirm the Spec path and digest are unchanged and no second task directory appears.

- [ ] **Step 4: Run one authenticated end-to-end task with Codex**

Use a harmless fixture change with an existing deterministic test. In an interactive Claude Code session:

1. Invoke `/quality-goal --mode=light <fixture goal>`.
2. Review the compact Plan and explicitly approve implementation.
3. Verify Codex runs with Terra/high and `workspace-write`.
4. Intentionally leave no failing test/check before code review.
5. Verify the fresh reviewer returns schema-valid JSON.
6. Verify the orchestrator independently reruns commands and writes `report.md`.
7. Confirm no commit, push, merge, deployment, production action, or credential output occurred.

If either subscription is unavailable, report `BLOCKED` and retain the claim level `fixture tested`, not `end-to-end verified`.

- [ ] **Step 5: Run one strict dry run through Plan approval**

Use the authorization/tenant-isolation fixture, stop before implementation unless the fixture has safe tests, and verify threat/trust, isolation, rollback applicability, observability, and high-risk E2E sections are hard requirements. Confirm the selected Codex command is Sol/high without invoking a weaker fallback.

- [ ] **Step 6: Write the implementation report**

Create `docs/development/2026-08-25-quality-goal/report.md` from the template. Include:

- baseline failures and with-skill improvements by scenario ID;
- deterministic unit/static test command, count, and exit code;
- fixture repository evidence;
- live Claude/Codex versions and exact commands where run;
- review schema failures/retries observed;
- remaining Medium/Low findings;
- the highest truthful claim among `structurally validated`, `fixture tested`, and `end-to-end verified`;
- final status or exact blocker and recovery action.

- [ ] **Step 7: Final verification**

```bash
python3 -m unittest discover -s .claude/skills/quality-goal/tests -p 'test_*.py' -v
python3 -m py_compile \
  .claude/skills/quality-goal/scripts/validate_review.py \
  .claude/skills/quality-goal/scripts/quality_state.py
git diff --check
git status --short
```

Expected: tests and compilation pass; `git diff --check` reports no whitespace errors; status contains only intended bundle, report, and any pre-recorded unrelated paths unchanged.

- [ ] **Step 8: Optional authorized commit checkpoint**

```bash
git add .claude .gitignore docs/development/2026-08-25-quality-goal/report.md
git commit -m "feat: deliver verified quality-goal workflow"
```

---

## Acceptance-criteria traceability

| Spec AC | Implementation tasks | Required evidence |
|---|---|---|
| 1. Auto route and print reasons | 4, 7, 9 | routing content tests plus three fresh-session outputs |
| 2. Overrides, invalid mode, downgrade confirmation | 4, 7, 9 | content tests and override pressure runs |
| 3. Manual-only skill | 7 | exact frontmatter assertion |
| 4. Light compact Plan/report only | 5, 7, 9 | light fixture file tree and approval transcript |
| 5. Standard/strict Spec, Plan, Report | 5, 7, 9 | generated fixture documents and template tests |
| 6. Fresh read-only reviewer and valid JSON | 2, 6, 9 | frontmatter tests, validation output, review files |
| 7. Spec/Plan hybrid gates | 2, 4, 8 | threshold/blocker/required-check unit tests |
| 8. One final Plan approval | 7, 9 | approval-pressure run and approval digest |
| 9. Exact Codex model route | 4, 7, 9 | model-routing test and captured command evidence |
| 10. Code hard gate | 2, 7, 8, 9 | failed-command and High-finding tests plus E2E report |
| 11. Bounded loops | 3, 8, 9 | round-limit and stable-ID regression tests |
| 12. Resume without duplicate stage | 3, 8, 9 | resume unit test and interrupted live fixture |
| 13. Complete final Report | 5, 7, 9 | report template test and rendered implementation report |
| 14. Preserve unrelated changes/no external mutation | 3, 4, 7, 8, 9 | dirty-worktree byte check and E2E safety audit |
| 15. Baseline/with-skill coverage | 1, 8, 9 | nine-scenario comparison and final claim level |

## Execution checkpoints

1. **RED checkpoint:** Task 1 baseline is captured before `SKILL.md` exists.
2. **Deterministic GREEN checkpoint:** Tasks 2–8 tests pass twice.
3. **Behavioral GREEN checkpoint:** all nine with-skill scenarios satisfy their assertions in fresh contexts.
4. **Live checkpoint:** one authenticated Claude Code → Codex → Claude review cycle completes in a disposable Git fixture.
5. **Release checkpoint:** Report states the truthful claim level and no hard gate is waived.

Do not start Task 2 until the baseline results have been captured. Do not start Task 7 if deterministic gate/state tests are failing. Do not claim completion if Task 9 cannot reach the live checkpoint; use the appropriate lower claim level and record the blocker.
