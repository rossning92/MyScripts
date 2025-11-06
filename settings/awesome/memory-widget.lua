local awful = require("awful")

local memory_widget = {}

local function worker()
    memory_widget = awful.widget.watch(
        'free -h',
        1,
        function(widget, stdout)
            local total, used = stdout:match("Mem:%s+(%S+)%s+(%S+)")
            if total and used then
                local formatted_used = used:gsub("Gi", "")
                local formatted_total = total:gsub("Gi", "G")
                widget:set_text(" " .. formatted_used .. "/" .. formatted_total)
            end
        end
    )

    return memory_widget
end

return setmetatable(memory_widget, {
    __call = function(_)
        return worker()
    end
})
