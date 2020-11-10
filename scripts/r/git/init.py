import os
from subprocess import call

os.chdir(os.environ['CUR_DIR_'])

call('git init')
open('.gitignore', 'w')
