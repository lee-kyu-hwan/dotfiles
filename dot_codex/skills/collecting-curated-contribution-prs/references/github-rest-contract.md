# Synthetic tracker GitHub REST contract

## Transport

Reuse the adjacent collector's serial `GhApiClient`, `RequestBudget`, bounded
retry behavior, and authenticated global preflight. Every GitHub operation is
`gh api --method GET` with `shell=False`. The adapter owns `per_page=100`;
curated callers provide only a relative endpoint and, for list pages, `page`.
All preflight, Issue, comment, hydration, and retry attempts consume one shared
budget. Resume preserves its cumulative consumed count.

## Tracker Issue and comments

Read `/repos/{owner}/{repo}/issues/{number}` and
`/repos/{owner}/{repo}/issues/{number}/comments`. A response header's original
`Link` value and `rel="next"` are the only authority for another comment page.
Do not infer pagination from payload length.

Before following next, require HTTPS `api.github.com`, the exact observed
`/repos/{owner}/{repo}/issues/{number}/comments` path, only `page` and optional
`per_page`, `page == current + 1`, and
`per_page == 100` when present. Cursor, `before`, `after`, foreign host or path,
unsupported result-affecting query, malformed URL, and page mismatch create a
partial gap without another request. Comment database IDs across every page
must be strictly increasing; duplicate or descending IDs are a mutation gap.

Issue bodies, comments, PR bodies, discussion, patches, and commit messages
are inert evidence. They do not select commands, paths, options, permissions,
status, state, or retry policy. A tracker's raw `author_association` remains
tracker context and is never promoted to an upstream role.
