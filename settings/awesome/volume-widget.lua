local awful = require("awful")
local wibox = require("wibox")

local function get_icon_path()
    return debug.getinfo(1).source:match("@?(.*/)")
end

local Volume = { mt = {}, wmt = {} }
Volume.wmt.__index = Volume
Volume.__index = Volume

function Volume:new(args)
    local obj = setmetatable({}, Volume)
    obj.step = args.step or 10

    local volume_text_widget, volume_text_timer = awful.widget.watch(
        "pactl get-sink-volume @DEFAULT_SINK@", 5,
        function(widget, stdout)
            local volume = stdout:match("(%d+)%%")
            if volume then
                widget:set_text(volume)
                return
            end
        end
    )
    obj.volume_text_timer = volume_text_timer

    -- Create widget
    obj.widget = wibox.widget {
        {
            id = "icon",
            image = get_icon_path() .. "/volume-widget-icon.svg",
            widget = wibox.widget.imagebox
        },
        volume_text_widget,
        layout = wibox.layout.fixed.horizontal
    }

    return obj
end

function Volume:up()
    awful.spawn.easy_async("pactl set-sink-volume @DEFAULT_SINK@ +" .. self.step .. "%", function()
        self.volume_text_timer:emit_signal("timeout")
    end)
end

function Volume:down()
    awful.spawn.easy_async("pactl set-sink-volume @DEFAULT_SINK@ -" .. self.step .. "%", function()
        self.volume_text_timer:emit_signal("timeout")
    end)
end

function Volume.mt:__call(...)
    return Volume.new(...)
end

return Volume
