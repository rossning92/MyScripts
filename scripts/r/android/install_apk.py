from _shutil import *
import re
from _setup_android_env import *
from _android import *

file = os.environ['SELECTED_FILE']
assert os.path.splitext(file)[1].lower() == '.apk'

# call_echo('adb wait-for-device')

adb_install(file)

# TODO: check super su / root permission
su = 'su -c'
su = ''

# Push data
tar_file = os.path.splitext(file)[0] + '.tar'
pkg = os.path.splitext(os.path.basename(file))[0]
if exists(tar_file):
    print2('Restore data...')
    call(f'adb push "{tar_file}" /sdcard/')
    call(f'adb shell {su} tar -xf /sdcard/{pkg}.tar')

    out = check_output(f'adb shell dumpsys package {pkg} | grep userId')
    out = out.decode().strip()

    userId = re.findall(r'userId=(\d+)', out)[0]
    print2(f'Change owner of {pkg} => {userId}')
    call(f'adb shell {su} chown -R {userId}:{userId} /data/data/{pkg}')

    print2('Reset SELinux perms')
    call(f'adb shell {su} restorecon -R /data/data/{pkg}')

# Push obb file
obb_folder = os.path.splitext(file)[0]
if os.path.isdir(obb_folder):
    print2('Push obb...')
    call2(f'adb push "{obb_folder}" /sdcard/android/obb')

# Run app
pkg = get_pkg_name_apk(file)
try:
    start_app(pkg)
    logcat(pkg)
except:
    print2('ERROR: start app failed.', color='red')
