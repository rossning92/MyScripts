# https://www.internalfb.com/intern/wiki/VROS/Fastboot_Feature_Matrix/

adb root

adb shell getprop ro.boot.bootreason
adb shell ls -lah /sys/fs/pstore
adb pull /sys/fs/pstore

run_script ext/open.py .
# adb shell cat /sys/fs/pstore/console-ramoops*
# adb shell cat /proc/last_kmsg
