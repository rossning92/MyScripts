result=$(adb shell dumpsys power | grep "mWakefulness=")
echo $result
if [[ $result == *"Awake"* ]]; then
    echo "Screen is already on."
else
    echo "Turning screen on."
    adb shell input keyevent 26
fi
