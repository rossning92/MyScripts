import argparse
import re
import sys
import time
from collections import defaultdict
from typing import DefaultDict, List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from _math import plt_pause


def plot_time_series(
    metrics: List[str],
    names: Optional[List[str]] = None,
    samples=500,
    out_image: Optional[str] = None,
    out_csv: Optional[str] = None,
):
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

    data: DefaultDict[str, List[float]] = defaultdict(list)
    frame_index = 0
    last_update = 0.0

    def update_plot():
        plt.cla()
        for name, ys in data.items():
            maxsize = min(len(ys), samples)
            plt.plot(
                np.arange(frame_index, frame_index + maxsize),
                ys[-samples:],
                label=name,
                linewidth=0.5,
            )

        plt.legend()
        plt.ylim(bottom=min_val, top=max_val)
        plt_pause(0.01)

    min_val = 0.0
    max_val = 0.0
    while True:
        line = sys.stdin.readline()
        if request_exit or line == "":
            update_plot()
            break

        line = line.rstrip("\n")

        for i, patt in enumerate(metrics):
            match = re.search(patt, line)
            if match:
                if names is not None:
                    assert len(names) == len(metrics)
                    name = names[i]
                    val = float(match.group(1))
                else:
                    name = match.group(1)
                    val = float(match.group(2))
                data[name].append(val)
                frame_index = len(data[name]) + 1
                min_val = min(min_val, val * 1.15)
                max_val = max(max_val, val * 1.15)

            now = time.time()
            if now - last_update > 0.5:
                last_update = now
                update_plot()

    if out_image:
        plt.savefig(out_image)
    plt.close()

    print("Live plot closed.")

    if out_csv:
        df = pd.DataFrame.from_dict(data, orient="index")
        df = df.transpose()
        df.to_csv(out_csv)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--names",
        nargs="+",
        help="Optional metric names. Number of metric names must match number of metric patterns.",
    )
    parser.add_argument(
        "--metrics",
        "-m",
        nargs="+",
        help="Metric regex. If there are groups defined, the first group should match the metric name, and the second group should match the value.",
    )
    parser.add_argument(
        "--out-image",
        type=str,
        nargs="?",
        help="Output image.",
    )
    parser.add_argument(
        "--out-csv",
        type=str,
        nargs="?",
        help="Output csv.",
    )
    args = parser.parse_args()

    plot_time_series(
        names=args.names,
        metrics=args.metrics,
        out_image=args.out_image,
        out_csv=args.out_csv,
    )
