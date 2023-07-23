set -e
adb root
while true; do
    read -p "find by keyword: " kw
    adb shell "find / -name '*${kw}*' 2>/dev/null"
    printf "(search completed)\n\n"
done
