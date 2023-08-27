set -e

source "$(dirname "$0")/_wsl_screen_workaround.sh"

name="$1"
command="$2"
screen -S $name -X stuff "${command}"
