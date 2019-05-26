import _conda; _conda.setup_env()
from _shutil import *

args = ['cmd', '/K', 'activate.bat']
call(args)