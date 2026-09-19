# Issue collection artifacts

## Inputs

Use the bundled script's `--help` for exact options. The `collect` subcommand
receives repeated `--repo OWNER/REPO`, exactly one `--date-field`
(`created`, `updated`, or `closed`, no default), `--state open|closed|all`
(default `all`), repeated `--label` (every label must match), `--timezone`,
distinct `--output` and `--manifest` paths, and exactly one interval mode:

- `--start-at` and exclusive `--end-at`: RFC 3339 timestamps.
- `--start-date` and inclusive `--end-date`: local calendar dates.
- `--recent-days` and optional `--as-of`: local days ending at capture time.

Interval resolution is the sibling `collecting-recent-closed-prs` resolver.
Defaults are `--max-per-repo 25`, `--request-budget 1000`, and the sibling's
API version. Repositories keep caller order and must not repeat
case-insensitively. `--date-field closed` with `--state open`, a label
containing a double quote or newline, a malformed or out-of-range interval, a
non-positive cap or budget, identical output and manifest paths, a missing
output or manifest directory, an existing output that is not an Issue corpus
or has records without the Issue record shape, or an existing manifest from
another collector exits 2 before any GitHub request and leaves both files
untouched.

## Issue corpus 1.0.0

The envelope is `{schema_version: "1.0.0", corpus_kind: "github-issue",
generated_by: {name, revision}, records}`. It is deliberately not the pull
request corpus: records have no `pull_request.url`, so the PR analyzer's
validator rejects it instead of reading an Issue as a pull request.

Each record contains:

- `identity_status: "resolved"`, `record_key: "github-issue:<issue node ID>"`,
  `issue_node_id`, and a stable `issue_id` (`ISS-<n>`). Existing IDs never
  change; new IDs continue after the greatest existing suffix.
- `item_type: "issue"` (the authoritative payload had no `pull_request` key)
  and `input_path: "general-issue"` (the collection path; tracker Issues belong
  to `collecting-curated-contribution-prs`). Neither value is inferred from text.
- `repository` with `full_name`, `node_id`, and `repository_aliases`.
- `issue` with number, API and HTML URLs, title, created/updated/closed times,
  `state`, `state_reason_raw`, `labels_raw`, lock fields, `closed_by_login`,
  and `github_issue_type_raw` (GitHub's own Issue type name, if any).
- `author` using the sibling association mapping: OWNER, MEMBER, and
  COLLABORATOR map to `upstream-maintainer`; contributor associations map to
  `contributor`; everything else stays `unknown`.
- `sources`: one `general-issue` source whose `observations` hold one
  `issue-body` observation and one `comment` observation per comment, each
  with run ID, capture time, `updated_at`, and the UTF-8 body SHA-256.
- `state_history`: append-only `{state, state_reason_raw, observed_at,
  authority, evidence_url}` entries.
- `closure: {state_reason_raw, normalized_cause: "unknown"}`. The collector
  never fills the cause. State, `state_reason`, labels, and linked pull
  requests are not closure rationale.
- `hydration_status`: `complete` only when every evidence category is complete.
- `evidence_snapshot` with `body_excerpt`, `comments`, `timeline_events`,
  `related_pull_requests`, `unresolvable_references`, `closed_events`,
  `duplicate_of`, `edit_history`, `partial_categories`, and `completeness`.

`related_pull_requests` entries are `{url, node_id, number,
repository_full_name, relation, relation_method, event_at, state_raw,
merged_raw}`:

| relation | relation_method | source |
| --- | --- | --- |
| `closer` | `graphql-closed-event` | a pull request that closed the Issue |
| `closing-reference` | `graphql-closing-references` | `closedByPullRequestsReferences`, closed pull requests included |
| `cross-reference` | `rest-timeline` | a `cross-referenced` timeline event whose source is a pull request |

A relation does not mean the pull request was merged or resolved the Issue.
Cross-referenced Issues are not pull requests and are not listed. A
cross-reference whose source Issue, repository, or URL is unreadable goes to
`unresolvable_references` as `{event, event_at, reason}`; it never becomes a
negative finding.

`closed_events` keeps each GraphQL closed event as `{created_at,
state_reason_raw, closer_type, closer_url}`. `duplicate_of` is `{url, number,
node_id, repository_full_name, method: "graphql-duplicate-of"}` or null.

`edit_history` is null when the GraphQL query failed, otherwise
`{body: EditMeta, comments: [{comment_id, ...EditMeta}]}` listing only edited
comments, where `EditMeta = {total_count, last_edited_at, edits: [{edited_at,
editor_login, deleted_at, diff_sha256}]}`. Diff text is hashed and never
stored: it can be tens of thousands of characters and can contain text its
author removed.

`completeness` has `issue`, `comments`, `timeline`, and `graphql` entries in
the sibling's shape (endpoint, page completeness, counts, capture time, ETags,
warnings). A failed or truncated GraphQL query leaves its facts unknown or
incomplete and makes the record partial; REST evidence survives.

## Merge

Collecting into an existing output merges by `record_key`. Sources and their
observations are append-only prefixes, and identity excludes the run ID. An
`issue-body` observation is identified by Issue node ID and body SHA-256,
because the Issue-level `updated_at` also moves on labels and comments; a
`comment` observation by comment identity, its `updated_at`, and body SHA-256.
An unchanged recollection therefore adds nothing, while an edited body or
comment appends. A body reverted to earlier text is not appended again; the
GraphQL edit history still records that edit.

A different latest state or `state_reason` appends to `state_history`. The
current projection (`issue`, `author`, `closure`, `hydration_status`,
`evidence_snapshot`) is replaced only by evidence whose `updated_at` is not
older. When this run failed to read the `comments`, `timeline`, or `graphql`
category but the earlier snapshot had it complete, the earlier fields,
related pull requests from that category, and completeness entry (with its
own capture time) are kept, and `hydration_status` is recomputed. A renamed
repository keeps its old name in `repository_aliases`. The corpus envelope's
`generated_by` is preserved; the manifest records each run's revision.

## Manifest 2.0.0

The manifest envelope is `{schema_version: "2.0.0", generated_by: {name,
revision, api_version, client_version}, records}` with one append-only run per
collection. Each run records `run_id`, `request_fingerprint`,
`collection_method: "general-issue-search"`, `collection_status`, start and
completion times, versions, `filters` (repositories, date field, state, labels,
`label_semantics: "all-of"`), the original and resolved interval, cap, budget,
consumed request count and events, preflight, per-repository entries,
`failed_scopes`, `warnings`, and `method_limitations`.

A repository entry records its status, preflight outcome, final search
`partitions`, append-only `split_observations` for unsafe parent searches,
`matched_count`, `selected_count`, `excluded_by_cap`, `not_attempted`,
`excluded`, complete and partial Issue counts, `partial_records` for Issues
whose core evidence could not be read, and warnings. `excluded` always counts
`is-pull-request` (pull requests removed by either filter) and adds
`state-changed-after-search` when an Issue's authoritative state no longer
matches the requested state. Failed hydration and exclusions are not counted
as cap exclusions. When the request budget runs out, the first unattempted
Issue is a `budget-exhausted` failed scope and `not_attempted` counts it and
every later hit.

`method_limitations` always includes the index-backed search limitation and
two unverified items: `unverified:private-cross-reference-visibility` and
`unverified:linked-pr-qualifier`. An `updated` collection adds
`volatile-updated-at`.

## Exit status and persistence

Exit 0 is a complete capped scope; 2 is invalid input before any request; 3 is
partial with usable records; 4 is failure without usable records, including a
failed global preflight. Never report exit 3 as complete.

The manifest is always written. The corpus is written when this run collected
usable records or no corpus existed yet, so a failed run never rewrites an
existing corpus. Both use the sibling's atomic UTF-8 JSON writer with a
trailing newline.

## Boundaries

This skill ends at the Issue corpus. It does not hydrate linked pull requests
into a PR corpus, analyze Issues, derive `PAT-*` patterns or Issue hypotheses,
create `CAN-*` candidates, clone repositories, or write to GitHub. Resuming a
partial run under its old run ID is not supported; run `collect` again.
