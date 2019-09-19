import matplotlib.pyplot as plt
import os
import numpy as np


def save_fig(out_file='figure.png'):
    plt.gcf().tight_layout()
    plt.savefig(out_file, dpi=200)
    os.system(out_file)


plt.style.use('fivethirtyeight')
