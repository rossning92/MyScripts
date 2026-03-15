local wezterm = require 'wezterm'

wezterm.on('format-window-title', function(tab, pane, tabs, panes, config)
  local title = os.getenv('WEZTERM_WINDOW_TITLE')
  local original_title = ''

  if tab and tab.active_pane and tab.active_pane.title then
    original_title = tab.active_pane.title
  end

  if title and title ~= '' then
    if original_title ~= '' then
      return title .. ' - ' .. original_title
    end
    return title
  end
end)

return {
  hide_tab_bar_if_only_one_tab = true,
  window_close_confirmation = 'NeverPrompt',
  initial_cols = 120,
  initial_rows = 30,
  font_size = 10.0,
  window_padding = {
    left = 0,
    right = 0,
    top = 0,
    bottom = 0,
  },
  colors = {
    foreground = '#f8f8f2',
    background = '#282a36',
    ansi = {
      '#21222c',
      '#ff5555',
      '#50fa7b',
      '#f1fa8c',
      '#caa9fa',
      '#ff79c6',
      '#8be9fd',
      '#bfbfbf',
    },
    brights = {
      '#6272a4',
      '#ff6e67',
      '#5af78e',
      '#f4f99d',
      '#caa9fa',
      '#ff92d0',
      '#9aedfe',
      '#e6e6e6',
    },
  },
  keys = {
    { key = 'C',     mods = 'CTRL|SHIFT', action = wezterm.action.CopyTo 'Clipboard' },
    { key = 'V',     mods = 'CTRL|SHIFT', action = wezterm.action.PasteFrom 'Clipboard' },
    { key = 'Space', mods = 'CTRL',       action = wezterm.action.ActivateCopyMode },
  },
}
