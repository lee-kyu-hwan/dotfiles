---
name: move-window-to-session
description: Use when moving a tmux window to another session, reorganizing windows across tmux sessions, or splitting workmux worktree windows out of the main session
---

# Move Window To Session

tmux 윈도우를 다른 세션으로 옮기고, 원본 세션의 번호 구멍을 메우고, workmux 기록과
resurrect 저장까지 맞춘다.

**순서가 핵심이다.** `tmux move-window`만 하면 workmux는 옛 세션을 계속 가리키고,
저장 전에 재부팅되면 이동 자체가 사라진다. workmux 0.1.233에는 세션 간 이동 명령이
없어서 이 정리를 대신해 줄 도구가 없다.

## 파라미터

- **args** (선택): `<윈도우이름|세션:번호> <대상세션>`
- args가 비어있으면 아래로 목록을 보여주고 사용자에게 선택을 요청한다.

```bash
tmux list-windows -a -F '#{session_name}:#{window_index}  #{window_name}  #{window_panes}p'
```

윈도우 여러 개를 받으면 각각에 대해 실행 순서를 반복하고, resurrect 저장은 **맨 마지막에 한 번만** 한다.

## 실행 전 필수 확인

이동 전에 확인한다. 사후 복구가 어렵다.

**1. 원본 세션이 비게 되는가**

마지막 윈도우를 옮기면 **원본 세션이 소멸한다.** `detach-on-destroy`가 기본 `on`이라
그 세션에 붙어 있던 클라이언트는 detach되고, 이 저장소는 `.zshrc`에서 `exec tmux`를
하므로 **detach = Ghostty 창이 닫힌다.** 세션을 비울 상황이면 진행 전에 사용자에게 알린다.

```bash
tmux list-windows -t {원본세션} -F '#{window_index}' | wc -l   # 1이면 세션 소멸
tmux list-clients -F '#{client_tty} #{client_session}'          # 붙어 있는 클라이언트
```

**2. 대상 세션이 있는가** (tmux는 대소문자를 구분한다)

```bash
tmux has-session -t {대상세션} 2>/dev/null && echo 있음 || echo 없음
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

```bash
# (a) git config — workmux가 close/remove/open에서 윈도우를 찾는 근거
git -C {worktree경로} config workmux.worktree.{worktree명}.window-session {대상세션}

# (b) agent state — dashboard·last-done·last-agent 표시의 근거
d="$HOME/.local/state/workmux/agents"
sock=$(tmux display-message -p '#{socket_path}')
boot=$(tmux display-message -p '#{start_time}')
for p in $(tmux list-panes -t {대상세션}:{새번호} -F '#{pane_id}'); do
  for f in "$d"/tmux__*.json; do
    [ -e "$f" ] || continue
    [ "$(jq -r '.pane_key.pane_id // ""' "$f")" = "$p" ] || continue
    [ "$(jq -r '.pane_key.instance // ""' "$f")" = "$sock" ] || continue  # 다른 tmux 서버
    [ "$(jq -r '.boot_id // ""' "$f")" = "$boot" ] || continue            # 이전 부팅 = resurrect 입력
    jq --arg s "{대상세션}" --arg w "$(tmux display-message -p -t "$p" '#{window_name}')" \
      '.session_name = $s | .window_name = $w' "$f" > "$f.tmp" && mv -- "$f.tmp" "$f"
    echo "synced workmux agent state: $p → {대상세션}"
  done
done
```

state 파일은 **삭제하지 않고 갱신한다.** 지우면 살아있는 pane의 에이전트 상태
(윈도우 탭의 🤖/💬/✅, `prefix + G`의 `last-done` 대상)가 사라진다.

`instance`·`boot_id` 가드는 `remove-worktree` 스킬의 고아 정리와 같은 이유로 둔다 —
다른 tmux 서버의 state를 건드리지 않고, 이전 부팅 state(`workmux resurrect`의 입력)를
망가뜨리지 않는다.

worktree 경로와 이름은 `workmux list`로 확인한다. mode 자체를 세션으로 바꾸고 싶다면
이 스킬이 아니라 `workmux open {이름} --session`이다 — 다만 그건 pane을 다시 띄우므로
**돌고 있는 에이전트가 유지되지 않는다.** 에이전트를 살린 채 옮기는 게 목적이면
이 스킬의 `move-window`가 맞다.

### 4. resurrect 즉시 저장

```bash
"$(tmux show-options -gv @resurrect-save-script-path)"
```

continuum 자동 저장은 15분 주기라, 저장 전에 재부팅되면 이동 전 배치로 복원된다.
경로를 하드코딩하지 말고 위 옵션에서 읽는다(`@resurrect-dir`이 기본값이 아니다).

### 5. 마무리 보고

```bash
tmux list-windows -a -F '#{session_name}:#{window_index}  #{window_name}'
```

옮긴 윈도우의 새 위치, 원본 세션의 번호 상태, 원본 세션이 소멸했는지를 보고한다.

## 함정

| 증상 | 원인 | 대응 |
|------|------|------|
| `index in use: 0` | 대상 인덱스가 점유됨 | `-t {세션}:`으로 콜론까지만 지정 |
| 원본에 번호 구멍 | `renumber-windows`는 close에만 발동 | `move-window -r -t {원본}:` |
| `-r`이 먹지 않음 | `-s`로 세션을 줬다 | `-r`은 `-t` 세션을 재정렬한다 |
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
