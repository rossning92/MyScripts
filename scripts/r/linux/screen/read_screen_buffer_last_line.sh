set -e

name="$1"

screen -S $name -X hardcopy /tmp/screen_buffer.txt
cat /tmp/screen_buffer.txt | awk '/./{line=$0} END{print line}'
