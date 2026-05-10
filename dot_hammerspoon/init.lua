-- =============================================================================
-- Hammerspoon init.lua — Magnet 호환 윈도우 매니지먼트
-- Magnet 기본 단축키를 그대로 사용한다.
-- =============================================================================

-- Magnet과 동일하게 즉시 이동 (애니메이션 없음)
hs.window.animationDuration = 0

-- ---------------------------------------------------------------------------
-- Modifier 정의
-- ---------------------------------------------------------------------------
local mash    = { "ctrl", "alt" }         -- ⌃⌥
local mashCmd = { "ctrl", "alt", "cmd" }  -- ⌃⌥⌘ (모니터 간 이동)
local appKey  = { "alt", "cmd" }          -- ⌥⌘ (앱 토글, 한손 가능)

-- ---------------------------------------------------------------------------
-- 복원용: 이동 전 윈도우 위치 저장
-- ---------------------------------------------------------------------------
local windowHistory = {}

local function saveHistory(win)
  local id = win:id()
  if id and not windowHistory[id] then
    windowHistory[id] = win:frame()
  end
end

-- ---------------------------------------------------------------------------
-- 헬퍼: 화면 비율로 윈도우 이동
--   xRatio, yRatio: 화면 내 시작 위치 (0~1)
--   wRatio, hRatio: 윈도우 크기 비율 (0~1)
-- ---------------------------------------------------------------------------
local function moveTo(xRatio, yRatio, wRatio, hRatio)
  return function()
    local win = hs.window.focusedWindow()
    if not win then return end
    saveHistory(win)

    local screen = win:screen():frame()
    win:setFrame({
      x = math.floor(screen.x + screen.w * xRatio),
      y = math.floor(screen.y + screen.h * yRatio),
      w = math.floor(screen.w * wRatio),
      h = math.floor(screen.h * hRatio),
    })
  end
end

-- ---------------------------------------------------------------------------
-- 헬퍼: 다른 모니터로 이동 (위치 비율 유지)
-- ---------------------------------------------------------------------------
local function moveToScreen(direction)
  return function()
    local win = hs.window.focusedWindow()
    if not win then return end
    local target = direction == "next"
      and win:screen():next()
      or  win:screen():previous()
    win:moveToScreen(target, true, false, 0)
  end
end

-- ---------------------------------------------------------------------------
-- 헬퍼: 이전 위치로 복원
-- ---------------------------------------------------------------------------
local function restore()
  local win = hs.window.focusedWindow()
  if not win then return end
  local id = win:id()
  if id and windowHistory[id] then
    win:setFrame(windowHistory[id])
    windowHistory[id] = nil
  end
end

-- ---------------------------------------------------------------------------
-- 헬퍼: 현재 크기 유지하고 화면 중앙으로
-- ---------------------------------------------------------------------------
local function center()
  local win = hs.window.focusedWindow()
  if not win then return end
  saveHistory(win)
  win:centerOnScreen()
end

-- ---------------------------------------------------------------------------
-- 사이클 분할: 같은 화살표 반복 시 1/2 → 1/3 → 1/4 순환
-- ---------------------------------------------------------------------------
local cycleSteps = {
  -- {xRatio, yRatio, wRatio, hRatio}
  left   = { {0,   0,   1/2, 1  }, {0,   0,   1/3, 1  }, {0,   0,   1/4, 1  } },
  right  = { {1/2, 0,   1/2, 1  }, {2/3, 0,   1/3, 1  }, {3/4, 0,   1/4, 1  } },
  top    = { {0,   0,   1,   1/2}, {0,   0,   1,   1/3}, {0,   0,   1,   1/4} },
  bottom = { {0,   1/2, 1,   1/2}, {0,   2/3, 1,   1/3}, {0,   3/4, 1,   1/4} },
}

local function frameMatches(f, screen, xR, yR, wR, hR)
  local tol = 5  -- sub-pixel 허용 오차
  return math.abs(f.x - (screen.x + screen.w * xR)) < tol
    and  math.abs(f.y - (screen.y + screen.h * yR)) < tol
    and  math.abs(f.w - (screen.w * wR))            < tol
    and  math.abs(f.h - (screen.h * hR))            < tol
end

local function cycleSide(side)
  return function()
    local win = hs.window.focusedWindow()
    if not win then return end
    saveHistory(win)

    local screen = win:screen():frame()
    local f = win:frame()
    local steps = cycleSteps[side]

    -- 현재 위치가 사이클의 어느 단계인지 판단
    local nextIdx = 1  -- 기본: 첫 단계 (1/2)
    for i, s in ipairs(steps) do
      if frameMatches(f, screen, s[1], s[2], s[3], s[4]) then
        nextIdx = (i % #steps) + 1  -- 다음 단계, 끝이면 1로 wrap
        break
      end
    end

    local s = steps[nextIdx]
    win:setFrame({
      x = math.floor(screen.x + screen.w * s[1]),
      y = math.floor(screen.y + screen.h * s[2]),
      w = math.floor(screen.w * s[3]),
      h = math.floor(screen.h * s[4]),
    })
  end
end

-- =============================================================================
-- 키바인딩 (Magnet 기본 단축키)
-- =============================================================================

-- Halves with cycle: ⌃⌥ + 화살표 (반복 시 1/2 → 1/3 → 1/4 순환)
hs.hotkey.bind(mash, "left",  cycleSide("left"))
hs.hotkey.bind(mash, "right", cycleSide("right"))
hs.hotkey.bind(mash, "up",    cycleSide("top"))
hs.hotkey.bind(mash, "down",  cycleSide("bottom"))

-- Corners (Quarters): ⌃⌥ + U/I/J/K
hs.hotkey.bind(mash, "u", moveTo(0,   0,   0.5, 0.5))  -- 좌상
hs.hotkey.bind(mash, "i", moveTo(0.5, 0,   0.5, 0.5))  -- 우상
hs.hotkey.bind(mash, "j", moveTo(0,   0.5, 0.5, 0.5))  -- 좌하
hs.hotkey.bind(mash, "k", moveTo(0.5, 0.5, 0.5, 0.5))  -- 우하

-- Thirds: ⌃⌥ + D/F/G
hs.hotkey.bind(mash, "d", moveTo(0,   0, 1/3, 1))  -- 좌 1/3
hs.hotkey.bind(mash, "f", moveTo(1/3, 0, 1/3, 1))  -- 중 1/3
hs.hotkey.bind(mash, "g", moveTo(2/3, 0, 1/3, 1))  -- 우 1/3

-- Two-Thirds: ⌃⌥ + E/T
hs.hotkey.bind(mash, "e", moveTo(0,   0, 2/3, 1))  -- 좌 2/3
hs.hotkey.bind(mash, "t", moveTo(1/3, 0, 2/3, 1))  -- 우 2/3

-- Maximize / Center / Restore
hs.hotkey.bind(mash, "return", moveTo(0, 0, 1, 1))  -- 최대화 ⌃⌥Return
hs.hotkey.bind(mash, "c",      center)              -- 중앙   ⌃⌥C
hs.hotkey.bind(mash, "delete", restore)             -- 복원   ⌃⌥Delete

-- Move to Display: ⌃⌥⌘ + ←/→
hs.hotkey.bind(mashCmd, "left",  moveToScreen("previous"))
hs.hotkey.bind(mashCmd, "right", moveToScreen("next"))

-- =============================================================================
-- 앱 토글 (⌥⌘ + 한 글자) — 한손 누름 가능
-- 같은 키 다시 누르면 hide. 미설치 앱은 자동 스킵해서 머신별 portability 확보.
-- 일부 앱의 같은 단축키(⌥⌘T=Toolbar 등)는 Hammerspoon이 글로벌로 가로챈다.
-- =============================================================================
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

local function bindIfAppExists(modifier, key, appName)
  if hs.application.infoForBundlePath("/Applications/" .. appName .. ".app") then
    hs.hotkey.bind(modifier, key, toggleApp(appName))
  end
end

bindIfAppExists(appKey, "w", "Google Chrome")  -- Web
bindIfAppExists(appKey, "s", "Slack")
bindIfAppExists(appKey, "g", "Figma")          -- G = Graphics (F는 Mail Search 충돌)
bindIfAppExists(appKey, "e", "Ghostty")        -- E = 터미널 (T는 Toolbar 충돌 다수)

-- =============================================================================
-- 설정 자동 리로드 (~/.hammerspoon/ 내 .lua 변경 시)
-- =============================================================================
local function reloadConfig(files)
  for _, file in ipairs(files) do
    if file:sub(-4) == ".lua" then
      hs.reload()
      return
    end
  end
end

hs.pathwatcher.new(os.getenv("HOME") .. "/.hammerspoon/", reloadConfig):start()

hs.alert.show("Hammerspoon loaded ✓")
