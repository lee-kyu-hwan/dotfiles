# Stow 기반 Dotfiles 관리 시스템 설계

## 개요

맥북 초기화 후 개발 환경을 빠르게 복원하기 위해, 기존 수동 symlink 방식(`install.sh`)을 **GNU Stow** 기반으로 전환한다. 각 도구의 설정을 독립 패키지로 분리하여 선택적 설치/제거를 지원하고, 회사/개인 등 복수 환경에 대응한다.

## 배경

### 현재 상태
- `tmux/.tmux.conf` — symlink으로 관리 중
- `claude/settings.json` — symlink으로 관리 중
- `iterm2/com.googlecode.iterm2.plist` — 복사 방식
- `zsh/` — 빈 디렉토리
- `install.sh` — 수동 symlink/copy 스크립트

### 문제점
- symlink 생성 로직이 `install.sh`에 하드코딩
- 패키지 추가 시 스크립트 수정 필요
- 선택적 설치/제거 불편
- 환경별 분기 미지원

## 디렉토리 구조

```
dotfiles/                           # Stow directory (target: $HOME)
├── tmux/
│   └── .tmux.conf                  # → ~/.tmux.conf
├── zsh/
│   └── .zshrc                      # → ~/.zshrc
├── git/
│   └── .gitconfig                  # → ~/.gitconfig (공통 설정)
├── git-work/
│   └── .gitconfig-work             # → ~/.gitconfig-work
├── git-personal/
│   └── .gitconfig-personal         # → ~/.gitconfig-personal
├── ghostty/
│   └── .config/
│       └── ghostty/
│           └── config              # → ~/.config/ghostty/config
├── claude/
│   └── .claude/
│       └── settings.json           # → ~/.claude/settings.json
├── brew/
│   └── .Brewfile                   # → ~/.Brewfile
├── bootstrap.sh                    # 초기 세팅 스크립트
├── .stow-local-ignore              # Stow가 무시할 파일 패턴
├── .gitignore
├── docs/
│   └── superpowers/
│       └── specs/
└── README.md
```

### Stow 패키지 규칙

- 각 패키지 디렉토리 안의 파일 경로가 `$HOME` 기준 경로와 동일해야 한다.
- `stow <패키지명>` → 해당 패키지의 symlink을 `$HOME`에 생성한다.
- `stow -D <패키지명>` → 해당 패키지의 symlink을 제거한다.
- `stow --restow <패키지명>` → 기존 symlink을 재생성한다 (멱등성 보장).

### 환경별 패키지

환경별로 다른 설정이 필요한 도구는 `<도구>-<환경>` 형태의 별도 패키지로 분리한다.

예: `git-work/`, `git-personal/`

공통 `.gitconfig`에서 `includeIf`로 환경별 설정 파일을 조건부 로드한다:

```gitconfig
[user]
    name = 이규환

[includeIf "gitdir:~/code/work/"]
    path = ~/.gitconfig-work

[includeIf "gitdir:~/code/personal/"]
    path = ~/.gitconfig-personal
```

이 패턴은 Git에 국한되지 않고, 환경별 분기가 필요한 모든 도구에 적용 가능하다.

## bootstrap.sh 설계

맥북 초기화 후 한 번 실행으로 전체 환경을 복원하는 스크립트.

### 실행 방식

```bash
# 대화형 (환경 선택 프롬프트)
./bootstrap.sh

# 비대화형 (CI 또는 자동화)
./bootstrap.sh --profile work
./bootstrap.sh --profile personal
```

### 실행 단계

```bash
#!/bin/bash
set -euo pipefail

DOTFILES_DIR="$(cd "$(dirname "$0")" && pwd)"
PROFILE=""

# 인자 파싱
while [[ $# -gt 0 ]]; do
    case $1 in
        --profile) PROFILE="$2"; shift 2 ;;
        --help) echo "Usage: ./bootstrap.sh [--profile work|personal]"; exit 0 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# 1단계: Xcode CLI Tools
xcode-select --install 2>/dev/null || true

# 2단계: Homebrew 설치
if ! command -v brew &>/dev/null; then
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    eval "$(/opt/homebrew/bin/brew shellenv)"
fi

# 3단계: Stow 설치
brew install stow

# 4단계: 공통 Stow 패키지 적용
cd "$DOTFILES_DIR"
COMMON_PACKAGES=(tmux zsh git ghostty claude brew)
for pkg in "${COMMON_PACKAGES[@]}"; do
    if [ -d "$pkg" ]; then
        stow --verbose --restow "$pkg"
    fi
done

# 5단계: Brewfile로 패키지 일괄 설치
brew bundle --global

# 6단계: 환경별 패키지
if [ -z "$PROFILE" ]; then
    echo "환경을 선택하세요:"
    echo "1) work"
    echo "2) personal"
    echo "3) 건너뛰기"
    read -rp "> " choice
    case $choice in
        1) PROFILE="work" ;;
        2) PROFILE="personal" ;;
        3) PROFILE="" ;;
    esac
fi

if [ -n "$PROFILE" ]; then
    for pkg in "$DOTFILES_DIR"/*-"$PROFILE"; do
        pkg_name=$(basename "$pkg")
        if [ -d "$pkg" ]; then
            stow --verbose --restow "$pkg_name"
        fi
    done
fi

# 7단계: 후처리
# tmux 설정 리로드
tmux source-file ~/.tmux.conf 2>/dev/null || true

echo "✅ dotfiles 설치 완료!"
```

### 설계 원칙

- **멱등성**: `--restow`로 반복 실행해도 안전하다.
- **선택적 설치**: 특정 패키지만 `stow <이름>`으로 개별 관리 가능하다.
- **비대화형 지원**: `--profile` 플래그로 자동화 스크립트에서 사용 가능하다.
- Stow 5단계 이전에 brew 패키지를 설치하면 이후 brew 패키지에서 설치하는 도구가 아직 없을 수 있으므로, Stow 적용을 먼저 하고 brew bundle을 그 뒤에 실행한다. (Brewfile symlink이 먼저 필요)

## .stow-local-ignore

Stow가 패키지가 아닌 파일들을 무시하도록 설정한다:

```
\.git
\.gitignore
README\.md
bootstrap\.sh
docs
LICENSE
\.stow-local-ignore
```

## 마이그레이션 계획

### 제거 대상
| 파일/디렉토리 | 이유 |
|---|---|
| `install.sh` | `bootstrap.sh`로 대체 |
| `iterm2/` | Ghostty로 교체 |

### 변환 대상
| 현재 | 변경 후 | 작업 |
|---|---|---|
| `tmux/.tmux.conf` | `tmux/.tmux.conf` | 경로 동일, 유지 |
| `claude/settings.json` | `claude/.claude/settings.json` | `.claude/` 하위로 이동 |
| `zsh/` (비어있음) | `zsh/.zshrc` | `~/.zshrc` 내용 복사 |

### 새로 생성
| 패키지 | 작업 |
|---|---|
| `git/.gitconfig` | 현재 `~/.gitconfig` 참고하여 작성 |
| `git-work/.gitconfig-work` | 회사 환경 설정 |
| `git-personal/.gitconfig-personal` | 개인 환경 설정 |
| `ghostty/.config/ghostty/config` | Ghostty 설정 작성 |
| `brew/.Brewfile` | `brew bundle dump`로 생성 |
| `.stow-local-ignore` | 비패키지 파일 무시 설정 |
| `bootstrap.sh` | 초기 세팅 스크립트 |

### 마이그레이션 순서

1. 기존 symlink 정리 (`rm ~/.tmux.conf ~/.claude/settings.json`)
2. `claude/settings.json` → `claude/.claude/settings.json`으로 이동
3. `~/.zshrc` 내용을 `zsh/.zshrc`로 복사
4. 새 패키지 생성 (git, ghostty, brew)
5. `.stow-local-ignore` 작성
6. `bootstrap.sh` 작성
7. Stow 설치 (`brew install stow`)
8. `stow --simulate` 으로 dry-run 확인
9. `stow --restow` 으로 실제 적용
10. 정상 작동 확인
11. `install.sh`, `iterm2/` 제거
12. `README.md` 업데이트
13. Git 커밋

## 패키지 추가 가이드

향후 새로운 도구의 설정을 추가할 때:

```bash
# 1. 패키지 디렉토리 생성 (홈 기준 경로 유지)
mkdir -p dotfiles/neovim/.config/nvim

# 2. 설정 파일 배치
cp ~/.config/nvim/init.lua dotfiles/neovim/.config/nvim/

# 3. Stow 적용
cd dotfiles && stow neovim

# 4. bootstrap.sh의 COMMON_PACKAGES에 추가
COMMON_PACKAGES=(tmux zsh git ghostty claude brew neovim)
```

## 제약 사항

- **GNU Stow 필수**: Homebrew로 설치 (`brew install stow`)
- **macOS 전용**: `bootstrap.sh`가 Homebrew 기반으로 설계됨
- **Ghostty 필요**: iTerm2 설정은 마이그레이션 후 제거됨
- **SSH 미포함**: SSH 키/설정은 별도 관리 (dotfiles 범위 밖)
- **바이너리 파일 미지원**: Stow는 텍스트 기반 설정 파일에 적합. 바이너리 설정(plist 등)은 보조 스크립트로 처리
