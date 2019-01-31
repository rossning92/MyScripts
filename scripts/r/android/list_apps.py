from _shutil import *
from _gui import *

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
    'uninstall'
]

i = search(opt)
if i == -1:
    sys.exit(1)

if opt[i] == 'start':
    call('adb shell monkey -p %s -c android.intent.category.LAUNCHER 1' % pkg)
