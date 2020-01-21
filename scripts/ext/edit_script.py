import os
from _editor import *
from _shutil import *
from _appmanager import *


def edit_project_script(project_folder, file):
    vscode = get_executable('code')
    start_process([vscode, project_folder, file])


os.chdir('../../')
project_folder = getcwd()

script_path = os.environ['ROSS_SELECTED_SCRIPT_PATH']
print2('Edit Script: ' + script_path)
edit_project_script(project_folder, script_path)
