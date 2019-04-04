from _shutil import *


def start_app(pkg):
    args = 'adb shell monkey -p %s -c android.intent.category.LAUNCHER 1' % pkg
    print('Start app: ' + args)
    call(args)


def logcat(pkg_name=None, highlight=None, filter_str=None):
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

        # filter by string
        if filter_str and re.search(filter_str.encode(), line) is None:
            return None

        return line

    call('adb logcat -c')

    if highlight is None:
        highlight = {}

    call_highlight('adb logcat',
                   filter_line=filter_line,
                   highlight={
                       ' (E|F) ': 'RED',
                       '!!.*?!!': 'RED',
                       ' W ': 'YELLOW',
                       'ROSS:': 'GREEN',
                       **highlight
                   })


def backup_pkg(pkg, out_dir=None):
    # Get apk path
    # 'package:/data/app/com.github.uiautomator-1AfatTFmPxzjNwUtT-5h7w==/base.apk'
    out = subprocess.check_output('adb shell pm path %s' % pkg)
    apk_path = out.decode().strip().replace('package:', '')

    # Pull apk
    subprocess.call('adb pull %s %s.apk' % (apk_path, pkg), cwd=out_dir)

    # Pull data
    subprocess.call(f'adb shell su -c tar -cf /sdcard/{pkg}.tar /data/data/{pkg}')
    subprocess.call(f'adb pull /sdcard/{pkg}.tar', cwd=out_dir)
    subprocess.call(f'adb shell rm /sdcard/{pkg}.tar')