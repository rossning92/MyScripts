from _shutil import *
from _appmanager import *

vscode = get_executable('vscode')
subprocess.Popen([vscode, os.path.realpath(r'{{GIT_REPO}}')])
