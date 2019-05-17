from _shutil import *
import re

file = os.environ['SELECTED_FILE']
assert os.path.splitext(file)[1].lower() == '.apk'

print('Install apk...')
try:
    check_output(['adb', 'install', '-r', file], stderr=subprocess.STDOUT)
except subprocess.CalledProcessError as e:
    msg = e.output.decode()
    match = re.search('INSTALL_FAILED_UPDATE_INCOMPATIBLE: Package ([^ ]+)', msg)
    if match is not None:
        pkg = match.group(1)
        print('[INSTALL_FAILED_UPDATE_INCOMPATIBLE] Uninstalling %s...' % pkg)
        call('adb uninstall %s' % pkg)
        subprocess.check_call(['adb', 'install', '-r', file])

tar_file = os.path.splitext(file)[0] + '.tar'
pkg = os.path.splitext(os.path.basename(file))[0]
if exists(tar_file):
    print('Restore data...')
    call(f'adb push "{tar_file}" /sdcard/')
    call(f'adb shell su -c tar -xf /sdcard/{pkg}.tar')

    out = check_output(f'adb shell dumpsys package {pkg} | grep userId')
    out = out.decode().strip()

    userId = re.findall(r'userId=(\d+)', out)[0]
    print(f'Change owner of {pkg} => {userId}')
    call(f'adb shell su -c chown -R {userId}:{userId} /data/data/{pkg}')

    print('Reset SELinux perms')
    call(f'adb shell su -c restorecon -R /data/data/{pkg}')
