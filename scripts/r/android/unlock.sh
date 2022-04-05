# Check if device is locked
out=$(adb shell dumpsys nfc | grep 'mScreenState=')
if [[ "$out" == *"_LOCKED"* ]]; then
    echo "Device is locked, unlocking..."
    adb shell input keyevent 224
    sleep 2

    # Swipe up
    adb shell input touchscreen swipe 540 1000 540 200
    sleep 2

    adb shell input text {{ANDROID_PIN}}
    adb shell input keyevent KEYCODE_ENTER
else
    echo "Device is not locked."
fi
