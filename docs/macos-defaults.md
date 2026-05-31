# macOS 시스템 설정

`run_onchange_configure-macos.sh.tmpl`로 macOS 시스템 설정을 자동 관리. 새 머신에서 `chezmoi apply` 시 자동 실행.

## 동작 방식

`run_onchange_*.sh.tmpl` 패턴 — 렌더링된 스크립트 내용이 바뀌면 chezmoi가 SHA256 hash로 감지해서 자동 재실행한다. GUI에서 설정만 되돌린 경우에는 스크립트 hash가 그대로라 다음 `chezmoi apply`만으로 재실행되지 않는다.

강제로 다시 적용하려면 스크립트 주석이라도 수정해 hash를 바꾸는 방법이 가장 단순하다. 실행 상태를 직접 지울 때는 `scriptState` 전체가 아니라 `configure-macos.sh`에 해당하는 key만 삭제한다:

```bash
chezmoi state dump | rg -C2 configure-macos.sh
chezmoi state delete --bucket=scriptState --key=<configure-macos.sh의 hash>
chezmoi apply
```

## 적용된 설정 (20개)

### 키보드 (vim/Flutter 개발자 필수)

| 항목 | 값 | 효과 |
|------|-----|------|
| `ApplePressAndHoldEnabled` | false | vim hjkl 반복 가능 (액센트 메뉴 비활성화) |
| `KeyRepeat` | 2 | 키 반복 속도 빠르게 (재로그인 필요) |
| `InitialKeyRepeat` | 15 | 반복 시작 시간 짧게 (재로그인 필요) |
| `NSAutomatic{Capitalization,SpellingCorrection,QuoteSubstitution,DashSubstitution,PeriodSubstitution}Enabled` | false | 자동 텍스트 변환 5종 끔 (코드 작성 거슬림 제거) |

### 트랙패드

| 항목 | 값 | 효과 |
|------|-----|------|
| `Clicking` | true | 탭 클릭 활성화 (4개 도메인) |

### Finder

| 항목 | 값 | 효과 |
|------|-----|------|
| `ShowPathbar` | true | 경로 표시줄 |
| `ShowStatusBar` | true | 상태 표시줄 |
| `AppleShowAllExtensions` | true | 모든 확장자 표시 |
| `FXDefaultSearchScope` | SCcf | 현재 폴더에서 검색 (전체 Mac 아님) |
| `FXEnableExtensionChangeWarning` | false | 확장자 변경 경고 끔 |
| `DSDontWriteNetworkStores`, `DSDontWriteUSBStores` | true | .DS_Store 외장에 안 만듦 |

### Dock

| 항목 | 값 | 효과 |
|------|-----|------|
| `autohide` | true | 자동 숨김 |
| `autohide-delay` | 0 | 등장 지연 0초 |
| `autohide-time-modifier` | 0.4 | 등장 애니메이션 빠르게 |
| `show-recents` | false | 최근 앱 영역 숨김 |
| `mru-spaces` | false | Spaces 자동 재정렬 끔 (tmux/Hammerspoon 사용자 muscle memory 보호) |

### 스크린샷

| 항목 | 값 | 효과 |
|------|-----|------|
| `location` | `~/Pictures/Screenshots` | 데스크탑 정돈 |
| `type` | png | PNG 무손실 |
| `disable-shadow` | true | 윈도우 캡처 시 그림자 제거 |

### 메뉴바

| 항목 | 값 | 효과 |
|------|-----|------|
| `Show24Hour` | true | 24시간 형식 |
| `ShowSeconds` | false | 초 숨김 |
| `ShowDate` | 1 | 날짜 표시 |

### 윈도우 매니지먼트

| 항목 | 값 | 효과 |
|------|-----|------|
| `EnableTilingByEdgeDrag` | false | 시스템 Window Tiling 끔 (Hammerspoon과 충돌 방지) |

## 의도적으로 뺀 것들

| 항목 | 이유 |
|------|------|
| `nvram StartupMute` (시작음 끔) | Apple Silicon에서 SIP 영향으로 실패 가능 |
| 자연스러운 스크롤 끄기 | 사용자 취향 강함 |
| Caps Lock → Esc 매핑 | 한영 전환에 사용 중 |
| 윈도우 애니메이션 가속 (`NSWindowResizeTime`) | 일부 앱(Excel) 깨짐 보고 |
| Spotlight 카테고리 | macOS 26에서 키 변경됨, 안전성 ↓ |
| 핫코너 | GUI에서 직접 설정 권장 |
| 방화벽 켜기 (sudo) | 회사 MDM과 충돌 가능 |

## TCC 보호 영역 (자동화 불가)

다음은 **macOS 보안 모델상 자동 부여 불가**. 새 머신에서 GUI로 직접 설정 필요:

- **손쉬운 사용 (Accessibility)** — Hammerspoon, macism
- **화면 녹화** — KeyCastr
- **Full Disk Access** — 필요 시 직접 추가
- **자동화 (Apple Events)** — AppleScript 사용 앱

## 수정 흐름

```bash
chezmoi edit ~/.config/dotfiles/run_onchange_configure-macos.sh.tmpl
# 또는 직접 편집:
$EDITOR ~/code/dotfiles/run_onchange_configure-macos.sh.tmpl

# chezmoi apply 시 hash 변경 감지 → 자동 재실행
chezmoi apply
```

## 새 머신 셋업 흐름

```bash
# 1. README의 2단계 설치 흐름 실행
./install.sh
claude "~/code/dotfiles/setup.sh를 실행해서 개발 환경 설정을 완료해줘"

# 2. 자동 적용된 설정 확인
defaults read com.apple.dock autohide   # 1
defaults read -g KeyRepeat              # 2

# 3. TCC 권한 GUI에서 부여 (위 목록 참고)

# 4. 재로그인 (KeyRepeat 등 일부 설정 완전 적용용)
```

## 반영 시점

| 즉시 (killall) | 재로그인 필요 |
|----------------|---------------|
| Dock, Finder, 스크린샷, 메뉴바, 자동텍스트, ApplePressAndHoldEnabled | KeyRepeat, InitialKeyRepeat |

스크립트 마지막에 `Dock`, `Finder`, `SystemUIServer`, `ControlCenter`, `cfprefsd`를 일괄 `killall`해서 즉시 반영.

## 새 설정 추가 방법

1. **plistwatch 사용** (가장 안전):
   ```bash
   brew install plistwatch
   plistwatch
   # 다른 터미널에서 GUI 설정 토글 → 정확한 defaults write 명령 자동 출력
   ```

2. **mathiasbynens/dotfiles의 .macos 참고** — 200+ 설정 레퍼런스
3. **macos-defaults.com** — 카테고리별 검색 가능

## 참고 자료

- [mathiasbynens/dotfiles - .macos](https://github.com/mathiasbynens/dotfiles/blob/main/.macos)
- [macos-defaults.com](https://macos-defaults.com/)
- [chezmoi: Use scripts to perform actions](https://www.chezmoi.io/user-guide/use-scripts-to-perform-actions/)
- [Okta: Discovering macOS Settings with PlistWatch](https://developer.okta.com/blog/2021/07/19/discover-macos-settings-with-plistwatch)
- [Eclectic Light: How Preferences do and don't work](https://eclecticlight.co/2023/07/28/how-preferences-do-and-dont-work/)
