if 1:
    import sys
    import traceback

    def excepthook(exc_type, exc_value, exc_traceback):
        traceback.print_tb(exc_traceback)
        print(exc_value)
        input("press enter key...")

    sys.excepthook = excepthook

from typing import Any, NamedTuple
import webbrowser
import urllib
import re
import capture_animation
from slide.generate import generate_slide
from r.open_with.open_with_ import open_with
from _shutil import *
from collections import defaultdict
from collections import OrderedDict
import numpy as np
import argparse
import hashlib

if 1:
    import os
    import sys

    sys.path.append(os.path.dirname(os.path.abspath(__file__)))


if 1:  # Import moviepy
    f = glob.glob(r"C:\Program Files\ImageMagick-*\magick.exe")[0]
    os.environ["IMAGEMAGICK_BINARY"] = f
    from moviepy.config import change_settings
    from moviepy.editor import *
    import moviepy.video.fx.all as vfx
    import moviepy.audio.fx.all as afx
    from moviepy.video.tools.subtitles import SubtitlesClip


ADD_SUBTITLE = False
VOLUME_DIM = 0.15
FADE_DURATION = 0.2
AUTO_TTS = True

change_settings({"FFMPEG_BINARY": "ffmpeg"})


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


class _AudioTrack:
    def __init__(self):
        self.clips = []
        self.vol_keypoints = []


class _AnimationInfo:
    def __init__(self):
        self.clip_info_list = []
        self.url = None
        self.calc_length = True
        self.url_params = {}


_audio_track_cur_pos = 0
_pos_list = [0]
_pos_dict = {"a": 0}


_add_fadeout_to_last_clip = False

_video_tracks = OrderedDict(
    [("vid", []), ("hl", []), ("hl2", []), ("md", []), ("overlay", []), ("text", [])]
)
_cur_vid_track_name = "vid"  # default video track

_audio_tracks = OrderedDict(
    [("bgm", _AudioTrack()), ("record", _AudioTrack()), ("sfx", _AudioTrack())]
)
_cur_audio_track_name = "record"

_animations = defaultdict(_AnimationInfo)

_subtitle = []
_srt_lines = []
_srt_index = 1

_bgm_clip = None
_bgm = {}
_bgm_vol = []

_crossfade = False


def crossfade(b):
    global _crossfade
    _crossfade = b


def _get_hash(text):
    hash_object = hashlib.md5(text.encode())
    hash = hash_object.hexdigest()[0:16]
    return hash


def _get_track(tracks, name):
    print("  track=%s" % name)

    if name not in tracks:
        raise Exception("track is not defined: %s" % name)
    track = tracks[name]

    return track


def _get_vid_track(name=None):
    if name is None:
        name = _cur_vid_track_name
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

    PATT_FLOAT = r"([-+]?\d*\.?\d*)"

    if p is None:
        return _pos_list[-1]

    if type(p) == int or type(p) == float:
        return float(p)

    if type(p) == str:
        if p in _pos_dict:
            return _pos_dict[p]

        # TODO: remove
        match = re.match(r"^\+=" + PATT_FLOAT + "$", p)
        if match:
            delta = float(match.group(1))
            return _pos_list[-1] + delta

        # TODO: remove
        match = re.match(r"^\<" + PATT_FLOAT + "$", p)
        if match:
            delta = float(match.group(1))
            clip_info = _get_vid_track()[-1]
            return clip_info.start + delta

        # TODO: remove
        match = re.match(r"^(\^+)" + PATT_FLOAT + "$", p)
        if match:
            index_back_in_history = len(match.group(1))
            delta = float(match.group(2))
            return _pos_list[-index_back_in_history - 1] + delta

        match = re.match(r"^([a-z_]+)" + PATT_FLOAT + "$", p)
        if match:
            tag = match.group(1)
            assert match.group(2) != ""
            delta = float(match.group(2))
            return _pos_dict[tag] + delta

    raise Exception("Invalid param.")


def _set_pos(t, tag=None):
    t = _get_pos(t)
    _pos_list.append(t)

    if tag is not None:
        _pos_dict[tag] = t


def _format_time(sec):
    td = datetime.timedelta(seconds=sec)
    return "%02d:%02d:%02d,%03d" % (
        td.seconds // 3600,
        td.seconds // 60,
        td.seconds % 60,
        td.microseconds // 1000,
    )


def _generate_text_image(
    text,
    font="Source-Han-Sans-CN",
    font_size=50,
    color="#ffffff",
    stroke_color="#000000",
):
    # Generate subtitle png image using magick
    tempfile_fd, tempfilename = tempfile.mkstemp(suffix=".png")
    os.close(tempfile_fd)
    cmd = [
        glob.glob(r"C:\Program Files\ImageMagick-*\magick.exe")[0],
        "-background",
        "transparent",
        "-font",
        font,
        "-pointsize",
        "%d" % font_size,
        "-stroke",
        stroke_color,
        "-strokewidth",
        "6",
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


def record(f, t="a", **kwargs):
    if not os.path.exists(f):
        f = "tmp/record/" + f + ".final.wav"
        assert os.path.exists(f)

    audio(f, t=t, **kwargs)

    END_CHAR = ["。", "，", "！", "、"]

    global _srt_index

    if ADD_SUBTITLE:
        assert len(_subtitle) > 0
        start = end = _get_pos("as")
        subtitle = _subtitle[-1].strip()

        if subtitle[-1] not in END_CHAR:
            subtitle += END_CHAR[0]

        length = len(subtitle)
        word_dura = (_get_pos("ae") - start) / length

        i = 0
        MAX = 5
        word = ""

        while i < length:
            if subtitle[i] in ["，", "。", "！"] and len(word) > MAX:
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


def vol(vol, duration=0.25, track=None, t=None):
    t = _get_pos(t)

    print("change vol=%.2f  at=%.2f  duration=%.2f" % (vol, t, duration))
    _get_audio_track(track).vol_keypoints.append((t, vol, duration))


def bgm_vol(v, **kwawgs):
    vol(v, track="bgm", **kwawgs)


def _add_audio_clip(
    file, track=None, t=None, subclip=None, duration=None, move_playhead=True
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
    f, move_playhead=False, t="a", in_duration=0.5, out_duration=0.5, vol=0.1, **kwargs
):
    print("bgm: %s" % f)
    t = _get_pos(t)

    if len(_get_audio_track("bgm").clips) > 0:
        bgm_vol(0, duration=out_duration, t=t - out_duration)
        audio_end(track="bgm", t=t, move_playhead=False)

    audio(f, track="bgm", move_playhead=move_playhead, t=t, **kwargs)
    bgm_vol(vol, duration=in_duration, t=t)


def sfx(f, **kwargs):
    audio(f, track="sfx", move_playhead=False, **kwargs)


def pos(p, tag=None):
    _set_pos(p, tag=tag)


def image(f, pos="center", **kwargs):
    print("image: %s" % f)
    _add_clip(f, pos=pos, **kwargs)


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
    tmp_file = "tmp/codeimg/%s.png" % _get_hash(s)
    if not os.path.exists(tmp_file):
        gen_code_image(s, out_file=tmp_file, line_no=line_no)
    _add_clip(tmp_file, track=track, **kwargs)


def code(s, track="vid", line_no=True, mark=[], debug=False, **kwargs):
    from r.web.webscreenshot import webscreenshot

    mkdir("tmp/codeimg")
    tmp_file = "tmp/codeimg/%s.png" % _get_hash(s + str(mark))
    if not os.path.exists(tmp_file):
        javascript = "setCode('%s'); " % s.replace("'", "\\'").replace("\n", "\\n")
        mark_group = list(zip(*(iter(mark),) * 4))
        for x in mark_group:
            javascript += "markText(%d, %d, %d, %d); " % (x[0], x[1], x[2], x[3])

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
    tmp_folder = os.path.join(
        tempfile.gettempdir(),
        "animation",
        os.path.splitext(os.path.basename(tar_file))[0],
    )

    # Unzip
    print2("Unzip to %s" % tmp_folder)
    shutil.unpack_archive(tar_file, tmp_folder)

    # Get all image files
    image_files = sorted(glob.glob((os.path.join(tmp_folder, "*.png"))))

    clip = ImageSequenceClip(image_files, fps=FPS)
    return clip


def _update_prev_clip(track):
    _clip_extend_prev_clip(track)

    # _add_fadeout(track)


def _create_mpy_clip(
    file=None,
    clip_operations=None,
    speed=None,
    pos=None,
    text_overlay=None,
    no_audio=False,
    duration=None,
    vol=None,
    transparent=True,
    subclip=None,
):
    if file is None:
        clip = ColorClip((200, 200), color=(0, 1, 0)).set_duration(0)

    elif file.endswith(".tar"):
        clip = create_image_seq_clip(file)

    elif file.endswith(".png"):
        clip = ImageClip(file).set_duration(5)
        if not transparent:
            clip = clip.set_mask(None)

    else:
        clip = VideoFileClip(file)

    if subclip is not None:
        clip = clip.subclip(subclip)

    if duration is not None:
        clip = clip.set_duration(duration)

    if speed is not None:
        clip = clip.fx(vfx.speedx, speed)

    if clip_operations is not None:
        clip = clip_operations(clip)

    if no_audio:
        clip = clip.set_audio(None)

    if clip.audio is not None and vol:
        if isinstance(vol, (int, float)):
            clip.audio = clip.audio.fx(afx.volumex, vol)
        else:
            clip.audio = _adjust_mpy_audio_clip_volume(clip.audio, vol)

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

    return clip


def _add_clip(
    file=None,
    clip_operations=None,
    speed=None,
    pos=None,
    track=None,
    fadein=False,
    fadeout=False,
    crossfade=None,
    t=None,
    duration=None,
    text_overlay=None,
    **kwargs
):
    track = _get_vid_track(track)

    # _update_prev_clip(track)

    t = _get_pos(t)
    _pos_dict["vs"] = t

    clip_info = _VideoClipInfo()
    clip_info.file = file
    clip_info.start = t
    clip_info.pos = pos
    clip_info.speed = speed
    clip_info.fadein = fadein
    clip_info.fadeout = fadeout
    clip_info.crossfade = crossfade or _crossfade
    clip_info.text_overlay = text_overlay
    clip_info.duration = duration

    if file is not None:
        clip_info.mpy_clip = _create_mpy_clip(
            file=file,
            clip_operations=clip_operations,
            speed=speed,
            pos=pos,
            duration=duration,
            **kwargs
        )

        # Advance the pos
        end = t + clip_info.mpy_clip.duration
        _pos_list.append(end)
        _pos_dict["ve"] = end

    track.append(clip_info)

    return clip_info


def _animation(url, name, track=None, params={}, calc_length=True, **kwargs):
    anim = _animations[name]
    anim.url = url
    anim.url_params = params
    anim.calc_length = calc_length
    anim.clip_info_list.append(_add_clip(track=track, **kwargs))


def anim(s, **kwargs):
    _animation(url="http://localhost:8080/%s.html" % s, name=slugify(s), **kwargs)


def image_anim(file, t=5, **kwargs):
    _animation(
        url="http://localhost:8080/image.html",
        name=os.path.splitext(file)[0],
        params={"t": "%d" % t, "src": file},
        **kwargs
    )


def title_anim(h1, h2, **kwargs):
    _animation(
        url="http://localhost:8080/title-animation.html",
        name=slugify("title-%s-%s" % (h1, h2)),
        params={"h1": h1, "h2": h2},
        **kwargs
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


def video(f, **kwargs):
    print("video: %s" % f)
    _add_clip(f, **kwargs)


def screencap(f, speed=None, track=None, **kwargs):
    print("screencap: %s" % f)
    _add_clip(
        "screencap/" + f,
        clip_operations=lambda x: x.crop(x1=0, y1=0, x2=2560, y2=1380)
        .resize(0.75)
        .set_position((0, 22)),
        speed=speed,
        track=track,
        **kwargs
    )


def md(s, track="md", fadein=True, fadeout=True, pos="center", name=None, **kwargs):
    mkdir("tmp/md")
    # out_file = "tmp/slides/%s.png" % slugify(name if name else s)
    out_file = "tmp/md/%s.png" % _get_hash(s)

    if not os.path.exists(out_file):
        generate_slide(
            s, template_file="markdown.html", out_file=out_file, gen_html=True
        )

    _add_clip(out_file, track=track, fadein=fadein, fadeout=fadeout, pos=pos, **kwargs)


def hl(pos, track="hl", **kwargs):
    image(
        "../image/highlight.png",
        pos=pos,
        track=track,
        fadein=True,
        fadeout=True,
        **kwargs
    )


def track(name="vid"):
    global _cur_vid_track_name
    _cur_vid_track_name = name


def _update_clip_duration(track):
    prev_clip_info = None
    for clip_info in track:
        if (prev_clip_info is not None) and (prev_clip_info.duration is None):
            prev_clip_info.duration = clip_info.start - prev_clip_info.start

        prev_clip_info = clip_info

    # update last clip duration
    if len(track) > 0 and track[-1].duration is None:
        track[-1].duration = track[-1].mpy_clip.duration


def _export_video(resolution=(1920, 1080), fps=25):
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

    # Animation
    if 1:
        for name, animation_info in _animations.items():
            out_file = "tmp/animation/%s.mov" % name
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

                    final_url = (
                        animation_info.url
                        + "?"
                        + "&".join(
                            [
                                "%s=%s" % (k, urllib.parse.quote(v))
                                for k, v in params.items()
                            ]
                        )
                    )

                    capture_animation.capture_js_animation(
                        url=final_url, out_file=out_file,
                    )

            for i, clip_info in enumerate(animation_info.clip_info_list):
                clip_info.mpy_clip = _create_mpy_clip(
                    file=(out_file if i == 0 else "tmp/animation/%s.%d.mov" % (name, i))
                )

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

                # crossfade?
                if i + 1 < len(track) and track[i + 1].crossfade:
                    duration += FADE_DURATION * 0.5

                clip_info.mpy_clip = clip_info.mpy_clip.set_duration(duration)

            if clip_info.fadein:
                # TODO: crossfadein and crossfadeout is very slow in moviepy
                if track_name != "vid":
                    clip_info.mpy_clip = clip_info.mpy_clip.crossfadein(FADE_DURATION)
                else:
                    clip_info.mpy_clip = clip_info.mpy_clip.fx(
                        vfx.fadein, FADE_DURATION
                    )

            if clip_info.fadeout:
                if track_name != "vid":
                    clip_info.mpy_clip = clip_info.mpy_clip.crossfadeout(FADE_DURATION)
                else:
                    clip_info.mpy_clip = clip_info.mpy_clip.fx(
                        vfx.fadeout, FADE_DURATION
                    )

            if clip_info.crossfade:
                video_clips.append(
                    clip_info.mpy_clip.set_duration(FADE_DURATION)
                    .crossfadein(FADE_DURATION)
                    .set_start(clip_info.start - 0.5 * FADE_DURATION)
                )
                video_clips.append(
                    clip_info.mpy_clip.set_start(clip_info.start + 0.5 * FADE_DURATION)
                )
            else:

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

            if clip_info.start is not None:
                clip = clip.set_start(clip_info.start)

            if clip_info.duration is not None:
                clip = clip.set_duration(clip_info.duration)

            clips.append(clip)

        if len(clips) > 0:
            clip = CompositeAudioClip(clips)
            if len(track.vol_keypoints) > 0:
                clip = _adjust_mpy_audio_clip_volume(clip, track.vol_keypoints)
                print(track.vol_keypoints)

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

    final_clip.write_videofile(
        "out.mp4", codec="libx264", threads=8, fps=fps, ffmpeg_params=["-crf", "19"]
    )

    open_with("out.mp4", program_id=1)


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


def tts():
    text = _subtitle[-1]
    hash = _get_hash(text)

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

    record(file_name)


def _parse_script(text):
    _subtitle.append(text)

    if AUTO_TTS:
        tts()


def _parse_text(text, **kwargs):
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

            exec(python_code, globals())

        elif text[p : p + 2] == "{{":
            end = find_next(text, "}}", p)
            python_code = text[p + 2 : end].strip()
            p = end + 2

            exec(python_code, globals())

        elif text[p : p + 1] == "#":
            p = find_next(text, "\n", p) + 1

        elif text[p : p + 3] == "---":
            p = find_next(text, "\n", p) + 1

        else:
            end = find_next(text, "\n", p)
            line = text[p:end].strip()
            p = end + 1

            if line != "":
                print2(line, color="green")
                _parse_script(line)

            # _export_srt()
        # sys.exit(0)

    _export_video(**kwargs)


if __name__ == "__main__":
    print(os.getcwd())

    parser = argparse.ArgumentParser()
    parser.add_argument("--stdin", default=False, action="store_true")
    parser.add_argument("-i", "--input", type=str, default=None)
    args = parser.parse_args()

    if args.stdin:
        s = sys.stdin.read()
        _parse_text(s)

    elif args.input:
        _parse_text(args.input)

    else:
        PROJ_DIR = r"{{VIDEO_PROJECT_DIR}}"

        FPS = int("{{_FPS}}") if "{{_FPS}}" else 25
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

            _parse_text(s)
