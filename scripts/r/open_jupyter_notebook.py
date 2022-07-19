from _shutil import *
import os

cd(os.environ["CWD"])

args = "jupyter notebook"
if "FILE" in os.environ:
    args += ' "' + os.environ["FILE"] + '"'

try:
    call2(args)
except:
    call2("conda install jupyter -y")
    call2(args)
