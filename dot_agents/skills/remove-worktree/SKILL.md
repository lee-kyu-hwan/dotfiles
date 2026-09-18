---
name: remove-worktree
description: Use when removing a git worktree and its tmux window after finishing work on a branch
---

# Remove Worktree

workmux로 worktree와 tmux 윈도우를 함께 제거한다.

## 파라미터

- **args** (선택): worktree 이름 = `workmux list`의 `PATH` 열 basename (= 디렉토리명).
  **tmux 윈도우 이름에서 유추하지 않는다.** `workmux remove`와 `close`는 디렉토리명만
  받는데, 윈도우 이름은 `--target-name`이나 브랜치명 슬러그에서 나와 디렉토리명과 다르다
  (윈도우 `worktree-issue-window-name` ↔ 디렉토리 `fix-worktree-issue-window-name`).
- args가 비어있으면 `workmux list`로 목록을 보여주고 사용자에게 선택을 요청한다.
  제거할 worktree 안에서 실행할 때는 인자를 생략하면 현재 디렉토리가 대상이 된다.

## 정리 대상 판정

어느 worktree를 지울지 고를 때는 **`git branch --merged`를 정본**으로 삼되, **이슈 상태
(OPEN/CLOSED)와 main 대비 고유 커밋 수를 함께 표시**해 사용자가 판단할 재료를 준다.
한 기준만 보면 오판한다.

- PR 머지 기록을 보는 도구(Orca UI 등)는 **PR 없이 로컬에서 머지한** 브랜치를 놓친다.
  2026-09-18 정리에서 `--merged`는 11개, Orca UI는 7개를 머지로 판정했다.
- 머지된 브랜치의 고유 커밋 수는 정의상 0이다. 그래서 **머지됨 + 고유 커밋 0**만으로는
  "작업이 main에 들어갔다"와 "이 브랜치에서 작업한 적이 없다"(갓 만든 worktree, 실제 작업은
  다른 브랜치·PR로 나간 경우)를 가르지 못한다. 이슈 상태와 브랜치 끝 커밋(`TIP`)을 같이
  보고, 이슈가 OPEN이면 지우기 전에 사용자에게 확인한다. `TIP`이 `Merge pull request #148 …`
  처럼 다른 작업의 머지 커밋이면 이 브랜치에는 자기 작업이 없다.
- 머지되지 않은 브랜치의 고유 커밋 수는 **지우면 잃는 커밋 수**다.

```bash
BASE=main   # 로컬 기준이다. PR 머지 후 main을 pull하지 않았다면 먼저 pull한다
merged=$(git branch --merged "$BASE" --format='%(refname:short)')   # 정본
printf 'WORKTREE\tMERGED\tISSUE\tUNIQUE\tTIP\n'
workmux list --json \
  | jq -r '.[] | select(.is_main | not) | [(.path | split("/") | last), .branch] | @tsv' \
  | while IFS=$'\t' read -r name b; do
      m=no; printf '%s\n' "$merged" | grep -qxF -- "$b" && m=yes
      n=$(printf '%s' "$b" | grep -oE '^[0-9]+')                    # 브랜치명 앞 숫자 = 이슈 번호
      s=$([ -n "$n" ] && gh issue view "$n" --json state -q .state </dev/null 2>/dev/null)
      printf '%s\t%s\t%s\t%s\t%s\n' "$name" "$m" "${s:--}" "$(git rev-list --count "$BASE..$b")" \
        "$(git log -1 --format=%s "$b" | cut -c1-50)"
    done
```

## 선행 확인 (삭제 전)

`workmux remove` 전에 대상 worktree마다 아래 세 가지를 확인한다. **하나라도 출력이 있으면
사용자에게 보고하고 중단한다.** `workmux remove`의 미커밋 경고는 `git status` 기준이라
`.gitignore` 대상을 보지 못하고, `workmux list`의 AGENT 열은 고아 state나 등록되지 않은 창
때문에 비어 보일 수 있어서 둘 다 이 확인을 대신하지 못한다.

```bash
NAME={이름}   # worktree 안에서 인자 없이 지울 때는 WT=$(git rev-parse --show-toplevel)
WT=$(workmux list --json | jq -r --arg n "$NAME" '.[] | select(.path | endswith("/" + $n)) | .path')
MAIN=$(workmux list --json | jq -r '.[] | select(.is_main) | .path')
: "${WT:?STOP — worktree를 찾지 못함. NAME을 확인한다}"   # 빈 WT로 계속하면 3이 모든 pane을 잡는다
BRANCH=$(git -C "$WT" branch --show-current)   # remove가 로컬 브랜치를 지우므로 미리 잡아 둔다
devdocs() { find "$1/docs/development" -type f ! -name .DS_Store 2>/dev/null | sed "s|^$1/||" | sort; }

# 1. quality-state — .gitignore 대상이라 git status에 뜨지 않고 worktree와 함께 사라진다
[ -d "$WT/.claude/quality-state" ] && du -sh "$WT/.claude/quality-state" \
  && find "$WT/.claude/quality-state" -mindepth 1 -maxdepth 1

# 2. main에 없는 개발 기록 — quality-goal이 docs/development/에 만들지만 커밋은 지시하지 않는다
comm -23 <(devdocs "$WT") <(devdocs "$MAIN")

# 3. 살아있는 에이전트 — AGENT 열이 아니라 실제 명령으로 판정한다. 셸이 아니면 살아있다고 본다
#    (Claude Code는 pane 명령이 `2.1.275` 같은 버전 문자열로 보인다)
tmux list-panes -a -F '#{session_name}:#{window_index}.#{pane_index}|#{pane_current_command}|#{pane_current_path}' 2>/dev/null \
  | awk -F'|' -v wt="$WT" '($3 == wt || index($3, wt "/") == 1) && $2 !~ /^-?(zsh|bash|sh|fish)$/'
#    tmux 밖(Orca 터미널 등)에서 도는 프로세스는 cwd로 잡는다
lsof -d cwd -F pcn 2>/dev/null | awk -v wt="$WT" '
  /^p/ {pid = substr($0, 2)} /^c/ {cmd = substr($0, 2)}
  /^n/ {p = substr($0, 2); if ((p == wt || index(p, wt "/") == 1) && cmd !~ /^-?(zsh|bash|sh|fish|lsof|awk)$/) print pid, cmd, p}'
```

걸렸을 때:

- **1** — 보존 여부를 사용자에게 묻는다. 보존은 저장소 밖 `~/.local/share/quality-goal-archive/<worktree명>/`
  으로 복사하는 것이 관례다(#127). 2026-09-18 정리에서 이 확인 없이 지워 실행 기록 39건이 9건으로 줄었다.
- **2** — main으로 옮겨 커밋할지 사용자에게 묻는다. 같은 정리에서 worktree 8개의 기록 41파일을
  수동으로 옮겨 살렸다.
- **3** — 에이전트를 끝낼지 사용자에게 묻는다. 지금 세션이 그 worktree 안에서 돌고 있으면
  자기 자신과 그 자식 프로세스(`node`·`caffeinate` 등)도 잡히므로 빼고 판단한다.

`ls`는 alias(eza 등)로 바뀌어 있을 수 있어 쓰지 않는다. 셸 상태는 명령 호출마다 초기화될 수
있으므로 변수와 `devdocs`는 호출할 때마다 다시 정의한다.

## 실행 순서

```bash
workmux list                      # 대상 확인
workmux remove {이름}             # worktree + tmux 윈도우 + 로컬 브랜치
# 그리고 아래 "고아 agent state 정리"를 반드시 실행한다
```

`workmux remove`는 기본적으로 **확인 프롬프트를 띄우고 미커밋 변경이 있으면 경고**한다.
그 프롬프트를 `-f`로 우회하지 않고 사용자에게 직접 확인받는다.

이 경고는 `git status` 기준이라 `.gitignore` 대상인 `.claude/quality-state/`를 잡지 못한다.
**`workmux remove` 앞에는 위 선행 확인을, 뒤에는 아래 사후 정리를 반드시 실행한다.**

## 고아 agent state 정리 (workmux 0.1.233 버그 우회)

**`workmux remove`·`close` 후에는 반드시 아래를 실행한다.** 안 하면 dashboard·sidebar·
`workmux status`가 **전부** 빈 화면이 된다.

```bash
d="$HOME/.local/state/workmux/agents"
live=$(tmux list-panes -a -F '#{pane_id}') || live=""
if [ -d "$d" ] && [ -n "$live" ]; then
  sock=$(tmux display-message -p '#{socket_path}')
  boot=$(tmux display-message -p '#{start_time}')
  for f in "$d"/tmux__*.json; do
    [ -e "$f" ] || continue
    [ "$(jq -r '.pane_key.instance // ""' "$f")" = "$sock" ] || continue  # 다른 tmux 서버
    [ "$(jq -r '.boot_id // ""' "$f")" = "$boot" ] || continue            # 이전 부팅 = resurrect 입력
    p=$(jq -r '.pane_key.pane_id // ""' "$f")
    printf '%s\n' "$live" | grep -qxF -- "$p" && continue                 # 살아있는 pane
    rm -f -- "$f" && echo "pruned stale workmux agent state: $p"
  done
fi
```

**왜 필요한가:** `remove`·`close`는 tmux 윈도우만 kill하고 agent state 파일은 지우지
않는다. 원래는 reconcile이 나중에 수거하지만, v0.1.233의 `51bd57c6`(#209 수정)이 그
수거 경로를 깨뜨렸다 — 없는 pane을 조회하면 tmux는 exit 0으로 빈 필드를 돌려주는데
workmux가 이를 "판단 불가"로 보고 열거 **전체**를 에러로 중단한다. 그래서 **에이전트가
돌던 worktree를 제거할 때마다 고아 파일이 하나씩 쌓이고 그 즉시 모든 뷰가 빈다.**
`reap-agents`는 탈출구가 아니다 — 오래된 agent **프로세스**를 종료하는 명령이고
state 파일은 지우지 않는다.

두 가드는 workmux의 reconcile 로직을 그대로 따른 것이므로 **지우지 말 것**:
- `instance` 비교 — 다른 tmux 서버의 state를 건드리지 않는다
- `boot_id` 비교 — tmux/컴퓨터 크래시 후 남은 이전 부팅의 state는 `workmux resurrect`의
  입력이다. 지우면 복구가 불가능해진다

**삭제 조건은 upstream이 아니라 설치 버전이다.**
[raine/workmux#213](https://github.com/raine/workmux/issues/213)은 upstream
v0.1.234(2026-08-04)에서 이미 고쳐졌지만, 이 우회책은 **0.1.233에 고정된 머신**에
필요하다. upstream 기준으로 읽고 지우면 `remove` 한 번에 모든 뷰가 비는 상태로
되돌아간다. 아래가 참일 때만 이 섹션 전체를 삭제한다.

```bash
workmux --version   # 0.1.234 이상이면 이 섹션은 죽은 코드다
```

관련: 0.1.233은 `--parent-session`에 넘긴 세션명의 대소문자를 보존하지 않는다
(v0.1.234에서 수정). `1-main`은 소문자라 현재 영향은 없다.

### 자주 쓰는 변형

| 상황 | 명령 |
|------|------|
| 브랜치는 남기고 worktree·윈도우만 | `workmux remove {이름} -k` |
| 윈도우만 닫고 worktree 유지 | `workmux close {이름}` |
| PR 머지 후 upstream이 사라진 것 일괄 | `workmux remove --gone` |
| 머지하면서 정리까지 | `workmux merge {이름}` |

## git-crypt 저장소에서도 그대로 쓴다

제거는 checkout을 하지 않아 smudge 필터가 개입하지 않으므로, **생성과 달리 특별한
우회가 필요 없다.** 저장소에 `scripts/remove-worktree.sh`가 있어도 `workmux remove`를
쓴다 — 그 스크립트는 worktree 삭제와 prune만 하고 tmux 윈도우는 정리하지 않는다.

저장소별 정리 작업이 필요하면 스킬이 아니라 `.workmux.yaml`의 `pre_remove` 훅에 넣는다.

## 사후 정리

`workmux remove`는 worktree, handle에 등록된 창 하나, 로컬 브랜치만 지운다. 아래 세 가지는
남으므로 위 "고아 agent state 정리" 다음에 직접 확인한다. 선행 확인의 변수(`WT`·`MAIN`·
`BRANCH`)와 `devdocs`를 그대로 쓴다.

```bash
: "${WT:?선행 확인의 변수를 먼저 정의한다}"
PARENT=$(dirname "$WT")   # worktree들의 상위 디렉토리 (예: ~/code/dotfiles__worktrees)

# 4. trash 잔여 — remove가 trash로 옮긴 뒤 못 지운 worktree 사본. quality-goal의 contract-pin이
#    읽기 전용(dr-xr-xr-x)이라 rm -rf만으로는 Permission denied로 실패한다
find "$PARENT" -maxdepth 1 -name '.workmux_trash_*' | while IFS= read -r t; do
  if [ -d "$t/.claude/quality-state" ]; then echo "보류(quality-state 있음): $t"; continue; fi
  if [ -n "$(comm -23 <(devdocs "$t") <(devdocs "$MAIN"))" ]; then echo "보류(main에 없는 기록): $t"; continue; fi
  chmod -R u+w "$t" && rm -rf "$t" || echo "삭제 실패: $t"
done
find "$PARENT" -maxdepth 1 -name '.workmux_trash_*'   # 보류한 것 말고 남은 게 있으면 실패다

# 5. 고아 pane — 같은 worktree에서 따로 연 러너·감시 창은 remove가 닫지 않는다.
#    삭제된 경로를 cwd로 가진 pane을 찾는다 (경로가 빈 pane은 판단할 수 없어 건너뛴다)
tmux list-panes -a -F '#{session_name}:#{window_index}.#{pane_index}|#{pane_current_command}|#{pane_current_path}' 2>/dev/null \
  | while IFS='|' read -r target cmd p; do [ -n "$p" ] && [ ! -d "$p" ] && echo "$target $cmd $p"; done

# 6. 원격 브랜치 — remove는 로컬 브랜치만 지운다
[ -n "$BRANCH" ] && git -C "$MAIN" ls-remote --exit-code --heads origin "$BRANCH" >/dev/null && echo "원격에 남음: $BRANCH"
```

- **4** — trash는 선행 확인을 거치지 않은 옛 사본일 수 있다. quality-state나 main에 없는 기록이
  있으면 지우지 않고 선행 확인 1·2처럼 보고한다. 삭제가 조용히 실패하면 trash가 계속 쌓이므로
  마지막 `find`로 남은 것을 확인한다.
- **5** — 사용자 확인 후 `tmux kill-pane -t <target>`으로 닫는다. 창의 pane이 전부 고아면
  `tmux kill-window -t <세션:창>`. 2026-09-18에 `105-fix`를 지운 뒤 `105-qg-runner` 창이
  이렇게 남았다.
- **6** — 아래가 전부 참일 때만 사용자 확인 후 `git -C "$MAIN" push origin --delete "$BRANCH"`로 지운다.
  원격 삭제는 되돌리기 어렵고 다른 사람에게도 보인다. `-k`로 브랜치를 남겼거나 `--gone`으로
  지웠다면 건너뛴다.
  - 정리 대상 판정에서 `MERGED`가 yes였다
  - 원격에만 있는 커밋이 없다: `git -C "$MAIN" fetch origin "$BRANCH" && git -C "$MAIN" rev-list --count main..FETCH_HEAD`가 0
  - 열린 PR이 없다: `$MAIN`에서 `gh pr list --head "$BRANCH" --state open`이 비어 있다. head
    브랜치를 지우면 PR이 닫힌다

지운 worktree 안에서 돌던 셸은 cwd가 사라져 git·gh가 동작하지 않으므로 git은 `-C "$MAIN"`으로,
gh는 `$MAIN`에서 실행한다. 처리 결과(지운 trash, 닫은 pane, 지운 원격 브랜치, 보류한 항목)를
마무리 보고에 함께 적는다.

## 마무리

`workmux list`로 최종 상태를 안내한다. 삭제된 항목이 목록에서 사라졌는지 확인한다.

**`workmux list`만으로는 위 고아 state 실패를 잡을 수 없다.** 고아가 있어도 표는
정상처럼 exit 0으로 출력되고 AGENT 열만 조용히 빈다. `workmux status`는 에러를
찍으면서도 exit 0을 반환하므로 종료 코드로도 구분되지 않는다. 문자열로 확인한다.

```bash
workmux status 2>&1 | grep -q '^Error:' && echo "고아 state 남음 — prune 재실행 필요"
```

## 주의사항

- `-f`(강제)는 미커밋 변경을 무시하므로 사용자가 명시적으로 요청할 때만 쓴다.
- `--all`은 메인 worktree를 제외한 전부를 지운다. 사용자가 명시적으로 요청할 때만 쓴다.
