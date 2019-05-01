from _setup_android_env import *
from _shutil import *

f= get_files()[0]
print(f)

setup_android_env()
call(['aapt', 'dump', 'badging', f])
