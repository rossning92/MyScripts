set -e

source "$(dirname "$0")/_wsl_screen_workaround.sh"

screen -d -X stuff 'push\n'
