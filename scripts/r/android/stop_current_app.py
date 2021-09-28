from _android import get_active_pkg_and_activity, adb_shell

if __name__ == "__main__":
    pkg, activity = get_active_pkg_and_activity()
    adb_shell("am force-stop {}".format(pkg))
