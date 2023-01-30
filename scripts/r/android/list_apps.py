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
    i = select_option(lines, save_history=SCRIPT_NAME)
    if i == -1:
        return None
    else:
        return lines[i]


if __name__ == "__main__":
    pkg = select_app_pkg()
    if not pkg:
        sys.exit(0)

    opt = [
        "start",
        "uninstall",
        "backup",
        "dumpsys",
        "permissions",
    ]
    i = select_option(opt)
    if i == -1:
        sys.exit(0)

    if opt[i] == "start":
        set_variable("PKG_NAME", pkg)
        os.environ["PKG_NAME"] = pkg
        run_script("r/android/restart_app.py", new_window=True)

    elif opt[i] == "backup":
        out_dir = os.environ.get(
            "ANDROID_APP_BACKUP_DIR", os.path.expanduser("~/android_backup")
        )
        os.makedirs(out_dir, exist_ok=True)
        backup_pkg(pkg, out_dir=out_dir)
        shell_open(out_dir)

    elif opt[i] == "uninstall":
        call_echo(["adb", "uninstall", pkg])

    elif opt[i] == "dumpsys":
        call_echo(["adb", "shell", "dumpsys", "package", pkg])
        input("Press enter to continue...")

    elif opt[i] == "permissions":
        call_echo(["adb", "shell", f"dumpsys package {pkg} | grep permission"])
        input("Press enter to continue...")

    elif opt[i] == "activities":
        call_echo(["adb", "shell", f"dumpsys package {pkg} | grep Activities"])
        input("Press enter to continue...")
