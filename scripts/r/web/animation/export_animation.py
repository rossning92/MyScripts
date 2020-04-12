from typing import Any, NamedTuple
import webbrowser
import urllib
import re
import capture_animation
from slide.generate import generate_slide
from r.open_with.open_with_ import open_with
from _shutil import *
from collections import defaultdict

if 1:
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))


if 1:  # Import moviepy
    f = glob.glob(r'C:\Program Files\ImageMagick-*\magick.exe')[0]
    os.environ['IMAGEMAGICK_BINARY'] = f
    from moviepy.config import change_settings
    from moviepy.editor import *
    import moviepy.video.fx.all as vfx

change_settings({"FFMPEG_BINARY": "ffmpeg"})

PROJ_DIR = r'{{VIDEO_PROJECT_DIR}}'

FPS = int('{{_FPS}}')
FADEOUT_DURATION = 0.25
PARSE_LINE_START = int(
    '{{_PARSE_LINE_START}}') if '{{_PARSE_LINE_START}}' else None
PARSE_LINE_END = int(
    '{{_PARSE_LINE_END}}') if '{{_PARSE_LINE_END}}' else None


class _ClipInfo:
    def __init__(self):
        self.file: str = None
        self.start: float = 0
        self.duration: float = None
        self.mpy_clip: Any = None
        self.speed: float = 1
        self.pos = None


class _AnimationInfo:
    def __init__(self):
        self.clip_info_list = []
        self.url = None
        self.url_params = {}


audio_clips = []
cur_markers = None

_audio_track_cur_pos = 0
_pos_list = [0]
_pos_tags = {}

_audio_track_cur_duration = 0


_add_fadeout_to_last_clip = False

_video_tracks = {}
_cur_vid_track_name = '@'  # default video track

_animations = defaultdict(_AnimationInfo)


def _get_vid_track(name=None):
    if name is None:
        name = _cur_vid_track_name

    if name not in _video_tracks:
        track = []
        _video_tracks[name] = track
    else:
        track = _video_tracks[name]

    return track


def _get_markers(file):
    marker_file = file + '.marker.txt'
    if os.path.exists(marker_file):
        with open(marker_file, 'r') as f:
            s = f.read()
            return [float(x) for x in s.split()]
    else:
        return None


def get_meta_data(type_):
    s = open('index.md', 'r', encoding='utf-8').read()
    matches = re.findall(r'<!-- ' + type_ + r'([\w\W]+?)-->', s)
    matches = [x.strip() for x in matches]
    return matches


def get_all_meta_data():
    s = open('index.md', 'r', encoding='utf-8').read()
    matches = re.findall(r'<!--\s*([a-zA-z-_]+:[\d\D]+?)\s*-->', s)
    matches = [x.strip() for x in matches]
    return matches


def get_all_python_block():
    lines = open('index.md', 'r', encoding='utf-8').readlines()

    if PARSE_LINE_START is not None:
        lines = lines[(PARSE_LINE_START - 1): (PARSE_LINE_END)]

    s = '\n'.join(lines)

    matches = re.findall(r'<!---\s*([\w\W]+?)\s*-->', s)
    matches = [x.strip() for x in matches]
    return matches


def record(f):
    print(f)
    audio('out/record/' + f)


def audio(f):
    global _audio_track_cur_pos, _audio_track_cur_duration, audio_clips, cur_markers

    _audio_track_cur_pos += _audio_track_cur_duration

    # Also forward video track pos
    _pos_tags['audio'] = _audio_track_cur_pos
    _pos_list.append(_audio_track_cur_pos)

    # HACK: still don't know why changing buffersize would help reduce the noise at the end
    audio_clip = AudioFileClip(f, buffersize=400000)

    audio_clip = audio_clip.set_start(_audio_track_cur_pos)

    audio_clips.append(audio_clip)

    _audio_track_cur_duration = audio_clip.duration

    # Get markers
    cur_markers = _get_markers(f)
    if cur_markers:
        print(cur_markers)


def pos(p):
    PATT_FLOAT = r'([-+]?\d*\.?\d*)'

    success = False
    if type(p) == str:
        match = re.match(r'^\+=' + PATT_FLOAT + '$', p)
        if match:
            delta = float(match.group(1))

            _pos_list.append(_pos_list[-1] + delta)

            return

        match = re.match(r'^\<' + PATT_FLOAT + '$', p)
        if match:
            delta = float(match.group(1))
            clip_info = _get_vid_track()[-1]

            _pos_list.append(clip_info.start + delta)

            return

        match = re.match(r'^(\^+)' + PATT_FLOAT + '$', p)
        if match:
            index_back_in_history = len(match.group(1))
            delta = float(match.group(2))
            _pos_list.append(
                _pos_list[-index_back_in_history - 1] + delta)

            return

        match = re.match(r'^([a-z_]+)' + PATT_FLOAT + '$', p)
        if match:
            tag = match.group(1)
            delta = float(match.group(2))
            _pos_list.append(_pos_tags[tag] + delta)

            return

    raise Exception('Invalid param.')


def image(f, pos=None, track=None):
    _add_clip(f, pos=pos, track=track)


def _add_fadeout(track):
    global _add_fadeout_to_last_clip

    if _add_fadeout_to_last_clip:
        clip_info = track[-1]

        if clip_info.mpy_clip is not None:
            clip_info.mpy_clip = clip_info.mpy_clip.fx(
                vfx.fadeout, FADEOUT_DURATION)

            _add_fadeout_to_last_clip = False


def create_image_seq_clip(tar_file):
    tmp_folder = os.path.join(tempfile.gettempdir(), 'animation',
                              os.path.splitext(os.path.basename(tar_file))[0])

    # Unzip
    print2('Unzip to %s' % tmp_folder)
    shutil.unpack_archive(tar_file, tmp_folder)

    # Get all image files
    image_files = sorted(glob.glob((os.path.join(tmp_folder, '*.png'))))

    clip = ImageSequenceClip(image_files, fps=FPS)
    return clip


def _update_prev_clip(track):
    _clip_extend_prev_clip(track)

    # _add_fadeout(track)


def _create_mpy_clip(file=None, clip_operations=None, speed=None, pos=None):
    if file is None:
        clip = ColorClip((200, 200), color=(0, 1, 0)).set_duration(0)

    elif file.endswith('.tar'):
        clip = create_image_seq_clip(file)

    elif file.endswith('.png'):
        clip = ImageClip(file).set_duration(
            2).crossfadein(FADEOUT_DURATION)

    else:
        clip = VideoFileClip(file)

    if speed is not None:
        clip = clip.fx(vfx.speedx, speed)

    if clip_operations is not None:
        clip = clip_operations(clip)

    if pos is not None:
        half_size = [x // 2 for x in clip.size]
        clip = clip.set_position(
            (pos[0] - half_size[0], pos[1] - half_size[1]))

    return clip


def _add_clip(file=None, clip_operations=None, speed=None, pos=None, tag=None, track=None):
    track = _get_vid_track(track)

    _update_prev_clip(track)

    cur_pos = _pos_list[-1]

    if tag:
        _pos_tags[tag] = cur_pos

    clip_info = _ClipInfo()

    if file is not None:
        clip_info.mpy_clip = _create_mpy_clip(
            file=file,
            clip_operations=clip_operations,
            speed=speed,
            pos=pos
        )

        # Advance the pos
        _pos_list.append(cur_pos + clip_info.mpy_clip.duration)

    clip_info.start = cur_pos
    clip_info.pos = pos
    clip_info.speed = speed
    track.append(clip_info)

    return clip_info


def _animation(url, name, track=None, params={}):
    anim = _animations[name]
    anim.url = url
    anim.url_params = params
    anim.clip_info_list.append(_add_clip(track=track))


def anim(s):
    _animation(
        url='http://localhost:8080/%s.html' % s,
        name=slugify(s),
    )


def image_anim(file, t=5):
    _animation(
        url='http://localhost:8080/image.html',
        name=os.path.splitext(file)[0],
        params={'t': '%d' % t, 'src': file}
    )


def title_anim(h1, h2):
    _animation(
        url='http://localhost:8080/title-animation.html',
        name=slugify('title-%s-%s' % (h1, h2)),
        params={'h1': h1, 'h2': h2},
    )


def _clip_extend_prev_clip(track=None):
    if len(track) == 0:
        return

    clip_info = track[-1]

    if clip_info.duration is None:
        clip_info.duration = _pos_list[-1] - clip_info.start
        print('previous clip start, duration updated: %.2f, %.2f' %
              (clip_info.start, clip_info.duration))


def empty(track=None):
    track = _get_vid_track(track)
    _clip_extend_prev_clip(track)


# TODO: This does not work
def fadeout():
    global _add_fadeout_to_last_clip
    _add_fadeout_to_last_clip = True


# TODO: This does not work
def list_anim(s):
    out_file = 'animation/list-animation-' + slugify(s) + '.mov'
    print(out_file)

    os.makedirs('animation', exist_ok=True)
    if not os.path.exists(out_file):
        url = 'http://localhost:8080/list-animation.html?s=%s' % (
            urllib.parse.quote(s)
        )
        capture_animation.capture_js_animation(
            url,
            out_file=out_file)

    # Get markers
    # markers = _get_markers(out_file)

    _get_vid_track().append(clip)


def video(f, track=None, pos=None):
    print('Video: %s' % f)
    _add_clip(f, tag='video', track=track, pos=pos)


def screencap(f, speed=None, track=None):
    _add_clip(
        f,
        clip_operations=lambda x: x.crop(
            x1=0, y1=0, x2=2560, y2=1380).resize(0.75).set_position((0, 22)),
        speed=speed,
        tag='video',
        track=track,
    )


def md(s, track='text'):
    mkdir('tmp/slides')
    out_file = 'tmp/slides/%s.png' % slugify(s)

    if not os.path.exists(out_file):
        generate_slide(s,
                       template_file='markdown.html',
                       out_file=out_file,
                       gen_html=True)

    _add_clip(out_file, track=track)


def hl(pos, track='hl'):
    image('images/highlight.png', pos=pos, track=track)


def track(name='@'):
    global _cur_vid_track_name
    _cur_vid_track_name = name


def export_video(resolution=(1920, 1080), fps=FPS):
    # Update last clip for each track.
    for track in _video_tracks.values():
        _update_prev_clip(track)

    # Animation
    if 1:
        for name, animation_info in _animations.items():
            subclip_dura_list = '|'.join(
                ['%g' % x.duration for x in animation_info.clip_info_list])
            print(subclip_dura_list)
            out_file = 'tmp/animation/%s.mov' % name
            os.makedirs('tmp/animation', exist_ok=True)

            if 1:  # generate animation video file

                if not os.path.exists(out_file):
                    params = {
                        'cut': subclip_dura_list,
                        **animation_info.url_params
                    }

                    final_url = animation_info.url + '?' + '&'.join([
                        '%s=%s' % (k, urllib.parse.quote(
                            v)) for k, v in params.items()
                    ])

                    capture_animation.capture_js_animation(
                        url=final_url,
                        out_file=out_file,
                    )

            for i, clip_info in enumerate(animation_info.clip_info_list):
                clip_info.mpy_clip = _create_mpy_clip(
                    file=(out_file if i == 0 else 'tmp/animation/%s.%d.mov' % (name, i)))

    # Update clip length and fx for each track.
    for track in _video_tracks.values():
        for clip_info in track:
            assert (clip_info.mpy_clip is not None) and (
                clip_info.duration is not None)

            # Use duration to extend / hold the last frame instead of creating new clips.
            clip_info.mpy_clip = clip_info.mpy_clip.set_duration(
                clip_info.duration)

    if audio_clips:
        final_audio_clip = CompositeAudioClip(audio_clips)
        # final_audio_clip.write_audiofile('out.wav')
    else:
        final_audio_clip = None

    video_clips = []
    for _, track in sorted(_video_tracks.items()):
        for clip_info in track:
            video_clips.append(clip_info.mpy_clip.set_start(clip_info.start))
    final_clip = CompositeVideoClip(
        video_clips, size=resolution).set_audio(final_audio_clip)

    # final_clip.show(10.5, interactive=True)
    # final_clip.preview(fps=10, audio=False)

    final_clip.write_videofile(
        'out.mp4', codec='libx264', threads=8, fps=fps,
        ffmpeg_params=['-crf', '19'])

    open_with('out.mp4', program_id=1)


if __name__ == '__main__':
    cd(PROJ_DIR)

    blocks = get_all_python_block()
    for b in blocks:
        exec(b, globals())

    export_video()
