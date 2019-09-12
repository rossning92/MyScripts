import os
import datetime
import subprocess
import sys
from PyQt5.QtWidgets import QApplication, QInputDialog

os.chdir('../')

rel_path = os.getenv('ROSS_SELECTED_SCRIPT_PATH').replace(os.getcwd(), '')
rel_path = os.path.dirname(rel_path)
rel_path = rel_path[1:]
rel_path = rel_path.replace('\\', '/')
rel_path += '/'

_app = QApplication([])

input_dialog = QInputDialog(None)
input_dialog.setInputMode(QInputDialog.TextInput)
input_dialog.setWindowTitle('Create New Script')
input_dialog.setLabelText('Script name:')
input_dialog.setTextValue(rel_path)
input_dialog.resize(800, 400)
input_dialog.setStyleSheet('''
font: 12pt "Consolas";
color: rgb(255, 255, 255);
border: none;
background-color: rgb(0, 0, 0);
''')

ok = input_dialog.exec_()
if ok:
    file_path = input_dialog.textValue()
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
