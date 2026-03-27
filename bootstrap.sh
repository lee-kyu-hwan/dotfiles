#!/bin/bash
set -euo pipefail

DOTFILES_DIR="$(cd "$(dirname "$0")" && pwd)"
PROFILE=""

usage() {
    echo "Usage: $0 [--profile work|personal]"
    echo ""
    echo "Options:"
    echo "  --profile  환경 프로필 (work 또는 personal)"
    echo "  --help     도움말"
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --profile) PROFILE="$2"; shift 2 ;;
        --help) usage; exit 0 ;;
        *) echo "Unknown option: $1"; usage; exit 1 ;;
    esac
done

echo "=== dotfiles bootstrap ==="
echo "Source: $DOTFILES_DIR"
echo ""

# 1단계: Xcode CLI Tools
echo "[1/7] Xcode CLI Tools..."
xcode-select --install 2>/dev/null || echo "  already installed"

# 2단계: Homebrew
echo "[2/7] Homebrew..."
if ! command -v brew &>/dev/null; then
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    eval "$(/opt/homebrew/bin/brew shellenv)"
else
    echo "  already installed"
fi

# 3단계: Stow
echo "[3/7] GNU Stow..."
brew install stow 2>/dev/null || echo "  already installed"

# 4단계: 공통 Stow 패키지 적용
echo "[4/7] Stow packages..."
cd "$DOTFILES_DIR"
COMMON_PACKAGES=(tmux zsh git ghostty claude brew)
for pkg in "${COMMON_PACKAGES[@]}"; do
    if [ -d "$pkg" ]; then
        echo "  stow $pkg"
        stow --verbose=0 --target="$HOME" --restow "$pkg"
    fi
done

# 5단계: Brewfile로 패키지 일괄 설치
echo "[5/7] Brew bundle..."
brew bundle --global --no-lock

# 6단계: 환경별 패키지
echo "[6/7] Profile packages..."
if [ -z "$PROFILE" ]; then
    echo "  환경을 선택하세요:"
    echo "  1) work"
    echo "  2) personal"
    echo "  3) 건너뛰기"
    read -rp "  > " choice
    case $choice in
        1) PROFILE="work" ;;
        2) PROFILE="personal" ;;
        *) PROFILE="" ;;
    esac
fi

if [ -n "$PROFILE" ]; then
    for pkg_dir in "$DOTFILES_DIR"/*-"$PROFILE"; do
        if [ -d "$pkg_dir" ]; then
            pkg_name=$(basename "$pkg_dir")
            echo "  stow $pkg_name"
            stow --verbose=0 --target="$HOME" --restow "$pkg_name"
        fi
    done
    echo "  profile: $PROFILE"
else
    echo "  skipped"
fi

# 7단계: 후처리
echo "[7/7] Post-install..."
tmux source-file ~/.tmux.conf 2>/dev/null && echo "  tmux config reloaded" || true

echo ""
echo "✅ dotfiles 설치 완료!"
