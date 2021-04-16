from _appmanager import *
from _shutil import *
from _term import *

magick = get_executable("magick")
lines = list(proc_lines([magick, "-list", "font"]))
print(lines)

search(lines)
