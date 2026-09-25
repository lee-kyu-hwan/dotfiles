---
name: create-worktree
description: Use when creating a git worktree for a branch or a pull request (PR) review, optionally opening it in a named tmux session
---

# Create Worktree

브랜치 또는 PR의 git worktree를 만들거나 기존 worktree를 재개한다. 경로는 둘이다. Orca
전용 경로는 tmux·workmux 없이 git과 Orca CLI로만 진행하고, tmux 경로(legacy)는 선택한
tmux 세션의 workmux 윈도우로 연결한다. 창과 세션 상태를 추측하지 말고 아래 순서대로
확인한다.

## 실행 순서 요약

1. 입력 파싱(파라미터). `ROOT`를 스킬을 시작한 셸에서 한 번 구해 고정한다
2. 경로 선택(경로 선택 절). tmux·workmux 명령을 하나도 실행하기 전에 정한다
3. PR 모드면 저장소 확정과 PR 해석 → head 브랜치·`headRefOid`·작성자 확보
4. Orca를 쓸 수 있으면 계보 입력 확정: 저장소 범위·호출자·부모 전체 ID와 이슈·PR
   참조(Orca 계보 설정 절). cwd를 바꾸기 전이어야 한다
5. 경로별 실행
   - Orca 전용: 기존 worktree 판정(`git worktree list --porcelain`과 Orca 저장소 범위
     목록) → 없으면 "Orca 전용 생성", 있으면 재개. 끝까지 tmux·workmux를 부르지 않는다
   - tmux(legacy): 기존 worktree·handle 확보(`workmux list --json`) → 창 탐지(`is_open` →
     저장 세션 → `target-window` → pane 경로) → 세션 선택 → 세션 검증 → 이름 파생 → 창
     처리 또는 생성·오픈
6. 새로 만들었든 재개했든 대상 worktree 하나에 `organize-worktree-lineage` 단일 대상
   모드를 명시 호출하고 결과를 재조회로 검증한다(Orca 계보 설정 절)
7. 사용자가 역할을 `repo_orchestrator`·`epic_orchestrator`로 명시했을 때만, 6의 재조회
   검증을 통과한 그 대상 하나로 `start-orca-orchestrator`(#209)를 실제로 호출하고 출력
   상태를 검증한다(조정자 시작 연결 절)
8. 사후 검증과 보고

아래 절은 주제별로 묶여 있어 이 순서와 배열이 다르다. 실행은 이 순서를 따른다.

## 파라미터

- 첫 번째 positional 인자는 필수인 브랜치명 또는 PR 참조다. 없으면 사용자에게 묻는다.
- 두 번째 positional 인자는 선택 사항이며 정확한 tmux 세션명이다.
- positional 인자가 세 개 이상이면 추측하지 말고 `<branch-name|pr-ref> [target-session]`
  사용법을 안내한 뒤 중단한다.
- PR 모드는 다음 세 형태에서만 선택한다.
  - `https://github.com/{owner}/{repo}/pull/{번호}` 전체 URL
  - `{owner}/{repo}#{번호}`
  - `PR 1313`, `1313번 PR`, `pull request 1313`처럼 번호 앞뒤에 표지가 있는 자연어
- 표지 없는 맨 숫자(`1313`)는 PR로 단정하지 않는다. GitHub의 이슈와 PR은 번호 공간을
  공유하므로 엉뚱한 대상을 checkout할 수 있다. 브랜치로 해석하거나 해석할 수 없으면
  확인한다.
- 자연어 호출은 `(브랜치명|PR 참조, 대상 세션)` 2-튜플로 환원한다. 브랜치/PR 참조가
  둘 이상이거나 세션명이 둘 이상이면 중단하고 확인한다. 자연어가 2-튜플로 환원됐으면
  positional 인자 수 제한을 적용하지 않는다.
- 세션명에 접두사를 붙이거나 현재 세션 목록에서 비슷한 이름을 추측하지 않는다.
- Orca 계보 플래그 `--epic <이슈번호>`와 `--standalone`, 대상 플래그
  `--issue <이슈번호>`와 `--role <repo_orchestrator|epic_orchestrator>`는 선택 사항이다.
  positional 인자 수에 세지 않는다. 전체 사용법은
  `<branch-name|pr-ref> [target-session] [--epic <이슈번호> | --standalone] [--issue <이슈번호>] [--role <repo_orchestrator|epic_orchestrator>]`다.
- 두 플래그를 함께 주거나 `--epic` 값이 숫자가 아니면 추측하지 말고 중단한다. 둘 다
  없으면 기본값(호출자 worktree, PR 모드의 남의 PR은 `review`)이다. 의미는 "Orca 계보
  설정" 절에 있다.
- `--standalone`은 Orca `--no-parent`(최상위)다. `organize-worktree-lineage`의 `standalone`
  역할 그룹 밑에 두는 것과 다르며 같은 뜻으로 바꾸지 않는다.
- `--issue`는 대상 worktree에 연결할 이슈다. 부모 에픽을 찾는 `--epic`과 뜻이 다르다.
  값이 숫자가 아니거나 두 번 주면 중단한다. 해석과 충돌 규칙은 Orca 계보 설정의 "이슈·PR
  참조 해석"에 있다.
- `--role`은 대상 worktree의 조정자 역할이다. 값은 `repo_orchestrator`·`epic_orchestrator`
  중 정확히 하나이며 다른 값이거나 두 번 주면 중단한다. 주면 계보 검증 뒤
  `start-orca-orchestrator`(#209)를 호출하고, 주지 않으면 호출하지 않는다(조정자 시작 연결
  절). 역할 호출은 계보 검증이 전제이므로 Orca를 쓸 수 없으면 영속 명령 전에 중단한다.
- 역할은 사용자가 이번 호출에서 명시한 값으로만 정한다. 브랜치명, `epic-<번호>` 같은
  디렉터리·폴더 이름, `linkedIssue`, `--epic`·`--standalone` 여부에서 추론하지 않는다.
- 자연어 호출에서 에픽 이슈 번호나 최상위(독립) 배치가 명시됐을 때만 해당 플래그로
  환원한다. 어느 쪽인지 모호하면 기본값으로 가정하지 말고 확인한다. 대상 이슈는
  `이슈 208`처럼 표지가 있을 때만 `--issue`로, 조정자 역할은 `에픽 조정자로`·`repo
  orchestrator로`처럼 역할을 명시했을 때만 `--role`로 환원한다. 표지 없는 번호나 `#208`만으로는
  이슈로 단정하지 않는다.

## 경로 선택

tmux·workmux 명령(`tmux ...`, `workmux ...`. 읽기 전용 `workmux list`·`--dry-run` 포함)을
하나라도 실행하기 전에 경로를 정한다. 판정에는 입력과 Orca 사용 가능 여부만 쓴다.

| 조건 | 경로 |
| --- | --- |
| 대상 세션을 명시했다 | tmux(legacy) |
| 세션 명시 없음, Orca 사용 가능 | Orca 전용 |
| 세션 명시 없음, Orca 사용 불가 | tmux(legacy) |

Orca 사용 가능은 다음 두 조건이 모두 참일 때다. 실행 파일만 있고 앱이 응답하지 않으면
사용 불가다.

```bash
ORCA=/Applications/Orca.app/Contents/Resources/bin/orca
[ -x "$ORCA" ] && "$ORCA" worktree list --json    # 종료 코드 0, 응답 ok: true
```

Orca 전용으로 정했으면 이번 호출의 처음부터 끝까지 tmux·workmux 명령을 실행하지 않는다.
기존 worktree 판정, 경로·브랜치·부모 확인, 사후 검증 모두 git과 Orca CLI 응답만 쓴다.
워크트리 식별자(handle)·창 탐지·세션 선택·세션 검증·이름 파생 절과 `window-session`
읽기·쓰기를 모두 건너뛴다. 중간에 tmux 경로로 바꾸지 않는다. 막히면 멈추고 보고한다.

명시 세션 같은 legacy tmux 요청은 tmux 경로로 보존한다. 그 경로는 아래 워크트리 식별자
절부터 사후 검증의 tmux 부분까지를 따른다. Orca를 쓸 수 있으면 tmux 경로에서도 계보는
단일 대상 모드로 설정한다(Orca 계보 설정 절).

세션을 명시하지 않았는데 Orca를 쓸 수 있으면 handle에 저장된 `window-session`도 보지
않는다. handle은 workmux로만 얻기 때문이다. 저장된 세션으로 열려면 그 세션을 명시한다.

## 워크트리 식별자

이 절은 tmux 경로에서만 쓴다. Orca 전용 경로는 handle을 구하지 않는다.

git config 키의 `{handle}`은 `workmux list --json` 항목의 `handle` 필드다.
브랜치명이나 tmux 창 이름으로 유추하지 않는다. handle은 기본 명명에서는 `path`의
basename과 같을 수 있지만 `worktree_naming`, `worktree_prefix`, `--name`에 따라 달라질
수 있다. 특히 PR 모드의 `--target-name`은 handle과 창 이름을 구조적으로 갈라놓는다.

handle 하나에는 최대 `.mode`, `.target-window`, `.window-session`, `.window-token` 하위
키가 있다. 이 스킬은 `.window-session`만 읽거나 쓰고, `.target-window`는 창 탐지에서만
읽는다. 잘못된 handle로 `git config`를 쓰면 오류 없이 새 섹션이 생기므로 실제 값을
확보하기 전에는 쓰지 않는다.

`workmux list --json`을 쓸 수 없을 때만 worktree 절대경로의 basename을 폴백으로 쓴다.
그 경우 `path` 필드와 대조해 확인하며, 대조할 수 없으면 중단한다.

## 세션 선택

이 절은 tmux 경로에서만 쓴다. 세션을 명시하지 않았으면 이 절에 오는 것은 Orca를 쓸 수
없을 때뿐이다(경로 선택 절).

먼저 대상 브랜치의 기존 worktree와 경로를 확인해 handle을 확보한다. 그 후
`SELECTED_SESSION`을 다음 우선순위로 정한다.

1. 이번 호출에서 사용자가 명시한 세션
2. 기존 worktree의 `workmux.worktree.{handle}.window-session`이 `^[0-9]+-.+$`를 만족하고
   실제로 존재할 때의 저장값
3. 모드 기본값: PR 모드면 `2-review`
4. 전역 기본값 `1-main`

저장값은 사용자가 창을 직접 옮긴 기록이고 모드 기본값은 관습이므로, 저장값이 모드
기본값보다 우선한다.

| 명시 세션 | 유효하고 생존한 저장값 | 모드 | 선택 결과 |
| --- | --- | --- | --- |
| `3-personal` | `2-review` | PR | `3-personal` |
| 없음 | `3-personal` | PR | `3-personal` |
| 없음 | 없음 | PR | `2-review` |
| 없음 | 없음 | 브랜치 | 전역 기본값 `1-main` |

저장값은 셸 glob(`[0-9]*-*`)이 아니라 정규식 `^[0-9]+-.+$`로 판정한다. glob의 첫
`*`는 숫자 반복이 아닌 임의 문자열이어서 `1legacy-session`과 `1-`도 통과한다. 예전
마이그레이션에서 남은 값(예: `1-main`이 아닌 형식 밖 값)은 레거시로 취급한다.

선택 세션이 확정되기 전에는 영속 변경을 만드는 `workmux add`, `workmux open`,
`workmux remove`, `workmux close`를 실행하지 않는다. 읽기 전용 `workmux list --json`과
`--dry-run` 조회는 예외다.

명시 세션이 유효한 저장값을 덮었으면 창을 연 뒤 handle의 `window-session`이 명시 세션을
가리키는지 확인하고 다르면 갱신한다. 형식은 유효하지만 사라진 저장 세션이면 다음처럼
복구한다.

1. 사라진 저장값을 사용자에게 알린다.
2. 모드 기본값과 전역 기본값으로 계산한 대안을 제시하고 확인받는다.
3. 확인된 세션으로 진행한다.
4. 세션을 자동 생성하지 않는다.

레거시 또는 사라진 저장값을 고칠 때 기록할 값은 창의 실제 위치로 정한다.

| 상태 | `window-session` 갱신 대상 |
| --- | --- |
| 창이 닫혀 있음 | `SELECTED_SESSION` |
| 창이 열려 있고 명시 세션으로 이동함 | `SELECTED_SESSION` |
| 창이 열려 있으나 이동하지 않음 | 창 탐지로 확정한 실제 세션 |

실제 세션을 확정하지 못했으면 갱신하지 않는다. 세션 미명시 호출에서 열린 창을 옮기지
않는 경우에는 선택값이 아니라 실제 위치를 기록해야 config와 창 위치가 어긋나지 않는다.

## 세션 검증

tmux 경로에서만 쓴다. 선택 세션은 영속 workmux 명령 전에 검증한다.

```bash
tmux list-sessions -F '#{session_name}'
```

먼저 종료 코드를 확인한다. exit 1과 `error connecting to ...`는 tmux 서버 부재이고,
`tmux` 명령 자체가 없는 것은 tmux 미설치다. 둘 다 세션 부재와 구분해 기록한다. 목록
조회가 성공했을 때만 다음처럼 전체 문자열 일치로 확인한다.

```bash
tmux list-sessions -F '#{session_name}' | grep -qxF -- "$SELECTED_SESSION"
```

`tmux has-session -t`는 쓰지 않는다. tmux target은 접두사 매칭을 하므로 `2`나 `2-rev`가
의도치 않은 세션에 매칭될 수 있다. 선택 세션이 없으면 자동 생성하지 않는다. 검증 없이
`--parent-session`에 없는 값을 주면 workmux가 세션을 만들고 config에 영구 저장하는 유령
세션 위험이 있다.

선택 세션이 없거나 tmux 서버가 없거나 tmux가 설치되지 않았을 때는 세션의 출처로 처리를
정한다. 여기서 Orca 전용으로 바꾸지 않는다. Orca 전용은 경로 선택에서만 정한다.

| 세션 출처 | 처리 |
| --- | --- |
| 명시 세션 | 오타 가능성과 부재 종류를 알리고 중단한다 |
| 저장값 | 앞 절의 복구 경로를 따른다 |
| 모드·전역 기본값 | 부재 종류를 보고하고 중단한다. Orca를 쓸 수 없을 때만 이 행에 온다 |

## PR 해석

PR 입력에서는 다음 표로 `{owner}/{repo}`를 확정한다.

| 입력 | `{owner}/{repo}` 출처 |
| --- | --- |
| 전체 PR URL | URL 경로 |
| `{owner}/{repo}#{번호}` | 입력 문자열 |
| 표지가 있는 자연어 | 현재 저장소 |

현재 저장소는 우선 `gh repo view --json owner,name -q '.owner.login + "/" + .name'`으로
구하고, 실패하면 `git remote get-url origin`을 파싱한다. 둘 다 실패하면 중단한다.
입력 저장소와 현재 저장소가 다르면 두 값을 알리고 중단한다.

확정한 저장소에서 다음 다섯 필드와 내 로그인을 조회한다.

```bash
gh pr view {번호} --repo {owner}/{repo} --json number,state,headRefName,headRefOid,author
gh api user --jq .login
```

`number`, `headRefName`, `headRefOid`는 각각 이름 파생과 내용 검증에 쓰고, `state`는
CLOSED·MERGED 처리에 쓴다. `author.login`과 내 로그인은 Orca 계보의 `review` 부모 판정에만
쓴다. `gh`가 없거나 인증·조회에 실패하면 추측하지 말고 중단한다.
CLOSED 또는 MERGED면 상태를 알리고 계속할지 확인한다. 자동 중단하지 않되 head 브랜치가
삭제되어 fetch가 실패할 수 있음을 안내한다.

동일한 head 브랜치의 worktree가 이미 있으면 생성만 건너뛰고 기존 경로의 재개로
진행한다(tmux 경로는 창 처리, Orca 전용은 재개). 같은 이름의 로컬 브랜치가 head OID와
다르면 덮어쓰지 않고 중단한다.

래퍼 경로와 Orca 전용 경로에서 새 worktree를 만들기 전, 로컬 브랜치가 없을
때는 PR head를 확보한다.

```bash
git fetch origin "refs/pull/{PR번호}/head:{head브랜치명}"
git rev-parse --verify "refs/heads/{head브랜치명}"
```

검증 OID가 `headRefOid`와 다르거나 fetch가 실패하면 중단하고 래퍼를 호출하지 않는다.
래퍼는 브랜치를 찾지 못하면 현재 HEAD에서 빈 브랜치를 만들 수 있다.
래퍼가 없는 tmux 경로는 `workmux add --pr`가 체크아웃을 직접 하므로 사전 fetch가 필요 없다.
대신 생성 후 `HEAD`가 `headRefOid`와 같은지 검증해 같은 보장을 얻는다.

`workmux add --pr`에는 원시 입력을 넘기지 않는다. 저장소 일치와 PR 조회로 확정한 숫자만
정규화해 넘긴다. 따라서 `{owner}/{repo}#{번호}`와 자연어 표지 입력도 `--pr {PR번호}`가
된다.

## 이름 파생

tmux 경로의 창 이름에만 쓴다. Orca 전용 경로는 `{브랜치}`를 그대로 쓰고 창 이름을 만들지
않는다.

- 짧은 이름은 브랜치명(또는 PR head 브랜치명)의 마지막 `/` 뒤 부분이다.
  `392-feat/add-partner-chat-enabled`의 짧은 이름은 `add-partner-chat-enabled`다.
- 브랜치 모드의 이슈 번호는 브랜치명 맨 앞의 숫자 또는 `ZF-숫자`만 인식한다.
  `feat/392-add-x`에는 이슈 번호가 없다. 이 규칙은 창 이름 전용이며 그대로 둔다.
  `lee-kyu-hwan/208-...`의 창 이름에도 이슈 번호를 붙이지 않는다. Orca 계보에 넘길 이슈
  번호는 Orca 계보 설정의 "이슈·PR 참조 해석"을 따른다.
- PR 모드 창 이름은 `{PR번호}-{짧은이름}`이며, head 브랜치의 이슈 번호보다 PR 번호를
  우선한다.
- 브랜치 모드에 이슈 번호가 없으면 `--target-name`을 생략한다.
- workmux가 target name을 소문자로 정규화하므로 안내와 재사용에도 소문자 값을 쓴다.
- 창 이름 충돌 시 브랜치 모드는 `{repo명}-{짧은이름}`, PR 모드는
  `{PR번호}-{repo명}-{짧은이름}`으로 재시도한다.

## 생성·오픈 경로

저장소 루트에서 분기한다. 서브디렉터리나 기존 worktree에서의 오판을 막기 위해 상대
경로로 판정하지 않는다. `ROOT`는 스킬을 시작한 셸에서 1단계에 한 번 구한 값이며 이후
다시 계산하지 않는다.

```bash
ROOT=$(git rev-parse --show-toplevel)    # 1단계에서 한 번
test -f "$ROOT/scripts/create-worktree.sh"
git -C "$ROOT" config --get filter.git-crypt.smudge
```

git-crypt 저장소에서는 PR 모드를 포함해 원칙적으로 `workmux add`를 쓰지 않는다.

- 래퍼가 있으면 실행 권한을 먼저 확인한다. **실행 권한이 없으면** 경로를 바꾸지 말고
  오류로 보고한다. 래퍼가 실패하면 즉시 중단하고 `workmux open`으로 진행하지 않는다.
  확인 프롬프트를 `-y`나 `yes |`로 자동 우회하지 않는다.
- **예외:** git-crypt 필터가 있는데 래퍼가 없으면 `workmux add` 전에 사용자에게 확인받고
  진행한다.

래퍼 경로의 PR 모드는 head 브랜치를 확보한 뒤 다음 순서로 실행한다.

```bash
./scripts/create-worktree.sh {head브랜치명}
workmux open {handle} --target-name {PR번호}-{짧은이름} --parent-session "$SELECTED_SESSION"
```

브랜치 모드도 래퍼가 출력한 경로와 handle을 확보한 뒤 `workmux open`을 사용한다.
이슈 번호가 없으면 `--target-name`을 생략한다. 래퍼 출력에서 worktree 절대경로를 얻고,
그 경로와 일치하는 `workmux list --json` 항목의 handle을 쓴다. 아직 목록에 없으면
경로 basename을 `git worktree list --porcelain`으로 대조한 폴백으로만 사용하고, open 뒤
실제 창을 다시 확인한다. `workmux open`은 `git worktree list`로 찾으므로 `worktree_dir`
밖의 형제 디렉터리도 인식한다.

래퍼가 없는 PR 모드는 positional 브랜치명과 `--name`을 생략한다.

```bash
workmux add --pr {PR번호} --target-name {PR번호}-{짧은이름} --parent-session "$SELECTED_SESSION"
```

브랜치 모드는 이슈 번호가 있을 때만 `--target-name {이슈번호}-{짧은이름}`을 추가한다.
생성 전 `workmux add ... --dry-run`으로 예상 경로와 handle을 확인할 수 있다. 생성 뒤에는
출력과 `workmux list --json`에서 실제 경로·handle을 얻으며 이름을 추측하지 않는다.

`--parent-session`은 session mode, 샌드박스 안, `--count`, `--foreach`, 여러 `--agent`,
stdin을 통한 여러 worktree 생성에서는 지원되지 않으므로 그 조합에서는 생략한다.
PR worktree 생성 뒤에는 `git -C "{worktree경로}" rev-parse HEAD`가 `headRefOid`와 같은지
검증한다. 다르면 성공으로 보고하지 않는다.

### Orca 전용 생성

경로 선택에서 Orca 전용으로 정했을 때만 이 절을 쓴다. 이 경로는 workmux와 tmux에
기대지 않는다. `workmux add`(`--dry-run` 포함)·`workmux open`·`workmux list`와 tmux 조회를
실행하지 않고, worktree 경로·브랜치·부모는 git과 Orca CLI 응답에서만 얻는다. 저장소
판정(`ROOT`, 래퍼, git-crypt 필터)은 위와 같다. PR 모드는 위 "PR 해석"의 fetch·OID 검증을,
모든 모드는 Orca 계보 설정 절의 부모 확정(`REPO_ID`·`PARENT_ID`)을 먼저 끝낸다.

| 저장소 | 생성 | 사용자 확인 |
| --- | --- | --- |
| 래퍼 있음 | 래퍼 본문에 `workmux`·`tmux` 호출이 없음을 읽어 확인한 뒤 `./scripts/create-worktree.sh {브랜치}`만 실행. 출력에서 절대경로를 얻는다 | 없음 |
| 래퍼 없음, git-crypt 없음 | 아래 `orca worktree create` | `post-checkout` 훅이 있거나 아래 이름 검증 게이트에 걸릴 때 |
| 래퍼 없음, git-crypt 있음 | 위 예외와 같이 확인받고 worktree 절대경로를 사용자에게 받은 뒤 `organize-worktree-lineage` §7의 3단계(`--no-checkout` → 링크 → checkout)를 `--detach` 대신 브랜치로 수행한다 | 항상 |

`{브랜치}`는 PR 모드면 head 브랜치명, 브랜치 모드면 입력 브랜치명이다.
`lee-kyu-hwan/208-...`처럼 사용자 접두사가 붙은 이름도 바꾸지 않고 그대로 넘긴다. 그
이름이 보존되는지는 `orca worktree create`의 이름 검증 게이트로 판정한다. 래퍼
경로의 실행 권한·실패 규칙은 위 git-crypt 절과 같고, 래퍼 뒤 `workmux open`만 생략한다.
래퍼 본문에 `workmux`나 `tmux` 호출이 있으면 이 경로의 보장이 깨지므로 실행하지 않고
멈춰 보고한다. git-crypt 수동 경로에서 사용자가 경로를 주지 않으면 추측하지 않고 중단한다.

래퍼도 git-crypt도 없는 저장소는 `orca worktree create`로 만든다. worktree 경로는 Orca가
정하므로 미리 계산하지 않는다. `--base-branch`에 줄 `BASE_REF`와 생성 뒤 기대하는
`HEAD`는 다음과 같다. 기대 `HEAD`는 생성 전에 기록한다.

| 경우 | `BASE_REF` | 기대 `HEAD` |
| --- | --- | --- |
| PR 모드 | `{head브랜치명}` (PR 해석에서 fetch·검증한 로컬 브랜치) | `headRefOid` |
| 브랜치 모드, 로컬 브랜치 있음 | `{브랜치}` | `git -C "$ROOT" rev-parse "refs/heads/{브랜치}"` |
| 브랜치 모드, `origin/{브랜치}`만 있음 | `origin/{브랜치}` | `git -C "$ROOT" rev-parse "refs/remotes/origin/{브랜치}"` |
| 브랜치 모드, 어디에도 없음 | `$DEFAULT_BRANCH` | `git -C "$ROOT" rev-parse "$DEFAULT_BRANCH"` |

```bash
# 브랜치가 어디에도 없을 때만. 실제 기본 브랜치(main·develop 등)를 쓴다
DEFAULT_BRANCH=$(git -C "$ROOT" symbolic-ref --short refs/remotes/origin/HEAD)   # 예: origin/develop

# 부모 옵션은 둘 중 하나만 준다
if [ "$STANDALONE" = 1 ]; then
    "$ORCA" worktree create --repo "id:$REPO_ID" --name "{브랜치}" \
        --base-branch "$BASE_REF" --no-parent --setup skip --json
else
    "$ORCA" worktree create --repo "id:$REPO_ID" --name "{브랜치}" \
        --base-branch "$BASE_REF" --parent-worktree "id:$PARENT_ID" --setup skip --json
fi
```

- `symbolic-ref`가 실패하면 기본 브랜치를 추측하지 말고 중단한다. 현재 체크아웃된
  브랜치를 base로 쓰지 않는다(아래 "계보와 git base는 별개다").
- `REPO_ID`를 확정하지 못했거나, `--standalone`이 아닌데 `PARENT_ID`가 없으면 명령을
  만들지 않고 중단해 보고한다. 부모 없이 만들거나 `--no-parent`로 바꿔 진행하지 않는다.
- `--setup skip`을 명시한다. 저장소 setup 정책(기본값 `inherit`)을 따르지 않는다. 이
  옵션은 setup hook만 생략한다. Orca에 설정된 기본 terminal 명령은 생성과 함께 여는 첫
  terminal에서 그대로 실행될 수 있으므로 `--setup skip`만으로 무해하다고 단정하지 않는다.
  이 스킬은 그 설정을 읽거나 바꾸지 않고, 결과에 "기본 terminal 명령 실행 여부 미확인"으로
  남긴다.
- Orca가 생성과 함께 여는 첫 terminal을 그대로 쓴다. terminal을 더 만들거나 명령을 보내지
  않는다. 에이전트가 자동으로 시작된다고 가정하지 않는다. 모델·계정·권한을 지정하거나
  넓히는 옵션이나 설정을 더하지 않는다. `--role`이 있을 때의 조정자 시작도 이 스킬이 아니라
  `start-orca-orchestrator`가 한다(조정자 시작 연결 절).
- 응답은 `result.worktree` 객체로 읽는다. top-level `result.path`를 가정하지 않는다.
  `result.worktree.id`(전체 `id`)를 `NEW_ID`로 기록하고, 없으면 실패다. 저장소 범위 목록을
  다시 읽어 `id`가 `NEW_ID`인 항목 하나를 찾고 그 항목의 `path`를 `WORKTREE_PATH`로 쓴다.
  다음을 모두 만족해야 성공이다.
  - `NEW_ID`의 `::` 앞부분이 `REPO_ID`와, `::` 뒷부분이 그 항목의 `path`와 같다. 응답에
    `result.worktree.path`가 있으면 그 값도 같아야 한다.
  - 그 항목의 `branch`가 `refs/heads/{브랜치}`와 정확히 같다. Orca가 접두사를 붙이거나
    다른 이름을 만들었으면 실패다.
  - `git -C "$WORKTREE_PATH" rev-parse HEAD`가 위 표의 기대 `HEAD`와 같다.
- **이름 검증 게이트.** `--name`에 준 이름이 그대로 `refs/heads/{브랜치}`가 되는지는 이
  문서에서 확인하지 않았다. 특히 다음 경우는 확인되지 않았다.
  - 이미 있는 브랜치 이름을 줄 때 Orca가 그 브랜치를 그대로 체크아웃하는지
  - `lee-kyu-hwan/208-...`처럼 사용자 접두사(`/`)가 붙은 이름을 줄 때, Orca 저장소
    설정의 git 사용자 이름(`gitUsername`)이 한 번 더 붙거나 다른 이름이 되는지

  둘 중 하나에 해당하면 생성 전에 이 미검증 사실과 기대 브랜치를 보여 주고 확인받는다.
  확인이 없으면 만들지 않는다. 확인받았어도 접두사 브랜치가 보존된다고 가정하지 않고, 위
  `branch`·`HEAD` 검증을 통과해야만 성공으로 본다.
- 명령이 실패하거나 검증이 어긋나면 오류 원문과 만들어진 경로·브랜치를 보고하고
  중단한다. worktree를 되돌리지 않으며 workmux나 `git worktree add`로 다시 시도하지 않는다.

setup·hook을 새로 실행하지 않는다.

- `git worktree add`의 checkout은 저장소의 `post-checkout` 훅을 실행하고,
  `orca worktree create`도 git checkout을 거치므로 같은 훅이 돌 수 있다. 래퍼 없는
  경로에서는 생성 전에 `git -C "$ROOT" rev-parse --git-path hooks/post-checkout`이 가리키는
  파일이 실행 가능한지 보고, 그렇다면 멈추고 확인받는다. 훅을 끄는 설정으로 우회하지
  않는다.
- 래퍼는 저장소가 정한 생성 어댑터다. 래퍼가 하는 일(의존성 설치 등)을 이 스킬이 더하거나
  빼지 않는다.

Orca 전용 경로에서 같은 브랜치의 worktree가 이미 있으면 새로 만들지 않고 재개한다. 존재
판정은 `git -C "$ROOT" worktree list --porcelain`의 경로·브랜치로 하고, 저장소 범위 Orca
목록에서 `path`가 그 경로인 항목의 전체 `id`를 대상으로 삼는다. 창을 열거나 옮기지 않으며
`window-session`을 읽거나 쓰지 않는다. 계보는 Orca 계보 설정 절의 단일 대상 모드 호출로
확인하고 적용한 뒤 경로를 안내한다.

## Orca 계보 설정

workmux는 Orca를 모른다. `workmux add`로 만든 worktree는 git·Orca 목록에는 뜨지만 Orca
계보(parent/child) 밖에 생긴다. 이 스킬은 계보를 직접 `set`하지 않고, 대상 worktree 하나에
`organize-worktree-lineage`의 단일 대상 모드(§12)를 명시 호출한다.

| 경우 | 대상 |
| --- | --- |
| 신규 생성 (workmux·래퍼·git-crypt 수동·`orca worktree create` 모두) | 이번 호출이 만든 worktree |
| 기존 대상 재개 (tmux 경로의 창 처리, Orca 전용 재개) | 같은 브랜치의 기존 worktree |

`orca worktree create`는 생성 명령에서 부모를 이미 지정하지만 그래도 호출한다. 부모가
이미 같으면 단일 대상 모드는 부모를 다시 쓰지 않고 이슈·상태 적용과 재조회 검증만 한다.
재개에서 기존 부모가 이번 부모 확정 결과와 다르면 단일 대상 모드가 변경 계획을 보여 주고
승인받는다. 조용히 덮어쓰지 않는다.

이 스킬은 대상 하나만 다룬다. 다른 역할 worktree를 만들거나 다른 worktree의 부모를 바꾸지
않는다. 여러 worktree를 한 번에 편성할 때는 `organize-worktree-lineage` 일괄 모드를 쓴다.
명시 역할이 있을 때 계보 검증 뒤 `start-orca-orchestrator`(#209)를 부르는 규칙은 아래
"조정자 시작 연결"에 있다. 이 스킬은 그 스킬의 본문을 대신 수행하지 않는다.

### 저장소 범위 목록의 전체 `id`로만 지정한다

부모 후보와 대상 worktree는 `REPO_ID`로 좁힌 목록(`worktree list --repo "id:$REPO_ID"`)에서
찾아 전체 `id`(`<repoId>::<절대경로>`)로 기록한다. 부모를 지정하는 옵션(`--parent-worktree`)과
그 대상(`--worktree`)에는 그 값을 `id:<전체 id>`로 쓰고, `path:<절대경로>`는 같은 목록에서
그 `id`의 `path`로 대조한 값일 때만 쓴다. 사후 확인도 같은 목록에서 전체 `id`로 대조한다.

| 셀렉터 | 부모 지정에 쓰지 않는 이유 |
| --- | --- |
| `issue:<번호>` · `name:` · `branch:` | 셀렉터에 저장소 범위가 없다. 이 저장소의 worktree로 해석됐는지 셀렉터만으로는 보장되지 않으므로 전체 `id`로 확정한다(#176). `review` 같은 이름은 저장소마다 같다 |
| `active` · `current` | 셸 cwd로 해석된다. 새 worktree로 `cd`한 뒤에는 새 worktree 자신을 가리킨다 |

### 부모 확정 (경로 선택 뒤, 영속 명령 전)

cwd를 바꾸기 전에 한 번만 한다. 여기서 확정하지 못한 부모를 생성 뒤에 다시 추측하지
않는다.

1. **저장소 범위.** 메인 worktree 경로를 git에서 얻고, Orca 전체 목록에서 `path`가 그와
   정확히 같은 항목 하나의 `id`에서 `::` 앞부분을 `REPO_ID`로 쓴다. 이후 조회는 저장소
   범위 목록만 쓴다.

   ```bash
   MAIN=$(git -C "$ROOT" worktree list --porcelain | sed -n '1s/^worktree //p')
   "$ORCA" worktree list --json                          # path == $MAIN 인 항목 → REPO_ID
   "$ORCA" worktree list --repo "id:$REPO_ID" --json     # REPO_WORKTREES
   ```

   일치 항목이 0개 또는 2개 이상이면 저장소 범위를 확정하지 못한 것이다.
2. **호출자.** `"$ORCA" worktree current --json`을 이 단계에서 한 번만 읽어 `id`와 `path`를
   `CALLER_ID`·`CALLER_PATH`로 기록한다. `CALLER_PATH`가 `ROOT`와 같고 `CALLER_ID`가
   `REPO_WORKTREES`에 있어야 한다. 다르면 cwd가 바뀌었거나 다른 저장소·폴더 컨텍스트다.
   두 값을 보고한다.
3. **부모.** 위에서부터 먼저 맞는 것을 따른다. 명시 플래그가 PR 작성자 판정보다 우선한다.

| 조건 | 부모 후보 (`REPO_WORKTREES`에서만) | 설정 옵션 |
| --- | --- | --- |
| `--standalone` | 없음. main 밑이 아니라 main과 형제 | `--no-parent` |
| `--epic {이슈번호}` | `linkedIssue`가 그 번호인 worktree | `--parent-worktree "id:$PARENT_ID"` |
| PR 모드, 작성자가 내가 아님 | `review` 역할 worktree | `--parent-worktree "id:$PARENT_ID"` |
| 그 외 (브랜치 모드, 내 PR, `review` 역할 0개) | 호출자 (`PARENT_ID=$CALLER_ID`) | `--parent-worktree "id:$PARENT_ID"` |

`--no-parent`와 `--parent-worktree`는 서로 배타적이다. 한 명령에는 표의 행이 정한 하나만
넣고 둘을 함께 주지 않는다.

`review` 역할 worktree는 `displayName`이 `review`이고 `parentWorktreeId`가 메인 worktree의
`id`인 항목이다(`organize-worktree-lineage` §7이 만드는 형태). 저장소 범위 목록 안에서만
찾으므로 다른 저장소의 `review`와 섞이지 않는다. 0개면 새로 만들지 않고 호출자 밑에 둔 뒤
그 사실을 보고한다.

후보를 정한 뒤 `PARENT_ID`(전체 `id`)와 `PARENT_PATH`를 기록한다. 실패 처리는 다음과 같다.
어느 경우에도 다른 셀렉터로 바꿔 다시 시도하지 않는다.

| 상황 | 처리 |
| --- | --- |
| `--epic`·`review` 후보가 2개 이상 | worktree를 만들지 않고 후보의 전체 `id`를 모두 보고한다. 하나를 고르지 않는다 |
| `--epic` 후보가 0개 | worktree를 만들지 않고 보고한 뒤 확인받는다 |
| `--epic`·`review`인데 저장소 범위 미확정 | worktree를 만들지 않고 보고한다 |
| 호출자 부모인데 저장소 범위 미확정, 또는 `worktree current` 실패 | Orca에 등록되지 않은 저장소 등이다. 계보 없이 진행하고 결과에 알린다. 단 `orca worktree create`로 만들 경로(Orca 전용, 래퍼·git-crypt 없음)는 `REPO_ID`가 필요하므로 만들지 않고 보고한다 |
| 호출자 확인(2)이 어긋남 | worktree를 만들지 않고 `ROOT`·`CALLER_PATH`·`CALLER_ID`를 보고한다 |
| `--role`인데 저장소 범위 미확정, 또는 `worktree current` 실패 | 위 "계보 없이 진행"을 적용하지 않는다. 조정자 시작은 계보 검증이 전제이므로 worktree를 만들지 않고 보고한다 |

### 이슈·PR 참조 해석 (부모 확정과 함께, 영속 명령 전)

단일 대상 모드에 넘길 `ISSUE_REFS`와 `PR_REFS`를 부모 확정과 같은 시점에 정한다. 여기서
정하지 못한 번호를 생성 뒤에 다시 추측하지 않는다. 브랜치명은 바꾸지 않는다. 접두사를 떼는
것은 번호를 읽을 때뿐이고 `--name`·`BASE_REF`·검증의 `refs/heads/{브랜치}`에는 입력 그대로의
이름을 쓴다. 기본 브랜치(`main`·`develop`) 판정, `--standalone`, 래퍼·git-crypt 생성 경로는
이 해석과 무관하게 위 절을 그대로 따른다.

`PR_REFS`는 PR 모드면 PR 해석에서 확정한 번호 하나, 브랜치 모드면 비어 있다.

`ISSUE_REFS`는 명시 입력을 우선한다.

1. **명시 이슈.** `--issue` 또는 표지가 있는 자연어로 받은 번호.
2. **브랜치 번호.** 대상 브랜치명(PR 모드는 head 브랜치명, `refs/heads/`를 뗀 값)에 아래
   표를 적용한다. 명시 이슈가 있어도 대조하려고 계산한다.
3. 둘 다 없으면 `없음`이다.

| 브랜치명 형태 | 브랜치 번호 |
| --- | --- |
| `208-feat/x`처럼 맨 앞이 `^[0-9]+-` | 그 숫자 |
| `<gitUsername>/208-x`처럼 맨 앞이 저장소에서 확인한 `gitUsername`과 `/`이고, 그 한 접두사를 뗀 나머지가 `^[0-9]+-` | 그 숫자 |
| `feat/392-add-x`, `other-user/208-x`처럼 첫 `/` 앞이 `gitUsername`이 아님 | 없음. 임의의 `/` 앞부분은 떼지 않는다 |
| `<gitUsername>/feat/208-x`처럼 접두사 뒤가 `^[0-9]+-`가 아님 | 없음 |
| `<gitUsername>/<gitUsername>/208-x`처럼 접두사가 겹침 | 모호. 아래 표대로 멈춘다 |
| `main`·`develop`, `ZF-123-x`, 그 외 숫자로 시작하지 않는 이름 | 없음. `ZF-숫자`는 창 이름 전용이며 GitHub 이슈 번호가 아니다 |

`gitUsername`은 Orca 저장소 설정의 git 사용자 이름이다(이름 검증 게이트와 같은 값). 이
저장소(`REPO_ID`)에 대한 Orca 조회 응답에서 관측한 값만 쓴다. git `user.name`, GitHub
로그인(`gh api user`), 셸 사용자명, 브랜치의 첫 `/` 앞부분으로 대신하지 않는다. 설치된 Orca
1.4.209에서는 읽기 전용 `"$ORCA" repo show --repo "id:$REPO_ID" --json` 응답의
`result.repo.gitUsername`에 이 값이 있음을 관측했다. 이 명령·필드로만 읽는다. 다른 호스트·버전의
응답에 그 필드가 없거나, 관측하지 못했거나 비었거나 `/`를 포함하면 접두사 행을 적용하지
않고 브랜치 번호를 `없음`으로 둔 뒤, 결과에 "`gitUsername` 미관측으로 접두사 해석 안 함"을
적는다. 접두사 비교는 대소문자를 구분하는
전체 문자열 일치다.

다음이면 영속 명령 전에 멈춘다. 하나를 고르거나 다른 출처로 바꿔 다시 시도하지 않는다.

| 상황 | 처리 |
| --- | --- |
| 명시 이슈가 둘 이상(`--issue` 반복, 자연어의 여러 번호) | 모두 보여 주고 확인받는다 |
| 명시 이슈와 브랜치 번호가 모두 있고 다름 | 두 값과 출처를 보여 주고 확인받는다 |
| 접두사가 겹침 | 보고한다. Orca가 `gitUsername`을 한 번 더 붙인 증상일 수 있다(이름 검증 게이트) |
| PR 모드 재개에서 대상의 `linkedPR`이 있고 PR 번호와 다름 | 두 값을 보고한다 |
| `--role epic_orchestrator`인데 `ISSUE_REFS`가 정확히 하나가 아님 | 에픽 번호를 확인받는다. 브랜치·`linkedIssue`에서 고르지 않는다 |

PR 모드의 PR 번호와 head 브랜치 번호는 종류가 달라 충돌이 아니다. 재개 대상의
`linkedIssue`가 `ISSUE_REFS`와 다르면 여기서 멈추지 않고 단일 대상 모드가 계획을 보여 주고
승인받는다. 결과에는 `ISSUE_REFS`와 그 출처(`explicit`·`branch-leading`·
`branch-gitUsername-prefix`·`none`)를 적는다.

### PR 모드는 보드 상태도 함께 설정한다

PR 리뷰용 worktree는 계보와 별개로 보드 상태를 `in-review`로 둔다. 계보는 "무엇에 속하나",
상태는 "어느 단계인가"를 답하는 별개 축이다. 작성자·경로와 무관하게 같다. 이 값은 단일
대상 모드의 보드 상태 입력으로 넘긴다.

남이 작성한 PR은 내 에픽에 속하지 않으므로 기본값이 `review` 역할 worktree다. 내가
작성자인 PR은 `review`로 옮기지 않고 브랜치 모드와 같은 부모에 두며 상태만 바꾼다.

브랜치 모드에서는 상태를 바꾸지 않는다. 기본값 그대로 둔다.

`--standalone`은 에픽 조정자 worktree처럼 새 뿌리를 만들 때 쓴다. 하위 작업이
`--epic {이슈번호}`로 이 worktree를 찾으려면 이슈가 연결돼 있어야 한다. 생성 뒤
`linkedIssue`가 비어 있으면 그 사실을 결과에 알린다.

### 표시 이름은 정하지 않는다

이 스킬은 `displayName`을 만들거나 에픽 제목을 요약하지 않는다. 에픽 표시 이름의 정본은
`organize-worktree-lineage` §13이다. 사용자가 `--role epic_orchestrator`(자연어로는 에픽
조정자)를 명시했을 때만 단일 대상 모드에 역할 `epic`과 에픽 번호(`ISSUE_REFS`의 번호 하나)를
넘긴다. `repo_orchestrator`는 단일 대상 모드의 역할로 넘기지 않는다. 역할을 추측하지 않는다.
단일 대상 모드 결과의
`displayName`·`displayNameSource`·`epicTitle`·`namingDecision`은 이 이름과 값 그대로
보고한다.

### 실행

`orca`는 PATH 심링크 권한 결함이 있어 절대경로로 부른다(#140). PATH의 `orca`로
폴백하지 않는다.

1. **대상 확정.** 저장소 범위 목록을 다시 읽어 대상 항목의 전체 `id`를 `NEW_ID`로 기록한다.
   `orca worktree create`로 만들었으면 응답의 `result.worktree.id`이고 목록과 대조를 이미
   마쳤다(Orca 전용 생성 절). 그 외에는 `path`가 `$WORKTREE_PATH`인 항목이다.
2. **단일 대상 모드 호출.** 다음 입력을 모두 명시해 `organize-worktree-lineage` §12를
   실행한다. 이 스킬이 `worktree set`을 따로 부르지 않는다.

   | 입력 | 값 |
   | --- | --- |
   | 저장소 | `REPO_ID` |
   | 대상 | `NEW_ID` |
   | 부모 | `PARENT_ID`(전체 `id`). `--standalone`이면 `no-parent` |
   | 이슈·PR 참조 | 이슈·PR 참조 해석 절의 `ISSUE_REFS`와 `PR_REFS`. 비었으면 `없음` |
   | git base 확인 근거 | 대상 브랜치, `git -C "$WORKTREE_PATH" rev-parse HEAD`, 신규 생성이면 기대 `HEAD`(PR 모드는 `headRefOid`)와의 일치 여부, 재개면 "기존 브랜치 그대로, base 변경 없음" |
   | 역할·에픽 | 표시 이름 절을 따른다 |
   | 보드 상태 | PR 모드면 `in-review`. 브랜치 모드는 주지 않는다 |

3. **결과 검증.** 단일 대상 모드의 보고만으로 끝내지 않는다. 이 스킬이 저장소 범위 목록을
   다시 읽어 `NEW_ID` 항목의 `parentWorktreeId`가 `PARENT_ID`와 같은지(`--standalone`이면
   비어 있는지), PR 모드면 `workspaceStatus`가 `in-review`인지 확인한다. 다르면 성공으로
   보고하지 않는다.

```bash
ORCA=/Applications/Orca.app/Contents/Resources/bin/orca
if [ -x "$ORCA" ]; then
    "$ORCA" worktree list --repo "id:$REPO_ID" --json    # 1. 대상 확정 → NEW_ID
    # 2. organize-worktree-lineage 단일 대상 모드(§12)가 NEW_ID 하나에만 set한다
    "$ORCA" worktree list --repo "id:$REPO_ID" --json    # 3. 결과 검증
fi
```

`$WORKTREE_PATH`는 대상의 절대경로다. tmux 경로는 `workmux list --json`, 래퍼는 그 출력,
`orca worktree create`는 `result.worktree.id`로 찾은 저장소 범위 목록 항목의 `path`,
git-crypt 수동 경로는 사용자가 준 경로, 재개는 `git worktree list --porcelain`의 기존
경로다. `$PARENT_ID`는 부모 확정에서 기록한 전체 `id`다. 호출자 부모면 `$CALLER_ID`다.

- `[ -x ]`가 거짓이면 Orca가 없는 머신이다. 계보 설정을 건너뛰고 결과에 그 사실을
  기록한다. 실패로 보고하지 않는다. tmux 경로의 동작은 이전과 같다.
- 부모 확정에서 "계보 없이 진행"으로 정했으면(`REPO_ID` 없음) 이 블록 전체를 건너뛴다.
- 대상 확정에서 `path`가 `$WORKTREE_PATH`인 항목이 없으면 외부 worktree 표시
  설정(`externalWorktreeVisibility`) 때문일 수 있다. 단일 대상 모드를 부르지 않고 보고한다.
- 단일 대상 모드가 멈추거나 승인받지 못하면 그 보고를 그대로 전하고, 다른 셀렉터나 직접
  `set`으로 다시 시도하지 않는다. 자기 자신이나 사라진 부모에 붙이는 경우도 그 모드가
  멈춘다.
- 생성 뒤 계보 적용이 실패해도 worktree를 되돌리지 않는다. 오류 원문을 보고한다.
- 결과 보고에 `REPO_ID`, 부모 결정 근거(표의 행), `PARENT_ID`, 확인한
  `parentWorktreeId`(또는 건너뛴 이유), `ISSUE_REFS`와 그 출처, `PR_REFS`, 신규 생성인지
  재개인지, 단일 대상 모드 결과의 네 표시 이름 필드를 포함한다.

### 조정자 시작 연결 (#209)

사용자가 `--role`(또는 자연어로 역할)을 명시했을 때만 이 절을 쓴다. 역할이 없으면
`start-orca-orchestrator`를 부르지 않고 결과에 "조정자 시작: 호출 안 함(명시 역할 없음)"이라고
적는다. 스킬 이름을 안내하거나 다음 할 일로 적는 것은 호출이 아니다. 역할이 명시됐는데
호출하지 않았거나 호출 출력이 없으면 이 스킬의 결과를 성공으로 보고하지 않는다.
`start-orca-orchestrator`의 본문은 이 스킬이 정하지 않는다. 이 절은 호출 조건, 넘기는 계약,
출력을 받는 규칙만 정한다.

**호출 조건.** 다음을 모두 만족할 때 한 번만 호출한다. 하나라도 어긋나면 호출하지 않고
이유를 보고한다.

- 실행 3의 재조회 검증을 통과했다. 신규 생성과 같은 브랜치 재개에 똑같이 적용한다.
- 대상은 그 검증을 통과한 `NEW_ID` 하나다. 다른 worktree나 호출자를 대상으로 바꾸지 않는다.
- `--role epic_orchestrator`면 `ISSUE_REFS`가 정확히 하나이고 에픽 저장소 `{owner}/{repo}`를
  PR 해석과 같은 방법(`gh repo view`, 실패하면 `origin` URL)으로 확정했다.

**입력 계약 (`schema_version: 1`).** 값은 이번 호출에서 실제로 읽은 git·Orca 응답과 사용자
입력에서만 채운다.

| 필드 | 값 |
| --- | --- |
| `schema_version` | `1` |
| `mode` | 필수. 이번 호출이 대상을 새로 만들었으면 `start`, 같은 브랜치의 기존 worktree를 재개했으면 `resume`. 결과 보고의 신규 생성·재개 구분과 같아야 한다 |
| `repository` | `{id: REPO_ID, path: MAIN}` |
| `target.worktree_id` · `target.path` | `NEW_ID` · 실행 3 재조회 항목의 `path` |
| `target.explicit_role` | 사용자가 명시한 `repo_orchestrator` 또는 `epic_orchestrator` |
| `target.epic` | `epic_orchestrator`면 `{issue: ISSUE_REFS의 번호, repo: "{owner}/{repo}"}`, `repo_orchestrator`면 `null` |
| `target.scope[]` | 사용자가 이번 호출에서 준 범위 그대로. 없으면 `[]` |
| `caller.worktree_id` | `CALLER_ID`(부모 확정 2에서 읽은 값) |
| `caller.role` | 사용자가 호출자 역할을 명시했으면 그 값, 아니면 `null` |
| `caller.existing_coordinator` | 호출 직전 Orca 조회에서 호출자 쪽 조정자 terminal을 관측했으면 `{handle, session_id}`, 아니면 `null` |
| `lineage.parent_worktree_id` | 재조회한 `parentWorktreeId`. `--standalone`이면 `null` |
| `lineage.parent_choice` | 계약 enum `explicit_parent`·`no_parent`만. 부모 확정 표의 `--standalone` 행이면 `no_parent`, 나머지 행(`--epic`·남의 PR·그 외)이면 `explicit_parent`. 적용한 행(`standalone`·`epic`·`review`·`caller`)은 부모 선택 사유이므로 이 필드에 넣지 않고 `safety.guards[]`의 부모 확정 항목과 결과 보고의 부모 결정 근거에 남긴다 |
| `lineage.issue_refs[]` · `lineage.pr_refs[]` | `ISSUE_REFS` · `PR_REFS` |
| `lineage.git_base` | `{ref: BASE_REF(재개면 대상 브랜치), commit: git -C "$WORKTREE_PATH" rev-parse HEAD, evidence: 실행 2에 넘긴 git base 확인 근거}` |
| `naming` | 단일 대상 모드 결과의 `displayName`·`displayNameSource`·`epicTitle`·`namingDecision`을 이름·값 그대로 |
| `existing_session` | 호출 직전 Orca 조회에서 대상 worktree의 에이전트 세션을 관측했으면 `{handle, provider, account_profile, session_id, model_effort_source, observed_at}`, 아니면 `null` |
| `handoff.children[]` | 실행 3 재조회 목록에서 `parentWorktreeId`가 `NEW_ID`인 항목마다 객체 `{worktree_id, path, branch, dirty, writer, profile, session_id, owned_files, progress}` 하나. 필드별 출처는 표 아래 목록을 따른다 |
| `handoff.next_actions[]` · `dependencies[]` · `cross_epic_conflicts[]` · `evidence_paths[]` | 사용자가 이번 호출에서 준 값만. 없으면 `[]` |
| `authorization` | 사용자가 이번 호출에서 준 `allowed_actions[]`·`remote_write`·`forbidden_paths[]`를 그대로 보존한다. 주지 않았으면 `allowed_actions: []`·`forbidden_paths: []`이고, 원격 쓰기를 명시 허용받지 않았으면 `remote_write: "forbidden"`이다. 금지를 불리언 `false`로 쓰지 않는다. 이 스킬이 값을 더하거나 넓히지 않는다 |
| `safety.guards[]` | 이번 호출이 실제로 통과한 검사(예: 재조회 검증, 명시 역할, 단일 대상) |
| `safety.unverified[]` | 관측하지 못한 값과 사유 |
| `runtime_ids[]` | `{kind, id, source}`. `kind`는 `run`·`task`·`dispatch`만이다. 실행 컨텍스트가 실제로 발급한 ID와 그 값을 읽은 출처만 넣는다. worktree ID는 `target.worktree_id`에 있으므로 넣지 않는다 |

- 관측하지 못한 값은 위처럼 `null`이나 `[]`로 두고 사유를 `safety.unverified`에 적는다. 객체의
  일부 필드만 관측했으면 그 필드만 `null`이다. 별도 `unknowns` 입력 필드를 만들거나 사용자에게
  요구하지 않는다. `next_actions` 같은 사용자 인계 필드의 `[]`는 "전달받은 것 없음"이지 없음을
  확인했다는 뜻이 아니다. `handoff.children`의 `[]`는 재조회에서 자식 항목을 관측하지 못했다는
  뜻이다.
- `mode: resume`은 기존 세션을 이어받는다. 이어받을 기존 세션의 정확한 `session_id`와
  `account_profile`(계정·프로필)이 없거나 관측하지 못했으면 값을 만들어 넣거나 다른 세션·기본
  프로필로 채우지 않고, `mode`를 `start`로 바꾸지도 않는다. `resume` 그대로 `existing_session`
  (또는 그 필드)을 `null`로 두고 사유를 `safety.unverified`에 적어 넘긴다. `unverifiable`·
  `blocked` 판정은 #209가 한다.
- `handoff.children[]` 각 객체는 다음 출처로만 채운다. 결과 보고에 필드별 출처를 적는다. 모르면
  `null`로 두고 `safety.unverified`에 `<자식 worktree_id>의 <필드>: 사유`를 적는다. 브랜치명·
  표시 이름·이슈·디렉터리 이름에서 다른 사람이나 다른 writer의 작업을 추론하지 않는다.
  - `worktree_id`·`path`·`branch`: 저장소 범위 Orca 목록(실행 3 재조회)의 `id`·`path`·`branch`.
    `branch`는 `git -C "$ROOT" worktree list --porcelain`의 같은 경로 항목과 대조해 다르면 `null`
  - `dirty`: `git --no-optional-locks -C "<자식 path>" status --porcelain`이 성공하면 출력이
    비었는지로 `false`·`true`. 실패하면 `null`
  - `profile`·`session_id`: 호출 직전 Orca terminal 조회에서 그 자식 worktree의 terminal로 관측한
    값만. 필드 위치 미확인은 아래 조정자·세션 값과 같다
  - `writer`·`owned_files`·`progress`: 사용자가 이번 호출에서 인계한 값만
- 조정자·세션 값은 호출 직전 Orca terminal 조회(`"$ORCA" terminal list --json`)에서 읽는다.
  handle은 재생성되면 바뀌므로 저장해 둔 값을 쓰지 않는다. `observed_at`은 그 조회 시각이다.
  provider·계정 프로필·session id를 담는 응답 필드는 이 문서에서 확인하지 않았으므로,
  응답에 없으면 추정하지 않고 `null`로 둔다.
- Run·Task·Dispatch ID, session id, handle을 만들거나 예시 값을 넣지 않는다. 발급받지 않았거나
  관측하지 못한 Run·Task·Dispatch ID는 `runtime_ids`에서 뺀다.

**호출.** `start-orca-orchestrator` 스킬을 위 계약 하나로 명시 호출한다. 이 스킬이 조정자
terminal을 만들거나, 에이전트를 띄우거나, terminal에 입력을 보내지 않는다. 그 스킬을
인라인으로 베껴 수행하지 않는다.

**출력 처리.** #209의 `status`(`started`·`resumed`·`already_active`·`blocked`·`unverifiable`)를
원문 그대로 전한다. 다른 값으로 바꾸거나 합치지 않는다.

| `status` | 처리 |
| --- | --- |
| `started`·`resumed` | 아래 네 단계 관측과 policy ACK 대조를 모두 통과할 때만 성공으로 보고한다 |
| `already_active` | 기존 세션을 그대로 보고한다. 계약·프롬프트·정책을 다시 주입하지 않고 #209를 다시 부르지 않는다 |
| `blocked`·`unverifiable` | 사유 원문을 전한다. 입력을 바꾸거나 다른 경로로 다시 시도하지 않는다 |

- 네 단계는 `ready`·`input_accepted`·`turn_started`·`policy_ack`다. #209 출력에서 각 단계의
  관측 근거를 확인한다. 하나라도 관측되지 않았으면 `status`가 `started`·`resumed`여도 성공으로
  쓰지 않고, `status` 원문과 관측되지 않은 단계를 함께 보고한다.
- policy ACK의 첫 3행은 이번 호출의 실제 정책 digest, 실제 인계 digest, 전체
  `target.worktree_id`(`NEW_ID`)와 각각 일치해야 한다. 기대값은 #209가 적용한 정책과 이
  스킬이 넘긴 계약에서 얻으며 ACK 본문에서 거꾸로 가져오지 않는다. 축약 ID나 경로만 맞는
  것은 일치가 아니다. 어긋나면 `policy_ack`를 관측하지 못한 것으로 본다.
- 어느 결과든 worktree와 계보는 되돌리지 않는다.
- 결과 보고에 호출 여부(안 했으면 이유), `status` 원문, 네 단계 관측 결과, ACK 대조 결과,
  계약의 `safety.unverified`를 포함한다.

### 계보와 git base는 별개다

계보는 Orca에서 worktree를 보기 좋게 묶는 용도일 뿐 코드 흐름과 무관하다. Orca 가이드도
*"`--no-parent` only controls Orca lineage; it does not choose the Git base."*라고
경고한다. `--epic`으로 에픽 worktree 밑에 붙여도 git base는 에픽 브랜치가 아니라
workmux의 base 규칙을 따른다. 그래서 에픽 밑 하위 작업도 각자 독립적으로 PR을 낼 수
있다.

- 이 dotfiles의 workmux 설정은 `base_branch: auto`라서 원격 기본 브랜치(예:
  `origin/main`)에서 갈라진다.
- `base_branch` 설정이 없으면 workmux는 현재 체크아웃된 브랜치를 base로 쓴다. 에픽이나
  feature worktree 안에서 실행하면 계보와 무관하게 stacked branch가 되므로
  `--base {기본브랜치}`를 명시해 현재 브랜치가 base로 잡히는 것을 막는다.
- Orca 전용 경로의 `orca worktree create`는 신규 브랜치에
  `--base-branch`로 `origin/HEAD`가 가리키는 실제 기본 브랜치를 명시한다.
  `base_branch: auto`와 같은 결과다.
- 계보에 맞추려고 `--base`를 바꾸거나 base에 맞추려고 계보를 바꾸지 않는다. stacked
  branch는 사용자가 명시적으로 요청할 때만 만든다.
- 계보 부모는 브랜치명에서 해석한 이슈 번호로 정하지 않는다. `lee-kyu-hwan/208-...`처럼
  사용자 접두사가 붙은 브랜치도 부모 확정 결과는 같다.

계정 프로필(`claude`/`claude-profile1`)은 이 스킬이 고르지 않는다. 에이전트를 자동
실행하지 않으므로 필요 없고, 그 선택은 에이전트를 띄우는 `orca-worktree` 스킬(#141)의
몫이다. `--role`로 `start-orca-orchestrator`를 부를 때도 프로필을 정하지 않고, Orca에서
관측한 값만 계약의 `existing_session.account_profile`로 옮긴다.

## 기존 worktree 처리

이 절은 tmux 경로의 기존 worktree 처리다. Orca 전용 경로의 재개는 "Orca 전용 생성" 절
끝을 따른다.

세션 선택보다 먼저 `git worktree list --porcelain`과 `workmux list --json`으로 브랜치의
기존 worktree 경로·handle을 확인한다. 같은 브랜치가 이미 있으면 새로 만들지 않고 그
경로를 안내한다. 존재 판정은 `git worktree list --porcelain`으로 한다. `workmux list --json`이
실패하면 handle만 비워 둔다. 창 처리가 끝나면 Orca를 쓸 수 있을 때 단일 대상 모드로
계보를 확인한다(Orca 계보 설정 절).

기존 창은 이번 호출에서 파생한 이름으로 찾지 않는다. 다음 순서로 탐지한다.

1. `workmux list --json`의 handle 항목에서 `is_open`을 확인한다. 이 값은 단서이며 최종
   판정이 아니다(아래 참조).
2. `workmux.worktree.{handle}.window-session` 저장값으로 세션 후보를 좁힌다.
3. `workmux.worktree.{handle}.target-window` 저장값으로 창 후보를 좁힌다. 저장값은 실제
   창 이름의 접미사다. `nerdfont` 설정에 따라 글리프와 공백이 앞에 붙을 수 있으므로
   동등 비교가 아니라 접미사 비교로 판정한다.
4. pane 현재 경로를 worktree 절대경로와 교차 확인한다.

```bash
tmux list-panes -a -F '#{session_name}:#{window_index} #{window_id} #{pane_id} #{pane_current_path}' \
  | awk -v wt="{worktree절대경로}" '$4 == wt || index($4, wt"/") == 1'
```

동일 `window_id`의 여러 pane은 하나의 창으로 중복 제거한다. 이후 조작은 바뀌지 않는
`window_id`와 `pane_id`를 기준으로 하며, 변하는 `session:index`를 기준으로 하지 않는다.
경로에 공백이 있으면 위 매칭은 신뢰할 수 없고 pane cwd는 사용자가 `cd`로 바꿀 수 있다.

`window-session` 또는 `target-window`가 없으면 그 단서만 제외하고 나머지와 pane 경로로
진행한다. 둘 다 없어도 pane 매칭이 정확히 하나면 사용하되 결과에 기록한다.

저장값과 pane 실측이 다르면 실측을 신뢰하고 차이를 보고한다. 단, `target-window` 앞의
글리프·공백 접두사 때문에 생기는 차이는 "저장값과 실측이 다르다"에 해당하지 않는다. 그
보고는 저장 세션이나 창 자체가 어긋났을 때만 한다. `is_open` 값과 무관하게 서로 다른
`window_id`가 둘 이상이면 추측하지 않는다. `is_open`인데 pane 매칭이 없을 때도 같다.
저장된 세션·창 이름 후보를 보여 주고 확인받으며, 실제 위치를 확정하지 못했으면
`window-session`을 갱신하지 않는다.

`is_open`도 단서다. workmux는 토큰·저장 이름·세션 같은 메타데이터로 창을 식별해
`is_open`을 정하므로, 그 식별이 어긋나면 살아 있는 창도 거짓이 될 수 있다. pane이 다른
handle의 창에 얹혀 있거나, `break-pane`으로 만든 창처럼 추가 단서까지 맞지 않는 경우가
그렇다. `is_open`이 거짓이라도 신뢰할 수 있는 pane 매칭이 정확히 하나면 창이 열려 있다고
본다. 이때 메타데이터는 실측과 어긋난 것이므로 그 사실과 실측 위치를 보고한다.
메타데이터를 고치지 않는다. 얹힘 상태에서는 `window-session`도 갱신하지 않는다. 이
스킬은 `window-token`과 `target-window`를 쓰지 않으며(워크트리 식별자 절), 다른 handle의
창에 얹힌 pane에 그 창의 토큰을 맞추면 두 handle이 같은 창을 가리키게 된다. 매칭된
pane이 다른 handle의 창에 얹혀 있으면 그 창은 이 worktree의 창이 아니다. 기존 위치
안내나 이동 같은 창 단위 조작 전에 독립 창으로 분리할지 확인받고, 아래 분기표의 이동
행을 그대로 적용하지 않는다. 창이 닫혀 있다는 확정은 매칭을 신뢰할 수 있는 상태에서
pane이 0건일 때만 한다. 경로에 공백이 있거나 pane cwd가 바뀐 것으로 의심되면 판정 불가로
두고 저장된 세션·창 후보를 제시해 확인받는다.

- 창이 닫혀 있으면(`is_open`이 거짓이고, 신뢰할 수 있는 매칭에서 pane이 0건이면) 선택
  세션으로 연다.
- 창이 열려 있고 실제 세션이 선택 세션과 같으면 중복 창을 만들지 않고 기존 위치를
  안내한다.
- 창이 열려 있고 사용자가 세션을 명시하지 않았으면 다른 세션에 있어도 옮기지 않는다.
  레거시·사라진 저장값을 고치는 경우에는 실제 세션을 기록한다.
- 창이 열려 있고 사용자가 다른 세션을 명시했으면 `workmux open`으로 재구성하지 말고
  `move-window-to-session` 스킬로 이동한다.

이동 직전 `window_id`에서 현재 위치를 다시 해석해 `세션:번호` 형태로 얻고, 반드시
`move-window-to-session` 스킬을 호출한다. 그 스킬에 넘기는 인자는 `<세션:번호>`와
`<대상세션>` 두 개뿐이다. handle과 worktree 경로는 인자가 아니라 이후 확인에 쓰는 참고
값이다. 그 스킬을 인라인으로 베껴 수행하지 않는다. 그 스킬만이 agent state 동기화와
resurrect 즉시 저장을 수행하므로 이를 건너뛰면 재부팅 후 이동이 사라지거나 dashboard가
옛 세션을 가리킬 수 있다. 이동 후에도 같은 `window_id`로 위치를 확인한다. 그 스킬은
`workmux list`의 PATH basename에서 이름을 파생하므로, 기본 명명이 아니면 handle과
어긋날 수 있다. 이동이 끝나면
`workmux.worktree.{handle}.window-session`을 읽는다.

- 대상 세션과 같으면 정상이다.
- 다르면 그 스킬이 basename 키에 쓴 것이다. handle 키를 직접 대상 세션으로 갱신하고
  그 사실을 보고한다. 갱신도 실패하면 중단한다.

## 사후 검증

tmux 경로에서는 실제 창 이름과 세션을 다음으로 확인한다. `workmux list`에는 창 이름 열이 없으므로
추측해서 안내하지 않는다.

```bash
tmux list-windows -a -F '#{session_name}:#{window_index}\t#{window_name}'
```

실제 창 위치를 확인한 뒤의 처리는 이번 호출이 무엇을 했는지에 따라 다르다.

- **창을 새로 만들거나 열었으면**: 실제 세션이 선택 세션과 다르면 잘못 만들어진
  세션과 git config를 함께 정리한다.
- **창을 옮겼으면**: 최종 위치가 선택 세션과 다르면 이동이 완결되지 않은 것이다.
  그 사실을 보고하고, config에 잘못된 값을 쓰지 않는다.
- **창을 옮기지 않았으면**: 실제 세션이 선택 세션과 다른 것이 정상이다. 정리하지
  않는다. 이때의 `window-session` 갱신은 "세션 선택"의 갱신 대상 표가 관장한다.

결과에는 worktree 경로, handle, 브랜치, 실제 세션, 실제 창 이름을 보고한다. PR 모드는
PR 번호와 head OID도 포함한다. Orca를 썼으면 Orca 계보 설정 절의 결과와 조정자 시작 연결
결과도 함께 보고한다.

Orca 전용으로 진행했으면 위 tmux 조회를 하지 않는다. 대신 다음을 확인한다.

- `git -C "$ROOT" worktree list --porcelain`에 `$WORKTREE_PATH`와 브랜치가 있다.
- PR 모드면 `git -C "$WORKTREE_PATH" rev-parse HEAD`가 `headRefOid`와 같다.
- Orca 계보 설정 절의 결과 검증을 통과했다(부모 `id`, PR 모드의 `in-review`).

결과에는 세션을 "없음(Orca 전용)"과 그렇게 정한 이유(세션 명시 없음, Orca 사용 가능)로
적는다. 신규 생성인지 재개인지, worktree 경로, 브랜치, `NEW_ID`, 부모 결과, 단일 대상
모드의 네 표시 이름 필드, 조정자 시작 연결 결과를 보고한다. `orca worktree create`로
만들었으면 기본 terminal 명령 실행 여부 미확인도 적는다. 창을 만들지 않았으므로 창 이름과 handle은 보고하지 않는다.

## 주의사항

- 에이전트(Claude·Codex)를 포함해 어떤 프로그램도 이 스킬이 직접 자동 실행하지 않는다.
  예외는 명시 역할로 `start-orca-orchestrator`에 조정자 시작을 맡기는 것 하나다. 레이아웃의
  세 pane은 모두 빈 셸이므로 필요할 때 사용자가 직접 시작한다.
- 개발 서버는 별도 윈도우나 pane에서 실행한다. worktree마다 상주시켜서는 안 된다.
  포트가 충돌하고 개당 1~2GB를 쓸 수 있다.
- 레이아웃은 `~/.config/workmux/config.yaml`에서 바꾸며, 저장소별 설정은 저장소 루트의
  `.workmux.yaml`에 둔다.
