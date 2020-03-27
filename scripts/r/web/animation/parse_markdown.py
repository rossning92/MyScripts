from _shutil import *
import generate_slides
import urllib
import webbrowser
import capture_animation
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip, ColorClip
from moviepy.config import change_settings
import moviepy.video.fx.all as vfx
from r.open_with.open_with_ import open_with

change_settings({"FFMPEG_BINARY": "ffmpeg"})

PROJ_DIR = r'{{VIDEO_PROJECT_DIR}}'

video_clips = []
audio_clips = []
cur_markers = None

audio_track_cur_pos = 0
audio_track_cur_duration = 0

video_track_cur_pos = 0
video_track_cur_duration = 0


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
    s = open('index.md', 'r', encoding='utf-8').read()
    matches = re.findall(r'<!---\s*([\w\W]+?)\s*-->', s)
    matches = [x.strip() for x in matches]
    return matches


def audio(f):
    global audio_track_cur_pos, audio_track_cur_duration, audio_clips, cur_markers, video_track_cur_pos

    audio_track_cur_pos += audio_track_cur_duration

    # Also forward video track pos
    video_track_cur_pos = audio_track_cur_pos

    # HACK:
    f = 'out/' + f
    print(f)

    # HACK: still don't know why changing buffersize would help reduce the noise at the end
    audio_clip = AudioFileClip(f, buffersize=400000)
    audio_track_cur_duration = audio_clip.duration

    audio_clip = audio_clip.set_start(audio_track_cur_pos)
    audio_clips.append(audio_clip)

    # Get markers
    cur_markers = _get_markers(f)
    if cur_markers:
        print(cur_markers)


def _animation(url, file_prefix, part=None):
    global video_track_cur_pos

    file_prefix = 'animation/' + slugify(file_prefix)

    if part is not None:
        out_file = '%s-%d.mov' % (file_prefix, part)
    else:
        out_file = '%s.mov' % file_prefix
    print(out_file)

    os.makedirs('animation', exist_ok=True)
    if not os.path.exists(out_file):

        capture_animation.capture_js_animation(
            url,
            out_file=file_prefix)

    # Get markers
    markers = _get_markers(out_file)
    if markers:
        # Try to align with audio markers
        for i, (m1, m2) in enumerate(zip(cur_markers, markers)):
            clip = VideoFileClip(out_file)

            if i < len(markers) - 1:
                clip = clip.subclip(m2, markers[i+1])
                delta = (cur_markers[i+1] - cur_markers[i]
                         ) - (markers[i+1] - markers[i])
                if delta > 0:
                    clip = clip.fx(vfx.freeze, 'end', delta)
            else:
                clip = clip.subclip(m2)

            clip = clip.set_start(video_track_cur_pos + m1)
            print(m2, video_track_cur_pos + m1)
            video_clips.append(clip)

    else:
        if video_clips:
            prev_start, prev_clip = video_clips[-1]
            prev_duration = prev_clip.duration
            prev_end = prev_start + prev_duration
            gap = video_track_cur_pos - prev_end
            if gap > 0:
                print('fill the gap:', gap)

                clip = prev_clip.to_ImageClip(
                    prev_duration-0.001).set_duration(gap)
                video_clips.append((prev_end, clip))

        clip = VideoFileClip(out_file)
        video_clips.append((video_track_cur_pos, clip))

        video_track_cur_pos += clip.duration


def anim(s, part=None):
    url = 'http://localhost:8080/%s.html' % s
    file_prefix = slugify(s)
    _animation(url, file_prefix, part=part)


def title_anim(h1, h2, part=None):
    file_prefix = slugify('title-%s-%s' % (h1, h2))
    url = 'http://localhost:8080/title-animation.html?h1=%s&h2=%s' % (
        urllib.parse.quote(h1),
        urllib.parse.quote(h2)
    )

    _animation(url, file_prefix, part=part)


# TODO: refactor
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
    markers = _get_markers(out_file)
    if markers:
        # Try to align with audio markers
        for i, (m1, m2) in enumerate(zip(cur_markers, markers)):
            clip = VideoFileClip(out_file)

            if i < len(markers) - 1:
                clip = clip.subclip(m2, markers[i+1])
                delta = (cur_markers[i+1] - cur_markers[i]
                         ) - (markers[i+1] - markers[i])
                if delta > 0:
                    clip = clip.fx(vfx.freeze, 'end', delta)
            else:
                clip = clip.subclip(m2)

            clip = clip.set_start(audio_track_cur_pos + m1)
            print(m2, audio_track_cur_pos + m1)
            video_clips.append(clip)

    else:
        clip = VideoFileClip(out_file).set_start(audio_track_cur_pos)
        video_clips.append(clip)


def video(f):
    print('video')


cd(PROJ_DIR)


blocks = get_all_python_block()
for b in blocks[30:]:
    exec(b, globals())


final_audio_clip = CompositeAudioClip(audio_clips)
# final_audio_clip.write_audiofile('out.wav')

if len(video_clips) == 0:
    video_clips.append(
        ColorClip((1920, 1080), color=(39, 60, 117), duration=1))


final_clip = CompositeVideoClip([clip.set_start(start) for start, clip in video_clips], size=(
    1920, 1080)).set_audio(final_audio_clip)

# final_clip.show(10.5, interactive=True)
# final_clip.preview(fps=10, audio=False)

final_clip.write_videofile('out.mp4', codec='nvenc', threads=8, fps=25)

open_with('out.mp4')


sys.exit(0)


# for s in get_meta_data('ani:'):
#     out_file = slugify('ani-' + s) + '.mov'
#     if not os.path.exists(out_file):
#         url = 'http://localhost:8080/%s.html' % s
#         capture_animation.capture_js_animation(
#             url,
#             out_file=out_file
#         )
