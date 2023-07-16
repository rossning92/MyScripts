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

{{ f'trace="{PERFETTO_OUT_FILE}"' if PERFETTO_OUT_FILE else r'''
cd "$HOME/Desktop/"
device=$(adb shell getprop ro.product.device | tr -d '\r')
trace="trace-$device-$(date +'%Y%m%d%H%M%S').perfetto-trace"''' }}
adb pull /data/misc/perfetto-traces/trace "$trace"

{{ "" if PERFETTO_OUT_FILE else 'run_script r/android/perfetto/open_perfetto_trace.py "$trace"' }}
