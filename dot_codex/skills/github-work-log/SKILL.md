---
name: github-work-log
description: Use when writing a Korean work log, report, or weekly summary for an explicit date or date range (YYYYMMDD, 오늘, 어제, 이번 주) from GitHub activity collected via API. For today's quick log saved to document/daily, use daily-work-log instead.
---

# GitHub Work Log

## Overview

Use GitHub API data as the source of truth for Korean work-log and report drafts. Accept a
date-only request, collect activity through `gh api`, then synthesize business-facing work items.

## Date Contract

Accept only one date argument:

- `YYYYMMDD` for one day (e.g. `20260626`)
- `YYYYMMDD-YYYYMMDD` for a range (e.g. `20260626-20260629`)
- Korean relative dates like `어제`, `이번 주`, or `오늘` when the request explicitly mentions
  GitHub activity/API — resolve to absolute dates in `Asia/Seoul` and convert to `YYYYMMDD` or
  `YYYYMMDD-YYYYMMDD` format

**Boundary with daily-work-log**: a bare "오늘 업무 보고 작성해줘" with no GitHub activity mention
defers to `daily-work-log`. Use this skill when a past date/range is given, or the user explicitly
asks for a GitHub comment/review/PR-activity-based summary.

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
./scripts/collect-github-activity.sh YYYYMMDD
./scripts/collect-github-activity.sh YYYYMMDD-YYYYMMDD
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

Default output format — use this unless the user asks for `간단히` or `요약만`:

```text
**업무 수행 내역**

1. {업무 제목}
   진행 상태: 완료 / 소요 시간: 0시간 00분

2. {업무 제목}
   진행 상태: 완료 / 소요 시간: 0시간 00분

3. {업무 제목}
   진행 상태: 완료 / 소요 시간: 0시간 00분

4. {업무 제목}
   진행 상태: 완료·진행중 / 소요 시간: 0시간 00분

---

**성과 및 특이사항**
- 주요 성과: {한 문장}
- 이슈 / 장애: 없음
- 협업 요청 사항: 없음

---

**익일(출근일) 업무 계획**

1. {계획} [상]
2. {계획} [중]
3. {계획} [하]
```

Output rules:

- Exactly four work items. No markdown tables.
- Total 소요 시간 across four items: 10 hours (for a single day or averaged over the period).
- Exactly three 익일 업무 계획 items with priority tags [상/중/하].
- Omit issue numbers, PR numbers, commit prefixes, and review-request process activities from item titles.
- When the user requests `간단히` or `요약만`, fall back to a simple numbered list instead.

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
