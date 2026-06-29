---
name: github-work-log
description: Use when writing a Korean work log, daily report, weekly summary, or date-range summary from GitHub activity using only a date argument and GitHub API data.
argument-hint: "YYYY-MM-DD 또는 YYYY-MM-DD..YYYY-MM-DD"
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

- `YYYY-MM-DD`: 하루 활동
- `YYYY-MM-DD..YYYY-MM-DD`: 기간 활동
- `오늘`, `어제`, `이번 주`: `Asia/Seoul` 기준 절대 날짜로 변환한 뒤 실행

기본값:

- GitHub 사용자: `gh api user --jq .login` 결과
- 저장소: `zambaguni/zambaguni-front`
- 시간대: `Asia/Seoul`

다른 저장소를 사용하라고 사용자가 명시한 경우에만 `GITHUB_WORK_LOG_REPO=owner/repo` 환경
변수를 사용한다.

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

스크립트 출력에는 다음 항목이 포함된다.

- GraphQL `contributionsCollection` 기반 기여 요약
- 생성한 PR
- 머지된 PR
- 리뷰한 PR
- 생성한 이슈
- 댓글로 참여한 이슈/PR 대화
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

## 간단 요약 형식

사용자가 단순히 "뭐 했는지 정리"를 요청하면 아래 형식으로 답한다.

```text
1. {작업 제목}
   - {업무 관점의 세부 내용}
```

---

## 보고서 형식

사용자가 `보고`, `재택근무 보고`, `업무 보고`를 요청하면 아래 형식을 사용한다.

```markdown
## 업무 수행 내역

| No. | 업무 내용 | 진행 상태 | 소요 시간 |
|-----|----------|-----------|-----------|
| 1 | {업무 제목} | 완료 | N시간 00분 |
| 2 | {업무 제목} | 완료 | N시간 00분 |
| 3 | {업무 제목} | 완료 | N시간 00분 |
| 4 | {업무 제목} | 완료/진행중 | N시간 00분 |

### 1. {업무 제목}
- {세부 내용}

### 2. {업무 제목}
- {세부 내용}

### 3. {업무 제목}
- {세부 내용}

### 4. {업무 제목}
- {세부 내용}

## 성과 및 특이사항

**주요 성과**

- {성과}

## 익일(출근일) 업무 계획

1. {계획}
2. {계획}
3. {계획}
```

보고서 작성 규칙:

- 업무 수행 내역은 정확히 4개로 작성한다.
- 소요 시간 합계는 정확히 8시간으로 맞춘다.
- 익일 업무 계획은 정확히 3개로 작성한다.
- 이슈 번호, PR 번호, 커밋 prefix, 리뷰 요청 같은 프로세스 활동은 업무 항목에 넣지 않는다.
- 초안을 먼저 보여주고 사용자 승인을 기다린다.
- 사용자가 승인하고 저장을 요청한 경우에만 파일을 쓴다.

---

## 한계

GitHub Search API의 댓글 검색은 개별 댓글 본문이 아니라 대화 단위 결과일 수 있다. 따라서 수집
JSON은 업무 요약의 근거로만 사용하고 최종 문장은 업무 관점으로 재구성한다.
