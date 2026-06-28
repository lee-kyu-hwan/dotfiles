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
- Repository: `zambaguni/zambaguni-front`
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
- commit search results

Use `GITHUB_WORK_LOG_REPO=owner/repo` only when the user explicitly requests a different
repository. It is an environment override, not a normal prompt parameter.

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

## Limitations

GitHub Search can identify PRs, issues, reviews, comments, and commits matching the date range,
but some comment searches are conversation-level rather than exact comment-body extraction. Treat
the collected JSON as evidence to summarize, not as final wording.
