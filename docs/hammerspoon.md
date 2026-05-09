# Hammerspoon 사용 가이드

macOS 자동화 툴. Lua 스크립트로 윈도우 매니지먼트, 단축키, 시스템 자동화를 구현한다.

## 설치

```bash
brew install --cask hammerspoon
```

Brewfile에 포함되어 있어 `brew bundle --global`로 자동 설치.

## 초기 설정

1. Hammerspoon 실행 → 메뉴바 망치 아이콘 표시
2. **시스템 설정 → 손쉬운 사용(Accessibility)** 권한 부여 (필수)
3. 추가 권한 (필요 시):
   - **화면 기록** — 윈도우 캡처/제어 일부 기능
   - **자동화** — AppleScript로 다른 앱 제어
4. 설정 파일 위치: `~/.hammerspoon/init.lua`

로그인/계정 가입은 필요 없음 (오픈소스 MIT 라이선스).

## 현재 설정 — Magnet 호환 윈도우 매니지먼트

dotfiles의 `dot_hammerspoon/init.lua`에 Magnet 기본 단축키를 그대로 매핑한 윈도우 매니지먼트를 구성했다. **외부 Spoon이나 라이브러리 의존 없이 Hammerspoon 내장 API만 사용** (`hs.window`, `hs.hotkey`, `hs.pathwatcher`, `hs.alert`).

### 지원 단축키 전체

| 동작 | 단축키 |
|------|--------|
| 좌/우/상/하 절반 | `⌃⌥` + ←/→/↑/↓ |
| 좌상/우상/좌하/우하 모서리 (4분할) | `⌃⌥` + U/I/J/K |
| 좌/중/우 1/3 | `⌃⌥` + D/F/G |
| 좌 2/3 | `⌃⌥` + E |
| 우 2/3 | `⌃⌥` + T |
| 최대화 | `⌃⌥` + Return |
| 중앙 (현재 크기 유지) | `⌃⌥` + C |
| 이전 위치 복원 | `⌃⌥` + Delete |
| 이전/다음 모니터로 이동 | `⌃⌥⌘` + ←/→ |

### 구현 디테일

- `hs.window.animationDuration = 0` — Magnet과 동일한 즉시 이동
- `moveTo(xRatio, yRatio, wRatio, hRatio)` 단일 헬퍼로 DRY 구성 (모든 분할 동작이 이 함수 하나)
- `screen:frame()` 사용 — Dock/메뉴바 영역 존중
- `math.floor` 적용 — sub-pixel 잘림 방지
- 윈도우 ID 기반 history 테이블로 "복원" 동작 구현 (Magnet의 ⌃⌥Delete와 동일 동작)
- `hs.pathwatcher` 내장 — `~/.hammerspoon/` 내 .lua 파일 변경 시 자동 리로드

### Magnet에서 마이그레이션 시 주의사항

1. **Magnet 종료 필수** — 메뉴바 Magnet 아이콘 → Quit. 동시 실행 시 같은 단축키가 충돌
2. **Magnet 로그인 항목 제거** — 시스템 설정 → 일반 → 로그인 항목에서 Magnet 빼기 (재부팅 시 자동 실행 방지)
3. **Hammerspoon을 로그인 항목에 추가** — Hammerspoon Preferences → "Launch Hammerspoon at login" 체크
4. 며칠 사용 후 안정적이면 Magnet 앱 자체 제거 가능

### init.lua 수정 흐름

```bash
chezmoi edit ~/.hammerspoon/init.lua    # 자동 apply + commit + push
# 저장 즉시 pathwatcher가 hs.reload() 호출 → 변경사항 즉시 반영
```

### 의도적으로 사용하지 않은 Spoon

아래 Spoon들은 강력하지만 **"Magnet 단축키 그대로"** 라는 요구와 매핑이 어긋나서 사용하지 않았다. 향후 사이클식 분할이나 더 풍부한 기능을 원할 때 단계적 도입 가능.

| Spoon | 설치 시점 |
|-------|----------|
| MiroWindowsManager | 같은 키 반복으로 1/2→1/3→2/3 사이클을 원할 때 |
| SpoonInstall | 다른 Spoon을 코드로 관리하고 싶을 때 |
| ReloadConfiguration | 자체 pathwatcher 대신 Spoon 방식 선호 시 |

## 커뮤니티 표준 사용 패턴

awesome-hammerspoon, 공식 Spoons, 5+ 인기 dotfiles (zzamboni, cmsj, philc, trishume), HN/Reddit 토론을 cross-reference한 결과.

### 0. 거의 모든 init.lua의 공통 시작 부분

```lua
super = {"cmd", "ctrl", "alt"}
hyper = {"cmd", "ctrl", "alt", "shift"}

-- 파일 변경 시 자동 reload
hs.loadSpoon("ReloadConfiguration")
spoon.ReloadConfiguration:start()

-- Spoon 패키지 매니저
hs.loadSpoon("SpoonInstall")
spoon.SpoonInstall.use_syncinstall = true
Install = spoon.SpoonInstall

hs.alert.show("Config loaded")
```

### A. 윈도우 매니지먼트 — 가장 많이 쓰이는 영역

Rectangle/Magnet/Spectacle 대체로 쓰는 게 압도적.

가장 자주 등장하는 매핑:

| 동작 | 키 |
|------|-----|
| 좌/우 절반 | hyper + ←/→ |
| 전체화면 | hyper + F |
| 화면 중앙 | hyper + C |
| 다음 모니터 | hyper + N |
| 1/2 → 1/3 → 2/3 사이클 | 같은 키 반복 |

**가장 인기 Spoon: MiroWindowsManager**

```lua
hs.loadSpoon("MiroWindowsManager")
hs.window.animationDuration = 0.3
spoon.MiroWindowsManager:bindHotkeys({
  up         = {hyper, "up"},
  down       = {hyper, "down"},
  left       = {hyper, "left"},
  right      = {hyper, "right"},
  fullscreen = {hyper, "f"},
  nextscreen = {hyper, "n"},
})
```

Spectacle 사용자 마이그레이션은 **Lunette** Spoon이 표준.

### B. 앱 런처/스위처 — "토글식" 패턴

같은 키를 다시 누르면 hide되는 패턴.

| 키 | 앱 |
|-----|----|
| hyper + E | 터미널 (Ghostty/iTerm) |
| hyper + W | 브라우저 (Chrome/Arc) |
| hyper + S | Slack |
| hyper + C | 에디터 (VS Code) |
| hyper + N | 노트 (Notion/Obsidian) |
| hyper + F | Finder |

```lua
local function toggleApp(name)
  return function()
    local app = hs.application.find(name)
    if app and app:isFrontmost() then
      app:hide()
    else
      hs.application.launchOrFocus(name)
    end
  end
end

hs.hotkey.bind(hyper, "e", toggleApp("Ghostty"))
hs.hotkey.bind(hyper, "w", toggleApp("Google Chrome"))
hs.hotkey.bind(hyper, "s", toggleApp("Slack"))
hs.hotkey.bind(hyper, "c", toggleApp("Visual Studio Code"))
```

### C. Hyper Key 패턴

거의 보편적. 두 갈래.

**1. 간단 방식: 4-modifier 클러스터**

```lua
hyper = {"cmd", "ctrl", "alt", "shift"}
```

macOS Sequoia의 시스템 설정 "Hyper Key" 옵션 또는 Karabiner-Elements로 Caps Lock → ⌃⌥⌘⇧ 매핑.

**2. 고급 방식: F18 modal trigger** (Brett Terpstra/Evan Travers 스타일)

Caps Lock → F18 (Karabiner) → Hammerspoon이 modal로 처리. **HYPER+SHIFT+R** 같은 추가 modifier 조합 가능. Vim 사용자에게 폭발적 인기.

```lua
local hyperModal = hs.hotkey.modal.new({}, "F17")

local function enterHyper() hyperModal.triggered = false; hyperModal:enter() end
local function exitHyper()
  hyperModal:exit()
  if not hyperModal.triggered then
    hs.eventtap.keyStroke({}, "ESCAPE")  -- tap-only 면 ESC
  end
end
hs.hotkey.bind({}, "F18", enterHyper, exitHyper)

hyperModal:bind({}, "l", function() hs.caffeinate.lockScreen(); hyperModal.triggered=true end)
hyperModal:bind({"shift"}, "r", function() hs.reload(); hyperModal.triggered=true end)
```

별도로 거의 만장일치 추천: **Caps Lock = tap Esc / hold Ctrl** (Karabiner Complex Modifications).

### D. TOP 10 Spoons (커뮤니티 cross-reference 빈도순)

| 순위 | Spoon | 용도 |
|----|------|------|
| 1 | SpoonInstall | Spoon 패키지 매니저 |
| 2 | ReloadConfiguration | 설정 자동 reload |
| 3 | MiroWindowsManager | 윈도우 분할 |
| 4 | WindowHalfsAndThirds | 단순 분할 |
| 5 | Caffeine | 슬립 방지 |
| 6 | Seal | Spotlight/Alfred 대체 |
| 7 | ClipboardTool | 클립보드 히스토리 |
| 8 | URLDispatcher | URL → 앱 라우팅 (회사/개인 분기) |
| 9 | HeadphoneAutoPause | 헤드폰 분리 시 일시정지 |
| 10 | KSheet | 단축키 치트시트 |

### E. 자동 환경 전환 — "신세계" 평가받는 영역

#### WiFi 자동 감지

집/회사 SSID에 따라 볼륨, 네트워크 위치 자동 변경.

```lua
local homeSSID = "MyHomeWiFi"
local lastSSID = hs.wifi.currentNetwork()

local function ssidChanged()
  local newSSID = hs.wifi.currentNetwork()
  if newSSID == homeSSID and lastSSID ~= homeSSID then
    hs.audiodevice.defaultOutputDevice():setVolume(50)
  elseif newSSID ~= homeSSID and lastSSID == homeSSID then
    hs.audiodevice.defaultOutputDevice():setVolume(0)
  end
  lastSSID = newSSID
end

wifiWatcher = hs.wifi.watcher.new(ssidChanged):start()
```

#### 외부 모니터 연결 시 자동 레이아웃

```lua
local internal = "Built-in Retina Display"
local external = "LG UltraFine"

local function applyLayout()
  if #hs.screen.allScreens() > 1 then
    hs.layout.apply({
      {"Slack",         nil, external, hs.layout.left50,    nil, nil},
      {"Google Chrome", nil, external, hs.layout.right50,   nil, nil},
      {"Ghostty",       nil, internal, hs.layout.maximized, nil, nil},
    })
  end
end

screenWatcher = hs.screen.watcher.new(applyLayout):start()
applyLayout()
```

#### USB 인식 자동화

특정 USB 장치 연결 시 앱 자동 실행 (cmsj 메인테이너 유명 사례).

```lua
usbWatcher = hs.usb.watcher.new(function(e)
  if e.productName == "ScanSnap S1300i" and e.eventType == "added" then
    hs.application.launchOrFocus("ScanSnap Manager")
  end
end):start()
```

#### Sleep/Wake 시 자동 음소거

```lua
caffeineWatcher = hs.caffeinate.watcher.new(function(eventType)
  if eventType == hs.caffeinate.watcher.systemWillSleep then
    hs.audiodevice.defaultOutputDevice():setMuted(true)
  elseif eventType == hs.caffeinate.watcher.systemDidWake then
    hs.audiodevice.defaultOutputDevice():setMuted(false)
  end
end)
caffeineWatcher:start()
```

### F. 한국 사용자에게 유용한 패턴

#### 한영 입력기 토글

```lua
hs.hotkey.bind({}, "right_alt", function()
  local id = hs.keycodes.currentSourceID()
  hs.keycodes.currentSourceID(
    id:find("Roman")
      and "com.apple.inputmethod.Korean.2SetKorean"
      or "com.apple.keylayout.ABC"
  )
end)
```

### G. 기타 추천 패턴

#### 다른 앱 모두 hide

```lua
hs.hotkey.bind({"cmd","shift"}, "h", function()
  local front = hs.application.frontmostApplication()
  for _, app in ipairs(hs.application.runningApplications()) do
    if app:bundleID() ~= front:bundleID() and app:kind() == 1 then
      app:hide()
    end
  end
end)
```

#### Vim 모드를 모든 텍스트 필드에

```lua
local vim = hs.loadSpoon("VimMode"):new()
vim:disableForApp("Code"):enterWithSequence("jk")
```

#### 화면 잠그기

```lua
hs.hotkey.bind(hyper, "l", function()
  hs.caffeinate.lockScreen()
end)
```

#### 똑똑한 볼륨 컨트롤

볼륨 0 근처에서 작은 step (실수로 폭음 방지).

```lua
hs.hotkey.bind({}, "F11", function()
  local d = hs.audiodevice.defaultOutputDevice()
  local v = d:volume()
  d:setVolume(math.max(0, v < 20 and v - 2 or v - 5))
end)
```

## 신규 사용자 추천 시작 세트 (Top 7)

조사한 모든 출처의 교집합. 이것만으로 Rectangle + Alfred + Caffeine + Karabiner 일부를 한 번에 대체.

1. **Boilerplate** — super/hyper 정의 + ReloadConfiguration
2. **MiroWindowsManager** — 윈도우 분할 한 방
3. **앱 토글 함수 + hyper + 한 글자** (5개 핵심 앱)
4. **Caps Lock = tap Esc / hold Ctrl** + Hyper Key (Karabiner)
5. **Caffeine + HeadphoneAutoPause** — 두 줄짜리 QoL Spoon
6. **WiFi watcher** — 집/회사 자동 모드 전환
7. **Screen watcher + hs.layout** — 외부 모니터 자동 레이아웃

익숙해진 후 `ClipboardTool` → `URLDispatcher` → `Seal` → `VimMode` 단계적 추가가 표준 학습 경로.

## dotfiles로 관리하기

`~/.hammerspoon/init.lua`를 chezmoi로 관리하려면:

```bash
chezmoi add ~/.hammerspoon/init.lua
chezmoi add ~/.hammerspoon/Spoons   # Spoon 디렉토리 전체
```

여러 lua 파일로 분할한 경우 디렉토리 통째로 add 가능.

## 참고 자료

- [공식 사이트](https://www.hammerspoon.org/)
- [Getting Started](https://www.hammerspoon.org/go/)
- [Spoons 디렉토리](https://www.hammerspoon.org/Spoons/)
- [API 문서](https://www.hammerspoon.org/docs/)
- [Sample Configurations Wiki](https://github.com/Hammerspoon/hammerspoon/wiki/Sample-Configurations)
- [awesome-hammerspoon](https://github.com/ashfinal/awesome-hammerspoon)
- [Learn Hammerspoon](https://learnhammerspoon.com/)

### 인기 dotfiles 레퍼런스

- [zzamboni/dot-hammerspoon](https://github.com/zzamboni/dot-hammerspoon)
- [cmsj/hammerspoon-config (메인테이너)](https://github.com/cmsj/hammerspoon-config)
- [trishume/dotfiles](https://github.com/trishume/dotfiles)
- [philc/hammerspoon-config](https://github.com/philc/hammerspoon-config)

### Hyper Key 가이드

- [Brett Terpstra: Hyper Key with Karabiner](https://brettterpstra.com/2017/06/15/a-hyper-key-with-karabiner-elements-full-instructions/)
- [Evan Travers: A Better Hyper Key](https://evantravers.com/articles/2020/06/08/hammerspoon-a-better-better-hyper-key/)
- [jasonrudolph/keyboard - "ubiquitous keybindings"](https://github.com/jasonrudolph/keyboard)
