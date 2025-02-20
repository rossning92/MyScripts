vim.wo.relativenumber = true
vim.wo.number = true
vim.g.mapleader = " "
vim.opt.shortmess:append("I")     -- Disable intro message
vim.opt.clipboard = "unnamedplus" -- Use system clipboard

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

local function read_text_file(filepath)
  local file, err = io.open(filepath, "r")
  if not file then
    error("Error: Could not open file '" .. filepath .. "'. " .. (err or "Unknown error"))
  end

  local text = file:read("*a")
  file:close()
  os.remove(filepath)
  return text
end

local function get_selected_text()
  local mode = vim.fn.mode()
  local start_pos = vim.fn.getpos("v")
  local end_pos = vim.fn.getpos(".")

  -- Swap start_pos and end_pos if start comes after end.
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

  return text
end

local function replace_selected_text(text)
  local mode = vim.fn.mode()
  local start_pos = vim.fn.getpos("v")
  local end_pos = vim.fn.getpos(".")

  -- Swap start_pos and end_pos if start comes after end.
  if start_pos[2] > end_pos[2] or (start_pos[2] == end_pos[2] and start_pos[3] > end_pos[3]) then
    start_pos, end_pos = end_pos, start_pos
  end

  -- Retrieve the lines in the buffer from start_pos to end_pos.
  local lines = vim.api.nvim_buf_get_lines(0, start_pos[2] - 1, end_pos[2], false)

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

local function run_in_terminal(cmd, opts)
  opts = opts or {}

  -- Create a new buffer (unlisted and scratch)
  local bufnr = vim.api.nvim_create_buf(false, true)

  -- Split the current window and open the new buffer in the bottom half
  vim.cmd('split')
  vim.cmd('wincmd J')                           -- Move the new split to the bottom
  local win_id = vim.api.nvim_get_current_win() -- Get the current window ID
  vim.api.nvim_win_set_buf(win_id, bufnr)       -- Set the buffer to the new window

  -- Start a terminal and run command
  vim.fn.termopen(cmd, {
    on_exit = function(_, exit_code, _)
      if exit_code == 0 then
        -- Close the window if exit code is 0
        vim.api.nvim_win_close(win_id, true)
        if opts.on_exit then
          opts.on_exit()
        end
      end
    end
  })

  -- Start insert mode
  vim.cmd("startinsert")
end

local function fix()
  local text = get_selected_text()
  local tmp_file = os.tmpname()
  run_in_terminal(
    "run_script r/ai/complete_chat.py -o " ..
    tmp_file .. " \'Fix the spelling and grammar of the following text and only return the corrected text:\n---\n" ..
    text:gsub("'", "'\\''") .. "\'", {
      on_exit = function()
        local new_text = read_text_file(tmp_file)
        os.remove(tmp_file)
        replace_selected_text(new_text)
      end
    })
end
vim.keymap.set({ "n", "i", "v" }, "<C-k>f", fix)

local function append_line(line)
  line = string.gsub(line, '^%s*(.-)%s*$', '%1') -- trim trailing spaces

  local current_line = vim.api.nvim_get_current_line()
  local cur_row_number = vim.api.nvim_win_get_cursor(0)[1] -- 1-based

  -- Determine where to insert this new line
  local insert_index -- zero-based
  if current_line == "" then
    insert_index = cur_row_number - 1
  else
    insert_index = cur_row_number
  end

  -- Insert line
  vim.api.nvim_buf_set_lines(0, insert_index, insert_index, false, { line })

  -- Move cursor to the end of the newly inserted line
  vim.api.nvim_win_set_cursor(0, {
    insert_index + 1, -- row number: 1-based
    #line             -- column index: 0-based
  })
end

local function speech_to_text()
  local tmp_file = os.tmpname()
  run_in_terminal("run_script r/speech_to_text.py -o " .. tmp_file, {
    on_exit = function()
      local text = read_text_file(tmp_file)
      os.remove(tmp_file)
      if text ~= "" then
        append_line(text)
      end
    end
  })
end
vim.keymap.set({ "n", "i" }, "<C-v>", speech_to_text)

local function run_coder()
  local full_path = vim.api.nvim_buf_get_name(0)
  if full_path ~= "" then
    -- Get selected line ranges
    local start_pos = vim.fn.getpos("v")
    local end_pos = vim.fn.getpos(".")

    -- If any text is selected
    if start_pos[2] ~= end_pos[2] or start_pos[3] ~= end_pos[3] then
      local line_start = start_pos[2]
      local line_end = end_pos[2]

      -- Swap line start and end if start comes after end
      if line_start > line_end then
        line_start, line_end = line_end, line_start
      end

      -- Concatenate selected line range at the end
      full_path = full_path .. "#" .. line_start .. "-" .. line_end
    end

    run_in_terminal('run_script r/ai/coder.py "' .. full_path .. '"', {
      on_exit = function()
        -- Reload the current file from disk
        vim.api.nvim_command('edit!')
      end
    })
  end
end
vim.keymap.set({ "n", "i", "v" }, "<C-i>", run_coder)
