set -e

source "$(dirname "$0")/_wsl_screen_workaround.sh"

screen -S od -X hardcopy /tmp/screen_buffer.txt
cat /tmp/screen_buffer.txt
