# Data Contract

## Input and validation

Accept only a normalized corpus envelope with `schema_version: "1.0.0"` and `records`. Before analysis, run `python3 scripts/validate_corpus.py CURRENT [--existing PREVIOUS_CORPUS]`. `--existing` accepts only a previous normalized corpus for append-only comparison. Read optional existing enriched PR and PAT outputs separately to preserve IDs and histories; they are not `PREVIOUS_CORPUS` unless an enriched PR corpus independently satisfies the normalized-corpus contract.

An unsupported schema version stops analysis and requires an explicit versioned migration with stated input/output versions and conversion rules. An invalid `1.0.0` corpus stops analysis and requires corrected input. A failed append-only or preservation comparison stops analysis until the conflict is resolved. Never automatically retry, silently repair, downgrade, or reinterpret any of these cases.

## Identity and append-only state

`identity_status` is `resolved` only when the PR and repository identities are verified. A resolved record uses `record_key: github-pr:<pull_request_node_id>`; an unresolved record retains its observed URL but has no PR ID and is not automatically merged by guesswork.

Existing resolved identity mappings and IDs win. For a newly resolved identity, allocate the next `PR-*` after the maximum existing numeric ID. Never fill gaps, recycle, renumber, or reorder IDs. Existing `PAT-*` IDs follow the same stable rule. Preserve all historical arrays exactly as prefixes: `state_history`, each source's `observations`, `analysis_history`, and any existing pattern history or evidence snapshots. Append new observations or analysis; use `superseded_by` instead of erasing a conclusion.

## Interpretation boundary

Keep observed facts and their sources separate from analysis. Record changed facts, stated or evidenced motivation, maintainer review judgment, and closure reason in distinct fields. Label an interpretation as inference, identify its support, and leave it unknown when evidence does not support it. State alone is not a reason or judgment.

## Side effects and recovery

The analyzer reads supplied local artifacts and may write only requested enriched local outputs. It never edits input in place or creates external state. It does not automatically retry or silently repair a version, validation, identity, preservation, or unavailable-evidence failure; report the limitation and await the required migration, corrected input, resolved conflict, or evidence.
