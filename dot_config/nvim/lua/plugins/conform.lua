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
