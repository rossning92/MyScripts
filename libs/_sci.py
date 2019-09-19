from _shutil import try_import
import os

try_import('matplotlib.pyplot', as_='plt')
try_import('numpy', as_='np')
try_import('pandas', as_='pd')


def save_fig(out_file='figure.png'):
    plt.gcf().tight_layout()
    plt.savefig(out_file, dpi=200)
    os.system(out_file)


plt.style.use('fivethirtyeight')
