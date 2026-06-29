#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  collect-github-activity.sh YYYY-MM-DD
  collect-github-activity.sh YYYY-MM-DD..YYYY-MM-DD

Environment:
  GITHUB_WORK_LOG_REPOS  Comma or whitespace separated owner/repo scopes.
                         Defaults to zambaguni/zambaguni-front,zambaguni/zambaguni-mobile.
  GITHUB_WORK_LOG_REPO   Legacy single owner/repo scope override.
USAGE
}

die() {
  echo "error: $*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"
}

to_utc_iso() {
  local date="$1"
  local time="$2"
  local epoch

  if epoch="$(TZ=Asia/Seoul date -j -f "%Y-%m-%d %H:%M:%S" "${date} ${time}" "+%s" 2>/dev/null)"; then
    date -u -r "$epoch" "+%Y-%m-%dT%H:%M:%SZ"
    return 0
  fi

  if TZ=Asia/Seoul date -d "${date} ${time}" -u "+%Y-%m-%dT%H:%M:%SZ" >/dev/null 2>&1; then
    TZ=Asia/Seoul date -d "${date} ${time}" -u "+%Y-%m-%dT%H:%M:%SZ"
    return 0
  fi

  die "failed to convert Asia/Seoul date to UTC ISO: ${date} ${time}"
}

validate_date() {
  [[ "$1" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] || die "invalid date: $1"
}

resolve_repos() {
  local raw="${GITHUB_WORK_LOG_REPOS:-${GITHUB_WORK_LOG_REPO:-zambaguni/zambaguni-front zambaguni/zambaguni-mobile}}"
  raw="${raw//,/ }"

  # shellcheck disable=SC2206
  REPOS=($raw)

  [[ "${#REPOS[@]}" -gt 0 ]] || die "expected at least one repository"

  local repo
  for repo in "${REPOS[@]}"; do
    [[ "$repo" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]] || die "invalid repository: $repo"
  done
}

repo_slug() {
  echo "${1//\//-}"
}

parse_date_arg() {
  local raw="$1"

  if [[ "$raw" == *".."* ]]; then
    FROM_DATE="${raw%%..*}"
    TO_DATE="${raw##*..}"
  else
    FROM_DATE="$raw"
    TO_DATE="$raw"
  fi

  validate_date "$FROM_DATE"
  validate_date "$TO_DATE"

  [[ "$FROM_DATE" > "$TO_DATE" ]] && die "from date must be before or equal to to date"
  return 0
}

search_issues() {
  local query="$1"

  gh api --method GET /search/issues \
    -H "Accept: application/vnd.github+json" \
    -f q="$query" \
    -f sort=updated \
    -f order=desc \
    -F per_page=100 \
    --jq '{
      total_count,
      incomplete_results,
      items: [
        .items[] | {
          title,
          html_url,
          number,
          state,
          created_at,
          updated_at,
          closed_at,
          author: .user.login,
          repository: (.repository_url | sub("^https://api.github.com/repos/"; "")),
          is_pull_request: has("pull_request")
        }
      ]
    }'
}

merge_search_files() {
  jq -s '{
    total_count: (map(.total_count) | add // 0),
    incomplete_results: (map(.incomplete_results) | any),
    items: (map(.items) | add | sort_by(.updated_at // .created_at // "") | reverse)
  }' "$@"
}

merge_item_files() {
  jq -s '{
    total_count: (map(.total_count) | add // 0),
    items: (map(.items) | add)
  }' "$@"
}

search_issues_in_repos() {
  local name="$1"
  local query_tail="$2"
  local files=()
  local repo
  local file

  for repo in "${REPOS[@]}"; do
    file="$tmpdir/${name}-$(repo_slug "$repo").json"
    search_issues "repo:${repo} ${query_tail}" >"$file"
    files+=("$file")
  done

  merge_search_files "${files[@]}"
}

list_issue_comments() {
  local repo="$1"
  local login="$2"
  local from_utc="$3"
  local to_utc="$4"

  gh api --paginate --method GET "/repos/${repo}/issues/comments" \
    -H "Accept: application/vnd.github+json" \
    -f since="$from_utc" \
    -F per_page=100 |
    jq -s \
      --arg repo "$repo" \
      --arg login "$login" \
      --arg from "$from_utc" \
      --arg to "$to_utc" \
      '[
        .[][] |
        select(.user.login == $login) |
        select(.created_at >= $from and .created_at <= $to) |
        {
          id,
          html_url,
          issue_url,
          repository: $repo,
          author: .user.login,
          created_at,
          updated_at,
          body
        }
      ] | {
        total_count: length,
        items: .
      }'
}

list_issue_comments_in_repos() {
  local files=()
  local repo
  local file

  for repo in "${REPOS[@]}"; do
    file="$tmpdir/issue-comments-$(repo_slug "$repo").json"
    list_issue_comments "$repo" "$login" "$from_utc" "$to_utc" >"$file"
    files+=("$file")
  done

  merge_item_files "${files[@]}"
}

list_pull_request_review_comments() {
  local repo="$1"
  local login="$2"
  local from_utc="$3"
  local to_utc="$4"

  gh api --paginate --method GET "/repos/${repo}/pulls/comments" \
    -H "Accept: application/vnd.github+json" \
    -f since="$from_utc" \
    -F per_page=100 |
    jq -s \
      --arg repo "$repo" \
      --arg login "$login" \
      --arg from "$from_utc" \
      --arg to "$to_utc" \
      '[
        .[][] |
        select(.user.login == $login) |
        select(.created_at >= $from and .created_at <= $to) |
        {
          id,
          html_url,
          pull_request_url,
          pull_request_review_id,
          repository: $repo,
          author: .user.login,
          created_at,
          updated_at,
          path,
          line,
          original_line,
          diff_hunk,
          body
        }
      ] | {
        total_count: length,
        items: .
      }'
}

list_pull_request_review_comments_in_repos() {
  local files=()
  local repo
  local file

  for repo in "${REPOS[@]}"; do
    file="$tmpdir/pull-request-review-comments-$(repo_slug "$repo").json"
    list_pull_request_review_comments "$repo" "$login" "$from_utc" "$to_utc" >"$file"
    files+=("$file")
  done

  merge_item_files "${files[@]}"
}

list_pull_request_reviews() {
  local repo="$1"
  local login="$2"
  local from_utc="$3"
  local to_utc="$4"
  local reviewed_prs_file="$5"

  jq -r '.items[]?.number' "$reviewed_prs_file" |
    sort -nu |
    while read -r pr_number; do
      [[ -n "$pr_number" ]] || continue

      gh api --paginate --method GET "/repos/${repo}/pulls/${pr_number}/reviews" \
        -H "Accept: application/vnd.github+json" \
        -F per_page=100 |
        jq -s \
          --arg repo "$repo" \
          --arg login "$login" \
          --arg from "$from_utc" \
          --arg to "$to_utc" \
          --argjson prNumber "$pr_number" \
          '.[][] |
            select(.user.login == $login) |
            select(.submitted_at != null) |
            select(.submitted_at >= $from and .submitted_at <= $to) |
            {
              id,
              html_url,
              pull_request_url,
              pull_request_number: $prNumber,
              repository: $repo,
              author: .user.login,
              state,
              submitted_at,
              body
            }'
    done |
    jq -s '{
      total_count: length,
      items: .
    }'
}

list_pull_request_reviews_in_repos() {
  local files=()
  local repo
  local reviewed_file
  local output_file

  for repo in "${REPOS[@]}"; do
    reviewed_file="$tmpdir/reviewed-prs-$(repo_slug "$repo").json"
    output_file="$tmpdir/pull-request-reviews-$(repo_slug "$repo").json"
    list_pull_request_reviews "$repo" "$login" "$from_utc" "$to_utc" "$reviewed_file" >"$output_file"
    files+=("$output_file")
  done

  merge_item_files "${files[@]}"
}

search_commits() {
  local query="$1"

  gh api --method GET /search/commits \
    -H "Accept: application/vnd.github+json" \
    -f q="$query" \
    -f sort=author-date \
    -f order=desc \
    -F per_page=100 \
    --jq '{
      total_count,
      incomplete_results,
      items: [
        .items[] | {
          sha,
          html_url,
          message: .commit.message,
          author_name: .commit.author.name,
          author_date: .commit.author.date,
          repository: .repository.full_name
        }
      ]
    }'
}

search_commits_in_repos() {
  local query_tail="$1"
  local files=()
  local repo
  local file

  for repo in "${REPOS[@]}"; do
    file="$tmpdir/commits-$(repo_slug "$repo").json"
    search_commits "repo:${repo} ${query_tail}" >"$file"
    files+=("$file")
  done

  merge_search_files "${files[@]}"
}

main() {
  if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
  fi

  [[ "$#" -eq 1 ]] || die "expected exactly one date argument"

  require_command gh
  require_command jq

  parse_date_arg "$1"
  resolve_repos

  local login
  login="$(gh api user --jq .login)"

  local from_iso="${FROM_DATE}T00:00:00+09:00"
  local to_iso="${TO_DATE}T23:59:59+09:00"
  local from_utc
  local to_utc
  from_utc="$(to_utc_iso "$FROM_DATE" "00:00:00")"
  to_utc="$(to_utc_iso "$TO_DATE" "23:59:59")"
  local date_range="${FROM_DATE}..${TO_DATE}"
  local tmpdir
  tmpdir="$(mktemp -d)"
  TMPDIR_TO_CLEAN="$tmpdir"
  trap '[[ -n "${TMPDIR_TO_CLEAN:-}" ]] && rm -rf "$TMPDIR_TO_CLEAN"' EXIT

  local graphql_query='
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        login
        contributionsCollection(from: $from, to: $to) {
          startedAt
          endedAt
          totalCommitContributions
          totalIssueContributions
          totalPullRequestContributions
          totalPullRequestReviewContributions
          totalRepositoriesWithContributedCommits
          restrictedContributionsCount
          commitContributionsByRepository(maxRepositories: 25) {
            repository { nameWithOwner url }
            contributions(first: 100, orderBy: {field: OCCURRED_AT, direction: DESC}) {
              totalCount
              nodes { occurredAt commitCount url }
            }
          }
          issueContributions(first: 100, orderBy: {direction: DESC}) {
            totalCount
            nodes {
              occurredAt
              issue { title url number repository { nameWithOwner } }
            }
          }
          pullRequestContributions(first: 100, orderBy: {direction: DESC}) {
            totalCount
            nodes {
              occurredAt
              pullRequest {
                title
                url
                number
                state
                merged
                mergedAt
                repository { nameWithOwner }
              }
            }
          }
          pullRequestReviewContributions(first: 100, orderBy: {direction: DESC}) {
            totalCount
            nodes {
              occurredAt
              pullRequest {
                title
                url
                number
                repository { nameWithOwner }
              }
              pullRequestReview { state submittedAt url }
            }
          }
        }
      }
    }'

  gh api graphql \
    -f query="$graphql_query" \
    -f login="$login" \
    -f from="$from_iso" \
    -f to="$to_iso" >"$tmpdir/contributions.json"

  search_issues_in_repos "created-prs" "is:pr author:${login} created:${date_range}" \
    >"$tmpdir/created-prs.json"
  search_issues_in_repos "merged-prs" "is:pr author:${login} merged:${date_range}" \
    >"$tmpdir/merged-prs.json"
  search_issues_in_repos "reviewed-prs" "is:pr reviewed-by:${login} updated:${date_range}" \
    >"$tmpdir/reviewed-prs.json"
  search_issues_in_repos "created-issues" "is:issue author:${login} created:${date_range}" \
    >"$tmpdir/created-issues.json"
  search_issues_in_repos "commented-conversations" "commenter:${login} updated:${date_range}" \
    >"$tmpdir/commented-conversations.json"
  list_issue_comments_in_repos \
    >"$tmpdir/issue-comments.json"
  list_pull_request_review_comments_in_repos \
    >"$tmpdir/pull-request-review-comments.json"
  list_pull_request_reviews_in_repos \
    >"$tmpdir/pull-request-reviews.json"
  search_commits_in_repos "author:${login} author-date:${date_range} merge:false" \
    >"$tmpdir/commits.json"

  local repos_json
  repos_json="$(printf '%s\n' "${REPOS[@]}" | jq -R . | jq -s .)"

  jq -n \
    --argjson repos "$repos_json" \
    --arg login "$login" \
    --arg timezone "Asia/Seoul" \
    --arg fromDate "$FROM_DATE" \
    --arg toDate "$TO_DATE" \
    --arg fromIso "$from_iso" \
    --arg toIso "$to_iso" \
    --arg fromUtc "$from_utc" \
    --arg toUtc "$to_utc" \
    --slurpfile contributions "$tmpdir/contributions.json" \
    --slurpfile createdPrs "$tmpdir/created-prs.json" \
    --slurpfile mergedPrs "$tmpdir/merged-prs.json" \
    --slurpfile reviewedPrs "$tmpdir/reviewed-prs.json" \
    --slurpfile createdIssues "$tmpdir/created-issues.json" \
    --slurpfile commentedConversations "$tmpdir/commented-conversations.json" \
    --slurpfile issueComments "$tmpdir/issue-comments.json" \
    --slurpfile pullRequestReviewComments "$tmpdir/pull-request-review-comments.json" \
    --slurpfile pullRequestReviews "$tmpdir/pull-request-reviews.json" \
    --slurpfile commits "$tmpdir/commits.json" \
    '{
      meta: {
        source: "github-api",
        repository: ($repos | join(",")),
        repositories: $repos,
        login: $login,
        timezone: $timezone,
        from_date: $fromDate,
        to_date: $toDate,
        from_iso: $fromIso,
        to_iso: $toIso,
        from_utc: $fromUtc,
        to_utc: $toUtc
      },
      contributions: $contributions[0].data.user.contributionsCollection,
      searches: {
        created_pull_requests: $createdPrs[0],
        merged_pull_requests: $mergedPrs[0],
        reviewed_pull_requests: $reviewedPrs[0],
        created_issues: $createdIssues[0],
        commented_conversations: $commentedConversations[0],
        issue_comments: $issueComments[0],
        pull_request_review_comments: $pullRequestReviewComments[0],
        pull_request_reviews: $pullRequestReviews[0],
        commits: $commits[0]
      }
    }'
}

main "$@"
