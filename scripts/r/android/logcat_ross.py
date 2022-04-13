from _android import logcat
from _shutil import call2
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pkg",
        default=None,
        type=str,
    )

    args = parser.parse_args()

    call2("adb wait-for-device")
    logcat(
        regex=r"{{_REGEX}}" if r"{{_REGEX}}" else r"ROSS:| F libc |Abort message:",
    )
