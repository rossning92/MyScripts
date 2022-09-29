import os

from _editor import open_in_vscode
from _script import (
    get_script_config_file,
    get_script_default_config,
    get_script_directories,
)
from _shutil import load_yaml, save_yaml
from _term import DictEditWindow

SCRIPT_ROOT = os.path.dirname(os.path.abspath(__file__))


def get_selected_script_dir_rel():
    rel_path = os.getenv("SCRIPT").replace(os.getcwd() + os.path.sep, "")
    rel_path = os.path.dirname(rel_path)
    rel_path = rel_path.replace("\\", "/")
    rel_path += "/"
    return rel_path


def edit_myscript_script(file):
    if os.path.splitext(file)[1] == ".link":
        file = open(file, "r", encoding="utf-8").read().strip()

    project_folder = os.path.abspath(os.path.join(SCRIPT_ROOT, ".."))
    if file.startswith(project_folder):
        open_in_vscode([project_folder, file])
        return

    script_dirs = get_script_directories()
    for _, d in script_dirs:
        if d in file:
            open_in_vscode([d, file])
            return

    open_in_vscode([file])


def get_my_script_root():
    return os.path.abspath(SCRIPT_ROOT + "/../")


def enter_script_path():
    script_dir = get_selected_script_dir_rel().lstrip("/")
    script_path = input("Script path (%s [Enter]): " % script_dir)
    if not script_path:
        script_name = input("Script path %s" % script_dir)
        if not script_name:
            return ""

        script_path = script_dir + script_name

    # Check if new script should be saved in script directories
    script_dirs = get_script_directories()
    arr = script_path.split("/")
    if arr:
        matched_script_dir = next(filter(lambda x: x[0] == arr[0], script_dirs), None)
        if matched_script_dir:
            arr[0] = matched_script_dir[1]
    script_path = "/".join(arr)

    return script_path


def edit_script_config(script_path):
    default_config = get_script_default_config()

    script_config_file = get_script_config_file(script_path)
    if not os.path.exists(script_config_file):
        data = {}
    else:
        data = load_yaml(script_config_file)

    data = {**default_config, **data}

    def on_dict_update(dict):
        data = {k: v for k, v in dict.items() if default_config[k] != v}
        save_yaml(data, script_config_file)

    w = DictEditWindow(data, default_dict=default_config, on_dict_update=on_dict_update)
    ret = w.exec()
    if ret == -1:
        return False
    else:
        return True
