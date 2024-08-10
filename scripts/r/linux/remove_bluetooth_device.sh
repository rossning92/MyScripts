out=$(bluetoothctl devices Paired | sed $'s,\x1b\\[[0-9;]*[a-zA-Z],,g' | fzf)
mac_addr=$(echo "$out" | grep -o '[0-9a-fA-F:]\{17\}')
bluetoothctl untrust "$mac_addr"
bluetoothctl remove "$mac_addr"
