from _shutil import *
from _script import *
from _android import *

pkg = '{{PKG_NAME}}'

restart_app(pkg)

if '{{_SHOW_LOGCAT}}':
    logcat(pkg)
