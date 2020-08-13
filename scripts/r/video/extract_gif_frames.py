from _shutil import *
from _appmanager import *

f = get_files(cd=True)[0]
mkdir("out")
call_echo([get_executable("magick"), f, "-coalesce", "out/%05d.png"])
