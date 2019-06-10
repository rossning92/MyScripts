from _shutil import *


def start_app(pkg):
    args = 'adb shell monkey -p %s -c android.intent.category.LAUNCHER 1' % pkg
    print('> ' + args)
    subprocess.call(args, shell=True)


def restart_app(pkg):
    args = f'adb shell am force-stop {pkg}'
    print('> ' + args)
    subprocess.call(args, shell=True)
    start_app(pkg)


def restart_current_app():
    out = check_output('adb shell "dumpsys activity activities | grep mFocusedActivity"', shell=True).decode().strip()
    match = re.search(r'\{([^}]+)\}', out).group(1)
    pkg_activity = match.split()[2]
    pkg, activity = pkg_activity.split('/')

    call2('adb shell am force-stop %s' % pkg)
    call2('adb shell am start -n %s' % pkg_activity)


def logcat(pkg_name=None, highlight=None, filter_str=None):
    pid_map = {}

    def filter_line(line):
        # Always show fatal message (backtrace)
        if b' F DEBUG ' in line:
            return line

        # Filter by pkg_name
        if pkg_name:
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

    # Check root permission
    try:
        subprocess.call('adb root')
        su = ''
    except:
        su = 'su -c'

    # Pull data
    subprocess.call(f'adb shell {su} tar -cf /sdcard/{pkg}.tar /data/data/{pkg}')
    subprocess.call(f'adb pull /sdcard/{pkg}.tar', cwd=out_dir)
    subprocess.call(f'adb pull /sdcard/android/obb/{pkg}', cwd=out_dir)
    subprocess.call(f'adb shell rm /sdcard/{pkg}.tar')


def screenshot(out_file=None):
    if out_file is None:
        src_file = datetime.datetime.now().strftime('Screenshot_%y%m%d%H%M%S.png')
    else:
        src_file = os.path.basename(out_file)

    print('Taking screenshot...')
    subprocess.check_call(['adb', 'shell', 'screencap -p /sdcard/%s' % src_file])
    subprocess.check_call(['adb', 'pull', '-a', '/sdcard/%s' % src_file, out_file])
    subprocess.check_call(['adb', 'shell', 'rm /sdcard/%s' % src_file])


def get_active_pkg_and_activity():
    out = check_output('adb shell "dumpsys activity activities | grep mFocusedActivity"', shell=True).decode().strip()
    match = re.search(r'\{([^}]+)\}', out).group(1)
    pkg_activity = match.split()[2]
    pkg, activity = pkg_activity.split('/')
    return pkg, activity


def take_screenshot(file_name=None):
    if not file_name:
        file_name = datetime.datetime.now().strftime('Screenshot_%y%m%d%H%M%S.png')

    print('Taking screenshot ...')
    subprocess.check_call(['adb', 'shell', 'screencap -p /sdcard/%s' % file_name])
    subprocess.check_call(['adb', 'pull', '-a', '/sdcard/%s' % file_name])
    subprocess.check_call(['adb', 'shell', 'rm /sdcard/%s' % file_name])
