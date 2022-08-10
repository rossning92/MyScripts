import os
from urllib.request import urlretrieve

from _script import set_variable
from _shutil import call_echo

project_folder = os.environ["CWD"]
os.chdir(project_folder)

urlretrieve(
    "https://raw.githubusercontent.com/github/gitignore/master/Unity.gitignore",
    ".gitignore",
)

call_echo("git init")
call_echo("git add -A")
call_echo('git commit -m "Inital commit."')

set_variable("GIT_REPO", project_folder)
