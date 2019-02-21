from _shutil import *

pid_map = {}


def filter_line(line):
    try:
        arr = line.split()
        pid = int(arr[2])
    except:
        return line

    if pid not in pid_map:
        out = check_output('adb shell ps -p %d' % pid)
        process_name = out.split()[-1]
        pid_map[pid] = process_name
    else:
        process_name = pid_map[pid]

    if b'{{PKG_NAME}}' not in process_name:
        return None

    return line


call('adb logcat -c')

call_highlight('adb logcat',
               filter_line=filter_line,
               highlight={' (E|F) ': 'RED'})
