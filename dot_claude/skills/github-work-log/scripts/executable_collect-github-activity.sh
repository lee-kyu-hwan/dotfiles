#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  collect-github-activity.sh YYYYMMDD
  collect-github-activity.sh YYYYMMDD-YYYYMMDD

Environment:
  GITHUB_WORK_LOG_REPO  owner/repo scope. Defaults to zambaguni/zambaguni-front.
USAGE
}

die() {
  echo "error: $*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"
}

validate_date() {
  [[ "$1" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] || die "invalid date: $1"
}

compact_to_iso() {
  local d="$1"
  echo "${d:0:4}-${d:4:2}-${d:6:2}"
}

parse_date_arg() {
  local raw="$1"

  if [[ "$raw" =~ ^[0-9]{8}-[0-9]{8}$ ]]; then
    FROM_DATE="$(compact_to_iso "${raw%-*}")"
    TO_DATE="$(compact_to_iso "${raw#*-}")"
  elif [[ "$raw" =~ ^[0-9]{8}$ ]]; then
    FROM_DATE="$(compact_to_iso "$raw")"
    TO_DATE="$FROM_DATE"
  else
    die "invalid date format: $raw (expected YYYYMMDD or YYYYMMDD-YYYYMMDD)"
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
          state,
          created_at,
          updated_at,
          closed_at,
          author: .user.login,
          is_pull_request: has("pull_request")
        }
      ]
    }'
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

main() {
  if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
  fi

  [[ "$#" -eq 1 ]] || die "expected exactly one date argument"

  require_command gh
  require_command jq

  parse_date_arg "$1"

  local repo="${GITHUB_WORK_LOG_REPO:-zambaguni/zambaguni-front}"
  local login
  login="$(gh api user --jq .login)"

  local from_iso="${FROM_DATE}T00:00:00+09:00"
  local to_iso="${TO_DATE}T23:59:59+09:00"
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

  search_issues "repo:${repo} is:pr author:${login} created:${date_range}" \
    >"$tmpdir/created-prs.json"
  search_issues "repo:${repo} is:pr author:${login} merged:${date_range}" \
    >"$tmpdir/merged-prs.json"
  search_issues "repo:${repo} is:pr reviewed-by:${login} updated:${date_range}" \
    >"$tmpdir/reviewed-prs.json"
  search_issues "repo:${repo} is:issue author:${login} created:${date_range}" \
    >"$tmpdir/created-issues.json"
  search_issues "repo:${repo} commenter:${login} updated:${date_range}" \
    >"$tmpdir/commented-conversations.json"
  search_commits "repo:${repo} author:${login} author-date:${date_range} merge:false" \
    >"$tmpdir/commits.json"

  jq -n \
    --arg repo "$repo" \
    --arg login "$login" \
    --arg timezone "Asia/Seoul" \
    --arg fromDate "$FROM_DATE" \
    --arg toDate "$TO_DATE" \
    --arg fromIso "$from_iso" \
    --arg toIso "$to_iso" \
    --slurpfile contributions "$tmpdir/contributions.json" \
    --slurpfile createdPrs "$tmpdir/created-prs.json" \
    --slurpfile mergedPrs "$tmpdir/merged-prs.json" \
    --slurpfile reviewedPrs "$tmpdir/reviewed-prs.json" \
    --slurpfile createdIssues "$tmpdir/created-issues.json" \
    --slurpfile commentedConversations "$tmpdir/commented-conversations.json" \
    --slurpfile commits "$tmpdir/commits.json" \
    '{
      meta: {
        source: "github-api",
        repository: $repo,
        login: $login,
        timezone: $timezone,
        from_date: $fromDate,
        to_date: $toDate,
        from_iso: $fromIso,
        to_iso: $toIso
      },
      contributions: $contributions[0].data.user.contributionsCollection,
      searches: {
        created_pull_requests: $createdPrs[0],
        merged_pull_requests: $mergedPrs[0],
        reviewed_pull_requests: $reviewedPrs[0],
        created_issues: $createdIssues[0],
        commented_conversations: $commentedConversations[0],
        commits: $commits[0]
      }
    }'
}

main "$@"
