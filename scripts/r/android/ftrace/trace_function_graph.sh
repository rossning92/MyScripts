# https://lwn.net/Articles/370423/

set -e
adb root
adb shell cat /sys/kernel/tracing/available_tracers
adb shell cat /sys/kernel/tracing/current_tracer

adb shell 'echo 1 >/sys/kernel/tracing/options/funcgraph-proc'

echo 'Initialize function_graph tracer...'
adb shell 'echo 0 >/sys/kernel/tracing/tracing_on'
adb shell 'echo 96000 >/sys/kernel/tracing/buffer_size_kb' # 96M
adb shell "echo function_graph >/sys/kernel/tracing/current_tracer"

{{if FTRACE_FILTER}}
echo 'Set filter: {{FTRACE_FILTER}}'
adb shell "echo '{{FTRACE_FILTER}}' >/sys/kernel/tracing/set_ftrace_filter"
{{else}}
adb shell "echo '' >/sys/kernel/tracing/set_ftrace_filter"
{{end}}

{{if FTRACE_PID}}
echo 'Set ftrace pid: {{FTRACE_PID}}'
adb shell "echo '{{FTRACE_PID}}' >/sys/kernel/tracing/set_ftrace_pid"
{{else}}
adb shell "echo '' >/sys/kernel/tracing/set_ftrace_pid"
{{end}}

echo 'Start trace...'
adb shell "echo 1 >/sys/kernel/tracing/tracing_on"

echo 'Wait for 3 second...'
sleep 3

echo 'Pull trace file...'
adb shell 'cat /sys/kernel/tracing/trace | head -n 10000>/data/local/tmp/trace'
cd ~/Desktop/
adb pull /data/local/tmp/trace trace.txt

echo 'Cleanup...'
adb shell "echo nop >/sys/kernel/tracing/current_tracer"
adb shell "echo 0 >/sys/kernel/tracing/tracing_on"

run_script r/logviewer.py trace.txt
