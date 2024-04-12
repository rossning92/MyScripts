import os
import sys

from _script import run_script, start_script
from _shutil import get_files


def create_link(script):
    d = os.path.realpath(os.path.dirname(__file__) + "/../link")
    os.makedirs(d, exist_ok=True)

    if sys.platform == "win32":
        file = os.path.join(d, os.path.splitext(os.path.basename(script))[0] + ".cmd")
        with open(file, "w", encoding="utf-8") as f:
            f.write(
                "\n".join(["@echo off", 'run_script @cd=1:template=0 "%s"' % script])
            )
    else:
        raise Exception("Unsupported platform: %s" % sys.platform)

    print("Link created: %s" % file)
    return file


if __name__ == "__main__":
    files = get_files()
    if len(files) > 0:
        script = files[0]
        file = create_link(script)
        start_script(file=file, restart_instance=True)

    else:
        # Run last script
        start_script(restart_instance=True)
