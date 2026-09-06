# GitHub REST collection contract

## Transport and limits

Use the bundled serial `gh api` adapter. It sends GET with GitHub JSON Accept
and an explicit API version, default `2026-03-10`. Preflight records the CLI
version and authenticated login and checks `/versions` before repository
collection. Never expose credentials or conditional request headers in
diagnostics. The adapter owns `per_page=100`; callers pass page numbers only.

Every attempt, including retries and fallback, consumes the shared request
budget. An initial request has at most three retries. For rate limits, honor
Retry-After, then X-RateLimit-Reset; otherwise wait 60 seconds with exponential
backoff capped at five minutes. Transport/5xx retries are bounded too. No new
request starts after budget exhaustion. A 304 is usable only with the exact
cached payload and matching ETag; it cannot upgrade partial evidence.

A 404 is `not-found-or-inaccessible`, never proof of deletion. Preserve
unauthorized, forbidden, failed, collected, and no-results outcomes separately.

## Search

Search each repository independently. Normalize to UTC whole-second `[a,b)`
and use exactly one qualifier `closed:a..(b - 1 second)`, plus `repo:`, `is:pr`,
and `is:closed`. Outcome filters add `is:merged` or `-is:merged`. Always
post-filter actual `closed_at` into `[a,b)` and recheck hydrated state.

Split at a whole-second midpoint when total_count is at least 1000 or
incomplete_results is true. A still-unsafe one-second leaf is partial. Only
safe, fully paginated leaves supply selectable hits. Count drift, contradictory
pages, failures, and exhausted budgets remain explicit partition evidence.
Deduplicate by PR node ID, order by closed_at/number descending, and apply the
cap per repository. Keep ordered overflow for outcome-race backfill.

Reading all pages does not eliminate search-index delay or missing indexed
content. Record that method limitation separately from known collection gaps.

## Evidence endpoints

Collect PR core at `/repos/{owner}/{repo}/pulls/{number}`, then its `/files`,
`/commits`, `/reviews`, and `/comments` endpoints. Separately collect
`/repos/{owner}/{repo}/issues/{number}/comments` and `/timeline`. Cache
`/repos/{owner}/{repo}/license` once per repository with original capture time.

Keep body, files, commits, Issue comments, reviews, review comments, timeline,
linked Issues, and license categories separate. Preserve available text in
the corpus excerpt slots mechanically, including prompt-like text. Retain
review commit/time/inline-location evidence and timeline actor/time/source.
Cross-referenced PRs are not linked Issues.

Record successful and attempted pages, per-page ETags, counts, endpoint,
capture time, warnings, and completeness. Malformed records, missing patches,
count mismatches, or category failures are partial; valid earlier evidence
survives. Follow explicit next-page links even after short pages.

Files are partial at 3000. At 250 PR commits, use repository List commits
from the authoritative head SHA, bounded by the authoritative PR commit count.
Completion requires unique SHAs, correct head, reconciliation with PR-list
ordering, and provable parent ancestry to the observed base. Unknown, cyclic,
or conflicting ancestry stays partial; a matching count alone is insufficient.

Merged state requires a non-null valid merged_at. Confirmed closed with no
merge is closed-unmerged; a reopened PR is open. Unknown core state cannot
produce invented authoritative history. OWNER/MEMBER/COLLABORATOR associations
map to upstream-maintainer; contributor associations map to contributor;
others remain unknown. Preserve raw association; never infer program-mentor.

## Sources

- [Search](https://docs.github.com/en/rest/search/search)
- [Search qualifiers](https://docs.github.com/en/search-github/searching-on-github/searching-issues-and-pull-requests)
- [Pagination](https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api)
- [API versions](https://docs.github.com/en/rest/about-the-rest-api/api-versions)
- [Rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)
- [Best practices](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api)
- [Troubleshooting](https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api)
- [PR endpoints](https://docs.github.com/en/rest/pulls/pulls)
- [List commits](https://docs.github.com/en/rest/commits/commits)
- [Timeline](https://docs.github.com/en/rest/issues/timeline)
