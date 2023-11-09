pkg="${_PROC}"

echo -e ">>> Summary:"
pid=$(adb shell pidof "$pkg")
adb shell cat /proc/$pid/status | grep 'VmRSS'
adb shell dumpsys meminfo $pkg | grep -E 'TOTAL RSS|Graphics:'

echo -e ">>> adb shell dumpsys meminfo $pkg"
adb shell dumpsys meminfo $pkg

echo -e ">>> Private_maps"
adb shell cat /proc/$pid/private_maps | head

# https://poby.medium.com/linux-memory-demystified-eb33e81699b2
echo -e ">>> adb shell cat /proc/$pid/status"
adb shell cat /proc/$pid/status

echo -e ">>> adb shell dumpsys gfxinfo $pkg"
adb shell dumpsys gfxinfo $pkg

echo -e ">>> adb exec-out gpumeminfo -p $pid -o"
adb exec-out "gpumeminfo -p $pid -o"

echo -e ">>> dmabuf_dump"
adb shell dmabuf_dump $pid
