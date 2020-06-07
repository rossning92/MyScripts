run_script /r/android/unlock.sh

# Set display timeout to 1 minute.
adb shell settings put system screen_off_timeout 60000

# Kill the camera app.
adb shell am force-stop com.sec.android.app.camera

# When phone is in portrait mode, default to back camera.
adb shell am start -a android.media.action.VIDEO_CAPTURE
echo 'Wait for 2s.'
sleep 2

# Press volume key to start recording.
adb shell input keyevent KEYCODE_VOLUME_DOWN
echo -e '\033[0;36mRecording started.\033[0m'

echo 'Manual focus at center.'
adb shell input tap 540 1296

read -p 'Press <enter> to stop...'
adb shell input keyevent KEYCODE_VOLUME_DOWN
sleep 1

echo 'Confirm saving the file.'
adb shell input keyevent 66

echo 'Wait for 2s.'
sleep 2

# Dump the file.
file=$(adb shell 'ls /sdcard/DCIM/Camera' | tail -n 1)
cd ~/Desktop
adb pull /sdcard/DCIM/Camera/$file
adb shell rm /sdcard/DCIM/Camera/$file

# Preview the file.
mpv $file
