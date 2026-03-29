return {
  {
    "williamboman/mason.nvim",
    opts = {},
  },
  {
    "williamboman/mason-lspconfig.nvim",
    dependencies = { "williamboman/mason.nvim" },
    opts = {
      ensure_installed = {
        "ts_ls",
        "tailwindcss",
        "eslint",
        "lua_ls",
        "jsonls",
      },
    },
  },
  {
    "hrsh7th/cmp-nvim-lsp",
    config = function()
      vim.api.nvim_create_autocmd("LspAttach", {
        callback = function(args)
          local map = function(keys, func, desc)
            vim.keymap.set("n", keys, func, { buffer = args.buf, desc = desc })
          end
          map("gd", vim.lsp.buf.definition, "정의로 이동")
          map("gr", vim.lsp.buf.references, "참조 목록")
          map("K", vim.lsp.buf.hover, "호버 정보")
          map("<leader>ca", vim.lsp.buf.code_action, "코드 액션")
          map("<leader>rn", vim.lsp.buf.rename, "이름 변경")
        end,
      })

      vim.lsp.config("*", {
        capabilities = require("cmp_nvim_lsp").default_capabilities(),
      })

      vim.lsp.config("lua_ls", {
        settings = {
          Lua = {
            diagnostics = { globals = { "vim" } },
          },
        },
      })

      vim.lsp.enable({ "ts_ls", "tailwindcss", "eslint", "lua_ls", "jsonls" })
    end,
  },
}
