-- vtsls: VSCode TypeScript 확장 래퍼 (ts_ls 대체)
-- Turborepo 모노레포 환경에서 앱별 tsconfig.json 기준으로 루트 감지

local function is_deno_project(path)
  return vim.fs.root(path, { "deno.json", "deno.jsonc", "deno.lock" }) ~= nil
end

return {
  cmd = { "vtsls", "--stdio" },
  filetypes = {
    "javascript",
    "javascriptreact",
    "javascript.jsx",
    "typescript",
    "typescriptreact",
    "typescript.tsx",
  },
  root_markers = { "tsconfig.json", "jsconfig.json", "package.json" },
  root_dir = function(bufnr, on_dir)
    local bufname = vim.api.nvim_buf_get_name(bufnr)
    if is_deno_project(bufname) then
      return -- Deno 프로젝트면 vtsls 비활성화
    end

    -- tsconfig.json 기준 루트 (모노레포에서 앱별 분리)
    local root = vim.fs.root(bufnr, { "tsconfig.json", "jsconfig.json" })
    if root then
      on_dir(root)
      return
    end

    -- 폴백: package.json 또는 .git
    root = vim.fs.root(bufnr, { "package.json", ".git" })
    if root then
      on_dir(root)
    end
  end,
  settings = {
    vtsls = {
      autoUseWorkspaceTsdk = true,
      experimental = {
        maxInlayHintLength = 30,
        completion = {
          enableServerSideFuzzyMatch = true,
        },
      },
    },
    typescript = {
      updateImportsOnFileMove = { enabled = "always" },
      suggest = { completeFunctionCalls = true },
      inlayHints = {
        enumMemberValues = { enabled = true },
        functionLikeReturnTypes = { enabled = true },
        parameterNames = { enabled = "literals" },
        parameterTypes = { enabled = true },
        propertyDeclarationTypes = { enabled = true },
        variableTypes = { enabled = false },
      },
    },
    javascript = {
      updateImportsOnFileMove = { enabled = "always" },
      suggest = { completeFunctionCalls = true },
      inlayHints = {
        enumMemberValues = { enabled = true },
        functionLikeReturnTypes = { enabled = true },
        parameterNames = { enabled = "literals" },
        parameterTypes = { enabled = true },
        propertyDeclarationTypes = { enabled = true },
        variableTypes = { enabled = false },
      },
    },
  },
}
