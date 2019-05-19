from _shutil import *
from _script import *
from _android import *

pkg = '{{PKG_NAME}}'

call(f'adb shell am force-stop {pkg}')

start_app(pkg)

if '{{RESTART_APP_SHOW_LOGCAT}}':
    logcat(pkg)
