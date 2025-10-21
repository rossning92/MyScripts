import argparse
import subprocess

from _pkgmanager import find_executable

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("app", type=str)
    parser.add_argument("args", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    executable = find_executable(args.app, install=True)
    if not executable:
        raise Exception(f"Cannot find executable for app {args.app}")

    subprocess.check_call([executable, *args.args])
