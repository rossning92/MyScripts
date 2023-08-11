import logging
import os
import subprocess
import time
from statistics import mean
from typing import List

from _shutil import setup_logger

last_total_idle = None

# https://man7.org/linux/man-pages/man5/proc.5.html


def get_cpu_usage(proc_name, samples=10) -> List[float]:
    result: List[float] = []
    prev_ticks = None
    past = None
    while len(result) < 10:
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
            val = (ticks - prev_ticks) / (now - past)
            result.append(val)
            logging.info("Sample (%d/%d): %.2f" % (len(result), samples, val))

        prev_ticks = ticks
        past = now

        time.sleep(1)

    return result


if __name__ == "__main__":
    setup_logger()

    proc_name = os.environ["_PROC_NAME"]
    out_file = os.environ.get("OUT_FILE", "")

    result = get_cpu_usage(proc_name)
    mean_val = mean(result)
    print("%.4f" % mean_val)

    if out_file:
        with open(out_file, "w", encoding="utf-8") as f:
            f.write("%.4f" % mean_val)
