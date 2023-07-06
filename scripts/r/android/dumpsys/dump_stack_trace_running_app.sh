set -e
# read -p "enter pid: " pid
pid="$(adb shell pidof {{APP_PROC_NAME}})"
adb shell debuggerd -b $pid
