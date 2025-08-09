# https://github.com/Layerex/dmenu-bluetooth/blob/master/dmenu-bluetooth

echo 'Start scan...'
bluetoothctl --timeout 100 scan on >/dev/null &
scan_pid=$!

addr=$(bluetoothctl devices | fzf --header "Scanning for devices... (Press Ctrl+R to refresh)" --bind "ctrl-r:reload:bluetoothctl devices" | grep -o '[0-9a-fA-F:]\{17\}')
if [ -z "$addr" ]; then
    echo "Scan cancelled"
    kill -INT $scan_pid 2>/dev/null
    exit 0
fi

echo 'Stop scan...'
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
