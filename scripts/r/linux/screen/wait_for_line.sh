set -e

name="$1"
line="$2"

while true; do
    screen -S $name -X hardcopy /tmp/screen_buffer.txt
    last_line="$(cat /tmp/screen_buffer.txt | awk '/./{line=$0} END{print line}')"
    echo "$last_line"
    if [[ "$last_line" == *"$line"* ]]; then
        break
    fi
    sleep 1
done
