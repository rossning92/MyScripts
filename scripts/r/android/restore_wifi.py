from _android import *

cd('~/Desktop/android_backup')

call2('adb push wifi.tar /data/local/tmp/wifi.tar')
adb_shell2(f"tar -xvf /data/local/tmp/wifi.tar", root=True)
