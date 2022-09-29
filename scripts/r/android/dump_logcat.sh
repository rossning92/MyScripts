cd ~/Desktop/

echo 'Clear logcat buffer...'
adb logcat -c

echo press ctrl-c to stop
if [ -n "${LOG_FILE}" ]; then
    filename="${LOG_FILE}"
else
    filename="logcat_$(date +%Y%m%d_%H%M%S).log"
fi
adb logcat | tee $filename
