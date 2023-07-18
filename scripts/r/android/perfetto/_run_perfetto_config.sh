#!/bin/bash

# https://cs.android.com/android/platform/superproject/+/master:external/perfetto/tools/record_android_trace

set -e
adb root

# Encode perfetto configurations into a binary file called "config.bin"
protoc --encode=perfetto.protos.TraceConfig -I "{{PERFETTO_REPO}}" protos/perfetto/config/perfetto_config.proto >config.bin <<EOF
{{TRACE_CONFIG_STR}}
duration_ms: {{PERFETTO_DURATION_MS}}
EOF

adb push config.bin /data/misc/perfetto-traces/config.bin

adb shell perfetto -c /data/misc/perfetto-traces/config.bin -o /data/misc/perfetto-traces/trace

{{ f'trace="{PERFETTO_OUT_FILE}"' if PERFETTO_OUT_FILE else r'''
cd "$HOME/Desktop/"
device=$(adb shell getprop ro.product.device | tr -d '\r')
trace="trace-$device-$(date +'%Y%m%d%H%M%S').perfetto-trace"''' }}
adb pull /data/misc/perfetto-traces/trace "$trace"

{{ "" if PERFETTO_OUT_FILE else 'run_script r/android/perfetto/open_perfetto_trace.py "$trace"' }}
