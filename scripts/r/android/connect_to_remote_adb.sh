kill -9 `pidof adb`

if ! ps h -o pid -C socat; then
    killall java >/dev/null 2>/dev/null
    killall adb >/dev/null 2>/dev/null
    socat TCP-LISTEN:5037,fork TCP:localhost:15037 >/dev/null &
fi
