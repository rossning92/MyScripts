local wibox = require("wibox")

local function script_path()
    return debug.getinfo(1).source:match("@?(.*/)")
end

local function run(command)
    local prog = io.popen(command)
    local result = prog:read('*all')
    prog:close()
    return result
end

local Volume = { mt = {}, wmt = {} }
Volume.wmt.__index = Volume
Volume.__index = Volume

function Volume:new(args)
    local obj = setmetatable({}, Volume)
    obj.step = args.step or 10

    -- Create widget
    obj.widget = wibox.widget {
        {
            id = "icon",
            image = script_path() .. '/icons/volume.svg',
            widget = wibox.widget.imagebox
        },
        {
            id = 'txt',
            widget = wibox.widget.textbox
        },
        layout = wibox.layout.fixed.horizontal
    }

    -- Check the volume every 5 seconds
    obj.timer = timer({ timeout = 5 })
    obj.timer:connect_signal("timeout", function() obj:update() end)
    obj.timer:start()

    obj:update()

    return obj
end

function Volume:update()
    self.widget:get_children_by_id('txt')[1]:set_text(self:getVolume())
end

function Volume:up()
    run("pactl set-sink-volume @DEFAULT_SINK@ +" .. self.step .. "%");
    self:update()
end

function Volume:down()
    run("pactl set-sink-volume @DEFAULT_SINK@ -" .. self.step .. "%");
    self:update()
end

function Volume:getVolume()
    return run("pactl get-sink-volume @DEFAULT_SINK@ | grep -Po '\\d+(?=%)' | head -n 1")
end

function Volume.mt:__call(...)
    return Volume.new(...)
end

return Volume
