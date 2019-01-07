import glob
import subprocess
import os
import sys
from _pycharm import open_with_pycharm

# Open python file
if len(sys.argv) == 2:
    path = sys.argv[1]

# Open project folder
else:
    path = os.path.abspath(os.getcwd() + '/../../')

open_with_pycharm(path)
