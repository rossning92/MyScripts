local awful = require("awful")
local wibox = require("wibox")

local function get_icon_path()
    return debug.getinfo(1).source:match("@?(.*/)")
end

local disk_usage_widget = {}

local function worker()
    local icon_widget = wibox.widget {
        image  = get_icon_path() .. "/disk-usage-widget-icon.svg",
        resize = true,
        widget = wibox.widget.imagebox
    }

    local text_widget = awful.widget.watch(
        'bash -c "df -h --output=used,size / | tail -n +2 | awk \'{print $1 + 0 \\"/\\" $2}\'"',
        30
    )

    disk_usage_widget = wibox.widget {
        icon_widget,
        text_widget,
        layout = wibox.layout.fixed.horizontal,
    }

    return disk_usage_widget
end

return setmetatable(disk_usage_widget, {
    __call = function(_)
        return worker()
    end
})
