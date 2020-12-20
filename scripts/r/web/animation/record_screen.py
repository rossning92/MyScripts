from _shutil import *
from _term import *
import keyboard
import pyautogui


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
        pass

    def set_region(self, region):
        pass

    def start_record(self):
        pyautogui.hotkey("alt", "f9")

    def stop_record(self):
        pyautogui.hotkey("alt", "f9")

    def save_record(self, file, overwrite=False):
        files = glob.glob(
            os.path.expandvars("%USERPROFILE%\\Videos\\Desktop\\**\\*.mp4"),
            recursive=True,
        )
        files = sorted(list(files), key=os.path.getmtime, reverse=True)
        recent_file = files[0]
        move_file(recent_file, file)


if __name__ == "__main__":
    out_dir = os.path.join(os.environ["VIDEO_PROJECT_DIR"], "screencap")

    sr = ShadowPlayScreenRecorder()

    # ch = getch()
    # if ch == "1":
    #     sr.set_region([0, 0, 1920, 1080])
    # elif ch == "2":
    #     screen_resolution = pyautogui.size()
    #     x = (screen_resolution[0] - 1920) // 2
    #     y = (screen_resolution[1] - 1080) // 2
    #     sr.set_region([x, y, 1920, 1080])
    # if ch == "3":
    #     sr.set_region([1, 120, 2532, 1260])

    sr.start_record()
    minimize_cur_terminal()

    keyboard.wait("f6", suppress=True)
    sr.stop_record()
    activate_cur_terminal()

    # Save file
    name = input("input file name (no ext): ")
    if name:
        dst_file = os.path.join(
            out_dir, "%d-%s.mp4" % (int(time.time()), slugify(name))
        )
        sr.save_record(dst_file)
        print2("File saved: %s" % dst_file, color="green")

        call_echo(["mpv", dst_file])

    sleep(1)
