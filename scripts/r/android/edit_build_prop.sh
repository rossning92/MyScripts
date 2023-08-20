adb shell "cat >/data/local/tmp/s.sh" <<EOF
    set -e
    mount -o rw,remount /
    if grep -q "net.tethering.noprovisioning=" /system/build.prop; then
        sed -i 's/net.tethering.noprovisioning=.*/net.tethering.noprovisioning=true/' /system/build.prop
    else
        echo "net.tethering.noprovisioning=true" >>/system/build.prop
    fi
    cat /system/build.prop
EOF
adb shell chmod +x /data/local/tmp/s.sh

adb shell su -c /data/local/tmp/s.sh
