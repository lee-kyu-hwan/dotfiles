# Extraction Contract

## Mechanical and judgment work

Pattern extraction means reading PR text and judging what recurs. Scripts do everything that needs no judgment, and they gate every judgment with a mechanical check.

| Step | Kind | Tool |
| --- | --- | --- |
| Validate the corpus | mechanical | `scripts/validate_corpus.py CURRENT` |
| Build the digest and shards | mechanical | `scripts/build_digest.py` |
| Write worker prompts | mechanical | `scripts/build_prompts.py extract` / `verify` |
| Extract patterns and observations | judgment | independent worker calls |
| Check quotes and distinct PRs | mechanical | `scripts/check_extraction.py` |
| Synthesize candidates | judgment | coordinator |
| Adversarially verify each candidate | judgment | independent worker calls |
| Accept or reject | judgment above mechanical floors | coordinator, then `validate_corpus.py --analysis-output` |

The output validator used to check only shape, so an envelope serialized with `patterns: []` passed without anyone reading the PRs. It now rejects a current pattern without two distinct evidence PRs and a verbatim quote for each, and an output without the extraction ledger. An empty `patterns` array remains valid only as a recorded outcome of this procedure.

## Digest and split rule

`build_digest.py CURRENT --out DIR` renders one section per PR headed `### <key> — <title>`. The key is `<repository name>#<number>`, or `<owner>/<name>#<number>` when two repositories share a name. It keeps the title, the body up to 1,500 characters, the first 20 non-lockfile diff excerpts up to 900 characters each, commit subject lines, up to 30 items per discussion category at 700 characters each, timeline event counts with closed, merged, reopened, and labeled excerpts, and linked issues of the PR's own repository. Cross-reference events and linked issues from other repositories never enter the digest or count as quotable text: the collector derives linked issues from cross-references, authenticated snapshots can reach private repositories, and the digest leaves the machine whenever a model service answers a prompt. HTML comments are dropped, cuts are marked `…[+N chars]`, and free text is indented so that only section headers start a line with `### `. Keys, `url:`/`repository:`/`state:` lines, file-list headers, author markers, and cut markers are digest scaffolding, not source text, so they can never be quoted.

The split criterion is size, never repository or corpus:

- When all sections fit in `--max-bytes` (default 160,000 UTF-8 bytes, roughly 40–50k tokens), the digest is one file and every worker reads every PR. Parallelism comes from lenses, so recurrence across repositories stays visible. The 2026-09-06 run of 13 PRs is about 70 KB.
- Above the budget, sections are interleaved across repositories and packed into shards `digest-01.md`, `digest-02.md`, and so on, so shards mix repositories as far as the repository counts allow. Recurrence across shards is recovered in candidate synthesis from each shard's observations, and each candidate's verification prompt carries its cited sections in full plus a title index of every other PR.
- A single PR section above the budget is an error. Raise `--max-bytes`; never drop a PR.

One investigation is one corpus. When collection produced several corpora, have them combined into one before analysis. PR-* IDs are unique only inside a corpus and the verifier reads one analysis output, so a pattern that spans corpora cannot otherwise be recorded.

## Lenses

`build_prompts.py extract --digest-dir DIR --out RUN/extract` writes one prompt per shard and lens into `RUN/extract/prompts/`: `blind` (no restriction), `correctness`, `structure`, `maintenance`, and `review`. Run all five by default. The blind lens catches what the focused lenses miss, and the focused lenses read deeper. Each prompt asks for `patterns` (behavior seen in two or more PRs), `observations` (single-PR behavior), and `rejected` ideas, with a verbatim quote on every piece of evidence.

## Running prompts

Every prompt file is the whole input of one independent, tool-less call whose answer is one JSON object saved as `<run>/results/<prompt stem>.result.json`. `build_prompts.py` empties `<run>/prompts` and `<run>/results` before writing, and refuses a run directory that holds the other kind of prompt, so extraction and verification never share or reuse stale files. Choose the executor by availability:

1. `agy` is on `PATH`: follow the `dispatching-agy-workers` skill, for example `python3 <that skill>/scripts/agy_fanout.py RUN/extract/prompts/*.md --out RUN/extract/results --expect-json`. This keeps the digest out of the coordinator's context and Claude/Codex usage small.
2. No `agy`: give each prompt file to its own sub-agent without tools, and save its JSON answer.
3. No sub-agents: answer each prompt file yourself, one at a time, and save each answer the same way. This is slower and spends coordinator context; nothing else changes.

A missing executor never skips extraction. Record the executor in the ledger.

## Checking

`check_extraction.py CURRENT RUN/extract/results/*.result.json` checks every `pr` + `quote` pair against that PR's source text in the corpus, with the same comparison the output validator uses. A quote is 20–300 characters inside one title, body, diff excerpt, commit message, discussion excerpt, or own-repository linked issue after HTML comments are dropped and whitespace is collapsed. Stitched (`...`), reworded, or re-quoted text fails. Exit 1 means some quotes failed. Drop those quotes and never repair them. The report lists, per extraction pattern, the distinct PRs whose supporting quote verified, and per verification, the PRs whose `holds: true` check verified. `verified_evidence` lists every verified quote with its PR-* ID.

## Candidate synthesis

Read every result's patterns, observations, and rejected ideas together with the check report. Merge items that describe the same behavior across lenses and shards. Observations of the same behavior in different PRs form a candidate even when no single worker saw both. Write `candidates.json` as `[{"id": "C1", "statement": "...", "cited_prs": ["<key>", ...], "found_by": "..."}]`, citing only PRs with a verified quote. Extractor confidence is not evidence and is not copied.

## Adversarial verification

`build_prompts.py verify --digest-dir DIR --candidates candidates.json --out RUN/verify` writes one prompt per candidate into `RUN/verify/prompts/`. Run each as a new independent call into `RUN/verify/results/` and check those results again. The verifier looks for counterexamples in the uncited PRs, counts distinct PRs and repositories, judges whether the candidate points to a defect class that can find contributions elsewhere, and grades confidence.

## Acceptance

A candidate becomes a `PAT-*` only when all of these hold:

- At least two distinct PRs with analyzed PR-* records support it. A PR supports it when a verified quote from extraction or verification backs it and the verifier did not judge it `holds: false`. The output validator enforces the two PRs and their quotes.
- The verdict is `supported` or `weak`, and the verifier judged the candidate actionable, meaning it points to a defect class that can find contributions elsewhere. A `weak` acceptance is `low` confidence, and its caveats go into `confidence.limitations`.
- No verified counterexample contradicts the statement. A counterexample that only narrows it becomes a countercondition.

Confidence comes from the verifier and is capped. Evidence from one repository is at most `medium`. Support that rests on a closed-unmerged PR or on a bot's claim is at most `medium`, and support only from closed-unmerged PRs is `low`. Partial required evidence prevents `high`.

Reuse an existing `PAT-*` for the same behavior. New IDs continue after the greatest numeric suffix. Existing patterns are never dropped. An existing pattern keeps its ID while two PRs still support it, even when the verdict is `weak` or it is not actionable, and `confidence.limitations` says so. An existing pattern that loses its two supporting PRs is superseded by an accepted pattern, or the run stops and reports it.

Map an accepted candidate to the pattern record this way:

- `description` is the verifier's revised statement.
- `evidence_pr_ids` are the PR-* IDs of the verified supporting PRs.
- `confidence.evidence` holds at least one quote entry `PR-005 "<verified quote>"` per evidence PR, plus free-text reasons.
- `counterconditions` includes counterexamples that narrow the pattern.
- `search_clues`, `expected_tests`, and `maintainer_judgment_required` come from the extraction and verification results.

## Ledger

`limitations` holds exactly one entry that starts with `pattern-extraction: `. Record the digest size and shard count, the lenses, the executor, quote counts, candidates, accepted IDs, and each rejected candidate with its reason, for example:

```text
pattern-extraction: digest 70286 B in 1 shard; lenses blind,correctness,structure,maintenance,review; executor agy gemini-3.1-pro-low; quotes extraction 25/30, verification 18/20; candidates C1-C7; accepted C1→PAT-002, C7→PAT-003, C3→PAT-001 kept (not actionable); rejected C2 and C6 (one supporting PR after verification), C4 (not actionable), C5 (counterexample eslint-plugin-promise#590)
```

Keep the digest, keymap, prompts, results, check reports, and `candidates.json` next to the output. They share the corpus's privacy: local research artifacts, not publication material.
