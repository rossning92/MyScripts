from _shutil import *

chdir(os.environ['CUR_DIR_'])

call2('sox concat.wav out.wav silence -l 1 0.1 2% -1 0.8 2%')
