from utils.android import adb_shell, get_active_pkg_and_activity

if __name__ == "__main__":
    pkg, activity = get_active_pkg_and_activity()
    adb_shell("am force-stop {}".format(pkg))
