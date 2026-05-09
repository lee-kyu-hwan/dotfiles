local opt = vim.opt

opt.number = true
opt.relativenumber = true
opt.tabstop = 2
opt.shiftwidth = 2
opt.expandtab = true
opt.smartindent = true
opt.wrap = false
opt.cursorline = true
opt.signcolumn = "yes"
opt.clipboard = "unnamedplus"
opt.ignorecase = true
opt.smartcase = true
opt.termguicolors = true
opt.splitbelow = true
opt.splitright = true
opt.undofile = true
opt.updatetime = 250
opt.timeoutlen = 500

-- 외부에서 변경된 파일 자동 reload
opt.autoread = true

vim.api.nvim_create_autocmd({ "FocusGained", "BufEnter", "CursorHold", "CursorHoldI" }, {
  pattern = "*",
  callback = function()
    if vim.fn.mode() ~= "c" and vim.fn.getcmdwintype() == "" then
      vim.cmd("checktime")
    end
  end,
})

vim.api.nvim_create_autocmd("FileChangedShellPost", {
  pattern = "*",
  callback = function()
    vim.notify("파일이 외부에서 변경되어 reload됨", vim.log.levels.INFO)
  end,
})

vim.g.mapleader = " "
vim.g.maplocalleader = " "
