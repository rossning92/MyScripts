# https://cs.android.com/android/platform/superproject/+/master:external/perfetto/tools/record_android_trace
import os

from _perfetto import start_trace

open_trace = bool(os.environ.get("OPEN_TRACE"))

start_trace(
    r"""
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
            atrace_categories: "pm"
            atrace_apps: "%s"
        }
    }
}

# Track event
data_sources: {
    config {
        name: "track_event"
        track_event_config {
            enabled_categories: "*"
        }
    }
}

# Memory
# https://perfetto.dev/docs/data-sources/memory-counters
# data_sources: {
#     config {
#         name: "linux.process_stats"
#         process_stats_config {
#             scan_all_processes_on_start: true
#             proc_stats_poll_ms: 100
#         }
#     }
# }
# data_sources: {
#     config {
#         name: "linux.ftrace"
#         ftrace_config {
#             ftrace_events: "mm_event/mm_event_record"
#             ftrace_events: "kmem/rss_stat"
#             ftrace_events: "kmem/ion_heap_grow"
#             ftrace_events: "kmem/ion_heap_shrink"
#         }
#     }
# }

duration_ms: 3000
"""
    % (os.environ["ATRACE_APPS"]),
    open_trace=open_trace,
)
