import glob
import subprocess
import os


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

    ahk_script = os.path.join(os.path.dirname(__file__), '_activate_pycharm.ahk')
    subprocess.Popen(['AutoHotkeyU64.exe', ahk_script])


def open_in_androidstudio(path, line=None):
    args = [r"C:\Program Files\Android\Android Studio\bin\studio64.exe"]
    if line is not None:
        args += ['--line', str(line)]
    args.append(path)
    subprocess.Popen(args)


def open_with_text_editor(path, line_no=None):
    if os.name == 'posix':
        subprocess.Popen(['atom', path])
    else:
        try:
            args = ['notepad++', path]
            if line_no is not None:
                args.append(f'-n{line_no}')
            subprocess.Popen(args, creationflags=subprocess.CREATE_NEW_CONSOLE)
        except:
            subprocess.Popen(['notepad', path], creationflags=subprocess.CREATE_NEW_CONSOLE)
