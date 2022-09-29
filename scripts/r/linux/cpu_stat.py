import re
import subprocess

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from _math import plt_pause
from _shutil import *
import time

core_names = []
last_total_idle = None

plt.show(block=False)
for i in range(999999):
    sample = subprocess.check_output(
        "adb shell cat /proc/stat", universal_newlines=True
    )

    matches = re.findall("^(cpu.*?) (.*)", sample, flags=re.MULTILINE)

    total_idle_per_sample = []
    core_names.clear()
    for grps in matches:
        core_name = grps[0]
        ticks = [int(x) for x in grps[1].split()]

        total_ticks = np.sum(ticks)
        COL_IDLE = 3
        total_idle_per_core = np.array([total_ticks, ticks[COL_IDLE]])
        total_idle_per_sample.append(total_idle_per_core)
        core_names.append(core_name)

    if i == 0:
        for x in core_names:
            print(f"{x}\t", end="")
        print()

    if last_total_idle is not None:
        diff = np.array(total_idle_per_sample) - np.array(last_total_idle)
        cpu_util = np.apply_along_axis(lambda x: 1 - x[1] / x[0], -1, diff)
        for x in cpu_util:
            print(f"{x*100:.0f}%\t", end="")
        print()

    last_total_idle = total_idle_per_sample

    time.sleep(2)
