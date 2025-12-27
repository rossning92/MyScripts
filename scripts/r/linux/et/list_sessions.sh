#!/bin/bash

threshold_seconds=$((12 * 60 * 60))
inactive_pids=()

echo -e "PID\tTTY\tSTATUS"
echo -e "---\t---\t------"

for pid in $(pgrep etterminal); do
    # Get TTY index from fdinfo if it exists (ptmx is usually FD 7)
    tty_index=$(grep -s "tty-index:" /proc/$pid/fdinfo/7 | awk '{print $2}')
    if [ -n "$tty_index" ]; then
        tty="/dev/pts/$tty_index"

        mtime=$(stat -c %Y "$tty" 2>/dev/null)
        if [ -n "$mtime" ]; then
            now=$(date +%s)
            idle=$((now - mtime))
            status=$(awk -v s="$idle" 'BEGIN{if(s>=3600)printf "IDLE %dh%dm%ds",int(s/3600),int(s%3600/60),int(s%60);else if(s>=60)printf "IDLE %dm%ds",int(s/60),int(s%60);else printf "IDLE %ds",s}')
            if [ "$idle" -ge "$threshold_seconds" ]; then
                inactive_pids+=("$pid")
            fi
        else
            status="IDLE (No TTY mtime)"
        fi
    else
        tty="N/A"
        status="HANG"
        inactive_pids+=("$pid")
    fi

    echo -e "$pid\t${tty#/dev/}\t$status"
done

if [ "${#inactive_pids[@]}" -gt 0 ]; then
    echo
    read -r -p "Kill inactive sessions (>12h)? [y/N] " answer
    if [[ "$answer" =~ ^[Yy]$ ]]; then
        kill "${inactive_pids[@]}" 2>/dev/null
    fi
fi
