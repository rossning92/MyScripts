from utils.android import *

cd("~/Desktop/android_backup")

adb_shell2(
    f"tar -cf /data/local/tmp/wifi.tar /data/misc/wifi/WifiConfigStore.xml", root=True
)
call2("adb pull /data/local/tmp/wifi.tar")
