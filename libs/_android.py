from _shutil import *


def start_app(pkg_name):
    args = 'adb shell monkey -p %s -c android.intent.category.LAUNCHER 1' % pkg_name
    print('Start app: ' + args)
    call(args)


def logcat(pkg_name=None):
    pid_map = {}

    def filter_line(line):
        # Filter by pkg_name
        if pkg_name is not None:
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

            if pkg_name.encode() not in process_name:
                return None

        return line

    call('adb logcat -c')

    call_highlight('adb logcat',
                   filter_line=filter_line,
                   highlight={
                       ' (E|F) ': 'RED',
                       ' W ': 'YELLOW',
                       'ROSS:': 'GREEN'
                   })
