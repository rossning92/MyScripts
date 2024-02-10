import os
import subprocess
import sys

from _android import backup_pkg, get_apk_path
from _script import set_variable, start_script
from _shutil import call_echo, shell_open
from utils.clip import set_clip
from utils.menu import Menu
from utils.menu.actionmenu import ActionMenu
from utils.menu.select import select_option

SCRIPT_NAME = os.path.splitext(os.path.basename(__file__))[0]


def select_app_pkg():
    s = subprocess.check_output(
        ["adb", "shell", "pm list packages"], universal_newlines=True
    )
    s = s.replace("package:", "")
    lines = s.splitlines()
    lines = sorted(lines)
    i = select_option(lines, history=SCRIPT_NAME)
    if i == -1:
        return None
    else:
        return lines[i]


menu = ActionMenu(close_on_selection=True)


@menu.func()
def restart_app():
    start_script("r/android/restart_app.py", restart_instance=True)


@menu.func()
def restart_app_with_logcat():
    start_script("r/android/restart_app_logcat.py", restart_instance=True)


@menu.func()
def set_variable_package_name():
    set_variable("PKG_NAME", pkg)


@menu.func()
def copy_package_name_to_clipboard():
    set_clip(pkg)


@menu.func()
def backup_app():
    out_dir = os.environ.get("ANDROID_APP_BACKUP_DIR")
    if not out_dir:
        out_dir = os.path.expanduser("~/android_backup")
    os.makedirs(out_dir, exist_ok=True)
    backup_pkg(pkg, out_dir=out_dir)
    shell_open(out_dir)


@menu.func()
def _get_apk_path():
    print(get_apk_path(pkg))
    input("(press enter key to exit...)")


@menu.func()
def uninstall_app():
    call_echo(["adb", "uninstall", pkg])


@menu.func()
def dumpsys_package():
    lines = subprocess.check_output(
        ["adb", "shell", f"dumpsys package {pkg}"], universal_newlines=True
    ).splitlines()
    Menu(items=lines).exec()


@menu.func()
def dumpsys_package_permission():
    lines = subprocess.check_output(
        ["adb", "shell", f"dumpsys package {pkg} | grep permission"],
        universal_newlines=True,
    ).splitlines()
    Menu(items=lines).exec()


@menu.func()
def get_app_version():
    call_echo(["run_script", "r/android/get_app_version.sh"])
    input("(press enter to continue)")


if __name__ == "__main__":
    pkg = select_app_pkg()
    if not pkg:
        sys.exit(0)
    else:
        set_variable("PKG_NAME", pkg)

    menu.exec()
