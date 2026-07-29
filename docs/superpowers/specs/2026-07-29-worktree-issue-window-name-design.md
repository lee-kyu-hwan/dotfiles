# Worktree issue window name 복원 설계

## 목표

workmux 전환 과정에서 빠진 issue 번호 기반 tmux window 이름 규칙을 Codex와
Claude의 `create-worktree` 스킬에 복원한다. Worktree 디렉터리 이름은 바꾸지 않는다.

## 동작

- 브랜치 선두의 숫자 또는 `ZF-숫자`를 issue 번호로 인식한다.
- issue 번호가 있으면 window 이름을 `{issue번호}-{짧은이름}`으로 만든다.
- issue 번호가 없으면 짧은 이름을 그대로 사용한다.
- `workmux add`와 `workmux open`에 `--target-name`을 전달해 window 이름만 지정한다.

예:

| 브랜치 | 디렉터리 suffix | window target |
| --- | --- | --- |
| `392-feat/add-partner-chat-enabled` | `add-partner-chat-enabled` | `392-add-partner-chat-enabled` |
| `ZF-115-chore/some-feature` | `some-feature` | `ZF-115-some-feature` |
| `fix/login-bug` | `login-bug` | `login-bug` |

## 변경 범위

- `dot_agents/skills/create-worktree/SKILL.md`
- `dot_claude/skills/create-worktree/SKILL.md`

두 파일의 본문은 동일하게 유지하고 Claude 전용 frontmatter만 보존한다. workmux 설정,
worktree 디렉터리 규칙, pane 레이아웃은 변경하지 않는다.

## 검증

수정 전 시나리오에서 issue 번호가 `workmux` 명령에 전달되지 않는 것을 확인한다.
수정 후 두 스킬 모두 다음을 명시하는지 검증한다.

1. 숫자 issue prefix를 추출해 `--target-name`에 포함한다.
2. `ZF-숫자` prefix를 보존한다.
3. issue가 없는 브랜치는 짧은 이름만 사용한다.
4. `workmux add`와 `workmux open` 양쪽 경로에 같은 규칙을 적용한다.
5. Codex와 Claude 본문이 frontmatter를 제외하고 동일하다.
