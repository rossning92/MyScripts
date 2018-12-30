import glob


def _find_pycharm():
    global pycharm
    files = glob.glob(r'C:\Program Files\JetBrains\**\pycharm64.exe', recursive=True) + glob.glob(
        r'C:\Program Files (x86)\JetBrains\**\pycharm64.exe', recursive=True)
    if len(files) == 0:
        raise Exception('Cannot find pycharm.')
    pycharm = files[0]


_find_pycharm()
