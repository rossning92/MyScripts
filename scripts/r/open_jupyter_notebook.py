from _shutil import *
import os

cd(os.environ['_CUR_DIR'])

args = 'jupyter notebook'
if '_FILE' in os.environ:
    args += ' "' + os.environ["_FILE"] + '"'

try:
    call2(args)
except:
    call2('conda install jupyter -y')
    call2(args)
