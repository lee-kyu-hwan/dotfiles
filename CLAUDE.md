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

### 분기 시스템

- **OS 분기**: `{{ if eq .chezmoi.os "darwin" }}` — `dot_tmux.conf.tmpl`, `dot_zshrc.tmpl`에서 사용
- **머신 분기**: `.machine_type` (work/personal/server) — `.chezmoiignore`에서 파일 제외에만 사용
- **git identity 분기**: `.gitconfig`의 `includeIf`로 `~/code/work/`와 `~/code/personal/` 자동 분기. `machine_type`으로 git 설정을 나누지 않음

### .chezmoiignore

`server`에서만 macOS 전용 파일(Brewfile, Ghostty, KeyCastr)을 제외. 나머지 설정은 모든 머신에 배포.

### 설치 2단계 구조

- `install.sh` — 사람이 실행. Homebrew/apt + Node.js(Linux) + Claude Code CLI
- `setup.sh` — Claude Code가 실행. Oh My Zsh + TPM + chezmoi init/apply + brew bundle

### Neovim 구조

`dot_config/nvim/lua/` 하위:
- `config/` — options, keymaps, lazy.nvim 부트스트랩
- `plugins/` — 플러그인별 파일 분리 (lsp, cmp, telescope, neo-tree, git, conform, editor, theme, treesitter)
- lsp.lua는 `vim.lsp.config()` + `vim.lsp.enable()` 네이티브 API 사용 (Neovim 0.11+ 필요)

### 자동 실행 스크립트

- `run_onchange_brew-bundle.sh.tmpl` — Brewfile 변경 시 `brew bundle --global` 자동 실행 (macOS only)
- `run_once_configure-keycastr.sh.tmpl` — 최초 1회 KeyCastr 설정 적용 (macOS only)

## 언어

사용자와의 대화는 항상 한국어로. 커밋 메시지도 한국어.
