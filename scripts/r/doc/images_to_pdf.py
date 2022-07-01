from _pkgmanager import get_executable
from _shutil import call_echo, get_files, setup_nodejs

if __name__ == "__main__":
    setup_nodejs()

    magick = get_executable("magick")

    files = get_files(cd=True)

    call_echo([magick] + files + ["out.pdf"])
