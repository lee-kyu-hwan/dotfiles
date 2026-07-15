# nvm 기반 Node 24 dotfiles 관리 설계

## 목표

새 머신에서 `chezmoi apply`만으로 nvm과 Node.js 24가 재현 가능하게 설치되도록 한다. Node.js 설치 주체를 Homebrew에서 nvm으로 단일화하고, 새 zsh 세션은 기본적으로 Node.js 24를 사용한다.

## 현재 상태

- macOS Brewfile이 `node`를 설치한다.
- Linux `install.sh`는 NodeSource를 통해 시스템 Node.js를 설치한다.
- 현재 머신에는 curl 설치 방식으로 nvm v0.40.5가 `~/.config/nvm`에 설치되어 있다.
- nvm 설치기가 `~/.zshrc`에 초기화 코드를 직접 추가했지만 chezmoi 소스에는 반영되지 않아 다음 `chezmoi apply`에서 사라질 수 있다.

## 결정

### 설치 및 업그레이드

- chezmoi `run_onchange` 스크립트가 공식 버전 URL로 nvm v0.40.5를 설치한다.
- `PROFILE=/dev/null`을 사용해 nvm 설치기가 홈의 셸 설정을 직접 수정하지 못하게 한다.
- `NVM_DIR`은 XDG 경로인 `${XDG_CONFIG_HOME:-$HOME/.config}/nvm`을 사용한다.
- 스크립트가 `nvm install 24`, `nvm alias default 24`, `nvm use default`를 실행한다.
- nvm 업그레이드는 스크립트의 고정 버전을 변경하는 명시적인 dotfiles 변경으로 수행한다.
- Node.js 24는 정확한 patch가 아니라 major를 지정해 설치 시점의 최신 24.x를 사용한다.

### 셸 초기화

- `dot_zshrc.tmpl`이 `NVM_DIR`을 선언하고 `nvm.sh` 및 bash completion을 조건부로 로드한다.
- 셸 초기화는 chezmoi만 관리하며 설치 스크립트는 `.zshrc`를 수정하지 않는다.
- default alias 덕분에 새 대화형 zsh 세션은 Node.js 24를 사용한다.

### 기존 Node 설치 정리

- macOS Brewfile의 `brew "node"`를 제거한다.
- Linux의 초기 bootstrap에는 Claude Code 실행을 위한 시스템 Node.js 설치를 유지한다. 이후 `chezmoi apply`가 nvm Node.js 24를 설치하고 대화형 셸의 기본 Node를 전환한다.
- 기존 머신에 이미 설치된 Homebrew Node는 이 작업에서 강제 제거하지 않는다. PATH 우선순위는 nvm이 담당하고, 사용자가 원하면 별도로 `brew uninstall node`를 실행할 수 있다.

## 변경 파일

- `run_onchange_install-nvm.sh.tmpl`: nvm v0.40.5와 Node.js 24 설치 및 default alias 설정
- `dot_zshrc.tmpl`: nvm 초기화 코드
- `dot_Brewfile`: Homebrew Node 제거
- `README.md`: 설치 흐름과 관리 정책 설명
- `docs/cli-tools.md`: Node.js 사용·버전 전환 명령을 nvm 기준으로 수정

## 오류 처리

- 설치 스크립트는 `set -euo pipefail`로 실행한다.
- curl 다운로드, nvm 로드, Node.js 24 설치 중 하나라도 실패하면 chezmoi 적용을 실패시킨다.
- 이미 nvm 또는 Node.js 24가 설치된 경우에도 안전하게 다시 실행할 수 있도록 멱등성을 유지한다.
- 설치 완료 후 `command -v nvm`, `nvm version`, `node --version`, `nvm alias default`를 출력해 진단 가능하게 한다.

## 검증

1. 변경된 셸 스크립트에 `bash -n`을 실행한다.
2. `chezmoi execute-template`로 zsh 템플릿 렌더링을 확인한다.
3. `chezmoi diff`에서 의도한 `.zshrc` 및 Brewfile 변경만 확인한다.
4. `chezmoi apply`를 실행한다.
5. 새 zsh에서 `command -v nvm`, `nvm version`, `node --version`, `nvm alias default`를 확인한다.
6. 기대값은 nvm v0.40.5, Node.js v24.x, default alias 24이다.
7. dotfiles 저장소에서 `git diff --check`를 통과한다.

## 비목표

- 프로젝트 디렉터리 진입 시 `.nvmrc`를 자동으로 실행하는 zsh hook은 추가하지 않는다.
- pnpm 설치 및 Corepack 정책은 변경하지 않는다.
- 기존 Homebrew Node 패키지를 자동 제거하지 않는다.
- Node.js 24의 정확한 patch 버전을 dotfiles에 고정하지 않는다.
