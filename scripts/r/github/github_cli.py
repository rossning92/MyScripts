from _appmanager import *
from _shutil import *

exe = get_executable('hub')

call2('hub create')
call2('hub sync')
