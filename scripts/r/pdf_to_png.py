from _shutil import *
from _appmanager import *

get_executable("ghostscript")


pdf_file = get_files()[0]
assert pdf_file.endswith(".pdf")

out_dir = os.path.splitext(pdf_file)[0]
mkdir(out_dir)

gswin64 = find_file(r"C:\Program Files\gs\*\bin\gswin64c.exe")
out_file = os.path.join(out_dir, "%03d.png")
call_echo(
    [
        gswin64,
        "-dBATCH",
        "-dNOPAUSE",
        "-sDEVICE=pnggray",
        "-r300",
        "-dUseCropBox",
        "-sOutputFile=%s" % out_file,
        pdf_file,
    ]
)
