import argparse
import re
import sys
import time
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from _math import plt_pause


def plot_time_series(metric_regex, samples=500):
    plt.style.use("bmh")

    # Setup ESC key to exit live plot
    request_exit = False

    def key_pressed(event):
        nonlocal request_exit

        if event.key == "escape":
            request_exit = True

    fig, _ = plt.subplots()
    fig.canvas.mpl_connect("key_press_event", key_pressed)
    plt.show(block=False)

    data = defaultdict(list)
    frame_index = 0

    last_update = 0.0

    while True:
        line = sys.stdin.readline()
        if line == "":
            break
        else:
            line = line.rstrip("\n")

        if request_exit:
            break

        for name, patt in metric_regex.items():
            match = re.findall(patt, line)
            if match:
                val = float(match[0])
                data[name].append(val)
                frame_index = len(data[name]) + 1

            now = time.time()
            if now - last_update > 0.5:
                plt.cla()
                for name, ys in data.items():
                    maxsize = min(len(ys), samples)
                    plt.plot(
                        np.arange(frame_index, frame_index + maxsize),
                        ys[-samples:],
                        label=name,
                    )

                plt.legend()
                plt.ylim(bottom=-2, top=10)
                plt_pause(0.01)
                last_update = now

    plt.close()

    print("Live plot closed.")

    df = pd.DataFrame.from_dict(data, orient="index")
    df = df.transpose()
    df.to_csv("data.csv")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--metric",
        "-m",
        metavar="METRIC=REGEX",
        nargs="+",
        help="Provide both the name and regular expression to match the metric.",
    )
    args = parser.parse_args()

    metric_regex = {
        m.split("=", 1)[0]: re.compile(m.split("=", 1)[1]) for m in args.metric
    }
    plot_time_series(metric_regex=metric_regex)
