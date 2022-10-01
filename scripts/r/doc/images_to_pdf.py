from _pkgmanager import require_package
from _shutil import call_echo, get_files, setup_nodejs

if __name__ == "__main__":
    setup_nodejs()

    magick = require_package("magick")

    files = get_files(cd=True)

    call_echo([magick] + files + ["out.pdf"])
