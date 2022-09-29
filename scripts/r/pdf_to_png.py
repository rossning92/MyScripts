from _shutil import get_files, mkdir, call_echo, find_newest_file

import os

if __name__ == "__main__":
    pdf_file = get_files()[0]
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
