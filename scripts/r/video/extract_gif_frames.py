from _pkgmanager import find_executable, require_package
from _shutil import call_echo, get_files, mkdir

if __name__ == "__main__":
    f = get_files(cd=True)[0]
    mkdir("out")
    require_package("magick")
    magick = find_executable("magick")
    call_echo([magick, f, "-coalesce", "out/%05d.png"])
