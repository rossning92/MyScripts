set -e
read -p "enter pid: " pid
adb shell debuggerd -b $pid
