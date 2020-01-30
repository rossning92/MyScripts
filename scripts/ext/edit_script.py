import os
from _shutil import *
from _ext import *

script_path = os.environ['ROSS_SELECTED_SCRIPT_PATH']
print2('Edit Script: ' + script_path)
edit_myscript_script(script_path)
