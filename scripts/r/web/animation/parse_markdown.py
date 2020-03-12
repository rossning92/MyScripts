from _shutil import *
import generate_slides
import urllib
import webbrowser
import capture_animation
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip
from moviepy.config import change_settings
import moviepy.video.fx.all as vfx

change_settings({"FFMPEG_BINARY": "ffmpeg"})

PROJ_DIR = r'C:\Data\how_to_make_video'

video_clips = []
audio_clips = []
cur_markers = None
cur_pos = 0
cur_duration = 0


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
    matches = re.findall(r'```py\s+([\w\W+]+?)\s+```', s)
    matches = [x.strip() for x in matches]
    return matches


def audio(f):
    global cur_pos, cur_duration, audio_clips, cur_markers

    cur_pos += cur_duration

    f = 'out/' + f
    print(f)

    audio_clip = AudioFileClip(f)
    cur_duration = audio_clip.duration

    audio_clip = audio_clip.set_start(cur_pos)
    audio_clips.append(audio_clip)

    # Get markers
    cur_markers = _get_markers(f)
    if cur_markers:
        print(cur_markers)


def title_animation(s):
    out_file = 'animation/title-animation-' + slugify(s) + '.mov'
    print(out_file)

    os.makedirs('animation', exist_ok=True)
    if not os.path.exists(out_file):
        h1 = re.search('^# (.*)', s, flags=re.MULTILINE).group(1)
        h2 = re.search('^## (.*)', s, flags=re.MULTILINE).group(1)
        url = 'http://localhost:8080/title-animation.html?h1=%s&h2=%s' % (
            urllib.parse.quote(h1),
            urllib.parse.quote(h2)
        )
        capture_animation.capture_js_animation(
            url,
            out_file=out_file)

    clip = VideoFileClip(out_file).set_start(cur_pos)
    video_clips.append(clip)


def list_animation(s):
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

            clip = clip.set_start(cur_pos + m1)
            print(m2, cur_pos + m1)
            video_clips.append(clip)

    else:
        clip = VideoFileClip(out_file).set_start(cur_pos)
        video_clips.append(clip)


def video(f):
    print('video')


cd(PROJ_DIR)


blocks = get_all_python_block()
for b in blocks[0:2]:
    exec(b, globals())


final_audio_clip = CompositeAudioClip(audio_clips)
# final_audio_clip.write_audiofile('out.mp3', fps=44100)

final_clip = CompositeVideoClip(video_clips, size=(
    1920, 1080)).set_audio(final_audio_clip)

# final_clip.show(10.5, interactive=True)
# final_clip.preview(fps=10, audio=False)

final_clip.write_videofile('out.mp4', codec='h264_nvenc', threads=8, fps=25)


sys.exit(0)


# for s in get_meta_data('ani:'):
#     out_file = slugify('ani-' + s) + '.mov'
#     if not os.path.exists(out_file):
#         url = 'http://localhost:8080/%s.html' % s
#         capture_animation.capture_js_animation(
#             url,
#             out_file=out_file
#         )
