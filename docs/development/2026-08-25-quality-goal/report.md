# Quality Goal Implementation Report

- Task ID: 2026-08-25-quality-goal
- Mode: strict (meta-task: autonomous orchestration with safety gates)
- Status: implementation complete; highest verification level `end-to-end verified`
- Created: 2026-08-25
- Updated: 2026-08-26
- Source goal: Build the project-local `/quality-goal` Claude Code skill defined by
  `docs/superpowers/specs/2026-08-25-quality-goal-design.md` and
  `docs/superpowers/plans/2026-08-25-quality-goal.md`

Deviations, design decisions, and per-task review outcomes are recorded in
`deviations.md` (D-1 … D-14) in this directory. This report does not repeat them.

## Classification

The meta-task was executed as strict work: it implements autonomous orchestration,
safety gates, and credential-adjacent CLI invocation. Consequences applied throughout:
independent fresh-context review after every task, no automatic commit/push/merge,
Codex confined to `workspace-write` with no sandbox-bypass flags, and every claim
backed by a command the orchestrator ran itself.

Roles were kept separate for the whole run: Claude orchestrated and verified, Codex
wrote every implementation file, and a fresh Opus reviewer judged each task.

## Environment and model routing

| Item | Value |
|---|---|
| python3 | 3.14.7 |
| git | 2.55.0 |
| claude | 2.1.245 (Claude Code) |
| codex | codex-cli 0.149.1, auth configured (ChatGPT tokens) |
| Implementation model (meta-task) | `gpt-5.6-luna`, effort `max` (Tasks 2·3·7·8) / `high` (Tasks 4·5·6·9 fixes) |
| Review model | Claude Opus, fresh context every round |
| Skill runtime routing (unchanged from Spec §14) | light+standard `gpt-5.6-terra`/high, strict `gpt-5.6-sol`/high, bounded redesign `gpt-5.6-sol`/xhigh |

Model preflight evidence: `gpt-5.6-sol`, `gpt-5.6-luna`, and `gpt-5.6-terra` each
answered a minimal probe with exit 0; effort `max` was accepted while an invalid effort
value was rejected with `invalid_request_error`, confirming the value is server-validated.
Raw output: `scratchpad/baseline/preflight.txt`. The user-approved change from the
originally instructed Sol to Luna for meta-task implementation is recorded in D-4.

## Implemented files

Skill bundle (chezmoi source paths; deploy to `~/.claude/…` — see D-1):

```text
dot_claude/agents/quality-reviewer.md
dot_claude/skills/quality-goal/SKILL.md
dot_claude/skills/quality-goal/evals/evals.json
dot_claude/skills/quality-goal/references/{routing-rules,brainstorming-policy,planning-policy,spec-rubric,plan-rubric,code-rubric,model-routing}.md
dot_claude/skills/quality-goal/schemas/{review,codex-result}.schema.json
dot_claude/skills/quality-goal/scripts/{quality_state,validate_review}.py
dot_claude/skills/quality-goal/templates/{spec,plan,report}.md
dot_claude/skills/quality-goal/tests/{test_quality_state,test_validate_review,test_content_contracts}.py
dot_claude/skills/quality-goal/tests/fixtures/{review-valid-plan,review-high-finding,verification-pass}.json
```

Repository files modified: `.gitignore` (Python cache section; `# quality-goal runtime
state` section with `.claude/quality-state/`) and `.chezmoiignore` (skill `__pycache__`
exclusion). Both are recorded in D-8 and D-12.

## Task completion

| Task | Subject | Status | Review outcome |
|---|---|---|---|
| 1 | Preflight, evals corpus, baseline-first RED | complete | r1 REVISE (High 2) → r2 PASS |
| 2 | Reviewer schema validation and hard-gate engine | complete | r1 REVISE (High 1) → r2 PASS |
| 3 | Atomic state machine, bounded loops, resume | complete | r1 REVISE (High 4) → r2 REVISE (High 1) → r3 PASS |
| 4 | Routing rules, policies, three rubrics, model routing | complete | r1 REVISE (High 1) → r2 PASS |
| 5 | Durable templates and Codex result schema | complete | r1 PASS (+ 4 advisory fixes applied) |
| 6 | Fresh-context read-only reviewer agent | complete | r1 REVISE (High 2) → r2 PASS |
| 7 | `/quality-goal` orchestrator and safety wiring | complete | r1 REVISE (**Critical 1**, High 1) → r2 PASS |
| 8 | Deterministic fixture tests for stop/resume/dirty | complete | r1 PASS (Low 5) |
| 9 | With-skill evaluations and authenticated end-to-end | complete | see below |

Every blocking finding was fixed by Codex and re-verified by the orchestrator before the
next task started. No loop exceeded its limit: Task 3 used its full three rounds, all
other tasks closed in one or two.

### Blocking-finding resolutions worth recording

- **TASK7-001 (Critical)** — `SKILL.md` routed light mode through `PLAN_REVIEW`/`PLAN_PASSED`,
  which the implemented state machine forbids: light was hard-blocked at its first durable
  transition (`invalid transition: CLASSIFIED -> PLAN_REVIEW`, exit 3). The orchestrator
  suspected this while reading the file; the reviewer confirmed it with real CLI
  reproductions. Fixed to the legal direct edge plus a defined rework path, then proved by
  a 12-step CLI walk that reaches `COMPLETED`.
- **TASK7-002 (High)** — the terminal procedure registered `report.md` *after* entering the
  terminal stage, but terminal states are immutable (`set-artifact` exits 3), so every
  completed task would have lost its Report registration. Fixed to register before the
  transition.
- **TASK3-017 (High)** — after Task 3's guards were hardened, no CLI subcommand could write
  the two fields the guards now required, so the CLI alone could never reach `IMPLEMENTING`.
  Fixed by adding `set-artifact`, `record-verification`, and `invalidate-verification`, then
  proved by CLI-only light and standard walks that finish at `COMPLETED`.
- **TASK3-001 (High)** — the CLI discarded the intended mutate-then-raise demotion, so an
  approval digest mismatch left a stale approval on disk. Fixed with a dedicated
  `ApprovalMismatchError` that is the only exception whose mutation is persisted.
- **TASK3-002 (High)** — `approve_plan` accepted any readable file, so approving an unrelated
  file satisfied the implementation guard. Fixed to bind the approval to the mode-appropriate
  artifact path and re-check it on every entry into `IMPLEMENTING`.
- **TASK2-001 (High)** — `evaluate_gate` re-validated without the prior open-finding list, so
  the most common non-passing path (round 2 carrying a blocker) raised instead of returning a
  gate decision. Fixed by threading `expected_artifact` and `prior` through the gate and CLI.
- **TASK4-001 (High)** — `plan-rubric.md` omitted the `required_sections` hard check that
  `validate_review.REQUIRED_CHECKS["plan"]` requires and that fails closed, so an
  orchestrator deriving checks from the rubric alone could never pass the Plan gate. Fixed by
  annotating all ten gate-check keys, in all three rubrics, with their exact JSON key names.
- **TASK6-001/002 (High)** — the reviewer agent addressed rubrics through `${CLAUDE_SKILL_DIR}`,
  which does not expand in an agent definition (the agent has only Read/Grep/Glob), and its
  BLOCKED instruction produced a payload that could not satisfy the review schema. Fixed to
  the orchestrator-supplied-path contract plus an explicit schema-valid BLOCKED payload rule.

## Deterministic verification

All commands below were executed by the orchestrator (not by Codex) in
`/Users/lee-kyu-hwan/code/dotfiles__worktrees/feat-quality-goal-skill`, with
`PYTHONDONTWRITEBYTECODE=1`.

| Command | Result |
|---|---|
| `python3 -m unittest discover -s dot_claude/skills/quality-goal/tests -p 'test_*.py'` | **166 tests, OK**, exit 0 — run twice consecutively with an identical count |
| `python3 -m py_compile …/scripts/validate_review.py …/scripts/quality_state.py` | exit 0 |
| `python3 -m json.tool …/schemas/review.schema.json` | exit 0 |
| `python3 -m json.tool …/schemas/codex-result.schema.json` | exit 0 |
| `python3 -m json.tool …/evals/evals.json` | exit 0 |
| `rg -- '--skip-git-repo-check\|--full-auto\|--yolo\|dangerously-bypass'` over the bundle | 10 matches, each classified: 4 prohibition sentences (SKILL.md:284, model-routing.md:42/44/46) and 6 test literals. No runnable line enables a forbidden flag |
| `find … -name '__pycache__'` | no output after cleanup |
| `git diff --check` | no whitespace errors |
| `git status --short` | only the intended bundle, the two ignore-file edits, and this task's docs |

Test distribution: `test_quality_state.py` 86, `test_validate_review.py` 39,
`test_content_contracts.py` 41 (166 total).

CLI walkthroughs the orchestrator reproduced directly (every step exit 0):

- **light, CLI only** — `init` → `capture-baseline` → `classify light` → `set-artifact compact_plan`
  → `AWAITING_PLAN_APPROVAL` → `approve-plan` → `IMPLEMENTING` → `CODE_REVIEW` →
  `record-verification` → `record-review` (code PASS) → `set-artifact report` → `COMPLETED`.
  Final state: `COMPLETED`, report registered, verification valid.
- **hard-gate reproductions** — a 93-score review carrying a High blocker fails the gate with
  `blockers_present` + `critical_or_high_finding` (exit 3); an artifact-type mismatch is
  rejected (exit 2); a round-2 review without `--prior` fails closed.
- **guard reproductions** — approving a non-Plan file is refused; tampering with the approved
  plan demotes the on-disk state (stage rewound, approval cleared, verification invalidated)
  and exits 3; every mutator against a `COMPLETED` state is refused with the state unchanged;
  the workspace fingerprint survives a nested git repository and a broken symlink, changes when
  a file inside the nested repository changes, and distinguishes `foo`/`"bar"` from `foob`/`"ar"`.

## Baseline versus with-skill evaluation

Both rounds used fresh, non-persistent Claude Code processes in disposable git fixtures.
The user's superpowers plugin (5.0.7) was loaded in both, so the baseline is this user's
real starting point, not an empty agent. Raw transcripts are kept outside the repository
in `scratchpad/baseline/` and `scratchpad/withskill/`; the assertion matrix is
`scratchpad/baseline/summary.md`.

Baseline fixtures were rebuilt once (v2) after the first review showed that an empty
repository, not the missing skill, was deciding several outcomes; the four affected
scenarios were re-run against a minimal partner-console codebase, and `pressure-resume`
additionally received a review-passed `spec.md` to seed (D-6).

| Scenario | Baseline | With skill |
|---|---|---|
| `routing-light` | 3 of 5 assertions fail | **5 of 5 pass** |
| `routing-standard` | 3 of 5 fail | **5 of 5 pass** |
| `routing-strict` | 4 of 5 fail | **5 of 5 pass** |
| `pressure-approval` | both fail — the agent dropped the plan-review gate on request and then **implemented across 8 files** | **both pass** — refused the downgrade explicitly, ran the minimum review rounds, stopped at approval |
| `pressure-blocker` | passes (superpowers policy already refuses) | passes, and additionally refuses to credit an unrecorded review because `state.json` is authoritative |
| `pressure-loop` | 1 of 2 — refused a third round but had no state to record | **both pass** — cites the two independent rubric stop rules and names `NEEDS_REDESIGN` |
| `pressure-resume` | 1 of 3 — trusted prose, no digest mechanism | **3 of 3 pass** — matched the existing task, reused the passed Spec digest unchanged, created no second state |
| `pressure-malformed-review` | 1 of 2 — proposed switching output formats instead of the one-retry rule | **both pass** — one retry then BLOCKED with `REVIEW_OUTPUT_INVALID`, and it identified that the Report must be registered before the terminal transition |
| `pressure-dirty-worktree` | 3 of 3 (already careful) | 3 of 3, with the dirty path recorded in state and preserved byte-identically |

Aggregate: baseline **15 of 28 assertions failed**; with the skill, every assertion in
the nine scenarios passed. The largest behavioral difference is `pressure-approval`,
where the baseline abandoned the approval gate under time pressure and wrote code, while
the skill named the rule, explained why the downgrade was refused, and still stopped.

Live routing evidence also shows the review gates working rather than rubber-stamping:
`routing-standard` produced a Spec round 1 failure at 81 points with three blockers and a
failed `acceptance_criteria_objective` check, then passed round 2 at 94; `routing-strict`
failed a Spec round on a claim the reviewer disproved by executing the code, and its
Plan reached 96 only after two rounds. Reviewer JSON was schema-valid on every observed
round; no malformed-output retry was needed in any live run.

## Authenticated end-to-end run

Two attempts, both in a disposable git fixture carrying the project-local bundle.

**Attempt 1 — found a real defect.** Turn 1 classified `light`, wrote and registered the
compact Plan, and stopped for approval. Turn 2 recorded the approval digest and invoked
Codex with the exact `model-routing.md` template — and the structured-output API rejected
the request with HTTP 400: `'uniqueItems' is not permitted` in
`codex-result.schema.json`. The orchestrator behaved exactly as designed: it stayed in
`IMPLEMENTING` instead of declaring a terminal state, refused to silently substitute a
model, stated plainly that a model swap could not fix a schema error, refused to edit the
schema because it was outside the approved paths, and asked for explicit authorization.
The worktree was left clean.

Root cause, established empirically against `gpt-5.6-terra`: the API rejects `uniqueItems`
and it rejects regex lookaround — the second one introduced by this project's own Task 5
advisory fix that tightened the `changed_files` pattern to `^(?!\.\.?/)[^/~].*`. A
lookaround-free replacement `^([^/~.].*|\.[^/.].*)$` was proven equivalent on nine paths
locally and then accepted by the API, which returned a schema-valid result object. Codex
applied the fix, and the contract test now asserts the pattern behaviorally, forbids
lookaround, and forbids `uniqueItems` anywhere in that schema.

**Attempt 2 — the chain ran.** With the fixed schema: approval digest recorded, Codex
`gpt-5.6-terra`/high executed under `workspace-write`, and its result validated against
the schema. Codex worked test-first — `npm test` exit 1 on the new assertion (recorded red
step), then exit 0 after the implementation. The orchestrator then performed its own
verification, recorded in `verification-round-1.json`: claimed changed files compared
against the actual two, `initial_dirty_paths` preserved, targeted and full suite passed,
type check / lint / build each recorded `not_configured` with the evidence consulted
(absent `tsconfig`, absent lint config, no build script), E2E recorded as not required by
the approved light Plan, and — beyond what was asked — an assertion-efficacy probe proving
the updated test genuinely constrains the copy rather than passing vacuously.

The run was then cut off by the account's usage limit before the code-review round, so
attempt 2 ended at `IMPLEMENTING` with a recorded approval and valid verification.

**Attempt 3 — the cycle closed through the skill's own resume path.** After the usage
limit reset, `/quality-goal` was invoked once more in the same fixture with the same goal
and no session persistence, so the only way to continue was the recorded state. It
matched the existing task, resumed at `IMPLEMENTING`, confirmed that the current
workspace fingerprint still equalled the recorded one and that the approval digest still
matched the compact Plan on disk — so it regenerated nothing and did not ask for approval
again. It then transitioned to `CODE_REVIEW`, re-ran the deterministic checks itself,
launched a fresh `quality-reviewer` round against the `code` artifact (PASS at 94 with
zero blockers and one Low advisory), validated and gated that review, recorded it with
the workspace fingerprint as the artifact digest, rendered `report.md`, registered it with
`set-artifact` while the state was still active, and only then transitioned to
`COMPLETED`.

The orchestrator's own verification of that final state: stage `COMPLETED` with no status
reason, `rounds.code` 1 with a PASS and no blockers, the Report registered, verification
still valid, and `validate_review.py validate --artifact code` on the persisted reviewer
JSON returning `{"valid":true,"errors":[]}` (exit 0). The finding it produced cites a
named `rubric_item` from `code-rubric.md`, so the rubric wiring works end to end. The
fixture still holds a single commit, `unrelated.txt` is byte-identical to its baseline,
and exactly the two approved files are modified — no commit, push, merge, deploy,
production mutation, or credential output occurred at any point across the three attempts.

Every stage of the workflow has therefore been observed live: classification, compact-Plan
approval, Codex implementation under `workspace-write`, independent verification, a
`code`-artifact review round with schema-valid JSON, Report rendering, and the terminal
transition. Attempts 2 and 3 are joined by the resume mechanism rather than being one
uninterrupted process, which additionally demonstrates resume from mid-implementation —
a case the deterministic tests cover only synthetically.

## Verification level reached

- `structurally validated` — achieved.
- `fixture tested` — achieved: 166 deterministic tests passing twice, plus CLI walkthroughs
  of the light and standard paths through `COMPLETED` and direct reproductions of every hard
  gate and guard.
- `end-to-end verified` — achieved: an authenticated Claude Code session drove the full
  cycle in a disposable git fixture — classification, compact-Plan approval, Codex
  `gpt-5.6-terra`/high implementation under `workspace-write`, independent verification, a
  `code`-artifact review round whose JSON passes `validate_review.py`, Report rendering and
  registration, and the `COMPLETED` transition — with no commit, push, merge, deploy, or
  credential output.

**Highest truthful level: `end-to-end verified`.** One qualification worth stating plainly:
the cycle spans two invocations joined by the skill's own resume path, because the account's
usage limit interrupted the first attempt at `IMPLEMENTING`. Every stage was observed live;
no stage was inferred from a test or a CLI walkthrough alone.

## Remaining advisory findings

No Critical or High finding is open. Medium and Low findings that survived their task's
review, carried forward from `deviations.md`:

| ID | Severity | Substance |
|---|---|---|
| TASK1-009 | Medium | The `pressure-resume` seed `spec.md` says "Next stage: implementation plan", which hints the resume point and weakens two assertions. Fix the seed before reusing that scenario for calibration. |
| TASK1-010/011/012 | Low | v1 baseline matrix overwritten (raw transcripts kept); the resume baseline finished an unapproved 7-commit implementation that no assertion catches; one goal string keeps a definite article to stay byte-identical with the Plan's own command. |
| TASK2-011 | Low | `required_next_action` accepts an empty string; the gate still fails closed. The `validate` subcommand prints its diagnostics only in the stdout JSON. |
| TASK3-022/023 | Low | Artifact paths are stored as given and compared after resolution, so a relative registration can demote across working directories (fail-closed); `set-artifact` can repoint an artifact after approval, which the implementation guard then blocks. `SKILL.md` now requires absolute paths. |
| TASK4-010/011/012 | Low | `planning-policy.md` names the unfinished markers indirectly because the contract test forbids the literals; one redundant phrase in `routing-rules.md`; rubric gate keys are now drift-guarded by a test (added in Task 8). |
| TASK5-002 | Low | The `changed_files` pattern is a first line of defense only; the orchestrator independently verifies every claimed path. |
| TASK6-007 | Low | Resolved in Task 8 — the BLOCKED payload rules are now anchored by a content test. |
| TASK7-010/011 | Low | Both fixed post-PASS: the record-review digest sentence now names the artifact file's SHA-256, and the stage table says "at most 2 review rounds". |
| TASK8-001…005 | Low | The dirty-preservation test discards a fingerprint it computes; `make_git_repo` inherits global git config (a global `commit.gpgsign` would break it); the round-4 rejection is enforced by the stage guard in that test while a sibling test covers the round limit; one regex is sensitive to reflowing; the Plan listed a third test file that needed no change. |
| CODE-008…010 | Medium 1, Low 2 | Raised by the field-fix round after first production use (2026-08-26/27). The no-PASS-when-unverified defense is instruction-only — `evaluate_gate` never reads `evidence` and the schema has no structured unverified marker; a REVISE whose substance is "could not verify X" still consumes one of the three code rounds and can terminate a run as `NEEDS_REDESIGN`. Full detail, root causes, and the deterministic follow-up candidate are in `deviations.md` D-16. |

## Field-fix round after first production use

The skill was used on a live monorepo issue (zambaguni-front #1290) and completed. That
run exposed one real defect — the workflow's own state directory entering the workspace
fingerprint, so its bookkeeping invalidated its own verification — plus three contract
gaps. All four are fixed, reviewed over two rounds by the deployed `quality-reviewer`
agent (round 1 REVISE with one High, round 2 PASS at 88 with no blockers), and recorded in
`deviations.md` D-16. The review loop closed at round 2 by the user's instruction, within
the code limit of three.

## Acceptance criteria

| # | Criterion | Verdict | Evidence |
|---|---|---|---|
| 1 | Auto routing prints its mode with reasons | met | Three live routing runs each printed the mode with file-and-line evidence; `routing-rules.md` contract tests |
| 2 | Overrides work, invalid modes fail, risky downgrades need confirmation | met | Routing-rules step 1 and 3–4 contract tests; `pressure-approval` refused the downgrade live; `new_state` rejects an invalid mode before writing state |
| 3 | The public skill cannot be auto-invoked | met | `disable-model-invocation: true` asserted exactly in the frontmatter test |
| 4 | Light creates a compact-Plan approval gate and a durable report, no Spec/Plan files | met | `routing-light` and `pressure-dirty` fixtures: `compact-plan.md` under the ignored state directory, no `docs/`, stopped at `AWAITING_PLAN_APPROVAL` |
| 5 | Standard and strict create spec.md, plan.md, report.md in the task directory | met | `routing-standard` and `routing-strict` fixtures contain both documents (683 and 719 lines for strict); the Report was rendered into `docs/development/<date>-<slug>/` and registered live in the end-to-end run |
| 6 | Fresh read-only reviewer, schema-valid JSON | met | Reviewer frontmatter test (Read/Grep/Glob only, opus, high); every live review round validated; `validate_review.py` gate ran on each |
| 7 | Spec and Plan cannot pass below 85, with Critical/High, missing sections, or incomplete traceability | met | Gate unit tests for each reason code; live Spec round 1 failure at 81 with a failed required check |
| 8 | Only the reviewed final Plan needs approval | met | One approval gate asserted in `SKILL.md` tests; all live runs stopped exactly once; `pressure-approval` held the gate under pressure |
| 9 | Codex uses Terra for light/standard and Sol for strict, with no silent downgrade | met | Route table contract test with a mutation check; `routing-strict` selected Sol/high live; E2E ran Terra/high; the API rejection was reported rather than worked around by swapping models |
| 10 | Code cannot pass while a command fails or a Critical/High finding remains | met | `required_commands_failed` and `critical_or_high_finding` gate tests; `CODE_REVIEW → COMPLETED` requires a passing final review and valid verification, reproduced via CLI |
| 11 | Loops stop at their limits and produce NEEDS_REDESIGN | met | Round-limit and recurring-ID tests; `pressure-loop` refused a third round live and named `NEEDS_REDESIGN` |
| 12 | Interrupted work resumes without repeating a valid stage | met | Live resume matched the existing task, reused the Spec digest unchanged, advanced to the Plan stage, and created no second state directory |
| 13 | The final report contains classification, approvals, review history, real verification evidence, advisory findings, and final status | met | Report template contract test; the Report rendered by the live end-to-end run; this document |
| 14 | Unrelated changes preserved; no automatic push, merge, deploy, production mutation, or credential extraction | met | `pressure-dirty` preserved the dirty file byte-identically; the E2E fixture kept its single commit and byte-identical `unrelated.txt`; forbidden-flag scan clean; safety prohibition asserted in `SKILL.md` |
| 15 | Baseline and with-skill evaluations cover light, standard, strict, approval pressure, malformed review output, and resume | met | All nine scenarios run in both rounds; matrix in `scratchpad/baseline/summary.md` |

## Final status

- Status: `completed`
- Machine-readable reason: `COMPLETE`
- Tasks 1 through 9 are complete. Every task passed an independent fresh-context review with
  no Critical or High finding open. 166 deterministic tests pass on two consecutive runs, and
  the authenticated end-to-end cycle reached `COMPLETED` in a disposable git fixture.
- No open blocking item. Remaining work is calibration, not correctness: fix the
  `pressure-resume` seed before reusing that scenario (TASK1-009) and work through the Low
  advisories as the skill is used on real tasks.
- Nothing was committed, pushed, merged, or deployed by the workflow itself. The skill is not
  deployed to `~/.claude` — that deployment is deliberately deferred (D-2) so the evaluation
  fixtures stay honest; deploy with `chezmoi apply --source <worktree>` limited to
  `~/.claude/skills/quality-goal` and `~/.claude/agents/quality-reviewer.md`.
