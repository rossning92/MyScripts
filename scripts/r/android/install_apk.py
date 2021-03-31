from _shutil import *
import re
from _android import *


files = get_files()

for file in files:
    assert os.path.splitext(file)[1].lower() == ".apk"

    print("APK file: %s" % file)
    adb_install2(file)

    if len(files) == 1:
        # Run app
        pkg = get_pkg_name_apk(file)
        try:
            start_app(pkg)
        except:
            print2("ERROR: start app failed.", color="red")
        logcat(pkg)
