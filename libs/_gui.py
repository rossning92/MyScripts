import os
import sys
import subprocess
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import threading
import queue

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


def get_qss():
    return '''
        * {
            font: 12pt "Consolas";
            color: rgb(255, 255, 255);
            border: none;
            background-color: rgb(0, 0, 0);
        }
        
        QWidget:item:selected {
            background-color: orange;
            color: rgb(0, 0, 0);
        }
    '''


class MyDialog(QDialog):
    def __init__(self, title=''):
        super().__init__()

        self.installEventFilter(self)
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint)
        self.resize(800, 400)

        self.setStyleSheet(get_qss())

        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def eventFilter(self, obj, e):
        if e.type() == QEvent.KeyPress:
            if e.key() == Qt.Key_Return or e.key() == Qt.Key_Enter:
                self.accept()
                return True
            elif e.key() == Qt.Key_Escape:
                sys.exit(0)
        return False

    def add_shortcut(self, hotkey, func):
        print('%s => %s' % (hotkey, func.__name__))
        QShortcut(QKeySequence(hotkey), self, func)


class SelectWidget(QWidget):
    def __init__(self, options):
        super().__init__()

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

        # Auto adjust width
        self.listWidget.setMinimumWidth(self.listWidget.sizeHintForColumn(0) + 10)

    def get_selected(self):
        selected_indices = []
        for i in range(self.listWidget.count()):
            if self.listWidget.item(i).isSelected():
                selected_indices.append(i)
        return selected_indices


def select_options(options, title=None):
    dialog = MyDialog()
    if title:
        dialog.setWindowTitle(title)

    sw = SelectWidget(options)
    dialog.layout().addWidget(sw)

    return_code = dialog.exec_()
    if return_code != QDialog.Accepted:
        return []

    return sw.get_selected()


class SearchWidget(QWidget):
    on_new_line = pyqtSignal(str)

    def __init__(self, items=None, search_func=None, cancel_func=None):
        super().__init__()

        self.items = items if items is not None else []
        self.matched_items = []

        self.search_func = search_func
        self.cancel_func = cancel_func
        self.on_new_line.connect(self.on_new_line_slot)
        self.new_text = None
        self.condition = threading.Condition()
        self.search_thread = threading.Thread(target=self._search_thread)
        self.search_thread.daemon = True
        self.search_thread.start()

        self.selected_index = -1

        vbox = QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)

        self.lineEdit = QLineEdit()
        self.lineEdit.textChanged.connect(self.on_lineEdit_textChanged)
        vbox.addWidget(self.lineEdit)

        self.listWidget = QListWidget()
        self.listWidget.setFocusPolicy(Qt.NoFocus)
        self.listWidget.setStyleSheet("QListView::item:selected { background: #3a4660; color: #ffffff; }")
        self.listWidget.itemDoubleClicked.connect(self.listWidget_itemDoubleClicked)
        self.listWidget.itemSelectionChanged.connect(self.listWidget_itemSelectionChanged)
        vbox.addWidget(self.listWidget)

        self.setLayout(vbox)

        if items is not None:
            self.on_lineEdit_textChanged("")

        self.installEventFilter(self)

    def listWidget_itemDoubleClicked(self, item):
        pass

    def listWidget_itemSelectionChanged(self):
        for i in range(self.listWidget.count()):
            if self.listWidget.item(i).isSelected():
                self.selected_index = i
                return

        self.selected_index = -1

    def _search_item(self, text):
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
        # self.resize(800, 600)

    def on_new_line_slot(self, line):
        if line is None:
            self.listWidget.clear()
        else:
            self.listWidget.addItem(line)

    def _search_thread(self):
        text = None
        while True:
            with self.condition:
                while text == self.new_text:
                    self.condition.wait()
                text = self.new_text

            print('Clear')
            self.on_new_line.emit(None)
            for l in self.search_func(text):
                self.on_new_line.emit(l)
            print('Finished')

    def _search_async(self, text):
        if self.cancel_func is not None:
            self.cancel_func()

        with self.condition:
            self.new_text = text
            self.condition.notify()

    def on_lineEdit_textChanged(self, text):
        if self.search_func is not None:
            self._search_async(text)
        else:
            self._search_item(text)

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

    def get_selected(self):
        if self.selected_index < 0:
            return -1
        else:
            return self.matched_items[self.selected_index]


def search(items=None, title=None, search_func=None, cancel_func=None):
    dialog = MyDialog()

    if title:
        dialog.setWindowTitle(title)

    sw = SearchWidget(items=items, search_func=search_func, cancel_func=cancel_func)
    dialog.layout().addWidget(sw)

    return_code = dialog.exec_()
    if return_code != QDialog.Accepted:
        return -1

    return sw.get_selected()


def gui_input(prompt=None, default_text=None):
    input_dialog = QInputDialog(None)
    input_dialog.setInputMode(QInputDialog.TextInput)
    input_dialog.setWindowTitle(prompt)
    input_dialog.setLabelText(prompt)
    input_dialog.setTextValue(default_text)
    input_dialog.resize(800, 400)
    input_dialog.setStyleSheet(get_qss())

    ok = input_dialog.exec_()
    if ok:
        return input_dialog.textValue()
    else:
        return None


if __name__ == '__main__':
    print(search(['hello' + str(i) for i in range(5)]))
