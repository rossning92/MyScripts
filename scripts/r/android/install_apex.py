import argparse
from subprocess import check_call

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("apex", type=str)
    args = parser.parse_args()

    # check_call(["run_script", "quest/adb_remount.sh"])
    check_call(["adb", "install", "-d", "-g", args.apex])
