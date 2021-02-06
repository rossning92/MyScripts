import os
from _script import *
from _ext import *


os.chdir('../../')

script_path = os.environ['_SCRIPT_PATH']
meta_file = os.path.abspath(os.path.splitext(script_path)[0] + '.yaml')

meta = get_script_meta(meta_file)
save_meta_file(meta, meta_file)

edit_myscript_script(meta_file)
