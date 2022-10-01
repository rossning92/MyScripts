from _pkgmanager import require_package
from _shutil import call_echo

magick = require_package("magick")
call_echo([magick, "-list", "font"])
