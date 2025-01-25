vim.wo.relativenumber = true

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

vim.g.mapleader = " "

require("lazy").setup({
  "folke/which-key.nvim",
  { "folke/neoconf.nvim",               cmd = "Neoconf" },
  "folke/neodev.nvim",
  {
    'nvim-telescope/telescope.nvim',
    tag = '0.1.6',
    dependencies = { 'nvim-lua/plenary.nvim' }
  },

  -- https://lsp-zero.netlify.app/v3.x/tutorial.html
  { 'VonHeikemen/lsp-zero.nvim',        branch = 'v3.x' },
  { 'williamboman/mason.nvim' },
  { 'williamboman/mason-lspconfig.nvim' },
  { 'neovim/nvim-lspconfig' },
  { 'hrsh7th/cmp-nvim-lsp' },
  { 'hrsh7th/nvim-cmp' },
  { 'L3MON4D3/LuaSnip' },
})

-- Setup telescope
local builtin = require('telescope.builtin')
vim.keymap.set('n', '<leader>ff', builtin.find_files, {})
vim.keymap.set('n', '<leader>fg', builtin.live_grep, {})
vim.keymap.set('n', '<leader>fb', builtin.buffers, {})
-- Lists available help tags
vim.keymap.set('n', '<leader>fh', builtin.help_tags, {})

---
-- LSP setup
---
local lsp_zero = require('lsp-zero')

lsp_zero.on_attach(function(client, bufnr)
  -- see :help lsp-zero-keybindings
  -- to learn the available actions
  lsp_zero.default_keymaps({ buffer = bufnr })
end)

--- if you want to know more about lsp-zero and mason.nvim
--- read this: https://github.com/VonHeikemen/lsp-zero.nvim/blob/v3.x/doc/md/guide/integrate-with-mason-nvim.md
require('mason').setup({})
require('mason-lspconfig').setup({
  handlers = {
    lsp_zero.default_setup,
    lua_ls = function()
      -- (Optional) configure lua language server
      local lua_opts = lsp_zero.nvim_lua_ls()
      require('lspconfig').lua_ls.setup(lua_opts)
    end,
  }
})

---
-- Autocompletion config
---
local cmp = require('cmp')
local cmp_action = lsp_zero.cmp_action()

cmp.setup({
  mapping = cmp.mapping.preset.insert({
    -- `Enter` key to confirm completion
    ['<CR>'] = cmp.mapping.confirm({ select = false }),

    -- Ctrl+Space to trigger completion menu
    ['<C-Space>'] = cmp.mapping.complete(),

    -- Navigate between snippet placeholder
    ['<C-f>'] = cmp_action.luasnip_jump_forward(),
    ['<C-b>'] = cmp_action.luasnip_jump_backward(),

    -- Scroll up and down in the completion documentation
    ['<C-u>'] = cmp.mapping.scroll_docs(-4),
    ['<C-d>'] = cmp.mapping.scroll_docs(4),
  }),
  snippet = {
    expand = function(args)
      require('luasnip').lsp_expand(args.body)
    end,
  },
})

local function execute_command(command)
  local handle = io.popen(command)
  if handle == nil then
    print("Error: failed to execute command")
    return nil
  end

  local text = handle:read("*a")
  handle:close()
  return text
end

local function replace_selected_text(expr)
  local mode = vim.fn.mode()
  local start_pos = vim.fn.getpos("v")
  local end_pos = vim.fn.getpos(".")

  -- Swap start_pos and end_pos if start comes after end.
  -- This ensures selections are correctly handled even if made from end to start.
  if start_pos[2] > end_pos[2] or (start_pos[2] == end_pos[2] and start_pos[3] > end_pos[3]) then
    start_pos, end_pos = end_pos, start_pos
  end

  -- Retrieve the lines in the buffer from start_pos to end_pos.
  local lines = vim.api.nvim_buf_get_lines(0, start_pos[2] - 1, end_pos[2], false)

  -- Extract text only within the region defined by start_pos and end_pos.
  local text = ""
  if mode == 'v' then
    for i, line in ipairs(lines) do
      local start_col = (i == 1) and start_pos[3] or 1
      local end_col = (i == #lines) and end_pos[3] or #line
      text = text .. line:sub(start_col, end_col) .. (i ~= #lines and '\n' or '')
    end
  else
    text = table.concat(lines, '\n')
  end

  -- Apply function on the extracted text.
  text = expr(text)

  if mode == 'v' then
    -- Reconstruct the text by splicing the replaced text back into the original lines.
    text = lines[1]:sub(1, start_pos[3] - 1) .. text .. lines[#lines]:sub(end_pos[3] + 1)
  end

  -- Split the reconstructed text back into lines.
  lines = {}
  for line in text:gmatch("[^\r\n]+") do
    table.insert(lines, line)
  end

  -- Set the modified lines back to the buffer.
  vim.api.nvim_buf_set_lines(0, start_pos[2] - 1, end_pos[2], false, lines)

  -- Move cursor to the end of the last line of the replaced text.
  vim.api.nvim_win_set_cursor(0, { start_pos[2] + #lines - 1, #lines[#lines] })
end

local function fix()
  replace_selected_text(function(text)
    return execute_command(
      "run_script r/ai/openai/complete_chat.py \'Fix the spelling and grammar of the following text and only return the corrected text:\n---\n" ..
      text:gsub("'", "'\\''") .. "\'")
  end)
end
vim.keymap.set({ "n", "i", "v" }, "<C-k>f", fix)

local function speech_to_text()
  local output = execute_command("run_script r/speech_to_text.py")
  if output then
    output = string.gsub(output, '^%s*(.-)%s*$', '%1') -- trim trailing spaces

    local row, col = unpack(vim.api.nvim_win_get_cursor(0))
    vim.api.nvim_buf_set_lines(0, row, row, false, { output })
    -- Move cursor to the end of the newly inserted line
    vim.api.nvim_win_set_cursor(0, { row + 1, #output })
  end
end
vim.keymap.set({ "n", "i" }, "<C-i>", speech_to_text)
