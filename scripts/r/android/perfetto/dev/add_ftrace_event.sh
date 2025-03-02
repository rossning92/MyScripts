# https://perfetto.dev/docs/contributing/common-tasks#add-a-new-ftrace-event

set -e

source "$(dirname "$0")/_setup_perfetto_project.sh"

tools/install-build-deps

# 1. Add src/traced/probes/ftrace/test/data/synthetic/events/EVENT_GROUP/EVENT_NAME/format

# 2. Add the event to src/tools/ftrace_proto_gen/event_list.

# This will update ftrace_event.proto
tools/run_ftrace_proto_gen

mkdir -p out/
mkdir -p out/android
# This will update event_info.cc and perfetto_trace.proto
tools/gen_all out/android

# Build tracebox and sideload

# Build UI
