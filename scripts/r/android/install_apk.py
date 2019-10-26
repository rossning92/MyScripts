from _shutil import *
import re
from _setup_android_env import *
from _android import *

file = os.environ['SELECTED_FILE']
assert os.path.splitext(file)[1].lower() == '.apk'




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
setup_android_env()
print('Start the app...')
out = subprocess.check_output(['aapt', 'dump', 'badging', file]).decode()
try:
    package_name = re.search("package: name='(.*?)'", out).group(1)
    activity_name = re.search("launchable-activity: name='(.*?)'", out).group(1)
    print('PackageName: %s' % package_name)
    print('LaunchableActivity: %s' % activity_name)
    start_app(package_name)
    logcat(package_name)
except:
    print('Cannot launch the app')
