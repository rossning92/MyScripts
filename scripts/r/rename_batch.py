import os
import time

from _editor import open_in_editor
from _shutil import get_files, write_temp_file


def wait_until_file_modified(f):
    last_mtime = os.path.getmtime(f)
    while True:
        time.sleep(0.2)
        mtime = os.path.getmtime(f)
        if mtime > last_mtime:
            return


if __name__ == "__main__":
    files = get_files(cd=True, ignore_dirs=False)
    files = sorted(files)

    tmp_file = write_temp_file("\n".join(files), ".txt")
    open_in_editor(tmp_file)

    wait_until_file_modified(tmp_file)

    with open(tmp_file, "r", encoding="utf-8") as f:
        new_files = f.readlines()
        new_files = [x.strip() for x in new_files]

    for old, new in zip(files, new_files):
        if old != new:
            print("%s => %s" % (old, new))
            os.rename(old, new)
