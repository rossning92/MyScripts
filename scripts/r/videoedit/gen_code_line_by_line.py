from _shutil import get_files
import os

f = get_files()[0]
name_no_ext, ext = os.path.splitext(f)
out_dir = name_no_ext
os.makedirs(out_dir, exist_ok=True)

with open(f, "r", encoding="utf-8") as f:
    lines = f.read().splitlines()


for i in range(0, len(lines)):
    s = "\n".join(lines[0:i+1])

    out_file = out_dir + "/%03d%s" % (i+1, ext)
    with open(out_file, "w") as f:
        f.write(s)
