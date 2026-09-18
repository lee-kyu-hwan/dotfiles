# Spec r1 readiness evidence

- Artifact: `spec.md`
- Formal round: 1
- Final artifact digest: `ffa1251b56a0be6799dc8deb6fb590d0047b3a877179c5510aabeff2069508d1`
- Route: fresh Codex `gpt-5.6-sol`, high effort, read-only, repository-canonical quality-goal v6.0.0 watchdog.
- Final outcome: `READY`, score 100, checklist C1 through C8 all pass, no findings and no blockers, all 10 evidence entries `verified: true`.

## Attempt history, in chronological order

The state helper numbers recorded attempts in the order they were written, which does not match the chronological order for the first two entries. The actual sequence was:

1. Stalled invocation on digest `0f07d57e…`: `activity_stall` after 603s with no events after `turn.started`, SIGTERM sent, no result produced, preservation bundle created, `residual_pids` empty. Recorded with `--invocation-status failed`. This is the known Codex model-turn stall on this host; the watchdog bounded it as designed and the read-only sandbox meant no artifact changed.
2. Restart within the phase watchdog restart budget, on digest `0f07d57e…`: 295s, exit 0, schema passed, `REVISE` score 90. `SPEC-009`, `SPEC-010`, `SPEC-011` judged resolved. One High blocker `READY-001`.
3. After the `READY-001` revision, on digest `21c6c377…`: 393s, exit 0, schema passed, `REVISE` score 88. `READY-001` judged resolved. One new High blocker `READY-002`.
4. After the `READY-002` revision, on digest `ffa1251b…`: 302s, exit 0, schema passed, `READY` score 100, no blockers.

## Findings raised and resolved before any formal round was spent

- `READY-001` (High): the Spec required Claude to fail closed outside the two declared account roots while the Problem section, `R3.3`, Architecture and the Authorization and tenant isolation subsection allowed selection outside those roots given a further "reviewed mapping", contradicting `AC-12`'s unconditional judgement. Resolved by making the initial-policy behaviour unconditionally fail closed and defining any future widening as a pre-launch reviewed Spec and registry source revision rather than a runtime exception. Zero occurrences of the exception wording remain.
- `READY-002` (High): the `claude-profile2` home contract was internally impossible, because `R3.4` and the registry interface required the exact absolute config-home path to exist and be exported while `R6.5`, `AC-30` and the `CMD-15` pass condition prohibited any config-home path in source or rendered output; that over-broad rule also obscured the narrower provider-default-home requirement. Resolved by narrowing the prohibition to unintended-disclosure surfaces while explicitly permitting the reviewed registry source, the rendered target and the private child environments, and by strengthening `R3.4`, `AC-13` and the `CMD-17` pass condition with a five-surface provider-default-home export prohibition covering source, rendered target, argv, verifier environment and provider environment. The absolute credential non-replication rule was confirmed unweakened.

## Carried-forward formal findings

`SPEC-009`, `SPEC-010` and `SPEC-011` originate in the predecessor execution's formal round 2 and were judged resolved in every completed attempt, each exactly once, with file-and-line evidence.

## Authoritative user corrections verified

`USER-WORKSPACE-DIRECTORY-SELECTION`, `USER-NEUTRAL-ALIAS-LEGACY-PROTECTION`, `USER-CLAUDE-DEFAULT-UNSET`, `USER-PERMISSION-BOUNDARY-SEPARATION`, `USER-CROSS-PROFILE-MOVE`, `USER-CLAUDE-SETTINGS-ISOLATION` and `USER-WORKMUX-HOOK-SEMANTICS` were each verified with file-and-line evidence.

## Shape at the final digest

54 requirements `R1.1`–`R11.8`, 54 acceptance criteria `AC-1`–`AC-54`, 54 traceability rows, judgement commands `CMD-1`–`CMD-23`, fourteen decisions, one matched strict marker pair, all twelve template sections in canonical order.

## Deterministic checks

- `revision_check.py --artifact spec` exit 0, `passed: true`, 0 empty cells, 0 removed IDs, revision notes not required at round 1.
- `git diff --check` passed.
- Baseline `python3 -m unittest tests/test_ai_session.py`: 19 tests, OK.

## Safety

Only `claude --help` and `codex --version` style help and version evidence was used, all of it captured previously. No auth, status, login, logout, usage, network or model probe, no identity enrollment, no account-home or credential read, no `chezmoi apply`, and no pane, session or process mutation.

## Relationship between this record and `state.json`

`state.json` records three of the four attempts, in write order rather than chronological order: the restart result (`REVISE`, 90), the stalled invocation (`invocation_failed`), and the final result (`READY`, 100) at the current digest. The third chronological attempt, `REVISE` score 88 on digest `21c6c377…` which raised `READY-002`, was deliberately not appended to `state.json` after the `READY` entry, because appending it out of order would make the last recorded readiness look like a `REVISE` at a superseded digest. Its full artifacts are preserved and auditable at `.claude/quality-state/20260915T045020Z-103-account-workspace-directory-기반-codex-0b1ffbac/readiness-spec-r1-v2/` with its own `result.json`, `execution-record.json`, `prompt.md` and `events.jsonl`. Readiness is advisory and decides no state transition, so this affects no gate.
