---
name: create-worktree
description: Use when creating a new git worktree for a branch to work on in isolation from the main workspace
argument-hint: <branch-name>
user-invocable: true
allowed-tools: Bash
---

# Create Worktree

git worktree를 만들고 workmux로 tmux 윈도우를 연다. pane 레이아웃은
`~/.config/workmux/config.yaml`(좌 nvim / 우상 / 우하)이 담당하므로 여기서
tmux를 직접 조작하지 않는다. 새 workmux 윈도우는 `1-main` 세션에 연다
(이미 다른 세션으로 옮겨 둔 worktree는 예외 — 아래 "부모 tmux 세션" 참조).

## 파라미터

- **args** (필수): 브랜치명 (예: `278-feat/chat-infrastructure`, `ZF-100-feat/login`)
- args가 비어있으면 사용자에게 브랜치명을 물어본다.

## 부모 tmux 세션

window mode의 `workmux add`와 `workmux open` 호출에 `--parent-session 1-main`을
넘긴다. 실행 중인 에이전트가 `3-personal` 같은 다른 세션에 있어도 현재 세션을 부모로
사용하지 않는다.

```bash
tmux list-sessions -F '#{session_name}'    # 종료 코드를 먼저 본다
```

`list-sessions`가 exit 1 + `error connecting to ...`로 실패하면 tmux 서버 자체가 없는
것이다. "세션이 없다"와 구분해 그대로 보고한다 — `grep`에 바로 물리면 두 상황이 똑같이
"없음"으로 뭉개져 사용자가 엉뚱한 안내를 받는다.

```bash
tmux list-sessions -F '#{session_name}' | grep -qxF -- 1-main && echo 있음 || echo 없음
```

`has-session -t 1-main`을 쓰지 않는 이유: tmux 타깃은 접두사 매칭을 하므로
`1-maintenance` 세션만 있어도 exit 0을 낸다(실측). 순번 접두사를 쓰는 지금은 함정이
더 넓다 — `1-main`만 있어도 `has-session -t 1`이 exit 0이다. 없는데 있다고 판정하면
아래 오류 처리가 발동하지 않는다.

`1-main` 세션이 없으면 **여기서 멈춘다.** 현재 세션으로 대체하지 말고 사용자에게
오류를 알린다. 이 체크를 건너뛰면 안전망이 없다 — workmux는 `--parent-session`에 없는
세션명을 받으면 **오류 없이 그 세션을 새로 만들고**(rc=0, 0.1.233 실측) 그 값을
`workmux.worktree.{이름}.window-session` git config에 영구 저장한다. 그러면 아래
"예외 1"이 그 잘못된 값을 "의도적으로 옮긴 것"으로 승격시켜, 이후 모든 `workmux open`이
유령 세션을 계속 존중한다. 자기 교정 경로가 없다.

**예외 1 — 이미 옮겨 둔 worktree.** `workmux open`은 기존 worktree도 여는 명령이다.
git config의 `workmux.worktree.{이름}.window-session`이 `1-main`이 아니면 그것은
`move-window-to-session`으로 **의도적으로 옮긴** 것이므로, `--parent-session`을
생략해 그 값을 존중한다. 무조건 붙이면 옮겨 둔 창을 조용히 `1-main`으로 되끌고 온다.

```bash
git -C {worktree경로} config --get workmux.worktree.{이름}.window-session
```

**예외 2 — 지원되지 않는 조합.** `--parent-session`은 session mode, 샌드박스 안,
그리고 여러 worktree를 한 번에 만드는 경우(`--count`, `--foreach`, 여러 `--agent`,
stdin)에는 거부된다. 그때는 생략한다.

## 실행 순서

저장소가 **래퍼 스크립트를 제공하는지**로 경로가 갈린다. 판정은 저장소 루트를 기준으로
한다 — 상대 경로로 판정하면 서브디렉터리나 기존 worktree 안에서 스킬을 부를 때 false가
되어, git-crypt 저장소인데도 아래에서 금지하는 `workmux add` 경로로 빠진다.

```bash
ROOT=$(git rev-parse --show-toplevel)
[[ -f "$ROOT/scripts/create-worktree.sh" ]] && echo "스크립트 경로" || echo "workmux 경로"
git -C "$ROOT" config --get filter.git-crypt.smudge   # 값이 있으면 git-crypt 저장소
```

스크립트가 있는데 실행 권한이 없으면 경로를 바꾸지 말고 그 사실을 오류로 알린다.
`git-crypt` 필터가 설정되어 있는데 스크립트가 없으면 사용자에게 확인받고 진행한다.

### 스크립트가 있을 때 (git-crypt 저장소)

`workmux add`를 쓰지 않는다. workmux는 내부적으로 `git worktree add`를 실행하는데,
git-crypt 저장소에서는 그것이 smudge 필터 에러로 **실패한다**. 아래 `--no-checkout`
서술은 이 git-crypt 경로에 대한 것이다 — 래퍼의 비-git-crypt 분기는 평범한
`git worktree add`를 쓴다.

```bash
./scripts/create-worktree.sh {브랜치명}    # --no-checkout 생성·키 링크·체크아웃 + 의존성 설치
workmux open {디렉토리명} --target-name {윈도우이름} --parent-session 1-main  # 이슈 번호가 있을 때
workmux open {디렉토리명} --parent-session 1-main                          # 이슈 번호가 없을 때
```

- **스크립트가 실패하면 여기서 멈춘다.** 종료 코드를 확인하고, 실패했으면
  `workmux open`으로 넘어가지 않는다. 스크립트는 worktree를 `--no-checkout`으로 만든 뒤
  키 링크·체크아웃·의존성 설치를 하므로 뒤쪽에서 죽어도 worktree는 남는다 — 그 상태로
  `workmux open`을 실행하면 성공해버려서 파일이 암호화된 채이거나 의존성이 없는
  worktree를 정상으로 보고하게 된다.
- 스크립트의 확인 프롬프트는 `-y`나 `yes |`로 우회하지 않고 사용자에게 직접 확인받는다.
- **스크립트 출력에서 worktree 절대경로를 확보한다.** `workmux open`에 넘길
  디렉토리명은 그 경로의 basename이다 (아래 "이름 파생" 참조).
- `workmux open`은 `git worktree list`로 worktree를 찾으므로 `worktree_dir` 밖의
  형제 디렉토리도 그대로 인식한다.

### 스크립트가 없을 때

workmux가 생성과 윈도우 구성을 한 번에 한다.

```bash
workmux add {브랜치명} --target-name {윈도우이름} --parent-session 1-main  # 이슈 번호가 있을 때
workmux add {브랜치명} --parent-session 1-main                          # 이슈 번호가 없을 때
```

## 이름 파생

- **짧은 이름**: 브랜치명에서 마지막 `/`까지를 제거한다.
  `392-feat/add-partner-chat-enabled` → `add-partner-chat-enabled`
- **이슈 번호**: 브랜치명 **맨 앞**의 숫자 또는 `ZF-숫자`만 인식한다. 맨 앞이 아니면
  이슈 번호가 아니다 — `feat/392-add-x`는 이슈 번호가 없는 것으로 본다.
- **윈도우이름**: 이슈 번호가 있을 때만 `{이슈번호}-{짧은이름}`을 만들어
  `--target-name`에 넘긴다. **이슈 번호가 없으면 `--target-name`을 생략한다.**
  짧은 이름만 넘기는 것은 어느 경로에서도 하지 않는다 — 브랜치 prefix와 저장소
  이름을 모두 잃어 충돌 확률만 높아진다.

  | 브랜치 | `--target-name` | `add` 경로 윈도우 | `open` 경로 윈도우 |
  | --- | --- | --- | --- |
  | `392-feat/add-partner-chat-enabled` | `392-add-partner-chat-enabled` | `392-add-partner-chat-enabled` | 같음 |
  | `ZF-115-chore/some-feature` | `ZF-115-some-feature` | `zf-115-some-feature` | 같음 |
  | `fix/login-bug` | 생략 | `fix-login-bug` | `zambaguni-front-login-bug` |

  생략했을 때 workmux가 쓰는 기본 이름은 경로마다 다르다.
  `workmux open`은 넘긴 디렉토리명(`{repo명}-{짧은이름}`)을 그대로 써서 저장소 이름이
  들어가지만, `workmux add`는 브랜치명 슬러그를 써서 저장소 이름이 **없다**. 그래서
  `add` 경로에서는 두 저장소가 같은 브랜치명을 쓰면 두 번째가
  `✗ A tmux window named '...' already exists`로 실패한다 — 그때는
  `--target-name {repo명}-{짧은이름} --parent-session 1-main`으로 재시도한다.

  workmux는 target name을 소문자로 정규화한다. 사용자에게 안내하거나 이후 명령에
  재사용할 이름은 정규화된 소문자 쪽이다.
- **디렉토리명**: 스크립트는 계속 `../{repo명}-{짧은이름}` 에 만들며 이슈 번호를 붙이지 않는다.
  `workmux open`에는 이 디렉토리명(`zambaguni-front-add-partner-chat-enabled`)을 넘긴다.
- 같은 브랜치의 worktree가 이미 있으면 새로 만들지 않고 기존 경로를 안내한다.

## 마무리

```bash
workmux list
tmux list-windows -a -F '#{session_name}:#{window_index}\t#{window_name}'
```

`workmux list`의 어떤 열에도 윈도우 이름이 없다. `MUX ✓`는 윈도우가 열렸다는 것만
알려주므로, 사용자에게 윈도우 이름을 안내하기 전에 `tmux list-windows`로 실제 이름을
확인한다. 추측한 이름을 안내하면 사용자가 `workmux close`에 없는 이름을 넘기게 된다.

**윈도우가 실제로 어느 세션에 있는지 확인하는 것은 생략할 수 없다.** workmux는 존재하지
않는 `--parent-session` 값을 받아도 오류 없이 그 세션을 만들어 버리므로(위 "부모 tmux
세션" 참조), 창이 엉뚱한 세션에 열린 것을 알려 주는 신호가 이 검증뿐이다. 새로 만든
것이면 `1-main`, 그 밖에는 git config의 `window-session`이 가리키는 세션이어야 한다.
어긋나면 사용자에게 알리고 잘못 만들어진 세션과 git config 값을 함께 정리한다.

## 주의사항

- **git-crypt 저장소에서 `workmux add`를 쓰지 않는다.** 위 분기를 반드시 지킨다.
- 에이전트(claude·codex)는 자동 실행되지 않는다. 레이아웃 설정이 nvim만 띄우고
  나머지 pane은 빈 셸로 열며, 필요할 때 사용자가 직접 시작한다.
- 개발 서버는 이 레이아웃에 없다. 별도 윈도우나 pane으로 띄운다 —
  worktree마다 상주시키면 포트가 충돌하고 개당 1~2GB를 쓴다.
- 레이아웃을 바꾸려면 스킬이 아니라 `~/.config/workmux/config.yaml`을 고친다.
  저장소별로 다르게 하려면 저장소 루트에 `.workmux.yaml`을 둔다.
