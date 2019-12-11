from _gui import *
from _shutil import *

lines = []
for ns in ['system', 'secure', 'global']:
    lines += ['system ' + x for x in read_lines('adb shell settings list ' + ns)]

lines = [x.replace('=', ' ') for x in lines]

i = search(lines)
set_clip('adb shell settings put ' + lines[i])
