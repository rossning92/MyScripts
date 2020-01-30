import glob
import subprocess
import os
from _shutil import exec_ahk, start_process
from _appmanager import get_executable


def get_pycharm_executable():
    files = glob.glob(r'C:\Program Files\JetBrains\**\pycharm64.exe', recursive=True) + glob.glob(
        r'C:\Program Files (x86)\JetBrains\**\pycharm64.exe', recursive=True)
    if len(files) == 0:
        raise Exception('Cannot find pycharm.')
    pycharm = files[0]
    return pycharm


def open_in_pycharm(path):
    pycharm = get_pycharm_executable()
    subprocess.Popen([pycharm, path])

    ahk_script = os.path.join(os.path.dirname(
        __file__), '_activate_pycharm.ahk')
    subprocess.Popen(['AutoHotkeyU64.exe', ahk_script])


def open_in_androidstudio(path, line=None):
    args = [r"C:\Program Files\Android\Android Studio\bin\studio64.exe"]
    if line is not None:
        args += ['--line', str(line)]
    args.append(path)
    subprocess.Popen(args)
    exec_ahk('WinActivate ahk_exe studio64.exe')


def open_in_vscode(file, line_no=None):
    vscode = get_executable('vscode')
    if type(file) == str:
        if line_no is None:
            subprocess.Popen([vscode, file], close_fds=True)
        else:
            subprocess.Popen(
                [vscode, f'{file}:{line_no}', '-g'], close_fds=True)
    else:
        subprocess.Popen([vscode] + file, close_fds=True)


def open_with_text_editor(path, line_no=None):
    if os.name == 'posix':
        subprocess.Popen(['code', path])
    else:
        if os.path.splitext(path)[1] == '.py':
            open_in_pycharm(path)
        elif os.path.splitext(path)[1] == '.js':
            open_in_vscode(path)
        else:
            try:
                args = ['notepad++', path]
                if line_no is not None:
                    args.append(f'-n{line_no}')
                subprocess.Popen(args, close_fds=True)
            except:
                subprocess.Popen(['notepad', path], close_fds=True)
