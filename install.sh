#!/bin/bash
set -e

DOTFILES="$(cd "$(dirname "$0")" && pwd)"

install_tmux() {
    echo "[tmux] Installing..."

    if ! command -v brew &>/dev/null; then
        echo "[brew] Homebrew not found. Install from https://brew.sh"
        exit 1
    fi

    if ! command -v macism &>/dev/null; then
        echo "[brew] Installing macism..."
        brew tap laishulu/homebrew
        brew install macism
    else
        echo "[brew] macism already installed"
    fi

    ln -sf "$DOTFILES/tmux/.tmux.conf" "$HOME/.tmux.conf"
    echo "[tmux] Linked .tmux.conf"

    if tmux list-sessions &>/dev/null; then
        tmux source-file "$HOME/.tmux.conf"
        echo "[tmux] Config reloaded"
    fi
}

install_claude() {
    echo "[claude] Installing..."
    mkdir -p "$HOME/.claude"
    ln -sf "$DOTFILES/claude/settings.json" "$HOME/.claude/settings.json"
    echo "[claude] Linked settings.json"
}

install_iterm2() {
    echo "[iterm2] Installing..."
    cp "$DOTFILES/iterm2/com.googlecode.iterm2.plist" \
       "$HOME/Library/Preferences/com.googlecode.iterm2.plist"
    echo "[iterm2] Copied preferences. Restart iTerm2 to apply changes"
}

usage() {
    echo "Usage: $0 [component ...]"
    echo ""
    echo "Components: tmux, claude, iterm2"
    echo ""
    echo "  $0              Install all"
    echo "  $0 tmux         Install tmux only"
    echo "  $0 claude tmux  Install claude and tmux"
}

echo "=== dotfiles install ==="
echo "Source: $DOTFILES"
echo ""

if [ $# -eq 0 ]; then
    install_tmux
    install_claude
    install_iterm2
else
    for component in "$@"; do
        case "$component" in
            tmux)   install_tmux ;;
            claude) install_claude ;;
            iterm2) install_iterm2 ;;
            -h|--help) usage; exit 0 ;;
            *) echo "Unknown component: $component"; usage; exit 1 ;;
        esac
    done
fi

echo ""
echo "=== Done ==="
