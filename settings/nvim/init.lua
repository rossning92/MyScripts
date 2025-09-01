-- A starting point for Neovim config: https://github.com/nvim-lua/kickstart.nvim/blob/master/init.lua

vim.wo.relativenumber = true
vim.wo.number = true
vim.g.mapleader = " "
vim.opt.shortmess:append("I")     -- Disable intro message
vim.opt.clipboard = "unnamedplus" -- Use system clipboard
vim.opt.termguicolors = true
vim.opt.mouse = ""                -- Disable mouse
vim.opt.messagesopt = "wait:1000,history:500"

-- Better up/down movement
vim.keymap.set('n', '<up>', "v:count == 0 ? 'gk' : 'k'", { expr = true, silent = true })
vim.keymap.set('n', '<down>', "v:count == 0 ? 'gj' : 'j'", { expr = true, silent = true })
vim.keymap.set('i', '<up>', '<C-o>gk', { silent = true })
vim.keymap.set('i', '<down>', '<C-o>gj', { silent = true })

vim.keymap.set('n', '<C-A>', 'ggVG', { noremap = true, silent = true })
vim.keymap.set('i', '<C-A>', '<Esc>ggVG', { noremap = true, silent = true })

-- Terminal settings
vim.api.nvim_command("autocmd TermOpen * startinsert")
vim.api.nvim_command("autocmd TermOpen * setlocal nonumber norelativenumber signcolumn=no")

-- auto-reload files when modified externally
-- https://unix.stackexchange.com/a/383044
vim.o.autoread = true
vim.api.nvim_create_autocmd({ "BufEnter", "CursorHold", "CursorHoldI", "FocusGained" }, {
  command = "if mode() != 'c' | checktime | endif",
  pattern = { "*" },
})
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"

if not (vim.uv or vim.loop).fs_stat(lazypath) then
  vim.fn.system({
    "git",
    "clone",
    "--filter=blob:none",
    "https://github.com/folke/lazy.nvim.git",
    "--branch=stable", -- latest stable release
    lazypath,
  })
end
vim.opt.rtp:prepend(lazypath)

require("lazy").setup({
  spec = {
    { import = "plugins" },
  },
})
