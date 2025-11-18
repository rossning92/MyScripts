local utils = require 'mp.utils'

local function set_clip(text)
    local platform = jit and jit.os or ""

    if platform == "Windows" then
        utils.subprocess_detached({
            args = { "powershell", "set-clipboard", "\"" .. text:gsub("\n", "`n") .. "\"" },
        })
    elseif platform == "Linux" then
        mp.command_native_async({
            name = "subprocess",
            args = { "xclip", "-selection", "clipboard" },
            stdin_data = text,
        }, function() end)
    else
        mp.osd_message("Clipboard copy not supported on this platform")
    end
end

mp.add_forced_key_binding("m", "copy_mouse_to_clipboard", function()
    local mouse_x, mouse_y = mp.get_mouse_pos()
    local osd_width, osd_height = mp.get_osd_size()
    local normalized_mouse_x = mouse_x / osd_width
    local normalized_mouse_y = mouse_y / osd_height
    local out_x = normalized_mouse_x * 1920
    local out_y = normalized_mouse_y * 1080

    local message = string.format("{{ hl(pos=(%d, %d), t='as') }}", math.floor(out_x + 0.5), math.floor(out_y + 0.5))
    mp.osd_message(message)
    set_clip(message)
end)
