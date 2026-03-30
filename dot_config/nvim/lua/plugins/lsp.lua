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
          -- gd만 Telescope로 오버라이드 (import문이 아닌 실제 소스 파일로 이동)
          -- 나머지는 Neovim 0.11 빌트인 사용: grr, gri, grt, gra, grn, gO, K, gD
          map("gd", "<cmd>Telescope lsp_definitions<cr>", "정의로 이동")
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
