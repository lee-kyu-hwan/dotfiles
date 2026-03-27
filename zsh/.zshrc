# Path to your Oh My Zsh installation.
export ZSH="$HOME/.oh-my-zsh"

# Starship을 사용하므로 Oh My Zsh 테마 비활성화
ZSH_THEME=""

plugins=(git)

source $ZSH/oh-my-zsh.sh

# ============================================================
# Homebrew
# ============================================================
eval "$(/opt/homebrew/bin/brew shellenv)"

# ============================================================
# Java
# ============================================================
if [ -d "/opt/homebrew/opt/openjdk@17" ]; then
    export PATH="/opt/homebrew/opt/openjdk@17/bin:$PATH"
    export JAVA_HOME="/opt/homebrew/opt/openjdk@17"
fi

# ============================================================
# Bun
# ============================================================
[ -s "$HOME/.bun/_bun" ] && source "$HOME/.bun/_bun"
export BUN_INSTALL="$HOME/.bun"
export PATH="$BUN_INSTALL/bin:$PATH"

# ============================================================
# Android Studio
# ============================================================
if [ -d "$HOME/Library/Android/sdk" ]; then
    export ANDROID_HOME="$HOME/Library/Android/sdk"
    export PATH="$PATH:$ANDROID_HOME/emulator"
    export PATH="$PATH:$ANDROID_HOME/platform-tools"
fi

# ============================================================
# PATH 추가
# ============================================================
export PATH="$HOME/.local/bin:$PATH"
export PATH="$PATH:$HOME/.pub-cache/bin"
export PATH="$PATH:$HOME/.maestro/bin"

# ============================================================
# Aliases
# ============================================================
alias ll='ls -lah'
alias dotfiles='cd ~/code/dotfiles'

# ============================================================
# Starship prompt (마지막에 로드)
# ============================================================
eval "$(starship init zsh)"
