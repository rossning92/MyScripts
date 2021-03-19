adb root
adb shell "grep --no-filename -B 3 -E --color=always 'Abort message' /data/tombstones/*"
