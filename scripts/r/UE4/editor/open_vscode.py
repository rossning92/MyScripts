import os
import subprocess

from _pkgmanager import find_executable, require_package

require_package("vscode")
vscode = find_executable("vscode")
subprocess.Popen([vscode, os.path.realpath(r"{{UE_SOURCE}}")])
