#!/bin/bash
set -e

DOTFILES="$(cd "$(dirname "$0")" && pwd)"

echo "=== dotfiles install ==="
echo "Source: $DOTFILES"
echo ""

# --- Homebrew dependencies ---
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

# --- tmux ---
echo "[tmux] Linking .tmux.conf"
ln -sf "$DOTFILES/tmux/.tmux.conf" "$HOME/.tmux.conf"

# Reload if tmux is running
if tmux list-sessions &>/dev/null; then
    tmux source-file "$HOME/.tmux.conf"
    echo "[tmux] Config reloaded"
fi

# --- Claude Code ---
echo "[claude] Linking settings.json"
mkdir -p "$HOME/.claude"
ln -sf "$DOTFILES/claude/settings.json" "$HOME/.claude/settings.json"

echo "[claude] Linking settings.local.json"
ln -sf "$DOTFILES/claude/settings.local.json" "$HOME/.claude/settings.local.json"

# --- iTerm2 ---
echo "[iterm2] Copying preferences"
# iTerm2 plist은 심볼릭 링크가 아닌 복사로 처리 (macOS defaults 시스템 호환)
cp "$DOTFILES/iterm2/com.googlecode.iterm2.plist" \
   "$HOME/Library/Preferences/com.googlecode.iterm2.plist"
echo "[iterm2] Restart iTerm2 to apply changes"

echo ""
echo "=== Done ==="
