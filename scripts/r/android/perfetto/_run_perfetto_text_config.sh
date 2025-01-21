adb shell perfetto \
    -c - --txt \
    -o /data/misc/perfetto-traces/trace \
    <<EOF
{{TRACE_CONFIG_STR}}
duration_ms: {{PERFETTO_DURATION_MS}}
EOF
