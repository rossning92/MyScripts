import os
from _editor import *
from _shutil import *

os.chdir('../../')

script_path = os.environ['ROSS_SELECTED_SCRIPT_PATH']
print2('Edit Script: ' + script_path)
open_with_text_editor(script_path)
