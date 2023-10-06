adb logcat -c
adb logcat | grep TreeDebug | sed 's/.*TreeDebug: //'
