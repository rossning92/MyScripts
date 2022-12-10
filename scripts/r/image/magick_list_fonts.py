from _pkgmanager import find_executable, require_package
from _shutil import call_echo

require_package("magick")
magick = find_executable("magick")
call_echo([magick, "-list", "font"])
