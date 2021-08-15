import os

from _shutil import call_echo, get_files

files = get_files(cd=True)

for f in files:
    if not os.path.isfile(f):
        continue

    print(f)

    name_no_ext, ext = os.path.splitext(f)

    os.makedirs("out", exist_ok=True)
    out_file = "out/%s.mp3" % name_no_ext

    args = ["ffmpeg", "-i", f]
    args += ["-codec:a", "libmp3lame", "-qscale:a", "2"]
    args += [out_file]

    call_echo(args)
