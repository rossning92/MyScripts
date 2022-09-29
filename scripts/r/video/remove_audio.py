from _shutil import *
from _video import *


files = get_files(cd=True)

for in_file in files:
    if not os.path.isfile(in_file):
        continue

    fn, ext = os.path.splitext(in_file)
    out_file = "%s_noaudio.mp4" % fn

    call_echo(["ffmpeg", "-i", in_file, "-c", "copy", "-an", out_file])
