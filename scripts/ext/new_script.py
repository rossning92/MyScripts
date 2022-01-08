import os
import shutil

from _ext import edit_myscript_script, enter_script_path, get_my_script_root

if __name__ == "__main__":
    os.chdir("../")

    script_path = enter_script_path()
    if not script_path:
        print("Canceled")
        exit(0)

    dir_name = os.path.dirname(script_path)
    if dir_name != "":
        os.makedirs(dir_name, exist_ok=True)

    name, ext = os.path.splitext(script_path)
    if not ext:
        print("Please specify script extension")
        exit(0)

    if ext == ".py":
        shutil.copyfile(get_my_script_root() + "/templates/python.py", script_path)
    else:
        # Create empty file
        with open(script_path, "w") as f:
            pass

    edit_myscript_script(os.path.realpath(script_path))
