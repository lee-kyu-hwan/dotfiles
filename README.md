# dotfiles

macOS / Linux 개발 환경 설정을 [chezmoi](https://www.chezmoi.io/)로 관리합니다.

## 빠른 시작

```bash
git clone https://github.com/lee-kyu-hwan/dotfiles.git ~/code/dotfiles
cd ~/code/dotfiles

# 1단계: 최소 환경 설치 (사람이 직접 실행)
./install.sh

# 2단계: 나머지 설정 (Claude Code에게 맡기기)
claude "~/code/dotfiles/setup.sh를 실행해서 개발 환경 설정을 완료해줘"
```

### 설치 흐름

```
./install.sh (사람)                    claude → setup.sh (AI)

macOS:                                 ┌──────────────────────────┐
┌──────────────────────┐               │ Oh My Zsh                │
│ [1/3] Xcode CLI      │               │ TPM (tmux plugin)        │
│ [2/3] Homebrew       │  ───────────> │ chezmoi init + apply     │
│ [3/3] Claude Code    │               │ Brew bundle              │
└──────────────────────┘               └──────────────────────────┘

Linux:                                 ┌──────────────────────────┐
┌──────────────────────┐               │ Linux 개발 도구            │
│ [1/4] (skip)         │               │ Oh My Zsh                │
│ [2/4] apt/dnf        │  ───────────> │ TPM (tmux plugin)        │
│ [3/4] Node.js (LTS)  │               │ chezmoi init + apply     │
│ [4/4] Claude Code    │               └──────────────────────────┘
└──────────────────────┘
```

## 머신 타입

`setup.sh` 실행 시 머신 타입을 선택합니다:

| 타입 | 설명 | OS |
|------|------|----|
| `work` | 회사 맥북 | macOS |
| `personal` | 개인 맥북 | macOS |
| `server` | 클라우드 개발 서버 | Linux |

> **Linux 참고**: `install.sh`에서 Node.js(LTS)와 Claude Code CLI를 자동 설치합니다.

## 패키지 목록

### chezmoi 관리 설정

| 패키지 | 설명 | work | personal | server |
|--------|------|----------|----------|--------|
| tmux | tmux 설정 (macOS: 한글 IME 호환) ([키맵 & 치트시트](docs/tmux.md)) | O | O | O |
| zsh | Zsh 설정 (Oh My Zsh + Starship + autosuggestions + syntax-highlighting) | O | O | O |
| git | Git 설정 (includeIf 분기, delta, alias) | O | O | O |
| neovim | Neovim (lazy.nvim, LSP, telescope) ([키맵 & 치트시트](docs/neovim.md)) | O | O | O |
| lazygit | lazygit 터미널 Git UI | O | O | O |
| starship | Starship 프롬프트 | O | O | O |
| claude | Claude Code 전역 설정 | O | O | O |
| aws | AWS CLI SSO 설정 ([설정 문서](docs/aws-cli.md)) | O | O | X |
| ghostty | Ghostty 터미널 설정 | O | O | X |
| keycastr | 키 입력 시각화 ([설정 문서](docs/keycastr.md)) | O | O | X |

### Homebrew 패키지 (macOS)

CLI 도구, 앱, 런타임은 Brewfile로 관리합니다. 상세 목록:

- [CLI 도구 목록 & 사용법](docs/cli-tools.md) — bat, eza, zoxide, fzf, delta, jq 등 22개
- [앱 & 런타임 목록](docs/apps.md) — Android Studio, Ghostty, Flutter, Redis 등 11개

#### 패키지 추가

```bash
chezmoi edit ~/.Brewfile
```

에디터에서 패키지를 추가하고 저장하면 자동으로 설치부터 git push까지 완료됩니다:

1. `chezmoi apply` → `~/.Brewfile` 반영
2. `brew bundle --global` → 패키지 설치
3. `git commit` + `git push` → dotfiles 저장소에 반영

## 사용법

### 설정 변경 후 적용

```bash
chezmoi apply
```

### 변경 사항 미리보기

```bash
chezmoi diff
```

### 설정 파일 편집

```bash
chezmoi edit ~/.zshrc
```

`chezmoi edit`으로 수정하면 저장 시 자동으로 apply + commit + push됩니다.

## Shell 플러그인

| 플러그인 | 기능 |
|----------|------|
| zsh-autosuggestions | 이전 명령어 기반 자동 완성 제안 (→ 키로 수락) |
| zsh-syntax-highlighting | 유효한 명령어는 녹색, 잘못된 명령어는 빨간색으로 표시 |

macOS는 Homebrew, Linux는 Oh My Zsh custom plugins 경로에서 로드.

## Git

`includeIf`로 디렉토리 기반 이메일 자동 분기 외에, 아래 기능이 추가로 설정되어 있다:

### Git Alias

| Alias | 명령어 | 설명 |
|-------|--------|------|
| `git st` | `status -sb` | 간결한 상태 확인 |
| `git l` | `log --oneline --graph -20` | 최근 20개 커밋 그래프 |
| `git ll` | `log --graph --pretty=...` | 상세 커밋 로그 (작성자, 시간) |
| `git amend` | `commit --amend --no-edit` | 마지막 커밋에 변경사항 추가 |
| `git fixup` | `commit --fixup` | fixup 커밋 생성 (rebase용) |
| `git undo` | `reset --soft HEAD~1` | 마지막 커밋 취소 (변경사항 유지) |
| `git unstage` | `reset HEAD --` | staged 파일을 unstage |

### Delta (diff pager)

`git diff`, `git log -p` 등에서 자동으로 delta가 적용되어 side-by-side diff + syntax highlighting + line numbers로 표시.

### 기타 설정

- `merge.conflictstyle = zdiff3` — 충돌 시 base 코드도 함께 표시
- `rebase.autoStash = true` — rebase 시 자동 stash/pop
- `rebase.autoSquash = true` — fixup 커밋 자동 squash
- `diff.algorithm = histogram` — 더 정확한 diff 알고리즘

## Neovim

Leader 키는 `<Space>`. 주요 키맵: `<Space>e` (파일 탐색기), `<Space>ff` (파일 검색), `<Space>gg` (LazyGit).

전체 커스텀 키맵과 Vim 치트시트는 [docs/neovim.md](docs/neovim.md) 참고.

### 주요 플러그인

| 플러그인 | 기능 |
|----------|------|
| vim-tmux-navigator | `Ctrl+h/j/k/l`로 tmux/neovim 창 이동 통합 |
| todo-comments.nvim | `TODO`/`FIXME`/`HACK` 하이라이트 + 검색 |
| lualine.nvim | 하단 상태바 (모드, 브랜치, diff, 진단) |
| indent-blankline.nvim | 들여쓰기 가이드라인 표시 |
| telescope.nvim | 파일/텍스트/버퍼/TODO 검색 |
| gitsigns.nvim | Git hunk 탐색, stage/reset, blame |
| neo-tree.nvim | 파일 탐색기 |
| treesitter + textobjects | 코드 구조 기반 선택/이동 |
| flash.nvim | 화면 내 빠른 점프 |
| harpoon | 즐겨찾기 파일 4개 즉시 전환 |
| trouble.nvim | 진단/에러 목록 |
| nvim-ts-autotag | HTML/JSX 태그 자동 닫기/동기화 |

## 주의사항

### 설정 수정은 반드시 `chezmoi edit`으로

```bash
# O — source repo에 반영되고 자동 commit + push
chezmoi edit ~/.zshrc

# X — $HOME 파일만 바뀌고 repo에는 반영 안 됨
vim ~/.zshrc
```

직접 `~/.zshrc`를 수정하면 다음 `chezmoi apply` 시 **덮어써집니다.**

### source 파일을 직접 수정한 경우

```bash
# 1. 변경사항 확인
chezmoi diff

# 2. $HOME에 적용
chezmoi apply

# 3. git commit + push는 수동으로
git add -A && git commit -m "설명" && git push
```

`chezmoi edit`이 아닌 직접 source 수정 시에는 auto commit/push가 동작하지 않습니다.

### Neovim 업그레이드 후 캐시 오류

`brew upgrade` 후 Neovim 버전이 올라가면 lua 바이트코드 캐시가 구버전 경로를 가리켜 오류가 발생할 수 있습니다.

```
module 'vim.filetype.detect' not found
```

캐시를 삭제하면 해결됩니다:

```bash
rm -rf ~/.cache/nvim && rm -rf ~/.local/share/nvim/lazy
```

이후 nvim을 열면 lazy.nvim이 플러그인을 재설치합니다.

### 이직 시

`dot_gitconfig-work`의 email만 변경하면 됩니다:

```bash
chezmoi edit ~/.gitconfig-work
```

### 파일 추가하기

```bash
# 1. 기존 설정 파일을 chezmoi에 등록
chezmoi add ~/.config/새앱/config

# 2. 자동으로 source repo에 dot_config/새앱/config 생성

# 3. server에서 제외하려면 .chezmoiignore에 추가
chezmoi edit-config-template  # 또는 직접 .chezmoiignore 수정
```

### OS 분기가 필요한 파일

`.tmpl` 확장자를 붙이고 Go 템플릿 문법 사용:

```
{{ if eq .chezmoi.os "darwin" }}
macOS 전용 설정
{{ else }}
Linux 전용 설정
{{ end }}
```

현재 OS 분기 파일: `.tmux.conf`, `.zshrc`
