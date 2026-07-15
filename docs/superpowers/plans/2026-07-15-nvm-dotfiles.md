# nvm 기반 Node 24 dotfiles 관리 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `chezmoi apply`로 nvm v0.40.5와 최신 Node.js 24.x를 설치하고 새 zsh 세션의 기본 Node 버전을 24로 설정한다.

**Architecture:** chezmoi `run_onchange` 스크립트가 버전이 고정된 공식 nvm 설치 스크립트를 실행하고 Node.js 24 및 default alias를 보장한다. 셸 초기화는 `dot_zshrc.tmpl`만 관리하며, Homebrew Node 의존성을 제거해 대화형 셸의 Node 관리 주체를 nvm으로 단일화한다.

**Tech Stack:** chezmoi 2.70+, Bash, zsh, nvm v0.40.5, Node.js 24, Homebrew Bundle

---

## 파일 구조

- Create: `run_onchange_install-nvm.sh.tmpl` — nvm v0.40.5 설치·업데이트, Node.js 24 설치, default alias 검증
- Modify: `dot_zshrc.tmpl` — 모든 지원 OS에서 XDG 기반 nvm 초기화
- Modify: `dot_Brewfile` — Homebrew Node 관리 제거
- Modify: `README.md` — 설치 흐름과 Node 관리 정책 문서화
- Modify: `docs/cli-tools.md` — nvm 기반 Node 버전 확인·전환 명령 문서화

### Task 1: nvm 및 Node.js 24 자동 설치

**Files:**

- Create: `run_onchange_install-nvm.sh.tmpl`
- Modify: `dot_zshrc.tmpl:74-75`

- [ ] **Step 1: 원하는 설정이 아직 없음을 확인한다**

Run:

```bash
cd ~/code/dotfiles
set -euo pipefail
test -f run_onchange_install-nvm.sh.tmpl
rg -q 'NVM_VERSION="v0.40.5"' run_onchange_install-nvm.sh.tmpl
rg -q 'export NVM_DIR=' dot_zshrc.tmpl
```

Expected: `run_onchange_install-nvm.sh.tmpl`이 없으므로 exit code 1.

- [ ] **Step 2: nvm 설치 스크립트를 추가한다**

Create `run_onchange_install-nvm.sh.tmpl`:

```bash
#!/bin/bash
set -euo pipefail

NVM_VERSION="v0.40.5"
NODE_VERSION="24"
export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
export NVM_DIR="$XDG_CONFIG_HOME/nvm"

install_script="$(mktemp)"
trap 'rm -f "$install_script"' EXIT

curl -fsSL \
  "https://raw.githubusercontent.com/nvm-sh/nvm/${NVM_VERSION}/install.sh" \
  -o "$install_script"
PROFILE=/dev/null NVM_DIR="$NVM_DIR" bash "$install_script"

# shellcheck source=/dev/null
. "$NVM_DIR/nvm.sh"

nvm install "$NODE_VERSION"
nvm alias default "$NODE_VERSION"
nvm use default

expected_nvm_version="${NVM_VERSION#v}"
actual_nvm_version="$(nvm --version)"
actual_node_version="$(node --version)"
default_node_version="$(nvm version default)"

if [[ "$actual_nvm_version" != "$expected_nvm_version" ]]; then
  echo "Expected nvm $expected_nvm_version, got $actual_nvm_version" >&2
  exit 1
fi

if [[ "$actual_node_version" != v24.* ]]; then
  echo "Expected Node.js v24.x, got $actual_node_version" >&2
  exit 1
fi

if [[ "$default_node_version" != v24.* ]]; then
  echo "Expected default Node.js v24.x, got $default_node_version" >&2
  exit 1
fi

echo "nvm $actual_nvm_version"
echo "Node.js $actual_node_version"
echo "default $default_node_version"
```

- [ ] **Step 3: zsh 초기화 코드를 추가한다**

Insert after the macOS-only block ending at `dot_zshrc.tmpl:74`:

```zsh
# ============================================================
# nvm + Node.js
# ============================================================
export NVM_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"

```

- [ ] **Step 4: 스크립트와 렌더링 결과를 검증한다**

Run:

```bash
cd ~/code/dotfiles
set -euo pipefail
bash -n run_onchange_install-nvm.sh.tmpl
chezmoi execute-template < dot_zshrc.tmpl > /tmp/dotfiles-zshrc-rendered
zsh -n /tmp/dotfiles-zshrc-rendered
rg -q 'NVM_VERSION="v0.40.5"' run_onchange_install-nvm.sh.tmpl
rg -q 'export NVM_DIR=' /tmp/dotfiles-zshrc-rendered
```

Expected: exit code 0.

- [ ] **Step 5: 설치 및 셸 설정을 커밋한다**

```bash
cd ~/code/dotfiles
git add run_onchange_install-nvm.sh.tmpl dot_zshrc.tmpl
git commit -m "feat: nvm과 Node 24 자동 설치"
```

### Task 2: Homebrew Node 제거 및 문서 갱신

**Files:**

- Modify: `dot_Brewfile:24`
- Modify: `README.md:21-78`
- Modify: `docs/cli-tools.md:451-468`

- [ ] **Step 1: 원하는 관리 정책이 아직 반영되지 않았음을 확인한다**

Run:

```bash
cd ~/code/dotfiles
set -euo pipefail
if rg -q '^brew "node"$' dot_Brewfile; then
  exit 1
fi
rg -q 'nvm install 24' README.md
rg -q 'nvm alias default 24' docs/cli-tools.md
```

Expected: Brewfile에 `brew "node"`가 있어 exit code 1.

- [ ] **Step 2: Homebrew Node 항목을 제거한다**

Remove this exact line from `dot_Brewfile`:

```ruby
brew "node"
```

- [ ] **Step 3: README의 설치 흐름과 패키지 목록을 갱신한다**

Add `nvm + Node.js 24` to the `setup.sh` side of both macOS and Linux installation diagrams, and add this row to the `chezmoi 관리 설정` table after `zsh`:

```markdown
| nvm | Node.js 버전 관리 (nvm v0.40.5 + 기본 Node.js 24) | O | O | O |
```

Add this section before `### Homebrew 패키지 (macOS)`:

````markdown
### Node.js

Node.js는 Homebrew가 아니라 nvm으로 관리합니다. `chezmoi apply`가 nvm v0.40.5와 최신 Node.js 24.x를 설치하고 default alias를 24로 설정합니다.

```bash
nvm install 24
nvm use 24
nvm alias default 24
```

프로젝트에 `.nvmrc`가 있으면 해당 디렉터리에서 `nvm install`과 `nvm use`를 실행합니다.
````

- [ ] **Step 4: CLI 문서의 Node 항목을 nvm 기준으로 교체한다**

Replace `docs/cli-tools.md`의 `### node` section with:

````markdown
### node / nvm

Node.js 런타임은 nvm으로 관리하며 기본 버전은 최신 24.x다. nvm 자체는 dotfiles에서 v0.40.5로 고정한다.

```sh
# 현재 버전 확인
nvm --version
node --version

# Node.js 24 설치 및 사용
nvm install 24
nvm use 24

# 새 셸의 기본 버전 설정
nvm alias default 24

# 프로젝트의 .nvmrc 사용
nvm install
nvm use

# 설치된 버전 확인
nvm ls
```
````

- [ ] **Step 5: 정책과 문서 형식을 검증한다**

Run:

```bash
cd ~/code/dotfiles
set -euo pipefail
if rg -q '^brew "node"$' dot_Brewfile; then
  exit 1
fi
rg -q 'nvm v0.40.5' README.md
rg -q 'nvm install 24' README.md
rg -q 'nvm alias default 24' docs/cli-tools.md
git diff --check
```

Expected: exit code 0.

- [ ] **Step 6: 패키지 정책과 문서를 커밋한다**

```bash
cd ~/code/dotfiles
git add dot_Brewfile README.md docs/cli-tools.md
git commit -m "docs: nvm 기반 Node 관리 방법 추가"
```

### Task 3: chezmoi 적용 및 실제 셸 검증

**Files:**

- Apply: `~/.zshrc`
- Apply: `~/.Brewfile`
- Execute: `run_onchange_install-nvm.sh.tmpl`

- [ ] **Step 1: 적용 예정 변경을 확인한다**

Run:

```bash
cd ~/code/dotfiles
chezmoi diff ~/.zshrc ~/.Brewfile
```

Expected: `.zshrc`에는 nvm 관리 블록이 추가되고 curl 설치기가 직접 추가한 파일 끝의 중복 블록은 사라진다. `.Brewfile`에서는 `brew "node"`만 제거된다.

- [ ] **Step 2: 관리 파일을 먼저 적용한다**

Run:

```bash
chezmoi apply --exclude=scripts ~/.zshrc ~/.Brewfile
```

Expected: exit code 0. 다른 chezmoi 대상의 로컬 차이는 변경하지 않는다.

- [ ] **Step 3: 변경된 chezmoi 스크립트를 실행한다**

Run:

```bash
chezmoi apply --include=scripts
```

Expected: nvm v0.40.5가 `~/.config/nvm`에 설치 또는 갱신되고 최신 Node.js 24.x가 default alias로 설정된다. 변경된 Brewfile에 대한 `brew bundle --global`도 성공한다.

- [ ] **Step 4: 새 zsh 세션의 기본 Node를 검증한다**

Run:

```bash
TMUX=verification zsh -lic '
  set -e
  test "$(command -v nvm)" = "nvm"
  test "$(nvm --version)" = "0.40.5"
  [[ "$(node --version)" == v24.* ]]
  [[ "$(nvm version default)" == v24.* ]]
'
```

Expected: exit code 0.

- [ ] **Step 5: chezmoi 및 저장소 최종 상태를 검증한다**

Run:

```bash
cd ~/code/dotfiles
set -euo pipefail
chezmoi diff ~/.zshrc ~/.Brewfile
brew bundle check --global
git diff --check
git status -sb
```

Expected: `.zshrc`와 `.Brewfile`의 chezmoi diff가 없고, Brew bundle check와 Git 공백 검사가 통과하며, `chore/add-nvm` 브랜치에 커밋되지 않은 변경이 없다.

### Task 4: 최종 이력 확인

**Files:** None

- [ ] **Step 1: 커밋과 변경 범위를 확인한다**

Run:

```bash
cd ~/code/dotfiles
git log --oneline origin/main..HEAD
git diff --stat origin/main...HEAD
git status -sb
```

Expected: 설계, nvm 설치·셸 설정, 문서·Brewfile의 세 커밋만 존재하고 작업 트리가 깨끗하다. 사용자가 push를 요청하지 않았으므로 원격 전송은 하지 않는다.
