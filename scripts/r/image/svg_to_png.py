from _shutil import *
from _appmanager import *

magick = get_executable('magick')

f = get_files(cd=True)[0]
name, ext = os.path.splitext(f)

call2([magick, '-density', '1200', '-background', 'None', f, name + '.png'])
