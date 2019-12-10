adb shell settings put global window_animation_scale 0
adb shell settings put global transition_animation_scale 0
adb shell settings put global animator_duration_scale 0


magick -size 32x32 xc:black empty.png
adb push empty.png /sdcard/empty.png
rm empty.png
adb shell am start -a android.intent.action.ATTACH_DATA -c android.intent.category.DEFAULT -d file:///sdcard/empty.png -t "image/*" -e mimeType "image/*"
