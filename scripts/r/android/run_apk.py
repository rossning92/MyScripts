import argparse
import re
import subprocess

from _android import adb_install, app_is_installed, restart_app, setup_android_env

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file")
    args = parser.parse_args()
    apk = args.file

    setup_android_env()
    out = subprocess.check_output(
        ["aapt", "dump", "badging", apk], universal_newlines=True
    )
    match = re.search(r"package: name='(.+?)'", out)
    if match:
        pkg_name = match.group(1)
        print(pkg_name)

    if not app_is_installed(pkg_name):
        adb_install(apk)

    restart_app(pkg_name)
