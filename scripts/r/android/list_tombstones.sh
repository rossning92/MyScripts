adb root
adb shell "grep -E --color=always '>>>|Abort message' /data/tombstones/*"
