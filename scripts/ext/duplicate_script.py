from _gui import gui_input
from _editor import *
from _shutil import *
from _ext import *

os.chdir("../")

script_path = enter_script_path()

if script_path:
    dir_name = os.path.dirname(script_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    src_script = os.getenv("_SCRIPT")
    copy(src_script, script_path)

    edit_myscript_script(os.path.realpath(script_path))
