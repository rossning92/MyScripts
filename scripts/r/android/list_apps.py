import os
import subprocess
import sys

from _android import backup_pkg
from _script import run_script, set_variable
from _shutil import call_echo, shell_open
from _term import select_option

SCRIPT_NAME = os.path.splitext(os.path.basename(__file__))[0]


def select_app_pkg():
    s = subprocess.check_output(
        ["adb", "shell", "pm list packages"], universal_newlines=True
    )
    s = s.replace("package:", "")
    lines = s.splitlines()
    lines = sorted(lines)
    i = select_option(lines, history_file_name=SCRIPT_NAME)
    if i == -1:
        return None
    else:
        return lines[i]


if __name__ == "__main__":
    pkg = select_app_pkg()
    if not pkg:
        sys.exit(0)

    opt = [
        "set PKG_NAME=%s" % pkg,
        "restart app",
        "uninstall app",
        "backup app",
        "dumpsys package",
        "dumpsys package: permissions",
    ]
    i = select_option(opt)
    if i == -1:
        sys.exit(0)

    if i == 0:
        set_variable("PKG_NAME", pkg)

    elif i == 1:
        set_variable("PKG_NAME", pkg)
        run_script("r/android/restart_app_logcat.py", new_window=True)

    elif i == 3:
        out_dir = os.environ.get("ANDROID_APP_BACKUP_DIR")
        if not out_dir:
            out_dir = os.path.expanduser("~/android_backup")
        os.makedirs(out_dir, exist_ok=True)
        backup_pkg(pkg, out_dir=out_dir)
        shell_open(out_dir)

    elif i == 2:
        call_echo(["adb", "uninstall", pkg])

    elif i == 4:
        call_echo(["adb", "shell", "dumpsys", "package", pkg])
        input("Press enter to continue...")

    elif i == 5:
        call_echo(["adb", "shell", f"dumpsys package {pkg} | grep permission"])
        input("Press enter to continue...")
