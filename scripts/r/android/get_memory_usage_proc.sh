pkg="${_PROC}"

pid=$(adb shell pidof "$pkg")
adb shell cat /proc/$pid/private_maps | head

# https://poby.medium.com/linux-memory-demystified-eb33e81699b2
echo -e "\n\n\n\nadb shell cat /proc/$pid/status"
adb shell cat /proc/$pid/status | grep --color 'VmRSS\|$'

echo -e "\n\n\n\nadb shell dumpsys meminfo $pkg"
adb shell dumpsys meminfo $pkg | grep --color 'RSS\|$'

# adb shell dumpsys gfxinfo $pkg
# adb exec-out gpumeminfo -p $pid | grep "Total"
