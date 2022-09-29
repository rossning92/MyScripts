from _pkgmanager import get_executable
from _shutil import call_echo

magick = get_executable("magick")
call_echo([magick, "-list", "font"])
