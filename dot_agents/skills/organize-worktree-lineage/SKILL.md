---
name: organize-worktree-lineage
description: Use when organizing existing git worktrees into Orca lineage — linking issues, setting parent worktrees and board status in bulk
---

# Organize Worktree Lineage

이미 있는 worktree 여러 개를 Orca 계보(parent/child)와 이슈 연결, 보드 상태로 한 번에
편성한다. 새 worktree 하나에 계보를 붙이는 것은 `create-worktree`의 몫이다.

조회는 read-only다. 변경은 계획을 보여 주고 승인받은 뒤에만 실행한다.

## 실행 순서 요약

1. 대상 worktree 수집
2. 브랜치명에서 이슈 번호 추출
3. 상위 에픽 조회
4. PR 상태 조회
5. 그룹 판정 — 중간 worktree가 필요한 에픽 선별
6. 변경 계획 표시 및 승인
7. 적용과 사후 확인

## 1. 대상 수집

```bash
orca worktree list --json
```

`result.worktrees[]`에서 다음을 읽는다. 다른 출처로 대체하지 않는다.

| 필드 | 용도 |
| --- | --- |
| `id` | `<repoId>::<절대경로>`. 셀렉터로 쓸 값 |
| `path` | 실제 경로 |
| `branch` | `refs/heads/...`. **이슈 번호의 정본** |
| `projectId` | 저장소 구분 |
| `parentWorktreeId` | 이미 계보가 있는지 |
| `linkedIssue` | 이미 이슈가 연결됐는지 |
| `workspaceStatus` | 현재 보드 상태 |
| `isMainWorktree` | 메인은 편성 대상이 아니다 |

저장소가 여럿이면 어느 저장소를 편성할지 먼저 확정한다. 지정이 없으면 후보를 제시하고
선택받는다. 전체 저장소를 기본값으로 삼지 않는다.

외부 worktree가 목록에 없으면 표시 설정을 확인한다. Orca는 저장소마다
`externalWorktreeVisibility`를 가지며 전역 기본값이 `hide`다. CLI 옵션이 없으므로 앱
UI에서 바꿔야 한다. 목록에 없는 worktree를 "없는 것"으로 단정하지 않는다.

## 2. 이슈 번호 추출

**브랜치명이 정본이다.** `displayName`, tmux 창 이름, 디렉터리 이름에서 번호를
역추론하지 않는다.

```
refs/heads/1352-improvement/guest-booking-token-url-removal
            ^^^^ 이슈 번호
```

패턴은 `<번호>-<type>/<이름>`이다. 선행 숫자가 없으면 번호를 얻지 못한 것으로 처리한다.

번호를 얻지 못한 worktree는 **사용자에게 보고하고 건너뛴다.** 디렉터리 이름이 비슷하다는
이유로 다른 이슈에 연결하지 않는다.

> 실측 근거: tmux 창 이름의 번호는 이슈가 아니라 **PR 번호**였고, 그마저도 최신이 아니었다.
> 창 `1216-user-partnership-inquiry`의 실제 PR은 #1305, 창 `1471-admin-partner-vat-reports`의
> 실제 PR은 #1476이었다. 브랜치의 `1216-feat/...`, `1467-feat/...`가 각각 정확한 이슈였다.

## 3. 상위 에픽 조회

```bash
gh api graphql -f query='
{ repository(owner:"<owner>", name:"<repo>") {
    issue(number:<번호>) { number title parent { number title } } } }'
```

`parent`가 없으면 단독 이슈다. 에픽이 없다고 해서 임의의 그룹을 만들지 않는다.

조회에 실패하면 그 항목을 건너뛰고 보고한다. 실패를 "에픽 없음"으로 해석하지 않는다.

## 4. PR 상태 조회

```bash
gh pr list --head "<브랜치명>" --state all --json number,state,reviewDecision,isDraft,author
```

`--head`에는 `refs/heads/`를 뗀 브랜치명을 넣는다.

**한 브랜치에 PR이 여럿일 수 있다.** 닫고 다시 연 경우다. 첫 항목(`.[0]`)을 집으면
틀린다. 다음 순서로 고른다.

1. `OPEN`이 있으면 그것
2. 없으면 `MERGED`
3. 둘 다 없고 `CLOSED`만 있으면 그때 폐기 후보로 본다

PR이 2개 이상이면 전부 보고한다. 실측 사례다.

```
1467-feat/admin-partner-vat-reports     PR#1476 CLOSED · PR#1471 OPEN   ← 살아있음
fix/partner-rate-tables-asm-only        PR#1421 CLOSED · PR#1419 MERGED ← 머지됨
```

두 경우 모두 `.[0]`이 `CLOSED`를 집어 "폐기"로 오판했다. 진행 중인 리뷰를 지울 뻔했다.

## 5. 상태 도출

**먼저 PR 작성자가 나인지 본다.** 같은 `CHANGES_REQUESTED`라도 내 PR이면 내가 고칠
차례이고, 남의 PR이면 상대가 고칠 차례다. 작성자를 보지 않으면 정반대로 판정한다.

```bash
gh pr view <번호> --json author,reviewDecision,reviewRequests,state
gh api user --jq .login    # 내 로그인
```

### 내가 작성자인 PR — 내 작업이다

| PR 상태 | `workspaceStatus` |
| --- | --- |
| `MERGED` | `completed` |
| `OPEN`, 리뷰 결정 없음 | `in-review` — 내가 리뷰를 기다린다 |
| `OPEN` + `CHANGES_REQUESTED` | `in-progress` — 내가 고쳐야 한다 |
| `OPEN` + `isDraft` | `in-progress` |
| PR 없음 | `in-progress` |
| `CLOSED` | **판단 보류.** 변경하지 않고 보고한다 |

### 남이 작성자인 PR — 내가 리뷰할 대상이다

| 조건 | `workspaceStatus` |
| --- | --- |
| `reviewRequests`에 내가 있다 | `in-review` — 내가 리뷰할 차례다 |
| 내가 이미 리뷰했고 재요청이 없다 | `completed` — 내 할 일은 끝났다. 정리 후보 |
| `MERGED` · `CLOSED` | `completed` — 정리 후보 |

`reviewRequests`에 다시 포함되면 과거에 리뷰를 냈더라도 `in-review`로 되돌린다.
`CHANGES_REQUESTED`를 냈다는 사실만으로 `in-progress`로 두지 않는다. 고칠 사람은 내가
아니다.

`CLOSED`는 재작업 중일 수도 폐기일 수도 있다. 내가 작성자면 자동으로 정하지 않는다.

`completed`로 판정된 worktree는 정리 후보이기도 하다. 목록을 보고하되 이 스킬에서
제거하지 않는다. 제거는 `remove-worktree`의 몫이다.

## 6. 그룹 판정

에픽별로 자식 worktree 수를 센다.

- **자식 2개 이상** — 중간 worktree(조정자) 생성을 제안한다
- **자식 1개** — 만들지 않는다. 메인 직속에 둔다. 중간 노드는 여러 자식을 조율할 때
  의미가 있다. 자식이 늘면 그때 만든다

이미 중간 worktree가 있는 에픽은 그것을 재사용한다.

## 7. 중간 worktree 생성

조정자는 코드를 고치지 않으므로 `--detach`로 만든다. 브랜치를 남기지 않아 나중에 정리할
것이 줄어들고, `develop` 같은 공용 브랜치를 점유하지 않는다. git worktree는 같은 브랜치를
두 곳에 체크아웃할 수 없다. 의존성은 설치하지 않는다.

base는 로컬 브랜치가 아니라 `origin/<base>`를 쓴다. 로컬이 뒤처져 있으면 조정자가
낡은 상태로 태어난다.

먼저 저장소의 git-crypt 사용 여부를 확인한다.

```bash
git -C "$MAIN" config --get filter.git-crypt.smudge
```

### git-crypt가 없는 경우

```bash
git -C "$MAIN" worktree add --detach "$WORKTREE_PATH" "$BASE_BRANCH"
```

### git-crypt가 있는 경우

`git worktree add`를 그냥 쓰면 smudge 필터가 키를 찾지 못해 실패한다.

```
fatal: <경로>: smudge filter git-crypt failed
```

저장소에 래퍼(`scripts/create-worktree.sh` 등)가 있으면 우선 사용한다. 다만 래퍼는 보통
브랜치를 만들고 의존성까지 설치하므로, 조정자 용도로 맞지 않으면 3단계로 직접 만든다.

```bash
git -C "$MAIN" worktree add --no-checkout --detach "$WORKTREE_PATH" "$BASE_BRANCH"
GIT_DIR_PATH=$(git -C "$WORKTREE_PATH" rev-parse --absolute-git-dir)
ln -s ../../git-crypt "$GIT_DIR_PATH/git-crypt"
git -C "$WORKTREE_PATH" checkout
```

링크는 상대 경로로 건다. 링크 자체의 위치를 기준으로 해석되므로 메인 clone이 옮겨져도
깨지지 않는다.

체크아웃 뒤 복호화를 검증한다. 암호화 파일의 첫 10바이트가 git-crypt blob 헤더
(`00474954435259505400`)면 복호화가 적용되지 않은 것이다.

```bash
od -An -tx1 -N10 "$WORKTREE_PATH/<암호화된 파일>" | tr -d '[:space:]'
```

## 8. 변경 계획 표시

적용 전에 표로 보여 준다. 승인 없이 실행하지 않는다.

```
worktree                          이슈    현재 부모   →  새 부모      상태 변경
guest-booking-token-url-removal   #1352   없음          epic-1350    없음 → in-progress
forum-board-noindex               #1411   없음          epic-1287    없음 → completed
```

다음은 별도 항목으로 함께 보고한다.

- 이슈 번호를 얻지 못한 worktree
- PR이 `CLOSED`라 상태를 보류한 worktree
- `completed`로 판정돼 정리 후보가 된 worktree
- 새로 만들 중간 worktree와 그 경로

**이미 계보가 있는 worktree**는 현재 부모를 보여 주고 바꿀지 확인받는다. 조용히
덮어쓰지 않는다.

## 9. 적용

```bash
orca worktree set --worktree "path:<경로>" \
  --issue <번호> \
  --parent-worktree "<셀렉터>" \
  --workspace-status <id> \
  --json
```

- 부모 셀렉터는 `issue:<에픽번호>`(중간 worktree가 그 이슈에 연결된 경우) 또는
  `path:<메인 경로>`를 쓴다
- 중간 worktree 자신에게는 `--issue <에픽번호>`와 `--display-name`을 함께 설정한다
- 계보를 의도적으로 두지 않을 때만 `--no-parent`를 쓴다

한 번에 한 worktree씩 실행하고 각 응답의 `ok`를 확인한다. 실패한 항목을 성공으로 보고하지
않는다.

## 10. 사후 확인

`orca worktree list --json`을 다시 읽어 `parentWorktreeId`, `linkedIssue`,
`workspaceStatus`가 계획과 일치하는지 대조한다. 명령의 응답만으로 끝내지 않는다.

계보 연결 수와 이슈 연결 수를 전체 대비로 보고한다. 미연결로 남은 항목은 이유와 함께
열거한다. 메인 worktree는 부모가 없는 것이 정상이다.

## 11. 조정자 worktree 갱신

`--detach`로 만든 조정자는 생성 시점에 고정된다. 자동으로 최신을 따라가지 않는다.

```bash
git -C "$COORD" fetch origin "$BASE" --quiet
git -C "$COORD" checkout --detach "origin/$BASE"
```

브랜치를 체크아웃한 worktree도 `git pull` 없이는 똑같이 뒤처지므로 detached라서 생기는
문제가 아니다. 오히려 `git pull`은 로컬 커밋이 있으면 merge가 일어나지만, detached
checkout은 항상 origin 상태 그대로다. 조정자는 커밋하지 않으므로 이쪽이 안전하다.

**조정자에서 무언가를 판정하기 전에 먼저 갱신한다.** 실측에서 기준 worktree가 20커밋
뒤처진 채로 비교해, 이미 머지된 파일 64개를 "없는 기록"으로 집계했다. 실제로 없는 것은
11개였다. 뒤처진 기준은 판단을 뒤집는다.

## 주의

- worktree id는 `<repoId>::<절대경로>`다. **경로를 옮기면 계보와 이슈 연결이 끊긴다.**
  편성 중에 디렉터리를 이동하지 않는다.
- 터미널 handle은 재생성되면 바뀐다. 저장해 둔 값으로 조작하면 `terminal_handle_stale`이
  난다. 필요할 때마다 `orca terminal list`로 다시 얻는다.
- 조정자 터미널을 만들 때는 명령 없이 셸만 띄운다. 에이전트 기동은 사용자의 몫이다.
