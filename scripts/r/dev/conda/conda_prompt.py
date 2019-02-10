import _conda
from _shutil import *

args = ['cmd', '/K', 'activate.bat']

try:
    args = conemu_wrap_args(args)
except:
    print('ConEmu not installed. Fallback to cmd.')

Popen(args)
