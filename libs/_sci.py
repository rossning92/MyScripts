from _shutil import try_import
import os

plt = try_import('matplotlib.pyplot', pkg_name='matplotlib')
np = try_import('numpy')
pd = try_import('pandas')


def save_fig(out_file='figure.png'):
    plt.gcf().tight_layout()
    plt.savefig(out_file, dpi=200)
    os.system(out_file)


plt.style.use('fivethirtyeight')
