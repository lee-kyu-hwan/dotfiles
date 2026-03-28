# dotfiles

macOS / Linux 개발 환경 설정을 [chezmoi](https://www.chezmoi.io/)로 관리합니다.

## 빠른 시작

```bash
git clone https://github.com/lee-kyu-hwan/dotfiles.git ~/code/dotfiles
cd ~/code/dotfiles
./bootstrap.sh
```

## 머신 타입

`bootstrap.sh` 실행 시 머신 타입을 선택합니다:

| 타입 | 설명 | OS |
|------|------|----|
| `work-mac` | ALA 회사 맥북 | macOS |
| `personal` | 개인 맥북 | macOS |
| `server` | 클라우드 개발 서버 | Linux |

## 패키지 목록

| 패키지 | 설명 | work-mac | personal | server |
|--------|------|----------|----------|--------|
| tmux | tmux 설정 (macOS: 한글 IME 호환) | O | O | O |
| zsh | Zsh 설정 (Oh My Zsh + Starship) | O | O | O |
| git | Git 설정 (includeIf 분기) | O | O | O |
| neovim | Neovim (lazy.nvim, LSP, telescope) | O | O | O |
| lazygit | lazygit 터미널 Git UI | O | O | O |
| starship | Starship 프롬프트 | O | O | O |
| claude | Claude Code 전역 설정 | O | O | O |
| ghostty | Ghostty 터미널 설정 | O | O | X |
| brew | Homebrew 패키지 목록 | O | O | X |

## 사용법

### 설정 변경 후 적용

```bash
chezmoi apply
```

### 변경 사항 미리보기

```bash
chezmoi diff
```

### 설정 파일 편집

```bash
chezmoi edit ~/.zshrc
```

## Git 환경별 설정

`includeIf`로 디렉토리 기반 자동 분기:

- `~/code/work/` 하위 → `.gitconfig-work` (회사 이메일)
- `~/code/personal/` 하위 → `.gitconfig-personal` (개인 이메일)
