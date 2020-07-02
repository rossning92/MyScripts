import os
from _shutil import *
from _ext import *

script_path = os.environ['_SCRIPT_PATH'].strip()
print2('Edit Script: ' + script_path)
edit_myscript_script(script_path)
