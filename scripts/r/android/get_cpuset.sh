pid=$(adb shell pidof "{{_PROC_NAME}}")
echo "{{_PROC_NAME}}: $pid"
printf "\n"

# echo "cat /proc/$pid/cpuset"
# echo "(cpuset file in procfs which shows where in the hierarchy the process is attached to)"
# cpuset_file=$(adb shell "cat /proc/$pid/cpuset")
# printf "${cpuset_file}\n"

# adb shell "ls /dev/cpuset/${cpuset_file}"

adb shell "cat /proc/$pid/status" | grep Cpus_allowed

adb shell "taskset -p $pid"

# taskset -p 4 $pid
