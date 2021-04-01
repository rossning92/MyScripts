# adb shell input keyevent 82
adb shell input keyevent 224
sleep 2

# Swipe up
adb shell input touchscreen swipe 540 1000 540 200
sleep 2

adb shell input text {{ANDROID_PIN}}
adb shell input keyevent KEYCODE_ENTER
