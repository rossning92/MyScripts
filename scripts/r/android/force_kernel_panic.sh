set -e
adb root
adb shell "echo c >/proc/sysrq-trigger"
