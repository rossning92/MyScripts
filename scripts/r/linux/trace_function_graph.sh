# https://lwn.net/Articles/370423/

set -e
adb root
adb shell cat /sys/kernel/tracing/available_tracers
adb shell cat /sys/kernel/tracing/current_tracer

echo 'Initialize function_graph tracer...'
adb shell 'echo 0 >/sys/kernel/tracing/tracing_on'
adb shell 'echo 96000 >/sys/kernel/tracing/buffer_size_kb' # 96M
adb shell "echo function_graph >/sys/kernel/tracing/current_tracer"

echo 'Start trace...'
adb shell "echo 1 >/sys/kernel/tracing/tracing_on"
sleep 0.1
echo 'Stop trace...'
adb shell "echo 0 >/sys/kernel/tracing/tracing_on"

echo 'Pull trace file...'
adb shell 'cat /sys/kernel/tracing/trace | head -n 1000>/data/local/tmp/trace'

echo 'Cleanup...'
adb shell "echo nop >/sys/kernel/tracing/current_tracer"

cd ~/Desktop
adb pull /data/local/tmp/trace trace.txt
cmd /c start trace.txt
