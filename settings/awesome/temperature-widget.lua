local awful = require("awful")
local wibox = require("wibox")

local widget = {}

local function worker()
    script_dir = debug.getinfo(1).source:match("@?(.*/)")
    local icon_widget = wibox.widget {
        image  = script_dir .. "/temperature-widget-icon.svg",
        resize = true,
        widget = wibox.widget.imagebox
    }

    local text_widget = awful.widget.watch(
        "cat /sys/class/thermal/thermal_zone0/temp", 10,
        function(widget, stdout)
            local temp = math.floor(tonumber(stdout) / 1000)
            widget:set_text(tostring(temp))
        end
    )

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
