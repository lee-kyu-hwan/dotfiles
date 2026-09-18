# Synthetic curated collection contract

## Inputs and envelopes

The caller supplies one normalized `OWNER/REPO`, a positive Issue number,
positive unique-PR cap, positive shared request budget, and two distinct local
destinations. Existing corpus and manifest inputs are paired. Exact resume also
requires a run ID; collection text never supplies a control input.

Corpus output uses schema `1.0.0` with `generated_by` and `records`. Fresh
output identifies `collecting-curated-contribution-prs` and its computed
revision. Existing corpus merge preserves the complete prior envelope value
and append-only source, observation, and state prefixes. The sibling merger is
always called with `source_policy="explicit-only"`.

Manifest output uses schema `2.0.0`, the curated generator, and append-only
`records`. Every run records a stable run ID, request fingerprint, exact
`collection_method: "tracker-issue-comments"`, normalized tracker identity,
cap, cumulative budget and requests, page provenance, reference counts,
hydration outcomes, warnings, failed scopes, timestamps, and status. Same-run
resume replaces only the matching last checkpoint; collection without a
resume ID appends a new run.

## Sources and observations

The tracker source key is deterministically namespaced by the synthetic or
caller-owned Issue node ID. Immutable source metadata identifies the tracker
Issue, collection method, skill name, and revision. Run-specific request and
page facts belong only in the manifest.

Issue-body observations identify the Issue node, URLs, update time, and UTF-8
body SHA-256. Comment observations preserve run ID, `comment_id`, node ID,
`comment_url`, `comment_html_url`, login, raw tracker `author_association`,
created and updated times, and UTF-8 body SHA-256. No alias key duplicates
those three canonical comment facts. Tracker association is never upstream role
evidence. Content identity excludes run ID so unchanged recollection is not
duplicated while edits append.

PR URLs are classified from their associated label text, never from URL spans
themselves. The same-line prefix is checked first, followed by the immediately
preceding line. All URL spans are removed from each label before keyword
matching. The English keywords `example`, `examples`, `notice`, `notices`, and
`announcement` match only at ASCII letter boundaries. For Korean, the
normalized label's first token must be `예시` or `공지` and be followed immediately
by the label end or `:`, `：`, `-`, `–`, or `—`. A match excludes the reference and the
manifest exclusion records the matched keyword, evaluated
label, and whether it came from the same-line prefix or previous line. This is
a deliberately narrow label heuristic: labels farther away than one line,
synonyms outside the listed vocabulary, and ambiguous prose require caller
review and are not silently inferred.

When authoritative PR state cannot be read, the unresolved partial record is
kept so its tracker evidence and failed hydration outcome remain auditable. To
satisfy the corpus invariant without inventing open, closed, merged, or deleted
state, it receives one `unknown` state event whose authority is the GitHub
access failure and whose `failure_basis.endpoint_categories` names the missing
evidence. This option preserves the failed submission in the corpus and allows
the documented analyzer handoff to validate it.

## Status and persistence

Complete capped scope exits 0. Invalid CLI, schema, fingerprint, resume, or
manifest discriminator exits 2 before GitHub access or destination changes.
Usable evidence with pagination, ordering, access, hydration, or budget gaps
is partial and exits 3. A global collection failure or failure with no usable
record writes a failed manifest and exits 4.

Corpus and manifest are serialized as UTF-8 JSON with a trailing newline and
atomically replaced through sibling temporary files. A failed serialization
or replacement preserves previous destination bytes and removes temporary
files. Runtime payloads and outputs remain only at caller-selected paths;
repository fixtures and examples are synthetic public data.
