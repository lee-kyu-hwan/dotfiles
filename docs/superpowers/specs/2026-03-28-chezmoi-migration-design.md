# Stow → Chezmoi 마이그레이션 설계

## 배경

현재 dotfiles는 GNU Stow로 관리되나, 다음 요구사항이 추가됨:

- **멀티 OS**: macOS (회사/개인 맥북) + Linux (클라우드 개발 서버)
- **머신별 설정 분기**: ALA 회사맥북, 개인 맥북, Linux 서버
- **서버 용도**: tmux persistent 세션으로 AI agent 대화 컨텍스트 유지 (SSH 접속 → tmux attach)

stow는 조건 분기 기능이 없어 chezmoi로 전환한다.

### 전제

- macOS: Apple Silicon (arm64) 기준. Intel Mac은 Homebrew 경로(`/usr/local/bin/brew`)를 분기 처리한다.
- Linux: **server (클라우드 개발 서버)만 지원**. GUI 없는 헤드리스 환경. tmux + neovim + claude code + git + zsh + starship을 배포한다. Ghostty, Brewfile 등 macOS 전용 항목만 제외.

## 목표

- 기존 git history 유지 (점진적 마이그레이션)
- `~/code/dotfiles` 경로 유지
- 머신별 `./bootstrap.sh` 한 번으로 전체 설정 적용 (chezmoi init → diff 확인 → stow 정리 → apply)

## 디렉토리 구조

```
~/code/dotfiles/
├── .chezmoi.toml.tmpl              # 머신별 변수 (init 시 프롬프트)
├── .chezmoiignore                  # OS/머신별 파일 제외
├── dot_tmux.conf.tmpl              # tmux (OS 분기)
├── dot_zshrc.tmpl                  # zsh (OS 분기)
├── dot_gitconfig.tmpl              # git (머신 변수)
├── dot_gitconfig-work              # git ALA 회사 환경
├── dot_gitconfig-personal          # git 개인 환경
├── dot_gitignore_global            # global gitignore
├── dot_Brewfile                    # Homebrew packages
├── dot_config/
│   ├── ghostty/
│   │   └── config                  # Ghostty 터미널
│   ├── nvim/
│   │   ├── init.lua                # Neovim 진입점
│   │   └── lua/
│   │       ├── config/
│   │       │   ├── lazy.lua        # lazy.nvim 부트스트랩
│   │       │   ├── keymaps.lua     # 키바인딩
│   │       │   └── options.lua     # 에디터 옵션
│   │       └── plugins/
│   │           ├── lsp.lua         # nvim-lspconfig + mason
│   │           ├── cmp.lua         # nvim-cmp 자동완성
│   │           ├── treesitter.lua  # 구문 하이라이팅
│   │           ├── telescope.lua   # fuzzy finder
│   │           ├── conform.lua     # 포매팅 (prettier, eslint)
│   │           ├── neo-tree.lua    # 파일 탐색기
│   │           ├── git.lua         # gitsigns + lazygit.nvim
│   │           ├── editor.lua      # autopairs, Comment, which-key
│   │           └── theme.lua       # 테마
│   ├── lazygit/
│   │   └── config.yml              # lazygit 설정
│   └── starship.toml               # Starship 프롬프트
├── dot_claude/
│   └── settings.json               # Claude Code 전역 설정
├── bootstrap.sh                    # chezmoi 설치 + init
└── README.md
```

## 머신 변수 시스템

### .chezmoi.toml.tmpl

```toml
{{- $machine_type := promptChoiceOnce "machine_type" "Machine type (work-mac: ALA 회사맥북, personal: 개인맥북, server: Linux 개발서버)" (list "work-mac" "personal" "server") }}

[data]
  machine_type = "{{ $machine_type }}"
```


생성되는 `~/.config/chezmoi/chezmoi.toml`:

```toml
[data]
  machine_type = "work-mac"
```

### 분기 조합

| 조건 | 역할 |
|------|------|
| `chezmoi.os` (darwin/linux) | `.tmux.conf`, `.zshrc`, `.Brewfile` 등 OS별 분기 |
| `machine_type` (work-mac/personal/server) | 설치 범위(파일 집합) 결정만 담당 |
| git `includeIf` | 저장소 위치별 work/personal 분기 (기존 방식 유지) |

**핵심 원칙**: `machine_type`은 "어떤 파일을 설치할지"만 결정한다. git identity 분기는 `.gitconfig`의 `includeIf`로 유지하며, macOS 머신에서는 `.gitconfig-work`와 `.gitconfig-personal`을 모두 배포한다.

## 파일별 분기 전략

### 템플릿 파일 (.tmpl)

| 파일 | 분기 조건 | 내용 |
|------|-----------|------|
| `dot_tmux.conf.tmpl` | `chezmoi.os` | macOS: macism 한글 IME + 자음 바인딩, Linux: 표준 prefix |
| `dot_zshrc.tmpl` | `chezmoi.os` | macOS: Homebrew/Java/Bun/Android 경로, Linux: 미포함 |
| `dot_gitconfig.tmpl` | 없음 (공통) | user/core/lfs 설정 + `defaultBranch = develop` + includeIf. 템플릿 불필요하면 정적 파일로 변경 가능 |

### 정적 파일 (템플릿 불필요)

| 파일 | 설명 |
|------|------|
| `dot_gitconfig-work` | ALA 회사 git 설정 |
| `dot_gitconfig-personal` | 개인 git 설정 |
| `dot_gitignore_global` | 공통 gitignore |
| `dot_Brewfile` | Homebrew 패키지 목록 |
| `dot_config/ghostty/config` | Ghostty 터미널 설정 |
| `dot_config/nvim/` | Neovim 설정 (init.lua + lua/) |
| `dot_config/lazygit/config.yml` | lazygit 설정 |
| `dot_config/starship.toml` | Starship 프롬프트 |
| `dot_claude/settings.json` | Claude Code 전역 설정 |

### .chezmoiignore

```
# server: macOS 전용 항목만 제외
{{ if eq .machine_type "server" }}
.Brewfile
.config/ghostty/config
{{ end }}
```

- `server`: macOS 전용(Ghostty, Brewfile)만 제외. tmux, neovim, zsh, git, starship, claude 모두 배포
- `work-mac`/`personal`: 모든 파일 배포

### 머신별 배포 대상

| 파일 | work-mac | personal | server |
|------|----------|----------|--------|
| `.tmux.conf` | O | O | O |
| `.zshrc` | O | O | O |
| `.gitconfig` | O | O | O |
| `.gitconfig-work` | O | O | O |
| `.gitconfig-personal` | O | O | O |
| `.gitignore_global` | O | O | O |
| `.config/nvim/` | O | O | O |
| `.config/lazygit/config.yml` | O | O | O |
| `.config/starship.toml` | O | O | O |
| `.claude/settings.json` | O | O | O |
| `.Brewfile` | O | O | **X** |
| `.config/ghostty/config` | O | O | **X** |

## Neovim 설정

Neovim을 dotfiles 관리 대상에 추가한다. Next.js + React Native 개발 환경 기준.

### Brewfile 추가

```
brew "neovim"
brew "lazygit"
brew "ripgrep"       # telescope 의존 (이미 존재)
brew "fd"            # telescope 파일 검색
```

### 플러그인 구성

패키지 매니저: **lazy.nvim**

| 플러그인 | 용도 |
|----------|------|
| nvim-lspconfig + mason.nvim | LSP (ts_ls, tailwindcss, eslint) |
| nvim-cmp + cmp-nvim-lsp | 자동완성 |
| nvim-treesitter | 구문 하이라이팅 (tsx, typescript, json, lua, css) |
| telescope.nvim | fuzzy finder (파일/텍스트 검색) |
| conform.nvim | 포매팅 (prettier, eslint) |
| neo-tree.nvim | 파일 탐색기 |
| gitsigns.nvim | git 변경사항 표시 |
| lazygit.nvim | neovim 안에서 lazygit 팝업 (`<leader>gg`) |
| which-key.nvim | 키바인딩 가이드 |
| nvim-autopairs | 괄호/따옴표 자동 닫기 |
| Comment.nvim | 주석 토글 |
| catppuccin 또는 tokyonight | 테마 |

### 파일 구조

```
dot_config/nvim/
├── init.lua                # lazy.nvim 부트스트랩 + require
└── lua/
    ├── config/
    │   ├── lazy.lua        # lazy.nvim 설정
    │   ├── keymaps.lua     # 키바인딩
    │   └── options.lua     # 에디터 옵션 (number, tab, clipboard 등)
    └── plugins/
        ├── lsp.lua         # lspconfig + mason (ts_ls, tailwindcss, eslint)
        ├── cmp.lua         # nvim-cmp
        ├── treesitter.lua  # treesitter
        ├── telescope.lua   # telescope
        ├── conform.lua     # conform (prettier, eslint)
        ├── neo-tree.lua    # neo-tree
        ├── git.lua         # gitsigns + lazygit.nvim
        ├── editor.lua      # autopairs, Comment, which-key
        └── theme.lua       # 테마
```

### 분기

- Neovim 설정은 **템플릿 불필요** (OS 공통)
- 모든 머신(`work-mac`/`personal`/`server`)에 동일하게 배포

## .gitconfig 병합

현재 로컬과 repo의 차이를 병합:

- `name`: `이규환` (한글 통일)
- `email`: `lgh778923@gmail.com` (기본값, 공통)
- `defaultBranch`: `develop` (로컬에서 가져옴)
- `core.excludesfile`: `~/.gitignore_global` (repo에서 유지)
- `filter "lfs"`: repo에서 유지
- `includeIf`: 모든 머신에 포함. server에서도 `~/code/work/`, `~/code/personal/` 분기 사용 가능

**git identity 모델**: 기본 email은 `.gitconfig`에 공통으로 두고, `~/code/work/`와 `~/code/personal/` 하위 저장소는 `includeIf`로 자동 분기한다. `machine_type`으로 git 설정을 나누지 않는다.

## Claude Code 전역 설정

`dot_claude/settings.json` 내용 (superpowers 추가):

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  },
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    }
  },
  "permissions": {
    "allow": [
      "WebSearch",
      "WebFetch(domain:*)"
    ],
    "defaultMode": "auto"
  },
  "enabledPlugins": {
    "superpowers@claude-plugins-official": true,
    "frontend-design@claude-plugins-official": true,
    "code-review@claude-plugins-official": true,
    "code-simplifier@claude-plugins-official": true,
    "pr-review-toolkit@claude-plugins-official": true,
    "figma@claude-plugins-official": true
  },
  "language": "Korean",
  "alwaysThinkingEnabled": true,
  "effortLevel": "high",
  "skipAutoPermissionPrompt": true
}
```

## bootstrap.sh

```bash
#!/bin/bash
set -euo pipefail

DOTFILES_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== dotfiles bootstrap ==="
echo "Source: $DOTFILES_DIR"
echo ""

# 1. Xcode CLI Tools (macOS only)
if [[ "$(uname)" == "Darwin" ]]; then
    echo "[1/6] Xcode CLI Tools..."
    if ! xcode-select -p &>/dev/null; then
        xcode-select --install
        echo "  설치 완료 후 다시 실행하세요."
        exit 0
    else
        echo "  already installed"
    fi
fi

# 2. 패키지 매니저 + 기본 도구
if [[ "$(uname)" == "Darwin" ]]; then
    echo "[2/6] Homebrew..."
    if ! command -v brew &>/dev/null; then
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    # Apple Silicon / Intel 분기
    if [ -f /opt/homebrew/bin/brew ]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    elif [ -f /usr/local/bin/brew ]; then
        eval "$(/usr/local/bin/brew shellenv)"
    fi
else
    echo "[2/6] Linux 패키지..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get update
        sudo apt-get install -y git tmux neovim zsh ripgrep fd-find curl starship lazygit
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y git tmux neovim zsh ripgrep fd-find curl starship lazygit
    fi
fi

# 3. chezmoi 설치 + init (Stow 해제 전에 먼저 검증)
echo "[3/6] chezmoi..."
if ! command -v chezmoi &>/dev/null; then
    sh -c "$(curl -fsLS get.chezmoi.io)" -- -b "$HOME/.local/bin"
    export PATH="$HOME/.local/bin:$PATH"
fi
CHEZMOI="$(command -v chezmoi)"

echo "  chezmoi init..."
"$CHEZMOI" init --source "$DOTFILES_DIR"

echo "  chezmoi diff (변경 사항 미리보기)..."
"$CHEZMOI" diff || true
echo ""
read -rp "  적용하시겠습니까? (y/N) " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "  건너뜀. 'chezmoi apply'로 나중에 적용할 수 있습니다."
    exit 0
fi

# 4. 기존 Stow 환경 정리 (chezmoi 검증 통과 후 실행)
echo "[4/6] Stow 마이그레이션 정리..."
STOW_TARGETS=(.tmux.conf .zshrc .gitconfig .gitconfig-work .gitconfig-personal
              .gitignore_global .Brewfile .config/ghostty/config
              .config/starship.toml .claude/settings.json)
stow_found=false
for target in "${STOW_TARGETS[@]}"; do
    filepath="$HOME/$target"
    if [ -L "$filepath" ]; then
        echo "  unlink $filepath"
        unlink "$filepath"
        stow_found=true
    elif [ -f "$filepath" ]; then
        echo "  backup & remove $filepath → ${filepath}.bak"
        mv "$filepath" "${filepath}.bak"
        stow_found=true
    fi
done
if command -v stow &>/dev/null && [ -f "$DOTFILES_DIR/.stow-local-ignore" ]; then
    echo "  stow -D (기존 패키지 해제)..."
    cd "$DOTFILES_DIR"
    for pkg in tmux zsh git git-work git-personal ghostty claude brew starship; do
        [ -d "$pkg" ] && stow --target="$HOME" -D "$pkg" 2>/dev/null || true
    done
fi
if [ "$stow_found" = false ]; then
    echo "  기존 Stow 환경 없음 (skip)"
fi

# 5. chezmoi apply
echo "[5/6] chezmoi apply..."
"$CHEZMOI" apply

# 6. Brew bundle (macOS only)
if [[ "$(uname)" == "Darwin" ]] && [ -f "$HOME/.Brewfile" ]; then
    echo "[6/6] Brew bundle..."
    brew bundle --global --no-lock
else
    echo "[6/6] Brew bundle... skipped (not macOS)"
fi

echo ""
echo "✅ dotfiles 설치 완료!"
```

### bootstrap 설계 원칙

- **chezmoi 바이너리 경로**: `command -v chezmoi` 결과를 재사용. brew/수동 설치 모두 대응
- **Stow 해제 시점**: chezmoi init + diff 검증 + 사용자 확인 **후**에 실행. 취소 시 기존 환경 유지
- **일반 파일 백업**: symlink가 아닌 파일은 `.bak`으로 이동(mv)하여 대상 경로를 비운 뒤 진행
- **Apple Silicon / Intel 분기**: `/opt/homebrew/bin/brew`와 `/usr/local/bin/brew` 모두 확인
- **dry-run 제공**: `chezmoi diff`로 변경사항 미리보기 후 확인 프롬프트
- **신규 머신 / 기존 머신 모두 지원**: stow 잔재가 없으면 정리 단계는 no-op

## 점진적 마이그레이션 절차

기존 Stow 사용자가 chezmoi로 전환하는 순서:

1. **상태 확인**: 기존 symlink 상태 점검 (`ls -la`)
2. **chezmoi init + 검증**: `chezmoi init --source ~/code/dotfiles`, `chezmoi diff`로 변경사항 확인
3. **사용자 확인**: diff 결과를 보고 적용 여부 결정 (여기서 취소하면 기존 환경 유지)
4. **기존 Stow 해제**: symlink unlink + 일반 파일은 `.bak`으로 이동(원본 제거)
5. **chezmoi apply**: 새 설정 적용
6. **검증**: `chezmoi verify`, 실제 셸/git/tmux 동작 확인
7. **안정화 후 정리**: 최소 1회 이상 사용 검증 후 stow 디렉토리 및 `.bak` 파일 삭제

### 삭제 대상 (안정화 후)

- `tmux/`, `zsh/`, `git/`, `git-work/`, `git-personal/`, `ghostty/`, `claude/`, `brew/`, `starship/` (stow 패키지 디렉토리)
- `.stow-local-ignore`

**주의**: stow 디렉토리는 chezmoi apply 후 즉시 삭제하지 않는다. 실제 사용에서 문제가 없음을 확인한 뒤 삭제한다.

## 이직 시 변경 방법

이직은 work identity 교체이지, `machine_type` 추가가 아니다. 설치 범위(`work-mac`/`personal`/`server`)는 변하지 않는다.

1. `dot_gitconfig-work`의 email을 새 회사 email로 변경

이 한 단계면 끝난다. `machine_type` 선택지, `.gitconfig` 템플릿, `.chezmoiignore` 모두 수정 불필요. `includeIf`가 `~/code/work/` 하위 저장소에 자동으로 새 email을 적용한다.

`work-mac`은 "회사 macOS"라는 설치 범위 레이블이지 특정 회사 식별자가 아니다. 이직 후에도 macOS 설치 범위는 동일하므로 레이블 변경은 불필요하다.

## settings.local.json 처리

현재 `.gitignore`에서 `claude/.claude/settings.local.json`을 제외하고 있다. chezmoi 전환 후:

- `settings.local.json`은 머신별 로컬 오버라이드이므로 chezmoi 관리 대상에서 **제외**
- `.gitignore` 업데이트:
  - stow 경로 `claude/.claude/settings.local.json` 제거
  - 새 방어 규칙 `dot_claude/settings.local.json` 추가 — chezmoi source 디렉토리(`dot_claude/`) 안에 로컬 파일이 실수로 생성되어 커밋되는 것을 방지. 현재 저장소가 이미 이 패턴으로 방어해온 것을 유지하는 것
- 각 머신에서 `~/.claude/settings.local.json`을 수동 생성. chezmoi는 source에 없는 파일을 건드리지 않으므로 충돌 없음
