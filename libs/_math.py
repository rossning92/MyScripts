import glob
import os

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from _shutil import get_temp_file_name


def mat_inv(m):
    from scipy.linalg import inv

    return inv(m)


def save_fig(out_file=None, open_file=False, size_inch=None, dpi=300):
    if out_file is None:
        out_file = get_temp_file_name(".png")

    if size_inch:
        plt.gcf().set_size_inches(size_inch[0], size_inch[1])

    plt.gcf().tight_layout()

    plt.savefig(out_file, dpi=dpi)
    if open_file:
        os.system('start "" "%s"' % out_file)


def setup_plt_style(dark=False, cn=False, size_inch=None):
    if dark:
        plt.style.use("dark_background")
    else:
        plt.style.use("fivethirtyeight")

    if cn:
        matplotlib.rcParams["font.family"] = "Microsoft YaHei"
        matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei"]

    if size_inch:
        plt.gcf().set_size_inches(size_inch[0], size_inch[1])
        # plt.gcf().tight_layout()


def read_csv(csv_files):
    data_frames = [pd.read_csv(f) for f in glob.glob(csv_files)]
    df = pd.concat(data_frames, ignore_index=True)
    return df


def append_csv(df, csv_file):
    if os.path.exists(csv_file):
        df2 = pd.read_csv(csv_file)
        df = pd.concat([df2, df], sort=False)
    df.to_csv(csv_file, index=False)


def save_animation_as_gif(animate):
    import matplotlib.animation as animation

    anim = animation.FuncAnimation(
        plt.gcf(),
        animate,
        frames=np.arange(0.0, 2 * np.pi, 0.05),
        interval=10,
        blit=True,
        repeat=False,
    )

    # save animation at 30 frames per second
    anim.save("myAnimation.gif", writer="imagemagick", fps=25)


def plt_pause(interval):
    """The function updates the canvas without activating the window."""

    backend = plt.rcParams["backend"]
    if backend in matplotlib.rcsetup.interactive_bk:
        figManager = matplotlib._pylab_helpers.Gcf.get_active()
        if figManager is not None:
            canvas = figManager.canvas
            if canvas.figure.stale:
                canvas.draw()
            canvas.start_event_loop(interval)
            return
