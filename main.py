#!/usr/bin/env python3
import sys
import os

sys.path.append(os.path.abspath('./libs'))

import datetime
from colorama import Fore
import colorama
import glob
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from os.path import expanduser
from gui import ProcessWidget
from myutils import *
import time

SCRIPT_EXTENSIONS = {'.py', '.cmd', '.bat', '.sh', '.ps1', '.ahk'}


def get_data_folder():
    folder = os.path.join('data', platform.node())
    os.makedirs(folder, exist_ok=True)
    return folder


def should_update():
    global last_max_mtime
    global last_file_list

    mtime_list = []
    file_list = []
    for f in glob.iglob('scripts/**/*.*', recursive=True):
        mtime_list.append(os.stat(f).st_mtime)
        file_list.append(f)

    max_mtime = max(mtime_list)

    try:
        last_max_mtime
        last_file_list
    except NameError:
        last_max_mtime = max_mtime
        last_file_list = file_list
        return False

    if file_list != last_file_list or max_mtime > last_max_mtime:
        last_max_mtime = max_mtime
        last_file_list = file_list
        return True
    else:
        return False


def insert_line_if_not_exist(line, file, after_line=None):
    lines = None
    with open(expanduser(file), 'r') as f:
        lines = f.readlines()

        success = False
        for i in range(len(lines)):
            if lines[i].strip() == line.strip():
                print('`%s` is already in `%s`: line %d' % (line, file, i + 1))
                return False

        for i in range(len(lines)):
            if lines[i].strip() == after_line.strip():
                lines.insert(i + 1, line + '\n')
                success = True
                break

        if not success:
            print("Can't find line `%s`" % after_line)
            return False

    if lines is None:
        return False

    with open(expanduser(file), 'w') as f:
        f.writelines(lines)
        return True

    return False


variables = {}

colorama.init()


def menu_item(f):
    return f


def exec2(name):
    matched = list(filter(lambda x: x.name == name, self.script_items))
    matched[0].execute()


def select_item(items, prompt='PLEASE INPUT:'):
    matched_items = []
    while True:
        print()
        for i in matched_items:
            print('[%d] %s' % (i + 1, items[i]))

        # Get user input
        print(Fore.LIGHTGREEN_EX + prompt + Fore.RESET)
        user_input = input('> ')
        user_input = user_input.lower()

        if user_input == '':
            return matched_items[0]
        elif user_input.isdigit():
            return int(user_input) - 1
        else:
            matched_items = []

            user_input_tokens = user_input.split(' ')
            for i in range(len(items)):
                menu_name = items[i].name.lower()

                matched = all([(x in menu_name) for x in user_input_tokens])
                if matched:
                    matched_items.append(i)

            if len(items) == 0:
                matched_items = range(len(items))


class EditVariableWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.variableUIs = {}
        layout = QFormLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        try:
            with open(get_variable_file()) as f:
                self.variables = json.load(f)
        except Exception:
            self.variables = {}

    def init(self, varList=[]):
        for i in range(self.layout().count()):
            self.layout().itemAt(i).widget().deleteLater()

        row = 0
        self.variableUIs = {}
        for variable in sorted(varList):
            comboBox = QComboBox()
            comboBox.setMinimumContentsLength(20)
            comboBox.setEditable(True)
            if variable in self.variables:
                var_values = self.variables[variable]
                for v in var_values:
                    comboBox.addItem(v)
            if comboBox.count() > 0:
                comboBox.setCurrentIndex(comboBox.count() - 1)

            self.layout().addRow(QLabel(variable + ':'), comboBox)

            self.variableUIs[variable] = comboBox
            row += 1

    def save(self):
        for k, v in self.variableUIs.items():
            text = v.currentText()
            if k not in self.variables:
                var_values = []
                self.variables[k] = var_values
            else:
                var_values = self.variables[k]

            try:
                var_values.remove(text)
            except ValueError:
                pass
            var_values.append(text)

        with open(get_variable_file(), 'w') as f:
            json.dump(self.variables, f, indent=4)

    def get_variables(self):
        return self.variables


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Init script access time
        try:
            with open(get_data_folder() + '/script_access_time.json', 'r') as f:
                self.script_access_time = json.load(f)
        except FileNotFoundError:
            self.script_access_time = {}

        self.script_items = []
        self.matched_items = []

        self.ui = uic.loadUi('MainDialog.ui', self)

        # self.ui.listWidget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self.installEventFilter(self)
        self.setWindowTitle('MyScripts - GUI')

        self.editVariableWidget = EditVariableWidget()
        self.ui.layout().addWidget(self.editVariableWidget)

        self.init_script_items()
        self.on_inputBox_textChanged()

        # Process list ui
        # self.processWidget = ProcessWidget()
        # self.ui.layout().addWidget(self.processWidget)

        self.startTimer(1000)

        # Register hotkey
        for item in self.script_items:
            hotkey = item.meta['hotkey']
            if hotkey is not None:
                print('Hotkey: %s: %s' % (hotkey, item.name))
                QShortcut(QKeySequence(hotkey), self, lambda item=item: item.execute())

        self.register_global_hotkeys()

    def register_global_hotkeys(self):
        if platform.system() == 'Windows':
            with open('tmp/GlobalHotkey.ahk', 'w') as f:
                f.write('#SingleInstance Force\n')

                for item in self.script_items:
                    hotkey = item.meta['globalHotkey']
                    if hotkey is not None:
                        print('Global Hotkey: %s: %s' % (hotkey, item.name))
                        hotkey = hotkey.replace('Ctrl+', '^')
                        hotkey = hotkey.replace('Alt+', '!')
                        hotkey = hotkey.replace('Shift+', '+')
                        hotkey = hotkey.replace('Win+', '#')

                        f.write(f'''
                            {hotkey}::Run python -c "from _script import *;run_script('{item.script_path}')"
                        '''.strip() + '\n')

            subprocess.Popen(['AutoHotkeyU64.exe', 'tmp/GlobalHotkey.ahk'])

        else:
            import keyboard
            keyboard.unhook_all()
            for item in self.script_items:
                hotkey = item.meta['globalHotkey']
                if hotkey is not None:
                    print('Global Hotkey: %s: %s' % (hotkey, item.name))
                    keyboard.add_hotkey(hotkey,
                                        lambda item=item: item.execute())

    def timerEvent(self, e):
        if should_update():
            self.init_script_items()
            self.update_items(self.ui.inputBox.text())

    def init_script_items(self):
        # Load scripts
        self.script_items = []
        files = glob.glob('scripts/**/*.*', recursive=True)
        # files.sort(key=os.path.getmtime, reverse=True)
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext not in SCRIPT_EXTENSIONS:
                continue

            script = ScriptItem(file)

            # Check if auto run script
            # TODO: only run modified scripts
            if script.meta['autoRun']:
                script.execute()

            # Hide files starting with '_'
            base_name = os.path.basename(file)
            if not base_name.startswith('_'):
                self.script_items.append(script)

        self.sort_scripts()

    def on_inputBox_textChanged(self, user_input=None):
        self.update_items(user_input)

    def update_items(self, user_input=None):
        self.ui.listWidget.clear()
        self.matched_items = []

        # Initialize matched items
        if user_input is None or user_input == '':
            self.matched_items = list(range(len(self.script_items)))
        elif user_input.isdigit():
            idx = int(user_input) - 1
            if idx >= 0 and idx < len(self.script_items):
                self.matched_items.append(idx)
        else:
            user_input = user_input.lower()
            user_input_tokens = user_input.split(' ')
            for i in range(len(self.script_items)):
                menu_name = self.script_items[i].name.lower()
                matched = all([(x in menu_name) for x in user_input_tokens])
                if matched:
                    self.matched_items.append(i)

        for i in self.matched_items:
            self.ui.listWidget.addItem('%3d. %s' % (i + 1, self.script_items[i]))

        self.editVariableWidget.init()  # Clear all widget
        if len(self.matched_items) > 0:
            # Set selected items
            first_matched_item = self.script_items[self.matched_items[0]]
            self.ui.listWidget.setCurrentRow(0)
            os.environ['ROSS_SELECTED_SCRIPT_PATH'] = os.path.join(os.getcwd(), first_matched_item.script_path)

            # Display variable list
            if 'get_variables' in dir(first_matched_item):
                self.editVariableWidget.init(first_matched_item.get_variable_names())

                # Save current selected menu items
                # with open('data/SelectedScript.txt', 'w') as f:
                #    f.write(first_matched_item.script_path)

    def event(self, e):
        if e.type() == QEvent.WindowActivate:
            self.ui.inputBox.setFocus(True)
            self.ui.inputBox.selectAll()
        return super().event(e)

    def execute_selected_script(self, control_down):
        idx = self.matched_items[0]

        self.ui.editVariableWidget.save()
        global variables
        variables = self.ui.editVariableWidget.get_variables()

        self.hide()

        script = self.script_items[idx]
        script.execute(control_down=control_down)

        # Update script access time
        self.script_access_time[script.script_path] = time.time()
        with open(get_data_folder() + '/script_access_time.json', 'w') as f:
            json.dump(self.script_access_time, f, indent=4)

        # sort scripts
        self.sort_scripts()

        self.show()

        # Update input box
        self.ui.inputBox.setText(script.name)

    def sort_scripts(self):
        def key(script):
            if script.script_path in self.script_access_time:
                return max(self.script_access_time[script.script_path],
                           os.path.getmtime(script.script_path))
            else:
                return os.path.getmtime(script.script_path)

        self.script_items = sorted(self.script_items, key=key, reverse=True)

    def eventFilter(self, obj, e):
        if e.type() == QEvent.KeyPress:

            if e.modifiers() == Qt.ControlModifier and e.key() == Qt.Key_F:
                self.ui.inputBox.setFocus(True)
                self.ui.inputBox.selectAll()
                return True

            if len(self.matched_items) == 0:
                return False
            idx = self.matched_items[0]

            if e.key() == Qt.Key_Enter or e.key() == Qt.Key_Return:
                self.execute_selected_script(e.modifiers() == Qt.ControlModifier)
                return True

            if e.modifiers() == Qt.ControlModifier and e.key() == Qt.Key_E:
                path = self.script_items[idx].script_path
                open_text_editor(path)
                return True

            if e.modifiers() == Qt.ControlModifier and e.key() == Qt.Key_O:
                path = self.script_items[idx].script_path
                script = self.script_items[idx].render()
                ext = self.script_items[idx].ext

                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as f:
                    f.write(script.encode())
                    f.flush()
                    open_text_editor(f.name)
                    return True

        return super().eventFilter(obj, e)


if __name__ == '__main__':
    bin_dir = os.path.join(os.getcwd(), 'bin')
    os.environ['PATH'] = os.pathsep.join([
        bin_dir,
        os.path.abspath('./tmp/bin')  # exe proxy
    ]) + os.pathsep + os.environ['PATH']
    os.environ['PYTHONPATH'] = os.path.abspath('./libs')

    time_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(Fore.LIGHTGREEN_EX + time_now + ' Script is loaded' + Fore.RESET)

    print('Python executable: %s' % sys.executable)

    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
