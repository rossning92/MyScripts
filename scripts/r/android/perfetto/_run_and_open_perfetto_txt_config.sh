#!/bin/bash

# https://cs.android.com/android/platform/superproject/+/master:external/perfetto/tools/record_android_trace

set -e
adb root

adb shell perfetto \
    -c - --txt \
    -o /data/misc/perfetto-traces/trace \
    <<EOF
{{TRACE_CONFIG_STR}}
duration_ms: {{PERFETTO_DURATION_MS}}
EOF

{{if PERFETTO_OUT_FILE}}
trace="{PERFETTO_OUT_FILE}"
{{else}}
cd "$HOME/Desktop/"
device=$(adb shell getprop ro.product.device | tr -d '\r')
trace="trace-$device-$(date +'%Y%m%d%H%M%S').perfetto-trace"
{{end}}
echo "Saving as '$trace'..."
adb pull /data/misc/perfetto-traces/trace "$trace"

{{if not PERFETTO_OUT_FILE}}
run_script r/android/perfetto/open_perfetto_trace.py "$trace"
{{end}}
