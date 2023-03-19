import argparse
import os
import re

from _editor import open_in_editor
from _script import set_variable
from _shutil import call_echo, get_home_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", type=str, nargs="?")
    args = parser.parse_args()

    if args.url:
        url = args.url
    else:
        url = os.environ["GIT_URL"]

    project_root = os.path.join(get_home_path(), "Projects")
    os.makedirs(project_root, exist_ok=True)
    os.chdir(project_root)
    project_name = os.path.basename(url)
    project_name = re.sub(".git$", "", project_name)

    if not os.path.exists(project_name):
        os.makedirs(project_name)
        os.chdir(project_name)
        call_echo("git clone %s --single-branch --filter=blob:none ." % url)

    set_variable("GIT_REPO", os.path.realpath(project_name))

    open_in_editor(os.path.abspath(project_name))
