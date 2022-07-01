import os

from _shutil import get_files

from .ipython import record_ipython

if __name__ == "__main__":
    file = get_files()[0]
    out_file = os.path.splitext(file)[0] + ".mp4"

    with open(file, encoding="utf-8") as f:
        cmd = f.read()

    record_ipython(out_file, cmd=cmd, startup="import torch")
