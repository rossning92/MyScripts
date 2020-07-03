from _appmanager import *
from _shutil import *

magick = get_executable("magick")
call_echo([magick, "-list", "font"])
input()
