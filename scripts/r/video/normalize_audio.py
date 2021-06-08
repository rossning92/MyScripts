from _shutil import *


f = get_files(cd=True)[0]
call_echo(
    [
        "ffmpeg",
        "-i",
        f,
        "-af",
        "volumedetect",
        "-vn",
        "-sn",
        "-dn",
        "-f",
        "null",
        "/dev/null",
    ]
)

mkdir("out")
gain = input("gain:")
call_echo(
    [
        "ffmpeg",
        "-i",
        f,
        "-af",
        "volume=%sdB" % gain,
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        os.path.join("out", f),
        "-y",
    ]
)
