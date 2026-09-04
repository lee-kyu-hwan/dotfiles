# PR review session 동기화 스킬 사전 조사

- 작성일: 2026-08-31
- 대상 브랜치: `feat/sync-pr-review-session-skill`
- 대상 도구: Codex, Claude Code, GitHub, tmux, workmux
- 연구 상태: **예비 근거 문서 — deep-research 검증 보고서 미완료**

## 연구 질문

Codex와 Claude Code가 함께 사용하는 PR review-session 동기화 스킬을 설계할 때 필요한
Agent Skills 호환성, GitHub 리뷰 상태 의미, tmux/workmux 수명주기와 안전한 생성·제거
규칙은 무엇인가?

## 연구 상태와 한계

`deep-research` 워크플로를 위 질문으로 실행했다. 검색·fetch·주장 검증 과정에서 Claude
Code 주간 사용 한도에 도달해 외부 호출이 HTTP 429로 종료됐다. 호출기는 Haiku 검색
요청 42회를 기록했지만 워크플로의 구조화된 반환값을 받지 못했다. 따라서 `status`,
`findings`, `confirmed`, `refuted`, `unverified`, `unranked`, `sources`, `stats`는 모두
회수할 수 없었다.

특히 다음 커버리지 값은 **0이 아니라 알 수 없음**이다.

- `anglesNoResults`, `anglesFailed`, `anglesWithoutFetch`
- `fetchSkipped`, `fetchErrored`, `budgetDropped`
- `claimsExtracted`, `claimsVerified`, `unverified`, `killed`

그러므로 이 문서는 deep-research의 2표 이상 지지를 받은 확정 finding을 전달하는
보고서가 아니다. 워크플로 중단 뒤 공식 1차 자료와 현재 로컬 환경을 별도로 대조해 만든
예비 설계 근거다. 사용 한도 재설정 뒤 같은 질문으로 워크플로를 재실행하고, 그 결과와
충돌하는 항목은 갱신해야 한다.

이 문서에서는 근거 성격을 다음처럼 표시한다.

| 표기 | 의미 |
| --- | --- |
| `[P]` | 공식 규격이나 해당 제품의 1차 문서에서 확인 |
| `[L]` | 현재 머신·저장소에서 읽기 전용으로 실측 |
| `[D]` | `[P]`·`[L]`과 이 대화의 요구사항에서 도출한 설계 결정 |
| `[U]` | 구현 전에 확정해야 할 미결정 항목 |

## 결론 요약

1. `[D]` GitHub를 PR 상태의 source of truth로 두고, workmux와 tmux는 그 상태를
   표현하는 로컬 실행 자원으로 취급한다.
2. `[D]` 현재 `reviewRequests`에 사용자가 다시 포함돼 있으면 과거의 승인보다 우선해
   review window를 유지하거나 다시 만든다. 재리뷰 요청은 과거 review 결과와 별개의
   현재 작업 요청이기 때문이다.
3. `[D]` `MERGED`, `CLOSED`, 그리고 현재 재리뷰 요청이 없는 `OPEN + APPROVED` PR은
   `2-review`의 원하는 집합에서 제외한다. PR 작성자가 현재 사용자라면 review session이
   아니라 `1-main`의 개발 작업으로 분류한다.
4. `[D]` 상태 조회는 항상 read-only다. 생성·이동·제거·리뷰 제출·thread resolve는
   사용자가 명시적으로 요청한 모드에서만 수행한다.
5. `[D]` worktree의 자원 식별자는 `workmux list --json`의 `handle`과 `path`다. tmux
   `session:index`나 창 이름에서 worktree 이름을 역추론하지 않는다.
6. `[D]` 동기화는 `관찰 → 원하는 상태 계산 → 변경 계획 표시 → 재검증 → 변경 → 사후
   검증`의 두 단계 절차로 만든다. GitHub 조회가 실패하거나 빈 결과의 원인을 판별할 수
   없으면 제거는 한 건도 실행하지 않는다.
7. `[D]` 두 에이전트의 본문은 하나의 표준 `SKILL.md`를 공유하고 Claude 경로는 그
   디렉터리를 symlink하는 방식을 우선 검토한다. 파괴적 명령이 포함되므로
   `allowed-tools: Bash` 같은 포괄적 사전 승인은 넣지 않는다.
8. `[D]` PR review 품질과 review-session 수명주기는 분리한다. 동기화 스킬이 리뷰를
   요청할 수는 있지만, 실제 코드 분석은 `pr-review-toolkit`에 맡기고 GitHub 제출 형식과
   resolve 조건만 계약으로 강제한다.

## 1. Codex와 Claude Code의 스킬 호환성

### 공통 규격

`Agent Skills` 규격에서 skill은 최소 `SKILL.md`를 가진 디렉터리다. `name`과
`description`은 필수이며, 이름은 디렉터리명과 같아야 한다. 표준 frontmatter는
`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`다.
`allowed-tools`는 실험 항목이고 호스트별 지원 차이가 있을 수 있다. `[P]`
([Agent Skills specification](https://agentskills.io/specification))

OpenAI Docs는 Codex가 skill의 이름과 설명을 먼저 보고 필요할 때 전체 `SKILL.md`를
읽는 progressive disclosure 모델을 설명한다. Codex의 사용자 범위 위치는
`~/.agents/skills`, 저장소 범위 위치는 `.agents/skills`이며 symlink된 skill 디렉터리도
지원한다. `agents/openai.yaml`은 Codex UI와 invocation policy를 위한 선택 메타데이터다.
`[P]` ([OpenAI Docs: Build skills](https://developers.openai.com/codex/skills))

Claude Code도 Agent Skills 공개 규격을 따르고, 사용자 범위 `~/.claude/skills`와 저장소
범위 `.claude/skills`를 사용한다. symlink된 skill 디렉터리를 따라가며 같은 target이 여러
위치에 있으면 한 번만 로드한다. 다만 `argument-hint`, `disable-model-invocation`,
`user-invocable`, `context`, 동적 shell injection 등은 Claude Code 확장이다. 표준 밖
frontmatter는 claude.ai 업로드나 Skills API packaging에서 hard error가 될 수 있다.
`[P]` ([Claude Code: Extend Claude with skills](https://code.claude.com/docs/en/slash-commands))

### 권장 배포 형태

이 skill은 개인 dotfiles에서 Codex와 로컬 Claude Code가 같이 쓰는 것이 1차 목표다.
두 호스트가 모두 symlink directory를 지원하므로, 표준 frontmatter만 사용한 하나의
canonical skill을 두 경로에서 읽게 하는 구성이 가장 드리프트가 적다. `[D]`

```text
dot_agents/skills/sync-pr-review-session/
├── SKILL.md
├── agents/
│   └── openai.yaml
└── references/
    ├── github-state-model.md
    └── reconciliation.md

dot_claude/skills/
└── symlink_sync-pr-review-session.tmpl
    -> ~/.agents/skills/sync-pr-review-session
```

Claude Code는 `agents/openai.yaml`을 사용하지 않고, Codex만 선택적으로 읽는다. 공통
`SKILL.md`에는 Claude 전용 frontmatter를 넣지 않는다. 자연어 요청에서도 skill이
선택될 수 있게 두되, 본문에서 다음 mutation gate를 강제한다. `[D]`

- “상태 확인”, “목록”, “request가 왔는지”는 read-only다.
- “동기화”, “만들어”, “옮겨”, “제거해”, “resolve해”, “리뷰를 제출해”처럼 변경을
  명시한 요청만 해당 변경을 허용한다.
- 한 종류의 mutation 권한을 다른 종류로 확대하지 않는다. 예를 들어 “window 동기화”는
  GitHub review 제출이나 thread resolve 권한이 아니다.

Claude 전용 자동 호출 차단이나 argument UI가 꼭 필요해지면 두 개의 얇은
`SKILL.md` wrapper를 만들고 공통 workflow reference를 공유하는 대안으로 전환한다.
본문 전체를 두 벌 복사하는 방식은 피한다. 현재 저장소의 Codex/Claude
`create-worktree`와 `remove-worktree` 사본은 이미 frontmatter 밖 본문 차이가 있어,
복제된 지침이 실제로 드리프트할 수 있음을 보여준다. `[L]`

### 권한 설계

`allowed-tools`는 도구를 사전 승인하는 성격이므로 이 skill에는 넣지 않는다. 이 workflow는
worktree와 tmux window, 로컬 branch를 제거할 수 있고 GitHub review/thread 상태도 바꿀 수
있다. 플랫폼의 정상 승인 흐름과 기존 `remove-worktree` 안전 검사를 유지하는 편이 맞다.
`[D]`

## 2. GitHub 상태 모델

### 서로 다른 세 종류의 상태

GitHub GraphQL의 `PullRequest.state`는 `OPEN`, `CLOSED`, `MERGED`를 구분한다.
`reviewDecision`은 PR 전체의 현재 review 상태이며 `APPROVED`, `CHANGES_REQUESTED`,
`REVIEW_REQUIRED` 값을 가진다. `reviewRequests`는 PR에 걸린 현재 review request
목록이다. 세 필드는 같은 정보를 반복하는 것이 아니다. `[P]`
([GitHub GraphQL pull request reference](https://docs.github.com/en/graphql/reference/pulls))

GitHub는 이미 리뷰한 사람에게 변경 후 다시 review를 요청할 수 있다고 명시한다. 따라서
“예전에 승인함”과 “지금 다시 review 요청을 받음”은 동시에 관찰될 수 있는 별도 사건으로
다뤄야 한다. `[P/D]`
([Requesting a pull request review](https://docs.github.com/en/pull-requests/how-tos/create-pull-requests/requesting-a-pull-request-review))

`gh pr list`와 `gh pr view`는 `state`, `isDraft`, `author`, `headRefName`,
`headRefOid`, `reviewDecision`, `reviewRequests`, `latestReviews`를 JSON field로 제공한다.
`gh pr list`의 기본 limit는 30이므로 자동화에서는 명시적 limit 또는 GraphQL pagination이
필요하다. `[P]` ([gh pr list](https://cli.github.com/manual/gh_pr_list),
[gh pr view](https://cli.github.com/manual/gh_pr_view))

현재 사용자의 login은 `gh api user`로 얻고, 다음 최소 필드를 수집한다. `[D]`

```text
number, url, state, isDraft, author.login,
headRefName, headRefOid,
reviewDecision, reviewRequests, latestReviews
```

`reviewDecision`은 PR 전체 상태이므로 “내 최신 review”를 보고하려면
`latestReviews`에서 viewer를 따로 찾는다. “나에게 지금 요청이 왔는가”는 과거 review
목록이 아니라 현재 `reviewRequests`를 기준으로 한다. 팀 review request는 User와 Team
union을 구분하고, 현재 사용자의 team membership을 확인할 수 없으면 직접 request로
오인하지 말고 “team request, membership 미확인”으로 보고한다. `[D]`

### `2-review` 원하는 상태 결정표

아래 순서를 위에서부터 적용한다. 이는 GitHub의 API 사실 그 자체가 아니라 이 대화에서
확인한 운영 규칙이다. `[D]`

| 우선순위 | PR 조건 | `2-review` 목표 | 이유 |
| --- | --- | --- | --- |
| 1 | `MERGED` 또는 `CLOSED` | 없음 | 더 이상 review 대상이 아님 |
| 2 | `author.login == viewer.login` | 없음 | 자신의 PR은 `1-main` 개발 작업으로 분류 |
| 3 | viewer에게 현재 직접 또는 확인된 team request | 있음 | 현재 재리뷰 요청이 과거 승인보다 우선 |
| 4 | draft이고 현재 request 없음 | 없음 | ready 전에는 자동 review 대상에서 제외 |
| 5 | `OPEN + APPROVED`, 현재 request 없음 | 없음 | 사용자 결정: 승인된 PR window는 불필요 |
| 6 | 그 밖의 `OPEN` 타인 PR | 있음 | 아직 승인되지 않은 repository review 후보 |

따라서 `APPROVED`였더라도 `reviewRequests`에 viewer가 다시 나타나면 priority 3에서
window를 유지하거나 재생성한다. 반대로 현재 request가 없어도 `REVIEW_REQUIRED`,
`CHANGES_REQUESTED`, 또는 decision 미정인 타인 PR은 repository의 전체 review queue를
유지하려는 현재 운영 방식상 포함한다. `[D]`

`gh search prs --review-requested=@me --state=open`은 현재 요청을 교차 확인하는 보조
수단이다. 다만 이 검색 결과만으로 repository의 전체 미승인 PR 목록을 대체하지 않는다.
`[P/D]` ([gh search prs](https://cli.github.com/manual/gh_search_prs))

### review thread와 resolve

GraphQL `PullRequestReviewThread`에는 `isResolved`, `isOutdated`, `path`, `line`,
`viewerCanResolve`, `viewerCanUnresolve`가 있다. `resolveReviewThread` mutation은 thread ID를
받아 resolve한다. GitHub UI 문서상 PR 작성자 또는 repository write 권한 보유자는
conversation을 resolve할 수 있다. `[P]`
([GitHub GraphQL pull request reference](https://docs.github.com/en/graphql/reference/pulls),
[About pull request reviews](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests/about-pull-request-reviews))

다음은 별도의 명시적 `resolve-addressed` 동작으로 둔다. `[D]`

1. unresolved thread를 전부 가져온다.
2. 각 thread의 지적이 현재 head commit에서 실제로 반영됐는지 코드와 필요한 test로
   다시 확인한다.
3. `isOutdated`만으로 해결됐다고 판정하지 않는다. 코드가 이동했을 뿐일 수 있다.
4. 해결된 thread이고 `viewerCanResolve`가 true일 때만 mutation 계획에 넣는다.
5. 해결되지 않았거나 판단할 수 없는 thread는 이유와 함께 남긴다.
6. mutation 뒤 `isResolved`를 다시 조회한다.

window 제거와 thread resolve는 연결하지 않는다. PR이 merge됐다는 이유로 모든 thread를
resolve하거나, window를 제거했다는 이유로 GitHub 상태를 바꾸지 않는다. `[D]`

## 3. 리뷰 작성 형식과 권한 실패

GitHub의 review는 전체 summary와 파일·라인별 inline comment를 한 review에 함께 담을 수
있다. REST “Create a review” endpoint는 `body`, `event`, `commit_id`와 함께
`comments[]`의 `path`, `line`, `side`, `start_line`, `start_side`, `body`를 받는다.
개별 review comment endpoint는 line뿐 아니라 `subject_type: file`도 지원한다. `[P]`
([REST API: pull request reviews](https://docs.github.com/en/rest/pulls/reviews),
[REST API: review comments](https://docs.github.com/en/rest/pulls/comments))

`gh pr review`의 공개 CLI 옵션은 approve/comment/request-changes와 review body를 제공하지만
inline comment 배열을 직접 받는 옵션은 없다. 따라서 “수정할 파일별로 thread 아래에
inline review를 작성”하려면 `gh api`로 review payload를 제출하거나 GraphQL pending
review와 thread mutation을 사용해야 한다. `[P/D]`
([gh pr review](https://cli.github.com/manual/gh_pr_review))

동기화 skill이 pane의 AI에게 review를 지시할 때는 다음 contract를 prompt에 포함한다.
`[D]`

- 기존 review, unresolved thread, 최신 head OID를 먼저 읽는다.
- 코드 분석은 `$pr-review-toolkit`을 사용해 전체 diff와 관련 test를 검토한다.
- 실제 수정이 필요한 finding은 파일 또는 line에 붙는 inline comment로 작성한다.
- PR 전체 판단과 공통 사항만 review summary에 쓴다.
- 같은 finding을 summary와 inline에 중복 작성하지 않는다.
- finding이 없으면 inline comment를 억지로 만들지 않는다.
- review는 최신 `headRefOid`에 묶고 제출 직전 OID를 다시 확인한다.

API가 403을 반환하면 품질 판단을 “개선 사항 없음”으로 바꾸면 안 된다. 준비한 summary와
inline payload를 보존해 대상 path/line과 함께 사용자에게 보여 주고, 필요한 GitHub
권한이 없음을 별도로 보고한다. 422라면 stale line/OID나 payload 검증 오류일 수 있으므로
최신 diff를 다시 매핑하되, 다른 위치에 top-level comment로 몰아넣지 않는다. `[D]`

## 4. workmux와 tmux 자원 모델

workmux `list --json`은 `project`, `project_path`, `handle`, `branch`, `path`, `is_main`,
`mode`, `has_uncommitted_changes`, `is_open`, `agent_statuses`, `created_at`를 제공한다.
PR 상태, tmux session 이름, window 이름은 JSON contract에 없다. `[P]`
([workmux README](https://github.com/raine/workmux/blob/main/README.md))

현재 머신의 `workmux 0.1.248`에서도 같은 shape를 확인했다. 이 skill의 worktree handle은
`feat-sync-pr-review-session-skill`, path는
`/Users/lee-kyu-hwan/code/dotfiles__worktrees/feat-sync-pr-review-session-skill`로
반환됐다. `[L]`

workmux handle과 path를 실제 worktree identity로 사용하고 다음 정보를 별도로 join한다.
`[D]`

- GitHub: `(owner, repo, PR number)`, `headRefName`, `headRefOid`
- workmux: `(project_path, handle)`, `branch`, `path`
- tmux: `window_id`, 현재 `session_name`, 현재 `window_index`, pane ID와 cwd

PR 번호를 window 이름에서 파싱하는 것은 표시용 fallback으로도 사용하지 않는다. PR의
`headRefName`과 workmux의 `branch`를 exact match하고, 후보가 하나일 때만 연결한다.
후보가 없거나 둘 이상이면 자동 생성·제거 대신 conflict로 보고한다. `[D]`

tmux의 session, window, pane에는 각각 수명 동안 변하지 않는 고유 ID가 있고 window ID는
`@`, pane ID는 `%`로 시작한다. 반면 window index는 `move-window -r`이나
`renumber-windows`로 바뀔 수 있다. `[P]` ([tmux manual](https://man.openbsd.org/tmux),
[tmux Getting Started](https://github.com/tmux/tmux/wiki/Getting-Started))

따라서 사용자가 “2번 window”라고 지시하면 그 순간 `2-review:2`를 `window_id`와
worktree path로 해석해 snapshot을 만든다. 실제 mutation 직전 같은 `window_id`의 현재
위치를 다시 구한다. 앞선 window가 제거돼 index가 당겨졌다고 해서 새 `:2`를 같은
대상으로 간주하지 않는다. `[D]`

### 생성과 제거

window가 필요한데 worktree가 없으면 PR URL과 정확한 `2-review` session을 기존
`create-worktree` skill에 넘긴다. orchestration skill이 git-crypt, PR head OID 검증,
window naming, 저장 session 복구 로직을 복사하지 않는다. `[D]`

현재 이 feature worktree의 committed `create-worktree`는 branch-only 버전이다. main
working tree에는 PR 참조와 target session을 처리하는 미커밋 개정이 있으므로,
orchestration 구현 전에 그 dependency를 별도 commit으로 확정하고 이 branch에
rebase/cherry-pick해야 한다. 미커밋 파일에만 존재하는 contract를 전제로 구현하지 않는다.
`[L/D]`

제거는 `workmux list --json`에서 얻은 실제 handle을 기존 `remove-worktree` skill에
넘긴다. workmux는 worktree, window, local branch를 함께 제거하며 기본적으로 dirty
worktree 제거를 거부한다. Git 자체도 clean하지 않은 linked worktree는 `--force` 없이는
제거하지 않는다. `[P]` ([workmux README](https://github.com/raine/workmux/blob/main/README.md),
[git-worktree documentation](https://git-scm.com/docs/git-worktree))

자동 동기화에서는 `--force`, `--all`, `rm -rf`, 직접 `tmux kill-window`를 사용하지
않는다. 다음 중 하나라도 참이면 제거를 skip하고 보고한다. `[D]`

- `has_uncommitted_changes == true`
- `git -C <path> status --porcelain`이 비어 있지 않음
- agent status가 `working` 또는 `waiting`이고 사용자가 그 실행 종료까지 명시하지 않음
- worktree/PR mapping이 유일하지 않음
- 제거 직전 GitHub 상태 재조회 실패
- 대상이 main worktree

## 5. 권장 reconciliation 절차

### 단계 A — 관찰

1. `gh`, `git`, `tmux`, `workmux` 가용성과 GitHub 인증을 확인한다.
2. 대상 repository와 viewer login을 확정한다.
3. 모든 relevant PR을 pagination해 수집한다.
4. `workmux list --json`, `git worktree list --porcelain`, tmux window/pane 목록을 각각
   종료 코드와 함께 읽는다.
5. PR과 worktree를 repository + exact branch로 연결하고 중복·고아를 표시한다.

명령 실패와 정상적인 빈 배열을 구분한다. GitHub나 workmux 조회가 실패했는데 빈 queue로
간주하면 정상 window를 전부 제거할 수 있으므로, 관찰 실패는 mutation 전체를 닫는
hard gate다. `[D]`

### 단계 B — 원하는 상태 계산

각 PR/worktree에 다음 중 정확히 하나를 부여한다. `[D]`

| action | 의미 |
| --- | --- |
| `KEEP` | 원하는 session에 필요한 자원이 이미 있음 |
| `CREATE` | 필요한 PR인데 worktree/window가 없음 |
| `OPEN` | worktree는 있으나 window가 닫혀 있음 |
| `REPORT_MISPLACED` | window가 다른 session에 있음; 명시적 normalize 전에는 이동 안 함 |
| `REMOVE` | merge/close/승인으로 불필요하고 안전 검사 통과 |
| `SKIP_DIRTY` | 제거 대상이지만 local 변경이 있음 |
| `SKIP_AGENT_ACTIVE` | 제거 대상이지만 AI process가 활동 중 |
| `CONFLICT` | PR-worktree mapping 또는 상태를 유일하게 확정할 수 없음 |
| `IGNORE_OWN` | viewer가 작성한 PR |

상태 요청이면 이 계획을 표로 보고하고 끝낸다. “동기화/정리”가 명시됐을 때만 mutation
단계로 간다. 다른 session에 의도적으로 옮겨 둔 window는 saved placement를 존중하고,
사용자가 session 정규화까지 요청했을 때만 `move-window-to-session` skill을 사용한다.
`[D]`

### 단계 C — 적용

1. 각 대상의 GitHub 상태, worktree clean 상태, stable tmux ID를 다시 읽는다.
2. 제거는 handle 단위로 실행하고 매번 목록을 새로 읽는다.
3. 생성/열기는 PR URL과 target session을 `create-worktree`에 전달한다.
4. pane에 agent 실행이나 prompt 전달이 요청됐으면 window ID로 현재 pane 1을 다시 찾고,
   pane 존재와 실행 중 command를 확인한 뒤 전달한다.
5. 한 대상의 실패는 기록하되 다른 대상의 식별자를 index로 재사용하지 않는다.

### 단계 D — 사후 검증

같은 discovery를 다시 실행해 다음을 확인한다. `[D]`

- 원하는 PR마다 worktree와 window가 정확히 하나 있음
- 제외 대상의 안전하게 제거 가능한 자원이 사라짐
- dirty/active/conflict 대상은 보존됨
- `2-review`의 실제 session/window 이름과 stable ID가 보고값과 일치
- GitHub mutation을 수행한 경우 review/thread 상태가 기대값과 일치

두 번째 실행의 plan이 모두 `KEEP`, `IGNORE_OWN`, 또는 설명된 skip이면 idempotent한
동기화로 본다.

## 6. 사용자에게 보여 줄 상태 표

상태 보고에는 window index만 보여 주지 말고 다음 열을 함께 둔다. `[D]`

| 열 | 출처 |
| --- | --- |
| window | 현재 `session:index`, stable `window_id`, 실제 window name |
| worktree | workmux `handle`, absolute `path`, branch, dirty 여부 |
| PR | `owner/repo#number`, title, `OPEN/CLOSED/MERGED`, draft 여부 |
| review | aggregate `reviewDecision`, viewer latest review |
| request | direct/team/current request 여부 |
| threads | unresolved 수, resolve 가능 수 |
| AI | pane 1 존재, Codex/Claude command, working/waiting/done |
| action | `KEEP/CREATE/REMOVE/...`와 한 문장 이유 |

“나한테 다시 request가 온 PR”은 별도 소제목으로 뽑는다. 과거 승인 이력이 있어도 현재
request가 있으면 여기에 포함한다.

## 7. 구현 범위 제안

첫 버전의 `sync-pr-review-session`은 다음 네 동작만 지원하는 것이 적절하다. `[D]`

1. `status`: PR, window, AI, request 상태를 읽기 전용으로 보고
2. `sync`: 명시적 요청에 따라 clean한 CREATE/OPEN/REMOVE만 적용
3. `dispatch-review`: 선택된 pane에 `pr-review-toolkit` + inline review contract를 전달
4. `resolve-addressed`: 반영 확인이 끝난 thread만 명시적으로 resolve

`create-worktree`, `remove-worktree`, `move-window-to-session`, `pr-review-toolkit`의 세부
절차를 새 skill에 복사하지 않는다. 새 skill은 상태를 계산하고 올바른 하위 skill을
선택하며, 각 동작 전후의 invariant를 검증하는 orchestration layer다.

## 8. 구현 전 확정할 항목

- `[U]` 팀 request를 “현재 사용자에게 온 request”로 인정할 membership 확인 방법.
  권한이 부족하면 team request를 별도 범주로 둘지 결정해야 한다.
- `[U]` draft PR을 current request가 없어도 전체 review queue에 포함할지. 현재 제안은
  제외다.
- `[U]` 다른 session으로 의도적으로 옮긴 review worktree를 `sync`가 자동으로
  `2-review`로 되돌릴지. 현재 제안은 보고만 하고 explicit normalize에서만 이동이다.
- `[U]` agent가 `done`이지만 pane에 process가 남아 있을 때 approved/merged cleanup을
  자동 실행할지. 현재 제안은 clean이면 허용하되 최종 구현 test에서 검증한다.
- `[U]` GitHub aggregate `APPROVED`와 viewer 개인 approval 중 어떤 것을 window 제거
  기준으로 삼을지. 현재 대화에 맞춘 제안은 aggregate `reviewDecision == APPROVED`다.
- `[U]` deep-research 워크플로 재실행 결과. 구조화된 stats와 confirmed/refuted 항목을
  회수하기 전까지 이 문서는 최종 연구 보고서가 아니다.

## 9. 최소 acceptance criteria

1. 현재 re-request가 과거 approval보다 우선한다.
2. merge/close/approved-no-request PR은 clean할 때만 제거 후보가 된다.
3. viewer 본인의 PR은 `2-review`에서 만들지 않는다.
4. 상태 요청은 파일, GitHub, git, tmux, workmux 상태를 바꾸지 않는다.
5. API/CLI 조회 실패는 “대상 없음”으로 변환되지 않고 제거를 차단한다.
6. worktree target은 window index/name이 아니라 workmux handle/path로 확정한다.
7. window index가 중간에 바뀌어도 stable ID 재검증으로 다른 창을 조작하지 않는다.
8. dirty worktree와 active agent window는 force 없이 보존한다.
9. 같은 상태에서 sync를 두 번 실행해 두 번째 mutation이 0건이다.
10. Codex와 Claude Code가 같은 상태 결정표와 mutation gate를 읽는다.
11. review finding은 path/line/file inline comment로 제출되고 summary에 중복되지 않는다.
12. 권한 실패는 “finding 없음”으로 바뀌지 않고 준비된 payload와 실패 원인이 보고된다.
13. thread는 실제 반영 확인과 `viewerCanResolve` 검증 뒤에만 resolve된다.
14. deep-research 재실행 전에는 이 문서의 `[D]` 항목을 verified finding으로 부르지 않는다.

## 출처

- [Agent Skills specification](https://agentskills.io/specification)
- [OpenAI Docs: Build skills](https://developers.openai.com/codex/skills)
- [Claude Code: Extend Claude with skills](https://code.claude.com/docs/en/slash-commands)
- [GitHub GraphQL pull request reference](https://docs.github.com/en/graphql/reference/pulls)
- [GitHub: Requesting a pull request review](https://docs.github.com/en/pull-requests/how-tos/create-pull-requests/requesting-a-pull-request-review)
- [GitHub: About pull request reviews](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests/about-pull-request-reviews)
- [GitHub REST API: Pull request reviews](https://docs.github.com/en/rest/pulls/reviews)
- [GitHub REST API: Pull request review comments](https://docs.github.com/en/rest/pulls/comments)
- [GitHub CLI: gh pr list](https://cli.github.com/manual/gh_pr_list)
- [GitHub CLI: gh pr view](https://cli.github.com/manual/gh_pr_view)
- [GitHub CLI: gh pr review](https://cli.github.com/manual/gh_pr_review)
- [GitHub CLI: gh search prs](https://cli.github.com/manual/gh_search_prs)
- [workmux README](https://github.com/raine/workmux/blob/main/README.md)
- [git-worktree documentation](https://git-scm.com/docs/git-worktree)
- [tmux manual](https://man.openbsd.org/tmux)
- [tmux Getting Started](https://github.com/tmux/tmux/wiki/Getting-Started)
