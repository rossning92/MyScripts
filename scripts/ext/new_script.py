from _editor import *
from _ext import *
import click

os.chdir("../")

rel_path = get_selected_script_dir_rel().lstrip("/")
print(rel_path)


s = input("New script name: %s" % rel_path)
if s:
    script_path = rel_path + s

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
