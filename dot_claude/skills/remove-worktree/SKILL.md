---
name: remove-worktree
description: Use when removing a git worktree and its tmux window after finishing work on a branch
argument-hint: <worktree-name>
user-invocable: true
allowed-tools: Bash
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

## 실행 순서

```bash
workmux list                      # 대상 확인
workmux remove {이름}             # worktree + tmux 윈도우 + 로컬 브랜치
# 그리고 아래 "고아 agent state 정리"를 반드시 실행한다
```

`workmux remove`는 기본적으로 **확인 프롬프트를 띄우고 미커밋 변경이 있으면 경고**한다.
그 프롬프트를 `-f`로 우회하지 않고 사용자에게 직접 확인받는다.

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
`reap-agents`도 같은 에러로 죽어서 탈출구가 못 된다.

두 가드는 workmux의 reconcile 로직을 그대로 따른 것이므로 **지우지 말 것**:
- `instance` 비교 — 다른 tmux 서버의 state를 건드리지 않는다
- `boot_id` 비교 — tmux/컴퓨터 크래시 후 남은 이전 부팅의 state는 `workmux resurrect`의
  입력이다. 지우면 복구가 불가능해진다

upstream 이슈 [raine/workmux#213](https://github.com/raine/workmux/issues/213)이 수정되면
이 섹션 전체를 삭제한다.

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

## 마무리

`workmux list`로 최종 상태를 안내한다. 삭제된 항목이 목록에서 사라졌는지 확인한다.

## 주의사항

- `-f`(강제)는 미커밋 변경을 무시하므로 사용자가 명시적으로 요청할 때만 쓴다.
- `--all`은 메인 worktree를 제외한 전부를 지운다. 사용자가 명시적으로 요청할 때만 쓴다.
