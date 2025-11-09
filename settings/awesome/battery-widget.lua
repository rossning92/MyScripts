local awful = require("awful")

local function has_battery()
    local handle = io.popen("ls /sys/class/power_supply 2>/dev/null")
    if not handle then
        return false
    end

    for name in handle:lines() do
        if name:match("^BAT") then
            handle:close()
            return true
        end
    end

    handle:close()
    return false
end

local function worker()
    if not has_battery() then
        return nil
    end

    return awful.widget.watch(
        "acpi --battery", 10,
        function(widget, stdout)
            local battery_level = stdout:match("(%d+)%%")
            local is_charging = stdout:find("Charging") ~= nil
            if battery_level then
                local icon = is_charging and "󰂄" or "󰁹"
                widget:set_text(icon .. " " .. battery_level)
            end
        end
    )
end

return setmetatable({}, {
    __call = function(_)
        return worker()
    end
})
