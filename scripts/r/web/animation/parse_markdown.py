from _shutil import *
import generate_slides
import urllib
import webbrowser
import capture_animation
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip
from moviepy.config import change_settings

change_settings({"FFMPEG_BINARY": "ffmpeg"})

PROJ_DIR = r'C:\Data\how_to_make_video'


def get_meta_data(type_):
    s = open('index.md', 'r', encoding='utf-8').read()
    matches = re.findall('<!-- ' + type_ + r'([\w\W]+?)-->', s)
    matches = [x.strip() for x in matches]
    return matches


def get_all_meta_data():
    s = open('index.md', 'r', encoding='utf-8').read()
    matches = re.findall('<!--\s*([a-zA-z-_]+:[\d\D]+?)\s*-->', s)
    matches = [x.strip() for x in matches]
    return matches


cd(PROJ_DIR)


meta_data = get_all_meta_data()
meta_data = meta_data[:11]
# print(meta_data)

video_clips = []
audio_clips = []

cur_pos = 0
cur_duration = 0
for meta in meta_data:
    patt = r'^record:\s+'
    if re.match(patt, meta):
        cur_pos += cur_duration

        audio_file = 'out/' + re.sub(patt, '', meta)
        print(audio_file)

        audio_clip = AudioFileClip(audio_file)
        cur_duration = audio_clip.duration

        audio_clip = audio_clip.set_start(cur_pos)
        audio_clips.append(audio_clip)

    patt = r'^title-animation:\s+'
    if re.match(patt, meta):
        s = re.sub(patt, '', meta)
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

    patt = r'^list-animation:\s+'
    if re.match(patt, meta):
        s = re.sub(patt, '', meta)
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

        clip = VideoFileClip(out_file).set_start(cur_pos)
        video_clips.append(clip)


final_audio_clip = CompositeAudioClip(audio_clips)
# final_audio_clip.write_audiofile('out.mp3', fps=44100)

final_clip = CompositeVideoClip(video_clips, size=(
    1920, 1080)).set_audio(final_audio_clip)
final_clip.write_videofile('out.mp4', codec='h264_nvenc', threads=8)

sys.exit(0)


# for s in get_meta_data('ani:'):
#     out_file = slugify('ani-' + s) + '.mov'
#     if not os.path.exists(out_file):
#         url = 'http://localhost:8080/%s.html' % s
#         capture_animation.capture_js_animation(
#             url,
#             out_file=out_file
#         )
