# https://www.kernel.org/doc/html/v4.19/trace/events.html
# Must enable particular events for tracing before running the script,
# For example: echo 1 > /sys/kernel/debug/tracing/events/sched/sched_wakeup/enable

set -e

cd ~/Desktop
if [[ -z "$OUT_FILE" ]]; then
    OUT_FILE="trace.log"
    if [[ "$(uname -o)" == "Msys" ]]; then
        OUT_FILE="$(cygpath -w "${OUT_FILE}")"
    fi
fi

adb root

adb shell 'echo 0 >/sys/kernel/tracing/tracing_on'
adb shell 'echo 96000 >/sys/kernel/tracing/buffer_size_kb' # 96M

adb shell "echo '' >/sys/kernel/tracing/trace"

adb shell "echo 1 >/sys/kernel/tracing/tracing_on"

if [[ -z "$TRACE_SECOND" ]]; then
    adb shell cat /sys/kernel/tracing/trace_pipe >"$OUT_FILE" 2>&1 &
    run_script r/logviewer.py "$OUT_FILE"
else
    echo "Start tracking for ${TRACE_SECOND} seconds..."
    sleep "${TRACE_SECOND}"
fi

echo 'Stop tracing...'
adb shell "echo 0 >/sys/kernel/tracing/tracing_on"

if [[ -n "$TRACE_SECOND" ]]; then
    echo 'Copy trace result to /data/local/tmp/trace'
    adb shell 'cp /sys/kernel/tracing/trace /data/local/tmp/trace'
    adb pull -p /data/local/tmp/trace "$OUT_FILE"

    if [[ "$NO_OPEN" != "1" ]]; then
        run_script r/logviewer.py "$OUT_FILE"
    fi
fi
