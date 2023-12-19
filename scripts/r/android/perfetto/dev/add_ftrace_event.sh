# https://perfetto.dev/docs/contributing/common-tasks#add-a-new-ftrace-event

set -e

source "$(dirname "$0")/_setup_perfetto_project.sh"

tools/run_ftrace_proto_gen

tools/gen_all out/ui

# Build tracebox and sideload

# Build UI
