# PERFETTO_DURATION_MS, PERFETTO_OUT_FILE, CALLSTACK_SAMPLING_PROCESS
{{ include('r/android/perfetto/_run_perfetto_txt_config.sh', {'TRACE_CONFIG_STR': include('_perfetto_config_default.txt')}) }}
