return {
  {
    "lewis6991/gitsigns.nvim",
    event = { "BufReadPre", "BufNewFile" },
    config = function()
      require("gitsigns").setup({
        current_line_blame = true,
        current_line_blame_opts = { delay = 300 },
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
          map("n", "<leader>hb", gs.toggle_current_line_blame, "blame 토글")
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
