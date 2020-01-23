import os
import datetime
import subprocess
import sys
from _gui import gui_input
from _editor import *

os.chdir('../')

rel_path = os.getenv('ROSS_SELECTED_SCRIPT_PATH').replace(os.getcwd(), '')
rel_path = os.path.dirname(rel_path)
rel_path = rel_path[1:]
rel_path = rel_path.replace('\\', '/')
rel_path += '/'

file_path = gui_input('Script name:', rel_path)
if file_path:
    dir_name = os.path.dirname(file_path)
    if dir_name != '':
        os.makedirs(dir_name, exist_ok=True)

    # Create empty file
    with open(file_path, 'w') as f:
        pass

    edit_myscript_script(file_path)
