---
name: organize-worktree-lineage
description: Use when organizing existing git worktrees into Orca lineage — linking issues, setting parent worktrees and board status in bulk, or applying one explicitly named worktree's lineage and epic display name (single-target mode)
argument-hint: "[repo] [--dry-run]"
user-invocable: true
allowed-tools: Bash
---

# Organize Worktree Lineage

이미 있는 worktree를 Orca 계보(parent/child)와 이슈 연결, 보드 상태로 편성한다. 모드는
둘이고 한 실행에서 섞지 않는다.

| 모드 | 범위 | 절 |
| --- | --- | --- |
| 일괄 | 저장소 하나의 worktree 전체를 판정해 한 번에 편성한다 | §1–§11 |
| 단일 대상 | 호출자가 명시한 worktree 하나의 계보·이슈·표시 이름만 적용한다 | §12 |

`create-worktree`는 새로 만들거나 재개한 worktree 하나에 단일 대상 모드를 명시 호출한다.
에픽 표시 이름의 결정 규칙은 §13 한 곳에만 둔다.

조회는 read-only다. 변경은 계획을 보여 주고 승인받은 뒤에만 실행한다. 단일 대상 모드의
승인 기준은 §12에 있다.

## 실행 순서 요약 — 일괄 모드

단일 대상 모드는 §12의 순서만 따르고 아래 판정(§2–§6)을 거치지 않는다.

1. 대상 worktree 수집
2. 브랜치명에서 이슈 번호 추출
3. PR 조회 — 작성자 확인
4. 상위 에픽 조회
5. 그룹 판정 — `review` → `epic-<번호>` → `standalone`
6. 상태 도출 — 묶음마다 다른 어휘
7. 역할 worktree 생성
8. 변경 계획 표시 및 승인
9. 적용
10. 사후 확인
11. 조정자 worktree 갱신

## 편성 구조

메인 밑에는 역할 worktree(조정자)만 둔다. 작업 worktree는 모두 역할 worktree 밑에 들어간다.

```
<메인>
├── review          남의 PR — 리뷰하려고 만든 worktree
├── epic-<번호>     상위 에픽이 있는 내 이슈. 에픽마다 하나
└── standalone      에픽이 없는 내 이슈
```

작업 worktree를 메인 직속에 흩어두지 않는다.

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
| `linkedPR` | Orca가 채운 PR 번호. PR 조회(§3)에 먼저 쓴다. 비어 있을 수 있다 |
| `workspaceStatus` | 현재 보드 상태 |
| `isMainWorktree` | 메인은 편성 대상이 아니다 |

저장소가 여럿이면 어느 저장소를 편성할지 먼저 확정한다. 지정이 없으면 후보를 제시하고
선택받는다. 전체 저장소를 기본값으로 삼지 않는다.

확정한 뒤에는 그 저장소 범위 목록만 쓴다. `<repoId>`는 확정한 저장소 worktree의 `id`에서
`::` 앞부분이다.

```bash
orca worktree list --repo "id:<repoId>" --json
```

이후 역할 worktree 재사용·부모 후보·사후 확인은 모두 이 목록 안에서 찾고, 부모는 전체
`id`로 기록한다. 부모 지정에는 그 값을 `id:<전체 id>`로 쓰거나, 같은 목록에서 그 `id`와
대조한 경로를 `path:<절대경로>`로 쓴다. `issue:` · `name:` · `branch:` 셀렉터와 cwd로
해석되는 `active`는 부모 지정에 쓰지 않는다. 앞의 셋은 셀렉터에 저장소 범위가 없어 이
저장소의 worktree로 해석됐는지 보장되지 않는다(#176).

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

번호를 얻지 못한 worktree는 **사용자에게 보고하고 에픽 판정과 이슈 연결에서 건너뛴다.**
디렉터리 이름이 비슷하다는 이유로 다른 이슈에 연결하지 않는다. PR 조회(§3)는 이슈 번호가
아니라 `linkedPR`과 브랜치로 하므로 이런 worktree도 조회한다.

> 실측 근거: tmux 창 이름의 번호는 이슈가 아니라 **PR 번호**였고, 그마저도 최신이 아니었다.
> 창 `1216-user-partnership-inquiry`의 실제 PR은 #1305, 창 `1471-admin-partner-vat-reports`의
> 실제 PR은 #1476이었다. 브랜치의 `1216-feat/...`, `1467-feat/...`가 각각 정확한 이슈였다.

## 3. PR 조회

worktree마다 PR 하나를 정한다.

```bash
gh api user --jq .login    # 내 로그인

# linkedPR이 있으면 — 정확히 하나
gh pr view <linkedPR> --json number,state,reviewDecision,isDraft,author

# linkedPR이 없으면 — 브랜치로 찾는다
gh pr list --head "<브랜치명>" --state all --json number,state,reviewDecision,isDraft,author
```

**`linkedPR`이 있으면 그것을 쓴다.** 추가 조회 없이 PR이 하나로 정해진다. `linkedPR`은
Orca가 채우고 CLI로 설정할 수 없어서 비어 있는 worktree가 많다. 없을 때만 브랜치로 찾는다.

`--head`에는 `refs/heads/`를 뗀 브랜치명을 넣는다. owner 접두사(`<owner>:<브랜치>`)는
붙이지 않는다. 붙이면 fork PR도 0건이 된다. 접두사 없이도 fork PR과 원격에서 지운 브랜치의
PR이 찾힌다.

**한 브랜치에 PR이 여럿일 수 있다.** 흔한 브랜치명이 fork끼리 겹친 경우와, 닫고 다시 연
경우다.

**작성자가 서로 다른 PR이 섞였으면 판정하지 않고 보고한다.** 아래 선택 규칙은 한 사람이
닫고 다시 연 경우를 위한 것이라, 섞인 결과에 쓰면 남의 PR을 집는다.

```
eslint/eslint  --head patch-1                    100건 이상 (--limit 100에 걸림)
eslint/eslint  --head fix-no-loss-of-precision   #21337 OPEN sethamus · #20164 MERGED fasttime
```

작성자가 모두 같아도 첫 항목(`.[0]`)을 집으면 틀린다. 다음 순서로 고른다.

1. `OPEN`이 있으면 그것
2. 없으면 `MERGED`
3. 둘 다 없고 `CLOSED`만 있으면 그때 폐기 후보로 본다

PR이 2개 이상이면 전부 보고한다. 실측 사례다.

```
1467-feat/admin-partner-vat-reports     PR#1476 CLOSED · PR#1471 OPEN   ← 살아있음
fix/partner-rate-tables-asm-only        PR#1421 CLOSED · PR#1419 MERGED ← 머지됨
```

두 경우 모두 `.[0]`이 `CLOSED`를 집어 "폐기"로 오판했다. 진행 중인 리뷰를 지울 뻔했다.

고른 PR의 `author.login`을 내 로그인과 비교한다. 그룹 판정 ①의 근거다(§5).

## 4. 상위 에픽 조회

```bash
gh api graphql -f query='
{ repository(owner:"<owner>", name:"<repo>") {
    issue(number:<번호>) { number title parent { number title } } } }'
```

`parent`가 있으면 `epic-<parent 번호>` 밑, 없으면 `standalone` 밑이다. 에픽이 없는 이슈를
묶으려고 임의의 에픽 그룹을 만들지 않는다. PR 작성자가 내가 아닌 worktree는 `review`로
가므로(§5 ①) 조회하지 않아도 된다.

조회에 실패하면 그 항목을 건너뛰고 보고한다. 실패를 "에픽 없음"으로 해석하지 않는다.

`parent.title`은 에픽 역할 worktree의 표시 이름 결정(§13)에 `epicTitle`로 넘긴다.

## 5. 그룹 판정

위에서부터 먼저 맞는 것을 따른다.

```
① PR 작성자가 내가 아니다 (§3)   → review 밑
② 이슈에 상위 에픽이 있다 (§4)    → epic-<에픽번호> 밑
③ 그 외                            → standalone 밑
```

**①이 ②보다 먼저다.** 에픽에 속한 이슈라도 남의 PR이면 `review`에 남는다. 남의 작업이기
때문이다. 남의 브랜치 worktree는 리뷰하려고 만든 것이다.

리뷰 요청이 지금 inbox에 있는지는 ① 판정에 쓰지 않는다. 리뷰를 내면 요청이 inbox에서
빠지므로, inbox로 판정하면 상대가 고치는 중인 PR이 ②③으로 흘러간다. inbox는 `review`
밑 상태에만 쓴다(§6).

①에 걸리지 않은 worktree는 내 PR이거나 PR이 없는 내 브랜치다. 그래서 ②③에는 내 작업만
들어간다.

**이미 `review` 밑에 있다는 사실은 판정 근거가 아니다.** 근거로 삼으면 한번 잘못 들어간
worktree가 빠져나오지 못한다. 작성자가 나인 PR이 `review` 밑에 있으면 ②③으로 옮긴다.

예외는 하나다. `review` 밑 worktree가 `linkedPR`도 없고 `--head`로도 PR을 찾지 못하면
계보와 상태를 바꾸지 않고 보고한다. 리뷰 worktree에는 PR이 있어야 하므로, 여기서 PR 없음은
"내 브랜치"라는 증거가 아니라 데이터가 없다는 뜻이다. 그대로 ③으로 옮기면 남의 작업이 내
묶음에 들어갈 수 있다. 드문 경우다. fork PR과 원격에서 지운 브랜치의 PR도 `--head`로
찾힌다(eslint/eslint fork PR, zambaguni-front #1475·#1472 실측). 매번 보고되므로 오분류가
조용히 남지 않는다.

§3에서 작성자가 섞여 판정하지 않은 worktree는 편성하지 않는다.

이슈 번호가 없는 worktree(§2)는 ①에 걸리면 이슈 연결 없이 `review`로 편성하고, 아니면
편성하지 않는다.

**자식 수를 세지 않는다.** 에픽이 있으면 그 밑에 들어갈 worktree가 하나뿐이어도
`epic-<번호>`를 만든다. 판정이 기계적이어야 다시 돌려도 같은 결과가 나온다.

역할 worktree가 이미 있으면 재사용한다. 저장소 범위 목록(§1)에서 다음으로 찾는다.

| 역할 | 기존 역할 worktree 판정 |
| --- | --- |
| 리뷰 | `displayName`이 `review`이고 `parentWorktreeId`가 메인의 `id` |
| 에픽 | `linkedIssue`가 에픽 번호이고 `parentWorktreeId`가 메인의 `id` |
| 단독 | `displayName`이 `standalone`이고 `parentWorktreeId`가 메인의 `id` |

에픽 역할은 표시 이름이 아니라 `linkedIssue`로 찾는다. 에픽 표시 이름은 §13에 따라 달라질
수 있다.

후보가 2개 이상이면 하나를 고르지 않는다. 후보의 전체 `id`를 보고하고 그 역할 밑으로
가는 항목을 편성하지 않는다.

## 6. 상태 도출

상태 어휘는 **묶음마다 다르다.** 소유권이 다른 것을 같은 축으로 두면 정반대로 판정한다.
같은 `CHANGES_REQUESTED`라도 내 PR이면 내가 고칠 차례이고, 남의 PR이면 상대가 고칠
차례다.

> 실측 근거: `review` 밑 worktree를 `in-progress`로 뒀다가 틀렸다. 내가 작업 중인 게
> 아니라 상대가 고치는 중이었다.

### 내 작업 — `epic-*` · `standalone` 밑

`in-progress` · `in-review` · `completed` 세 값을 쓴다.

| PR 상태 | `workspaceStatus` |
| --- | --- |
| `MERGED` | `completed` |
| `OPEN`, 리뷰 결정 없음 | `in-review` — 내 PR이 리뷰를 기다린다 |
| `OPEN` + `APPROVED` | `in-review` — 머지를 기다린다 |
| `OPEN` + `CHANGES_REQUESTED` | `in-progress` — 내가 고쳐야 한다 |
| `OPEN` + `isDraft` | `in-progress` |
| PR 없음 | `in-progress` |
| `CLOSED` | **판단 보류.** 변경하지 않고 보고한다 |

`CLOSED`는 재작업 중일 수도 폐기일 수도 있다. 자동으로 정하지 않는다.

### 리뷰 — `review` 밑

`in-review` · `completed` 두 값만 쓴다. 상대의 진행 상태를 내 보드가 추적하지 않는다.

```bash
# 지금 리뷰 요청이 와 있는 PR — GitHub inbox
gh pr list --repo "<owner>/<repo>" --search "review-requested:@me" --state open \
  --limit 100 --json number,headRefName
```

`--repo`로 저장소를 반드시 지정한다. 지정하지 않으면 다른 저장소 PR이 섞인다. 브라우저의
`github.com/pulls/inbox?filter=repo:<owner/repo>`와 같은 결과다. 결과 개수가 `--limit`과
같으면 잘린 것이다. 늘려서 다시 조회한다. PR의 `headRefName`과 worktree `branch`가 같으면
inbox에 있는 것이다.

`gh search prs --review-requested=@me`는 매칭에 쓸 수 없다. `headRefName` 필드를
제공하지 않는다(`Unknown JSON field: "headRefName"`).

| 조건 | `workspaceStatus` |
| --- | --- |
| inbox에 있다 | `in-review` — 내 차례다 |
| inbox에 없다 (요청 없음 · 상대 차례 · 머지됨) | `completed` — 내 차례가 아니다 |

`in-progress`·`todo`는 `review` 밑에서 쓰지 않는다. `CHANGES_REQUESTED`를 냈어도 고칠
사람은 내가 아니다. 재요청으로 inbox에 다시 들어오면 `in-review`로 되돌린다.

### 정리 후보

`review` 밑 worktree는 **PR이 `MERGED` 또는 `CLOSED`면 제거 대상이다.** 상대가 머지하면
내가 볼 일이 없다. inbox에 없어도 PR이 `OPEN`이면 상대 차례일 뿐이니 남긴다. 제거한 뒤
재요청이 오면 `create-worktree`로 다시 만든다.

내 작업 묶음에서 `completed`로 판정된 worktree도 정리 후보다.

정리 후보는 목록으로 보고하되 이 스킬에서 제거하지 않는다. 제거는 `remove-worktree`의
몫이다.

## 7. 역할 worktree 생성

역할 worktree는 조정자다. 만드는 것은 §8에서 승인받은 뒤다.

아래 표는 역할 worktree 자신의 설정이다. 그 밑의 작업 worktree는 묶음과 관계없이 자기
이슈 번호를 연결한다(§9).

| 역할 | 디렉터리 이름 | `--display-name` | `--issue` |
| --- | --- | --- | --- |
| 리뷰 | `review` | `review` | 주지 않는다 |
| 에픽 | `epic-<에픽번호>` | §13의 결정값. 제목을 확인하지 못했으면 `epic-<에픽번호>` | `<에픽번호>`. 보드에서 에픽을 가리킨다. 셀렉터로는 쓰지 않는다 |
| 단독 | `standalone` | `standalone` | 주지 않는다 |

디렉터리 이름·`linkedIssue`·전체 `id`는 표시 이름과 무관하게 고정한다.

조정자는 코드를 고치지 않으므로 `--detach`로 만든다. 브랜치를 남기지 않아 나중에 정리할
것이 줄어들고, `develop` 같은 공용 브랜치를 점유하지 않는다. git worktree는 같은 브랜치를
두 곳에 체크아웃할 수 없다. 의존성은 설치하지 않는다. 설치하지 않은 조정자는 작다
(zambaguni-front 기준 117M).

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

### Orca 등록

```bash
orca worktree set --worktree "path:$WORKTREE_PATH" --display-name "<표시 이름>" \
  --parent-worktree "path:$MAIN" --workspace-status in-progress --json
orca terminal create --worktree "path:$WORKTREE_PATH" --title "<디렉터리 이름>-ORCH" --json
```

`epic-*`에는 `--issue <에픽번호>`를 함께 준다. 셀렉터는 `name:`이 아니라 `path:`를
쓴다. `review`·`standalone`은 저장소마다 같은 이름이라 `name:`으로는 저장소를 가리지
못한다. 등록 뒤 저장소 범위 목록(§1)을 다시 읽어 새 역할 worktree의 전체 `id`를 기록한다.
§9의 부모 셀렉터와 §10의 대조에 이 값을 쓴다.

## 8. 변경 계획 표시

적용 전에 표로 보여 준다. 승인 없이 실행하지 않는다.

```
worktree                          이슈    현재 부모   →  새 부모       상태 변경
guest-booking-token-url-removal   #1352   없음          epic-1350     없음 → in-progress
admin-partner-vat-reports         #1467   없음          review        없음 → completed
forum-board-noindex               #1411   없음          standalone    없음 → completed
```

다음은 별도 항목으로 함께 보고한다.

- 이슈 번호를 얻지 못한 worktree
- PR이 `CLOSED`라 상태를 보류한 worktree
- `linkedPR`이 없고 `--head` 결과에 작성자가 섞여 판정하지 않은 worktree
- `review` 밑인데 `linkedPR`도 `--head` 결과도 없어 옮기지 않은 worktree
- 정리 후보가 된 worktree — `review` 밑 PR `MERGED`·`CLOSED`, 내 작업 `completed`
- 새로 만들 역할 worktree와 그 경로
- 에픽 역할 worktree(새로 만들거나 재사용)의 표시 이름 결정 — §13의 네 필드

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

- 부모 셀렉터는 묶음과 관계없이 `id:<역할 worktree 전체 id>` 또는 그 `id`와 대조한
  `path:<역할 worktree 경로>`를 쓴다. 값은 §5·§7에서 저장소 범위 목록으로 확정한 역할
  worktree의 것이다. `epic-*` 밑이라도 `issue:<에픽번호>`를 쓰지 않는다
- 부모 경로가 대상 worktree 자신의 경로와 같으면 실행하지 않고 보고한다
- `--issue`에는 그 worktree 브랜치의 이슈 번호를 준다. 번호를 얻지 못한 `review` 밑
  worktree만 `--issue`를 뺀다
- 역할 worktree 자신은 §7의 Orca 등록으로 설정한다
- 계보를 의도적으로 두지 않을 때만 `--parent-worktree` 대신 `--no-parent`를 쓴다. 두
  옵션을 한 명령에 함께 주지 않는다

한 번에 한 worktree씩 실행하고 각 응답의 `ok`를 확인한다. 실패한 항목을 성공으로 보고하지
않는다.

## 10. 사후 확인

저장소 범위 목록(§1)을 다시 읽어 `parentWorktreeId`, `linkedIssue`, `workspaceStatus`가
계획과 일치하는지 대조한다. `parentWorktreeId`는 기록해 둔 역할 worktree의 전체 `id`와
같아야 한다. 다른 저장소의 worktree를 가리키면 실패다. 명령의 응답만으로 끝내지 않는다.

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

## 12. 단일 대상 모드

호출자가 명시한 worktree 하나에만 계보·이슈 연결·보드 상태와, 에픽 역할이면 표시 이름을
적용한다. `create-worktree`가 신규 생성과 기존 대상 재개에서 이 모드를 호출한다. 부모는
판정하지 않고 입력으로 받는다. 일괄 모드의 §2–§6 판정, §7 역할 worktree 생성, §11 갱신은
하지 않는다.

### 입력

| 입력 | 형식 | 필수 |
| --- | --- | --- |
| 저장소 | repo ID, 또는 메인 worktree 절대경로 | 예 |
| 대상 | 전체 worktree `id`(`<repoId>::<절대경로>`), 또는 절대경로 | 예 |
| 부모 | 부모의 전체 `id`, 또는 `no-parent`. 둘 중 하나만 | 예 |
| 이슈·PR 참조 | 연결할 이슈 번호와 PR 번호. 없으면 `없음`이라고 명시한다 | 예 |
| git base 확인 근거 | 대상 브랜치와 `HEAD`, 호출자가 계보와 별도로 확인한 base(예: 기대 `HEAD` 일치) | 예 |
| 역할 | `epic` · `review` · `standalone`. 역할 worktree가 아니면 주지 않는다 | 아니오 |
| 기존 `displayName`과 사용자 지정 여부 | 호출자가 아는 값. 모르면 `미상` | 에픽 역할이면 예 |
| 이전 결과 | 이전 실행 결과의 `displayName`·`epicTitle`. 없으면 `없음` | 에픽 역할이면 예 |
| 에픽 번호·제목 | 에픽 역할일 때. 제목을 모르면 `미상` | 에픽 역할이면 번호는 예 |
| 보드 상태 | 호출자가 정한 `workspaceStatus`. 이 모드는 상태를 도출하지 않는다 | 아니오 |

- 부모는 전체 `id`로만 받는다. `path:` · `issue:` · `name:` · `branch:` · `active`로 받지
  않는다(§1).
- PR 번호는 `linkedPR`을 CLI로 설정할 수 없으므로(§3) 적용하지 않고 결과에 기록만 한다.
- 이슈 번호는 호출자가 준 값을 쓴다. 대상 브랜치명에서 §2로 다시 추출하거나 호출자의 해석을
  뒤집지 않는다. `lee-kyu-hwan/208-...`처럼 §2의 선행 숫자 규칙으로는 번호가 없는 사용자
  접두사 브랜치도 호출자가 준 번호로 연결한다. 해석 규칙은 `create-worktree`의 "이슈·PR 참조
  해석"에 있다.
- 에픽 역할이면 이슈 참조는 에픽 번호다.
- 역할은 호출자가 명시한 값만 받는다. `create-worktree`의 `epic_orchestrator`는 `epic`으로
  넘어오고, `repo_orchestrator`는 역할 없이 넘어온다. 이 모드가 브랜치·디렉터리 이름·
  `linkedIssue`에서 역할을 추론하지 않는다.
- 계보는 git base를 정하지 않는다. 이 모드는 base를 바꾸거나 계보에 맞춰 판정하지 않고,
  받은 근거를 대조해 결과에 옮긴다.
- 에픽 제목이 `미상`이면 §4 조회를 한 번 할 수 있다. 호출자가 GitHub 조회를 금지했거나
  조회가 실패하면 조회하지 않은 것으로 두고 §13의 미확인 규칙을 따른다.

### 멈추는 경우

다음이면 `set`을 하나도 하지 않고, 받은 입력과 어긋난 값을 그대로 보고한다. 다른 셀렉터로
바꾸거나 부모를 추측해 다시 시도하지 않는다. 역할 worktree가 없다고 새로 만들지 않는다.

- 필수 입력이 없거나, 부모를 전체 `id`와 `no-parent`로 함께 주었거나, 입력이 둘 이상으로
  해석된다
- 저장소를 확정하지 못했다 — 경로와 일치하는 메인 항목이 0개·2개 이상이거나, 저장소 범위
  목록 조회가 실패했다
- 대상이 저장소 범위 목록에서 0개·2개 이상이거나 메인 worktree다
- 부모 전체 `id`가 저장소 범위 목록에 없거나, 대상 자신이거나, 부모의 조상 사슬
  (`parentWorktreeId`를 따라간 항목)에 대상이 있다
- git base 근거의 `HEAD`가 `git -C "<대상 경로>" rev-parse HEAD`와 다르다
- 에픽 역할인데 에픽 번호가 없거나, 대상의 `linkedIssue`가 다른 번호다

### 순서

1. **저장소.** repo ID면 그대로 쓴다. 절대경로면 전체 목록에서 `path`가 그 경로이고
   `isMainWorktree`인 항목 하나의 `id`에서 `::` 앞부분을 쓴다. 이후
   `orca worktree list --repo "id:<repoId>" --json`만 쓰고, 첫 결과를 적용 전 스냅숏으로
   보관한다.
2. **대상.** 스냅숏에서 `id`가 입력 전체 `id`와 같거나 `path`가 입력 절대경로와 같은 항목
   하나. `TARGET_ID`·`TARGET_PATH`로 기록한다.
3. **부모.** `no-parent`거나, 스냅숏에서 `id`가 입력 전체 `id`와 정확히 같은 항목.
   `PARENT_ID`로 기록한다.
4. **git base 근거 대조.** 위 멈추는 경우를 따른다.
5. **표시 이름.** 에픽 역할이면 §13으로 정한다. 아니면 `displayName`을 건드리지 않는다.
6. **계획과 승인.** 대상의 현재 값과 계획을 비교한다.
   - 현재 `parentWorktreeId`가 비어 있지 않은데 계획과 다르면(`no-parent`로 떼는 경우
     포함) 현재 부모 → 새 부모 계획을 보여 주고 승인받는다. 조용히 덮어쓰지 않는다(§8).
   - 현재 `linkedIssue`가 다른 번호거나, §13이 `revised`로 기존 이름을 바꾸면 같다.
   - 승인받지 못하면 아무것도 적용하지 않고 보고한다.
   - 그 외(빈 값을 채우거나 이미 같은 값)는 호출자의 명시 입력을 지시로 보고, 계획을
     결과에 남긴 뒤 적용한다.
7. **적용.** 대상 하나에 `set`을 한 번 한다. 이미 같은 값의 옵션은 뺀다. 바꿀 값이 없으면
   `set`을 하지 않는다.

   ```bash
   orca worktree set --worktree "id:<TARGET_ID>" \
     --parent-worktree "id:<PARENT_ID>" \
     --issue <번호> \
     --display-name "<§13 결정값>" \
     --workspace-status <호출자가 준 값> \
     --json
   ```

   - `no-parent`면 `--parent-worktree` 대신 `--no-parent`를 준다. 두 옵션을 함께 주지
     않는다.
   - `--issue`는 이슈 참조가 `없음`이면 뺀다. `--display-name`은 §13이 이름을 바꿀 때만,
     `--workspace-status`는 호출자가 줬을 때만 넣는다.
8. **재조회.** 같은 저장소 범위 목록을 다시 읽는다. 응답의 `ok`만으로 끝내지 않는다.
   - `TARGET_ID` 항목의 `parentWorktreeId`가 `PARENT_ID`와 같다(`no-parent`면 비어 있다).
     `linkedIssue`·`displayName`·`workspaceStatus`가 계획과 같다. 다르면 성공으로 보고하지
     않는다.
   - 대상 외 항목의 `parentWorktreeId`·`linkedIssue`·`displayName`을 스냅숏과 비교한다.
     달라졌으면 같은 저장소의 다른 작업일 수 있으므로 되돌리지 않고 차이를 보고한다.

### 하지 않는 것

- 다른 역할 worktree를 만들지 않는다.
- 대상 외 worktree의 부모·이슈·상태·표시 이름을 바꾸지 않는다. 대상의 자식이나 같은 에픽
  밑 형제도 그대로 둔다. 예를 들어 에픽 밑 검증 worktree(#192 verifier)가 대상이 아니면
  그 부모는 바꾸지 않는다.
- 저장소 전체를 재편성하지 않는다. 필요하면 일괄 모드를 따로 실행한다.
- git base를 바꾸거나 디렉터리를 옮기지 않는다.

### 결과

다음 필드를 이 이름 그대로 보고한다. 호출자는 이 이름으로 읽는다.

```
repoId             <repoId>
targetId           <대상 전체 id>
targetPath         <대상 절대경로>
parent             <PARENT_ID | no-parent>  (이전: <이전 parentWorktreeId | 없음>)
linkedIssue        <번호 | 없음>
pr                 <번호 | 없음>  (기록만)
gitBase            <받은 근거와 대조 결과>
workspaceStatus    <재조회 값>
displayName        <재조회 값>
displayNameSource  <§13 값>
epicTitle          <사용한 제목 원문 | 미확인 | 해당 없음>
namingDecision     <§13 값>
verification       <재조회 대조 결과. 대상 외 항목 변화 포함>
```

`displayName` · `displayNameSource` · `epicTitle` · `namingDecision` 네 필드는 에픽 역할이
아니어도 넣는다. 이때 `displayNameSource`와 `namingDecision`은 `not-applicable`, `epicTitle`은
`해당 없음`이다.

이 모드는 조정자를 시작하지 않고 `start-orca-orchestrator`(#209)를 부르지 않는다.
`create-worktree`가 이 결과를 재조회로 검증한 뒤, 사용자가 역할을 명시했을 때만 네 표시 이름
필드를 #209 계약의 `naming`에 이름·값 그대로 옮기고 `parent`·`linkedIssue`·`pr`·`gitBase`를
`lineage`의 근거로 쓴다.

## 13. 에픽 표시 이름

에픽 역할 worktree의 `displayName`은 이 절에서만 정한다. 일괄 모드(§7과 재사용한 에픽 역할
worktree)와 단일 대상 모드(§12)가 같은 규칙을 쓴다. `create-worktree`와
`start-orca-orchestrator`(#209)는 이름을 따로 만들거나 제목을 다시 요약하지 않는다. 단일
대상 모드 결과의 네 필드를 받아 그대로 쓴다.

### 형식

`<대표 제목> · #<에픽번호>`

- `<대표 제목>`은 유효한 에픽 제목의 핵심 목표를 짧게 드러내는 구절이다. 보드에서 한 줄로
  읽히는 길이로 줄인다.
- 제목 앞의 `[epic]` 접두사(대소문자 무관)와 앞뒤 공백을 뗀다. 뗀 뒤 비어 있으면 유효한
  제목이 아니다.
- 디렉터리 이름 `epic-<번호>`, `linkedIssue`, 전체 `id`는 바꾸지 않는다. 표시 이름은 보드
  표시만 바꾼다. 역할 판정(§5)은 `linkedIssue`로 하므로 표시 이름과 무관하다.

예: 제목 `[epic] 게스트 예약 흐름의 토큰 URL 제거와 보안 정비`, 번호 1350 →
`게스트 예약 토큰 URL 제거 · #1350`

### 결정

위에서부터 먼저 맞는 것을 따른다. 새 이름(`decided`·`revised`의 제목 요약)은 유효한 에픽
제목을 이번에 확인했을 때만 적용한다. 확인하지 못했으면(조회 실패·`미상`·유효하지 않음)
그 행을 건너뛰고 마지막 행으로 간다.

| 조건 | `displayName` | `displayNameSource` | `namingDecision` |
| --- | --- | --- | --- |
| 사용자가 이번에 이름 변경을 명시 요청 | 지정한 이름. 재요약 요청이면 유효한 제목에서 새로 정한다 | `user` 또는 `epic-title` | `revised` |
| 호출자가 현재 이름을 사용자 지정이라고 명시했다 | 보존 | `user` | `preserved` |
| 현재 이름이 이전 결과의 `displayName`과 같고, 이전 `epicTitle`이 지금 제목과 다르다 | 지금 제목에서 새로 정한다 | `epic-title` | `revised` |
| 현재 이름이 이전 결과의 `displayName`과 같다 | 보존 | `previous` | `preserved` |
| 현재 이름이 비었거나 디렉터리 이름 `epic-<번호>`와 같다 | 제목에서 정한다 | `epic-title` | `decided` |
| 그 외 — 결정 출처를 모르거나(사용자 지정 여부 `미상` 포함) 제목을 확인하지 못했다 | 보존. 이름이 없으면 `epic-<번호>` | `previous` · `unknown` · `fallback` 중 해당 | `unverified` |

- 결정 출처는 호출자의 명시와 이전 결과로만 안다. 이름 모양이나 Orca의
  `displayNameMode`(예: `fixed`)로 사용자 지정인지 자동 생성인지 단정하지 않는다.
- 한 번 정한 요약은 다시 돌려도 다시 요약하지 않는다. 명시 요청이나 제목의 실제 변경일
  때만 재검토한다. 이전 `epicTitle`이 없으면 제목이 바뀌었다고 판단하지 않는다.
- `epicTitle`에는 확인한 제목 원문(접두사 포함)을 넣는다. 확인하지 못했으면 `미확인`이다.
- `revised`로 기존 이름을 바꾸는 것은 승인 대상이다(일괄 모드 §8, 단일 대상 모드 §12의 6).
- `·`(U+00B7)가 `--display-name`에 그대로 저장되는지는 이 문서에서 확인하지 않았다.
  재조회한 `displayName`이 결정값과 다르면 성공으로 보고하지 않는다.

## 주의

- worktree id는 `<repoId>::<절대경로>`다. **경로를 옮기면 계보와 이슈 연결이 끊긴다.**
  편성 중에 디렉터리를 이동하지 않는다.
- 터미널 handle은 재생성되면 바뀐다. 저장해 둔 값으로 조작하면 `terminal_handle_stale`이
  난다. 필요할 때마다 `orca terminal list`로 다시 얻는다.
- 조정자 터미널을 만들 때는 명령 없이 셸만 띄운다. 에이전트 기동은 사용자의 몫이다.
