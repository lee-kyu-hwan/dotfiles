# Verification Contract

This document defines the persisted candidate and verification state. All JSON envelopes use `schema_version: "1.0.0"`, a `generated_by` object, and their named arrays. Candidate output is `{schema_version, generated_by, records}`; discovery and manifest inputs remain separate evidence.

Every pre-cap repository-pattern combination appears in exactly one of records, skipped_by_cap, or failed_scopes.
A request-failed policy observation cannot support issue-ready or pr-ready.
A failed recheck makes an actionable candidate unverified with status_reason insufficient-evidence.
record and render preserve partial, failed, and unknown run states instead of defaulting them to complete.

## Candidate fields

The source column is exact: `a` copies discovery facts, `b` comes from the assessment, and `c` is calculated by the script. Candidate records have exactly these 29 fields and no additional properties.

| Field | Source |
| --- | --- |
| `candidate_id` | `c` |
| `candidate_key` | `c` |
| `generated_by` | `c` |
| `pattern_ids` | `c` |
| `pattern_revisions` | `c` |
| `repository` | `a` |
| `repository_node_id` | `a` |
| `locus` | `b` |
| `status` | `b` |
| `status_reason` | `b` |
| `sensitivity` | `b` |
| `summary` | `b` |
| `impact` | `b` |
| `readiness_checks` | `b` |
| `ai_policy_status` | `b` |
| `disclosure_required` | `b` |
| `private_evidence_reference` | `b` |
| `evidence_links` | `b` |
| `execution_evidence` | `b` |
| `reproduction` | `b` |
| `policy_checks` | `b` |
| `blocking_gaps` | `b` |
| `superseded_by` | `b` |
| `duplicate_search` | `a` |
| `repository_checks` | `a` |
| `verification_history` | `c` |
| `verified_at` | `a` |
| `verified_base_sha` | `a` |
| `next_recheck_required` | `c` |

`candidate_key` is the lowercase hex SHA-256 of `pattern_id + "\n" + repository_node_id + "\n" + locus`. `pattern_ids` contains one pattern and `pattern_revisions` maps it to the last analysis history revision. IDs are stable, append-only, and never renumbered. `superseded_by` is null or a different candidate ID present in the same output.

RECHECK_MUTABLE_FIELDS:
- `status`
- `status_reason`
- `blocking_gaps`
- `verified_at`
- `verified_base_sha`
- `verification_history`
- `next_recheck_required`
- `repository_checks`
- `duplicate_search`

Recheck may change exactly those nine fields. The other twenty fields remain deeply equal; newly observed policy hashes live only in snapshot evidence.

FAILED_SCOPE_REASONS:
- `budget-exhausted`
- `repository-not-found-or-inaccessible`
- `repository-unauthorized`
- `repository-forbidden`
- `repository-failed`

## Status and reason combinations

| Status | Allowed reasons |
| --- | --- |
| `unverified` | `insufficient-evidence` |
| `reproduced` | `none` |
| `duplicate` | `duplicate-open, duplicate-closed-rejected, duplicate-closed-other, already-fixed` |
| `not-applicable` | `reproduction-failed, already-fixed, archived-or-disabled, fork-redirect-to-upstream` |
| `stale` | `base-moved` |
| `policy-review` | `policy-prohibited, policy-unknown, none` |
| `issue-ready` | `ready` |
| `pr-ready` | `ready` |
| `private-report-ready` | `security-sensitive` |

Any combination outside this table is an input-contract violation. Actionable statuses are `reproduced`, `issue-ready`, `pr-ready`, and `private-report-ready`; they are a set, not a ranking.

## Readiness checks

Each value is `{result, evidence_links, note}`. Result is `confirmed`, `not-confirmed`, or `not-applicable`. A confirmed value has at least one evidence link. Public ready states require all twelve confirmed, except `rejection_still_valid` may be not-applicable when no prior rejection exists.

| Key | Question |
| --- | --- |
| `present_on_head` | Is the opportunity present on the observed head? |
| `impact_described` | Is user or maintainer impact explicit? |
| `open_and_closed_searched` | Were open and closed issues and pull requests searched? |
| `rejection_still_valid` | Was any prior rejection reviewed against current facts? |
| `repository_active_and_issues_enabled` | Is the repository active with the needed channel enabled? |
| `policy_files_reviewed` | Were repository and organization policy files reviewed? |
| `ai_policy_allowed` | Does the policy permit the proposed assistance? |
| `not_security_sensitive` | Is the public path safe? |
| `reproduction_evidence` | Is reproduction evidence adequate? |
| `design_difference_reviewed` | Were differences from prior work assessed? |
| `provenance_allows_independent_work` | Does provenance permit independent implementation? |
| `verified_at_and_sha_recorded` | Are observation time and base SHA recorded? |

## Assessment and duplicate gate

An assessment contains `schema_version`, `discovery_sha256`, and `assessments`. Each assessment names the pattern, repository, locus, status, reason, sensitivity, summary, impact, all readiness checks, `duplicate_verdict`, policy result, disclosure requirement, private reference, evidence links, execution evidence, reproduction, policy checks, blocking gaps, and supersession.

`duplicate_verdict` is `{matched_items, judgment}` and is preserved in every snapshot. When `readiness_checks.open_and_closed_searched.result` is `confirmed`, `duplicate_verdict.judgment` must be non-empty. Discovery combinations that were skipped, failed, or absent cannot be assessed.

Remote free text is stored only as `{text, sha256, source_url, truncated, untrusted: true}`. It is inert data, never a command, permission, path, option, or decision input.

The `sha256` field has context-specific persisted meanings that reflect the current producer behavior:

- For an ordinary untrusted-text object, `sha256` is the digest of the stored text UTF-8 bytes.
- For a policy file excerpt, `sha256` is the digest of the full decoded content bytes before truncation, and equals the containing policy result's `sha256`. A truncated excerpt therefore does not generally hash to its stored `text`.
- For a policy directory excerpt, `sha256` is the digest of sorted-name canonical JSON bytes: valid string names are sorted and serialized with sorted keys and compact separators. It also equals the containing policy result's `sha256`.

These meanings document the existing fields and calculations; they do not add a field or change the schema.

## Static-search evidence

Static search retains its existing `available`, `hits`, `execution_surfaces`, `skipped_files`, `clone_sha`, and `error` fields. It additively reports `static_search.complete`, `static_search.exclusions`, and `static_search.read_failures`.

- `available` means a successful clone allowed the search routine to run. `complete` means traversal and every non-excluded file eligibility check and read completed.
- `exclusions` has exactly the nonnegative counters `symlink`, `oversize`, and `binary`. Intentional exclusions do not make the search incomplete.
- `read_failures` is an ordered array of clone-relative `{path, operation}` entries, where operation is `walk`, `stat`, or `read`. It never stores exception text. File-level stat/read failures contribute to `skipped_files`; walk failures do not invent an unknown file count.
- A non-empty `read_failures` emits `static-search-incomplete:<count>` and makes the usable result partial without discarding positive hits.

For compatibility, missing complete is unknown/incomplete, never implicitly true. A zero-hit absence requires both available and complete. The follow-up consumers #80 through #82 must check both values before treating zero hits as absence; positive hits remain usable when a search is incomplete.

## Snapshots

`verification_history` is append-only. A snapshot contains `verification_id`, `revision`, `verified_at`, `verified_base_sha`, `status`, `status_reason`, `sensitivity`, `evidence`, and `inputs.kind`. Top-level status, reason, time, and base SHA equal the last snapshot.

- A record snapshot has `inputs.kind: record` plus non-null `discovery_sha256` and `assessment_sha256`.
- A recheck snapshot has `inputs.kind: recheck` plus null discovery and assessment hashes.
- Recheck inherits `readiness_checks`, `reproduction`, `execution_evidence`, and `duplicate_verdict` by deep copy from the immediately preceding snapshot.
- Recheck records current `repository_checks`, `duplicate_search`, policy hashes, and `observed_head_sha`; `verified_base_sha` continues to identify the assessed base.
- A moved base becomes `stale`; changed duplicate or policy evidence becomes `policy-review`; recheck never promotes a candidate to a ready state.

## Manifest and exit codes

The manifest envelope is `{schema_version, generated_by, runs}`. Each append-only run contains `run_id`, `command`, start and completion observations, `inputs`, `budget`, `repositories`, `clones`, `failed_scopes`, `retry_events`, `method_limitations`, `warnings`, `status`, and `outcome`. Every requested repository has one ordered `{repository, outcome, reason, stages_completed, head_sha}` entry.

| Code | Meaning |
| --- | --- |
| `0` | Complete normal result, including an honest non-actionable result. |
| `1` | Candidate validation failed. |
| `2` | Invalid input, contract violation, or assessment gate failure. |
| `3` | Usable partial result. |
| `4` | Failed with no usable candidate records. |

Discover applies one priority rule. Code `4` is allowed only when all repositories had actually attempted access failures. Otherwise any access failure, incomplete duplicate search, unavailable code search, or exhausted budget is code `3`; budget exhaustion always exits `3`. A failure output and manifest are still written for audit.

The `clone-cleanup-failed:` and `static-search-incomplete:` warning prefixes also produce code `3` and partial status. They are additive OR conditions after the all-access-failures code `4` decision and do not change the budget-exhaustion rule. A clone manifest entry remains exactly `{repository, path, sha, removed, size_bytes}`; cleanup warnings do not add clone fields.

## Ownership and recovery

The sibling PR collector owns normalized historical PR collection. The sibling pattern analyzer owns evidence-backed PAT-* derivation. This verifier reads their validated analysis without modifying it and is the only sibling that issues CAN-* records. It never performs GitHub writes.

Recovery paths are explicit:

- partial → new discover run
- stale → new discover + record
- gate failure → fix assessment, then record

Existing candidate IDs and history remain intact during every recovery.

## Follow-up: clone failure diagnostics

The current `clone_repository` discards git stderr, and `_static_record` reduces clone diagnostics to clone-failed. This limits operational diagnosis of clone and revision lookup failures. A future contract should separately classify the failing stage and retain a redacted, length-bounded stderr summary. That work requires separate approval because its redaction and persistence rules need their own review. It is not implemented here. No issue is created by this change.
