# https://lwn.net/Articles/370423/

set -e
adb root
adb shell cat /sys/kernel/tracing/available_tracers
adb shell cat /sys/kernel/tracing/current_tracer

echo 'Initialize function_graph tracer...'
adb shell 'echo 0 >/sys/kernel/tracing/tracing_on'
adb shell 'echo 96000 >/sys/kernel/tracing/buffer_size_kb' # 96M
adb shell "echo function_graph >/sys/kernel/tracing/current_tracer"

adb shell "echo >/sys/kernel/tracing/set_ftrace_filter"
# adb shell "echo dsi_* >>/sys/kernel/tracing/set_ftrace_filter"
# adb shell "echo mutex_* >>/sys/kernel/tracing/set_ftrace_filter"

# adb shell "echo '' >/sys/kernel/tracing/set_ftrace_pid"

echo 'Start trace...'
adb shell "echo 1 >/sys/kernel/tracing/tracing_on"

echo 'Pull trace file...'
adb shell 'cat /sys/kernel/tracing/trace | head -n 10000>/data/local/tmp/trace'
cd ~/Desktop/
adb pull /data/local/tmp/trace trace.txt

echo 'Cleanup...'
adb shell "echo nop >/sys/kernel/tracing/current_tracer"
adb shell "echo 0 >/sys/kernel/tracing/tracing_on"

run_script r/logviewer.py trace.txt
