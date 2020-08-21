from _shutil import try_import
import os
import glob
import matplotlib.pyplot as plt
from matplotlib import rcParams

# import pandas as pd
import numpy as np
import math


def mat_inv(m):
    from scipy.linalg import inv

    return inv(m)


def save_fig(out_file="figure.png", open_file=True, size_inch=None, dpi=300):
    out_file = os.path.realpath(out_file)

    if size_inch:
        plt.gcf().set_size_inches(size_inch[0], size_inch[1])

    plt.gcf().tight_layout()

    plt.savefig(out_file, dpi=dpi)
    if open_file:
        os.system('start "" "%s"' % out_file)


def setup_plt_style():
    plt.style.use("fivethirtyeight")


def use_dark_theme():
    plt.style.use("dark_background")


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
