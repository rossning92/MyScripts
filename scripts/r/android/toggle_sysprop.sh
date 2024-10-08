toggle_sysprop() {
    while true; do
        val=$(adb shell getprop $1 | tr -d '\r')
        read -n1 -p 'wait for key' ans
        if [[ "$val" == '1' ]]; then
            echo "Set $1 = 0"
            adb shell setprop $1 0
        else
            echo "Set $1 = 1"
            adb shell setprop $1 1
        fi
    done
}
