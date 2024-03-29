import os
import subprocess

from _pkgmanager import find_executable, require_package

if __name__ == "__main__":
    require_package("vscode")
    vscode = find_executable("vscode")
    subprocess.Popen([vscode, os.path.realpath(r"{{UE_SOURCE}}")])
