local awful = require("awful")
local wibox = require("wibox")

local battery_widget = {}

local function worker()
    script_dir = debug.getinfo(1).source:match("@?(.*/)")
    local icon_widget = wibox.widget {
        image  = script_dir .. "/battery-widget.svg",
        resize = true,
        widget = wibox.widget.imagebox
    }

    local text_widget = awful.widget.watch(
        "acpi --battery", 30,
        function(widget, stdout)
            local battery_level = stdout:match("(%d+)%%")
            if battery_level then
                widget:set_text(battery_level)
            end
        end
    )

    battery_widget = wibox.widget {
        icon_widget,
        text_widget,
        layout = wibox.layout.fixed.horizontal,
    }

    return battery_widget
end

return setmetatable(battery_widget, {
    __call = function(_)
        return worker()
    end
})
