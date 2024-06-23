local awful = require("awful")
local wibox = require("wibox")

local function get_icon_path()
    return debug.getinfo(1).source:match("@?(.*/)")
end

local memory_widget = {}

local function worker(user_args)
    local args = user_args or {}

    local memory_icon = wibox.widget {
        image  = get_icon_path() .. "/memory-widget-icon.svg",
        resize = true,
        widget = wibox.widget.imagebox
    }

    local memory_text = awful.widget.watch(
        'bash -c "free -h | awk \'/^Mem/ {print $3 + 0 \\"/\\" $2}\'"',
        10
    )

    memory_widget = wibox.widget {
        memory_icon,
        memory_text,
        layout = wibox.layout.fixed.horizontal,
    }

    return memory_widget
end

return setmetatable(memory_widget, {
    __call = function(_, ...)
        return worker(...)
    end
})
