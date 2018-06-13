#!/usr/bin/env python3

import subprocess
import datetime
import os
import tempfile
from colorama import Fore
import colorama
import glob
import jinja2
import re
import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtCore import Qt, QEvent
from os.path import expanduser
import json


# https://phabricator.intern.facebook.com/diffusion/OVRSOURCE/browse/master/Software/Apps/Native/VrShell/
VR_SHELL = '/Users/rossning92/vrshell/ovrsource/Software/Apps/Native/VrShell'
# VR_SHELL  = '/Users/rossning92/ovrsource/Software/Apps/Native/VrShell'

VR_DRIVER = '/Users/rossning92/ovrsource/Software/OculusSDK/Mobile/VrDriver'
PANEL_APP = '/Users/rossning92/vrshell/ovrsource/Software/Apps/Native/VrShell/MyFancyProject'

SETUP_ENV = '''
export ANDROID_HOME=/opt/android_sdk
export ANDROID_SDK=$ANDROID_HOME
export ANDROID_SDK_ROOT=$ANDROID_SDK
export ANDROID_NDK=/opt/android_sdk/ndk-bundle
export ANDROID_NDK_REPOSITORY=$ANDROID_NDK
export ANDROID_NDK_HOME=$ANDROID_NDK
export ADB_PATH=$ANDROID_SDK_ROOT/platform-tools/adb
export PATH=$ANDROID_HOME/platform-tools:$ANDROID_HOME/tools:$ANDROID_NDK:$PATH
'''


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


def get_context(windows_path=False):
    ovrsource = 'ovrsource2'
    if windows_path:
        ovrsource = 'C:\\open\\' + ovrsource
    else:
        ovrsource = '/c/open/' + ovrsource

    return {
        'VR_SHELL': VR_SHELL,
        'VR_DRIVER': VR_DRIVER,
        'PANEL_APP': PANEL_APP,
        'SETUP_ENV': SETUP_ENV,
        'OVRSOURCE': ovrsource,
        'BUILD_CONFIG': 'Debug',
        **variables
    }


def open_text_editor(path):
    if os.name == 'posix':
        subprocess.Popen(['atom', path])
    else:
        subprocess.Popen(['notepad++', path])


colorama.init()


def bash(cmd):
    if os.name == 'nt':
        subprocess.call([
            # r'C:\Program Files\Git\git-bash.exe',
            r'C:\Program Files\Git\bin\bash.exe',
            '--login',
            '-i',
            '-c',
            cmd])
    elif os.name == 'posix':  # MacOSX
        subprocess.call(cmd, shell=True)
    else:
        raise Exception('Non supported OS version')


def cmd(cmd, newterminal=False, runasadmin=False):
    assert os.name == 'nt'
    with tempfile.NamedTemporaryFile(delete=False, suffix='.cmd') as temp:
        # cmd = cmd.replace('\n', '\r\n')  # TODO
        temp.write(cmd.encode('utf-8'))
        temp.flush()


        cmdline = 'cmd /c {}{}{}'.format(
            'start /i cmd /c ' if newterminal else '',
            temp.name,
            ' & pause' if newterminal else ''
        )
        if runasadmin:
            params.insert(0, 'Elevate.exe')
            # params.append('& if errorlevel 1 pause') # Pause when failure

        print(cmdline)
        ret = subprocess.call(cmdline)
        print(Fore.LIGHTGREEN_EX + 'Script return code: ' + str(ret) + Fore.RESET)


menu_items = []


class Item:
    def __str__(self):
        return self.name

    def execute(self):
        raise NotImplementedError


class MenuItem(Item):
    def __init__(self, func):
        self.name = func.__name__
        self.func = func

    def execute(self):
        self.func()


def menu_item(f):
    menu_items.append(MenuItem(f))
    return f


class ScriptItem(Item):
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath="./"))
    loaded_scripts = {}

    def __init__(self, script_path):
        # BUG: jinja2 doesn't support '\' in path
        self.script_path = script_path.replace('\\', '/')

        base_name = os.path.basename(self.script_path)
        name, ext = os.path.splitext(base_name)

        self.ext = ext

        patt = r'\[([a-zA-Z_][a-zA-Z_0-9]*)\]'
        self.flags = set(re.findall(patt, name))
        self.name = re.sub(patt, '', name)

        ScriptItem.loaded_scripts[self.name] = self

    def render(self):
        template = ScriptItem.env.get_template(self.script_path)
        script = template.render({
            'include': ScriptItem.include,
            **get_context(self.ext.lower() == '.cmd')})
        return script

    def execute(self):
        script = self.render()
        if self.ext == '.cmd':
            cmd(script,
                runasadmin=('run_as_admin' in self.flags),
                newterminal=('new_window' in self.flags))
        elif self.ext == '.sh':
            bash(script)
        else:
            print('Not supported script:', self.ext)

    def get_variables(self):
        with open(self.script_path) as f:
            script = f.read()
            variables = re.findall(r'\{\{([A-Z_]+)\}\}', script)
            return variables

    def include(script_name):
        return ScriptItem.loaded_scripts[script_name].render()


def exec2(name):
    matched = list(filter(lambda x: x.name == name, menu_items))
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


@menu_item
def _build_panelapp_multiple_res():
    # Different resolutions
    res = ((1440, 1620), (1320, 1485), (1200, 1350), (1080, 1215), (960, 1080))
    ref_res = (1280, 1440)

    for i in range(len(res)):

        res_str = '%dx%d' % (res[i][0], res[i][1])
        print(Fore.LIGHTGREEN_EX + 'Building for res: ' + res_str + Fore.RESET)

        # Modify src files
        ratio = res[i][0] / ref_res[0]
        bash(f'''
        cd {PANEL_APP}/Src
        sed -i.bak 's|(1)|{ratio}|g' MyFancyProject.cpp
        cd {VR_SHELL}/VrShell/Src/AppModel
        sed -i.bak 's|(1)|{ratio}|g' PanelRenderLayer.cpp
        ''')

        exec2('build_my_panel_app')
        exec2('build_VrShell')

        # Recover src files
        bash(f'''
        cd {PANEL_APP}/Src
        mv MyFancyProject.cpp.bak MyFancyProject.cpp
        cd {VR_SHELL}/VrShell/Src/AppModel
        mv PanelRenderLayer.cpp.bak PanelRenderLayer.cpp
        ''')

        # Copy files
        bash(f'cp {VR_SHELL}/VrShell/Projects/Android-MP/build/outputs/apk/release/vrshell-release.apk {res_str}_vrshell.apk')
        bash(f'cp {PANEL_APP}/Projects/Android/build/outputs/apk/release/MyFancyProject-armeabi-v7a-release.apk {res_str}_panelapp.apk')


@menu_item
def _build_vrdriver_fov_on_and_off():
    exec2('build_VrDriver')
    bash(f'cp {VR_DRIVER}/Projects/Android/build/outputs/apk/release/VrDriver-release.apk vrdriver.apk')


@menu_item
def get_ovrsource________():
    OVR_SRC_PATH = r'C:\open\ovrsource2'

    # https://our.intern.facebook.com/intern/wiki/Dex/ovrsource
    # ovrsource: bi-directional bridge:
    #   Oculus Perforce server <=> Mercurial repository
    if os.name == 'nt':
        cmd(f'''
fbclone ovrsource {OVR_SRC_PATH}
cd {OVR_SRC_PATH}
hg sparse enableprofile SparseProfiles/OculusPCSDK.sparse
hg sparse enableprofile SparseProfiles/OculusCoreTech.sparse
''')

    if os.name == 'posix':
        bash(f'''
cd ~
if [ ! -d ovrsource ]; then
    fbclone ovrsource --sparse SparseProfiles/OculusSkyline.sparse
fi
cd ovrsource


#hg sparse enableprofile SparseProfiles/OculusVrShell.sparse
#hg sparse enableprofile SparseProfiles/OculusMobileSDK.sparse

#hg sparse enableprofile SparseProfiles/OculusPCSDK.sparse
#hg sparse enableprofile SparseProfiles/OculusCoreTech.sparse
''')


@menu_item
def edit_script():
    items = list(ScriptItem.loaded_scripts.values())
    idx = select_item(items, prompt='Edit script: enter script name:')
    path = items[idx].script_path
    if os.name == 'posix':
        subprocess.Popen(['atom', path])
    else:
        subprocess.Popen(['notepad++', path])


@menu_item
def show_script():
    items = list(ScriptItem.loaded_scripts.values())
    idx = select_item(items, prompt='Show script: enter script name:')
    script = items[idx].render()
    ext = items[idx].ext

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as f:
        f.write(script.encode())
        f.flush()
        open_text_editor(f.name)


@menu_item
def new_script():
    print(Fore.LIGHTGREEN_EX + 'Enter new script name:' + Fore.RESET)
    user_input = input('> ')
    path = 'scripts/' + user_input
    subprocess.Popen(['notepad++', path])


@menu_item
def hg_test():
    # Enable histedit extension
    insert_line_if_not_exist('histedit =', '~/.hgrc', '[extensions]')

    out = subprocess.check_output('cd ~/ovrsource ; hg log --limit 3', shell=True)
    out = out.decode()
    out = re.findall('changeset:\s+([a-z0-9]+)', out)

    subprocess.call('cd ~/ovrsource ; hg checkout %s' % out[2], shell=True)
    subprocess.call('cd ~/ovrsource ; hg graft %s' % out[0], shell=True)
    subprocess.call('cd ~/ovrsource ; hg graft %s' % out[1], shell=True)


class EditVariableWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.variableUIs = {}
        self.setLayout(QFormLayout())

        try:
            with open('variables.json') as f:
                self.variables = json.load(f)
        except Exception:
            self.variables = {}

    def init(self, varList=[]):
        for i in range(self.layout().count()):
            self.layout().itemAt(i).widget().deleteLater()

        row = 0
        self.variableUIs = {}
        for variable in varList:
            comboBox = QComboBox()
            comboBox.setEditable(True)
            if variable in self.variables:
                comboBox.setCurrentText(self.variables[variable])

            self.layout().addRow(QLabel(variable + ':'), comboBox)

            self.variableUIs[variable] = comboBox
            row += 1

    def save(self):
        for k, v in self.variableUIs.items():
            self.variables[k] = v.currentText()

        with open('variables.json', 'w') as f:
            json.dump(self.variables, f, indent=4)

    def get_variables(self):
        return self.variables


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi('MainDialog.ui', self)
        self.installEventFilter(self)
        self.setWindowTitle('MyScripts - GUI')
        self.matched_items = []

        self.editVariableWidget = EditVariableWidget()
        self.ui.layout().addWidget(self.editVariableWidget)

        self.on_inputBox_textChanged()

    def on_inputBox_textChanged(self, user_input=None):
        self.ui.listWidget.clear()
        self.matched_items = []

        if user_input is None or user_input == '':
            self.matched_items = list(range(len(menu_items)))
        elif user_input.isdigit():
            idx = int(user_input) - 1
            if idx >= 0 and idx < len(menu_items):
                self.matched_items.append(idx)
        else:
            user_input = user_input.lower()
            user_input_tokens = user_input.split(' ')
            for i in range(len(menu_items)):
                menu_name = menu_items[i].name.lower()
                matched = all([(x in menu_name) for x in user_input_tokens])
                if matched:
                    self.matched_items.append(i)

        for i in self.matched_items:
            self.ui.listWidget.addItem('[%d] %s' % (i + 1, menu_items[i]))
            if 'get_variables' in dir(menu_items[i]):
                self.editVariableWidget.init(menu_items[i].get_variables())

        if self.ui.listWidget.count() > 0:
            self.ui.listWidget.setCurrentRow(0)

    def event(self, e):
        if e.type() == QEvent.WindowActivate:
            self.ui.inputBox.setFocus(True)
            self.ui.inputBox.selectAll()
        return super().event(e)

    def eventFilter(self, obj, e):
        if e.type() == QEvent.KeyPress:

            if e.key() == Qt.Key_0:
                print('YOYO')

            if len(self.matched_items) == 0:
                return False
            idx = self.matched_items[0]

            if e.key() == Qt.Key_Enter or e.key() == Qt.Key_Return:
                self.ui.editVariableWidget.save()
                global variables
                variables = self.ui.editVariableWidget.get_variables()
                self.hide()
                menu_items[idx].execute()
                self.show()
                return True

            if e.modifiers() == Qt.ControlModifier and e.key() == Qt.Key_E:
                path = menu_items[idx].script_path
                open_text_editor(path)
                return True

            if e.modifiers() == Qt.ControlModifier and e.key() == Qt.Key_O:
                path = menu_items[idx].script_path
                script = menu_items[idx].render()
                ext = menu_items[idx].ext

                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as f:
                    f.write(script.encode())
                    f.flush()
                    open_text_editor(f.name)
                    return True

        return super().eventFilter(obj, e)


if __name__ == '__main__':
    time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(Fore.LIGHTGREEN_EX + time + ' Script is loaded' + Fore.RESET)

    # Load scripts
    script_items = []
    files = glob.glob('scripts/*.*', recursive=True)
    files.sort(key=os.path.getmtime, reverse=True)
    for file in files:
        script_items.append(ScriptItem(file))

    menu_items = script_items + menu_items

    if True:
        app = QApplication(sys.argv)

        ex = MainWindow()
        ex.show()

        sys.exit(app.exec_())

    while True:
        opt = select_item(menu_items, prompt='Run script:')

        # Execute command
        menu_items[opt].execute()

        last_opt = opt


# hg rebase -s <target_commit_id> -d <dest_commit_id>
