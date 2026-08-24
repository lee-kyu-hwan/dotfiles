# tmux 키맵 & 치트시트

Prefix 키: `Ctrl+B` (macOS에서는 자동으로 영문 전환 후 prefix 테이블 진입)

`★` = 커스텀 키맵 (chezmoi로 관리, `dot_tmux.conf.tmpl`에 정의)

## 커스텀 키맵

### 패널 분할 & 기본 조작

| 키 | 기능 | 구분 |
|----|------|------|
| `prefix` → `\|` | 수직 분할 (현재 경로 유지) | ★ |
| `prefix` → `-` | 수평 분할 (현재 경로 유지) | ★ |
| `prefix` → `r` | 설정 리로드 (`tmux.conf` 재적용) | ★ |
| `prefix` → `=` | 아래부터 쌓는 스택 레이아웃 정렬 | ★ |

> 기본 분할 키 `%`/`"`도 여전히 동작하지만, `|`/`-`가 더 직관적입니다.
>
> `prefix → =`는 패인을 **한 행에 최대 3개씩, 아래부터 쌓는** 레이아웃으로 정렬합니다. 6개까지는 2행으로 균등 분배(위 행 ≤ 아래 행), 7개부터는 아래 행을 3개씩 채우고 나머지를 맨 위에 둡니다:
>
> | 패인 수 | 레이아웃(위→아래) | 패인 수 | 레이아웃(위→아래) |
> |---|---|---|---|
> | 2 | `1 + 1` | 7 | `1 + 3 + 3` |
> | 3 | `1 + 2` | 8 | `2 + 3 + 3` |
> | 4 | `2 + 2` | 9 | `3 + 3 + 3` |
> | 5 | `2 + 3` | 10 | `1 + 3 + 3 + 3` |
> | 6 | `3 + 3` | … | … |
>
> tmux 기본 레이아웃에는 없는 배치라, `~/.local/bin/tmux-stack-layout` 스크립트가 패인 개수에 맞춰 레이아웃 문자열을 동적으로 생성한다(`dot_local/bin/`로 관리).

### 윈도우 관리

| 키 | 기능 | 구분 |
|----|------|------|
| `Shift+←` / `Shift+→` | 이전/다음 윈도우 (prefix 불필요) | ★ |
| `Ctrl+Shift+←` / `Ctrl+Shift+→` | 윈도우 순서 왼쪽/오른쪽 이동 | ★ |
| `prefix` → `R` | 윈도우 번호 즉시 재정렬 (빈 번호 메우기) | ★ |

> `renumber-windows on`이 켜져 있어 **윈도우를 닫으면 빈 번호가 자동으로 메워집니다** (예: `0,1,4` → `0,1,2`). `prefix → R`은 닫지 않고도 즉시 재정렬하는 수동 트리거입니다. base-index가 0이라 번호는 0부터 매겨집니다.

### 창 이동 (vim-tmux-navigator)

tmux 패인과 Neovim 창을 구분 없이 이동합니다. prefix 없이 사용.

| 키 | 기능 | 구분 |
|----|------|------|
| `Ctrl+h` | 왼쪽으로 이동 (tmux/vim 공유) | ★ |
| `Ctrl+j` | 아래로 이동 (tmux/vim 공유) | ★ |
| `Ctrl+k` | 위로 이동 (tmux/vim 공유) | ★ |
| `Ctrl+l` | 오른쪽으로 이동 (tmux/vim 공유) | ★ |
| `Ctrl+\` | 직전 패인/창으로 토글 이동 (tmux/vim 공유) | ★ |

### 한글 IME 호환 (macOS only)

> macOS에서 한글 입력 중 `Ctrl+B`를 누르면 macism으로 자동 영문 전환 후 prefix가 작동합니다.
> 창/패인 전환 시에도 자동으로 영문 입력으로 초기화됩니다.

| 키 | 기능 | 구분 |
|----|------|------|
| `Ctrl+B` | prefix (macOS: 영문 전환 + prefix) | ★ |
| `prefix` → `Ctrl+B` | 리터럴 `Ctrl+B` 전송 (중첩 tmux에 prefix 전달) | ★ |
| `prefix` → `:` | 명령어 모드 (영문 자동 전환) | ★ |

> `prefix → Ctrl+B`는 OS별로 정의가 다릅니다. macOS는 `send-keys C-b`(prefix가 `M-F12`라 C-b는 영문 전환 트릭에 쓰임), Linux는 표준 `send-prefix`. 결과는 둘 다 안쪽으로 `Ctrl+B`를 전달합니다.

### 자음 바인딩 (macOS only — 안전망)

> macism 전환이 느릴 때를 대비한 폴백. 한글 입력 상태에서도 동작합니다.

| 키 | 원래 키 | 기능 | 구분 |
|----|---------|------|------|
| `prefix` → `ㅈ` | `w` | 윈도우/세션 트리 | ★ |
| `prefix` → `ㅊ` | `c` | 새 윈도우 | ★ |
| `prefix` → `ㄷ` | `d` | 세션 분리 (detach) | ★ |
| `prefix` → `ㅜ` | `n` | 다음 윈도우 | ★ |
| `prefix` → `ㅍ` | `p` | 이전 윈도우 | ★ |
| `prefix` → `ㅌ` | `x` | 패인 종료 (확인) | ★ |
| `prefix` → `ㅋ` | `z` | 패인 줌 토글 | ★ |
| `prefix` → `ㄴ` | `s` | 세션 목록 (이름순 고정) | ★ |
| `prefix` → `ㅐ` | `o` | 다음 패인으로 이동 | ★ |
| `prefix` → `ㅣ` | `l` | 레이아웃 전환 | ★ |
| `prefix` → `ㅂ` | `q` | 패인 번호 표시 | ★ |
| `prefix` → `ㅅ` | `t` | 시계 모드 | ★ |

### 화면 클리어

| 키 | 기능 | 구분 |
|----|------|------|
| `Ctrl+L` | 오른쪽 패인/창으로 이동 (vim-tmux-navigator) | ★ |
| `prefix` → `Ctrl+L` | 화면 + 스크롤백 클리어 | ★ |

> vim-tmux-navigator가 `Ctrl+L`을 "오른쪽 이동"으로 가져가므로, 화면 클리어는 `prefix + Ctrl+L`로 옮겼습니다.
>
> ⚠️ 단, 플러그인은 보상으로 `prefix C-l`을 `send-keys C-l`(단순 클리어)에 **자동 매핑**하는데, 이게 우리의 `clear-history`(스크롤백 클리어) 바인딩을 덮어쓴다. 이를 막기 위해 플러그인 로드 전에 자동 매핑을 비활성화한다:
> ```tmux
> set -g @vim_navigator_prefix_mapping_clear_screen ""
> ```
> 이 한 줄이 있어야 `prefix + Ctrl+L`의 스크롤백 클리어가 실제로 동작한다. ([vim-tmux-navigator Issue #9](https://github.com/christoomey/vim-tmux-navigator/issues/9))

### 복사 모드 커스텀

OSC 52 클립보드 전달을 켜고, 복사 모드는 Vim 스타일 키로 사용합니다.

| 키 | 기능 | 구분 |
|----|------|------|
| `prefix` → `[` | 복사 모드 진입 | 기본 |
| `v` | 선택 시작 | ★ |
| `y` | 선택 영역 복사 후 종료 | ★ |
| `ㅂ` | 한글 입력 상태에서 복사 모드 종료 (`q` 폴백) | ★ |

마우스 드래그 종료 시 자동 복사는 꺼져 있습니다. 의도하지 않은 클립보드 변경을 피하고 `prefix` → `[` → `v` → `y` 흐름을 사용합니다.

### 비주얼 설정

| 항목 | 설정 | 구분 |
|------|------|------|
| 비활성 패인 배경 | 어둡게 (colour238) | ★ |
| 활성 패인 배경 | 밝게 (colour0) | ★ |
| 패인 테두리 | 비활성 colour238, 활성 colour51 (파란색) | ★ |
| 마우스 지원 | 켜짐 | ★ |
| 상태바 | 세션명, 창 상태, 날짜/시간 표시 | ★ |
| 창 activity 표시 | 출력 중이면 초록 `●` 표시 | ★ |
| 창 silence 표시 | 20초 무출력이면 빨강 `⏸` 표시 | ★ |

### 세션 복원

TPM으로 `tmux-resurrect`, `tmux-continuum`을 사용합니다.

| 항목 | 설정 |
|------|------|
| pane 내용 저장 | 켜짐 |
| 저장 위치 | `~/.local/share/tmux/resurrect` |
| 자동 저장 주기 | 15분 |
| tmux 시작 시 자동 복원 | 켜짐 |

이름 없이 만들어진 `0`번 세션은 `session-created` 훅이 `1-main`으로 개명합니다. 단
`1-main`이 이미 있으면 이 개명은 **조용히 실패**하고(`duplicate session`, 훅 경로에서는
오류가 표시되지 않음) 세션은 `0`이라는 이름으로 남습니다. `.zshrc`가 항상 `-s 1-main`을
지정하므로 통상 흐름에서는 훅이 발동하지 않고, 인수 없이 `tmux`를 직접 실행했을 때만
이 경로를 타게 됩니다. 규칙 밖 이름(`0`, `1`)이 생기면 `prefix → $`로 직접 고칩니다.

### 세션 이름 규칙

세션명은 `{순번}-{이름}` 형식을 씁니다 (`1-main`, `2-review`, `3-personal`,
`4-eslint`, `5-quick`). `prefix → s`가 `choose-tree -Zs -O name`으로 바인딩되어
있어 목록이 **이름순**으로 나오기 때문입니다. tmux의 기본 정렬은 `index`(세션
생성 순)라서 접두사가 없으면 만든 순서대로 섞여 나옵니다.

| 키 | 기능 |
|----|------|
| `prefix` → `s` | 세션 목록 (이름순 고정) |
| 목록 안에서 `O` | 정렬 필드 순환 (`index`/`name`/`activity`/`z`) — 일회성 |
| 목록 안에서 `r` | 정렬 역순 — 일회성 |
| `prefix` → `$` | 세션 이름 변경 |

> 이름순 정렬은 자연 정렬이 아니라 바이트 비교입니다. 그래서 세션이 10개를 넘으면
> `10-`이 `2-` **앞에** 오면서 순번의 의미가 깨집니다. 9개까지는 문제가 없고, 그
> 이상 쓰게 되면 `01-`/`02-` 제로패딩으로 바꿔야 합니다.

> `prefix → w`(윈도우 트리)는 `index` 정렬을 유지합니다. `-O name`은 트리 전체에
> 적용돼 세션 안의 윈도우까지 이름순으로 섞이는데, 윈도우는 번호 순이 맞습니다.
> 대신 `prefix → w`의 **세션 행도 생성 순으로 남습니다** — 순번 접두사는 그쪽
> 목록에서는 순서에 영향을 주지 않습니다.

> 세션 이름을 바꿀 때 함께 고쳐야 하는 곳: `.tmux.conf`의 `session-created` 훅
> (`rename-session`의 대상 이름 — 세션명을 자동으로 결정하는 1차 지점), `~/.zshrc`의
> `exec tmux new-session -A -s 1-main`, `create-worktree`·`move-window-to-session`
> 스킬의 `--parent-session`, workmux의 `workmux.worktree.*.window-session` git
> config, 그리고 이 문서.

### 기존 세션 개명 (구 이름이 남은 머신)

`main`/`quick` 같은 구 이름 세션이 살아 있는 머신에서 새 설정을 적용하면, `-A`는
**이름이 정확히 일치할 때만** 붙기 때문에 빈 `1-main` 세션이 새로 생기고 터미널은
거기에 붙습니다. 기존 작업은 `main`에 그대로 남고 화면에는 아무 경고가 없습니다.

**먼저 상태를 확인합니다.** 절차가 상태에 따라 갈리기 때문입니다.

```bash
tmux list-sessions -F '#{session_name}: #{session_windows}w'
```

**상태 A — `main`만 있음** (새 셸을 아직 열지 않았을 때). 그대로 개명합니다.

```bash
tmux rename-session -t main 1-main
```

**상태 B — `main`과 `1-main`이 함께 있음** (새 셸을 이미 열어 버렸을 때). 이 상태에서
`rename-session -t main 1-main`을 그냥 실행하면 `duplicate session: 1-main`으로
**실패합니다**(exit 1).

`1-main`을 `kill-session`으로 치우는 방식은 **쓰지 않습니다.** `list-windows`로는
그 세션을 지워도 되는지 알 수 없습니다 — 윈도우가 하나여도 여러 Ghostty 클라이언트가
그 하나를 공유할 수 있고, pane 안에 포그라운드 프로세스가 돌고 있을 수 있습니다.
`kill-session`은 붙어 있는 클라이언트를 모두 detach시키고, `.zshrc`가 `exec tmux`를
하므로 **그 터미널 창들이 닫힙니다.**

개명은 비파괴적이고 붙어 있는 클라이언트도 세션을 따라옵니다. 이름만 서로 비켜
주는 방식을 씁니다.

```bash
# 1. 이름을 비켜 준다 (클라이언트와 실행 중 프로세스는 그대로 유지된다)
tmux rename-session -t 1-main 0-migrating
tmux rename-session -t main 1-main

# 2. 임시 세션에 붙어 있던 클라이언트를 새 1-main으로 옮긴다 (detach 없이)
tmux list-clients -t 0-migrating -F '#{client_tty}' \
  | while read -r tty; do tmux switch-client -c "$tty" -t 1-main; done

# 3. 임시 세션에 살릴 것이 있는지 확인한다
tmux list-windows -t 0-migrating -F '#{window_index} #{window_name} #{pane_current_command}'
tmux move-window -s 0-migrating:0 -t 1-main:   # 살릴 것이 있을 때만 (`:`로 대상 세션 명시)

# 4. 클라이언트가 0이고 남길 것이 없을 때만 지운다
tmux list-clients -t 0-migrating -F '#{client_tty}'   # 비어 있어야 한다
tmux kill-session -t 0-migrating
```

3단계에서 마지막 윈도우를 옮겼다면 임시 세션은 그 시점에 스스로 사라지므로 4단계는
`can't find session`이 됩니다. 정상입니다.

**상태 C — `1-main`만 있음.** `main` 쪽은 끝난 상태입니다.

**`quick` 세션은 A/B/C 어느 상태에서도 따로 확인합니다.** `1-main` 개명과 무관하게
남아 있을 수 있고, 방치하면 resurrect가 계속 구 이름으로 저장·복원합니다. 타깃
접두사 매칭 때문에 존재 확인은 정확 매칭으로 해야 합니다.

```bash
tmux list-sessions -F '#{session_name}' | grep -qxF -- quick   && echo "quick 있음"
tmux list-sessions -F '#{session_name}' | grep -qxF -- 5-quick && echo "5-quick 있음"
```

- `quick`만 있으면 `tmux rename-session -t quick 5-quick`.
- 둘 다 있으면 상태 B와 같은 충돌입니다. 위 상태 B 절차를 `quick`/`5-quick`에 그대로
  적용하거나, 어느 쪽을 남길지 정하고 `move-window`로 합칩니다.
- `quick`이 없으면 건너뜁니다.

**workmux 메타데이터도 함께 옮깁니다.** git config의 `window-session` 값은 세션
개명을 따라오지 않습니다. 값이 정확히 `main`인 항목은 규칙 이전의 기본값이므로
`1-main`으로 갱신합니다. 갱신하지 않으면 `create-worktree`의 "예외 1"이 이 값을
의도적인 이동으로 오분류해 `workmux open`이 `main` 세션을 되살립니다.

`main`만이 아닙니다. `review`/`personal`/`eslint`/`quick`도 같은 규칙으로 개명되므로
구 이름 전체를 옮겨야 합니다. 규칙에 맞는 값(`숫자-`로 시작)은 `move-window-to-session`
이 의도적으로 기록한 것이니 건드리지 않습니다.

```bash
# 저장소마다 (worktree들은 .git/config를 공유하므로 한 번이면 됩니다)
git config --get-regexp '^workmux\.worktree\..*\.window-session'

git config --get-regexp '^workmux\.worktree\..*\.window-session' \
  | while read -r k v; do
      case "$v" in
        main)     n=1-main    ;;
        review)   n=2-review  ;;
        personal) n=3-personal;;
        eslint)   n=4-eslint  ;;
        quick)    n=5-quick   ;;
        *) continue ;;          # 규칙에 맞는 값과 알 수 없는 값은 그대로 둔다
      esac
      git config "$k" "$n" && echo "migrated: $k $v → $n"
    done
```

위 `case`에 없는 규칙 밖 값이 남아 있으면(첫 명령의 출력에서 `숫자-`로 시작하지 않는
것) 어느 세션으로 옮길지 직접 정해야 합니다. 그대로 두면 `create-worktree`가 레거시로
판단해 `1-main`으로 되돌립니다.

**workmux는 세션명을 두 곳에 저장합니다.** git config만 고치면 절반입니다. agent
state(`~/.local/state/workmux/agents/*.json`)의 `session_name`은 윈도우 탭의
에이전트 표시, `prefix + G`의 `last-done`, dashboard의 근거이므로 여기도 갱신해야
스테일 표시가 사라집니다 (`move-window-to-session` 스킬의 3-(b)와 같은 저장소).

```bash
command -v jq >/dev/null || { echo "jq가 필요합니다" >&2; return 1 2>/dev/null || exit 1; }

d="$HOME/.local/state/workmux/agents"
sock=$(tmux display-message -p '#{socket_path}')
boot=$(tmux display-message -p '#{start_time}')
rc=0
for f in "$d"/tmux__*.json; do
  [ -e "$f" ] || continue
  [ "$(jq -r '.pane_key.instance // ""' "$f")" = "$sock" ] || continue   # 다른 tmux 서버
  [ "$(jq -r '.boot_id // ""' "$f")" = "$boot" ] || continue             # 이전 부팅 state
  old=$(jq -r '.session_name // ""' "$f")
  case "$old" in
    main)     new=1-main    ;;
    review)   new=2-review  ;;
    personal) new=3-personal;;
    eslint)   new=4-eslint  ;;
    quick)    new=5-quick   ;;
    *) continue ;;
  esac
  if jq --arg s "$new" '.session_name = $s' "$f" > "$f.tmp" && mv -- "$f.tmp" "$f"; then
    echo "synced: $(basename "$f") $old → $new"
  else
    rm -f -- "$f.tmp"
    echo "실패: $f ($old → $new)" >&2
    rc=1
  fi
done
[ "$rc" = 0 ] || echo "일부 state를 갱신하지 못했습니다 — 위 오류를 확인하세요" >&2
```

`echo`를 `jq`/`mv` 성공 조건 안에 둡니다. 밖에 두면 파싱·쓰기·이동 중 무엇이 실패해도
`synced`가 찍혀, 마이그레이션이 끝난 줄 알았는데 dashboard와 `last-done`이 계속 구
세션을 가리키게 됩니다.

`instance`·`boot_id` 가드는 스킬과 같은 이유로 둡니다 — 다른 tmux 서버의 state를
건드리지 않고, `workmux resurrect`의 입력인 이전 부팅 state를 망가뜨리지 않습니다.
그래서 이전 부팅 기록에는 구 이름이 남습니다. 그쪽은 복원 후 이 절차를 한 번 더
돌리면 정리됩니다.

개명 후 `prefix + C-s`로 스냅샷을 다시 저장하고, 구 이름이 담긴 예전 스냅샷은
지웁니다.

```bash
command ls ~/.local/share/tmux/resurrect/     # 구 이름이 담긴 파일 확인
```

재저장하지 않으면 구 스냅샷이 복원될 때 세션이 **이중화**됩니다. resurrect의
`restore.sh`는 스냅샷의 세션명이 현재 세션과 다르면 오류 없이 `new_session`으로
새로 만들기 때문에, 재부팅마다 `1-main`과 `main`이 함께 존재하는 상태가 재생산됩니다.

---

## tmux 기본 치트시트

### 세션

| 명령어 / 키 | 기능 |
|-------------|------|
| `tmux` | 새 세션 시작 |
| `tmux new -s 이름` | 이름 지정 세션 |
| `tmux ls` | 세션 목록 |
| `tmux attach -t 이름` | 세션 붙기 |
| `tmux kill-session -t 이름` | 세션 종료 |
| `prefix` → `d` | 세션 분리 (detach) |
| `prefix` → `s` | 세션 목록 선택 (이름순 고정 — 세션 이름 규칙 참고) |
| `prefix` → `$` | 세션 이름 변경 |

### 윈도우

| 키 | 기능 |
|----|------|
| `prefix` → `c` | 새 윈도우 |
| `prefix` → `n` | 다음 윈도우 |
| `prefix` → `p` | 이전 윈도우 |
| `prefix` → `0-9` | 번호로 윈도우 이동 |
| `prefix` → `w` | 윈도우 목록 트리 |
| `prefix` → `,` | 윈도우 이름 변경 |
| `prefix` → `&` | 윈도우 종료 (확인) |

### 패인

| 키 | 기능 |
|----|------|
| `prefix` → `\|` | 세로 분할 (★ 현재 경로 유지) |
| `prefix` → `-` | 가로 분할 (★ 현재 경로 유지) |
| `prefix` → `%` | 세로 분할 (기본) |
| `prefix` → `"` | 가로 분할 (기본) |
| `prefix` → `방향키` | 패인 이동 |
| `prefix` → `o` | 다음 패인 |
| `prefix` → `x` | 패인 종료 (확인) |
| `prefix` → `z` | 패인 줌 (전체화면 토글) |
| `prefix` → `q` | 패인 번호 표시 → 번호 입력으로 이동 |
| `prefix` → `{` / `}` | 패인 위치 교체 |
| `prefix` → `Space` | 레이아웃 순환 |

### 패인 크기 조절

| 키 | 기능 |
|----|------|
| `prefix` → `Ctrl+방향키` | 1칸씩 조절 |
| `prefix` → `Alt+방향키` | 5칸씩 조절 |

### 복사 모드

| 키 | 기능 |
|----|------|
| `prefix` → `[` | 복사 모드 진입 |
| `q` | 복사 모드 종료 |
| `v` | 선택 시작 (★ Vim 스타일) |
| `y` | 선택 복사 후 종료 (★ Vim 스타일) |
| `Space` | 선택 시작 (기본) |
| `Enter` | 선택 복사 (기본) |
| `prefix` → `]` | 붙여넣기 |
| `/` | 검색 |
| `n` / `N` | 다음/이전 검색 결과 |

### 기타

| 키 / 명령어 | 기능 |
|-------------|------|
| `prefix` → `t` | 시계 표시 |
| `prefix` → `:` | 명령어 모드 |
| `tmux source-file ~/.tmux.conf` | 설정 재로드 |
| `prefix` → `?` | 전체 키바인딩 목록 |
