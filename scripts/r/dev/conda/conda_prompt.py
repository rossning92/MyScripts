import _conda
from _shutil import *

_conda.setup_env()

cd_current_dir()

args = ['cmd', '/K', 'call', 'activate.bat']
call2(args)
