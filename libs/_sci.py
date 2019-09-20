from _shutil import try_import
import os

plt = try_import('matplotlib.pyplot', pkg_name='matplotlib')
np = try_import('numpy')
pd = try_import('pandas')

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


def save_fig(out_file='figure.png', open_file=True):
    plt.gcf().tight_layout()
    plt.savefig(out_file, dpi=200)
    if open_file:
        os.system(out_file)


plt.style.use('fivethirtyeight')
