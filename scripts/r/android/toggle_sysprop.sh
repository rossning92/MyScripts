{{val=SYSPROP_VAL if 'SYSPROP_VAL' in globals() else 1}}
toggle_sysprop() {
    while true; do
        val=$(adb shell getprop $1 | tr -d '\r')
        read -n1 -p 'wait for key' ans
        if [[ "$val" == '{{val}}' ]]; then
            echo "Set $1 = 0"
            adb shell setprop $1 0
        else
            echo "Set $1 = {{val}}"
            adb shell setprop $1 {{val}}
        fi
    done
}
toggle_sysprop {{SYSPROP_NAME}}
