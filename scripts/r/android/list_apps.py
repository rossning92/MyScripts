import os
import sys

from _android import backup_pkg, select_app_pkg
from _script import run_script, set_variable
from _shutil import call_echo, shell_open
from _term import select_option

if __name__ == "__main__":
    pkg = select_app_pkg()
    if not pkg:
        sys.exit(1)

    opt = [
        "start",
        "uninstall",
        "backup",
        "dumpsys",
        "permissions",
    ]
    i = select_option(opt)
    if i == -1:
        sys.exit(1)

    set_variable("PKG_NAME", pkg)

    if opt[i] == "start":
        set_variable("PKG_NAME", pkg)
        run_script("restart_app", variables={"PKG_NAME": pkg}, new_window=True)

    elif opt[i] == "backup":
        out_dir = os.path.abspath("/tmp/android_backup")
        os.makedirs(out_dir, exist_ok=True)
        backup_pkg(pkg, out_dir=out_dir)
        shell_open(out_dir)

    elif opt[i] == "uninstall":
        call_echo(["adb", "uninstall", pkg])

    elif opt[i] == "dumpsys":
        call_echo(["adb", "shell", "dumpsys", "package", pkg])
        input("Press enter to continue...")

    elif opt[i] == "permissions":
        call_echo(["adb", "shell", "dumpsys package %s | grep permission" % pkg])
        input("Press enter to continue...")

    elif opt[i] == "activities":
        call_echo(["adb", "shell", f"dumpsys package {pkg} | grep Activities" % pkg])
        input("Press enter to continue...")