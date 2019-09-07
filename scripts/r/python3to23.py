from _shutil import *

f = get_files(cd=True)[0]

call2(['3to2', '-w', f])
call2(['python-modernize', '-w', f])
