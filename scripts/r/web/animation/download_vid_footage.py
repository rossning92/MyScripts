from _shutil import *
from slide import generate
from _video import *


cd('~/Downloads')


exec_ahk('''
    WinActivate, ahk_exe chrome.exe
    Send {F6}
    Send ^c
    ClipWait 2
    Send {Esc}
''')

url = 'https://www.youtube.com/watch?v=QBfV-hDsV-Q'
url = get_clip()

title = check_output_echo(
    f'youtube-dl --get-title {url}')
file_name = slugify(title)
print2('FileName: ' + file_name)

call_echo(
    f'youtube-dl -f bestvideo[ext=mp4] --no-mtime -o {file_name}.%(ext)s {url}')

# Slide
generate.generate_slide(text='Source: %s' % title,
                               out_file=file_name + '.png',
                               template_file='caption.html')

# Cut
if '{{_START_AND_DURATION}}':
    start_and_duration = '{{_START_AND_DURATION}}'.split()
    out_file = f'{file_name}_cut_{"_".join(start_and_duration)}.mp4'
    if not os.path.exists(out_file):
        ffmpeg(f'{file_name}.mp4',
               out_file=out_file,
               start_and_duration=start_and_duration)
