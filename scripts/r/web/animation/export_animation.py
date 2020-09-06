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
    from moviepy.config import change_settings
    from moviepy.editor import *
    import moviepy.video.fx.all as vfx
    import moviepy.audio.fx.all as afx
    from moviepy.video.tools.subtitles import SubtitlesClip


ADD_SUBTITLE = True
VOLUME_DIM = 0.15
FADE_DURATION = 0.2
AUTO_GENERATE_TTS = False
IMAGE_SEQUENCE_FPS = 25
FPS = 25
SCALE = 1.0

# change_settings({"FFMPEG_BINARY": get_executable("ffmpeg")})


class _VideoClipInfo:
    def __init__(self):
        self.file: str = None
        self.start: float = 0
        self.duration: float = None
        self.mpy_clip: Any = None
        self.speed: float = 1
        self.pos = None
        self.fadein: bool = False
        self.fadeout: bool = False
        self.crossfade: bool = False
        self.text_overlay: str = None


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
_pos_list = [0]
_pos_dict = {"a": 0, "as": 0, "ae": 0, "vs": 0, "ve": 0}


_add_fadeout_to_last_clip = False

_video_tracks = OrderedDict(
    [("vid", []), ("hl", []), ("hl2", []), ("md", []), ("overlay", []), ("text", [])]
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

_crossfade = False


def _format_time(sec):
    td = datetime.timedelta(seconds=sec)
    return "%02d:%02d:%02d,%03d" % (
        td.seconds // 3600,
        td.seconds // 60,
        td.seconds % 60,
        td.microseconds // 1000,
    )


def crossfade(b):
    global _crossfade
    _crossfade = b


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
        return _pos_list[-1]

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
    _pos_list.append(t)

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
    text = text.replace("%", "%%")

    # Generate subtitle png image using magick
    tempfile_fd, tempfilename = tempfile.mkstemp(suffix=".png")
    os.close(tempfile_fd)
    cmd = [
        IMAGE_MAGICK,
        "-background",
        "transparent",
        "-font",
        r"C:/Windows/Fonts/SourceHanSansSC-Medium.otf",
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


def record(f, t="a", postprocess=True, **kwargs):
    if not os.path.exists(f):
        f = "record/" + f
        assert os.path.exists(f)

    # Post-process audio
    if postprocess:
        f = process_audio_file(f)

    audio(f, t=t, **kwargs)

    _pos_dict["re"] = _get_pos("ae")

    END_CHARS = ["。", "，", "！", "、", "；", "？", "|"]

    global _srt_index
    global _last_subtitle_index

    if ADD_SUBTITLE:
        if len(_subtitle) == 0:
            print("WARNING: no subtitle found")

        else:
            idx = len(_subtitle) - 1
            if _last_subtitle_index == idx:
                print2("WARNING: subtitle used twice: %s" % _subtitle[idx])
            _last_subtitle_index = idx

            start = end = _get_pos("as")
            subtitle = _subtitle[idx].strip()

            if subtitle[-1] not in END_CHARS:
                subtitle += END_CHARS[0]

            length = len(subtitle)
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
    _pos_list.append(_pos_dict["a"])


def _set_vol(vol, duration=0.25, track=None, t=None):
    t = _get_pos(t)

    print("change vol=%.2f  at=%.2f  duration=%.2f" % (vol, t, duration))
    track_ = _get_audio_track(track)
    if len(track_.clips) == 0:
        raise Exception("No audio clip to set volume in track: %s" % track)

    t_in_clip = t - track_.clips[-1].start
    assert t_in_clip >= 0
    track_.clips[-1].vol_keypoints.append((t_in_clip, vol, duration))


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
        _pos_list.append(_pos_dict["as"])

    clip_info = _AudioClipInfo()

    if not os.path.exists(file):
        raise Exception("Please make sure `%s` exists." % file)
    clip_info.file = file

    # HACK: still don't know why changing buffersize would help reduce the noise at the end
    clip_info.mpy_clip = AudioFileClip(file, buffersize=400000)

    clip_info.duration = duration
    clip_info.subclip = subclip
    clip_info.start = t
    clip_info.loop = loop

    if move_playhead:
        # Forward audio track pos
        _pos_dict["a"] = _pos_dict["ae"] = _pos_dict["as"] + (
            clip_info.mpy_clip.duration if duration is None else duration
        )

    clips.append(clip_info)

    return clip_info


def audio(f, **kwargs):
    _add_audio_clip(f, **kwargs)


def audio_end(*, t=None, track=None, move_playhead=True):
    t = _get_pos(t)

    clips = _get_audio_track(track).clips
    if len(clips) == 0:
        print2("WARNING: no previous audio clip to set the end point.")
        return

    duration = t - clips[-1].start
    assert duration > 0
    clips[-1].duration = duration

    if move_playhead:
        _pos_dict["a"] = t
        _pos_list.append(_pos_dict["a"])


def bgm(
    f,
    move_playhead=False,
    t="a",
    crossfade=0,
    in_duration=0.5,
    out_duration=0.5,
    vol=0.10,
    track="bgm",
    norm=False,
    **kwargs,
):
    print("bgm: %s" % f)
    t = _get_pos(t)

    if norm:
        f = dynamic_audio_normalize(f)

    if len(_get_audio_track(track).clips) > 0:
        if crossfade > 0:
            _set_vol(0, duration=crossfade, t=t, track=track)
            audio_end(track=track, t=t + crossfade, move_playhead=False)
        else:
            _set_vol(0, duration=out_duration, t=t - out_duration, track=track)
            audio_end(track=track, t=t, move_playhead=False)

    audio(f, track=track, move_playhead=move_playhead, t=t, **kwargs)

    if crossfade > 0:
        _set_vol(vol, duration=crossfade, t=t, track=track)
    else:
        _set_vol(vol, duration=in_duration, t=t, track=track)


def sfx(f, **kwargs):
    audio(f, track="sfx", move_playhead=False, **kwargs)


def pos(p, tag=None):
    _set_pos(p, tag=tag)


# Deprecated
def image(f, pos="center", **kwargs):
    clip(f, **kwargs)


# Deprecated
def video(f, **kwargs):
    clip(f, **kwargs)


def clip(f, **kwargs):
    print("clip: %s" % f)
    _add_clip(f, **kwargs)


def fps(v):
    global FPS
    FPS = v


def overlay(
    f, pos="center", duration=3, fadein=True, fadeout=True, track="overlay", **kwargs
):
    print("image: %s" % f)
    _add_clip(
        f,
        pos=pos,
        duration=duration,
        fadein=fadein,
        fadeout=fadeout,
        track=track,
        **kwargs,
    )


def comment(text, pos=(960, 200), duration=4, **kwargs):
    md(
        '<span style="color:#f6e58d;font-size:0.8em">%s</span>' % text,
        pos=pos,
        duration=duration,
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
    _add_clip(temp_file, track=track, pos=pos, **kwargs)


def code_carbon(s, track="vid", line_no=True, **kwargs):
    from r.web.carbon_gen_code_image import gen_code_image

    mkdir("tmp/codeimg")
    tmp_file = "tmp/codeimg/%s.png" % get_hash(s)
    if not os.path.exists(tmp_file):
        gen_code_image(s, out_file=tmp_file, line_no=line_no)
    _add_clip(tmp_file, track=track, **kwargs)


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

    _add_clip(tmp_file, track=track, transparent=False, **kwargs)


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


def _create_mpy_clip(
    file=None,
    clip_operations=None,
    speed=None,
    pos=None,
    text_overlay=None,
    no_audio=False,
    na=False,
    duration=None,
    vol=None,
    transparent=True,
    subclip=None,
    extract_frame=None,
    loop=False,
    expand=False,
):
    if file is None:
        clip = ColorClip((200, 200), color=(0, 0, 0)).set_duration(2)

    elif file.endswith(".tar"):
        clip = create_image_seq_clip(file)

    elif file.endswith(".png") or file.endswith(".jpg"):
        if expand:
            clip = ImageClip(_load_and_expand_img(file))
        else:
            clip = ImageClip(file)

        clip = clip.set_duration(5)
        if not transparent:
            clip = clip.set_mask(None)

    else:
        clip = VideoFileClip(file)

    # video clip operations / fx
    if subclip is not None:
        clip = clip.subclip(subclip)

    if speed is not None:
        clip = clip.fx(vfx.speedx, speed)

    if extract_frame is not None:
        clip = clip.to_ImageClip(extract_frame).set_duration(5)

    if clip_operations is not None:
        clip = clip_operations(clip)

    if no_audio or na:
        clip = clip.set_audio(None)

    if clip.audio is not None and vol:
        if isinstance(vol, (int, float)):
            clip.audio = clip.audio.fx(afx.volumex, vol)
        else:
            clip.audio = _adjust_mpy_audio_clip_volume(clip.audio, vol)

    # Loop or change duration
    if loop:
        clip = clip.fx(vfx.loop).set_duration(clip.duration)

    if duration is not None:
        clip = clip.set_duration(duration)

    if pos is not None:
        # (x, y) marks the center location of the of the clip instead of the top
        # left corner.
        if pos == "center":
            clip = clip.set_position(("center", "center"))
        elif isinstance(pos[0], (int, float)):
            half_size = [x // 2 for x in clip.size]
            clip = clip.set_position((pos[0] - half_size[0], pos[1] - half_size[1]))
        else:
            clip = clip.set_position(pos)

    if SCALE != 1.0:
        clip = clip.resize(SCALE)

    return clip


def _add_clip(
    file=None,
    clip_operations=None,
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
    **kwargs,
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
    clip_info.crossfade = (not fadein and not fadeout) and (crossfade or _crossfade)
    clip_info.fadein = fadein
    clip_info.fadeout = fadeout

    clip_info.text_overlay = text_overlay
    clip_info.duration = duration

    clip_info.mpy_clip = _create_mpy_clip(
        file=file,
        clip_operations=clip_operations,
        speed=speed,
        pos=pos,
        duration=duration,
        transparent=transparent,
        **kwargs,
    )

    if move_playhead:  # Advance the pos
        end = t + clip_info.mpy_clip.duration
        _pos_list.append(end)
        _pos_dict["ve"] = end

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

    anim.clip_info_list.append(_add_clip(track=track, **kwargs))


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
            "previous clip (start, duration) updated: (%.2f, %.2f)"
            % (clip_info.start, clip_info.duration)
        )


def video_end(track=None, t=None):
    print("video_end: track=%s" % track)
    track = _get_vid_track(track)
    _clip_extend_prev_clip(track, t=t)


def empty(**kwargs):
    _add_clip(None, **kwargs)


def screencap(f, speed=None, track=None, **kwargs):
    print("screencap: %s" % f)
    _add_clip(
        "screencap/" + f,
        clip_operations=lambda x: x.crop(x1=0, y1=0, x2=2560, y2=1380)
        .resize(0.75)
        .set_position((0, 22)),
        speed=speed,
        track=track,
        **kwargs,
    )


def md(s, track="md", fadein=True, fadeout=True, pos="center", name=None, **kwargs):
    mkdir("tmp/md")
    # out_file = "tmp/slides/%s.png" % slugify(name if name else s)
    out_file = "tmp/md/%s.png" % get_hash(s)

    if not os.path.exists(out_file):
        generate_slide(
            s, template_file="markdown.html", out_file=out_file, gen_html=True
        )

    _add_clip(out_file, track=track, fadein=fadein, fadeout=fadeout, pos=pos, **kwargs)


def hl(pos, track="hl", duration=2, file=None, preset=0, **kwargs):
    PRESETS = [
        "../image/cursor.png",
        "../animation/click.tar",
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


def _export_video(resolution=(1920, 1080), audio_only=False):
    resolution = [int(x * SCALE) for x in resolution]

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
                _add_clip(
                    overlay_file,
                    t=clip_info.start,
                    duration=clip_info.duration,
                    track="overlay",
                )

    # Generate animation clips
    if not audio_only:
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
                clip_info.mpy_clip = _create_mpy_clip(
                    # file=(
                    #     out_file
                    #     if i == 0
                    #     else "tmp/animation/%s.%d.%s" % (name, i, anim_ext)
                    # )
                    # HACK:
                    file=out_file
                )
                if animation_info.overlay:
                    clip_info.duration = clip_info.mpy_clip.duration

    # Update MoviePy clip object in each track.
    video_clips = []
    for track_name, track in _video_tracks.items():
        for i, clip_info in enumerate(track):
            assert clip_info.mpy_clip is not None
            assert clip_info.duration is not None

            if clip_info.duration is not None:
                # Unlink audio clip from video clip (adjust audio duration)
                if clip_info.mpy_clip.audio is not None:
                    audio_clip = clip_info.mpy_clip.audio.set_start(
                        clip_info.start
                    ).set_duration(
                        min(clip_info.duration, clip_info.mpy_clip.audio.duration)
                    )
                    audio_clips.append(audio_clip)
                    clip_info.mpy_clip = clip_info.mpy_clip.set_audio(None)

                # Use duration to extend / hold the last frame instead of creating new clips.
                duration = clip_info.duration
                assert duration > 0

                # Crossfade?
                EPSILON = 0.1  # To avoid float point error
                if i + 1 < len(track) and track[i + 1].crossfade:
                    duration += FADE_DURATION * 0.5 + EPSILON

                assert duration > 0
                clip_info.mpy_clip = clip_info.mpy_clip.set_duration(duration)

            if clip_info.crossfade:
                video_clips.append(
                    clip_info.mpy_clip.set_duration(FADE_DURATION)
                    .crossfadein(FADE_DURATION)
                    .set_start(clip_info.start - 0.5 * FADE_DURATION)
                )
                video_clips.append(
                    clip_info.mpy_clip.subclip(FADE_DURATION).set_start(
                        clip_info.start + 0.5 * FADE_DURATION
                    )
                )
            else:
                if clip_info.fadein:
                    # TODO: crossfadein and crossfadeout is very slow in moviepy
                    if track_name != "vid":
                        clip_info.mpy_clip = clip_info.mpy_clip.crossfadein(
                            FADE_DURATION
                        )
                    else:
                        clip_info.mpy_clip = clip_info.mpy_clip.fx(
                            vfx.fadein, FADE_DURATION
                        )

                if clip_info.fadeout:
                    if track_name != "vid":
                        clip_info.mpy_clip = clip_info.mpy_clip.crossfadeout(
                            FADE_DURATION
                        )
                    else:
                        clip_info.mpy_clip = clip_info.mpy_clip.fx(
                            vfx.fadeout, FADE_DURATION
                        )

                video_clips.append(clip_info.mpy_clip.set_start(clip_info.start))

    if len(video_clips) == 0:
        video_clips.append(ColorClip((200, 200), color=(0, 1, 0)).set_duration(2))
        # raise Exception("no video clips??")
    final_clip = CompositeVideoClip(video_clips, size=resolution)

    # Deal with audio clips
    for _, track in _audio_tracks.items():
        clips = []
        for clip_info in track.clips:
            clip = clip_info.mpy_clip

            if clip_info.subclip is not None:
                clip = clip.subclip(clip_info.subclip)

            if clip_info.duration is not None:
                if clip_info.loop:
                    clip = clip.fx(afx.audio_loop, duration=clip_info.duration)
                else:
                    clip = clip.set_duration(clip_info.duration)

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
            fps=FPS,
            ffmpeg_params=["-crf", "19"],
        )

        open_with(f"{out_filename}.mp4")


def _adjust_mpy_audio_clip_volume(clip, vol_keypoints):
    xp = []
    fp = []
    cur_vol = 0

    for i, (start, vol, duration) in enumerate(vol_keypoints):
        if isinstance(vol, (int, float)):
            xp += [start, start + duration]
            fp += [cur_vol, vol]
            cur_vol = vol

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


def _tts():
    text = _subtitle[-1]
    hash = get_hash(text)

    mkdir("tmp/tts")
    file_name = "tmp/tts/%s.wav" % hash
    if not os.path.exists(file_name):
        print("generate tts file: %s" % file_name)
        tmp_file = "tmp/tts/%s_gtts.mp3" % hash
        call2(
            ["gtts-cli", text, "--lang", "zh-cn", "--nocheck", "--output", tmp_file,]
        )
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
                file_name,
            ]
        )
        os.remove(tmp_file)

    record(file_name, postprocess=False)


def tts(enabled=True):
    global AUTO_GENERATE_TTS
    AUTO_GENERATE_TTS = enabled


def _parse_line(line):
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
    with open("timestamp.txt", "w", encoding="utf-8") as f:
        f.write("%s (%s)\n" % (section_name, _convert_to_readable_time(t)))


def _interface():
    return {
        "anim": lambda *_, **__: None,
        "audio_end": lambda *_, **__: None,
        "audio_gap": lambda *_, **__: None,
        "audio": lambda *_, **__: None,
        "bgm_vol": lambda *_, **__: None,
        "bgm": lambda *_, **__: None,
        "clip": lambda *_, **__: None,
        "code_carbon": lambda *_, **__: None,  # deprecated, use `code` instead
        "code": lambda *_, **__: None,
        "comment": lambda *_, **__: None,
        "crossfade": lambda *_, **__: None,
        "empty": lambda *_, **__: None,  # deprecated
        "fps": lambda *_, **__: None,
        "hl": lambda *_, **__: None,
        "image_anim": lambda *_, **__: None,
        "image": lambda *_, **__: None,  # deprecated, use `clip` instead
        "md": lambda *_, **__: None,
        "overlay": lambda *_, **__: None,
        "pos": lambda *_, **__: None,
        "record": lambda *_, **__: None,
        "sfx": lambda *_, **__: None,
        "text": lambda *_, **__: None,
        "title_anim": lambda *_, **__: None,
        "tts": lambda *_, **__: None,
        "video_end": lambda *_, **__: None,
        "video": lambda *_, **__: None,  # deprecated, use `clip` instead
        "vol": lambda *_, **__: None,
    }


def _default_impl():
    return {
        **_interface(),
        "anim": anim,
        "audio_end": audio_end,
        "audio_gap": audio_gap,
        "audio": audio,
        "bgm_vol": bgm_vol,
        "bgm": bgm,
        "clip": clip,
        "code_carbon": code_carbon,  # deprecated, use `code` instead
        "code": code,
        "comment": comment,
        "crossfade": crossfade,
        "empty": empty,  # deprecated
        "fps": fps,
        "hl": hl,
        "image_anim": image_anim,
        "image": image,  # deprecated, use `clip` instead
        "md": md,
        "overlay": overlay,
        "pos": pos,
        "record": record,
        "sfx": sfx,
        "text": text,
        "title_anim": title_anim,
        "tts": tts,
        "video_end": video_end,
        "video": video,  # deprecated, use `clip` instead
        "vol": vol,
    }


def _remove_unused_recordings(s):
    recordings = set()
    impl = {**_interface(), "record": (lambda f, **kargs: recordings.add(f))}
    _parse_text(s, impl=impl)

    file_to_delete = []
    for f in os.listdir("record"):
        if f not in recordings and f.endswith(".wav"):
            file_to_delete.append(f)

    print("Used recordings: %d" % len(recordings))
    print("Recordings to delete: %d" % len(file_to_delete))
    if input("press y to confirm deletion: ") == "y":
        for f in file_to_delete:
            os.remove(os.path.join("record", f))


def _parse_text(text, impl=_default_impl(), parse_line=None, **kwargs):
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

            if line != "" and parse_line is not None:
                parse_line(line)

            # _export_srt()
        # sys.exit(0)


def _show_stats(s):
    TIME_PER_CHAR = 0.1334154351395731

    total = 0

    def parse_line(line):
        nonlocal total
        total += len(line)

    _parse_text(s, impl=_interface(), parse_line=parse_line)

    total_secs = TIME_PER_CHAR * total
    print("Estimated Time: %s" % _format_time(total_secs))

    input()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stdin", default=False, action="store_true")
    parser.add_argument("-i", "--input", type=str, default=None)
    parser.add_argument("--proj_dir", type=str, default=None)
    parser.add_argument("-a", "--audio_only", action="store_true", default=False)
    parser.add_argument(
        "--remove_unused_recordings", action="store_true", default=False
    )
    parser.add_argument("--show_stats", action="store_true", default=False)

    args = parser.parse_args()

    # HACK
    if args.audio_only:
        ADD_SUBTITLE = False

    if args.proj_dir is not None:
        os.chdir(args.proj_dir)
    print("Project dir: %s" % os.getcwd())

    # Read text
    if args.stdin:
        s = sys.stdin.read()

    elif args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            s = f.read()

    else:
        PROJ_DIR = r"{{VIDEO_PROJECT_DIR}}"

        PARSE_LINE_RANGE = (
            [int(x) for x in "{{_PARSE_LINE_RANGE}}".split()]
            if "{{_PARSE_LINE_RANGE}}"
            else None
        )
        ADD_SUBTITLE = bool("{{_ADD_SUBTITLE}}")

        cd(PROJ_DIR)

        with open("index.md", "r", encoding="utf-8", newline="\n") as f:
            s = f.read()

            # Filter lines
            lines = s.splitlines()
            if PARSE_LINE_RANGE is not None:
                lines = lines[PARSE_LINE_RANGE[0] - 1 : PARSE_LINE_RANGE[1]]
            s = "\n".join(lines)

    if args.remove_unused_recordings:
        _remove_unused_recordings(s)
    elif args.show_stats:
        _show_stats(s)
    else:
        _parse_text(s, audio_only=args.audio_only, parse_line=_parse_line)
        _export_video(audio_only=args.audio_only)
