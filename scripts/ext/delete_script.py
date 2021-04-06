import os
from _shutil import *
from _gui import *

script_path = os.getenv('_SCRIPT')

if gui_question('Confirm delete script: %s' % script_path):
    os.remove(script_path)
