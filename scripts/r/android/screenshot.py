import datetime
import os
import subprocess

from _shutil import shell_open

# adb shell screencap -p /sdcard/screencap.png
# adb pull /sdcard/screencap.png

if __name__ == "__main__":
    n = int("{{_COUNT}}") if r"{{_COUNT}}" else 1

    os.chdir(os.path.expanduser("~/Desktop"))

    for i in range(n):
        print("Taking screenshot...")
        file_name = datetime.datetime.now().strftime("Screenshot_%y%m%d%H%M%S.png")
        subprocess.check_call(["adb", "shell", "screencap -p /sdcard/%s" % file_name])
        subprocess.check_call(["adb", "pull", "-a", "/sdcard/%s" % file_name])
        subprocess.check_call(["adb", "shell", "rm /sdcard/%s" % file_name])

    if n == 1:
        shell_open(file_name)
