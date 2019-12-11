from _gui import *
from _shutil import *
import numpy as np

last_result = None
while True:
    lines = ['<refresh>']
    for ns in ['system', 'secure', 'global']:
        lines += ['system ' + x for x in read_lines('adb shell settings list ' + ns)]
    lines = [x.replace('=', ' ') for x in lines]

    if last_result is not None:
        print(np.setdiff1d(last_result, lines))

    i = search(lines)
    if lines[i] == '<refresh>':
        last_result = lines
        continue

    set_clip('adb shell settings put ' + lines[i])
    break
