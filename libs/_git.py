import os
import subprocess

from _shutil import get_home_path, make_and_change_dir, print2


def git_clone(url):
    proj_path = os.path.join(get_home_path(), "Projects")
    make_and_change_dir(proj_path)
    folder_name = url.split("/")[-1]
    if not os.path.exists(folder_name):
        subprocess.check_call(["git", "clone", "--recurse-submodules", url])
    else:
        print2("%s already exists. Don't clone" % folder_name)
    path = os.path.abspath(folder_name)
    os.chdir(path)
    return path
