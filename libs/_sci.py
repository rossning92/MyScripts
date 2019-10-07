from _shutil import try_import
import os
import glob

plt = try_import('matplotlib.pyplot', pkg_name='matplotlib')
np = try_import('numpy')
pd = try_import('pandas')

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


def save_fig(out_file='figure.png', open_file=True):
    out_file = os.path.realpath(out_file)
    plt.gcf().tight_layout()
    plt.savefig(out_file, dpi=200)
    if open_file:
        os.system('start "" "%s"' % out_file)


plt.style.use('fivethirtyeight')


def read_csv(csv_files):
    data_frames = [pd.read_csv(f) for f in glob.glob(csv_files)]
    df = pd.concat(data_frames, ignore_index=True)
    return df
