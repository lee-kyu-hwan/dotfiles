---
name: move-window-to-session
description: Use when moving a tmux window to another session, reorganizing windows across tmux sessions, or splitting workmux worktree windows out of the main session
---

# Move Window To Session

tmux 윈도우를 다른 세션으로 옮기고, 원본 세션의 번호 구멍을 메우고, workmux 기록과
resurrect 저장까지 맞춘다.

**순서가 핵심이다.** `tmux move-window`만 하면 workmux는 옛 세션을 계속 가리키고,
저장 전에 재부팅되면 이동 자체가 사라진다. workmux에는 세션 간 윈도우 이동 명령이
없어서(0.1.243까지 확인) 이 정리를 대신해 줄 도구가 없다 —
`workmux --help`에 그런 명령이 생기면 이 스킬을 그것으로 대체한다.

## 파라미터

- **args** (선택): `<윈도우이름|세션:번호> <대상세션>`
- args가 비어있으면 아래로 목록을 보여주고 사용자에게 선택을 요청한다.

```bash
tmux list-windows -a -F '#{session_name}:#{window_index}  #{window_name}  #{window_panes}p'
```

윈도우 여러 개를 받으면 각각에 대해 실행 순서를 반복하고, resurrect 저장은 **맨 마지막에 한 번만** 한다.

## 이동 전에 잡아둘 것

`move-window`는 배정된 인덱스를 출력하지 않고, 2단계 재정렬이 번호를 또 바꾼다.
그래서 번호로 뒤를 쫓지 않고 **이동에도 불변인 식별자를 미리 잡는다.**
pane id와 window id는 `move-window`로 바뀌지 않는다.

```bash
WID=$(tmux display-message -p -t {원본세션}:{번호} '#{window_id}')   # @N
PANES=$(tmux list-panes -t {원본세션}:{번호} -F '#{pane_id}')        # %N %N ...
```

## 실행 전 필수 확인

이동 전에 확인한다. 사후 복구가 어렵다.

**1. 원본 세션이 비게 되는가**

마지막 윈도우를 옮기면 **원본 세션이 소멸한다.** `detach-on-destroy`가 기본 `on`이라
그 세션에 붙어 있던 클라이언트는 detach되고, 이 저장소는 `.zshrc`에서 `exec tmux`를
하므로 **detach = Ghostty 창이 닫힌다.** 세션을 비울 상황이면 진행 전에 사용자에게 알린다.

```bash
tmux list-windows -t {원본세션} -F '#{window_index}' | wc -l   # 1이면 세션 소멸
tmux list-clients -t {원본세션} -F '#{client_tty} #{client_session}'  # 붙어 있는 클라이언트
```

**2. 대상 세션이 있는가**

`has-session`을 그냥 쓰면 안 된다. tmux 타깃은 **접두사 매칭**을 하므로
`1-maintenance` 세션만 있어도 `has-session -t 1-main`이 exit 0으로 "있음"을 낸다
(실측). 세션명이 순번으로 시작하는 지금은 함정이 더 넓다 — `1-main`만 있어도
`has-session -t 1`이 exit 0이다. 그 상태로 1단계를 실행하면 세션이 새로 생기지도
않고 윈도우가 **엉뚱한 기존 세션으로 조용히 들어간다** — 오타로 세션이 생기는 것보다 나쁘다.
대소문자는 구분하므로(`ZZSRC` → exit 1) 대소문자 오타는 걸러진다.

```bash
tmux list-sessions -F '#{session_name}' | grep -qxF -- '{대상세션}' && echo 있음 || echo 없음
```

없으면 **오타로 엉뚱한 세션이 생기는 것을 막기 위해 이름을 사용자에게 확인받고** 만든다.

```bash
tmux new-session -d -s {대상세션}
```

## 실행 순서

### 1. 이동 — 대상은 `세션:` 형태로만 지정한다

```bash
tmux move-window -s {원본세션}:{번호} -t {대상세션}:
```

`-t {대상세션}:{번호}`처럼 인덱스를 붙이면 그 번호가 쓰이고 있을 때
`index in use: 0`으로 **실패한다.** 콜론까지만 쓰면 빈 번호에 붙는다.
특정 위치에 꽂아야 할 때만 `-a`(뒤에 삽입) / `-b`(앞에 삽입)를 쓴다.

`link-window`는 쓰지 않는다 — 윈도우가 두 세션에 동시에 속하게 되고,
resurrect가 이를 링크로 저장하지 못해 복원 시 윈도우가 중복 생성된다.

### 2. 원본 세션 번호 재정렬

```bash
tmux move-window -r -t {원본세션}:
```

`renumber-windows on`은 윈도우를 **닫을 때만** 발동하므로 이동 자리는 구멍으로 남는다.
그리고 `-r`은 **`-t`가 가리키는 세션**을 재정렬한다 — `-r -s {원본세션}:0`은 조용히
아무 일도 하지 않는다.

### 3. workmux 기록 동기화 (workmux 윈도우일 때만)

윈도우가 workmux worktree면 **두 곳**이 옛 세션명을 붙들고 있다. 둘 다 고친다.

`{worktree명}`은 **`workmux list`의 `PATH` 열 basename(= 디렉터리명)**이다.
`BRANCH` 열이나 tmux 윈도우 이름에서 유추하지 않는다 — 셋이 다 다를 수 있고
(디렉터리 `fix-worktree-issue-window-name` ↔ 브랜치 `codex-pr-review-toolkit`),
틀린 이름을 넘겨도 git은 **에러 없이** 새 섹션을 만들어 버린다. 실제 키는 옛 세션명을
그대로 유지하므로 이 단계가 막으려던 실패가 그대로 남고 config에 쓰레기까지 쌓인다.

```bash
# (a) git config — workmux가 close/remove/open에서 윈도우를 찾는 근거
git -C {worktree경로} config workmux.worktree.{worktree명}.window-session {대상세션}

# (b) agent state — dashboard·last-done·last-agent 표시의 근거
d="$HOME/.local/state/workmux/agents"
sock=$(tmux display-message -p '#{socket_path}')
boot=$(tmux display-message -p '#{start_time}')
for p in $PANES; do
  for f in "$d"/tmux__*.json; do
    [ -e "$f" ] || continue
    [ "$(jq -r '.pane_key.pane_id // ""' "$f")" = "$p" ] || continue
    [ "$(jq -r '.pane_key.instance // ""' "$f")" = "$sock" ] || continue  # 다른 tmux 서버
    [ "$(jq -r '.boot_id // ""' "$f")" = "$boot" ] || continue            # 이전 부팅 = resurrect 입력
    if jq --arg s "{대상세션}" --arg w "$(tmux display-message -p -t "$p" '#{window_name}')" \
         '.session_name = $s | .window_name = $w' "$f" > "$f.tmp" && mv -- "$f.tmp" "$f"; then
      echo "synced workmux agent state: $p → {대상세션}"
    else
      rm -f -- "$f.tmp"
      echo "state 갱신 실패: $f" >&2
    fi
  done
done
```

**살아있는 pane의** state 파일은 삭제하지 않고 갱신한다. 지우면 에이전트 상태
(윈도우 탭의 🤖/💬/✅, `prefix + G`의 `last-done` 대상)가 사라진다. 죽은 pane의
고아 state를 지우는 것은 `remove-worktree` 스킬의 별개 절차다.

돌고 있는 에이전트는 다음 status 이벤트에 `session_name`을 스스로 다시 쓰는 것으로
보인다(`updated_ts`가 초 단위로 갱신된다). 확실히 이 블록이 필요한 대상은 이벤트가
멈춘 **idle·done 기록**이다 — 그래도 전부 돌리는 편이 안전하고 비용도 없다.

`instance`·`boot_id` 가드는 `remove-worktree` 스킬의 고아 정리와 같은 이유로 둔다 —
다른 tmux 서버의 state를 건드리지 않고, 이전 부팅 state(`workmux resurrect`의 입력)를
망가뜨리지 않는다.

mode 자체를 세션으로 바꾸고 싶다면 이 스킬이 아니라 `workmux open {이름} --session`이다.
다만 두 가지를 알고 써야 한다.

- `--session`은 **mode 변경을 영구 저장한다.** 그 뒤로는 `--parent-session`이
  `--parent-session requires window mode`로 거부되므로, `create-worktree`가 쓰는
  조합이 깨진다. 되돌리려면 `--mode window`가 필요하다.
- workmux가 레이아웃을 다시 구성하므로 **돌고 있는 에이전트가 유지되지 않는 것으로
  보인다** — 문서에 명시가 없어 확인하지 못했다. 에이전트를 살린 채 옮기는 것이
  목적이면 이 스킬의 `move-window`를 쓴다.

### 4. resurrect 즉시 저장

```bash
"$(tmux show-options -gv @resurrect-save-script-path)"
```

continuum 자동 저장은 15분 주기라, 저장 전에 재부팅되면 이동 전 배치로 복원된다.
경로를 하드코딩하지 말고 위 옵션에서 읽는다 — 플러그인 설치 경로(TPM / 패키지 매니저)가
머신마다 다르다. 저장 내용이 직전 저장과 같으면 resurrect가 방금 쓴 파일을 지우므로
새 `.txt`가 안 생길 수 있다. 정상이니 실패로 읽지 않는다.

### 5. 마무리 보고

```bash
tmux display-message -p -t "$WID" '옮긴 윈도우: #{session_name}:#{window_index} #{window_name}'
tmux list-windows -a -F '#{session_name}:#{window_index}  #{window_name}'
```

`$WID`로 조회하면 이름이 같은 윈도우가 둘 있어도 옮긴 그 윈도우를 정확히 짚는다.

옮긴 윈도우의 새 위치, 원본 세션의 번호 상태, 원본 세션이 소멸했는지를 보고한다.

## 함정

| 증상 | 원인 | 대응 |
|------|------|------|
| `index in use: 0` | 대상 인덱스가 점유됨 | `-t {세션}:`으로 콜론까지만 지정 |
| 원본에 번호 구멍 | `renumber-windows`는 close에만 발동 | `move-window -r -t {원본}:` |
| `-r`이 먹지 않음 | `-s`로 세션을 줬다 / 대상 세션명이 틀렸다 (둘 다 exit 0 무동작) | `-r -t {원본}:` 로 정확한 이름 |
| Ghostty 창이 닫힘 | 마지막 윈도우 이동 → 세션 소멸 → detach → `exec tmux`가 끝남 | 이동 전 잔여 윈도우 수 확인 |
| dashboard가 옛 세션 표시 | agent state의 `session_name` 스테일 | 3-(b) |
| `workmux close/remove`가 윈도우를 못 찾음 | git config `window-session` 스테일 | 3-(a) |
| 재부팅 후 이동이 사라짐 | continuum 저장 주기 15분 | 4 |
| 대상 세션에서 pane이 좁아 보임 | 대상 세션에 attach하는 시점의 클라이언트 크기로 맞춰짐 (`window-size latest`) | 정상. attach하면 해소된다 |

## 사람이 직접 할 때

에이전트 없이 손으로 할 때의 최소 절차. workmux 윈도우가 아니면 이걸로 충분하다.

| 키 | 동작 |
|----|------|
| `prefix` → `.` | 대상 `세션:` 입력 (tmux 기본 `move-window`) |
| `prefix` → `R` | 원본 세션 번호 재정렬 (그 세션 안에서 눌러야 한다) |
| `prefix` → `C-s` | resurrect 즉시 저장 |

workmux worktree 윈도우라면 3번 동기화가 빠지므로 이 스킬을 쓴다.
