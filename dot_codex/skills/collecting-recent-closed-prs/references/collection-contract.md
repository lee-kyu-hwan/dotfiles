# Collection artifacts and handoff

## Inputs

Use the bundled script's `--help` for exact accepted options. The `collect`
subcommand receives repeated `--repo owner/name`, a `--timezone`, output corpus
and manifest paths, and exactly one interval mode:

- `--start-at` and exclusive `--end-at`: RFC 3339 timestamps.
- `--start-date` and inclusive `--end-date`: local calendar dates.
- `--recent-days` and optional `--as-of`: local days ending at capture time.

Seven recent days means six complete local days plus the current partial day.
The script stores original inputs and resolved UTC bounds. Defaults are
outcome `all`, `--max-per-repo 25`, `--request-budget 1000`, and API version
`2026-03-10`. Repositories, output paths, and timezone are caller choices.
Malformed inputs fail before GitHub requests. Existing output paths are only
replaced as part of the explicitly requested output operation.

## Corpus 1.0.0

The corpus envelope contains `schema_version: "1.0.0"`, `generated_by` with
name/revision, and `records`. Resolved identity uses global PR node ID and
`github-pr:<node_id>`. Repository node+PR number is corroboration; a shared URL
cannot override conflicting node identities. Unresolved entries have null
PR IDs. Repository aliases preserve renamed names.

Existing non-null PR IDs never change or get reused. New IDs start after the
greatest numeric suffix and are allocated deterministically. Inputs are copied;
unknown JSON fields/types and existing history/source prefixes are preserved.
`recent-closed` is one stable source key; observations append by complete
`run_id + updated_at + body_sha256` identity. Existing legacy observations
remain intact. Do not synthesize these facts when core evidence is unavailable.

The latest authoritative timestamp controls the materialized PR state and
evidence. Earlier observations remain in append-only history. Missing core
authority must not manufacture a closed state or state-history event. Evidence
text fills body/change/discussion excerpt slots without interpreting motive,
review judgment, reusable patterns, or contribution candidates.

## Manifest 2.0.0

The manifest is a separate envelope with `schema_version: "2.0.0"`,
`generated_by`, and `records` containing collection runs. Each run records its
stable run_id, request fingerprint, original/resolved interval, timezone,
as_of, current-day coverage, ordered repositories, outcome, cap, budget,
API/client versions, method limitations, repository outcomes/counts, exact
partitions, selected PR completeness, consumed requests, retry/conditional
events, timestamps, warnings, and final status.

Complete means the declared capped scope and required evidence were processed;
it does not mean an uncapped census or a perfect GitHub index. Known access,
partition, evidence, and budget gaps are partial. Global preflight failure or
no usable valid corpus is failed. Current-day coverage is explicit even when
the bounded interval through as_of is fully processed.

Resume uses the existing run_id and fingerprint. The fingerprint includes
repository order, resolved interval, timezone/input mode, outcome, cap, budget,
and API version. Changed inputs fail before network access. Completed leaves
and complete PR evidence are reusable; partial work needs retry. Preserve the
previous observation and capture new completion evidence.

Use `--resume-run-id` explicitly with the existing corpus and manifest. Without
it, collection appends a new run and preserves older runs. For recent-day
resume, pass the original `--as-of` so the resolved interval does not drift.
The original request budget includes previous attempts; resume does not reset
it. An exhausted budget requires a new run with a suitable budget, not a
changed fingerprint on the old run. Safe-leaf and completed-PR checkpoints
survive later failures, including a failed resume preflight.

JSON artifacts use UTF-8 and trailing newlines. Atomic replacement uses a
temporary file beside its destination, preserving the prior file on failed
replacement. Markdown is rendered from successfully saved JSON and puts a
partial warning plus failed scopes before the inventory. Show per-repository
matched/selected/excluded counts and sampling limits.

## Migration and exit status

`migrate-manifest --input V1 --output V2` explicitly migrates legacy 1.0.0:
runs→records, run_key→run_id, kind→collection_method,
captured_at→completed_at, github_api_version→api_version,
github_cli_version→client_version. Unknown started_at is null. Remaining
legacy JSON is retained under legacy_payload. Migration warnings explain
missing facts; historical runs remain partial. Same-file replacement requires
the explicit replacement option.

Exit 0 is complete collection or successful migration/validation; 2 is invalid
input, unsupported version, or incompatible resume; 3 is partial with usable
output; 4 is failure without usable output. Never report exit 3 as complete.

Before offline analysis, validate saved corpus with the adjacent analyzer's
`scripts/validate_corpus.py`; use `--existing` when proving preserved history.
If partial identity/core evidence fails its input contract, retain the failure
evidence and explain that handoff is incomplete. Never fabricate state history
to satisfy validation. Candidate validation and GitHub writes require their
own workflow and authorization.

Core evidence that cannot support a valid observation is retained under the
repository manifest's `partial_records`, outside the analyzer corpus. Failed
or reclassified candidates are not counted as exclusions caused by the cap.
