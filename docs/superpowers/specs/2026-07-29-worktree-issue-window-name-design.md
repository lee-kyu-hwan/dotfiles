# Worktree issue window name 복원 설계

## 목표

workmux 전환 과정에서 빠진 issue 번호 기반 tmux window 이름 규칙을 Codex와
Claude의 `create-worktree` 스킬에 복원한다. Worktree 디렉터리 이름은 바꾸지 않는다.

## 동작

- 브랜치 **맨 앞**의 숫자 또는 `ZF-숫자`를 issue 번호로 인식한다. 맨 앞이 아닌 숫자는
  issue 번호가 아니다 — `feat/392-add-x`는 issue 번호가 없는 것으로 본다.
- issue 번호가 있으면 `--target-name {issue번호}-{짧은이름}`을 전달해 window 이름만
  지정한다. 디렉터리 이름은 기존 규칙 그대로 둔다.
- **issue 번호가 없으면 `--target-name`을 생략한다.** 짧은 이름만 넘기면
  `fix/login-bug`처럼 흔한 브랜치가 저장소마다 같은 window 이름이 되어 두 번째
  worktree에서 `✗ A tmux window named '...' already exists`로 실패한다.
- 생략했을 때 workmux가 쓰는 기본 이름은 경로마다 다르다 (실측):
  `workmux open`은 넘긴 디렉터리명(`{repo명}-{짧은이름}`)을 그대로 써서 저장소 이름이
  들어가고, `workmux add`는 브랜치명 슬러그를 써서 저장소 이름이 없다
  (`fix/login-bug` → `fix-login-bug`). 따라서 `add` 경로에서는 저장소 간 충돌이
  여전히 가능하다 — 충돌 시 `--target-name {repo명}-{짧은이름}`으로 재시도한다.
  생략이 짧은 이름보다 나은 이유는 브랜치 prefix가 살아남기 때문이다.
- workmux는 target name을 소문자로 정규화한다. 사용자에게 안내하거나 이후 명령에
  재사용할 이름은 정규화된 소문자 쪽이다.
- `workmux list`에는 window 이름 열이 없다. 안내 전에 `tmux list-windows`로 실제
  이름을 확인한다.

예:

| 브랜치 | 래퍼 스크립트 디렉터리 suffix | `--target-name` | `add` 경로 window | `open` 경로 window |
| --- | --- | --- | --- | --- |
| `392-feat/add-partner-chat-enabled` | `add-partner-chat-enabled` | `392-add-partner-chat-enabled` | `392-add-partner-chat-enabled` | 같음 |
| `ZF-115-chore/some-feature` | `some-feature` | `ZF-115-some-feature` | `zf-115-some-feature` | 같음 |
| `fix/login-bug` | `login-bug` | 생략 | `fix-login-bug` | `zambaguni-front-login-bug` |

## 변경 범위

- `dot_agents/skills/create-worktree/SKILL.md`
- `dot_claude/skills/create-worktree/SKILL.md`
- `dot_agents/skills/remove-worktree/SKILL.md`
- `dot_claude/skills/remove-worktree/SKILL.md`
- `dot_agents/skills/remove-worktree/agents/openai.yaml`

`remove-worktree`를 함께 고치는 이유: 그 스킬은 worktree 이름을 "tmux window 이름에서
`wm-` prefix를 뗀 것"으로 안내했는데, window 이름과 디렉터리 이름은 이미 다르다
(window `worktree-issue-window-name` ↔ 디렉터리 `fix-worktree-issue-window-name`).
`workmux remove`와 `close`는 디렉터리 이름만 받으므로 그 안내를 따르면 대상을 찾지 못한다.

각 스킬의 두 사본은 본문을 동일하게 유지하고 Claude 전용 frontmatter만 보존한다.
workmux 설정, worktree 디렉터리 규칙, pane 레이아웃은 변경하지 않는다.

## 검증

수정 전 시나리오에서 issue 번호가 `workmux` 명령에 전달되지 않는 것을 확인한다.
수정 후 다음을 검증한다.

1. 숫자 issue prefix를 추출해 `--target-name`에 포함한다.
2. `ZF-숫자` prefix를 인식하고, workmux의 실제 target은 소문자로 정규화된다.
3. issue 번호가 없는 브랜치는 `--target-name`을 생략한다.
4. `workmux add`와 `workmux open` 양쪽 경로에 같은 규칙을 적용한다.
5. 각 스킬의 Codex와 Claude 본문이 frontmatter를 제외하고 동일하다.
6. `remove-worktree`가 worktree 이름을 `workmux list`의 `PATH` 열에서 유도하고
   window 이름에서 유추하지 않는다.
7. 저장소 루트 기준으로 래퍼 스크립트 유무를 판정한다 — 서브디렉터리에서 호출해도
   git-crypt 저장소가 `workmux add` 경로로 빠지지 않는다.
