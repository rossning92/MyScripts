import os
from subprocess import check_call

os.chdir(os.environ["CWD"])

check_call("git log --name-only")
