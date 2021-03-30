from _shutil import *
from _script import *
from _android import *

if __name__ == "__main__":
    # Run app using monkey:
    # adb shell monkey -p your.app.package.name -c android.intent.category.LAUNCHER 1

    if len(sys.argv) == 2:
        pkg = sys.argv[1]
    else:
        pkg = r"{{PKG_NAME}}"

    # call2("adb logcat -c")

    restart_app(pkg, use_monkey=False)

    if "{{_SHOW_LOGCAT}}":
        logcat(proc_name=pkg)
