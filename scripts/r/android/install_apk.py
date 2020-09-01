from _shutil import *
import re
from _setup_android_env import *
from _android import *

file = os.environ['_FILE']
assert os.path.splitext(file)[1].lower() == '.apk'

print('APK file: %s' % file)
adb_install2(file)

# Run app
pkg = get_pkg_name_apk(file)
try:
    start_app(pkg)
except:
    print2('ERROR: start app failed.', color='red')
logcat(pkg)
