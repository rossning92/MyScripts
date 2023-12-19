set -e

source "$(dirname "$0")/_setup_perfetto_project.sh"

tools/install-build-deps --ui

ui/build

ui/run-dev-server --serve-port 10005
