from _shutil import *

for f in get_files(cd=True):
    mkdir("out")
    args = [
        "ffmpeg",
        "-i",
        f,
        "-filter:v",
        "crop=1920:1080:320:180,scale=1920:-2,reverse,mpdecimate,setpts=N/FRAME_RATE/TB,setpts=2.0*PTS*(1+random(0)*0.02)",
        "-pix_fmt",
        "yuv420p",
        "-c:v",
        "libx264",
        "-crf",
        "19",
        "-preset",
        "slow",
        "-pix_fmt",
        "yuv420p",
        "-an",
        "out/%s" % f,
        "-y",
    ]
    call_echo(args)
