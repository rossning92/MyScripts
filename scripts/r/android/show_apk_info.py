from _android import setup_android_env
from _shutil import *

# aapt dump badging xxx.apk

f = get_files()[0]
print(f)

setup_android_env()
call_echo(["aapt", "dump", "badging", f])

call_echo(["apksigner", "verify", "--print-certs", f])
