set -e
pid=$(adb shell pidof {{PROC_NAME}})
echo "logcat for {{PROC_NAME}}, pid=${pid}"
adb logcat | grep " $pid "
