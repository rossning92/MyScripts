cd ~/Desktop/

echo 'Clear logcat buffer.'
adb shell logcat -b all -c

adb logcat
