# https://source.android.com/docs/core/architecture/kernel/using-debugfs-12
set -e
adb root

if ! adb shell mountpoint -q /sys/kernel/debug; then
    adb shell mount -t debugfs debugfs /sys/kernel/debug
else
    echo "debugfs is already mounted."
fi

# adb shell setprop persist.dbg.keep_debugfs_mounted 1
