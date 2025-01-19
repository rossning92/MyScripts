# https://cs.android.com/android/platform/superproject/+/master:external/perfetto/tools/record_android_trace

# PERFETTO_DURATION_MS, PERFETTO_OUT_FILE
{{ include('r/android/perfetto/_run_and_open_perfetto_txt_config.sh', {'TRACE_CONFIG_STR': '''
buffers: {
    size_kb: 63488
    fill_policy: DISCARD
}
buffers: {
    size_kb: 4096
    fill_policy: DISCARD
}
data_sources: {
    config {
        name: "linux.ftrace"
        ftrace_config {
            ftrace_events: "raw_syscalls/sys_enter"
            ftrace_events: "raw_syscalls/sys_exit"
        }
    }
}
'''}) }}
