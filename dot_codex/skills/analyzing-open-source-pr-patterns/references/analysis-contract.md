# Analysis Contract

## PR records

For each resolved analyzed record, retain `pr_id`, `analysis_generated_by`, and append-only `analysis_history`; enrich the current projection with `change_summary`, `motivation`, `files_changed`, `test_evidence`, `review_summary`, `closure_reason`, `pattern_ids`, `evidence_links`, `evidence_manifest`, `license_spdx`, `provenance_mode`, `confidence`, and `superseded_by`. Preserve the supporting source, fact/inference status, and uncertainty for each conclusion.

`evidence_manifest` separately records `files`, `commits`, `issue_comments`, `reviews`, `review_comments`, and `timeline`. For every category, record the endpoint or local alternative, `pages_complete`, `returned_count`, known limit, observation time, and warnings. Do not merge comment categories. If a required category is partial or selected content and no adequate alternative source exists, confidence cannot be `high`; state the resulting limitation. A merged PR can support an accepted change conclusion. A closed-unmerged PR establishes only that it was not merged; rejection and its reason require direct evidence.

## Pattern records

Each `PAT-*` record includes `pattern_id`, description, `generated_by`, `evidence_pr_ids`, positive applicability, non-applicability/counterconditions, search clues, expected tests or reproduction, maintainer judgment required, source license, `provenance_mode`, confidence and its evidence/limitations, and `superseded_by`. Use a stable existing pattern ID when its identity remains the same; append a replacement and link it when its meaning changes. Do not turn one PR into a confident universal pattern: it may be a low-confidence observation with explicit limits, not a broadly reusable conclusion.

Use `license_spdx: NOASSERTION` when the source license is unknown. Default `provenance_mode` to `independent-reimplementation`. `adapted` and `verbatim` require compatibility and review evidence; unknown license never supports copied code.

## Output boundary

Emit schema `1.0.0` enriched `PR-*`, `PAT-*`, and explicit limitations only. The analyzer does not collect live PRs, browse or clone repositories, validate candidates, create external state, or create `CAN-*`. When asked for candidates, end with: "Handoff to the verifier: validate the applicable PAT-* records against the requested candidate scope before creating any CAN-* record."
