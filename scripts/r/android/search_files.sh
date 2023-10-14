set -e
adb root
adb shell "find / -name '*$1*' 2>/dev/null"
