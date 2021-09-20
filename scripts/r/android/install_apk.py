import argparse
import os

from _android import adb_install2, get_pkg_name_apk, logcat, start_app
from _shutil import get_files, print2

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", nargs="?", default=None)
    parser.add_argument("-r", "--run", default=bool, action="store_true")

    args = parser.parse_args()

    if args.file:
        adb_install2(args.file)

        if args.run:
            pkg = get_pkg_name_apk(args.file)
            try:
                start_app(pkg)
            except:
                print2("ERROR: start app failed.", color="red")
            logcat(pkg)

    else:
        files = get_files()
        for file in files:
            assert os.path.splitext(file)[1].lower() == ".apk"

            adb_install2(file)

            if len(files) == 1:
                # Run app
                pkg = get_pkg_name_apk(file)
                try:
                    start_app(pkg)
                except:
                    print2("ERROR: start app failed.", color="red")
                logcat(pkg)
