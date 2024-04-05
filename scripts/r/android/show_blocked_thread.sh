adb root

# Dumps tasks that are in uninterruptable (blocked) state.
# https://www.kernel.org/doc/html/v4.10/admin-guide/sysrq.html
adb shell "echo w > /proc/sysrq-trigger"

sleep 1
run_script r/logviewer.py -f "Show Blocked State" --cmdline adb shell dmesg -T
