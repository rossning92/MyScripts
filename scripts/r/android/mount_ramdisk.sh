set -e
adb root
adb shell mount -o size=16M -t tmpfs tmpfs /data/local/tmp
