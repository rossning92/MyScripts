import os
import sys
import subprocess
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

check_error_code = True


def run(args):
    ps = subprocess.Popen(args)
    ret = ps.wait()
    if check_error_code and ret != 0:
        raise Exception('Process returns non zero')


_app = QApplication([])


class _MyDialog(QDialog):
    def __init__(self, options, title=None):
        super().__init__()

        if title:
            self.setWindowTitle(title)
        self.resize(800, 400)
        
        self.installEventFilter(self)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0);
        self.setLayout(layout)

        self.listWidget = QListWidget()
        self.listWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.listWidget.setFont(QFont('Consolas', 10))
        for opt in options:
            self.listWidget.addItem(opt)

        if self.listWidget.count() > 0:
            self.listWidget.setCurrentRow(0)

        layout.addWidget(self.listWidget)

    def eventFilter(self, obj, e):
        if e.type() == QEvent.KeyPress:
            if e.key() == Qt.Key_Return or e.key() == Qt.Key_Enter:
                self.accept()
                return True
            elif e.key() == Qt.Key_Escape:
                self.reject()
                return True
        return False


def select_options(options, title=None):
    dialog = _MyDialog(options, title)
    return_code = dialog.exec_()
    if return_code != QDialog.Accepted:
        return []
    
    selected_indices = []
    lw = dialog.listWidget
    for i in range(lw.count()):
        if lw.item(i).isSelected():
            selected_indices.append(i)
    return selected_indices
