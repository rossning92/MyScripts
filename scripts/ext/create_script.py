from _gui import gui_input
from _editor import *
from _ext import *

os.chdir('../')
rel_path = get_selected_script_dir_rel()

file_path = gui_input('Script name:', rel_path)
if file_path:
    dir_name = os.path.dirname(file_path)
    if dir_name != '':
        os.makedirs(dir_name, exist_ok=True)

    # Create empty file
    with open(file_path, 'w') as f:
        pass

    edit_myscript_script(os.path.realpath(file_path))
