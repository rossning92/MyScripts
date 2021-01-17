from _shutil import *

files = get_files(cd=True)

mkdir("out")


for f in files:
    if not os.path.isfile(f):
        continue

    out_file = "out/" + os.path.basename(f)
    call_echo(
        [
            "ffmpeg",
            "-i",
            f,
            "-strict",
            "-2",
            "-c",
            "copy",
            "-metadata:s:v:0",
            "rotate=-90",
            out_file,
        ]
    )
