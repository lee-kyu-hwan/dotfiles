# dotfiles

macOS / Linux 개발 환경 설정을 [chezmoi](https://www.chezmoi.io/)로 관리합니다.

## 빠른 시작

```bash
git clone https://github.com/lee-kyu-hwan/dotfiles.git ~/code/dotfiles
cd ~/code/dotfiles

# 1단계: 최소 환경 설치 (사람이 직접 실행)
./install.sh

# 2단계: 나머지 설정 (Claude Code에게 맡기기)
claude "~/code/dotfiles/setup.sh를 실행해서 개발 환경 설정을 완료해줘"
```

### 설치 흐름

```
./install.sh (사람)              claude → setup.sh (AI)
┌──────────────────┐            ┌──────────────────────────┐
│ Xcode CLI Tools  │            │ Oh My Zsh                │
│ Homebrew / apt   │  ───────>  │ TPM (tmux plugin)        │
│ Claude Code CLI  │            │ chezmoi init + apply     │
└──────────────────┘            │ Brew bundle (macOS)      │
                                │ Stow 정리 (마이그레이션)  │
                                └──────────────────────────┘
```

## 머신 타입

`setup.sh` 실행 시 머신 타입을 선택합니다:

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
| neovim | Neovim (lazy.nvim, LSP, telescope) ([키맵 & 치트시트](docs/neovim.md)) | O | O | O |
| lazygit | lazygit 터미널 Git UI | O | O | O |
| starship | Starship 프롬프트 | O | O | O |
| claude | Claude Code 전역 설정 | O | O | O |
| ghostty | Ghostty 터미널 설정 | O | O | X |
| brew | Homebrew 패키지 목록 | O | O | X |
| keycastr | 키 입력 시각화 ([설정 문서](docs/keycastr.md)) | O | O | X |

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

`chezmoi edit`으로 수정하면 저장 시 자동으로 apply + commit + push됩니다.

## Git 환경별 설정

`includeIf`로 디렉토리 기반 자동 분기:

- `~/code/work/` 하위 → `.gitconfig-work` (회사 이메일)
- `~/code/personal/` 하위 → `.gitconfig-personal` (개인 이메일)

## Neovim

Leader 키는 `<Space>`. 주요 키맵: `<Space>e` (파일 탐색기), `<Space>ff` (파일 검색), `<Space>gg` (LazyGit).

전체 커스텀 키맵과 Vim 치트시트는 [docs/neovim.md](docs/neovim.md) 참고.

## 주의사항

### 설정 수정은 반드시 `chezmoi edit`으로

```bash
# O — source repo에 반영되고 자동 commit + push
chezmoi edit ~/.zshrc

# X — $HOME 파일만 바뀌고 repo에는 반영 안 됨
vim ~/.zshrc
```

직접 `~/.zshrc`를 수정하면 다음 `chezmoi apply` 시 **덮어써집니다.**

### source 파일을 직접 수정한 경우

```bash
# 1. 변경사항 확인
chezmoi diff

# 2. $HOME에 적용
chezmoi apply

# 3. git commit + push는 수동으로
git add -A && git commit -m "설명" && git push
```

`chezmoi edit`이 아닌 직접 source 수정 시에는 auto commit/push가 동작하지 않습니다.

### 이직 시

`dot_gitconfig-work`의 email만 변경하면 됩니다:

```bash
chezmoi edit ~/.gitconfig-work
```

### 파일 추가하기

```bash
# 1. 기존 설정 파일을 chezmoi에 등록
chezmoi add ~/.config/새앱/config

# 2. 자동으로 source repo에 dot_config/새앱/config 생성

# 3. server에서 제외하려면 .chezmoiignore에 추가
chezmoi edit-config-template  # 또는 직접 .chezmoiignore 수정
```

### OS 분기가 필요한 파일

`.tmpl` 확장자를 붙이고 Go 템플릿 문법 사용:

```
{{ if eq .chezmoi.os "darwin" }}
macOS 전용 설정
{{ else }}
Linux 전용 설정
{{ end }}
```

현재 OS 분기 파일: `.tmux.conf`, `.zshrc`
