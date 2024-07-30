# https://cs.android.com/android/platform/superproject/+/master:external/perfetto/tools/record_android_trace
# https://perfetto.dev/docs/reference/trace-config-proto#HeapprofdConfig

# PERFETTO_DURATION_MS, PERFETTO_REPO, PERFETTO_OUT_FILE
{{ include('r/android/perfetto/_run_perfetto_txt_config.sh', {'TRACE_CONFIG_STR': '''
buffers: {
    size_kb: 131072
    fill_policy: DISCARD
}

buffers: {
    size_kb: 131072
    fill_policy: DISCARD
}


data_sources: {
    config {
        name: "android.packages_list"
        target_buffer: 1
    }
}

data_sources: {
    config {
        name: "android.heapprofd"
        target_buffer: 0
        heapprofd_config {
            sampling_interval_bytes: 4096
            process_cmdline: "''' + HEAPPROF_PROC + '''"
            continuous_dump_config {
                dump_phase_ms: 1000
                dump_interval_ms: 1000
            }
            shmem_size_bytes: 8388608
            block_client: true
        }
    }
}
'''
}) }}
