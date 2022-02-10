cd ~/Desktop/
filename="logcat_$(date +%Y%m%d_%H%M%S).log"

echo press ctrl-c to stop
adb logcat >$filename
