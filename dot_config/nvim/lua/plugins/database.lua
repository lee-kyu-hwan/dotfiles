return {
  {
    "kristijanhusak/vim-dadbod-ui",
    dependencies = {
      { "tpope/vim-dadbod", lazy = true },
    },
    cmd = { "DBUI", "DBUIToggle", "DBUIAddConnection", "DBUIFindBuffer" },
    keys = {
      { "<leader>db", "<cmd>DBUIToggle<cr>", desc = "DB UI 토글" },
    },
    init = function()
      vim.g.db_ui_use_nerd_fonts = 1
      local mysql_bin = "/opt/homebrew/opt/mysql-client/bin"
      if vim.fn.isdirectory(mysql_bin) == 1 then
        vim.env.PATH = mysql_bin .. ":" .. vim.env.PATH
      end
    end,
  },
}
