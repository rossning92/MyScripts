adb shell "getprop | grep 'ro.build'"
adb shell "echo Android version: `adb shell getprop ro.build.version.release`"
