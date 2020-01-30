import os
from _appmanager import get_executable
from _shutil import *

def get_selected_script_dir_rel():
    rel_path = os.getenv('ROSS_SELECTED_SCRIPT_PATH').replace(os.getcwd(), '')
    rel_path = os.path.dirname(rel_path)
    rel_path = rel_path[1:]
    rel_path = rel_path.replace('\\', '/')
    rel_path += '/'
    return rel_path


def edit_myscript_script(file):
    project_folder = os.path.realpath(os.path.dirname(__file__) + '/../')
    os.chdir(project_folder)
    vscode = get_executable('code')
    start_process([vscode, project_folder, file])
