set -e

name="$1"

source "$(dirname "$0")/_wsl_screen_workaround.sh"

# Kill screen sessions by name
screen -ls | grep $name | cut -d. -f1 | awk '{print $1}' | xargs kill
