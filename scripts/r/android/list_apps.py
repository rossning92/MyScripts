from _shutil import *
from _gui import *

lines = check_output('adb shell pm list packages').decode().splitlines()
search(lines)
