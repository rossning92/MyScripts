local gears = require("gears")
local awful = require("awful")

local widget = {}

local function worker()
    local temp_paths = {
        "/sys/class/thermal/thermal_zone0/temp", -- For Intel CPUs
        "/sys/class/hwmon/hwmon1/temp1_input"    -- For AMD CPUs
    }
    local temp_path

    for _, path in ipairs(temp_paths) do
        if gears.filesystem.file_readable(path) then
            temp_path = path
            break
        end
    end

    if temp_path then
        widget = awful.widget.watch(
            "cat " .. temp_path,
            10,
            function(widget, stdout)
                local temp = math.floor(tonumber(stdout) / 1000)
                widget:set_text(" " .. tostring(temp) .. "°C")
            end
        )
    end

    return widget
end

return setmetatable(widget, {
    __call = function(_)
        return worker()
    end
})
