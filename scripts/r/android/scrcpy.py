import ctypes
import os
import subprocess
import time

from _android import wait_until_boot_complete
from _script import get_variable
from _shutil import kill_proc


def get_screen_size():
    user32 = ctypes.windll.user32
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


last_serial = None


def update_android_serial():
    global last_serial
    serial = get_variable("ANDROID_SERIAL")

    if serial != last_serial:
        last_serial = serial

        if serial:
            os.environ["ANDROID_SERIAL"] = serial
        else:
            if "ANDROID_SERIAL" in os.environ:
                del os.environ["ANDROID_SERIAL"]

        return True
    else:
        return False


if __name__ == "__main__":
    win_pos = [int(x) for x in "{{_POS}}".split()]

    while True:
        wait_until_boot_complete()

        args = [
            "scrcpy",
            "--always-on-top",
        ]

        if win_pos:
            args += [
                "--window-x",
                "%s" % win_pos[0],
                "--window-y",
                "%s" % win_pos[1],
            ]

        if "{{_SIZE}}":
            args += ["--max-size", "{{_SIZE}}"]

        try:
            ps = subprocess.Popen(args, stdin=subprocess.PIPE)

            while not update_android_serial() and ps.poll() is None:
                time.sleep(3)

            kill_proc(ps)
        except KeyboardInterrupt:
            print("Exiting...")
