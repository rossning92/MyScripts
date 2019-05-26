import os
from subprocess import call

os.chdir(os.environ['CURRENT_FOLDER'])

call('git init')
open('.gitignore', 'w')
