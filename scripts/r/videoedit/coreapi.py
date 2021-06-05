import os
import re
import subprocess
import tarfile
from typing import Dict, List

import numpy as np
from _shutil import call2, file_is_old, format_time, get_hash, mkdir, print2, timing
from audio.postprocess import dynamic_audio_normalize, process_audio_file
from moviepy.editor import *
from PIL import Image

import core
import datastruct
from render_animation import render_animation
from render_text import render_text

SCRIPT_ROOT = os.path.dirname(os.path.abspath(__file__))

global_scale = 1.0
pos_dict = {"c": 0, "a": 0, "as": 0, "ae": 0, "vs": 0, "ve": 0}

VOLUME_DIM = 0.15
FADE_DURATION = 0.2
VIDEO_CROSSFADE_DURATION = FADE_DURATION
FPS = 30
IMAGE_SEQUENCE_FPS = FPS
DEFAULT_AUDIO_FADING_DURATION = 0.25
DEFAULT_IMAGE_CLIP_DURATION = 2

_enable_subtitle = True
_audio_only = False
_cached_line_to_tts = None
_last_frame_indices: Dict[str, int] = {}
_enable_tts = False
_subtitle: List[str] = []
_srt_lines = []
_srt_index = 1
_last_subtitle_index = -1
_crossfade = 0


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


@core.on_api
def on_api_(func_name):
    print("%s()" % func_name)

    if func_name != "record":
        _try_generate_tts()
    else:
        global _cached_line_to_tts
        _cached_line_to_tts = None


@core.api
def crossfade(v):
    global _crossfade
    if v == True:
        _crossfade = VIDEO_CROSSFADE_DURATION
    else:
        _crossfade = float(v)


def _get_time(p):
    if isinstance(p, (int, float)):
        return p

    PATT_NUMBER = r"[+-]?(?:[0-9]*[.])?[0-9]+"

    if p is None:
        return pos_dict["c"]

    if type(p) == int or type(p) == float:
        return float(p)

    if type(p) == str:
        if p in pos_dict:
            return pos_dict[p]

        match = re.match(r"^([a-z_]+)(" + PATT_NUMBER + ")$", p)
        if match:
            tag = match.group(1)
            assert match.group(2)
            delta = float(match.group(2))
            return pos_dict[tag] + delta

    raise Exception("Invalid pos='%s'" % p)


def _set_pos(t, tag=None):
    t = _get_time(t)

    if t != "c":
        pos_dict["c"] = t

    if tag is not None:
        pos_dict[tag] = t


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


@core.api
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
        pos_dict["re"] = _get_time("ae")
        pos_dict["c"] = _get_time("as")

    END_CHARS = ["。", "，", "！", "、", "；", "？", "|"]

    global _srt_index
    global _last_subtitle_index

    if _enable_subtitle and subtitle and not _audio_only:
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
                                "%s --> %s" % (format_time(start), format_time(end)),
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


@core.api
def audio_gap(duration):
    pos_dict["a"] += duration
    pos_dict["ae"] = pos_dict["as"] = pos_dict["a"]
    pos_dict["c"] = pos_dict["a"]


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


@core.api
def setp(name, t=None):
    t = _get_time(t)
    pos_dict[name] = t


@core.api
def vol(vol, duration=DEFAULT_AUDIO_FADING_DURATION, **kwargs):
    return _set_vol(vol, duration=duration, **kwargs)


@core.api
def bgm_vol(vol, duration=DEFAULT_AUDIO_FADING_DURATION, **kwawgs):
    _set_vol(vol, duration=duration, track="bgm", **kwawgs)


def _create_audio_file_clip(file):
    return AudioFileClip(file, buffersize=400000)


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
        pos_dict["as"] = t

    clip_info = datastruct.AudioClip()

    if not os.path.exists(file):
        raise Exception("Please make sure `%s` exists." % file)
    clip_info.file = os.path.abspath(file)

    # HACK: still don't know why changing buffersize would help reduce the noise at the end
    clip_info.mpy_clip = _create_audio_file_clip(file)

    if subclip is not None:
        clip_info.subclip = subclip
    else:
        clip_info.subclip = None

    clip_info.duration = None
    clip_info.start = t
    clip_info.loop = loop

    if move_playhead:
        # Forward audio track pos
        pos_dict["c"] = pos_dict["a"] = pos_dict["ae"] = pos_dict["as"] + (
            clip_info.mpy_clip.duration
            if clip_info.duration is None
            else clip_info.duration
        )

    clips.append(clip_info)

    return clip_info


@core.api
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


@core.api
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
        pos_dict["c"] = pos_dict["a"] = t


@core.api
def bgm(
    f, move_playhead=False, vol=0.1, track="bgm", norm=True, loop=True, **kwargs,
):
    print("bgm: %s" % f)

    if norm:
        f = dynamic_audio_normalize(f)

    audio(
        f, track=track, move_playhead=move_playhead, loop=loop, vol=vol, **kwargs,
    )


@core.api
def sfx(f, **kwargs):
    audio(f, track="sfx", move_playhead=False, **kwargs)


@core.api
def pos(t="c", tag=None):
    _set_pos(t, tag=tag)


@core.api
def clip(f, **kwargs):
    print("clip: %s" % f)
    _add_video_clip(f, **kwargs)


@core.api
def fps(v):
    global FPS
    FPS = v


@core.api
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


@core.api
def comment(text, pos=(960, 100), duration=4, track="overlay", **kwargs):
    md(
        text, pos=pos, duration=duration, track=track, **kwargs,
    )


@core.api
def credit(text, pos=(960, 40), duration=4, track="overlay", **kwargs):
    md(
        '<span style="font-size:0.6em">%s</span>' % text,
        pos=pos,
        duration=duration,
        track=track,
        **kwargs,
    )


@core.api
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
        pos_dict["vs"] = t

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
    clip_info.scale = (scale[0] * global_scale, scale[1] * global_scale)
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
        pos_dict["c"] = pos_dict["ve"] = end

    while len(track) > 0 and clip_info.start < track[-1].start:
        print("WARNING: clip `%s` has been removed" % track[-1].file)
        track.pop()

    track.append(clip_info)

    return clip_info


@core.api
def anim(file, **kwargs):
    video_file = os.path.splitext(file)[0] + ".webm"
    if file_is_old(file, video_file):
        if os.path.exists(video_file):
            os.remove(video_file)
        render_animation(os.path.abspath(file))
    _add_video_clip(video_file, **kwargs)


@core.api
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


@core.api
def empty(**kwargs):
    _add_video_clip(None, **kwargs)


def _generate_slide(in_file, template, out_file=None):
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


@core.api
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

        _generate_slide(in_file, template=template, out_file=out_file)

    _add_video_clip(out_file, pos=pos, **kwargs)


@core.api
def md(s, track="md", move_playhead=False, **kwargs):
    slide(
        s,
        track=track,
        template="markdown",
        crossfade=VIDEO_CROSSFADE_DURATION,
        move_playhead=move_playhead,
        **kwargs,
    )


@core.api
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


@core.api
def tts(enabled=True):
    global _enable_tts
    _enable_tts = enabled


@core.api
def parse_line(line):
    print2(line, color="green")
    _subtitle.append(line)

    if _enable_tts:
        global _cached_line_to_tts
        _cached_line_to_tts = line


@core.api
def audio_only():
    global _audio_only
    global _enable_subtitle

    _audio_only = True
    _enable_subtitle = False


@core.api
def preview():
    global _enable_subtitle
    global global_scale

    _enable_subtitle = False
    global_scale = 0.25
    tts(True)

