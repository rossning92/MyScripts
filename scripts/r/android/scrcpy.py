import ctypes
import os
import subprocess
import time

from _script import get_variable
from _shutil import kill_proc
from utils.android import wait_until_boot_complete


def get_screen_size():
    user32 = ctypes.windll.user32
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


serial = get_variable("ANDROID_SERIAL")


def update_android_serial():
    global serial
    s = get_variable("ANDROID_SERIAL")

    if s != serial:
        serial = s

        if s:
            os.environ["ANDROID_SERIAL"] = s
        else:
            if "ANDROID_SERIAL" in os.environ:
                del os.environ["ANDROID_SERIAL"]

        return True
    else:
        return False


if __name__ == "__main__":

    while True:
        wait_until_boot_complete()

        args = ["scrcpy", "--window-title=scrcpy"]

        if os.environ.get("SCRCPY_POS"):
            win_pos = [int(x) for x in os.environ["SCRCPY_POS"].split()]
            args += [
                "--always-on-top",
                "--window-x",
                "%s" % win_pos[0],
                "--window-y",
                "%s" % win_pos[1],
            ]

        if serial:
            args += ["--serial", serial]

        if os.environ.get("SCRCPY_HEIGHT"):
            args += ["--max-size", os.environ["SCRCPY_HEIGHT"]]

        ps = subprocess.Popen(args, stdin=subprocess.PIPE)
        ps.stdin.close()  # to avoid stuck in "press any key..."

        try:
            while (not update_android_serial()) and (
                # Process is still alive
                ps.poll()
                is None
            ):
                time.sleep(3)

        except Exception as ex:
            print("Retry on error:", ex)
            pass
        except KeyboardInterrupt:
            print("Restarting...")
            pass

        kill_proc(ps)
