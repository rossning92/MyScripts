from subprocess import check_call
import datetime
import os

n = "{{SCREENSHOT_COUNT}}"
if n:
    n = int(n)
else:
    n = 1

os.chdir(os.path.expanduser("~/Desktop"))


# adb shell screencap -p /sdcard/screencap.png
# adb pull /sdcard/screencap.png

for i in range(n):
    print("Taking screenshot...")
    file_name = datetime.datetime.now().strftime("Screenshot_%y%m%d%H%M%S.png")
    check_call(["adb", "shell", "screencap -p /sdcard/%s" % file_name])
    check_call(["adb", "pull", "-a", "/sdcard/%s" % file_name])
    check_call(["adb", "shell", "rm /sdcard/%s" % file_name])

if n == 1:
    os.system(f'start "" "{file_name}"')
