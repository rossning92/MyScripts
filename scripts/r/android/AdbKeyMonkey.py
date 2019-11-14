from _shutil import *
from _android import *

make_and_change_dir('C:\\tools')
download('https://github.com/ckesc/AdbKeyMonkey/releases/download/v1.0.4/AdbKeyMonkey-1.0.4.jar')

setup_android_env()

subprocess.Popen('AdbKeyMonkey-1.0.4.jar', close_fds=True, shell=True)
