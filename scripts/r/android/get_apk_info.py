import sys

from _shutil import call_echo, get_files
from utils.android import setup_android_env

# aapt dump badging xxx.apk


if __name__ == "__main__":
    f = get_files()[0]
    print(f)

    setup_android_env()
    call_echo(["aapt", "dump", "badging", f])
    call_echo(
        ["apksigner", "verify", "--print-certs", f], shell=sys.platform == "win32"
    )

    input("Press enter to exit...")
