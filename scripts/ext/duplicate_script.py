from _gui import gui_input
from _editor import *
from _shutil import *
from _ext import *

os.chdir('../')
rel_path = get_selected_script_dir_rel()
src_script = os.getenv('ROSS_SELECTED_SCRIPT_PATH')

file_path = gui_input('Duplicate script:', rel_path)
if file_path:
    dir_name = os.path.dirname(file_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    copy(src_script, file_path)

    edit_myscript_script(os.path.realpath(script_path))
