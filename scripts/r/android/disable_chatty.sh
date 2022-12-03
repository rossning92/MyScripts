set -e
adb root
adb shell setprop ro.logd.filter disable
adb shell setprop persist.logd.filter disable
