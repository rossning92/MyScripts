-- https://devrandom.ro/blog/2022-awesome-window-manager-hacks.html

local awful = require("awful")
local M = {}
local is_updating = false

function M.split_screen()
    local geo = screen[1].geometry
    local aspect = geo.width / geo.height

    local screen1_width, screen2_width
    if aspect < 21 / 9 then
        screen1_width = math.floor(geo.width * 2 / 3 + 0.5)
        screen2_width = geo.width - screen1_width
    else
        screen1_width = math.floor(geo.width * 3 / 4 + 0.5)
        screen2_width = geo.width - screen1_width
    end

    local parent = screen[1]
    parent.original_w = geo.width
    parent.original_h = geo.height
    parent:fake_resize(geo.x, geo.y, screen1_width, geo.height)
    local fake = screen.fake_add(geo.x + screen1_width, geo.y, screen2_width, geo.height)
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

function M.remove_fakes()
    for s in screen do
        if s.fakes then
            for _, f in pairs(s.fakes) do
                f:fake_remove()
            end
            s.fakes = nil
        end
    end
end

function M.toggle_layout()
    if is_updating then return end
    is_updating = true

    if (screen.count() == 1) then
        M.split_screen()
    else
        M.reset_layout()
    end

    is_updating = false
end

function M.init_layout()
    if is_updating then return end
    is_updating = true

    local s = screen[1]
    if not s then
        is_updating = false
        return
    end

    local aspect = s.geometry.width / s.geometry.height

    -- Automatically split the screen if it is a ultra wide screen.
    if aspect >= 21 / 9 then
        M.split_screen()
    else
        M.remove_fakes()
    end

    is_updating = false
end

return M
