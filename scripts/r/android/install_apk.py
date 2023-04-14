import argparse
import logging
import os

from _android import adb_install2, get_pkg_name_apk, setup_android_env
from _shutil import call_echo, get_files, setup_logger
from _term import set_terminal_title

if __name__ == "__main__":
    setup_logger(level=logging.INFO)
    setup_android_env()
    set_terminal_title("r/android/install_apk")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", metavar="N", type=str, nargs="+")
    parser.add_argument("-r", "--run", default=False, action="store_true")
    parser.add_argument("-f", "--force_reinstall", default=False, action="store_true")
    parser.add_argument("-p", "--grant_permissions", default=False, action="store_true")

    args = parser.parse_args()

    pkg = None
    if args.files:
        for file in args.files:
            adb_install2(
                file,
                force_reinstall=args.force_reinstall,
                grant_permissions=args.grant_permissions,
            )

            if len(args.files) == 1 and args.run:
                pkg = get_pkg_name_apk(file)

    else:
        files = get_files()
        for file in files:
            assert os.path.splitext(file)[1].lower() == ".apk"

            adb_install2(
                file,
                force_reinstall=args.force_reinstall,
                grant_permissions=args.grant_permissions,
            )

            if len(files) == 1:
                pkg = get_pkg_name_apk(file)

    if pkg is not None:
        # Run app
        call_echo(
            "run_script r/android/restart_app.py",
            env={**os.environ, "PKG_NAME": pkg},
        )

        # try:
        #     start_app(pkg)
        # except:
        #     print2("ERROR: start app failed.", color="red")
        # logcat(pkg)
