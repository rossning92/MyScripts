from _shutil import *


items = {}

for line in read_lines(
    [
        "adb",
        "exec-out",
        "logcat | grep -E ' F libc' | grep -v 'mrservice'",
    ]
):
    print2(line, end="\r\n", color="black")