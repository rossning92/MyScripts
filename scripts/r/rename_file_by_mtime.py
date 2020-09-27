from _shutil import *
import datetime
from _term import *

os.chdir(os.environ["_CUR_DIR"])

new_file_names = {}
files = list(glob.glob("*"))
files = sorted(files, key=lambda x: os.path.getmtime(x))

i = 1
for f in files:
    time_str = time.strftime("%y%m%d%H%M%S", time.gmtime(os.path.getmtime(f)))
    time_str = "%04d" % i
    i += 1

    assert time_str not in new_file_names

    ext = os.path.splitext(f)[1]

    new_file_names[f] = time_str + ext

for k, v in new_file_names.items():
    print("%s => %s" % (k, v))

print("Press Y to continue")
if getch() == "y":
    for k, v in new_file_names.items():
        os.rename(k, v)
