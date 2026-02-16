adb root
while true; do
    adb exec-out dmesg --follow
done
