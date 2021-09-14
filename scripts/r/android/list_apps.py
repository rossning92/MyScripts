import os
import subprocess
import sys

from _android import backup_pkg
from _script import run_script, set_variable
from _term import Menu, call_echo, mkdir

if __name__ == "__main__":

    s = subprocess.check_output("adb shell pm list packages").decode()
    s = s.replace("package:", "")
    lines = s.splitlines()
    lines = sorted(lines)
    i = Menu(items=lines).exec()
    if i == -1:
        sys.exit(1)

    pkg = lines[i]
    print("Selected: " + pkg)

    opt = [
        "start",
        "uninstall",
        "backup",
    ]

    i = Menu(items=opt).exec()
    if i == -1:
        sys.exit(1)

    set_variable("PKG_NAME", pkg)

    if opt[i] == "start":
        set_variable("PKG_NAME", pkg)
        run_script("restart_app", variables={"PKG_NAME": pkg}, new_window=True)

    elif opt[i] == "backup":
        out_dir = os.path.expanduser("~/Desktop/android_backup")
        mkdir(out_dir)
        backup_pkg(pkg, out_dir=out_dir)

    elif opt[i] == "uninstall":
        call_echo(["adb", "uninstall", pkg])
