---
name: analyzing-open-source-pr-patterns
description: Use when analyzing an already normalized corpus of open-source pull requests to extract evidence-backed, reusable change patterns. Do not use for PR collection, live candidate validation, or personal GitHub work logs.
---

# Analyze Open-Source PR Patterns

Analyze only the supplied local normalized corpus and optional existing local PR/pattern outputs. Read [the data contract](references/data-contract.md) and [the analysis contract](references/analysis-contract.md) before producing results.

1. Run `python3 scripts/validate_corpus.py CURRENT [--existing PREVIOUS_CORPUS]`. `PREVIOUS_CORPUS` is only a previous normalized corpus. Read optional existing enriched PR/PAT outputs separately to preserve IDs/history; do not pass them to `--existing` unless an enriched PR corpus itself satisfies the normalized-corpus contract. Support schema `1.0.0` only: an unsupported version stops for an explicit versioned migration, an invalid `1.0.0` corpus stops for corrected input, and a preservation conflict stops until resolved. Never retry or repair these cases automatically.
2. Preserve existing identity mappings, IDs, and every historical array. Existing IDs win. Allocate a `PR-*` only for a newly resolved identity, after the current maximum; never fill gaps, reorder IDs, or give an unresolved record a PR ID. Preserve stable `PAT-*` IDs and supersede rather than replace conclusions.
3. For each PR, record changed facts, motivation, review judgment, and closure reason as distinct fields. Attribute evidence and mark inference or unknowns. A `closed-unmerged` state alone does not establish rejection or its reason.
4. Grade every evidence category independently and set confidence from its completeness and alternatives. Missing or partial required content without an alternative source cannot be high confidence; report the limitation.
5. Create a pattern only for genuinely recurring behavior. One PR is an observation, not a confident universal pattern. State positive applicability, counterconditions, search clues, expected tests, and maintainer decisions still required.
6. Record the source license. Default to `independent-reimplementation`; do not propose copied code when the license is unknown. Use `adapted` or `verbatim` only with compatibility and review evidence.
7. Emit only schema-`1.0.0` enriched `PR-*`, `PAT-*`, and explicit limitations. Do not collect live PRs, browse or clone candidate repositories, create external state, or emit `CAN-*`. End candidate requests with an explicit handoff to the verifier.

Capabilities are local historical analysis and requested local output writing only; never mutate the supplied input in place. Do not automatically retry or silently repair version, validation, identity, preservation, or missing-evidence failures: report the condition and await the required migration, corrected input, resolved conflict, or evidence. Stop on unsupported schema, invalid corpus, unresolved identity needing an ID, or a preservation conflict.
