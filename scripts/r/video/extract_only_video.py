import os
import subprocess
import sys
import locale
from _shutil import *

f = get_files(cd=True)[0]
name, ext = os.path.splitext(f)
call2('ffmpeg -i "%s" -c copy -an "%s_out%s"' % (f, name, ext))
