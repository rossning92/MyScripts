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

if [[ -n "{{PERFETTO_OUT_FILE}}" ]]; then
    out_file="{{PERFETTO_OUT_FILE}}"
else
    cd "$HOME/Desktop/"
    device=$(adb shell getprop ro.product.device | tr -d '\r')
    out_file="trace-$device-$(date +'%Y%m%d%H%M%S').perfetto-trace"
fi

adb pull /data/misc/perfetto-traces/trace "$out_file"

if [[ -z "{{PERFETTO_OUT_FILE}}" ]]; then
    run_script r/android/perfetto/open_perfetto_trace.py "$out_file"
fi
