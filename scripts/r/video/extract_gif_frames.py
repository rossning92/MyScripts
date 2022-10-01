from _pkgmanager import require_package
from _shutil import call_echo, get_files, mkdir

if __name__ == "__main__":
    f = get_files(cd=True)[0]
    mkdir("out")
    call_echo([require_package("magick"), f, "-coalesce", "out/%05d.png"])
