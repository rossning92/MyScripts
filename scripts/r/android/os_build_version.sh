adb shell getprop | grep fingerprint
adb shell "echo Android version: `adb shell getprop ro.build.version.release`"