adb root
adb remount
adb shell "sed -i 's/ro.logd.size=.*/ro.logd.size=16M/g' /system/build.prop"
adb shell "sed -i 's/ro.logd.size.main=.*/ro.logd.size.main=16M/g' /system/build.prop"
adb shell "sed -i 's/ro.logd.size.radio=.*/ro.logd.size.radio=16M/g' /system/build.prop"
adb shell "sed -i 's/ro.logd.size.kernel=.*/ro.logd.size.kernel=16M/g' /system/build.prop"
