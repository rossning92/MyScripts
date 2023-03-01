while true; do
    read -p "find by keyword: " kw
    adb shell "find /sys -name '*${kw}*' 2>&1"
    printf "\n\n"
done
