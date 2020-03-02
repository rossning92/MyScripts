#!/usr/bin/env python3

import time
from gui import ProcessWidget
from os.path import expanduser
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import uic
from PyQt5.QtWidgets import *
import glob
import datetime
import sys
import os

if 1:
    sys.path.append(os.path.abspath('./libs'))
    from _gui import *
    from _script import *
    from _shutil import *

GLOBAL_HOTKEY = gettempdir() + '/GlobalHotkey.ahk'

# TODO: move to configuration file
SCRIPT_PATH_LIST = [
    ['', 'scripts'],
    ['gdrive', expandvars(r"%USERPROFILE%\Google Drive\Scripts")]
]

SCRIPT_REFRESH_INTERVAL = 2000


def timeit2(func):
    import timeit
    print(timeit.timeit(func, number=1))


def add_keyboard_hooks(keyboard_hooks):
    if sys.platform != 'linux':
        import keyboard
        keyboard.unhook_all()
        for hotkey, func in keyboard_hooks.items():
            keyboard.add_hotkey(hotkey, func)


def get_user_data_folder():
    folder = os.path.join('data', platform.node())
    os.makedirs(folder, exist_ok=True)
    return folder


def get_scripts_recursive(directory):
    for root, dirs, files in os.walk(directory, topdown=True):
        dirs[:] = [d for d in dirs if not d.startswith('_')]
        for f in files:
            ext = os.path.splitext(f)[1].lower()

            # Filter by script extensions
            if ext in SCRIPT_EXTENSIONS:
                yield os.path.join(root, f)



def should_update(folder_list):
    global last_max_mtime
    global last_file_list

    mtime_list = []
    file_list = []

    for folder in folder_list:
        for f in get_scripts_recursive(folder):
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


def _replace_prefix(text, prefix, repl=''):
    if text.startswith(prefix):
        return repl + text[len(prefix):]
    return text  # or whatever


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


def select_item(items, prompt='PLEASE INPUT:'):
    matched_items = []
    while True:
        print()
        for i in matched_items:
            print('[%d] %s' % (i + 1, items[i]))

        # Get user input
        print2(prompt, color='green')
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

        self.variables = {}
        self.variables_mtime = None

    def load_variables(self):
        try:
            file = get_variable_file()
            mtime = os.path.getmtime(file)
            if self.variables_mtime is None or mtime > self.variables_mtime:
                with open(file) as f:
                    self.variables = json.load(f)
                    self.variables_mtime = mtime
        except Exception:
            print('Failed to load variable file.')

    def update_items(self, varList=[], hide_prefix=None):
        self.load_variables()

        for i in range(self.layout().count()):
            self.layout().itemAt(i).widget().deleteLater()

        row = 0
        self.variableUIs = {}
        for variable in sorted(varList):
            comboBox = QComboBox()

            comboBox.setMinimumContentsLength(20)
            comboBox.setEditable(True)

            var_values = None
            if variable in self.variables:
                var_values = self.variables[variable]
                for v in var_values:
                    comboBox.addItem(v)
            if comboBox.count() > 0:
                comboBox.setCurrentIndex(comboBox.count() - 1)

                # Auto complete
                completer = QCompleter(var_values)
                completer.setCaseSensitivity(Qt.CaseInsensitive)
                completer.setFilterMode(Qt.MatchContains)
                completer.setCompletionMode(QCompleter.PopupCompletion)
                completer.popup().setStyleSheet(get_qss())
                comboBox.setCompleter(completer)

            # Label text
            if hide_prefix:
                label_text = re.sub('^' + re.escape(hide_prefix), '', variable)
            else:
                label_text = variable
            self.layout().addRow(QLabel(label_text), comboBox)

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
            with open(get_user_data_folder() + '/script_access_time.json', 'r') as f:
                self.script_access_time = json.load(f)
        except FileNotFoundError:
            self.script_access_time = {}

        self.script_items = []
        self.matched_items = []
        self.modified_time = {}
        self.script_by_path = {}

        self.ui = uic.loadUi('MainDialog.ui', self)

        # self.ui.listWidget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        QCoreApplication.instance().installEventFilter(self)

        self.setWindowTitle('MyScripts - GUI')

        self.editVariableWidget = EditVariableWidget()
        self.ui.layout().addWidget(self.editVariableWidget)

        self.init_script_items()
        self.on_inputBox_textChanged()

        # Process list ui
        # self.processWidget = ProcessWidget()
        # self.ui.layout().addWidget(self.processWidget)

        self.startTimer(SCRIPT_REFRESH_INTERVAL)

        self.setFocusPolicy(Qt.StrongFocus)

        # Register hotkey
        for item in self.script_items:
            hotkey = item.meta['hotkey']
            if hotkey is not None:
                print('Hotkey: %s: %s' % (hotkey, item.name))
                QShortcut(QKeySequence(hotkey), self,
                          lambda item=item: self.execute_script(item))

        self.register_global_hotkeys()

    def execute_script(self, script, control_down=False):
        # Set selected file and current folder to as environment variables
        if script.meta['autoRun'] is False:
            args = update_env_var_explorer()
        else:
            args = None

        # HACK: always create new window
        restart_instance = None
        # if not script.name.startswith('ext/') and script.ext in ['.py', '.cmd', '.bat', '.ps1', '.ipynb', '.js']:
        #     control_down = True
        #     restart_instance = True

        new_window = True if control_down else None
        script.execute(new_window=new_window, args=args,
                       restart_instance=restart_instance)

    def register_global_hotkeys(self):
        if platform.system() == 'Windows':
            with open(GLOBAL_HOTKEY, 'w') as f:
                f.write('''#SingleInstance, Force
#include libs/ahk/ExplorerHelper.ahk
; SetTitleMatchMode, 2
RunScript(name, path)
{
    if WinExist(name)
    {
        WinActivate % name
    }
    else if WinExist("Administrator:  " name)
    {
        WinActivate % "Administrator:  " name
    }
    else
    {
        WriteExplorerInfoToJson()
        Run cmd /c ''' + sys.executable + ' "' + os.path.realpath('bin/run_script.py') + '''" --console_title "%name%" --restart_instance 0 "%path%" || pause
    }
}
''')

                for item in self.script_items:
                    hotkey = item.meta['globalHotkey']
                    if hotkey is not None:
                        print('Global Hotkey: %s: %s' % (hotkey, item.name))
                        hotkey = hotkey.replace('Ctrl+', '^')
                        hotkey = hotkey.replace('Alt+', '!')
                        hotkey = hotkey.replace('Shift+', '+')
                        hotkey = hotkey.replace('Win+', '#')

                        f.write(
                            f'{hotkey}::RunScript("{item.name}", "{item.script_path}")\n')

            subprocess.Popen([get_ahk_exe(), GLOBAL_HOTKEY],
                             close_fds=True, shell=True)

        else:
            keyboard_hooks = {}
            for item in self.script_items:
                hotkey = item.meta['globalHotkey']
                if hotkey is not None:
                    print('Global Hotkey: %s: %s' % (hotkey, item.name))
                    keyboard_hooks[hotkey] = lambda item=item: self.execute_script(
                        item)
            add_keyboard_hooks(keyboard_hooks)

    def timerEvent(self, e):
        if should_update([x[1] for x in SCRIPT_PATH_LIST]):
            self.init_script_items()
            self.update_gui(self.ui.inputBox.text())

    def init_script_items(self):
        self.script_items = []

        for prefix, script_path in SCRIPT_PATH_LIST:
            files = get_scripts_recursive(script_path)
            for file in files:
                ext = os.path.splitext(file)[1].lower()

                # File has been removed during iteration
                if not os.path.exists(file):
                    continue

                mtime = os.path.getmtime(file)

                name = _replace_prefix(file, script_path, prefix)
                name, ext = os.path.splitext(name)  # Remove ext
                name = name.replace('\\', '/')
                name = _replace_prefix(name, '/', '')
                if ext == '.link':
                    name += ' [lnk]'

                script = ScriptItem(file, name=name)

                if file not in self.modified_time or mtime > self.modified_time[file]:
                    # Check if auto run script
                    if script.meta['autoRun']:
                        print2('AUTORUN: ', end='', color='cyan')
                        print(file)
                        script.execute(new_window=False)

                # Hide files starting with '_'
                base_name = os.path.basename(file)
                if not base_name.startswith('_'):
                    self.script_items.append(script)

                self.modified_time[file] = mtime

        self.sort_scripts()

    def on_inputBox_textChanged(self, user_input=None):
        self.update_gui(user_input)

    def update_gui(self, user_input=None):
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
            self.ui.listWidget.addItem(
                '%3d. %s' % (i + 1, self.script_items[i]))

        self.editVariableWidget.update_items()  # Clear all widget
        if len(self.matched_items) > 0:
            # Set selected items
            first_matched_script = self.script_items[self.matched_items[0]]
            self.ui.listWidget.setCurrentRow(0)
            script_abs_path = os.path.abspath(first_matched_script.script_path)
            os.environ['ROSS_SELECTED_SCRIPT_PATH'] = script_abs_path

            # Display variable list
            if 'get_variables' in dir(first_matched_script) and first_matched_script.meta['template']:
                self.editVariableWidget.update_items(first_matched_script.get_variable_names(),
                                                     hide_prefix=first_matched_script.get_public_variable_prefix())

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

        self.hide()

        script = self.script_items[idx]
        self.execute_script(script, control_down=control_down)

        # Update script access time
        self.script_access_time[script.script_path] = time.time()
        with open(get_user_data_folder() + '/script_access_time.json', 'w') as f:
            json.dump(self.script_access_time, f, indent=4)

        # sort scripts
        self.sort_scripts()

        self.show()

        # Update input box
        self.ui.inputBox.setText(script.name)

        # HACK: reset title
        if platform.system() == 'Windows':
            ctypes.windll.kernel32.SetConsoleTitleA(b'MyScripts - Console')

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
            if len(self.matched_items) == 0:
                return False
            idx = self.matched_items[0]

            if e.key() == Qt.Key_Enter or e.key() == Qt.Key_Return:
                self.execute_selected_script(
                    e.modifiers() == Qt.ControlModifier)
                return True

            if e.modifiers() == Qt.ControlModifier:
                if e.key() == Qt.Key_O:
                    path = self.script_items[idx].script_path
                    script = self.script_items[idx].render()
                    ext = self.script_items[idx].ext

                    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as f:
                        f.write(script.encode())
                        f.flush()
                        open_text_editor(f.name)
                        return True

                elif e.key() == Qt.Key_F:
                    self.ui.inputBox.setFocus(True)
                    self.ui.inputBox.selectAll()
                    return True

                elif e.key() == Qt.Key_E:  # TODO: HACK: QShortcut `Ctrl+E` does not work on Ubuntu
                    run_script('scripts/ext/edit_script')
                    return True

        return super().eventFilter(obj, e)


if __name__ == '__main__':
    if is_instance_running():
        print('An instance is running. Exited.')
        sys.exit(0)

    t_start = time.time()

    refresh_env()

    bin_dir = os.path.join(os.getcwd(), 'bin')
    os.environ['PATH'] = os.pathsep.join([
        bin_dir,
        os.path.abspath('./tmp/bin')  # exe proxy
    ]) + os.pathsep + os.environ['PATH']
    os.environ['PYTHONPATH'] = os.path.abspath('./libs')

    print('Python executable: %s' % sys.executable)

    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()

    t_end = time.time()
    # time_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print2('Script is loaded. Takes %.2f secs.' %
           (t_end - t_start), color='green')

    sys.exit(app.exec_())
