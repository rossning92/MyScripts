import os
from myutils import *

os.chdir('../../')

script_path = os.environ['ROSS_SELECTED_SCRIPT_PATH']
meta_file = os.path.abspath(os.path.splitext(script_path)[0] + '.yaml')

meta = get_script_meta(meta_file)
save_meta_file(meta, meta_file)

open_text_editor(meta_file)
