echo 'Wait for sys.boot_completed...'
while [ "$(adb shell getprop sys.boot_completed | tr -d '\r')" != "1" ]; do sleep 1; done
sleep 10
