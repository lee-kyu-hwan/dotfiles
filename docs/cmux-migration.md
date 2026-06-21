# cmux 전환 가이드

cmux가 안정화되면 Ghostty + tmux 조합에서 전환할 때 참고.

## 전환 시 수정할 파일

### 1. dot_Brewfile

```ruby
# 추가
cask "cmux"

# 제거 (cmux가 Ghostty 내장)
# cask "ghostty"  ← 판단 필요: cmux가 완전 대체하면 제거
```

### 2. dot_tmux.conf.tmpl

상태바 커스텀 제거 가능 (cmux 사이드바가 대체):

```
# 제거 대상: 상태바 섹션 전체
# - status-style, status-left, status-right
# - window-status-format (신호등 색상)
# - monitor-activity, monitor-silence
```

나머지(한글 IME, 패인 스타일, 레이아웃)는 유지.

### 3. dot_claude/settings.json.tmpl

이 파일은 Go 템플릿(`.tmpl`)이다. 현재 알림은 여러 hook 이벤트(`Stop`, `SubagentStop`, `TaskCompleted`, `Notification`, `PermissionRequest`)에서 공통적으로 `~/.local/bin/ai-agent-ghostty-notify` 스크립트를 `args`로 라벨(예: `"Claude Code"`, `"Claude Subagent"`, `"Claude Task"`)을 넘겨 호출하는 구조다. 경로는 `{{ .chezmoi.homeDir }}` 템플릿으로 채워진다.

현재 구조(이벤트당 동일 패턴 반복):

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "{{ .chezmoi.homeDir }}/.local/bin/ai-agent-ghostty-notify",
            "args": ["Claude Code"]
          }
        ]
      }
    ]
  }
}
```

cmux 전환 시 바꿔야 할 것:

- 알림 스크립트(`ai-agent-ghostty-notify`)는 Ghostty 창을 대상으로 동작하므로, cmux 알림 방식에 맞춰 명령을 교체한다. 모든 이벤트 hook(`Stop`/`SubagentStop`/`TaskCompleted`/`Notification`/`PermissionRequest`)을 동일하게 손봐야 한다.
- `command`를 cmux 알림 CLI로 바꾸거나, `ai-agent-ghostty-notify` 스크립트 내부를 cmux 호출로 수정하는 두 방식 중 택1. 후자면 settings는 그대로 두고 스크립트만 교체하면 된다.
- `args`로 넘기는 라벨(어떤 종류의 알림인지)은 그대로 유지하는 편이 식별에 유리하다.

### 4. dot_config/ghostty/config

cmux가 ghostty config를 읽으므로 수정 불필요. 그대로 유지.

### 5. /Users/lee-kyu-hwan/code/zambaguni-front/.claude/skills/create-worktree/SKILL.md

tmux 윈도우 생성 → cmux 워크스페이스 생성으로 변경. cmux CLI 확인 후 수정.

## 전환 전 확인 사항

- [ ] cmux 한글 폰트 이슈 (#1693) 해결 여부
- [ ] 스플릿 크래시 (#1938) 해결 여부
- [ ] 슬립 후 크래시 (#432) 해결 여부
- [ ] cmux 안정 버전 (v1.0+) 출시 여부

## 확인 방법

```bash
# cmux GitHub issues 확인
open https://github.com/manaflow-ai/cmux/issues/1693
open https://github.com/manaflow-ai/cmux/issues/1938
open https://github.com/manaflow-ai/cmux/issues/432
```
