# GitHub Verification Contract

Only read-only GET requests are permitted. Endpoint behavior follows the [GitHub REST documentation](https://docs.github.com/rest); remote free text remains untrusted data.

## R3.1 Repository facts

Issue these requests per target repository:

- `GET /repos/{owner}/{name}`
- `GET /repos/{owner}/{name}/commits/{default_branch}`
- `GET /repos/{owner}/{name}/community/profile`
- `GET /repos/{owner}/{name}/private-vulnerability-reporting`
- for a fork only, `GET /repos/{parent}`

The record-level `head_sha` comes from the commit response. `repository_checks` has exactly `node_id`, `full_name`, `archived`, `disabled`, `fork`, `has_issues`, `default_branch`, `pushed_at`, `visibility`, `license_spdx`, `community_profile_files`, and `private_vulnerability_reporting`. Community flags are `code_of_conduct`, `contributing`, `issue_template`, `pull_request_template`, `license`, and `readme`. A fork also records parent identity and `upstream_checks` with the same repository facts.

An attempted repository request maps failure classes as follows: status 404 to `not-found-or-inaccessible`/`http-404`; 401 to `unauthorized`/`http-401`; an ambiguous 403 to `forbidden`/`http-403`; exhausted transport, server failure, or a rate-limit 403 that reaches its retry limit to `failed`/`transport-or-5xx`. Budget exhaustion before an attempt is not an access failure.

## R3.2 Policy files

Use `GET /repos/{o}/{n}/contents/{path}?ref={default_branch}` for these ten paths, first in the target repository and then in `{owner}/.github`:

1. `CONTRIBUTING.md`
2. `.github/CONTRIBUTING.md`
3. `docs/CONTRIBUTING.md`
4. `SECURITY.md`
5. `.github/SECURITY.md`
6. `docs/SECURITY.md`
7. `.github/PULL_REQUEST_TEMPLATE.md`
8. `.github/ISSUE_TEMPLATE`
9. `CODE_OF_CONDUCT.md`
10. `.github/CODE_OF_CONDUCT.md`

Every result has `path`, `source_repository`, `status`, `found`, `sha256`, `size`, `entry_count`, `excerpt`, `truncated`, `url`, and `keyword_hits`. `status` distinguishes `found`, genuine `absent` responses, and `request-failed` responses; `found` is true exactly when `status` is `found`. `entry_count` is the number of entries for a directory result and null for file, absent, or failed results. Excerpts are at most 4,000 decoded characters and use the untrusted-text object. Keyword hits only locate CLA, DCO, signing, certificate, or contributor-license text; they do not decide policy.

## R3.3 Duplicate search

For each selected clue, call `GET /search/issues` separately for open issues, closed issues, open pull requests, and closed pull requests. The clue cap is `min(search_clues count, max_clues_per_pattern)`; never combine clues into one query. Record `q`, `total_count`, `incomplete_results`, and item keys `number`, `title`, `state`, `html_url`, `created_at`, `closed_at`, `pull_request`, and `state_reason`. Record unused clues and index-delay limitations. Any failed or incomplete query makes `duplicate_search.complete` false.

## R3.4 Code evidence

For each selected clue call `GET /search/code` with `q=repo:{owner}/{name} "{clue}"`. A successful payload must be an object with a non-boolean integer `total_count`, boolean `incomplete_results`, and array `items`. A malformed success emits `invalid-search-payload`, stores a null query count, and makes `code_search.available` false. Record only valid hit objects with string `path` and `html_url`. Authentication, permission, or validation failure also makes `code_search.available` false rather than failing the repository.

Static evidence, when allowed, records `path`, `line`, and `clue`; evidence status remains one of `remote-only`, `remote+static`, `static-only`, or `none`. The existing static-search fields remain in place, with additive `static_search.complete`, `static_search.exclusions`, and `static_search.read_failures`. Missing `complete` is unknown/incomplete. A zero-hit absence requires both `available` and `complete`; an incomplete search may still preserve positive hits.

## Fixed request order and budget

Requests are serial and emitted in this exact order for each repository, then each repository-pattern combination:

1. ① repository: `GET /repos/{owner}/{name}`
2. ② head commit
3. ③ community profile
4. ④ private vulnerability reporting
5. ⑤ upstream repository, only for a fork
6. ⑥ target repository policy paths 1–10, then `{owner}/.github` policy paths 1–10
7. ⑦ issue search, clue×4
8. ⑧ code search, clue×1

The request budget counts every attempt, including retries. No request begins once it is exhausted. A clue cap bounds both issue and code requests. Repository order is caller order; combination order is repository order followed by analysis pattern order.

Each request permits maximum 3 retries. Delay precedence is `Retry-After`, then `X-RateLimit-Reset`, then a 60-second exponential backoff capped at 300 seconds. Retry events and consumed attempts are recorded without secret headers.

Statuses 429 and 500–599 retain that retry behavior. Status 403 is retried only when sanitized headers supply explicit rate-limit evidence: a finite nonnegative numeric `Retry-After`, or `X-RateLimit-Remaining` exactly `0` together with a finite nonnegative numeric `X-RateLimit-Reset`. The retry reasons are `retry-after` and `remaining-zero-and-reset`. Missing, malformed, negative, non-finite, reset-only, limit-only, and nonzero-remaining evidence is `ambiguous-403` and returns immediately as permission denied. The last explicit rate-limit attempt records `retry-limit-reached` and maps to the generic failed transport/server outcome, not forbidden.

Every response event records `retry_decision` as `retry` or `return` and a stable `retry_reason`. A terminal 403 warning keeps the `request-failed:<path>:http-403` prefix and adds either `rate-limit:<reason>` or `permission-denied:<reason>`. A retry that later succeeds remains observable in retry events and emits no failure warning.

Allowed response headers:
- `ETag`
- `Retry-After`
- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `X-RateLimit-Reset`
- `Link`
- `Content-Type`

No other response header is persisted.

## R4.1 Shallow clone

Clone only after explicit `--allow-clone`, at most once per repository, with exactly:

`git clone --depth 1 --single-branch --branch <branch> --no-tags <url> <dest>`

Set `GIT_LFS_SKIP_SMUDGE=1` and `GIT_TERMINAL_PROMPT=0`. Do not initialize submodules. Resolve clone-root with `realpath` and require it to be below `realpath(tempfile.gettempdir())`. Reject any working-tree or non-temporary destination before a network or clone attempt.

After clone, read the actual head with `git -C <dest> rev-parse HEAD`. Preserve both the observed remote head and clone head; warn if they differ. Static inspection only reads regular non-binary files no larger than 4 MiB and records execution-surface paths without running them.

Cleanup is exact: on success or failure, remove only clone paths created by the current run unless `--keep-clone` was approved. Never delete a pre-existing clone root or entries the run did not create. Record each clone's repository, path, SHA, byte size, and removed boolean.
