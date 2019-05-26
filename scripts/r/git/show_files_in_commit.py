import os
from subprocess import check_call

os.chdir(os.environ['CURRENT_FOLDER'])

check_call('git log --name-only')
