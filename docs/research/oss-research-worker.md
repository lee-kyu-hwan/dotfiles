# Orca에서 OSS 조사 워커 실행

`oss-research-worker`는 #189의 조사 전용 실행기다. `claude-profile1`과
`claude-profile2`는 인증 계정을 고른다. 권한은 실행기가 고정한 Claude CLI
옵션이 결정한다. 평소 계정 설정 파일은 바꾸지 않는다.

## 실행

1. Orca의 dotfiles 하위 작업트리 안에 지시 파일을 둔다. 지시에는 읽을 로컬
   corpus와 필요한 결과를 적는다. 파일은 작업트리 내부의 일반 파일이어야 한다.
2. 두 작업트리에 다음 명령을 각각 실행한다. `path:` 뒤에는 해당 작업트리의
   절대 경로를 넣는다.

```bash
orca terminal create --worktree path:/absolute/dotfiles-child-1 \
  --title 'OSS 조사 profile1' \
  --command 'python3 dot_local/bin/executable_oss-research-worker --profile claude-profile1 --prompt-file task.txt'

orca terminal create --worktree path:/absolute/dotfiles-child-2 \
  --title 'OSS 조사 profile2' \
  --command 'python3 dot_local/bin/executable_oss-research-worker --profile claude-profile2 --prompt-file task.txt'
```

`orca terminal read --terminal <handle> --limit 100 --json`으로 출력을 확인한다.
이 경로는 Orca의 기본 `worker-start --agent claude`를 호출하지 않는다.

## 권한 경계

실행기는 `--safe-mode --restricted --strict-mcp-config`로 사용자 설정,
스킬, 플러그인, 훅, MCP를 끄고 `--tools Read,Glob,Grep`만 제공한다.
`dontAsk`와 `--permission-prompts none`으로 추가 도구 승인을 받지 않는다.
파일 도구는 실행한 작업트리 안에서만 동작한다. `claude-profile1`은
`CLAUDE_CONFIG_DIR=~/.local/share/ai-account-profiles/claude/profile1`을 쓰고,
`claude-profile2`는 기본 `~/.claude`를 쓰도록 상속된 값을 제거한다.

워커가 GitHub를 직접 조회하거나 조사 스킬의 스크립트를 실행할 수 없다.
조정자가 검토된 수집 결과를 로컬 파일로 제공해야 한다. #192에서 전송
계층을 읽기 전용으로 제한하기 전에는 기존 스크립트의 원격 실행을
조사 워커에게 위임하지 않는다. 로컬 보고서 파일도 조정자가 기록한다.

2026-09-23 설치된 Claude Code 2.1.280의 실제 `claude-profile2` 세션에서
`gh issue create --help`를
요청했을 때, Claude는 제공된 도구가 `Read`, `Glob`, `Grep`뿐이어서 명령을
실행할 수 없다고 응답했다. GitHub 요청은 발생하지 않았다.

## 범위

이 실행기는 지정한 경로로 시작한 조사 워커만 제한한다. 일반 Claude·Codex
세션이나 사용자가 직접 실행한 Orca 에이전트의 권한은 바꾸지 않는다.
