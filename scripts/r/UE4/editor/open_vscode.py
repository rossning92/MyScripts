import os
import subprocess

from _pkgmanager import require_package

vscode = require_package("vscode")
subprocess.Popen([vscode, os.path.realpath(r"{{UE_SOURCE}}")])
