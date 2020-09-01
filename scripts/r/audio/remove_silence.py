from _shutil import *

chdir(os.environ['_CUR_DIR'])

call2('sox concat.wav out.wav silence -l 1 0.1 2% -1 0.8 2%')
