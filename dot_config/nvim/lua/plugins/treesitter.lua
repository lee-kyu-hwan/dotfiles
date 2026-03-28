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
