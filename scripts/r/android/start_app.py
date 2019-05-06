from _shutil import *
from _script import *
from _android import *

pkg = r'{{PKG_NAME}}'

call(f'adb shell am force-stop {pkg}')

start_app(pkg)

if '{{START_APP_SHOW_LOGCAT}}':
    run_script('logcat', variables={'PKG_NAME': pkg, 'LOGCAT_FILTER': ''})
