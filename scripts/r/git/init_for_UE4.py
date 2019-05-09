import os
from urllib.request import urlretrieve
from subprocess import call

os.chdir(os.environ['CURRENT_FOLDER'])

urlretrieve('https://raw.githubusercontent.com/github/gitignore/master/UnrealEngine.gitignore', '.gitignore')

call('git init')
call('git add -A')
call('git commit -m "initial commit"')
