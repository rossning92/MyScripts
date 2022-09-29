import os

import keyboard
from _script import get_variable, input2
from _shutil import cd

from .common import *
from .record_screen import recorder

root = os.path.dirname(os.path.abspath(__file__))


def record_sonic_pi(file=None):
    if file is None:
        file = input2("Name without ext", "SONIC_PI_LAST_RECORD")
        file += ".mp4"

    exec_ahk(
        """
        #include <Window>
        WinActivate, ahk_exe sonic-pi.exe
        SetWindowPos("A", 0, 0, 1920, 1080)
        """
    )
    sleep(0.5)

    recorder.loudnorm = True
    recorder.set_region([0, 0, 1920, 1080])
    recorder.start_record(file)

    pyautogui.hotkey("alt", "r")

    keyboard.wait("f6", suppress=True)
    pyautogui.hotkey("alt", "s")
    sleep(1)

    recorder.stop_record()


if __name__ == "__main__":
    cd(get_variable("VIDEO_PROJECT_DIR") + "/screencap")
    record_sonic_pi()
