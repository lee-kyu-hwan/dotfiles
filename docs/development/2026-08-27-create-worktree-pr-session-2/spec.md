# Quality Goal Specification

- Task ID: 20260827T111202Z-28-35-create-worktree-스킬-재실행-pr-링크-입력-시-ea9373b7
- Mode: standard
- Status: SPEC_REVIEW (round 2)
- Created: 2026-08-27T11:12:02Z
- Updated: 2026-08-27T11:12:02Z
- Source goal: #28 #35 create-worktree 스킬 재실행 — PR 링크 입력 시 2-review 세션에 PR 번호 윈도우를 생성하고 대상 세션을 직접 지정하도록 확장한다. SPEC-011(창 탐지 규칙)과 SPEC-012({이름} 정의)를 Spec 초안에 선반영한다

## Problem and context

`create-worktree` 스킬은 현재 브랜치명 하나만 입력으로 받고, workmux 윈도우를 항상
`1-main` 세션에 연다. 두 가지 한계가 실제 사용에서 드러났다.

**한계 1 — PR 리뷰용 worktree를 PR 번호로 식별할 수 없다.** 현행 규칙은 브랜치명 맨
앞의 숫자만 이슈 번호로 인식해 `{이슈번호}-{짧은이름}` 윈도우를 만든다
(`dot_claude/skills/create-worktree/SKILL.md:145-147`). PR head 브랜치명에는 보통 PR
번호가 아니라 원 이슈 번호가 들어 있다. 이 저장소의 PR #31이 그 사례다 — head 브랜치가
`30-enhancement/tmux-open-pr-shortcut`이라 현행 규칙으로는 창 이름이 `30-...`이 되어
PR #31을 가리키지 못한다.

**한계 2 — 대상 세션을 지정할 수 없어 불필요한 이동이 발생한다.** 이슈 #35가 기록한
실제 사례에서 사용자가 `2-review`를 명시했음에도 현행 스킬은 `1-main`에 창을 연 뒤
`move-window-to-session` 전체 절차를 밟아야 했다. 처음부터
`--parent-session 2-review`를 쓰면 전부 불필요한 작업이다.

**선행 실행의 결과.** 같은 목표로 2026-08-27에 수행한 quality-goal 실행이
`NEEDS_REDESIGN`(`REVIEW_LIMIT_EXHAUSTED:spec`)으로 종료됐다. 산출물은
`docs/development/2026-08-27-create-worktree-pr-session/`에 있다. 종료 사유는 설계
결함이 아니라 두 개의 미정의 구간이었다 — 창 탐지 방법과 workmux git config 키의
`{이름}`. 이 Spec은 그 둘을 실측 근거와 함께 처음부터 채운다(R2.0, R7.1).

### 측정된 사실 (2026-08-27 실측)

| 사실 | 관찰 명령 | 결과 |
|---|---|---|
| workmux 버전 | `workmux --version` | `workmux 0.1.248` |
| `--pr` 플래그 | `workmux add --help` | `--pr <NUMBER\|URL>` |
| `--pr`와 positional | `workmux add --help` | "`[BRANCH_NAME]` ... When used with `--pr`, this becomes the custom local branch name" |
| `add`의 이름·세션 플래그 | `workmux add --help` | `--name`, `--target-name`, `--parent-session`, `--dry-run` 모두 존재 |
| `workmux open`의 `--pr` 부재 | `workmux open --help` | `--pr` 없음. `--target-name`, `--parent-session`은 있음 |
| `workmux list --json` | `workmux list --help` | `--json  Output as JSON` |
| JSON 필드 | `workmux list --json` | `handle`, `path`, `branch`, `is_open`, `mode`, `is_main`, `project` |
| tmux 세션 | `tmux list-sessions -F '#{session_name}'` | `1-main`, `2-review`, `3-personal`, `4-eslint`, `5-quick` |
| dotfiles git-crypt | `git config --get filter.git-crypt.smudge` | 값 없음. 래퍼도 없음 |
| zambaguni-front git-crypt | 같음 | `"git-crypt" smudge`. 래퍼 존재 |
| 현재 저장소 판정 | `gh repo view --json owner,name -q '.owner.login + "/" + .name'` | `lee-kyu-hwan/dotfiles` |
| PR #31 | `gh pr view 31 --json state,headRefName,headRefOid` | `OPEN`, `30-enhancement/tmux-open-pr-shortcut`, `9cfc6267ced574945814536710cf1019a37dc354` |
| PR #31 원격 head | `git ls-remote origin '30-enhancement/tmux-open-pr-shortcut'` | `9cfc6267...` |
| PR #31 pull ref | `git ls-remote origin 'refs/pull/31/head'` | `9cfc6267...` 동일 |
| PR #32 | `gh pr view 32 --json state,headRefName` | `OPEN`, `feat/codex-playwright-e2e-profile` (숫자 접두사 없음) |
| tmux 서버 부재 | `tmux -L quality-goal-nonexistent-socket list-sessions` | exit 1 + `error connecting to ...` |
| 없는 세션 판정 | `... \| grep -qxF -- 'definitely-not-a-session'` | exit 1 |
| `has-session` 접두사 함정 | `tmux has-session -t 2` / `-t 2-rev` | 둘 다 exit 0 (그런 세션 없음) |
| 같은 조건 `grep -qxF` | `... \| grep -qxF -- '2-rev'` | exit 1 (올바름) |
| `quick_validate.py` (dot_agents) | 아래 "frontmatter 검증" | `Skill is valid!`, exit 0 |
| `quick_validate.py` (dot_claude) | 같음 | `Unexpected key(s) ... argument-hint, user-invocable`, **exit 0** |
| 현재 `description` | `sed -n 3p` 두 파일 | 양쪽 동일: "Use when creating a new git worktree for a branch to work on in isolation from the main workspace" |

### `workmux add --pr`의 실제 산출물 (dry-run 실측)

`--dry-run`은 영속 변경 없이 결과를 보여 준다. PR #31에 대해 실행한 결과다.

```
$ workmux add --pr 31 --dry-run
PR #31: feat(tmux): prefix + P 로 현재 브랜치의 PR 을 브라우저에서 연다
Branch: 30-enhancement/tmux-open-pr-shortcut
Worktree: /Users/lee-kyu-hwan/code/dotfiles__worktrees/30-enhancement-tmux-open-pr-shortcut
Base:     origin/30-enhancement/tmux-open-pr-shortcut
Target:   30-enhancement-tmux-open-pr-shortcut (window)
```

여기서 두 가지가 확정된다.

1. **handle은 브랜치 슬러그다** — `30-enhancement/tmux-open-pr-shortcut`의 `/`를 `-`로
   바꾼 `30-enhancement-tmux-open-pr-shortcut`. 이 저장소에는 `worktree_naming` 설정이
   없으므로 기본 전략이 적용된 결과다.
2. **`--target-name`을 주면 handle과 창 이름이 갈라진다** — handle은 위 그대로
   `30-enhancement-tmux-open-pr-shortcut`이지만 창 이름은 `31-tmux-open-pr-shortcut`이
   된다. 이것이 R7.1이 창 이름으로 매칭하면 안 되는 이유의 **PR 모드 직접 사례**다.

handle이 브랜치에서 파생될 수 있다는 사실은 AC-9의 판정 기준에도 영향을 준다 —
"브랜치에서 유추한 키 조회가 실패해야 한다"는 조건은 이 경우 성립하지 않는다. AC-9은
그 대신 "실제로 존재하는 유일한 키가 handle 기준 키인지"로 판정한다.

### 워크트리 식별자 실측 (R2.0의 근거)

이 저장소의 살아 있는 worktree 하나가 이름 유추의 위험을 보여준다. handle이 항상
브랜치에서 파생되는 것은 **아니다**.

```
$ workmux list
BRANCH                                AGE  AGENT  MUX  UNMERGED  PATH
chore/post-upgrade-skill-maintenance  2d   -      ✓    -         ../dotfiles__worktrees/feat-quality-goal-skill
```

디렉터리명(`feat-quality-goal-skill`)과 브랜치명(`chore/post-upgrade-skill-maintenance`)이
전혀 다르다. 실제 git config 키는 디렉터리명 쪽이다.

```
$ git -C ../dotfiles__worktrees/feat-quality-goal-skill config --get-regexp '^workmux\.worktree\.'
workmux.worktree.feat-quality-goal-skill.mode window
workmux.worktree.feat-quality-goal-skill.window-session 3-personal

$ git -C ... config --get 'workmux.worktree.post-upgrade-skill-maintenance.window-session'
(출력 없음, exit 1)
```

`move-window-to-session/SKILL.md:104-108`은 이 상황을 "틀린 이름을 넘겨도 git은
**에러 없이** 새 섹션을 만들어 버린다"고 경고한다 — 읽기는 빈 값을 주고, 쓰기는 조용히
쓰레기 섹션을 만들며 진짜 키는 옛 값을 유지한다.

`workmux list --json`은 이 이름을 `handle`로 직접 준다.

```json
{ "handle": "feat-quality-goal-skill",
  "path": "/Users/.../dotfiles__worktrees/feat-quality-goal-skill",
  "branch": "chore/post-upgrade-skill-maintenance",
  "is_open": true, "mode": "window", "is_main": false }
```

**두 사례를 합치면**: handle은 브랜치 슬러그일 수도(dry-run 사례) 완전히 다를 수도(위
사례) 있다. 어느 쪽이든 유추하지 말고 `handle`을 읽어야 한다는 결론은 같다.

### 창 위치 실측 (R7.1의 근거)

`is_open: true`인 위 worktree의 실제 창을 이름에 의존하지 않고 찾을 수 있다.

```
$ WT=/Users/lee-kyu-hwan/code/dotfiles__worktrees/feat-quality-goal-skill
$ tmux list-panes -a -F '#{session_name}:#{window_index} #{window_id} #{pane_id} #{pane_current_path}' \
    | awk -v wt="$WT" '$4 == wt || index($4, wt"/") == 1'
3-personal:2 @19 %60 /Users/lee-kyu-hwan/code/dotfiles__worktrees/feat-quality-goal-skill
```

`workmux list --json`의 `is_open`, git config의 `window-session`(`3-personal`), pane
경로 매칭 결과가 모두 일치한다. `window_id`(`@19`)와 `pane_id`(`%60`)는 `move-window`로
바뀌지 않는 안정 식별자다(`move-window-to-session/SKILL.md:32-39`).

### 래퍼 스크립트의 브랜치 판별

`zambaguni-front/scripts/create-worktree.sh:82-98` 실측. 래퍼는
`git fetch --prune origin` 후 3단계로 판별한다.

1. `refs/remotes/origin/{BRANCH}`가 있으면 → tracking 브랜치 모드
2. `refs/heads/{BRANCH}`가 있으면 → 기존 로컬 브랜치 모드
3. **둘 다 없으면 → 현재 HEAD 기준으로 새 브랜치 생성 (`-b`)**

3번이 결정적이다. 같은 저장소 PR이면 래퍼 자신의 fetch가 `origin/{head}`를 만들어 1번이
적용되지만, **fork PR의 head 브랜치는 `origin`에 없다.** `git fetch --prune origin`은
`refs/pull/*/head`를 가져오지 않으므로 3번으로 떨어져 **PR 내용이 전혀 없는 빈 브랜치를
현재 HEAD에서 만들고** 겉보기에 성공한 worktree를 남긴다. 이 실패는 조용하다.

## Goals

1. PR 참조를 입력하면 PR 번호로 식별되는 리뷰용 worktree 윈도우를 만든다. 창 이름은
   PR head 브랜치의 이슈 번호가 아니라 PR 번호를 쓴다.
2. 대상 tmux 세션을 호출 시 지정할 수 있게 하고, 지정된 세션에 처음부터 직접 창을
   만들어 `1-main` 경유 이동을 없앤다.
3. 세션 선택 규칙을 결정적 우선순위로 일반화하고, Claude와 Codex 두 원본이 동일하게
   읽게 한다.
4. worktree 식별과 창 탐지를 이름 유추가 아닌 안정 식별자로 규정해, 잘못된 git config
   키와 중복 창 생성을 막는다.
5. 현행 스킬의 기존 규칙을 회귀 없이 보존한다. 보존 대상은 R9.6에 열거하고 AC-56으로
   검증한다.
6. 유령 세션, 저장소 불일치, 브랜치 충돌, PR 내용이 없는 빈 worktree, 사라진 저장
   세션을 부작용이 생기기 전에 차단하거나 복구 경로를 제공한다.

## Non-goals

- tmux 세션 자동 생성. 선택 세션이 없으면 중단하거나 확인받는다(R2.5).
- workmux session mode 전환(`--session`, `--mode session`)이나 pane 레이아웃 변경.
- `move-window-to-session` 스킬 내부 동작·입력 계약 변경. 그 스킬이 **받아들이는 형식
  으로** 인자를 맞춰 호출한다(R7.5).
- `remove-worktree` 스킬 변경.
- 대상 저장소의 `scripts/create-worktree.sh` 래퍼 수정. 3단계 판별은 그대로 두고
  스킬이 호출 전에 전제를 보장한다.
- workmux의 `worktree_naming` 설정 변경. handle 파생 규칙은 workmux에 맡기고 읽기만
  한다.
- 개발 서버나 에이전트 자동 실행.
- PR 리뷰 자체의 수행.
- `review/pr-{번호}` 같은 별칭 브랜치 생성.
- GitHub 쓰기 작업(코멘트, 라벨, 상태 변경).
- `workmux` 자체의 기능 추가나 버그 수정.
- 선행 실행 산출물(`docs/development/2026-08-27-create-worktree-pr-session/`) 수정.
  baseline의 initial dirty path로 기록되어 보존된다.
- quality-goal 스킬 자체의 결함(#43, #44) 수정. 별도 이슈로 추적된다.

## Requirements

### R1. 입력 규격

- **R1.1** 첫 번째 positional 인자는 브랜치명 또는 PR 참조이며 필수다. 비어 있으면
  사용자에게 물어본다.
- **R1.2** 두 번째 positional 인자는 정확한 tmux 세션명이며 선택이다.
- **R1.3** 세 번째 이상의 positional 인자가 오면 추측하지 말고 사용법을 안내하고
  중단한다. positional 형태 호출에만 적용된다(R1.6 참조).
- **R1.4** PR 모드는 다음 형태에서만 자동 선택된다.
  - 전체 GitHub PR URL: `https://github.com/{owner}/{repo}/pull/{번호}`
  - `{owner}/{repo}#{번호}` 형식
  - 자연어 문장에서 숫자 앞뒤에 PR 표지가 있는 경우 ("PR 1313", "1313번 PR",
    "pull request 1313")
- **R1.5** 표지 없는 맨 숫자(`1313`)는 PR 참조로 보지 않는다. GitHub는 이슈와 PR이
  번호 공간을 공유하므로 맨 숫자를 PR로 단정하면 엉뚱한 대상을 체크아웃할 수 있다.
  표지가 없으면 브랜치 모드로 해석하거나, 브랜치로도 해석되지 않으면 확인한다.
- **R1.6** 자연어 호출은 `(브랜치명|PR참조, 대상세션)` 2-튜플로 환원한다.
  - 첫 요소: 문장에서 발견된 브랜치명 또는 R1.4 형태의 PR 참조. 두 개 이상이면 중단
    하고 확인한다.
  - 둘째 요소: 문장에서 발견된 tmux 세션명. 두 개 이상이면 중단하고 확인한다.
  - 환원 결과가 2-튜플을 넘지 않으므로 R1.3의 중단은 자연어 호출에서 발동하지 않는다.
- **R1.7** 세션명을 접두사로 보정하거나 존재하는 세션 목록에서 추측하지 않는다.
- **R1.8** Claude frontmatter의 `argument-hint`는
  `<branch-name|pr-ref> [target-session]`로 갱신한다.

### R2. worktree 식별자와 세션 선택

- **R2.0 워크트리 식별자 정의.** `workmux.worktree.{이름}.window-session`을 비롯한
  모든 workmux git config 키의 `{이름}`은 **workmux worktree handle**이며 다음으로
  얻는다.

  ```bash
  workmux list --json    # 각 항목의 handle 필드 (= path 필드의 basename)
  ```

  **브랜치명이나 tmux 창 이름에서 유추하면 안 된다.** handle은 브랜치 슬러그와 같을
  수도(`workmux add --pr 31 --dry-run` 실측: `30-enhancement-tmux-open-pr-shortcut`)
  전혀 다를 수도(이 저장소 실측: 디렉터리 `feat-quality-goal-skill` / 브랜치
  `chore/post-upgrade-skill-maintenance`) 있어 규칙으로 예측할 수 없다. 창 이름은
  `--target-name`으로 바뀌므로 더더욱 근거가 못 된다. 틀린 키를 넘겨도 git은 오류 없이
  새 섹션을 만들고 진짜 키는 옛 값을 유지하므로
  (`move-window-to-session/SKILL.md:104-108`), 읽기는 빈 값을 주고 쓰기는 조용히
  실패한다. 그 결과 R2 우선순위 2가 빈 값으로 떨어져 R2.1이 막으려던 실패가 재발한다.

  `workmux list --json`을 쓸 수 없으면 worktree 절대경로의 basename을 폴백으로 쓰되,
  `path` 필드와 대조해 확인한다. 대조할 수단조차 없으면 중단한다.

세션(`SELECTED_SESSION`)은 다음 순서로 결정한다.

1. 사용자가 이번 호출에서 명시한 대상 세션
2. 기존 worktree의 `workmux.worktree.{handle}.window-session` 값이 `^[0-9]+-.+$`를
   만족하고 **그 세션이 실제로 존재할 때** 그 값 (R2.5)
3. 입력 모드 기본값 — PR 모드이면 `2-review`
4. 전역 기본값 `1-main`

- **R2.1** 저장값이 모드 기본값보다 우선한다. 저장값은 사용자가 직접 창을 옮긴 행동의
  기록이고 모드 기본값은 관습이다. 관습이 기록을 덮으면 현행 "예외 1"이 막으려던
  실패가 `2-review` 이름으로 재발한다.
- **R2.2** 저장값이 `^[0-9]+-.+$`를 만족하지 않으면 레거시 값으로 보고 우선순위 2에서
  제외하며, 선택된 세션으로 갱신한다. 판정은 셸 glob(`[0-9]*-*`)이 아니라 정규식으로
  한다 — glob의 첫 `*`는 임의 문자열이라 `1legacy-session`이나 `1-`가 통과한다.
- **R2.3** 선택 세션이 확정되기 전에는 어떤 workmux 명령도 실행하지 않는다.
- **R2.4** 명시 세션(우선순위 1)이 유효한 저장값(우선순위 2)을 덮은 경우, 창을 연 뒤
  `workmux.worktree.{handle}.window-session`이 명시 세션을 가리키는지 확인하고 다르면
  갱신한다. 갱신하지 않으면 다음번 세션 미명시 호출이 옛 세션으로 되돌아간다.
- **R2.5 사라진 저장 세션의 복구.** 저장값이 형식은 유효하나 그 세션이 지금 존재하지
  않으면(닫혔거나 이름이 바뀜) 막다른 길이 되지 않게 한다. 우선순위 2를 건너뛰고
  다음을 수행한다.

  1. 저장값이 가리키는 세션이 사라졌음을 그 값과 함께 사용자에게 알린다.
  2. 우선순위 3·4로 결정되는 세션을 제시하고 확인받는다.
  3. 확인되면 그 세션으로 진행하고 `window-session`을 갱신한다.
  4. 세션을 자동 생성하지 않는다.

  이 규칙이 없으면 R3.5의 무조건 중단이 매 호출마다 반복되어 자기 교정 경로가 없다.
  스킬이 `window-session`을 직접 쓰는 것은 R2.2·R2.4·R2.5·R8.2 네 곳뿐이다.

### R3. tmux 세션 검증

- **R3.1** `tmux list-sessions -F '#{session_name}'`을 단독 실행해 종료 코드를 먼저
  확인한다.
- **R3.2** exit 1과 `error connecting to ...`이면 tmux 서버 부재로 보고하고 중단한다.
  "세션이 없다"와 구분한다.
- **R3.3** 목록 조회 성공 후 `grep -qxF -- "$SELECTED_SESSION"`으로 전체 문자열 일치를
  확인한다.
- **R3.4** `has-session -t`를 쓰지 않는다. 접두사 매칭 때문에 `has-session -t 2`와
  `-t 2-rev`가 모두 exit 0이다(실측).
- **R3.5** 선택 세션이 없으면 자동 생성하지 않는다. 저장값에서 온 경우는 R2.5의 복구
  경로를 타고, 사용자가 명시한 경우는 오타 가능성을 알리고 중단한다. workmux는 존재
  하지 않는 `--parent-session` 값을 오류 없이 받아 세션을 만들고 git config에 영구
  저장하므로, 이 검사가 유일한 안전망이다.
- **R3.6** 현행의 "`1-main` 존재 확인"은 "선택 세션 존재 확인"으로 일반화한다.

### R4. PR 참조 해석

- **R4.0 저장소 판정.** PR 참조에서 `{owner}/{repo}`를, 현재 작업 대상에서 현재
  저장소를 각각 확정한다. 둘 다 이름이 있어야 R4.2의 비교가 성립한다.

  | 입력 형태 | `{owner}/{repo}` 출처 |
  |---|---|
  | 전체 PR URL | URL 경로의 `{owner}/{repo}` |
  | `{owner}/{repo}#{번호}` | 문자열 그대로 |
  | 표지 있는 자연어 (`PR 1313`) | 명시되지 않았으므로 **현재 저장소로 간주** |

  현재 저장소는 다음으로 얻는다.

  ```bash
  gh repo view --json owner,name -q '.owner.login + "/" + .name'
  ```

  이 명령이 실패하면 `git remote get-url origin`을 폴백으로 쓰고 `{owner}/{repo}`를
  파싱한다. 둘 다 실패하면 저장소를 확정할 수 없으므로 중단한다.
- **R4.1** PR 번호, head 브랜치명, head 커밋 OID, 상태를 조회한다.

  ```bash
  gh pr view {번호} --repo {owner}/{repo} --json number,state,headRefName,headRefOid
  ```

  조회 필드는 소비되는 것만 요청한다 — `number`·`headRefName`·`headRefOid`는 이름
  파생과 검증에, `state`는 R4.7에 쓰인다. base 저장소는 R4.0에서 이미 확정되므로 별도
  필드가 필요 없고, fork 여부는 R4.6의 pull ref가 균일하게 처리한다.
- **R4.2** R4.0의 `{owner}/{repo}`와 현재 저장소가 다르면 중단한다. 자연어 형태는
  현재 저장소로 간주되므로 이 비교가 자동으로 통과한다.
- **R4.3** PR head 브랜치의 worktree가 이미 있으면 **새 worktree를 만들지 않는다.**
  별칭 브랜치도 만들지 않는다. 생성 단계만 건너뛰고 R7의 창 처리로 넘어간다. 전체
  작업 중단이 아니다.
- **R4.4** 같은 이름의 로컬 브랜치가 있는데 R4.1의 head OID와 다른 커밋을 가리키면
  덮어쓰지 않고 중단한다.
- **R4.5** `gh`가 없거나 인증되지 않았거나 조회가 실패하면 보고하고 중단한다. 추측
  하지 않는다.
- **R4.6 PR head 브랜치 확보.** worktree를 새로 만들기 전에 PR head 커밋이 로컬에서
  `{head브랜치명}`으로 도달 가능함을 보장한다. 래퍼는 브랜치가 로컬과 `origin` 양쪽에
  없으면 현재 HEAD에서 빈 브랜치를 만들므로(래퍼 82-98행), 이 보장 없이 래퍼를 부르면
  PR 내용이 없는 worktree가 조용히 생긴다.

  ```bash
  # 로컬 브랜치가 이미 있으면 R4.4의 OID 비교로 판정이 끝나 있다.
  # 없을 때만 pull ref에서 가져온다. fork PR도 이 ref로 동일하게 처리된다.
  git fetch origin "refs/pull/{PR번호}/head:{head브랜치명}"
  git rev-parse --verify "refs/heads/{head브랜치명}"   # == R4.1의 headRefOid
  ```

  fetch 실패나 OID 불일치면 중단하고 래퍼를 부르지 않는다. 래퍼 없는 경로는
  `workmux add --pr`가 체크아웃을 직접 하므로 사전 fetch 대신 사후 검증(R6.8)으로 같은
  보장을 얻는다.
- **R4.7 PR 상태 처리.** `state`가 `OPEN`이 아니면(`CLOSED`, `MERGED`) 알리고 계속할지
  확인한다. 자동 중단하지 않는다 — 머지된 PR을 사후에 들여다보는 것은 정당한 용도다.
  다만 head 브랜치가 삭제되었을 수 있으므로 R4.6의 fetch 실패 가능성을 함께 안내한다.

### R5. 윈도우 이름 파생

- **R5.1** 짧은 이름은 브랜치명(PR 모드에서는 PR head 브랜치명)에서 마지막 `/`까지를
  제거한 부분이다. `392-feat/add-partner-chat-enabled` → `add-partner-chat-enabled`.
- **R5.2** 브랜치 모드에서 이슈 번호는 브랜치명 맨 앞의 숫자 또는 `ZF-숫자`만 인식한다.
- **R5.3** PR 모드의 윈도우 이름은 `{PR번호}-{짧은이름}`이다. PR head 브랜치가 이슈
  번호로 시작하더라도 PR 번호를 쓴다.
- **R5.4** 브랜치 모드에서 이슈 번호가 없으면 `--target-name`을 생략한다.
- **R5.5** workmux가 target name을 소문자로 정규화하므로, 안내와 재사용에 쓰는 이름은
  정규화된 소문자다.
- **R5.6** 창 이름 충돌 시 재시도 이름은 모드별로 다르다.
  - 브랜치 모드: `{repo명}-{짧은이름}` (현행 규칙 유지)
  - PR 모드: `{PR번호}-{repo명}-{짧은이름}` — PR 번호를 보존한다.

### R6. 생성·오픈 경로

- **R6.1** 경로 분기는 저장소 루트(`git rev-parse --show-toplevel`) 기준으로
  `scripts/create-worktree.sh` 존재 여부로 판정한다. 상대 경로로 판정하면 서브디렉터리
  나 기존 worktree 안에서 부를 때 false가 된다.
- **R6.2** git-crypt 저장소에서 `workmux add`를 쓰지 않는다. PR 모드도 마찬가지다.
- **R6.3** 래퍼 없는 저장소의 PR 모드는 positional 브랜치명을 생략한다.

  ```bash
  workmux add --pr {PR참조} \
    --target-name {PR번호}-{짧은이름} \
    --parent-session {선택세션}
  ```

  positional을 주면 그것이 커스텀 로컬 브랜치명이 되어 PR head 브랜치가 쓰이지 않는다.
  `--target-name`과 `--parent-session`이 `--pr`와 함께 쓸 수 있음은 `workmux add --help`
  실측으로 확인했다.
- **R6.4** 래퍼 있는 저장소의 PR 모드는 R4.6으로 head 브랜치를 확보한 뒤 실행한다.

  ```bash
  ./scripts/create-worktree.sh {head브랜치명}
  workmux open {handle} \
    --target-name {PR번호}-{짧은이름} \
    --parent-session {선택세션}
  ```

- **R6.5** 래퍼가 실패하면 종료 코드를 확인해 중단하고 `workmux open`으로 넘어가지
  않는다. 확인 프롬프트를 `-y`나 `yes |`로 우회하지 않는다. 실행 권한이 없으면 경로를
  바꾸지 말고 오류로 보고한다.
- **R6.6** 모든 `workmux add`/`workmux open` 예시가 고정 `1-main`이 아니라 선택 세션
  변수를 쓴다.
- **R6.7** `--parent-session` 미지원 조합(session mode, 샌드박스 안, `--count`,
  `--foreach`, 여러 `--agent`, stdin)에서는 플래그를 생략한다.
- **R6.8 PR worktree 내용 검증.** 생성 직후 worktree의 HEAD가 R4.1의 `headRefOid`와
  같은지 확인한다. 다르면 PR 내용이 없는 worktree이므로 성공으로 보고하지 않는다.
- **R6.9 경로·handle 확보.** 생성 후 worktree 경로와 handle을 명령 출력에서 얻는다.
  경로나 이름을 추측하지 않는다.
  - 래퍼 경로: 래퍼가 출력하는 worktree 절대경로를 쓴다. handle은
    `workmux list --json`에서 `path`가 그 경로와 같은 항목의 `handle`이다.
  - `workmux add --pr` 경로: 생성 후 `workmux list --json`에서 `branch`가 PR head
    브랜치와 일치하는 항목의 `handle`과 `path`를 읽는다. workmux의 디렉터리 명명은
    `worktree_naming` 설정에 좌우되므로 규칙으로 추정하지 않는다.
  - 실행 전 `workmux add ... --dry-run`으로 예상 경로·handle을 미리 볼 수 있다.
    영속 변경이 없으므로 확인용으로 쓴다.
- **R6.10 git-crypt 필터가 있으나 래퍼가 없는 저장소.** 현행 규칙을 유지한다 —
  `filter.git-crypt.smudge` 값이 있는데 `scripts/create-worktree.sh`가 없으면
  사용자에게 확인받고 진행한다(`dot_claude/skills/create-worktree/SKILL.md:106`).
  R6.1의 분기가 래퍼 존재 여부만 보므로, 이 확인 없이는 R6.2가 금지하는
  `workmux add` 경로로 조용히 들어간다.

### R7. 기존 worktree 상태별 동작

- **R7.0 worktree 존재·경로 판정.** 세션 선택(R2)보다 먼저 대상 브랜치의 worktree
  존재 여부와 경로를 확정한다. 저장 세션을 읽으려면 handle이 필요하고, handle은
  `workmux list --json`에서 경로로 찾기 때문이다.

  ```bash
  git worktree list --porcelain   # branch refs/heads/{브랜치명} 항목의 worktree 경로
  workmux list --json             # 그 경로와 일치하는 항목의 handle
  ```

- **R7.1 창 열림 여부와 위치 판정.** 창이 열려 있는지, 어느 세션·어느 창인지를
  **이름이 아닌 안정 식별자로** 판정한다. 3단계를 모두 쓴다.

  1. **열림 여부** — `workmux list --json`에서 해당 handle 항목의 `is_open`.
  2. **세션** — `git config --get workmux.worktree.{handle}.window-session`.
  3. **실제 창·pane** — 창 이름에 의존하지 않고 pane의 작업 디렉터리로 매칭한다.

     ```bash
     tmux list-panes -a -F '#{session_name}:#{window_index} #{window_id} #{pane_id} #{pane_current_path}' \
       | awk -v wt="{worktree절대경로}" '$4 == wt || index($4, wt"/") == 1'
     ```

     실측 결과 `3-personal:2 @19 %60 {worktree경로}`를 정확히 짚었다.

  **창 이름으로 매칭하지 않는다.** 창 이름은 `--target-name`으로 결정되며 모드마다
  파생 규칙이 다르다. PR #31 dry-run 실측이 직접 사례다 — handle은
  `30-enhancement-tmux-open-pr-shortcut`인데 PR 모드 창 이름은
  `31-tmux-open-pr-shortcut`이다. 이름으로 찾으면 열려 있는 창을 놓치고 R7.3의 중복
  창 금지가 조용히 실패한다.

  **확보한 `window_id`(`@N`)와 `pane_id`(`%N`)를 이후 조작의 기준으로 삼는다.** 둘은
  `move-window`로 바뀌지 않는 반면 `session:index`는 바뀐다
  (`move-window-to-session/SKILL.md:32-39`).

  **매칭기의 한계.** 위 `awk`는 공백으로 필드를 나누므로 **worktree 경로에 공백이 있으면
  동작하지 않는다.** 경로에 공백이 있으면 이 매칭을 신뢰하지 말고 아래 불일치 처리로
  넘어간다. pane의 cwd는 사용자가 `cd`로 바꿀 수도 있어 완전하지 않다.

  **불일치 처리.** `is_open`이 참인데 매칭 0건이면(경로에 공백, 또는 사용자가 `cd` 함)
  추측하지 말고 `window-session`이 가리키는 세션의 창 목록을 보여 주고 확인받는다.
  매칭 2건 이상이면 그대로 보고하고 확인받는다.

- **R7.2** 창이 닫혀 있으면(`is_open`이 거짓) 선택 세션으로 직접 연다.
- **R7.3** 창이 열려 있고 선택 세션과 같은 세션이면 중복 창을 만들지 않고 기존 위치를
  안내한다.
- **R7.4** 창이 열려 있고 다른 세션이며 사용자가 대상을 명시하지 않았으면 기존 위치를
  존중한다(R2 우선순위 2가 이미 그 값을 선택하므로 R7.3으로 귀결된다).
- **R7.5 열린 창의 명시적 이동.** 창이 열려 있고 다른 세션이며 사용자가 대상을
  명시했으면, `workmux open`으로 재구성하지 않고 `move-window-to-session` 스킬을 쓴다.
  살아 있는 pane과 에이전트 상태를 보존하기 위해서다.

  그 스킬의 입력 계약은 `<윈도우이름|세션:번호> <대상세션>`이므로
  (`move-window-to-session/SKILL.md:21`), R7.1이 확보한 `window_id`를 **그대로 넘기지
  않는다.** 호출 직전에 `window_id`로 현재 위치를 해석해 `세션:번호` 형태로 넘긴다.

  ```bash
  SRC=$(tmux display-message -p -t "{window_id}" '#{session_name}:#{window_index}')
  # move-window-to-session 에 넘기는 인자: "$SRC" "{선택세션}"
  ```

  `window_id`로 해석하는 이유는 그 사이 다른 창이 열리고 닫혀 번호가 밀렸을 수 있기
  때문이다. 호출이 끝난 뒤에도 같은 `window_id`로 최종 위치를 재확인한다.

  그 스킬은 내부적으로 worktree 경로와 worktree명(= handle)도 쓰므로
  (`move-window-to-session/SKILL.md:114`), R7.0·R7.1에서 확보한 경로와 handle을 함께
  전달한다. 그 스킬의 3-(a) 단계가 `window-session`을 대상 세션으로 갱신하므로 R2.4는
  덮어쓰기가 아니라 **확인**으로 동작한다.

- **R7.6** 같은 브랜치의 worktree가 이미 있으면 새로 만들지 않고 기존 경로를 안내한다.
  R4.3과 같은 규칙이며 PR 모드에도 동일하게 적용된다.

### R8. 생성 후 검증

- **R8.1** `tmux list-windows -a -F '#{session_name}:#{window_index}\t#{window_name}'`로
  실제 윈도우 이름과 세션을 확인한다. `workmux list`에는 윈도우 이름 열이 없으므로
  추측해서 안내하면 사용자가 `workmux close`에 없는 이름을 넘기게 된다.
- **R8.2** 실제 세션이 선택 세션과 다르면 알리고, 잘못 만들어진 세션과 git config 값을
  함께 정리한다.
- **R8.3** 결과 보고에 worktree 경로, handle, 브랜치, 실제 세션, 실제 윈도우 이름을
  포함한다. PR 모드에서는 PR 번호와 head OID도 포함한다.

### R9. 문서 동기화

- **R9.1** 두 SKILL.md 본문은 Claude 전용 frontmatter를 제외하고 동일해야 한다.
- **R9.2** 현존하는 workmux 버전 표기 불일치(`dot_agents:43` vs `dot_claude:46`)를
  더 정확한 `dot_claude` 쪽 문구로 통일한다.
- **R9.3** `openai.yaml`의 `default_prompt`에 대상 세션 또는 PR 참조 사례를 반영한다.
- **R9.4** 홈의 적용본을 직접 수정하지 않는다. chezmoi 원본만 고치고 `chezmoi apply`로
  적용한다.
- **R9.5 `description` frontmatter 갱신.** 두 SKILL.md의 `description`은 현재 양쪽 다
  "Use when creating a new git worktree for a branch to work on in isolation from the
  main workspace"로, **브랜치만 언급한다**(실측). 에이전트는 이 문장으로 호출을
  라우팅하므로, PR 참조와 대상 세션이 유효한 입력이 된 뒤에도 이대로 두면 "PR 31을
  2-review에 열어줘" 같은 R1.4·R1.6 호출이 스킬에 도달하지 못할 수 있다. PR 참조와
  대상 세션 지정을 포함하도록 양쪽 모두 갱신한다.
- **R9.6 보존 대상 규칙 목록 (Goal 5의 검증 근거).** 아래 현행 규칙은 재작성 후에도
  두 SKILL.md에 남아 있어야 한다. 각 항목은 해당 요구사항이 계승하거나 그대로 유지한다.

  | # | 보존 규칙 | 계승 위치 |
  |---|---|---|
  | 1 | git-crypt 저장소에서 `workmux add` 금지 | R6.2 |
  | 2 | 래퍼 실패 시 중단, `workmux open` 미진행 | R6.5 |
  | 3 | 래퍼 확인 프롬프트 자동 우회 금지 | R6.5 |
  | 4 | 래퍼 실행 권한 없으면 경로 변경 없이 오류 보고 | R6.5 |
  | 5 | git-crypt 필터 있는데 래퍼 없으면 사용자 확인 후 진행 | R6.10 |
  | 6 | 저장소 루트 기준 경로 분기 | R6.1 |
  | 7 | `has-session` 금지와 접두사 함정 근거 | R3.4 |
  | 8 | 유령 세션 위험 서술(workmux가 없는 세션을 만들고 config에 저장) | R3.5 |
  | 9 | 레거시 `window-session` 값의 정규식 판정과 glob 반례 | R2.2 |
  | 10 | `--parent-session` 미지원 조합 예외 | R6.7 |
  | 11 | 창 이름 충돌 재시도 | R5.6 |
  | 12 | `workmux list`에 윈도우 이름 열이 없으므로 `tmux list-windows`로 확인 | R8.1 |
  | 13 | `workmux open`이 `git worktree list`로 찾으므로 `worktree_dir` 밖 형제 디렉터리도 인식 | R6.9 서술에 포함 |
  | 14 | 에이전트 자동 실행 안 함 | 주의사항 절 유지 |
  | 15 | 개발 서버는 별도 윈도우·pane (포트 충돌, 개당 1~2GB) | 주의사항 절 유지 |
  | 16 | 레이아웃은 `~/.config/workmux/config.yaml`, 저장소별은 `.workmux.yaml` | 주의사항 절 유지 |
  | 17 | 같은 브랜치 worktree가 있으면 기존 경로 안내 | R7.6 |
  | 18 | 이슈 번호는 브랜치명 맨 앞의 숫자 또는 `ZF-숫자`만 | R5.2 |

## Acceptance criteria

검증 유형: **[실행]**(명령 종료 코드·출력으로 판정), **[문서]**(두 SKILL.md에 해당
규칙이 기술되어 있는지 검토로 판정).

| ID | 기준 | 검증 방법 | 커버 |
|---|---|---|---|
| AC-1 | 입력 계약이 `<브랜치명\|PR참조> [대상세션]`으로 문서화되고 첫 인자 누락 시 묻는다 | [문서] 파라미터 절 | R1.1, R1.2 |
| AC-2 | positional 3개 이상이면 사용법 안내 후 중단 | [문서] R1.3 | R1.3 |
| AC-3 | PR 모드 트리거 3종이 열거된다 | [문서] R1.4 | R1.4 |
| AC-4 | 표지 없는 맨 숫자를 PR로 해석하지 않는 규칙과 근거가 기술된다 | [문서] R1.5 | R1.5 |
| AC-5 | 자연어 → 2-튜플 환원과 "두 개 이상 중단"이 기술된다 | [문서] R1.6 | R1.6 |
| AC-6 | 세션명 접두사 보정·추측 금지가 기술된다 | [문서] R1.7 | R1.7 |
| AC-7 | `argument-hint`가 `<branch-name\|pr-ref> [target-session]`이다 | [실행] `grep -q` → exit 0 | R1.8 |
| AC-8 | `{이름}`이 `workmux list --json`의 `handle`로 정의되고, 브랜치·창 이름 유추 금지가 **양방향 실측 반례**(브랜치와 같은 경우·다른 경우)와 함께 기술된다 | [문서] R2.0 | R2.0 |
| AC-9 | 실제 존재하는 workmux worktree 키가 handle 기준 키뿐이다 | [실행] 스모크에서 `git config --get-regexp '^workmux\.worktree\.'` 출력의 모든 키가 `workmux.worktree.{H}.{속성}` 형태이고 `{H}` == `workmux list --json`의 `handle`. handle이 브랜치 슬러그와 다른 경우에 한해 브랜치 유추 키 조회가 exit 1임을 증거로 추가 기록 | R2.0 |
| AC-10 | 세션 우선순위가 명시값 > 저장값 > 모드 기본값 > `1-main`으로 기술된다 | [문서] 저장값이 모드 기본값보다 위임을 확인 | R2.1 |
| AC-11 | 레거시 저장값을 정규식으로 판정하고 glob을 금지하는 근거가 기술된다 | [문서] R2.2 | R2.2 |
| AC-12 | 선택 세션 확정 전 workmux 명령 금지가 기술된다 | [문서] R2.3 | R2.3 |
| AC-13 | 명시 세션이 저장값을 덮으면 git config가 명시 세션을 가리킨다 | [실행] 스모크 3차에서 `window-session`이 `2-review` → `3-personal`로 바뀜 | R2.4 |
| AC-14 | 형식은 유효하나 사라진 저장 세션에 복구 경로가 있다 | [문서] R2.5의 4단계(알림·제시·확인 후 갱신·자동 생성 금지) | R2.5 |
| AC-15 | tmux 서버 부재를 세션 부재와 구분해 감지한다 | [실행] `tmux -L quality-goal-nonexistent-socket list-sessions` → exit 1 + `error connecting to`. + [문서] 구분 서술 | R3.1, R3.2 |
| AC-16 | 없는 세션은 `grep -qxF`로 부재 판정되고 자동 생성하지 않는다 | [실행] `... \| grep -qxF -- 'definitely-not-a-session'` → exit 1. + [문서] R3.5 | R3.3, R3.5 |
| AC-17 | `has-session` 접두사 함정이 실측 근거와 함께 금지된다 | [실행] `has-session -t 2` → 0, `-t 2-rev` → 0, `grep -qxF 2-rev` → 1. + [문서] R3.4 | R3.4 |
| AC-18 | 고정 `1-main` 검사가 선택 세션 검사로 일반화된다 | [실행] 아래 "`1-main` 잔존 검사" | R3.6, R6.6 |
| AC-19 | `{owner}/{repo}`와 현재 저장소의 확정 방법이 입력 형태별로 기술된다 | [문서] R4.0의 표와 `gh repo view` 명령·폴백 | R4.0 |
| AC-20 | PR 조회가 소비되는 필드만 요청하고 각 소비처가 명시된다 | [문서] R4.1 | R4.1 |
| AC-21 | base 저장소 불일치 시 중단하며, 비교 대상 두 값이 R4.0에서 확정된 것임이 기술된다 | [문서] R4.2 | R4.2 |
| AC-22 | 기존 worktree면 생성만 건너뛰고 R7으로 진행(전체 중단 아님) | [문서] R4.3 + 흐름도 분기 일치 | R4.3, R7.6 |
| AC-23 | 동명 로컬 브랜치가 head OID와 다르면 중단 | [문서] R4.4 | R4.4 |
| AC-24 | `gh` 부재·미인증·실패 시 추측 없이 중단 | [문서] R4.5 | R4.5 |
| AC-25 | 래퍼 경로에서 `refs/pull/{N}/head`로 head를 확보하고 실패 시 래퍼를 부르지 않는다 | [문서] R4.6의 명령·중단 규칙 + 래퍼 3단계 판별 근거 | R4.6 |
| AC-26 | CLOSED·MERGED PR에 대한 동작이 정의된다 | [문서] R4.7 | R4.7 |
| AC-27 | 짧은 이름이 마지막 `/` 뒤로 파생된다 | [문서] R5.1 | R5.1 |
| AC-28 | 브랜치 모드 이슈 번호 규칙이 유지된다 | [문서] R5.2 | R5.2 |
| AC-29 | PR head가 이슈 번호로 시작해도 창 이름에 PR 번호가 쓰인다 | [실행] 스모크 1차에서 창 이름이 `31-tmux-open-pr-shortcut`이고 `30-`으로 시작하지 않음 | R5.3 |
| AC-30 | 이슈 번호 없으면 `--target-name` 생략 | [문서] R5.4 | R5.4 |
| AC-31 | 소문자 정규화가 안내에 반영된다 | [문서] R5.5 | R5.5 |
| AC-32 | PR 모드 충돌 재시도가 PR 번호를 보존한다 | [문서] R5.6의 모드별 구분 | R5.6 |
| AC-33 | 경로 분기를 저장소 루트 기준으로 판정한다 | [문서] R6.1 | R6.1 |
| AC-34 | git-crypt 저장소에서 `workmux add`를 쓰지 않는다 | [문서] R6.2 + git-crypt 분기에 래퍼 호출만 존재 | R6.2 |
| AC-35 | 래퍼 없는 PR 경로가 positional을 생략하고 `--pr`를 쓴다 | [실행] 스모크 1차에서 worktree 브랜치가 `30-enhancement/tmux-open-pr-shortcut` | R6.3 |
| AC-36 | 래퍼 있는 PR 경로가 확보 → 래퍼 → `workmux open` 순서로 기술된다 | [문서] R6.4 | R6.4 |
| AC-37 | 래퍼 실패·권한 없음 시 창을 열지 않고 프롬프트를 우회하지 않는다 | [문서] R6.5 | R6.5 |
| AC-38 | `--parent-session` 미지원 조합 예외가 유지된다 | [문서] R6.7 | R6.7 |
| AC-39 | 생성된 worktree HEAD가 PR head OID와 일치한다 | [실행] 스모크 1차에서 `git -C {wt} rev-parse HEAD` == `9cfc6267ced574945814536710cf1019a37dc354` | R6.8 |
| AC-40 | 경로·handle을 명령 출력에서 얻고 추측하지 않는다 | [문서] R6.9의 경로별 획득 방법. + [실행] 스모크 1차에서 `workmux list --json`으로 handle을 읽어 보고 | R6.9 |
| AC-41 | git-crypt 필터가 있으나 래퍼가 없으면 사용자 확인 후 진행한다 | [문서] R6.10 | R6.10 |
| AC-42 | worktree 존재 판정이 세션 선택보다 먼저다 | [문서] 흐름도에서 R7.0이 R2보다 앞 | R7.0 |
| AC-43 | 창 열림·위치 판정이 이름이 아닌 `is_open` + pane 경로 + 안정 식별자로 규정되고, PR 모드 실측 사례(handle `30-enhancement-tmux-open-pr-shortcut` vs 창 이름 `31-tmux-open-pr-shortcut`)가 근거로 제시된다 | [문서] R7.1. + [실행] 스모크 1차에서 pane 경로 매칭이 방금 만든 창을 정확히 1건 반환 | R7.1 |
| AC-44 | 매칭 0건·2건 이상과 경로 공백 한계에서 추측하지 않는다 | [문서] R7.1의 한계·불일치 처리 | R7.1 |
| AC-45 | 창이 닫혀 있으면 선택 세션으로 직접 연다 | [문서] R7.2 | R7.2 |
| AC-46 | **선택 세션과 같은 세션에** 이미 열려 있으면 중복 창을 만들지 않는다 | [실행] 스모크 2차에서 창이 있는 세션(`2-review`)을 그대로 지정해 재호출 → pane 경로 매칭 결과가 1건 유지 | R7.3 |
| AC-47 | 세션 미명시 시 기존 위치를 존중한다 | [문서] R7.4 | R7.4 |
| AC-48 | 열린 창의 명시적 이동이 `move-window-to-session`의 입력 계약(`세션:번호`)에 맞춰 호출되고, `window_id`로 직전 해석·사후 재확인한다 | [문서] R7.5의 인자 구성·해석 명령. + [실행] 스모크 3차에서 창이 `3-personal`로 이동하고 `window_id`가 동일 | R7.5 |
| AC-49 | 생성 후 실제 세션·창 이름을 `tmux list-windows`로 확인한다 | [실행] 스모크 1차에서 실행·기록 | R8.1 |
| AC-50 | 세션 불일치 시 잘못된 세션과 git config를 정리한다 | [문서] R8.2 | R8.2 |
| AC-51 | 보고에 경로·handle·브랜치·세션·창이름(+PR번호·head OID) 포함 | [실행] 스모크 1차 보고에 7항목 존재 | R8.3 |
| AC-52 | 두 SKILL.md 본문이 Claude frontmatter 외에 동일하다 | [실행] `diff` 출력이 `3a4,6`과 그 3줄만 | R9.1, R9.2 |
| AC-53 | `openai.yaml` `default_prompt`에 세션 또는 PR 사례 반영 | [실행] `grep -qE '2-review\|pull/'` → exit 0 | R9.3 |
| AC-54 | chezmoi 원본만 수정되고 적용본이 일치한다 | [실행] `chezmoi apply` 후 3개 파일 `cmp` → exit 0 | R9.4 |
| AC-55 | 두 SKILL.md의 `description`이 PR 참조와 대상 세션을 포함하도록 갱신된다 | [실행] 두 파일 3행에 대해 `grep -qiE 'pull request\|PR' && grep -qiE 'session'` → exit 0. 두 파일의 `description`이 서로 동일 | R9.5 |
| AC-56 | R9.6의 보존 규칙 18개가 모두 두 SKILL.md에 남아 있다 | [실행/검토] 각 항목을 두 파일에서 확인. 누락 0건 | R9.6, Goal 5 |
| AC-57 | PR 모드 신규 worktree에서 세션 미명시 시 `2-review`가 선택된다 | [실행] 스모크 1차에서 창이 `2-review`에 열림 | R2 우선순위 3 |
| AC-58 | 두 스킬이 frontmatter 검증 기준선을 만족한다 | [실행] 아래 "frontmatter 검증" | 도구 위생 |
| AC-59 | 공백 오류·시크릿 유출 없음 | [실행] `git diff --check` → 0, `pre-commit run --all-files` 통과 | 저장소 위생 |

### 요구사항 전수 대응 확인

R1.1→AC-1, R1.2→AC-1, R1.3→AC-2, R1.4→AC-3, R1.5→AC-4, R1.6→AC-5, R1.7→AC-6,
R1.8→AC-7, R2.0→AC-8·AC-9, R2.1→AC-10, R2.2→AC-11, R2.3→AC-12, R2.4→AC-13,
R2.5→AC-14, R3.1→AC-15, R3.2→AC-15, R3.3→AC-16, R3.4→AC-17, R3.5→AC-16, R3.6→AC-18,
R4.0→AC-19, R4.1→AC-20, R4.2→AC-21, R4.3→AC-22, R4.4→AC-23, R4.5→AC-24, R4.6→AC-25,
R4.7→AC-26, R5.1→AC-27, R5.2→AC-28, R5.3→AC-29, R5.4→AC-30, R5.5→AC-31, R5.6→AC-32,
R6.1→AC-33, R6.2→AC-34, R6.3→AC-35, R6.4→AC-36, R6.5→AC-37, R6.6→AC-18, R6.7→AC-38,
R6.8→AC-39, R6.9→AC-40, R6.10→AC-41, R7.0→AC-42, R7.1→AC-43·AC-44, R7.2→AC-45,
R7.3→AC-46, R7.4→AC-47, R7.5→AC-48, R7.6→AC-22, R8.1→AC-49, R8.2→AC-50, R8.3→AC-51,
R9.1→AC-52, R9.2→AC-52, R9.3→AC-53, R9.4→AC-54, R9.5→AC-55, R9.6→AC-56.
**미대응 요구사항 없음.**

### `1-main` 잔존 검사 (AC-18의 실행 정의)

```bash
grep -n -- '1-main' dot_agents/skills/create-worktree/SKILL.md \
                    dot_claude/skills/create-worktree/SKILL.md
```

**허용되는 잔존 용례**

1. R2 우선순위 4순위를 설명하는 "전역 기본값 `1-main`" 서술
2. 우선순위 예시 표에서 기본값 결과를 보이는 셀
3. 유령 세션 위험이나 레거시 마이그레이션을 설명하며 예시로 드는 문장

**금지되는 잔존 용례** — 하나라도 남으면 AC-18 실패.

1. `--parent-session 1-main` 리터럴이 실행 명령 예시에 있음
2. `grep -qxF -- 1-main`처럼 검증 대상이 고정됨
3. `git config ... window-session 1-main`처럼 기록 값이 고정됨
4. "`1-main` 세션이 없으면 여기서 멈춘다"처럼 중단 조건이 묶임
5. "새로 만든 것이면 `1-main`"처럼 사후 검증 기대값이 고정됨

### frontmatter 검증 (AC-58의 실행 정의)

```bash
QV=/Users/lee-kyu-hwan/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator/scripts/quick_validate.py
python3 "$QV" /Users/lee-kyu-hwan/code/dotfiles/dot_claude/skills/create-worktree
python3 "$QV" /Users/lee-kyu-hwan/code/dotfiles/dot_agents/skills/create-worktree
```

실측 기준선(변경 전): `dot_agents` → `Skill is valid!` exit 0. `dot_claude` →
`Unexpected key(s) in SKILL.md frontmatter: argument-hint, user-invocable.` **exit 0**.

판정 기준은 **종료 코드 0 + `dot_claude`의 메시지가 위 Claude 전용 키 안내에서 늘어나지
않을 것.** 새로운 종류의 경고가 추가되면 실패로 본다.

## Architecture

스킬은 실행 코드가 아니라 에이전트가 읽고 따르는 절차 문서다. "아키텍처"는 문서가
기술하는 결정 흐름과 그것이 호출하는 외부 도구 경계를 뜻한다.

### 결정 흐름

worktree 식별(R7.0)과 창 탐지(R7.1)가 세션 선택(R2)보다 **앞선다** — 저장 세션을
읽으려면 handle이 필요하고 handle은 경로로 찾기 때문이다.

```
1. 입력 파싱 (R1)
     ├─ positional 3개 이상 → 사용법 안내 후 중단
     ├─ PR 참조 판정 (R1.4 / R1.5)
     └─ 자연어면 2-튜플 환원 (R1.6)
          ↓
2. 저장소 확정 (R4.0)  [PR 모드]
     PR 참조에서 {owner}/{repo} / gh repo view로 현재 저장소
          ↓
3. PR 해석 (R4.1, R4.2, R4.5, R4.7)
     ├─ 번호·head브랜치·headRefOid·state 조회
     ├─ base 저장소 불일치 → 중단
     └─ state != OPEN → 알리고 확인
          ↓
4. worktree 식별 (R7.0)
     git worktree list --porcelain → 경로
     workmux list --json           → handle (없으면 신규)
          ↓
5. 창 탐지 (R7.1)  [worktree가 있을 때만]
     is_open → window-session → pane 경로 매칭 → window_id/pane_id 확보
          ↓
6. 세션 선택 (R2)
     명시값 > 유효·생존 저장값 > 모드 기본값(PR→2-review) > 1-main
     저장값이 형식 유효하나 세션 부재 → R2.5 복구
          ↓
7. 세션 검증 (R3)
     list-sessions 종료 코드 → grep -qxF 전체 일치 → 없으면 중단 또는 R2.5
          ↓
8. 이름 파생 (R5)
          ↓
9. 분기
     ├─ [worktree 있음] (R4.3 → R7.2~R7.5)
     │     ├─ is_open 거짓 → 선택 세션으로 workmux open
     │     ├─ is_open 참 & 같은 세션 → 안내만 (중복 창 금지)
     │     └─ is_open 참 & 다른 세션 & 명시됨
     │           → window_id로 세션:번호 해석 → move-window-to-session
     │
     └─ [worktree 없음] → 브랜치 안전 검사 (R4.4) → 생성 (R6)
           ├─ 래퍼 있음: R4.6 fetch → 래퍼 → workmux open
           ├─ 래퍼 없음: workmux add --pr (positional 생략)
           └─ git-crypt 필터 있으나 래퍼 없음 → 사용자 확인 (R6.10)
          ↓
10. 생성 후 검증 (R6.8, R6.9, R8, R2.4)
     HEAD == headRefOid → handle·경로 확보 → tmux 대조 → git config 확인
```

### 구성 요소와 책임 경계

| 구성 요소 | 책임 | 이번 변경 |
|---|---|---|
| `dot_claude/.../SKILL.md` | Claude Code가 읽는 절차 + Claude 전용 frontmatter | 본문 확장, `argument-hint`·`description` 갱신 |
| `dot_agents/.../SKILL.md` | Codex·공용 에이전트가 읽는 절차 | 본문 동일 확장, `description` 갱신 |
| `dot_agents/.../agents/openai.yaml` | Codex UI 메타데이터 | `default_prompt` 갱신 |
| `workmux` (0.1.248) | worktree 생성·창 구성·`--pr` 체크아웃·`list --json` 상태 조회·`--dry-run` 미리보기 | 호출만 |
| 대상 저장소의 `scripts/create-worktree.sh` | git-crypt worktree 생성·키 링크·의존성 설치 | 호출만. 3단계 판별의 전제를 R4.6이 보장 |
| `gh` | PR 메타데이터·현재 저장소 조회 (읽기 전용) | 신규 의존 |
| `git fetch origin refs/pull/N/head` | PR head 커밋 확보 | 신규 의존 (래퍼 경로) |
| `tmux list-panes -a` | 이름 독립 창 매칭 | 신규 의존 (R7.1) |
| `move-window-to-session` 스킬 | 열린 창 이동 + 메타데이터 동기화 | 호출만. **입력 계약에 맞춰 `세션:번호`로 호출** |
| `~/.config/workmux/config.yaml` | pane 레이아웃, `base_branch: auto` | 변경 없음 |

### 결정: 두 원본의 동기화 방식

- **대안 A — 심볼릭 링크**: Claude 전용 frontmatter가 파일 앞에 있어야 하므로 파일
  전체를 링크할 수 없다. 탈락.
- **대안 B — 생성 스크립트**: 변경 범위(#35가 지정한 3개 파일)를 넘어서고 chezmoi
  흐름에 빌드 단계를 넣는다. 탈락.
- **대안 C — 수동 유지 + `diff` 검증(채택)**: 기존 관행과 같고 추가 장치가 없다.

## Interfaces and data flow

### 스킬 입력 계약

```
<브랜치명|PR참조> [대상세션]
```

| 입력 | 모드 | 대상 세션 | 창 이름 |
|---|---|---|---|
| `1290-bug/partner-robots-yeti-disallow` | 브랜치 | `1-main` (기본) | `1290-partner-robots-yeti-disallow` |
| `1290-bug/... 2-review` | 브랜치 | `2-review` (명시) | 같음 |
| `fix/login-bug` | 브랜치 | `1-main` | `--target-name` 생략 |
| `https://github.com/owner/repo/pull/1247` | PR | `2-review` (모드 기본) | `1247-{짧은이름}` |
| `zambaguni/zambaguni-front#1313` | PR | `2-review` | `1313-snap-board-grid-windowing` |
| `.../pull/1247 3-personal` | PR | `3-personal` (명시) | `1247-...` |
| 위 PR + 저장값 `3-personal`(생존), 세션 미명시 | PR | `3-personal` (저장값 우선) | `1247-...` |
| 위 PR + 저장값 `3-personal`, `2-review` 명시 | PR | `2-review` (명시 우선) + config 갱신 | `1247-...` |
| 위 PR + 저장값 `9-gone`(형식 유효, 세션 부재) | PR | R2.5 복구 → 확인 후 `2-review` | `1247-...` |
| `1313` (표지 없는 맨 숫자) | 브랜치 또는 확인 요청 | — | — |
| "PR 1313을 2-review에 열어줘" | PR (표지 있음, 저장소는 현재 저장소) | `2-review` | `1313-...` |

### 외부 명령 계약

**저장소·PR 메타데이터 (읽기 전용)**

```bash
gh repo view --json owner,name -q '.owner.login + "/" + .name'
gh pr view {번호} --repo {owner}/{repo} --json number,state,headRefName,headRefOid
```

**worktree 식별과 창 탐지**

```bash
git worktree list --porcelain
workmux list --json          # handle, path, branch, is_open, mode
git config --get workmux.worktree.{handle}.window-session
tmux list-panes -a -F '#{session_name}:#{window_index} #{window_id} #{pane_id} #{pane_current_path}'
```

**PR head 확보 (래퍼 경로)**

```bash
git fetch origin "refs/pull/{PR번호}/head:{head브랜치명}"
git rev-parse --verify "refs/heads/{head브랜치명}"
```

**생성 — 래퍼 없음 / 있음**

```bash
workmux add --pr {PR참조} --target-name {PR번호}-{짧은이름} --parent-session {선택세션}
workmux add --pr {PR참조} --dry-run     # 사전 확인용, 영속 변경 없음

./scripts/create-worktree.sh {head브랜치명}
workmux open {handle} --target-name {PR번호}-{짧은이름} --parent-session {선택세션}
```

**열린 창 이동 (R7.5)**

```bash
SRC=$(tmux display-message -p -t "{window_id}" '#{session_name}:#{window_index}')
# move-window-to-session 인자: "$SRC" "{선택세션}"  (+ 컨텍스트로 worktree 경로·handle)
```

**생성 후 검증**

```bash
git -C {worktree경로} rev-parse HEAD                  # == headRefOid
git -C {worktree경로} rev-parse --abbrev-ref HEAD     # == head브랜치명
tmux list-windows -a -F '#{session_name}:#{window_index}\t#{window_name}'
git -C {worktree경로} config --get workmux.worktree.{handle}.window-session
```

### 상태 저장소

| 위치 | 내용 | 읽기 | 쓰기 |
|---|---|---|---|
| `workmux.worktree.{handle}.window-session` | 창이 속한 세션 | R2 우선순위 2, R7.1 | R2.2·R2.4·R2.5·R8.2 네 경우만. workmux와 `move-window-to-session`도 각자 쓴다 |
| `workmux list --json` | handle·path·branch·is_open·mode | R7.0, R7.1, R6.9 | 없음 |
| tmux 서버 | 세션·윈도우·pane 목록 | R3, R7.1, R8.1 | 창 이동(R7.5)은 `move-window-to-session`이 수행. 세션 자동 생성은 금지 |
| `git worktree list` | worktree 경로·브랜치 | R7.0 | 없음 |
| `~/.local/state/workmux/agents/*.json` | 에이전트 상태 | — | `move-window-to-session`이 담당 |

## Failure behavior

| 실패 | 감지 | 동작 |
|---|---|---|
| positional 3개 이상 | 인자 개수 | 사용법 안내 후 중단 |
| 자연어에서 브랜치·PR 참조 2개 이상 | R1.6 | 중단하고 확인 |
| 자연어에서 세션명 2개 이상 | R1.6 | 중단하고 확인 |
| 표지 없는 맨 숫자 | R1.5 | 브랜치로 해석하거나 확인. PR로 단정 금지 |
| **현재 저장소를 확정 못 함** | `gh repo view`·`git remote` 모두 실패 | 중단. R4.2 비교가 성립하지 않으므로 진행 불가 |
| `gh` 없음·미인증·조회 실패 | 종료 코드 | 보고 후 중단. 추측 금지 |
| PR base 저장소 불일치 | R4.0의 두 값 비교 | 중단 |
| PR state가 CLOSED·MERGED | R4.7 | 알리고 계속할지 확인. head 브랜치 삭제 가능성 안내 |
| **PR head fetch 실패** | `git fetch` 종료 코드 | **중단. 래퍼를 부르지 않는다** — 부르면 빈 브랜치 worktree가 생긴다 |
| **확보된 OID ≠ `headRefOid`** | `git rev-parse` 비교 | 중단. 래퍼를 부르지 않는다 |
| **생성된 worktree HEAD ≠ `headRefOid`** | R6.8 | 성공으로 보고하지 않고 PR 내용 없음을 알린다 |
| 동명 로컬 브랜치가 다른 커밋 | OID 비교 | 중단. 덮어쓰지 않음 |
| PR head의 worktree가 이미 있음 | R7.0 | **중단이 아님.** 생성만 건너뛰고 R7 창 처리로 진행 |
| **`is_open` 참인데 pane 매칭 0건** | R7.1 | 추측 금지. `window-session` 세션의 창 목록을 보여 주고 확인 |
| **pane 매칭 2건 이상** | R7.1 | 그대로 보고하고 확인 |
| **worktree 경로에 공백** | R7.1 매칭기 한계 | 매칭 결과를 신뢰하지 않고 불일치 처리로 넘어감 |
| **handle을 얻지 못함** | `workmux list --json` 결과 없음 | 경로 basename 폴백 + `path` 대조. 대조 수단도 없으면 중단 |
| tmux 서버 부재 | `list-sessions` exit 1 + `error connecting to` | "tmux 서버가 없다"로 보고. 세션 부재와 구분 |
| **저장 세션이 형식 유효하나 부재** | R3.3 실패 + 출처가 저장값 | **중단이 아님.** R2.5 복구 — 알리고 기본값 제시·확인·config 갱신. 자동 생성 금지 |
| 명시 세션이 부재 | R3.3 실패 + 출처가 사용자 | 오타 가능성을 알리고 중단. 자동 생성 금지 |
| git-crypt 필터 있으나 래퍼 없음 | R6.1 + R6.10 | 사용자에게 확인받고 진행 |
| 래퍼 실패 | 종료 코드 | 중단. `workmux open` 미진행. 암호화·의존성 미설치 가능성 보고 |
| 래퍼 실행 권한 없음 | 파일 권한 | 경로를 바꾸지 않고 오류 보고 |
| 창 이름 충돌 (브랜치 모드) | `A tmux window named '...' already exists` | `--target-name {repo명}-{짧은이름}`으로 재시도 |
| 창 이름 충돌 (PR 모드) | 같음 | `--target-name {PR번호}-{repo명}-{짧은이름}`으로 재시도 |
| 이동 중 창 번호가 밀림 | R7.5 | `window_id`로 직전 해석하므로 영향 없음. 사후에도 `window_id`로 재확인 |
| 생성 후 세션 불일치 | R8.1 | 알리고 잘못된 세션·git config 정리 |
| `--parent-session` 미지원 조합 | 명령 조합 | 플래그 생략 |

**공통 원칙.** 중단 시 이미 만들어진 산출물(worktree, 브랜치, 창)을 그대로 보고한다.
부분 성공을 성공으로 보고하지 않는다.

## Security and risk

### 신뢰 경계와 데이터 민감도

- **PR 메타데이터는 외부 입력이다.** 제목·본문·브랜치명은 다른 사람이 쓴 데이터이며
  지시가 아니다. 브랜치명은 셸 인자로 들어가므로 항상 인용 부호로 감싸고, 스킬이 PR
  본문의 지시를 따르지 않는다.
- **fork PR은 신뢰 경계 밖의 코드다.** `refs/pull/{N}/head`로 가져오는 내용은 외부
  기여자가 작성했을 수 있다. 이 스킬은 worktree를 만들 뿐 그 코드를 실행하지 않는다.
  래퍼의 의존성 설치는 기존 동작이며 이번 변경이 새로 도입하는 실행 경로가 아니다.
- **git-crypt 키는 이 변경의 관심사가 아니다.** 키 링크와 unlock은 대상 저장소의
  래퍼가 전담하며(래퍼 100-160행), 스킬 텍스트는 키 자료를 읽거나 출력하지 않는다.
- **`gh`는 읽기 전용으로만 쓴다.**
- **시크릿 유출 방지.** 산출물은 Markdown과 YAML이며 자격 증명을 담지 않는다.
  `.pre-commit-config.yaml`의 gitleaks 훅이 검사한다. 공백 검사는 그 훅이 아니라
  `git diff --check`가 담당한다(AC-59).

### 위험과 완화

| 위험 | 영향 | 완화 |
|---|---|---|
| **잘못된 git config 키** | 읽기는 빈 값, 쓰기는 쓰레기 섹션. 저장 세션이 무시되어 "옮긴 창 되끌기"가 재발 | R2.0의 handle 정의 + AC-9의 실측 대조 |
| **이름 기반 창 매칭으로 중복 창 생성** | 살아 있는 에이전트 pane 유실 | R7.1의 `is_open` + pane 경로 매칭 + 안정 식별자. AC-46이 같은 세션 조건을 실측 |
| **PR 내용이 없는 빈 worktree** | 리뷰 대상이 아닌 코드를 리뷰 | R4.6 사전 fetch + R6.8 사후 OID 검증 이중 방어 |
| **사라진 저장 세션으로 영구 중단** | 매 호출 실패, 자기 교정 경로 없음 | R2.5 복구 경로 |
| 유령 세션 생성 | workmux가 없는 세션을 만들고 config에 영구 저장 | R3.5 사전 검증 |
| 의도적으로 옮긴 창 되끌기 | 사용자 배치가 조용히 무너짐 | R2.1 저장값 우선 |
| 명시 세션 미반영 | 다음 호출이 옛 세션으로 되돌아감 | R2.4 |
| **이동 중 창 번호 변동** | 엉뚱한 창을 옮김 | R7.5의 `window_id` 직전 해석 |
| PR 번호와 이슈 번호 혼동 | 엉뚱한 창 이름 | R1.5, R5.3, R5.6. AC-29가 실측 |
| 로컬 브랜치 덮어쓰기 | 미푸시 커밋 유실 | R4.4 |
| 열린 창 재구성으로 에이전트 상태 유실 | 작업 손실 | R7.5 |
| **`description` 미갱신으로 라우팅 실패** | PR 자연어 호출이 스킬에 도달하지 못함 | R9.5 + AC-55 |
| 기존 규칙 유실 | 재작성 과정에서 안전장치가 사라짐 | R9.6 목록 + AC-56 |
| 두 원본 drift | Claude와 Codex가 다르게 동작 | R9.1 + AC-52 |
| 스모크 테스트 부작용 | 실제 worktree·창 생성 | 자신의 dotfiles PR #31 + `--dry-run` 사전 확인 + 정리 절차 |

### 롤백

산출물은 chezmoi 소스의 Markdown·YAML 3개 파일이다. 롤백은 `git revert` 또는
`git checkout -- {경로}` 후 `chezmoi apply`이며 데이터 마이그레이션이 없다. 스모크
테스트로 만들어진 worktree·창·로컬 브랜치는 Test strategy의 정리 절차로 제거한다.

### 비적용 항목

standard 등급이며 다음은 해당 사항이 없다.

- **인증·인가·테넌시**: 권한 경계를 다루지 않는다. `gh`는 사용자 자신의 기존 자격
  증명을 쓰며 이 변경이 권한을 넓히지 않는다.
- **DB 스키마·마이그레이션·백필**: 영속 스키마가 없다.
- **공개 API 호환성·멱등성·동시성**: 외부 노출 계약이 없다. 단일 사용자가 대화형으로
  호출한다.
- **프로덕션 변경**: 프로덕션 시스템을 건드리지 않는다.

## Test strategy

이 저장소에는 테스트 스위트·타입 체크·빌드가 없다(`package.json`, `Makefile`,
`justfile`, `.github/workflows` 부재 실측). 검증은 세 층으로 한다.

### 1층 — 부작용 없는 실행 검사

| 검사 | 명령 | 커버 |
|---|---|---|
| frontmatter | `quick_validate.py` 2회, 기준선 대조 | AC-58 |
| `argument-hint` | `grep -q` | AC-7 |
| `description` | 두 파일 3행에 PR·session 표현 존재, 양쪽 동일 | AC-55 |
| 두 본문 동일성 | `diff` → `3a4,6`과 그 3줄만 | AC-52 |
| `1-main` 잔존 | 허용/금지 목록 대조 | AC-18 |
| 보존 규칙 18개 | R9.6 목록을 두 파일에서 확인 | AC-56 |
| `openai.yaml` | `grep -qE '2-review\|pull/'` | AC-53 |
| tmux 서버 부재 | `tmux -L quality-goal-nonexistent-socket list-sessions` → exit 1 | AC-15 |
| 없는 세션 판정 | `grep -qxF -- 'definitely-not-a-session'` → exit 1 | AC-16 |
| 접두사 함정 | `has-session -t 2` → 0, `-t 2-rev` → 0, `grep -qxF 2-rev` → 1 | AC-17 |
| chezmoi 일치 | `chezmoi diff` → `chezmoi apply` → 3개 파일 `cmp` | AC-54 |
| 공백·시크릿 | `git diff --check`, `pre-commit run --all-files` | AC-59 |

tmux 검사 3종은 읽기 전용이거나 별도 소켓을 쓰므로 실제 세션 배치를 바꾸지 않는다.
예상 종료 코드는 2026-08-27에 실측했다.

### 2층 — 문서 검토

`[문서]` 기준은 절차 서술이므로 해당 규칙이 두 SKILL.md에 명시적으로 기술되어 있는지
검토로 판정한다. 확인 대상은 수용 기준 표에 특정해 두었다.

**이 층의 한계.** 문서 존재 검사는 "규칙이 올바르게 적혀 있음"만 보이고 "따랐을 때
실제로 옳은 결과가 나옴"은 보이지 않는다. 그래서 위험도가 높은 항목들(유령 세션 방지,
서버 부재 구분, 접두사 함정, git config 키 정합, 창 매칭 정확도, 중복 창 금지, 창
이동, PR 번호 파생, worktree 내용, 세션 덮어쓰기, description 라우팅, 보존 규칙)은
1층·3층의 실행 검사로 끌어올렸다. 남은 `[문서]` 기준은 실패 상황을 인위로 만들어야
검증되는 것들(fetch 실패, 저장소 불일치, 래퍼 부재 등)이며, 이 한계를 보고서에
기록한다.

### 3층 — 실제 스모크 테스트

**대상**: `lee-kyu-hwan/dotfiles` PR #31.

**가용성 실측 (2026-08-27)**: `state=OPEN`, head 브랜치
`30-enhancement/tmux-open-pr-shortcut`가 원격에 존재(`9cfc6267...`),
`refs/pull/31/head`도 같은 OID.

**선정 근거**: PR 번호(31)와 head 브랜치의 이슈 번호(30)가 달라 R5.3을 판별한다.
dotfiles는 git-crypt가 아니고 래퍼도 없으므로 `workmux add --pr` 경로를 탄다.

**사전 확인**: `workmux add --pr 31 --dry-run`으로 예상 경로·handle·target을 먼저
본다. 영속 변경이 없다. 실측된 예상값은 worktree
`.../dotfiles__worktrees/30-enhancement-tmux-open-pr-shortcut`, handle
`30-enhancement-tmux-open-pr-shortcut`이다.

**대체 계획**: 실행 시점에 #31이 닫혀 head 브랜치가 사라졌으면 같은 조건(PR 번호 ≠
head 브랜치 접두사 숫자)을 만족하는 다른 열린 PR로 교체한다. PR #32는 head가
`feat/codex-playwright-e2e-profile`로 숫자 접두사가 없어 AC-29를 판별하지 못하므로
대체 대상이 아니다. 조건을 만족하는 PR이 없으면
AC-9·13·29·35·39·40·43·46·48·49·51·57을 문서 검토로 강등하고 보고서에 한계로 명시한다.
이 강등은 "조건 만족 PR 부재"가 관찰되었을 때만 발동한다.

#### 1차 — 세션 미명시 신규 생성

| 단계 | 관찰 | 커버 |
|---|---|---|
| 세션 미명시로 PR 모드 실행 | 창이 `2-review`에 열림 | AC-57 |
| 창 이름 | `31-tmux-open-pr-shortcut` (`30-`으로 시작하지 않음) | AC-29 |
| worktree 브랜치 | `rev-parse --abbrev-ref HEAD` == `30-enhancement/tmux-open-pr-shortcut` | AC-35 |
| worktree HEAD | `rev-parse HEAD` == `9cfc6267ced574945814536710cf1019a37dc354` | AC-39 |
| handle·경로 확보 | `workmux list --json`에서 `branch` 일치 항목의 `handle`·`path`를 읽어 보고 | AC-40 |
| **git config 키 정합** | `git config --get-regexp '^workmux\.worktree\.'`의 모든 키가 `workmux.worktree.{handle}.*` 형태. handle이 브랜치 슬러그와 다를 때만 브랜치 유추 키 exit 1을 추가 증거로 기록 | AC-9 |
| **창 매칭 정확도** | pane 경로 매칭이 방금 만든 창의 `window_id`를 정확히 1건 반환 | AC-43 |
| 실제 창 위치 | `tmux list-windows -a` 출력 기록 | AC-49 |
| 결과 보고 | 경로·handle·브랜치·세션·창이름·PR번호·head OID 7항목 | AC-51 |

#### 2차 — 같은 세션 재호출 (R7.3의 조건)

1차로 창이 `2-review`에 있는 상태에서 **같은 세션 `2-review`를 명시해** 재호출한다.

| 단계 | 관찰 | 커버 |
|---|---|---|
| 같은 PR을 `2-review` 명시로 재호출 | 중복 창이 생기지 않음 — pane 경로 매칭 결과가 1건 유지, `window_id`도 동일 | AC-46 |

이 단계가 R7.3의 "선택 세션 == 현재 세션" 분기를 실제로 태운다.

#### 3차 — 다른 세션 명시 이동 (R7.5·R2.4의 조건)

| 단계 | 관찰 | 커버 |
|---|---|---|
| 같은 PR을 `3-personal` 명시로 재호출 | 창이 `3-personal`로 이동하고 `window_id`가 1차와 동일(재생성 아님) | AC-48 |
| git config 갱신 | `window-session`이 `2-review` → `3-personal`로 바뀜 | AC-13 |

#### 정리 절차 (검증 후 필수)

```bash
workmux remove {handle}              # worktree + 창 제거
git worktree list                    # 잔여물 없음 확인
tmux list-windows -a                 # 잔여 창 없음 확인
git branch --list '30-enhancement/tmux-open-pr-shortcut'   # 남아 있으면 그때만 -D
```

`workmux remove`가 로컬 브랜치까지 지우므로(`remove-worktree/SKILL.md:26`)
`git branch -D`를 무조건 실행하지 않는다. 남아 있는지 먼저 확인하고 남았을 때만 지운다.

**git-crypt 경로(AC-36)는 스모크 테스트하지 않는다.** `zambaguni-front` worktree
생성은 의존성 설치로 개당 1~2GB를 쓰고 업무 저장소에 부작용을 남긴다. 문서 검토로
판정하고 보고서에 한계로 기록한다. 다만 R4.6의 근거인 래퍼의 3단계 판별 로직은
`zambaguni-front/scripts/create-worktree.sh:82-98`을 직접 읽어 확인했다.

## Decisions

### D1. 세션 우선순위에서 저장값이 모드 기본값보다 우선한다

이슈 #35는 "명시값 > 모드 기본값 > 저장 세션 > 1-main"을 권장했다. 이를 뒤집어
"명시값 > 저장 세션 > 모드 기본값 > 1-main"으로 채택했다.

근거: 저장값은 사용자가 `move-window-to-session`으로 직접 창을 옮긴 행동의 기록이고,
모드 기본값은 관습이다. 관습이 기록을 덮으면 현행 "예외 1"이 막으려던 실패가
`2-review` 이름으로 재발한다. 사용자가 2026-08-27 확인에서 이 순서를 선택했다. 신규
worktree에는 저장값이 없으므로 PR 모드 기본값 `2-review`가 정상 동작한다(AC-57 실측).

### D2. PR 참조는 표지가 있을 때만 인식한다

표지 없는 맨 숫자를 PR로 해석하지 않는다. GitHub는 이슈와 PR이 번호 공간을 공유하므로
맨 숫자를 PR로 단정하면 엉뚱한 브랜치를 체크아웃할 수 있다. R1.4의 자연어 케이스가
R1.5와 모순되지 않는 이유는 금지 대상이 **표지 없는** 맨 숫자이기 때문이다.

### D3. PR 모드에서 positional 브랜치명을 생략한다

`workmux add --help` 실측: "`[BRANCH_NAME]` ... When used with `--pr`, this becomes the
custom local branch name". positional을 주면 PR head 대신 그 이름으로 로컬 브랜치가
생긴다. 같은 `--help`에서 `--target-name`·`--parent-session`이 `--pr`와 공존 가능함도
확인했다.

### D4. worktree 식별자는 handle이며 유추하지 않는다

`{이름}`을 `workmux list --json`의 `handle`(= `path` basename)로 정의했다.

대안 비교:

- **대안 A — 브랜치명 사용**: 실측 반례가 존재한다. 디렉터리
  `feat-quality-goal-skill` / 브랜치 `chore/post-upgrade-skill-maintenance`에서 브랜치
  유추 키 조회가 exit 1이다. 탈락.
- **대안 B — tmux 창 이름 사용**: `--target-name`으로 결정되며 모드마다 다르다. 탈락.
- **대안 C — 경로 basename 사용**: 대체로 handle과 같지만 `worktree_naming` 설정이
  바뀌면 어긋날 수 있다. `workmux list --json`이 없을 때의 폴백으로만 두고 `path`
  대조를 요구한다.
- **대안 D — `workmux list --json`의 `handle`(채택)**: workmux 자신이 쓰는 이름을
  직접 읽으므로 유추가 없다.

**handle이 브랜치 슬러그와 같을 수도 있다.** `workmux add --pr 31 --dry-run` 실측에서
handle이 `30-enhancement-tmux-open-pr-shortcut`으로 브랜치 슬러그와 일치했다. 이는
대안 A를 정당화하지 않는다 — 같을 수도 다를 수도 있어 **예측이 불가능**하다는 것이
핵심이고, 그래서 읽어야 한다. 이 사실은 AC-9의 판정 기준에도 반영했다(브랜치 유추 키
조회 실패를 필수 조건이 아니라 조건부 증거로 강등).

### D5. 창 탐지는 이름이 아닌 안정 식별자로 한다

`is_open` → `window-session` → pane 경로 매칭 3단계를 쓰고, 얻은 `window_id`·`pane_id`를
이후 조작의 기준으로 삼는다.

대안 비교:

- **대안 A — 창 이름 매칭**: 모드마다 파생 규칙이 다르다. PR #31 dry-run 실측이 직접
  사례다 — handle `30-enhancement-tmux-open-pr-shortcut` vs PR 모드 창 이름
  `31-tmux-open-pr-shortcut`. 열린 창을 놓치고 중복 창을 만든다. 탈락.
- **대안 B — `session:index` 사용**: `move-window`와 번호 재정렬로 바뀐다
  (`move-window-to-session/SKILL.md:32-39`). 추적 기준으로 부적합. 탈락.
- **대안 C — 에이전트 state 파일 조회**: `~/.local/state/workmux/agents/*.json`은
  에이전트가 붙은 pane만 담는다. 레이아웃이 nvim만 자동 실행하므로
  (`~/.config/workmux/config.yaml:9-16`) 창이 있어도 항목이 없을 수 있다. 탈락.
- **대안 D — `is_open` + pane 경로 + `window_id`(채택)**: 실측으로 tmux 실제 상태와
  일치함을 확인했고 이름에 의존하지 않는다.

pane cwd는 사용자가 바꿀 수 있고 매칭기가 공백 경로에 약하므로 완전하지 않다. 그래서
0건·2건 이상·공백 경로에서 추측하지 않고 확인받는 규칙을 함께 둔다(R7.1).

### D6. 래퍼는 고치지 않고 스킬이 전제를 보장한다

래퍼의 "둘 다 없으면 현재 HEAD에서 새 브랜치"는 브랜치 모드에서는 올바른 동작이다.
문제는 PR 모드에서 head가 `origin`에 없을 때(fork PR)뿐이다.

- **대안 A — 래퍼에 `--pr` 지원 추가**: 다른 저장소를 고쳐야 하고 변경 범위 밖. 탈락.
- **대안 B — 스킬이 호출 전 fetch로 전제 보장(채택)**: `refs/pull/{N}/head`를 로컬
  브랜치로 가져오면 래퍼의 2번 경로로 확정된다. 같은 저장소 PR과 fork PR을 동일하게
  처리한다.
- **대안 C — PR 모드에서 git-crypt 저장소 미지원**: #28의 요구를 포기. 탈락.

사후 검증(R6.8)을 함께 두어 전제 보장이 실패해도 조용한 성공이 되지 않게 한다.

### D7. 기존 worktree는 중단이 아니라 창 처리로 분기한다

이슈 #28의 "중단한다"는 **중복 worktree나 별칭 브랜치를 만들지 말라**는 뜻이지 창을
열지 말라는 뜻이 아니다. 문자 그대로 전체 중단으로 읽으면 PR 리뷰 창을 두 번째부터
영영 열 수 없어 Goal 2와 R7 전체가 무의미해진다. "생성 단계만 건너뛰고 R7으로 진행"
으로 확정했다(R4.3).

### D8. PR state는 소비하되 자동 중단하지 않는다

`state`를 조회 필드에 넣고 R4.7에서 소비한다. CLOSED·MERGED PR을 사후에 들여다보는
것은 정당한 용도이므로 자동 중단하지 않고 알린 뒤 확인받는다. 저장소 관련 필드는 R4.0이
URL·현재 저장소에서 확정하므로 조회 필드에서 제외했고, fork 여부는 pull ref가 균일
처리하므로 `isCrossRepository`도 넣지 않는다 — 요구만 하고 쓰지 않는 필드는 검증을
형식화한다.

### D9. workmux 버전 표기 불일치를 `dot_claude` 쪽으로 통일한다

이슈 #35는 두 원본이 frontmatter만 다르다고 전제했으나 실측에서 `dot_agents:43`
"0.1.233 실측"과 `dot_claude:46` "0.1.233 확인·0.1.248 재확인"이 다르다. 후자가 현재
설치 버전까지 재확인한 더 정확한 서술이므로 그쪽으로 통일한다.

### D10. 스모크 테스트를 3차까지 나눈다

한 번의 호출로는 R7.3(같은 세션)과 R7.5(다른 세션)를 동시에 태울 수 없다. 두 분기는
상호 배타적이므로 각각의 조건을 만드는 호출이 필요하다.

- 1차 — 신규 생성, 세션 미명시 → R2 우선순위 3, 이름 파생, 내용 검증
- 2차 — 같은 세션 명시 → R7.3의 중복 창 금지
- 3차 — 다른 세션 명시 → R7.5의 이동과 R2.4의 config 갱신

2차를 빼고 3차만 하면 R7.3의 분기 조건이 한 번도 실행되지 않는다.

### D11. 정리 시 `git branch -D`를 조건부로 한다

`remove-worktree/SKILL.md:26`에 따르면 `workmux remove`가 로컬 브랜치까지 지운다.
무조건 실행하면 정리 중 오류가 난다. `git branch --list`로 확인한 뒤 남았을 때만
지운다.

### D12. `move-window-to-session`의 입력 계약에 맞춰 호출한다

그 스킬의 계약은 `<윈도우이름|세션:번호> <대상세션>`이며 내부에서 `{원본세션}:{번호}`,
`{worktree경로}`, `{worktree명}`을 쓴다. 스킬 수정은 비범위이므로 `window_id`를 그대로
넘기지 않고, 호출 직전에 `tmux display-message -p -t "{window_id}"`로 현재
`세션:번호`를 해석해 넘긴다(R7.5).

`window_id`를 거쳐 해석하는 이유는 R7.1 시점과 호출 시점 사이에 다른 창이 열리고 닫혀
번호가 밀렸을 수 있기 때문이다. 이동 후 재확인도 같은 `window_id`로 한다. 그 스킬의
3-(a)가 `window-session`을 갱신하므로 R2.4는 덮어쓰기가 아니라 확인으로 동작한다.

### D13. `description`도 갱신한다

`argument-hint`만 고치면 Claude의 인자 힌트는 맞지만 **라우팅이 바뀌지 않는다.**
`description`은 에이전트가 "이 요청에 이 스킬을 쓸까"를 판단하는 문장이고, 현재 양쪽
파일 모두 브랜치만 언급한다(실측). PR 참조가 유효한 입력이 된 이상 그 문장도 PR과
대상 세션을 포함해야 "PR 31을 2-review에 열어줘"가 스킬에 도달한다. 두 파일의
`description`은 서로 동일하게 유지한다(R9.1의 본문 동일성과 별개로, frontmatter의
`description`은 양쪽 공통 필드다).

### D14. 보존 대상 규칙을 명시적으로 열거한다

Goal 5의 "회귀 없음"은 검증 가능해야 한다. 재작성 과정에서 조용히 사라지기 쉬운 현행
규칙 18개를 R9.6에 열거하고 AC-56으로 확인한다. 특히 5번(git-crypt 필터 있으나 래퍼
없음)은 R6.1의 분기가 래퍼 존재만 보기 때문에 누락되면 R6.2가 금지하는 경로로 조용히
들어간다.

### D15. 스모크 테스트 대상은 dotfiles PR #31이다

PR 번호(31)와 head 브랜치 이슈 번호(30)가 달라 R5.3을 판별하는 가용 케이스다.
2026-08-27 실측으로 `state=OPEN`이고 head 브랜치가 원격에 살아 있음을 확인했으며,
`--dry-run`으로 예상 산출물까지 미리 확인했다. PR #32는 head에 숫자 접두사가 없어
대체 대상이 아니다. #31이 닫혔을 경우의 대체 계획은 Test strategy 3층에 있다.

### D16. git-crypt 경로는 문서 검토 + 래퍼 소스 확인으로 검증한다

실제 검증은 업무 저장소에 1~2GB 규모 부작용을 남긴다. 대신 R4.6의 근거가 되는 래퍼의
브랜치 판별 로직을 소스에서 직접 읽어 확인했고 그 실측을 Problem and context에
기록했다. 이 한계를 보고서에 명시한다.

### 미해결 사항

없다. 모든 중대 결정이 위에 해소되어 있다.
