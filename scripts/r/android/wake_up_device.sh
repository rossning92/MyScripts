# run_script r/android/keep_awake.sh

adb shell input keyevent 224 # KEYCODE_WAKEUP

while true; do
    adb shell dumpsys power | grep 'mWakefulness='
    sleep 2
done
