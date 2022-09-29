import os
import subprocess

from _pkgmanager import get_executable

vscode = get_executable("vscode")
subprocess.Popen([vscode, os.path.realpath(r"{{UE_SOURCE}}")])
