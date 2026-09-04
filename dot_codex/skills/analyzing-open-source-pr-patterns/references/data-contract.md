# Data Contract

## Input and validation

Accept only a normalized corpus envelope with `schema_version: "1.0.0"` and `records`. Before analysis, resolve `SKILL_DIR` to the absolute directory containing `SKILL.md`, then run:

```text
python3 "$SKILL_DIR/scripts/validate_corpus.py" --print-revision
python3 "$SKILL_DIR/scripts/validate_corpus.py" CURRENT [--existing PREVIOUS_CORPUS]
```

`--existing` accepts only a previous normalized corpus for append-only comparison. Optional prior enriched output is instead passed to `--existing-analysis` during output validation.

An unsupported schema version stops analysis and requires an explicit versioned migration with stated input/output versions and conversion rules. An invalid `1.0.0` corpus stops analysis and requires corrected input. A failed append-only or preservation comparison stops analysis until the conflict is resolved. Never automatically retry, silently repair, downgrade, or reinterpret any of these cases.

## Identity and append-only state

`identity_status` is `resolved` only when the PR and repository identities are verified. A resolved record uses `record_key: github-pr:<pull_request_node_id>`; an unresolved record retains its observed URL but has no PR ID and is not automatically merged by guesswork.

Existing resolved identity mappings and IDs win. Never fill gaps, recycle, renumber, or reorder IDs. Existing `PAT-*` IDs follow the same stable rule. Preserve `state_history`, `analysis_history`, pattern history, and evidence snapshots exactly as prefixes.

For normalized-corpus `--existing` comparison, the previous `sources[].source_key` sequence must be an exact prefix of the current sequence: new sources append only. For each prior source, every field other than `observations` is immutable and deep-equal. Its previous `observations` array must be an exact prefix of the current array. Reordering sources, inserting before them, or rewriting `kind`, `run_key`, URLs, node IDs, or other metadata is invalid.

Analysis output preserves every normalized field and type. Resolved records match by `pull_request_node_id`; unresolved records match only by the observed `pull_request.url`. The only analysis additions are the current `analysis` projection and append-only `analysis_history` described in the analysis contract.

## Deterministic analysis revision

`--print-revision` returns `sha256:<64 lowercase hex>`. It hashes these six relative paths in sorted order:

```text
SKILL.md
agents/openai.yaml
references/analysis-contract.md
references/data-contract.md
scripts/validate_corpus.py
tests/test_validate_corpus.py
```

For each path, the canonical byte sequence is: its UTF-8 path-byte length as an unsigned 8-byte big-endian integer, its UTF-8 path bytes, its raw-content length in the same integer format, then its raw file bytes. Concatenate those six framed entries and take SHA-256. The path is relative, so byte-identical source and installed trees have the same revision.

Use that value for the envelope `analysis_generated_by.revision`, every current record snapshot, every current pattern `generated_by.revision`, and every current pattern snapshot.

## Output validation

After writing a separate output file, run:

```text
python3 "$SKILL_DIR/scripts/validate_corpus.py" CURRENT \
  --analysis-output OUTPUT [--existing-analysis PREVIOUS_OUTPUT]
```

`--existing-analysis` is valid only with `--analysis-output`. This command validates the normalized input, exact output shape and types, record preservation, current projections/snapshots, and optional append-only PR/pattern histories. A JSON read, UTF-8 decode, schema, shape, identity, type, or preservation error exits 1 with concise stderr and no traceback.

## Interpretation boundary

Keep observed facts and their sources separate from analysis. Record changed facts, stated or evidenced motivation, maintainer review judgment, and closure reason in distinct fields. Label an interpretation as inference, identify its support, and leave it unknown when evidence does not support it. State alone is not a reason or judgment.

## Side effects and recovery

The analyzer reads supplied local artifacts and may write only requested enriched local outputs. It never edits input in place or creates external state. It does not automatically retry or silently repair a version, validation, identity, preservation, or unavailable-evidence failure; report the limitation and await the required migration, corrected input, resolved conflict, or evidence.
