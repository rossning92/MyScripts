from _shutil import *
import os

cd(os.environ['CURRENT_FOLDER'])

args = 'jupyter notebook'
if 'SELECTED_FILE' in os.environ:
    args += ' "' + os.environ["SELECTED_FILE"] + '"'

try:
    call2(args)
except:
    call2('conda install jupyter -y')
    call2(args)
