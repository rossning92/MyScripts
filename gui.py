from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QPlainTextEdit
import subprocess
import threading


class ProcessWidget(QWidget):
    onPipeRead = pyqtSignal(object, bytes)

    def __init__(self):
        super().__init__()

        self.onPipeRead.connect(self.onPipeReadSlot)

        self.setLayout(QVBoxLayout())

        self.tabWidget = QTabWidget()
        self.tabWidget.setTabShape(QTabWidget.Triangular)
        self.layout().addWidget(self.tabWidget)

        self.tabs = {}

    def run(self, args, name=None):
        ps = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        threading.Thread(target=ProcessWidget.readPipeThread, args=(self, ps, ps.stdout)).start()
        threading.Thread(target=ProcessWidget.readPipeThread, args=(self, ps, ps.stderr)).start()

        plainTextEdit = QPlainTextEdit()
        self.tabWidget.addTab(plainTextEdit, str(ps))
        self.tabs[ps] = plainTextEdit

    def readPipeThread(self, ps, pipe):
        while True:
            data = pipe.read1(1024)
            if data is not None:
                self.onPipeRead.emit(ps, data)

            if data == b'':  # Pipe is closed
                break

        print('Pipe closed')

    def onPipeReadSlot(self, ps, data):
        plainTextEdit = self.tabs[ps]
        plainTextEdit.insertPlainText(data.decode())
