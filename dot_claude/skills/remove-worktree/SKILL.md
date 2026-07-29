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

- **args** (선택): worktree 이름 (디렉토리명, tmux 윈도우 이름에서 `wm-` prefix를 뗀 것)
- args가 비어있으면 `workmux list`로 목록을 보여주고 사용자에게 선택을 요청한다.

## 실행 순서

```bash
workmux list                      # 대상 확인
workmux remove {이름}             # worktree + tmux 윈도우 + 로컬 브랜치
```

`workmux remove`는 기본적으로 **확인 프롬프트를 띄우고 미커밋 변경이 있으면 경고**한다.
그 프롬프트를 `-f`로 우회하지 않고 사용자에게 직접 확인받는다.

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
