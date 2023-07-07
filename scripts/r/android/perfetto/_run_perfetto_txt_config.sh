#!/bin/bash

# https://cs.android.com/android/platform/superproject/+/master:external/perfetto/tools/record_android_trace

set -e
cd $HOME/Desktop/
adb root

adb shell perfetto \
    -c - --txt \
    -o /data/misc/perfetto-traces/trace \
    <<EOF
{{TRACE_CONFIG_STR}}
duration_ms: {{PERFETTO_DURATION_MS}}
EOF

device=$(adb shell getprop ro.product.device | tr -d '\r')
out_file="trace-$device-$(date +'%Y%m%d%H%M%S').perfetto-trace"
adb pull /data/misc/perfetto-traces/trace "$out_file"

run_script r/android/perfetto/open_perfetto_trace.py "$out_file"
