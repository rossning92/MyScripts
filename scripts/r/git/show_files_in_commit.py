import os
from subprocess import check_call

os.chdir(os.environ['CUR_DIR_'])

check_call('git log --name-only')
