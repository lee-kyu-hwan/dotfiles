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
