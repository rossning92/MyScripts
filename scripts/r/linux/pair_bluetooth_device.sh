set -e

# sudo systemctl restart bluetooth.service
# sleep 3

out=$(bluetoothctl --timeout 10 scan on | sed $'s,\x1b\\[[0-9;]*[a-zA-Z],,g' | grep 'NEW' | fzf)
mac_addr=$(echo "$out" | grep -o '[0-9a-fA-F:]\{17\}')
echo "$mac_addr"

echo "Start Bluetooth agent..."
bt-agent &
pid=$!

echo "Pairing $mac_addr"
bluetoothctl pair "$mac_addr" >/dev/null

echo "Stop Bluetooth agent..."
kill -INT $pid
