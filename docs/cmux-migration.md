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

### 3. dot_claude/settings.json

cmux 알림 CLI 연동:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "cmux notify --title 'Claude Code' --message '작업 완료'"
          }
        ]
      }
    ]
  }
}
```

### 4. dot_config/ghostty/config

cmux가 ghostty config를 읽으므로 수정 불필요. 그대로 유지.

### 5. .claude/skills/create-worktree/SKILL.md (zambaguni-front)

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
