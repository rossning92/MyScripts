import os
import sys
from _editor import open_in_pycharm

# Open python file
if len(sys.argv) == 2:
    path = sys.argv[1]

# Open project folder
else:
    path = os.path.abspath(os.getcwd() + '/../../')

open_in_pycharm(path)
