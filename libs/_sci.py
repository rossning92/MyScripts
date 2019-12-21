from _shutil import try_import
import os
import glob

try_import('matplotlib.pyplot', pkg_name='matplotlib')
try_import('numpy')
try_import('pandas')

import matplotlib.pyplot as plt
from matplotlib import rcParams
import pandas as pd
import numpy as np


def save_fig(out_file='figure.png', open_file=True, size_inch=None, dpi=300):
    out_file = os.path.realpath(out_file)

    if size_inch:
        plt.gcf().set_size_inches(size_inch[0], size_inch[1])

    plt.gcf().tight_layout()

    plt.savefig(out_file, dpi=dpi)
    if open_file:
        os.system('start "" "%s"' % out_file)


def setup_plt_style():
    plt.style.use('fivethirtyeight')


def read_csv(csv_files):
    data_frames = [pd.read_csv(f) for f in glob.glob(csv_files)]
    df = pd.concat(data_frames, ignore_index=True)
    return df
