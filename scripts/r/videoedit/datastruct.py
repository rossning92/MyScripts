from typing import Any, Dict, List
from collections import OrderedDict


default_video_track_name = "vid"
default_audio_track_name = "record"


class VideoClip:
    def __init__(self):
        self.file = None
        self.start = 0
        self.duration = None
        self.mpy_clip = None
        self.speed = 1
        self.pos = None
        self.fadein = 0
        self.fadeout = 0
        self.crossfade = 0

        self.no_audio = False
        self.norm = False
        self.vol = None
        self.transparent = True
        self.subclip = None
        self.frame = None
        self.loop = False
        self.expand = False

        self.scale = (1.0, 1.0)
        self.width = None
        self.height = None

        self.auto_extend = True


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


video_tracks: Dict[str, List[VideoClip]] = OrderedDict(
    [
        ("bg", []),
        ("bg2", []),
        ("vid", []),
        ("vid2", []),
        ("vid3", []),
        ("hl", []),
        ("hl2", []),
        ("md", []),
        ("overlay", []),
        ("text", []),
    ]
)

audio_tracks: Dict[str, AudioTrack] = OrderedDict(
    [
        ("bgm", AudioTrack()),
        ("bgm2", AudioTrack()),
        ("record", AudioTrack()),
        ("sfx", AudioTrack()),
    ]
)


def _get_track(tracks, name):
    if name not in tracks:
        raise Exception("Track is not defined: %s" % name)
    track = tracks[name]

    return track


def get_vid_track(name=None):
    if name is None:
        name = default_video_track_name
    return _get_track(video_tracks, name)


def get_audio_track(name=None):
    if name is None:
        name = default_audio_track_name
    return _get_track(audio_tracks, name)
