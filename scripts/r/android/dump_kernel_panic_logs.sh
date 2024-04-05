# https://www.internalfb.com/intern/wiki/VROS/Fastboot_Feature_Matrix/

adb root

adb shell ls -lah /sys/fs/pstore
adb shell cat /sys/fs/pstore/console-ramoops*
adb shell cat /proc/last_kmsg

adb pull /sys/fs/pstore
