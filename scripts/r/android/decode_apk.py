from _setup_android_env import *
from _shutil import *

f = get_files(cd=True)[0]
setup_android_env()
call(['apktool', 'decode', f])
