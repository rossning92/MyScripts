from python_mpv_jsonipc import MPV
import sys
import subprocess
from _shutil import *
import threading


def edit_video(file):
    in_time = 0
    out_time = 0
    history_files = []

    # Uses MPV that is in the PATH.
    mpv = MPV()

    history_files.append(file)
    mpv.play(history_files[-1])

    def get_temp_file():
        return os.path.join(gettempdir(), get_time_str() + ".mp4")

    def show_cut_info():
        mpv.command("show-text", "[%.3f, %.3f]" % (in_time, out_time), "3000")

    @mpv.on_key_press("[")
    def set_in_time():
        nonlocal in_time
        in_time = mpv.playback_time
        show_cut_info()

    @mpv.on_key_press("]")
    def set_out_time():
        nonlocal out_time
        out_time = mpv.playback_time
        show_cut_info()

    @mpv.on_key_press("x")
    def cut_video_file():
        if in_time is not None and out_time is not None:
            mpv.command("show-text", "Cutting video...", "3000")
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
            mpv.command("show-text", "Done.", "3000")

    @mpv.on_key_press("ctrl+s")
    def save():
        for i, file in enumerate(history_files):
            if i == len(history_files) - 1:
                shutil.copy(history_files[-1], history_files[0])
            else:
                os.remove(file)

        del history_files[1:]
        mpv.command("show-text", "File saved: %s" % history_files[0], "3000")

        try:
            mpv.terminate()
        except RuntimeError:
            pass

    @mpv.on_key_press("ctrl+z")
    def undo():
        if len(history_files) > 1:
            f = history_files.pop()
            os.remove(f)
        mpv.play(history_files[-1])
        mpv.command("show-text", "Undo", "3000")

    def create_filtered_video(vf):
        out_file = get_temp_file()
        args = [
            "ffmpeg",
            "-i",
            history_files[-1],
            "-filter:v",
            vf,
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
        mpv.command("show-text", "Done.", "3000")

    @mpv.on_key_press("c")
    def crop_video():
        mpv.command("show-text", "Cropping video...", "3000")
        create_filtered_video("crop=1920:1080:320:180")

    @mpv.on_key_press("t")
    def code_typing_effect():
        mpv.command("show-text", "Creating typing effect...", "3000")
        create_filtered_video(
            "crop=1920:1080:320:180"
            ",scale=1920:-2"
            ",reverse"
            ",mpdecimate"
            ",setpts=N/FRAME_RATE/TB"
            ",setpts=2.0*PTS*(1+random(0)*0.02)"
        )

    @mpv.on_key_press("r")
    def crop_chrome():
        mpv.command("show-text", "Cropping chrome...", "3000")
        create_filtered_video("crop=2537:1330:0:50" ",scale=1920:-2")

    @mpv.on_key_press("2")
    def set_speed_2x():
        mpv.command("show-text", "Setting speed to 2x...", "3000")
        create_filtered_video("setpts=PTS/2")


if __name__ == "__main__":
    f = get_files()[0]
    edit_video(f)
