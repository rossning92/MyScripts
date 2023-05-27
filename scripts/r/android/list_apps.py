import os
import subprocess
import sys

from _android import backup_pkg
from _script import set_variable, start_script
from _shutil import call_echo, set_clip, shell_open
from _term import Menu, select_option

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


menu = Menu(close_on_selection=True)


@menu.item()
def restart_app():
    set_variable("PKG_NAME", pkg)
    start_script("r/android/restart_app_logcat.py", restart_instance=True)


@menu.item()
def set_variable_package_name():
    set_variable("PKG_NAME", pkg)


@menu.item()
def copy_package_name_to_clipboard():
    set_clip(pkg)


@menu.item()
def backup_app():
    out_dir = os.environ.get("ANDROID_APP_BACKUP_DIR")
    if not out_dir:
        out_dir = os.path.expanduser("~/android_backup")
    os.makedirs(out_dir, exist_ok=True)
    backup_pkg(pkg, out_dir=out_dir)
    shell_open(out_dir)


@menu.item()
def uninstall_app():
    call_echo(["adb", "uninstall", pkg])


@menu.item()
def dumpsys_package():
    call_echo(["adb", "shell", "dumpsys", "package", pkg])
    input("(press enter to continue)")


@menu.item()
def dumpsys_package_permission():
    call_echo(["adb", "shell", f"dumpsys package {pkg} | grep permission"])
    input("(press enter to continue)")


if __name__ == "__main__":
    pkg = select_app_pkg()
    if not pkg:
        sys.exit(0)

    menu.exec()
