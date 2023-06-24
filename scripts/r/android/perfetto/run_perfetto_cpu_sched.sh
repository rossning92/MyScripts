{{ include('r/android/perfetto/run_perfetto_txt_config.sh', {'TRACE_CONFIG_STR': '''
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
        name: "linux.process_stats"
        target_buffer: 1
        process_stats_config {
            scan_all_processes_on_start: true
        }
    }
}
data_sources: {
    config {
        name: "linux.sys_stats"
        sys_stats_config {
            stat_period_ms: 1000
            stat_counters: STAT_CPU_TIMES
            stat_counters: STAT_FORK_COUNT
        }
    }
}
data_sources: {
    config {
        name: "linux.ftrace"
        ftrace_config {
            ftrace_events: "ftrace/print"
            ftrace_events: "power/suspend_resume"
            ftrace_events: "sched/sched_process_exit"
            ftrace_events: "sched/sched_process_free"
            ftrace_events: "sched/sched_switch"
            ftrace_events: "sched/sched_wakeup_new"
            ftrace_events: "sched/sched_wakeup"
            ftrace_events: "sched/sched_waking"
            ftrace_events: "task/task_newtask"
            ftrace_events: "task/task_rename"
            atrace_categories: "gfx"
            atrace_apps: "*"
            # ftrace_events: "raw_syscalls/sys_enter"
            # ftrace_events: "raw_syscalls/sys_exit"
        }
    }
}
data_sources: {
    config {
        name: "track_event"
        track_event_config {
            enabled_categories: "*"
            # enabled_categories: "gpu_renderstage"
            # enabled_categories: "gpu_surface_workload"
        }
    }
}
'''}) }}

# PERFETTO_DURATION_MS, PERFETTO_REPO