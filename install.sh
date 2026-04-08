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

# 1. 패키지 매니저 + 기본 도구
if [[ "$(uname)" == "Darwin" ]]; then
    echo "[1/2] Homebrew..."
    if ! command -v brew &>/dev/null; then
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    if [ -f /opt/homebrew/bin/brew ]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    elif [ -f /usr/local/bin/brew ]; then
        eval "$(/usr/local/bin/brew shellenv)"
    fi
else
    echo "[1/2] Linux 기본 패키지 + Node.js..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get update
        sudo apt-get install -y git curl
        if ! command -v node &>/dev/null; then
            curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
            sudo apt-get install -y nodejs
        else
            echo "  node already installed ($(node --version))"
        fi
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y git curl
        if ! command -v node &>/dev/null; then
            curl -fsSL https://rpm.nodesource.com/setup_lts.x | sudo bash -
            sudo dnf install -y nodejs
        else
            echo "  node already installed ($(node --version))"
        fi
    fi
fi

echo "[2/2] Claude Code CLI..."
if ! command -v claude &>/dev/null; then
    curl -fsSL https://claude.ai/install.sh | bash
else
    echo "  already installed"
fi

echo ""
echo "✅ 1단계 완료! 이제 Claude Code에게 나머지를 맡기세요:"
echo ""
echo "  claude \"~/code/dotfiles/setup.sh를 실행해서 개발 환경 설정을 완료해줘\""
echo ""
