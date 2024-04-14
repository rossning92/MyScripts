import argparse
import logging
import os

from _android import restart_app
from _shutil import call_echo
from utils.logger import setup_logger

if __name__ == "__main__":
    setup_logger(level=logging.DEBUG)
    # Run app using monkey:
    # adb shell monkey -p your.app.package.name -c android.intent.category.LAUNCHER 1

    if os.environ.get("CLEAR_LOGCAT_BEFORE_RESTART_APP"):
        call_echo(["run_script", "r/android/clear_logcat.sh"])

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pkg", type=str, nargs="?", default=None)
    args = parser.parse_args()

    if os.environ.get("WAKE_UP_DEVICE"):
        call_echo(["run_script", "r/android/wake_up_device.sh"])

    if args.pkg:
        pkg = args.pkg
    else:
        pkg = os.environ.get("PKG_NAME")

    restart_app(pkg, use_monkey=bool(os.environ.get("USE_MONKEY")))
