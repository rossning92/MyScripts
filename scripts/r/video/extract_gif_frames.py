from _pkgmanager import get_executable
from _shutil import call_echo, get_files, mkdir

if __name__ == "__main__":
    f = get_files(cd=True)[0]
    mkdir("out")
    call_echo([get_executable("magick"), f, "-coalesce", "out/%05d.png"])
