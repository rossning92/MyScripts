import argparse
import logging
import os
import subprocess
import time
from statistics import mean
from typing import Iterator, Optional

from utils.logger import setup_logger

last_total_idle = None

# https://man7.org/linux/man-pages/man5/proc.5.html


def get_cpu_usage(proc_name, samples: Optional[int] = None) -> Iterator[float]:
    prev_ticks = None
    past = 0.0
    counter = 0
    while samples is None or counter < samples:
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
            yield val
            logging.info(f"Sample {counter}: {val:.2f}")
            counter += 1

        prev_ticks = ticks
        past = now

        time.sleep(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", "-n", type=int, nargs="?")
    args = parser.parse_args()

    setup_logger()

    proc_name = os.environ["_PROC_NAME"]
    out_file = os.environ.get("OUT_FILE", "")

    result = get_cpu_usage(proc_name, samples=args.samples)
    mean_val = mean(result)
    print("%.4f" % mean_val)

    if out_file:
        with open(out_file, "w", encoding="utf-8") as f:
            f.write("%.4f" % mean_val)
