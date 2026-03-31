local map = vim.keymap.set

-- 창 이동
map("n", "<C-h>", "<C-w>h", { desc = "왼쪽 창으로" })
map("n", "<C-j>", "<C-w>j", { desc = "아래 창으로" })
map("n", "<C-k>", "<C-w>k", { desc = "위 창으로" })
map("n", "<C-l>", "<C-w>l", { desc = "오른쪽 창으로" })

-- 버퍼
map("n", "<S-h>", "<cmd>bprevious<cr>", { desc = "이전 버퍼" })
map("n", "<S-l>", "<cmd>bnext<cr>", { desc = "다음 버퍼" })

-- ESC로 검색 하이라이트 제거
map("n", "<Esc>", "<cmd>nohlsearch<cr>", { desc = "검색 하이라이트 제거" })

-- 경로 복사
map("n", "<leader>yp", function() vim.fn.setreg("+", vim.fn.expand("%")) end, { desc = "상대 경로 복사" })
map("n", "<leader>yP", function() vim.fn.setreg("+", vim.fn.expand("%:p")) end, { desc = "절대 경로 복사" })
map("n", "<leader>yf", function() vim.fn.setreg("+", vim.fn.expand("%:t")) end, { desc = "파일명 복사" })
map("n", "<leader>yl", function() vim.fn.setreg("+", vim.fn.expand("%") .. ":" .. vim.fn.line(".")) end, { desc = "경로:라인번호 복사" })

-- 비주얼 모드에서 들여쓰기 유지
map("v", "<", "<gv")
map("v", ">", ">gv")
