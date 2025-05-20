set -e

screen -S "$1" -X hardcopy /tmp/screen_buffer.txt
cat /tmp/screen_buffer.txt
