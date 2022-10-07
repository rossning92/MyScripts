import os
import subprocess
import time

last_total_idle = None

# https://man7.org/linux/man-pages/man5/proc.5.html

proc_name = os.environ["_PROC_NAME"]

prev_ticks = None
past = None
for i in range(999999):
    now = time.time()
    out = subprocess.check_output(
        ["adb", "shell", "cat", f"/proc/$(pidof {proc_name})/stat"],
        universal_newlines=True,
    ).strip()

    arr = out.split()

    utime = float(arr[13])
    stime = float(arr[14])
    ticks = utime + stime

    if prev_ticks:
        print("%.2f" % ((ticks - prev_ticks) / (now - past)))

    prev_ticks = ticks
    past = now

    time.sleep(1)
