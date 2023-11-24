# https://cs.android.com/android/platform/superproject/+/master:external/perfetto/tools/record_android_trace

# PERFETTO_DURATION_MS, PERFETTO_OUT_FILE
{{ include('r/android/perfetto/_run_perfetto_txt_config.sh', {'TRACE_CONFIG_STR': '''
buffers: {
    size_kb: 129024
    fill_policy: DISCARD
}
buffers: {
    size_kb: 129024
    fill_policy: DISCARD
}
data_sources: {
    config {
        name: "track_event"
        target_buffer: 0
        track_event_config {
            enabled_categories: "*"
        }
    }
}
'''}) }}
