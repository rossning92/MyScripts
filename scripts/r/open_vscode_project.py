from _editor import *
from _shutil import *

proj_dir = get_selected_folder()
print('Project path: %s' % proj_dir)
open_in_vscode(proj_dir)
