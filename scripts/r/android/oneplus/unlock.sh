out=$(adb shell dumpsys power | grep "mWakefulness=")
echo $out
if [[ $out == *"Dozing"* ]]; then
    adb shell input keyevent 82
    sleep 1
    
	# Swipe up
	adb shell input touchscreen swipe 540 1000 540 400
	sleep 1
	
    adb shell input text 123475
    adb shell input keyevent KEYCODE_ENTER
fi
