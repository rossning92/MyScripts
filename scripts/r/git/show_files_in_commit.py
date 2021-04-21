import os
from subprocess import check_call

os.chdir(os.environ['_CUR_DIR'])

check_call('git log --name-only')
