from _shutil import *

from postprocess import loudnorm

files = get_files(cd=True)

for file in files:
    if not os.path.isfile(file):
        continue

    print(file)
    os.makedirs("out", exist_ok=True)
    out_file = "out/%s" % file

    loudnorm(file, out_file)
