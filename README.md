# dotfiles

macOS 개발 환경 설정 (tmux, iTerm2, Claude Code)

## 사전 준비

### Homebrew

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### macism

tmux에서 한/영 자동 전환에 사용하는 CLI 도구.
macOS의 CJK 입력 소스 전환 버그를 해결한 유일한 CLI 도구로, `im-select`보다 안정적이다.

```bash
brew tap laishulu/homebrew
brew install macism
```

설치 확인:

```bash
macism                                    # 현재 입력 소스 ID 출력
macism com.apple.keylayout.ABC            # 영문 전환
```

### tmux

```bash
brew install tmux
```

## 설치

```bash
git clone https://github.com/lee-kyu-hwan/dotfiles.git ~/dotfiles
cd ~/dotfiles
```

### 전체 설치

```bash
./install.sh
```

### 개별 설치

원하는 구성 요소만 선택하여 설치할 수 있다.

```bash
./install.sh tmux         # tmux만 설치
./install.sh claude       # Claude Code만 설치
./install.sh iterm2       # iTerm2만 설치
./install.sh tmux claude  # tmux + Claude Code 설치
```

### 사용법 확인

```bash
./install.sh --help
```

## 주의 사항

- **기존 설정이 덮어씌워진다.** 설치 시 기존 로컬 설정 파일이 백업 없이 대체된다. 기존 설정을 보존하려면 설치 전에 직접 백업해야 한다.
  - tmux: `cp ~/.tmux.conf ~/.tmux.conf.bak`
  - Claude Code: `cp ~/.claude/settings.json ~/.claude/settings.json.bak`
  - iTerm2: `cp ~/Library/Preferences/com.googlecode.iterm2.plist ~/Library/Preferences/com.googlecode.iterm2.plist.bak`
- **tmux, Claude Code 설정은 심볼릭 링크로 연결된다.** 로컬에서 설정을 수정하면 레포의 원본 파일이 함께 변경된다.
- **iTerm2 설정은 복사본이다.** macOS defaults 시스템과의 호환을 위해 심볼릭 링크가 아닌 복사로 처리된다. iTerm2 설정을 변경해도 레포에 자동 반영되지 않는다.
- **macism이 필요하다.** tmux 한글 입력 호환 기능은 macism에 의존한다. `./install.sh tmux` 실행 시 자동으로 설치된다.

## 구성 파일

```
dotfiles/
├── install.sh
├── tmux/.tmux.conf
├── claude/settings.json
└── iterm2/com.googlecode.iterm2.plist
```

### tmux

한글 입력 상태에서도 tmux 단축키가 동작하도록 3가지를 설정한다.

**1. Ctrl+B 영문 자동 전환**

`Ctrl+B`를 누르는 순간 `macism`으로 영문 전환 후 prefix 테이블에 진입한다.
한글 모드에서 `Ctrl+B` → `w` 를 누르면 영문 전환이 먼저 일어나 `w`가 그대로 전달된다.

**2. 자음 바인딩 (안전망)**

`macism` 전환이 느릴 경우를 대비해 두벌식 자음을 영문 키에 매핑한다.

| 한글 | 영문 | 동작 |
|------|------|------|
| ㅈ | w | 윈도우 리스트 |
| ㅊ | c | 새 윈도우 |
| ㄷ | d | 디태치 |
| ㅜ | n | 다음 윈도우 |
| ㅍ | p | 이전 윈도우 |
| ㅌ | x | 패인 종료 |
| ㅋ | z | 패인 줌 |
| ㄴ | s | 세션 리스트 |
| ㅐ | o | 다음 패인 |
| ㅣ | l | 레이아웃 전환 |
| ㅂ | q | 패인 번호 표시 |
| ㅅ | t | 시계 |

**3. macism 훅 & 명령어 모드**

- 창/패널 전환 시 자동으로 영문 입력으로 초기화
- `:` 명령어 모드 진입 시 영문으로 전환

### iTerm2

설치 후 추가로 설정할 것:

1. Settings (`Cmd+,`) → **Profiles** → **Keys** → **General**
2. **Left Option key** → `Esc+` 로 변경

이 설정으로 `Alt+1` ~ `Alt+5` tmux 레이아웃 단축키가 동작한다.

### Claude Code

- `settings.json`: 플러그인, 권한, 언어 설정
