local awful = require("awful")

local disk_usage_widget = {}

local function worker()
    disk_usage_widget = awful.widget.watch(
        "df -h --output=used,size /",
        30,
        function(widget, stdout)
            local used, size = stdout:match("\n%s*(%S+)%s+(%S+)")
            if used and size then
                widget:set_text(" " .. used .. "/" .. size)
            end
        end
    )

    return disk_usage_widget
end

return setmetatable(disk_usage_widget, {
    __call = function(_)
        return worker()
    end
})
