from _shutil import *
import datetime


def start_app(pkg, use_monkey=False):
    if use_monkey:
        args = 'adb shell monkey -p %s -c android.intent.category.LAUNCHER 1' % pkg
        print('> ' + args)
        subprocess.call(args, shell=True)
    else:
        args = f'adb shell "dumpsys package | grep -i {pkg}/ | grep Activity"'
        out = subprocess.check_output(args, shell=True)
        out = out.decode().strip()
        # out = out.splitlines()[0].strip()

        id, pkg_activity = out.split()
        print('> ActivityName: ' + pkg_activity)
        args = 'adb shell am start -n %s' % pkg_activity
        print('> ' + args)
        call2(args)


def restart_app(pkg):
    print('Stop app: ' + pkg)
    call2('adb shell am force-stop %s' % pkg)
    start_app(pkg)


def restart_current_app():
    out = check_output('adb shell "dumpsys activity activities | grep mFocusedActivity"', shell=True).decode().strip()
    match = re.search(r'\{([^}]+)\}', out).group(1)
    pkg_activity = match.split()[2]
    pkg, activity = pkg_activity.split('/')

    call2('adb shell am force-stop %s' % pkg)
    call2('adb shell am start -n %s' % pkg_activity)


def logcat(pkg_name=None, highlight=None, filter_str=None, clear=False, show_log_after_secs=-2):
    pid_map = {}

    def filter_line(line):
        # Always show fatal message (backtrace)
        if b' F DEBUG ' in line:
            return line
        elif b'ROSS:' in line:
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

        if show_log_after_secs is not None:
            try:
                dt = datetime.datetime.strptime(line[:14].decode(), '%m-%d %H:%M:%S')
                if dt < dt_start:
                    return None
            except:
                pass

        # Filter by string
        if filter_str and re.search(filter_str.encode(), line) is None:
            return None

        return line

    if show_log_after_secs is not None:
        out = subprocess.check_output(['adb', 'shell', "date '+%m-%d %H:%M:%S'"], shell=True)
        out = out.decode().strip()
        dt_start = datetime.datetime.strptime(out, '%m-%d %H:%M:%S')
        dt_start += datetime.timedelta(seconds=show_log_after_secs)

    if clear:
        call2('adb logcat -c')

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


def setup_android_env():
    env = os.environ

    ADK_SEARCH_PATH = [
        # Installed by choco
        r'C:\Android\android-sdk',

        # Default SDK path installed by Android Studio
        os.path.abspath(os.getenv('LOCALAPPDATA') + '/Android/Sdk')
    ]

    # ANDROID_HOME
    for p in ADK_SEARCH_PATH:
        if os.path.exists(p):
            env['ANDROID_HOME'] = p
            print2('ANDROID_HOME=%s' % p)
            break
    if 'ANDROID_HOME' not in env:
        raise Exception('Cannot find ANDROID_HOME')

    # NDK
    env['ANDROID_NDK_HOME'] = \
        env['ANDROID_NDK_ROOT'] = \
        env['NDKROOT'] = \
        env['NDK_ROOT'] = \
        env['ANDROID_HOME'] + '/ndk-bundle'

    # Setup PATH
    path = [
        env['ANDROID_HOME'] + '/platform-tools',
        env['ANDROID_HOME'] + '/tools',
        env['ANDROID_HOME'] + '/tools/bin',
        env['ANDROID_HOME'] + '/ndk-bundle',
    ]

    # Set PATH environ
    jdk_list = sorted(glob.glob(r'C:\Program Files\Java\jdk*'))
    if len(jdk_list) == 0:
        raise Exception('Cannot find JDK')
    jdk_path = jdk_list[-1] + '\\bin'  # Choose latest JDK
    print2('JDK: ' + jdk_path)
    path.append(jdk_path)

    # Android build tools (latest)
    path_list = sorted(glob.glob(env['ANDROID_HOME'] + '\\build-tools\\*'))
    if len(path_list) > 0:
        print2('Android SDK: build-tools: ' + path_list[-1])
        path.append(path_list[-1])

    prepend_to_path(path)
