import argparse
import logging
import os
import subprocess

from _shutil import call_echo
from utils.android import clear_logcat, logcat, restart_app
from utils.logger import setup_logger

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pkg", type=str, nargs="?", default=None)
    args = parser.parse_args()

    setup_logger(level=logging.DEBUG)

    if os.environ.get("WAKE_UP_DEVICE"):
        call_echo(["run_script", "r/android/wake_up_device.sh"])

    if args.pkg:
        pkg = args.pkg
    else:
        pkg = os.environ["PKG_NAME"]

    clear_logcat()
    restart_app(pkg, use_monkey=bool(os.environ.get("USE_MONKEY")))

    if os.environ.get("_SHOW_FULL_LOGCAT"):
        subprocess.call(["adb", "logcat"])
    else:
        logcat(
            pkg=pkg,
            show_fatal_error=bool(os.environ.get("LOGCAT_SHOW_FATAL_ERROR")),
        )
