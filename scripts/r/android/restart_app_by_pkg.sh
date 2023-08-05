adb shell am force-stop {{PKG_NAME}}
adb shell am start -n {{ shell(["adb", "shell", f"dumpsys package | grep -i {PKG_NAME} | grep Activity"]).split()[1] }}
