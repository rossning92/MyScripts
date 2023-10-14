set -e

screen -S od -X hardcopy /tmp/screen_buffer.txt
cat /tmp/screen_buffer.txt
