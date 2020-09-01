import os
from urllib.request import urlretrieve
from subprocess import call
from _script import *

proj_path = os.path.realpath(os.environ['_CUR_DIR'])

os.chdir(proj_path)

urlretrieve('https://raw.githubusercontent.com/github/gitignore/master/UnrealEngine.gitignore', '.gitignore')

call('git init')
call('git add -A')
call('git commit -m "initial commit"')

set_variable('GIT_REPO', proj_path)
