import os
import re

from _editor import open_in_vscode
from _script import set_variable
from _shutil import call_echo, chdir, mkdir

if __name__ == "__main__":
    mkdir("~/Projects")
    chdir("~/Projects")

    folder = os.path.basename("{{GIT_URL}}")
    folder = re.sub(".git$", "", folder)

    if not os.path.exists(folder):
        call_echo("git clone %s --depth=1" % "{{GIT_URL}}")

    set_variable("GIT_REPO", os.path.realpath(folder))

    open_in_vscode(folder)
