# https://github.com/Layerex/dmenu-bluetooth/blob/master/dmenu-bluetooth

echo 'Start scan...'
bluetoothctl --timeout 100 scan on >/dev/null &
scan_pid=$!
sleep 3

while true; do
    out=$(bluetoothctl devices | fzf)
    addr=$(echo "$out" | grep -o '[0-9a-fA-F:]\{17\}')
    if [[ -n "$addr" ]]; then
        break
    fi
done

kill -INT $scan_pid

echo "Start Bluetooth agent..."
bt-agent &
pid=$!

echo "Pairing $addr"
bluetoothctl pair "$addr" >/dev/null
bluetoothctl trust "$addr"
bluetoothctl connect "$addr"

echo "Stop Bluetooth agent..."
kill -INT $pid
