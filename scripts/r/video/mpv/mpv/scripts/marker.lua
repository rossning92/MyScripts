local utils = require('mp.utils')

local out = ''

local function set_clipboard(text)
    mp.commandv('run', 'powershell', 'set-clipboard', text)
end

local function add_marker()
    local time_pos = mp.get_property_number('time-pos')
    local time_pos_osd = mp.get_property_osd('time-pos/full')

    local mouse_x, mouse_y = mp.get_mouse_pos()
    local s = time_pos .. '!' .. mouse_x .. '!' .. mouse_y
    set_clipboard(s)
    mp.osd_message(s, 1)

    out = out .. time_pos .. '\n'
end

local function save_to_text_file()
    local path = mp.get_property('path')
    dir, name_ext = utils.split_path(path)
    local out_path = utils.join_path(dir, name_ext .. '.marker.txt')
    local file = io.open(out_path, 'w')
    file:write(out)
    file:close()
    mp.osd_message('Saved to: ' .. out_path, 3)
    out = ''
end

mp.add_forced_key_binding('m', 'add_marker', add_marker)
mp.add_forced_key_binding('M', 'save_to_text_file', save_to_text_file)
