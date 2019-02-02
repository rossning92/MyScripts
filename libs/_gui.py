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
font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
font.setPointSize(10)
_app.setFont(font)


class MyDialog(QDialog):
    def __init__(self, title=''):
        super().__init__()

        self.installEventFilter(self)
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)
        self.resize(800, 400)

        vbox = QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)
        self.setLayout(vbox)

    def eventFilter(self, obj, e):
        if e.type() == QEvent.KeyPress:
            if e.key() == Qt.Key_Return or e.key() == Qt.Key_Enter:
                self.accept()
                return True
            elif e.key() == Qt.Key_Escape:
                self.reject()
                return True
        return False


class OptionDialog(MyDialog):
    def __init__(self, options, title=None):
        super().__init__()

        if title:
            self.setWindowTitle(title)
        self.resize(800, 400)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.listWidget = QListWidget()
        self.listWidget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        for opt in options:
            self.listWidget.addItem(opt)

        if self.listWidget.count() > 0:
            self.listWidget.setCurrentRow(0)

        layout.addWidget(self.listWidget)

        self.installEventFilter(self)


def select_options(options, title=None):
    dialog = OptionDialog(options, title)
    return_code = dialog.exec_()
    if return_code != QDialog.Accepted:
        return []

    selected_indices = []
    lw = dialog.listWidget
    for i in range(lw.count()):
        if lw.item(i).isSelected():
            selected_indices.append(i)
    return selected_indices


class SearchWidget(QWidget):
    def __init__(self, items, title=''):
        super().__init__()

        self.items = items
        self.matched_items = []
        self.selected_index = -1

        vbox = QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)

        self.lineEdit = QLineEdit()
        self.lineEdit.textChanged.connect(self.on_lineEdit_textChanged)
        vbox.addWidget(self.lineEdit)

        self.listWidget = QListWidget()
        self.listWidget.itemDoubleClicked.connect(self.listWidget_itemDoubleClicked)
        self.listWidget.itemSelectionChanged.connect(self.listWidget_itemSelectionChanged)
        vbox.addWidget(self.listWidget)

        self.setLayout(vbox)

        self.on_lineEdit_textChanged("")

        self.installEventFilter(self)

    def listWidget_itemDoubleClicked(self, item):
        self.accept()

    def listWidget_itemSelectionChanged(self):
        for i in range(self.listWidget.count()):
            if self.listWidget.item(i).isSelected():
                self.selected_index = i
                return

        self.selected_index = -1

    def on_lineEdit_textChanged(self, text):
        kw_list = text.split()

        self.listWidget.clear()
        self.matched_items.clear()
        self.selected_index = -1

        for i in range(len(self.items)):
            if self._kw_match(kw_list, str(self.items[i])):
                self.listWidget.addItem(self.items[i])
                self.matched_items.append(i)

        if self.listWidget.count() > 0:
            self.selected_index = 0
            self.listWidget.item(0).setSelected(True)

        self.listWidget.setMinimumWidth(self.listWidget.sizeHintForColumn(0) + 100)
        self.resize(800, 600)

    def _kw_match(self, kw_list, text):
        text = text.lower()
        for kw in kw_list:
            if kw.lower() not in text:
                return False
        return True

    def eventFilter(self, obj, e):
        if e.type() == QEvent.KeyPress:
            if e.key() == Qt.Key_Up:
                self.move_selection(True)
                return True
            elif e.key() == Qt.Key_Down:
                self.move_selection(False)
                return True
            else:
                return super().eventFilter(obj, e)
        else:
            return super().eventFilter(obj, e)

    def move_selection(self, up=False):
        if up:
            self.selected_index = max(0, self.selected_index - 1)
        else:
            self.selected_index = min(self.listWidget.count() - 1, self.selected_index + 1)

        self.listWidget.item(self.selected_index).setSelected(True)

    def selected_index(self):
        if self.selected_index <= 0:
            return -1
        else:
            return self.matched_items[self.selected_index]


def search(items, title=''):
    dialog = MyDialog()

    sw = SearchWidget(items, title=title)
    dialog.layout().addWidget(sw)

    return_code = dialog.exec_()
    if return_code != QDialog.Accepted:
        return -1

    return dialog.selected_index()


if __name__ == '__main__':
    search(['hello' + str(i) for i in range(5)])
