import os
from subprocess import call

os.chdir(os.environ['_CUR_DIR'])

call('git init')
open('.gitignore', 'w')
