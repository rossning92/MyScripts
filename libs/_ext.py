import os
from _appmanager import get_executable
from _shutil import *
from _editor import open_in_vscode


def get_selected_script_dir_rel():
    rel_path = os.getenv("_SCRIPT").replace(os.getcwd() + os.path.sep, "")
    rel_path = os.path.dirname(rel_path)
    rel_path = rel_path.replace("\\", "/")
    rel_path += "/"
    return rel_path


def edit_myscript_script(file):
    if os.path.splitext(file)[1] == ".link":
        file = open(file, "r", encoding="utf-8").read().strip()

    project_folder = os.path.realpath(os.path.dirname(__file__) + "/../")
    open_in_vscode([project_folder, file])


def get_my_script_root():
    return os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + "/../")


def enter_script_path():
    script_dir = get_selected_script_dir_rel().lstrip("/")
    script_path = input("Script path (%s [Enter]): " % script_dir)
    if not script_path:
        script_name = input("Script path %s" % script_dir)
        if not script_name:
            return ""

        script_path = script_dir + script_name

    return script_path
