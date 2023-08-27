set -e
source "$(dirname "$0")/_wsl_screen_workaround.sh"

name="$1"

screen -S $name -X hardcopy /tmp/screen_buffer.txt
cat /tmp/screen_buffer.txt | awk '/./{line=$0} END{print line}'
