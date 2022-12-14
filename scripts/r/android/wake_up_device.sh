# run_script r/android/keep_awake.sh

adb shell input keyevent 224 # KEYCODE_WAKEUP
for i in {1..3}; do
    adb shell dumpsys power | grep 'mWakefulness='
    sleep 1
done
