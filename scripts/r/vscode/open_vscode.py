from _shutil import start_process
from _appmanager import get_executable


vscode = get_executable("vscode")
start_process(vscode)
