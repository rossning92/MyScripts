import os
from _editor import *
from _shutil import *
from _appmanager import *


script_path = os.environ['ROSS_SELECTED_SCRIPT_PATH']
print2('Edit Script: ' + script_path)
edit_myscript_script(script_path)
