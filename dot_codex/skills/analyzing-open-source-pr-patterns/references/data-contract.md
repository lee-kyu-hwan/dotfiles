# Data Contract

## Input and validation

Accept only a normalized corpus envelope with `schema_version: "1.0.0"` and `records`. Before analysis, run `scripts/validate_corpus.py CURRENT`; when prior corpus data exists, run `scripts/validate_corpus.py CURRENT --existing EXISTING`. An unsupported version, invalid document, or failed preservation comparison stops analysis and requires an explicit migration with stated input/output versions and conversion rules. Never silently repair, downgrade, or reinterpret a version.

## Identity and append-only state

`identity_status` is `resolved` only when the PR and repository identities are verified. A resolved record uses `record_key: github-pr:<pull_request_node_id>`; an unresolved record retains its observed URL but has no PR ID and is not automatically merged by guesswork.

Existing resolved identity mappings and IDs win. For a newly resolved identity, allocate the next `PR-*` after the maximum existing numeric ID. Never fill gaps, recycle, renumber, or reorder IDs. Existing `PAT-*` IDs follow the same stable rule. Preserve all historical arrays exactly as prefixes: `state_history`, each source's `observations`, `analysis_history`, and any existing pattern history or evidence snapshots. Append new observations or analysis; use `superseded_by` instead of erasing a conclusion.

## Interpretation boundary

Keep observed facts and their sources separate from analysis. Record changed facts, stated or evidenced motivation, maintainer review judgment, and closure reason in distinct fields. Label an interpretation as inference, identify its support, and leave it unknown when evidence does not support it. State alone is not a reason or judgment.

## Side effects and recovery

The analyzer reads supplied local artifacts and may write only requested enriched local outputs. It never edits input in place or creates external state. It does not automatically retry a failed validation, migration, identity conflict, or unavailable evidence; report the limitation and stop or await corrected input.
