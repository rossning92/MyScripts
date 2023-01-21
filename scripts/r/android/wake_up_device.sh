# run_script r/android/keep_awake.sh

out=$(adb shell dumpsys power | grep 'mWakefulness=')
echo "${out}"
if [[ "$out" == *"Asleep"* ]]; then
    adb shell input keyevent 26 # power key
    # adb shell input keyevent 224 # KEYCODE_WAKEUP
fi
