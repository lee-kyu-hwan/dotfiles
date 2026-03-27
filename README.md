# dotfiles

macOS 개발 환경 설정을 [GNU Stow](https://www.gnu.org/software/stow/)로 관리합니다.

## 빠른 시작

```bash
# ⚠️ 반드시 ~/code/dotfiles 경로에 clone해야 합니다 (아래 주의사항 참고)
git clone https://github.com/lee-kyu-hwan/dotfiles.git ~/code/dotfiles
cd ~/code/dotfiles
./bootstrap.sh
```

## 패키지 목록

| 패키지 | 설명 | 대상 |
|--------|------|------|
| `tmux` | tmux 설정 (한글 IME 호환) | `~/.tmux.conf` |
| `zsh` | Zsh 쉘 설정 (Oh My Zsh) | `~/.zshrc` |
| `git` | Git 공통 설정 | `~/.gitconfig` |
| `git-work` | Git 회사 환경 | `~/.gitconfig-work` |
| `git-personal` | Git 개인 환경 | `~/.gitconfig-personal` |
| `ghostty` | Ghostty 터미널 설정 | `~/.config/ghostty/config` |
| `claude` | Claude Code 설정 | `~/.claude/settings.json` |
| `brew` | Homebrew 패키지 목록 | `~/.Brewfile` |

## 사용법

### 전체 설치

```bash
./bootstrap.sh                    # 대화형
./bootstrap.sh --profile work     # 비대화형 (회사)
./bootstrap.sh --profile personal # 비대화형 (개인)
```

### 개별 패키지 관리

```bash
cd ~/code/dotfiles
stow --target=$HOME tmux          # 심볼릭 링크 생성
stow --target=$HOME -D tmux       # 심볼릭 링크 제거
stow --target=$HOME --restow tmux # 재적용 (멱등)
```

### 환경별 설정

Git은 `includeIf`를 사용하여 디렉토리 기반으로 환경을 분기합니다:

- `~/code/work/` 하위 저장소 → `.gitconfig-work` 적용 (회사 이메일)
- `~/code/personal/` 하위 저장소 → `.gitconfig-personal` 적용 (개인 이메일)
- 그 외 → `.gitconfig` 기본 설정 적용

## 패키지 추가하기

```bash
# 1. 패키지 디렉토리 생성 ($HOME 기준 경로 유지)
mkdir -p <패키지명>/.config/<앱>

# 2. 설정 파일 배치
cp ~/.config/<앱>/config <패키지명>/.config/<앱>/config

# 3. Stow 적용
cd ~/code/dotfiles
stow --target=$HOME <패키지명>

# 4. bootstrap.sh의 COMMON_PACKAGES에 추가
```

## ⚠️ 주의사항

### dotfiles 경로 고정

GNU Stow는 **상대경로 심볼릭 링크**를 생성합니다. 예를 들어:

```
~/.tmux.conf → code/dotfiles/tmux/.tmux.conf
```

따라서 **반드시 `~/code/dotfiles` 경로에 clone**해야 합니다.
다른 경로에 clone하면 심볼릭 링크가 깨집니다.

경로를 변경해야 할 경우:
1. 모든 Stow 패키지를 unstow: `stow --target=$HOME -D tmux zsh git ...`
2. 새 경로로 이동
3. 다시 stow: `stow --target=$HOME tmux zsh git ...`

### --target=$HOME 필수

dotfiles가 `~/code/dotfiles`에 있어 Stow 기본 타겟(`../`)이 `~/code/`가 됩니다.
항상 `--target=$HOME` 옵션을 사용해야 합니다. `bootstrap.sh`는 이를 자동으로 처리합니다.

### 기존 파일 충돌

Stow는 대상 위치에 일반 파일(symlink이 아닌)이 이미 있으면 **충돌 오류**를 발생시킵니다.
이 경우 기존 파일을 백업/삭제한 후 다시 시도하세요:

```bash
mv ~/.zshrc ~/.zshrc.bak
stow --target=$HOME zsh
```

## tmux 한글 입력 지원

한글 입력 상태에서도 tmux 단축키가 동작하도록 3가지를 설정합니다:

1. **Ctrl+B 자동 전환**: prefix 키 입력 시 macism으로 영문 전환
2. **자음 바인딩 (안전망)**: 한글 자음(ㅈ, ㅊ 등)을 영문 키에 매핑
3. **macism 훅**: 창/패널 전환 시 자동 영문 전환

## 의존성

- [Homebrew](https://brew.sh)
- [GNU Stow](https://www.gnu.org/software/stow/) (`brew install stow`)
- [macism](https://github.com/laishulu/macism) (tmux 한글 지원)
- [Starship](https://starship.rs) (쉘 프롬프트)
- [Oh My Zsh](https://ohmyz.sh)
