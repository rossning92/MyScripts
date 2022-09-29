import os

from _android import screenshot
from _shutil import shell_open

# adb shell screencap -p /sdcard/screencap.png
# adb pull /sdcard/screencap.png

if __name__ == "__main__":
    n = int("{{_COUNT}}") if r"{{_COUNT}}" else 1

    os.chdir(os.path.expanduser("~/Desktop"))

    for i in range(n):
        file_name = screenshot(scale=float("{{_SCALE}}") if "{{_SCALE}}" else None)

    if n == 1:
        shell_open(file_name)
