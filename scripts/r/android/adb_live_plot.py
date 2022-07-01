import re
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
from _android import clear_logcat
from _math import plt_pause
from _shutil import read_proc_lines


def plot_time_series(kw, show_recent=500):
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

    clear_logcat()

    # Read all lines with camera phase sync timestamps
    patt = re.compile("(" + kw + ")=([+-]?([0-9]*[.])?[0-9]+)")
    it = read_proc_lines(["adb", "exec-out", f"logcat | grep -E '({kw})='"])
    for line in it:
        if request_exit:
            it.close()
            break

        matches = re.findall(patt, line)
        print(matches)
        for match in matches:
            data[match[0]].append(float(match[1]))
            plt.cla()

            for name, ys in data.items():
                maxsize = min(len(ys), show_recent)

                plt.plot(
                    np.arange(frame_index, frame_index + maxsize),
                    ys[-show_recent:],
                    label=name,
                )

        if matches:
            plt.legend()
            plt.ylim(bottom=0)
            plt_pause(0.01)
            frame_index += 1

    plt.close()
    print("Live plot closed.")


if __name__ == "__main__":
    plot_time_series("{{_KEYWORDS}}")
