#!/bin/bash

# https://cs.android.com/android/platform/superproject/+/master:external/perfetto/tools/record_android_trace

set -e
adb root

{{ include('_run_perfetto_text_config.sh', {'TRACE_CONFIG_STR': TRACE_CONFIG_STR, 'PERFETTO_DURATION_MS': PERFETTO_DURATION_MS}) }}

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
run_script r/android/perfetto/open_perfetto_trace.py "$trace" {{if PERFETTO_UI_URL}}--url "{{PERFETTO_UI_URL}}"{{end}}
{{end}}
