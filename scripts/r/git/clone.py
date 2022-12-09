import os
import re

from _editor import open_in_editor
from _script import set_variable
from _shutil import call_echo, get_home_path

if __name__ == "__main__":
    project_root = os.path.join(get_home_path(), "Projects")
    os.makedirs(project_root, exist_ok=True)
    os.chdir(project_root)

    project_dir = os.path.basename(os.environ["GIT_URL"])
    project_dir = re.sub(".git$", "", project_dir)

    if not os.path.exists(project_dir):
        os.makedirs(project_dir)
        os.chdir(project_dir)
        call_echo(
            "git clone %s --single-branch --filter=blob:none ." % os.environ["GIT_URL"]
        )

    set_variable("GIT_REPO", os.path.realpath(project_dir))

    open_in_editor(project_dir)
