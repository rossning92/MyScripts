set -e
name="$1"
if [[ -z "$name" ]]; then
    echo 'ERROR: session name cannot be empty'
    exit 1
fi

echo "$(cat)" >/tmp/screenbuf.txt
screen -xd -S $name -X msgwait 0
screen -xd -S $name -X readbuf /tmp/screenbuf.txt
screen -xd -S $name -X paste .
