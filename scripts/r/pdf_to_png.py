from _shutil import *
from _appmanager import *

get_executable('magick')
get_executable('ghostscript')



f = get_files()[0]
assert f.endswith('.pdf')

out_dir = os.path.splitext(f)[0]
mkdir(out_dir)

call2(['magick', '-density', '300', f, os.path.join(out_dir, '%03d.png')])
