return {
  {
    "goolord/alpha-nvim",
    event = "VimEnter",
    dependencies = { "nvim-tree/nvim-web-devicons" },
    config = function()
      local alpha = require("alpha")
      local dashboard = require("alpha.themes.dashboard")

      local header = {
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡰⡪⠢⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢨⢪⢊⢐⠸⢐⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡪⡲⣐⢐⠈⡐⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠝⡨⠠⢑⠔⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢐⠡⠀⠄⢕⢱⠠⠣⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡎⣜⢨⠠⡁⠎⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡜⣜⢮⢢⢃⠆⠕⢅⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡐⡕⡕⡇⡧⡱⣘⢌⢜⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡰⡘⢎⠣⢋⠪⠨⠂⠅⠅⡑⢅⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠔⠢⡣⣣⢪⡲⡌⡆⠔⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠄⡃⠅⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡀⣂⢢⠀⠀⠀⠀⠀⡀⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡄⡀⣢⡺⣮⣳⡣⡂⡀⡠⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⣕⢗⣽⣳⡳⣕⡳⡐⢜⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⣗⢽⡺⡮⡏⢮⢪⠪⠪⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⡎⡎⡎⢎⠣⠃⢅⠅⠅⢕⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢐⢕⢕⢪⢂⠡⠑⠐⠈⠄⡱⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⢱⢱⢱⢱⢑⢅⠊⠄⠅⡒⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡎⡎⣎⢧⢣⢣⠪⡘⢌⢂⢊⢆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⢱⢱⢕⢧⢳⢱⢱⢡⠱⡐⢅⢪⢂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⢣⢳⢹⡪⡳⣝⢜⢜⢔⠱⡨⡂⢕⢕⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⢣⢣⢳⠵⣝⢝⡜⣜⢜⢔⢕⢱⠨⡢⢣⢪⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⢔⢕⢕⡕⡗⣝⣮⣷⣿⡿⣟⣷⣧⣕⠕⡜⡸⡘⡬⡂⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀",
        "⠀⠀⠀⠀⠀⠀⠀⢀⢰⢸⢸⡸⡱⡱⣽⣾⣿⣯⣷⣿⣿⣟⣷⡿⣷⡱⡘⡌⡎⡎⡆⣂⠀⠀⠀⠀⠀⠀⠀⠀",
      }

      -- MacGraw color map:
      --   MacGrawComb   = red comb / hat
      --   MacGrawBody   = Matrix green body
      --   MacGrawBeak   = orange beak
      --   MacGrawShades = dark gray eyes / brow
      vim.api.nvim_set_hl(0, "MacGrawComb", { fg = "#c44a3d" })
      vim.api.nvim_set_hl(0, "MacGrawBody", { fg = "#00ff41" })
      vim.api.nvim_set_hl(0, "MacGrawBeak", { fg = "#e5892d" })
      vim.api.nvim_set_hl(0, "MacGrawShades", { fg = "#30343a" })

      -- Orange beak ranges: [line] = { start_char, end_char }
      local beak_ranges = {
        [14] = { 19, 21 },
        [15] = { 18, 22 },
        [16] = { 17, 23 },
        [17] = { 16, 24 },
        [18] = { 16, 24 },
        [19] = { 17, 23 },
        [20] = { 18, 22 },
        [21] = { 19, 21 },
      }

      -- Dark gray eye / brow ranges. Multiple ranges can be used on one line.
      local shade_ranges = {
        [11] = { { 19, 22 } },
        [12] = { { 19, 21 }, { 27, 28 } },
        [13] = { { 16, 25 } },
        [14] = { { 16, 18 }, { 22, 25 } },
        [15] = { { 16, 17 }, { 23, 26 } },
      }

      local function byteidx(line, char_index)
        return vim.fn.byteidx(line, char_index)
      end

      local function header_hl()
        local highlights = {}

        for line_number, line in ipairs(header) do
          if line_number <= 10 then
            highlights[line_number] = { { "MacGrawComb", 0, -1 } }
          else
            local line_highlights = { { "MacGrawBody", 0, -1 } }

            for _, range in ipairs(shade_ranges[line_number] or {}) do
              local start_col, end_col = unpack(range)
              table.insert(line_highlights, {
                "MacGrawShades",
                byteidx(line, start_col - 1),
                byteidx(line, end_col),
              })
            end

            if beak_ranges[line_number] then
              local start_col, end_col = unpack(beak_ranges[line_number])
              table.insert(line_highlights, {
                "MacGrawBeak",
                byteidx(line, start_col - 1),
                byteidx(line, end_col),
              })
            end

            highlights[line_number] = line_highlights
          end
        end

        return highlights
      end

      dashboard.section.header.val = header
      dashboard.section.header.opts.hl = header_hl()

      dashboard.section.buttons.val = {
        dashboard.button("l", "  LazyGit", "<leader>gg"),
        dashboard.button("d", "  Database", "<leader>db"),
        dashboard.button("f", "  파일 검색", "<cmd>Telescope find_files<cr>"),
        dashboard.button("r", "  최근 파일", "<cmd>Telescope oldfiles<cr>"),
        dashboard.button("g", "  텍스트 검색", "<cmd>Telescope live_grep<cr>"),
        dashboard.button("p", "  프로젝트 파일 검색", "<leader>fp"),
        dashboard.button("P", "  프로젝트 텍스트 검색", "<leader>fP"),
        dashboard.button("e", "  파일 탐색기", "<cmd>Neotree toggle<cr>"),
        dashboard.button("q", "  종료", "<cmd>qa<cr>"),
      }

      dashboard.section.footer.val = "MacGraw 🐧"

      alpha.setup(dashboard.config)
    end,
  },
}
