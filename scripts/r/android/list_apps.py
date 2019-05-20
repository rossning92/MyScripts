from _shutil import *
from _gui import *
from _script import *
from _android import *

s = check_output('adb shell pm list packages').decode()
s = s.replace('package:', '')
lines = s.splitlines()
lines = sorted(lines)
i = search(lines)
if i == -1:
    sys.exit(1)

pkg = lines[i]
print("Selected: " + pkg)

opt = [
    'start',
    'uninstall',
    'backup',
]

i = search(opt)
if i == -1:
    sys.exit(1)

set_variable('PKG_NAME', pkg)

if opt[i] == 'start':
    set_variable('PKG_NAME', pkg)
    run_script('restart_app', variables={'PKG_NAME': pkg}, new_window=True)

elif opt[i] == 'backup':
    out_dir = expanduser('~/Desktop/android_backup')
    mkdir(out_dir)
    backup_pkg(pkg, out_dir=out_dir)

elif opt[i] == 'uninstall':
    call(f'adb uninstall {pkg}')
