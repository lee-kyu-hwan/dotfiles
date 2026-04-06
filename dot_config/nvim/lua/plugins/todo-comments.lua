return {
  {
    "folke/todo-comments.nvim",
    dependencies = { "nvim-lua/plenary.nvim" },
    event = { "BufReadPost", "BufNewFile" },
    keys = {
      { "]t", function() require("todo-comments").jump_next() end, desc = "다음 TODO" },
      { "[t", function() require("todo-comments").jump_prev() end, desc = "이전 TODO" },
      { "<leader>xt", "<cmd>Trouble todo toggle<cr>", desc = "TODO 목록 (Trouble)" },
      { "<leader>ft", "<cmd>TodoTelescope<cr>", desc = "TODO 검색" },
    },
    opts = {},
  },
}
