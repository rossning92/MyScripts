import _conda
from _shutil import *

args = ['cmd', '/K', 'activate.bat']

conemu = get_conemu_args()
if conemu:
    args = conemu + args

call(args)
