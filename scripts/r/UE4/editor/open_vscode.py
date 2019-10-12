from _script import *
from _appmanager import *
from _editor import *

vscode = get_executable('vscode')
subprocess.Popen([vscode, os.path.realpath(r'{{UE_SOURCE}}')])