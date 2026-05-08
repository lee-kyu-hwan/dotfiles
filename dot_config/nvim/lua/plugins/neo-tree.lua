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
        window = {
          mappings = {
            ["z"] = "close_all_nodes",
            ["Z"] = "expand_all_nodes",
            ["y"] = function(state)
              local node = state.tree:get_node()
              local name = node.name
              vim.fn.setreg("+", name)
              vim.notify("Copied: " .. name)
            end,
            ["Y"] = function(state)
              local node = state.tree:get_node()
              local path = vim.fn.fnamemodify(node:get_id(), ":.")
              vim.fn.setreg("+", path)
              vim.notify("Copied: " .. path)
            end,
            ["gy"] = function(state)
              local node = state.tree:get_node()
              local path = node:get_id()
              vim.fn.setreg("+", path)
              vim.notify("Copied: " .. path)
            end,
          },
        },
        filesystem = {
          follow_current_file = { enabled = true },
          filtered_items = {
            hide_dotfiles = false,
            hide_gitignored = false,
          },
        },
      })
    end,
  },
}
