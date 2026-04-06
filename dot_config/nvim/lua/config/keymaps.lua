local map = vim.keymap.set

-- 창 이동: vim-tmux-navigator 플러그인이 <C-h/j/k/l> 담당

-- 창 분할/닫기
map("n", "<leader>sv", "<cmd>vsplit<cr>", { desc = "수직 분할" })
map("n", "<leader>sh", "<cmd>split<cr>", { desc = "수평 분할" })
map("n", "<leader>sx", "<cmd>close<cr>", { desc = "현재 창 닫기" })
map("n", "<leader>se", "<C-w>=", { desc = "창 크기 균등화" })

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
