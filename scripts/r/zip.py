import argparse
import os
from typing import List, Optional
from zipfile import ZipFile


def create_zip_file(files: List[str], out_file: Optional[str]):
    common_path = os.path.commonpath(files)
    if out_file is None:
        out_file = os.path.basename(common_path.rstrip(os.path.sep)) + ".zip"
    with ZipFile(out_file, "w") as zipf:
        for file in files:
            arcname = os.path.relpath(file, common_path)
            zipf.write(file, arcname=arcname)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("files", type=str, nargs="+")
    parser.add_argument("-o", "--out", type=str, nargs="?")
    args = parser.parse_args()

    create_zip_file(files=args.files, out_file=args.out)
