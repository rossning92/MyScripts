import argparse
import os

from _android import logcat

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pkg", type=str)
    args = parser.parse_args()
    logcat(
        pkg=args.pkg,
        show_fatal_error=bool(os.environ.get("LOGCAT_SHOW_FATAL_ERROR")),
    )
