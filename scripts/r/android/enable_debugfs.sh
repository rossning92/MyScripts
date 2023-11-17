# https://source.android.com/docs/core/architecture/kernel/using-debugfs-12
set -e
adb root

adb shell "[ ! -d /sys/kernel/debug ] && mount -t debugfs debugfs /sys/kernel/debug || true"

# adb shell setprop persist.dbg.keep_debugfs_mounted 1
