import os
import sys

sys.path.insert(0, os.path.realpath(os.path.dirname(__file__) + "/../libs"))

from _script import start_script

start_script(file=sys.argv[1])
