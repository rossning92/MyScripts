import os
import datetime
import subprocess
import sys
from _gui import gui_input
from _editor import *
from _shutil import *

os.chdir('../')

src_script = os.getenv('ROSS_SELECTED_SCRIPT_PATH')

rel_path = src_script.replace(os.getcwd(), '')
rel_path = os.path.dirname(rel_path)
rel_path = rel_path[1:]
rel_path = rel_path.replace('\\', '/')
rel_path += '/'

file_path = gui_input('Duplicate script:', rel_path)
if file_path:
    dir_name = os.path.dirname(file_path)
    if dir_name != '':
        os.makedirs(dir_name, exist_ok=True)

    copy(src_script, file_path)

    open_with_text_editor(file_path)
