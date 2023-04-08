set -e
read -p "enter tid: " tid
proc=$(adb shell "readlink -f /proc/*/task/$tid/../..")
adb shell "cat $proc/cmdline"
