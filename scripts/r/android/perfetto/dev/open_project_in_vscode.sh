set -e

source "$(dirname "$0")/_setup_perfetto_project.sh"

code --remote wsl+Ubuntu-20.04 "$(pwd)"
