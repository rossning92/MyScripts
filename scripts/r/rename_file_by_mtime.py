import os
import time

from _shutil import confirm, get_files

if __name__ == "__main__":
    new_file_names = {}
    files = get_files()
    files = sorted(files, key=lambda x: os.path.getmtime(x))

    for f in files:
        time_str = time.strftime("%y%m%d%H%M%S", time.gmtime(os.path.getmtime(f)))
        assert time_str not in new_file_names
        ext = os.path.splitext(f)[1]

        new_file_names[f] = time_str + ext

    for k, v in new_file_names.items():
        print("%s => %s" % (k, v))

    if confirm("rename"):
        for k, v in new_file_names.items():
            os.rename(k, v)
