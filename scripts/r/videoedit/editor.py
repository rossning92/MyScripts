import functools
import json
import math
import os
import re
import subprocess
import tarfile
from collections import OrderedDict
from pprint import pprint
from typing import Any, Dict, List, Literal, Optional, Sequence, Tuple, Union

import moviepy.audio.fx.all as afx
import moviepy.video.fx.all as vfx
import numpy as np
from _pkgmanager import require_package
from _shutil import call2, file_is_old, format_time, get_hash, mkdir, print2
from audio.postprocess import dynamic_audio_normalize, process_audio_file
from moviepy.editor import (
    AudioFileClip,
    ColorClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    ImageSequenceClip,
    VideoFileClip,
    concatenate_videoclips,
)
from PIL import Image
from utils.template import render_template

from . import common
from .export_movy_animation import export_movy_animation
from .render_text import render_text

SCRIPT_ROOT = os.path.dirname(os.path.abspath(__file__))


default_video_track_name = "vid"
default_audio_track_name = "record"


class VideoClip:
    def __init__(self):
        # Timing
        self.file = None
        self.start = 0
        self.duration = None
        self.subclip: Optional[Tuple[float, ...]] = None
        self.frame = None
        self.loop = False

        # Transform
        self.scale = (1.0, 1.0)
        self.width = None
        self.height = None
        self.pos = None
        self.transparent = True  # TODO: remove
        self.auto_extend = True
        self.filtering: Literal["linear", "nearest"] = "linear"

        # Vfx
        self.speed = 1
        self.fadein = 0
        self.fadeout = 0
        self.crossfade = 0

        # Audio
        self.no_audio = False
        self.norm = False
        self.vol = None

        # Metadata
        self.mpy_clip = None

    def __repr__(self):
        return f"VideoClip({os.path.basename(self.file)}, t={self.start:.1f}, d={self.duration:.1f})"


class AudioClip:
    def __init__(self):
        self.file: str = None
        self.mpy_clip: Any = None
        self.speed: float = 1
        self.start: float = None
        self.subclip: float = None
        self.vol_keypoints = []
        self.loop = False


class AudioTrack:
    def __init__(self):
        self.clips = []


VOLUME_DIM = 0.15
FADE_DURATION = 0.2
VIDEO_CROSSFADE_DURATION = FADE_DURATION
FPS = 30
IMAGE_SEQUENCE_FPS = FPS
DEFAULT_AUDIO_FADING_DURATION = 0.25
DEFAULT_IMAGE_CLIP_DURATION = 2
SUBTITLE_GAP_THRESHOLD = 0.5


class State:
    def __init__(self):
        self.global_scale = 1.0
        self.pos_dict = {"t": 0, "a": 0, "as": 0, "ae": 0, "vs": 0, "ve": 0}
        self.enable_subtitle = True
        self.audio_only = False
        self.cached_line_to_tts = None
        self.last_frame_indices: Dict[str, int] = {}
        self.enable_tts = False
        self.subtitle: List[str] = []
        self.srt_lines = []
        self.srt_index = 1
        self.last_subtitle_index = -1
        self.last_subtitle_end_time = 0.0
        self.crossfade = 0

        self.video_tracks: Dict[str, List[VideoClip]] = OrderedDict(
            [
                ("bg", []),
                ("bg2", []),
                ("vid", []),
                ("vid2", []),
                ("vid3", []),
                ("hl", []),
                ("hl2", []),
                ("md", []),
                ("md2", []),
                ("overlay", []),
                ("overlay2", []),
                ("text", []),
            ]
        )

        self.audio_tracks: Dict[str, AudioTrack] = OrderedDict(
            [
                ("bgm", AudioTrack()),
                ("bgm2", AudioTrack()),
                ("record", AudioTrack()),
                ("sfx", AudioTrack()),
            ]
        )


_state = State()


def get_pos_dict():
    return _state.pos_dict


def reset():
    global _state
    _state = State()


def _get_track(tracks, name):
    if name not in tracks:
        raise common.VideoEditException("Track is not defined: %s" % name)
    track = tracks[name]

    return track


def get_vid_track(name=None):
    if name is None:
        name = default_video_track_name
    return _get_track(_state.video_tracks, name)


def get_audio_track(name=None):
    if name is None:
        name = default_audio_track_name
    return _get_track(_state.audio_tracks, name)


def get_current_audio_pos():
    return _state.pos_dict["a"]


def _tts_to_wav_gtts(out_file, text):
    require_package("gtts")
    tmp_file = out_file + ".tmp.mp3"
    call2(["gtts-cli", text, "--lang", "zh", "--nocheck", "--output", tmp_file])
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
    if _state.cached_line_to_tts is None:
        return

    hash = get_hash(_state.cached_line_to_tts)

    mkdir("tmp/tts")
    out_file = "tmp/tts/%s.wav" % hash
    if not os.path.exists(out_file):
        print("generate tts file: %s" % out_file)

        _tts_to_wav_gtts(out_file, _state.cached_line_to_tts)

    record(out_file, postprocess=False, vol=2)

    _state.cached_line_to_tts = None


@common.on_api
def on_api_(func_name):
    if func_name != "record":
        _try_generate_tts()
    else:
        _state.cached_line_to_tts = None


@common.api
def crossfade(v):
    if v == True:
        _state.crossfade = VIDEO_CROSSFADE_DURATION
    else:
        _state.crossfade = float(v)


def _get_time(p):
    if isinstance(p, (int, float)):
        return p

    PATT_NUMBER = r"[+-]?(?:[0-9]*[.])?[0-9]+"

    if p is None:
        return _state.pos_dict["t"]

    if type(p) == int or type(p) == float:
        return float(p)

    if type(p) == str:
        if p in _state.pos_dict:
            return _state.pos_dict[p]

        match = re.match(r"^([a-z_]+)(" + PATT_NUMBER + ")$", p)
        if match:
            tag = match.group(1)
            assert match.group(2)
            delta = float(match.group(2))
            return _state.pos_dict[tag] + delta

    raise common.VideoEditException('Invalid pos="%s"' % p)


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


@common.api
def record(
    file,
    t="a",
    postprocess=True,
    move_playhead=True,
    subtitle=True,
    subtitle_duration=None,
    cut_voice=True,
    apad=0.1,
    silenceremove=True,
    **kwargs,
):
    if not os.path.exists(file):
        file = "record/" + file
        assert os.path.exists(file)

    # Post-process audio
    if postprocess:
        name_no_ext = os.path.splitext(os.path.basename(file))[0]
        out_file = "tmp/record/" + name_no_ext + ".wav"
        if file_is_old(file, out_file):
            process_audio_file(
                file,
                out_file,
                cut_voice=cut_voice,
                enable_silenceremove=silenceremove,
            )
        file = out_file

    audio(file, t=t, move_playhead=move_playhead, apad=apad, **kwargs)

    if move_playhead:
        _state.pos_dict["re"] = _get_time("ae")
        _state.pos_dict["t"] = _get_time("as")

    END_CHARS = ["。", "，", "、", "！", "；", "？", "|"]

    if _state.enable_subtitle and subtitle and not _state.audio_only:
        if len(_state.subtitle) == 0:
            print("WARNING: no subtitle found")

        else:
            idx = len(_state.subtitle) - 1
            if _state.last_subtitle_index == idx:
                print2("WARNING: subtitle used twice: %s" % _state.subtitle[idx])
            else:
                _state.last_subtitle_index = idx

                start = end = _get_time("as")
                subtitle = _state.subtitle[idx].strip()

                if subtitle[-1] not in END_CHARS:
                    subtitle += END_CHARS[0]

                length = len(subtitle)
                if subtitle_duration is not None:
                    char_duration = subtitle_duration / length
                else:
                    char_duration = (_get_time("ae") - start) / length

                MIN_SENTENSE_LEN = 8
                sentense = ""
                for i, ch in enumerate(subtitle):
                    if (
                        ch in END_CHARS
                        and len(sentense) >= MIN_SENTENSE_LEN
                        and i < length - MIN_SENTENSE_LEN
                    ) or i == length - 1:
                        _state.srt_lines.extend(
                            [
                                "%d" % _state.srt_index,
                                "%s --> %s" % (format_time(start), format_time(end)),
                                sentense,
                                "",
                            ]
                        )

                        # Skip tiny gaps between subtitles
                        if (
                            abs(start - _state.last_subtitle_end_time)
                            < SUBTITLE_GAP_THRESHOLD
                        ):
                            start = _state.last_subtitle_end_time
                        _add_subtitle_clip(
                            start=start,
                            end=end,
                            text=sentense,
                        )
                        _state.last_subtitle_end_time = end

                        end += char_duration
                        start = end
                        sentense = ""
                        _state.srt_index += 1
                    else:
                        if ch in END_CHARS:
                            sentense += " "
                        else:
                            sentense += ch
                        end += char_duration


@common.api
def audio_gap(duration, bgm_vol=None, fade_duration=0.5):
    if bgm_vol is not None:
        last_bgm_clip = get_last_audio_clip(track="bgm")
        if last_bgm_clip is not None:
            _, prev_vol = last_bgm_clip.vol_keypoints[-1]
            globals()["bgm_vol"](bgm_vol, t="ae", duration=fade_duration)

    _state.pos_dict["a"] += duration
    _state.pos_dict["ae"] = _state.pos_dict["as"] = _state.pos_dict["a"]
    _state.pos_dict["t"] = _state.pos_dict["a"]

    if bgm_vol is not None and last_bgm_clip is not None:
        globals()["bgm_vol"](prev_vol, t="a-%g" % fade_duration, duration=fade_duration)


def get_last_audio_clip(track=None):
    track_ = get_audio_track(track)
    if len(track_.clips) == 0:
        print2("WARNING: No audio clip to set volume in track: %s" % track)
        return

    return track_.clips[-1]


def _set_vol(vol, duration=0, track=None, t=None):
    """Set volume of a specific track at a given time. Returns previous volume."""

    assert duration >= 0

    t = _get_time(t)

    print("change vol=%.2f  at=%.2f  duration=%.2f" % (vol, t, duration))
    last_audio_clip = get_last_audio_clip(track)

    t_in_clip = t - last_audio_clip.start
    assert t_in_clip >= 0

    # Add keypoints
    if len(last_audio_clip.vol_keypoints) > 0:  # has previous keypoint
        prev_t, prev_vol = last_audio_clip.vol_keypoints[-1]
        if t_in_clip <= prev_t:
            raise Exception(
                "The current keypoint ts must be later than the previous keypoint"
            )
        last_audio_clip.vol_keypoints.append((t_in_clip, prev_vol))
    else:
        prev_vol = vol

    last_audio_clip.vol_keypoints.append((t_in_clip + duration, vol))

    return prev_vol


@common.api
def setp(name, t=None):
    t = _get_time(t)
    _state.pos_dict[name] = t


@common.api
def vol(vol, duration=DEFAULT_AUDIO_FADING_DURATION, **kwargs):
    return _set_vol(vol, duration=duration, **kwargs)


@common.api
def bgm_vol(vol, duration=DEFAULT_AUDIO_FADING_DURATION, **kwawgs):
    _set_vol(vol, duration=duration, track="bgm", **kwawgs)


@functools.lru_cache(maxsize=None)
def _load_audio_clip(file):
    return AudioFileClip(file, buffersize=400000)


def _add_audio_clip(
    file,
    track=None,
    t=None,
    subclip=None,
    duration=None,
    move_playhead=True,
    loop=False,
    apad=0.0,
):
    clips = get_audio_track(track).clips

    t = _get_time(t)

    if move_playhead:
        _state.pos_dict["as"] = t

    clip_info = AudioClip()

    if not os.path.exists(file):
        raise common.VideoEditException('Clip file "%s" does not exist.' % file)
    clip_info.file = os.path.abspath(file)

    # HACK: still don't know why changing buffersize would help reduce the noise at the end
    clip_info.mpy_clip = _load_audio_clip(file)

    if subclip is not None:
        if isinstance(subclip, (int, float)):
            clip_info.subclip = (subclip, clip_info.mpy_clip.duration)
        else:
            clip_info.subclip = subclip
    else:
        clip_info.subclip = None

    clip_info.duration = None
    clip_info.start = t
    clip_info.loop = loop

    if move_playhead:
        # Forward audio track pos
        _state.pos_dict["t"] = _state.pos_dict["a"] = _state.pos_dict["ae"] = (
            _state.pos_dict["as"]
            + (
                clip_info.mpy_clip.duration
                if clip_info.duration is None
                else clip_info.duration
            )
            + apad
        )

    clips.append(clip_info)

    return clip_info


@common.api
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
    apad=0.0,
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

    clip = _add_audio_clip(
        f, t=t, track=track, move_playhead=move_playhead, apad=apad, **kwargs
    )

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


@common.api
def audio_end(track, t=None, move_playhead=True, fadeout=0, crossfade=0):
    t = _get_time(t)

    clips = get_audio_track(track).clips
    if len(clips) == 0:
        print2("WARNING: no previous audio clip to set the end point.")
        return

    # Fade out of previous audio clip
    duration = None
    if len(get_audio_track(track).clips) > 0:
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
        _state.pos_dict["t"] = _state.pos_dict["a"] = t


@common.api
def bgm(
    f,
    move_playhead=False,
    vol=0.08,
    track="bgm",
    norm=True,
    loop=True,
    **kwargs,
):
    print("bgm: %s" % f)

    if norm:
        f = dynamic_audio_normalize(f)

    audio(
        f,
        track=track,
        move_playhead=move_playhead,
        loop=loop,
        vol=vol,
        **kwargs,
    )


@common.api
def sfx(f, **kwargs):
    audio(f, track="sfx", move_playhead=False, **kwargs)


@common.api
def pos(t, tag=None):
    t = _get_time(t)
    if tag is not None:
        _state.pos_dict[tag] = t
    else:
        _state.pos_dict = {k: t for k in _state.pos_dict.keys()}


def get_pos(tag):
    return _state.pos_dict[tag]


@common.api
def clip(file, **kwargs):
    if _state.audio_only:
        return

    print("clip: %s" % file)
    _add_video_clip(file, **kwargs)


@common.api
def fps(v):
    global FPS
    FPS = v


@common.api
def overlay(
    file,
    duration=3,
    crossfade=VIDEO_CROSSFADE_DURATION,
    fadeout=VIDEO_CROSSFADE_DURATION,
    track="overlay",
    **kwargs,
):
    if _state.audio_only:
        return

    print("image: %s" % file)
    _add_video_clip(
        file,
        duration=duration,
        crossfade=crossfade,
        fadeout=fadeout,
        track=track,
        **kwargs,
    )


@common.api
def comment(text, pos=(960, 100), duration=4, track="overlay", **kwargs):
    md(
        text,
        pos=pos,
        duration=duration,
        track=track,
        **kwargs,
    )


@common.api
def credit(text, pos=(960, 40), duration=4, track="overlay", **kwargs):
    md(
        '<span style="font-size:0.6em">%s</span>' % text,
        pos=pos,
        duration=duration,
        track=track,
        **kwargs,
    )


def _get_video_resolution(file):
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
                file,
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


@functools.lru_cache(maxsize=None)
def _load_mpy_clip(
    file,
    scale=(1.0, 1.0),
    frame=None,
    transparent=True,
    width=None,
    height=None,
    filtering: Literal["linear", "nearest"] = "linear",
):

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
        if (
            scale[0] != 1.0
            or scale[1] != 1.0
            or width is not None
            or height is not None
        ) and filtering == "linear":
            w, h = _get_video_resolution(f)
            w, h = compute_size(w, h)
            target_resolution = [int(h * scale[0]), int(w * scale[1])]
        else:
            target_resolution = None

        return VideoFileClip(
            f,
            target_resolution=target_resolution,
            # has_mask=transparent and f.endswith(".gif"),
        )

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
            clip = ImageClip(file).set_duration(DEFAULT_IMAGE_CLIP_DURATION)
            if not export_shapes:
                clip = clip.set_mask(None)

    elif file.endswith(".png") or file.endswith(".jpg"):
        clip = ImageClip(file)

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
    subclip: Optional[Union[Sequence[Union[float, str]], Union[float, str]]] = None,
    frame=None,
    n=None,
    loop=False,
    scale=(1.0, 1.0),
    width=None,
    height=None,
    filtering: Literal["linear", "nearest"] = "linear",
    **_,
):
    subclip2: Optional[Tuple[float, ...]] = None
    if subclip is not None:
        if isinstance(subclip, (int, float, str)):
            subclip = (subclip,)

        metadata_file = os.path.splitext(file)[0] + ".json"
        if os.path.exists(metadata_file):
            with open(metadata_file, "r", encoding="utf-8") as f:
                medadata = json.load(f)

                def get_time_by_marker(name: str) -> float:
                    for marker in medadata["markers"]:
                        if marker["name"] == name:
                            return marker["time"]
                    raise common.VideoEditException('Marker "%s" not found' % name)

                # replace marker with time
                subclip2 = tuple(
                    [
                        get_time_by_marker(x) if isinstance(x, str) else x
                        for x in subclip
                    ]
                )
        else:
            subclip2 = tuple((float(x) for x in subclip))

    clip_info = VideoClip()

    # Alias
    if n is not None:
        frame = n
    if cf is not None:
        crossfade = cf

    # Extract only one frame
    if frame is not None:
        if frame == "next":
            frame = _state.last_frame_indices[file] + 1
        if type(frame) != int:
            raise common.VideoEditException(f"Invalid frame param: {frame}")
        _state.last_frame_indices[file] = frame
    clip_info.frame = frame

    if isinstance(scale, (int, float)):
        scale = (scale, scale)

    track = get_vid_track(track)
    t = _get_time(t)

    if move_playhead:
        _state.pos_dict["vs"] = t

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
        elif _state.crossfade:
            clip_info.crossfade = _state.crossfade
    clip_info.fadeout = fadeout

    if duration is not None:
        clip_info.auto_extend = False

    clip_info.no_audio = no_audio or na
    clip_info.norm = norm
    clip_info.vol = vol

    if track is None or track == "vid":
        transparent = False
    clip_info.transparent = transparent
    clip_info.subclip = subclip2
    clip_info.loop = True if file.endswith(".gif") else loop
    clip_info.scale = (scale[0] * _state.global_scale, scale[1] * _state.global_scale)
    clip_info.width = width
    clip_info.height = height
    clip_info.filtering = filtering

    # Load mpy clip
    clip_info.mpy_clip = _load_mpy_clip(
        file=clip_info.file,
        scale=clip_info.scale,
        frame=clip_info.frame,
        transparent=clip_info.transparent,
        width=clip_info.width,
        height=clip_info.height,
        filtering=filtering,
    )
    if isinstance(clip_info.mpy_clip, VideoFileClip) and filtering == "linear":
        clip_info.scale = (1.0, 1.0)  # HACK: video file clip are pre-scaled

    # Duration
    if duration is None:
        if subclip2 is not None:
            if len(subclip2) == 1:
                duration = (
                    clip_info.mpy_clip.duration / (speed if speed else 1) - subclip2[0]
                )
            else:
                duration = subclip2[1] - subclip2[0]
        else:
            duration = clip_info.mpy_clip.duration / (speed if speed else 1)
    clip_info.duration = duration

    if move_playhead:  # Advance the pos
        end = t + duration
        _state.pos_dict["t"] = _state.pos_dict["ve"] = end

    while len(track) > 0 and clip_info.start < track[-1].start:
        print(
            "WARNING: clip(file=%s, t=%d) has been removed"
            % (track[-1].file, clip_info.start)
        )
        track.pop()

    track.append(clip_info)

    return clip_info


prev_anim_clip: Optional[VideoClip] = None


@common.api
def anim(file, format: Literal["webm", "png"] = "webm", **kwargs):
    global prev_anim_clip

    if _state.audio_only:
        return

    # Generate video file from .js file
    if format == "webm":
        ext = ".webm"
    elif format == "png":
        ext = ".tar"
    else:
        raise Exception("Invalid format specified: {format}")

    base_name = os.path.basename(os.path.splitext(file)[0])
    out_file = f"tmp/animation/{base_name}{ext}"

    if file_is_old(file, out_file):
        # Remove old video file
        if os.path.exists(out_file):
            os.remove(out_file)

        # Remove old metadata file
        metadata_file = "tmp/animation/%s.json" % base_name
        if os.path.exists(metadata_file):
            os.remove(metadata_file)

        mkdir("tmp/animation")
        base_name = os.path.splitext(os.path.basename(file))[0]
        export_movy_animation(
            os.path.abspath(file),
            out_file=out_file,
        )

    clip_info = _add_video_clip(out_file, **kwargs)

    if clip_info.subclip is not None:
        assert type(clip_info.subclip) == tuple
        if prev_anim_clip:
            if prev_anim_clip.file == os.path.abspath(out_file):
                if (
                    prev_anim_clip.subclip is not None
                    and len(prev_anim_clip.subclip) == 1
                ):
                    prev_anim_clip.subclip = (
                        prev_anim_clip.subclip[0],
                        clip_info.subclip[0],
                    )
                    print("Update prev anim clip subclip:", prev_anim_clip.subclip)

    prev_anim_clip = clip_info


@common.api
def video_end(track=None, t=None, fadeout=None):
    if _state.audio_only:
        return

    track_name = track if track else default_video_track_name
    print('video_end(track="%s")' % track_name)
    track = get_vid_track(track)

    if len(track) == 0:
        raise common.VideoEditException(f'track "{track_name}" has no clip yet')

    clip = track[-1]
    clip.duration = _get_time(t) - clip.start
    clip.auto_extend = False

    if fadeout is not None:
        clip.fadeout = fadeout

    print("clip updated: start=%.2f duration=%.2f" % (clip.start, clip.duration))


@common.api
def empty(**kwargs):
    if _state.audio_only:
        return

    _add_video_clip(None, **kwargs)


def _generate_slide(in_file, template, out_file=None, public=None):
    args = [
        "run_script",
        "r/videoedit/slide/export.js",
        "-i",
        os.path.realpath(in_file),
        "-o",
        os.path.realpath(out_file),
        "-t",
        template,
    ]

    if public:
        args += ["--public", public]
    call2(args)


@common.api
def slide(
    s,
    template,
    pos="center",
    name=None,
    **kwargs,
):
    if os.path.exists(s):
        mkdir("tmp/md")
        out_file = "tmp/md/%s.png" % get_hash(s)
        if file_is_old(s, out_file):
            _generate_slide(s, template=template, out_file=out_file, public=os.getcwd())

    else:
        mkdir("tmp/md")
        hash = get_hash(s)
        in_file = "tmp/md/%s.md" % hash
        out_file = "tmp/md/%s.png" % hash

        if not os.path.exists(out_file):
            with open(in_file, "w", encoding="utf-8") as f:
                f.write(s)

            _generate_slide(
                in_file, template=template, out_file=out_file, public=os.getcwd()
            )

    _add_video_clip(out_file, pos=pos, **kwargs)


@common.api
def md(s, track="md", move_playhead=False, **kwargs):
    slide(
        s,
        track=track,
        template="markdown",
        crossfade=VIDEO_CROSSFADE_DURATION,
        move_playhead=move_playhead,
        **kwargs,
    )


@common.api
def code(file, **kwargs):
    _, ext = os.path.splitext(file)
    with open(file, encoding="utf-8") as f:
        s = f.read()

    s = render_template(s, context=kwargs)

    base_name = get_hash(s)
    out_file = f"tmp/code/{base_name}.md"
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(f'```{ext.lstrip(".")}\n' f"{s}\n" "```\n")

    slide(out_file, template="code", **kwargs)


@common.api
def hl(pos=None, rect=None, track="hl", duration=2, file=None, **kwargs):
    if _state.audio_only:
        return

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
            pos=(rect[0] + rect[2] * 0.5, rect[1] + rect[3] * 0.5),
            scale=(rect[2] / 100, rect[3] / 100),
            **extra_args,
        )


@common.api
def tts(enabled=True):
    _state.enable_tts = enabled


def _remove_bold_italic_markers(text: str) -> str:
    """
    Remove Markdown bold and italic markers (*, _, **, __, ***, ___)
    from the given text while keeping the plain text content.
    """
    # Remove *** or ___ (bold+italic combined)
    text = re.sub(r"(\*\*\*|___)(.*?)\1", r"\2", text)
    # Remove ** or __ (bold)
    text = re.sub(r"(\*\*|__)(.*?)\1", r"\2", text)
    # Remove * or _ (italic)
    text = re.sub(r"(\*|_)(.*?)\1", r"\2", text)
    return text


@common.api
def parse_line(line):
    line = _remove_bold_italic_markers(line)

    print2(line, color="green")
    _state.subtitle.append(line)

    if _state.enable_tts:
        _state.cached_line_to_tts = line


def enable_preview():
    _state.global_scale = 0.25
    tts(True)


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
    width,
    height,
    vol,
    filtering: Literal["linear", "nearest"],
    **kwargs,
):
    assert duration is not None

    # Must adjust clip speed first
    if speed is not None:
        clip = clip.fx(
            # pylint: disable=maybe-no-member
            vfx.speedx,
            speed,
        )

    # video clip operations / fx
    if subclip is not None:
        assert isinstance(subclip, (tuple, list))
        assert len(subclip) == 1 or len(subclip) == 2
        if len(subclip) == 1 or subclip[1] == -1:
            clip = clip.subclip(subclip[0]).set_duration(duration)
        else:
            subclip_duration = subclip[1] - subclip[0]
            if loop:
                clip = clip.subclip(subclip[0], subclip[1]).set_duration(
                    subclip_duration
                )
            elif duration > subclip_duration:
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

    if frame is not None:
        clip = clip.to_ImageClip(frame).set_duration(duration)

    # Loop or change duration
    if loop:
        clip = clip.fx(
            # pylint: disable=maybe-no-member
            vfx.loop,
            duration=duration,
        )

    if subclip is None:
        clip = clip.set_duration(duration)

    # Scale should be done before translation
    if scale[0] != 1.0 or scale[1] != 1.0 or width is not None or height is not None:
        if width and height:
            target_size = (int(width * scale[0]), int(height * scale[1]))
        elif width:
            aspect = clip.w / clip.h
            target_size = (int(width * scale[0]), int(width / aspect * scale[1]))
        elif height:
            aspect = clip.w / clip.h
            target_size = (int(height * aspect * scale[0]), int(height * scale[1]))
        else:
            target_size = (int(clip.w * scale[0]), int(clip.h * scale[1]))

        if filtering == "linear":
            if not isinstance(clip, VideoFileClip):  # VideoFileClip are pre-scaled
                clip = clip.resize(target_size)
        else:

            def resize_nearest(target_size):
                """Return a function to be used with clip.fl() that resizes frames to `target_size`."""

                def fl_func(get_frame, t):
                    frame = get_frame(t)
                    img = Image.fromarray(frame)
                    img_resized = img.resize(
                        target_size, resample=Image.Resampling.NEAREST
                    )
                    return np.array(img_resized)

                return fl_func

            clip = clip.fl(resize_nearest(target_size))

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
                    pos[i] = int(_state.global_scale * pos[i])
                    pos[i] = pos[i] - half_size[i]
            clip = clip.set_position(pos)
        else:
            clip = clip.set_position(pos)

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
                assert prev_clip_info.duration > 0
                prev_clip_info.auto_extend = False

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
            if "re" in _state.pos_dict:
                duration = max(duration, _state.pos_dict["re"] - clip_info.start)

            prev_clip_info.duration = duration
            prev_clip_info.auto_extend = False

        if prev_clip_info.crossfade > 0:
            prev_clip_info.fadeout = prev_clip_info.crossfade


def _adjust_mpy_audio_clip_volume(clip, vol_keypoints):
    xp = []
    fp = []

    for p, vol in vol_keypoints:
        if isinstance(vol, (int, float)):
            xp.append(p)
            fp.append(vol)
        else:
            raise common.VideoEditException(
                "Unsupported bgm parameter type:" % type(vol)
            )

    def volume_adjust(gf, t):
        factor = np.interp(t, xp, fp)
        factor = np.vstack([factor, factor]).T
        return factor * gf(t)

    return clip.fl(volume_adjust)


def set_audio_only(audio_only=True):
    _state.audio_only = audio_only
    if _state.audio_only:
        print("Audio only enabled.")


def export_video(*, out_filename, resolution, preview=False):
    resolution = [int(x * _state.global_scale) for x in resolution]

    audio_clips = []

    # Update clip duration for each track
    for track in _state.video_tracks.values():
        _update_clip_duration(track)

    # TODO: post-process video track clips

    # Output
    for track_name, track in _state.video_tracks.items():
        if len(track) > 0:
            pprint({track_name: track})

    # Update MoviePy clip object in each track.
    video_clips = []
    for track_name, track in _state.video_tracks.items():
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
                    assert len(clip_info.subclip) == 2 and clip_info.subclip[1] > 0
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
    for _, track in _state.audio_tracks.items():
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
        final_audio_clip.fps = 44100

        final_clip = final_clip.set_audio(final_audio_clip)

    # final_clip.show(10.5, interactive=True)

    os.makedirs("tmp/out", exist_ok=True)

    if _state.audio_only:
        final_audio_clip.fps = 44100
        final_audio_clip.write_audiofile("%s.mp3" % out_filename)
        return "%s.mp3" % out_filename

    else:
        if preview:
            final_clip.preview(fps=15)
            import pygame

            pygame.quit()
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
            return "%s.mp4" % out_filename
