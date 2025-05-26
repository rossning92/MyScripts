-- https://github.com/nvim-lua/kickstart.nvim/blob/master/init.lua

vim.wo.relativenumber = true
vim.wo.number = true
vim.g.mapleader = " "
vim.opt.shortmess:append("I")     -- Disable intro message
vim.opt.clipboard = "unnamedplus" -- Use system clipboard
vim.opt.termguicolors = false

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
  -- Detect tabstop and shiftwidth automatically
  'NMAC427/guess-indent.nvim',

  'folke/which-key.nvim',

  -- Fuzzy finder
  {
    'nvim-telescope/telescope.nvim',
    event = 'VimEnter',
    dependencies = {
      'nvim-lua/plenary.nvim',
      { -- If encountering errors, see telescope-fzf-native README for installation instructions
        'nvim-telescope/telescope-fzf-native.nvim',

        -- `build` is used to run some command when the plugin is installed/updated.
        -- This is only run then, not every time Neovim starts up.
        build = 'make',

        -- `cond` is a condition used to determine whether this plugin should be
        -- installed and loaded.
        cond = function()
          return vim.fn.executable 'make' == 1
        end,
      },
      { 'nvim-telescope/telescope-ui-select.nvim' },

      -- Useful for getting pretty icons, but requires a Nerd Font.
      { 'nvim-tree/nvim-web-devicons',            enabled = vim.g.have_nerd_font },
    },
    config = function()
      require('telescope').setup {
        -- You can put your default mappings / updates / etc. in here
        --  All the info you're looking for is in `:help telescope.setup()`
        --
        -- defaults = {
        --   mappings = {
        --     i = { ['<c-enter>'] = 'to_fuzzy_refine' },
        --   },
        -- },
        -- pickers = {}
        extensions = {
          ['ui-select'] = {
            require('telescope.themes').get_dropdown(),
          },
        },
      }

      -- Enable Telescope extensions if they are installed
      pcall(require('telescope').load_extension, 'fzf')
      pcall(require('telescope').load_extension, 'ui-select')

      -- See `:help telescope.builtin`
      local builtin = require 'telescope.builtin'
      vim.keymap.set('n', '<leader>sh', builtin.help_tags, { desc = '[S]earch [H]elp' })
      vim.keymap.set('n', '<leader>sk', builtin.keymaps, { desc = '[S]earch [K]eymaps' })
      vim.keymap.set('n', '<leader>sf', builtin.find_files, { desc = '[S]earch [F]iles' })
      vim.keymap.set('n', '<leader>ss', builtin.builtin, { desc = '[S]earch [S]elect Telescope' })
      vim.keymap.set('n', '<leader>sw', builtin.grep_string, { desc = '[S]earch current [W]ord' })
      vim.keymap.set('n', '<leader>sg', builtin.live_grep, { desc = '[S]earch by [G]rep' })
      vim.keymap.set('n', '<leader>sd', builtin.diagnostics, { desc = '[S]earch [D]iagnostics' })
      vim.keymap.set('n', '<leader>sr', builtin.resume, { desc = '[S]earch [R]esume' })
      vim.keymap.set('n', '<leader>s.', builtin.oldfiles, { desc = '[S]earch Recent Files ("." for repeat)' })
      vim.keymap.set('n', '<leader><leader>', builtin.buffers, { desc = '[ ] Find existing buffers' })

      -- Slightly advanced example of overriding default behavior and theme
      vim.keymap.set('n', '<leader>/', function()
        -- You can pass additional configuration to Telescope to change the theme, layout, etc.
        builtin.current_buffer_fuzzy_find(require('telescope.themes').get_dropdown {
          winblend = 10,
          previewer = false,
        })
      end, { desc = '[/] Fuzzily search in current buffer' })

      -- It's also possible to pass additional configuration options.
      --  See `:help telescope.builtin.live_grep()` for information about particular keys
      vim.keymap.set('n', '<leader>s/', function()
        builtin.live_grep {
          grep_open_files = true,
          prompt_title = 'Live Grep in Open Files',
        }
      end, { desc = '[S]earch [/] in Open Files' })
    end,
  },

  -- Setup LSP (Language Server Protocol)
  {
    'neovim/nvim-lspconfig',
    dependencies = {
      -- Automatically install LSPs and related tools to stdpath for Neovim
      -- Mason must be loaded before its dependents so we need to set it up here.
      -- NOTE: `opts = {}` is the same as calling `require('mason').setup({})`
      { 'mason-org/mason.nvim', opts = {} },
      'mason-org/mason-lspconfig.nvim',
      'WhoIsSethDaniel/mason-tool-installer.nvim',

      -- Useful status updates for LSP.
      { 'j-hui/fidget.nvim',    opts = {} },

      -- Allows extra capabilities provided by blink.cmp
      'saghen/blink.cmp',
    },
    config = function()
      --  The function gets run when an LSP attaches to a particular buffer:
      vim.api.nvim_create_autocmd('LspAttach', {
        group = vim.api.nvim_create_augroup('kickstart-lsp-attach', { clear = true }),
        callback = function(event)
          -- Helper function for key maps.
          local map = function(keys, func, desc, mode)
            mode = mode or 'n'
            vim.keymap.set(mode, keys, func, { buffer = event.buf, desc = 'LSP: ' .. desc })
          end

          -- Rename the variable under your cursor.
          --  Most Language Servers support renaming across files, etc.
          map('grn', vim.lsp.buf.rename, '[R]e[n]ame')

          -- Execute a code action, usually your cursor needs to be on top of an error
          -- or a suggestion from your LSP for this to activate.
          map('gra', vim.lsp.buf.code_action, '[G]oto Code [A]ction', { 'n', 'x' })

          -- Find references for the word under your cursor.
          map('grr', require('telescope.builtin').lsp_references, '[G]oto [R]eferences')

          -- Jump to the implementation of the word under your cursor.
          --  Useful when your language has ways of declaring types without an actual implementation.
          map('gri', require('telescope.builtin').lsp_implementations, '[G]oto [I]mplementation')

          -- Jump to the definition of the word under your cursor.
          --  This is where a variable was first declared, or where a function is defined, etc.
          --  To jump back, press <C-t>.
          map('grd', require('telescope.builtin').lsp_definitions, '[G]oto [D]efinition')

          -- WARN: This is not Goto Definition, this is Goto Declaration.
          --  For example, in C this would take you to the header.
          map('grD', vim.lsp.buf.declaration, '[G]oto [D]eclaration')

          -- Fuzzy find all the symbols in your current document.
          --  Symbols are things like variables, functions, types, etc.
          map('gO', require('telescope.builtin').lsp_document_symbols, 'Open Document Symbols')

          -- Fuzzy find all the symbols in your current workspace.
          --  Similar to document symbols, except searches over your entire project.
          map('gW', require('telescope.builtin').lsp_dynamic_workspace_symbols, 'Open Workspace Symbols')

          -- Jump to the type of the word under your cursor.
          --  Useful when you're not sure what type a variable is and you want to see
          --  the definition of its *type*, not where it was *defined*.
          map('grt', require('telescope.builtin').lsp_type_definitions, '[G]oto [T]ype Definition')

          -- This function resolves a difference between neovim nightly (version 0.11) and stable (version 0.10)
          ---@param client vim.lsp.Client
          ---@param method vim.lsp.protocol.Method
          ---@param bufnr? integer some lsp support methods only in specific files
          ---@return boolean
          local function client_supports_method(client, method, bufnr)
            if vim.fn.has 'nvim-0.11' == 1 then
              return client:supports_method(method, bufnr)
            else
              return client.supports_method(method, { bufnr = bufnr })
            end
          end

          -- The following two autocommands are used to highlight references of the
          -- word under your cursor when your cursor rests there for a little while.
          --    See `:help CursorHold` for information about when this is executed
          --
          -- When you move your cursor, the highlights will be cleared (the second autocommand).
          local client = vim.lsp.get_client_by_id(event.data.client_id)
          if client and client_supports_method(client, vim.lsp.protocol.Methods.textDocument_documentHighlight, event.buf) then
            local highlight_augroup = vim.api.nvim_create_augroup('kickstart-lsp-highlight', { clear = false })
            vim.api.nvim_create_autocmd({ 'CursorHold', 'CursorHoldI' }, {
              buffer = event.buf,
              group = highlight_augroup,
              callback = vim.lsp.buf.document_highlight,
            })

            vim.api.nvim_create_autocmd({ 'CursorMoved', 'CursorMovedI' }, {
              buffer = event.buf,
              group = highlight_augroup,
              callback = vim.lsp.buf.clear_references,
            })

            vim.api.nvim_create_autocmd('LspDetach', {
              group = vim.api.nvim_create_augroup('kickstart-lsp-detach', { clear = true }),
              callback = function(event2)
                vim.lsp.buf.clear_references()
                vim.api.nvim_clear_autocmds { group = 'kickstart-lsp-highlight', buffer = event2.buf }
              end,
            })
          end

          -- The following code creates a keymap to toggle inlay hints in your
          -- code, if the language server you are using supports them
          --
          -- This may be unwanted, since they displace some of your code
          if client and client_supports_method(client, vim.lsp.protocol.Methods.textDocument_inlayHint, event.buf) then
            map('<leader>th', function()
              vim.lsp.inlay_hint.enable(not vim.lsp.inlay_hint.is_enabled { bufnr = event.buf })
            end, '[T]oggle Inlay [H]ints')
          end
        end,
      })

      -- Diagnostic Config
      -- See :help vim.diagnostic.Opts
      vim.diagnostic.config {
        severity_sort = true,
        float = { border = 'rounded', source = 'if_many' },
        underline = { severity = vim.diagnostic.severity.ERROR },
        signs = vim.g.have_nerd_font and {
          text = {
            [vim.diagnostic.severity.ERROR] = '󰅚 ',
            [vim.diagnostic.severity.WARN] = '󰀪 ',
            [vim.diagnostic.severity.INFO] = '󰋽 ',
            [vim.diagnostic.severity.HINT] = '󰌶 ',
          },
        } or {},
        virtual_text = {
          source = 'if_many',
          spacing = 2,
          format = function(diagnostic)
            local diagnostic_message = {
              [vim.diagnostic.severity.ERROR] = diagnostic.message,
              [vim.diagnostic.severity.WARN] = diagnostic.message,
              [vim.diagnostic.severity.INFO] = diagnostic.message,
              [vim.diagnostic.severity.HINT] = diagnostic.message,
            }
            return diagnostic_message[diagnostic.severity]
          end,
        },
      }

      -- LSP servers and clients are able to communicate to each other what features they support.
      --  By default, Neovim doesn't support everything that is in the LSP specification.
      --  When you add blink.cmp, luasnip, etc. Neovim now has *more* capabilities.
      --  So, we create new capabilities with blink.cmp, and then broadcast that to the servers.
      local capabilities = require('blink.cmp').get_lsp_capabilities()

      -- Enable the following language servers
      local servers = {
        -- clangd = {},
        -- gopls = {},
        pyright = {},
        -- rust_analyzer = {},
        -- lua_ls = {},
      }

      -- Ensure the servers and tools above are installed
      local ensure_installed = vim.tbl_keys(servers or {})
      vim.list_extend(ensure_installed, {
        'stylua', -- Used to format Lua code
      })
      require('mason-tool-installer').setup { ensure_installed = ensure_installed }

      require('mason-lspconfig').setup {
        ensure_installed = {}, -- explicitly set to an empty table (Kickstart populates installs via mason-tool-installer)
        automatic_installation = false,
        handlers = {
          function(server_name)
            local server = servers[server_name] or {}
            -- This handles overriding only values explicitly passed
            -- by the server configuration above. Useful when disabling
            -- certain features of an LSP (for example, turning off formatting for ts_ls)
            server.capabilities = vim.tbl_deep_extend('force', {}, capabilities, server.capabilities or {})
            require('lspconfig')[server_name].setup(server)
          end,
        },
      }
    end,
  },

  -- Autocompletion
  {
    'saghen/blink.cmp',
    event = 'VimEnter',
    version = '1.*',
    dependencies = {
      -- Snippet Engine
      {
        'L3MON4D3/LuaSnip',
        version = '2.*',
        build = (function()
          -- Build Step is needed for regex support in snippets.
          -- This step is not supported in many windows environments.
          -- Remove the below condition to re-enable on windows.
          if vim.fn.has 'win32' == 1 or vim.fn.executable 'make' == 0 then
            return
          end
          return 'make install_jsregexp'
        end)(),
        dependencies = {
          -- `friendly-snippets` contains a variety of premade snippets.
          --    See the README about individual language/framework/plugin snippets:
          --    https://github.com/rafamadriz/friendly-snippets
          -- {
          --   'rafamadriz/friendly-snippets',
          --   config = function()
          --     require('luasnip.loaders.from_vscode').lazy_load()
          --   end,
          -- },
        },
        opts = {},
      },
      'folke/lazydev.nvim',
    },
    --- @module 'blink.cmp'
    --- @type blink.cmp.Config
    opts = {
      keymap = {
        preset = 'default',
      },
      appearance = {
        nerd_font_variant = 'mono',
      },
      completion = {
        documentation = { auto_show = false, auto_show_delay_ms = 500 },
      },
      sources = {
        default = { 'lsp', 'path', 'snippets', 'lazydev' },
        providers = {
          lazydev = { module = 'lazydev.integrations.blink', score_offset = 100 },
        },
      },
      snippets = { preset = 'luasnip' },
      fuzzy = { implementation = 'lua' },
      signature = { enabled = true },
    },
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
    text = vim.api.nvim_buf_get_text(0, start_pos[2] - 1, start_pos[3] - 1, end_pos[2] - 1, end_pos[3], {})[1]
  else
    text = table.concat(lines, '\n')
    start_pos[3] = 1
    end_pos[3] = #(lines[#lines] or '')
  end

  return text, start_pos, end_pos
end

local function replace_text(text, start_pos, end_pos)
  -- Split the reconstructed text back into lines.
  local lines = {}
  for line in text:gmatch("[^\r\n]+") do
    table.insert(lines, line)
  end

  -- Set the modified lines back to the buffer.
  -- vim.api.nvim_buf_set_lines(0, start_pos[2] - 1, end_pos[2], false, lines)
  vim.api.nvim_buf_set_text(0, start_pos[2] - 1, start_pos[3] - 1, end_pos[2] - 1, end_pos[3], lines)

  -- Move cursor to the end of the last line of the replaced text.
  vim.api.nvim_win_set_cursor(0, { start_pos[2] + #lines - 1, #lines[#lines] })
end

local function run_in_terminal(cmd, opts)
  opts = opts or {}

  -- Create a new buffer (unlisted and scratch)
  local bufnr = vim.api.nvim_create_buf(false, true)

  -- Split the current window and open the new buffer in the bottom half
  vim.cmd('split')
  vim.cmd('wincmd J') -- Move the new split to the bottom
  local win_id = vim.api.nvim_get_current_win()
  if opts.height then
    vim.api.nvim_win_set_height(win_id, opts.height)
  end
  vim.api.nvim_win_set_buf(win_id, bufnr)

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
end

local function is_windows()
  local os_name = os.getenv("OS")
  return os_name and os_name:lower():match("windows")
end

-- Workaround: If Neovim is running on Windows within MSYS2, we should force set
-- the default shell to cmd.exe in order to have commands like `termopen`
-- working properly.
if is_windows() then
  vim.o.shell = "cmd.exe"
end

local function fix()
  -- Prompt
  local text, start_pos, end_pos = get_selected_text()
  local prompt = "Fix the spelling and grammar of the following text and only return the corrected text:\n---\n" .. text
  local prompt_file = os.tmpname()
  local file = io.open(prompt_file, "w")
  if file then
    file:write(prompt)
    file:close()
  end

  local output_file = os.tmpname()
  run_in_terminal(
    "run_script r/ai/complete_chat.py --quiet -o " .. output_file .. " " .. prompt_file, {
      height = 1,
      on_exit = function()
        local new_text = read_text_file(output_file)
        replace_text(new_text, start_pos, end_pos)

        os.remove(prompt_file)
        os.remove(output_file)
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
    height = 1,
    on_exit = function()
      local text = read_text_file(tmp_file)
      os.remove(tmp_file)
      if text ~= "" then
        append_line(text)
      end
    end
  })
end
vim.keymap.set('n', "<leader><space>", speech_to_text)

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
