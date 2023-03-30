pkg="${_PROC}"

pid=$(adb shell pidof "$pkg")
adb shell cat /proc/$pid/status | grep 'VmRSS'
adb shell dumpsys meminfo $pkg | grep -E 'TOTAL RSS|Graphics:'
printf "\n\n\n"

adb shell cat /proc/$pid/private_maps | head

# https://poby.medium.com/linux-memory-demystified-eb33e81699b2
echo -e "\n\n\n\n> adb shell cat /proc/$pid/status"
adb shell cat /proc/$pid/status

echo -e "\n\n\n\n> adb shell dumpsys meminfo $pkg"
adb shell dumpsys meminfo $pkg

echo -e "\n\n\n\n> adb shell dumpsys gfxinfo $pkg"
adb shell dumpsys gfxinfo $pkg

echo -e "\n\n\n\n> adb exec-out gpumeminfo -p $pid -o"
adb exec-out "gpumeminfo -p $pid -o"
