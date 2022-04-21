cd ~/Desktop/

echo 'Clear logcat buffer...'
adb logcat -c

echo press ctrl-c to stop
filename="logcat_$(date +%Y%m%d_%H%M%S).log"
adb logcat | tee $filename
