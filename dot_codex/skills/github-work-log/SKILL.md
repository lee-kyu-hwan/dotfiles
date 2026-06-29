---
name: github-work-log
description: Use when writing a Korean work log, daily report, weekly summary, or date-range summary from GitHub activity using only a date argument and GitHub API data.
---

# GitHub Work Log

## Overview

Use GitHub API data as the source of truth for Korean work-log and report drafts. Accept a
date-only request, collect activity through `gh api`, then synthesize business-facing work items.

## Date Contract

Accept only one date argument:

- `YYYY-MM-DD` for one day
- `YYYY-MM-DD..YYYY-MM-DD` for a range
- Korean relative dates like `오늘`, `어제`, `이번 주` only after resolving them to absolute dates
  in `Asia/Seoul`

Do not ask for repository, login, branch, or local git details unless the API collection fails.

Defaults:

- GitHub login: current authenticated user from `gh api user`
- Repositories: `zambaguni/zambaguni-front`, `zambaguni/zambaguni-mobile`
- Timezone: `Asia/Seoul`

## Hard Rules

- Use GitHub API as the activity source of truth.
- Do not use local `git log` as an activity source.
- Do not use `document/daily/*.txt` as an activity source.
- Do not write files unless the user explicitly asks to save the report.
- If GitHub authentication, repository access, or API collection fails, stop and report the
  blocker with the command that failed.

## Collection

Run the bundled script from the skill directory:

```bash
./scripts/collect-github-activity.sh YYYY-MM-DD
./scripts/collect-github-activity.sh YYYY-MM-DD..YYYY-MM-DD
```

The script returns JSON containing:

- contribution totals from GraphQL `contributionsCollection`
- created pull requests
- merged pull requests
- reviewed pull requests
- created issues
- issue and pull request conversations where the user commented
- exact issue and pull request comments authored by the user
- pull request inline review comments authored by the user
- submitted pull request reviews authored by the user
- commit search results

Use `GITHUB_WORK_LOG_REPOS=owner/repo,owner/repo` only when the user explicitly requests a
different repository set. `GITHUB_WORK_LOG_REPO=owner/repo` is still supported as a legacy
single-repository override. These are environment overrides, not normal prompt parameters.

## Synthesis

Group raw GitHub items into business-facing themes. Prefer product or workflow outcomes over
implementation trivia:

- Good: `파트너 모바일 지도 카드 사용성 개선`
- Avoid: `fix: marker padding`, `PR #123 처리`

When drafting a work report, use exactly four work items totaling eight hours and exactly three
next-business-day plan items:

```markdown
## 업무 수행 내역

| No. | 업무 내용 | 진행 상태 | 소요 시간 |
|-----|----------|-----------|-----------|
| 1 | {업무 제목} | 완료 | N시간 00분 |

### 1. {업무 제목}
- {세부 내용}

## 성과 및 특이사항

**주요 성과**

- {성과}

## 익일(출근일) 업무 계획

1. {계획}
```

For a simple summary, use a shorter numbered list:

```text
1. {작업 제목}
   - {업무 관점의 세부 내용}
```

## Comment and Review Evidence

Prefer exact REST-collected comment and review data when summarizing discussion work:

- `searches.issue_comments` contains issue and pull request conversation comments created by the
  user during the date range.
- `searches.pull_request_review_comments` contains inline PR review comments created by the user
  during the date range.
- `searches.pull_request_reviews` contains submitted PR review records, including review state and
  body, filtered by `submitted_at`.

Use `searches.commented_conversations` as a backup signal for conversation context, not as proof
that every listed conversation received a new user comment in the range.

## Limitations

GitHub Search can identify PRs, issues, reviews, comments, and commits matching the date range,
but some search results are conversation-level rather than exact activity records. Treat the
collected JSON as evidence to summarize, not as final wording. Exact comment and review fields are
more reliable for "what the user wrote" than search conversation matches.
