import argparse
import glob
import importlib
import inspect
import math
import os
import re
import subprocess
import sys

import moviepy.audio.fx.all as afx
import moviepy.video.fx.all as vfx
import numpy as np
from _appmanager import get_executable
from _shutil import format_time, get_time_str, getch, print2
from moviepy.config import change_settings
from moviepy.editor import *
from open_with.open_with import open_with

import codeapi
import core
import coreapi
import datastruct

SCRIPT_ROOT = os.path.dirname(os.path.abspath(__file__))

ignore_undefined = False

if 1:
    change_settings({"FFMPEG_BINARY": get_executable("ffmpeg")})


# def _get_markers(file):
#     marker_file = file + ".marker.txt"
#     if os.path.exists(marker_file):
#         with open(marker_file, "r") as f:
#             s = f.read()
#             return [float(x) for x in s.split()]
#     else:
#         return None


# def _load_and_expand_img(f):
#     fg = Image.open(f).convert("RGBA")
#     bg = Image.new("RGB", (1920, 1080))
#     bg.paste(fg, ((bg.width - fg.width) // 2, (bg.height - fg.height) // 2), fg)
#     return np.array(bg)


def _update_mpy_clip(
    clip,
    subclip,
    speed,
    frame,
    norm,
    loop,
    duration,
    pos,
    scale,
    vol,
    **kwargs,
):
    assert duration is not None

    # video clip operations / fx
    if subclip is not None:
        if isinstance(subclip, (int, float)):
            clip = clip.subclip(subclip).set_duration(duration)

        else:
            subclip_duration = subclip[1] - subclip[0]
            if duration > subclip_duration:
                c1 = clip.subclip(subclip[0], subclip[1])
                c2 = clip.to_ImageClip(subclip[1]).set_duration(
                    duration - subclip_duration
                )
                clip = concatenate_videoclips([c1, c2])

                # HACK: workaround for a bug: 'CompositeAudioClip' object has no attribute 'fps'
                if clip.audio is not None:
                    clip = clip.set_audio(clip.audio.set_fps(44100))
            else:
                clip = clip.subclip(subclip[0], subclip[1]).set_duration(duration)

    if speed is not None:
        clip = clip.fx(
            # pylint: disable=maybe-no-member
            vfx.speedx,
            speed,
        )

    if frame is not None:
        clip = clip.to_ImageClip(frame).set_duration(duration)

    # Loop or change duration
    if loop:
        clip = clip.fx(
            # pylint: disable=maybe-no-member
            vfx.loop
        )

    if subclip is None:
        clip = clip.set_duration(duration)

    if pos is not None:
        # (x, y) marks the center location of the of the clip instead of the top
        # left corner.
        if pos == "center":
            clip = clip.set_position(("center", "center"))
        elif isinstance(pos, (list, tuple)):
            pos = list(pos)
            half_size = [x // 2 for x in clip.size]
            for i in range(2):
                if isinstance(pos[i], (int, float)):
                    pos[i] = pos[i] - half_size[i]
                    pos[i] = int(coreapi.global_scale * pos[i])
            clip = clip.set_position(pos)
        else:
            clip = clip.set_position(pos)

    if scale[0] != 1.0 or scale[1] != 1.0:
        clip = clip.resize((int(clip.w * scale[0]), int(clip.h * scale[1])))

    return clip


def _update_clip_duration(track):
    def is_connected(prev_clip, cur_clip):
        return math.isclose(
            prev_clip.start + prev_clip.duration,
            cur_clip.start,
            rel_tol=1e-3,
        )

    prev_clip_info = None
    for clip_info in track:
        if prev_clip_info is not None:
            if prev_clip_info.auto_extend:
                prev_clip_info.duration = clip_info.start - prev_clip_info.start
                prev_clip_info.auto_extend = False
                assert prev_clip_info.duration > 0

            # Apply fadeout to previous clip if it's not connected with
            # current clip.
            if prev_clip_info.crossfade > 0 and not is_connected(
                prev_clip_info, clip_info
            ):
                prev_clip_info.fadeout = prev_clip_info.crossfade

        prev_clip_info = clip_info

    # Update last clip duration
    if prev_clip_info is not None:
        if prev_clip_info.auto_extend:
            duration = prev_clip_info.duration

            # Extend the last video clip to match the voice track
            if "re" in coreapi.pos_dict:
                duration = max(duration, coreapi.pos_dict["re"] - clip_info.start)

            prev_clip_info.duration = duration
            prev_clip_info.auto_extend = False

        if prev_clip_info.crossfade > 0:
            prev_clip_info.fadeout = prev_clip_info.crossfade


def _export_video(*, resolution, audio_only):
    resolution = [int(x * coreapi.global_scale) for x in resolution]

    audio_clips = []

    # Update clip duration for each track
    for track in datastruct.video_tracks.values():
        _update_clip_duration(track)

    # TODO: post-process video track clips

    # Update MoviePy clip object in each track.
    video_clips = []
    for track_name, track in datastruct.video_tracks.items():
        for i, clip_info in enumerate(track):
            assert clip_info.mpy_clip is not None
            assert clip_info.duration is not None

            # Unlink audio clip from video clip (adjust audio duration)
            if clip_info.no_audio:
                clip_info.mpy_clip = clip_info.mpy_clip.set_audio(None)

            elif clip_info.mpy_clip.audio is not None:
                audio_clip = clip_info.mpy_clip.audio
                clip_info.mpy_clip = clip_info.mpy_clip.set_audio(None)

                # Audio timing
                # TODO: audio subclip
                if clip_info.subclip is not None:
                    duration = clip_info.subclip[1] - clip_info.subclip[0]
                    audio_clip = audio_clip.subclip(
                        clip_info.subclip[0], clip_info.subclip[1]
                    )
                else:
                    duration = clip_info.duration
                    duration = min(duration, audio_clip.duration)
                    audio_clip = audio_clip.set_duration(duration)
                audio_clip = audio_clip.set_start(clip_info.start)

                # Adjust volume
                if clip_info.norm:
                    audio_clip = audio_clip.fx(
                        # pylint: disable=maybe-no-member
                        afx.audio_normalize
                    )
                if clip_info.vol is not None:
                    if isinstance(clip_info.vol, (int, float)):
                        audio_clip = audio_clip.fx(
                            # pylint: disable=maybe-no-member
                            afx.volumex,
                            clip_info.vol,
                        )
                    else:
                        audio_clip = _adjust_mpy_audio_clip_volume(
                            audio_clip, clip_info.vol
                        )

                audio_clips.append(audio_clip)

            # If the next clip has crossfade enabled
            crossfade_duration = track[i + 1].crossfade if (i < len(track) - 1) else 0
            if crossfade_duration:
                # clip_info.fadeout = crossfade_duration  # Fadeout current clip
                clip_info.duration += crossfade_duration

            clip_info.mpy_clip = _update_mpy_clip(clip_info.mpy_clip, **vars(clip_info))

            # Deal with video fade in / out / crossfade
            if clip_info.fadein:
                assert isinstance(clip_info.fadein, (int, float))
                # TODO: crossfadein and crossfadeout is very slow in moviepy
                if track_name != "vid":
                    clip_info.mpy_clip = clip_info.mpy_clip.crossfadein(
                        clip_info.fadein
                    )
                else:
                    clip_info.mpy_clip = clip_info.mpy_clip.fx(
                        # pylint: disable=maybe-no-member
                        vfx.fadein,
                        clip_info.fadein,
                    )

            elif (
                clip_info.crossfade > 0
            ):  # crossfade and fadein should not happen at the same time
                video_clips.append(
                    clip_info.mpy_clip.set_duration(clip_info.crossfade)
                    .crossfadein(clip_info.crossfade)
                    .set_start(clip_info.start)
                )

                clip_info.mpy_clip = clip_info.mpy_clip.subclip(clip_info.crossfade)
                clip_info.start += clip_info.crossfade

            if clip_info.fadeout:
                assert isinstance(clip_info.fadeout, (int, float))
                if track_name != "vid":
                    # pylint: disable=maybe-no-member
                    clip_info.mpy_clip = clip_info.mpy_clip.crossfadeout(
                        clip_info.fadeout
                    )
                else:

                    clip_info.mpy_clip = clip_info.mpy_clip.fx(
                        # pylint: disable=maybe-no-member
                        vfx.fadeout,
                        clip_info.fadeout,
                    )

            video_clips.append(clip_info.mpy_clip.set_start(clip_info.start))

    if len(video_clips) == 0:
        video_clips.append(ColorClip((200, 200), color=(0, 1, 0)).set_duration(2))
        # raise Exception("no video clips??")
    final_clip = CompositeVideoClip(video_clips, size=resolution)

    # Resize here is too late, does not speed up the video encoding at all.
    # final_clip = final_clip.resize(width=480)

    # Deal with audio clips
    for _, track in datastruct.audio_tracks.items():
        clips = []
        for clip_info in track.clips:
            if clip_info.loop:
                # HACK: reload the clip.
                #
                # still don't know why using loaded mpy_clip directly will cause
                # "IndexError: index -200001 is out of bounds for axis 0 with
                # size 0"...
                clip = AudioFileClip(clip_info.file, buffersize=400000)
            else:
                clip = clip_info.mpy_clip

            if clip_info.subclip is not None:
                clip = clip.subclip(clip_info.subclip[0], clip_info.subclip[1])

            duration = clip_info.duration
            if duration is not None:
                if clip_info.loop:
                    # pylint: disable=maybe-no-member
                    clip = clip.fx(afx.audio_loop, duration=duration)
                else:
                    duration = min(duration, clip.duration)
                    if clip_info.subclip:
                        duration = min(
                            duration, clip_info.subclip[1] - clip_info.subclip[0]
                        )
                    clip = clip.set_duration(duration)

            if clip_info.start is not None:
                clip = clip.set_start(clip_info.start)

            # Adjust volume by keypoints
            if len(clip_info.vol_keypoints) > 0:
                clip = _adjust_mpy_audio_clip_volume(clip, clip_info.vol_keypoints)

            clips.append(clip)

        if len(clips) > 0:
            clip = CompositeAudioClip(clips)
            audio_clips.append(clip)

    if final_clip.audio:
        audio_clips.append(final_clip.audio)

    if len(audio_clips) > 0:
        final_audio_clip = CompositeAudioClip(audio_clips)

        # XXX: Workaround for exception: 'CompositeAudioClip' object has no attribute 'fps'.
        # See: https://github.com/Zulko/moviepy/issues/863
        # final_audio_clip.fps = 44100

        final_clip = final_clip.set_audio(final_audio_clip)

    # final_clip.show(10.5, interactive=True)

    os.makedirs("tmp/out", exist_ok=True)

    if audio_only:
        final_audio_clip.fps = 44100
        final_audio_clip.write_audiofile("%s.mp3" % out_filename)
        open_with("%s.mp3" % out_filename, program_id=0)

    else:
        final_clip.write_videofile(
            "%s.mp4" % out_filename,
            temp_audiofile="%s.mp3" % out_filename,
            remove_temp=False,
            codec="libx264",
            threads=8,
            fps=coreapi.FPS,
            ffmpeg_params=["-crf", "19"],
        )

        subprocess.Popen(
            ["mpv", "--force-window", "--geometry=1920x1080", f"{out_filename}.mp4"],
            close_fds=True,
        )


def _adjust_mpy_audio_clip_volume(clip, vol_keypoints):
    xp = []
    fp = []

    print("vol_keypoints:", vol_keypoints)
    for (p, vol) in vol_keypoints:
        if isinstance(vol, (int, float)):
            xp.append(p)
            fp.append(vol)
        else:
            raise Exception("unsupported bgm parameter type:" % type(vol))

    def volume_adjust(gf, t):
        factor = np.interp(t, xp, fp)
        factor = np.vstack([factor, factor]).T
        return factor * gf(t)

    return clip.fl(volume_adjust)


# def _export_srt():
#     with open("out.srt", "w", encoding="utf-8") as f:
#         f.write("\n".join(_srt_lines))


def _convert_to_readable_time(seconds):
    seconds = int(seconds)
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60

    if hour > 0:
        return "%d:%02d:%02d" % (hour, minutes, seconds)
    else:
        return "%02d:%02d" % (minutes, seconds)


def _write_timestamp(t, section_name):
    os.makedirs(os.path.dirname(out_filename), exist_ok=True)

    if not hasattr(_write_timestamp, "f"):
        _write_timestamp.f = open("%s.txt" % out_filename, "w", encoding="utf-8")

    _write_timestamp.f.write("%s (%s)\n" % (section_name, _convert_to_readable_time(t)))
    _write_timestamp.f.flush()


@core.api
def include(file):
    with open(file, "r", encoding="utf-8") as f:
        s = f.read()

    cwd = os.getcwd()
    os.chdir(os.path.dirname(os.path.abspath(file)))
    _parse_text(s)
    os.chdir(cwd)


def _remove_unused_recordings(s):
    used_recordings = set()
    unused_recordings = []

    apis = {"record": (lambda f, **kargs: used_recordings.add(f))}
    _parse_text(s, apis=apis)

    files = [f for f in glob.glob("record/*") if os.path.isfile(f)]
    files = [f.replace("\\", "/") for f in files]

    for f in files:
        if f not in used_recordings:
            unused_recordings.append(f)

    print2("Used   : %d" % len(used_recordings), color="green")
    print2("Unused : %d" % len(unused_recordings), color="red")
    assert len(used_recordings) + len(unused_recordings) == len(files)
    print("Press y to clean up: ", end="", flush=True)
    if getch() == "y":
        for f in unused_recordings:
            try:
                os.remove(f)
            except:
                print("WARNING: failed to remove: %s" % f)


def _parse_text(text, apis=core.apis, **kwargs):
    def find_next(text, needle, p):
        pos = text.find(needle, p)
        if pos < 0:
            pos = len(text)
        return pos

    # Remove all comments
    text = re.sub(r"<!--[\d\D]*?-->", "", text)

    p = 0  # Current position
    while p < len(text):
        if text[p : p + 2] == "{{":
            end = find_next(text, "}}", p)
            python_code = text[p + 2 : end].strip()
            p = end + 2

            if ignore_undefined:
                try:
                    exec(python_code, apis)
                except NameError:  # API is not defined
                    pass  # simply ignore
            else:
                exec(python_code, apis)

            continue

        if text[p : p + 1] == "#":
            end = find_next(text, "\n", p)

            line = text[p:end].strip()
            _write_timestamp(coreapi.pos_dict["a"], line)

            p = end + 1
            continue

        match = re.match("---((?:[0-9]*[.])?[0-9]+)?\n", text[p:])
        if match is not None:
            if match.group(1) is not None:
                coreapi.audio_gap(float(match.group(1)))
            else:
                coreapi.audio_gap(0.2)
            p += match.end(0) + 1
            continue

        # Parse regular text
        end = find_next(text, "\n", p)
        line = text[p:end].strip()
        p = end + 1

        if line != "" and "parse_line" in apis:
            apis["parse_line"](line)

    # Call it at the end
    core.on_api_func(None)


def _show_stats(s):
    TIME_PER_CHAR = 0.1334154351395731

    total = 0

    def parse_line(line):
        nonlocal total
        total += len(line)

    _parse_text(s, apis={"parse_line": parse_line}, ignore_undefined=True)

    total_secs = TIME_PER_CHAR * total
    print("Estimated Time: %s" % format_time(total_secs))

    input()


def load_config():
    import yaml

    CONFIG_FILE = "config.yaml"
    DEFAULT_CONFIG = {"fps": 30}

    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            config = yaml.load(f.read(), Loader=yaml.FullLoader)
    else:
        with open(CONFIG_FILE, "w", newline="\n") as f:
            yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False)
        config = DEFAULT_CONFIG

    coreapi.fps(config["fps"])


if __name__ == "__main__":
    out_filename = "tmp/out/" + get_time_str()

    parser = argparse.ArgumentParser()
    parser.add_argument("--stdin", default=False, action="store_true")
    parser.add_argument("--proj_dir", type=str, default=None)
    parser.add_argument("-i", "--input", type=str, default=None)
    parser.add_argument("-a", "--audio_only", action="store_true", default=False)
    parser.add_argument(
        "--remove_unused_recordings", action="store_true", default=False
    )
    parser.add_argument("--show_stats", action="store_true", default=False)
    parser.add_argument("--preview", action="store_true", default=False)

    args = parser.parse_args()

    if args.proj_dir is not None:
        os.chdir(args.proj_dir)
    elif args.input:
        os.chdir(os.path.dirname(args.input))
    print("Project dir: %s" % os.getcwd())

    # Load custom APIs (api.py) if exists
    if os.path.exists("api.py"):
        sys.path.append(os.getcwd())
        mymodule = importlib.import_module("api")
        global_functions = inspect.getmembers(mymodule, inspect.isfunction)
        core.apis.update({k: v for k, v in global_functions})

    # HACK
    if args.audio_only:
        coreapi.audio_only()

    # Read text
    if args.stdin:
        s = sys.stdin.read()

    elif args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            s = f.read()

    else:
        raise Exception("Either --stdin or --input should be specified.")

    load_config()

    if args.preview:
        coreapi.preview()

    if args.remove_unused_recordings:
        ignore_undefined = True
        _remove_unused_recordings(s)
    elif args.show_stats:
        ignore_undefined = True
        _show_stats(s)
    else:
        _parse_text(s, apis=core.apis)
        _export_video(resolution=(1920, 1080), audio_only=args.audio_only)
