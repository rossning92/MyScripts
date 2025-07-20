# Check if device is locked
out=$(adb shell "dumpsys window | grep mDreamingLockscreen")
if [[ "$out" == *"mDreamingLockscreen=true"* ]]; then
    echo "Device is locked, unlocking..."
    adb shell input keyevent 224 # KEYCODE_WAKEUP
    sleep 2

    # Swipe up
    adb shell input touchscreen swipe 540 1000 540 200
    sleep 0.5

    echo "Entering pin..."
    adb shell input text ${ANDROID_PIN}
    sleep 0.5
    adb shell input keyevent 66 # KEYCODE_ENTER
fi
