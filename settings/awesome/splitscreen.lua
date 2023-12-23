-- https://devrandom.ro/blog/2022-awesome-window-manager-hacks.html

local awful = require("awful")
local M = {}

function M.split_screen()
    if (screen.count() ~= 1) then
        -- A sanity check, so we don't split multiple times.
        debug("More than 1 screen, skip split_screen()", screen.count())
        return
    end
    local geo = screen[1].geometry
    local new_width = math.ceil(3 * geo.width / 4) - 30 -- personal sweet spot for main screen size
    local new_width2 = geo.width - new_width
    local parent = screen[1]
    parent.original_w = geo.width
    parent.original_h = geo.height
    parent:fake_resize(geo.x, geo.y, new_width, geo.height)
    local fake = screen.fake_add(geo.x + new_width, geo.y, new_width2, geo.height)
    if (parent.fakes == nil) then
        parent.fakes = {}
    end
    parent.fakes[fake.index] = fake
    for k, v in pairs(fake.tags) do
        v.layout = awful.layout.suit.tile.bottom
    end
    collectgarbage('collect')
end

function M.reset_layout()
    for s in screen do
        if s.fakes then
            for _, f in pairs(s.fakes) do
                f:fake_remove()
            end
            s.fakes = nil

            local geo = s.geometry
            s:fake_resize(geo.x, geo.y, s.original_w, geo.height)
        end
    end
end

function M.toggle_layout()
    if (screen.count() == 1) then
        M.split_screen()
    else
        M.reset_layout()
    end
end

function M.init_layout()
    if (screen.count() ~= 1) then
        -- A sanity check, so we don't split multiple times.
        debug("More than 1 screen, skip split_screen()", screen.count())
        return
    end

    -- Automatically split the screen if it is a ultra wide screen.
    local geo = screen[1].geometry
    if geo.width / geo.height > 2 then
        M.split_screen()
    end
end

return M
