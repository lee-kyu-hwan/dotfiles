return {
  -- Mason: LSP 서버 자동 설치
  {
    "mason-org/mason.nvim",
    opts = {},
  },

  -- Mason-lspconfig: 설치된 서버 자동 활성화 (automatic_enable)
  {
    "mason-org/mason-lspconfig.nvim",
    dependencies = {
      "mason-org/mason.nvim",
      "saghen/blink.cmp",
    },
    opts = {
      automatic_enable = true,
      ensure_installed = {
        "vtsls",
        "tailwindcss",
        "eslint",
        "lua_ls",
        "jsonls",
      },
    },
    config = function(_, opts)
      require("mason-lspconfig").setup(opts)

      -- 전체 서버 공통 capabilities (blink.cmp)
      vim.lsp.config("*", {
        capabilities = require("blink.cmp").get_lsp_capabilities(),
      })

      -- LspAttach: 버퍼별 키맵 + 기능 활성화
      vim.api.nvim_create_autocmd("LspAttach", {
        callback = function(args)
          local client = vim.lsp.get_client_by_id(args.data.client_id)
          if not client then return end

          local map = function(keys, func, desc)
            vim.keymap.set("n", keys, func, { buffer = args.buf, desc = desc })
          end

          -- gd: Telescope로 정의 이동 (import문 아닌 실제 소스)
          -- 나머지 빌트인: grr, gri, grt, gra, grn, grx, gO, K, gD
          map("gd", "<cmd>Telescope lsp_definitions<cr>", "정의로 이동")

          -- Inlay Hints 토글
          if client:supports_method("textDocument/inlayHint") then
            vim.lsp.inlay_hint.enable(true, { bufnr = args.buf })
            map("<leader>ih", function()
              vim.lsp.inlay_hint.enable(
                not vim.lsp.inlay_hint.is_enabled({ bufnr = args.buf }),
                { bufnr = args.buf }
              )
            end, "Inlay Hints 토글")
          end

          -- CodeLens 자동 갱신
          if client:supports_method("textDocument/codeLens") then
            vim.lsp.codelens.refresh()
            vim.api.nvim_create_autocmd({ "BufEnter", "InsertLeave" }, {
              buffer = args.buf,
              callback = function()
                vim.lsp.codelens.refresh({ bufnr = args.buf })
              end,
            })
          end
        end,
      })
    end,
  },
}
