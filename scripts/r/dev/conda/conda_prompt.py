import _conda
from _shutil import *

_conda.setup_env()

cd_current_dir()

args = ['cmd', '/K', 'activate.bat']
call(args)
