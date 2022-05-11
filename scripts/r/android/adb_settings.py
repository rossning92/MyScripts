import numpy as np
from _shutil import proc_lines, set_clip
from _term import select_option

last_result = None
while True:
    lines = ["<refresh>"]
    for ns in ["system", "secure", "global"]:
        lines += ["system " + x for x in proc_lines("adb shell settings list " + ns)]
    lines = [x.replace("=", " ") for x in lines]

    if last_result is not None:
        print(np.setdiff1d(last_result, lines))

    i = select_option(lines)
    if lines[i] == "<refresh>":
        last_result = lines
        continue

    set_clip("adb shell settings put " + lines[i])
    break
