import logging
import os
import subprocess

from _android import clear_logcat, logcat, restart_app
from _shutil import call_echo, setup_logger

if __name__ == "__main__":
    setup_logger(level=logging.DEBUG)

    if os.environ.get("WAKE_UP_DEVICE"):
        call_echo(["run_script", "r/android/wake_up_device.sh"])

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
