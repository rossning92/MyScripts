import os
from myutils import *

os.chdir('../../')

script_path = os.environ['ROSS_SELECTED_SCRIPT_PATH']
meta_file = os.path.splitext(script_path)[0] + '.yaml'

ScriptMeta(meta_file).save()

open_text_editor(meta_file)
