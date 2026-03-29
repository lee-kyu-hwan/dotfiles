#!/bin/bash
set -euo pipefail

# =============================================================
# 1단계: 최소 환경 설치 (사람이 직접 실행)
#
# Homebrew/기본 패키지 + Claude Code CLI 설치 후
# 나머지는 Claude Code에게 setup.sh 실행을 맡긴다.
# =============================================================

echo "=== dotfiles install (1/2) ==="
echo ""

# 1. Xcode CLI Tools (macOS only)
if [[ "$(uname)" == "Darwin" ]]; then
    echo "[1/3] Xcode CLI Tools..."
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
    echo "[2/3] Homebrew..."
    if ! command -v brew &>/dev/null; then
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    if [ -f /opt/homebrew/bin/brew ]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    elif [ -f /usr/local/bin/brew ]; then
        eval "$(/usr/local/bin/brew shellenv)"
    fi
else
    echo "[2/4] Linux 기본 패키지..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get update
        sudo apt-get install -y git curl
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y git curl
    fi

    # 3. Node.js (Linux — Claude Code CLI에 필요)
    echo "[3/4] Node.js..."
    if ! command -v node &>/dev/null; then
        if command -v apt-get &>/dev/null; then
            curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
            sudo apt-get install -y nodejs
        elif command -v dnf &>/dev/null; then
            curl -fsSL https://rpm.nodesource.com/setup_lts.x | sudo bash -
            sudo dnf install -y nodejs
        fi
    else
        echo "  already installed ($(node --version))"
    fi
fi

# macOS: 3/3, Linux: 4/4
if [[ "$(uname)" == "Darwin" ]]; then
    STEP="[3/3]"
else
    STEP="[4/4]"
fi

echo "$STEP Claude Code CLI..."
if [[ "$(uname)" == "Darwin" ]]; then
    if ! command -v claude &>/dev/null; then
        brew install --cask claude-code
    else
        echo "  already installed"
    fi
else
    if ! command -v claude &>/dev/null; then
        npm install -g @anthropic-ai/claude-code
    else
        echo "  already installed"
    fi
fi

echo ""
echo "✅ 1단계 완료! 이제 Claude Code에게 나머지를 맡기세요:"
echo ""
echo "  claude \"~/code/dotfiles/setup.sh를 실행해서 개발 환경 설정을 완료해줘\""
echo ""
