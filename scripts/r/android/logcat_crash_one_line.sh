while true; do
    adb wait-for-device
    echo 'start logcat ---'
    adb logcat --buffer=crash | grep -E '<<<|Abort message: '
done
