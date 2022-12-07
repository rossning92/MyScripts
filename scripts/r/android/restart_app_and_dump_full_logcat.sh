adb shell logcat -b all -c
run_script r/android/restart_app.py ${PKG_NAME} &
adb logcat
