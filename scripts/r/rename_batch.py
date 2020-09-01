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


os.chdir(os.environ["_CUR_DIR"])

files = glob.glob("**/*", recursive=True)
files = [x for x in files if os.path.isfile(x)]

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
