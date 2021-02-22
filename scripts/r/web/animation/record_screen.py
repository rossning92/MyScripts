from _shutil import *
from _term import *
from _video import ffmpeg, remove_audio
import keyboard
import pyautogui
import argparse

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from video_editor import edit_video


class CapturaScreenRecorder:
    def __init__(self):
        self.tmp_file = os.path.join(gettempdir(), "screen-record.mp4")
        self.captura_ps = None
        self.region = None

    def set_region(self, region):
        self.region = region

    def start_record(self):
        if self.captura_ps is not None:
            return

        args = [
            "captura-cli",
            "start",
            "--speaker=4",
            "--cursor",
            "-r",
            "60",
            "--vq",
            "100",
            "-f",
            self.tmp_file,
            "-y",
        ]

        if self.region is not None:
            args += [
                "--source",
                ",".join(["%d" % x for x in self.region]),
            ]

        self.captura_ps = subprocess.Popen(
            args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        )

        while True:
            line = self.captura_ps.stdout.readline().decode()
            # print(line)
            if "Press p" in line:
                print2("Recording started.", color="green")
                break

    def stop_record(self):
        self.captura_ps
        if self.captura_ps is None:
            return

        self.captura_ps.stdin.write(b"q")
        self.captura_ps.stdin.close()
        self.captura_ps.wait()
        print2("Recording stopped.", color="green")
        self.captura_ps = None

    def save_record(self, file, overwrite=False):
        move_file(self.tmp_file, file)


class ShadowPlayScreenRecorder:
    def __init__(self):
        self.region = None

    def set_region(self, region):
        self.region = region

    def start_record(self):
        pyautogui.hotkey("alt", "f9")
        time.sleep(1)

    def stop_record(self):
        pyautogui.hotkey("alt", "f9")
        time.sleep(0.5)

    def save_record(self, file, overwrite=False):
        # Get recorded video file
        files = glob.glob(
            os.path.expandvars("%USERPROFILE%\\Videos\\**\\*.mp4"), recursive=True,
        )
        files = sorted(list(files), key=os.path.getmtime, reverse=True)
        src_file = files[0]

        if self.region is not None:
            tmp_file = get_temp_file_name(".mp4")
            ffmpeg(
                src_file,
                out_file=tmp_file,
                extra_args=[
                    "-filter:v",
                    "crop=%d:%d:%d:%d"
                    % (self.region[2], self.region[3], self.region[0], self.region[1]),
                ],
                quiet=True,
                no_audio=True,
                nvenc=True,
            )
            os.remove(src_file)
            src_file = tmp_file

        move_file(src_file, file)


recorder = ShadowPlayScreenRecorder()

if __name__ == "__main__":
    out_dir = os.path.join(os.environ["VIDEO_PROJECT_DIR"], "screencap")
    parser = argparse.ArgumentParser()
    parser.add_argument("--rect", type=int, nargs="+", default=None)

    args = parser.parse_args()

    sr = ShadowPlayScreenRecorder()
    if args.rect is not None:
        sr.set_region(args.rect)

    sr.start_record()
    minimize_cur_terminal()

    keyboard.wait("f6", suppress=True)
    sr.stop_record()
    activate_cur_terminal()

    # Save file
    name = input("input file name (no ext): ")
    if name:
        dst_file = get_temp_file_name(".mp4")
        sr.save_record(dst_file)

        src_file = dst_file
        dst_file = os.path.join(out_dir, "%s.mp4" % slugify(name))
        remove_audio(src_file, dst_file)

        print2("File saved: %s" % dst_file, color="green")
        call_echo(["mpv", dst_file])
        # edit_video(dst_file)

    sleep(1)
