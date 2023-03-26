import argparse

from _script import add_script_dir
from _shutil import get_current_folder

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prefix", type=str, nargs="?", default=None)
    parser.add_argument("script_dir", type=str, nargs="?", default=None)

    args = parser.parse_args()
    if args.prefix and args.script_dir:
        script_dir = args.script_dir
        prefix = args.prefix
    else:
        script_dir = get_current_folder()
        prefix = input("prefix: ")

    print("Add script directory: %s: %s" % (prefix, script_dir))
    add_script_dir(script_dir, prefix=prefix)
