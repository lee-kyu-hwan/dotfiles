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
