# CLI 도구 가이드

Brewfile에서 관리하는 CLI 도구 목록과 사용법 정리.

## 도구 요약표

| 도구 | 대체 대상 | 역할 |
|------|-----------|------|
| [bat](#bat) | `cat` | 파일 내용 출력 (syntax highlighting, 줄번호, git 변경 표시) |
| [eza](#eza) | `ls` | 디렉토리 목록 (컬러, 아이콘, git 상태) |
| [fd](#fd) | `find` | 파일 검색 |
| [ripgrep](#ripgrep) | `grep` | 텍스트 검색 |
| [zoxide](#zoxide) | `cd` | 디렉토리 이동 (학습 기반) |
| [fzf](#fzf) | - | 범용 fuzzy finder |
| [delta](#delta) | - | git diff pager (syntax highlighting) |
| [lazygit](#lazygit) | - | 터미널 Git UI |
| [git](#git) | - | 버전 관리 |
| [git-lfs](#git-lfs) | - | Git Large File Storage |
| [gh](#gh) | - | GitHub CLI |
| [neovim](#neovim) | `vi` | 에디터 |
| [starship](#starship) | - | 프롬프트 |
| [tmux](#tmux) | - | 터미널 멀티플렉서 |
| [jq](#jq) | - | JSON 파싱/필터링 |
| [awscli](#awscli) | - | AWS CLI |
| [node](#node) | - | Node.js 런타임 |
| [pnpm](#pnpm) | `npm` | Node.js 패키지 매니저 |
| [pipx](#pipx) | - | Python CLI 도구 격리 설치 |
| [python@3.12](#python312) | - | Python 런타임 |
| [tree](#tree) | - | 디렉토리 트리 출력 |
| [macism](#macism) | - | macOS IME 전환 (tmux 한글 호환) |
| [zsh-autosuggestions](#zsh-autosuggestions) | - | 이전 명령어 기반 자동 완성 제안 |
| [zsh-syntax-highlighting](#zsh-syntax-highlighting) | - | 명령어 구문 강조 (유효=녹색, 오류=빨간색) |

---

## 파일/텍스트 도구

### bat

`cat`을 대체하는 파일 뷰어. syntax highlighting, 줄번호, git 변경 표시를 지원한다.

```sh
# 파일 내용 출력 (syntax highlighting 적용)
bat README.md

# 줄번호 없이 출력 (cat과 동일한 출력)
bat --style=plain README.md

# 여러 파일 합쳐서 출력
bat src/index.ts src/utils.ts
```

### eza

`ls`를 대체하는 파일 목록 도구. 컬러, 아이콘, git 상태 표시를 지원한다.

```sh
# 기본 목록 (아이콘 포함)
eza --icons

# 상세 목록 + git 상태
eza -la --icons --git

# 트리 형식으로 출력 (2단계 깊이)
eza --tree --level=2 --icons
```

### fd

`find`를 대체하는 파일 검색 도구. 빠르고 직관적인 문법을 제공한다.

```sh
# 현재 디렉토리에서 .ts 파일 검색
fd --extension ts

# 파일명으로 검색
fd "config"

# 특정 디렉토리에서 검색 + 숨김 파일 포함
fd --hidden --no-ignore ".env" ~/code
```

### ripgrep

`grep`을 대체하는 텍스트 검색 도구. .gitignore를 자동으로 존중하며 매우 빠르다.

```sh
# 현재 디렉토리에서 텍스트 검색
rg "useEffect"

# 파일 타입 지정 검색
rg --type ts "interface User"

# 대소문자 무시 + 컨텍스트 3줄 표시
rg -i -C 3 "error handling"
```

### tree

디렉토리 구조를 트리 형식으로 출력한다.

```sh
# 현재 디렉토리 트리 출력
tree

# 깊이 2단계까지만 출력
tree -L 2

# 숨김 파일 포함, 디렉토리만 출력
tree -ad -L 3
```

---

## 탐색/검색 도구

### fzf

범용 fuzzy finder. 파이프로 연결해 어떤 목록에도 사용할 수 있다. `Ctrl+R`로 히스토리 검색, `Ctrl+T`로 파일 검색이 기본 제공된다.

```sh
# 현재 디렉토리에서 파일 fuzzy 검색
fzf

# 히스토리에서 명령어 검색 (Ctrl+R)
# 터미널에서 Ctrl+R 입력

# 검색 결과를 다른 명령어에 연결
vim $(fzf)
```

### zoxide

`cd`를 대체하는 디렉토리 이동 도구. 방문 기록을 학습해 짧은 키워드로 이동할 수 있다. `z` 명령어로 사용한다.

```sh
# 디렉토리 이동 (방문 기록 기반 fuzzy 매칭)
z dotfiles

# 여러 키워드로 좁히기
z code proj

# fzf와 연동해 인터랙티브 선택
zi
```

---

## Git 도구

### git

분산 버전 관리 시스템.

```sh
# 변경사항 커밋
git commit -m "feat: 기능 추가"

# 브랜치 생성 및 전환
git switch -c feature/new-feature

# 원격 저장소와 동기화
git pull --rebase origin main
```

### git-lfs

Git Large File Storage. 대용량 파일(이미지, 동영상, 바이너리 등)을 git에서 효율적으로 관리한다.

```sh
# LFS로 추적할 파일 패턴 등록
git lfs track "*.psd"

# LFS 추적 파일 목록 확인
git lfs ls-files

# LFS 파일 다운로드
git lfs pull
```

### delta

git diff에 syntax highlighting을 적용하는 pager. `.gitconfig`에서 `core.pager = delta`로 설정되어 `git diff`, `git log -p`, `git show` 등에서 자동 적용된다. lazygit에서도 사용.

현재 설정: side-by-side diff + line numbers + navigate 모드 (`n`/`N`으로 파일 간 이동).

```sh
# git diff에서 자동으로 사용됨
git diff

# git log에서도 사용
git log -p

# 두 파일 직접 비교
delta file1.ts file2.ts
```

### lazygit

터미널 기반 Git UI. 키보드만으로 stage, commit, push, rebase 등을 직관적으로 수행할 수 있다.

```sh
# lazygit 실행
lazygit

# 특정 디렉토리에서 실행
lazygit -p ~/code/myproject
```

주요 단축키:
- `space`: 파일 stage/unstage
- `c`: 커밋
- `P`: push
- `p`: pull
- `R`: rebase

커스텀 단축키 (`dot_config/lazygit/config.yml`):
- `y` (Files): 파일 경로를 클립보드에 복사
- `b` (Files): `gh browse`로 GitHub에서 열기
- `b` (Commits): `gh browse <sha>`로 해당 커밋을 GitHub에서 열기

### gh

GitHub CLI. 브라우저 없이 PR, Issue, Release 등을 관리한다.

```sh
# PR 생성
gh pr create --title "feat: 기능 추가" --body "설명"

# PR 목록 확인
gh pr list

# Issue 생성
gh issue create --title "버그 리포트"
```

---

## 터미널 환경

### starship

크로스 쉘 프롬프트. git 상태, 언어 버전, 명령 실행 시간 등을 자동으로 표시한다. `~/.config/starship.toml`에서 설정한다.

```sh
# 설정 편집
nvim ~/.config/starship.toml

# 현재 설정 확인
starship config

# 프롬프트 미리보기
starship explain
```

### tmux

터미널 멀티플렉서. 하나의 터미널에서 여러 세션/창/패널을 관리하고, SSH 세션 유지에 유용하다. 이 dotfiles의 tmux 설정은 [tmux.md](./tmux.md)를 참고한다.

```sh
# 새 세션 시작
tmux new -s main

# 세션 목록 확인
tmux ls

# 세션에 재연결
tmux attach -t main
```

### macism

macOS IME(입력기) 전환 CLI 도구. tmux에서 노멀 모드 진입 시 영문으로 자동 전환하는 데 사용된다.

```sh
# 현재 입력기 확인
macism

# 영문 입력기로 전환
macism com.apple.keylayout.ABC

# 한글 입력기로 전환
macism com.apple.inputmethod.Korean.2SetKorean
```

---

## 에디터

### neovim

Vim 기반 에디터. 이 dotfiles의 neovim 설정은 [neovim.md](./neovim.md)를 참고한다.

```sh
# 파일 열기
nvim README.md

# 현재 디렉토리 열기
nvim .

# 특정 줄로 이동해서 열기
nvim +42 src/index.ts
```

---

## Shell 플러그인

### zsh-autosuggestions

이전에 입력했던 명령어를 기반으로 자동 완성을 제안한다. 회색으로 표시되며 `→` 키로 수락.

```sh
# 예: 이전에 git commit -m "feat: 기능 추가"를 입력한 적이 있다면
# git 까지 입력하면 나머지가 회색으로 제안됨
git commit -m "feat: 기능 추가"   # → 키로 수락

# 부분 수락: Ctrl+→ (단어 단위로 수락)
```

### zsh-syntax-highlighting

명령어를 입력하는 동안 실시간으로 구문 강조를 적용한다.

- 유효한 명령어: **녹색**
- 잘못된 명령어: **빨간색**
- 파일 경로: **밑줄**

별도 설정 없이 설치만 하면 동작한다.

---

## 데이터/클라우드 도구

### jq

JSON 파싱 및 필터링 도구. API 응답이나 설정 파일 처리에 유용하다.

```sh
# JSON 파일 pretty print
jq . data.json

# 특정 필드 추출
jq '.users[].name' data.json

# curl 응답을 바로 파싱
curl -s https://api.example.com/users | jq '.[0].email'
```

### awscli

AWS 서비스를 CLI에서 관리하는 도구.

```sh
# S3 버킷 목록 확인
aws s3 ls

# EC2 인스턴스 목록 확인
aws ec2 describe-instances --query 'Reservations[*].Instances[*].InstanceId'

# 프로파일 지정해서 실행
aws --profile work s3 ls
```

---

## 언어/런타임

### node

Node.js 런타임.

```sh
# 버전 확인
node --version

# 스크립트 실행
node script.js

# REPL 실행
node
```

### pnpm

`npm`을 대체하는 빠른 Node.js 패키지 매니저. 디스크 공간을 효율적으로 사용한다.

```sh
# 패키지 설치
pnpm install

# 패키지 추가
pnpm add react

# 스크립트 실행
pnpm dev
```

### pipx

Python CLI 도구를 격리된 환경에 설치하는 도구. 시스템 Python을 오염시키지 않고 CLI 도구를 설치할 수 있다.

```sh
# CLI 도구 설치
pipx install black

# 설치된 도구 목록
pipx list

# 일회성으로 실행 (설치 없이)
pipx run cowsay hello
```

### python@3.12

Python 런타임.

```sh
# 버전 확인
python3 --version

# 스크립트 실행
python3 script.py

# 가상환경 생성
python3 -m venv .venv
```
