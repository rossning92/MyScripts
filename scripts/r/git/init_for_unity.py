import os
from urllib.request import urlretrieve
from subprocess import call
from _shutil import *
from _script import *

project_folder = os.environ['_CUR_DIR']
os.chdir(project_folder)

urlretrieve('https://raw.githubusercontent.com/github/gitignore/master/Unity.gitignore', '.gitignore')

call_echo('git init')
call_echo('git add -A')
call_echo('git commit -m "Inital commit."')

set_variable('GIT_REPO', project_folder)
run_script('/r/git/cmd')
