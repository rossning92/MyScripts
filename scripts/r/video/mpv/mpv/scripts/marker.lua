local utils = require('mp.utils')

local out = ''

local function add_marker()
    local time_pos = mp.get_property_number('time-pos')
    local time_pos_osd = mp.get_property_osd('time-pos/full')
    mp.osd_message('Marker: ' .. time_pos_osd, 1)

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
