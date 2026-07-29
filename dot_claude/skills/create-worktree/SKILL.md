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
tmux를 직접 조작하지 않는다.

## 파라미터

- **args** (필수): 브랜치명 (예: `278-feat/chat-infrastructure`, `ZF-100-feat/login`)
- args가 비어있으면 사용자에게 브랜치명을 물어본다.

## 실행 순서

저장소가 **래퍼 스크립트를 제공하는지**로 경로가 갈린다.

```bash
[[ -x scripts/create-worktree.sh ]] && echo "스크립트 경로" || echo "workmux 경로"
```

### 스크립트가 있을 때 (git-crypt 저장소)

`workmux add`를 쓰지 않는다. workmux는 내부적으로 `git worktree add`를 실행하는데,
git-crypt 저장소에서는 그것이 smudge 필터 에러로 **실패한다**.

```bash
./scripts/create-worktree.sh {브랜치명}    # 필터 우회·키 링크·재체크아웃 + 의존성 설치
workmux open {디렉토리명} --target-name {윈도우이름}  # 기존 worktree를 입양해 레이아웃만 얹는다
```

- 스크립트의 확인 프롬프트는 `-y`나 `yes |`로 우회하지 않고 사용자에게 직접 확인받는다.
- **스크립트 출력에서 worktree 절대경로를 확보한다.** `workmux open`에 넘길
  디렉토리명은 그 경로의 basename이다 (아래 "이름 파생" 참조).
- `workmux open`은 `git worktree list`로 worktree를 찾으므로 `worktree_dir` 밖의
  형제 디렉토리도 그대로 인식한다.

### 스크립트가 없을 때

workmux가 생성과 윈도우 구성을 한 번에 한다.

```bash
workmux add {브랜치명} --target-name {윈도우이름}
```

## 이름 파생

- **짧은 이름**: 브랜치명에서 `*/` prefix를 제거한다.
- **이슈 번호**: 브랜치명의 선행 숫자 ID 또는 `ZF-숫자`를 사용하며, 없으면 생략한다.
- **윈도우이름**: 이슈 번호가 있으면 `{이슈번호}-{짧은이름}`, 없으면 짧은 이름이다.
  workmux는 target name을 소문자로 정규화하므로 `ZF-숫자`가 포함된 실제 target도 소문자다.
  `392-feat/add-partner-chat-enabled` → `392-add-partner-chat-enabled`,
  `ZF-115-feat/some-feature` → `zf-115-some-feature`,
  `login-bug` → `login-bug`
- **디렉토리명**: 스크립트는 계속 `../{repo명}-{짧은이름}` 에 만들며 이슈 번호를 붙이지 않는다.
  `workmux open`에는 이 디렉토리명(`zambaguni-front-add-partner-chat-enabled`)을 넘긴다.
- 같은 브랜치의 worktree가 이미 있으면 새로 만들지 않고 기존 경로를 안내한다.

## 마무리

`workmux list`로 결과를 확인하고 사용자에게 worktree 경로와 열린 윈도우를 안내한다.
`MUX` 열에 `✓`가 있으면 윈도우가 열린 것이다.

## 주의사항

- **git-crypt 저장소에서 `workmux add`를 쓰지 않는다.** 위 분기를 반드시 지킨다.
- 에이전트(claude·codex)는 자동 실행되지 않는다. 레이아웃 설정이 nvim만 띄우고
  나머지 pane은 빈 셸로 열며, 필요할 때 사용자가 직접 시작한다.
- 개발 서버는 이 레이아웃에 없다. Quick Command나 별도 윈도우로 띄운다 —
  worktree마다 상주시키면 포트가 충돌하고 개당 1~2GB를 쓴다.
- 레이아웃을 바꾸려면 스킬이 아니라 `~/.config/workmux/config.yaml`을 고친다.
  저장소별로 다르게 하려면 저장소 루트에 `.workmux.yaml`을 둔다.
