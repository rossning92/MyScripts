pkg=com.oculus.sdk.vrcubeworldna
out=$(adb shell dumpsys package | grep -i $pkg | grep Activity)
pkg_activity=$(echo "$out" | awk '{print $2}')
