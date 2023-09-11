#!/bin/bash

app=$1
cur_desktop=$(wmctrl -d | grep '\*' | cut -d ' ' -f1)
matched_win_ids=$(wmctrl -l | grep -- "$app" | grep " $cur_desktop " | awk '{print $1}')
win_ids=($(xprop -root | awk -F'# ' '/_NET_CLIENT_LIST_STACKING/ {gsub(/,/, " "); print $2}'))

for ((idx = ${#win_ids[@]} - 1; idx >= 0; idx--)); do
    for i in $matched_win_ids; do
        if [[ $((i)) == $((win_ids[idx])) ]]; then
            wmctrl -ia $i
            exit 0
        fi
    done
done

exit 1
