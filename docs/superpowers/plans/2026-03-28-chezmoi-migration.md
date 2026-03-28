# Stow → Chezmoi 마이그레이션 구현 플랜

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** GNU Stow 기반 dotfiles를 chezmoi로 전환하여 macOS(회사/개인) + Linux(클라우드 서버) 멀티 환경을 단일 repo로 관리한다.

**Architecture:** 기존 stow 패키지 디렉토리를 chezmoi의 flat naming convention(`dot_`, `.tmpl`)으로 변환한다. `.chezmoi.toml.tmpl`로 머신 타입을 프롬프트 받고, `.chezmoiignore`로 macOS 전용 파일을 server에서 제외한다. OS 분기가 필요한 `.tmux.conf`과 `.zshrc`는 chezmoi 템플릿으로 작성한다.

**Tech Stack:** chezmoi, Go templates, lazy.nvim, lazygit

**Spec:** `docs/superpowers/specs/2026-03-28-chezmoi-migration-design.md`

---

## File Map

### 생성할 파일 (chezmoi 구조)

| 파일 | 역할 |
|------|------|
| `.chezmoi.toml.tmpl` | 머신 변수 프롬프트 (machine_type) |
| `.chezmoiignore` | server에서 macOS 전용 파일 제외 |
| `dot_tmux.conf.tmpl` | tmux 설정 (OS 분기 템플릿) |
| `dot_zshrc.tmpl` | zsh 설정 (OS 분기 템플릿) |
| `dot_gitconfig` | git 공통 설정 (defaultBranch=develop 추가) |
| `dot_gitconfig-work` | git 회사 환경 |
| `dot_gitconfig-personal` | git 개인 환경 |
| `dot_gitignore_global` | global gitignore |
| `dot_Brewfile` | Homebrew 패키지 (neovim, lazygit, fd 추가) |
| `dot_config/ghostty/config` | Ghostty 설정 |
| `dot_config/starship.toml` | Starship 프롬프트 |
| `dot_claude/settings.json` | Claude Code 전역 설정 (superpowers 추가) |
| `dot_config/lazygit/config.yml` | lazygit 설정 |
| `dot_config/nvim/init.lua` | Neovim 진입점 |
| `dot_config/nvim/lua/config/options.lua` | 에디터 옵션 |
| `dot_config/nvim/lua/config/keymaps.lua` | 키바인딩 |
| `dot_config/nvim/lua/config/lazy.lua` | lazy.nvim 부트스트랩 |
| `dot_config/nvim/lua/plugins/theme.lua` | 테마 (catppuccin) |
| `dot_config/nvim/lua/plugins/treesitter.lua` | 구문 하이라이팅 |
| `dot_config/nvim/lua/plugins/telescope.lua` | fuzzy finder |
| `dot_config/nvim/lua/plugins/lsp.lua` | LSP + mason |
| `dot_config/nvim/lua/plugins/cmp.lua` | 자동완성 |
| `dot_config/nvim/lua/plugins/conform.lua` | 포매팅 |
| `dot_config/nvim/lua/plugins/neo-tree.lua` | 파일 탐색기 |
| `dot_config/nvim/lua/plugins/git.lua` | gitsigns + lazygit.nvim |
| `dot_config/nvim/lua/plugins/editor.lua` | autopairs, Comment, which-key |

### 수정할 파일

| 파일 | 변경 |
|------|------|
| `bootstrap.sh` | 전체 재작성 (chezmoi 기반) |
| `.gitignore` | stow 경로 제거, chezmoi 경로 추가 |
| `README.md` | chezmoi 기반으로 재작성 |

### 삭제할 파일 (안정화 후)

| 파일 | 이유 |
|------|------|
| `tmux/`, `zsh/`, `git/`, `git-work/`, `git-personal/`, `ghostty/`, `claude/`, `brew/`, `starship/` | stow 패키지 디렉토리 |
| `.stow-local-ignore` | stow 전용 |

---

## Task 1: chezmoi 인프라 파일 생성

**Files:**
- Create: `.chezmoi.toml.tmpl`
- Create: `.chezmoiignore`

- [ ] **Step 1: `.chezmoi.toml.tmpl` 생성**

```toml
{{- $machine_type := promptChoiceOnce "machine_type" "Machine type (work-mac: ALA 회사맥북, personal: 개인맥북, server: Linux 개발서버)" (list "work-mac" "personal" "server") }}

[data]
  machine_type = "{{ $machine_type }}"
```

- [ ] **Step 2: `.chezmoiignore` 생성**

```
README.md
docs/**
bootstrap.sh
LICENSE

# stow 잔재 (마이그레이션 기간 동안 chezmoi가 무시)
tmux/**
zsh/**
git/**
git-work/**
git-personal/**
ghostty/**
claude/**
brew/**
starship/**
.stow-local-ignore

# server: macOS 전용 항목만 제외
{{ if eq .machine_type "server" }}
.Brewfile
.config/ghostty/config
{{ end }}
```

> **중요**: stow 패키지 디렉토리와 repo 메타 파일(README, docs, bootstrap.sh)도 ignore에 추가해야 한다. 이들이 없으면 chezmoi가 `~/tmux/`, `~/docs/` 등을 홈에 생성하려 시도한다.

- [ ] **Step 3: 커밋**

```bash
git add .chezmoi.toml.tmpl .chezmoiignore
git commit -m "feat(chezmoi): 인프라 파일 생성 (.chezmoi.toml.tmpl, .chezmoiignore)"
```

---

## Task 2: 정적 설정 파일 변환 (stow → chezmoi 네이밍)

**Files:**
- Create: `dot_gitconfig-work`
- Create: `dot_gitconfig-personal`
- Create: `dot_gitignore_global`
- Create: `dot_config/ghostty/config`
- Create: `dot_config/starship.toml`

- [ ] **Step 1: git 관련 정적 파일 복사**

```bash
cp git-work/.gitconfig-work dot_gitconfig-work
cp git-personal/.gitconfig-personal dot_gitconfig-personal
cp git/.gitignore_global dot_gitignore_global
```

- [ ] **Step 2: config 디렉토리 파일 복사**

```bash
mkdir -p dot_config/ghostty
cp ghostty/.config/ghostty/config dot_config/ghostty/config
cp starship/.config/starship.toml dot_config/starship.toml
```

- [ ] **Step 3: 커밋**

```bash
git add dot_gitconfig-work dot_gitconfig-personal dot_gitignore_global dot_config/
git commit -m "feat(chezmoi): 정적 설정 파일 변환 (git, ghostty, starship)"
```

---

## Task 3: .gitconfig 템플릿 생성 (defaultBranch 추가)

**Files:**
- Create: `dot_gitconfig`

스펙 검토 결과 `.gitconfig`에 OS 분기가 필요 없다 (모든 머신에 동일 배포). 정적 파일로 생성하되, 로컬에서 누락된 `defaultBranch = develop`을 추가한다.

- [ ] **Step 1: `dot_gitconfig` 생성**

```ini
[user]
	name = 이규환
	email = lgh778923@gmail.com

[init]
	defaultBranch = develop

[core]
	excludesfile = ~/.gitignore_global

[filter "lfs"]
	clean = git-lfs clean -- %f
	smudge = git-lfs smudge -- %f
	process = git-lfs filter-process
	required = true

[includeIf "gitdir:~/code/work/"]
	path = ~/.gitconfig-work

[includeIf "gitdir:~/code/personal/"]
	path = ~/.gitconfig-personal
```

- [ ] **Step 2: 커밋**

```bash
git add dot_gitconfig
git commit -m "feat(chezmoi): .gitconfig 변환 (defaultBranch=develop 추가)"
```

---

## Task 4: .tmux.conf 템플릿 생성 (OS 분기)

**Files:**
- Create: `dot_tmux.conf.tmpl`

- [ ] **Step 1: `dot_tmux.conf.tmpl` 생성**

```
set -g mouse on

{{ if eq .chezmoi.os "darwin" -}}
# ============================================================
# 한글 입력 호환 설정 (macOS only)
# ============================================================

# --- 1. Ctrl+B 누르는 순간 영문 전환 (핵심) ---
set -g prefix M-F12
bind -n C-b {
    run-shell "macism com.apple.keylayout.ABC"
    switch-client -T prefix
}
bind C-b send-keys C-b

# --- 1-1. 자음 바인딩 (안전망) ---
bind ㅈ choose-tree -Zw         # w
bind ㅊ new-window              # c
bind ㄷ detach-client            # d
bind ㅜ next-window              # n
bind ㅍ previous-window          # p
bind ㅌ confirm-before -p "kill-pane #P? (y/n)" kill-pane  # x
bind ㅋ resize-pane -Z           # z
bind ㄴ choose-tree -Zs          # s
bind ㅐ select-pane -t :.+       # o
bind ㅣ select-layout next       # l
bind ㅂ display-panes            # q
bind ㅅ clock-mode               # t

# --- 2. macism 훅 (상태 초기화) ---
set-hook -g after-select-pane   'run-shell "macism com.apple.keylayout.ABC"'
set-hook -g after-select-window 'run-shell "macism com.apple.keylayout.ABC"'
set-hook -g pane-focus-in       'run-shell "macism com.apple.keylayout.ABC"'

# --- 3. 명령어 모드 강제 전환 ---
bind : run-shell "macism com.apple.keylayout.ABC" \; command-prompt

{{ else -}}
# ============================================================
# Linux: 표준 prefix
# ============================================================
set -g prefix C-b
bind C-b send-prefix

{{ end -}}
# ============================================================
# Pane 구분: 비활성 pane 어둡게 처리
# ============================================================
set -g window-style 'bg=colour235'
set -g window-active-style 'bg=colour0'
set -g pane-border-style fg=colour238
set -g pane-active-border-style fg=colour51

# ============================================================
# Pane 레이아웃 정렬
# ============================================================
bind = select-layout even-horizontal
```

- [ ] **Step 2: 커밋**

```bash
git add dot_tmux.conf.tmpl
git commit -m "feat(chezmoi): .tmux.conf 템플릿 (macOS 한글IME / Linux 표준 prefix 분기)"
```

---

## Task 5: .zshrc 템플릿 생성 (OS 분기)

**Files:**
- Create: `dot_zshrc.tmpl`

- [ ] **Step 1: `dot_zshrc.tmpl` 생성**

```
# Path to your Oh My Zsh installation.
export ZSH="$HOME/.oh-my-zsh"

# Starship을 사용하므로 Oh My Zsh 테마 비활성화
ZSH_THEME=""

plugins=(git)

source $ZSH/oh-my-zsh.sh

{{ if eq .chezmoi.os "darwin" -}}
# ============================================================
# Homebrew
# ============================================================
if [ -f /opt/homebrew/bin/brew ]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
elif [ -f /usr/local/bin/brew ]; then
    eval "$(/usr/local/bin/brew shellenv)"
fi

# ============================================================
# Java
# ============================================================
if [ -d "/opt/homebrew/opt/openjdk@17" ]; then
    export PATH="/opt/homebrew/opt/openjdk@17/bin:$PATH"
    export JAVA_HOME="/opt/homebrew/opt/openjdk@17"
fi

# ============================================================
# Bun
# ============================================================
[ -s "$HOME/.bun/_bun" ] && source "$HOME/.bun/_bun"
export BUN_INSTALL="$HOME/.bun"
export PATH="$BUN_INSTALL/bin:$PATH"

# ============================================================
# Android Studio
# ============================================================
if [ -d "$HOME/Library/Android/sdk" ]; then
    export ANDROID_HOME="$HOME/Library/Android/sdk"
    export PATH="$PATH:$ANDROID_HOME/emulator"
    export PATH="$PATH:$ANDROID_HOME/platform-tools"
fi

{{ end -}}
# ============================================================
# PATH 추가
# ============================================================
export PATH="$HOME/.local/bin:$PATH"
export PATH="$PATH:$HOME/.pub-cache/bin"
export PATH="$PATH:$HOME/.maestro/bin"

# ============================================================
# Aliases
# ============================================================
alias ll='ls -lah'
alias dotfiles='cd ~/code/dotfiles'

# ============================================================
# Starship prompt (마지막에 로드)
# ============================================================
eval "$(starship init zsh)"
```

> **참고**: `.zshrc` 템플릿에서 Homebrew 경로도 Apple Silicon / Intel 분기를 추가했다.

- [ ] **Step 2: 커밋**

```bash
git add dot_zshrc.tmpl
git commit -m "feat(chezmoi): .zshrc 템플릿 (macOS Homebrew/Java/Bun/Android 분기)"
```

---

## Task 6: Claude Code + Brewfile 변환

**Files:**
- Create: `dot_claude/settings.json`
- Create: `dot_Brewfile`

- [ ] **Step 1: `dot_claude/settings.json` 생성 (superpowers 추가)**

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  },
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    }
  },
  "permissions": {
    "allow": [
      "WebSearch",
      "WebFetch(domain:*)"
    ],
    "defaultMode": "auto"
  },
  "enabledPlugins": {
    "superpowers@claude-plugins-official": true,
    "frontend-design@claude-plugins-official": true,
    "code-review@claude-plugins-official": true,
    "code-simplifier@claude-plugins-official": true,
    "pr-review-toolkit@claude-plugins-official": true,
    "figma@claude-plugins-official": true
  },
  "language": "Korean",
  "alwaysThinkingEnabled": true,
  "effortLevel": "high",
  "skipAutoPermissionPrompt": true
}
```

- [ ] **Step 2: `dot_Brewfile` 생성 (neovim, lazygit, fd 추가)**

```ruby
# Taps
tap "laishulu/homebrew"

# CLI Tools
brew "awscli"
brew "fd"
brew "gh"
brew "git"
brew "git-lfs"
brew "lazygit"
brew "neovim"
brew "node"
brew "pnpm"
brew "pipx"
brew "python@3.12"
brew "ripgrep"
brew "starship"
brew "tmux"
brew "tree"
brew "laishulu/homebrew/macism"

# Languages & Runtimes
brew "cocoapods"
brew "gemini-cli"
brew "openjdk@17"

# Data
brew "redis", restart_service: :changed

# Casks
cask "claude-code"
cask "copilot-cli"
cask "ghostty"
cask "reactotron"
```

> **변경점**: `stow` 제거, `neovim`, `lazygit`, `fd` 추가. 알파벳순 정렬.

- [ ] **Step 3: 커밋**

```bash
git add dot_claude/ dot_Brewfile
git commit -m "feat(chezmoi): Claude Code 설정 (superpowers 추가) + Brewfile (neovim, lazygit, fd)"
```

---

## Task 7: lazygit 설정

**Files:**
- Create: `dot_config/lazygit/config.yml`

- [ ] **Step 1: `dot_config/lazygit/config.yml` 생성**

```yaml
gui:
  showIcons: true
  nerdFontsVersion: "3"
  theme:
    lightTheme: false
git:
  paging:
    pager: "delta --dark --paging=never"
os:
  editPreset: "nvim"
```

> **참고**: `editPreset: "nvim"`으로 lazygit 내 편집 시 neovim을 사용한다. `delta`가 설치되어 있지 않으면 pager 설정은 무시되고 기본 pager가 사용된다.

- [ ] **Step 2: 커밋**

```bash
git add dot_config/lazygit/
git commit -m "feat(chezmoi): lazygit 설정 (neovim 연동, nerd font 아이콘)"
```

---

## Task 8: Neovim 코어 설정 (lazy.nvim + options + keymaps)

**Files:**
- Create: `dot_config/nvim/init.lua`
- Create: `dot_config/nvim/lua/config/lazy.lua`
- Create: `dot_config/nvim/lua/config/options.lua`
- Create: `dot_config/nvim/lua/config/keymaps.lua`

- [ ] **Step 1: `dot_config/nvim/init.lua` 생성**

```lua
require("config.options")
require("config.lazy")
require("config.keymaps")
```

- [ ] **Step 2: `dot_config/nvim/lua/config/options.lua` 생성**

```lua
local opt = vim.opt

opt.number = true
opt.relativenumber = true
opt.tabstop = 2
opt.shiftwidth = 2
opt.expandtab = true
opt.smartindent = true
opt.wrap = false
opt.cursorline = true
opt.signcolumn = "yes"
opt.clipboard = "unnamedplus"
opt.ignorecase = true
opt.smartcase = true
opt.termguicolors = true
opt.splitbelow = true
opt.splitright = true
opt.undofile = true
opt.updatetime = 250
opt.timeoutlen = 300

vim.g.mapleader = " "
vim.g.maplocalleader = " "
```

- [ ] **Step 3: `dot_config/nvim/lua/config/lazy.lua` 생성**

```lua
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.loop.fs_stat(lazypath) then
  vim.fn.system({
    "git", "clone", "--filter=blob:none",
    "https://github.com/folke/lazy.nvim.git",
    "--branch=stable", lazypath,
  })
end
vim.opt.rtp:prepend(lazypath)

require("lazy").setup("plugins", {
  change_detection = { notify = false },
})
```

- [ ] **Step 4: `dot_config/nvim/lua/config/keymaps.lua` 생성**

```lua
local map = vim.keymap.set

-- 창 이동
map("n", "<C-h>", "<C-w>h", { desc = "왼쪽 창으로" })
map("n", "<C-j>", "<C-w>j", { desc = "아래 창으로" })
map("n", "<C-k>", "<C-w>k", { desc = "위 창으로" })
map("n", "<C-l>", "<C-w>l", { desc = "오른쪽 창으로" })

-- 버퍼
map("n", "<S-h>", "<cmd>bprevious<cr>", { desc = "이전 버퍼" })
map("n", "<S-l>", "<cmd>bnext<cr>", { desc = "다음 버퍼" })

-- ESC로 검색 하이라이트 제거
map("n", "<Esc>", "<cmd>nohlsearch<cr>", { desc = "검색 하이라이트 제거" })

-- 비주얼 모드에서 들여쓰기 유지
map("v", "<", "<gv")
map("v", ">", ">gv")
```

- [ ] **Step 5: 커밋**

```bash
git add dot_config/nvim/
git commit -m "feat(nvim): 코어 설정 (lazy.nvim, options, keymaps)"
```

---

## Task 9: Neovim 플러그인 — 테마 + treesitter

**Files:**
- Create: `dot_config/nvim/lua/plugins/theme.lua`
- Create: `dot_config/nvim/lua/plugins/treesitter.lua`

- [ ] **Step 1: `dot_config/nvim/lua/plugins/theme.lua` 생성**

```lua
return {
  {
    "catppuccin/nvim",
    name = "catppuccin",
    lazy = false,
    priority = 1000,
    config = function()
      require("catppuccin").setup({
        flavour = "mocha",
      })
      vim.cmd.colorscheme("catppuccin")
    end,
  },
}
```

- [ ] **Step 2: `dot_config/nvim/lua/plugins/treesitter.lua` 생성**

```lua
return {
  {
    "nvim-treesitter/nvim-treesitter",
    build = ":TSUpdate",
    event = { "BufReadPost", "BufNewFile" },
    config = function()
      require("nvim-treesitter.configs").setup({
        ensure_installed = {
          "tsx", "typescript", "javascript", "json", "json5",
          "html", "css", "lua", "bash", "markdown", "markdown_inline",
          "yaml", "toml", "gitcommit", "diff",
        },
        highlight = { enable = true },
        indent = { enable = true },
      })
    end,
  },
}
```

- [ ] **Step 3: 커밋**

```bash
git add dot_config/nvim/lua/plugins/theme.lua dot_config/nvim/lua/plugins/treesitter.lua
git commit -m "feat(nvim): 테마 (catppuccin mocha) + treesitter"
```

---

## Task 10: Neovim 플러그인 — telescope

**Files:**
- Create: `dot_config/nvim/lua/plugins/telescope.lua`

- [ ] **Step 1: `dot_config/nvim/lua/plugins/telescope.lua` 생성**

```lua
return {
  {
    "nvim-telescope/telescope.nvim",
    branch = "0.1.x",
    dependencies = {
      "nvim-lua/plenary.nvim",
      { "nvim-telescope/telescope-fzf-native.nvim", build = "make" },
    },
    keys = {
      { "<leader>ff", "<cmd>Telescope find_files<cr>", desc = "파일 검색" },
      { "<leader>fg", "<cmd>Telescope live_grep<cr>", desc = "텍스트 검색" },
      { "<leader>fb", "<cmd>Telescope buffers<cr>", desc = "버퍼 목록" },
      { "<leader>fh", "<cmd>Telescope help_tags<cr>", desc = "도움말 검색" },
      { "<leader>fr", "<cmd>Telescope oldfiles<cr>", desc = "최근 파일" },
    },
    config = function()
      local telescope = require("telescope")
      telescope.setup({
        defaults = {
          file_ignore_patterns = { "node_modules", ".git/", "dist/" },
        },
      })
      telescope.load_extension("fzf")
    end,
  },
}
```

- [ ] **Step 2: 커밋**

```bash
git add dot_config/nvim/lua/plugins/telescope.lua
git commit -m "feat(nvim): telescope fuzzy finder"
```

---

## Task 11: Neovim 플러그인 — LSP + mason

**Files:**
- Create: `dot_config/nvim/lua/plugins/lsp.lua`

- [ ] **Step 1: `dot_config/nvim/lua/plugins/lsp.lua` 생성**

```lua
return {
  {
    "neovim/nvim-lspconfig",
    event = { "BufReadPre", "BufNewFile" },
    dependencies = {
      "williamboman/mason.nvim",
      "williamboman/mason-lspconfig.nvim",
    },
    config = function()
      require("mason").setup()
      require("mason-lspconfig").setup({
        ensure_installed = {
          "ts_ls",
          "tailwindcss",
          "eslint",
          "lua_ls",
          "jsonls",
        },
      })

      local lspconfig = require("lspconfig")
      local capabilities = require("cmp_nvim_lsp").default_capabilities()

      local on_attach = function(_, bufnr)
        local map = function(keys, func, desc)
          vim.keymap.set("n", keys, func, { buffer = bufnr, desc = desc })
        end
        map("gd", vim.lsp.buf.definition, "정의로 이동")
        map("gr", vim.lsp.buf.references, "참조 목록")
        map("K", vim.lsp.buf.hover, "호버 정보")
        map("<leader>ca", vim.lsp.buf.code_action, "코드 액션")
        map("<leader>rn", vim.lsp.buf.rename, "이름 변경")
      end

      local servers = { "ts_ls", "tailwindcss", "eslint", "jsonls" }
      for _, server in ipairs(servers) do
        lspconfig[server].setup({
          capabilities = capabilities,
          on_attach = on_attach,
        })
      end

      lspconfig.lua_ls.setup({
        capabilities = capabilities,
        on_attach = on_attach,
        settings = {
          Lua = {
            diagnostics = { globals = { "vim" } },
          },
        },
      })
    end,
  },
}
```

- [ ] **Step 2: 커밋**

```bash
git add dot_config/nvim/lua/plugins/lsp.lua
git commit -m "feat(nvim): LSP + mason (ts_ls, tailwindcss, eslint, lua_ls, jsonls)"
```

---

## Task 12: Neovim 플러그인 — 자동완성 (nvim-cmp)

**Files:**
- Create: `dot_config/nvim/lua/plugins/cmp.lua`

- [ ] **Step 1: `dot_config/nvim/lua/plugins/cmp.lua` 생성**

```lua
return {
  {
    "hrsh7th/nvim-cmp",
    event = "InsertEnter",
    dependencies = {
      "hrsh7th/cmp-nvim-lsp",
      "hrsh7th/cmp-buffer",
      "hrsh7th/cmp-path",
      "L3MON4D3/LuaSnip",
      "saadparwaiz1/cmp_luasnip",
    },
    config = function()
      local cmp = require("cmp")
      local luasnip = require("luasnip")

      cmp.setup({
        snippet = {
          expand = function(args)
            luasnip.lsp_expand(args.body)
          end,
        },
        mapping = cmp.mapping.preset.insert({
          ["<C-n>"] = cmp.mapping.select_next_item(),
          ["<C-p>"] = cmp.mapping.select_prev_item(),
          ["<C-d>"] = cmp.mapping.scroll_docs(-4),
          ["<C-f>"] = cmp.mapping.scroll_docs(4),
          ["<C-Space>"] = cmp.mapping.complete(),
          ["<CR>"] = cmp.mapping.confirm({ select = true }),
          ["<Tab>"] = cmp.mapping(function(fallback)
            if cmp.visible() then
              cmp.select_next_item()
            elseif luasnip.expand_or_jumpable() then
              luasnip.expand_or_jump()
            else
              fallback()
            end
          end, { "i", "s" }),
        }),
        sources = cmp.config.sources({
          { name = "nvim_lsp" },
          { name = "luasnip" },
        }, {
          { name = "buffer" },
          { name = "path" },
        }),
      })
    end,
  },
}
```

- [ ] **Step 2: 커밋**

```bash
git add dot_config/nvim/lua/plugins/cmp.lua
git commit -m "feat(nvim): nvim-cmp 자동완성 (LSP, buffer, path, luasnip)"
```

---

## Task 13: Neovim 플러그인 — conform (포매팅)

**Files:**
- Create: `dot_config/nvim/lua/plugins/conform.lua`

- [ ] **Step 1: `dot_config/nvim/lua/plugins/conform.lua` 생성**

```lua
return {
  {
    "stevearc/conform.nvim",
    event = { "BufWritePre" },
    keys = {
      { "<leader>cf", function() require("conform").format({ async = true }) end, desc = "포맷" },
    },
    config = function()
      require("conform").setup({
        formatters_by_ft = {
          javascript = { "prettier" },
          typescript = { "prettier" },
          javascriptreact = { "prettier" },
          typescriptreact = { "prettier" },
          css = { "prettier" },
          html = { "prettier" },
          json = { "prettier" },
          yaml = { "prettier" },
          markdown = { "prettier" },
          lua = { "stylua" },
        },
        format_on_save = {
          timeout_ms = 3000,
          lsp_format = "fallback",
        },
      })
    end,
  },
}
```

- [ ] **Step 2: 커밋**

```bash
git add dot_config/nvim/lua/plugins/conform.lua
git commit -m "feat(nvim): conform 포매팅 (prettier, stylua, format-on-save)"
```

---

## Task 14: Neovim 플러그인 — neo-tree + git + editor

**Files:**
- Create: `dot_config/nvim/lua/plugins/neo-tree.lua`
- Create: `dot_config/nvim/lua/plugins/git.lua`
- Create: `dot_config/nvim/lua/plugins/editor.lua`

- [ ] **Step 1: `dot_config/nvim/lua/plugins/neo-tree.lua` 생성**

```lua
return {
  {
    "nvim-neo-tree/neo-tree.nvim",
    branch = "v3.x",
    dependencies = {
      "nvim-lua/plenary.nvim",
      "nvim-tree/nvim-web-devicons",
      "MunifTanjim/nui.nvim",
    },
    keys = {
      { "<leader>e", "<cmd>Neotree toggle<cr>", desc = "파일 탐색기" },
    },
    config = function()
      require("neo-tree").setup({
        filesystem = {
          follow_current_file = { enabled = true },
          filtered_items = {
            hide_dotfiles = false,
            hide_gitignored = true,
          },
        },
      })
    end,
  },
}
```

- [ ] **Step 2: `dot_config/nvim/lua/plugins/git.lua` 생성**

```lua
return {
  {
    "lewis6991/gitsigns.nvim",
    event = { "BufReadPre", "BufNewFile" },
    config = function()
      require("gitsigns").setup({
        signs = {
          add = { text = "│" },
          change = { text = "│" },
          delete = { text = "_" },
          topdelete = { text = "‾" },
          changedelete = { text = "~" },
        },
        on_attach = function(bufnr)
          local gs = package.loaded.gitsigns
          local map = function(mode, l, r, desc)
            vim.keymap.set(mode, l, r, { buffer = bufnr, desc = desc })
          end
          map("n", "]h", gs.next_hunk, "다음 hunk")
          map("n", "[h", gs.prev_hunk, "이전 hunk")
          map("n", "<leader>hs", gs.stage_hunk, "hunk stage")
          map("n", "<leader>hr", gs.reset_hunk, "hunk reset")
          map("n", "<leader>hp", gs.preview_hunk, "hunk 미리보기")
        end,
      })
    end,
  },
  {
    "kdheepak/lazygit.nvim",
    dependencies = { "nvim-lua/plenary.nvim" },
    keys = {
      { "<leader>gg", "<cmd>LazyGit<cr>", desc = "LazyGit" },
    },
  },
}
```

- [ ] **Step 3: `dot_config/nvim/lua/plugins/editor.lua` 생성**

```lua
return {
  {
    "windwp/nvim-autopairs",
    event = "InsertEnter",
    config = true,
  },
  {
    "numToStr/Comment.nvim",
    keys = {
      { "gcc", mode = "n", desc = "주석 토글 (줄)" },
      { "gc", mode = "v", desc = "주석 토글 (선택)" },
    },
    config = true,
  },
  {
    "folke/which-key.nvim",
    event = "VeryLazy",
    config = function()
      require("which-key").setup()
    end,
  },
}
```

- [ ] **Step 4: 커밋**

```bash
git add dot_config/nvim/lua/plugins/neo-tree.lua dot_config/nvim/lua/plugins/git.lua dot_config/nvim/lua/plugins/editor.lua
git commit -m "feat(nvim): neo-tree, gitsigns, lazygit.nvim, autopairs, Comment, which-key"
```

---

## Task 15: bootstrap.sh 재작성

**Files:**
- Modify: `bootstrap.sh`

- [ ] **Step 1: `bootstrap.sh` 전체 교체**

```bash
#!/bin/bash
set -euo pipefail

DOTFILES_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== dotfiles bootstrap ==="
echo "Source: $DOTFILES_DIR"
echo ""

# 1. Xcode CLI Tools (macOS only)
if [[ "$(uname)" == "Darwin" ]]; then
    echo "[1/6] Xcode CLI Tools..."
    if ! xcode-select -p &>/dev/null; then
        xcode-select --install
        echo "  설치 완료 후 다시 실행하세요."
        exit 0
    else
        echo "  already installed"
    fi
fi

# 2. 패키지 매니저 + 기본 도구
if [[ "$(uname)" == "Darwin" ]]; then
    echo "[2/6] Homebrew..."
    if ! command -v brew &>/dev/null; then
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    # Apple Silicon / Intel 분기
    if [ -f /opt/homebrew/bin/brew ]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    elif [ -f /usr/local/bin/brew ]; then
        eval "$(/usr/local/bin/brew shellenv)"
    fi
else
    echo "[2/6] Linux 패키지..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get update
        sudo apt-get install -y git tmux neovim zsh ripgrep fd-find curl starship lazygit
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y git tmux neovim zsh ripgrep fd-find curl starship lazygit
    fi
fi

# 3. chezmoi 설치 + init (Stow 해제 전에 먼저 검증)
echo "[3/6] chezmoi..."
if ! command -v chezmoi &>/dev/null; then
    sh -c "$(curl -fsLS get.chezmoi.io)" -- -b "$HOME/.local/bin"
    export PATH="$HOME/.local/bin:$PATH"
fi
CHEZMOI="$(command -v chezmoi)"

echo "  chezmoi init..."
"$CHEZMOI" init --source "$DOTFILES_DIR"

echo "  chezmoi diff (변경 사항 미리보기)..."
"$CHEZMOI" diff || true
echo ""
read -rp "  적용하시겠습니까? (y/N) " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "  건너뜀. 'chezmoi apply'로 나중에 적용할 수 있습니다."
    exit 0
fi

# 4. 기존 Stow 환경 정리 (chezmoi 검증 통과 후 실행)
echo "[4/6] Stow 마이그레이션 정리..."
STOW_TARGETS=(.tmux.conf .zshrc .gitconfig .gitconfig-work .gitconfig-personal
              .gitignore_global .Brewfile .config/ghostty/config
              .config/starship.toml .claude/settings.json)
stow_found=false
for target in "${STOW_TARGETS[@]}"; do
    filepath="$HOME/$target"
    if [ -L "$filepath" ]; then
        echo "  unlink $filepath"
        unlink "$filepath"
        stow_found=true
    elif [ -f "$filepath" ]; then
        echo "  backup & remove $filepath → ${filepath}.bak"
        mv "$filepath" "${filepath}.bak"
        stow_found=true
    fi
done
if command -v stow &>/dev/null && [ -f "$DOTFILES_DIR/.stow-local-ignore" ]; then
    echo "  stow -D (기존 패키지 해제)..."
    cd "$DOTFILES_DIR"
    for pkg in tmux zsh git git-work git-personal ghostty claude brew starship; do
        [ -d "$pkg" ] && stow --target="$HOME" -D "$pkg" 2>/dev/null || true
    done
fi
if [ "$stow_found" = false ]; then
    echo "  기존 Stow 환경 없음 (skip)"
fi

# 5. chezmoi apply
echo "[5/6] chezmoi apply..."
"$CHEZMOI" apply

# 6. Brew bundle (macOS only)
if [[ "$(uname)" == "Darwin" ]] && [ -f "$HOME/.Brewfile" ]; then
    echo "[6/6] Brew bundle..."
    brew bundle --global --no-lock
else
    echo "[6/6] Brew bundle... skipped (not macOS)"
fi

echo ""
echo "✅ dotfiles 설치 완료!"
```

- [ ] **Step 2: 커밋**

```bash
git add bootstrap.sh
git commit -m "feat(chezmoi): bootstrap.sh 재작성 (chezmoi 기반, stow 마이그레이션 포함)"
```

---

## Task 16: .gitignore 업데이트

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: `.gitignore` 교체**

```
# Secrets
.env
.env.*
*.key
*.pem
*.p12
*.pfx
*credentials*
*secret*
id_rsa*
id_ed25519*

# Local settings (chezmoi source 방어)
dot_claude/settings.local.json

# macOS
.DS_Store
```

> **변경점**: stow 경로 `claude/.claude/settings.local.json` → chezmoi source 경로 `dot_claude/settings.local.json`

- [ ] **Step 2: 커밋**

```bash
git add .gitignore
git commit -m "chore: .gitignore 업데이트 (stow → chezmoi 경로)"
```

---

## Task 17: README.md 재작성

**Files:**
- Modify: `README.md`

- [ ] **Step 1: `README.md` 교체**

```markdown
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
```

- [ ] **Step 2: 커밋**

```bash
git add README.md
git commit -m "docs: README 재작성 (chezmoi 기반)"
```

---

## Task 18: chezmoi apply 로컬 검증

**Files:** 없음 (검증만)

- [ ] **Step 1: chezmoi 설치 (아직 없다면)**

```bash
brew install chezmoi
```

- [ ] **Step 2: chezmoi init 실행**

```bash
chezmoi init --source ~/code/dotfiles
```

Expected: `machine_type` 프롬프트가 뜨면 `work-mac` 선택

- [ ] **Step 3: chezmoi diff 확인**

```bash
chezmoi diff
```

Expected: 변경될 파일 목록이 표시됨. 기존 파일과의 차이를 확인

- [ ] **Step 4: chezmoi apply 실행**

```bash
chezmoi apply
```

Expected: 모든 설정 파일이 `$HOME`에 배치됨

- [ ] **Step 5: 검증**

```bash
# symlink가 아닌 일반 파일로 배치되었는지 확인
ls -la ~/.tmux.conf ~/.zshrc ~/.gitconfig ~/.Brewfile
ls -la ~/.config/ghostty/config ~/.config/starship.toml
ls -la ~/.config/nvim/init.lua ~/.config/lazygit/config.yml
ls -la ~/.claude/settings.json

# git 설정 확인
git config user.name
git config init.defaultBranch

# neovim 실행 (플러그인 자동 설치 확인)
nvim --headless "+Lazy! sync" +qa
```

- [ ] **Step 6: 커밋 (검증 결과 수정사항 있으면)**

```bash
git add -A
git commit -m "fix(chezmoi): 검증 후 수정사항 반영"
```

---

## Task 19: stow 잔재 정리 (안정화 후)

> **주의**: 이 태스크는 Task 18 검증을 통과하고, 실제 사용에서 문제가 없음을 확인한 후에만 진행한다.

**Files:**
- Delete: `tmux/`, `zsh/`, `git/`, `git-work/`, `git-personal/`, `ghostty/`, `claude/`, `brew/`, `starship/`
- Delete: `.stow-local-ignore`

- [ ] **Step 1: stow 패키지 디렉토리 삭제**

```bash
rm -rf tmux/ zsh/ git/ git-work/ git-personal/ ghostty/ claude/ brew/ starship/
rm -f .stow-local-ignore
```

- [ ] **Step 2: `.chezmoiignore`에서 stow 잔재 규칙 제거**

`.chezmoiignore`에서 아래 라인들을 삭제한다:

```
# stow 잔재 (마이그레이션 기간 동안 chezmoi가 무시)
tmux/**
zsh/**
git/**
git-work/**
git-personal/**
ghostty/**
claude/**
brew/**
starship/**
.stow-local-ignore
```

- [ ] **Step 3: 커밋**

```bash
git add -A
git commit -m "chore: stow 패키지 디렉토리 및 잔재 정리"
```
