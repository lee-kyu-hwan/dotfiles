# Verification

Use the repository's fixed Python 3.14.7 interpreter. Spec CMD-4 records
`python3 -VV`, asserts the exact `(3, 14, 7)` tuple, and then runs a non-empty
source suite. The live API case is collected but normally skipped because its
opt-in environment variable is unset, so this deterministic gate makes no model
calls. Type checking, linting, and builds are **not configured** and must be
reported that way rather than as passing checks.

| Driver | Purpose and pass condition |
|---|---|
| DRV-1 | Run the complete source suite with the fixed interpreter; require exit code 0 and a non-empty selection. This is the suite boundary in Spec CMD-4. |
| DRV-2 | Check argument parsing and defaults. This contributes to Spec CMD-2. |
| DRV-3 | Check producer selection and Claude/Codex command contracts. This contributes to Spec CMD-2. |
| DRV-4 | Scan the whole skill for forbidden Codex options; only a successful no-match result passes. This contributes to Spec CMD-2. |
| DRV-5 | Scan the whole skill for GitHub write commands; only a successful no-match result passes. This contributes to Spec CMD-2. |
| DRV-6 | Check the read-only, no-mutation, textual-source scanner contract. This contributes to Spec CMD-2. |
| DRV-7 | Check prompt delivery, cleanup, prompt identity, and every start-before-first-read boundary. This is the targeted lifecycle boundary in Spec CMD-1. |
| DRV-8 | Check the recursively closed reviewer schema and empty-findings acceptance. This contributes to Spec CMD-2. |
| DRV-9 | Check the recursively closed critique schema and evidence invariants. This contributes to Spec CMD-2. |
| DRV-10 | Check the recursively closed synthesis schema and fresh-Claude boundary. This contributes to Spec CMD-2. |
| DRV-11 | Check required package files, deployable component names, cache exclusion, and source/archive relative-path equality. This covers the contract portion of Spec CMD-2 and the archive boundary in Spec CMD-5. |
| DRV-12 | Check valid-producer gates, explicit no-findings handling, failure provenance, and entrypoint exit mapping. This is the deterministic behavior boundary in Spec CMD-3. |
| DRV-13 | Check project-local slash dispatch and its no-changes provenance in the isolated harness described by Spec CMD-6. |
| DRV-14 | Opt in to real reviewer, critique, and synthesis schema calls only in the dedicated evidence harness described by Spec CMD-7. |
| DRV-15 | Run the guarded product-repository end-to-end harness only after its branch, cleanliness, diff, and preserved-run preconditions pass, as described by Spec CMD-8. |

Spec CMD-5 first creates and confirms a real `__pycache__` fixture, archives
without changing `$HOME`, compares cache-excluded source and archive relative
paths literally, requires zero cache and marker entries, runs the complete
suite from the extracted deployment, and cleans both fixture and archive.

Spec CMD-7 is the only live API schema gate, and Spec CMD-8 is the only product
repository E2E gate. They are intentionally excluded from the default source
suite and are run by the orchestrator only with their explicit preconditions
and evidence locations.

DRV-4 and DRV-5 scan this entire skill directory, including hidden and ignored
files. Their patterns are intentionally not reproduced here. Where a name is
needed, use the safe placeholders `<forbidden-codex-option-N>` and
`<github-write-command-N>`.
