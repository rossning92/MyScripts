import os
from _appmanager import get_executable
from _shutil import *


def get_selected_script_dir_rel():
    rel_path = os.getenv('_SCRIPT_PATH').replace(os.getcwd() + os.path.sep, '')
    rel_path = os.path.dirname(rel_path)
    rel_path = rel_path.replace('\\', '/')
    rel_path += '/'
    return rel_path


def edit_myscript_script(file):
    if os.path.splitext(file)[1] == '.link':
        file = open(file, 'r', encoding='utf-8').read().strip()

    project_folder = os.path.realpath(os.path.dirname(__file__) + '/../')
    os.chdir(project_folder)
    vscode = get_executable('vscode')
    start_process([vscode, project_folder, file])


def get_my_script_root():
    return os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + '/../')
