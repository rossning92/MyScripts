# PERFETTO_DURATION_MS, PERFETTO_REPO, PERFETTO_OUT_FILE
{{ include('r/android/perfetto/_run_perfetto_txt_config.sh', {'TRACE_CONFIG_STR': include('_perfetto_config_default.txt')}) }}
