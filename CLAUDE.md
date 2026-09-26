# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 개요

chezmoi로 관리하는 macOS/Linux dotfiles. `dot_` 접두사 파일이 `$HOME`에 배치되고, `.tmpl` 확장자 파일은 Go 템플릿으로 OS/머신별 분기된다.

## 주요 명령어

```bash
chezmoi apply              # source → $HOME 적용
chezmoi diff               # 변경사항 미리보기
chezmoi edit ~/.zshrc      # 설정 편집 (자동 apply + commit + push)
chezmoi add ~/.config/앱/config  # 새 파일 등록
```

설정 파일을 직접 수정하면 안 됨. 반드시 `chezmoi edit` 사용. 직접 source 파일을 수정하면 `chezmoi apply` + 수동 commit/push 필요.

단, 사용자가 위임·커밋 금지·원격 쓰기 금지를 지시한 작업에서는 이 자동 apply/commit/push 흐름보다 그 지시가 우선한다 (아래 "Orca 조정자·워커 역할 경계" 참고).

### 설정 파일 변경 흐름

```bash
chezmoi edit ~/.zshrc      # 편집 → 자동 apply + commit + push
```

### Brew 패키지 추가 흐름

```bash
chezmoi edit ~/.Brewfile    # 패키지 추가 → 자동 apply + commit + push + brew bundle
```

`run_onchange_brew-bundle.sh.tmpl`이 Brewfile 변경을 감지하여 `brew bundle --global`을 자동 실행한다.

## 아키텍처

### 파일 네이밍 규칙

- `dot_파일명` → `$HOME/.파일명`으로 배치 (e.g. `dot_gitconfig` → `~/.gitconfig`)
- `dot_config/앱/` → `$HOME/.config/앱/`으로 배치
- `.tmpl` 확장자 → Go 템플릿으로 처리 후 배치

### Claude 스킬·워크플로우 위치

- `dot_agents/skills/` → `~/.agents/skills/` — 에이전트 공용 스킬 (Claude Code 외 도구도 읽음)
- `dot_claude/skills/` → `~/.claude/skills/` — Claude Code 전용 스킬
- `dot_claude/workflows/` → `~/.claude/workflows/` — Claude Code 워크플로우 스크립트

### 분기 시스템

- **OS 분기**: `{{ if eq .chezmoi.os "darwin" }}` — `dot_tmux.conf.tmpl`, `dot_zshrc.tmpl`에서 사용
- **머신 분기**: `.machine_type` (work/personal/server) — `.chezmoiignore`에서 파일 제외에만 사용
- **git identity 분기**: `.gitconfig`의 `includeIf`로 `~/code/work/`와 `~/code/personal/` 자동 분기. `machine_type`으로 git 설정을 나누지 않음

### .chezmoiignore

`server`에서만 macOS 전용 파일(Brewfile, Ghostty, Hammerspoon, KeyCastr)을 제외. 나머지 설정은 모든 머신에 배포.

### 설치 2단계 구조

- `install.sh` — 사람이 실행. Homebrew/apt + Node.js(Linux) + Claude Code CLI
- `setup.sh` — Claude Code가 실행. Oh My Zsh + TPM + chezmoi init/apply + brew bundle

### Neovim 구조

`dot_config/nvim/lua/` 하위:
- `config/` — options, keymaps, lazy.nvim 부트스트랩
- `plugins/` — 플러그인별 파일 분리 (lsp, cmp/blink.cmp, telescope, neo-tree, git, conform, editor, theme, treesitter, database, dashboard)
- lsp.lua는 `vim.lsp.config()` + mason-lspconfig `automatic_enable` 기반 네이티브 LSP API 사용 (Neovim 0.11+ 필요)

### Neovim 캐시 문제

`brew upgrade` 후 Neovim 버전이 올라가면 lua 바이트코드 캐시가 구버전 경로를 가리켜 오류가 발생할 수 있다. 해결:

```bash
rm -rf ~/.cache/nvim && rm -rf ~/.local/share/nvim/lazy
```

커뮤니티 표준 해결법이며, 자동화는 권장되지 않는다 (Brewfile 변경마다 플러그인 전체 재설치가 발생하기 때문).

### 자동 실행 스크립트

- `run_onchange_brew-bundle.sh.tmpl` — Brewfile 변경 시 `brew bundle --global` 자동 실행 (macOS only)
- `run_onchange_before_install-nvm.sh.tmpl` — nvm(v0.40.5) 설치. `$XDG_CONFIG_HOME/nvm`에 둔다
- `run_onchange_configure-macos.sh.tmpl` — macOS 시스템 설정 (defaults write) 변경 시 자동 적용 (macOS only). 자세한 내용은 `docs/macos-defaults.md`
- `run_once_configure-keycastr.sh.tmpl` — 최초 1회 KeyCastr 설정 적용 (macOS only)
- `run_once_install-claude-plugins.sh.tmpl` — 최초 1회 Claude Code superpowers 플러그인 설치 (macOS only)
- `run_once_install-maestro.sh.tmpl` — 최초 1회 Maestro CLI 설치 (macOS only)
- `run_onchange_install-orca-skills.sh.tmpl` — Orca 번들 스킬(`orchestration`·`orca-cli`) 설치 (macOS only). Orca 미설치 시 아무것도 하지 않는다

## Orca 조정자·워커 역할 경계

**적용 조건**: 사용자가 Orca 워커를 지정했거나 이 세션에 조정자(오케스트레이터) 역할을 맡긴 작업에만 적용한다. 사용자가 직접 구현을 맡긴 일반 작업은 평소대로 직접 구현하며, 이 절을 이유로 위임하지 않는다. 역할은 트리 깊이나 이름으로 추론하지 않고 사용자 지시와 Orca preamble로 판단한다.

### 조정자

- 소스·테스트·설정·제품 문서를 직접 편집하지 않는다. 작은 수정이나 리뷰 지적 반영도 Orca 하위 워크트리의 워커에게 맡긴다.
- review-only 워커의 결과를 받아도 직접 고치지 않고 구현 워커에게 넘긴다. #199의 PR 리뷰 규칙, Orca `orchestration` 스킬의 `references/coordinator-loop.md` 규칙과 같다.
- 담당: 워커별 정확한 worktree와 소유 파일 지정, 작업 지시, 상태 확인, 읽기 전용 검토, 로컬 검증, 피드백, 로컬 통합 조율.
- 워커 보고의 사실 주장(커밋 존재, 날짜, 저장했다는 파일 등)은 직접 다시 확인한 뒤 전달한다.

### 워커

- 배정받은 worktree의 소유 파일만 편집한다. 1 worktree 1 writer이며, 다른 워커의 변경을 되돌리거나 덮어쓰지 않는다.
- 범위 밖 수정이 필요하면 직접 하지 않고 조정자에게 묻는다. 질문은 그 세션에서 쓸 수 있다고 확인된 ask·escalation 경로(예: 일반 세션의 `orca orchestration ask`)로만 한다. 그런 경로가 없으면 추측으로 진행하지 않고 transcript에 blocker를 남겨 조정자가 확인하게 한다.
- 완료는 Orca 완료 계약대로 `worker_done`을 한 번 보고하되, 그 세션에서 실제로 확인된 최소 보고 경로만 쓴다. 예: Bash가 없는 제한 세션에 해당 Dispatch reporter(check/ack/`worker_done`)가 붙어 있으면 그것을 쓴다. 보고 경로가 없으면 Bash·네트워크를 열지 않고 transcript로 조정자에게 차단·미확인 상태를 알리며, 정식 완료로 주장하지 않는다.

### 위임 절차

1. **범위 정리** — 작업을 worktree 단위로 나누고, worktree마다 writer 하나와 소유 파일 목록을 정한다. 같은 파일을 건드리는 작업(예: #206·#207)은 소유권과 병합 순서를 먼저 정한다.
2. **워커 확보** — 사용자가 지정한 실제 프로필(예: `claude-profile1`·`claude-profile2`) 터미널을 쓴다. `worker-start --agent claude`만으로 프로필이 선택된다고 가정하지 않고, 실행 argv가 안전한 옵션인지, 핸들이 셸이 아닌 에이전트 터미널이고 ready(`tui-idle`)인지 확인한 뒤 배정한다. 프로필·provider·모델·effort를 자동으로 바꾸지 않는다.
3. **지시 전달** — 프롬프트에 worktree 경로, 소유 파일, 금지 범위, 수락 기준, 보고 방법을 넣는다. 작업에 걸린 안전 제약도 워커 지시문에 그대로 옮긴다. 예: OSS 조사에서는 외부 저장소 이슈·댓글·PR·review·push 등 원격 쓰기 금지.
4. **수거·검증** — 완료 보고를 받으면 조정자가 diff와 보고서를 읽기 전용으로 검토하고 로컬 검증을 한다. 고칠 점은 같은 워커에게 다시 보내고, 통합은 조정자가 조율한다.

```text
worktree : ~/orca/workspaces/dotfiles/<branch>   writer: claude-profile1
소유 파일: AGENTS.md, CLAUDE.md  (그 밖의 파일 수정 금지)
금지     : commit·push·GitHub 쓰기, chezmoi edit/apply, 전역 설정·인증 변경
완료 보고: 세션에서 확인된 보고 경로로 worker_done 1회 (없으면 차단·미확인으로 알림, 위 "워커" 참고)
```

### chezmoi 흐름과의 우선순위

위 `chezmoi edit`의 자동 apply + commit + push 설명은 편집 방법 안내일 뿐, 명시적 위임·커밋 금지·원격 쓰기 금지 지시보다 우선하지 않는다. 그런 작업의 워커는 `chezmoi edit`/`apply` 대신 배정된 worktree의 source 파일을 편집하고, commit/push는 지시가 있을 때만 한다.

### 범위

이 절은 dotfiles 저장소의 진입점(`AGENTS.md`·`CLAUDE.md`)에만 적용된다. 모든 저장소 공통 역할 정책과 `start-orca-orchestrator` 스킬은 #209 담당이며, 이 절로 전역 배포된 것이 아니다. Orca 번들 스킬(`orchestration`·`orca-cli`)은 수정·복제하지 않고 설치된 버전을 참조한다.

## 언어

사용자와의 대화는 항상 한국어로. 커밋 메시지도 한국어.
