#!/bin/bash


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
        else
            status="IDLE (No TTY mtime)"
        fi
    else
        tty="N/A"
        status="HANG"
    fi

    echo -e "$pid\t${tty#/dev/}\t$status"
done

