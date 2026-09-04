# Analysis Contract

## Exact output envelope

The enriched JSON has exactly these top-level fields:

```text
{
  schema_version: "1.0.0",
  generated_by: exact deep copy of input generated_by,
  analysis_generated_by: {
    name: "analyzing-open-source-pr-patterns",
    revision: current deterministic sha256 revision
  },
  records: [EnrichedRecord],
  patterns: [PatternRecord],
  limitations: [string]
}
```

No additional top-level field is valid. In particular, no `CAN-*` field or record is valid.

## Reusable analysis types

```text
EvidenceClaim = {
  value: string | null,
  basis: "fact" | "inference" | "unknown",
  evidence_links: [string]
}

Confidence = {
  level: "high" | "medium" | "low",
  evidence: [string],
  limitations: [string]
}

AnalysisProjection = {
  change_summary: EvidenceClaim,
  motivation: EvidenceClaim,
  review_judgment: EvidenceClaim,
  closure_reason: EvidenceClaim,
  files_changed: [string],
  test_evidence: [EvidenceClaim],
  pattern_ids: ["PAT-..."],
  evidence_links: [string],
  evidence_manifest: object,
  license_spdx: string,
  provenance_mode: "independent-reimplementation" | "adapted" | "verbatim",
  confidence: Confidence,
  superseded_by: string | null
}

AnalysisSnapshot = {
  revision: "sha256:<64 lowercase hex>",
  generated_at: RFC3339 string,
  evidence_manifest: object,
  conclusion: AnalysisProjection
}
```

For each input record, preserve every normalized field and its JSON type. Present records in any order, but retain all identities, IDs, normalized values, source ordering/metadata, and normalized histories. Match resolved records by PR node identity and unresolved records by their observed PR URL. Add exactly `analysis` and `analysis_history` as analysis fields.

`analysis` is the current `AnalysisProjection`. `analysis_history` is the exact input or prior-output history prefix plus exactly one `AnalysisSnapshot` for this run. Preserve every old item exactly even if it predates the strict shape. The newest snapshot revision equals the envelope revision; its `evidence_manifest` equals the current projection manifest; its `conclusion` deep-equals the current projection.

Keep changed facts, motivation, review judgment, and closure reason distinct. A merged PR can support an accepted-change conclusion. `closed-unmerged` establishes only that it was not merged; rejection, judgment, and reason require direct evidence. State transitions, chronology, review disposition, and maintainer judgment are not themselves closure-rationale evidence. When the normalized closure reason is `unknown` and no direct rationale is present, the current projection uses exactly:

```json
{"value": null, "basis": "unknown", "evidence_links": []}
```

## Pattern records

```text
PatternProjection = {
  pattern_id: "PAT-...",
  description: string,
  generated_by: {
    name: "analyzing-open-source-pr-patterns",
    revision: current deterministic sha256 revision
  },
  evidence_pr_ids: ["PR-..."],
  applicability: [string],
  counterconditions: [string],
  search_clues: [string],
  expected_tests: [string],
  maintainer_judgment_required: [string],
  source_licenses: [{ pr_id: "PR-...", spdx_id: string }],
  provenance_mode: "independent-reimplementation" | "adapted" | "verbatim",
  confidence: Confidence,
  superseded_by: string | null
}

PatternRecord = PatternProjection + {
  pattern_history: [{
    revision: "sha256:<64 lowercase hex>",
    generated_at: RFC3339 string,
    conclusion: PatternProjection
  }]
}
```

Every pattern uses this one shape; `source_license` is not an alternative field. The newest pattern snapshot conclusion deep-equals the current projection and its revision equals the current deterministic revision. A new pattern starts with one snapshot. Every existing pattern remains present with the same stable ID, its old `pattern_history` as an exact prefix, and exactly one new snapshot. Old history items may use a legacy shape and remain unchanged.

Create a pattern only for genuinely recurring behavior. A single PR may support a low-confidence observation, not a confident universal rule. State both applicability and counterconditions.

## Evidence, confidence, license, and boundary

`evidence_manifest` records `files`, `commits`, `issue_comments`, `reviews`, `review_comments`, and `timeline` separately. For each category, retain its endpoint or local alternative, page completeness, returned count, known limit, observation time, and warnings. Do not merge comment categories. Partial or selected required evidence without an adequate alternative prevents `high` confidence and becomes an explicit limitation.

Use `license_spdx: "NOASSERTION"` when a record's source license is unknown. Pattern `source_licenses` retains one object per supporting PR. Default provenance to `independent-reimplementation`. `adapted` and `verbatim` require compatible licenses and review evidence; an unknown license never supports copied code.

Emit only the exact schema-`1.0.0` envelope above. The analyzer does not collect live PRs, browse or clone repositories, validate candidates, create external state, or create `CAN-*`. When asked for candidates, end with: "Handoff to the verifier: validate the applicable PAT-* records against the requested candidate scope before creating any CAN-* record."
