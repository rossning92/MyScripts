import os

from _android import screenshot
from _shutil import setup_logger, shell_open

# adb shell screencap -p /sdcard/screencap.png
# adb pull /sdcard/screencap.png

if __name__ == "__main__":
    setup_logger()

    n = int(os.environ.get("_COUNT", "1"))

    os.chdir(os.path.expanduser("~/Desktop"))

    for i in range(n):
        file_name = screenshot(
            scale=float(os.environ["_SCALE"]) if "_SCALE" in os.environ else None
        )

    if n == 1:
        shell_open(file_name)
