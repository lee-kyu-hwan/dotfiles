return {
  {
    "nvim-treesitter/nvim-treesitter",
    build = ":TSUpdate",
    event = { "BufReadPost", "BufNewFile" },
    config = function()
      require("nvim-treesitter").setup({
        ensure_installed = {
          "tsx", "typescript", "javascript", "json", "json5",
          "html", "css", "lua", "bash", "markdown", "markdown_inline",
          "yaml", "toml", "gitcommit", "diff",
        },
      })
    end,
  },
  {
    "nvim-treesitter/nvim-treesitter-textobjects",
    branch = "main",
    dependencies = { "nvim-treesitter/nvim-treesitter" },
    event = { "BufReadPost", "BufNewFile" },
    config = function()
      require("nvim-treesitter-textobjects").setup({
        select = { lookahead = true },
        move = { set_jumps = true },
      })

      local select = require("nvim-treesitter-textobjects.select").select_textobject
      local swap = require("nvim-treesitter-textobjects.swap")
      local move = require("nvim-treesitter-textobjects.move")
      local map = vim.keymap.set

      -- 선택
      map({ "x", "o" }, "af", function() select("@function.outer", "textobjects") end, { desc = "함수 전체" })
      map({ "x", "o" }, "if", function() select("@function.inner", "textobjects") end, { desc = "함수 본문" })
      map({ "x", "o" }, "ac", function() select("@class.outer", "textobjects") end, { desc = "클래스 전체" })
      map({ "x", "o" }, "ic", function() select("@class.inner", "textobjects") end, { desc = "클래스 본문" })
      map({ "x", "o" }, "aa", function() select("@parameter.outer", "textobjects") end, { desc = "파라미터 전체" })
      map({ "x", "o" }, "ia", function() select("@parameter.inner", "textobjects") end, { desc = "파라미터 내부" })

      -- 교환
      map("n", "<leader>a", function() swap.swap_next("@parameter.inner") end, { desc = "다음 파라미터와 교환" })
      map("n", "<leader>A", function() swap.swap_previous("@parameter.inner") end, { desc = "이전 파라미터와 교환" })

      -- 이동
      map({ "n", "x", "o" }, "]m", function() move.goto_next_start("@function.outer", "textobjects") end, { desc = "다음 함수 시작" })
      map({ "n", "x", "o" }, "[m", function() move.goto_previous_start("@function.outer", "textobjects") end, { desc = "이전 함수 시작" })
      map({ "n", "x", "o" }, "]M", function() move.goto_next_end("@function.outer", "textobjects") end, { desc = "다음 함수 끝" })
      map({ "n", "x", "o" }, "[M", function() move.goto_previous_end("@function.outer", "textobjects") end, { desc = "이전 함수 끝" })
    end,
  },
  {
    "windwp/nvim-ts-autotag",
    event = "InsertEnter",
    opts = {},
  },
}
