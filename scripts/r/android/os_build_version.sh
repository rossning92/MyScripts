adb shell getprop | grep fingerprint
adb shell "echo OS Version: `adb shell getprop ro.build.version.release`"