local gears = require("gears")
local awful = require("awful")
local wibox = require("wibox")

local widget = {}

local function worker()
    local script_dir = debug.getinfo(1).source:match("@?(.*/)")
    local icon_widget = wibox.widget {
        image  = script_dir .. "/temperature-widget-icon.svg",
        resize = true,
        widget = wibox.widget.imagebox
    }

    local temp_paths = {
        "/sys/class/thermal/thermal_zone0/temp", -- For Intel CPUs
        "/sys/class/hwmon/hwmon1/temp1_input"    -- For AMD CPUs
    }
    local temp_path
    local text_widget

    for _, path in ipairs(temp_paths) do
        if gears.filesystem.file_readable(path) then
            temp_path = path
            break
        end
    end

    if temp_path then
        text_widget = awful.widget.watch(
            "cat " .. temp_path, 10,
            function(widget, stdout)
                local temp = math.floor(tonumber(stdout) / 1000)
                widget:set_text(tostring(temp))
            end
        )
    else
        text_widget = wibox.widget.textbox("NA")
    end

    widget = wibox.widget {
        icon_widget,
        text_widget,
        layout = wibox.layout.fixed.horizontal,
    }

    return widget
end

return setmetatable(widget, {
    __call = function(_)
        return worker()
    end
})
