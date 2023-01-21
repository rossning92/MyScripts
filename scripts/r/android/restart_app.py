import argparse
import logging
import os
import subprocess

from _android import clear_logcat, logcat, restart_app
from _shutil import call_echo, setup_logger

if __name__ == "__main__":
    setup_logger(level=logging.DEBUG)
    # Run app using monkey:
    # adb shell monkey -p your.app.package.name -c android.intent.category.LAUNCHER 1

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pkg", type=str, nargs="?", default=None)
    args = parser.parse_args()

    if os.environ.get("WAKE_UP_DEVICE"):
        call_echo(["run_script", "r/android/wake_up_device.sh"])

    if args.pkg:
        restart_app(args.pkg, use_monkey=bool(os.environ.get("USE_MONKEY")))

    else:
        pkg = os.environ.get("PKG_NAME")

        clear_logcat()
        restart_app(pkg, use_monkey=bool(os.environ.get("USE_MONKEY")))
        if os.environ.get("_SHOW_LOGCAT"):
            if os.environ.get("_SHOW_FULL_LOGCAT"):
                subprocess.call(["adb", "logcat"])
            else:
                logcat(
                    pkg=pkg,
                    show_fatal_error=bool(os.environ.get("LOGCAT_SHOW_FATAL_ERROR")),
                )
