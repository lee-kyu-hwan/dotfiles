---
name: github-work-log
description: Use when writing a Korean work log, report, or weekly summary for an explicit date or date range (YYYYMMDD, 오늘, 어제, 이번 주) from GitHub activity collected via API. For today's quick log saved to document/daily, use daily-work-log instead.
argument-hint: "YYYYMMDD 또는 YYYYMMDD-YYYYMMDD"
user-invocable: true
allowed-tools: Bash
---

# GitHub 업무 로그

인자: `$ARGUMENTS`

---

## 핵심 원칙

GitHub API 데이터를 유일한 활동 근거로 사용해 한글 업무 로그나 보고서 초안을 작성한다. 날짜만
받고, 사용자명·저장소·브랜치는 묻지 않는다.

---

## 입력 규칙

허용 인자:

- `YYYYMMDD`: 하루 활동 (예: `20260626`)
- `YYYYMMDD-YYYYMMDD`: 기간 활동 (예: `20260626-20260628`)
- `어제`, `이번 주`, 또는 GitHub 활동/API 기반 요약을 명시한 `오늘`: `Asia/Seoul` 기준 절대 날짜로
  변환한 뒤 실행

**daily-work-log와의 경계**: "오늘 업무 보고 작성해줘"처럼 GitHub 활동 언급 없이 당일 작업만
요청하면 `daily-work-log`가 우선한다. 이 스킬은 과거 날짜·기간이 명시되었거나, 사용자가 GitHub
댓글/리뷰/PR 활동 기반 요약임을 밝혔을 때 사용한다.

기본값:

- GitHub 사용자: `gh api user --jq .login` 결과
- 저장소: `zambaguni/zambaguni-front`, `zambaguni/zambaguni-mobile`
- 시간대: `Asia/Seoul`

다른 저장소 집합을 사용하라고 사용자가 명시한 경우에만
`GITHUB_WORK_LOG_REPOS=owner/repo,owner/repo` 환경 변수를 사용한다. 레거시 단일 저장소
override인 `GITHUB_WORK_LOG_REPO=owner/repo`도 계속 지원된다.

---

## 금지 사항

- 로컬 `git log`를 활동 근거로 사용하지 않는다.
- `document/daily/*.txt`를 활동 근거로 사용하지 않는다.
- 사용자가 저장을 명시하지 않으면 파일을 쓰지 않는다.
- GitHub 인증, 저장소 접근, API 호출이 실패하면 추정하지 말고 실패한 명령과 blocker를 보고한다.

---

## 수집 절차

1. `$ARGUMENTS`를 절대 날짜 인자로 확정한다.
2. 아래 스크립트를 실행해 GitHub API JSON을 수집한다.

```bash
~/.claude/skills/github-work-log/scripts/collect-github-activity.sh "$ARGUMENTS"
```

`오늘`, `어제`, `이번 주` 같은 자연어 인자는 스크립트 호출 전 `Asia/Seoul` 기준으로 `YYYYMMDD` 또는 `YYYYMMDD-YYYYMMDD` 형식으로 변환한다.

스크립트 출력에는 다음 항목이 포함된다.

- GraphQL `contributionsCollection` 기반 기여 요약
- 생성한 PR / 머지된 PR / 리뷰한 PR
- 생성한 이슈
- 댓글로 참여한 이슈/PR 대화 (`searches.commented_conversations`)
- 사용자가 작성한 이슈/PR 댓글 원문 (`searches.issue_comments`)
- 사용자가 작성한 PR 인라인 리뷰 댓글 (`searches.pull_request_review_comments`)
- 사용자가 제출한 PR 리뷰 기록 — 리뷰 상태·본문 포함 (`searches.pull_request_reviews`)
- 커밋 검색 결과

---

## 작성 방식

수집 JSON을 그대로 나열하지 말고 업무 관점으로 묶는다.

좋은 표현:

- `파트너 모바일 지도 카드 사용성 개선`
- `예약 상세 화면의 데이터 표시 안정화`
- `배포 전 CI 오류 원인 분석 및 수정`

피할 표현:

- `fix: marker padding`
- `PR #123 처리`
- `리뷰 요청`

---

## 댓글·리뷰 근거

토론/리뷰 업무를 요약할 때는 REST로 수집한 정확한 댓글·리뷰 데이터를 우선 사용한다:

- `searches.issue_comments`: 기간 내 사용자가 작성한 이슈/PR 대화 댓글
- `searches.pull_request_review_comments`: 기간 내 사용자가 작성한 PR 인라인 리뷰 댓글
- `searches.pull_request_reviews`: `submitted_at` 기준으로 필터된 제출 리뷰 기록 (리뷰 상태·본문 포함)

`searches.commented_conversations`는 대화 맥락의 보조 신호로만 쓴다. 목록의 모든 대화에
기간 내 새 댓글이 달렸다는 증거로 쓰지 않는다.

---

## 기본 출력 형식

특별한 키워드 없이 호출하면 아래 폼 형식으로 출력한다. 이 형식이 기본값이다.

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

출력 규칙:

- 항목은 정확히 4개로 작성한다.
- 소요 시간 합계는 기간 내 총 활동량을 기반으로 추정한다 (단일 날짜면 시작~종료 기준, 기간이면 일 평균 10시간 기준).
- 표(markdown table)는 사용하지 않는다.
- 이슈 번호, PR 번호, 커밋 prefix 같은 프로세스 활동은 항목에 넣지 않는다.
- 익일 계획은 정확히 3개, 우선순위(상/중/하)를 대괄호로 표기한다.
- 사용자가 `간단히`, `요약만` 을 요청하면 번호 목록 형태의 단순 요약으로 대신한다.

---

## 한계

GitHub Search는 날짜 범위에 맞는 PR·이슈·리뷰·댓글·커밋을 찾을 수 있지만, 일부 검색 결과는
개별 활동이 아니라 대화 단위일 수 있다. 수집 JSON은 업무 요약의 근거로만 사용하고 최종 문장은
업무 관점으로 재구성한다. "사용자가 무엇을 썼는가"는 검색 대화 매칭보다 정확한 댓글·리뷰
필드(`issue_comments`, `pull_request_review_comments`, `pull_request_reviews`)가 더 신뢰할 수 있다.
