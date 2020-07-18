from python_mpv_jsonipc import MPV
import sys
import subprocess
from _shutil import *
import threading

in_time = 0
out_time = 0
history_files = []

history_files.append(get_files()[0])

# Uses MPV that is in the PATH.
mpv = MPV()
mpv.play(history_files[-1])

close_event = threading.Event()


def get_temp_file():
    return os.path.join(gettempdir(), get_time_str() + ".mp4")


def show_cut_info():
    mpv.command("show-text", "[%.3f, %.3f]" % (in_time, out_time), "3000")


@mpv.on_key_press("[")
def set_in_time():
    global in_time
    in_time = mpv.playback_time
    show_cut_info()


@mpv.on_key_press("]")
def set_out_time():
    global out_time
    out_time = mpv.playback_time
    show_cut_info()


@mpv.on_key_press("x")
def cut_video_file():
    if in_time is not None and out_time is not None:
        out_file = get_temp_file()
        args = [
            "ffmpeg",
            "-y",
            "-nostdin",
            "-i",
            history_files[-1],
            "-ss",
            "%.3f" % in_time,
            "-strict",
            "-2",
            "-t",
            "%.3f" % (out_time - in_time),
            "-codec:v",
            "libx264",
            "-crf",
            "19",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            out_file,
        ]
        subprocess.check_call(args)
        history_files.append(out_file)
        mpv.play(out_file)
        mpv.command("show-text", "File cut.", "3000")


@mpv.on_key_press("ctrl+s")
def save():
    for i, file in enumerate(history_files):
        if i == len(history_files) - 1:
            shutil.copy(history_files[-1], history_files[0])
        else:
            os.remove(file)

    del history_files[1:]
    mpv.command("show-text", "File saved.", "3000")


@mpv.on_key_press("ctrl+z")
def undo():
    if len(history_files) > 1:
        history_files.pop()
    mpv.play(history_files[-1])
    mpv.command("show-text", "Undo", "3000")


@mpv.on_key_press("1")
def code_typing_effect():
    out_file = get_temp_file()
    args = [
        "ffmpeg",
        "-i",
        history_files[-1],
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
        out_file,
        "-y",
    ]
    subprocess.check_call(args)
    history_files.append(out_file)
    mpv.play(out_file)
    mpv.command("show-text", "Code typing effect.", "3000")
