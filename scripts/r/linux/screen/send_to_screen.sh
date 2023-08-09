set -e

source "$(dirname "$0")/_wsl_screen_workaround.sh"

command="$1"
screen -d -X stuff "${command}"
