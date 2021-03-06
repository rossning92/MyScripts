from _shutil import *
import datetime
from _editor import *


def wait_until_file_modified(f):
    last_mtime = os.path.getmtime(f)
    while True:
        time.sleep(0.2)
        mtime = os.path.getmtime(f)
        if mtime > last_mtime:
            return


files = get_files(cd=True, ignore_dirs=False)
files = sorted(files)

# sub_files = []
# for f in files:
#     if os.path.isdir(f):
#         sub_files.extend(glob.glob(os.path.join(f, "*")))

# print(sub_files)
# files = sub_files


tmp_file = write_temp_file("\n".join(files), ".txt")
open_in_vscode(tmp_file)

wait_until_file_modified(tmp_file)

with open(tmp_file, "r", encoding="utf-8") as f:
    new_files = f.readlines()
    new_files = [x.strip() for x in new_files]

for old, new in zip(files, new_files):
    if old != new:
        print("%s => %s" % (old, new))
        os.rename(old, new)
