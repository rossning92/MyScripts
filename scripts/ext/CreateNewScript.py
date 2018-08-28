import os
import datetime
import subprocess
import sys
from PyQt5.QtWidgets import QApplication, QInputDialog

os.chdir('../')

_app = QApplication([])
file_path, okPressed = QInputDialog.getText(None, "Create New Script", "Script name:")
if okPressed:
    dir_name = os.path.dirname(file_path)
    if dir_name != '':
        os.makedirs(dir_name, exist_ok=True)

    # Create empty file
    with open(file_path, 'w') as f:
        pass

    if sys.platform == 'darwin':
        subprocess.Popen(['atom', file_path])
    else:
        subprocess.Popen(['notepad++', file_path])
