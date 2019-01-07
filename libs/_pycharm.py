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


def open_with_pycharm(path):
    pycharm = get_pycharm_executable()
    subprocess.Popen([pycharm, path])

    subprocess.Popen(['AutoHotkeyU64.exe', os.path.join(os.path.dirname(__file__), '_activate_pycharm.ahk')])
