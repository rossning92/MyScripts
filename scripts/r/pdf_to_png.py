import argparse
import os

from _shutil import call_echo, find_newest_file, mkdir

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_file")
    args = parser.parse_args()

    pdf_file = args.pdf_file
    assert pdf_file.endswith(".pdf")

    out_dir = os.path.splitext(pdf_file)[0]
    mkdir(out_dir)

    gswin64 = find_newest_file(r"C:\Program Files\gs\*\bin\gswin64c.exe")
    out_file = os.path.join(out_dir, "%03d.png")
    call_echo(
        [
            gswin64,
            "-dBATCH",
            "-dNOPAUSE",
            "-sDEVICE=png16m",
            "-r600",
            "-dDownScaleFactor=3",
            "-dUseCropBox",
            "-sOutputFile=%s" % out_file,
            pdf_file,
        ]
    )
