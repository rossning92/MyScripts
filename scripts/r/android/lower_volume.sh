# # set volume of media to $value (0-15)
# adb shell media volume --show --stream 3 --set 0
# # media vol +
# adb shell media volume --show --adj raise
# # media vol -
# adb shell media volume --show --adj lower
# # play - pause
# adb shell media dispatch play-pause
# #next
# adb shell media dispatch next
# #prev
# adb shell media dispatch previous >/dev/null

for i in {1..10}; do adb shell input keyevent 25; done
