import os

from _android import logcat, restart_app
from _shutil import setup_logger

if __name__ == "__main__":
    setup_logger()
    # Run app using monkey:
    # adb shell monkey -p your.app.package.name -c android.intent.category.LAUNCHER 1

    pkg = os.environ.get("PKG_NAME")

    restart_app(pkg, use_monkey=bool(os.environ.get("USE_MONKEY")))
    if os.environ.get("_SHOW_LOGCAT"):
        logcat(pkg=pkg)
