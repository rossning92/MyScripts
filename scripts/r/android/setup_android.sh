set -e

echo 'Disable window animation...'
adb shell settings put global window_animation_scale 0
adb shell settings put global transition_animation_scale 0
adb shell settings put global animator_duration_scale 0

if [[ -n ${_REMOVE_WALLPAPER} ]]; then
    echo 'Remove wallpaper...'
    magick -size 32x32 xc:black empty.png
    adb push empty.png /sdcard/empty.png
    rm empty.png
    adb shell am start -a android.intent.action.ATTACH_DATA -c android.intent.category.DEFAULT -d file:///sdcard/empty.png -t "image/*" -e mimeType "image/*"
fi

# echo 'Disable navigation gestures...'
# adb shell settings put system op_navigation_bar_type 3 # Navigation gestures
# adb shell settings put system status_bar_show_battery_percent 1

# echo 'Enable Lift up display (OP5t)...'
# adb shell settings put system prox_wake_enabled 1
# adb shell settings put system doze_enabled 1
# adb shell settings put system aod_clock_style 1

# https://github.com/agnostic-apollo/Android-Docs/blob/master/en/docs/apps/processes/phantom-cached-and-empty-processes.md#commands-to-disable-phantom-process-killing-and-tldr
echo 'Disable the phantom processes killing'
ANDROID_VERSION=$(adb shell getprop ro.build.version.release | tr -d '[:space:]')
if [ "$ANDROID_VERSION" -ge "14" ]; then
    adb shell su -c "setprop persist.sys.fflag.override.settings_enable_monitor_phantom_procs false"
fi
