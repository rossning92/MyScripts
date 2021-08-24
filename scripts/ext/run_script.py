import os
import sys

from _script import get_files, run_script


def create_link(script):
    d = os.path.realpath(os.path.dirname(__file__) + "/../link")
    os.makedirs(d, exist_ok=True)

    if sys.platform == "win32":
        file = os.path.join(d, os.path.splitext(os.path.basename(script))[0] + ".cmd")
        with open(file, "w", encoding="utf-8") as f:
            f.write("\n".join(["@echo off", 'run_script @cd=1 "%s"' % script]))
    else:
        raise Exception("Unsupported platform: %s" % sys.platform)

    print("Link created: %s" % file)
    return file


if __name__ == "__main__":
    script = get_files()[0]
    file = create_link(script)
    run_script(file, new_window=True)
