local awful = require("awful")

local cpu_widget = {}
local prev_total = 0
local prev_idle = 0

local function worker()
    local icon = '';
    cpu_widget = awful.widget.watch(
        'cat /proc/stat',
        1,
        function(widget, stdout)
            local cpu_line = stdout:match("cpu%s+(.-)\n")
            if cpu_line then
                local user, nice, system, idle, iowait, irq, softirq, steal, guest, guest_nice = cpu_line:match(
                    "(%d+)%s+(%d+)%s+(%d+)%s+(%d+)%s+(%d+)%s+(%d+)%s+(%d+)%s+(%d+)%s+(%d+)%s+(%d+)")
                if user then
                    local idle_sum = idle + iowait
                    local total = user + nice + system + idle + iowait + irq + softirq + steal + guest + guest_nice
                    local diff_total = total - prev_total
                    local diff_idle = idle_sum - prev_idle
                    if diff_total > 0 then
                        local usage = math.floor(((diff_total - diff_idle) / diff_total) * 100 + 0.5)
                        widget:set_text(icon .. usage .. "% ")
                    end
                    prev_total = total
                    prev_idle = idle_sum
                end
            end
        end
    )

    return cpu_widget
end

return setmetatable(cpu_widget, {
    __call = function(_)
        return worker()
    end
})
