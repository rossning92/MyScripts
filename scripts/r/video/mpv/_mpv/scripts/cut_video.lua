local utils = require("mp.utils")

local in_time = nil
local out_time = nil

local function format_time(seconds)
    if not seconds then
        return "unset"
    end
    local h = math.floor(seconds / 3600)
    local m = math.floor((seconds % 3600) / 60)
    local s = seconds % 60
    if h > 0 then
        return string.format("%d:%02d:%05.2f", h, m, s)
    end
    return string.format("%02d:%05.2f", m, s)
end

local function show_status()
    mp.osd_message(string.format("Cut Range: [%s, %s]", format_time(in_time), format_time(out_time)))
end

local function current_time()
    return mp.get_property_number("time-pos")
end

local function set_in_point()
    local time = current_time()
    if time then
        in_time = time
        if out_time and out_time < in_time then
            out_time = nil
        end
        show_status()
    else
        mp.osd_message("Failed to get time-pos to set IN point")
    end
end

local function set_out_point()
    local time = current_time()
    if time then
        out_time = time
        if in_time and in_time > out_time then
            in_time = nil
        end
        show_status()
    else
        mp.osd_message("Failed to get time-pos to set OUT point")
    end
end

local function start_cut()
    if not in_time or not out_time then
        mp.osd_message("Please set IN and OUT points before cutting")
        return
    end
    local duration = out_time - in_time
    if duration <= 0 then
        mp.osd_message("Invalid cut duration")
        return
    end
    local path = mp.get_property("path")
    if not path then
        mp.osd_message("Failed to get video path")
        return
    end
    local start = string.format("%.3f", in_time)
    local length = string.format("%.3f", duration)
    local env = utils.get_env_list()
    env[#env + 1] = string.format("CUT_VIDEO_START=%s", start)
    env[#env + 1] = string.format("CUT_VIDEO_DURATION=%s", length)
    mp.command_native_async({
        name = "subprocess",
        playback_only = false,
        args = { "run_script", "r/video/cut_video.sh", path },
        env = env
    }, function(success, result, err)
        if success then
            mp.osd_message("Video cut finished successfully")
        else
            mp.osd_message("Video cut failed" .. (err and (": " .. err) or ""))
        end
    end)
    mp.osd_message(string.format("Cutting video from %s for %s seconds", format_time(in_time), length))
end

mp.add_forced_key_binding("[", "cut_video_set_in_point", set_in_point)
mp.add_forced_key_binding("]", "cut_video_set_out_point", set_out_point)
mp.add_forced_key_binding("c", "cut_video_start_cut", start_cut)
