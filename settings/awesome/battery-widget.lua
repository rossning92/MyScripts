local awful = require("awful")

local battery_widget = {}

local function worker()
    battery_widget = awful.widget.watch(
        "acpi --battery", 30,
        function(widget, stdout)
            local battery_level = stdout:match("(%d+)%%")
            if battery_level then
                widget:set_text('󰁹 ' .. battery_level)
            end
        end
    )
    return battery_widget
end

return setmetatable(battery_widget, {
    __call = function(_)
        return worker()
    end
})
