from _shutil import *
from _script import *
from _android import *

pkg = r'{{PKG_NAME}}'

call2('adb logcat -c')

restart_app(pkg, use_monkey=bool('{{USE_MONKEY}}'))

if '{{_SHOW_LOGCAT}}':
    logcat(proc_name=pkg)
