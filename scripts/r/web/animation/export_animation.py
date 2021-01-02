import argparse
import hashlib
import re
import tarfile
import urllib
import webbrowser
from collections import OrderedDict, defaultdict
from typing import Any, NamedTuple

import numpy as np
from PIL import Image

import capture_animation
from _appmanager import get_executable
from _shutil import *
from r.audio.postprocess import process_audio_file, dynamic_audio_normalize
from r.open_with.open_with_ import open_with
from slide.generate import generate_slide

SCRIPT_ROOT = os.path.dirname(os.path.abspath(__file__))

if 1:
    import os
    import sys

    sys.path.append(os.path.dirname(os.path.abspath(__file__)))


if 1:  # Import moviepy
    IMAGE_MAGICK = get_executable("magick")
    os.environ["IMAGEMAGICK_BINARY"] = IMAGE_MAGICK

    from moviepy.editor import *
    import moviepy.video.fx.all as vfx
    import moviepy.audio.fx.all as afx
    from moviepy.video.tools.subtitles import SubtitlesClip


_add_subtitle = False
_scale = 0.25
_audio_only = False
_impl = None

VOLUME_DIM = 0.15
FADE_DURATION = 0.2
AUTO_GENERATE_TTS = False
IMAGE_SEQUENCE_FPS = 25
FPS = 25
VIDEO_CROSSFADE_DURATION = FADE_DURATION
DEFAULT_AUDIO_FADING_DURATION = 0.25


if 0:
    from moviepy.config import change_settings

    change_settings({"FFMPEG_BINARY": get_executable("ffmpeg")})


class _VideoClipInfo:
    def __init__(self):
        self.file = None
        self.start = 0
        self.duration = None
        self.mpy_clip = None
        self.speed = 1
        self.pos = None
        self.fadein = False
        self.fadeout = False
        self.crossfade = False
        self.text_overlay = None

        self.no_audio = False
        self.norm = False
        self.vol = None
        self.transparent = True
        self.subclip = None
        self.frame = None
        self.loop = False
        self.expand = False
        self.scale = 1


class _AudioClipInfo:
    def __init__(self):
        self.file: str = None
        self.mpy_clip: Any = None
        self.speed: float = 1
        self.start: float = None
        self.subclip: float = None
        self.vol_keypoints = []
        self.loop = False


class _AudioTrack:
    def __init__(self):
        self.clips = []


class _AnimationInfo:
    def __init__(self):
        self.clip_info_list = []
        self.in_file = None
        self.calc_length = True
        self.url_params = {}
        self.overlay = False


_audio_track_cur_pos = 0
_pos_dict = {"c": 0, "a": 0, "as": 0, "ae": 0, "vs": 0, "ve": 0}


_add_fadeout_to_last_clip = False

_video_tracks = OrderedDict(
    [
        ("bg", []),
        ("vid", []),
        ("hl", []),
        ("hl2", []),
        ("md", []),
        ("overlay", []),
        ("text", []),
    ]
)
_cur_vid_track_name = "vid"  # default video track

_audio_tracks = OrderedDict(
    [
        ("bgm", _AudioTrack()),
        ("bgm2", _AudioTrack()),
        ("record", _AudioTrack()),
        ("sfx", _AudioTrack()),
    ]
)
_cur_audio_track_name = "record"

_animations = defaultdict(_AnimationInfo)

_subtitle = []
_srt_lines = []
_srt_index = 1
_last_subtitle_index = -1

_bgm_clip = None
_bgm = {}
_bgm_vol = []

_crossfade = 0


def _format_time(sec):
    td = datetime.timedelta(seconds=sec)
    return "%02d:%02d:%02d,%03d" % (
        td.seconds // 3600,
        td.seconds // 60,
        td.seconds % 60,
        td.microseconds // 1000,
    )


def crossfade(v):
    global _crossfade
    if v == True:
        _crossfade = VIDEO_CROSSFADE_DURATION
    else:
        _crossfade = float(v)


def _get_track(tracks, name):
    print("  track=%s" % name)

    if name not in tracks:
        raise Exception("track is not defined: %s" % name)
    track = tracks[name]

    return track


def _get_vid_track_name(name):
    if name is None:
        name = _cur_vid_track_name
    return name


def _get_vid_track(name=None):
    name = _get_vid_track_name(name)
    return _get_track(_video_tracks, name)


def _get_audio_track(name=None):
    if name is None:
        name = _cur_audio_track_name
    return _get_track(_audio_tracks, name)


def _get_markers(file):
    marker_file = file + ".marker.txt"
    if os.path.exists(marker_file):
        with open(marker_file, "r") as f:
            s = f.read()
            return [float(x) for x in s.split()]
    else:
        return None


def _get_pos(p):
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
    t = _get_pos(t)
    _pos_dict["c"] = t

    if tag is not None:
        _pos_dict[tag] = t


def _generate_text_image(
    text,
    font="Source-Han-Sans-CN-Medium",
    font_size=45,
    color="#ffffff",
    stroke_color="#000000",
):
    # Escape `%` in ImageMagick
    text = text.replace("\\*", "*").replace("\\", "\\\\").replace("%", "%%")

    # Generate subtitle png image using magick
    tempfile_fd, tempfilename = tempfile.mkstemp(suffix=".png")
    os.close(tempfile_fd)
    cmd = [
        IMAGE_MAGICK,
        "-background",
        "transparent",
        "-font",
        r"C:/Windows/Fonts/SourceHanSansSC-Bold.otf",
        "-pointsize",
        "%d" % font_size,
        "-stroke",
        stroke_color,
        "-strokewidth",
        "4",
        "-kerning",
        "%d" % int(font_size * 0.05),
        "-gravity",
        "center",
        "label:%s" % text,
        "-stroke",
        "None",
        "-fill",
        color,
        "label:%s" % text,
        "-layers",
        "merge",
        "PNG32:%s" % tempfilename,
    ]
    subprocess.check_call(cmd)
    return tempfilename


def _add_subtitle_clip(start, end, text):
    tempfilename = _generate_text_image(text)

    ci = _VideoClipInfo()
    ci.mpy_clip = (
        ImageClip(tempfilename).set_duration(end - start).set_pos(("center", 910))
    )
    ci.start = start
    ci.duration = end - start
    _video_tracks["text"].append(ci)


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
        _pos_dict["re"] = _get_pos("ae")
        _pos_dict["c"] = _get_pos("as")

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

                start = end = _get_pos("as")
                subtitle = _subtitle[idx].strip()

                if subtitle[-1] not in END_CHARS:
                    subtitle += END_CHARS[0]

                length = len(subtitle)
                if subtitle_duration is not None:
                    word_dura = subtitle_duration / length
                else:
                    word_dura = (_get_pos("ae") - start) / length

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


def audio_gap(duration):
    _pos_dict["a"] += duration
    _pos_dict["ae"] = _pos_dict["as"] = _pos_dict["a"]
    _pos_dict["c"] = _pos_dict["a"]


# Deprecated
def _set_vol(vol, duration=DEFAULT_AUDIO_FADING_DURATION, track=None, t=None):
    assert duration > 0

    t = _get_pos(t)

    print("change vol=%.2f  at=%.2f  duration=%.2f" % (vol, t, duration))
    track_ = _get_audio_track(track)
    if len(track_.clips) == 0:
        raise Exception("No audio clip to set volume in track: %s" % track)

    t_in_clip = t - track_.clips[-1].start
    assert t_in_clip >= 0

    # Add keypoints
    if len(track_.clips[-1].vol_keypoints) > 0:  # has previous keypoint
        _, prev_vol = track_.clips[-1].vol_keypoints[-1]
        track_.clips[-1].vol_keypoints.append((t_in_clip, prev_vol))
    track_.clips[-1].vol_keypoints.append((t_in_clip + duration, vol))


def mark(name, t=None):
    t = _get_pos(t)
    _pos_dict[name] = t


def vol(vol, **kwargs):
    _set_vol(vol, **kwargs)


def bgm_vol(v, **kwawgs):
    vol(v, track="bgm", **kwawgs)


def _add_audio_clip(
    file,
    track=None,
    t=None,
    subclip=None,
    duration=None,
    move_playhead=True,
    loop=False,
):
    clips = _get_audio_track(track).clips

    t = _get_pos(t)

    if move_playhead:
        _pos_dict["as"] = t

    clip_info = _AudioClipInfo()

    if not os.path.exists(file):
        raise Exception("Please make sure `%s` exists." % file)
    clip_info.file = os.path.abspath(file)

    # HACK: still don't know why changing buffersize would help reduce the noise at the end
    clip_info.mpy_clip = AudioFileClip(file, buffersize=400000)

    if subclip is not None:
        clip_info.duration = None
        clip_info.subclip = subclip
    else:
        clip_info.duration = None
        clip_info.subclip = None

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


def audio(
    f,
    crossfade=0,
    t=None,
    in_duration=0,
    out_duration=0,
    vol=1,
    track=None,
    move_playhead=True,
    **kwargs,
):
    t = _get_pos(t)

    audio_end(
        track=track,
        t=t,
        move_playhead=move_playhead,
        out_duration=out_duration,
        crossfade=crossfade,
    )

    clip = _add_audio_clip(f, t=t, track=track, move_playhead=move_playhead, **kwargs)

    if crossfade > 0:  # Crossfade in
        clip.vol_keypoints.append((0, 0))
        clip.vol_keypoints.append((crossfade, vol))
    elif in_duration > 0:  # fade in
        clip.vol_keypoints.append((0, 0))
        clip.vol_keypoints.append((in_duration, vol))
    else:
        clip.vol_keypoints.append((0, vol))


def audio_end(track, t=None, move_playhead=True, out_duration=0, crossfade=0):
    t = _get_pos(t)

    clips = _get_audio_track(track).clips
    if len(clips) == 0:
        print2("WARNING: no previous audio clip to set the end point.")
        return

    # Fade out of previous audio clip
    duration = None
    if len(_get_audio_track(track).clips) > 0:
        if crossfade > 0:  # Crossfade out
            _set_vol(0, duration=crossfade, t=t, track=track)
            duration = (t + crossfade) - clips[-1].start  # extend prev clip
        elif out_duration > 0:  # Fade out
            _set_vol(0, duration=out_duration, t=t - out_duration, track=track)
            duration = t - clips[-1].start
        else:
            duration = t - clips[-1].start

    if duration is not None and clips[-1].duration is None:
        assert duration > 0
        clips[-1].duration = duration
        print2("previous clip(%s) duration updated: %.2f" % (clips[-1].file, duration))

    if move_playhead:
        _pos_dict["c"] = _pos_dict["a"] = t


def bgm(
    f, move_playhead=False, vol=0.1, track="bgm", norm=False, loop=True, **kwargs,
):
    print("bgm: %s" % f)

    if norm:
        f = dynamic_audio_normalize(f)

    audio(
        f, track=track, move_playhead=move_playhead, loop=loop, vol=vol, **kwargs,
    )


def sfx(f, **kwargs):
    audio(f, track="sfx", move_playhead=False, **kwargs)


def pos(t, tag=None):
    _set_pos(t, tag=tag)


def clip(f, **kwargs):
    print("clip: %s" % f)
    _add_video_clip(f, **kwargs)


def fps(v):
    global FPS
    FPS = v


def overlay(
    f, pos="center", duration=3, fadein=True, fadeout=True, track="overlay", **kwargs
):
    print("image: %s" % f)
    _add_video_clip(
        f,
        pos=pos,
        duration=duration,
        fadein=fadein,
        fadeout=fadeout,
        track=track,
        **kwargs,
    )


def comment(text, pos=(960, 200), duration=4, track="overlay", **kwargs):
    md(
        '<span style="color:#f6e58d;font-size:0.8em">%s</span>' % text,
        pos=pos,
        duration=duration,
        track=track,
        **kwargs,
    )


def text(text, track="text", font_size=100, pos="center", **kwargs):
    temp_file = _generate_text_image(
        text,
        font="zcool-gdh",
        font_size=font_size,
        color="#ffd700",
        stroke_color="#6900ff",
    )
    _add_video_clip(temp_file, track=track, pos=pos, **kwargs)


def code(s, track="vid", line_no=True, mark=[], debug=False, **kwargs):
    from r.web.webscreenshot import webscreenshot

    mkdir("tmp/codeimg")
    tmp_file = "tmp/codeimg/%s.png" % get_hash(s + str(mark))
    if not os.path.exists(tmp_file):
        javascript = "setCode('%s'); " % s.replace("'", "\\'").replace("\n", "\\n")

        mark_group = list(zip(*(iter(mark),) * 4))
        for x in mark_group:
            javascript += "markText(%d, %d, %d, %d); " % (x[0], x[1], x[2], x[3],)

        javascript += "showLineNumbers(%s); " % ("true" if line_no else "false")

        webscreenshot(
            html_file=get_script_root() + "/r/web/_codeeditor/codeeditor.html",
            out_file=tmp_file,
            javascript=javascript,
            debug=debug,
        )

    _add_video_clip(tmp_file, track=track, transparent=False, **kwargs)


def codef(file, track="vid", **kwargs):
    from r.web.gen_code_image import gen_code_image_from_file

    out_file = os.path.splitext(file)[0] + ".png"
    gen_code_image_from_file(file, out_file, mtime=os.path.getmtime(file))

    _add_video_clip(out_file, track=track, transparent=False, **kwargs)

    return out_file


def _add_fadeout(track):
    global _add_fadeout_to_last_clip

    if _add_fadeout_to_last_clip:
        clip_info = track[-1]

        if clip_info.mpy_clip is not None:
            clip_info.mpy_clip = clip_info.mpy_clip.fx(vfx.fadeout, FADE_DURATION)

            _add_fadeout_to_last_clip = False


def create_image_seq_clip(tar_file):
    print("Load animation clip from %s" % tar_file)
    image_files = []
    t = tarfile.open(tar_file, "r")
    for member in t.getmembers():
        with t.extractfile(member) as fp:
            im = Image.open(fp)
            image_files.append(np.array(im))

    # tmp_folder = os.path.join(
    #     tempfile.gettempdir(),
    #     "animation",
    #     os.path.splitext(os.path.basename(tar_file))[0],
    # )

    # # Unzip
    # print2("Unzip to %s" % tmp_folder)
    # shutil.unpack_archive(tar_file, tmp_folder)

    # # Get all image files
    # image_files = sorted(glob.glob((os.path.join(tmp_folder, "*.png"))))

    clip = ImageSequenceClip(image_files, fps=IMAGE_SEQUENCE_FPS)
    return clip


def _update_prev_clip(track):
    _clip_extend_prev_clip(track)

    # _add_fadeout(track)


def _load_and_expand_img(f):
    fg = Image.open(f).convert("RGBA")
    bg = Image.new("RGB", (1920, 1080))
    bg.paste(fg, ((bg.width - fg.width) // 2, (bg.height - fg.height) // 2), fg)
    return np.array(bg)


def _get_ppt_image(f, index):
    from r.ppt.export_ppt import export_slides

    indices = [0] if index is None else [index]
    out_files = export_slides(f, indices=indices)
    return out_files[0]


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


def _preload_mpy_clip(
    file, scale=1, frame=None, expand=False, transparent=True, **kwargs
):
    def load_video_file_clip(f):
        nonlocal scale

        # Have ffmpeg resize the frames before returning them - faster speed.
        if scale != 1.0:
            w, h = _get_video_resolution(f)
            target_resolution = [int(h * scale), int(w * scale)]
        else:
            target_resolution = None

        return VideoFileClip(f, target_resolution=target_resolution)

    if file is None:
        clip = ColorClip((200, 200), color=(0, 0, 0)).set_duration(2)

    elif file.endswith(".tar"):
        clip = create_image_seq_clip(file)

    elif file.endswith(".pptx"):
        from r.ppt.export_ppt import export_slides, export_video

        if frame is None:
            file = export_video(file)
            clip = load_video_file_clip(file)
        else:
            file = export_slides(file, indices=[frame])[0]
            clip = ImageClip(file).set_duration(5)

    elif file.endswith(".png") or file.endswith(".jpg"):
        if expand:
            clip = ImageClip(_load_and_expand_img(file))
        else:
            clip = ImageClip(file)

        clip = clip.set_duration(5)
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
        clip = clip.fx(vfx.speedx, speed)

    if frame is not None:
        clip = clip.to_ImageClip(frame).set_duration(duration)

    # Loop or change duration
    if loop:
        clip = clip.fx(vfx.loop)

    if subclip is None:
        clip = clip.set_duration(duration)

    if pos is not None:
        # (x, y) marks the center location of the of the clip instead of the top
        # left corner.
        if pos == "center":
            clip = clip.set_position(("center", "center"))
        elif isinstance(pos[0], (int, float)):
            half_size = [x // 2 for x in clip.size]
            pos = [pos[0] - half_size[0], pos[1] - half_size[1]]
            pos = [int(_scale * x) for x in pos]
            clip = clip.set_position(pos)
        else:
            clip = clip.set_position(pos)

    if scale != 1.0:
        clip = clip.resize(scale)

    return clip


def _add_video_clip(
    file=None,
    speed=None,
    pos="center",
    track=None,
    fadein=False,
    fadeout=False,
    crossfade=None,
    t=None,
    duration=None,
    text_overlay=None,
    transparent=True,
    move_playhead=True,
    no_audio=False,
    na=False,
    norm=False,
    vol=None,
    subclip=None,
    frame=None,
    loop=False,
    expand=False,
    scale=1,
):
    if (track is None and _cur_vid_track_name == "vid") or (track == "vid"):
        transparent = False

    track = _get_vid_track(track)

    # _update_prev_clip(track)

    t = _get_pos(t)

    if move_playhead:
        _pos_dict["vs"] = t

    clip_info = _VideoClipInfo()
    clip_info.file = file
    clip_info.start = t
    clip_info.pos = pos
    clip_info.speed = speed

    # Note that crossfade, fadein and fadeout can not be specified at the same time.
    if _crossfade:
        clip_info.crossfade = _crossfade
    if crossfade is not None:
        clip_info.crossfade = crossfade

    clip_info.fadein = fadein
    clip_info.fadeout = fadeout

    clip_info.text_overlay = text_overlay
    clip_info.duration = duration

    clip_info.no_audio = no_audio or na
    clip_info.norm = norm
    clip_info.vol = vol
    clip_info.transparent = transparent
    clip_info.subclip = subclip
    clip_info.frame = frame
    clip_info.loop = loop
    clip_info.expand = expand
    clip_info.scale = scale * _scale

    clip_info.mpy_clip = _preload_mpy_clip(**vars(clip_info))
    if type(clip_info.mpy_clip) == VideoFileClip:
        clip_info.scale = scale  # HACK

    if move_playhead:  # Advance the pos
        if clip_info.duration is None:
            if clip_info.subclip:
                dura = clip_info.subclip[1] - clip_info.subclip[0]
            else:
                dura = clip_info.mpy_clip.duration
        else:
            dura = clip_info.duration

        end = t + dura
        _pos_dict["c"] = _pos_dict["ve"] = end

    while len(track) > 0 and clip_info.start < track[-1].start:
        print("WARNING: clip `%s` has been removed" % track[-1].file)
        track.pop()

    track.append(clip_info)

    return clip_info


def _animation(in_file, name, track=None, params={}, calc_length=True, **kwargs):
    anim = _animations[name]
    anim.in_file = in_file
    anim.url_params = params

    overlay = True if (_get_vid_track_name(track) != "vid") else False
    anim.overlay = overlay
    anim.calc_length = calc_length and not overlay

    anim.clip_info_list.append(_add_video_clip(track=track, **kwargs))


def anim(s, **kwargs):
    _animation(
        in_file=os.path.abspath("animation/%s.js" % s), name=slugify(s), **kwargs
    )


def image_anim(file, duration=5, **kwargs):
    _animation(
        in_file=os.path.abspath(SCRIPT_ROOT + "/_framework/pages/image.js"),
        name=os.path.splitext(file)[0],
        params={"t": "%d" % duration, "src": file},
        **kwargs,
    )


def title_anim(h1, h2, **kwargs):
    _animation(
        in_file=os.path.abspath(SCRIPT_ROOT + "/_framework/pages/title-animation.js"),
        name=slugify("title-%s-%s" % (h1, h2)),
        params={"h1": h1, "h2": h2},
        **kwargs,
    )


def _clip_extend_prev_clip(track=None, t=None):
    if len(track) == 0:
        return

    clip_info = track[-1]

    if clip_info.duration is None:
        clip_info.duration = _get_pos(t) - clip_info.start
        print(
            "previous clip updated: start=%.2f duration=%.2f"
            % (clip_info.start, clip_info.duration)
        )


def video_end(track=None, t=None):
    print("video_end: track=%s" % track)
    track = _get_vid_track(track)
    _clip_extend_prev_clip(track, t=t)


def empty(**kwargs):
    _add_video_clip(None, **kwargs)


def slide(
    s, template, pos="center", name=None, **kwargs,
):
    mkdir("tmp/md")
    # out_file = "tmp/slides/%s.png" % slugify(name if name else s)
    out_file = "tmp/md/%s.png" % get_hash(s)

    if not os.path.exists(out_file):
        generate_slide(s, template_file=template, out_file=out_file, gen_html=True)

    _add_video_clip(out_file, pos=pos, **kwargs)


def md(s, track="md", **kwargs):
    slide(s, track=track, template="markdown.html", fadein=True, fadeout=True, **kwargs)


def hl(pos, track="hl", duration=2, file=None, preset=0, **kwargs):
    PRESETS = [
        "../assets/image/cursor.png",
        "../assets/animation/click.tar",
    ]
    if file is None and preset >= 0:
        file = PRESETS[preset]

    clip(
        file,
        pos=pos,
        track=track,
        fadein=True,
        fadeout=True,
        duration=duration,
        move_playhead=False,
        **kwargs,
    )


def track(name="vid"):
    global _cur_vid_track_name
    _cur_vid_track_name = name


def _update_clip_duration(track):
    prev_clip_info = None
    for clip_info in track:
        if (prev_clip_info is not None) and (prev_clip_info.duration is None):
            prev_clip_info.duration = clip_info.start - prev_clip_info.start
            assert prev_clip_info.duration > 0

        prev_clip_info = clip_info

    # update last clip duration
    if len(track) > 0 and track[-1].duration is None:
        duration = track[-1].mpy_clip.duration

        # Extend the last video clip to match the voice track
        if "re" in _pos_dict:
            duration = max(duration, _pos_dict["re"] - clip_info.start)

        track[-1].duration = duration


def _export_video(resolution=(1920, 1080)):
    resolution = [int(x * _scale) for x in resolution]

    audio_clips = []

    # Update clip duration for each track
    for track in _video_tracks.values():
        _update_clip_duration(track)

    # Add text overlay clip
    for track in _video_tracks.values():
        for clip_info in track:
            if clip_info.text_overlay is not None:
                mkdir("tmp/text_overlay")
                overlay_file = "tmp/text_overlay/%s.png" % slugify(
                    clip_info.text_overlay
                )
                if not os.path.exists(overlay_file):
                    generate_slide(
                        clip_info.text_overlay,
                        template_file="source.html",
                        out_file=overlay_file,
                    )
                assert clip_info.duration is not None
                _add_video_clip(
                    overlay_file,
                    t=clip_info.start,
                    duration=clip_info.duration,
                    track="overlay",
                )

    # Generate animation clips
    if not _audio_only:
        for name, animation_info in _animations.items():
            if animation_info.overlay:
                anim_ext = "tar"
            else:
                anim_ext = "mp4"

            out_file = "tmp/animation/%s.%s" % (name, anim_ext)
            os.makedirs("tmp/animation", exist_ok=True)

            if 1:  # generate animation video file

                if not os.path.exists(out_file):
                    params = {**animation_info.url_params}

                    if animation_info.calc_length:
                        subclip_dura_list = "|".join(
                            ["%g" % x.duration for x in animation_info.clip_info_list]
                        )
                        print(subclip_dura_list)

                        params.update({"t": subclip_dura_list})

                    capture_animation.capture_js_animation(
                        in_file=animation_info.in_file,
                        out_file=out_file,
                        params=params,
                        content_base=os.getcwd(),
                    )

            for i, clip_info in enumerate(animation_info.clip_info_list):
                clip_info.mpy_clip = _preload_mpy_clip(file=out_file)
                if animation_info.overlay:
                    clip_info.duration = clip_info.mpy_clip.duration

    # Update MoviePy clip object in each track.
    video_clips = []
    for track_name, track in _video_tracks.items():
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
                    audio_clip = audio_clip.fx(afx.audio_normalize)
                if clip_info.vol is not None:
                    if isinstance(clip_info.vol, (int, float)):
                        audio_clip = audio_clip.fx(afx.volumex, clip_info.vol)
                    else:
                        audio_clip = _adjust_mpy_audio_clip_volume(
                            audio_clip, clip_info.vol
                        )

                audio_clips.append(audio_clip)

            # Increase duration for crossfade?
            EPSILON = 0.1  # To avoid float point error
            fade_duration = track[i].crossfade
            if fade_duration:
                clip_info.duration += fade_duration * 0.5 + EPSILON

            clip_info.mpy_clip = _update_mpy_clip(clip_info.mpy_clip, **vars(clip_info))

            # Deal with video fade in / out / crossfade
            if clip_info.fadein:
                # TODO: crossfadein and crossfadeout is very slow in moviepy
                if track_name != "vid":
                    clip_info.mpy_clip = clip_info.mpy_clip.crossfadein(
                        VIDEO_CROSSFADE_DURATION
                    )
                else:
                    clip_info.mpy_clip = clip_info.mpy_clip.fx(
                        vfx.fadein, VIDEO_CROSSFADE_DURATION
                    )

            elif (
                clip_info.crossfade > 0
            ):  # crossfade and fadein should not happen at the same time
                video_clips.append(
                    clip_info.mpy_clip.set_duration(clip_info.crossfade)
                    .crossfadein(clip_info.crossfade)
                    .set_start(clip_info.start - 0.5 * clip_info.crossfade)
                )

                clip_info.mpy_clip = clip_info.mpy_clip.subclip(clip_info.crossfade)
                clip_info.start += 0.5 * clip_info.crossfade

            if clip_info.fadeout:
                if track_name != "vid":
                    clip_info.mpy_clip = clip_info.mpy_clip.crossfadeout(
                        VIDEO_CROSSFADE_DURATION
                    )
                else:
                    clip_info.mpy_clip = clip_info.mpy_clip.fx(
                        vfx.fadeout, VIDEO_CROSSFADE_DURATION
                    )

            video_clips.append(clip_info.mpy_clip.set_start(clip_info.start))

    if len(video_clips) == 0:
        video_clips.append(ColorClip((200, 200), color=(0, 1, 0)).set_duration(2))
        # raise Exception("no video clips??")
    final_clip = CompositeVideoClip(video_clips, size=resolution)

    # Resize here is too late, does not speed up the video encoding at all.
    # final_clip = final_clip.resize(width=480)

    # Deal with audio clips
    for _, track in _audio_tracks.items():
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

    os.makedirs("out", exist_ok=True)
    out_filename = "out/" + get_time_str()

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


def _tts():
    text = _subtitle[-1]
    hash = get_hash(text)

    mkdir("tmp/tts")
    out_file = "tmp/tts/%s.wav" % hash
    if not os.path.exists(out_file):
        print("generate tts file: %s" % out_file)

        _tts_to_wav_microsoft(out_file, text)

    record(out_file, postprocess=False)


def tts(enabled=True):
    global AUTO_GENERATE_TTS
    AUTO_GENERATE_TTS = enabled


def final(b=True):
    global _add_subtitle
    global _scale
    global _crossfade

    if b:
        _add_subtitle = True
        _crossfade = VIDEO_CROSSFADE_DURATION
        _scale = 1.0


def parse_line(line):
    print2(line, color="green")
    _subtitle.append(line)

    if AUTO_GENERATE_TTS:
        _tts()


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
    if not hasattr(_write_timestamp, "f"):
        _write_timestamp.f = open("timestamp.txt", "w", encoding="utf-8")

    _write_timestamp.f.write("%s (%s)\n" % (section_name, _convert_to_readable_time(t)))
    _write_timestamp.f.flush()


def _interface():
    return {
        "anim": lambda *_, **__: None,
        "audio_end": lambda *_, **__: None,
        "audio_gap": lambda *_, **__: None,
        "audio": lambda *_, **__: None,
        "bgm_vol": lambda *_, **__: None,
        "bgm": lambda *_, **__: None,
        "clip": lambda *_, **__: None,
        "code": lambda *_, **__: None,
        "codef": lambda *_, **__: None,
        "comment": lambda *_, **__: None,
        "crossfade": lambda *_, **__: None,
        "empty": lambda *_, **__: None,  # deprecated
        "fps": lambda *_, **__: None,
        "hl": lambda *_, **__: None,
        "image_anim": lambda *_, **__: None,
        "image": lambda *_, **__: None,  # deprecated, use `clip` instead
        "include": lambda *_, **__: None,
        "mark": lambda *_, **__: None,
        "md": lambda *_, **__: None,
        "overlay": lambda *_, **__: None,
        "parse_line": lambda *_, **__: None,
        "pos": lambda *_, **__: None,
        "record": lambda *_, **__: None,
        "sfx": lambda *_, **__: None,
        "slide": lambda *_, **__: None,
        "text": lambda *_, **__: None,
        "title_anim": lambda *_, **__: None,
        "tts": lambda *_, **__: None,
        "video_end": lambda *_, **__: None,
        "video": lambda *_, **__: None,  # deprecated, use `clip` instead
        "vol": lambda *_, **__: None,
    }


def _default_impl():
    impl = {
        **_interface(),
        "anim": anim,
        "audio_end": audio_end,
        "audio_gap": audio_gap,
        "audio": audio,
        "bgm_vol": bgm_vol,
        "bgm": bgm,
        "clip": clip,
        "code": code,
        "codef": codef,
        "comment": comment,
        "crossfade": crossfade,
        "empty": empty,  # deprecated
        "final": final,
        "fps": fps,
        "hl": hl,
        "image_anim": image_anim,
        "image": clip,  # deprecated
        "mark": mark,
        "md": md,
        "overlay": overlay,
        "parse_line": parse_line,
        "pos": pos,
        "record": record,
        "sfx": sfx,
        "slide": slide,
        "text": text,
        "title_anim": title_anim,
        "tts": tts,
        "video_end": video_end,
        "video": clip,  # deprecated
        "vol": vol,
    }

    # Include function
    def include(file):
        with open(file, "r", encoding="utf-8") as f:
            s = f.read()

        cwd = os.getcwd()
        os.chdir(os.path.dirname(os.path.abspath(file)))
        _parse_text(s, impl)
        os.chdir(cwd)

    impl["include"] = include

    # Import `index.py` if exists
    MODULE = "index.py"
    if os.path.exists(MODULE):
        sys.path.append(os.getcwd())
        exec(open(MODULE, "r", encoding="utf-8").read(), impl)

    return impl


def _remove_unused_recordings(s):
    used_recordings = set()
    unused_recordings = []

    impl = {**_interface(), "record": (lambda f, **kargs: used_recordings.add(f))}
    _parse_text(s, impl=impl)

    files = [f for f in glob.glob("record/*") if os.path.isfile(f)]
    files = [f.replace("\\", "/") for f in files]

    for f in files:
        if f not in used_recordings:
            unused_recordings.append(f)

    print("Total: %d" % len(files))
    print("Used recordings: %d" % len(used_recordings))
    print("Recordings to delete: %d" % len(unused_recordings))
    assert len(used_recordings) + len(unused_recordings) == len(files)
    if input("press y to confirm deletion: ") == "y":
        for f in unused_recordings:
            try:
                os.remove(f)
            except:
                print("WARNING: failed to remove: %s" % f)


def _parse_text(text, impl, **kwargs):
    def find_next(text, needle, p):
        pos = text.find(needle, p)
        if pos < 0:
            pos = len(text)
        return pos

    # Remove all comments
    text = re.sub(r"<!--[\d\D]*?-->", "", text)

    p = 0  # Current position
    while p < len(text):
        if text[p : p + 2] == "! ":
            end = find_next(text, "\n", p)
            python_code = text[p + 2 : end].strip()
            p = end + 1

            exec(python_code, impl)

        elif text[p : p + 2] == "{" + "{":
            end = find_next(text, "}" + "}", p)
            python_code = text[p + 2 : end].strip()
            p = end + 2

            exec(python_code, impl)

        elif text[p : p + 1] == "#":
            end = find_next(text, "\n", p)

            line = text[p:end].strip()
            _write_timestamp(_pos_dict["a"], line)

            p = end + 1

        elif text[p : p + 3] == "---":
            audio_gap(0.2)
            p = find_next(text, "\n", p) + 1

        else:
            end = find_next(text, "\n", p)
            line = text[p:end].strip()
            p = end + 1

            if line != "":
                impl["parse_line"](line)

            # _export_srt()
        # sys.exit(0)


def _show_stats(s):
    TIME_PER_CHAR = 0.1334154351395731

    total = 0

    def parse_line(line):
        nonlocal total
        total += len(line)

    _parse_text(s, impl={**_interface(), "parse_line": parse_line})

    total_secs = TIME_PER_CHAR * total
    print("Estimated Time: %s" % _format_time(total_secs))

    input()


def load_config():
    import yaml

    CONFIG_FILE = "config.yaml"
    DEFAULT_CONFIG = {"final": False, "tts": False, "fps": 25}

    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            config = yaml.load(f.read(), Loader=yaml.FullLoader)
    else:
        with open(CONFIG_FILE, "w", newline="\n") as f:
            yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False)
        config = DEFAULT_CONFIG

    final(config["final"])
    tts(config["tts"])
    fps(config["fps"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stdin", default=False, action="store_true")
    parser.add_argument("--proj_dir", type=str, default=None)
    parser.add_argument("-i", "--input", type=str, default=None)
    parser.add_argument("-a", "--audio_only", action="store_true", default=False)
    parser.add_argument(
        "--remove_unused_recordings", action="store_true", default=False
    )
    parser.add_argument("--show_stats", action="store_true", default=False)

    args = parser.parse_args()

    if args.proj_dir is not None:
        os.chdir(args.proj_dir)
    elif args.input:
        os.chdir(os.path.dirname(args.input))
    print("Project dir: %s" % os.getcwd())

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

    if args.remove_unused_recordings:
        _remove_unused_recordings(s)
    elif args.show_stats:
        _show_stats(s)
    else:
        _parse_text(s, impl=_default_impl())
        _export_video()
