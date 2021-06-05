import argparse
import datetime
import glob
import importlib
import inspect
import math
import os
import re
import subprocess
import sys
import tarfile
from typing import Dict, List

import moviepy.audio.fx.all as afx
import moviepy.video.fx.all as vfx
import numpy as np
from _appmanager import get_executable
from _shutil import call2, file_is_old, get_hash, get_time_str, getch, mkdir, print2
from audio.postprocess import dynamic_audio_normalize, process_audio_file
from moviepy.config import change_settings
from moviepy.editor import *
from open_with.open_with import open_with
from PIL import Image

import datastruct
from render_animation import render_animation
from render_text import render_text

SCRIPT_ROOT = os.path.dirname(os.path.abspath(__file__))

_add_subtitle = True
_global_scale = 1.0
_audio_only = False
_apis = {}
_cached_line_to_tts = None
_last_frame_indices: Dict[str, int] = {}

VOLUME_DIM = 0.15
FADE_DURATION = 0.2
VIDEO_CROSSFADE_DURATION = FADE_DURATION
AUTO_GENERATE_TTS = False
FPS = 30
IMAGE_SEQUENCE_FPS = FPS
DEFAULT_AUDIO_FADING_DURATION = 0.25
DEFAULT_IMAGE_CLIP_DURATION = 2

ignore_undefined = False

if 0:
    change_settings({"FFMPEG_BINARY": get_executable("ffmpeg")})


_pos_dict = {"c": 0, "a": 0, "as": 0, "ae": 0, "vs": 0, "ve": 0}
_subtitle: List[str] = []
_srt_lines = []
_srt_index = 1
_last_subtitle_index = -1
_crossfade = 0


_on_api = None


def on_api(func):
    global _on_api
    _on_api = func


def api(f):
    def api_wrapper(*args, **kwargs):
        _on_api(f.__name__)
        f(*args, **kwargs)

    _apis[f.__name__] = api_wrapper
    return api_wrapper


@on_api
def on_api_(func_name):
    print("%s()" % func_name)
    input("yoyo")

    if func_name != "record":
        _try_generate_tts()
    else:
        global _cached_line_to_tts
        _cached_line_to_tts = None


def _format_time(sec):
    td = datetime.timedelta(seconds=sec)
    return "%02d:%02d:%02d,%03d" % (
        td.seconds // 3600,
        td.seconds // 60,
        td.seconds % 60,
        td.microseconds // 1000,
    )


@api
def crossfade(v):
    global _crossfade
    if v == True:
        _crossfade = VIDEO_CROSSFADE_DURATION
    else:
        _crossfade = float(v)


def _get_markers(file):
    marker_file = file + ".marker.txt"
    if os.path.exists(marker_file):
        with open(marker_file, "r") as f:
            s = f.read()
            return [float(x) for x in s.split()]
    else:
        return None


def _get_time(p):
    if isinstance(p, (int, float)):
        return p

    PATT_NUMBER = r"[+-]?(?:[0-9]*[.])?[0-9]+"

    if p is None:
        return _pos_dict["c"]

    if type(p) == int or type(p) == float:
        return float(p)

    if type(p) == str:
        if p in _pos_dict:
            return _pos_dict[p]

        match = re.match(r"^([a-z_]+)(" + PATT_NUMBER + ")$", p)
        if match:
            tag = match.group(1)
            assert match.group(2)
            delta = float(match.group(2))
            return _pos_dict[tag] + delta

    raise Exception("Invalid pos='%s'" % p)


def _set_pos(t, tag=None):
    t = _get_time(t)

    if t != "c":
        _pos_dict["c"] = t

    if tag is not None:
        _pos_dict[tag] = t


def _add_subtitle_clip(start, end, text):
    temp_file = render_text(text)
    _add_video_clip(
        temp_file,
        t=start,
        duration=end - start,
        pos=("center", 910),
        track="text",
        crossfade=0,
        fadein=0,
        fadeout=0,
        move_playhead=False,
    )


@api
def record(
    f,
    t="a",
    postprocess=True,
    move_playhead=True,
    subtitle=True,
    subtitle_duration=None,
    **kwargs,
):
    if not os.path.exists(f):
        f = "record/" + f
        assert os.path.exists(f)

    # Post-process audio
    if postprocess:
        f = process_audio_file(f, out_dir="tmp/record")

    audio(f, t=t, move_playhead=move_playhead, **kwargs)

    if move_playhead:
        _pos_dict["re"] = _get_time("ae")
        _pos_dict["c"] = _get_time("as")

    END_CHARS = ["。", "，", "！", "、", "；", "？", "|"]

    global _srt_index
    global _last_subtitle_index

    if _add_subtitle and subtitle and not _audio_only:
        if len(_subtitle) == 0:
            print("WARNING: no subtitle found")

        else:
            idx = len(_subtitle) - 1
            if _last_subtitle_index == idx:
                print2("WARNING: subtitle used twice: %s" % _subtitle[idx])
            else:
                _last_subtitle_index = idx

                start = end = _get_time("as")
                subtitle = _subtitle[idx].strip()

                if subtitle[-1] not in END_CHARS:
                    subtitle += END_CHARS[0]

                length = len(subtitle)
                if subtitle_duration is not None:
                    word_dura = subtitle_duration / length
                else:
                    word_dura = (_get_time("ae") - start) / length

                i = 0
                MAX = 5
                word = ""

                while i < length:
                    if subtitle[i] in END_CHARS and len(word) > MAX:
                        _srt_lines.extend(
                            [
                                "%d" % _srt_index,
                                "%s --> %s" % (_format_time(start), _format_time(end)),
                                word,
                                "",
                            ]
                        )

                        _add_subtitle_clip(start=start, end=end, text=word)

                        end += word_dura
                        start = end
                        word = ""
                        _srt_index += 1
                    else:
                        word += subtitle[i]
                        end += word_dura

                    i += 1


@api
def audio_gap(duration):
    _pos_dict["a"] += duration
    _pos_dict["ae"] = _pos_dict["as"] = _pos_dict["a"]
    _pos_dict["c"] = _pos_dict["a"]


def _set_vol(vol, duration=0, track=None, t=None):
    """Set volume of a specific track at a given time. Returns previous volume."""

    assert duration >= 0

    t = _get_time(t)

    print("change vol=%.2f  at=%.2f  duration=%.2f" % (vol, t, duration))
    track_ = datastruct.get_audio_track(track)
    if len(track_.clips) == 0:
        print2("WARNING: No audio clip to set volume in track: %s" % track)
        return

    t_in_clip = t - track_.clips[-1].start
    assert t_in_clip >= 0

    # Add keypoints
    if len(track_.clips[-1].vol_keypoints) > 0:  # has previous keypoint
        _, prev_vol = track_.clips[-1].vol_keypoints[-1]
        track_.clips[-1].vol_keypoints.append((t_in_clip, prev_vol))
    else:
        prev_vol = vol

    track_.clips[-1].vol_keypoints.append((t_in_clip + duration, vol))

    return prev_vol


@api
def setp(name, t=None):
    t = _get_time(t)
    _pos_dict[name] = t


@api
def vol(vol, duration=DEFAULT_AUDIO_FADING_DURATION, **kwargs):
    return _set_vol(vol, duration=duration, **kwargs)


@api
def bgm_vol(vol, duration=DEFAULT_AUDIO_FADING_DURATION, **kwawgs):
    _set_vol(vol, duration=duration, track="bgm", **kwawgs)


def _add_audio_clip(
    file,
    track=None,
    t=None,
    subclip=None,
    duration=None,
    move_playhead=True,
    loop=False,
):
    clips = datastruct.get_audio_track(track).clips

    t = _get_time(t)

    if move_playhead:
        _pos_dict["as"] = t

    clip_info = datastruct.AudioClip()

    if not os.path.exists(file):
        raise Exception("Please make sure `%s` exists." % file)
    clip_info.file = os.path.abspath(file)

    # HACK: still don't know why changing buffersize would help reduce the noise at the end
    clip_info.mpy_clip = AudioFileClip(file, buffersize=400000)

    if subclip is not None:
        clip_info.subclip = subclip
    else:
        clip_info.subclip = None

    clip_info.duration = None
    clip_info.start = t
    clip_info.loop = loop

    if move_playhead:
        # Forward audio track pos
        _pos_dict["c"] = _pos_dict["a"] = _pos_dict["ae"] = _pos_dict["as"] + (
            clip_info.mpy_clip.duration
            if clip_info.duration is None
            else clip_info.duration
        )

    clips.append(clip_info)

    return clip_info


@api
def audio(
    f,
    t=None,
    crossfade=0,
    fadein=0,
    fadeout=0,
    vol=1,
    track=None,
    move_playhead=True,
    solo=False,
    **kwargs,
):
    t = _get_time(t)

    if solo:
        prev_vol = _set_vol(0, track="bgm", t=t)

    audio_end(
        track=track,
        t=t,
        move_playhead=move_playhead,
        fadeout=fadeout,
        crossfade=crossfade,
    )

    clip = _add_audio_clip(f, t=t, track=track, move_playhead=move_playhead, **kwargs)

    if crossfade > 0:  # Crossfade in
        clip.vol_keypoints.append((0, 0))
        clip.vol_keypoints.append((crossfade, vol))
    elif fadein > 0:  # fade in
        clip.vol_keypoints.append((0, 0))
        clip.vol_keypoints.append((fadein, vol))
    else:
        clip.vol_keypoints.append((0, vol))

    if solo:
        _set_vol(prev_vol, track="bgm", t=clip.start + clip.mpy_clip.duration)


@api
def audio_end(track, t=None, move_playhead=True, fadeout=0, crossfade=0):
    t = _get_time(t)

    clips = datastruct.get_audio_track(track).clips
    if len(clips) == 0:
        print2("WARNING: no previous audio clip to set the end point.")
        return

    # Fade out of previous audio clip
    duration = None
    if len(datastruct.get_audio_track(track).clips) > 0:
        if crossfade > 0:  # Crossfade out
            _set_vol(0, duration=crossfade, t=t, track=track)
            duration = (t + crossfade) - clips[-1].start  # extend prev clip
        elif fadeout > 0:  # Fade out
            _set_vol(0, duration=fadeout, t=t - fadeout, track=track)
            duration = t - clips[-1].start
        else:
            duration = t - clips[-1].start

    if duration is not None and clips[-1].duration is None:
        assert duration > 0
        clips[-1].duration = duration
        print2("previous clip(%s) duration updated: %.2f" % (clips[-1].file, duration))

    if move_playhead:
        _pos_dict["c"] = _pos_dict["a"] = t


@api
def bgm(
    f, move_playhead=False, vol=0.1, track="bgm", norm=True, loop=True, **kwargs,
):
    print("bgm: %s" % f)

    if norm:
        f = dynamic_audio_normalize(f)

    audio(
        f, track=track, move_playhead=move_playhead, loop=loop, vol=vol, **kwargs,
    )


@api
def sfx(f, **kwargs):
    audio(f, track="sfx", move_playhead=False, **kwargs)


@api
def pos(t="c", tag=None):
    _set_pos(t, tag=tag)


@api
def clip(f, **kwargs):
    print("clip: %s" % f)
    _add_video_clip(f, **kwargs)


@api
def fps(v):
    global FPS
    FPS = v


@api
def overlay(
    f,
    duration=3,
    crossfade=VIDEO_CROSSFADE_DURATION,
    fadeout=VIDEO_CROSSFADE_DURATION,
    track="overlay",
    **kwargs,
):
    print("image: %s" % f)
    _add_video_clip(
        f,
        duration=duration,
        crossfade=crossfade,
        fadeout=fadeout,
        track=track,
        **kwargs,
    )


@api
def comment(text, pos=(960, 100), duration=4, track="overlay", **kwargs):
    md(
        text, pos=pos, duration=duration, track=track, **kwargs,
    )


@api
def credit(text, pos=(960, 40), duration=4, track="overlay", **kwargs):
    md(
        '<span style="font-size:0.6em">%s</span>' % text,
        pos=pos,
        duration=duration,
        track=track,
        **kwargs,
    )


@api
def codef(
    file,
    track="vid",
    size=None,
    jump_line=None,
    fontsize=None,
    mark_line=None,
    **kwargs,
):
    from web.gen_code_image import gen_code_image_from_file

    mkdir("tmp/code")
    hash = get_hash(
        str((file, os.path.getmtime(file), size, jump_line, fontsize, mark_line))
    )
    out_file = "tmp/code/%s.png" % hash
    if not os.path.exists(out_file):
        gen_code_image_from_file(
            file,
            out_file,
            size=size,
            jump_line=jump_line,
            fontsize=fontsize,
            mark_line=mark_line,
        )

    _add_video_clip(out_file, track=track, transparent=False, **kwargs)

    return out_file


def _create_image_seq_clip(tar_file):
    print("Load animation clip from %s" % tar_file)
    image_files = []
    t = tarfile.open(tar_file, "r")
    for member in t.getmembers():
        with t.extractfile(member) as fp:
            im = Image.open(fp)
            image_files.append(np.array(im))

    clip = ImageSequenceClip(image_files, fps=IMAGE_SEQUENCE_FPS)
    return clip


def _load_and_expand_img(f):
    fg = Image.open(f).convert("RGBA")
    bg = Image.new("RGB", (1920, 1080))
    bg.paste(fg, ((bg.width - fg.width) // 2, (bg.height - fg.height) // 2), fg)
    return np.array(bg)


def _get_video_resolution(f):
    resolution = (
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height",
                "-of",
                "csv=s=x:p=0",
                f,
            ]
        )
        .decode()
        .strip()
        .split("x")
    )
    resolution = [int(x) for x in resolution]
    return resolution


def _load_mpy_clip(
    file,
    scale=(1.0, 1.0),
    frame=None,
    transparent=True,
    width=None,
    height=None,
    **kwargs,
):
    def update_clip_size(clip):
        if not width and not height:
            return clip
        else:
            return clip.resize(width=width, height=height)

    def compute_size(w, h):
        aspect = w / h
        if not width and height:
            h = height
            w = height * aspect
        elif width and not height:
            w = width
            h = width / aspect
        elif width and height:
            w = width
            h = height
        return (w, h)

    def load_video_file_clip(f):
        nonlocal scale

        # Have ffmpeg resize the frames before returning them - faster speed.
        if scale[0] != 1.0 or scale[1] != 1.0:
            w, h = _get_video_resolution(f)
            w, h = compute_size(w, h)
            target_resolution = [int(h * scale[0]), int(w * scale[1])]
        else:
            target_resolution = None

        return VideoFileClip(f, target_resolution=target_resolution)

    if file is None:
        clip = ColorClip((200, 200), color=(0, 0, 0)).set_duration(2)

    elif file.endswith(".tar"):
        clip = _create_image_seq_clip(file)

    elif file.endswith(".pptx"):
        from ppt.export_ppt import export_slide, export_video

        if frame is None:
            file = export_video(file)
            clip = load_video_file_clip(file)
        else:
            export_shapes = bool(re.search(r"\boverlay[\\/]", file))
            file = export_slide(file, index=frame, export_shapes=export_shapes)
            clip = (
                ImageClip(file).set_duration(DEFAULT_IMAGE_CLIP_DURATION).set_mask(None)
            )
            clip = update_clip_size(clip)

    elif file.endswith(".png") or file.endswith(".jpg"):
        clip = ImageClip(file)
        clip = update_clip_size(clip)

        clip = clip.set_duration(DEFAULT_IMAGE_CLIP_DURATION)
        if not transparent:
            clip = clip.set_mask(None)

    else:
        clip = load_video_file_clip(file)

    return clip


def _update_mpy_clip(
    clip, subclip, speed, frame, norm, loop, duration, pos, scale, vol, **kwargs,
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
                    pos[i] = int(_global_scale * pos[i])
            clip = clip.set_position(pos)
        else:
            clip = clip.set_position(pos)

    if scale[0] != 1.0 or scale[1] != 1.0:
        clip = clip.resize((int(clip.w * scale[0]), int(clip.h * scale[1])))

    return clip


def _add_video_clip(
    file=None,
    speed=None,
    pos="center",
    track=None,
    fadein=0,
    fadeout=0,
    crossfade=None,
    cf=None,
    t=None,
    duration=None,
    transparent=True,
    move_playhead=True,
    no_audio=False,
    na=False,
    norm=False,
    vol=None,
    subclip=None,
    frame=None,
    n=None,
    loop=False,
    expand=False,
    scale=(1.0, 1.0),
    width=None,
    height=None,
):
    clip_info = datastruct.VideoClip()

    # Alias
    if n is not None:
        frame = n
    if cf is not None:
        crossfade = cf

    # Extract only one frame
    if frame is not None:
        if frame == "next":
            frame = _last_frame_indices[file] + 1
        if type(frame) != int:
            raise Exception("Invalid frame val.")
        _last_frame_indices[file] = frame
    clip_info.frame = frame

    if isinstance(scale, (int, float)):
        scale = (scale, scale)

    # TODO:
    if track is None or track == "vid":
        transparent = False

    track = datastruct.get_vid_track(track)
    t = _get_time(t)

    if move_playhead:
        _pos_dict["vs"] = t

    clip_info.file = os.path.abspath(file)
    clip_info.start = t
    clip_info.pos = pos
    clip_info.speed = speed

    # Crossfade / fadein / fadeout
    # Note that crossfade and fadein can not be specified at the same time.
    if fadein:
        clip_info.fadein = fadein
    else:
        if crossfade is not None:
            clip_info.crossfade = crossfade
        elif _crossfade:
            clip_info.crossfade = _crossfade
    clip_info.fadeout = fadeout

    if duration is not None:
        clip_info.auto_extend = False

    clip_info.no_audio = no_audio or na
    clip_info.norm = norm
    clip_info.vol = vol
    clip_info.transparent = transparent
    clip_info.subclip = subclip
    clip_info.loop = loop
    clip_info.expand = expand
    clip_info.scale = (scale[0] * _global_scale, scale[1] * _global_scale)
    clip_info.width = width
    clip_info.height = height

    # Load mpy clip
    clip_info.mpy_clip = _load_mpy_clip(**vars(clip_info))
    if type(clip_info.mpy_clip) == VideoFileClip:
        clip_info.scale = scale  # HACK

    # Duration
    if duration is None:
        if subclip:
            if isinstance(subclip, (int, float)):
                duration = clip_info.mpy_clip.duration - subclip
            else:
                duration = subclip[1] - subclip[0]
        else:
            duration = clip_info.mpy_clip.duration
    else:
        duration = duration
    clip_info.duration = duration

    if move_playhead:  # Advance the pos
        end = t + duration
        _pos_dict["c"] = _pos_dict["ve"] = end

    while len(track) > 0 and clip_info.start < track[-1].start:
        print("WARNING: clip `%s` has been removed" % track[-1].file)
        track.pop()

    track.append(clip_info)

    return clip_info


@api
def anim(file, **kwargs):
    video_file = os.path.splitext(file)[0] + ".webm"
    if file_is_old(file, video_file):
        if os.path.exists(video_file):
            os.remove(video_file)
        render_animation(os.path.abspath(file))
    _add_video_clip(video_file, **kwargs)


@api
def video_end(track=None, t=None, fadeout=None):
    print("video_end: track=%s" % track)
    track = datastruct.get_vid_track(track)

    assert len(track) > 0

    clip = track[-1]
    clip.duration = _get_time(t) - clip.start
    clip.auto_extend = False

    if fadeout is not None:
        clip.fadeout = fadeout

    print("clip updated: start=%.2f duration=%.2f" % (clip.start, clip.duration))


@api
def empty(**kwargs):
    _add_video_clip(None, **kwargs)


def generate_slide(in_file, template, out_file=None):
    call2(
        [
            "run_script",
            "/r/videoedit/slide/export.js",
            "-i",
            os.path.realpath(in_file),
            "-o",
            os.path.realpath(out_file),
            "-t",
            template,
        ]
    )


@api
def slide(
    s, template, pos="center", name=None, **kwargs,
):
    mkdir("tmp/md")
    hash = get_hash(s)
    in_file = "tmp/md/%s.md" % hash
    out_file = "tmp/md/%s.png" % hash

    if not os.path.exists(out_file):
        with open(in_file, "w", encoding="utf-8") as f:
            f.write(s)

        generate_slide(in_file, template=template, out_file=out_file)

    _add_video_clip(out_file, pos=pos, **kwargs)


@api
def md(s, track="md", move_playhead=False, **kwargs):
    slide(
        s,
        track=track,
        template="markdown",
        crossfade=VIDEO_CROSSFADE_DURATION,
        move_playhead=move_playhead,
        **kwargs,
    )


@api
def hl(pos=None, rect=None, track="hl", duration=2, file=None, **kwargs):
    # "../assets/animation/click.tar",

    extra_args = {
        "track": track,
        "fadein": VIDEO_CROSSFADE_DURATION,
        "fadeout": VIDEO_CROSSFADE_DURATION,
        "duration": duration,
        "move_playhead": False,
        **kwargs,
    }

    if pos is not None:
        if file is None:
            file = SCRIPT_ROOT + "/assets/mouse-cursor.png"
        _add_video_clip(file=file, pos=pos, **extra_args)
    elif rect is not None:
        _add_video_clip(
            file=SCRIPT_ROOT + "/assets/highlight-yellow.png",
            pos=(rect[0] + 50, rect[1] + 50),
            scale=(rect[2] / 100, rect[3] / 100),
            **extra_args,
        )


def _update_clip_duration(track):
    def is_connected(prev_clip, cur_clip):
        return math.isclose(
            prev_clip.start + prev_clip.duration, cur_clip.start, rel_tol=1e-3,
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
            if "re" in _pos_dict:
                duration = max(duration, _pos_dict["re"] - clip_info.start)

            prev_clip_info.duration = duration
            prev_clip_info.auto_extend = False

        if prev_clip_info.crossfade > 0:
            prev_clip_info.fadeout = prev_clip_info.crossfade


def _export_video(resolution=(1920, 1080)):
    resolution = [int(x * _global_scale) for x in resolution]

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

    if _audio_only:
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
            fps=FPS,
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


def _export_srt():
    with open("out.srt", "w", encoding="utf-8") as f:
        f.write("\n".join(_srt_lines))


def _tts_to_wav_google(out_file, text):
    tmp_file = "tmp/tts/%s_gtts.mp3" % hash
    call2(["gtts-cli", text, "--lang", "zh-cn", "--nocheck", "--output", tmp_file])
    call2(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "panic",
            "-i",
            tmp_file,
            "-filter:a",
            "atempo=1.75",
            "-vn",
            out_file,
        ]
    )
    os.remove(tmp_file)


def _tts_to_wav_microsoft(out_file, text):
    subprocess.check_call(
        [
            "powershell",
            "-ExecutionPolicy",
            "unrestricted",
            "-File",
            os.path.join(SCRIPT_ROOT, "tts_to_wav.ps1"),
            out_file,
            text,
        ]
    )


def _try_generate_tts():
    if _cached_line_to_tts is None:
        return

    hash = get_hash(_cached_line_to_tts)

    mkdir("tmp/tts")
    out_file = "tmp/tts/%s.wav" % hash
    if not os.path.exists(out_file):
        print("generate tts file: %s" % out_file)

        _tts_to_wav_microsoft(out_file, _cached_line_to_tts)

    record(out_file, postprocess=False, vol=2)


@api
def tts(enabled=True):
    global AUTO_GENERATE_TTS
    AUTO_GENERATE_TTS = enabled


@api
def parse_line(line):
    print2(line, color="green")
    _subtitle.append(line)

    if AUTO_GENERATE_TTS:
        global _cached_line_to_tts
        _cached_line_to_tts = line


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


@api
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


def _parse_text(text, apis=_apis, **kwargs):
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
            _write_timestamp(_pos_dict["a"], line)

            p = end + 1
            continue

        match = re.match("---((?:[0-9]*[.])?[0-9]+)?\n", text[p:])
        if match is not None:
            if match.group(1) is not None:
                audio_gap(float(match.group(1)))
            else:
                audio_gap(0.2)
            p += match.end(0) + 1
            continue

        # Parse regular text
        end = find_next(text, "\n", p)
        line = text[p:end].strip()
        p = end + 1

        if line != "" and "parse_line" in apis:
            apis["parse_line"](line)

    # Call it at the end
    _on_api(None)


def _show_stats(s):
    TIME_PER_CHAR = 0.1334154351395731

    total = 0

    def parse_line(line):
        nonlocal total
        total += len(line)

    _parse_text(s, apis={"parse_line": parse_line}, ignore_undefined=True)

    total_secs = TIME_PER_CHAR * total
    print("Estimated Time: %s" % _format_time(total_secs))

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

    fps(config["fps"])


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
        _apis.update({k: v for k, v in global_functions})

    # HACK
    if args.audio_only:
        _audio_only = True
        _add_subtitle = False

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
        _add_subtitle = False
        _global_scale = 0.25
        tts(True)

    if args.remove_unused_recordings:
        ignore_undefined = True
        _remove_unused_recordings(s)
    elif args.show_stats:
        ignore_undefined = True
        _show_stats(s)
    else:
        _parse_text(s, apis=_apis)
        _export_video()
