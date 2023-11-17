set -e
adb root
read -p "search:" kw
adb shell "find / -name '*$kw*' 2>/dev/null"
