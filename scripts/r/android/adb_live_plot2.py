import re
from collections import defaultdict
from queue import Queue

import matplotlib.pyplot as plt
import numpy as np
from _android import clear_logcat
from _math import plt_pause
from _shutil import proc_lines
import pandas as pd


def get_logcat_data():
    it = proc_lines(["adb", "exec-out", "logcat | grep 'ROSS:'"])
    for line in it:
        kvps = re.search("ROSS:(.*)", line).group(1).split()
        kvps = [x.split("=") for x in kvps]
        kvps = {k: float(v) for k, v in kvps}
        yield kvps


def plot_time_series(kw, show_recent=1000):
    fig, _ = plt.subplots()
    plt.show(block=False)

    data = defaultdict(list)
    frame_index = 0

    clear_logcat()

    it = get_logcat_data()
    for kvps in it:
        for k, v in kvps.items():
            data[k].append(v)

        if frame_index % 50 == 0:
            plt.cla()

            for name, ys in data.items():
                maxsize = min(len(ys), show_recent)

                xs = np.arange(frame_index, frame_index + maxsize)
                plt.plot(
                    xs,
                    ys[-show_recent:],
                    label=name,
                )

            plt.legend()
            plt.ylim(0, 1)
            plt_pause(0.00001)

            if not plt.get_fignums():
                it.close()

        frame_index += 1

    plt.close()
    print("Live plot closed.")

    df = pd.DataFrame.from_dict(data)
    df.to_csv("series.csv")
    print("Data saved to series.csv")


if __name__ == "__main__":
    plot_time_series("{{_KEYWORDS}}")
