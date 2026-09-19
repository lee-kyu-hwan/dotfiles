# GitHub API contract

## Transport

모든 GitHub 요청은 읽기 전용이다. REST 는 GET 만, GraphQL 은 query 만 쓴다.
mutation 은 쓰지 않는다.

Every GitHub request is read-only: REST requests use GET only, GraphQL requests
use query operations only, and no mutation is ever sent. REST calls go through
the sibling `collecting-recent-closed-prs` serial `GhApiClient` (`gh api
--method GET`, explicit API version, `per_page=100`, `shell=False`). GraphQL
calls go through a subclass that changes only the command line to `gh api
graphql` and refuses any document that is not a `query` operation before
running `gh`. `gh` sends GraphQL queries as HTTP POST; the method does not
change the read-only rule.

Both clients share one request budget and the sibling's retry, rate-limit,
parsing, and redaction behavior. Every attempt, including retries, consumes
the budget; no request starts after it is exhausted. The global preflight
checks `gh`, authentication, and the API version before any repository request.

## Search

Search each repository independently with `GET /search/issues` and exactly:
`repo:OWNER/REPO is:issue [is:open|is:closed]
FIELD:a..(b - 1 second) [label:"NAME" ...]`, where FIELD is the caller's date
field and `[a,b)` is the UTC whole-second interval. Space-separated label
qualifiers require every label. Neither `reason:` nor `linked:pr` is used.

When `total_count` is at least 1000 or `incomplete_results` is true, record the
parent search in `split_observations` and split at the whole-second midpoint;
a still-unsafe one-second leaf is partial. Only safe, fully paginated leaves
supply hits. Count drift, short pages, failures, and budget exhaustion are
explicit partition failures; after the budget runs out, every remaining
partition is recorded as failed rather than omitted.

Search hits are post-filtered: an item with a `pull_request` key is excluded
and counted as `is-pull-request`; the caller's date field must parse and lie
inside `[a,b)`. A hit without a usable node ID, number, or date makes the
repository partial. Hits are deduplicated by node ID, ordered by that date
field and number descending, and capped per repository.

Reading all pages does not remove search-index delay or missing indexed
content. `updated_at` also moves on events such as label changes.

## Evidence

For each selected hit, read the Issue at `/repos/{owner}/{repo}/issues/{n}`.
That payload is authoritative: a `pull_request` key excludes it as
`is-pull-request`, and a node ID different from the search hit is a failed
Issue. Then read `/comments` and `/timeline` with the sibling list-page reader.

Then send the fixed `IssueEvidence` GraphQL query for the same Issue. It reads
`userContentEdits` of the body and of each comment, `duplicateOf`,
`closedByPullRequestsReferences(includeClosedPrs: true)`, and closed events
with their `closer`. A GraphQL `errors` array, a missing Issue, or a mismatched
Issue ID fails the GraphQL category; its facts stay unknown. A connection with
`hasNextPage` other than `false` keeps the returned facts but is incomplete.
Diff text is hashed, never stored.

## Failures

A REST 404 is `not-found-or-inaccessible`, never proof of deletion; 401 is
`unauthorized`, 403 `forbidden`, and anything else `failed`. A repository
preflight failure marks that repository and its scope. An Issue whose core
read fails is kept in `partial_records` outside the corpus with its outcome.
GraphQL `NOT_FOUND` arrives as HTTP 200 with an `errors` array and is handled
as a failed GraphQL category, not as a missing Issue.

How the timeline presents cross-references from repositories the viewer cannot
read, and whether `linked:pr` matches `closedByPullRequestsReferences`, are
unverified; both are recorded as method limitations.

## Sources

- [Search issues and pull requests](https://docs.github.com/en/rest/search/search#search-issues-and-pull-requests)
- [Search qualifiers](https://docs.github.com/en/search-github/searching-on-github/searching-issues-and-pull-requests)
- [Issues](https://docs.github.com/en/rest/issues/issues)
- [Issue comments](https://docs.github.com/en/rest/issues/comments)
- [Timeline events](https://docs.github.com/en/rest/issues/timeline)
- [GraphQL Issue object](https://docs.github.com/en/graphql/reference/objects#issue)
- [Rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)
