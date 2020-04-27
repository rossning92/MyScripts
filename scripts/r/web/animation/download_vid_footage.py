from _shutil import *
from slide import generate
from _video import *


cd(r"{{VIDEO_PROJECT_DIR}}")


exec_ahk(
    """
    WinActivate, ahk_exe chrome.exe
    Send {F6}
    Send ^c
    ClipWait 2
    Send {Esc}
"""
)

url = get_clip()

start_and_duration = input("<start> <duration>: ")

title = check_output_echo(
    f'youtube-dl {url} -o "%(uploader)s - %(title)s" --get-filename'
).strip()
name = slugify(title)
out_file = "video/%s.mp4" % name
print2("Title: %s" % title)

call_echo(f"youtube-dl -f bestvideo[ext=mp4] --no-mtime -o {out_file} {url}")

# Cut
if start_and_duration.strip():
    start_and_duration = start_and_duration.split()
    cut_file = "video/%s-2.mp4" % name
    if not os.path.exists(cut_file):
        ffmpeg(out_file, out_file=cut_file, start_and_duration=start_and_duration)
    out_file = cut_file

code = f"""
! video('{out_file}', text_overlay='{title}')
"""

append_file("footage.txt", code)
