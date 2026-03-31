return {
  {
    "nvim-telescope/telescope.nvim",
    branch = "master",
    dependencies = {
      "nvim-lua/plenary.nvim",
      { "nvim-telescope/telescope-fzf-native.nvim", build = "make" },
    },
    cmd = { "Telescope" },
    keys = {
      { "<leader>ff", "<cmd>Telescope find_files<cr>", desc = "파일 검색" },
      { "<leader>fg", "<cmd>Telescope live_grep<cr>", desc = "텍스트 검색" },
      { "<leader>fb", "<cmd>Telescope buffers<cr>", desc = "버퍼 목록" },
      { "<leader>fh", "<cmd>Telescope help_tags<cr>", desc = "도움말 검색" },
      { "<leader>fr", "<cmd>Telescope oldfiles<cr>", desc = "최근 파일" },
      {
        "<leader>fp",
        function()
          -- 모노레포 프로젝트 디렉토리 선택 후 파일 검색
          local root = vim.fs.root(0, { "pnpm-workspace.yaml", ".git" }) or vim.uv.cwd()
          require("telescope.builtin").find_files({
            prompt_title = "프로젝트 선택",
            cwd = root,
            find_command = { "fd", "--type", "d", "--max-depth", "4", "--exclude", "node_modules", "--exclude", ".git", "--exclude", "dist", "--exclude", ".next" },
            attach_mappings = function(_, map)
              map("i", "<CR>", function(prompt_bufnr)
                local entry = require("telescope.actions.state").get_selected_entry(prompt_bufnr)
                require("telescope.actions").close(prompt_bufnr)
                require("telescope.builtin").find_files({
                  prompt_title = entry.value .. " 파일 검색",
                  cwd = root .. "/" .. entry.value,
                })
              end)
              return true
            end,
          })
        end,
        desc = "프로젝트 디렉토리 → 파일 검색",
      },
      {
        "<leader>fP",
        function()
          -- 모노레포 프로젝트 디렉토리 선택 후 텍스트 검색
          local root = vim.fs.root(0, { "pnpm-workspace.yaml", ".git" }) or vim.uv.cwd()
          require("telescope.builtin").find_files({
            prompt_title = "프로젝트 선택 (텍스트 검색)",
            cwd = root,
            find_command = { "fd", "--type", "d", "--max-depth", "4", "--exclude", "node_modules", "--exclude", ".git", "--exclude", "dist", "--exclude", ".next" },
            attach_mappings = function(_, map)
              map("i", "<CR>", function(prompt_bufnr)
                local entry = require("telescope.actions.state").get_selected_entry(prompt_bufnr)
                require("telescope.actions").close(prompt_bufnr)
                require("telescope.builtin").live_grep({
                  prompt_title = entry.value .. " 텍스트 검색",
                  cwd = root .. "/" .. entry.value,
                })
              end)
              return true
            end,
          })
        end,
        desc = "프로젝트 디렉토리 → 텍스트 검색",
      },
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
