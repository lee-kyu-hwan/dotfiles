# Quality Goal Specification

- Task ID: 20260827T080329Z-28-35-create-worktree-스킬에-pr-링크-입력-시-2-r-6b97d528
- Mode: standard
- Status: SPEC_REVIEW (round 2)
- Created: 2026-08-27T08:03:29Z
- Updated: 2026-08-27T08:03:34Z
- Source goal: #28 #35 create-worktree 스킬에 PR 링크 입력 시 2-review 세션에 PR 번호 윈도우를 생성하고 대상 세션을 직접 지정할 수 있도록 확장한다

## Problem and context

`create-worktree` 스킬은 현재 브랜치명 하나만 입력으로 받고, workmux 윈도우를 항상
`1-main` 세션에 연다. 두 가지 한계가 실제 사용에서 드러났다.

**한계 1 — PR 리뷰용 worktree를 PR 번호로 식별할 수 없다.** 현행 규칙은 브랜치명 맨
앞의 숫자만 이슈 번호로 인식해 `{이슈번호}-{짧은이름}` 윈도우를 만든다
(`dot_claude/skills/create-worktree/SKILL.md:145-147`). PR을 리뷰할 때는 PR 번호로
창을 찾는 편이 자연스러운데, PR head 브랜치명에는 보통 PR 번호가 아니라 원 이슈 번호가
들어 있다. 이 저장소의 PR #31이 그 사례다 — head 브랜치가
`30-enhancement/tmux-open-pr-shortcut`이라 현행 규칙으로는 창 이름이 `30-...`이 되어
PR #31을 가리키지 못한다.

**한계 2 — 대상 세션을 지정할 수 없어 불필요한 이동이 발생한다.** 이슈 #35가 기록한
실제 사례에서 사용자가 `2-review`를 명시했음에도 현행 스킬은 `1-main`에 창을 연 뒤
`move-window-to-session` 전체 절차(이동 → 번호 재정렬 → git config·agent state 동기화
→ resurrect 저장 → 재검증)를 밟아야 했다. 처음부터 `--parent-session 2-review`를 쓰면
전부 불필요한 작업이다.

**저장소 컨텍스트.** 스킬은 chezmoi 소스로 관리되며 Claude와 Codex가 각각 별도 원본을
읽는다. 실측 결과 두 원본은 Claude 전용 frontmatter 3줄과 workmux 버전 표기 문구 1줄
(`dot_agents:43` "0.1.233 실측" vs `dot_claude:46` "0.1.233 확인·0.1.248 재확인")에서
차이가 난다. `~/.codex/skills/create-worktree`에는 별도 사본이 없다(실측).

### 측정된 사실 (2026-08-27 실측)

이 Spec이 의존하는 외부 사실은 모두 아래 관찰에 근거한다.

| 사실 | 관찰 명령 | 결과 |
|---|---|---|
| workmux 버전 | `workmux --version` | `workmux 0.1.248` |
| `--pr` 플래그 존재 | `workmux add --help` | `--pr <NUMBER\|URL>` 존재 |
| `--pr`와 positional 관계 | `workmux add --help` | "`[BRANCH_NAME]` ... When used with `--pr`, this becomes the custom local branch name" |
| `workmux open`의 `--pr` 부재 | `workmux open --help` | `--pr` 없음. `--target-name`, `--parent-session`은 있음 |
| tmux 세션 목록 | `tmux list-sessions -F '#{session_name}'` | `1-main`, `2-review`, `3-personal`, `4-eslint`, `5-quick` |
| dotfiles의 git-crypt 여부 | `git config --get filter.git-crypt.smudge` | 값 없음. `scripts/create-worktree.sh`도 없음 |
| zambaguni-front의 git-crypt 여부 | 같은 명령 | `"git-crypt" smudge`. 래퍼 존재 |
| PR #31 상태 | `gh pr view 31 --repo lee-kyu-hwan/dotfiles --json state,headRefName,headRefOid` | `state=OPEN`, head `30-enhancement/tmux-open-pr-shortcut`, OID `9cfc6267ced574945814536710cf1019a37dc354` |
| PR #31 원격 head 브랜치 | `git ls-remote origin '30-enhancement/tmux-open-pr-shortcut'` | `9cfc6267...` — 원격에 존재 |
| PR #31의 pull ref | `git ls-remote origin 'refs/pull/31/head'` | `9cfc6267...` — 동일 OID |
| PR #32 상태 | `gh pr view 32 --json state,headRefName` | `state=OPEN`, head `feat/codex-playwright-e2e-profile` (숫자 접두사 없음) |

### 래퍼 스크립트의 브랜치 판별 (SPEC-001의 근거)

`zambaguni-front/scripts/create-worktree.sh:82-98` 실측. 래퍼는
`git fetch --prune origin` 후 3단계로 판별한다.

1. `refs/remotes/origin/{BRANCH}`가 있으면 → tracking 브랜치 모드
2. `refs/heads/{BRANCH}`가 있으면 → 기존 로컬 브랜치 모드
3. **둘 다 없으면 → 현재 HEAD 기준으로 새 브랜치 생성 (`-b`)**

3번이 결정적이다. 같은 저장소 PR이면 래퍼 자신의 `git fetch --prune origin`이
`origin/{head}`를 만들어 1번이 적용되지만, **fork PR의 head 브랜치는 `origin`에 없다.**
`git fetch --prune origin`은 `refs/pull/*/head`를 가져오지 않으므로 3번으로 떨어져
**PR 내용이 전혀 없는 빈 브랜치를 현재 HEAD에서 만들고**, 겉보기에 성공한 worktree를
남긴다. 이 실패는 조용하다.

## Goals

1. PR 참조를 입력하면 PR 번호로 식별되는 리뷰용 worktree 윈도우를 만든다. 창 이름은
   PR head 브랜치에 들어 있는 이슈 번호가 아니라 PR 번호를 쓴다.
2. 대상 tmux 세션을 호출 시 지정할 수 있게 하고, 지정된 세션에 처음부터 직접 창을
   만들어 `1-main` 경유 이동을 없앤다.
3. 세션 선택 규칙을 명시값 / 저장값 / 모드 기본값 / 전역 기본값의 결정적 우선순위로
   일반화하고, 그 규칙을 Claude와 Codex 두 원본이 동일하게 읽게 한다.
4. 기존 브랜치 입력 동작과 이미 다른 세션으로 옮겨 둔 worktree 존중 규칙을 회귀 없이
   보존한다.
5. 유령 세션 생성, 저장소 불일치, 브랜치 충돌, **PR 내용이 없는 빈 worktree** 같은
   실패를 부작용이 생기기 전에 차단한다.

## Non-goals

- tmux 세션 자동 생성. 선택 세션이 없으면 중단한다.
- workmux session mode 전환(`--session`, `--mode session`)이나 pane 레이아웃 변경.
  레이아웃은 `~/.config/workmux/config.yaml`이 계속 담당한다.
- `move-window-to-session` 스킬 내부 동작 변경. 이번 스킬은 그것을 호출할 뿐이다.
- `remove-worktree` 스킬 변경.
- 대상 저장소의 `scripts/create-worktree.sh` 래퍼 수정. 래퍼의 3단계 판별은 그대로 두고
  스킬이 호출 전에 전제를 보장한다.
- 개발 서버나 에이전트(claude·codex) 자동 실행.
- PR 리뷰 자체의 수행. 이 스킬은 리뷰 환경을 만들 뿐 리뷰하지 않는다.
- `review/pr-{번호}` 같은 별칭 브랜치 생성. PR head 브랜치를 그대로 쓴다.
- GitHub 쓰기 작업(코멘트, 라벨, 상태 변경).
- `workmux` 자체의 기능 추가나 버그 수정.

## Requirements

### R1. 입력 규격

- **R1.1** 첫 번째 positional 인자는 브랜치명 또는 PR 참조이며 필수다. 비어 있으면
  사용자에게 물어본다.
- **R1.2** 두 번째 positional 인자는 정확한 tmux 세션명이며 선택이다.
- **R1.3** 세 번째 이상의 positional 인자가 오면 추측하지 말고 사용법을 안내하고
  중단한다. 이 규칙은 **positional 형태 호출에만** 적용된다(R1.6 참조).
- **R1.4** PR 모드는 다음 형태에서만 자동 선택된다.
  - 전체 GitHub PR URL: `https://github.com/{owner}/{repo}/pull/{번호}`
  - `{owner}/{repo}#{번호}` 형식
  - 자연어 문장에서 숫자 앞뒤에 PR임을 나타내는 표지가 있는 경우
    (예: "PR 1313", "1313번 PR", "pull request 1313")
- **R1.5** 표지 없는 맨 숫자(`1313`)는 PR 참조로 보지 않는다. GitHub는 이슈와 PR이
  번호 공간을 공유하므로 맨 숫자를 PR로 단정하면 엉뚱한 대상을 체크아웃할 수 있다.
  표지가 없으면 브랜치 모드로 해석하거나, 브랜치로도 해석되지 않으면 사용자에게
  확인한다.
- **R1.6** 자연어 호출은 다음 규칙으로 `(브랜치명|PR참조, 대상세션)` 2-튜플로 환원한다.
  - 첫 요소: 문장에서 발견된 브랜치명 또는 R1.4 형태의 PR 참조. 두 개 이상 발견되면
    중단하고 사용자에게 확인한다.
  - 둘째 요소: 문장에서 발견된 tmux 세션명. 두 개 이상 발견되면 중단하고 확인한다.
  - 환원 결과가 2-튜플을 넘지 않으므로 R1.3의 "세 번째 positional" 중단은 자연어
    호출에서 발동하지 않는다. 대신 위 두 "두 개 이상" 규칙이 같은 역할을 한다.
- **R1.7** 세션명을 접두사로 보정하거나 존재하는 세션 목록에서 추측하지 않는다. 문장에
  나온 문자열을 그대로 쓴다.
- **R1.8** Claude frontmatter의 `argument-hint`는
  `<branch-name|pr-ref> [target-session]`로 갱신한다.

### R2. 세션 선택 우선순위

선택 세션(`SELECTED_SESSION`)은 다음 순서로 결정한다.

1. 사용자가 이번 호출에서 명시한 대상 세션
2. 기존 worktree의 `workmux.worktree.{이름}.window-session` git config 값이
   `^[0-9]+-.+$`를 만족할 때 그 값
3. 입력 모드 기본값 — PR 모드이면 `2-review`
4. 전역 기본값 `1-main`

- **R2.1** 저장값이 모드 기본값보다 우선한다. 저장값은 사용자가 과거에 직접 창을 옮긴
  행동의 기록이므로, 단순 관습인 모드 기본값이 그것을 덮으면 현행 "예외 1"이 막으려던
  실패(의도적으로 옮긴 창을 조용히 되끌고 옴)가 그대로 재발한다.
- **R2.2** 저장값이 `^[0-9]+-.+$`를 만족하지 않으면 규칙 이전 레거시 값으로 보고
  우선순위 2에서 제외하며, 선택된 세션으로 git config를 갱신한다. 판정은 셸
  glob(`[0-9]*-*`)이 아니라 정규식으로 한다 — glob의 첫 `*`는 숫자 반복이 아니라 임의
  문자열이라 `1legacy-session`이나 `1-`가 통과한다.
- **R2.3** 선택 세션이 확정되기 전에는 어떤 workmux 명령도 실행하지 않는다.
- **R2.4** 명시 세션(우선순위 1)이 유효한 저장값(우선순위 2)을 덮은 경우, 창을 연 뒤
  `workmux.worktree.{이름}.window-session`이 명시 세션을 가리키는지 확인하고 다르면
  갱신한다. 스킬이 이 값을 직접 쓰는 것은 이 경우와 R2.2, R8.2 세 곳뿐이다. 갱신하지
  않으면 다음번 세션 미명시 호출이 옛 세션으로 조용히 되돌아간다.

### R3. tmux 세션 검증

- **R3.1** `tmux list-sessions -F '#{session_name}'`을 단독 실행해 종료 코드를 먼저
  확인한다.
- **R3.2** exit 1과 `error connecting to ...`이면 tmux 서버 부재로 보고하고 중단한다.
  "세션이 없다"와 구분해서 보고한다.
- **R3.3** 목록 조회 성공 후 `grep -qxF -- "$SELECTED_SESSION"`으로 전체 문자열 일치를
  확인한다.
- **R3.4** `has-session -t`를 쓰지 않는다. tmux 타깃은 접두사 매칭을 하므로
  `has-session -t 2`와 `has-session -t 2-rev`가 모두 exit 0이다(실측).
- **R3.5** 선택 세션이 없으면 자동 생성하지 않고 중단한다. workmux는 존재하지 않는
  `--parent-session` 값을 오류 없이 받아 세션을 만들고 git config에 영구 저장하므로,
  이 검사가 유일한 안전망이다.
- **R3.6** 현행의 "`1-main` 존재 확인"은 "선택 세션 존재 확인"으로 일반화한다. 선택
  세션이 `2-review`라면 `1-main` 존재 여부는 생성에 필요하지 않다.

### R4. PR 참조 해석

- **R4.1** PR 번호, 실제 head 브랜치명, head 커밋 OID를 조회한다.

  ```bash
  gh pr view {번호} --repo {owner}/{repo} \
    --json number,state,headRefName,headRefOid,headRepositoryOwner,isCrossRepository,url
  ```

- **R4.2** PR 링크의 base 저장소와 현재 저장소가 다르면 중단한다.
- **R4.3** PR head 브랜치의 worktree가 이미 있으면 **새 worktree를 만들지 않는다.**
  별칭 브랜치도 만들지 않는다. 이 경우 생성을 건너뛰고 R7의 기존 worktree 창 처리로
  넘어간다. 전체 작업을 중단하는 것이 아니라 **생성 단계만** 건너뛴다.
- **R4.4** 같은 이름의 로컬 브랜치가 있는데 R4.1의 head OID와 다른 커밋을 가리키면
  덮어쓰지 않고 중단한다. 사용자의 미푸시 작업이 유실될 수 있기 때문이다.
- **R4.5** `gh`가 없거나 인증되지 않았거나 PR 조회가 실패하면 그 사실을 보고하고
  중단한다. PR 정보를 추측하지 않는다.
- **R4.6** **PR head 브랜치 확보(SPEC-001).** worktree를 새로 만들기 전에, PR head
  커밋이 로컬에서 `{head브랜치명}`으로 도달 가능함을 보장한다. 래퍼는 브랜치가 로컬과
  `origin` 양쪽에 없으면 현재 HEAD에서 빈 브랜치를 만들므로(래퍼 82-98행 실측), 이
  보장 없이 래퍼를 부르면 PR 내용이 없는 worktree가 조용히 생긴다.

  ```bash
  # 로컬 브랜치가 이미 있으면 R4.4의 OID 비교로 판정이 끝나 있다.
  # 없을 때만 pull ref에서 가져온다. fork PR도 이 ref로 동일하게 처리된다.
  git fetch origin "refs/pull/{PR번호}/head:{head브랜치명}"
  # 확보 확인 — 실패하면 중단하고 래퍼를 부르지 않는다.
  git rev-parse --verify "refs/heads/{head브랜치명}"   # == R4.1의 headRefOid
  ```

  fetch가 실패하거나 확보된 OID가 `headRefOid`와 다르면 중단한다. 이 요구는 래퍼가
  있는 경로와 없는 경로 모두에 적용된다 — 다만 래퍼 없는 경로는 `workmux add --pr`가
  체크아웃을 직접 하므로(R6.3) 사전 fetch 대신 **사후 검증**(R6.8)으로 같은 보장을
  얻는다.

### R5. 윈도우 이름 파생

- **R5.1** 짧은 이름은 브랜치명(PR 모드에서는 PR head 브랜치명)에서 마지막 `/`까지를
  제거한 부분이다. 예: `392-feat/add-partner-chat-enabled` → `add-partner-chat-enabled`.
- **R5.2** 브랜치 모드에서 이슈 번호는 브랜치명 맨 앞의 숫자 또는 `ZF-숫자`만 인식한다.
  맨 앞이 아니면 이슈 번호가 아니다. 현행 규칙을 그대로 유지한다.
- **R5.3** PR 모드의 윈도우 이름은 `{PR번호}-{짧은이름}`이다. PR head 브랜치가 이슈
  번호로 시작하더라도 PR 번호를 쓴다.
- **R5.4** 브랜치 모드에서 이슈 번호가 없으면 `--target-name`을 생략한다. 현행 규칙을
  유지한다.
- **R5.5** workmux가 target name을 소문자로 정규화하므로, 사용자에게 안내하거나 이후
  명령에 재사용할 이름은 정규화된 소문자다.
- **R5.6** **창 이름 충돌 시 재시도(SPEC-009).** 충돌 재시도 이름은 모드별로 다르다.
  - 브랜치 모드: `{repo명}-{짧은이름}` (현행 규칙 유지)
  - PR 모드: `{PR번호}-{repo명}-{짧은이름}` — PR 번호를 반드시 보존한다. 현행
    `{repo명}-{짧은이름}`을 그대로 쓰면 PR 번호가 사라져 이 변경의 목적 자체가 무너진다.

### R6. 생성·오픈 경로

- **R6.1** 경로 분기는 저장소 루트(`git rev-parse --show-toplevel`) 기준으로
  `scripts/create-worktree.sh` 존재 여부로 판정한다. 상대 경로로 판정하면 서브디렉터리나
  기존 worktree 안에서 부를 때 false가 된다. 현행 규칙을 유지한다.
- **R6.2** git-crypt 저장소에서 `workmux add`를 쓰지 않는다. PR 모드에서도 마찬가지다.
- **R6.3** 래퍼가 없는 저장소의 PR 모드는 positional 브랜치명을 생략하고 실행한다.

  ```bash
  workmux add --pr {PR참조} \
    --target-name {PR번호}-{짧은이름} \
    --parent-session {선택세션}
  ```

  positional을 주면 그것이 커스텀 로컬 브랜치명이 되어 PR head 브랜치가 쓰이지 않는다
  (`workmux add --help` 실측).
- **R6.4** 래퍼가 있는 저장소의 PR 모드는 R4.6으로 head 브랜치를 확보한 뒤 실행한다.

  ```bash
  ./scripts/create-worktree.sh {head브랜치명}
  workmux open {디렉토리명} \
    --target-name {PR번호}-{짧은이름} \
    --parent-session {선택세션}
  ```

- **R6.5** 래퍼가 실패하면 종료 코드를 확인해 중단하고 `workmux open`으로 넘어가지
  않는다. 래퍼의 확인 프롬프트를 `-y`나 `yes |`로 우회하지 않는다. 래퍼에 실행 권한이
  없으면 경로를 바꾸지 말고 오류로 보고한다.
- **R6.6** 모든 `workmux add`/`workmux open` 예시가 고정 `1-main`이 아니라 선택 세션
  변수를 쓴다.
- **R6.7** `--parent-session` 미지원 조합(session mode, 샌드박스 안, `--count`,
  `--foreach`, 여러 `--agent`, stdin)에서는 플래그를 생략한다. 현행 예외를 유지한다.
- **R6.8** **PR worktree 내용 검증(SPEC-001).** 생성 직후 worktree의 HEAD가 R4.1의
  `headRefOid`와 같은지 확인한다. 다르면 PR 내용이 없는 worktree이므로 성공으로
  보고하지 않고 사용자에게 알린다.

  ```bash
  git -C {worktree경로} rev-parse HEAD          # == headRefOid
  git -C {worktree경로} rev-parse --abbrev-ref HEAD   # == head브랜치명
  ```

### R7. 기존 worktree 상태별 동작

- **R7.0** 세션 선택(R2)보다 먼저 대상 브랜치의 worktree 존재 여부와 경로를 확정한다.
  저장 세션(R2 우선순위 2)을 읽으려면 worktree 경로가 필요하기 때문이다.

  ```bash
  git worktree list --porcelain   # branch refs/heads/{브랜치명} 항목의 worktree 경로
  ```

- **R7.1** worktree는 있는데 workmux 창이 닫혀 있으면 선택 세션으로 직접 연다.
- **R7.2** 창이 이미 열려 있고 선택 세션과 같은 세션이면 중복 창을 만들지 않고 기존
  위치를 안내한다.
- **R7.3** 창이 열려 있고 다른 세션이며 사용자가 대상을 명시하지 않았으면 기존 위치를
  존중한다(R2 우선순위 2가 이미 그 값을 선택했으므로 R7.2로 귀결된다).
- **R7.4** 창이 열려 있고 다른 세션이며 사용자가 대상을 명시했으면, `workmux open`으로
  재구성하지 않고 `move-window-to-session` 절차를 쓴다. 살아 있는 pane과 에이전트
  상태를 보존하기 위해서다. 이동 후 R2.4의 git config 확인을 수행한다.
- **R7.5** 같은 브랜치의 worktree가 이미 있으면 새로 만들지 않고 기존 경로를 안내하는
  현행 규칙을 유지한다. R4.3과 같은 규칙이며 PR 모드에도 동일하게 적용된다.

### R8. 생성 후 검증

- **R8.1** `tmux list-windows -a -F '#{session_name}:#{window_index}\t#{window_name}'`로
  실제 윈도우 이름과 세션을 확인한다. `workmux list`에는 윈도우 이름 열이 없으므로
  추측해서 안내하면 사용자가 `workmux close`에 없는 이름을 넘기게 된다.
- **R8.2** 실제 세션이 선택 세션과 다르면 사용자에게 알리고, 잘못 만들어진 세션과 git
  config 값을 함께 정리한다.
- **R8.3** 결과 보고에 worktree 경로, 브랜치, 실제 세션, 실제 윈도우 이름 네 가지를
  포함한다. PR 모드에서는 PR 번호와 head OID도 포함한다.

### R9. 문서 동기화

- **R9.1** `dot_agents/skills/create-worktree/SKILL.md`와
  `dot_claude/skills/create-worktree/SKILL.md`의 본문은 Claude 전용 frontmatter를
  제외하고 동일해야 한다.
- **R9.2** 현존하는 workmux 버전 표기 불일치(`dot_agents:43` vs `dot_claude:46`)를
  더 정확한 `dot_claude` 쪽 문구로 통일한다.
- **R9.3** `dot_agents/skills/create-worktree/agents/openai.yaml`의 `default_prompt`에
  대상 세션 또는 PR 참조 사례를 반영한다.
- **R9.4** 홈의 적용본(`~/.claude/skills/...`, `~/.agents/skills/...`)을 직접 수정하지
  않는다. chezmoi 원본만 고치고 `chezmoi apply`로 적용한다.

## Acceptance criteria

각 기준은 "검증 방법"의 관찰로 판정하며, "커버 요구사항" 열이 요구사항 전수 대응을
보인다. 검증 유형은 **[실행]**(명령 종료 코드·출력으로 판정), **[문서]**(두 SKILL.md에
해당 규칙이 기술되어 있는지 검토로 판정)로 표시한다.

| ID | 기준 | 검증 방법 | 커버 요구사항 |
|---|---|---|---|
| AC-1 | 입력 계약이 `<브랜치명\|PR참조> [대상세션]`으로 문서화되고, 첫 인자 누락 시 사용자에게 묻는다 | [문서] 두 SKILL.md의 파라미터 절 | R1.1, R1.2 |
| AC-2 | positional 3개 이상이면 사용법 안내 후 중단한다 | [문서] R1.3 서술 | R1.3 |
| AC-3 | PR 모드 트리거 형태 3종(URL, `owner/repo#N`, 표지 있는 자연어)이 열거된다 | [문서] R1.4 서술과 예시 | R1.4 |
| AC-4 | 표지 없는 맨 숫자를 PR로 해석하지 않는 규칙과 그 근거(번호 공간 공유)가 기술된다 | [문서] R1.5 서술 | R1.5 |
| AC-5 | 자연어 → 2-튜플 환원 규칙과 "두 개 이상 발견 시 중단"이 기술된다 | [문서] R1.6 서술 | R1.6 |
| AC-6 | 세션명을 접두사 보정하거나 목록에서 추측하지 않는 규칙이 기술된다 | [문서] R1.7 서술 | R1.7 |
| AC-7 | Claude frontmatter `argument-hint`가 `<branch-name\|pr-ref> [target-session]`이다 | [실행] `grep -q 'argument-hint: <branch-name|pr-ref> \[target-session\]' dot_claude/.../SKILL.md` → exit 0 | R1.8 |
| AC-8 | 세션 우선순위 4단계가 명시값 > 저장값 > 모드 기본값 > `1-main` 순으로 기술된다 | [문서] R2 우선순위 목록. 저장값이 모드 기본값보다 **위**임을 확인 | R2.1 |
| AC-9 | 레거시 저장값을 정규식으로 판정하고 셸 glob을 금지하는 근거가 기술된다 | [문서] R2.2 서술에 `^[0-9]+-.+$`와 glob 반례(`1legacy-session`, `1-`) 포함 | R2.2 |
| AC-10 | 선택 세션 확정 전 workmux 명령 금지가 기술된다 | [문서] R2.3 서술 | R2.3 |
| AC-11 | 명시 세션이 저장값을 덮었을 때 git config를 갱신하는 규칙이 기술되고, 스모크 테스트에서 값이 실제로 선택 세션을 가리킨다 | [문서] R2.4 서술 + [실행] 스모크 테스트 후 `git -C {worktree} config --get workmux.worktree.{이름}.window-session` == `2-review` | R2.4 |
| AC-12 | tmux 서버 부재를 세션 부재와 구분해 감지한다 | [실행] `tmux -L quality-goal-nonexistent-socket list-sessions` → exit 1 + `error connecting to` (별도 소켓이라 실서버 무영향). 두 SKILL.md에 이 구분이 기술됨 | R3.1, R3.2 |
| AC-13 | 없는 세션은 `grep -qxF` 전체 일치로 부재 판정되며, 이 판정 실패 시 workmux를 호출하지 않는다 | [실행] `tmux list-sessions -F '#{session_name}' \| grep -qxF -- 'definitely-not-a-session'` → exit 1. + [문서] R3.5의 중단 규칙 | R3.3, R3.5 |
| AC-14 | `has-session`의 접두사 함정이 실측 근거와 함께 금지된다 | [실행] `tmux has-session -t 2` → exit 0, `tmux has-session -t 2-rev` → exit 0, `grep -qxF -- 2-rev` → exit 1 (실측 완료). + [문서] R3.4 서술 | R3.4 |
| AC-15 | 고정 `1-main` 검사가 선택 세션 검사로 일반화된다 | [실행] 아래 "1-main 잔존 검사" 참조 | R3.6, R6.6 |
| AC-16 | PR 조회가 `state`, `headRefName`, `headRefOid`, `isCrossRepository`를 포함한다 | [문서] R4.1의 `gh pr view` 명령 | R4.1 |
| AC-17 | PR base 저장소 불일치 시 중단한다 | [문서] R4.2 서술 | R4.2 |
| AC-18 | PR head 브랜치의 worktree가 이미 있으면 생성을 건너뛰고 R7 창 처리로 넘어간다(전체 중단 아님) | [문서] R4.3 서술 + Architecture 흐름도의 분기 순서가 일치 | R4.3, R7.5 |
| AC-19 | 동명 로컬 브랜치가 head OID와 다르면 중단한다 | [문서] R4.4 서술 | R4.4 |
| AC-20 | `gh` 부재·미인증·조회 실패 시 추측 없이 중단한다 | [문서] R4.5 서술 | R4.5 |
| AC-21 | 래퍼 경로에서 `refs/pull/{N}/head`로 head 브랜치를 확보하고, 확보 실패 시 래퍼를 부르지 않는다 | [문서] R4.6의 fetch 명령과 중단 규칙 + 래퍼 3단계 판별 근거가 기술됨 | R4.6 |
| AC-22 | 짧은 이름이 마지막 `/` 뒤로 파생된다 | [문서] R5.1 서술과 예시 | R5.1 |
| AC-23 | 브랜치 모드 이슈 번호 규칙(맨 앞 숫자 또는 `ZF-숫자`)이 유지된다 | [문서] R5.2 서술 | R5.2 |
| AC-24 | PR head 브랜치가 이슈 번호로 시작해도 창 이름에 PR 번호가 쓰인다 | [실행] 스모크 테스트에서 창 이름이 `31-tmux-open-pr-shortcut`이고 `30-`으로 시작하지 않음 | R5.3 |
| AC-25 | 브랜치 모드에서 이슈 번호가 없으면 `--target-name`을 생략한다 | [문서] R5.4 서술 | R5.4 |
| AC-26 | target name 소문자 정규화가 안내에 반영된다 | [문서] R5.5 서술 | R5.5 |
| AC-27 | PR 모드 충돌 재시도 이름이 PR 번호를 보존한다 | [문서] R5.6의 `{PR번호}-{repo명}-{짧은이름}` 서술과 브랜치 모드와의 구분 | R5.6 |
| AC-28 | 경로 분기를 저장소 루트 기준으로 판정한다 | [문서] R6.1의 `git rev-parse --show-toplevel` 사용 | R6.1 |
| AC-29 | git-crypt 저장소에서 `workmux add`를 쓰지 않는다 | [문서] R6.2 서술 + git-crypt 분기에 래퍼 호출만 존재 | R6.2 |
| AC-30 | 래퍼 없는 PR 경로가 positional을 생략하고 `--pr`를 쓴다 | [실행] 스모크 테스트에서 worktree 브랜치가 `30-enhancement/tmux-open-pr-shortcut` | R6.3 |
| AC-31 | 래퍼 있는 PR 경로가 head 브랜치 확보 → 래퍼 → `workmux open` 순서로 기술된다 | [문서] R6.4의 명령 순서 | R6.4 |
| AC-32 | 래퍼 실패 시 창을 열지 않고, 프롬프트를 자동 우회하지 않는다 | [문서] R6.5 서술 | R6.5 |
| AC-33 | `--parent-session` 미지원 조합의 생략 예외가 유지된다 | [문서] R6.7 서술 | R6.7 |
| AC-34 | 생성된 worktree HEAD가 PR head OID와 일치한다 | [실행] 스모크 테스트에서 `git -C {worktree} rev-parse HEAD` == `9cfc6267ced574945814536710cf1019a37dc354` | R6.8 |
| AC-35 | worktree 존재 판정이 세션 선택보다 먼저 수행된다 | [문서] Architecture 흐름도에서 R7.0이 R2보다 앞. `git worktree list --porcelain` 사용 | R7.0 |
| AC-36 | 창이 닫힌 기존 worktree를 선택 세션에 직접 연다 | [문서] R7.1 서술 | R7.1 |
| AC-37 | 같은 세션에 이미 열려 있으면 중복 창을 만들지 않는다 | [문서] R7.2 서술 | R7.2 |
| AC-38 | 세션 미명시 시 기존 위치를 존중한다 | [문서] R7.3 서술 | R7.3 |
| AC-39 | 다른 세션의 열린 창을 명시적으로 옮길 때만 `move-window-to-session`을 쓴다 | [문서] R7.4 서술 | R7.4 |
| AC-40 | 생성 후 실제 세션·창 이름을 `tmux list-windows`로 확인한다 | [실행] 스모크 테스트에서 해당 명령 실행 및 결과 기록 | R8.1 |
| AC-41 | 세션 불일치 시 잘못된 세션과 git config를 함께 정리한다 | [문서] R8.2 서술 | R8.2 |
| AC-42 | 보고에 경로·브랜치·세션·창이름 4항목(PR 모드는 PR번호·head OID 추가)이 포함된다 | [실행] 스모크 테스트 보고에 6항목 존재 | R8.3 |
| AC-43 | 두 SKILL.md 본문이 Claude frontmatter 외에 동일하다 | [실행] `diff dot_agents/.../SKILL.md dot_claude/.../SKILL.md` 출력이 `3a4,6`과 그 3줄만 | R9.1, R9.2 |
| AC-44 | `openai.yaml` `default_prompt`에 세션 또는 PR 사례가 반영된다 | [실행] `grep -qE '2-review\|pull/' openai.yaml` → exit 0 | R9.3 |
| AC-45 | chezmoi 원본만 수정되고 적용본이 원본과 일치한다 | [실행] `chezmoi apply` 후 3개 파일 각각 `cmp` → exit 0 | R9.4 |
| AC-46 | PR 모드 신규 worktree에서 세션 미명시 시 `2-review`가 선택된다 | [실행] 스모크 테스트에서 창이 `2-review`에 열림 | R2 우선순위 3 |
| AC-47 | 두 스킬이 frontmatter 검증을 통과한다 | [실행] 아래 "frontmatter 검증" 참조 | — (도구 위생) |
| AC-48 | 공백 오류와 시크릿 유출이 없다 | [실행] `git diff --check` → exit 0, `pre-commit run --all-files` → 통과 | — (저장소 위생) |

### 요구사항 전수 대응 확인

R1.1→AC-1, R1.2→AC-1, R1.3→AC-2, R1.4→AC-3, R1.5→AC-4, R1.6→AC-5, R1.7→AC-6,
R1.8→AC-7, R2.1→AC-8, R2.2→AC-9, R2.3→AC-10, R2.4→AC-11, R3.1→AC-12, R3.2→AC-12,
R3.3→AC-13, R3.4→AC-14, R3.5→AC-13, R3.6→AC-15, R4.1→AC-16, R4.2→AC-17, R4.3→AC-18,
R4.4→AC-19, R4.5→AC-20, R4.6→AC-21, R5.1→AC-22, R5.2→AC-23, R5.3→AC-24, R5.4→AC-25,
R5.5→AC-26, R5.6→AC-27, R6.1→AC-28, R6.2→AC-29, R6.3→AC-30, R6.4→AC-31, R6.5→AC-32,
R6.6→AC-15, R6.7→AC-33, R6.8→AC-34, R7.0→AC-35, R7.1→AC-36, R7.2→AC-37, R7.3→AC-38,
R7.4→AC-39, R7.5→AC-18, R8.1→AC-40, R8.2→AC-41, R8.3→AC-42, R9.1→AC-43, R9.2→AC-43,
R9.3→AC-44, R9.4→AC-45. **미대응 요구사항 없음.**

### `1-main` 잔존 검사 (AC-15의 실행 정의)

`--parent-session 1-main` 리터럴만 grep하면 다른 하드코딩이 통과한다(SPEC-004).
두 SKILL.md에서 `1-main` 전체를 세고, 아래 허용 목록에 해당하는 것만 남아야 한다.

```bash
grep -n -- '1-main' dot_agents/skills/create-worktree/SKILL.md \
                    dot_claude/skills/create-worktree/SKILL.md
```

**허용되는 잔존 용례** — 이외의 출현은 회귀로 판정한다.

1. R2 우선순위 4순위를 설명하는 "전역 기본값 `1-main`" 서술
2. 우선순위 예시 표에서 기본값 결과를 보이는 셀
3. 유령 세션 위험이나 레거시 마이그레이션을 설명하며 예시로 드는 문장

**금지되는 잔존 용례** — 하나라도 남으면 AC-15 실패.

1. `--parent-session 1-main` 리터럴이 실행 명령 예시에 있는 경우
2. `grep -qxF -- 1-main`처럼 검증 대상이 `1-main`으로 고정된 경우
3. `git config ... window-session 1-main`처럼 기록 값이 고정된 경우
4. "`1-main` 세션이 없으면 여기서 멈춘다"처럼 중단 조건이 `1-main`에 묶인 경우
5. "새로 만든 것이면 `1-main`"처럼 사후 검증 기대값이 고정된 경우

### frontmatter 검증 (AC-47의 실행 정의)

```bash
python3 /Users/lee-kyu-hwan/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator/scripts/quick_validate.py \
  /Users/lee-kyu-hwan/code/dotfiles/dot_claude/skills/create-worktree
python3 /Users/lee-kyu-hwan/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator/scripts/quick_validate.py \
  /Users/lee-kyu-hwan/code/dotfiles/dot_agents/skills/create-worktree
```

실측 기준선(변경 전, 2026-08-27):

- `dot_agents` → `Skill is valid!`, exit 0
- `dot_claude` → `Unexpected key(s) in SKILL.md frontmatter: argument-hint, user-invocable.`, **exit 0**

`quick_validate.py`는 Claude 전용 키를 허용 목록에 두지 않으므로 `dot_claude`에서 이
안내가 나오지만 종료 코드는 0이다. 따라서 **판정 기준은 종료 코드 0 + `dot_claude`의
메시지가 위 Claude 전용 키 안내에서 늘어나지 않을 것**이다. 새로운 종류의 경고가
추가되면 실패로 본다.

## Architecture

스킬은 실행 가능한 코드가 아니라 **에이전트가 읽고 따르는 절차 문서**다. 따라서
"아키텍처"는 문서가 기술하는 결정 흐름과 그 흐름이 호출하는 외부 도구 경계를 뜻한다.

### 결정 흐름

worktree 존재 판정(R7.0)이 세션 선택(R2)보다 **앞선다** — 저장 세션을 읽으려면 worktree
경로가 필요하기 때문이다. 그리고 PR 모드의 기존 worktree는 중단이 아니라 창 처리로
분기한다(R4.3).

```
1. 입력 파싱 (R1)
     ├─ positional 3개 이상 → 사용법 안내 후 중단
     ├─ PR 참조 판정 (R1.4 / R1.5)
     └─ 자연어면 2-튜플 환원 (R1.6)
          ↓
2. PR 모드일 때: PR 해석 (R4.1, R4.2, R4.5)
     ├─ PR번호·head브랜치·headRefOid·isCrossRepository 조회
     └─ base 저장소 불일치 → 중단
          ↓
3. worktree 존재 판정 (R7.0)
     git worktree list --porcelain → 경로 확보 (없으면 null)
          ↓
4. 세션 선택 (R2)
     명시값 > 유효 저장값 > 모드 기본값(PR→2-review) > 1-main
          ↓
5. 세션 검증 (R3)
     list-sessions 종료 코드 → grep -qxF 전체 일치 → 없으면 중단
          ↓
6. 이름 파생 (R5)
     짧은 이름 → 창 이름 (PR 모드면 {PR번호}-, 아니면 {이슈번호}- 또는 생략)
          ↓
7. 분기
     ├─ [worktree 있음] (R4.3 → R7.1~R7.4)
     │     ├─ 창 닫힘 → 선택 세션으로 workmux open
     │     ├─ 창 열림 & 같은 세션 → 안내만
     │     └─ 창 열림 & 다른 세션 & 명시됨 → move-window-to-session
     │
     └─ [worktree 없음] → 브랜치 안전 검사 (R4.4) → 생성 (R6)
           ├─ 래퍼 있음: R4.6 fetch → 래퍼 → workmux open
           └─ 래퍼 없음: workmux add --pr (positional 생략)
          ↓
8. 생성 후 검증 (R6.8, R8)
     worktree HEAD == headRefOid → tmux list-windows 대조 → git config 확인(R2.4)
```

### 구성 요소와 책임 경계

| 구성 요소 | 책임 | 이번 변경 |
|---|---|---|
| `dot_claude/.../SKILL.md` | Claude Code가 읽는 절차 + Claude 전용 frontmatter | 본문 확장, `argument-hint` 갱신 |
| `dot_agents/.../SKILL.md` | Codex·공용 에이전트가 읽는 절차 | 본문을 Claude 본문과 동일하게 확장 |
| `dot_agents/.../agents/openai.yaml` | Codex UI 메타데이터 | `default_prompt` 예시 갱신 |
| `workmux` (0.1.248) | worktree 생성, tmux 창 구성, `--pr` 체크아웃 | 호출만. 변경 없음 |
| 대상 저장소의 `scripts/create-worktree.sh` | git-crypt worktree 생성·키 링크·의존성 설치 | 호출만. 변경 없음. 3단계 판별의 전제를 스킬이 R4.6으로 보장 |
| `gh` | PR 메타데이터 조회 (읽기 전용) | 신규 의존 |
| `git fetch origin refs/pull/N/head` | PR head 커밋 확보 | 신규 의존 (래퍼 경로) |
| `move-window-to-session` 스킬 | 열린 창 이동 + 메타데이터 동기화 | 호출만. 변경 없음 |
| `~/.config/workmux/config.yaml` | pane 레이아웃, `base_branch: auto` | 변경 없음 |

### 결정: 두 원본의 동기화 방식

두 SKILL.md 본문을 동일하게 유지해야 하는데(R9.1), 자동 동기화 장치를 도입할지 수동
유지할지가 선택지였다.

- **대안 A — 심볼릭 링크**: `dot_agents` 본문을 `dot_claude`로 링크. chezmoi가
  `symlink_` 접두사를 지원하지만, Claude 전용 frontmatter가 파일 앞에 있어야 하므로
  파일 전체를 링크할 수 없다. 탈락.
- **대안 B — 생성 스크립트**: 공통 본문에서 두 파일을 만드는 스크립트를 둔다. 이번
  변경 범위(#35 변경 대상 3개 파일)를 넘어서고, chezmoi 흐름에 새 빌드 단계를 넣는다.
  탈락.
- **대안 C — 수동 유지 + 검증(채택)**: 두 파일을 각각 수정하고 `diff`로 frontmatter
  외 동일함을 검증한다(AC-43). 기존 관행과 같고 추가 장치가 없다.

## Interfaces and data flow

### 스킬 입력 계약

```
<브랜치명|PR참조> [대상세션]
```

| 입력 | 모드 | 대상 세션 | 창 이름 |
|---|---|---|---|
| `1290-bug/partner-robots-yeti-disallow` | 브랜치 | `1-main` (기본) | `1290-partner-robots-yeti-disallow` |
| `1290-bug/... 2-review` | 브랜치 | `2-review` (명시) | `1290-partner-robots-yeti-disallow` |
| `fix/login-bug` | 브랜치 | `1-main` | `--target-name` 생략 |
| `https://github.com/owner/repo/pull/1247` | PR | `2-review` (모드 기본) | `1247-{PR head 짧은이름}` |
| `zambaguni/zambaguni-front#1313` | PR | `2-review` | `1313-snap-board-grid-windowing` |
| `https://github.com/o/r/pull/1247 3-personal` | PR | `3-personal` (명시) | `1247-...` |
| 위 PR + 저장값 `3-personal`, 세션 미명시 | PR | `3-personal` (저장값 우선, R2.1) | `1247-...` |
| 위 PR + 저장값 `3-personal`, `2-review` 명시 | PR | `2-review` (명시 우선) + git config 갱신(R2.4) | `1247-...` |
| `1313` (표지 없는 맨 숫자) | 브랜치 또는 확인 요청 (R1.5) | — | — |
| "PR 1313을 2-review에 열어줘" | PR (표지 있음) | `2-review` | `1313-...` |

### 외부 명령 계약

**PR 메타데이터 조회 (읽기 전용)**

```bash
gh pr view {번호} --repo {owner}/{repo} \
  --json number,state,headRefName,headRefOid,headRepositoryOwner,isCrossRepository,url
```

**PR head 브랜치 확보 (래퍼 경로, R4.6)**

```bash
git fetch origin "refs/pull/{PR번호}/head:{head브랜치명}"
git rev-parse --verify "refs/heads/{head브랜치명}"   # == headRefOid 확인
```

**래퍼 없는 저장소 — PR 모드**

```bash
workmux add --pr {PR참조} \
  --target-name {PR번호}-{짧은이름} \
  --parent-session {선택세션}
```

positional 브랜치명을 **생략**한다.

**래퍼 있는 저장소 — PR 모드**

```bash
./scripts/create-worktree.sh {head브랜치명}
workmux open {디렉토리명} \
  --target-name {PR번호}-{짧은이름} \
  --parent-session {선택세션}
```

**생성 후 검증**

```bash
git -C {worktree경로} rev-parse HEAD                  # == headRefOid (R6.8)
git -C {worktree경로} rev-parse --abbrev-ref HEAD     # == head브랜치명
tmux list-windows -a -F '#{session_name}:#{window_index}\t#{window_name}'
git -C {worktree경로} config --get workmux.worktree.{이름}.window-session
```

**브랜치 모드** — 현행과 동일하되 `--parent-session`이 선택 세션 변수를 쓴다.

### 상태 저장소

| 위치 | 내용 | 읽기 | 쓰기 |
|---|---|---|---|
| `workmux.worktree.{이름}.window-session` (git config) | 창이 속한 세션 | R2 우선순위 2 | 세 경우만: R2.2 레거시 갱신, R2.4 명시값 덮어쓰기, R8.2 불일치 정리. workmux 자신도 `--parent-session`을 받으면 이 값을 쓴다 |
| tmux 서버 | 세션·윈도우 목록 | R3 검증, R8.1 대조 | 없음 (세션 자동 생성 금지) |
| `git worktree list` | worktree 경로·브랜치 | R7.0 | 없음 |
| `~/.local/state/workmux/agents/*.json` | 에이전트 상태 | — | `move-window-to-session`이 담당. 이 스킬은 직접 건드리지 않음 |

## Failure behavior

| 실패 | 감지 | 사용자에게 보이는 동작 |
|---|---|---|
| positional 3개 이상 | 인자 개수 | 사용법 안내 후 중단 |
| 자연어에서 브랜치·PR 참조 2개 이상 | R1.6 환원 | 중단하고 사용자에게 확인 |
| 자연어에서 세션명 2개 이상 | R1.6 환원 | 중단하고 사용자에게 확인 |
| 표지 없는 맨 숫자 | R1.5 판정 | 브랜치로 해석하거나 사용자에게 확인. PR로 단정 금지 |
| `gh` 없음·미인증·PR 조회 실패 | 종료 코드 | 그 사실을 보고하고 중단. PR 정보 추측 금지 |
| PR base 저장소 ≠ 현재 저장소 | `gh` 응답 대조 | 중단. worktree 생성 안 함 |
| **PR head 브랜치 fetch 실패** | `git fetch` 종료 코드 | **중단. 래퍼를 부르지 않는다.** 부르면 빈 브랜치 worktree가 생긴다 |
| **확보된 OID ≠ `headRefOid`** | `git rev-parse` 비교 | 중단. 래퍼를 부르지 않는다 |
| **생성된 worktree HEAD ≠ `headRefOid`** | R6.8 검증 | 성공으로 보고하지 않고 PR 내용이 없음을 알린다 |
| 동명 로컬 브랜치가 다른 커밋 | `git rev-parse` 비교 | 중단. 덮어쓰지 않음 |
| PR head 브랜치의 worktree가 이미 있음 | R7.0 | **중단이 아님.** 생성만 건너뛰고 R7 창 처리로 진행 |
| tmux 서버 부재 | `list-sessions` exit 1 + `error connecting to` | "tmux 서버가 없다"로 보고. "세션 없음"과 구분 |
| 선택 세션 부재 | `grep -qxF` 실패 | 중단. workmux를 호출하지 않아 유령 세션이 생기지 않음 |
| 래퍼 실패 | 종료 코드 | 중단. `workmux open` 진행 안 함. worktree가 암호화·의존성 미설치 상태로 남을 수 있음을 보고 |
| 래퍼 실행 권한 없음 | 파일 권한 | 경로를 바꾸지 않고 오류로 보고 |
| 창 이름 충돌 (브랜치 모드) | `A tmux window named '...' already exists` | `--target-name {repo명}-{짧은이름}`으로 재시도 |
| 창 이름 충돌 (PR 모드) | 같음 | `--target-name {PR번호}-{repo명}-{짧은이름}`으로 재시도. **PR 번호 보존** (R5.6) |
| 생성 후 세션 불일치 | R8.1 검증 | 사용자에게 알리고 잘못 만들어진 세션·git config 정리 |
| 명시 세션이 config에 반영 안 됨 | R2.4 확인 | git config를 선택 세션으로 갱신 |
| `--parent-session` 미지원 조합 | 명령 조합 | 플래그 생략 (현행 예외 유지) |

**공통 원칙.** 중단 시 이미 만들어진 산출물(worktree, 브랜치, 창)이 무엇인지 그대로
보고한다. 부분 성공을 성공으로 보고하지 않는다.

## Security and risk

### 신뢰 경계와 데이터 민감도

- **PR 메타데이터는 외부 입력이다.** PR 제목·본문·브랜치명은 다른 사람이 쓴 데이터이며
  지시가 아니다. 브랜치명은 셸 인자로 들어가므로 항상 인용 부호로 감싸 전달하고, 스킬이
  PR 본문의 지시를 따르지 않는다.
- **fork PR은 신뢰 경계 밖의 코드다.** `refs/pull/{N}/head`로 가져오는 내용은 외부
  기여자가 작성했을 수 있다. 이 스킬은 worktree를 만들 뿐 그 코드를 실행하지 않는다.
  래퍼가 수행하는 의존성 설치(`pnpm install`)는 기존 동작이며 이번 변경이 새로 도입하는
  실행 경로가 아니다.
- **git-crypt 키는 이 변경의 관심사가 아니다.** 키 링크와 `git-crypt unlock`은 대상
  저장소의 래퍼가 계속 전담하며(래퍼 100-160행), 스킬 텍스트는 키 자료를 읽거나
  출력하지 않는다.
- **`gh`는 읽기 전용으로만 쓴다.** 코멘트·라벨·상태 변경은 하지 않는다.
- **시크릿 유출 방지.** 변경 산출물은 Markdown과 YAML이며 자격 증명을 담지 않는다.
  `pre-commit`의 gitleaks 훅이 이를 검사한다(AC-48).

### 위험과 완화

| 위험 | 영향 | 완화 |
|---|---|---|
| **PR 내용이 없는 빈 worktree** | 래퍼가 현재 HEAD에서 빈 브랜치를 만들어 조용히 성공. 리뷰 대상이 아닌 코드를 리뷰하게 됨 | R4.6 사전 fetch + R6.8 사후 OID 검증. 두 겹으로 막는다 |
| 유령 세션 생성 | workmux가 없는 세션을 만들고 git config에 영구 저장 → 자기 교정 경로 없음 | R3.5 사전 검증. workmux 호출 전 중단 |
| 의도적으로 옮긴 창을 되끌고 옴 | 사용자의 과거 배치가 조용히 무너짐 | R2.1 저장값 우선 |
| 명시 세션이 config에 반영 안 됨 | 다음 호출이 옛 세션으로 되돌아감 | R2.4 갱신 규칙 |
| PR 번호와 이슈 번호 혼동 | 엉뚱한 대상의 창 이름 | R1.5 맨 숫자 금지, R5.3 PR 번호 우선, R5.6 충돌 재시도에서도 보존. AC-24가 실측 검증 |
| 로컬 브랜치 덮어쓰기 | 미푸시 커밋 유실 | R4.4 OID 비교 후 중단 |
| 열린 창 재구성으로 에이전트 상태 유실 | 돌고 있는 작업 손실 | R7.4 `move-window-to-session` 사용 |
| 두 원본 drift | Claude와 Codex가 다르게 동작 | R9.1 + AC-43 `diff` 검증 |
| 스모크 테스트의 부작용 | 실제 worktree·tmux 창 생성 | 자신의 dotfiles 저장소 PR #31 사용. 정리 절차를 Test strategy에 포함 |

### 롤백

변경 산출물은 chezmoi 소스의 Markdown·YAML 3개 파일이다. 롤백은
`git revert` 또는 `git checkout -- {경로}` 후 `chezmoi apply`이며 데이터 마이그레이션이
없다. 스모크 테스트로 만들어진 worktree·창·로컬 브랜치는 Test strategy의 정리 절차로
제거한다.

### 비적용 항목

이 작업은 standard 등급이며 다음은 해당 사항이 없다.

- **인증·인가·테넌시**: 권한 경계를 다루지 않는다. `gh`는 사용자 자신의 기존 자격
  증명을 그대로 쓰며 이 변경이 권한을 넓히지 않는다.
- **DB 스키마·마이그레이션·백필**: 영속 스키마가 없다.
- **공개 API 호환성·멱등성·동시성**: 외부에 노출되는 계약이 없다. 스킬은 단일 사용자가
  대화형으로 호출한다.
- **프로덕션 변경**: 프로덕션 시스템을 건드리지 않는다.

## Test strategy

이 저장소에는 테스트 스위트·타입 체크·빌드가 없다(`package.json`, `Makefile`,
`justfile`, `.github/workflows` 부재 실측). 검증은 세 층으로 한다.

### 1층 — 부작용 없는 실행 검사

| 검사 | 명령 | 커버 |
|---|---|---|
| frontmatter | `quick_validate.py` 2회 (위 "frontmatter 검증" 기준선 대조) | AC-47 |
| `argument-hint` | `grep -q 'argument-hint: <branch-name\|pr-ref> \[target-session\]'` | AC-7 |
| 두 본문 동일성 | `diff` → `3a4,6`과 그 3줄만 | AC-43 |
| `1-main` 잔존 | 위 "1-main 잔존 검사"의 허용/금지 목록 대조 | AC-15 |
| `openai.yaml` | `grep -qE '2-review\|pull/'` | AC-44 |
| tmux 서버 부재 감지 | `tmux -L quality-goal-nonexistent-socket list-sessions` → exit 1 + `error connecting to` | AC-12 |
| 없는 세션 판정 | `tmux list-sessions -F '#{session_name}' \| grep -qxF -- 'definitely-not-a-session'` → exit 1 | AC-13 |
| 접두사 함정 재현 | `tmux has-session -t 2` → 0, `-t 2-rev` → 0, `grep -qxF 2-rev` → 1 | AC-14 |
| chezmoi 일치 | `chezmoi diff` → `chezmoi apply` → 3개 파일 `cmp` | AC-45 |
| 공백·시크릿 | `git diff --check`, `pre-commit run --all-files` | AC-48 |

위 tmux 검사 3종은 모두 **읽기 전용이거나 별도 소켓**을 쓰므로 실제 세션 배치를
바꾸지 않는다. 세 명령의 예상 종료 코드는 2026-08-27에 실측으로 확인했다.

### 2층 — 문서 검토

`[문서]`로 표시된 기준은 절차 서술이므로, 해당 규칙이 두 SKILL.md에 명시적으로
기술되어 있는지를 검토로 판정한다. 각 기준의 확인 대상은 수용 기준 표의 "검증 방법"
열에 특정해 두었다.

**이 층의 한계.** 문서 존재 검사는 "규칙이 올바르게 적혀 있음"만 보이고 "그 규칙을
따랐을 때 실제로 옳은 결과가 나옴"은 보이지 않는다. 그래서 가장 위험한 세 가지(유령
세션 방지, tmux 서버 부재 구분, 접두사 함정)는 1층의 실행 검사로 끌어올렸고, PR 번호
파생과 worktree 내용은 3층 실측으로 옮겼다. 남은 `[문서]` 기준은 실행 검증에 실제
worktree 생성이 필요한 것들이며, 이 한계를 보고서에 기록한다.

### 3층 — 실제 스모크 테스트

**대상**: `lee-kyu-hwan/dotfiles` PR #31.

**가용성 실측 (2026-08-27)**: `state=OPEN`, head 브랜치
`30-enhancement/tmux-open-pr-shortcut`가 원격에 존재(`9cfc6267...`),
`refs/pull/31/head`도 같은 OID로 해석됨. 리뷰 시점의 "이미 머지되어 head 브랜치가
삭제되었을 수 있다"는 우려는 실측으로 반증되었다.

**선정 근거**: PR 번호(31)와 head 브랜치의 이슈 번호(30)가 달라 R5.3을 판별한다.
dotfiles는 git-crypt가 아니고 래퍼도 없으므로 `workmux add --pr` 경로를 탄다.

**대체 계획**: 실행 시점에 PR #31이 닫혀 head 브랜치가 사라졌으면, 같은 조건(PR 번호
≠ head 브랜치 접두사 숫자)을 만족하는 다른 열린 PR로 교체한다. PR #32는 head가
`feat/codex-playwright-e2e-profile`로 숫자 접두사가 없어 AC-24를 판별하지 못하므로
대체 대상이 아니다. 조건을 만족하는 PR이 없으면 AC-24·AC-30·AC-34·AC-40·AC-42·AC-46·AC-11을
문서 검토로 강등하고 그 사실을 보고서에 한계로 명시한다. 이 강등은 임의 판단이 아니라
"조건을 만족하는 PR 부재"가 관찰되었을 때만 발동한다.

| 단계 | 관찰 | 커버 |
|---|---|---|
| 세션 미명시로 PR 모드 실행 | 창이 `2-review`에 열림 | AC-46 |
| 창 이름 | `31-tmux-open-pr-shortcut` (`30-`으로 시작하지 않음) | AC-24 |
| worktree 브랜치 | `git -C {wt} rev-parse --abbrev-ref HEAD` == `30-enhancement/tmux-open-pr-shortcut` | AC-30 |
| worktree HEAD | `git -C {wt} rev-parse HEAD` == `9cfc6267ced574945814536710cf1019a37dc354` | AC-34 |
| 실제 창 위치 | `tmux list-windows -a` 출력 기록 | AC-40 |
| git config | `workmux.worktree.{이름}.window-session` == `2-review` | AC-11 |
| 결과 보고 | 경로·브랜치·세션·창이름·PR번호·head OID 6항목 | AC-42 |

**정리 절차** (검증 후 반드시 수행):

```bash
workmux remove {worktree명}          # worktree + 창 제거
git branch -D 30-enhancement/tmux-open-pr-shortcut   # fetch로 만들어진 로컬 브랜치
git worktree list                    # 잔여물 없음 확인
tmux list-windows -a                 # 잔여 창 없음 확인
```

**git-crypt 경로(AC-31)는 스모크 테스트하지 않는다.** `zambaguni-front` worktree 생성은
의존성 설치로 개당 1~2GB를 쓰고 업무 저장소에 부작용을 남긴다. 문서 검토로 판정하고
이 제약을 보고서에 한계로 기록한다. 다만 R4.6의 근거가 되는 래퍼의 3단계 판별 로직은
`zambaguni-front/scripts/create-worktree.sh:82-98`을 직접 읽어 확인했다.

## Decisions

### D1. 세션 우선순위에서 저장값이 모드 기본값보다 우선한다

이슈 #35는 "명시값 > 모드 기본값 > 저장 세션 > 1-main"을 권장했다. 이를 뒤집어
"명시값 > 저장 세션 > 모드 기본값 > 1-main"으로 채택했다.

근거: 저장값은 사용자가 `move-window-to-session`으로 **직접 창을 옮긴 행동의 기록**이고,
모드 기본값은 단순 관습이다. 관습이 기록을 덮으면 현행 "예외 1"이 막으려던 실패 —
의도적으로 옮긴 창을 조용히 되끌고 오는 것 — 가 `2-review` 이름으로 재발한다. 사용자가
2026-08-27 확인에서 이 순서를 선택했다. 신규 worktree에는 저장값이 없으므로 PR 모드
기본값 `2-review`가 정상 동작한다(AC-46이 실측).

### D2. PR 참조는 표지가 있을 때만 인식한다

표지 없는 맨 숫자(`1313`)를 PR로 해석하지 않는다. GitHub는 이슈와 PR이 번호 공간을
공유하므로 맨 숫자를 PR로 단정하면 이슈 번호를 PR 번호로 오해해 엉뚱한 브랜치를
체크아웃할 수 있다. 전체 URL, `owner/repo#N`, 또는 숫자 앞뒤에 PR 표지가 있는 자연어만
PR 모드로 간다. 자연어 케이스에서 "표지"가 판정 기준이라는 점이 R1.5의 맨 숫자 금지와
모순되지 않는 이유다 — 금지 대상은 **표지 없는** 맨 숫자다.

### D3. PR 모드에서 positional 브랜치명을 생략한다

`workmux add --help` 실측: "`[BRANCH_NAME]` ... When used with `--pr`, this becomes the
custom local branch name". positional을 주면 PR head 브랜치 대신 그 이름으로 로컬
브랜치가 생기므로, PR head를 그대로 쓰려면 생략해야 한다.

### D4. 두 원본은 수동 유지하고 `diff`로 검증한다

심볼릭 링크는 Claude 전용 frontmatter 때문에 불가능하고, 생성 스크립트는 이번 변경
범위를 넘어선다. Architecture 절의 대안 비교 참조.

### D5. workmux 버전 표기 불일치를 `dot_claude` 쪽으로 통일한다

이슈 #35는 두 원본이 frontmatter만 다르다고 전제했으나 실측에서 `dot_agents:43`
"0.1.233 실측"과 `dot_claude:46` "0.1.233 확인·0.1.248 재확인"이 다르다. 후자가 현재
설치된 버전(0.1.248)까지 재확인한 더 정확한 서술이므로 그쪽으로 통일한다.

### D6. 래퍼는 고치지 않고 스킬이 전제를 보장한다

래퍼의 3단계 판별 중 "둘 다 없으면 현재 HEAD에서 새 브랜치"는 브랜치 모드에서는 올바른
동작이다(새 기능 브랜치를 만드는 정상 경로). 문제는 PR 모드에서 head 브랜치가 `origin`에
없을 때(fork PR)뿐이다.

- **대안 A — 래퍼에 `--pr` 지원 추가**: 다른 저장소(zambaguni-front)를 고쳐야 하고,
  이 작업의 변경 범위(#35가 지정한 3개 파일) 밖이다. 탈락.
- **대안 B — 스킬이 호출 전 fetch로 전제를 보장(채택)**: `refs/pull/{N}/head`를 로컬
  브랜치로 가져오면 래퍼의 2번 경로(로컬 브랜치 존재)로 확정된다. 래퍼를 건드리지 않고,
  같은 저장소 PR과 fork PR을 동일하게 처리한다.
- **대안 C — PR 모드에서 git-crypt 저장소를 미지원**: #28의 요구를 포기하게 되므로 탈락.

사후 검증(R6.8)을 함께 두어 전제 보장이 실패했을 때도 조용한 성공이 되지 않게 한다.

### D7. 기존 worktree는 중단이 아니라 창 처리로 분기한다

이슈 #28은 "PR head 브랜치가 이미 다른 worktree에서 사용 중이면 ... 중단한다"고 썼다.
그 의도는 **중복 worktree나 별칭 브랜치를 만들지 말라**는 것이지, 창을 열지 말라는 것이
아니다. 문자 그대로 전체 중단으로 읽으면 PR 리뷰용 창을 두 번째부터 영영 열 수 없어
Goal 2와 R7 전체가 무의미해진다. 따라서 "생성 단계만 건너뛰고 R7 창 처리로 진행"으로
확정했다(R4.3). 흐름도의 분기 순서도 이에 맞췄다.

### D8. 스모크 테스트 대상은 dotfiles PR #31이다

PR 번호(31)와 head 브랜치 이슈 번호(30)가 달라 R5.3을 판별하는 가용 케이스다. 2026-08-27
실측으로 `state=OPEN`이고 head 브랜치가 원격에 살아 있음을 확인했다. PR #32는 head
브랜치에 숫자 접두사가 없어 이 구분을 검증하지 못하므로 대체 대상이 아니다. 실행
시점에 #31이 닫혔을 경우의 대체 계획은 Test strategy 3층에 기술했다.

### D9. git-crypt 경로는 문서 검토 + 래퍼 소스 확인으로 검증한다

실제 검증은 업무 저장소에 1~2GB 규모 부작용을 남긴다. 대신 R4.6의 근거가 되는 래퍼의
브랜치 판별 로직을 소스에서 직접 읽어 확인했고(`scripts/create-worktree.sh:82-98`), 그
실측을 Problem and context에 기록했다. 이 한계를 보고서에 명시한다.

### 미해결 사항

없다. 모든 중대 결정이 위에 해소되어 있다.
