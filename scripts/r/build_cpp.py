import argparse

from _shutil import call_echo, prepend_to_path
import glob
import os

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file",
        help="Input file",
        type=str,
    )

    args = parser.parse_args()

    bin_dir = glob.glob(
        r"C:\Program Files (x86)\Microsoft Visual Studio\*\*\VC\Auxiliary\Build"
    )

    prepend_to_path(bin_dir[0])

    file = os.path.basename(args.file)
    dir_path = os.path.dirname(args.file)
    out = os.path.splitext(file)[0] + ".exe"

    os.chdir(dir_path)

    call_echo(
        [
            "call",
            "vcvarsall.bat",
            "x86",
            "&",
            "cl.exe",
            "/EHsc",
            file,
        ],
    )

    call_echo([out])
    input("press any key")
