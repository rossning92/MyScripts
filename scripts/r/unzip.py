from _appmanager import *
from _shutil import *

file = get_files(cd=True)[0]

if file.endswith(".tar.gz") or file.endswith(".tgz"):
    out_dir = file.rstrip(".tar.gz")
    mkdir(out_dir)
    call2('tar xzvf "%s" -C "%s"' % (file, out_dir))

else:
    _7z = get_executable("7z")

    out_dir = os.path.splitext(file)[0]
    args = [
        _7z,
        "x",  # Extract
        "-aoa",  # Overwrite all existing files
        "-o" + out_dir,  # Out folder
        file,
    ]
    call2(args)

shell_open(out_dir)
