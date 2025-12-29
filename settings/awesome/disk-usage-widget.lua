local awful = require("awful")

local disk_usage_widget = {}

local function worker()
    local icon = "";
    disk_usage_widget = awful.widget.watch(
        "df -h --output=used,size /",
        30,
        function(widget, stdout)
            local used, size = stdout:match("\n%s*(%S+)%s+(%S+)")
            if used and size then
                local formatted_used = used:gsub("G$", "")
                widget:set_text(icon .. formatted_used .. "/" .. size .. " ")
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
