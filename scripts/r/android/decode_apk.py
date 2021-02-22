from _android import setup_android_env
from _shutil import *

f = get_files(cd=True)[0]
setup_android_env()
call_echo(["apktool", "decode", f])
