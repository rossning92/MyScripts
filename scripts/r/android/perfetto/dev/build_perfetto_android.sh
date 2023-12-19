# https://perfetto.dev/docs/contributing/build-instructions#standalone-builds

set -e

source "$(dirname "$0")/_setup_perfetto_project.sh"

tools/install-build-deps --android

tools/gn args out/android

tools/ninja -C out/android
