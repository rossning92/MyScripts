# https://perfetto.dev/docs/quickstart/android-tracing#recording-a-trace

set -e

source "$(dirname "$0")/_setup_perfetto_project.sh"

tools/record_android_trace -t 3s --sideload-path out/android/tracebox sched
